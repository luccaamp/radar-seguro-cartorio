"""Simulador: ajuste as premissas e o cenário do STF; mercado total × seguradora hipotética, lado a lado.

Usa o mesmo motor do pipeline (src/motor.py), então o ponto de partida reproduz o cenário base do gold.
"""
import json

import pandas as pd
import streamlit as st
import yaml

from comum import (RAIZ, _br, aviso_estimativa, brl, conexao, consulta, demonstracao, md_seguro, num, pct, rodape,
                   slider_br, universo_txt, aprox)
from src import cenarios, estado
from src.model import simulador
from src.model.premissas import PremissaInvalida, com_novo_base
from src.model.rateio import METODOS
from src.motor import calcular_serventias, peso_indeterminada, premissas_nivel, resumo_mercado
from src.transform.gold import carregar_insumos

# modo demonstração (D-029): sem dados internos, recalcula a partir de gold.simulador_* (src/model/simulador.py)
DEMO = demonstracao()

st.set_page_config(page_title="Simulador", page_icon="🎛️", layout="wide")
st.title("Simulador — seguro-garantia do Prov. 227 (MG)")
aviso_estimativa()

CONFIG = RAIZ / "config"
REGRAS = yaml.safe_load((CONFIG / "regras_classificacao.yaml").read_text(encoding="utf-8"))
CENARIOS = yaml.safe_load((CONFIG / "cenarios_stf.yaml").read_text(encoding="utf-8"))
ROT_CEN = {"mantem": "Regra mantida", "suspende_8_17": "STF suspende arts. 8º a 17", "parcial": "Decisão parcial"}
ROTULO_RESULTADO = "Resultado técnico (antes de impostos, resseguro e capital)"
ROT_MET = {"por_empregados_cnj": "Por empregados (CNJ) — padrão", "arrecadacao": "Por arrecadação",
           "uniforme": "Uniforme", "peso_por_atribuicao": "Por atribuição"}


@st.cache_resource
def insumos():
    return carregar_insumos(conexao())


@st.cache_data
def calcular(regra: str, metodo: str, ajustes_json: str, versao: int) -> pd.DataFrame:
    semente, _ = estado.premissas_vigentes(conexao())
    lim = REGRAS["versoes"][regra]["limites"]
    p = premissas_nivel(semente, "base", peso_indeterminada(insumos().serventias, lim), json.loads(ajustes_json))
    return calcular_serventias(insumos(), p, lim, metodo, limites_faixa=LIM_BASE)[0]


LIM_BASE = REGRAS["versoes"][REGRAS["versao_base"]]["limites"]  # classe das faixas de déficit (D-019)
semente, versao = estado.premissas_vigentes(conexao())


def peso_indet(regra: str) -> float:
    """Peso da classe indeterminada no nível base: calculado das serventias (completo) ou lido do gold (demonstração,
    mesmo valor, gravado pela carga em gold.execucao)."""
    if DEMO:
        return float(consulta("SELECT peso_classe_indeterminada_base FROM gold.execucao WHERE regra_classe = ?",
                              [regra]).iloc[0, 0])
    return peso_indeterminada(insumos().serventias, REGRAS["versoes"][regra]["limites"])


pb = premissas_nivel(semente, "base", peso_indet(REGRAS["versao_base"]))
P = semente["premissas"]
VARIANTES = consulta("SELECT * FROM gold.simulador_variantes") if DEMO else None


def grade(coluna: str) -> list:
    """Pontos da grade de um controle do passivo (modo demonstração)."""
    return sorted(VARIANTES[coluna].unique().tolist())


def faixa_de(nome, chave=None):
    v = P[nome]["valores"]
    return v[chave] if chave else v


# ------------------------------------------------------------------ controles
st.header("Cenário")
c1, c2, c3 = st.columns([2, 1.3, 2])
cenario = c1.radio("Cenário do STF (ADI 8015)", list(CENARIOS["cenarios"]), format_func=ROT_CEN.get, horizontal=True,
                   help="\n\n".join(f"**{ROT_CEN[k]}**: {v['descricao']}" for k, v in CENARIOS["cenarios"].items()))
regra = c2.radio("Regra da Classe 1", ["v2", "v1"], horizontal=True,
                 format_func=lambda r: {"v2": "R$ 300 mil (Prov. 243)", "v1": "R$ 100 mil (213 original)"}[r])
metodo = c3.selectbox("Rateio do passivo entre serventias", METODOS, format_func=ROT_MET.get)
fracao_parcial = None
fracao_semente = float(CENARIOS["cenarios"]["parcial"]["ajustes"]["fracao_exigencia_garantia"])
if cenario == "parcial":
    fracao_parcial = c1.slider("Parte do valor hoje exigido que continua exigida", 0, 100, int(round(100 * fracao_semente)),
                               5, format="%d%%", help="fonte: suposição (valor inicial 50%)") / 100
x_parcial = pct(fracao_parcial if fracao_parcial is not None else fracao_semente, 0)
c1.caption(md_seguro(f"**Decisão parcial:** cenário hipotético: o STF suspende parte da obrigação, e só {x_parcial} do valor "
              f"hoje exigido continua exigido. {x_parcial} é suposição sem base em decisão real; até 17/10/2026 não "
              "havia liminar."))

aj: dict = {}
with st.expander("Premissas do déficit e da escolha da garantia (suposições, D-016)", expanded=True):
    a, b, c = st.columns(3)
    def pct_slider(col, rotulo, valor, maximo=100, **kw):
        """Controle em % inteiro; devolve fração."""
        return col.slider(rotulo, 0, maximo, int(round(100 * valor)), 5, format="%d%%", **kw) / 100

    def txt_faixa(nome, classe):
        v = faixa_de(nome, classe)
        return f"Faixa da semente: {pct(v['min'], 0)} a {pct(v['max'], 0)} (fonte: suposição)"

    pd2 = pct_slider(a, "Prob. de déficit — Classe 2", pb["prob_deficit"]["classe_2"], help=txt_faixa("prob_deficit", "classe_2"))
    pd3 = pct_slider(a, "Prob. de déficit — Classe 3", pb["prob_deficit"]["classe_3"], help=txt_faixa("prob_deficit", "classe_3"))
    pc2 = pct_slider(b, "Parte descoberta — Classe 2", pb["pct_descoberto"]["classe_2"], help=txt_faixa("pct_descoberto", "classe_2"))
    pc3 = pct_slider(b, "Parte descoberta — Classe 3", pb["pct_descoberto"]["classe_3"], help=txt_faixa("pct_descoberto", "classe_3"))
    seg = pct_slider(c, "Escolhe seguro-garantia", pb["escolha_garantia"]["seguro"])
    resto = int(round(100 * (1 - seg)))
    fia = pct_slider(c, "Escolhe fiança bancária (S1/S2)", min(pb["escolha_garantia"]["fianca"], 1 - seg), maximo=resto) \
        if resto > 0 else 0.0
    c.caption(f"Regulariza com bens próprios: **{pct(1 - seg - fia, 0)}** (o restante; as três somam 100%).")
    aj["prob_deficit"] = {"classe_2": pd2, "classe_3": pd3}
    aj["pct_descoberto"] = {"classe_2": pc2, "classe_3": pc3}
    aj["escolha_garantia"] = {"bens_proprios": round(1 - seg - fia, 10), "fianca": fia, "seguro": seg}

with st.expander("Premissas da receita do seguro", expanded=True):
    a, b, c = st.columns(3)
    aj["taxa_seguro_anual"] = slider_br(a, "Taxa anual (% da importância segurada)", 0.5, 5.0, 0.1,
                                        100 * pb["taxa_seguro_anual"],
                                        help="Faixa da semente: 1,0% a 3,5% (fonte: suposição)") / 100
    aj["market_share_hipotetico"] = slider_br(
        a, "Market share da seguradora hipotética", 1.0, 30.0, 0.1, 100 * pb["market_share_hipotetico"],
        help="Semente (SES, garantia, 12 meses até ago/2026): mínimo 3,9% = 10ª seguradora; base 5,2% = 5ª; "
             "**máximo 16,4% = fatia do líder atual do mercado**.") / 100
    aj["sinistralidade"] = slider_br(b, "Sinistralidade da SES (sinistro ÷ prêmio ganho), aplicada ao prêmio emitido "
                                     "do ano — aproximação", 0.0, 100.0, 0.1, 100 * pb["sinistralidade"],
                                     help="SES: mín 1,7% (menor janela anual do ramo 0775), base 10,9% (ramo 0775, "
                                         "setor público, art. 13, § 1º), máx 73,9% (ramo 0776, setor privado)") / 100
    aj["comissao"] = slider_br(b, "Despesa de comercialização (sobre o prêmio)", 0.0, 40.0, 0.1, 100 * pb["comissao"],
                               help="SES: 14,3% a 21,9%; base 17,1% (ramo 0775)") / 100
    aj["despesa_administrativa"] = slider_br(c, "Despesa administrativa (sobre o prêmio)", 0.0, 30.0, 0.5,
                                             100 * pb["despesa_administrativa"],
                                             help="Faixa da semente: 5% a 12% (fonte: suposição)") / 100

with st.expander("Premissas do passivo (art. 5º do Prov. 227)", expanded=DEMO):
    if DEMO:
        st.caption("Modo demonstração: o passivo vem de uma grade pré-calculada. Cada controle oferece só os pontos "
                   "da grade, e só **uma** premissa do passivo pode sair do valor base por vez (regra e rateio "
                   "combinam com qualquer uma). O resto fica disponível com os dados completos.")
    a, b, c = st.columns(3)
    if DEMO:
        aj["fap"] = a.select_slider("FAP (multiplicador do RAT)", grade("fap"), value=float(pb["fap"]),
                                    format_func=lambda v: _br(v, 2), help="Decreto 3.048, art. 202-A: entre 0,5 e 2,0")
        aj["fracao_ferias_vencidas_pendentes"] = a.select_slider(
            "Férias vencidas ainda não gozadas (períodos)", grade("fracao_ferias_vencidas_pendentes"),
            value=float(pb["fracao_ferias_vencidas_pendentes"]), format_func=lambda v: _br(v, 2),
            help="Suposição aprovada na D-017: mín 0, base 0,5, máx 1")
    else:
        aj["fap"] = slider_br(a, "FAP (multiplicador do RAT)", 0.5, 2.0, 0.1, float(pb["fap"]), casas=2, sufixo="",
                              help="Decreto 3.048, art. 202-A: entre 0,5 e 2,0")
        aj["fracao_ferias_vencidas_pendentes"] = slider_br(a, "Férias vencidas ainda não gozadas (períodos)", 0.0, 1.0,
                                                           0.1, float(pb["fracao_ferias_vencidas_pendentes"]), casas=2,
                                                           sufixo="",
                                                           help="Suposição aprovada na D-017: mín 0, base 0,5, máx 1")
    inss_aviso = b.checkbox("INSS sobre o aviso prévio indenizado", value=False,
                            help="Base: não incide (STJ, Tema 478). Marcado = cenário máximo.")
    aj["incidencias"] = {**pb["incidencias"],
                         "aviso_previo_indenizado": {"fgts": True, "inss": inss_aviso}}
    aj["limiar_vinculos_distribuicao_municipal"] = b.select_slider(
        "Vínculos mínimos para usar a distribuição do município",
        grade("limiar_vinculos_distribuicao_municipal") if DEMO else [10, 20, 30],
        value=int(pb["limiar_vinculos_distribuicao_municipal"]))
    aj["base_remuneracao_rais"] = c.radio("Base de remuneração (art. 6º)", ["dezembro", "media_anual"],
                                          format_func={"dezembro": "Remuneração de dezembro",
                                                       "media_anual": "Média anual"}.get)

# ------------------------------------------------------------------ cálculo
def totais_demo(regra: str, metodo: str) -> dict | None:
    """Totais da variante pré-calculada que corresponde aos controles do passivo; None se a combinação não está na
    grade (mais de uma premissa do passivo fora do valor base)."""
    valores = {"fap": aj["fap"], "fracao_ferias_vencidas_pendentes": aj["fracao_ferias_vencidas_pendentes"],
               "inss_aviso_previo": inss_aviso,
               "limiar_vinculos_distribuicao_municipal": aj["limiar_vinculos_distribuicao_municipal"],
               "base_remuneracao_rais": aj["base_remuneracao_rais"]}
    v = VARIANTES[(VARIANTES["regra_classe"] == regra) & (VARIANTES["metodo_rateio"] == metodo)]
    for k, x in valores.items():
        v = v[v[k] == x]
    if v.empty:
        return None
    linha = v.iloc[0]
    t = {k: linha[k] for k in ("n_serventias_ativas", "clt", "passivo_todas", "n_universo", "n_indeterminadas_universo",
                               "passivo_universo")}
    faixas = consulta("SELECT faixa, peso_com_passivo, passivo_ponderado FROM gold.simulador_base_classe "
                      "WHERE variante_id = ?", [int(linha["variante_id"])])
    for f in faixas.itertuples():
        t[f"peso_com_passivo_{f.faixa}"] = f.peso_com_passivo
        t[f"passivo_ponderado_{f.faixa}"] = f.passivo_ponderado
    return t


try:
    p = premissas_nivel(semente, "base", peso_indet(regra), aj)
    extra = {"fracao_exigencia_garantia": fracao_parcial} if fracao_parcial is not None else None
    if DEMO:
        t = totais_demo(regra, metodo)
        if t is None:
            st.warning("Esta combinação muda mais de uma premissa do passivo ao mesmo tempo: no modo demonstração, só "
                       "uma por vez (a grade pré-calculada). Volte as outras ao valor base. A combinação livre fica "
                       "disponível com os dados completos (veja 'Como rodar' no README).")
            st.stop()
        r = simulador.resumo_por_totais(t, p, CENARIOS, cenario, extra)
    else:
        serv = calcular(regra, metodo, json.dumps(aj, sort_keys=True), versao)
        r = resumo_mercado(serv, p, CENARIOS, cenario, extra)
except PremissaInvalida as e:
    st.error(f"Premissa inválida: {e}")
    st.stop()

ref = consulta("SELECT * FROM gold.fato_mercado_uf WHERE nivel = 'base' AND regra_classe = 'v2' AND cenario_stf = 'mantem'"
               ).iloc[0]

def delta(atual: float, referencia: float, fmt=brl, minimo: float = 0.5) -> str | None:
    """Diferença para o cenário base do painel; nada quando não há diferença relevante."""
    d = atual - referencia
    return None if abs(d) < minimo else ("+" if d > 0 else "") + fmt(d)


st.header("Resultado anual — MG")
st.caption(md_seguro("As setas comparam com o cenário base do painel (premissas vigentes, regra mantida, Classe 1 até R$ 300 mil)."))
k1, k2, k3, k4 = st.columns(4)
k1.metric("Obrigadas (universo)", aprox(r["n_universo"]), delta=delta(r["n_universo"], ref["n_universo"], num),
          delta_color="off", help=universo_txt(r["n_universo"], r["n_indeterminadas_universo"]))
k2.metric("Passivo dos obrigados", brl(r["passivo_universo"]), delta=delta(r["passivo_universo"], ref["passivo_universo"]),
          delta_color="off")
k3.metric("Com déficit (esperado)", aprox(r["n_deficit"]),   # rótulo curto: o longo era cortado em 1280 px
          delta=delta(r["n_deficit"], ref["n_deficit"], num), delta_color="off",
          help="Serventias com déficit, valor esperado: soma das probabilidades de déficit das serventias do universo (suposição, D-016).")
k4.metric("Déficit de cobertura", brl(r["valor_descoberto"]), delta=delta(r["valor_descoberto"], ref["valor_descoberto"]),
          delta_color="off")

# para custos, subir é ruim: cor invertida
LINHAS = [("importancia_segurada", "Importância segurada", "normal"), ("premio_emitido", "Prêmio emitido", "normal"),
          ("sinistro_esperado", "Sinistro esperado", "inverse"), ("comissao", "Despesa de comercialização", "inverse"),
          ("despesa_administrativa", "Despesa administrativa", "inverse"),
          ("resultado_tecnico", ROTULO_RESULTADO, "normal")]
st.write("")   # espaço entre o bloco de cima e os títulos das duas colunas (1.5)
st.divider()
m, s = st.columns(2)
for coluna, prefixo, titulo in ((m, "mercado", "Mercado total"),
                                (s, "seguradora", f"Seguradora hipotética ({pct(p['market_share_hipotetico'])} de share)")):
    with coluna:
        st.markdown(f"### {titulo}")   # h3 sob o h2 da seção (ordem dos títulos, acessibilidade)
        for chave, rot, cor in LINHAS:
            st.metric(rot, brl(r[f"{prefixo}_{chave}"]), delta=delta(r[f"{prefixo}_{chave}"], ref[f"{prefixo}_{chave}"]),
                      delta_color=cor)
        premio = r[f"{prefixo}_premio_emitido"]
        if premio > 0:
            st.caption(f"Margem de {pct(r[f'{prefixo}_resultado_tecnico'] / premio, 0)} não é lucro esperado: ver "
                       "limitações do modelo de sinistro (Etapa 2).")

teto = r["passivo_universo"] * p["taxa_seguro_anual"]
st.metric("Teto teórico do mercado (prêmio anual)", brl(teto),
          help="Não depende das suposições de déficit nem da escolha da garantia.")
st.caption(md_seguro(f"**Teto teórico = passivo dos obrigados × taxa** = {brl(r['passivo_universo'])} × "
              f"{pct(p['taxa_seguro_anual'])} = {brl(teto)} por ano. Supõe que todos os obrigados têm déficit igual ao "
              "passivo e todos escolhem seguro."))

with st.expander("Tabela por UF"):
    st.dataframe(pd.DataFrame([{"UF": "MG", "Obrigadas (≈, valor esperado)": num(r["n_universo"]),
                                "Déficit": brl(r["valor_descoberto"]),
                                "IS do mercado": brl(r["mercado_importancia_segurada"]),
                                "Prêmio do mercado": brl(r["mercado_premio_emitido"]),
                                "Prêmio da seguradora": brl(r["seguradora_premio_emitido"]),
                                f"{ROTULO_RESULTADO} da seguradora": brl(r["seguradora_resultado_tecnico"])}]),
                 hide_index=True, width="stretch")
    st.caption("Fase 1: só MG. As demais UFs entram na Fase 2.")
rodape(["cnj_serventias", "cnj_colaboradores", "cnj_arrecadacao", "rais_vinculos", "susep_ses_garantia"],
       f"Cenário: {ROT_CEN[cenario]}; regra {regra}; rateio {ROT_MET[metodo]}.", taxa=True)

# ------------------------------------------------------------------ salvar
st.header("Salvar cenário")
if DEMO:
    st.caption("Desativado no modo demonstração. Com os dados completos (ou recalculando com os dados públicos), os "
               "cenários ficam salvos em data/painel_estado.json, fora do banco.")
nome = st.text_input("Nome do cenário", placeholder="ex.: taxa 2,5% e share 10%", disabled=DEMO)
if st.button("Salvar", type="primary", disabled=DEMO or not nome):
    # D-034: o cenário vai para um arquivo próprio; o banco do pipeline e as versões de premissas não mudam
    _, diff = com_novo_base(semente, aj)
    cid = cenarios.salvar({
        "nome": nome, "versao_premissas": versao, "cenario_stf": cenario, "regra_classe": regra,
        "metodo_rateio": metodo, "nivel": "base", "premissas_alteradas": diff, "resultado": r,
        "ajustes": {**aj, **({"fracao_exigencia_garantia": fracao_parcial} if fracao_parcial else {})}})
    st.success(f"Cenário #{cid} salvo sobre as premissas versão {versao}" +
               (f" ({len(diff)} premissa(s) alterada(s))." if diff else " (sem mudança de premissa)."))

salvos, aviso_salvos = cenarios.ler()
if aviso_salvos:
    st.warning(aviso_salvos)
if salvos:
    tabela = pd.DataFrame([{**c, "premissas_alteradas": len(c.get("premissas_alteradas") or {})} for c in salvos])
    colunas = ["id", "nome", "criado_em", "versao_premissas", "premissas_alteradas", "cenario_stf", "regra_classe",
               "metodo_rateio"]
    st.dataframe(tabela.reindex(columns=colunas).sort_values("id", ascending=False), hide_index=True, width="stretch")
