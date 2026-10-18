"""Página inicial do painel. Rodar com: uv run streamlit run app/Inicio.py"""
import streamlit as st

from comum import aviso_estimativa, brl, consulta, execucao, faixa, md, num, rodape

st.set_page_config(page_title="Radar Seguro-Garantia Cartórios", page_icon="📊", layout="wide")
st.title("Radar Seguro-Garantia Cartórios")
st.markdown(
    "Painel de cartórios de **Minas Gerais** com dados públicos e simulador do mercado de **seguro-garantia** "
    "criado pelo **Provimento CNJ 227/2026**: o delegatário declara o passivo trabalhista de todos os prepostos "
    "e, se os bens livres não o cobrirem, apresenta fiança bancária (S1/S2) ou seguro-garantia de 100% do déficit "
    "(art. 13). Ficam fora as serventias da Classe 1 do Prov. 213 e as sob interinidade (art. 19).")
aviso_estimativa()

uf = consulta("SELECT * FROM gold.fato_mercado_uf WHERE regra_classe = 'v2' AND cenario_stf = 'mantem'").set_index("nivel")
e = execucao()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Serventias ativas em MG", num(uf.at["base", "n_serventias_ativas"]))
c2.metric("Empregados CLT declarados", num(uf.at["base", "clt"]))
c3.metric("Passivo trabalhista estimado (base)", brl(uf.at["base", "passivo_todas"]),
          help=f"Faixa: {brl(uf.at['min', 'passivo_todas'])} a {brl(uf.at['max', 'passivo_todas'])}")
c4.metric("Prêmio anual do mercado (base)", brl(uf.at["base", "mercado_premio_emitido"]),
          help=f"Faixa: {brl(uf.at['min', 'mercado_premio_emitido'])} a {brl(uf.at['max', 'mercado_premio_emitido'])}")
st.markdown(md(f"**Déficit de cobertura estimado:** {faixa(uf.at['min', 'valor_descoberto'], uf.at['base', 'valor_descoberto'], uf.at['max', 'valor_descoberto'])}. "
               "Cenário do STF: regra mantida. Regra de classe: Prov. 243 (Classe 1 até R$ 300 mil por semestre)."))
rodape(["cnj_serventias", "cnj_colaboradores", "cnj_arrecadacao", "rais_vinculos", "ibge_inpc", "susep_ses_garantia"])

st.subheader("Páginas")
st.markdown(
    "- **Mercado**: serventias, empregados, passivo e déficit por município, com mapa, ranking e filtros.\n"
    "- **Simulador**: ajuste as premissas e o cenário do STF e compare o mercado total com a seguradora hipotética.\n"
    "- **Qualidade dos dados**: data de referência de cada fonte, cobertura, divergências e contratos.")
st.subheader("Situação regulatória")
st.markdown(
    "ADI 8015 (ANOREG/BR contra os arts. 8º a 17 do Prov. 227), relator Min. Flávio Dino: rito do art. 12 da "
    "Lei 9.868/1999, **sem liminar**; informações do CNJ e da AGU prestadas, vista à PGR. *Conferido em 17/10/2026 "
    "no portal do STF.* O cenário \"suspende arts. 8º a 17\" está pronto no Simulador.")
st.caption(f"Peso da classe indeterminada no cenário base: {num(100 * e.peso_classe_indeterminada_base, 1)}% "
           f"(calculado na carga). Correção salarial da RAIS: INPC dez/2025 a {str(int(e.mes_inpc_final))[4:]}/"
           f"{str(int(e.mes_inpc_final))[:4]}, fator {num(e.fator_inpc, 4)}.")
