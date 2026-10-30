# Plano da mineração de dados de MG (Etapa 1)

> **O que é:** o detalhamento da **Etapa 1 — Mineração** do [`plano_projeto.md`](plano_projeto.md), o plano oficial do projeto (D-039). Aqui ficam as regras, o formato dos notebooks, os critérios de qualidade e o que cada notebook entrega. A visão geral, os portões e as decisões do autor ficam no plano do projeto. **Em conflito, vale o `plano_projeto.md`.**
> **Como usar:** em toda sessão desta etapa, a IA lê este arquivo inteiro e executa **só a parte pedida** (A, B ou C), com uma parada no fim de cada parte.
> **Criado em:** 2026-10-22. **Atualizado em:** 2026-10-28 (parte C fechada com o notebook 09; Portão 1 cumprido). Vira histórico: a Etapa 2 (pipeline) foi feita na mesma sessão, e as melhorias M1 a M10 também (notebook 10).

---

## 1. Objetivo

Entender a fundo os dados de MG e o mercado do Prov. 227: qualidade, exploração, padrões, grupos, classificação, regressão, previsão, sensibilidade e as lacunas que pedem fontes novas.

**Quem lê os notebooks precisa entender tudo**, inclusive pessoas da equipe que não participaram do projeto.

## 2. Regras

As regras do `CLAUDE.md` continuam (nada de commit sem pedido, não apagar dados, 100% gratuito, nenhum nome nem CPF de pessoa física, nenhum número sem fonte, cópia do banco), com estas regras próprias da etapa:

- **Os 10 números oficiais não mudam** nesta etapa. Tudo o que for diferente da base é sensibilidade ou projeção, rotulado como tal. Se algo indicar que o cálculo do painel deveria mudar, a IA avisa no relatório em vez de mudar.
- **Os métodos já foram escolhidos** pelos testes T1 a T7 ([`qa/analises/testes_metodos.md`](qa/analises/testes_metodos.md); script `scripts/testes_metodos.py`). O notebook usa o método vencedor, compara com a mesma referência do teste e mostra se o resultado bate com o do teste. Trocar de método só com o motivo escrito no notebook e no relatório.
- **Todos os notebooks vão para o git, em `notebooks/`, com as saídas** (D-038). Os notebooks podem usar todos os dados, inclusive `interno_*` e os resultados por cartório, identificados pelo CNS e pelo município (nunca pelo nome do responsável).
- **Cálculo reutilizável fica em `src/analise/`**, com teste. Os notebooks leem dados só por `src/notebooks.py` e chamam essas funções.
- **Tabelas para o painel:** o notebook desenha a tabela `gold.analise_*` (a função em `src/analise/` que a produz, com teste). Quem a grava no banco é o pipeline, na Etapa 2.
- **Gráficos** exportados em PNG em `docs/qa/analises/` (vão para o git), com nomes que dizem o conteúdo e o número do notebook na frente (`03_...png`).
- **Bibliotecas:** `scikit-learn`, `statsmodels` e `mlxtend` já estão no projeto. Pode adicionar outras gratuitas com `uv add`, listando no relatório.
- **Decida sozinho os detalhes pequenos.** Pare antes do fim da parte só se algo mudar os 10 números oficiais ou tocar em LGPD.
- Se a sessão estiver perto do limite, registre no `diario.md` onde parou, para a próxima sessão continuar.

## 3. Como cada notebook deve ser escrito

Cada seção tem, nesta ordem:
1. **A pergunta**, em uma frase.
2. **O método**, em português simples: o que é, **a fórmula ou a conta explicada com um exemplo pequeno**, e por que esse método e não outro (citando o teste que o escolheu).
3. **O código**, curto, chamando `src/analise/`.
4. **O resultado** (tabela ou gráfico).
5. **Como ler o resultado** e **o que ele significa para o mercado do Prov. 227**.
6. **Limitações:** o que esse resultado não diz.

Nada de código sem explicação. Termos técnicos explicados na primeira vez em que aparecem (por exemplo: mediana, quartil, correlação, R², validação cruzada, AUC, Brier, MAPE, lift, silhueta). O glossário de métricas do `testes_metodos.md` pode ser reaproveitado.

## 4. Critérios de qualidade (a banca vai perguntar)

- **Todo modelo tem uma referência simples** (o "chute": a média, a classe mais comum, o valor do semestre anterior) e só vale se for melhor que ela. A referência de cada notebook é a do teste correspondente (seção 5).
- **Validação honesta:**
  - validação cruzada nos modelos sem tempo;
  - nos modelos com tempo, **treinar só com o passado e testar no futuro** (nunca misturar);
  - nenhuma variável que "entregue a resposta" (vazamento). Exemplo: para prever vacância, não usar nada que só existe porque o cartório já está vago. Dizer no notebook quais variáveis foram descartadas por esse motivo.
- **Métricas explicadas** e sempre comparadas com a referência.
- **Incerteza:** previsões e projeções com faixa, não só um número.
- **Reprodutível:** semente fixa (a de `config/analise.yaml`) e o mesmo resultado ao rodar de novo. Os testes T1 a T7 usaram a semente 42; resultados um pouco diferentes nos notebooks por causa da semente são esperados e não precisam ser explicados.

---

## 5. Os notebooks

O resumo de cada um (método, referência, validação e entrega) está na tabela da Etapa 1 do [`plano_projeto.md`](plano_projeto.md). Aqui fica o que o notebook precisa cobrir.

### ✅ 01 — Qualidade e dados faltantes (parte A, feito em 2026-10-22)
O que falta em cada fonte e campo, valores atípicos, consistência entre fontes (CNJ × RAIS × CNPJ × BI do CNJ) e a conclusão sobre o que é confiável. Pendente do autor: a regra para semestre com salto grosseiro e a conferência das serventias 042986 e 035030.

### ✅ 02 — Análise exploratória (parte A, feito em 2026-10-22)
Distribuições em escala log, recortes por classe, atribuição, situação e região, série histórica da arrecadação e correlações.

### ✅ 03 — Padrões frequentes (parte B, feito em 2026-10-23)
- Regras de associação (Apriori, `mlxtend`) sobre as combinações de atribuições e características (porte, classe, situação, região), com foco nas regras que terminam em "obrigada".
- Suporte, confiança e lift explicados com um exemplo.
- **Referência:** a frequência simples de obrigadas por atribuição. Uma regra só interessa se o lift mostrar que ela diz mais que essa frequência.
- **Estabilidade:** manter só as regras que se repetem em 2 reamostragens de 80%.
- **Entrega:** as 10 regras principais e o que indicam para o mercado; desenho da `gold.analise_regras`.

### ✅ 04 — Agrupamentos (parte B, feito em 2026-10-23)
- k-means em escala log (receita, empregados, número de atribuições, situação), com k de 2 a 8 escolhido pela silhueta e pelo cotovelo; hierárquico (Ward) para comparar, com a concordância medida pelo índice de Rand ajustado.
- Perfil de cada grupo: quantos cartórios, receita e empregados medianos, % obrigadas, passivo e déficit esperados, atribuições típicas.
- **Qual grupo é o mercado-alvo do seguro e por quê.**
- **Entrega:** desenho da `gold.analise_grupos`.

### ✅ 05 — Classificação (parte B, feito em 2026-10-23)
Dois alvos com resposta real nos dados. Para cada um: referência, modelo vencedor do teste, logística para explicar os pesos, matriz de confusão, precisão, recall, AUC e Brier explicados, quais variáveis mais pesam (importância por permutação) e o que o resultado significa para o seguro.
- **(a) Vacância (teste T4):** floresta aleatória contra a proporção de vagas; validação cruzada estratificada 5 × 3; indicador AUC. **Vazamento declarado:** a receita e os empregados de um cartório vago são medidos já sob interino. O resultado é lido como **associação** ("cartórios vagos costumam ser assim"), não como previsão de quem vai vagar.
- **(b) Subida de classe (teste T3):** prever se o cartório passa de R$ 300 mil no ano seguinte, usando só a série até o ano anterior. Floresta aleatória contra a taxa histórica; validação temporal (treino até 2023, teste em 2024–25); indicador Brier. O teste mostrou que **todos os modelos subestimam as subidas** (218 previstas × 294 reais): recalibrar com 2022–23 e mostrar o efeito. **Entrega:** a contagem esperada de subidas em 2026 e 2027, com faixa (insumo do 07).

### ✅ 06 — Regressão (parte B, feito em 2026-10-23)
- **(a) Empregados CLT pela receita (teste T1):** floresta aleatória contra a mediana por faixa de receita; Poisson como versão interpretável. Validação deixando uma região intermediária de fora; indicador MAE. O teste mostrou erro de ~9% no total de uma região não vista: o total sai com ±10%. **Uso:** estimar empregados nos estados onde o CNJ não traz essa informação. **Entrega:** desenho da `gold.analise_clt_modelo`.
- **(b) Passivo por serventia:** decomposição do passivo em quantidade (CLT), salário e tempo de casa (passivo = CLT × passivo médio por vínculo), com regressão log-log nos resíduos e validação em 10 dobras. Mostra quanto do passivo vem de cada parte.
- Resíduos e limites de cada modelo.

### ✅ 07 — Previsão do mercado (parte C, feito em 2026-10-27)
- **Arrecadação de 2026 e 2027 (teste T2):** tendência log-linear com efeito de semestre, com o SARIMA para comparar, contra a referência "repete o último semestre". Faixa P10–P90 a partir dos erros do teste no passado.
- **Teste no passado:** origem móvel (treinos até 2019-2 … 2023-2) e o teste do treino até 2023, com MAPE e viés.
- **Atenção:** o 2026-1, mesmo incompleto, já passou do P90 da previsão do teste. Refazer com o 2026-1 completo, se já estiver disponível, e testar uma quebra de nível em 2025-2 (serventia 042986). Se o autor ainda não tiver decidido a regra do salto grosseiro, rodar com a regra atual e mostrar a quebra como sensibilidade.
- Com a previsão e a subida de classe do 05b, projetar para 2026 e 2027: quantos cartórios passam do limite, o universo de obrigadas, o passivo, a IS e o prêmio do mercado.
- **Dois cenários:** limite fixo e limite corrigido pela inflação (art. 16, §2º, do Prov. 213).
- Tudo rotulado como **projeção**, nunca como número oficial. **Entrega:** desenho da `gold.analise_previsao`.

### ✅ 08 — Sensibilidade e concentração (parte C, adiantado e feito em 2026-10-23)
- **Tornado e Monte Carlo (teste T7):** cada premissa sozinha do mínimo ao máximo; Monte Carlo triangular com a faixa P5–P95 ao lado dos cantos atuais (mínimo e máximo). A variante com as suposições de patrimônio juntas fica como sensibilidade. Usar as funções do modelo. **Entrega:** desenho da `gold.analise_tornado` e da `gold.analise_monte_carlo`.
- **Sensibilidades do passivo:** salário de dezembro ausente (teste T5: incluir os 887 vínculos com salário estimado, +1,0% no passivo médio) e reserva salarial por encolhimento (teste T6). Sem mudar a base (D-015 e D-022 mantidas).
- **Concentração:** curva de concentração e índice de Gini do passivo e da receita (quanto os 10% maiores concentram).
- **Receita líquida do Prov. 213, como sensibilidade:** citar o texto literal do art. 2º, XXIV, a partir do bronze; medir quantos providos ficam acima de R$ 300 mil pela arrecadação e pela arrecadação menos o repasse (CSV do BI), e o efeito no universo e no prêmio. **Sem mudar a base.**

### ✅ 09 — Conclusões e lacunas (parte C, feito em 2026-10-28)
- Os **8 a 10 achados principais**, cada um com o número, o gráfico e a frase para a apresentação.
- **Tabela de lacunas:** o que os dados não responderam, por quê, e se uma **fonte nova** resolveria (qual, se é pública e gratuita, se existe para todos os estados, quanto mudaria a análise). Já conhecidas: patrimônio livre do titular, taxa cobrada pelas seguradoras e a chance de a delegação terminar no ano (D-025).
- **Recomendação para o painel:** quais gráficos entram e em qual página (insumo das etapas 3 e 4).

### ✅ 10 — Melhorias de confiança (propostas de 2026-10-27; feitas em 2026-10-28)

> **2026-10-28:** o 09 foi feito antes das melhorias; no mesmo dia, as dez foram feitas no **notebook 10** (`notebooks/10_melhorias_confianca.ipynb`, `src/analise/melhorias.py`, D-045), e o 09 foi rodado de novo com elas. Status de cada uma:
> - **M1** feita: pela renda, a chance de déficit é de 6,9% (Classe 2) e 9,6% (Classe 3), contra 50% e 30% supostos; o total quase não muda (R$ 34,5 mi × R$ 36,9 mi). **Levada à base pela D-046** (premissas v3), depois de conferir as 50 obrigadas com saldo ≤ 0.
> - **M2** feita: com a M1, sinistralidade de 12% a 46% e lucro técnico; sem ela, prejuízo. O B2 e o B3 entraram (índice combinado; 243 apólices, prêmio médio de R$ 1,5 mil).
> - **M3** feita em parte: (b) teste desde 2012: o SARIMA ganha no longo prazo, a tendência na janela recente (mantida); (c) faixa da arrecadação com 86% de cobertura; a da contagem, calibrada (60%, contra 27%). (a) **fora** (D-046): o autor decidiu não usar a coleta de 28/10.
> - **M4** feita e **rejeitada**: o desvio condicionado não melhora; o erro das subidas vem da previsão de MG.
> - **M5** feita: passivo +14,6% em 2026 e +28,5% em 2027 (só no notebook 10; a tabela da projeção atualizada saiu com a coleta de 28/10, D-046).
> - **M6** feita: (a) faixa do universo de 894 a 1.121; (b) **regra do salto decidida (D-046)**: valor declarado na classe, aviso no pipeline e sensibilidade "sem os saltos"; (c) **fora** (D-046, sem coleta nova).
> - **M7** feita: prêmio por cenário do STF; andamento da ADI conferido em 28/10 (sem liminar).
> - **M8** feita: a SES não publica a importância segurada; grade taxa × adesão.
> - **M9** **fora** (D-046): dependia da coleta de 28/10, que o autor decidiu não usar.
> - **M10** feita: pela M1, as providas grandes têm 85% do déficit.

Da validação de todos os notebooks (`diario.md`, 2026-10-27). Nenhuma muda os 10 números sozinha: cada uma entra como sensibilidade ou projeção e, se for para a base, vira decisão nova (D-043 em diante). Todas usam dado público e gratuito; as que pedem coleta nova só rodam a pedido do autor (regra do `CLAUDE.md`).

| # | Análise e problema | Melhoria | Dado | Esforço | Ganho |
|---|---|---|---|---|---|
| M1 | **Degraus 5 e 6** (déficit): `prob_deficit` e `pct_descoberto` são só suposição (50% e 30% de chance de déficit nas Classes 2 e 3, na base) | **Capacidade de pagar com dado:** passivo ÷ saldo anual do titular (arrecadação − repasse − custeio, BI do CNJ), por serventia. Já medido em 18/10 (F6): 708 obrigadas cobrem o passivo com menos de 3 meses de saldo, 260 com 3 a 12 meses, 41 precisam de mais de 12, 47 têm saldo ≤ 0 e 74 não têm dado. Faixa de déficit por "meses de saldo", lado a lado com a por classe (é o B6 + F6 da lista de 18/10). Saldo é renda, não patrimônio: serve para calibrar, não para trocar a regra do art. 8º, § 1º | CSV do BI no bronze (contrato para o custeio repetido por atribuição no 2025-2) | médio | **alto**: tira a maior parte do "só suposição" dos passos 5 e 6 |
| M2 | **Pergunta 9** (lucro da seguradora) sem notebook; sinistralidade da SES de 1,7% a 73,9% (carteira de obras e contratos, outro risco) | **Sinistro por frequência × severidade (D-025):** P(fim da delegação) do 05c (≈ 4% ao ano; 2% a 7,5%) × P(não paga), aproximada pelo M1 (saldo ≤ 0 ou passivo acima de 12 meses de saldo), × déficit. Comparar a sinistralidade resultante com a da SES. Junto, o B2 e o B3 de 18/10 (índice combinado; prêmio mínimo e custo por apólice) | 05c, M1, SES no silver | médio | **alto**: a pergunta 9 passa a ter resposta própria |
| M3 | **Projeção 2026–27** (07): a principal supõe +7,3% em 2026, mas o 2026-1 limpo e completado está +22% sobre o 2025-1 | (a) **coleta e carga novas** com o 2026-1 completo (e o 2026-2, quando sair); (b) **origem móvel mais longa** (origens desde 2012-2) e escolha pela janela recente, testando a média de tendência e SARIMA; (c) conferir a **cobertura** das faixas no passado e alargá-las até cobrir ≈ 80% | API do Justiça Aberta (gratuita) | baixo a médio | médio: previsão menos conservadora e faixa honesta |
| M4 | **Subidas** (05b × 07: 145 × 78 em 2026); a recalibração do 05b piora na origem móvel | **Desvio condicionado:** sortear o desvio da serventia entre as que tiveram crescimento recente parecido (persistência, que é o que a floresta do 05b aproveita), e testar no mesmo teste no passado do 07. Se ganhar, as duas contagens convergem | série do silver | baixo | médio: uma só contagem de subidas, testada |
| M5 | **Prêmio projetado** com o passivo de 2025 | **Passivo de 2026 e 2027:** tempo de casa + 12 meses por vínculo (conta da lei, sem suposição) e salário corrigido pelo INPC realizado (IBGE, já no banco); as contratações ficam fora | RAIS 2025 e INPC | baixo | médio: prêmio projetado em valores do ano |
| M6 | **Degrau 3** (universo): a leitura literal da receita (art. 2º, XXIV) tira 20%; saltos grosseiros mexem no total de MG | (a) publicar o universo como **faixa entre as leituras** (arrecadação × arrecadação − repasse); (b) **regra do salto** decidida pelo autor; (c) conferir no Justiça Aberta as serventias 042986, 035030, 059816 e 046219 | BI e API | baixo | médio |
| M7 | **Risco jurídico** (ADI 8015) fora da faixa do prêmio | Mostrar o prêmio **condicionado ao cenário do STF** (mantém, meio-termo, suspende = zero), ao lado da P5–P95, e conferir o andamento da ADI no bronze (`data/bronze/stf`) na véspera | bronze do STF | baixo | alto na comunicação |
| M8 | **Taxa do seguro e adesão** (degraus 7 e 8): as suposições que mais mexem no prêmio, sem fonte | (a) verificar se a SUSEP publica a importância segurada por ramo (se sim, taxa média = prêmio ÷ IS); (b) sem fonte, mostrar o prêmio numa **grade taxa × adesão**, em vez de um número só (o B4 de 18/10: cenários coerentes) | SUSEP (a confirmar) | baixo | médio: deixa claro o que depende de quê |
| M9 | **Vacância** (05a e 05c): o cadastro só tem a situação atual | **Segunda coleta do cadastro do CNJ** (mesma API) para medir as mudanças de situação entre duas datas | API do Justiça Aberta | baixo | médio: melhora a P(fim) do M2 |
| M10 | **Grupos** (04): "o grupo 6 tem 55% do déficit" depende das suposições | Reescrever a leitura também em passivo (dado) e refazê-la com o M1 | — | baixo | baixo |

**Ordem sugerida (de 27/10):** M1 → M2 (juntos respondem a pergunta 9 e reduzem a incerteza dos passos 5 e 6), M5 e M4 (sem coleta), M7 e M10 (só texto e gráfico), depois M3, M6 e M9, quando o autor pedir a coleta nova. A coleta foi feita em 28/10, gratuita e só de conferência (o `config/escopo.yaml` não mudou).

---

## 6. As três partes

| Parte | O que faz | Entregáveis |
|---|---|---|
| ✅ **A** (2026-10-22) | Checagem do Ollama; base de `src/analise/`; notebooks **01** e **02** | feito e revisado |
| ✅ **B** (2026-10-23) | Notebooks **03, 04, 05 e 06** | notebooks; PNGs; métricas de cada modelo contra a referência e contra o resultado do teste; desenho de `analise_regras`, `analise_grupos` e `analise_clt_modelo` |
| ✅ **C** (2026-10-28) | Notebooks **07, 08 e 09** | notebooks; PNGs; desenho de `analise_previsao`, `analise_tornado` e `analise_monte_carlo`; achados; tabela de lacunas; recomendação para o painel |
| ✅ **Melhorias** (2026-10-28) | Notebook **10** (M1 a M10) e o 09 rodado de novo | notebook; PNGs `10_*`; desenho das seis tabelas da D-045 |

A geração das tabelas `gold.analise_*` no pipeline e a atualização do `gerar_publico.py` são da Etapa 2 do plano do projeto.

**Relatório no fim de cada parte** (curto):
- o que foi feito, notebook por notebook, com os principais números;
- os modelos: métrica contra a referência, o tipo de validação e se o resultado bate com o do teste;
- os PNGs gerados (nomes);
- bibliotecas adicionadas;
- problemas encontrados nos dados;
- suíte padrão;
- arquivos para commit.

Depois do relatório, **pare**.
