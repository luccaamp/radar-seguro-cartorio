# Plano completo do projeto — Radar Seguro-Garantia Cartórios

23/10/2026

> **Plano oficial do projeto (D-039).** Define as etapas, os portões e as decisões do autor até a entrega. O detalhamento da Etapa 1 (regras dos notebooks, critérios e partes) está no [`plano_mineracao.md`](plano_mineracao.md). Em conflito, vale este plano.

## Resumo

O projeto termina em seis etapas: mineração (notebooks 03 a 09), pipeline, painel, simulador, chat e entrega. A mineração já tem os métodos escolhidos, porque foram testados com os dados reais de MG antes de escrever este plano.

**Onde estamos (28/10/2026):** a primeira versão de MG (painel, simulador e chat reduzido, carga 2026-10-19) está concluída; a mineração terminou (notebooks 01 a 09, Portão 1 cumprido); a Etapa 2 (pipeline com as seis tabelas `gold.analise_*`) foi feita e conferida numa cópia (Portão 2 cumprido), com a D-043 proposta. A próxima é a Etapa 3 (painel).

## As perguntas do projeto

**A pergunta:** quanto dinheiro o seguro obrigatório dos cartórios (Prov. CNJ 227/2026) pode movimentar em Minas Gerais, **e quão certo é esse número?**

Ela tem duas metades, e cada uma está num ponto diferente:

| Metade | O que responde | Situação |
| --- | --- | --- |
| **"Quanto dinheiro"** | A escada de 9 perguntas abaixo, calculada pelo pipeline | ✅ **respondida** em 20/10/2026, para MG, no cenário de hoje (carga 2026-10-19) |
| **"Quão certo"** (e como muda) | Quanto confiar em cada degrau, o que mais pesa no resultado e como ele muda em 2026–27 | ✅ **respondida** em 28/10/2026 (notebooks 03 a 09; resumo no notebook 09): prêmio provável de R$ 206 a 736 mil (P5–P95); as lacunas que restam estão na tabela do 09 |

### Parte 1 — A escada (já respondida)

Cada resposta alimenta a próxima. Os números vêm do banco (`gold.fato_mercado_uf`, MG, regra de classe v2, cenário do STF "mantém"); a faixa vai do nível mínimo ao máximo das premissas.

| # | Pergunta | Como responde | Dado ou suposição | Resposta em MG (base) | Faixa (mín – máx) | Número oficial |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Quantos cartórios existem? | Conta os ativos | **Dado** (CNJ, cadastro) | 2.525 | — | nº 1 |
| 2 | Quantos funcionários CLT eles têm? | Soma o que cada cartório declara | **Dado** (CNJ) | 12.134 | — | nº 2 |
| 3 | Quantos são obrigados pela regra? | Tira a Classe 1 (até R$ 300 mil por semestre) e os sem titular | **Dado** + regra; a classe é aproximada (a receita publicada não é exatamente a da norma) | ≈ 1.121 | 1.103 – 1.159 | nº 3 |
| 4 | Quanto custaria demitir todos os funcionários? (a dívida, ou passivo) | Aviso prévio, férias, 13º, multa do FGTS e encargos de cada vínculo, como manda a norma | **Dado** (RAIS 2025, média salarial do município) + lei | R$ 311,9 mi (todos); R$ 238,1 mi (obrigados) | R$ 285,5 – 355,2 mi; R$ 216,4 – 279,8 mi | nºs 4 e 5 |
| 5 | Quantos não têm bens para cobrir a dívida? | Chance de déficit por classe | **Suposição** | ≈ 486 | 276 – 732 | nº 6 |
| 6 | Quanto falta, somando todos? | Parte da dívida sem bens, por classe | **Suposição** | R$ 36,9 mi | R$ 9,9 – 113,9 mi | nº 7 |
| 7 | Quanto disso vira seguro? | Divide o que falta entre bens, fiança e seguro | **Suposição** | R$ 18,4 mi garantidos | R$ 2,5 – 79,7 mi | nº 8 |
| 8 | Quanto as seguradoras receberiam por ano? | Valor garantido × taxa (2% na base) | **Suposição** (taxa) | R$ 368,7 mil | R$ 24,7 mil – 2,79 mi | nº 9 |
| 9 | Isso dá lucro para a seguradora? | Prêmio − prejuízos − comissão − despesas | **Dado** (SUSEP, 2020–2026) para prejuízos e comissão; **suposição** para as despesas | resultado técnico de R$ 236 mil por ano | de −R$ 218 mil a R$ 236 mil (no máximo, os prejuízos do ramo privado superam o prêmio) | — (no Simulador) |
| — | Qual o máximo possível? | Toda a dívida dos obrigados × 2%, como se ninguém tivesse bens | Não depende das suposições 5 a 7 | R$ 4,76 mi por ano | — | nº 10 (teto teórico) |

**Perguntas × números oficiais.** A escada tem 9 perguntas e o painel tem 10 números oficiais: as duas listas não são a mesma. A pergunta 4 dá dois números (o passivo de todas e o das obrigadas), a pergunta 9 é respondida no Simulador, sem um número único, e o nº 10 (teto teórico) é uma pergunta à parte. Os 10 números ficam fixos durante a mineração; mudar um deles exige uma decisão nova do autor.

**Dado × suposição.** As perguntas 1 a 4 se apoiam em dados públicos. Da 5 à 8, o cálculo precisa de coisas que ninguém publica: o patrimônio do titular, quanto dele cobre a dívida, quantos vão escolher seguro e a taxa que a seguradora vai cobrar. Sem isso, o projeto só daria o teto teórico. Essas suposições (`config/premissas/premissas_v002.yaml`, marcadas `fonte: suposição`) não vêm de dado: foram propostas pela IA e aprovadas pelo autor em 18/10/2026 (D-016), cada uma com uma justificativa tirada da norma (por exemplo, só contam bens penhoráveis, e a fiança só vale de bancos S1 ou S2). Por isso as respostas 5 a 9 sempre aparecem com faixa, e o Simulador deixa mudar cada suposição.

### Parte 2 — O que ainda falta responder ("quão certo" e "como muda")

A escada dá o número de hoje. Estas perguntas dizem quanto confiar nele e como ele muda. Nenhuma muda os 10 números: o que for diferente da base sai como sensibilidade ou projeção.

| Pergunta | Degraus da escada | Teste que escolheu o método | Onde responde | Situação |
| --- | --- | --- | --- | --- |
| Quão larga é, de verdade, a incerteza do prêmio? | 5 a 8 | T7 (Monte Carlo) | notebook 08 → painel e simulador | ✅ notebook 08 (23/10/2026): faixa P5–P95 de R$ 206 a 736 mil (T7: 207–737), cerca de 4,4 vezes mais estreita que a dos cantos; com as suposições de patrimônio juntas, R$ 155 a 906 mil. No painel, base > P5–P95 > cantos (D-042) |
| Qual suposição mais mexe no resultado? | 5 a 8 | T7 (tornado) | notebook 08 → simulador | ✅ notebook 08: a taxa (R$ 184–645 mil), seguida da escolha pelo seguro (R$ 184–516 mil); as premissas do passivo e do universo mexem menos de ±10% |
| O passivo (degrau 4) é robusto às escolhas de método? | 4 | T5 (salário ausente), T6 (reserva salarial) | notebook 08 | ✅ notebook 08: sim. Incluir os 887 vínculos muda +1,0% no passivo médio por vínculo e +0,6% no passivo total; o encolhimento (T6), −1,6%. Só na tabela de sensibilidade (D-042) |
| Quem é obrigado muda se a norma for lida ao pé da letra (receita líquida do repasse, art. 2º, XXIV, do Prov. 213)? | 3 a 8 | — | notebook 08 | ✅ notebook 08: o universo cai 20% (1.121 → 894) e o prêmio 8,5% (R$ 337,4 mil), com a faixa de déficit da base. Sensibilidade, sem mudar a base (D-042) |
| Quantos cartórios vão passar a ser obrigados em 2026 e 2027? | 3 | T3 (subida de classe) | notebooks 05b e 07 | ✅ notebooks 05b e 07: de 78 (07) a 145 (05b) subidas em 2026; universo de 1.147 em 2026 e 1.204 em 2027 com o limite fixo (projeção); as duas contagens ainda divergem (melhoria M4) |
| Quanto o mercado vai valer em 2026 e 2027? | 3 a 8 | T2 (arrecadação) | notebook 07 → painel | ✅ notebook 07 (27/10/2026): R$ 5,92 bi de arrecadação em 2026 e R$ 6,71 bi em 2027; prêmio entre R$ 366 e 369 mil (passivo de 2025). O 2026-1 "acima do P90" era, em grande parte, salto grosseiro; refazer com o semestre completo depende de coleta nova (M3) |
| Que tipo de cartório é obrigado, e qual é o cliente do seguro? | 3 e 7 | — | notebooks 03 e 04 | ✅ notebooks 03 e 04 (23/10/2026): RI (84% obrigadas) e 3 ou mais empregados (74% a 82%); cliente = providas grandes (grupo 6: 67% do passivo das obrigadas, 55% do déficit) |
| Como são os cartórios vagos (o risco que o seguro cobre)? | — | T4 (vacância) | notebook 05a | ✅ notebooks 05a e 05c (23/10/2026): AUC 0,88 (associação, não previsão); vacância observada de 2% a 7,5% ao ano |
| A escada vale para outros estados? | 2 e 4 | T1 (empregados pela receita) | notebook 06a; expansão depois da entrega | ✅ notebook 06 (23/10/2026): erro de 9,3% no total de uma região não vista (até 26%), −2,5% no total de MG; o passivo depende sobretudo da quantidade de empregados (75% a 79% da diferença entre cartórios). Só totais estaduais, com ±10% como piso e a RAIS como conferência (D-042) |
| O que os dados não respondem, e qual fonte resolveria? | 5 a 8 | — | notebook 09 | ✅ notebook 09 (28/10/2026): 8 lacunas (patrimônio do titular, taxa, adesão, fim da delegação, sinistros, 2026-1 completo, saltos, CLT fora de MG), com a fonte que resolveria cada uma |

**Fonte dos testes:** silver da carga 2026-10-19 (API do Justiça Aberta, RAIS 2025, IBGE) e as funções de `src/model/` do repositório, sem alterar o banco nem os 10 números. Script: `scripts/testes_metodos.py` (semente 42); resultados reproduzidos em 23/10/2026 com o silver do pacote da equipe (`carga-2026-10-19`). Explicação de cada teste e das métricas: [`qa/analises/testes_metodos.md`](qa/analises/testes_metodos.md).

## As etapas, da mineração à entrega

| Status | Etapa | O que faz | Portão para seguir |
| --- | --- | --- | --- |
| ✅ 20/10/2026 | Antes | Primeira versão de MG: pipeline, painel, simulador e os 10 números (carga 2026-10-19) | — |
| ✅ 21/10/2026 | Antes | Chat reduzido no painel (Ollama local, 5 ferramentas; D-036) | — |
| ✅ 22/10/2026 | 1 — parte A | Mineração: notebooks 01 (qualidade) e 02 (exploração), revisados | — |
| ✅ 23/10/2026 | 1 — preparo | Testes de métodos T1 a T7 ([`qa/analises/testes_metodos.md`](qa/analises/testes_metodos.md)) | — |
| ✅ 23/10/2026 | 1 — parte B | Mineração: notebooks 03 a 06 (e o extra 05c) | — |
| ✅ 28/10/2026 | 1 — parte C | Mineração: notebooks 07 a 09 (08 em 23/10, 07 em 27/10, 09 em 28/10) | **Portão 1:** ✅ cumprido em 28/10/2026 (01 a 08 em 27/10 e 09 em 28/10 rodados do zero com a mesma saída; os 10 números iguais) |
| ✅ 28/10/2026 | 2 | Pipeline (tabelas `gold.analise_*`; D-043 proposta) | **Portão 2:** ✅ cumprido numa cópia em 28/10/2026 (25 de 25 tabelas iguais e as 6 novas iguais às dos notebooks); falta a carga oficial, a pedido do autor |
| ✅ 28/10/2026 | 3 | Painel (D-049 proposta; `docs/painel/`, capturas em `docs/qa/painel/`) | — |
| ⬜ | 4 | Simulador | — |
| ⬜ | 5 | Chat | **Portão 3:** o critério "pronto quando" das etapas 3, 4 e 5 cumprido |
| ⬜ | 6 | Validação final, demo e entrega | — |

Cada portão só abre quando o seu critério é cumprido. Painel, simulador e chat dependem das mesmas tabelas do pipeline, então as etapas 3, 4 e 5 podem ser feitas em paralelo.

## Métodos de estimação testados

Sete pontos do projeto dependem de estimativa. Para cada um, testamos de 3 a 7 métodos contra uma referência simples, com o indicador fixado antes de rodar. Em todos, um método bate a referência; em dois (T2 e T3), o vencedor do passado erra para baixo em 2024–2026, e o plano trata isso.

| Teste | Pergunta (onde entra) | Validação | Indicador que decide | Vencedor | Vencedor × referência |
| --- | --- | --- | --- | --- | --- |
| T1 | Empregados CLT pela receita (06a; outros estados) | deixa uma das 13 regiões intermediárias de fora; 2.444 serventias | erro absoluto médio (MAE) por serventia, região fora | Floresta aleatória | MAE 1,86 × 2,34 (mediana por decil de receita); R² 0,75 |
| T2 | Arrecadação de MG em 2026–27 (07) | origem móvel: treina até 2019-2 … 2023-2, prevê 4 semestres | MAPE (erro % médio) | Tendência log-linear com efeito de semestre | 7,4% × 14,8% (repetir o último semestre) |
| T3 | Serventia abaixo de R$ 300 mil sobe de classe no ano seguinte? (05b) | temporal: treina até 2023, testa 2024–25 (2.692 casos) | Brier (erro da probabilidade) | Floresta aleatória | 0,068 × 0,099 (taxa histórica); AUC 0,88 |
| T4 | Serventia está vaga? (05a) | cruzada estratificada 5 × 3; 2.406 serventias | AUC | Floresta aleatória | 0,886 × 0,500; logística 0,848 |
| T5 | Salário de dezembro ausente (D-015) | esconde 20% dos salários conhecidos, 5 vezes | erro absoluto médio do passivo por vínculo | remuneração média × razão dezembro/média | 8,4% × 89% (excluir) |
| T6 | Salário de município com poucos vínculos (D-008, D-022) | nos 135 municípios com 20+ vínculos, finge ver só 5 | erro % do passivo médio por vínculo | encolhimento da amostra para a região (Bayes empírico) | 36,7% × 42,4% (região imediata, regra atual) |
| T7 | Faixa das suposições (passos 5 a 8) | sem valor real; 200 mil sorteios | largura e probabilidade declarada da faixa | Monte Carlo triangular | P5–P95 R$ 207–737 mil × cantos R$ 27 mil–2,37 mi |

**Por que esses indicadores.** O MAE com uma região de fora imita o uso real do T1 (um lugar que o modelo não viu). O Brier entra no T3 porque a projeção soma probabilidades para contar quantas sobem. No T7 não há valor real: o critério é a faixa dizer com que chance o número cai nela.

**O que cada resultado muda no plano**

- **T1 — nenhum método acerta o total com erro de até 5% quando a região sai.** O melhor erra 9,3% (floresta) e 8,8% (gradient boosting). Para outro estado: floresta por serventia e total publicado com ±10%. O Poisson fica perto (MAE 1,93) e serve quando for preciso explicar coeficientes.
- **T2 — o 1º semestre de 2026 já passou da previsão.** Mesmo incompleto (57 serventias sem informar), somou R$ 3,20 bi, 17% acima da previsão central e acima do P90. O notebook 07 refaz o teste com 2026-1 completo e testa uma quebra de nível em 2025-2 (conferir a serventia 042986, R$ 108 mi).
- **T3 — todos os modelos subestimam as subidas.** Previram 218 e houve 294 em 2024–25 (−26%): o crescimento nominal acelerou. Recalibrar com os anos recentes antes de projetar o universo; o cenário de limite corrigido pela inflação reduz as subidas.
- **T4 — leitura de associação, não de previsão.** Receita e CLT de uma vaga são medidos já sob interino, então parte do sinal vem da própria vacância (vazamento declarado no notebook).
- **T5 — manter a D-015 na base.** Só 154 dos 887 vínculos têm remuneração no ano; os outros 733 não têm salário nenhum. Os 887 têm mediana de 85 meses de casa (31 nos demais); incluí-los imputados sobe o passivo médio por vínculo de MG em 1,0%. Vira linha de sensibilidade.
- **T6 — a reserva atual (região imediata) foi a pior das reservas neste teste;** o estado ficou com 38,5%. Ressalva: os testados são os 135 maiores, que diferem mais da sua região do que os pequenos. O encolhimento ganha por pouco; entra como sensibilidade e não muda a base (regra da etapa).
- **T7 — os cantos atuais quase nunca acontecem.** Em 200 mil sorteios, 0,0% ficaram abaixo do dobro do canto mínimo e 0,1% acima da metade do máximo. Se as quatro suposições de patrimônio andarem juntas, a faixa P5–P95 vai a R$ 155–906 mil. A taxa é a suposição que mais mexe no prêmio (R$ 184–645 mil sozinha), seguida da escolha pelo seguro (R$ 184–516 mil).

Arrecadação semestral de MG, em R$ bilhões (API do Justiça Aberta, silver da carga 2026-10-19; previsão do T2 com a tendência log-linear e faixa P10–P90 dos erros do teste no passado):

| Semestre | Realizado | Previsão (P10 – central – P90) |
| --- | --- | --- |
| 2023-1 | 1,84 | — |
| 2023-2 | 2,18 | — |
| 2024-1 | 2,03 | — |
| 2024-2 | 2,50 | — |
| 2025-1 | 2,38 | — |
| 2025-2 | 3,13 | — |
| 2026-1 | 3,20 (parcial: 57 serventias sem informar) | 2,39 – 2,74 – 2,94 |
| 2026-2 | — | 2,78 – 3,18 – 3,42 |
| 2027-1 | — | 2,71 – 3,10 – 3,33 |
| 2027-2 | — | 3,14 – 3,61 – 3,87 |

A tendência que melhor previu o passado ficou abaixo do que 2026 já mostra, mesmo com 57 serventias ainda sem informar. Por isso a previsão do notebook 07 sai sempre com faixa e é refeita quando o semestre fechar.

## Etapa 1 — Mineração (notebooks 03 a 09)

A mineração é detalhada no [`plano_mineracao.md`](plano_mineracao.md) (regras, formato de cada notebook, critérios de qualidade e as partes A, B e C), com o método de cada notebook escolhido pelos testes acima. Cada notebook segue o formato: pergunta, método explicado, código curto em `src/analise/`, resultado, leitura e limitações. As tabelas `gold.analise_*` da coluna "Entrega" são desenhadas na Etapa 1 (função em `src/analise/`, com teste) e geradas pelo pipeline na Etapa 2.

| Notebook | Parte | Método principal | Referência a bater | Validação | Entrega |
| --- | --- | --- | --- | --- | --- |
| ✅ 01 Qualidade | A | faltantes, zeros, conflitos e outliers por fonte; consistência CNJ × RAIS × CNPJ × BI | — | — | feito em 22/10/2026; PNGs `01_*` em `docs/qa/analises/` |
| ✅ 02 Exploração | A | distribuições em escala log, por classe, atribuição, situação e região; série histórica | — | — | feito em 22/10/2026; PNGs `02_*` em `docs/qa/analises/` |
| 03 Padrões | B | Apriori (`mlxtend`) sobre atribuições, porte, classe, situação e região; regras com consequente "obrigada" | frequência simples de obrigadas por atribuição | regras que se repetem em 2 reamostragens de 80% | 10 regras com suporte, confiança e lift; `gold.analise_regras` |
| 04 Grupos | B | k-means em escala log (receita, CLT, nº de atribuições, situação), k de 2 a 8 pela silhueta; hierárquico Ward para comparar | — | silhueta e concordância k-means × Ward (índice de Rand ajustado) | perfil de cada grupo e o grupo-alvo do seguro; `gold.analise_grupos` |
| 05a Vacância | B | floresta aleatória (T4); logística para explicar os pesos | proporção de vagas | cruzada estratificada 5 × 3, AUC | importância por permutação; variáveis descartadas por vazamento |
| 05b Subida de classe | B | floresta aleatória (T3), recalibrada nos anos 2022–2023 | taxa histórica | temporal (treino até 2023, teste 2024–25), Brier | contagem esperada de subidas em 2026 e 2027 |
| ✅ 06a CLT pela receita | B | floresta aleatória (T1); Poisson como versão interpretável | mediana por decil de receita | região intermediária de fora, MAE | feito em 23/10/2026: MAE 1,86 × 2,34 da referência; `gold.analise_clt_modelo` desenhada; total com ±10% |
| ✅ 06b Passivo | B | decomposição: passivo = CLT × passivo médio por vínculo; regressão log-log nos resíduos | — | 10 dobras | feito em 23/10/2026: quantidade 75%, salário 18%, tempo de casa 6% (R² 0,99 fora da amostra); PNGs `06_*` |
| ✅ 07 Previsão | C | tendência log-linear com semestre (T2) e SARIMA, faixa P10–P90 dos erros do passado; refeito com 2026-1 completo | repetir o último semestre | origem móvel + treino até 2023 | arrecadação, universo, passivo, IS e prêmio de 2026–27, limite fixo e corrigido |
| ✅ 08 Sensibilidade | C | tornado + Monte Carlo (T7); curva de concentração e Gini; receita líquida do Prov. 213 | cantos atuais | — | feito em 23/10/2026: P5–P95 R$ 206–736 mil; Gini do passivo das obrigadas 0,63; `gold.analise_tornado` e `gold.analise_monte_carlo` desenhadas; PNGs `08_*` |
| ✅ 09 Conclusões | C | 8 a 10 achados com número, gráfico e frase; tabela de lacunas; recomendação ao painel | — | — | achados e lacunas para o painel e os slides |

**Lacunas já conhecidas para o 09** (nenhuma tem fonte pública hoje): patrimônio livre do titular (passos 5 e 6), taxa cobrada pelas seguradoras (passo 8) e a chance de a delegação terminar no ano (D-025, sinistro por frequência).

**Pronto quando:** os 7 notebooks rodam do zero com a mesma saída (semente fixa); cada modelo mostra a métrica contra a referência; os 10 números seguem iguais à linha de base; o relatório de cada parte está no `diario.md`.

## Etapa 2 — Pipeline

O que a mineração provar entra no pipeline como tabelas novas `gold.analise_*`, ao lado das 25 atuais, sem mexer nas que dão os 10 números. Mudar um dos 10 números exige uma decisão nova (D-043 em diante) aprovada pelo autor.

> **Feito em 28/10/2026 (D-043, proposta):** passos 1 a 3 e 5 completos; `pipeline.etapa_analise` grava as seis tabelas, e o pipeline do zero numa cópia deu 25 de 25 tabelas iguais, mais as 6 novas. Passo 4 em parte: o `gerar_publico.py` ganhou `--banco` e `--destino`, e a geração com as 4 tabelas agregadas passou nas travas numa cópia, mas o `data/publico/` só muda na próxima carga oficial (pedido do autor). As linhas novas da `sensibilidade_premissas` da D-042 ficaram de fora, porque mudariam uma das 25 tabelas.

1. Levar o cálculo dos notebooks para `src/analise/` com teste (o plano já exige); o pipeline chama essas funções.
2. Gerar as tabelas: `analise_regras`, `analise_grupos`, `analise_clt_modelo`, `analise_previsao` (2026–27 com P10–P90), `analise_tornado`, `analise_monte_carlo`.
3. Rodar o pipeline do zero numa cópia do banco: 25 de 25 tabelas antigas iguais à linha de base, mais as novas.
4. Atualizar o `gerar_publico.py` e o `manifesto.json`; decidir se a D-038 chega agora ao pipeline e ao auditor (pendência do autor).
5. Atualizar `dicionario_dados.md`, `SPEC.md` §3 e `ESTADO_ATUAL.md`.

**Decisões a propor ao autor, vindas dos testes** (nenhuma muda a base sozinha):

| Proposta | Origem | Efeito nos 10 números |
| --- | --- | --- |
| Faixa do prêmio com a hierarquia base > P5–P95 (R$ 210–740 mil) > cantos, para déficit, IS e prêmio (D-042, proposta) | T7, notebook 08 | nenhum (faixa nova, mesma base) |
| Salário estimado para os 887 vínculos sem dezembro, só na tabela de sensibilidade (D-042, proposta) | T5, notebook 08 | nenhum na base; +0,6% no passivo total se adotado |
| Encolhimento amostra → região, só na tabela de sensibilidade (D-042, proposta) | T6, notebook 08 | nenhum na base; −1,6% no passivo total se adotado |
| Receita líquida do repasse como sensibilidade do universo, com a faixa de déficit da base (D-042, proposta) | notebook 08 | nenhum na base; −20% no universo e −8,5% no prêmio se adotada |
| Previsão 2026–27 rotulada como projeção, nunca como número oficial | T2, T3 | nenhum |
| Regra para semestre com salto grosseiro (já pendente da parte A) | notebook 01 | até −11 obrigadas (≈ −1,0%) |

**Pronto quando:** pipeline do zero reproduz a linha de base e gera as tabelas novas; testes passam; conjunto público regenerado e conferido sem nome nem CPF.

## Etapas 3 a 5 — Painel, simulador e chat

As três peças já existem em versão de MG; aqui elas recebem os resultados da mineração e fecham o que falta para a demo.

**Etapa 3 — Painel (Streamlit, só leitura)**

Objetivo (desde 29/10/2026, D-051): **o painel responde a uma pergunta só**, a do projeto: *quanto dinheiro o seguro obrigatório dos cartórios (Prov. CNJ 227/2026) pode movimentar em Minas Gerais, e quão certo é esse número?* Todo o resto existe só para contar a história por trás da resposta. **O painel é a história; o chat é o detalhe:** um elemento que não ajuda a responder "quanto" ou "quão certo" sai do painel e fica no chat. (Até 28/10 o objetivo era "reunir todos os achados importantes"; o painel mostrava tudo e não informava nada: erro de direção registrado no `docs/erros_ia.md`.)

**Estrutura (terceira rodada, D-051; corte elemento a elemento em `docs/painel/corte.md`):**

| Página | Manchete | O que mostra |
|---|---|---|
| A resposta (Início) | "Quanto dinheiro o seguro obrigatório dos cartórios pode movimentar em Minas Gerais, e quão certo é esse número?" | o prêmio anual (valor base) em número grande, a faixa provável logo abaixo, uma frase de quão certo é e o funil da escada (cartórios ativos → obrigados → sem bens suficientes → déficit → vira seguro → prêmio) |
| Quão certo é | "Quão certo é o número?" | 2 números (parte da incerteza que vem da taxa e da adesão; o máximo que o dado público mexe), a faixa provável num gráfico (base, P5–P95 e extremos discretos) e as 5 suposições que mais pesam, com o valor na ponta |
| Onde está o mercado | "Onde está o dinheiro?" | um filtro (município), até 3 números, o mapa do déficit na largura da página e a concentração numa frase |
| Para onde vai | "Para onde vai o mercado até 2027?" | 2 números com o selo "projeção" (obrigados em 2027; dívida trabalhista em 2027), o prêmio projetado num gráfico com a faixa P10–P90 e uma frase de conclusão |
| Sobre os dados | "Sobre os dados" | os 10 números oficiais numa tabela compacta, fontes e datas, como foi calculado (carga, versão das premissas, regra de classe, nível) e 5 limitações |
| Chat | — | a página da Etapa 5; recebe as perguntas sugeridas das outras páginas pelo link `Chat?pergunta=` |

Regras da terceira rodada:
* Por página: uma manchete, no máximo 3 números em destaque, no máximo 2 gráficos, no máximo 2 frases por bloco e de 2 a 3 perguntas sugeridas para o chat. Nenhum número em destaque em duas páginas.
* **A fonte de cada número numa linha discreta** (só a fonte e a data); carga, versão das premissas, nível, regra de classe e UF ficam só em "Sobre os dados".
* **O STF e a ADI 8015 saem do painel inteiro** (etiquetas, cenários, cartões e textos); o assunto fica no chat. O painel supõe a regra do Provimento como publicada.
* O Simulador saiu da navegação (não responde "quão certo" melhor que o gráfico das sensibilidades); o arquivo continua em `app/simulador.py`, para a Etapa 4.
* As listas "Páginas" e a primeira regra abaixo são da segunda rodada (28/10) e ficam como histórico.

Antes de construir
* **Inventário de achados** (docs/painel/inventario_achados.md): todos os achados relevantes dos notebooks 01 a 09 e da Etapa 2. Para cada um: origem, número-chave, fonte e data, importância, onde entra no painel e em que formato. Achado de importância alta que ficar de fora precisa de justificativa.
* **Arquitetura da informação** (docs/painel/arquitetura.md):
  * a pergunta que cada página responde;
  * três níveis de leitura por página: 10 segundos (manchete), 1 minuto (gráficos centrais) e 5 minutos (detalhes e metodologia);
  * os filtros e o alcance de cada um.
* **Padrão visual** (docs/painel/padrao_visual.md, com tema em .streamlit/config.toml):
  * paleta com significado fixo (observado, projeção, incerteza), segura para daltonismo e com bom contraste;
  * tipografia e hierarquia;
  * uma única biblioteca de gráficos;
  * título que diz a conclusão, eixos com unidade, rodapé com fonte e data, formato brasileiro de números;
  * padrão único para faixa P5–P95 e para os rótulos da D-042.

Páginas (segunda rodada, 28/10/2026; substituídas pela estrutura da D-051, acima)
* **Início:**
  * os 10 números;
  * a "faixa provável" P5–P95 logo abaixo do déficit, da IS e do prêmio;
  * os cantos oficiais como nota secundária (D-042);
  * a situação da ADI 8015 conferida na véspera, com a data da conferência visível.
* **Mercado:**
  * mapa e filtros atuais;
  * os grupos do notebook 04;
  * o grupo-alvo do seguro.
* **Análises** (página nova ou seções no Mercado, decidido pelo inventário):
  * previsão 2026–27 com faixa;
  * concentração (Gini, com explicação para leigos);
  * os achados do 09;
  * os demais achados de importância alta do inventário.
* **Qualidade dos dados:**
  * as lacunas do 09;
  * o bloco "Passivo: escolhas de método" (T5 +0,6%, T6 −1,6% e a reserva no estado inteiro +5,9%);
  * a leitura literal do art. 2º, XXIV, do Prov. 213 (universo −20%, prêmio −8,5%);
  * tudo com os rótulos da D-042.

Regras
* Todo número com fonte e data de referência numa linha discreta (a versão das premissas fica em "Sobre os dados", D-051); projeção sempre rotulada.
* Números vêm do banco, de config/ ou dos artefatos das etapas anteriores, nunca fixos no código.
* Nenhum dado de pessoa física em tela, tooltip, download, log ou dado de demonstração.
* Interatividade com propósito: filtros, tooltips, expansores de metodologia e download dos dados agregados.
* Consultas com cache; nenhuma página demora mais que alguns segundos para abrir.
* Preparar para o chat da Etapa 5 (sem implementá-lo):
  * os números e as análises do painel (previsão com faixa, tornado, Gini, qualidade das fontes, decisões) saem de funções em src/, fora das páginas;
  * cada função devolve o valor junto com a conta, a fonte, a data de referência, a versão das premissas e o rótulo D-042, no mesmo formato que as ferramentas atuais do chat já usam;
  * as páginas só exibem o que essas funções devolvem, para que painel e chat mostrem sempre os mesmos números;
  * as ferramentas do chat que já existem continuam funcionando, e os testes delas continuam passando.

Pronto quando
* `tests/test_app.py` passa, cobrindo cada página no modo com banco e no modo demonstração, e conferindo os 10 números.
* O modo demonstração abre sem o banco local.
* Todo achado de importância alta do inventário está no painel ou tem justificativa para ficar de fora.
* A revisão foi feita em três olhares (dados, design e leitor leigo), com capturas de cada página em docs/qa/painel/.
* A página funciona em tela de 1366 px sem rolagem horizontal.

**Etapa 4 — Simulador**

- Controles atuais (taxa, escolha do seguro, market share, cenário do STF) e três novos: ano (2026 base, 2027 projeção), limite de classe fixo ou corrigido pela inflação, e a chave "faixa por sorteio" (Monte Carlo).
- Tornado ao vivo: mostra qual suposição mais mexe no resultado com os valores escolhidos.
- Os três cenários do STF (mantém, suspende os arts. 8º a 17, meio-termo), com o "suspende" zerando a demanda.
- **Pronto quando:** os testes do SPEC §3 passam (prêmio monotônico na taxa, suspende zera a demanda, mercado ≥ seguradora) e o simulador recalcula em menos de 1 segundo.

**Etapa 5 — Chat (Gemini, nível gratuito; D-060 a D-066)** — branch `etapa-5-chat`

- **Modelo:** só o Gemini, no nível gratuito do Google AI Studio, com o faturamento desligado (D-061, única exceção ao "100% gratuito"); nome do modelo em `config/llm.yaml`. O Ollama saiu do projeto (D-060, substitui a D-036). Funciona no link público (Streamlit Community Cloud, modo demonstração, lendo `data/publico/`) e na demo local dos dois PCs; a chave vem de `GEMINI_API_KEY` (ambiente, `.env` ou `st.secrets`).
- **O chat vê o que o painel vê:** 5 ferramentas (números, mercado, análises, qualidade, decisões e normas) que chamam as mesmas funções de `src/painel/analises.py` que as páginas; `tests/test_chat_cobertura.py` falha quando o painel ganha uma análise que o chat não alcança (D-062).
- **Sem Gemini, o chat não quebra:** perguntas prontas respondidas direto pelas ferramentas; até 20 perguntas ao modelo por sessão no link público (D-063).
- Gabarito de 52 perguntas (informais, com erro de digitação, ambíguas, fora do escopo, armadilhas, normas, gráficos e dados pessoais), congelado com hash; meta fixada antes da avaliação (D-065).
- Comparar as versões (a) sem ferramentas, (b) normas no prompt e (c) com ferramentas: acertos, alucinações, respostas sem fonte, "não sei" corretos e latência (`scripts/avaliar_chat.py`, com a API real, fora da suíte de testes).
- Regra mantida: o modelo não calcula; todo número vem de uma ferramenta, com conta e fonte. A suíte padrão (`uv run pytest`) passa sem chave e sem internet.
- **Pronto quando:** a versão (c) acerta pelo menos 85% do gabarito congelado e não inventa número em nenhuma armadilha.

## Etapa 6 — Validação final, demo e entrega

A entrega é a demo de 5 minutos com 5 slides, rodando no computador do autor, com o pacote `v1.0` publicado.

1. Conferir normas na véspera: ADI 8015, Provimentos 213, 227 e 243 e a atualização anual do limite de classe.
2. Rodar o pipeline do zero e conferir os 10 números contra a linha de base.
3. Revisão final de dados pessoais: nenhum nome nem CPF em painel, chat, notebook, gráfico ou arquivo publicado.
4. Slides: a pergunta, a escada de 9 perguntas (com os 10 números oficiais), o que é sólido × o que é suposição (faixa P5–P95), os 3 achados principais do 09, a decisão do STF.
5. Ensaiar a demo duas vezes: Início → Mercado → Simulador (mudar a taxa e o STF) → uma pergunta ao chat.
6. Release `v1.0` (o autor publica) e README com as limitações declaradas.

**Depois da entrega (opcional, nesta ordem):** expansão para outros estados com o modelo de CLT do T1 (validar primeiro num estado que tenha a contagem do CNJ) e, por último, o radar de normas.

### Riscos e o que fazer

| Risco | Efeito | O que fazer |
| --- | --- | --- |
| Liminar ou julgamento na ADI 8015 perto da entrega | mercado vai a zero no cenário "suspende" | cenário pronto no simulador; conferir na véspera |
| Arrecadação de 2026 muito acima da previsão (T2) | projeções de 2026–27 baixas demais | refazer o 07 com 2026-1 completo; mostrar a faixa |
| Subidas de classe subestimadas (T3) | universo de 2027 pequeno demais | recalibrar com 2022–23; dois cenários de limite |
| Suposições de patrimônio e taxa sem fonte | faixa larga do prêmio | Monte Carlo com faixa declarada; lacuna no 09 |
| Modelo de CLT erra ~9% no total fora da região (T1) | passivo de outros estados impreciso | publicar com ±10% e validar num estado com contagem |
| Painel aberto trava o pipeline (D-034) | carga falha | fechar o painel antes de rodar |

### Decisões que dependem do autor

| Decisão | Quando decidir | Por quê |
| --- | --- | --- |
| [ ] Decidir a regra para semestre com salto grosseiro e conferir as serventias 042986 e 035030 no Justiça Aberta | **Etapa 1**, antes da parte C (notebook 07) | o 07 testa a quebra de nível em 2025-2, que depende da 042986; a regra pode mudar os 10 números (até −11 obrigadas), então precisa estar decidida antes do pipeline |
| [ ] Aprovar as propostas da Etapa 2 (faixa P5–P95, sensibilidades T5 e T6, previsão rotulada) | **Portão 1**, no fim da Etapa 1 | o pipeline só gera as tabelas `gold.analise_*` aprovadas |
| [ ] Decidir se a D-038 chega ao pipeline, ao auditor e ao `gerar_publico.py` | **Etapa 2**, antes do passo 4 (`gerar_publico.py`) | o painel novo da Etapa 3 lê o conjunto público gerado aqui |
| [x] Fixar a meta de acerto do chat no gabarito congelado (85%, D-065, 2026-10-28) | **Início da Etapa 5**, antes da avaliação | a meta é o critério de pronto do chat e não pode ser fixada depois de ver o resultado |
| [ ] Confirmar se a expansão para outros estados entra antes ou depois da entrega | **Portão 3**, antes da Etapa 6 | se entrar antes, muda o escopo da entrega e dos slides |
