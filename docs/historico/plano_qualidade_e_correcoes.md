# Plano de correções, qualidade de dados e análises avançadas — fechamento da Fase 1 e Etapa 2

> **Histórico (D-037, 2026-10-22).** Não é mais um plano em execução; parte dele entrou no `docs/plano_mineracao.md`.

> **Nota (2026-10-21, D-035):** Bloco 1 concluído na Fase 1; Bloco 2 = E1 e Bloco 3 = E2 do `ROADMAP.md` (nesta pasta); as decisões novas são numeradas a partir da D-036 (as citações a D-026, D-027 e D-028 neste plano são numeração antiga).

> **Para o Claude Code.** Atue como **engenheiro de dados sênior, cientista de dados sênior e especialista em seguros**. Este documento junta tudo o que encontrei na revisão do painel (carga de 18/10/2026, 15:18) e propõe correções para os defeitos de tela, para as **limitações declaradas** e para a **qualidade dos dados**, além de análises novas.
>
> Os números marcados como **(BI)** foram calculados por mim **fora do projeto**, com o CSV do BI do CNJ (`data/bronze/cnj_bi_painel/2026-10-18/`) e o cadastro do BI que **não** está no projeto. Servem como **evidência e ordem de grandeza**. Recalcule tudo com o silver do projeto. Se der diferente, explique, sem ajustar para bater.

---

## 0. Regras e organização

**Regras (todas continuam):**
- `CLAUDE.md` acima de tudo.
- Nada de commit nem push.
- **Não apagar nada.** Premissas novas viram **nova versão** do YAML. Decisões novas recebem novos números (D-026 em diante) e as antigas não são editadas. Docs só recebem acréscimos.
- Correções de dado nunca alteram o bronze. Elas ficam em **tabelas de correção versionadas** (`config/*.yaml`), aplicadas no silver com uma coluna de marcação (`corrigido_por`, `imputado`).
- Nenhum número sem fonte e data-base. LGPD com o mínimo de 3 serventias.
- Arquivos grandes só por script, com saída de no máximo 50 linhas.

**Organização em 3 blocos, com parada entre eles:**

| Bloco | O que é | Muda números? | Quando |
|---|---|---|---|
| **1. Tela e engenharia** | Defeitos visuais, bug do "$", mapa, rótulos, testes de proteção | **Não** | Agora. Depois eu faço o **commit da Fase 1**. |
| **2. Qualidade de dados** | Classe das indeterminadas, semestres faltantes, município errado, receita bruta, custeio e repasse no silver, checagens novas | **Sim** | Primeiro **diagnóstico** (só medir, sem mudar o modelo) → **parada** → implementação do que eu aprovar |
| **3. Modelo de seguro** (Etapa 2) | B2, B6, B1, B3, B4 e incerteza | **Sim** | Depois do Bloco 2 |

Prioridade de cada item: **[E] essencial para a entrevista**, **[R] recomendado**, **[O] opcional**.

---

## BLOCO 1 — Tela e engenharia (sem mudar número)

### 1.1 [E] Bug: "$" virando fórmula no `st.markdown`
- **Evidência:** em "Limitações declaradas", o item "Regra dos R$ 300 mil" aparece com `**` e um trecho em fonte de código. O Streamlit lê o texto entre dois `$` como LaTeX.
- **Correção:** uma função única `md_seguro(texto)` em `app/comum.py` que escapa `$` para `\$`. Todo `st.markdown`, `st.caption`, `st.info` e afins com texto que pode ter "R$" passa por ela.
- **Teste:** varrer o código do `app/` e falhar se algum `st.markdown`, `st.caption`, `st.write`, `st.info` ou `st.warning` receber texto com "R$" sem passar por `md_seguro`. Um segundo teste renderiza a página Qualidade e procura o padrão de LaTeX.

### 1.2 [E] Mapa: municípios pequenos pintados com a soma da região inteira
- **Evidência:** no mapa de "Serventias ativas", as manchas mais escuras são grupos de **municípios minúsculos** (Zona da Mata e sul), porque **cada um** recebe o total da sua região imediata. Uma região com 10 cidades de 2 serventias pinta as 10 com "20". A leitura visual fica errada, e o efeito se repete nos mapas de passivo e de empregados.
- **Correção:** **dissolver** a geometria. Os municípios com menos de 3 serventias de cada região imediata viram **um único polígono** (`geopandas.dissolve`), pintado uma vez com o total.
  - Texto ao passar o mouse: "Região imediata de X — N municípios com menos de 3 serventias — total R$ …".
  - Gerar a geometria dissolvida **no gold** (`gold.geo_mapa_publico`), não na hora de abrir a página, e testar que nenhuma feição pública tem menos de 3 serventias.
- **Legenda:**
  - "Em branco: 2 municípios sem serventia no cadastro do CNJ (ver Limitações)";
  - "A cor representa o **total** da área; áreas agregadas somam vários municípios".
- **Teste automático de LGPD no texto do mouse:** inspecionar `fig.data[*].hovertext`, `customdata` e `locations` das figuras Plotly das 4 páginas e falhar se aparecer nome ou código de município com menos de 3 serventias.

### 1.3 [E] Rótulo do resultado
- "Resultado técnico" → **"Resultado técnico (antes de impostos, resseguro e capital)"**, no Simulador e na Tabela por UF.
- Linha embaixo, em fonte menor: "Margem de 64% não é lucro esperado: ver limitações do modelo de sinistro (Etapa 2)."

### 1.4 [R] Valores esperados com "≈"
- "Serventias com déficit (esperado)": **"≈ 486"** no Mercado, no Simulador e na sensibilidade.
- Mesmo padrão para qualquer contagem fracionária arredondada.

### 1.5 [R] Textos e rótulos cortados ou ambíguos
- Início: "Passivo dos obrigados — unive…" → trocar por um rótulo curto, "Passivo dos obrigados", com a explicação no "?".
- Qualidade: "Região imediata de São João del Rei (11 mu…" → coluna mais larga ou nome curto ("RI São João del Rei (11 mun.)") com o nome completo no "?".
- Qualidade, tabela de sensibilidade: o texto da linha do INPC também está cortado. Quebrar a linha ou encurtar.
- Simulador: espaço entre o bloco de cima (≈ 1.121 … R$ 36,9 mi) e os títulos "Mercado total" e "Seguradora hipotética" (hoje grudados).
- Contrato "período com valores conflitantes": mostrar **"154 linhas (77 pares CNS-período; 2 em 2025)"**.

### 1.6 [R] Fontes e referências
- Rodapé do Início: **tirar a SUSEP SES**, porque nada nessa página usa a SES (mesma lógica do E2).
- Tabela de fontes, arrecadação: data de referência **"classe: exercício 2025; série coletada até 2026-06-30"**.
- IBGE (IPCA): está listado em todas as páginas, mas não encontrei uso. **[VERIFICAR]** onde o IPCA é usado. Se não for usado, tire dos rodapés e mantenha só na tabela de fontes como "coletado, não usado".
- SUSEP SES, "valores em R$ (inferido)": confirme a unidade no dicionário da SES. Para razões (sinistralidade) a unidade não importa, mas se algum valor absoluto da SES aparecer na tela, importa.

### 1.7 [R] Engenharia
- **Banco recriado do zero a cada carga:** o pipeline grava num arquivo temporário e troca no fim (escrita atômica). Isso evita o crescimento de 11 MB → 28 MB, que vai piorar com o Brasil inteiro, e evita um banco meio gravado se a carga falhar.
- **Regra do `interno_*`:**
  - acrescentar ao `CLAUDE.md` e ao `docs/SPEC.md` (seção da Fase 3): "painel e chat só leem tabelas públicas; `gold.interno_*` é proibido fora do pipeline";
  - teste: varrer `app/` (e futuramente o código do chat) e falhar se aparecer `interno_`.
- **Reprodutibilidade:** um teste que roda o gold duas vezes a partir do mesmo silver e compara um hash das tabelas públicas (precisa ser idêntico).
- **Erro registrado "edição por script que falhou sem aviso":** **[VERIFICAR]** qual arquivo foi, se a edição foi refeita e se há teste cobrindo. Proibir daqui em diante editar código por script de substituição de texto: use a ferramenta de edição.

**Parada 1:** relatório curto do Bloco 1 (checklist, testes novos, prints esperados) → eu confiro o painel → **eu faço o commit da Fase 1**.

---

## BLOCO 2 — Qualidade de dados

> **Primeiro só diagnóstico.** Para cada item, rode a análise com o silver do projeto, mostre o **efeito em universo, passivo dos obrigados, déficit e prêmio** e proponha a decisão. **Não altere o modelo** até eu aprovar item por item. O diagnóstico pode criar scripts novos em `scripts/qualidade_fase1/`, que só leem dados.

### Q1. [E] Classe das indeterminadas: usar o ano anterior em vez de um peso médio
- **Problema:** 76 serventias com R$ 0 nos dois semestres de 2025 e 2 com conflito recebem **peso 67,8%** (a proporção média). O próprio painel mostra que elas são menores que a média, então o peso médio tende a superestimar.
- **Evidência (BI, MG):** dos **30 providos** com zero nos dois semestres de 2025, **29 têm arrecadação em 2024**: 14 com média acima de R$ 300 mil e 15 abaixo. Só 1 tem zero também em 2024 (e há 8 casos zerados em 2025 e 2024 com dado em 2023).
- **Proposta (D-026):** classe por **cascata temporal**:
  1. exercício 2025 (regra atual);
  2. se 2025 não tiver valor válido, usar **2024**;
  3. se não houver, 2023;
  4. só o que sobrar fica indeterminado, com o peso atual.

  Marcar `fonte_classe ∈ {2025, 2024, 2023, peso}`. Justificativa: a receita de um cartório muda pouco de um ano para o outro (ver Q3), e o zero de 2025 é, na maioria, falta de declaração.
- **Aceite:** indeterminados providos ≤ 3. Tabela de sensibilidade com "cascata" × "peso médio".

### Q2. [R] Semestre faltante: corrigir a sazonalidade
- **Problema:** com só um semestre, a regra atual compara aquele semestre sozinho com R$ 300 mil. Mas o 2º semestre arrecada sistematicamente mais.
- **Evidência (BI, MG):** razão 2º sem ÷ 1º sem de **1,19 (mediana, 2024)**, **1,22 (agregado, 2024)** e **1,19 (agregado, 2023)**. Há 145 providos com só um semestre em 2025. Imputar o semestre faltante pela razão sazonal muda a classe de **6** deles.
- **Proposta (D-027):** imputar o semestre faltante = semestre presente × razão sazonal (ou ÷ razão), calculada no próprio silver de MG com os anos completos. Marcar `imputado = true`. Efeito pequeno, mas metodologicamente correto e fácil de defender.
- **Aceite:** teste com um caso feito à mão; sensibilidade "com e sem imputação".

### Q3. [E] Estabilidade da classe e zona de fronteira
- **Evidência (BI, MG, providos):**
  - de 2023 para 2024, **132 de 1.654** mudaram de lado do limiar (112 subiram, 20 caíram);
  - de 2024 para 2025, **161** mudaram (132 subiram, 29 caíram);
  - **204 providos** têm média entre R$ 240 mil e R$ 360 mil (±20% do limiar).
- **Leitura:**
  - a classe é instável perto do limiar;
  - o universo **cresce ~6% a 8% ao ano**, porque o limiar é **nominal** (R$ 300 mil fixos) e os emolumentos são reajustados todo ano.
  - Isso é um **achado de mercado**: o mercado cresce sozinho enquanto o limiar não for corrigido.
- **Proposta:**
  - (a) **[E]** mostrar na Qualidade a matriz de transição de classe 2023→2024→2025 (contagens agregadas) e o número de serventias na zona de fronteira;
  - (b) **[R]** sensibilidade "limiar ±20%";
  - (c) **[O]** projeção simples do universo para 2026–2027, mantendo o limiar nominal e usando a taxa média de transição observada. Rotular como **projeção**.

### Q4. [E] Receita bruta (Prov. 213) × arrecadação × arrecadação menos repasse — o maior risco de definição
- **Problema:** a classe usa a **arrecadação** do Justiça Aberta, que inclui os **repasses** (taxas e fundos que não pertencem ao delegatário). Se a "receita bruta" do art. 2º, XXIV, do Prov. 213 **excluir** os repasses, o universo muda muito.
- **Evidência (BI, MG, 2025):**
  - repasse = **39% da arrecadação**;
  - providos acima de R$ 300 mil pela arrecadação: **1.095**; pela arrecadação **menos repasse**: **874** (**−20%**).
- **[VERIFICAR] obrigatório:** cite o **texto literal** do art. 2º, XXIV, do Prov. 213 (e alterações do 243) a partir da cópia oficial do bronze. A definição inclui ou exclui taxas, fundos e repasses? Não interprete de memória.
- **Proposta:**
  - se o texto **excluir** repasses, a leitura principal passa a ser "arrecadação − repasse", **com a minha aprovação**;
  - se **incluir**, fica como está e "líquida" vira sensibilidade;
  - se for ambíguo, as duas aparecem lado a lado no Início com a explicação.
- Depende do Q8 (repasse por serventia no silver).

### Q5. [R] Serventia registrada no município errado
- **Evidência (BI):**
  - **Campo Azul** (sem serventia no painel) **tem uma**: "Ofício de Registro Civil e Notas de Campo Azul", cadastrada no CNJ com cidade **Ubaí** (município de origem). É o tipo de erro de quem não atualizou o cadastro após a emancipação.
  - Em MG, **65 serventias ativas** têm na denominação o nome de **outro município** de MG. Muitas são **distritos** com o mesmo nome (normal), mas algumas podem ser o mesmo caso de Campo Azul.
  - Para Senador José Bento não achei correspondência; continua sem explicação.
- **Proposta (D-028):**
  1. Baixar a lista de **distritos do IBGE** (API de localidades, `/estados/31/distritos`, gratuita) para o bronze.
  2. Para cada serventia cuja denominação cita outro município: se o nome bate com um **distrito do município cadastrado**, está ok; se bate com um **município** (e não com um distrito dele), vira **candidata a correção**.
  3. Revisão manual das candidatas. As aprovadas vão para `config/correcoes_municipio.yaml`, com a evidência; o silver aplica e marca `corrigido_por`.
- **Efeito esperado:** mapa e contagens por município mais corretos, menos falsos "RAIS = 0 e CNJ > 0" (Q6) e contagens da regra de 3 serventias corretas.
- **LGPD:** o nome da serventia é dado institucional público, mas a lista de candidatas fica **só em `docs/` ou em `interno_*`**, nunca no painel.

### Q6. [R] RAIS × CNJ por município: medir na unidade certa
- **Problema:** só 69,1% dos municípios ficam dentro de ±20%, e 64 municípios têm RAIS = 0 com CNJ > 0. A RAIS pública **não tem identificador do empregador**: não dá para casar vínculo com serventia. O vínculo fica no endereço do CAEPF do titular, que pode ser em outro município.
- **Importante para a narrativa:** no modelo, a RAIS só fornece a **distribuição** de salário e tempo de casa. A **contagem** vem do CNJ. Então a divergência municipal afeta o passivo só pela escolha da distribuição, e essa sensibilidade (+3,6%) já está medida.
- **Proposta:**
  - (a) repetir as checagens do C1 no nível da **região imediata**, que é a unidade usada como reserva da distribuição, e mostrar os dois níveis;
  - (b) refazer depois do Q5 e medir quantos dos 64 casos eram município errado;
  - (c) manter as tolerâncias municipais como **aviso**, sem baixá-las.

### Q7. [R] Plausibilidade dos colaboradores declarados (autodeclarados e sem data)
- **Proposta de checagens novas (aviso, não erro):**
  - CLT = 0 com arrecadação anual acima de R$ 1 mi (cartório grande sem empregado declarado: improvável);
  - arrecadação por CLT muito baixa (abaixo do custo de folha estimado: mais empregados que a receita sustenta);
  - depois do Q8: folha estimada (CLT × salário médio da região × 1,43) **maior que o custeio declarado** (o custeio precisa cobrir a folha).
- Mostrar só **contagens** na Qualidade. Sensibilidade "excluindo serventias com colaboradores implausíveis" ou "trocando a contagem implausível pela mediana da classe". **Não trocar dado sem aprovação.**

### Q8. [E para Q4 e B6] Custeio e repasse no silver (CSV do BI, só MG)
- Tabela nova `silver.serventia_financeiro` (CNS, período, arrecadação, repasse, custeio, atos, fonte) a partir do CSV do bronze.
- **Contratos obrigatórios:**
  - **custeio deduplicado**: no 2º sem/2025, o custeio vem **repetido em cada linha de atribuição**, então é **um valor por CNS e período**. Teste com o caso de 6 atribuições;
  - arrecadação e repasse **somados** entre as linhas de atribuição;
  - 2026 fora (formato misto e custeio vazio);
  - linhas sem data descartadas e contadas;
  - custeio negativo → aviso; custeio = 0 com arrecadação > 0 → aviso (margem falsa de 100%);
  - total de MG 2025 contra o total de controle (arrecadação R$ 5.441,6 mi no BI) e contra o silver da API (arrecadação).
- **Arrecadação oficial continua a da API** (mais completa, F2). O CSV fornece **só repasse e custeio**.

### Q9. [R] Remuneração do art. 6º ("maior remuneração") e os 887 sem salário de dezembro
- **[VERIFICAR]** se o arquivo da RAIS no bronze tem as colunas de **remuneração mensal** (janeiro a dezembro). A RAIS pública costuma trazê-las.
- Se tiver:
  - (a) nova opção de base, **"maior remuneração mensal do ano"**, como sensibilidade. Aviso: inclui parcelas variáveis, então tende a superestimar a "maior remuneração fixa";
  - (b) os **887 sem remuneração de dezembro** passam a ter salário pela **média dos meses com valor**, marcados `imputado`, e entram na distribuição como sensibilidade.
- **Afastados (714):** manter na contagem do passivo. A dispensa durante o afastamento por doença fica suspensa, mas a obrigação existe. Acrescentar essa frase às Limitações.

### Q10. [O] CNPJ × CNJ (15,8% a mais)
- Melhorar a explicação do excesso com um casamento por **nome** (razão social × denominação, normalizados, só dentro do mesmo município) para MG. Mostrar o % de CNPJs casados e o % do excesso explicado. Só diagnóstico; não muda o modelo.

### Q11. [R] Monitoramento das fontes
- Contrato de **atualidade** (aviso): cada fonte com "coletado em" há mais de N dias (N por fonte em `config/qualidade.yaml`).
- Registrar na tabela de fontes a **data de publicação** do dado quando a fonte informar (RAIS, SES, CNPJ).

**Parada 2:** relatório do diagnóstico Q1–Q11 com:
- uma tabela "item × efeito em universo / passivo dos obrigados / déficit / prêmio";
- a decisão proposta em cada item.

Eu aprovo item a item e só então você implementa.

---

## BLOCO 3 — Modelo de seguro (Etapa 2, depois do Bloco 2)

> Só registre no `diario.md` como plano aprovado em princípio. **Não implemente agora.**

### S1. [E] B2 — índice combinado honesto
- Índice combinado = sinistralidade + comercialização + administrativa + **PIS/COFINS** (alíquota conferida no texto legal) + custo de resseguro (suposição com faixa).
- Mostrar o resultado e a margem com o rótulo completo.

### S2. [E] B6 — probabilidade de déficit pelo saldo, não por classe
- Com o Q8: saldo anual = arrecadação − repasse − custeio.
- Faixas por **passivo ÷ saldo anual**:
  - saldo ≤ 0;
  - mais de 12 meses;
  - 3 a 12 meses;
  - menos de 3 meses.

  Cada faixa com probabilidade e parte descoberta (suposições com faixa).
- Evidência do F6: só **41** precisam de mais de 12 meses e **47** têm saldo ≤ 0, contra ~490 hoje. Mostrar **lado a lado** com o modelo por classe.
- Deixar claro na tela: o Prov. 227 mede **bens livres de ônus**, e o saldo é só um indicador.

### S3. [E] B1 — sinistro por frequência × severidade (versão simples)
- **Achado:** hoje o sinistro implícito é **R$ 40,2 mil ÷ R$ 18,4 mi de IS = 0,22% da IS por ano**. Pela lógica do produto:
  > sinistro ≈ P(delegação termina no ano) × P(titular não paga | tem déficit) × parte paga − recuperação
  > ≈ (4% a 7%) × (≈ 40%) ≈ **1,6% a 2,8% da IS por ano**

  Isso está **perto ou acima da taxa de 2%**. Se confirmado, a conclusão vira **"mercado pequeno e, a 2%, provavelmente não lucrativo; o preço precisa considerar seleção adversa"**. É a conclusão de seguros mais forte do projeto.
- **Frequência:** o cadastro do BI **não serve** (datas de recadastramento). **[VERIFICAR, O]** se o TJMG publica as **listas semestrais de serventias vagas** (exigência da Res. CNJ 80/2009 para os concursos). Duas listas consecutivas dariam o número de **novas vacâncias por ano**, um dado real e gratuito. Se não houver acesso fácil, use suposição com faixa (2% a 8%) e registre.
- Manter a SES (média de vários anos) só como **comparação**.

### S4. [R] B3 — escala
- Número de apólices (≈ serventias com déficit × % seguro), prêmio médio, **prêmio mínimo por apólice** e **custo fixo por apólice** (suposições com faixa).
- Mostrar o resultado da seguradora hipotética com esses custos.

### S5. [R] B4 — incerteza bem apresentada
- **Gráfico tornado:** uma premissa por vez, entre o mínimo e o máximo dela.
- **[O] Monte Carlo** com semente fixa, sorteando **juntas** as premissas de seguro e as escolhas de dados do Bloco 2 (regra de classe, distribuição, imputação), com faixa de 90%.
- Substitui a leitura de "mínimo e máximo com tudo no extremo".

### S6. [R] Concentração do risco
- **Evidência (BI, MG):** os 10% maiores providos concentram **57% da arrecadação**; entre os obrigados, **50%**.
- **Proposta:** curva de concentração (agregada, sem identificar ninguém) do passivo e da IS. Leitura de seguro: poucos riscos grandes dominam a carteira, o que pede limite por risco e resseguro. Mostrar só percentis.

---

## Formato das respostas

- **Parada 1 (Bloco 1):** checklist, testes novos, o que mudou em cada página e a lista de arquivos (A/M) com sugestão de commit.
- **Parada 2 (Bloco 2, diagnóstico):** para cada item Q1–Q11, o número do projeto, o número de referência (BI) quando houver, o efeito estimado e a decisão proposta.
- Em qualquer ponto, se algo exigir mudar fora do plano, **pare e pergunte**.

**Comece pelo Bloco 1. Pare na Parada 1.**
