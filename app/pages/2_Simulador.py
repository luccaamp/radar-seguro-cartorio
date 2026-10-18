"""Simulador: ajuste as premissas e o cenário do STF; mercado total × seguradora hipotética, lado a lado.

Usa o mesmo motor do pipeline (src/motor.py), então o ponto de partida reproduz o cenário base do gold.
"""
import json

import pandas as pd
import streamlit as st
import yaml

from comum import RAIZ, aviso_estimativa, brl, conexao, consulta, md, num, pct, rodape
from src import estado
from src.model.premissas import PremissaInvalida, com_novo_base
from src.model.rateio import METODOS
from src.motor import calcular_serventias, peso_indeterminada, premissas_nivel, resumo_mercado
from src.transform.gold import carregar_insumos

st.set_page_config(page_title="Simulador", page_icon="🎛️", layout="wide")
st.title("Simulador — seguro-garantia do Prov. 227 (MG)")
aviso_estimativa()

CONFIG = RAIZ / "config"
REGRAS = yaml.safe_load((CONFIG / "regras_classificacao.yaml").read_text(encoding="utf-8"))
CENARIOS = yaml.safe_load((CONFIG / "cenarios_stf.yaml").read_text(encoding="utf-8"))
ROT_CEN = {"mantem": "Regra mantida", "suspende_8_17": "STF suspende arts. 8º a 17", "parcial": "Decisão parcial"}
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
    return calcular_serventias(insumos(), p, lim, metodo)[0]


semente, versao = estado.premissas_vigentes(conexao())
lim_v2 = REGRAS["versoes"]["v2"]["limites"]
pb = premissas_nivel(semente, "base", peso_indeterminada(insumos().serventias, lim_v2))
P = semente["premissas"]


def faixa_de(nome, chave=None):
    v = P[nome]["valores"]
    return v[chave] if chave else v


# ------------------------------------------------------------------ controles
st.subheader("Cenário")
c1, c2, c3 = st.columns([2, 1.3, 2])
cenario = c1.radio("Cenário do STF (ADI 8015)", list(CENARIOS["cenarios"]), format_func=ROT_CEN.get, horizontal=True,
                   help="\n\n".join(f"**{ROT_CEN[k]}**: {v['descricao']}" for k, v in CENARIOS["cenarios"].items()))
regra = c2.radio("Regra da Classe 1", ["v2", "v1"], horizontal=True,
                 format_func=lambda r: {"v2": "R$ 300 mil (Prov. 243)", "v1": "R$ 100 mil (213 original)"}[r])
metodo = c3.selectbox("Rateio do passivo entre serventias", METODOS, format_func=ROT_MET.get)
fracao_parcial = None
if cenario == "parcial":
    fracao_parcial = st.slider("Fração dos delegatários com déficit que continua obrigada a apresentar garantia",
                               0.0, 1.0, float(CENARIOS["cenarios"]["parcial"]["ajustes"]["fracao_exigencia_garantia"]),
                               0.05, help="fonte: suposição (valor inicial 50%)")

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
    aj["taxa_seguro_anual"] = a.slider("Taxa anual (% da importância segurada)", 0.5, 5.0,
                                       100 * pb["taxa_seguro_anual"], 0.1, format="%.1f%%",
                                       help="Faixa da semente: 1,0% a 3,5% (fonte: suposição)") / 100
    aj["market_share_hipotetico"] = a.slider(
        "Market share da seguradora hipotética", 1.0, 30.0, 100 * pb["market_share_hipotetico"], 0.1, format="%.1f%%",
        help="Semente (SES, garantia, 12 meses até ago/2026): mínimo 3,9% = 10ª seguradora; base 5,2% = 5ª; "
             "**máximo 16,4% = fatia do líder atual do mercado**.") / 100
    aj["sinistralidade"] = b.slider("Sinistralidade (sobre o prêmio ganho)", 0.0, 100.0, 100 * pb["sinistralidade"], 0.1,
                                    format="%.1f%%",
                                    help="SES: mín 1,7% (menor janela anual do ramo 0775), base 10,9% (ramo 0775, "
                                         "setor público, art. 13, § 1º), máx 73,9% (ramo 0776, setor privado)") / 100
    aj["comissao"] = b.slider("Despesa de comercialização (sobre o prêmio)", 0.0, 40.0, 100 * pb["comissao"], 0.1,
                              format="%.1f%%",
                              help="SES: 14,3% a 21,9%; base 17,1% (ramo 0775)") / 100
    aj["despesa_administrativa"] = c.slider("Despesa administrativa (sobre o prêmio)", 0.0, 30.0,
                                            100 * pb["despesa_administrativa"], 0.5, format="%.1f%%",
                                            help="Faixa da semente: 5% a 12% (fonte: suposição)") / 100

with st.expander("Premissas do passivo (art. 5º do Prov. 227)"):
    a, b, c = st.columns(3)
    aj["fap"] = a.slider("FAP (multiplicador do RAT)", 0.5, 2.0, float(pb["fap"]), 0.1,
                         help="Decreto 3.048, art. 202-A: entre 0,5 e 2,0")
    aj["fracao_ferias_vencidas_pendentes"] = a.slider("Férias vencidas ainda não gozadas (períodos)", 0.0, 1.0,
                                                      float(pb["fracao_ferias_vencidas_pendentes"]), 0.1)
    inss_aviso = b.checkbox("INSS sobre o aviso prévio indenizado", value=False,
                            help="Base: não incide (STJ, Tema 478). Marcado = cenário máximo.")
    aj["incidencias"] = {**pb["incidencias"],
                         "aviso_previo_indenizado": {"fgts": True, "inss": inss_aviso}}
    aj["limiar_vinculos_distribuicao_municipal"] = b.select_slider(
        "Vínculos mínimos para usar a distribuição do município", [10, 20, 30],
        value=int(pb["limiar_vinculos_distribuicao_municipal"]))
    aj["base_remuneracao_rais"] = c.radio("Base de remuneração (art. 6º)", ["dezembro", "media_anual"],
                                          format_func={"dezembro": "Remuneração de dezembro",
                                                       "media_anual": "Média anual"}.get)

# ------------------------------------------------------------------ cálculo
try:
    serv = calcular(regra, metodo, json.dumps(aj, sort_keys=True), versao)
    lim = REGRAS["versoes"][regra]["limites"]
    p = premissas_nivel(semente, "base", peso_indeterminada(insumos().serventias, lim), aj)
    extra = {"fracao_exigencia_garantia": fracao_parcial} if fracao_parcial is not None else None
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


st.subheader("Resultado anual — MG")
st.caption(md("As setas comparam com o cenário base do painel (premissas vigentes, regra mantida, Classe 1 até R$ 300 mil)."))
k1, k2, k3, k4 = st.columns(4)
k1.metric("Serventias no universo", num(r["n_universo"]), delta=delta(r["n_universo"], ref["n_universo"], num),
          delta_color="off")
k2.metric("Passivo no universo", brl(r["passivo_universo"]), delta=delta(r["passivo_universo"], ref["passivo_universo"]),
          delta_color="off")
k3.metric("Serventias com déficit (esperado)", num(r["n_deficit"]), delta=delta(r["n_deficit"], ref["n_deficit"], num),
          delta_color="off")
k4.metric("Déficit de cobertura", brl(r["valor_descoberto"]), delta=delta(r["valor_descoberto"], ref["valor_descoberto"]),
          delta_color="off")

# para custos, subir é ruim: cor invertida
LINHAS = [("importancia_segurada", "Importância segurada", "normal"), ("premio_emitido", "Prêmio emitido", "normal"),
          ("sinistro_esperado", "Sinistro esperado", "inverse"), ("comissao", "Despesa de comercialização", "inverse"),
          ("despesa_administrativa", "Despesa administrativa", "inverse"),
          ("resultado_tecnico", "Resultado técnico", "normal")]
m, s = st.columns(2)
for coluna, prefixo, titulo in ((m, "mercado", "Mercado total"),
                                (s, "seguradora", f"Seguradora hipotética ({pct(p['market_share_hipotetico'])} de share)")):
    with coluna:
        st.markdown(f"#### {titulo}")
        for chave, rot, cor in LINHAS:
            st.metric(rot, brl(r[f"{prefixo}_{chave}"]), delta=delta(r[f"{prefixo}_{chave}"], ref[f"{prefixo}_{chave}"]),
                      delta_color=cor)

with st.expander("Tabela por UF"):
    st.dataframe(pd.DataFrame([{"UF": "MG", "Serventias no universo": round(r["n_universo"], 1),
                                "Déficit (R$)": round(r["valor_descoberto"]),
                                "IS mercado (R$)": round(r["mercado_importancia_segurada"]),
                                "Prêmio mercado (R$)": round(r["mercado_premio_emitido"]),
                                "Prêmio seguradora (R$)": round(r["seguradora_premio_emitido"]),
                                "Resultado técnico seguradora (R$)": round(r["seguradora_resultado_tecnico"])}]),
                 hide_index=True, width="stretch")
    st.caption("Fase 1: só MG. As demais UFs entram na Fase 2.")
rodape(["cnj_serventias", "cnj_colaboradores", "cnj_arrecadacao", "rais_vinculos", "ibge_inpc", "susep_ses_garantia"],
       f"Cenário: {ROT_CEN[cenario]}; regra {regra}; rateio {ROT_MET[metodo]}.")

# ------------------------------------------------------------------ salvar
st.subheader("Salvar cenário")
nome = st.text_input("Nome do cenário", placeholder="ex.: taxa 2,5% e share 10%")
if st.button("Salvar", type="primary", disabled=not nome):
    con = conexao()
    novo, diff = com_novo_base(semente, aj)
    v = estado.salvar_versao(con, novo, diff, "autor (simulador)", f"simulador: {nome}") if diff else versao
    cid = estado.salvar_cenario(con, nome, v, cenario, regra, metodo, "base",
                                {**aj, **({"fracao_exigencia_garantia": fracao_parcial} if fracao_parcial else {})}, r)
    calcular.clear()
    st.success(f"Cenário #{cid} salvo com as premissas versão {v}" +
               (f" (nova versão; {len(diff)} premissa(s) alterada(s))." if diff else " (sem mudança de premissa)."))

salvos = consulta("SELECT id, nome, criado_em, versao_premissas, cenario_stf, regra_classe, metodo_rateio "
                  "FROM estado.cenarios_salvos ORDER BY id DESC")
if len(salvos):
    st.dataframe(salvos, hide_index=True, width="stretch")
