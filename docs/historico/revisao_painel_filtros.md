# Revisão do painel com filtros — correções antes do commit da Fase 1

> **Para o Claude Code.** Atue como **engenheiro de dados sênior, cientista de dados sênior, especialista em seguros e designer de UX sênior**. Este documento junta:
> 1. o contexto de onde estamos;
> 2. as decisões pendentes da Parada 1;
> 3. **todos os erros** encontrados na revisão do painel (carga de 18/10/2026, 17:14), incluindo as exportações com filtros (geral, cada métrica, Belo Horizonte, Classe 1, 2, 3 e indeterminada);
> 4. uma **auditoria própria** que você deve fazer do mapa e do resto do painel, além dos erros listados;
> 5. leituras de seguros para registrar.
>
> **Ordem:** leia tudo → faça a auditoria da seção 5 → corrija → pare com o relatório da seção 7. **Não comece o Bloco 2.** Nada de commit ou push.

---

## 1. Contexto (onde estamos)

- **Fase 1 (MG):** Etapa 1 e Bloco 1 feitos e **ainda não commitados**. 108 testes passando; números estáveis.
- **Números de referência (base, v2, regra mantida), que NÃO podem mudar nesta rodada:**

| Indicador | Valor |
|---|---|
| Serventias ativas | 2.525 |
| Empregados CLT | 12.134 |
| Obrigadas | ≈ 1.121 |
| Passivo de todas as ativas | R$ 311,9 mi |
| Passivo dos obrigados | R$ 238,1 mi |
| Com déficit | ≈ 486 |
| Déficit | R$ 36,9 mi |
| Importância segurada | R$ 18,4 mi |
| Prêmio | R$ 368,7 mil |
| Teto teórico | R$ 4,76 mi |

- **Somas por classe que conferem hoje** (precisam continuar conferindo):

| Grandeza | Classe 1 + 2 + 3 + indeterminada | Total |
|---|---|---|
| Serventias | 1.168 + 868 + 411 + 78 | 2.525 |
| CLT | 1.573 + 3.439 + 6.852 + 270 | 12.134 |
| Passivo de todas as ativas | 28,7 + 72,8 + 205,4 + 4,9 | 311,8 mi |
| Passivo dos obrigados | 61,7 + 174,2 + 2,1 | 238,0 mi |
| Déficit | 15,4 + 20,9 + 0,5 | 36,8 mi |
| Com déficit | 371 + 106 + 9 | 486 |

- **Próximas etapas (não fazer agora):** Bloco 2, qualidade de dados (`docs/bloco2_qualidade.md` e `docs/plano_qualidade_e_correcoes.md`); Bloco 3, modelo de seguro.

**Regras de sempre:**
- `CLAUDE.md` acima de tudo.
- Não apagar nada. Docs só com acréscimos; decisões novas a partir de D-026.
- LGPD: mínimo de 3 serventias. O painel só lê tabelas públicas.
- Testes na cópia do banco; conferir o banco real **e os Parquet do gold** antes e depois da suíte.
- Arquivos grandes só por script, com saída de no máximo 50 linhas.

---

## 2. Decisões da Parada 1

### 2.1 Mercado × tabela interna → **opção B aprovada** (D-026)
- **Sem filtro** (tudo "Todos"): como está hoje (municípios com ≥ 3 + grupos regionais dissolvidos).
- **Com filtro de atribuição, situação ou classe:** mapa, ranking e tabela passam para o nível da **região imediata**, **pré-agregados no gold** para cada valor de filtro (um filtro por vez), com a regra de 3 **e** a supressão complementar (item E1) aplicadas no gold.
  - Regiões que não passam sobem para a **região intermediária** ou entram em "outras regiões".
- **Filtro de município:** ver item U1 (regras próprias).
- Depois disso, **remover a exceção** de `1_Mercado.py` do teste `test_painel_nao_le_tabelas_internas`.

### 2.2 As 4 regiões com grupo pequeno < 3 → **não juntar a município nomeado** (D-026)
- Subir para o grupo de pequenos da **região intermediária** do IBGE (mesma lógica hierárquica da D-022).
- Só em último caso juntar a um município, com o rótulo **"Município X + N municípios pequenos"** (no mapa, no texto do mouse e na tabela).
- **Motivo:** juntar a um município nomeado faz o valor dele incluir os vizinhos, e a área aparece com o nome dele. Isso distorce o dado.

### 2.3 Explicar a contagem
"385 áreas: 315 municípios e 70 grupos". MG tem **70 regiões imediatas** e 4 tiveram o grupo juntado. Quantas regiões têm grupo próprio, quantas não têm município pequeno e quantas foram juntadas? Os números precisam fechar.

---

## 3. Erros encontrados (corrigir todos)

### 🔴 E1. [CRÍTICO — LGPD] Vazamento por subtração entre visões
- **Evidência** (visão geral × filtro Classe 3, tabela por município):

| Município | Geral | Classe 3 | Diferença = vazamento |
|---|---|---|---|
| Belo Horizonte | 34 serventias, 1.426 CLT, R$ 58,3 mi | 33 serventias, 1.417 CLT, R$ 57,9 mi | **1 serventia: 9 CLT, ~R$ 0,4 mi** |
| Uberaba | 9 serventias, 244 CLT, R$ 11,2 mi | 8 serventias, 239 CLT, R$ 11,0 mi | **1 serventia: 5 CLT, ~R$ 0,2 mi** |
| Betim | 6 serventias, 139 CLT, R$ 5,4 mi | 5 serventias, 136 CLT, R$ 5,3 mi | **1 serventia: 3 CLT, ~R$ 0,1 mi** |
| Uberlândia | 12 serventias, 430 CLT, R$ 17,1 mi | 10 serventias, 430 CLT, R$ 17,1 mi | 2 serventias com 0 CLT |

- **Problema:** a regra de 3 é checada em cada tabela **isoladamente**. Subtraindo uma visão da outra, isola-se um cartório. Isso é um **ataque por diferença**.
- **Correção — supressão complementar:** numa visão filtrada, uma área só aparece se o recorte tiver ≥ 3 **e** o complemento (total − recorte) for **0 ou ≥ 3**. Senão, a área vai para o agregado regional. Quando um filtro tem várias categorias, a supressão de **uma** categoria pode ser recuperada pelas outras. Se sobrar exatamente uma categoria suprimida num município, suprima também a segunda menor (**supressão secundária**).
- **Teste automático** `test_ataque_por_diferenca`: para **cada filtro e cada valor**, e para **cada par de visões públicas** (geral × filtrada, filtrada × filtrada do mesmo filtro), calcular a diferença por área e **falhar** se alguma diferença tiver 1 ou 2 serventias com qualquer valor não zero (serventias, CLT, passivo, déficit). Incluir o caso BH/Classe 3 como caso fixo.
- Registrar em `erros_ia.md`.

### 🟠 E2. Ranking corta as maiores barras e esconde o valor
- **Evidência:**
  - BH sem rótulo na visão geral e na Classe 3;
  - na Classe 2, Santa Luzia, Paracatu e Formiga cortadas, e "Arcos R$ 18…" truncado;
  - na indeterminada, Mutum sem rótulo.
- **Causa provável:** o eixo do ranking usa o mesmo teto do percentil 95 do mapa.
- **Correção:** o percentil 95 vale **só para a cor do mapa**. Eixo do ranking até o máximo × 1,15; rótulo sempre visível (fora da barra, ou dentro com contraste se não couber).

### 🟠 E3. Mapa sem escala de cores
- **Evidência:** a barra de cores (antes "R$ 0 … R$ 203,1 mil") sumiu nesta versão em todas as métricas.
- **Correção:** devolver a barra, com rótulos em R$ formatados ("R$ 50,8 mil", "R$ 1,3 mi") ou contagens. Quando a cor satura no percentil 95, o topo da escala diz "≥ R$ X".

### 🟠 E4. Colunas escondidas nas tabelas
- **Evidência:**
  - tabela **Faixas**: a coluna **"Prêmio anual"** está fora da área visível (a tabela termina em "Importância segurada");
  - **Tabela por município**: a coluna "Déficit" aparece cortada ("R$…").
- **Correção:** caber sem rolagem horizontal na largura de 1280 px. Prêmio e déficit sempre visíveis; abreviar cabeçalhos ("Passivo (todas)", "Passivo (obrigados)") com o texto completo no "?".

### 🟠 E5. Cinza × branco
- **Evidência:** a legenda diz "Em cinza: áreas com menos de 3 serventias no recorte", mas nas visões Classe 1, 2, 3 e indeterminada essas áreas saem **brancas**, iguais aos 2 municípios sem serventia.
- **Correção:** três estados visuais distintos, com legenda:
  1. **com valor** (escala de cor);
  2. **cinza** (sem dado publicável neste recorte);
  3. **hachurado ou cinza-claro com contorno** (sem serventia no cadastro: Campo Azul e Senador José Bento).

  Nunca branco puro dentro do estado.

### 🟠 E6. Visões vazias sem explicação (Classe 1)
- **Evidência:** com o filtro Classe 1:
  - KPIs "≈ 0" e "R$ 0,00" sem explicação;
  - ranking de déficit com 15 municípios a R$ 0,00 em ordem alfabética invertida (Borda da Mata … Abre Campo).
- **Correção:**
  - aviso: "A Classe 1 está fora da obrigação (Prov. 213/243): passivo exibido, déficit e prêmio zero por definição";
  - ranking troca para "Passivo de todas as ativas" ou some;
  - regra geral: **qualquer** visão em que a métrica escolhida é zero em todas as áreas mostra uma mensagem, não um gráfico vazio.

### 🟡 E7. Arredondamento contraditório
- **Evidência:**
  - Mutum aparece com "≈ 0" serventias com déficit na tabela, mas com o **maior** déficit no ranking da indeterminada;
  - BH "≈ 8" (era 8,4).
- **Correção:** contagens esperadas abaixo de 10 com **1 casa decimal** ("≈ 0,4"); a partir de 10, inteiro.

### 🟡 E8. Consistência de formato
- "≈8", "≈0", "≈9" sem espaço nos filtros; "≈ 486" com espaço na visão geral. Sempre **"≈ "**.
- "R$ 0,00" nos filtros e sem centavos no resto. Zero como **"R$ 0"**.
- Contrato "colaboradores informados: 4" → **"4 serventias sem colaboradores declarados"**.

### 🟡 E9. Limitação desatualizada
"Municípios sem serventia: … motivo não identificado". Já há evidência para Campo Azul: a serventia "…de Campo Azul" está cadastrada em **Ubaí**, provavelmente o município de origem antes da emancipação.
- **Só registrar no `diario.md`.** A correção do dado é o Q5 do Bloco 2.
- Na Limitação, trocar para: "Campo Azul: a serventia do município aparece no cadastro do CNJ com o município de Ubaí (correção prevista); Senador José Bento: motivo não identificado".

### 🟡 E10. Anomalia a investigar (só registrar)
**Mutum** tem **6 serventias indeterminadas** (todas zeradas em 2025). É improvável ser acaso: provável problema de declaração ou de coleta. Registrar no `diario.md` para o Q1 do Bloco 2 (verificar se há dado em 2024).

---

## 4. UX do filtro de município (novo)

### U1. Filtro de um município não pode deixar o resto do estado em branco
- **Evidência:** com Município = Belo Horizonte, o mapa mostra **o estado inteiro em branco** e um ponto minúsculo. Sem contexto, o mapa não informa nada.
- **Correção (padrão "destaque com contexto"):**
  1. o mapa continua mostrando **MG inteiro** em **cinza neutro** (com as bordas), para dar contexto;
  2. o município escolhido aparece **destacado** na cor da métrica, com contorno forte;
  3. o **zoom** enquadra a região intermediária do município (ele e os vizinhos), com o botão de "ver MG inteiro" do próprio Plotly;
  4. um texto curto ao lado: "Belo Horizonte: R$ 6,3 mi de déficit — 17% de MG; 1º de 853 municípios".
- **LGPD:**
  - município com ≥ 3 serventias: pode ser destacado, porque os números são os mesmos da visão geral e não há informação nova;
  - município com **menos de 3**: o filtro destaca **a área agregada** a que ele pertence (o grupo regional), com o aviso "Belo Vale está agregado à Região X (LGPD)". Nunca mostra o município sozinho.
- **Ranking com 1 item:** esconder e mostrar, no lugar, a **posição** do município no ranking estadual de cada métrica.
- **Filtros combinados** (município + classe, por exemplo): aplicar a mesma supressão complementar do E1. Se o recorte não passar, mostrar só o nível regional, com aviso.

### U2. Outras melhorias de UX (aplicar se forem simples; senão, listar como sugestão)
- **Estado dos filtros visível:** uma linha acima dos KPIs ("Filtros: Classe 3 · nível regional por LGPD") e um botão "Limpar filtros".
- **Tooltip do mapa padronizado:**
  - nome da área;
  - tipo (município, grupo regional ou região);
  - nº de serventias;
  - valor formatado;
  - % de MG.
- **Ranking e mapa sincronizados:** mesma métrica, mesmo recorte, mesmas áreas (se o mapa está em nível regional, o ranking também).
- **KPIs filtrados com referência:** mostrar "% de MG" embaixo de cada KPI quando houver filtro.

---

## 5. Auditoria própria (você verifica, além dos erros acima)

Não confie só na lista acima. **Audite o painel inteiro você mesmo**, de forma sistemática, e traga o que achar.

### 5.1 Como auditar
- Use o `streamlit.testing.v1.AppTest` (já disponível, gratuito) para percorrer **todas as combinações relevantes**:
  - as 4 métricas do mapa;
  - cada valor de cada filtro (um filtro por vez);
  - 3 municípios de exemplo: BH (grande), um com 3 a 5 serventias e um com menos de 3;
  - as duas regras de classe;
  - os 3 cenários do STF no Simulador.
- Para cada estado, extraia as **figuras Plotly** (`fig.to_dict()`) e as **tabelas** exibidas, e rode as checagens da seção 5.2 como **testes automáticos** (`tests/test_auditoria_painel.py`).
- **Opcional:** se quiser ver a tela de verdade, use o Playwright (gratuito e local) para tirar prints de cada estado em 1280 × 800 e 1920 × 1080 e salve em `docs/qa/` (fora do git, se forem muitos). **Peça minha aprovação antes de instalar qualquer pacote novo.**

### 5.2 Checagens obrigatórias, em cada estado

**Mapa**
- [ ] Tem escala de cores com rótulos formatados.
- [ ] Nenhuma área com branco puro dentro de MG; os três estados (valor, cinza, sem serventia) estão distintos e legendados.
- [ ] O tooltip não mostra município com menos de 3 serventias, nem no recorte filtrado.
- [ ] As áreas do mapa somam o total do KPI da mesma visão (tolerância de arredondamento).
- [ ] Com filtro de município: contexto em cinza, destaque e zoom (U1).
- [ ] Nenhuma área agregada leva o nome de um único município sem o "+ N municípios".

**Ranking**
- [ ] Todas as barras têm rótulo visível e não são cortadas.
- [ ] Quando todos os valores são zero ou há só 1 item: mensagem em vez de gráfico.
- [ ] Mesmas áreas e mesmo nível do mapa.

**Tabelas**
- [ ] Nenhuma coluna importante fora da área visível em 1280 px.
- [ ] Formato brasileiro, "≈ " com espaço, 1 casa decimal abaixo de 10, "R$ 0".
- [ ] Linha "Outros (menos de 3 serventias)" quando houver agregação, com os totais fechando.

**LGPD**
- [ ] `test_ataque_por_diferenca` passando para **todos** os filtros, valores e pares de visões.
- [ ] Nenhuma visão expõe uma área cujo complemento, em qualquer outra visão pública, tenha 1 ou 2 serventias.

**Consistência numérica**
- [ ] A soma por classe (1 + 2 + 3 + indeterminada) é igual ao total em serventias, CLT, passivo, déficit e "com déficit".
- [ ] A soma por atribuição e por situação é coerente com o total (atribuição pode somar mais que o total, porque uma serventia tem várias; explique na tela se for o caso).
- [ ] KPIs iguais entre Início, Mercado e Simulador na visão base.
- [ ] Faixa ordenada (mínimo ≤ base ≤ máximo) em todas as colunas da tabela Faixas, **em cada filtro**.

**Texto e acessibilidade**
- [ ] Nenhum texto cortado ("…") sem o texto completo no "?" ou no mouse.
- [ ] Contraste suficiente no tema escuro (texto cinza sobre fundo escuro nas notas de rodapé).
- [ ] Nada depende só de cor (legenda com texto).

**Desempenho**
- [ ] Tempo de troca de filtro (meça; se passar de ~2 s, use cache no carregamento das tabelas do gold).

### 5.3 Entregável da auditoria
Uma tabela **"achado × estado onde aparece × gravidade × correção × teste que cobre"**, separando o que você **corrigiu** do que você **só sugere**.

---

## 6. Leituras de seguros (só registrar no `diario.md`; não implementar)

1. **A Classe 2 pesa por causa da suposição, não do dado:** 26% do passivo dos obrigados, mas 42% do déficit, porque o fator suposto é 25% (Classe 2) contra 12% (Classe 3). Argumento central para o B6 (déficit pelo saldo).
2. **Prêmio por apólice muito baixo:** déficit médio de quem tem déficit ≈ R$ 41,5 mil (Classe 2) e ≈ R$ 197 mil (Classe 3). A 2%, dá ≈ R$ 830/ano e ≈ R$ 3,9 mil/ano por apólice. Na Classe 2, provavelmente abaixo do custo de análise; o B3 (prêmio mínimo e custo fixo) tende a mostrar que o mercado real é quase só a Classe 3, cerca de 100 cartórios em MG.
3. **Concentração:** BH responde por ≈ 17% do déficit e ≈ 22% do passivo dos obrigados de MG. Isso pede limite por risco e resseguro.
4. **Classe 1:** 46% das serventias, 13% dos empregados e 9% do passivo. Por isso a regra v1 × v2 muda pouco o resultado.
5. **Correção de leitura:** com o mapa dissolvido, a visão "Serventias ativas" continua escura no leste. Isso é **real** (municípios com muitos distritos e registro civil em cada um), não efeito de agregação.

---

## 7. Relatório ao fim (e PARE)

1. **Decisões aplicadas** (2.1, 2.2) e a explicação da contagem (2.3).
2. **Checklist E1 a E10, U1, U2:** feito ou sugerido, arquivo e teste.
3. **Resultado da auditoria própria** (tabela da 5.3).
4. **Prova:** suíte passando; banco real e Parquet do gold com a mesma data e o mesmo tamanho antes e depois da suíte; números de referência da seção 1 **inalterados**.
5. **O que eu devo conferir no painel**, por página e por filtro, incluindo: **filtro Classe 3 com BH, Uberaba e Betim** (não pode dar para subtrair) e **filtro Município = BH** (contexto em cinza, destaque e zoom).
6. **Arquivos** A/M e sugestão de mensagem de commit (Etapa 1 + Bloco 1 + esta rodada).

**Não comece o Bloco 2. Nada de commit ou push.**
