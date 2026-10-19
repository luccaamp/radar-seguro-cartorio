"""Reconciliações entre fontes e contratos do gold (SPEC §4). Divergência entre fontes = aviso; violação de contrato = erro.

Saídas: qualidade.reconciliacoes (resumo); qualidade.interno_rec_municipio (CNJ × CNPJ × RAIS por município, uso
interno) e qualidade.rec_municipio (versão pública: municípios com menos de 3 serventias agregados pela região imediata, D1).
"""
import duckdb
import numpy as np
import pandas as pd
import yaml

from src.quality.contratos import Checagem, chave_unica, condicao, sem_dados_pessoais
from src.transform.silver import CONFIG


def _linha(checagem, fonte_a, valor_a, fonte_b, valor_b, tolerancia, tipo="diferenca", detalhe=""):
    if tipo == "diferenca":
        dif = (valor_a - valor_b) / valor_b if valor_b else None
        ok = dif is not None and abs(dif) <= tolerancia
    elif tipo == "maximo":  # valor_a precisa ser <= tolerancia
        dif = valor_a
        ok = valor_a <= tolerancia
    else:  # mínimo: valor_a precisa ser >= tolerancia
        dif = valor_a
        ok = valor_a >= tolerancia
    return {"checagem": checagem, "fonte_a": fonte_a, "valor_a": float(valor_a), "fonte_b": fonte_b,
            "valor_b": None if valor_b is None else float(valor_b), "indicador": dif, "tolerancia": tolerancia,
            "status": "ok" if ok else "aviso", "detalhe": detalhe}


def rec_municipio_publico(rec: pd.DataFrame, limiar: int) -> pd.DataFrame:
    """D1: municípios com pelo menos `limiar` serventias no CNJ aparecem com o nome; os demais são somados por região
    imediata do IBGE numa linha "Região imediata de X (k municípios com menos de N serventias)"."""
    cols = ["n_cnj", "n_cnpj", "clt_cnj", "vinc_rais"]
    grandes = rec[rec["n_cnj"] >= limiar].assign(area=lambda d: d["municipio"], area_completa=lambda d: d["municipio"],
                                                 tipo="municipio", n_municipios=1)
    peq = (rec[rec["n_cnj"] < limiar].groupby("regiao_imediata")
           .agg(**{c: (c, "sum") for c in cols}, n_municipios=("cod_ibge", "size")).reset_index())
    # rótulo curto para a tabela (1.5) e o nome completo para o texto ao passar o mouse
    peq["area"] = [f"RI {r} ({n} mun.)" for r, n in zip(peq["regiao_imediata"], peq["n_municipios"])]
    peq["area_completa"] = [f"Região imediata de {r} ({n} municípios com menos de {limiar} serventias, somados)"
                            for r, n in zip(peq["regiao_imediata"], peq["n_municipios"])]
    peq["tipo"] = "regiao_agregada"
    campos = ["area", "area_completa", "tipo", "regiao_imediata", "n_municipios"] + cols
    out = pd.concat([grandes[campos], peq[campos]], ignore_index=True)
    out["dif_serventias"] = out["n_cnpj"] - out["n_cnj"]
    out["dif_empregados"] = out["vinc_rais"] - out["clt_cnj"]
    return out


def reconciliar(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    tol = yaml.safe_load((CONFIG / "qualidade.yaml").read_text(encoding="utf-8"))["tolerancias"]
    rec_mun = con.sql("""
        WITH cnj AS (SELECT s.cod_ibge, count(*) n_cnj, sum(k.clt) clt_cnj
                     FROM silver.serventia s LEFT JOIN silver.serventia_colaboradores k USING (cns)
                     WHERE s.status = 'Ativo' GROUP BY 1),
             cnpj AS (SELECT cod_ibge, count(*) n_cnpj FROM silver.cnpj_estabelecimento
                      WHERE situacao = 'ativa' AND cnae_principal GROUP BY 1),
             rais AS (SELECT cod_ibge, count(*) vinc_rais FROM silver.rais_vinculo WHERE ativo_31_12 GROUP BY 1)
        SELECT m.cod_ibge, m.nome AS municipio, m.regiao_imediata, coalesce(n_cnj, 0) n_cnj, coalesce(n_cnpj, 0) n_cnpj,
               coalesce(clt_cnj, 0) clt_cnj, coalesce(vinc_rais, 0) vinc_rais
        FROM silver.municipio_ibge m LEFT JOIN cnj USING (cod_ibge) LEFT JOIN cnpj USING (cod_ibge)
        LEFT JOIN rais USING (cod_ibge)""").df()
    rec_mun["dif_serventias"] = rec_mun["n_cnpj"] - rec_mun["n_cnj"]
    rec_mun["dif_empregados"] = rec_mun["vinc_rais"] - rec_mun["clt_cnj"]
    con.execute("CREATE SCHEMA IF NOT EXISTS qualidade")
    limiar = int(con.execute("SELECT max(limiar_lgpd) FROM gold.execucao").fetchone()[0])
    for nome, df in (("interno_rec_municipio", rec_mun), ("rec_municipio", rec_municipio_publico(rec_mun, limiar))):
        con.register("_df", df)
        con.execute(f"CREATE OR REPLACE TABLE qualidade.{nome} AS SELECT * FROM _df")
        con.unregister("_df")

    t = rec_mun.sum(numeric_only=True)
    corr = rec_mun[(rec_mun.clt_cnj > 0) | (rec_mun.vinc_rais > 0)][["clt_cnj", "vinc_rais"]].corr().iloc[0, 1]
    # C1: métricas por município que não são dominadas por BH
    com_dado = rec_mun[(rec_mun.clt_cnj > 0) | (rec_mun.vinc_rais > 0)]
    ambos = com_dado[(com_dado.clt_cnj > 0) & (com_dado.vinc_rais > 0)]
    corr_log = float(np.log(ambos.clt_cnj).corr(np.log(ambos.vinc_rais)))
    min_emp = tol["minimo_empregados_para_erro_pct"]
    f5 = com_dado[(com_dado.clt_cnj >= min_emp) | (com_dado.vinc_rais >= min_emp)]
    erro = ((f5.vinc_rais - f5.clt_cnj).abs() / f5.clt_cnj.where(f5.clt_cnj > 0)).fillna(np.inf)
    zero_rais = int(((com_dado.vinc_rais == 0) & (com_dado.clt_cnj > 0)).sum())
    zero_cnj = int(((com_dado.clt_cnj == 0) & (com_dado.vinc_rais > 0)).sum())
    # resumo PÚBLICO (só contagens agregadas) para o painel, que não lê tabelas interno_* (1.7)
    resumo = [("municipios_rais_zero_cnj_positivo", zero_rais, "municípios com RAIS = 0 e CNJ > 0"),
              ("municipios_cnj_zero_rais_positivo", zero_cnj, "municípios com CNJ = 0 e RAIS > 0")]
    for origem_d, n, v in con.execute("""SELECT origem_distribuicao, count(*), sum(n_vinculos_rais)
                                         FROM gold.interno_passivo_municipio WHERE nivel = 'base' GROUP BY 1""").fetchall():
        resumo += [(f"distribuicao_{origem_d}_municipios", n, f"municípios com distribuição salarial: {origem_d}"),
                   (f"distribuicao_{origem_d}_vinculos", v, f"vínculos próprios desses municípios: {origem_d}")]
    df_resumo = pd.DataFrame(resumo, columns=["chave", "valor", "descricao"])
    con.register("_df", df_resumo)
    con.execute("CREATE OR REPLACE TABLE qualidade.resumo_publico AS SELECT * FROM _df")
    con.unregister("_df")
    n_iguais = int((rec_mun.n_cnj == rec_mun.n_cnpj).sum())
    origem = con.sql("SELECT origem_receita, count(*) n FROM gold.interno_dim_serventia GROUP BY 1").df()
    validas = origem.loc[origem.origem_receita.isin(["media_2_semestres", "um_semestre"]), "n"].sum() / origem.n.sum()
    colab = con.sql("SELECT avg(informado::INT) FROM silver.serventia_colaboradores").fetchone()[0]
    dist = con.sql("""SELECT sum(n_vinculos_rais) FILTER (WHERE origem_distribuicao = 'municipio') / sum(n_vinculos_rais),
                             count(*) FILTER (WHERE origem_distribuicao = 'municipio'), count(*)
                      FROM gold.interno_passivo_municipio WHERE nivel = 'base'""").fetchone()
    linhas = [
        _linha("serventias ativas: CNPJ × CNJ (MG)", "CNPJ ativos, CNAE principal 6912-5/00", t.n_cnpj, "CNJ ativas",
               t.n_cnj, tol["serventias_cnj_x_cnpj_pct"],
               detalhe=f"{n_iguais} de {len(rec_mun)} municípios com a mesma contagem; o CNPJ guarda CNPJs não baixados"),
        _linha("empregados: RAIS × CNJ (MG)", "RAIS vínculos ativos em 31/12/2025", t.vinc_rais, "CNJ colaboradores CLT",
               t.clt_cnj, tol["empregados_cnj_x_rais_pct"]),
        _linha("empregados por município: correlação RAIS × CNJ", "correlação", corr, None, None,
               tol["correlacao_minima_municipio"], "minimo",
               detalhe="valores brutos: dominada por BH (ver as três checagens seguintes)"),
        _linha("empregados por município: correlação em log (RAIS × CNJ)", "correlação em log", corr_log, None, None,
               tol["correlacao_log_minima_municipio"], "minimo",
               detalhe=f"{len(ambos)} municípios com as duas fontes > 0; fora do log: {zero_rais} com RAIS = 0 e CNJ > 0, "
                       f"{zero_cnj} com CNJ = 0 e RAIS > 0"),
        _linha(f"empregados por município: erro percentual mediano (≥ {min_emp} empregados)", "erro mediano",
               float(np.median(erro)), None, None, tol["erro_pct_mediano_max_municipio"], "maximo",
               detalhe=f"|RAIS − CNJ| ÷ CNJ em {len(f5)} municípios"),
        _linha(f"empregados por município: fração dentro de ±20% (≥ {min_emp} empregados)", "fração de municípios",
               float((erro <= 0.20).mean()), None, None, tol["fracao_municipios_dentro_20pct_min"], "minimo",
               detalhe=f"{int((erro <= 0.20).sum())} de {len(f5)} municípios"),
        _linha("cobertura da arrecadação 2025 (receita de referência válida)", "fração das ativas", validas, None, None,
               tol["cobertura_arrecadacao_min"], "minimo",
               detalhe="; ".join(f"{r.origem_receita}: {r.n}" for r in origem.itertuples())),
        _linha("cobertura dos colaboradores declarados", "fração das ativas", colab, None, None,
               tol["cobertura_colaboradores_min"], "minimo"),
        _linha("vínculos com distribuição do próprio município", "fração dos vínculos", dist[0], None, None,
               tol["vinculos_com_distribuicao_municipal_min"], "minimo",
               detalhe=f"{dist[1]} de {dist[2]} municípios com serventia usam a distribuição própria; os demais, a da "
                       "região imediata ou, se ela tiver menos de 20 vínculos, a de MG (D-022)"),
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
        condicao(con, f"({g}.interno_serventia JOIN {g}.interno_passivo_municipio USING (cod_ibge, nivel))",
                 "rateio por_empregados_cnj = CLT × passivo médio", "abs(passivo - coalesce(clt, 0) * "
                 f"{g}.interno_passivo_municipio.passivo_medio_vinculo) > 0.01"),
        condicao(con, f"{g}.fato_mercado_municipio_publico", "exibição sem município com menos serventias que o limiar",
                 f"NOT agregado_lgpd AND n_serventias < (SELECT max(limiar_lgpd) FROM {g}.execucao)"),
        condicao(con, f"{g}.geo_mapa_publico", "mapa: nenhuma área pública com menos serventias que o limiar (1.2)",
                 f"n_serventias < (SELECT max(limiar_lgpd) FROM {g}.execucao)"),
        condicao(con, f"{g}.geo_area_municipio", "mapa: todo município com serventia pertence a uma área",
                 f"cod_ibge IN (SELECT cod_ibge FROM {g}.dim_municipio WHERE n_serventias > 0) AND area_id IS NULL"),
        condicao(con, f"{g}.fato_mercado_uf", "mercado ≥ seguradora hipotética",
                 "mercado_premio_emitido < seguradora_premio_emitido"),
        condicao(con, f"({g}.fato_mercado_uf v1 JOIN {g}.fato_mercado_uf v2 USING (nivel, cenario_stf))",
                 "monotonicidade: regra v1 (universo maior) ≥ v2 em déficit, IS e prêmio (D-019)",
                 "v1.regra_classe = 'v1' AND v2.regra_classe = 'v2' AND (v1.valor_descoberto < v2.valor_descoberto - 1e-6 "
                 "OR v1.mercado_importancia_segurada < v2.mercado_importancia_segurada - 1e-6 "
                 "OR v1.mercado_premio_emitido < v2.mercado_premio_emitido - 1e-6)"),
        condicao(con, f"{g}.fato_mercado_uf", "suspende_8_17 zera a demanda",
                 "cenario_stf = 'suspende_8_17' AND mercado_importancia_segurada <> 0"),
        condicao(con, f"{g}.fato_mercado_uf", "faixa ordenada (min ≤ base ≤ max) no déficit",
                 f"nivel = 'base' AND (valor_descoberto < (SELECT valor_descoberto FROM {g}.fato_mercado_uf x WHERE "
                 "x.nivel = 'min' AND x.regra_classe = fato_mercado_uf.regra_classe AND x.cenario_stf = "
                 "fato_mercado_uf.cenario_stf) OR valor_descoberto > (SELECT valor_descoberto FROM "
                 f"{g}.fato_mercado_uf x WHERE x.nivel = 'max' AND x.regra_classe = fato_mercado_uf.regra_classe "
                 "AND x.cenario_stf = fato_mercado_uf.cenario_stf))"),
    ] + sem_dados_pessoais(con, g)
