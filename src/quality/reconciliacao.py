"""Reconciliações entre fontes e contratos do gold (SPEC §4). Divergência entre fontes = aviso; violação de contrato = erro.

Saídas: qualidade.reconciliacoes (resumo); qualidade.interno_rec_municipio (CNJ × CNPJ × RAIS por município, uso
interno) e qualidade.rec_municipio (versão pública, uma linha por município, inclusive os pequenos; D-078).
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
    # 10 casas: a correlação em log mudava no 15º dígito conforme a ordem das linhas (refazer o gold a partir do
    # Parquet do silver dava 2,8e-15 de diferença e outro hash da tabela pública; D-044)
    arred = lambda v: None if v is None else round(float(v), 10)  # noqa: E731
    return {"checagem": checagem, "fonte_a": fonte_a, "valor_a": arred(valor_a), "fonte_b": fonte_b,
            "valor_b": arred(valor_b), "indicador": arred(dif), "tolerancia": tolerancia,
            "status": "ok" if ok else "aviso", "detalhe": detalhe}


def rec_municipio_publico(rec: pd.DataFrame) -> pd.DataFrame:
    """Versão pública da reconciliação por município: uma linha por município, com o nome, inclusive os de 1 ou 2
    serventias (D-078; antes, D1, os menores eram somados por região imediata). Mesmas colunas de antes."""
    cols = ["n_cnj", "n_cnpj", "clt_cnj", "vinc_rais"]
    out = rec.assign(area=rec["municipio"], area_completa=rec["municipio"], tipo="municipio", n_municipios=1)
    out = out[["area", "area_completa", "tipo", "regiao_imediata", "n_municipios"] + cols].reset_index(drop=True)
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
        SELECT m.cod_ibge, m.uf, m.nome AS municipio, m.regiao_imediata, coalesce(n_cnj, 0) n_cnj, coalesce(n_cnpj, 0) n_cnpj,
               coalesce(clt_cnj, 0) clt_cnj, coalesce(vinc_rais, 0) vinc_rais
        FROM silver.municipio_ibge m LEFT JOIN cnj USING (cod_ibge) LEFT JOIN cnpj USING (cod_ibge)
        LEFT JOIN rais USING (cod_ibge)""").df()
    rec_mun["dif_serventias"] = rec_mun["n_cnpj"] - rec_mun["n_cnj"]
    rec_mun["dif_empregados"] = rec_mun["vinc_rais"] - rec_mun["clt_cnj"]
    con.execute("CREATE SCHEMA IF NOT EXISTS qualidade")
    for nome, df in (("interno_rec_municipio", rec_mun), ("rec_municipio", rec_municipio_publico(rec_mun))):
        con.register("_df", df)
        con.execute(f"CREATE OR REPLACE TABLE qualidade.{nome} AS SELECT * FROM _df")
        con.unregister("_df")

    # resumo PÚBLICO (só contagens agregadas) para o painel, que não lê tabelas interno_* (1.7); por UF (D-088)
    resumo = []
    linhas = []
    for uf in rec_mun.loc[rec_mun.n_cnj > 0, "uf"].drop_duplicates():
        r, l_ = _conferencias_da_uf(con, rec_mun[rec_mun.uf == uf], uf, tol)
        resumo += r
        linhas += l_
    df_resumo = pd.DataFrame(resumo, columns=["uf", "chave", "valor", "descricao"])
    con.register("_df", df_resumo)
    con.execute("CREATE OR REPLACE TABLE qualidade.resumo_publico AS SELECT * FROM _df")
    con.unregister("_df")
    df = pd.DataFrame(linhas)
    con.register("_df", df)
    con.execute("CREATE OR REPLACE TABLE qualidade.reconciliacoes AS SELECT * FROM _df")
    con.unregister("_df")
    return df


def _conferencias_da_uf(con, rec_mun: pd.DataFrame, uf: str, tol: dict) -> tuple[list, list]:
    """As conferências entre fontes de uma UF (até a D-088 eram de MG, a única UF). Os nomes das checagens de MG são
    os mesmos de antes; cada linha leva a `uf`."""
    t = rec_mun.sum(numeric_only=True)
    corr = rec_mun[(rec_mun.clt_cnj > 0) | (rec_mun.vinc_rais > 0)][["clt_cnj", "vinc_rais"]].corr().iloc[0, 1]
    # C1: métricas por município que não são dominadas pela capital
    com_dado = rec_mun[(rec_mun.clt_cnj > 0) | (rec_mun.vinc_rais > 0)]
    ambos = com_dado[(com_dado.clt_cnj > 0) & (com_dado.vinc_rais > 0)]
    corr_log = float(np.log(ambos.clt_cnj).corr(np.log(ambos.vinc_rais)))
    min_emp = tol["minimo_empregados_para_erro_pct"]
    f5 = com_dado[(com_dado.clt_cnj >= min_emp) | (com_dado.vinc_rais >= min_emp)]
    erro = ((f5.vinc_rais - f5.clt_cnj).abs() / f5.clt_cnj.where(f5.clt_cnj > 0)).fillna(np.inf)
    zero_rais = int(((com_dado.vinc_rais == 0) & (com_dado.clt_cnj > 0)).sum())
    zero_cnj = int(((com_dado.clt_cnj == 0) & (com_dado.vinc_rais > 0)).sum())
    resumo = [(uf, "municipios_rais_zero_cnj_positivo", zero_rais, "municípios com RAIS = 0 e CNJ > 0"),
              (uf, "municipios_cnj_zero_rais_positivo", zero_cnj, "municípios com CNJ = 0 e RAIS > 0")]
    for origem_d, n, v in con.execute("""SELECT origem_distribuicao, count(*), sum(n_vinculos_rais)
                                         FROM gold.interno_passivo_municipio WHERE nivel = 'base' AND uf = ?
                                         GROUP BY 1 ORDER BY 1""", [uf]).fetchall():
        resumo += [(uf, f"distribuicao_{origem_d}_municipios", n, f"municípios com distribuição salarial: {origem_d}"),
                   (uf, f"distribuicao_{origem_d}_vinculos", v, f"vínculos próprios desses municípios: {origem_d}")]
    n_iguais = int((rec_mun.n_cnj == rec_mun.n_cnpj).sum())
    # ORDER BY: sem ele a ordem do texto do detalhe muda entre cargas (achado na prova de reprodutibilidade, D-029)
    origem = con.execute("SELECT origem_receita, count(*) n FROM gold.interno_dim_serventia WHERE uf = ? GROUP BY 1 "
                         "ORDER BY 1", [uf]).df()
    validas = origem.loc[origem.origem_receita.isin(["media_2_semestres", "um_semestre"]), "n"].sum() / origem.n.sum()
    colab = con.execute("SELECT avg(k.informado::INT) FROM silver.serventia_colaboradores k JOIN silver.serventia s "
                        "USING (cns) WHERE s.uf = ?", [uf]).fetchone()[0]
    dist = con.execute("""SELECT sum(n_vinculos_rais) FILTER (WHERE origem_distribuicao = 'municipio') / sum(n_vinculos_rais),
                                 count(*) FILTER (WHERE origem_distribuicao = 'municipio'), count(*)
                          FROM gold.interno_passivo_municipio WHERE nivel = 'base' AND uf = ?""", [uf]).fetchone()
    linhas = [
        _linha(f"serventias ativas: CNPJ × CNJ ({uf})", "CNPJ ativos, CNAE principal 6912-5/00", t.n_cnpj, "CNJ ativas",
               t.n_cnj, tol["serventias_cnj_x_cnpj_pct"],
               detalhe=f"{n_iguais} de {len(rec_mun)} municípios com a mesma contagem; o CNPJ guarda CNPJs não baixados"),
        _linha(f"empregados: RAIS × CNJ ({uf})", "RAIS vínculos ativos em 31/12/2025", t.vinc_rais, "CNJ colaboradores CLT",
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
                       f"região imediata ou, se ela tiver menos de 20 vínculos, a de {uf} (D-022)"),
    ]
    return resumo, [{"uf": uf, **x} for x in linhas]


def _regra_base() -> str:
    return yaml.safe_load((CONFIG / "regras_classificacao.yaml").read_text(encoding="utf-8"))["versao_base"]


def classe_api_x_bi(con: duckdb.DuckDBPyConnection) -> Checagem:
    """Aviso (D-048; caso da serventia 035030): serventias ativas cuja classe (regra base) mudaria se a
    receita de 2025 viesse do BI do CNJ, e não da API do Justiça Aberta. A classe continua pela API (D-010); a
    checagem só mostra quantas dependem da fonte. O CSV do BI é opcional (bronze): sem ele, sai com 0 e o motivo."""
    from src.analise import dados, enquadramento
    from src.analise.sensibilidade import receita_ref_bi
    nome = "classe pela API × pelo BI do CNJ (receita de 2025, regra base)"
    if not dados.arquivo_bi().exists():
        return Checagem("gold.interno_serventia", nome, "aviso", 0, "sem o CSV do BI do CNJ no bronze: não conferido")
    regra = _regra_base()
    api = con.execute("SELECT cns, classe FROM gold.interno_serventia WHERE nivel = 'base' AND regra_classe = ? "
                      "AND classe IN ('1', '2', '3')", [regra]).df()
    bi = receita_ref_bi(dados.arrecadacao_bi(con), 2025)
    m = api.merge(bi[["cns", "arrecadacao_bi"]], on="cns")
    m["classe_bi"] = enquadramento.classe_pela_receita(m["arrecadacao_bi"], regra)
    dif = m[m["classe"] != m["classe_bi"]]
    para_1 = int((dif["classe_bi"] == "1").sum())
    da_1 = int((dif["classe"] == "1").sum())
    return Checagem("gold.interno_serventia", nome, "aviso", len(dif),
                    f"{len(dif)} de {len(m)} serventias com as duas fontes mudariam de classe: {para_1} iriam para a "
                    f"Classe 1, {da_1} sairiam dela e {len(dif) - para_1 - da_1} trocariam entre a 2 e a 3; a classe "
                    "segue a API (D-010)" if len(dif) else "")


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
        condicao(con, f"{g}.dim_municipio", "por município (D-078): todo município com serventia na tabela de mercado",
                 f"n_serventias > 0 AND cod_ibge NOT IN (SELECT cod_ibge FROM {g}.fato_mercado_municipio_publico)"),
        condicao(con, f"{g}.dim_municipio", "por município (D-078): todo município com serventia no mapa (uma área "
                 "própria) e no ranking",
                 f"n_serventias > 0 AND (CAST(cod_ibge AS VARCHAR) NOT IN (SELECT area_id FROM {g}.geo_mapa_publico) "
                 f"OR cod_ibge NOT IN (SELECT cod_ibge FROM {g}.ranking_municipio_publico))"),
        condicao(con, f"{g}.geo_area_municipio", "mapa: todo município com serventia pertence a uma área",
                 f"cod_ibge IN (SELECT cod_ibge FROM {g}.dim_municipio WHERE n_serventias > 0) AND area_id IS NULL"),
        classe_api_x_bi(con),
        chave_unica(con, f"{g}.serventia_publico", "cns"),
        # com mais de uma UF (D-088), toda comparação entre linhas de fato_mercado_uf é feita dentro da mesma UF
        condicao(con, f"{g}.fato_mercado_uf", "por serventia (D-038): a soma de gold.serventia_publico dá o total da UF "
                 "(nível e regra base, STF mantém)",
                 f"nivel = 'base' AND regra_classe = '{_regra_base()}' AND cenario_stf = 'mantem' AND (abs(n_serventias_ativas - "
                 f"(SELECT count(*) FROM {g}.serventia_publico p WHERE p.uf = fato_mercado_uf.uf)) > 0 OR "
                 f"abs(valor_descoberto - (SELECT sum(valor_descoberto) FROM {g}.serventia_publico p WHERE "
                 f"p.uf = fato_mercado_uf.uf)) > 0.01 OR abs(mercado_premio_emitido - (SELECT sum(premio_emitido) "
                 f"FROM {g}.serventia_publico p WHERE p.uf = fato_mercado_uf.uf)) > 0.01)"),
        # situação e classe particionam a UF (cada serventia tem uma só): a soma dos recortes dá o total (D-088)
        condicao(con, f"{g}.fato_mercado_uf", "recortes por situação e por classe somam o total da UF (D-088)",
                 "cenario_stf = 'mantem' AND EXISTS (SELECT 1 FROM (SELECT filtro, sum(n_serventias_ativas) AS n, "
                 f"sum(valor_descoberto) AS d FROM {g}.mercado_filtro_uf f WHERE f.uf = fato_mercado_uf.uf AND "
                 "f.regra_classe = fato_mercado_uf.regra_classe AND f.nivel = fato_mercado_uf.nivel AND "
                 "f.filtro IN ('situacao', 'classe') GROUP BY filtro) s WHERE s.n <> fato_mercado_uf.n_serventias_ativas "
                 "OR abs(s.d - fato_mercado_uf.valor_descoberto) > 0.01)"),
        condicao(con, f"{g}.fato_mercado_uf", "mercado ≥ seguradora hipotética",
                 "mercado_premio_emitido < seguradora_premio_emitido"),
        condicao(con, f"({g}.fato_mercado_uf v1 JOIN {g}.fato_mercado_uf v2 USING (uf, nivel, cenario_stf))",
                 "monotonicidade: regra v1 (universo maior) ≥ v2 em déficit, IS e prêmio (D-019)",
                 "v1.regra_classe = 'v1' AND v2.regra_classe = 'v2' AND (v1.valor_descoberto < v2.valor_descoberto - 1e-6 "
                 "OR v1.mercado_importancia_segurada < v2.mercado_importancia_segurada - 1e-6 "
                 "OR v1.mercado_premio_emitido < v2.mercado_premio_emitido - 1e-6)"),
        condicao(con, f"{g}.fato_mercado_uf", "suspende_8_17 zera a demanda",
                 "cenario_stf = 'suspende_8_17' AND mercado_importancia_segurada <> 0"),
        condicao(con, f"{g}.fato_mercado_uf", "faixa ordenada (min ≤ base ≤ max) no déficit",
                 f"nivel = 'base' AND (valor_descoberto < (SELECT valor_descoberto FROM {g}.fato_mercado_uf x WHERE "
                 "x.uf = fato_mercado_uf.uf AND x.nivel = 'min' AND x.regra_classe = fato_mercado_uf.regra_classe AND "
                 "x.cenario_stf = fato_mercado_uf.cenario_stf) OR valor_descoberto > (SELECT valor_descoberto FROM "
                 f"{g}.fato_mercado_uf x WHERE x.uf = fato_mercado_uf.uf AND x.nivel = 'max' AND "
                 "x.regra_classe = fato_mercado_uf.regra_classe AND x.cenario_stf = fato_mercado_uf.cenario_stf))"),
    ] + sem_dados_pessoais(con, g)
