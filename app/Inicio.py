"""Entrada do painel e a página "A resposta". Rodar com: uv run streamlit run app/Inicio.py

O painel responde a uma pergunta (docs/painel/corte.md, D-051): quanto dinheiro o seguro obrigatório dos cartórios
pode movimentar em MG, e quão certo é esse número. Esta página dá a resposta: o prêmio anual (valor base), a faixa
provável logo abaixo, uma frase de quão certo é e o funil da escada. Tudo vem de src/painel/analises.py.

O menu tem duas seções (D-077): "A história" (as cinco páginas e o chat) e "Explorar" (o Simulador). Os endereços das
páginas são os mesmos de antes (os links `Chat?pergunta=` continuam valendo), e cada arquivo de app/pages/ também
roda sozinho (testes).
"""
import streamlit as st

from comum import analise, fonte_linha, pagina
from src.painel import graficos, ui


def inicio() -> None:
    premio = analise("faixa_d042", medida="premio")
    oficiais = analise("numeros_oficiais")
    pagina("Radar Seguro-Garantia · Cartórios de MG", "📊",
           "Quanto dinheiro o seguro obrigatório dos cartórios pode movimentar em Minas Gerais, e quão certo é esse "
           "número?",
           "Estimativa com dados públicos para o Provimento CNJ 227/2026, que obriga o cartório a garantir a dívida "
           "trabalhista com seus empregados.", sobre="A resposta")

    valor, unidade = premio["valor_base"].rsplit(" ", 1)
    ui.resposta("As seguradoras receberiam, por ano, em prêmios", valor, f"{unidade} por ano",
                f"provavelmente de {premio['faixa_provavel']}",
                "**Quão certo:** 9 em cada 10 simulações caem nessa faixa. A incerteza vem principalmente de duas "
                "suposições que ainda ninguém conhece: a **taxa do seguro** e a **adesão ao seguro**.")
    ui.grafico(graficos.funil(oficiais, fonte_linha(["cnj_serventias", "rais_vinculos"],
                                                    "Déficit, seguro e prêmio dependem de suposições do modelo")))
    ui.sugestoes(["Quanto a seguradora lucraria com esse mercado?", "Por que a Classe 1 fica fora da obrigação?",
                  "Quais são os 10 números principais do painel?"])


# url_path: os mesmos endereços do menu automático de antes. Os ícones do menu vêm do estilo.css (padrão do Raio-X),
# não do st.Page
st.navigation({
    "A história": [
        st.Page(inicio, title="Início", default=True),
        st.Page("pages/1_Quão_certo_é.py", title="Quão certo é", url_path="Quão_certo_é"),
        st.Page("pages/2_Onde_está_o_mercado.py", title="Onde está o mercado", url_path="Onde_está_o_mercado"),
        st.Page("pages/3_Para_onde_vai.py", title="Para onde vai", url_path="Para_onde_vai"),
        st.Page("pages/4_Sobre_os_dados.py", title="Sobre os dados", url_path="Sobre_os_dados"),
        st.Page("pages/5_Chat.py", title="Chat", url_path="Chat"),
    ],
    "Explorar": [
        st.Page("pages/6_Explorar.py", title="Simule você mesmo", url_path="Explorar"),
    ],
}).run()
