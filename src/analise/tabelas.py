"""Tabelas gold.analise_* (Etapa 2 do docs/plano_projeto.md): o cálculo dos notebooks 03, 04, 06, 07 e 08, do banco
até a tabela, numa função por tabela. O pipeline grava (pipeline.py, etapa_analise); o notebook 09 lê o resultado.

Cada função repete, na mesma ordem e com a mesma semente, as células do notebook que desenhou a tabela; o resultado
é igual ao do notebook (conferido em 2026-10-28, docs/diario.md). Só lê do banco (gold.interno_serventia,
gold.execucao, gold.fato_mercado_uf e o silver) e da config/: nada aqui muda a base nem os 10 números oficiais.
"""
import warnings

import numpy as np
import pandas as pd
import yaml

from src import estado
from src.analise import RAIZ, config, dados
from src.analise import classificacao as cl
from src.analise import enquadramento as enq
from src.analise import estatistica as est
from src.analise import grupos as gr
from src.analise import melhorias as mh
from src.analise import padroes
from src.analise import previsao as pv
from src.analise import regressao as rg
from src.analise import sensibilidade as se
from src.model import simulador
from src.motor import Insumos, calcular_serventias, peso_indeterminada, premissas_nivel, resumo_mercado
from src.transform.gold import carregar_insumos

SARIMA = "SARIMA(0,1,1)(0,1,1)2 (log)"
VARIANTE_PRINCIPAL = "tendência do T2 (principal)"
MEDIDAS_MERCADO = ["acima_do_limite", "providas_acima", "subidas", "descidas", "subidas_ate_consolidacao",
                   "classe_2_para_3", "n_universo", "passivo_universo", "valor_descoberto",
                   "mercado_importancia_segurada", "mercado_premio_emitido"]


def _cenarios() -> dict:
    return yaml.safe_load((RAIZ / "config" / "cenarios_stf.yaml").read_text(encoding="utf-8"))


def _limites() -> dict:
    regras = yaml.safe_load((RAIZ / "config" / "regras_classificacao.yaml").read_text(encoding="utf-8"))
    return regras["versoes"]["v2"]["limites"]


def _ano_enquadramento() -> int:
    return yaml.safe_load((RAIZ / "config" / "escopo.yaml").read_text(encoding="utf-8"))["ano_enquadramento"]


def _peso_indeterminada(con) -> float:
    return con.execute("SELECT peso_classe_indeterminada_base FROM gold.execucao WHERE regra_classe = 'v2'"
                       ).fetchone()[0]


def regras(con) -> pd.DataFrame:
    """gold.analise_regras (notebook 03): as regras estáveis que terminam em "obrigada", na ordem do lift."""
    trans = padroes.transacoes(dados.serventias(con))
    candidatas = padroes.regras_alvo(trans, padroes.regras(trans))
    return padroes.tabela_regras(candidatas, trans, padroes.estabilidade(trans))


def grupos(con) -> pd.DataFrame:
    """gold.analise_grupos (notebook 04): o grupo do k-means de cada serventia agrupada, com o k da maior silhueta."""
    semente = config()["semente"]
    sv = dados.serventias(con)
    x = gr.matriz(sv)
    z = gr.padronizar(x)
    escolha = gr.escolha_k(z)
    k = int(escolha.loc[escolha["silhueta"].idxmax(), "k"])
    grupo = pd.Series(gr.ordenar_por_receita(gr.kmeans(z, k), x["log_receita"]), index=x.index, name="grupo")
    perfil = gr.perfil(sv, grupo)
    nomes, confere = gr.nomes_grupos(perfil)
    if not confere:
        warnings.warn("analise_grupos: o perfil dos grupos mudou; nomes genéricos (renomear no notebook 04)")
    return gr.tabela_grupos(grupo, nomes, gr.grupo_alvo(perfil), k, semente)


def grupos_perfil(con, tab_grupos: pd.DataFrame) -> pd.DataFrame:
    """gold.analise_grupos_perfil (D-044): o perfil agregado de cada grupo da gold.analise_grupos (gr.perfil), sem
    nenhum dado por serventia, com a parte das serventias, das obrigadas e do passivo das obrigadas de MG. É a versão
    da análise de grupos que vai para o conjunto público."""
    sv = dados.serventias(con)
    t = tab_grupos.set_index("cns")
    p = gr.perfil(sv, t["grupo"])
    obr = sv["passivo"] * sv["peso_universo"]
    p.insert(0, "nome_grupo", t.groupby("grupo")["nome_grupo"].first())
    p.insert(1, "grupo_alvo", t.groupby("grupo")["grupo_alvo"].first())
    p["pct_serventias"] = p["serventias"] / p["serventias"].sum()
    p["pct_obrigadas_mg"] = p["obrigadas"] / sv["peso_universo"].sum()
    p["pct_passivo_obrigadas_mg"] = p["passivo_obrigadas"] / obr.sum()
    return p.rename(columns={"serventias": "n_serventias"}).reset_index()


def sensibilidade_metodo(con) -> pd.DataFrame:
    """gold.analise_sensibilidade_metodo (D-042, itens 2 e 3; D-044): as leituras alternativas do notebook 08 que
    refazem o modelo inteiro, ao lado da base. Universo: receita líquida do repasse (art. 2º, XXIV, do Prov. 213), com
    a faixa de déficit da base (D-019). Passivo: T5 (vínculos sem salário de dezembro com salário estimado), T6
    (reserva por encolhimento) e, para comparar, a reserva no estado inteiro (gold.sensibilidade_premissas). Nível
    base, regra v2, STF mantém. Nenhuma linha muda a base.
    A receita líquida usa o CSV do BI do CNJ no bronze, que é opcional (README; não vai no pacote público): sem ele, a
    linha sai com um aviso, e o pipeline a partir do silver continua rodando sem o bronze (D-029)."""
    semente_premissas, cenarios, limites = estado.ler_semente(), _cenarios(), _limites()
    p = premissas_nivel(semente_premissas, "base", _peso_indeterminada(con))
    ins = carregar_insumos(con)
    serv0 = calcular_serventias(ins, p, limites, limites_faixa=limites)[0]

    linha_liq = []
    if dados.arquivo_bi().exists():
        bi = dados.arrecadacao_bi(con)
        ins_liq = se.insumos_receita_liquida(ins, se.receita_ref_bi(bi[bi["cns"].isin(serv0["cns"])], 2025))
        p_liq = premissas_nivel(semente_premissas, "base", peso_indeterminada(ins_liq.serventias, limites))
        serv_liq = se.com_faixa_da_base(calcular_serventias(ins_liq, p_liq, limites, limites_faixa=limites)[0],
                                        serv0, p_liq)
        linha_liq = [("receita_liquida", "universo: leitura do Prov. 213", "Leitura literal do art. 2º, XXIV: "
                      "arrecadação − repasse (aproximada: o repasse do BI cobre só o inciso XXVI; o inciso XXV não "
                      "tem fonte)", resumo_mercado(serv_liq, p_liq, cenarios, "mantem"))]
    else:
        warnings.warn(f"analise_sensibilidade_metodo: sem o CSV do BI do CNJ ({dados.arquivo_bi().name}); a linha "
                      "da receita líquida fica de fora")
    # regra do salto (D-046): a base usa o valor declarado; aqui, a receita de quem tem salto grosseiro no ano de
    # enquadramento vira a média dos semestres sem o salto (notebook 01, §7b), com a faixa de déficit da base
    serie = dados.serie_arrecadacao(con)
    ref_ss = enq.receita_sem_saltos(serie, est.saltos(serie), _ano_enquadramento())
    s_ss = ins.serventias.copy()
    s_ss["receita_ref"] = s_ss["receita_ref"].where(s_ss["receita_ref"].isna(),
                                                    s_ss["cns"].map(ref_ss).combine_first(s_ss["receita_ref"]))
    ins_ss = Insumos(rais=ins.rais, serventias=s_ss, fator_inpc=ins.fator_inpc, mes_inpc=ins.mes_inpc,
                     regioes=ins.regioes)
    p_ss = premissas_nivel(semente_premissas, "base", peso_indeterminada(ins_ss.serventias, limites))
    serv_ss = se.com_faixa_da_base(calcular_serventias(ins_ss, p_ss, limites, limites_faixa=limites)[0], serv0, p_ss)
    linha_ss = ("sem_saltos", "universo: regra do salto", "Semestre de 2025 com salto grosseiro trocado pela média dos "
                "semestres sem salto (D-046; a base usa o valor declarado)", resumo_mercado(serv_ss, p_ss, cenarios,
                                                                                         "mantem"))

    rais5, _ = se.rais_com_salario_estimado(ins.rais, ins.regioes)
    ins5 = Insumos(rais=rais5, serventias=ins.serventias, fator_inpc=ins.fator_inpc, mes_inpc=ins.mes_inpc,
                   regioes=ins.regioes)
    municipios = ins.serventias.cod_ibge.dropna().astype(int).unique().tolist()
    medio6 = se.medio_com_encolhimento(se.vinculos_base(ins, p), municipios, p,
                                       int(p["limiar_vinculos_distribuicao_municipal"]), ins.regioes)
    gold_sem_regiao = con.execute("SELECT * FROM gold.sensibilidade_premissas WHERE chave = 'sem_regiao'").df()

    passivo = "passivo: escolhas de método"
    linhas = [
        ("base", "base", "Base (arrecadação; D-015 e D-022)", resumo_mercado(serv0, p, cenarios, "mantem")),
        *linha_liq,
        linha_ss,
        ("t5_salario_estimado", passivo, "T5: incluir os vínculos sem salário de dezembro, com salário estimado",
         resumo_mercado(calcular_serventias(ins5, p, limites, limites_faixa=limites)[0], p, cenarios, "mantem")),
        ("t6_encolhimento", passivo, "T6: reserva por encolhimento (município pequeno mistura a própria média com a "
         "da região)", resumo_mercado(se.calcular_com_medio(ins, p, limites, medio6), p, cenarios, "mantem")),
        ("sem_regiao", passivo, "Reserva da distribuição = MG inteiro, sem a região (gold.sensibilidade_premissas)",
         gold_sem_regiao.iloc[0].to_dict()),
    ]
    cols = ["n_universo", "passivo_todas", "passivo_universo", "valor_descoberto", "mercado_importancia_segurada",
            "mercado_premio_emitido"]
    out = pd.DataFrame([{"chave": c, "bloco": b, "rotulo": r, **{k: float(v[k]) for k in cols}}
                        for c, b, r, v in linhas])
    for c in cols:
        out[f"var_{c}"] = out[c] / out.loc[0, c] - 1
    return out


def clt_modelo(con) -> pd.DataFrame:
    """gold.analise_clt_modelo (notebook 06a): CLT declarado e previsto com a região intermediária de fora."""
    base = rg.base_clt(dados.serventias(con))
    prev, _, _ = rg.validar_grupo_fora(base, rg.METODOS_CLT)
    return rg.tabela_clt_modelo(base, prev)


def tornado_e_monte_carlo(con) -> tuple[pd.DataFrame, pd.DataFrame]:
    """gold.analise_tornado e gold.analise_monte_carlo (notebook 08): cada premissa sozinha do mínimo ao máximo e os
    sorteios triangulares das seis suposições (independentes e com o patrimônio junto)."""
    cfg = config()
    semente, n = cfg["semente"], cfg["sensibilidade"]["sorteios"]
    semente_premissas, cenarios = estado.ler_semente(), _cenarios()
    peso = _peso_indeterminada(con)
    p = premissas_nivel(semente_premissas, "base", peso)
    totais = simulador.totais(dados.serventias(con))
    faixas = se.faixas_suposicoes(semente_premissas)
    tor_sup = se.tornado(totais, faixas, p, cenarios).assign(grupo="suposição (passos 5 a 8)")
    tor_rec = se.tornado_recalculo(carregar_insumos(con), semente_premissas, peso, _limites(), cenarios).assign(
        grupo="passivo e universo")
    tor = pd.concat([tor_sup, tor_rec]).sort_values("amplitude", ascending=False).reset_index(drop=True)

    x_ind = se.sortear(faixas, n, semente)
    x_jun = se.sortear(faixas, n, semente, juntas=se.PATRIMONIO)
    cantos = {nv: {k: float(v[0]) for k, v in se.premio_vetorial(totais, {s: np.array([faixas.loc[s, nv]])
                                                                         for s in faixas.index}).items()}
              for nv in ("min", "base", "max")}
    res = {"independentes": se.resumo_sorteios(se.premio_vetorial(totais, x_ind)),
           "patrimônio junto": se.resumo_sorteios(se.premio_vetorial(totais, x_jun))}
    return se.tabela_tornado(tor), se.tabela_monte_carlo(res, cantos, n, semente)


def previsao(con) -> pd.DataFrame:
    """gold.analise_previsao (notebook 07): arrecadação de MG por semestre de 2026 e 2027 (5 variantes) e o mercado
    projetado por ano, variante da previsão e cenário do limite (11 medidas), com P10, central e P90. PROJEÇÃO."""
    cfg = config()
    pc, semente = cfg["previsao"], cfg["semente"]
    serie = dados.serie_arrecadacao(con)
    y_tudo = pv.serie_mg(serie)
    y = y_tudo.loc[:pc["ultimo_periodo"]]
    ult = y_tudo.index[-1]
    semente_premissas, cenarios, limites = estado.ler_semente(), _cenarios(), _limites()
    ano_b, h_max = pc["ano_base"], pc["horizonte"]

    sal = est.saltos(serie)
    ss = est.sem_saltos(serie, sal)
    y_ss = pv.serie_mg(ss).loc[:pc["ultimo_periodo"]]
    with warnings.catch_warnings():   # avisos de convergência do SARIMA e do Holt-Winters
        warnings.filterwarnings("ignore", module="statsmodels")
        _, erros = pv.origem_movel(y)
        prev = {m: pv.prever(y, m, h_max) for m in [pv.PRINCIPAL, SARIMA, pv.REFERENCIA]}
    faixas = {m: pv.faixa(prev[m], erros.loc[erros["metodo"] == m, "erro_rel"]) for m in prev}
    comp, _ = pv.completar_semestre(ss, ult, pc["completar_com"])
    y_c = pv.serie_mg(comp)
    _, err_ss = pv.origem_movel(y_ss, {pv.PRINCIPAL: pv.METODOS[pv.PRINCIPAL]})
    f_ss = pv.faixa(pv.prever(y_ss, pv.PRINCIPAL, h_max), err_ss["erro_rel"])
    q = pv.quebra_de_nivel(y_c, pc["quebra"])
    prev_q = pv.prever(y_c, q["funcao"], h_max - 1)          # o semestre completado já entra no ajuste
    f_q = pv.faixa(prev_q, erros.loc[erros["metodo"] == pv.PRINCIPAL, "erro_rel"])

    media, _ = cl.receita_anual(serie)
    lim1 = limites["classe_1_max"]
    dsv = {h: pv.desvios_individuais(media, sal, list(range(ano_b - h - pc["desvios"]["anos"] + 1, ano_b - h + 1)),
                                     h, lim1) for h in (1, 2)}
    p = premissas_nivel(semente_premissas, "base", _peso_indeterminada(con))
    serv0 = calcular_serventias(carregar_insumos(con), p, limites, limites_faixa=limites)[0]
    inflacao, _ = pv.inflacao_recente(dados.indice_preco(con, "IPCA"))
    ea = pv.erros_anuais(erros, pv.PRINCIPAL)
    fat = {VARIANTE_PRINCIPAL: pv.fatores_ano(prev[pv.PRINCIPAL], y, ano_b),
           f"quebra de nível em {pc['quebra']} (sensibilidade)": pv.fatores_ano(pd.concat([y_c.loc[ult:], prev_q]),
                                                                                y_c, ano_b)}
    rng = np.random.default_rng(semente)
    n = pc["sorteios"]
    linhas = []
    for ano in pc["anos"]:
        h = ano - ano_b
        d = dsv[h]["desvio"].to_numpy()
        e = ea.loc[ea["ano_frente"] == h, "erro_rel"].to_numpy()
        for variante, f in fat.items():
            rec_c = pv.sortear_receitas(serv0["receita_ref"], np.full(n, f[ano]), d, rng)
            rec_f = pv.sortear_receitas(serv0["receita_ref"], pv.sortear_fatores(float(f[ano]), e, n, rng), d, rng)
            for cen_lim, lim_ in [("limite fixo", limites),
                                  ("limite corrigido pelo IPCA", pv.limites_corrigidos(limites, inflacao, h))]:
                c = pv.projetar_mercado(serv0, rec_c, lim_, semente_premissas, cenarios)
                fx = pv.projetar_mercado(serv0, rec_f, lim_, semente_premissas, cenarios)
                for m in MEDIDAS_MERCADO:
                    linhas.append({"ano": ano, "variante": variante, "cenario_limite": cen_lim, "medida": m,
                                   "p10": fx[m].quantile(pc["faixa"][0]), "central": c[m].median(),
                                   "p90": fx[m].quantile(pc["faixa"][1])})
    arr = []
    for nome, f, real in [("tendência do T2, regra atual (principal)", faixas[pv.PRINCIPAL], y_tudo[ult]),
                          ("SARIMA, regra atual (comparação)", faixas[SARIMA], y_tudo[ult]),
                          ("referência: repete o último semestre", faixas[pv.REFERENCIA], y_tudo[ult]),
                          ("tendência do T2, sem saltos grosseiros", f_ss, y_c[ult]),
                          (f"quebra de nível em {pc['quebra']}, sem saltos e com o {ult} completado", f_q, np.nan)]:
        for periodo, r in f.iterrows():
            arr.append({"periodo": periodo, "variante": nome, "p10": r.p10, "central": r.central, "p90": r.p90,
                        "realizado": real if periodo == ult else np.nan})
    return pv.tabela_previsao(pd.DataFrame(arr), pd.DataFrame(linhas))


def melhorias(con, monte_carlo: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """As tabelas das melhorias de confiança (notebook 10; D-045): capacidade de pagar (M1, por faixa de meses de saldo
    e por faixa de déficit × horizonte), sinistro por frequência × severidade (M2), prêmio por cenário do STF (M7) e
    na grade taxa × adesão (M8). A M1 e a M2 usam o CSV do BI do CNJ no bronze, que é opcional: sem ele, essas três
    tabelas ficam de fora, com um aviso."""
    semente_premissas, cenarios = estado.ler_semente(), _cenarios()
    p = premissas_nivel(semente_premissas, "base", _peso_indeterminada(con))
    sv = dados.serventias(con)
    out = {"analise_premio_cenarios": mh.premio_por_cenario(monte_carlo, cenarios),
           "analise_premio_grade": mh.grade_taxa_adesao(float(sv["valor_descoberto"].sum()), semente_premissas)
           .reset_index().melt(id_vars="taxa", var_name="adesao", value_name="premio")
           .assign(adesao=lambda d: d["adesao"].str.removeprefix("adesao_").str.rstrip("%").astype(float) / 100)}
    if not dados.arquivo_bi().exists():
        warnings.warn(f"analise_capacidade_* e analise_sinistro: sem o CSV do BI do CNJ ({dados.arquivo_bi().name})")
        return out
    saldo = dados.saldo_bi(con, config()["melhorias"]["capacidade"]["ano"])
    cap = mh.capacidade(sv, saldo)
    faixas = mh.tabela_faixas(cap).reset_index()
    out["analise_capacidade_faixas"] = faixas.assign(faixa_meses=faixas["faixa_meses"].astype(str))
    cal = []
    for h in config()["melhorias"]["capacidade"]["horizontes"]:
        c = mh.calibracao(mh.capacidade(sv, saldo, h), p).reset_index()
        tot = {"faixa_deficit": "total", "obrigadas": c["obrigadas"].sum(), "com_dado_bi": c["com_dado_bi"].sum(),
               "deficit_modelo": c["deficit_modelo"].sum(), "deficit_m1": c["deficit_m1"].sum()}
        c = pd.concat([c, pd.DataFrame([tot])], ignore_index=True).assign(horizonte_meses=float(h))
        c["premio_modelo"] = [mh.mercado_por_deficit(v, p)["premio"] for v in c["deficit_modelo"]]
        c["premio_m1"] = [mh.mercado_por_deficit(v, p)["premio"] for v in c["deficit_m1"]]
        cal.append(c)
    out["analise_capacidade_calibracao"] = pd.concat(cal, ignore_index=True)
    out["analise_sinistro"] = mh.sinistro(cap, p)
    return out


def construir(con) -> dict[str, pd.DataFrame]:
    """As tabelas gold.analise_* (sem o prefixo): as seis do plano (D-043), as duas da D-044 e as das melhorias de
    confiança (D-045; as que dependem de um arquivo opcional do bronze ficam de fora sem ele)."""
    tornado, monte_carlo = tornado_e_monte_carlo(con)
    tab_grupos = grupos(con)
    return {"analise_regras": regras(con), "analise_grupos": tab_grupos,
            "analise_grupos_perfil": grupos_perfil(con, tab_grupos), "analise_clt_modelo": clt_modelo(con),
            "analise_previsao": previsao(con), "analise_tornado": tornado, "analise_monte_carlo": monte_carlo,
            "analise_sensibilidade_metodo": sensibilidade_metodo(con), **melhorias(con, monte_carlo)}
