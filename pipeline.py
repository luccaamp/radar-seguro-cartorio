"""Orquestrador único do projeto.

Uso:
  uv run pipeline.py            # do zero a partir dos snapshots do bronze: silver -> contratos -> gold -> qualidade (sem internet)
  uv run pipeline.py silver     # só bronze -> silver (+ contratos do silver)
  uv run pipeline.py gold       # só silver -> gold (+ contratos e reconciliações)
  uv run pipeline.py ingest     # coleta (precisa de internet; idempotente, só baixa o que falta)
"""
import sys

import duckdb
import pandas as pd
import yaml

from src.quality import contratos, reconciliacao
from src.transform import gold, silver
from src.transform.silver import BANCO, CONFIG


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


def etapa_gold(con) -> None:
    print("silver -> gold")
    for tabela, n in gold.construir(con).items():
        print(f"  gold.{tabela}: {n:,} linhas")
    print("contratos do gold")
    _relatar(contratos.gravar(con, reconciliacao.contratos_gold(con), "gold"))
    print("reconciliações entre fontes")
    for r in reconciliacao.reconciliar(con).itertuples():
        ind = ("" if pd.isna(r.indicador) else f"{r.indicador:+.1%}" if pd.notna(r.valor_b) else f"{r.indicador:.3f}")
        print(f"  [{r.status.upper()}] {r.checagem}: {ind} (tolerância {r.tolerancia}) {r.detalhe}")


def main(etapa: str = "all") -> None:
    if etapa == "ingest":
        etapa_ingest()
        return
    with duckdb.connect(str(BANCO)) as con:
        if etapa in ("all", "silver"):
            etapa_silver(con)
        if etapa in ("all", "gold"):
            etapa_gold(con)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
