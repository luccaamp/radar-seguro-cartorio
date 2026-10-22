# Plano da mineração de dados de MG

> **O que é:** o plano completo da mineração de dados, estatística e previsão de Minas Gerais. É executado em **três partes (A, B e C)**, cada uma numa sessão, com uma parada no fim de cada parte.
> **Como usar:** em toda sessão desta etapa, a IA lê este arquivo inteiro e executa **só a parte pedida**.
> **Criado em:** 2026-10-22. Vira histórico quando a parte C fechar.

---

## 1. Objetivo

Entender a fundo os dados de MG e o mercado do Prov. 227, com:
- qualidade e dados faltantes;
- análise exploratória;
- padrões frequentes;
- agrupamentos;
- classificação e regressão;
- previsão do tamanho do mercado;
- sensibilidade e concentração;
- conclusões e lacunas (se precisamos de fontes novas).

**Quem lê os notebooks precisa entender tudo**, inclusive pessoas da equipe que não participaram do projeto.

## 2. Regras

As regras do `CLAUDE.md` continuam (nada de commit sem pedido, não apagar dados, 100% gratuito, nenhum nome nem CPF de pessoa física, nenhum número sem fonte, cópia do banco), com estas regras próprias da etapa:

- **Os 10 números oficiais não mudam** nesta etapa. Tudo o que for diferente da base é sensibilidade ou projeção, rotulado como tal. Se algo indicar que o cálculo do painel deveria mudar, a IA avisa no relatório em vez de mudar.
- **Todos os notebooks vão para o git, em `notebooks/`, com as saídas** (D-038, 2026-10-22). É um estudo público, com dados públicos: os notebooks podem usar todos os dados, inclusive `interno_*` e os resultados por cartório, identificados pelo CNS e pelo município (nunca pelo nome do responsável).
- **Cálculo reutilizável fica em `src/analise/`**, com teste. Os notebooks leem dados só por `src/notebooks.py` e chamam essas funções.
- **Resultados que podem ir para o painel** viram tabelas `gold.analise_*`, geradas pelo pipeline e pelo `gerar_publico.py`.
- **Gráficos** exportados em PNG em `docs/qa/analises/` (vão para o git), com nomes que dizem o conteúdo.
- **Bibliotecas:** pode adicionar com `uv add` bibliotecas gratuitas de análise (por exemplo `scikit-learn`, `statsmodels`, `mlxtend`). Listar no relatório.
- **Decida sozinho os detalhes pequenos.** Pare antes do fim da parte só se algo mudar os 10 números oficiais ou tocar em LGPD.
- Se a sessão estiver perto do limite, registre no `diario.md` onde parou, para a próxima sessão continuar.

## 3. Como cada notebook deve ser escrito

Cada seção tem, nesta ordem:
1. **A pergunta**, em uma frase.
2. **O método**, em português simples: o que é, **a fórmula ou a conta explicada com um exemplo pequeno**, e por que esse método e não outro.
3. **O código**, curto, chamando `src/analise/`.
4. **O resultado** (tabela ou gráfico).
5. **Como ler o resultado** e **o que ele significa para o mercado do Prov. 227**.
6. **Limitações:** o que esse resultado não diz.

Nada de código sem explicação. Termos técnicos explicados na primeira vez em que aparecem (por exemplo: mediana, quartil, correlação, R², validação cruzada, AUC, MAPE, lift, silhueta).

## 4. Critérios de qualidade (a banca vai perguntar)

- **Todo modelo tem uma referência simples** (o "chute": a média, a classe mais comum, o valor do semestre anterior) e só vale se for melhor que ela.
- **Validação honesta:**
  - validação cruzada nos modelos sem tempo;
  - nos modelos com tempo, **treinar só com o passado e testar no futuro** (nunca misturar);
  - nenhuma variável que "entregue a resposta" (vazamento). Exemplo: para prever vacância, não usar nada que só existe porque o cartório já está vago. Dizer no notebook quais variáveis foram descartadas por esse motivo.
- **Métricas explicadas** e sempre comparadas com a referência.
- **Incerteza:** previsões e projeções com faixa, não só um número.
- **Reprodutível:** semente fixa e o mesmo resultado ao rodar de novo.

---

## 5. Os notebooks

### 01 — Qualidade e dados faltantes
- O que falta em cada fonte e campo: arrecadação "não informado", zeros, conflitos (D-004, D-013, D-014); CLT não informado; vínculos da RAIS sem salário de dezembro (D-015); municípios sem RAIS; serventias sem município casado.
- Quanto falta, em número e em %, com gráfico.
- Valores atípicos (outliers), com o critério usado.
- Consistência entre fontes: CNJ × RAIS × CNPJ × BI do CNJ (totais e por município).
- **Conclusão:** o que é confiável, o que é estimado e o tamanho de cada problema.

### 02 — Análise exploratória
- Distribuições de receita, empregados CLT e passivo (escala log, quartis, média × mediana).
- Por classe, atribuição, situação (provida, vaga, outras) e região intermediária.
- Série histórica da arrecadação semestral (MG e por classe).
- Correlações entre receita, empregados, atribuições e passivo.
- Mapas e rankings só agregados.

### 03 — Padrões frequentes
- Regras de associação (Apriori) sobre as combinações de atribuições e características (porte, classe, situação, região).
- Suporte, confiança e lift explicados com um exemplo.
- Quais combinações são comuns e o que indicam para o mercado (por exemplo: que tipo de cartório costuma ser obrigado).

### 04 — Agrupamentos
- Clusterização com dados das fontes em escala log (receita, empregados, número de atribuições, situação): k-means e, para comparar, um hierárquico.
- Número de grupos escolhido e justificado (cotovelo e silhueta).
- Perfil de cada grupo: quantos cartórios, receita e empregados medianos, % obrigadas, passivo e déficit esperados (agregados), atribuições típicas.
- **Qual grupo é o mercado-alvo do seguro e por quê.**

### 05 — Classificação
Dois alvos com resposta real nos dados:
- **(a) Vacância:** prever se o cartório está vago pela receita, empregados, atribuição e região (ligação com o risco do seguro: a delegação termina).
- **(b) Subida de classe:** prever se o cartório passa do limite de R$ 300 mil no ano seguinte, usando só a série até o ano anterior (ligação com o crescimento do mercado).

Para cada um: referência simples; regressão logística e árvore ou floresta; validação (cruzada em (a), temporal em (b)); matriz de confusão, precisão, recall e AUC explicados; quais variáveis mais pesam; o que o resultado significa para o seguro.

### 06 — Regressão
- **(a) Empregados CLT** pela receita, atribuições e região: R² e erro em validação cruzada. **Uso:** estimar empregados nos estados onde o CNJ não traz essa informação (expansão).
- **(b) Passivo por serventia** pela receita e pelos empregados: o que explica o passivo.
- Resíduos e limites de cada modelo.

### 07 — Previsão do mercado
- Prever a arrecadação de 2026 e 2027, para MG e por classe, com a série semestral da API.
- **Teste no passado:** treinar até 2023, prever 2024 e 2025, e mostrar o erro (MAPE) contra o método ingênuo.
- Com a previsão, projetar para 2026 e 2027: quantos cartórios passam do limite; o universo de obrigadas; o passivo; a IS; o prêmio do mercado.
- **Dois cenários:** limite fixo e limite corrigido pela inflação (art. 16, §2º, do 213).
- Faixa de incerteza em todas as projeções.

### 08 — Sensibilidade e concentração
- **Tornado:** o que mais mexe no prêmio e no déficit, uma premissa por vez, do mínimo ao máximo, usando as funções do modelo.
- **Concentração:** curva de concentração e índice de Gini do passivo e da receita (quanto os 10% maiores concentram).
- **Receita líquida do Prov. 213, como sensibilidade:** citar o texto literal do art. 2º, XXIV, a partir do bronze; medir quantos providos ficam acima de R$ 300 mil pela arrecadação e pela arrecadação menos o repasse (CSV do BI), e o efeito no universo e no prêmio. **Sem mudar a base.**

### 09 — Conclusões e lacunas
- Os **8 a 10 achados principais**, cada um com o número, o gráfico e a frase para a apresentação.
- **Tabela de lacunas:** o que os dados não responderam, por quê, e se uma **fonte nova** resolveria (qual, se é pública e gratuita, se existe para todos os estados, quanto mudaria a análise).
- **Recomendação para o painel:** quais gráficos entram e em qual página.

---

## 6. As três partes

| Parte | O que faz | Entregáveis |
|---|---|---|
| **A** | Checagem do Ollama (5 minutos: instalado? o `qwen3:8b` responde?); base de `src/analise/`; notebooks **01** e **02** | resultado do Ollama; notebooks 01 e 02; PNGs; testes |
| **B** | Notebooks **03, 04, 05 e 06** | notebooks; PNGs; métricas de cada modelo contra a referência |
| **C** | Notebooks **07, 08 e 09**; tabelas `gold.analise_*`; `gerar_publico.py` | notebooks; tabelas; achados; tabela de lacunas; recomendação para o painel |

**Relatório no fim de cada parte** (curto):
- o que foi feito, notebook por notebook, com os principais números;
- os modelos: métrica contra a referência e o tipo de validação;
- os PNGs gerados (nomes);
- bibliotecas adicionadas;
- problemas encontrados nos dados;
- suíte padrão;
- arquivos para commit.

Depois do relatório, **pare**.
