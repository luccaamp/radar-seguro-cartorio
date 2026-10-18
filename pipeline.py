"""Orquestrador único do projeto.

Uso:
  uv run pipeline.py            # do zero a partir dos snapshots do bronze (silver -> qualidade), sem internet
  uv run pipeline.py silver     # só bronze -> silver
  uv run pipeline.py quality    # só os contratos
  uv run pipeline.py ingest     # coleta (precisa de internet; idempotente, só baixa o que falta)
"""
import sys

import duckdb
import yaml

from src.quality import contratos
from src.transform import silver
from src.transform.silver import BANCO, CONFIG


def etapa_ingest() -> None:
    from src.ingest import cnj_arrecadacoes, cnj_complementares, cnj_serventias, cnpj, ibge, rais, susep
    esc = yaml.safe_load((CONFIG / "escopo.yaml").read_text(encoding="utf-8"))
    for uf in esc["ufs"]:
        cnj_serventias.coletar(uf)
        cnj_complementares.coletar(uf)
        cnj_arrecadacoes.coletar(uf)
        ibge.coletar(uf)
        rais.filtrar(rais.baixar(esc["snapshots"]["rais"], rais.PACOTE_UF[uf]), uf)
    cnpj.filtrar(cnpj.baixar(esc["snapshots"]["cnpj"]))
    susep.filtrar(susep.baixar())
    print("Atenção: atualize config/escopo.yaml se quiser que o pipeline use os snapshots novos.")


def etapa_silver(con) -> None:
    for tabela, n in silver.construir(con).items():
        print(f"  silver.{tabela}: {n:,} linhas")


def etapa_quality(con) -> None:
    df = contratos.gravar(con, contratos.contratos_silver(con), "silver")
    falhas = df[(df.violacoes > 0)]
    print(f"  {len(df)} checagens | {int((df.violacoes == 0).sum())} ok | "
          f"{int(((df.violacoes > 0) & (df.severidade == 'aviso')).sum())} avisos | "
          f"{int(((df.violacoes > 0) & (df.severidade == 'erro')).sum())} erros")
    for _, r in falhas.iterrows():
        print(f"  [{r.severidade.upper()}] {r.tabela}: {r.checagem} -> {r.violacoes:,} {r.detalhe}")
    if ((df.violacoes > 0) & (df.severidade == "erro")).any():
        raise SystemExit("Pipeline interrompido: contrato violado (ver acima).")


def main(etapa: str = "all") -> None:
    if etapa == "ingest":
        etapa_ingest()
        return
    with duckdb.connect(str(BANCO)) as con:
        if etapa in ("all", "silver"):
            print("bronze -> silver")
            etapa_silver(con)
        if etapa in ("all", "silver", "quality"):
            print("contratos do silver")
            etapa_quality(con)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
