"""Página inicial do painel. Rodar com: uv run streamlit run app/Inicio.py"""
import streamlit as st

from comum import (EXPLICA_NIVEIS, aviso_estimativa, brl, conexao, consulta, data_base_passivo, execucao, faixa,
                   md_seguro, n_indeterminadas_no_universo, num, pct, rodape, universo_txt)
from src import estado

st.set_page_config(page_title="Radar Seguro-Garantia Cartórios", page_icon="📊", layout="wide")
st.title("Radar Seguro-Garantia Cartórios")
st.markdown(
    "Painel de cartórios de **Minas Gerais** com dados públicos e simulador do mercado de **seguro-garantia** "
    "criado pelo **Provimento CNJ 227/2026**: o delegatário declara o passivo trabalhista dos empregados CLT "
    "(estatutários, estagiários e terceirizados ficam fora, D-003) "
    "e, se os bens livres não o cobrirem, apresenta fiança bancária (S1/S2) ou seguro-garantia de 100% do déficit "
    "(art. 13). Ficam fora as serventias da Classe 1 do Prov. 213 e as sob interinidade (art. 19).")
aviso_estimativa()

uf = consulta("SELECT * FROM gold.fato_mercado_uf WHERE regra_classe = 'v2' AND cenario_stf = 'mantem'").set_index("nivel")
e = execucao()
# duas linhas (contagens / valores em R$): com cinco colunas os valores em R$ eram cortados em 1280 px
c1, c2, _ = st.columns(3)
c3, c4, c5 = st.columns(3)
c1.metric("Serventias ativas em MG", num(uf.at["base", "n_serventias_ativas"]))
c2.metric("Empregados CLT declarados", num(uf.at["base", "clt"]))
c3.metric("Passivo de todas as ativas", brl(uf.at["base", "passivo_todas"]),
          help=md_seguro(f"Cenário base. Faixa: {brl(uf.at['min', 'passivo_todas'])} a {brl(uf.at['max', 'passivo_todas'])}"))
c4.metric("Passivo dos obrigados", brl(uf.at["base", "passivo_universo"]),
          help=md_seguro("Cenário base. Universo do Prov. 227: sem interinos e sem Classe 1 (art. 19); "
                         + universo_txt(uf.at["base", "n_universo"], n_indeterminadas_no_universo()) + ". Faixa: "
                         f"{brl(uf.at['min', 'passivo_universo'])} a {brl(uf.at['max', 'passivo_universo'])}"))
c5.metric("Prêmio anual do mercado", brl(uf.at["base", "mercado_premio_emitido"]),
          help=md_seguro(f"Cenário base. Faixa: {brl(uf.at['min', 'mercado_premio_emitido'])} a "
                         f"{brl(uf.at['max', 'mercado_premio_emitido'])}"))
st.markdown(md_seguro(f"**Déficit de cobertura estimado:** {faixa(uf.at['min', 'valor_descoberto'], uf.at['base', 'valor_descoberto'], uf.at['max', 'valor_descoberto'])}. "
                      "Cenário do STF: regra mantida. Regra de classe: Prov. 243 (Classe 1 até R$ 300 mil por semestre)."))
taxa_base = estado.premissas_vigentes(conexao())[0]["premissas"]["taxa_seguro_anual"]["valores"]["base"]
teto = uf.at["base", "passivo_universo"] * taxa_base
st.markdown(md_seguro(f"**Teto teórico do mercado:** {brl(teto)} por ano = passivo dos obrigados "
                      f"({brl(uf.at['base', 'passivo_universo'])}) × taxa base ({pct(taxa_base)}). Supõe que todos os "
                      "obrigados têm déficit igual ao passivo e todos escolhem seguro; não depende de nenhuma suposição "
                      "de déficit."))
st.caption(md_seguro(EXPLICA_NIVEIS))
# nada nesta página usa a SUSEP SES: a taxa do seguro é suposição (1.6)
rodape(["cnj_serventias", "cnj_colaboradores", "cnj_arrecadacao", "rais_vinculos"], taxa=True)

st.header("Páginas")
st.markdown(
    "- **Mercado**: serventias, empregados, passivo e déficit por município, com mapa, ranking e filtros.\n"
    "- **Simulador**: ajuste as premissas e o cenário do STF e compare o mercado total com a seguradora hipotética.\n"
    "- **Qualidade dos dados**: data de referência de cada fonte, cobertura, divergências, sensibilidade e contratos.")
st.header("Situação regulatória")
st.markdown(
    "ADI 8015 (ANOREG/BR contra os arts. 8º a 17 do Prov. 227), relator Min. Flávio Dino: rito do art. 12 da "
    "Lei 9.868/1999, **sem liminar**; informações do CNJ e da AGU prestadas, vista à PGR. *Conferido em 17/10/2026 "
    "no portal do STF.* O cenário \"suspende arts. 8º a 17\" está pronto no Simulador.")
st.caption(f"Peso da classe indeterminada no cenário base: {num(100 * e.peso_classe_indeterminada_base, 1)}% "
           f"(calculado na carga). Salário da RAIS sem correção (data-base {data_base_passivo()}, D-020); a correção pelo INPC "
           f"até {str(int(e.mes_inpc_final))[4:]}/{str(int(e.mes_inpc_final))[:4]} (fator {num(e.fator_inpc, 4)}) "
           "aparece só na tabela de sensibilidade da página Qualidade dos dados.")
