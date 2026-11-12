"""Quão certo é: a faixa provável do prêmio e as suposições que mais pesam nela (D-042; notebook 08).

Dois gráficos: a faixa (valor base, P5–P95 e extremos discretos) e as 5 suposições que mais mexem no prêmio. Depois, a
grade Taxa × adesão do V5 (D-082), um quadro de calor em HTML com o prêmio para cada par das duas suposições que mais
pesam. O resto da incerteza (mediana dos sorteios, sensibilidades de método) fica no chat. Tudo vem de
src/painel/analises.py.
"""
import streamlit as st

from comum import analise, avisar_se_preliminar, do_escopo, fonte_linha, pagina, uf_atual
from src.painel import graficos, ui

premio = analise("faixa_d042", medida="premio")
tor = analise("tornado")
grade = analise("grade_taxa_adesao")
pagina("Quão certo é", "🎯", f"Quão certo é o número {do_escopo(uf_atual())}?",
       "A faixa é larga porque duas suposições sem dado público, a taxa e a adesão ao seguro, decidem quase tudo.",
       sobre="Quão certo é", seletor="uf")
avisar_se_preliminar()

ui.grade([ui.kpi("Taxa e adesão ao seguro", tor["parte_das_duas_primeiras"],
                 "da incerteza do prêmio vem dessas duas suposições",
                 dica="taxa: quanto a seguradora cobra por ano sobre o valor segurado; adesão: a parte do déficit "
                      "que escolhe seguro em vez de fiança bancária ou bens"),
          ui.kpi("O que vem de dado público", f"até {tor['passivo_e_universo_no_maximo']}",
                 "é o máximo que a dívida trabalhista e o número de obrigados mexem no prêmio",
                 dica="premissas do passivo (férias, INSS, FAP) e de quem entra no universo, uma por vez")], 2)
fonte = fonte_linha(["cnj_serventias", "rais_vinculos"], "Simulações das suposições do modelo")
ui.grafico(graficos.faixa_premio(premio, fonte))
ui.frase("Os extremos exigem que todas as suposições errem para o mesmo lado ao mesmo tempo, o que quase nunca "
         "acontece. Medir a **taxa** e a **adesão** com as seguradoras estreitaria a faixa mais que qualquer outro "
         "dado.")
ui.grafico(graficos.tornado(tor, fonte))

st.header("Taxa × adesão")
ui.frase(f"O prêmio anual para cada par das duas suposições que mais pesam: vai de **{grade['de']}** a "
         f"**{grade['ate']}**. A célula com contorno grosso é a base do painel ({grade['base']}).")
ui.quadro_calor("Adesão", "taxa", grade["taxas"],
                [(linha["adesao"], [{"texto": c["premio"], "faixa": c["faixa"], "base": c["base"]}
                                    for c in linha["celulas"]]) for linha in grade["quadro"]])
ui.fonte(fonte_linha(["cnj_serventias", "rais_vinculos"],
                     "A SUSEP não publica a importância segurada; por isso a taxa média não sai de dado público"))
ui.sugestoes(["Qual seria o prêmio com uma taxa de 3%?", "Como é calculada a faixa provável?",
              "Que dados faltam para estreitar a faixa?"], pagina="Quão certo é")
