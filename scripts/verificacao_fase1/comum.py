"""Base dos scripts de conferência da Fase 1 (verificacao_final_fase1.md). SÓ LEITURA.

- O CSV do BI é lido do bronze por um DuckDB em memória; nada é gravado no banco do projeto.
- O silver e o gold são lidos das cópias em Parquet (data/silver, data/gold), que o pipeline grava junto com o banco.
- Os scripts imprimem só agregados (contagens e somas), nunca linhas brutas nem nomes de cartório.
"""
import json
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[2]
CSV_BI = RAIZ / "data/bronze/cnj_bi_painel/2026-10-18/atos_arrecadacoes_custeio_e_repasse.csv"
SILVER = RAIZ / "data/silver"
GOLD = RAIZ / "data/gold"


def _num(col: str) -> str:
    return f"TRY_CAST(replace(replace(nullif(trim({col}), '-'), '.', ''), ',', '.') AS DOUBLE)"


def conectar() -> duckdb.DuckDBPyConnection:
    """DuckDB em memória com as views: bi (CSV tipado), cad_br (cadastro Justiça Aberta, todas as UFs) e o silver/gold."""
    con = duckdb.connect()
    con.execute(f"""
        CREATE VIEW bi_bruto AS SELECT * FROM read_csv('{CSV_BI.as_posix()}', delim='\t', header=true,
            all_varchar=true, quote='', escape='')""")
    cols = [r[0] for r in con.execute("DESCRIBE bi_bruto").fetchall()]
    c = dict(zip(["cns", "ini", "fim", "custeio", "atrib", "atos", "arrec", "repasse"], cols))
    con.execute(f"""
        CREATE VIEW bi AS SELECT
            regexp_replace("{c['cns']}", '[^0-9]', '', 'g') AS cns,
            TRY_STRPTIME(nullif(trim("{c['ini']}"), '-'), '%d/%m/%Y')::DATE AS ini,
            TRY_STRPTIME(nullif(trim("{c['fim']}"), '-'), '%d/%m/%Y')::DATE AS fim,
            {_num(f'"{c["custeio"]}"')} AS custeio,
            nullif(trim("{c['atrib']}"), '-') AS atrib,
            {_num(f'"{c["atos"]}"')} AS atos,
            {_num(f'"{c["arrec"]}"')} AS arrec,
            {_num(f'"{c["repasse"]}"')} AS repasse
        FROM bi_bruto""")
    con.execute("""CREATE VIEW bi_p AS SELECT *, year(ini) AS ano,
                   CASE WHEN month(ini) = 1 AND month(fim) = 6 THEN 1 WHEN month(ini) = 7 AND month(fim) = 12 THEN 2 END AS sem
                   FROM bi""")
    # cadastro Justiça Aberta de todas as UFs (só cns, uf, status, situação: nada pessoal)
    linhas = []
    for arq in sorted((RAIZ / "data/bronze/cnj_justica_aberta/2026-10-17").glob("serventias_??.json")):
        for s in json.loads(arq.read_text(encoding="utf-8"))["data"]:
            sj = s.get("situacao_juridica_cartorio")
            linhas.append((s["cns"], s["uf"], s["status"], sj.get("descricao") if isinstance(sj, dict) else None))
    con.execute("CREATE TABLE cad_br (cns VARCHAR, uf VARCHAR, status VARCHAR, situacao VARCHAR)")
    con.executemany("INSERT INTO cad_br VALUES (?, ?, ?, ?)", linhas)
    for pasta, esquema in ((SILVER, "silver"), (GOLD, "gold")):
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {esquema}")
        for p in pasta.glob("*.parquet"):
            con.execute(f"CREATE VIEW {esquema}.{p.stem} AS SELECT * FROM read_parquet('{p.as_posix()}')")
    return con


def mostrar(con, titulo: str, sql: str, max_linhas: int = 12) -> None:
    print(f"\n## {titulo}")
    df = con.sql(sql).df()
    print(df.head(max_linhas).to_string(index=False))
