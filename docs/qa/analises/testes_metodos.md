# Testes de métodos de estimação (T1 a T7)

> **O que é:** a comparação de métodos que escolheu como cada notebook da mineração (03 a 09) vai estimar o que não está nos dados. Base do [`plano_projeto.md`](../../plano_projeto.md) (D-039).
> **Script:** [`scripts/testes_metodos.py`](../../../scripts/testes_metodos.py) (semente 42). **Resultados completos:** [`testes_metodos_resultados.json`](testes_metodos_resultados.json).
> **Dados:** silver da carga 2026-10-19 (API do Justiça Aberta, RAIS 2025, IBGE) e as premissas v2 (`config/premissas/premissas_v002.yaml`). O script só lê dados e não muda o banco nem os 10 números oficiais.
> **Rodado em:** 23/10/2026, duas vezes, com o mesmo resultado byte a byte.

## Como rodar

```bash
uv run python -I scripts/testes_metodos.py data/silver . <pasta_de_saida>
```

Leva cerca de 2 minutos e grava `<pasta_de_saida>/resultados.json`. Precisa do silver da carga instalado (`scripts/baixar_dados.py`, ver `CONTRIBUTING.md`) e do `scikit-learn` e do `statsmodels`, que já estão no `pyproject.toml`.

## Como os testes funcionam

Todos seguem a mesma regra, que vem dos critérios de qualidade do [`plano_mineracao.md`](../../plano_mineracao.md) (§4):

1. **Uma pergunta** que o projeto precisa estimar.
2. **Uma referência simples** (o "chute": a média, a mediana, o último valor). Um método só vale se for melhor que ela.
3. **Vários métodos candidatos**, do mais simples ao mais complexo.
4. **Uma validação honesta**: o método é avaliado em dados que ele não viu no treino. Quando há tempo, ele treina só com o passado e é testado no futuro.
5. **Um indicador escolhido antes de rodar**, que decide o vencedor. Os outros indicadores aparecem só para leitura.

## As métricas, em português simples

| Métrica | O que mede | Como ler | Exemplo |
|---|---|---|---|
| **MAE** (erro absoluto médio) | Quanto o valor previsto erra, em média, na unidade do dado | menor é melhor | MAE 1,86 = erra em média 1,86 empregado por cartório |
| **RMSE** | Como o MAE, mas pesa mais os erros grandes | menor é melhor | — |
| **R²** | Quanto da variação entre os cartórios o modelo explica | de 0 (nada) a 1 (tudo) | R² 0,75 = explica 75% da diferença entre cartórios |
| **MAPE** | Erro médio em % do valor real | menor é melhor | MAPE 7,4% = a previsão erra em média 7,4% |
| **MASE** | Erro comparado ao do método "repete o mesmo semestre do ano anterior" | abaixo de 1 = melhor que ele | — |
| **Viés** | Se o método erra mais para cima (+) ou para baixo (−) | perto de 0 é melhor | −2% = prevê 2% abaixo do real |
| **Brier** | Erro de uma probabilidade: (probabilidade prevista − o que aconteceu)², em média | menor é melhor | prever 90% e acontecer dá erro 0,01; prever 90% e não acontecer dá erro 0,81 |
| **AUC** | Se o modelo põe os casos "sim" acima dos casos "não" | 0,5 = chute; 1 = perfeito | AUC 0,88 = em 88% dos pares (um "sim", um "não"), o "sim" ganhou nota maior |
| **AP** (precisão média) | Como a AUC, mas focada nos casos "sim", útil quando eles são raros | de quase 0 a 1 | — |
| **P5, P50, P95** | Percentis: 5% dos resultados ficam abaixo do P5, metade abaixo do P50, 95% abaixo do P95 | a faixa P5–P95 contém 90% dos casos | — |

---

## T1 — Empregados CLT a partir da receita

- **Pergunta:** dá para estimar quantos empregados CLT um cartório tem a partir da receita e das atribuições?
- **Por que importa:** o CNJ só traz a contagem de empregados para MG. Para levar o modelo a outros estados, é preciso estimar.
- **Onde entra:** notebook 06a; expansão para outros estados.
- **Dados:** 2.444 serventias de MG com receita de 2025 válida e CLT informado; média de 4,85 empregados por cartório.
- **Validação:** cada uma das 13 regiões intermediárias de MG fica de fora uma vez. O modelo treina com as outras 12 e prevê a que ficou de fora, como se fosse um lugar novo.
- **Indicador que decide:** MAE com a região de fora.
- **Exigência extra:** o erro do **total** da região ficar até 5%, porque o passivo usa o total.

| Método | MAE (região fora) | R² (região fora) | Erro do total (%) |
|---|---|---|---|
| **Floresta aleatória** (vencedor) | **1,86** | 0,75 | 9,3 |
| Gradient boosting (Poisson) | 1,89 | 0,69 | 8,8 |
| Poisson (GLM) | 1,93 | 0,61 | 12,0 |
| Binomial negativa (GLM) | 1,99 | 0,66 | 10,9 |
| Regressão log-log | 2,29 | 0,54 | 13,6 |
| *Referência: mediana por faixa de receita* | *2,34* | *0,41* | *16,2* |
| Razão (CLT por real de receita) | 2,49 | 0,22 | 16,6 |

**Leitura:** a floresta erra 20% menos que a referência por cartório. Mas **nenhum método cumpriu a exigência de 5% no total**: o melhor fica perto de 9%.

**O que será usado:** floresta aleatória por serventia, com o total publicado com ±10%. O Poisson fica como versão "explicável", porque mostra quanto cada atribuição soma. Antes de usar em outro estado, validar num estado que tenha a contagem do CNJ.

---

## T2 — Previsão da arrecadação de MG

- **Pergunta:** quanto os cartórios de MG vão arrecadar em 2026 e 2027?
- **Por que importa:** a arrecadação define a classe de cada cartório e, portanto, quantos são obrigados pelo Prov. 227 nos próximos anos.
- **Onde entra:** notebook 07.
- **Dados:** a série semestral de MG de 2007-1 a 2025-2. O 2026-1 fica só para conferência, porque está incompleto (57 serventias sem informar).
- **Validação:** origem móvel. O método treina até 2019-2 e prevê os 4 semestres seguintes; depois treina até 2020-2, e assim por diante, até 2023-2.
- **Indicador que decide:** MAPE médio na origem móvel.

| Método | MAPE (%) | MASE | Viés 2024–25 (%) | Previsão 2026-1 (R$ bi) |
|---|---|---|---|---|
| **Tendência log-linear com efeito de semestre** (vencedor) | **7,4** | 0,52 | −2,1 | 2,74 |
| SARIMA | 10,5 | 0,83 | −2,2 | 2,90 |
| Holt-Winters amortecido | 11,9 | 0,95 | −6,0 | 2,86 |
| *Referência: repete o último semestre* | *14,8* | *1,30* | *−11,0* | *3,13* |
| Tendência (só os últimos 8 semestres) | 15,0 | 1,27 | +14,0 | 2,71 |
| Sazonal + crescimento do último ano | 19,5 | 1,67 | −9,9 | 2,88 |
| Sazonal ingênuo | 20,5 | 1,78 | −18,9 | 2,38 |

**Previsão do vencedor, em R$ bilhões (faixa P10–P90 a partir dos erros do teste no passado):**

| Semestre | P10 | Central | P90 |
|---|---|---|---|
| 2026-1 | 2,39 | 2,74 | 2,94 |
| 2026-2 | 2,78 | 3,18 | 3,42 |
| 2027-1 | 2,71 | 3,10 | 3,33 |
| 2027-2 | 3,14 | 3,61 | 3,87 |

**Leitura:** o 2026-1, mesmo incompleto, já somou **R$ 3,20 bi**: 17% acima da previsão central e acima do P90. A arrecadação acelerou em 2025-2 e 2026-1, e o melhor método do passado não pegou isso.

**Nota de 2026-10-27 (notebook 07):** a coluna **MASE** acima está com o divisor errado: o script dividia pela segunda diferença da série (`np.diff(x, 2)`), e não pelo erro do sazonal ingênuo. Com o divisor certo (`src/analise/previsao.py`), todos os MASE ficam ≈ 1,5 vez maiores (tendência 0,79; SARIMA 1,26; referência 1,99). O MAPE, que decide, e a ordem dos métodos não mudam. O notebook 07 também mostra que o 2026-1 "acima do P90" vinha, em grande parte, de saltos grosseiros de declaração (serventias 059816 e 046219): sem eles e com as 57 serventias sem informação completadas, o 2026-1 fica dentro da faixa.

**O que será usado:** a tendência log-linear, com o SARIMA para comparar, e sempre com a faixa. O notebook 07 refaz a previsão quando o 2026-1 fechar e testa se houve uma quebra de nível em 2025-2 (conferir a serventia 042986). A previsão é sempre rotulada como projeção, nunca como número oficial.

---

## T3 — Subida de classe

- **Pergunta:** um cartório abaixo do limite de R$ 300 mil por semestre vai passar do limite no ano seguinte?
- **Por que importa:** quem passa do limite sai da Classe 1 e fica obrigado pelo Prov. 227. É o crescimento do mercado.
- **Onde entra:** notebook 05b e a projeção do universo no 07.
- **Dados:** 24.416 casos de treino (anos até 2023) e 2.692 de teste (2024 e 2025). No teste, 10,9% subiram.
- **Validação:** temporal. Treina até 2023 e testa em 2024–25. As variáveis vêm só dos anos anteriores ao ano previsto.
- **Indicador que decide:** Brier, porque a projeção soma as probabilidades para contar quantos sobem. Por isso a probabilidade precisa estar certa, e não só a ordem dos cartórios.

| Método | Brier | AUC | AP | Subidas previstas | Subidas reais |
|---|---|---|---|---|---|
| **Floresta aleatória** (vencedor) | **0,068** | 0,88 | 0,54 | 218 | 294 |
| Regressão logística | 0,069 | 0,87 | 0,55 | 195 | 294 |
| Gradient boosting | 0,070 | 0,88 | 0,55 | 215 | 294 |
| *Referência: regra "repete o crescimento"* | *0,092* | *0,62* | *0,20* | *186* | *294* |
| *Referência: taxa histórica (2019–2023)* | *0,099* | *0,50* | *0,11* | *174* | *294* |

**Leitura:** os modelos acertam bem **quem** tende a subir (AUC 0,88), mas **todos subestimam quantos** sobem: previram 218 e houve 294 (−26%). O crescimento em reais acelerou depois de 2023.

**O que será usado:** floresta aleatória, recalibrada com os anos mais recentes (2022–23) antes de projetar. Dois cenários de limite: fixo e corrigido pela inflação (o corrigido reduz as subidas).

---

## T4 — Vacância

- **Pergunta:** dá para reconhecer os cartórios vagos (com interino) pela receita, pelos empregados, pelas atribuições e pela região?
- **Por que importa:** o fim da delegação é o risco que o seguro cobre (D-025).
- **Onde entra:** notebook 05a.
- **Dados:** 2.406 serventias providas ou vagas; 32,4% são vagas.
- **Validação:** cruzada estratificada, 5 partes, repetida 3 vezes. Cada parte é testada com um modelo treinado nas outras 4, mantendo a mesma proporção de vagas.
- **Indicador que decide:** AUC.

| Método | AUC | AP | Brier |
|---|---|---|---|
| **Floresta aleatória** (vencedor) | **0,886** | 0,79 | 0,123 |
| Gradient boosting | 0,870 | 0,77 | 0,139 |
| Regressão logística | 0,848 | 0,77 | 0,134 |
| *Referência: proporção de vagas* | *0,500* | *0,32* | *0,219* |

**Leitura:** os modelos separam bem vagas de providas. Mas há **vazamento**: a receita e os empregados de um cartório vago são medidos já sob o interino, então parte do sinal vem da própria vacância.

**O que será usado:** floresta aleatória, com a logística para explicar o peso de cada variável. O notebook trata o resultado como **associação** ("cartórios vagos costumam ser assim"), não como previsão de quem vai vagar, e declara as variáveis com vazamento.

---

## T5 — Salário de dezembro ausente

- **Pergunta:** os 887 vínculos da RAIS sem salário de dezembro, que a D-015 exclui do cálculo, deveriam receber um salário estimado?
- **Por que importa:** o passivo de cada vínculo depende do salário.
- **Onde entra:** sensibilidade do passivo (notebooks 01 e 08).
- **Dados:** 10.978 vínculos com salário de dezembro conhecido. Dos 887 sem dezembro, só 154 têm alguma remuneração no ano; os outros 733 não têm nenhuma.
- **Validação:** esconde 20% dos salários **conhecidos**, estima esses salários por cada método e compara o passivo estimado com o real, 5 vezes. O passivo é calculado pela função oficial do projeto (`passivo_vinculos`, premissas v2, nível base).
- **Indicador que decide:** erro absoluto médio do passivo por vínculo, em %.

| Método | Erro médio (%) | Viés no total (%) |
|---|---|---|
| **Remuneração média do ano × razão dezembro/média** (vencedor) | **8,4** | −1,8 |
| Regressão (tempo de casa, região, remuneração média) | 12,9 | −1,2 |
| Mediana da região imediata | 53,0 | −39,4 |
| *Referência: excluir (regra atual, D-015)* | *89,4* | *+4,1* |

**Leitura:** quando há remuneração no ano, estimar o salário é muito melhor que excluir. Mas isso vale só para 154 dos 887. Os 887 têm mais tempo de casa (mediana de 85 meses, contra 31 nos demais). Incluí-los com salário estimado sobe o passivo médio por vínculo de MG em **+1,0%** (de R$ 23.988 para R$ 24.233).

**O que será usado:** a D-015 continua na base (os 10 números não mudam). A inclusão estimada entra como linha de sensibilidade.

---

## T6 — Salário de município com poucos vínculos

- **Pergunta:** quando o município tem poucos vínculos na RAIS, de onde tirar o passivo médio por vínculo?
- **Por que importa:** em MG, a mediana é de 4 vínculos por município. Com tão poucos, a média do próprio município é instável. A regra atual (D-008, D-022) usa a região imediata como reserva.
- **Onde entra:** sensibilidade do passivo (notebook 08).
- **Dados:** 135 municípios com 20 ou mais vínculos, onde se conhece o valor real.
- **Validação:** em cada município, finge que só se viu uma amostra de 5 (ou 10) vínculos, sorteada 30 vezes, e compara a estimativa com o passivo médio real do município. Nada do município testado entra na estimativa, além da amostra.
- **Indicador que decide:** erro médio em %, ponderado pelo número de vínculos, com 5 vínculos (o caso típico).

| Método | Erro com 5 vínculos (%) | Erro com 10 vínculos (%) |
|---|---|---|
| **Encolhimento: mistura a amostra com a região** (vencedor) | **36,7** | 30,2 |
| Estado (sem o município) | 38,5 | 38,5 |
| *Referência: região imediata (regra atual, D-022)* | *42,4* | *42,4* |
| Só a amostra do próprio município | 50,8 | 34,5 |

**Leitura:** o encolhimento dá mais peso à amostra quando os municípios variam muito entre si e mais peso à região quando a amostra é pequena e ruidosa. Ele ganha, mas por pouco. A regra atual foi a pior das reservas. **Ressalva:** os testados são os 135 maiores municípios, que tendem a diferir mais da própria região do que os pequenos.

**O que será usado:** a regra atual continua na base. O encolhimento entra como sensibilidade da reserva salarial.

---

## T7 — Faixa de incerteza do prêmio

- **Pergunta:** como montar a faixa de mínimo e máximo do prêmio anual, que depende de suposições sem fonte (patrimônio do titular, escolha pelo seguro, taxa)?
- **Por que importa:** a partir do passo 5 da escada, todo número é suposição. A faixa diz o quanto ele é incerto.
- **Onde entra:** notebook 08, painel e simulador.
- **Dados:** o passivo das obrigadas por classe (`gold.simulador_base_classe`, nível base) e as faixas das premissas v2.
- **Validação:** não há valor real para comparar, porque nem o patrimônio nem a taxa são públicos. O teste compara **como** cada método monta a faixa, com 200 mil sorteios.
- **Indicador:** largura da faixa e com que chance o resultado cai nela.

| Método | P5 (R$ mil) | P50 (R$ mil) | P95 (R$ mil) |
|---|---|---|---|
| **Monte Carlo triangular** (escolhido) | **207** | **404** | **737** |
| Monte Carlo PERT | 203 | 378 | 665 |
| Monte Carlo uniforme | 154 | 407 | 949 |
| Monte Carlo triangular, suposições de patrimônio juntas | 155 | 400 | 906 |
| *Atual: cantos (tudo no mínimo / base / tudo no máximo)* | *27* | *369* | *2.370* |

**Tornado:** cada suposição vai sozinha do mínimo ao máximo, com as outras no valor base.

| Suposição | Prêmio no mínimo (R$ mil) | Prêmio no máximo (R$ mil) | Amplitude (R$ mil) |
|---|---|---|---|
| Taxa do seguro | 184 | 645 | 461 |
| Parte que escolhe seguro | 184 | 516 | 332 |
| Parte descoberta, Classe 3 | 264 | 526 | 261 |
| Chance de déficit, Classe 3 | 264 | 508 | 244 |
| Parte descoberta, Classe 2 | 305 | 465 | 160 |
| Chance de déficit, Classe 2 | 305 | 433 | 128 |

**Leitura:** os cantos atuais (R$ 27 mil a R$ 2,37 mi) quase nunca acontecem. Nos sorteios, nenhum ficou abaixo do dobro do canto mínimo e só 0,1% passou da metade do canto máximo, porque é raro todas as suposições irem ao extremo juntas. A **taxa** é a suposição que mais mexe no prêmio, seguida da escolha pelo seguro.

**O que será usado:** Monte Carlo triangular, com a faixa P5–P95 mostrada **ao lado** dos cantos (proposta ao autor; o valor base de R$ 368,7 mil não muda). A versão com as suposições de patrimônio juntas fica como sensibilidade. O tornado vai para o notebook 08 e para o simulador.

---

## Resumo: o que vai ser usado

| Teste | Método escolhido | Onde | Muda os 10 números? |
|---|---|---|---|
| T1 | Floresta aleatória (Poisson para explicar) | 06a, outros estados | Não |
| T2 | Tendência log-linear com semestre (SARIMA para comparar) | 07 | Não (projeção) |
| T3 | Floresta aleatória recalibrada com 2022–23 | 05b, 07 | Não (projeção) |
| T4 | Floresta aleatória (logística para explicar), como associação | 05a | Não |
| T5 | Remuneração média × razão, como sensibilidade | 01, 08 | Não (D-015 mantida) |
| T6 | Encolhimento amostra → região, como sensibilidade | 08 | Não (D-022 mantida) |
| T7 | Monte Carlo triangular ao lado dos cantos | 08, painel, simulador | Não |

Qualquer mudança na base depende de uma decisão nova (D-039 em diante) aprovada pelo autor.
