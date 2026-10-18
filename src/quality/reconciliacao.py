"""Reconciliações entre fontes e contratos do gold (SPEC §4). Divergência entre fontes = aviso; violação de contrato = erro.

Saídas: qualidade.reconciliacoes (resumo), qualidade.rec_municipio (CNJ × CNPJ × RAIS por município, para revisão).
"""
import duckdb
import pandas as pd
import yaml

from src.quality.contratos import Checagem, chave_unica, condicao, sem_dados_pessoais
from src.transform.silver import CONFIG


def _linha(checagem, fonte_a, valor_a, fonte_b, valor_b, tolerancia, tipo="diferenca", detalhe=""):
    if tipo == "diferenca":
        dif = (valor_a - valor_b) / valor_b if valor_b else None
        ok = dif is not None and abs(dif) <= tolerancia
    else:  # mínimo: valor_a precisa ser >= tolerancia
        dif = valor_a
        ok = valor_a >= tolerancia
    return {"checagem": checagem, "fonte_a": fonte_a, "valor_a": float(valor_a), "fonte_b": fonte_b,
            "valor_b": None if valor_b is None else float(valor_b), "indicador": dif, "tolerancia": tolerancia,
            "status": "ok" if ok else "aviso", "detalhe": detalhe}


def reconciliar(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    tol = yaml.safe_load((CONFIG / "qualidade.yaml").read_text(encoding="utf-8"))["tolerancias"]
    rec_mun = con.sql("""
        WITH cnj AS (SELECT s.cod_ibge, count(*) n_cnj, sum(k.clt) clt_cnj
                     FROM silver.serventia s LEFT JOIN silver.serventia_colaboradores k USING (cns)
                     WHERE s.status = 'Ativo' GROUP BY 1),
             cnpj AS (SELECT cod_ibge, count(*) n_cnpj FROM silver.cnpj_estabelecimento
                      WHERE situacao = 'ativa' AND cnae_principal GROUP BY 1),
             rais AS (SELECT cod_ibge, count(*) vinc_rais FROM silver.rais_vinculo WHERE ativo_31_12 GROUP BY 1)
        SELECT m.cod_ibge, m.nome AS municipio, coalesce(n_cnj, 0) n_cnj, coalesce(n_cnpj, 0) n_cnpj,
               coalesce(clt_cnj, 0) clt_cnj, coalesce(vinc_rais, 0) vinc_rais
        FROM silver.municipio_ibge m LEFT JOIN cnj USING (cod_ibge) LEFT JOIN cnpj USING (cod_ibge)
        LEFT JOIN rais USING (cod_ibge)""").df()
    rec_mun["dif_serventias"] = rec_mun["n_cnpj"] - rec_mun["n_cnj"]
    rec_mun["dif_empregados"] = rec_mun["vinc_rais"] - rec_mun["clt_cnj"]
    con.register("_df", rec_mun)
    con.execute("CREATE SCHEMA IF NOT EXISTS qualidade")
    con.execute("CREATE OR REPLACE TABLE qualidade.rec_municipio AS SELECT * FROM _df")
    con.unregister("_df")

    t = rec_mun.sum(numeric_only=True)
    corr = rec_mun[(rec_mun.clt_cnj > 0) | (rec_mun.vinc_rais > 0)][["clt_cnj", "vinc_rais"]].corr().iloc[0, 1]
    n_iguais = int((rec_mun.n_cnj == rec_mun.n_cnpj).sum())
    origem = con.sql("SELECT origem_receita, count(*) n FROM gold.interno_dim_serventia GROUP BY 1").df()
    validas = origem.loc[origem.origem_receita.isin(["media_2_semestres", "um_semestre"]), "n"].sum() / origem.n.sum()
    colab = con.sql("SELECT avg(informado::INT) FROM silver.serventia_colaboradores").fetchone()[0]
    dist = con.sql("""SELECT sum(n_vinculos_rais) FILTER (WHERE origem_distribuicao = 'municipio') / sum(n_vinculos_rais),
                             count(*) FILTER (WHERE origem_distribuicao = 'municipio'), count(*)
                      FROM gold.fato_passivo_municipio WHERE nivel = 'base'""").fetchone()
    linhas = [
        _linha("serventias ativas: CNPJ × CNJ (MG)", "CNPJ ativos, CNAE principal 6912-5/00", t.n_cnpj, "CNJ ativas",
               t.n_cnj, tol["serventias_cnj_x_cnpj_pct"],
               detalhe=f"{n_iguais} de {len(rec_mun)} municípios com a mesma contagem; o CNPJ guarda CNPJs não baixados"),
        _linha("empregados: RAIS × CNJ (MG)", "RAIS vínculos ativos em 31/12/2025", t.vinc_rais, "CNJ colaboradores CLT",
               t.clt_cnj, tol["empregados_cnj_x_rais_pct"]),
        _linha("empregados por município: correlação RAIS × CNJ", "correlação", corr, None, None,
               tol["correlacao_minima_municipio"], "minimo"),
        _linha("cobertura da arrecadação 2025 (receita de referência válida)", "fração das ativas", validas, None, None,
               tol["cobertura_arrecadacao_min"], "minimo",
               detalhe="; ".join(f"{r.origem_receita}: {r.n}" for r in origem.itertuples())),
        _linha("cobertura dos colaboradores declarados", "fração das ativas", colab, None, None,
               tol["cobertura_colaboradores_min"], "minimo"),
        _linha("vínculos com distribuição do próprio município", "fração dos vínculos", dist[0], None, None,
               tol["vinculos_com_distribuicao_municipal_min"], "minimo",
               detalhe=f"{dist[1]} de {dist[2]} municípios com serventia usam a distribuição própria; os demais, a de MG"),
    ]
    df = pd.DataFrame(linhas)
    con.register("_df", df)
    con.execute("CREATE OR REPLACE TABLE qualidade.reconciliacoes AS SELECT * FROM _df")
    con.unregister("_df")
    return df


def contratos_gold(con: duckdb.DuckDBPyConnection) -> list[Checagem]:
    g = "gold"
    return [
        chave_unica(con, f"{g}.interno_serventia", "cns, nivel, regra_classe"),
        condicao(con, f"{g}.interno_serventia", "universo nunca contém interino",
                 "situacao_juridica = 'VAGO' AND peso_universo > 0"),
        condicao(con, f"{g}.interno_serventia", "peso do universo entre 0 e 1", "peso_universo < 0 OR peso_universo > 1"),
        condicao(con, f"{g}.interno_serventia", "passivo não negativo", "passivo < 0"),
        condicao(con, f"{g}.interno_serventia", "déficit não maior que o passivo", "valor_descoberto > passivo + 1e-6"),
        condicao(con, f"({g}.interno_serventia JOIN {g}.fato_passivo_municipio USING (cod_ibge, nivel))",
                 "rateio por_empregados_cnj = CLT × passivo médio", "abs(passivo - coalesce(clt, 0) * "
                 f"{g}.fato_passivo_municipio.passivo_medio_vinculo) > 0.01"),
        condicao(con, f"{g}.fato_mercado_municipio_publico", "exibição sem município com menos serventias que o limiar",
                 f"NOT agregado_lgpd AND n_serventias < (SELECT max(limiar_lgpd) FROM {g}.execucao)"),
        condicao(con, f"{g}.fato_mercado_uf", "mercado ≥ seguradora hipotética",
                 "mercado_premio_emitido < seguradora_premio_emitido"),
        condicao(con, f"{g}.fato_mercado_uf", "suspende_8_17 zera a demanda",
                 "cenario_stf = 'suspende_8_17' AND mercado_importancia_segurada <> 0"),
        condicao(con, f"{g}.fato_mercado_uf", "faixa ordenada (min ≤ base ≤ max) no déficit",
                 f"nivel = 'base' AND (valor_descoberto < (SELECT valor_descoberto FROM {g}.fato_mercado_uf x WHERE "
                 "x.nivel = 'min' AND x.regra_classe = fato_mercado_uf.regra_classe AND x.cenario_stf = "
                 "fato_mercado_uf.cenario_stf) OR valor_descoberto > (SELECT valor_descoberto FROM "
                 f"{g}.fato_mercado_uf x WHERE x.nivel = 'max' AND x.regra_classe = fato_mercado_uf.regra_classe "
                 "AND x.cenario_stf = fato_mercado_uf.cenario_stf))"),
    ] + sem_dados_pessoais(con, g)
