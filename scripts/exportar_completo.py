"""Silver sem dado pessoal, gold completo e o CSV do BI do CNJ em data/completo/ (versionado no git, D-050), para quem
clona o repositório abrir o painel em modo completo sem baixar Release:

  uv run python scripts/exportar_completo.py             # regrava data/completo/ a partir de data/ e do banco
  uv run python scripts/exportar_completo.py --instalar  # (quem clonou) instala o silver e o CSV do BI em data/;
  uv run pipeline.py --a-partir-de silver                # depois recalcula o gold e grava data/radar.duckdb

O silver sai como no pacote público (D-030, D-031: sem as colunas de silver_publico_remover) e só se o contrato de
"sem dado pessoal" passar; o gold sai inteiro (inclusive interno_*), exportado do banco em só leitura. O CSV do BI do
CNJ (exportação manual, sem dado pessoal) vai comprimido: as tabelas analise_capacidade_*, analise_sinistro e uma
linha da analise_sensibilidade_metodo dependem dele. O --instalar confere o SHA-256 de cada arquivo e nunca
sobrescreve dados locais.
"""
import argparse
import gzip
import json
import shutil
import sys
import tempfile
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
from empacotar_dados import commit, gold_completo, silver_publico, silver_sem_dado_pessoal  # noqa: E402
from src import pacotes  # noqa: E402
from src.analise.dados import arquivo_bi  # noqa: E402
from src.transform.silver import BANCO, SILVER  # noqa: E402

DESTINO = RAIZ / "data" / "completo"


def bi_comprimido(pasta: Path) -> list[Path]:
    """O CSV do BI e o .meta.json dele, no mesmo caminho relativo do bronze; o CSV em gzip sem data (mesmo SHA-256)."""
    origem = arquivo_bi()
    destino = pasta / origem.relative_to(RAIZ / "data")
    destino.parent.mkdir(parents=True)
    gz = destino.with_name(origem.name + ".gz")
    with open(origem, "rb") as e, open(gz, "wb") as bruto, gzip.GzipFile(fileobj=bruto, mode="wb", mtime=0,
                                                                         filename="") as s:
        shutil.copyfileobj(e, s)
    meta = origem.with_name(origem.name + ".meta.json")
    shutil.copy2(meta, destino.parent / meta.name)
    return [gz, destino.parent / meta.name]


def exportar() -> None:
    with duckdb.connect(str(BANCO), read_only=True) as con:
        silver_sem_dado_pessoal(con)
        execucao = con.execute("SELECT * FROM gold.execucao").df().iloc[0]
        with tempfile.TemporaryDirectory() as tmp:
            novo = Path(tmp) / "completo"
            silver, retiradas = silver_publico(novo / "silver")
            gold = gold_completo(con, novo / "gold")
            bi = bi_comprimido(novo)
            manifesto = {
                "descricao": "Silver sem dado pessoal (D-031), gold completo e CSV do BI do CNJ da carga atual (D-050). "
                             "Para o modo completo: 'uv run python scripts/exportar_completo.py --instalar' e "
                             "'uv run pipeline.py --a-partir-de silver'.",
                "carga": f"{execucao['executado_em']:%Y-%m-%d}",
                "versao_premissas": int(execucao["versao_premissas"]),
                **commit(),
                "colunas_retiradas": retiradas,
                "arquivos": {p.relative_to(novo).as_posix(): pacotes.sha256(p) for p in silver + gold + bi},
            }
            (novo / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1), encoding="utf-8")
            if DESTINO.exists():
                shutil.rmtree(DESTINO)   # só o que este script gerou antes (versionado no git)
            mb_bi = bi[0].stat().st_size / 1e6
            shutil.copytree(novo, DESTINO)
    print(f"data/completo/: {len(silver)} tabelas do silver ({len(retiradas)} colunas retiradas), {len(gold)} do gold, "
          f"CSV do BI ({mb_bi:,.1f} MB comprimido)")


def instalar() -> None:
    """Silver em data/silver/ e o CSV do BI no bronze, conferindo o SHA-256; recusa se já houver dado local."""
    man = json.loads((DESTINO / "manifesto.json").read_text(encoding="utf-8"))
    for arq, sha in man["arquivos"].items():
        if pacotes.sha256(DESTINO / arq) != sha:
            raise SystemExit(f"{arq}: SHA-256 diferente do manifesto")
    bi = arquivo_bi()
    ocupados = [p for p in (SILVER, bi) if p.exists() and (p.is_file() or any(p.iterdir()))]
    if ocupados:
        raise SystemExit("Já há dados locais (nada foi instalado): " + ", ".join(p.relative_to(RAIZ).as_posix() for p in ocupados))
    SILVER.mkdir(parents=True, exist_ok=True)
    for p in sorted((DESTINO / "silver").glob("*.parquet")):
        shutil.copy2(p, SILVER / p.name)
    origem = DESTINO / bi.relative_to(RAIZ / "data")
    bi.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(origem.with_name(bi.name + ".gz"), "rb") as e, open(bi, "wb") as s:
        shutil.copyfileobj(e, s)
    shutil.copy2(origem.with_name(bi.name + ".meta.json"), bi.with_name(bi.name + ".meta.json"))
    print(f"instalados: {len(list(SILVER.glob('*.parquet')))} tabelas em data/silver/ e {bi.relative_to(RAIZ).as_posix()}. "
          "Agora: uv run pipeline.py --a-partir-de silver")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instalar", action="store_true", help="instala data/completo/ em data/ (quem clonou)")
    instalar() if ap.parse_args().instalar else exportar()
