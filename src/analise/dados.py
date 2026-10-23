"""Leitura das tabelas para a mineração, numa conexão somente leitura (src/notebooks.py).

Cada função devolve um DataFrame pronto para análise, uma linha por unidade (serventia, período ou município).
"""
from pathlib import Path

import duckdb
import pandas as pd
import yaml

from src.analise import RAIZ

ATRIBUICOES = ["notas", "rcpn", "ri", "rtd", "rcpj", "protesto"]
NOMES_ATRIBUICOES = {"notas": "Notas", "rcpn": "Registro civil (RCPN)", "ri": "Registro de imóveis (RI)",
                     "rtd": "Títulos e documentos (RTD)", "rcpj": "Pessoas jurídicas (RCPJ)", "protesto": "Protesto"}
SITUACOES = {"PROVIDO": "provida", "VAGO": "vaga"}   # o resto (intervenção, conversão em diligência) = "outras"


def serventias(con: duckdb.DuckDBPyConnection, nivel: str = "base", regra_classe: str = "v2") -> pd.DataFrame:
    """As serventias ativas com o resultado do modelo (gold.interno_serventia) num nível e numa regra de classe, mais
    o número de atribuições, o município e as regiões do IBGE e os colaboradores declarados ao CNJ. Uma serventia sem
    município casado continua na tabela, com o município vazio (LEFT JOIN)."""
    df = con.execute("""
        SELECT s.*, v.n_atribuicoes, v.data_situacao, m.nome AS municipio, m.regiao_imediata, m.regiao_intermediaria,
               m.populacao, c.informado AS colaboradores_informados, c.estatutarios, c.terceirizados
        FROM gold.interno_serventia s
        JOIN silver.serventia v USING (cns)
        LEFT JOIN silver.municipio_ibge m ON m.cod_ibge = s.cod_ibge
        LEFT JOIN silver.serventia_colaboradores c USING (cns)
        WHERE s.nivel = ? AND s.regra_classe = ?
        ORDER BY s.cns""", [nivel, regra_classe]).df()
    df["situacao"] = df["situacao_juridica"].map(SITUACOES).fillna("outras")
    return df


def serie_arrecadacao(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Arrecadação semestral das serventias ativas, como o pipeline a lê (versão 1 de cada período; o conflito entre
    versões fica marcado em `conflito_fonte`, D-014). Os anos de 2005 e 2006 vêm anuais na fonte e ficam fora."""
    df = con.execute("""
        SELECT cns, ano, semestre::INT AS semestre, informado, arrecadacao, conflito_fonte
        FROM silver.serventia_arrecadacao
        WHERE versao = 1 AND semestre IS NOT NULL
          AND cns IN (SELECT cns FROM silver.serventia WHERE status = 'Ativo')
        ORDER BY cns, ano, semestre""").df()
    df["periodo"] = df["ano"].astype(str) + "-" + df["semestre"].astype(str)
    return df


def arquivo_bi() -> Path:
    """O CSV do BI do CNJ no bronze (config/qualidade.yaml, controle_arrecadacao_mg.bi.arquivo)."""
    cfg = yaml.safe_load((RAIZ / "config" / "qualidade.yaml").read_text(encoding="utf-8"))
    return RAIZ / cfg["controle_arrecadacao_mg"]["bi"]["arquivo"]


def arrecadacao_bi(con: duckdb.DuckDBPyConnection, arquivo: Path | None = None) -> pd.DataFrame:
    """Arrecadação e repasse por serventia e semestre no BI do CNJ (exportação manual; só conferência).

    O arquivo é nacional, com CNS no formato 00.005-9, decimal com vírgula e '-' para vazio. A partir do 2º semestre
    de 2025 o BI separa as linhas por atribuição: aqui elas são somadas por serventia e período."""
    caminho = (Path(arquivo) if arquivo else arquivo_bi()).as_posix()
    num = "TRY_CAST(replace(replace(nullif({c}, '-'), '.', ''), ',', '.') AS DOUBLE)"
    df = con.execute(f"""
        WITH b AS (
            SELECT regexp_replace("CNS", '[^0-9]', '', 'g') AS cns,
                   try_strptime("Dat. início do período", '%d/%m/%Y')::DATE AS inicio,
                   try_strptime("Dat. final período", '%d/%m/%Y')::DATE AS fim,
                   {num.format(c='"Valor arrecadação"')} AS arrecadacao,
                   {num.format(c='"Valor repasse"')} AS repasse
            FROM read_csv('{caminho}', delim = '\t', header = true, all_varchar = true))
        SELECT cns, year(inicio) AS ano, CASE WHEN month(inicio) <= 6 THEN 1 ELSE 2 END AS semestre,
               sum(arrecadacao) AS arrecadacao_bi, sum(repasse) AS repasse_bi
        FROM b
        WHERE inicio IS NOT NULL AND datediff('month', inicio, fim) < 6    -- só semestres (2005 e 2006 são anuais)
        GROUP BY ALL""").df()
    return df


def reconciliacao_municipio(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Serventias (CNJ × CNPJ) e empregados (CNJ × RAIS) por município, como o pipeline reconcilia."""
    return con.execute("SELECT * FROM qualidade.interno_rec_municipio ORDER BY cod_ibge").df()


def indice_preco(con: duckdb.DuckDBPyConnection, indice: str = "IPCA") -> pd.DataFrame:
    """Número-índice mensal do IBGE (silver.indice_preco; no banco, desde jan/2019)."""
    return con.execute("SELECT ano_mes, numero_indice FROM silver.indice_preco WHERE indice = ? ORDER BY ano_mes",
                       [indice]).df()


def malha(con: duckdb.DuckDBPyConnection):
    """Malha municipal do IBGE (2022) como GeoDataFrame, com cod_ibge."""
    import json

    import geopandas as gpd
    linhas = con.execute("SELECT cod_ibge, feature_json FROM silver.malha_municipio ORDER BY ordem").fetchall()
    gdf = gpd.GeoDataFrame.from_features([json.loads(f) for _, f in linhas], crs="EPSG:4674")
    gdf["cod_ibge"] = [c for c, _ in linhas]
    return gdf[["cod_ibge", "geometry"]]


def vinculos_rais(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Vínculos da RAIS dos cartórios de MG (silver.rais_vinculo)."""
    return con.execute("SELECT * FROM silver.rais_vinculo").df()
