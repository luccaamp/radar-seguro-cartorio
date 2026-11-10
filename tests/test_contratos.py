"""Contratos de total de controle da arrecadação por UF (F2, D-024; Fase 3). Banco SINTÉTICO em memória."""
from pathlib import Path

import duckdb
import pytest
import yaml

from src import estados_config
from src.quality.contratos import controle_arrecadacao, saltos_arrecadacao

CONFIG = Path(__file__).resolve().parents[1] / "config"


def controle_arrecadacao_mg(con):
    return controle_arrecadacao(con, ["MG"])


def _banco(fator: float, uf: str = "MG") -> duckdb.DuckDBPyConnection:
    tot = estados_config.controle_arrecadacao("MG")["silver"]["totais"]
    con = duckdb.connect()
    con.execute("CREATE SCHEMA silver")
    con.execute(f"CREATE TABLE silver.serventia AS SELECT 'x' cns, '{uf}' uf, 'Ativo' status")
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


def test_texto_das_checagens_de_mg_nao_mudou():
    """Fase 3, bloco 1: o resultado com MG é idêntico ao de antes (os nomes vão para qualidade.checagens e o painel)."""
    nomes = [x.checagem for x in controle_arrecadacao_mg(_banco(1.0))]
    assert nomes == ["total MG 2025-1 × controle do silver (queda ≤ 0,5%)",
                     "total MG 2025-2 × controle do silver (queda ≤ 0,5%)",
                     "total MG 2025-1 × BI do CNJ (±1,0%)", "total MG 2025-2 × BI do CNJ (±3,0%)"]


def test_uf_sem_totais_de_controle_vira_aviso(monkeypatch):
    """UF SINTÉTICA 'ZZ' com serventias no silver e sem controle_arrecadacao: um aviso, nenhum erro."""
    con = _banco(1.0, "ZZ")
    monkeypatch.setattr(estados_config, "controle_arrecadacao", lambda uf: None)
    c = controle_arrecadacao(con, ["ZZ"])
    assert [(x.severidade, x.violacoes) for x in c] == [("aviso", 1)]
    assert "ZZ" in c[0].detalhe


def test_uf_sem_serventias_no_silver_nao_gera_checagem():
    assert controle_arrecadacao(_banco(1.0, "MG"), ["SP"]) == []


def test_salto_grosseiro_e_aviso_so_no_ano_de_enquadramento():
    """Regra do salto (D-046), série SINTÉTICA: 'a' salta 10× em 2025-1 (conta); 'b' salta em 2024-2 (fora do ano);
    'c' fica 9× acima (abaixo do corte); o zero de 'a' em 2024-1 não entra na mediana; 'd' está inativa."""
    ano = yaml.safe_load((CONFIG / "escopo.yaml").read_text(encoding="utf-8"))["ano_enquadramento"]
    assert ano == 2025
    con = duckdb.connect()
    con.execute("CREATE SCHEMA silver")
    con.execute("CREATE TABLE silver.serventia AS SELECT * FROM (VALUES ('a', 'Ativo'), ('b', 'Ativo'), ('c', 'Ativo'), "
                "('d', 'Inativo')) t(cns, status)")
    con.execute("CREATE TABLE silver.serventia_arrecadacao (cns VARCHAR, ano INT, semestre DOUBLE, versao INT, arrecadacao DOUBLE)")
    periodos = [(2022, 2), (2023, 1), (2023, 2), (2024, 1), (2024, 2), (2025, 1), (2025, 2)]
    series = {"a": [100, 100, 100, 0, 100, 1000, 100], "b": [100, 100, 100, 100, 1000, 100, 100],
              "c": [100, 100, 100, 100, 100, 900, 100], "d": [100, 100, 100, 100, 100, 5000, 100]}
    for cns, valores in series.items():
        for (a, s), v in zip(periodos, valores):
            con.execute("INSERT INTO silver.serventia_arrecadacao VALUES (?, ?, ?, 1, ?)", [cns, a, float(s), v])
    c = saltos_arrecadacao(con)
    assert c.severidade == "aviso" and c.violacoes == 1
    assert "1 semestres em 1 serventias" in c.detalhe and "D-046" in c.detalhe
