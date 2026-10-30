"""A resposta. Rodar com: uv run streamlit run app/Inicio.py

O painel responde a uma pergunta (docs/painel/corte.md, D-051): quanto dinheiro o seguro obrigatório dos cartórios
pode movimentar em MG, e quão certo é esse número. Esta página dá a resposta: o prêmio anual (valor base), a faixa
provável logo abaixo, uma frase de quão certo é e o funil da escada. Tudo vem de src/painel/analises.py.
"""
from comum import analise, fonte_linha, pagina
from src.painel import graficos, ui

premio = analise("faixa_d042", medida="premio")
oficiais = analise("numeros_oficiais")
pagina("Radar Seguro-Garantia · Cartórios de MG", "📊",
       "Quanto dinheiro o seguro obrigatório dos cartórios pode movimentar em Minas Gerais, e quão certo é esse número?",
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
