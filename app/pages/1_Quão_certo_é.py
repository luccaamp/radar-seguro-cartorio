"""Quão certo é: a faixa provável do prêmio e as suposições que mais pesam nela (D-042; notebook 08).

Dois gráficos: a faixa (valor base, P5–P95 e extremos discretos) e as 5 suposições que mais mexem no prêmio. O resto
da incerteza (mediana dos sorteios, grade taxa × adesão, sensibilidades de método) fica no chat. Tudo vem de
src/painel/analises.py.
"""
from comum import analise, fonte_linha, pagina
from src.painel import graficos, ui

premio = analise("faixa_d042", medida="premio")
tor = analise("tornado")
pagina("Quão certo é", "🎯", "Quão certo é o número?",
       "A faixa é larga porque duas suposições sem dado público, a taxa e a adesão ao seguro, decidem quase tudo.",
       sobre="Quão certo é")

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
ui.sugestoes(["Qual seria o prêmio com uma taxa de 3%?", "Como é calculada a faixa provável?",
              "Que dados faltam para estreitar a faixa?"])
