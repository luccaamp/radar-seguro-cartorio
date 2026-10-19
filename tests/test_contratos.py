"""Contratos de total de controle da arrecadação de MG (F2, D-024). Banco SINTÉTICO em memória."""
from pathlib import Path

import duckdb
import pytest
import yaml

from src.quality.contratos import controle_arrecadacao_mg

CONFIG = Path(__file__).resolve().parents[1] / "config"


def _banco(fator: float) -> duckdb.DuckDBPyConnection:
    tot = yaml.safe_load((CONFIG / "qualidade.yaml").read_text(encoding="utf-8"))["controle_arrecadacao_mg"]["silver"]["totais"]
    con = duckdb.connect()
    con.execute("CREATE SCHEMA silver")
    con.execute("CREATE TABLE silver.serventia AS SELECT 'x' cns, 'MG' uf, 'Ativo' status")
    con.execute("CREATE TABLE silver.serventia_arrecadacao (cns VARCHAR, ano INT, semestre DOUBLE, versao INT, arrecadacao DOUBLE)")
    for periodo, v in tot.items():
        ano, sem = periodo.split("-")
        con.execute("INSERT INTO silver.serventia_arrecadacao VALUES ('x', ?, ?, 1, ?)", [int(ano), float(sem), v * fator])
    return con


@pytest.mark.parametrize("fator, erros", [(1.0, 0), (0.996, 0), (0.99, 2)])
def test_controle_do_silver(fator, erros):
    c = controle_arrecadacao_mg(_banco(fator))
    assert sum(x.violacoes for x in c if x.severidade == "erro") == erros


def test_conferencia_com_o_bi_e_aviso():
    c = controle_arrecadacao_mg(_banco(1.0))
    bi = [x for x in c if "BI do CNJ" in x.checagem]
    assert len(bi) == 2 and all(x.severidade == "aviso" for x in bi)
    assert all(x.violacoes == 0 for x in bi)   # +0,24% (tol. 1%) e +2,16% (tol. 3%)
