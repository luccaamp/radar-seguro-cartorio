"""Orquestrador único do projeto.

Uso:
  uv run pipeline.py                         # bronze -> silver -> contratos -> gold -> qualidade (sem internet)
  uv run pipeline.py --a-partir-de bronze    # o mesmo
  uv run pipeline.py --a-partir-de silver    # recalcula o gold a partir de data/silver/*.parquet (sem bronze)
  uv run pipeline.py silver                  # só bronze -> silver (+ contratos do silver)
  uv run pipeline.py gold                    # só silver -> gold, com o silver do banco atual
  uv run pipeline.py ingest                  # coleta (precisa de internet; idempotente, só baixa o que falta)
"""
import argparse
import os
import sys
from pathlib import Path

import duckdb
import pandas as pd
import yaml

from src import estado
from src.quality import contratos, reconciliacao
from src.transform import gold, silver
from src.transform.silver import BANCO, CONFIG, SILVER

ETAPAS = ("all", "silver", "gold", "gold_de_parquet", "ingest")


def etapa_ingest() -> None:
    from src.ingest import (cnj_arrecadacoes, cnj_complementares, cnj_serventias, cnpj, ibge, legislacao, rais,
                            susep)
    esc = yaml.safe_load((CONFIG / "escopo.yaml").read_text(encoding="utf-8"))
    for uf in esc["ufs"]:
        cnj_serventias.coletar(uf)
        cnj_complementares.coletar(uf)
        cnj_arrecadacoes.coletar(uf)
        ibge.coletar(uf)
        rais.filtrar(rais.baixar(esc["snapshots"]["rais"], rais.PACOTE_UF[uf]), uf)
    cnpj.filtrar(cnpj.baixar(esc["snapshots"]["cnpj"]))
    susep.filtrar(susep.baixar())
    legislacao.coletar()
    print("Atenção: atualize config/escopo.yaml se quiser que o pipeline use os snapshots novos.")


def _relatar(df: pd.DataFrame) -> None:
    erros = (df.violacoes > 0) & (df.severidade == "erro")
    avisos = (df.violacoes > 0) & (df.severidade == "aviso")
    print(f"  {len(df)} checagens | {int((df.violacoes == 0).sum())} ok | {int(avisos.sum())} avisos | {int(erros.sum())} erros")
    for _, r in df[df.violacoes > 0].iterrows():
        print(f"  [{r.severidade.upper()}] {r.tabela}: {r.checagem} -> {r.violacoes:,} {r.detalhe}")
    if erros.any():
        raise SystemExit("Pipeline interrompido: contrato violado (ver acima).")


def etapa_silver(con) -> None:
    print("bronze -> silver")
    for tabela, n in silver.construir(con).items():
        print(f"  silver.{tabela}: {n:,} linhas")
    print("contratos do silver")
    _relatar(contratos.gravar(con, contratos.contratos_silver(con), "silver"))


def etapa_gold(con, exportar_parquet: bool = True) -> None:
    print("silver -> gold")
    for tabela, n in gold.construir(con, exportar_parquet).items():
        print(f"  gold.{tabela}: {n:,} linhas")
    print("contratos do gold")
    _relatar(contratos.gravar(con, reconciliacao.contratos_gold(con), "gold"))
    print("reconciliações entre fontes")
    for r in reconciliacao.reconciliar(con).itertuples():
        ind = ("" if pd.isna(r.indicador) else f"{r.indicador:+.1%}" if pd.notna(r.valor_b) else f"{r.indicador:.3f}")
        print(f"  [{r.status.upper()}] {r.checagem}: {ind} (tolerância {r.tolerancia}) {r.detalhe}")


def _silver_de_parquet(con, pasta: Path = SILVER) -> None:
    """Carrega o silver a partir dos Parquet de data/silver (camada instalada por scripts/baixar_dados.py) e roda os
    contratos do silver de novo sobre ele."""
    arquivos = sorted(pasta.glob("*.parquet"))
    if not arquivos:
        raise SystemExit(f"Nenhum Parquet em {pasta}. Instale o silver antes: uv run python scripts/baixar_dados.py "
                         "--nivel publico --camadas silver (ver README, 'Como rodar').")
    print(f"silver a partir de {pasta} ({len(arquivos)} tabelas)")
    con.execute("CREATE SCHEMA IF NOT EXISTS silver")
    for arq in arquivos:
        con.execute(f"CREATE OR REPLACE TABLE silver.{arq.stem} AS SELECT * FROM read_parquet('{arq.as_posix()}')")
    print("contratos do silver")
    _relatar(contratos.gravar(con, contratos.contratos_silver(con), "silver"))


def _trazer_do_banco_antigo(con, antigo: Path, etapa: str) -> None:
    """Copia para o banco novo o que a etapa não recria: o estado do usuário sempre; o silver (e as checagens do
    silver) quando a etapa é só o gold."""
    estado.criar_tabelas(con)
    if not antigo.exists():
        return
    con.execute(f"ATTACH '{antigo.as_posix()}' AS antigo (READ_ONLY)")
    existe = lambda esq, tab: con.execute(  # noqa: E731
        "SELECT count(*) FROM information_schema.tables WHERE table_catalog = 'antigo' AND table_schema = ? "
        "AND table_name = ?", [esq, tab]).fetchone()[0] > 0
    for tab in estado.TABELAS_ESTADO:
        if existe("estado", tab):
            con.execute(f"INSERT INTO estado.{tab} SELECT * FROM antigo.estado.{tab}")
    if etapa == "gold":
        con.execute("CREATE SCHEMA IF NOT EXISTS silver")
        for (tab,) in con.execute("SELECT table_name FROM information_schema.tables WHERE table_catalog = 'antigo' "
                                  "AND table_schema = 'silver'").fetchall():
            con.execute(f"CREATE TABLE silver.{tab} AS SELECT * FROM antigo.silver.{tab}")
        if existe("qualidade", "checagens"):
            con.execute("CREATE SCHEMA IF NOT EXISTS qualidade")
            con.execute("CREATE TABLE qualidade.checagens AS SELECT * FROM antigo.qualidade.checagens "
                        "WHERE camada = 'silver'")
    con.execute("DETACH antigo")


def main(etapa: str = "all", banco: Path = BANCO, exportar_parquet: bool = True) -> None:
    """Carga atômica (1.7): grava num arquivo temporário e só troca o banco no fim. Se a carga falhar, o banco
    anterior fica como estava; o arquivo não cresce de uma carga para outra.
    `exportar_parquet=False` (testes) só vale para a etapa gold; a etapa silver sempre exporta.
    `gold_de_parquet` (= --a-partir-de silver): o silver vem de data/silver/*.parquet, não do banco antigo."""
    if etapa not in ETAPAS:
        raise SystemExit(f"Etapa desconhecida: {etapa!r}. Use uv run pipeline.py --help.")
    if etapa == "ingest":
        etapa_ingest()
        return
    banco = Path(banco)
    temp = banco.with_name(banco.name + ".novo")
    for resto in (temp, temp.with_name(temp.name + ".wal")):   # sobra de uma carga anterior que falhou
        resto.unlink(missing_ok=True)
    try:
        with duckdb.connect(str(temp)) as con:
            _trazer_do_banco_antigo(con, banco, etapa)
            if etapa in ("all", "silver"):
                etapa_silver(con)
            if etapa == "gold_de_parquet":
                _silver_de_parquet(con)
            if etapa in ("all", "gold", "gold_de_parquet"):
                etapa_gold(con, exportar_parquet)
            con.execute("CHECKPOINT")
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    try:
        os.replace(temp, banco)
    except PermissionError as e:
        temp.unlink(missing_ok=True)
        raise SystemExit(f"Não foi possível trocar {banco.name}: o arquivo está aberto por outro programa "
                         "(feche o painel e rode de novo). O banco anterior não foi alterado.") from e


def argumentos(argv: list[str] | None = None) -> str:
    """Lê a linha de comando e devolve a etapa. Argumento desconhecido = erro, sem tocar no banco."""
    a = argparse.ArgumentParser(
        prog="uv run pipeline.py",
        description="Carga do Radar: bronze -> silver -> gold, com contratos e auditoria LGPD. Grava data/radar.duckdb "
                    "de forma atômica (o banco anterior só é trocado se a carga terminar).",
        epilog="Exemplos: 'uv run pipeline.py' (tudo a partir do bronze); 'uv run pipeline.py --a-partir-de silver' "
               "(gold a partir de data/silver, sem bronze); 'uv run pipeline.py ingest' (coleta; precisa de internet).")
    a.add_argument("etapa", nargs="?", choices=["all", "silver", "gold", "ingest"], default=None,
                   help="etapa isolada (modo antigo): silver = só bronze -> silver; gold = só silver -> gold com o "
                        "silver do banco atual; ingest = coleta")
    a.add_argument("--a-partir-de", choices=["bronze", "silver"], dest="a_partir_de",
                   help="bronze: recalcula silver e gold; silver: recalcula o gold a partir de data/silver/*.parquet, "
                        "sem coletar nem ler o bronze")
    args = a.parse_args(argv)
    if args.etapa and args.a_partir_de:
        a.error("use a etapa ou --a-partir-de, não os dois")
    if args.a_partir_de:
        return {"bronze": "all", "silver": "gold_de_parquet"}[args.a_partir_de]
    return args.etapa or "all"


if __name__ == "__main__":
    # saída em UTF-8 também quando redirecionada para arquivo ou pipe: o cp1252 do Windows não tem "≥" nem "−"
    # (docs/erros_ia.md, 2026-10-20)
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    main(argumentos(sys.argv[1:]))
