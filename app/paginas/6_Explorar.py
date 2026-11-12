"""Explorar: simule você mesmo (D-077). O Simulador, separado da história do painel.

O leitor muda as suposições (taxa, adesão ao seguro, cenário do STF e, no grupo avançado, déficit, passivo e
despesas) e vê o prêmio, a escada, a faixa por sorteio e o tornado recalculados na hora. Usa o mesmo motor do
pipeline (src/motor.py); com os controles no padrão, os números são os do painel. O tornado e a faixa por sorteio
saem de src/painel/explorar.py, ao redor dos valores escolhidos.
"""
import json

import pandas as pd
import streamlit as st
import yaml

from comum import (RAIZ, _br, aprox, avisar_se_preliminar, aviso_estimativa, brl, conexao, consulta, demonstracao,
                   do_escopo, md_seguro, num, pagina, pct, rodape, uf_atual, universo_txt)
from src import cenarios, estado
from src.analise.sensibilidade import faixas_suposicoes
from src.model import simulador
from src.model.premissas import PremissaInvalida, com_novo_base
from src.model.rateio import METODOS
from src.motor import calcular_serventias, peso_indeterminada, premissas_nivel, resumo_mercado
from src.painel import explorar, graficos, ui
from src.transform.gold import carregar_insumos, insumos_da_uf

# modo demonstração (D-029): sem dados internos, recalcula a partir de gold.simulador_* (src/model/simulador.py)
DEMO = demonstracao()

pagina("Explorar · Simule você mesmo", "🎛️", f"E se as suposições fossem outras {do_escopo(uf_atual())}?",
       "Mude a taxa do seguro, a adesão e o cenário do STF e veja o prêmio, a faixa provável e o que mais pesa "
       "mudarem na hora. Com os controles no padrão, os números são os do painel.", sobre="Explorar", seletor="uf")
UF = uf_atual()   # um estado por vez (D-088)
aviso_estimativa()
avisar_se_preliminar(UF)

CONFIG = RAIZ / "config"
REGRAS = yaml.safe_load((CONFIG / "regras_classificacao.yaml").read_text(encoding="utf-8"))
CENARIOS = yaml.safe_load((CONFIG / "cenarios_stf.yaml").read_text(encoding="utf-8"))
_PAINEL_CFG = yaml.safe_load((CONFIG / "painel.yaml").read_text(encoding="utf-8"))
PAINEL, PROJ_CFG = _PAINEL_CFG["explorar"], _PAINEL_CFG["projecao"]
ROT_LIM = {PROJ_CFG["leitura_limite_principal"]: "Fixo em R$ 300 mil (regra em vigor)",
           PROJ_CFG["leitura_limite_comparacao"]: "Corrigido pelo IPCA (comparação)"}
LIM_CURTO = {PROJ_CFG["leitura_limite_principal"]: "limite fixo em R$ 300 mil",
             PROJ_CFG["leitura_limite_comparacao"]: "limite corrigido pelo IPCA"}
ROT_CEN = {"mantem": "Regra mantida", "suspende_8_17": "STF suspende arts. 8º a 17", "parcial": "Decisão parcial"}
ROTULO_RESULTADO = "Resultado técnico (antes de impostos, resseguro e capital)"
ROT_MET = {"por_empregados_cnj": "Por empregados (CNJ) — padrão", "arrecadacao": "Por arrecadação",
           "uniforme": "Uniforme", "peso_por_atribuicao": "Por atribuição"}


@st.cache_resource
def _insumos_todos():
    return carregar_insumos(conexao())


@st.cache_resource
def insumos(uf: str):
    """Os insumos do modelo da UF (as serventias e os vínculos da RAIS dela; D-088). Cache por UF."""
    return insumos_da_uf(_insumos_todos(), uf)


@st.cache_data
def calcular(regra: str, metodo: str, ajustes_json: str, versao: int) -> pd.DataFrame:
    semente, _ = estado.premissas_vigentes(conexao())
    lim = REGRAS["versoes"][regra]["limites"]
    p = premissas_nivel(semente, "base", peso_indeterminada(insumos(UF).serventias, lim), json.loads(ajustes_json))
    return calcular_serventias(insumos(UF), p, lim, metodo, limites_faixa=LIM_BASE)[0]


LIM_BASE = REGRAS["versoes"][REGRAS["versao_base"]]["limites"]  # classe das faixas de déficit (D-019)
semente, versao = estado.premissas_vigentes(conexao())


def peso_indet(regra: str) -> float:
    """Peso da classe indeterminada no nível base: calculado das serventias (completo) ou lido do gold (demonstração,
    mesmo valor, gravado pela carga em gold.execucao)."""
    if DEMO:
        return float(consulta("SELECT peso_classe_indeterminada_base FROM gold.execucao WHERE regra_classe = ? "
                              "AND uf = ?", [regra, UF]).iloc[0, 0])
    return peso_indeterminada(insumos(UF).serventias, REGRAS["versoes"][regra]["limites"])


pb = premissas_nivel(semente, "base", peso_indet(REGRAS["versao_base"]))
P = semente["premissas"]
VARIANTES = consulta("SELECT * FROM gold.simulador_variantes WHERE uf = ?", [UF]) if DEMO else None
# projeção 2026–27 (notebook 07): os totais por faixa de déficit só existem nas cargas que os gravam
PREV = consulta("SELECT * FROM gold.analise_previsao WHERE bloco = 'mercado' AND uf = ?", [UF])
ANOS_PROJ = sorted({int(a) for a in PREV["periodo"]
                    if explorar.totais_projetados(PREV, {}, int(a), PROJ_CFG["leitura_limite_principal"],
                                                  PROJ_CFG["variante_principal"]) is not None})


def grade(coluna: str) -> list:
    """Pontos da grade de um controle do passivo (modo demonstração)."""
    return sorted(VARIANTES[coluna].unique().tolist())


def faixa_de(nome, chave=None):
    v = P[nome]["valores"]
    return v[chave] if chave else v


# ------------------------------------------------------------------ estado dos controles e atalhos
def opcoes(vmin: float, vmax: float, passo: float) -> list[float]:
    n = int(round((vmax - vmin) / passo))
    return [round(vmin + i * passo, 10) for i in range(n + 1)]


def mais_perto(lista: list, valor: float) -> float:
    return min(lista, key=lambda o: abs(o - valor))


# controles com chave: o padrão entra no session_state uma vez, e os atalhos só trocam esse estado
OPC_TAXA = opcoes(0.5, 5.0, 0.1)
PADRAO = {"x_taxa": mais_perto(OPC_TAXA, 100 * pb["taxa_seguro_anual"]),
          "x_seguro": int(round(100 * pb["escolha_garantia"]["seguro"])),
          "x_fianca": int(round(100 * pb["escolha_garantia"]["fianca"])),
          "x_cenario": "mantem"}
for k, v in PADRAO.items():
    st.session_state.setdefault(k, v)


def aplicar_atalho(ajustes: dict) -> None:
    """Volta todos os controles ao padrão e aplica o atalho (taxa em %, seguro em %, cenário)."""
    for k in [k for k in st.session_state if str(k).startswith("x_")]:
        del st.session_state[k]
    st.session_state.update(PADRAO)
    if "taxa" in ajustes:
        st.session_state["x_taxa"] = mais_perto(OPC_TAXA, float(ajustes["taxa"]))
    if "seguro" in ajustes:
        st.session_state["x_seguro"] = int(ajustes["seguro"])
        st.session_state["x_fianca"] = min(st.session_state["x_fianca"], 100 - int(ajustes["seguro"]))
    if "cenario" in ajustes:
        st.session_state["x_cenario"] = ajustes["cenario"]


st.markdown("## Comece por uma pergunta")   # h2 logo depois do h1 (ordem dos títulos, acessibilidade)
botoes = [(a["rotulo"], a["ajustes"], "secondary") for a in PAINEL["atalhos"]]
botoes.append(("Voltar ao cenário base", {}, "tertiary"))
for i in range(0, len(botoes), 2):   # duas colunas: o texto da pergunta cabe inteiro (em 4 colunas era cortado)
    for col, (rotulo, ajustes, tipo) in zip(st.columns(2), botoes[i:i + 2]):
        col.button(rotulo, on_click=aplicar_atalho, args=(ajustes,), width="stretch", type=tipo)

# ------------------------------------------------------------------ controles
aj: dict = {}
st.markdown("## Ano")
c1, c2 = st.columns([1.4, 2])
ano = c1.radio("Mercado de", ["hoje", *ANOS_PROJ], horizontal=True, key="x_ano",
               format_func=lambda a: "Hoje (base do painel)" if a == "hoje" else f"{a} (projeção)",
               help="Hoje: a classe pela receita de 2025, como no resto do painel. Projeção: a classe pela receita "
                    "projetada de cada cartório (notebook 07, valor central), com o passivo de 2025."
                    + ("" if ANOS_PROJ else " A carga atual não gravou os totais da projeção; os anos projetados "
                                            "aparecem depois da próxima carga."))
proj = ano != "hoje"
limite_proj = None
if proj:
    limite_proj = c2.radio("Limite da Classe 1 no ano projetado", list(ROT_LIM), format_func=ROT_LIM.get,
                           horizontal=True, key="x_limite",
                           help=md_seguro("Fixo: os R$ 300 mil do Prov. 243, a regra em vigor (D-049). Corrigido: "
                                          "o limite corrigido pelo IPCA recente, como comparação (o Prov. 243 não "
                                          "nomeia índice)."))
    c2.caption("Na projeção, o passivo, a regra de classe e o rateio ficam os do cenário base (a projeção foi "
               "calculada com eles); as suposições do prêmio continuam livres.")

st.markdown("## Cenário e mercado")
c1, c2, c3 = st.columns([1.4, 1, 1])
cenario = c1.radio("Cenário do STF (ADI 8015)", list(CENARIOS["cenarios"]), format_func=ROT_CEN.get, horizontal=True,
                   key="x_cenario",
                   help="\n\n".join(f"**{ROT_CEN[k]}**: {v['descricao']}" for k, v in CENARIOS["cenarios"].items()))
fracao_parcial = None
fracao_semente = float(CENARIOS["cenarios"]["parcial"]["ajustes"]["fracao_exigencia_garantia"])
if cenario == "parcial":
    fracao_parcial = c1.slider("Parte do valor hoje exigido que continua exigida", 0, 100,
                               int(round(100 * fracao_semente)), 5, format="%d%%",
                               help="fonte: suposição (valor inicial 50%)") / 100
    x_parcial = pct(fracao_parcial, 0)
    c1.caption(md_seguro(f"**Decisão parcial:** cenário hipotético: o STF suspende parte da obrigação, e só "
                         f"{x_parcial} do valor hoje exigido continua exigido. {x_parcial} é suposição sem base em "
                         "decisão real."))
taxa_faixa = faixa_de("taxa_seguro_anual")
aj["taxa_seguro_anual"] = c2.select_slider(
    "Taxa do seguro (% ao ano sobre a importância segurada)", options=OPC_TAXA, key="x_taxa",
    format_func=lambda o: f"{_br(o, 1)}%",
    help=f"Faixa da semente: {pct(taxa_faixa['min'])} a {pct(taxa_faixa['max'])} (fonte: suposição). A SES da SUSEP "
         "não publica a importância segurada, então a taxa média do ramo não sai dela.") / 100
seg = c3.slider("Escolhe o seguro-garantia (% do déficit)", 0, 100, step=5, format="%d%%", key="x_seguro",
                help="Faixa da semente: 25% a 70% (fonte: suposição, D-016)") / 100
resto = int(round(100 * (1 - seg)))
if st.session_state["x_fianca"] > resto:   # a adesão subiu: a fiança cabe no que sobra
    st.session_state["x_fianca"] = resto
fia = (c3.slider("Escolhe a fiança bancária (S1/S2)", 0, resto, step=5, format="%d%%", key="x_fianca") / 100
       if resto > 0 else 0.0)
c3.caption(f"Regulariza com bens próprios: **{pct(1 - seg - fia, 0)}** (o restante; as três somam 100%).")
aj["escolha_garantia"] = {"bens_proprios": round(1 - seg - fia, 10), "fianca": fia, "seguro": seg}

with st.expander("Avançado: déficit, despesas da seguradora, passivo e regra de classe"):
    st.markdown("**Déficit** (capacidade de pagar do titular, D-046)")
    a, b, c = st.columns(3)

    def pct_slider(col, rotulo, valor, maximo=100, casas=0, **kw):
        """Controle em % (inteiro, ou com `casas` decimais para premissa calculada); devolve fração. O valor inicial é
        o da semente na mesma precisão, para o padrão repetir a base do painel."""
        if not casas:
            return col.slider(rotulo, 0, maximo, int(round(100 * valor)), 5, format="%d%%", **kw) / 100
        passo = 10 ** -casas
        return col.slider(rotulo, 0.0, float(maximo), round(100 * valor, casas), passo, format=f"%.{casas}f%%",
                          **kw) / 100

    def txt_faixa(nome, classe):
        v = faixa_de(nome, classe)
        fonte = "suposição" if P[nome]["fonte"] == "suposição" else "BI do CNJ, capacidade de pagar"
        return f"Faixa da semente: {pct(v['min'], 1)} a {pct(v['max'], 1)} (fonte: {fonte})"

    pd2 = pct_slider(a, "Chance de déficit — Classe 2", pb["prob_deficit"]["classe_2"], casas=1,
                     help=txt_faixa("prob_deficit", "classe_2"))
    pd3 = pct_slider(a, "Chance de déficit — Classe 3", pb["prob_deficit"]["classe_3"], casas=1,
                     help=txt_faixa("prob_deficit", "classe_3"))
    pc2 = pct_slider(b, "Parte descoberta — Classe 2", pb["pct_descoberto"]["classe_2"], casas=1,
                     help=txt_faixa("pct_descoberto", "classe_2"))
    pc3 = pct_slider(b, "Parte descoberta — Classe 3", pb["pct_descoberto"]["classe_3"], casas=1,
                     help=txt_faixa("pct_descoberto", "classe_3"))
    aj["prob_deficit"] = {"classe_2": pd2, "classe_3": pd3}
    aj["pct_descoberto"] = {"classe_2": pc2, "classe_3": pc3}

    def slider_br(col, rotulo, vmin, vmax, passo, valor, casas=1, sufixo="%", **kw):
        ops = opcoes(vmin, vmax, passo)
        return col.select_slider(rotulo, options=ops, value=mais_perto(ops, valor),
                                 format_func=lambda o: f"{_br(o, casas)}{sufixo}", **kw)

    aj["market_share_hipotetico"] = slider_br(
        c, "Market share da seguradora hipotética", 1.0, 30.0, 0.1, 100 * pb["market_share_hipotetico"],
        help="Semente (SES, garantia, 12 meses até ago/2026): mínimo 3,9% = 10ª seguradora; base 5,2% = 5ª; "
             "**máximo 16,4% = fatia do líder atual do mercado**.") / 100

    st.markdown("**Despesas e sinistros da seguradora** (SUSEP SES)")
    a, b, c = st.columns(3)
    aj["sinistralidade"] = slider_br(a, "Sinistralidade da SES (sinistro ÷ prêmio ganho), aplicada ao prêmio emitido "
                                        "do ano — aproximação", 0.0, 100.0, 0.1, 100 * pb["sinistralidade"],
                                     help="SES: mín 1,7% (menor janela anual do ramo 0775), base 10,9% (ramo 0775, "
                                          "setor público, art. 13, § 1º), máx 73,9% (ramo 0776, setor privado)") / 100
    aj["comissao"] = slider_br(b, "Despesa de comercialização (sobre o prêmio)", 0.0, 40.0, 0.1, 100 * pb["comissao"],
                               help="SES: 14,3% a 21,9%; base 17,1% (ramo 0775)") / 100
    aj["despesa_administrativa"] = slider_br(c, "Despesa administrativa (sobre o prêmio)", 0.0, 30.0, 0.5,
                                             100 * pb["despesa_administrativa"],
                                             help="Faixa da semente: 5% a 12% (fonte: suposição)") / 100

    st.markdown("**Passivo** (art. 5º do Prov. 227) **e regra de classe**")
    if proj:
        st.caption(md_seguro(f"Travados no cenário base em {ano}: a projeção foi calculada com o passivo de 2025, a "
                             "regra de R$ 300 mil e o rateio padrão. Escolha \"Hoje\" para mexer neles."))
    if DEMO:
        st.caption("Modo demonstração: o passivo vem de uma grade pré-calculada. Cada controle oferece só os pontos "
                   "da grade, e só **uma** premissa do passivo pode sair do valor base por vez (regra e rateio "
                   "combinam com qualquer uma). O resto fica disponível com os dados completos.")
    a, b, c = st.columns(3)
    if DEMO:
        aj["fap"] = a.select_slider("FAP (multiplicador do RAT)", grade("fap"), value=float(pb["fap"]),
                                    format_func=lambda v: _br(v, 2), help="Decreto 3.048, art. 202-A: entre 0,5 e 2,0",
                                    disabled=proj)
        aj["fracao_ferias_vencidas_pendentes"] = a.select_slider(
            "Férias vencidas ainda não gozadas (períodos)", grade("fracao_ferias_vencidas_pendentes"),
            value=float(pb["fracao_ferias_vencidas_pendentes"]), format_func=lambda v: _br(v, 2),
            help="Suposição aprovada na D-017: mín 0, base 0,5, máx 1", disabled=proj)
    else:
        aj["fap"] = slider_br(a, "FAP (multiplicador do RAT)", 0.5, 2.0, 0.1, float(pb["fap"]), casas=2, sufixo="",
                              help="Decreto 3.048, art. 202-A: entre 0,5 e 2,0", disabled=proj)
        aj["fracao_ferias_vencidas_pendentes"] = slider_br(a, "Férias vencidas ainda não gozadas (períodos)", 0.0, 1.0,
                                                           0.1, float(pb["fracao_ferias_vencidas_pendentes"]), casas=2,
                                                           sufixo="",
                                                           help="Suposição aprovada na D-017: mín 0, base 0,5, máx 1",
                                                           disabled=proj)
    inss_aviso = b.checkbox("INSS sobre o aviso prévio indenizado", value=False,
                            help="Base: não incide (STJ, Tema 478). Marcado = cenário máximo.", disabled=proj)
    aj["incidencias"] = {**pb["incidencias"],
                         "aviso_previo_indenizado": {"fgts": True, "inss": inss_aviso}}
    aj["limiar_vinculos_distribuicao_municipal"] = b.select_slider(
        "Vínculos mínimos para usar a distribuição do município",
        grade("limiar_vinculos_distribuicao_municipal") if DEMO else [10, 20, 30],
        value=int(pb["limiar_vinculos_distribuicao_municipal"]), disabled=proj)
    aj["base_remuneracao_rais"] = c.radio("Base de remuneração (art. 6º)", ["dezembro", "media_anual"],
                                          format_func={"dezembro": "Remuneração de dezembro",
                                                       "media_anual": "Média anual"}.get, disabled=proj)
    regra = c.radio("Regra da Classe 1", ["v2", "v1"], horizontal=True, disabled=proj,
                    format_func=lambda r: {"v2": "R$ 300 mil (Prov. 243)", "v1": "R$ 100 mil (213 original)"}[r])
    metodo = b.selectbox("Rateio do passivo entre serventias", METODOS, format_func=ROT_MET.get, disabled=proj)
    if proj:   # a projeção foi calculada no cenário base do passivo, da regra e do rateio
        regra, metodo = REGRAS["versao_base"], METODOS[0]
        for k in ("fap", "fracao_ferias_vencidas_pendentes", "limiar_vinculos_distribuicao_municipal",
                  "base_remuneracao_rais", "incidencias"):
            aj[k] = pb[k]
        inss_aviso = bool(pb["incidencias"]["aviso_previo_indenizado"]["inss"])


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
                      "WHERE variante_id = ? AND uf = ?", [int(linha["variante_id"]), UF])
    for f in faixas.itertuples():
        t[f"peso_com_passivo_{f.faixa}"] = f.peso_com_passivo
        t[f"passivo_ponderado_{f.faixa}"] = f.passivo_ponderado
    return t


@st.cache_data(show_spinner=False)
def ao_vivo(totais_json: str, p_json: str, cenario: str, extra_json: str, versao: int) -> tuple[list[dict], dict]:
    """Tornado e faixa por sorteio ao redor dos valores escolhidos (src/painel/explorar.py). `versao`: das premissas
    (as faixas vêm da semente dela), para o cache não misturar versões."""
    t, p, extra = json.loads(totais_json), json.loads(p_json), json.loads(extra_json)
    f = faixas_suposicoes(semente)
    return (explorar.tornado(t, p, f, CENARIOS, cenario, extra),
            explorar.faixa_por_sorteio(t, p, f, CENARIOS, cenario, extra))


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
        t = simulador.totais(serv)
        r = resumo_mercado(serv, p, CENARIOS, cenario, extra)
    if proj:   # universo projetado: os totais da projeção, com as suposições do prêmio escolhidas aqui
        t = explorar.totais_projetados(PREV, t, ano, limite_proj, PROJ_CFG["variante_principal"])
        r = simulador.resumo_por_totais(t, p, CENARIOS, cenario, extra)
except PremissaInvalida as e:
    st.error(f"Premissa inválida: {e}")
    st.stop()

ref = consulta("SELECT * FROM gold.fato_mercado_uf WHERE nivel = 'base' AND regra_classe = 'v2' AND cenario_stf = 'mantem'"
               " AND uf = ?", [UF]).iloc[0]


def delta(atual: float, referencia: float, fmt=brl, minimo: float = 0.5) -> str | None:
    """Diferença para o cenário base do painel; nada quando não há diferença relevante."""
    d = atual - referencia
    return None if abs(d) < minimo else ("+" if d > 0 else "") + fmt(d)


# ------------------------------------------------------------------ resultado
st.divider()
premio = r["mercado_premio_emitido"]
dif = delta(premio, ref["mercado_premio_emitido"])
valor, unidade = brl(premio).rsplit(" ", 1) if premio else ("R$ 0", "")
ui.resposta("Com essas suposições, as seguradoras receberiam por ano, em prêmios"
            + (f", em {ano} (projeção)" if proj else ""), valor,
            f"{unidade} por ano".strip(),
            f"{dif} em relação ao painel (hoje)" if dif else "o mesmo valor do painel (cenário base)",
            f"**Escada:** {aprox(r['n_universo'])} cartórios obrigados → {aprox(r['n_deficit'])} com déficit → "
            f"déficit de {brl(r['valor_descoberto'])} → {brl(r['mercado_importancia_segurada'])} viram seguro → "
            f"prêmio de {brl(premio)} por ano.")
if proj:
    st.caption(md_seguro(f"**Projeção para {ano}** ({LIM_CURTO[limite_proj]}): o universo e o passivo por faixa "
                         "são o valor central da projeção do notebook 07 (receita de 2025 × crescimento projetado de "
                         f"{UF} × desvio sorteado de cada cartório), com o passivo de 2025. A faixa por sorteio abaixo "
                         "mede só as suposições do prêmio, não a incerteza da receita projetada (essa está em "
                         "\"Para onde vai\")."))

k1, k2, k3, k4 = st.columns(4)
k1.metric("Obrigadas (universo)", aprox(r["n_universo"]), delta=delta(r["n_universo"], ref["n_universo"], num),
          delta_color="off", help=universo_txt(r["n_universo"], r["n_indeterminadas_universo"]))
k2.metric("Passivo dos obrigados", brl(r["passivo_universo"]), delta=delta(r["passivo_universo"], ref["passivo_universo"]),
          delta_color="off")
k3.metric("Com déficit (esperado)", aprox(r["n_deficit"]),   # rótulo curto: o longo era cortado em 1280 px
          delta=delta(r["n_deficit"], ref["n_deficit"], num), delta_color="off",
          help="Serventias com déficit, valor esperado: soma das probabilidades de déficit das serventias do universo.")
k4.metric("Déficit de cobertura", brl(r["valor_descoberto"]), delta=delta(r["valor_descoberto"], ref["valor_descoberto"]),
          delta_color="off")

# faixa por sorteio e tornado ao redor dos valores escolhidos
fonte_sim = "Fonte: modelo do projeto, com as suposições escolhidas nesta página."
if premio > 0:
    tornado, mc = ao_vivo(json.dumps(t, sort_keys=True, default=float), json.dumps(p, sort_keys=True, default=str),
                          cenario, json.dumps(extra or {}), versao)
    st.markdown("## Quão certo é, com essas suposições")
    if st.toggle("Faixa por sorteio (Monte Carlo)", value=True,
                 help="Sorteios triangulares das seis suposições do prêmio: o valor mais provável é o escolhido aqui; o "
                      "mínimo e o máximo são os da semente (estendidos se você escolheu um valor fora deles)."):
        m = mc["premio"]
        ui.grafico(graficos.faixa_premio(
            {"valores": {"base": m["escolhido"], "p05": m["p05"], "p95": m["p95"], "extremo_min": m["extremo_min"],
                         "extremo_max": m["extremo_max"]},
             "valor_base": brl(m["escolhido"]), "faixa_provavel": f"{brl(m['p05'])} a {brl(m['p95'])}",
             "extremos": f"{brl(m['extremo_min'])} a {brl(m['extremo_max'])}"},
            f"{fonte_sim} {num(mc['n_sorteios'])} sorteios. Extremos: as seis suposições do prêmio no mínimo e no "
            "máximo, com o passivo e o universo escolhidos (não são os extremos teóricos oficiais do painel, que "
            "também mexem no passivo).", rotulo_base="valor escolhido"))
        ui.frase(f"Em 9 de cada 10 sorteios, o prêmio fica entre **{brl(m['p05'])}** e **{brl(m['p95'])}** por ano.")
    curtos = graficos.CURTOS
    primeira = curtos.get(tornado[0]["rotulo"], tornado[0]["rotulo"])
    ui.grafico(graficos.tornado({"tabela": tornado}, fonte_sim, n=int(PAINEL["topo_tornado"]),
                                titulo=f"Com essas suposições, o que mais mexe no prêmio é: {primeira.lower()}",
                                rotulo_base="valor escolhido"))
else:
    ui.frase("Com a obrigação suspensa, ninguém precisa contratar a garantia: **o prêmio é zero**, e não há faixa nem "
             "tornado a mostrar.")

# a seguradora hipotética (pergunta 9 da escada)
st.markdown("## Mercado total e uma seguradora hipotética")
LINHAS = [("importancia_segurada", "Importância segurada", "normal"), ("premio_emitido", "Prêmio emitido", "normal"),
          ("sinistro_esperado", "Sinistro esperado", "inverse"), ("comissao", "Despesa de comercialização", "inverse"),
          ("despesa_administrativa", "Despesa administrativa", "inverse"),
          ("resultado_tecnico", ROTULO_RESULTADO, "normal")]
m, s = st.columns(2)
for coluna, prefixo, titulo in ((m, "mercado", "Mercado total"),
                                (s, "seguradora", f"Seguradora hipotética ({pct(p['market_share_hipotetico'])} de share)")):
    with coluna:
        st.markdown(f"**{titulo}**")
        for chave, rot, cor in LINHAS:
            st.metric(rot, brl(r[f"{prefixo}_{chave}"]), delta=delta(r[f"{prefixo}_{chave}"], ref[f"{prefixo}_{chave}"]),
                      delta_color=cor)
        if r[f"{prefixo}_premio_emitido"] > 0:
            st.caption(f"Margem de {pct(r[f'{prefixo}_resultado_tecnico'] / r[f'{prefixo}_premio_emitido'], 0)} não "
                       "é lucro esperado: o modelo de sinistro é uma aproximação pela SES.")

teto = r["passivo_universo"] * p["taxa_seguro_anual"]
st.caption(md_seguro(f"**Teto teórico do mercado** = passivo dos obrigados × taxa = {brl(r['passivo_universo'])} × "
                     f"{pct(p['taxa_seguro_anual'])} = **{brl(teto)}** por ano. Supõe que todos os obrigados têm "
                     "déficit igual ao passivo e todos escolhem o seguro; não depende das outras suposições."))
rodape(["cnj_serventias", "cnj_colaboradores", "cnj_arrecadacao", "rais_vinculos", "susep_ses_garantia"],
       f"Cenário: {ROT_CEN[cenario]}; regra {regra}; rateio {ROT_MET[metodo]}"
       + (f"; projeção {ano}, {LIM_CURTO[limite_proj]} (rótulo: projeção)." if proj else "."), taxa=True)

ui.sugestoes(["Por que a taxa do seguro pesa tanto no prêmio?", "O que acontece se o STF suspender o Provimento 227?",
              "Quanto a seguradora lucraria com esse mercado?"], pagina="Simule você mesmo")

# ------------------------------------------------------------------ salvar
with st.expander("Salvar este cenário", expanded=False):
    if DEMO:
        st.caption("Desativado no modo demonstração. Com os dados completos (ou recalculando com os dados públicos), "
                   "os cenários ficam salvos em data/painel_estado.json, fora do banco.")
    nome = st.text_input("Nome do cenário", placeholder="ex.: taxa 2,5% e share 10%", disabled=DEMO)
    if st.button("Salvar", type="primary", disabled=DEMO or not nome):
        # D-034: o cenário vai para um arquivo próprio; o banco do pipeline e as versões de premissas não mudam
        _, diff = com_novo_base(semente, aj)
        cid = cenarios.salvar({
            "nome": nome, "versao_premissas": versao, "cenario_stf": cenario, "regra_classe": regra,
            "metodo_rateio": metodo, "nivel": "base", "premissas_alteradas": diff, "resultado": r,
            "ano": "hoje" if not proj else ano, "cenario_limite": limite_proj,
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
        st.dataframe(tabela.reindex(columns=colunas).sort_values("id", ascending=False), hide_index=True,
                     width="stretch")
