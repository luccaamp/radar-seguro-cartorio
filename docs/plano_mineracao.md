# Plano da mineração de dados de MG (Etapa 1)

> **O que é:** o detalhamento da **Etapa 1 — Mineração** do [`plano_projeto.md`](plano_projeto.md), o plano oficial do projeto (D-039). Aqui ficam as regras, o formato dos notebooks, os critérios de qualidade e o que cada notebook entrega. A visão geral, os portões e as decisões do autor ficam no plano do projeto. **Em conflito, vale o `plano_projeto.md`.**
> **Como usar:** em toda sessão desta etapa, a IA lê este arquivo inteiro e executa **só a parte pedida** (A, B ou C), com uma parada no fim de cada parte.
> **Criado em:** 2026-10-22. **Atualizado em:** 2026-10-23 (D-039: métodos escolhidos pelos testes T1 a T7). Vira histórico quando a parte C fechar (Portão 1 do plano do projeto).

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

### 03 — Padrões frequentes (parte B)
- Regras de associação (Apriori, `mlxtend`) sobre as combinações de atribuições e características (porte, classe, situação, região), com foco nas regras que terminam em "obrigada".
- Suporte, confiança e lift explicados com um exemplo.
- **Referência:** a frequência simples de obrigadas por atribuição. Uma regra só interessa se o lift mostrar que ela diz mais que essa frequência.
- **Estabilidade:** manter só as regras que se repetem em 2 reamostragens de 80%.
- **Entrega:** as 10 regras principais e o que indicam para o mercado; desenho da `gold.analise_regras`.

### 04 — Agrupamentos (parte B)
- k-means em escala log (receita, empregados, número de atribuições, situação), com k de 2 a 8 escolhido pela silhueta e pelo cotovelo; hierárquico (Ward) para comparar, com a concordância medida pelo índice de Rand ajustado.
- Perfil de cada grupo: quantos cartórios, receita e empregados medianos, % obrigadas, passivo e déficit esperados, atribuições típicas.
- **Qual grupo é o mercado-alvo do seguro e por quê.**
- **Entrega:** desenho da `gold.analise_grupos`.

### 05 — Classificação (parte B)
Dois alvos com resposta real nos dados. Para cada um: referência, modelo vencedor do teste, logística para explicar os pesos, matriz de confusão, precisão, recall, AUC e Brier explicados, quais variáveis mais pesam (importância por permutação) e o que o resultado significa para o seguro.
- **(a) Vacância (teste T4):** floresta aleatória contra a proporção de vagas; validação cruzada estratificada 5 × 3; indicador AUC. **Vazamento declarado:** a receita e os empregados de um cartório vago são medidos já sob interino. O resultado é lido como **associação** ("cartórios vagos costumam ser assim"), não como previsão de quem vai vagar.
- **(b) Subida de classe (teste T3):** prever se o cartório passa de R$ 300 mil no ano seguinte, usando só a série até o ano anterior. Floresta aleatória contra a taxa histórica; validação temporal (treino até 2023, teste em 2024–25); indicador Brier. O teste mostrou que **todos os modelos subestimam as subidas** (218 previstas × 294 reais): recalibrar com 2022–23 e mostrar o efeito. **Entrega:** a contagem esperada de subidas em 2026 e 2027, com faixa (insumo do 07).

### ✅ 06 — Regressão (parte B, feito em 2026-10-23)
- **(a) Empregados CLT pela receita (teste T1):** floresta aleatória contra a mediana por faixa de receita; Poisson como versão interpretável. Validação deixando uma região intermediária de fora; indicador MAE. O teste mostrou erro de ~9% no total de uma região não vista: o total sai com ±10%. **Uso:** estimar empregados nos estados onde o CNJ não traz essa informação. **Entrega:** desenho da `gold.analise_clt_modelo`.
- **(b) Passivo por serventia:** decomposição do passivo em quantidade (CLT), salário e tempo de casa (passivo = CLT × passivo médio por vínculo), com regressão log-log nos resíduos e validação em 10 dobras. Mostra quanto do passivo vem de cada parte.
- Resíduos e limites de cada modelo.

### 07 — Previsão do mercado (parte C)
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

### 09 — Conclusões e lacunas (parte C)
- Os **8 a 10 achados principais**, cada um com o número, o gráfico e a frase para a apresentação.
- **Tabela de lacunas:** o que os dados não responderam, por quê, e se uma **fonte nova** resolveria (qual, se é pública e gratuita, se existe para todos os estados, quanto mudaria a análise). Já conhecidas: patrimônio livre do titular, taxa cobrada pelas seguradoras e a chance de a delegação terminar no ano (D-025).
- **Recomendação para o painel:** quais gráficos entram e em qual página (insumo das etapas 3 e 4).

---

## 6. As três partes

| Parte | O que faz | Entregáveis |
|---|---|---|
| ✅ **A** (2026-10-22) | Checagem do Ollama; base de `src/analise/`; notebooks **01** e **02** | feito e revisado |
| **B** | Notebooks **03, 04, 05 e 06** | notebooks; PNGs; métricas de cada modelo contra a referência e contra o resultado do teste; desenho de `analise_regras`, `analise_grupos` e `analise_clt_modelo` |
| **C** | Notebooks **07, 08 e 09** | notebooks; PNGs; desenho de `analise_previsao`, `analise_tornado` e `analise_monte_carlo`; achados; tabela de lacunas; recomendação para o painel |

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
