"""Conclusões e lacunas (notebook 09): os números dos achados, lidos do banco e das tabelas gold.analise_*
(src/analise/tabelas.py). Nada aqui muda a base nem os 10 números oficiais; o que não é base sai como sensibilidade ou
projeção, rotulado como tal."""
import duckdb
import pandas as pd

from src import estado
from src.analise import dados, estatistica as est, grupos as gr, regressao as rg, sensibilidade as se, tabelas
from src.motor import calcular_serventias, peso_indeterminada, premissas_nivel, resumo_mercado
from src.transform.gold import carregar_insumos

COLUNAS_OFICIAIS = {"n_serventias_ativas": "serventias ativas", "clt": "empregados CLT", "n_universo": "obrigadas",
                    "passivo_todas": "passivo (todas)", "passivo_universo": "passivo (obrigadas)",
                    "n_deficit": "com déficit (esperado)", "valor_descoberto": "déficit",
                    "mercado_importancia_segurada": "IS do mercado", "mercado_premio_emitido": "prêmio anual"}


def numeros_oficiais(con) -> pd.DataFrame:
    """Os 10 números oficiais (regra v2, cenário do STF "mantém") nos níveis mínimo, base e máximo das premissas, de
    gold.fato_mercado_uf, mais o teto teórico (passivo das obrigadas × taxa do nível). Uma linha por número."""
    f = con.execute(f"""SELECT nivel, {', '.join(COLUNAS_OFICIAIS)} FROM gold.fato_mercado_uf
                        WHERE regra_classe = 'v2' AND cenario_stf = 'mantem'""").df().set_index("nivel").T
    taxa = estado.ler_semente()["premissas"]["taxa_seguro_anual"]["valores"]
    f.loc["teto"] = [f.loc["passivo_universo", n] * taxa[n] for n in f.columns]
    f.index = list(COLUNAS_OFICIAIS.values()) + ["teto teórico"]
    return f[["min", "base", "max"]]


NOMES_09 = ["analise_regras", "analise_grupos", "analise_clt_modelo", "analise_previsao", "analise_tornado",
            "analise_monte_carlo", "analise_sensibilidade_metodo", "analise_capacidade_calibracao", "analise_sinistro",
            "analise_premio_cenarios"]


def carregar(con) -> tuple[dict[str, pd.DataFrame], str]:
    """As tabelas gold.analise_* que o notebook 09 lê (NOMES_09: as seis da D-043, a sensibilidade de método da D-044
    e três das melhorias, D-045; a linha "sem os saltos" é da D-046): do
    banco, se o pipeline já as gravou, ou calculadas agora pelas mesmas funções do pipeline (src/analise/tabelas.py).
    Devolve as tabelas e de onde vieram."""
    no_banco = {t for (t,) in con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'gold' "
                                          "AND table_name LIKE 'analise_%'").fetchall()}
    nomes = NOMES_09
    if set(nomes) <= no_banco:
        return {t: con.execute(f"SELECT * FROM gold.{t}").df() for t in nomes}, "banco (gold.analise_*)"
    return tabelas.construir(con), "calculadas agora (src/analise/tabelas.py)"


def concentracao(sv: pd.DataFrame, topo: float) -> pd.DataFrame:
    """Gini e a parte dos `topo` maiores no passivo das obrigadas (dado) e no déficit esperado (suposição)."""
    obr = sv[sv["peso_universo"] > 0]
    series = {"passivo das obrigadas": obr["passivo"] * obr["peso_universo"], "déficit esperado": obr["valor_descoberto"]}
    return pd.DataFrame([{"medida": n, "gini": est.gini(s), "parte_do_topo": est.participacao_topo(s, topo)}
                         for n, s in series.items()])


def perfil_grupos(sv: pd.DataFrame, tab_grupos: pd.DataFrame) -> pd.DataFrame:
    """Perfil de cada grupo do notebook 04 (gr.perfil), com a parte das serventias, das obrigadas, do passivo das
    obrigadas (dado) e do déficit (suposição) de MG."""
    t = tab_grupos.set_index("cns")
    p = gr.perfil(sv, t["grupo"])
    p["nome"] = t.groupby("grupo")["nome_grupo"].first()
    p["grupo_alvo"] = t.groupby("grupo")["grupo_alvo"].first()
    obr = sv["passivo"] * sv["peso_universo"]
    p["pct_serventias"] = p["serventias"] / p["serventias"].sum()
    p["pct_obrigadas_mg"] = p["obrigadas"] / sv["peso_universo"].sum()
    p["pct_passivo_obrigadas_mg"] = p["passivo_obrigadas"] / obr.sum()
    return p


def erro_clt(tab_clt: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Do desenho da gold.analise_clt_modelo: o erro por serventia de cada método (MAE, R²) e o erro do total de CLT
    de cada região intermediária prevista de fora, em %."""
    metodos = {"floresta aleatória": "clt_previsto_floresta", "Poisson": "clt_previsto_poisson",
               "referência: mediana por faixa de receita": "clt_previsto_referencia"}
    m = pd.DataFrame({n: rg.metricas(tab_clt["clt_declarado"], tab_clt[c]) for n, c in metodos.items()}).T
    reg = tab_clt.groupby("regiao_intermediaria")[["clt_declarado", "clt_previsto_floresta"]].sum()
    reg["erro_total_pct"] = 100 * (reg["clt_previsto_floresta"] / reg["clt_declarado"] - 1)
    return m, reg.sort_values("erro_total_pct")


def efeito_receita_liquida(con: duckdb.DuckDBPyConnection, limites: dict, cenarios: dict) -> pd.DataFrame:
    """Sensibilidade do notebook 08 (seção 5): o universo e o mercado com a receita de referência descontada do
    repasse (art. 2º, XXIV, do Prov. 213; fração de repasse do BI do CNJ em 2025), com a faixa de déficit da base
    (D-019). Duas linhas (base e receita líquida) e as colunas de resumo_mercado."""
    semente = estado.ler_semente()
    ins = carregar_insumos(con)
    peso = con.execute("SELECT peso_classe_indeterminada_base FROM gold.execucao WHERE regra_classe = 'v2'"
                       ).fetchone()[0]
    p = premissas_nivel(semente, "base", peso)
    serv0 = calcular_serventias(ins, p, limites, limites_faixa=limites)[0]
    bi = dados.arrecadacao_bi(con)
    ins_liq = se.insumos_receita_liquida(ins, se.receita_ref_bi(bi[bi["cns"].isin(serv0["cns"])], 2025))
    p_liq = premissas_nivel(semente, "base", peso_indeterminada(ins_liq.serventias, limites))
    serv_liq = se.com_faixa_da_base(calcular_serventias(ins_liq, p_liq, limites, limites_faixa=limites)[0], serv0, p_liq)
    return pd.DataFrame([{"leitura": "base: arrecadação", **resumo_mercado(serv0, p, cenarios, "mantem")},
                         {"leitura": "sensibilidade: arrecadação − repasse",
                          **resumo_mercado(serv_liq, p_liq, cenarios, "mantem")}]).set_index("leitura")


def saltos_por_semestre(serie: pd.DataFrame, desde: int) -> pd.DataFrame:
    """Saltos grosseiros (estatistica.saltos) por semestre desde o ano `desde`: quantos e o excesso sobre a mediana
    anterior da serventia, ao lado da arrecadação total de MG."""
    sal = est.saltos(serie)
    sal = sal.assign(excesso=sal["arrecadacao"] - sal["mediana_anterior"])
    tot = serie.groupby("periodo")["arrecadacao"].sum()
    out = pd.DataFrame({"arrecadacao_mg": tot, "saltos": sal.groupby("periodo").size(),
                        "excesso": sal.groupby("periodo")["excesso"].sum()}).fillna({"saltos": 0, "excesso": 0})
    out = out[[int(p[:4]) >= desde for p in out.index]]
    out["pct_do_total"] = out["excesso"] / out["arrecadacao_mg"]
    return out
