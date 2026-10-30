"""Silver e gold completo versionados em data/completo (D-050): integridade, sem dado pessoal e coerência com o gold local.

A integridade e as colunas rodam em qualquer clone; a procura de nomes do cadastro precisa do bronze local e a
coerência, do banco local.
"""
import gzip
import hashlib
import json
from pathlib import Path

import duckdb
import pytest

from apoio_painel import BANCO_REAL, RAIZ
from src import publico

PASTA = RAIZ / "data" / "completo"
MAN = json.loads((PASTA / "manifesto.json").read_text(encoding="utf-8"))
BRONZE = RAIZ / "data" / "bronze"


def montar(destino: Path) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(destino))
    for camada in ("silver", "gold"):
        con.execute(f"CREATE SCHEMA {camada}")
        for p in sorted((PASTA / camada).glob("*.parquet")):
            con.execute(f"CREATE TABLE {camada}.{p.stem} AS SELECT * FROM read_parquet('{p.as_posix()}')")
    return con


def test_manifesto_e_arquivos_batem():
    no_disco = {p.relative_to(PASTA).as_posix() for p in PASTA.rglob("*") if p.is_file() and p.name != "manifesto.json"}
    assert set(MAN["arquivos"]) == no_disco
    for arq, sha in MAN["arquivos"].items():
        assert publico.sha256_arquivo(PASTA / arq) == sha, arq


def test_csv_do_bi_descomprimido_igual_ao_exportado():
    """O CSV do BI em gzip volta com o SHA-256 do .meta.json (o arquivo da exportação manual do autor)."""
    gz = next(PASTA.glob("bronze/cnj_bi_painel/*/*.csv.gz"))
    meta = json.loads(gz.with_name(gz.name.removesuffix(".gz") + ".meta.json").read_text(encoding="utf-8"))
    with gzip.open(gz, "rb") as f:
        assert hashlib.sha256(f.read()).hexdigest() == meta["sha256"]


def test_silver_sem_as_colunas_da_d031():
    remover = publico.CONFIG["silver_publico_remover"]
    for tabela, colunas in remover.items():
        p = PASTA / "silver" / f"{tabela}.parquet"
        nomes = {c for (c,) in duckdb.sql(f"SELECT name FROM parquet_schema('{p.as_posix()}')").fetchall()}
        assert not nomes & set(colunas), tabela


def test_sem_dado_pessoal(tmp_path):
    with montar(tmp_path / "completo.duckdb") as con:
        nomes = publico.nomes_do_cadastro(con, BRONZE) if BRONZE.exists() else None
        assert publico.checar_sem_dado_pessoal(con, nomes) == []


@pytest.mark.skipif(not BANCO_REAL.exists(), reason="sem banco local: nada a comparar")
def test_gold_completo_coerente_com_o_gold_local(tmp_path):
    """Se o banco local existir, data/completo/gold tem de ter o mesmo conteúdo (hash) que o gold dele."""
    with duckdb.connect(str(BANCO_REAL), read_only=True) as real, montar(tmp_path / "completo.duckdb") as copia:
        tabelas = [t for (t,) in real.execute("SELECT table_name FROM information_schema.tables "
                                              "WHERE table_schema = 'gold' ORDER BY 1").fetchall()]
        assert {p.stem for p in (PASTA / "gold").glob("*.parquet")} == set(tabelas)
        # carimbos de execução fora do hash, como no conjunto público (config/publico.yaml, sem_hash)
        sem_hash = {t: (publico.tabelas().get(f"gold.{t}") or {}).get("sem_hash") for t in tabelas}
        diferentes = [t for t in tabelas if publico.hash_conteudo(real, f"gold.{t}", sem_hash[t])
                      != publico.hash_conteudo(copia, f"gold.{t}", sem_hash[t])]
    assert not diferentes, f"data/completo desatualizado: rode `uv run python scripts/exportar_completo.py` ({diferentes[:5]})"
