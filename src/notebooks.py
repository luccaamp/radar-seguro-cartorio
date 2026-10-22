"""Acesso aos dados para notebooks (notebooks/README.md): SOMENTE LEITURA.

Notebook lê, não escreve. Com o banco local (data/radar.duckdb), abre em modo somente leitura; sem ele, usa o banco
de demonstração montado a partir do conjunto público (data/publico, D-029), também somente leitura. Nunca grava em
bronze, silver ou gold.

    from src.notebooks import conectar, ler
    con = conectar()
    df = ler("SELECT * FROM gold.fato_mercado_uf")

Todos os notebooks vão para o git com as saídas (D-038); podem ler qualquer tabela, inclusive `interno_*`, e mostrar
resultados por cartório, sem nome nem CPF de pessoa física.
"""
from pathlib import Path

import duckdb
import pandas as pd

from src import publico

RAIZ = Path(__file__).resolve().parents[1]
BANCO = RAIZ / "data" / "radar.duckdb"


def conectar(banco: Path | None = None) -> duckdb.DuckDBPyConnection:
    """Conexão SOMENTE LEITURA: o banco completo, se existir; senão, o de demonstração (conjunto público)."""
    caminho = Path(banco) if banco else (BANCO if BANCO.exists() else publico.banco_demonstracao())
    return duckdb.connect(str(caminho), read_only=True)


def ler(sql: str, params: list | None = None, con: duckdb.DuckDBPyConnection | None = None) -> pd.DataFrame:
    """Consulta numa conexão somente leitura (abre e fecha uma, se não for dada)."""
    if con is not None:
        return con.execute(sql, params or []).df()
    with conectar() as c:
        return c.execute(sql, params or []).df()
