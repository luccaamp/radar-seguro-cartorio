"""Para onde vai: o prêmio projetado para 2026 e 2027 num gráfico só, com a faixa P10–P90 (notebook 07), e o que muda
o prêmio até lá (o passivo projetado, M5 do notebook 10). Leitura do limite da Classe 1: a principal de
config/painel.yaml (limite fixo, D-049); a outra leitura, a arrecadação e as subidas ficam no chat. Sempre projeção.
"""
from comum import analise, fonte_linha, pagina, pct
from src.painel import analises, graficos, ui

por_ano = {a: analise("previsao_mercado", ano=a) for a in (2026, 2027)}
m5 = analises.passivo_m5()   # sem conexão (saída gravada do notebook 10); o chat também a alcança
ult = max(por_ano)
pagina("Para onde vai", "📈", "Para onde vai o mercado até 2027?",
       "Mais cartórios passam a ser obrigados, mas o prêmio só cresce se a dívida trabalhista crescer.",
       sobre="Para onde vai")

obrig, faixa_obrig = por_ano[ult]["principal"]["Obrigadas"].split(" (")
cartoes = [ui.kpi(f"Cartórios obrigados em {ult}", obrig, faixa_obrig.rstrip(")"), projecao=True,
                  dica="com a receita projetada de cada cartório; a classe vale para o ano seguinte")]
if "fator" in m5:
    cartoes.append(ui.kpi(f"Dívida trabalhista em {ult}", f"+{pct(m5['fator'][ult] - 1)}",
                          "mesmos empregados, um ano a mais de casa por ano e salário corrigido pela inflação",
                          projecao=True, dica="passivo trabalhista das obrigadas, sobre o de 2025"))
ui.grade(cartoes, len(cartoes))
ui.grafico(graficos.projecao_premio(por_ano, fonte_linha(["cnj_serventias", "rais_vinculos"],
                                                         "Arrecadação dos cartórios até o 1º semestre de 2026")))
ui.frase("Os cartórios que passam a ser obrigados são pequenos, por isso o prêmio projetado sobe pouco. Se a dívida "
         "trabalhista crescer como projetado, **o prêmio cresce na mesma proporção**.")
ui.sugestoes(["Quanto a arrecadação de MG deve crescer em 2026?",
              "Quantos cartórios sobem da Classe 1 para a 2 em 2026?",
              "E se o limite da Classe 1 for corrigido pela inflação?"])
