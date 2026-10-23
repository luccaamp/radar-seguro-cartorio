# Plano completo do projeto — Radar Seguro-Garantia Cartórios

23/10/2026 · @Leticia

> **Plano oficial do projeto (D-039).** Define as etapas, os portões e as decisões do autor até a entrega. O detalhamento da Etapa 1 (regras dos notebooks, critérios e partes) está no [`plano_mineracao.md`](plano_mineracao.md). Em conflito, vale este plano.

## Resumo

O projeto termina em seis etapas: mineração (notebooks 03 a 09), pipeline, painel, simulador, chat e entrega. A mineração já tem os métodos escolhidos, porque foram testados com os dados reais de MG antes de escrever este plano.

**Onde estamos (23/10/2026):** a primeira versão de MG (painel, simulador e chat reduzido, carga 2026-10-19) está concluída; parte A da mineração feita (notebooks 01 e 02).

## As perguntas do projeto

**A pergunta:** quanto dinheiro o seguro obrigatório dos cartórios (Prov. CNJ 227/2026) pode movimentar em Minas Gerais, **e quão certo é esse número?**

Ela tem duas metades, e cada uma está num ponto diferente:

| Metade | O que responde | Situação |
| --- | --- | --- |
| **"Quanto dinheiro"** | A escada de 9 perguntas abaixo, calculada pelo pipeline | ✅ **respondida** em 20/10/2026, para MG, no cenário de hoje (carga 2026-10-19) |
| **"Quão certo"** (e como muda) | Quanto confiar em cada degrau, o que mais pesa no resultado e como ele muda em 2026–27 | ⬜ **em andamento:** os testes T1 a T7 já escolheram os métodos; os notebooks 03 a 09 respondem |

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
| Quão larga é, de verdade, a incerteza do prêmio? | 5 a 8 | T7 (Monte Carlo) | notebook 08 → painel e simulador | teste feito: a faixa realista é R$ 207 – 737 mil (P5–P95), bem mais estreita que a dos cantos |
| Qual suposição mais mexe no resultado? | 5 a 8 | T7 (tornado) | notebook 08 → simulador | teste feito: a taxa, seguida da escolha pelo seguro |
| O passivo (degrau 4) é robusto às escolhas de método? | 4 | T5 (salário ausente), T6 (reserva salarial) | notebook 08 | teste feito: incluir os 887 vínculos muda +1,0% |
| Quantos cartórios vão passar a ser obrigados em 2026 e 2027? | 3 | T3 (subida de classe) | notebooks 05b e 07 | teste feito; os modelos subestimam as subidas e precisam de recalibração |
| Quanto o mercado vai valer em 2026 e 2027? | 3 a 8 | T2 (arrecadação) | notebook 07 → painel | teste feito; o 2026-1 já passou da previsão e o 07 refaz com o semestre completo |
| Que tipo de cartório é obrigado, e qual é o cliente do seguro? | 3 e 7 | — | notebooks 03 e 04 | ⬜ parte B |
| Como são os cartórios vagos (o risco que o seguro cobre)? | — | T4 (vacância) | notebook 05a | ⬜ parte B (leitura de associação, não de previsão) |
| A escada vale para outros estados? | 2 e 4 | T1 (empregados pela receita) | notebook 06a; expansão depois da entrega | teste feito: erro de ~9% no total de uma região não vista |
| O que os dados não respondem, e qual fonte resolveria? | 5 a 8 | — | notebook 09 | ⬜ parte C; já conhecidas: patrimônio do titular, taxa das seguradoras e chance de a delegação terminar |

**Fonte dos testes:** silver da carga 2026-10-19 (API do Justiça Aberta, RAIS 2025, IBGE) e as funções de `src/model/` do repositório, sem alterar o banco nem os 10 números. Script: `scripts/testes_metodos.py` (semente 42); resultados reproduzidos em 23/10/2026 com o silver do pacote da equipe (`carga-2026-10-19`). Explicação de cada teste e das métricas: [`qa/analises/testes_metodos.md`](qa/analises/testes_metodos.md).

## As etapas, da mineração à entrega

| Status | Etapa | O que faz | Portão para seguir |
| --- | --- | --- | --- |
| ✅ 20/10/2026 | Antes | Primeira versão de MG: pipeline, painel, simulador e os 10 números (carga 2026-10-19) | — |
| ✅ 21/10/2026 | Antes | Chat reduzido no painel (Ollama local, 5 ferramentas; D-036) | — |
| ✅ 22/10/2026 | 1 — parte A | Mineração: notebooks 01 (qualidade) e 02 (exploração), revisados | — |
| ✅ 23/10/2026 | 1 — preparo | Testes de métodos T1 a T7 ([`qa/analises/testes_metodos.md`](qa/analises/testes_metodos.md)) | — |
| ⬜ próxima | 1 — parte B | Mineração: notebooks 03 a 06 | — |
| ⬜ | 1 — parte C | Mineração: notebooks 07 a 09 | **Portão 1:** os notebooks rodam do zero com a mesma saída e os 10 números seguem iguais à linha de base |
| ⬜ | 2 | Pipeline (tabelas `gold.analise_*`) | **Portão 2:** o pipeline do zero reproduz a linha de base e gera as tabelas novas |
| ⬜ | 3 | Painel | — |
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
| 06a CLT pela receita | B | floresta aleatória (T1); Poisson como versão interpretável | mediana por decil de receita | região intermediária de fora, MAE | `gold.analise_clt_modelo`; total com ±10% |
| 06b Passivo | B | decomposição: passivo = CLT × passivo médio por vínculo; regressão log-log nos resíduos | — | 10 dobras | quanto do passivo vem de quantidade, salário e tempo de casa |
| 07 Previsão | C | tendência log-linear com semestre (T2) e SARIMA, faixa P10–P90 dos erros do passado; refeito com 2026-1 completo | repetir o último semestre | origem móvel + treino até 2023 | arrecadação, universo, passivo, IS e prêmio de 2026–27, limite fixo e corrigido |
| 08 Sensibilidade | C | tornado + Monte Carlo (T7); curva de concentração e Gini; receita líquida do Prov. 213 | cantos atuais | — | `gold.analise_tornado`, `gold.analise_monte_carlo` |
| 09 Conclusões | C | 8 a 10 achados com número, gráfico e frase; tabela de lacunas; recomendação ao painel | — | — | achados e lacunas para o painel e os slides |

**Lacunas já conhecidas para o 09** (nenhuma tem fonte pública hoje): patrimônio livre do titular (passos 5 e 6), taxa cobrada pelas seguradoras (passo 8) e a chance de a delegação terminar no ano (D-025, sinistro por frequência).

**Pronto quando:** os 7 notebooks rodam do zero com a mesma saída (semente fixa); cada modelo mostra a métrica contra a referência; os 10 números seguem iguais à linha de base; o relatório de cada parte está no `diario.md`.

## Etapa 2 — Pipeline

O que a mineração provar entra no pipeline como tabelas novas `gold.analise_*`, ao lado das 25 atuais, sem mexer nas que dão os 10 números. Mudar um dos 10 números exige uma decisão nova (D-041 em diante) aprovada pelo autor.

1. Levar o cálculo dos notebooks para `src/analise/` com teste (o plano já exige); o pipeline chama essas funções.
2. Gerar as tabelas: `analise_regras`, `analise_grupos`, `analise_clt_modelo`, `analise_previsao` (2026–27 com P10–P90), `analise_tornado`, `analise_monte_carlo`.
3. Rodar o pipeline do zero numa cópia do banco: 25 de 25 tabelas antigas iguais à linha de base, mais as novas.
4. Atualizar o `gerar_publico.py` e o `manifesto.json`; decidir se a D-038 chega agora ao pipeline e ao auditor (pendência do autor).
5. Atualizar `dicionario_dados.md`, `SPEC.md` §3 e `ESTADO_ATUAL.md`.

**Decisões a propor ao autor, vindas dos testes** (nenhuma muda a base sozinha):

| Proposta | Origem | Efeito nos 10 números |
| --- | --- | --- |
| Painel mostra a faixa P5–P95 do Monte Carlo ao lado dos cantos min/max | T7 | nenhum (faixa nova, mesma base) |
| Imputar os 154 vínculos com remuneração média, como sensibilidade | T5 | nenhum na base; +1,0% no passivo médio se adotado |
| Encolhimento amostra → região como sensibilidade da reserva salarial | T6 | nenhum na base |
| Previsão 2026–27 rotulada como projeção, nunca como número oficial | T2, T3 | nenhum |
| Regra para semestre com salto grosseiro (já pendente da parte A) | notebook 01 | até −11 obrigadas (≈ −1,0%) |

**Pronto quando:** pipeline do zero reproduz a linha de base e gera as tabelas novas; testes passam; conjunto público regenerado e conferido sem nome nem CPF.

## Etapas 3 a 5 — Painel, simulador e chat

As três peças já existem em versão de MG; aqui elas recebem os resultados da mineração e fecham o que falta para a demo.

**Etapa 3 — Painel (Streamlit, só leitura)**

- Início: os 10 números, com a faixa P5–P95 ao lado dos cantos e a situação da ADI 8015 conferida na véspera.
- Mercado: mapa e filtros atuais, mais os grupos do notebook 04 e o grupo-alvo do seguro.
- Página nova "Análises" (ou seções no Mercado): previsão 2026–27 com faixa, concentração (Gini) e os achados do 09.
- Qualidade dos dados: as lacunas do 09 e as linhas de sensibilidade novas (T5, T6).
- Todo número com fonte, data de referência e versão das premissas; projeção sempre rotulada.
- **Pronto quando:** `tests/test_app.py` passa e o modo demonstração abre sem o banco local.

**Etapa 4 — Simulador**

- Controles atuais (taxa, escolha do seguro, market share, cenário do STF) e três novos: ano (2026 base, 2027 projeção), limite de classe fixo ou corrigido pela inflação, e a chave "faixa por sorteio" (Monte Carlo).
- Tornado ao vivo: mostra qual suposição mais mexe no resultado com os valores escolhidos.
- Os três cenários do STF (mantém, suspende os arts. 8º a 17, meio-termo), com o "suspende" zerando a demanda.
- **Pronto quando:** os testes do SPEC §3 passam (prêmio monotônico na taxa, suspende zera a demanda, mercado ≥ seguradora) e o simulador recalcula em menos de 1 segundo.

**Etapa 5 — Chat (Ollama local, `qwen3:8b`)**

- Completar a E5: gabarito de 40 a 60 perguntas rotulado pelo autor e congelado com hash; as duas ferramentas que faltam (qualidade das fontes e decisões) e uma nova para as análises (previsão e tornado).
- Comparar as versões (a) sem ferramentas, (b) normas no prompt e (c) com ferramentas: acertos, alucinações, respostas sem fonte, "não sei" corretos e latência.
- Regra mantida: o modelo não calcula; todo número vem de uma ferramenta, com conta e fonte.
- **Pronto quando:** a versão (c) atinge a meta de acerto que o autor fixar no gabarito, sem número inventado nas armadilhas.

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
| [ ] Fixar a meta de acerto do chat no gabarito congelado | **Início da Etapa 5**, antes da avaliação | a meta é o critério de pronto do chat e não pode ser fixada depois de ver o resultado |
| [ ] Confirmar se a expansão para outros estados entra antes ou depois da entrega | **Portão 3**, antes da Etapa 6 | se entrar antes, muda o escopo da entrega e dos slides |
