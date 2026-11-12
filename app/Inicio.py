"""Entrada do painel e a página "A resposta". Rodar com: uv run streamlit run app/Inicio.py

O painel responde a uma pergunta (docs/painel/corte.md, D-051): quanto dinheiro o seguro obrigatório dos cartórios
pode movimentar em MG, e quão certo é esse número. Esta página dá a resposta: o prêmio anual (valor base), a faixa
provável logo abaixo, uma frase de quão certo é e o funil da escada. Tudo vem de src/painel/analises.py.

O menu fica no topo, como no V5 (D-082), numa linha só; o Simulador ("Simule") vem antes de "Sobre os dados". Os
endereços das páginas são os mesmos de antes (os links `Chat?pergunta=` continuam valendo), e cada arquivo de
app/paginas/ também roda sozinho (testes). A pasta NÃO se chama `pages/`: com esse nome, o Streamlit também a lê no
modo antigo de páginas, e quem abria direto o endereço de uma página num servidor recém-ligado (o Cloud acorda o app
assim) via o menu lateral com os nomes dos arquivos (2026-11-11).
"""
from pathlib import Path

import streamlit as st

from comum import REGIAO, analise, aprox, avisar_se_preliminar, brl, do_escopo, escopo, fonte_linha, num, pagina
from src.painel import graficos, ui


def inicio() -> None:
    e = escopo()
    pagina("Radar Seguro-Garantia · Cartórios do Sudeste", "📊",
           f"Quanto dinheiro o seguro obrigatório dos cartórios pode movimentar {do_escopo(e)}, e quão certo é esse "
           "número?",
           "Estimativa com dados públicos para o Provimento CNJ 227/2026, que obriga o cartório a garantir a dívida "
           "trabalhista com seus empregados.", sobre="A resposta", seletor="regiao")
    if e == REGIAO:
        inicio_regiao()
        return
    avisar_se_preliminar(e)
    premio = analise("faixa_d042", uf=e, medida="premio")
    oficiais = analise("numeros_oficiais", uf=e)

    valor, unidade = premio["valor_base"].rsplit(" ", 1)
    ui.resposta("As seguradoras receberiam, por ano, em prêmios", valor, f"{unidade} por ano",
                f"provavelmente de {premio['faixa_provavel']}",
                "**Quão certo:** 9 em cada 10 simulações caem nessa faixa. A incerteza vem principalmente de duas "
                "suposições que ainda ninguém conhece: a **taxa do seguro** e a **adesão ao seguro**.")
    # Panorama (V5, D-082): 6 indicadores com uma linha de contexto cada
    ui.grade([ui.kpi(k["rotulo"], k["valor"], k["nota"]) for k in analise("panorama", uf=e)["kpis"]], 3)
    ui.grafico(graficos.funil(oficiais, fonte_linha(["cnj_serventias", "rais_vinculos"],
                                                    "Déficit, seguro e prêmio dependem de suposições do modelo", uf=e)))
    ui.sugestoes(["Quanto a seguradora lucraria com esse mercado?", "Por que a Classe 1 fica fora da obrigação?",
                  "Quais são os 10 números principais do painel?"], pagina="Início")


def inicio_regiao() -> None:
    """O Sudeste somado (D-088): a resposta da região, com a faixa simulada sorteio a sorteio, os 6 indicadores
    somados e uma linha por estado, com o selo de calibrado ou de estimativa preliminar."""
    r = analise("regiao")
    valor, unidade = r["valor_base"].rsplit(" ", 1)
    ui.resposta("As seguradoras receberiam, por ano, em prêmios", valor, f"{unidade} por ano",
                f"provavelmente de {r['faixa_provavel']}",
                "**Quão certo:** 9 em cada 10 simulações caem nessa faixa. Só Minas Gerais tem as premissas "
                "calibradas; os outros estados usam as de MG como **estimativa preliminar**.")
    ui.grade([ui.kpi(k["rotulo"], k["valor"], k["nota"]) for k in r["kpis"]], 3)
    st.header("Estado por estado")
    ui.tabela(["Estado", "Situação", "Cartórios", "Obrigados", "Dívida trabalhista", "Déficit", "Prêmio por ano",
               "Faixa provável"],
              [[f"{x['estado']} ({x['uf']})", ui.selo("preliminar" if x["preliminar"] else "calibrado"),
                num(x["serventias"]), aprox(x["obrigadas"]), brl(x["passivo_obrigadas"]), brl(x["deficit"]),
                x["premio_txt"], x["faixa_txt"]] for x in r["tabela"]],
              numericas={2, 3, 4, 5, 6, 7}, so_no_computador={3, 4, 7}, html={1})
    ui.frase("Escolha um estado no seletor do topo para ver a resposta e os números dele. A faixa do Sudeste é "
             "simulada junta (as mesmas suposições valem para os quatro estados), não é a soma das faixas.")
    ui.fonte(fonte_linha(["cnj_serventias", "rais_vinculos"], "Déficit, seguro e prêmio dependem de suposições do "
                         "modelo; SP, RJ e ES com as premissas de MG (estimativa preliminar)"))
    ui.sugestoes(["Qual estado do Sudeste tem o maior mercado?", "Por que os números de SP são preliminares?",
                  "Quantos cartórios há na Bahia?"], pagina="Início")


# Menu no topo, como o V5 (D-082): a marca à esquerda e as páginas numa linha só; o Simulador ("Simule") entra antes de
# "Sobre os dados", como no V5. url_path: os mesmos endereços de antes (os links `Chat?pergunta=` continuam valendo).
st.logo(str(Path(__file__).with_name("static") / "marca.svg"), size="large")
st.navigation([
    st.Page(inicio, title="Início", default=True),
    st.Page("paginas/1_Quão_certo_é.py", title="Quão certo é", url_path="Quão_certo_é"),
    st.Page("paginas/2_Onde_está_o_mercado.py", title="Onde está o mercado", url_path="Onde_está_o_mercado"),
    st.Page("paginas/3_Para_onde_vai.py", title="Para onde vai", url_path="Para_onde_vai"),
    st.Page("paginas/7_Brasil.py", title="Brasil", url_path="Brasil"),
    st.Page("paginas/6_Explorar.py", title="Simule", url_path="Explorar"),
    st.Page("paginas/4_Sobre_os_dados.py", title="Sobre os dados", url_path="Sobre_os_dados"),
    st.Page("paginas/5_Chat.py", title="Pergunte à IA", url_path="Chat"),
], position="top").run()
