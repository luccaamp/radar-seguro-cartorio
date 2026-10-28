"""Análises: quão certo é o número e como ele muda até 2027 (notebooks 03 a 10; docs/painel/arquitetura.md).

Abas: incerteza (faixa D-042 e tornado), projeção 2026–27 (07 principal, leitura do limite e 05b como comparação),
concentração (Gini) e a pergunta 9. Tudo vem de src/painel/analises.py, o mesmo que o chat usará.
"""
import pandas as pd
import streamlit as st

from comum import analise, brl, md_seguro, pagina, rodape
from src.painel import graficos, ui

premio = analise("faixa_d042", medida="premio")
tor = analise("tornado")
cfg_proj = analise("previsao_mercado", ano=2027)
pagina("Análises", "📈", "Análises · quão certo e como muda",
       "O que mais pesa no número, e para onde ele vai",
       f"Duas suposições que ninguém conhece ainda, a **taxa** e a **adesão ao seguro**, explicam "
       f"{tor['parte_das_duas_primeiras']} da incerteza do prêmio. Até 2027, a projeção leva as obrigadas a "
       f"**{cfg_proj['principal']['Obrigadas'].split(' (')[0]}**, mas o prêmio só cresce se a dívida trabalhista crescer.")

# ---- os achados em uma frase (notebook 09)
conc = analise("concentracao")
p9 = analise("pergunta_9")
grp = analise("grupos")
st.header("Os achados em uma frase")
c1, c2 = st.columns(2)
with c1:
    ui.achado(f"O prêmio provável fica entre {premio['faixa_provavel']}",
              f"Os extremos ({premio['extremos']}) exigem que todas as suposições errem para o mesmo lado ao mesmo "
              f"tempo. Valor base: {premio['valor_base']}.")
    ui.achado(f"Os {conc['topo']} maiores têm {conc['parte_dos_maiores_no_passivo']} do passivo das obrigadas",
              f"O cliente do seguro são as providas grandes: {grp['parte_das_serventias']} dos cartórios agrupados e "
              f"{grp['parte_do_deficit']} do déficit (página Mercado).")
with c2:
    ui.achado("A seguradora tem lucro se o titular pagar com a renda",
              f"Com a capacidade de pagar (M1): {p9['com_a_capacidade_de_pagar']}. Sem ela, "
              f"{p9['sem_a_capacidade_de_pagar']}.")
    arr = analise("previsao_arrecadacao")
    ui.achado("A projeção tende a ser conservadora",
              (arr["realizado_acima_do_p90"][0] + ". " if arr["realizado_acima_do_p90"] else "")
              + "Toda projeção desta página é rotulada como projeção, nunca número oficial.", "proj")

aba1, aba2, aba3, aba4 = st.tabs(["Incerteza do prêmio", "Projeção 2026–27", "Concentração", "A seguradora tem lucro?"])

# ---- 1. incerteza (D-042)
with aba1:
    st.subheader("Base, faixa provável e extremos")
    ui.grade([ui.kpi_d042(analise("faixa_d042", medida=m)) for m in ("deficit", "importancia_segurada", "premio")], 3)
    ui.grafico(graficos.faixa_d042(premio))
    st.caption(md_seguro(f"{premio['nota_mediana']} {premio['nota_cantos_mc']}"))
    st.subheader("Sensibilidades: o que mais mexe no prêmio")
    ui.grafico(graficos.tornado(tor))
    st.markdown(md_seguro(f"As premissas do passivo e do universo mexem no máximo {tor['passivo_e_universo_no_maximo']} "
                          "do prêmio base: a incerteza vem quase toda das suposições dos passos 5 a 8."))
    with st.expander("Método, grade taxa × adesão e dados"):
        grade = analise("grade_taxa_adesao")
        g = pd.DataFrame(grade["tabela"])
        g["Taxa"] = g["taxa"].map(lambda t: f"{t * 100:.1f}%".replace(".", ","))
        g["Adesão"] = g["adesao"].map(lambda a: f"{a * 100:.0f}% escolhe seguro")
        g["Prêmio"] = g["premio"].map(brl)
        st.markdown(md_seguro(f"**Grade taxa × adesão** (prêmio de {grade['de']} a {grade['ate']}; {grade['observacao']})."))
        st.dataframe(g.pivot(index="Adesão", columns="Taxa", values="Prêmio"), width="stretch")
        st.markdown(md_seguro(f"**Monte Carlo:** {premio['conta']}. **Tornado:** {tor['conta']}."))
        ui.baixar(tor, "tornado_premio")
        ui.baixar(premio | {"tabela": [premio["valores"]]}, "faixa_premio")
    ui.fonte(premio)

# ---- 2. projeção
with aba2:
    c1, c2 = st.columns([1, 3])
    ano = c1.radio("Ano da receita", [2026, 2027], index=1, horizontal=True, key="a_ano")
    leituras = [cfg_proj["leitura_do_limite"], cfg_proj["comparacao"]]
    leitura = c2.radio("Limite da Classe 1", leituras, horizontal=True, key="a_limite",
                       format_func=lambda x: f"{x} (principal)" if x == leituras[0] else f"{x} (comparação)",
                       help=md_seguro("Principal: o limite fixo de R$ 300 mil do Prov. 243, a regra em vigor (D-049, "
                                      "proposta). Comparação: o limite corrigido pelo IPCA (art. 16, § 2º, do Prov. 213)."))
    pm = analise("previsao_mercado", ano=ano, leitura_limite=leitura)
    ui.achado(f"PROJEÇÃO para {ano} · leitura do limite em uso: {pm['leitura_do_limite']}",
              f"Na outra leitura ({pm['comparacao']}), a diferença é de {pm['diferenca_obrigadas']} obrigadas. "
              f"Base 2025 (número oficial): {pm['base_2025']['Obrigadas']} obrigadas e prêmio de "
              f"{pm['base_2025']['Prêmio anual']}.", "proj")
    cartoes = []
    for medida in ("Obrigadas", "Prêmio anual"):
        central, faixa = pm["principal"][medida].split(" (")
        cartoes.append(ui.kpi_projecao(f"{medida} em {ano}", central, faixa.rstrip(")"), pm["leitura_do_limite"]))
        cartoes.append(ui.kpi_comparacao(f"{medida} · {pm['comparacao']}", pm["na_comparacao"][medida].split(" (")[0]))
    ui.grade(cartoes, 4)
    ui.grafico(graficos.universo_projetado(pm))
    if pm["nota_passivo"]:
        st.caption(md_seguro(pm["nota_passivo"]))
    ui.grafico(graficos.previsao_arrecadacao(arr))
    st.caption(md_seguro(" · ".join(f"{a}: {t}" for a, t in arr["por_ano"].items()) + ". " + arr["observacao"]))
    sub = analise("subidas_comparacao")
    st.subheader(f"Quantas sobem da Classe 1 para a 2 em {sub['ano']}")
    ui.grafico(graficos.subidas(sub))
    st.caption(md_seguro(f"Principal (notebook 07): {sub['notebook_07']}. Comparação: 07 com o "
                         f"{sub['notebook_07_comparacao']}; notebook 05b: {sub['notebook_05b']}. {sub['observacao']}."))
    with st.expander("Método, limitações e dados"):
        st.markdown(md_seguro(
            f"- **Arrecadação:** {arr['conta']}.\n- **Mercado:** {pm['conta']}.\n- **Subidas:** {sub['conta']}.\n"
            "- A faixa P10–P90 da projeção por serventia cobriu o real em poucos casos no teste no passado "
            "(notebook 07): leia a faixa como mínima.\n"
            "- Ano = ano da receita; a classe vale para o ano seguinte (art. 16, § 1º, do Prov. 213)."))
        ui.baixar(pm, f"projecao_mercado_{ano}")
        ui.baixar(arr, "projecao_arrecadacao")
    ui.fonte(pm, "Projeção, não número oficial")

# ---- 3. concentração
with aba3:
    ui.grade([ui.kpi("Índice de Gini do passivo das obrigadas", conc["gini_passivo"], "dado",
                     conc["explicacao"]),
              ui.kpi(f"Parte dos {conc['topo']} maiores no passivo", conc["parte_dos_maiores_no_passivo"], "dado",
                     f"entre {conc['serventias']} serventias com peso no universo"),
              ui.kpi("Gini do déficit esperado", conc["gini_deficit"], "suposicao",
                     f"os {conc['topo']} maiores têm {conc['parte_dos_maiores_no_deficit']} do déficit")], 3)
    ui.grafico(graficos.lorenz(conc))
    with st.expander("Como ler a curva e dados"):
        st.markdown(md_seguro(f"{conc['explicacao']} Quanto mais a curva se afasta da diagonal, mais concentrado. "
                              f"{conc['conta']}."))
        ui.baixar(conc | {"tabela": conc["curva"]}, "curva_concentracao")
    ui.fonte(conc)

# ---- 4. pergunta 9
with aba4:
    st.markdown(md_seguro(f"**Pergunta 9 do projeto.** O sinistro acontece quando a delegação termina (morte, "
                          f"aposentadoria, perda) e o titular não paga a dívida. Chance de isso acontecer no ano: "
                          f"{p9['p_fim']} (mínimo, base e máximo; notebook 05c)."))
    ui.grafico(graficos.pergunta_9(p9))
    with st.expander("Capacidade de pagar (M1), método e dados"):
        cap = analise("capacidade_pagar")
        f = pd.DataFrame(cap["tabela"])
        st.markdown(md_seguro(f"**Meses de saldo para pagar o passivo** ({cap['conta']}; {cap['observacao']})."))
        st.dataframe(pd.DataFrame({"Faixa": f["faixa_meses"], "Obrigadas": f["obrigadas"].round(0).astype(int),
                                   "Parte das obrigadas": f["pct_obrigadas"].map(lambda v: f"{v:.1%}".replace(".", ",")),
                                   "Parte do déficit (modelo)": f["pct_deficit_modelo"].map(
                                       lambda v: f"{v:.1%}".replace(".", ","))}), hide_index=True, width="stretch")
        st.markdown(md_seguro(f"{p9['conta']}. Limitações: {p9['observacao']}."))
        ui.baixar(p9, "pergunta_9_sinistro")
    ui.fonte(p9)

rodape(["cnj_serventias", "cnj_colaboradores", "cnj_arrecadacao", "rais_vinculos", "ibge_ipca"], taxa=True,
       extra="Projeções do notebook 07 (gold.analise_previsao) e do 05b (saída gravada do notebook); faixas do 08.")
