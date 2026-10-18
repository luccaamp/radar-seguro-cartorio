# Revisão crítica da Fase 1 — painel de MG

> **Para o Claude Code.** Este documento junta a revisão que fiz do painel aberto em 18/10/2026, com a carga das 09:52 e as premissas na versão 1. Passei pelas quatro páginas: Início, Mercado, Simulador e Qualidade dos dados. Cada item diz **o que foi visto na tela**, **por que é um problema**, **o que verificar ou corrigir** e o **critério de aceite**.
>
> **Como proceder**
> 1. Leia tudo antes de mexer em qualquer coisa.
> 2. Responda primeiro às perguntas marcadas como **[VERIFICAR]**, com números tirados do banco, e só então proponha um plano. **Pare e espere a minha aprovação** antes de implementar.
> 3. Siga o `CLAUDE.md`:
>    - **nunca** faça commit nem push;
>    - todo número precisa ter fonte e data de referência;
>    - LGPD: nenhuma estimativa no nível de um cartório identificável;
>    - tudo gratuito e local.
> 4. Registre **na hora** cada erro confirmado em `docs/erros_ia.md`, cada descoberta em `docs/diario.md` e cada decisão nova em `docs/decisoes.md`.
> 5. Os valores citados abaixo vêm das telas. Se o banco mostrar outro número, diga qual e por quê.

---

## Prioridades

| Bloco | Itens | Quando |
|---|---|---|
| **A. Prováveis erros** | A1 a A5 | **Antes do commit da Fase 1** |
| **D. LGPD** | D1 | **Antes do commit da Fase 1** |
| **C. Qualidade e engenharia de dados** | C1 a C6 | Antes do commit (verificações); correções podem ir para um ajuste da Fase 1 |
| **B. Modelo de seguro** | B1 a B6 | Ajuste da Fase 1 (modelagem); discutir comigo antes |
| **E. Apresentação** | E1 a E4 | Junto com o bloco A |

---

## A. Prováveis erros

### A1. A correção "faixas sempre pela classe v2" não está funcionando

**O que se vê** na página Qualidade, em "Sensibilidade das escolhas de modelagem" (cenário regra mantida):

| Nível | Universo v2 | Universo v1 | Prêmio v2 | Prêmio v1 |
|---|---|---|---|---|
| min | 1.103 | 1.520 | R$ 26,2 mil | **R$ 22,8 mil** |
| base | 1.121 | 1.545 | R$ 404,4 mil | **R$ 382,9 mil** |
| max | 1.159 | 1.582 | R$ 3,0 mi | R$ 3,0 mi |

**Por que é um problema.** A regra v1 (Classe 1 até R$ 100 mil) põe **424 serventias a mais** no universo, e mesmo assim o prêmio **cai**. No máximo, os dois ficam iguais. Se a troca de regra mudasse só quem entra no universo, e as faixas de déficit continuassem pela classe v2, acrescentar serventias só poderia **aumentar ou manter** o déficit, a importância segurada e o prêmio. Do jeito que está, a troca de regra continua reclassificando serventias entre Classe 2 e Classe 3 (e talvez muda o peso da classe indeterminada), que era exatamente o erro que pedi para corrigir.

**O que fazer**
- **[VERIFICAR]** Mostre, para a regra v1, quantas serventias ficam em cada classe usada nas faixas de déficit, comparando com a v2.
- **[VERIFICAR]** Diga se o peso da classe indeterminada (67,8%) é recalculado quando a regra muda.
- Corrija para que a classe usada nas faixas de déficit seja **sempre a v2**. A regra v1 deve só incluir serventias no universo.

**Critério de aceite:** um teste automático de **monotonicidade**. Para min, base e max, `universo_v1 ⊇ universo_v2` implica `déficit_v1 ≥ déficit_v2`, `IS_v1 ≥ IS_v2` e `prêmio_v1 ≥ prêmio_v2`.

### A2. Datas de referência misturadas no passivo

**O que se vê:**
- empregados contados em **out/2026** (CNJ, colaboradores);
- distribuição de salário e tempo de casa de **31/12/2025** (RAIS);
- salário corrigido até **set/2026** (INPC dez/2025 a 09/2026, fator 1,0401);
- rodapé da página Mercado: "custo de demissão sem justa causa em **31/12/2025**".

**Por que é um problema.** Se a data-base é 31/12/2025, não faz sentido corrigir o salário até setembro de 2026. Se a data-base é a da primeira declaração (≈ 09/09/2026), então o tempo de casa precisa avançar cerca de 9 meses, e o 13º, as férias proporcionais e o aviso prévio proporcional mudam junto.

**O que fazer**
- **[VERIFICAR]** Qual data-base o código usa hoje em cada componente: tempo de casa, 13º, férias proporcionais, aviso prévio e correção salarial?
- Proponha **uma** data-base coerente com o Prov. 227 (art. 5º e regra da primeira declaração), aplique em todos os componentes e escreva no rodapé e em `docs/decisoes.md`.

**Critério de aceite:** uma única data-base explícita no painel. Todos os componentes calculados nela. Um teste que confira um vínculo de exemplo calculado à mão.

### A3. O 13º na data-base de 31/12 [VERIFICAR]

**Por que pode ser um problema.** Numa demissão em 31/12, o 13º do ano normalmente já foi pago (até 20/12), então o valor devido deveria ser zero. Se o modelo soma 12/12 de 13º, o passivo está inflado em cerca de um salário por empregado, algo como 10% a 15% do total.

**O que fazer**
- **[VERIFICAR]** Mostre como o 13º entra hoje no cálculo, com um vínculo de exemplo.
- Ajuste conforme a data-base decidida em A2.

**Critério de aceite:** a regra do 13º documentada em `docs/decisoes.md` e coberta por teste.

### A4. "490 serventias com déficit (esperado)" pode contar cartórios sem empregados [VERIFICAR]

**O que se vê.** O número é **igual (490)** nos quatro métodos de rateio: por empregados, arrecadação, uniforme e peso por atribuição. Isso indica que ele vem só da probabilidade por classe e não depende do passivo.

**Por que pode ser um problema.** Uma serventia com **zero empregados CLT** tem passivo zero e não pode ter déficit. Se a probabilidade também é aplicada a ela, o 490 está inflado.

**O que fazer**
- **[VERIFICAR]** Quantas das 1.121 serventias do universo têm zero CLT declarado? Quanto elas somam no 490?
- Se for o caso, aplique a probabilidade de déficit só onde o passivo é maior que zero.

**Critério de aceite:** serventias com passivo zero contribuem com zero para "serventias com déficit". Teste cobrindo esse caso.

### A5. Correções 2, 3, 4 e 6 já pedidas ainda não aparecem no painel

Conferido em 18/10, carga das 09:52:
- **Item 2:** a legenda do mapa ainda diz "Municípios em branco: menos de 3 serventias". O mapa continua com muitos buracos, sem a agregação pela **região imediata do IBGE**.
- **Item 3:** a página Mercado ainda mostra "Passivo estimado R$ 343,4 mi". Deveria mostrar dois valores com nomes claros: "Passivo de todas as ativas" (R$ 343,4 mi) e "Passivo dos obrigados — universo" (R$ 256,5 mi).
- **Item 4:**
  - a legenda do mapa mostra "350k" e "2.5M", sem R$ e em notação inglesa;
  - o bloco "Faixas (mínimo — base — máximo)" continua um parágrafo e deveria ser uma tabela pequena;
  - a "Tabela por UF" do Simulador mostra números crus ("40439940", "1121.3").
- **Item 6:** nada na tela explica o que o cenário "máximo" significa. O item B4 trata disso.

**[VERIFICAR]** As correções foram implementadas e o Streamlit não foi reiniciado, ou ainda não foram feitas?

**[VERIFICAR] Item 5** (testes gravando no banco real): anote a data de modificação do arquivo DuckDB real, rode a suíte de testes e confira se ela mudou. Ela não pode mudar.

---

## B. Modelo de seguro (discutir comigo antes de implementar)

### B1. A sinistralidade de 10,9% (ramo 0775) não representa este produto

**O que se vê.** No Simulador, o sinistro esperado é `prêmio × sinistralidade` (10,9%), o que dá um resultado técnico de R$ 258,8 mil sobre R$ 404,4 mil de prêmio (64%).

**Por que é um problema**
- **Seleção adversa embutida.** Só compra o seguro quem **já tem déficit**, ou seja, quem por definição não tem bens livres suficientes. A chance de o titular não pagar quando o risco acontece é alta.
- **O risco é outro.** A carteira atual dos ramos 0775 e 0776 é de obras e contratos. O risco aqui é a delegação terminar (morte, aposentadoria, perda, renúncia) e o titular não pagar as verbas rescisórias.
- **Cauda longa.** A sinistralidade de um ano no SES mistura prêmios e sinistros de safras diferentes e oscila muito entre anos.
- **Recuperação.** A seguradora cobra o tomador depois do sinistro, pela contragarantia. O modelo não considera isso.

**Proposta:** um modelo de **frequência × severidade**.

```
sinistro esperado = P(delegação termina no ano)
                  × P(titular não paga | tem déficit)
                  × parte da importância segurada efetivamente paga
                  − recuperação esperada
```

- A primeira probabilidade pode ser **estimada com dados**. O Justiça Aberta mostra as serventias vagas; com elas, estime uma taxa anual de vacância em MG. Se houver data de vacância ou histórico, use; senão, documente a aproximação.
- As demais probabilidades são suposições, com faixa e decisão registrada.
- Mantenha a sinistralidade do SES como **comparação**, não como premissa central. Use média de vários anos, não de um só.

**Conta ilustrativa** (hipóteses, não dados): 4% de vacância ao ano × 40% de calote ≈ **1,6% da IS ao ano**. Com taxa de 2%, isso daria sinistralidade de **~80%**.

**[VERIFICAR]** Que dado de vacância existe no bronze? Qual período da SES foi usado para os 10,9% e os 73,9%?

### B2. O resultado técnico de 64% não é realista e não é lucro

**Por que é um problema.** O índice combinado de 36% (10,9% de sinistro + 17,1% de comercialização + 8% administrativa) é implausível para um produto novo com seleção adversa. Em seguro-garantia, o comum fica perto de 80% a 90%. Além disso, faltam:
- PIS/COFINS sobre o prêmio (~4,65%);
- custo do resseguro;
- custo de capital regulatório;
- custo de análise de crédito de cada titular.

**O que fazer**
- Renomear deixando claro que é **resultado técnico antes de impostos e capital**.
- Mostrar o índice combinado.
- Adicionar ao menos PIS/COFINS como premissa com fonte.

### B3. A escala é pequena demais para custos em percentual

**Contas a partir do próprio painel:**
- 490 serventias com déficit × 50% escolhendo seguro ≈ **245 apólices** no mercado;
- prêmio médio de **~R$ 1.650/ano**;
- importância segurada média de ~R$ 82 mil (R$ 40,4 mi ÷ 490);
- a seguradora hipotética (5,2%) ficaria com **~13 apólices** e R$ 21,0 mil de prêmio.

**Por que é um problema.** Despesa administrativa de 8% sobre R$ 21 mil dá R$ 1,7 mil por ano, que não paga nem a análise de uma apólice. Com esse volume, o custo é **fixo por apólice**, não um percentual. Também falta o **prêmio mínimo** por apólice que as seguradoras costumam cobrar.

**O que fazer**
- Mostrar no Simulador o **número de apólices** e o **prêmio médio**.
- Avaliar uma premissa de custo fixo por apólice e uma de prêmio mínimo, ambas como suposição com faixa.

### B4. O cenário "máximo" combina todos os extremos ao mesmo tempo (resolve o item 6)

**Por que é um problema.** Mínimo e máximo põem **todas** as suposições no extremo de uma vez. É um cenário de probabilidade quase nula, e é por isso que a faixa chega a 100 vezes (R$ 26 mil a R$ 3 mi). E "mercado máximo" não quer dizer "melhor para a seguradora": mais déficit é mais risco.

**Proposta:**
- **Gráfico tornado:** mexe uma suposição por vez, entre o mínimo e o máximo dela, e mostra quanto o prêmio e o resultado mudam. Deve evidenciar que prob. de déficit, parte descoberta e taxa dominam.
- **Monte Carlo** simples, opcional: sorteia as suposições nas faixas e mostra uma faixa de 90%. Semente fixa, para ser reproduzível.
- Explicar em uma linha, na tela, o que min, base e max significam. Se fizer sentido, separar em "otimista" e "pessimista para a seguradora", que combinam prêmio **e** sinistro de forma coerente.

### B5. Premissas sem fonte ou sem definição

**[VERIFICAR]** Cada uma destas tem decisão registrada e fonte?
- **Férias vencidas ainda não gozadas = 0,50 período:** de onde vem? Não aparece nas "Limitações declaradas".
- **"Decisão parcial" do STF (ADI 8015):** o que ela suspende? Não há definição na tela.
- **Sliders "Escolhe seguro" e "Escolhe fiança":** são independentes. O que acontece com seguro 80% e fiança 40%? "Bens próprios" ficaria negativo. Precisa de trava ou normalização.
- **Rótulo "Sinistralidade (sobre o prêmio ganho)":** a conta usa o prêmio **emitido**. Alinhar o rótulo ou a conta.

### B6. A probabilidade de déficit ignora um dado que já temos

**O que se vê.** Prob. de déficit e parte descoberta são fixas **por classe** (Classe 2: 50% e 50%; Classe 3: 30% e 40%).

**Por que é um problema.** O déficit depende da relação entre o passivo e a capacidade de pagar. Já temos a **arrecadação** de cada serventia.

**Proposta, para discutir:** usar um indicador como `passivo ÷ arrecadação anual` para escalonar a probabilidade ou a parte descoberta, por exemplo em faixas. Isso troca suposições fixas por uma relação baseada em dado, ainda com parâmetros declarados como suposição. Registrar como decisão nova, sem apagar a versão atual: deve ser possível comparar as duas.

---

## C. Qualidade e engenharia de dados

### C1. A correlação RAIS × CNJ (0,996) é dominada por Belo Horizonte

**O que se vê.** Na Conferência entre fontes, a correlação por município é 0,996 (tolerância 0,95). O gráfico em escala log mostra muita dispersão nos municípios pequenos, com casos como CNJ = 2 e RAIS = 14. As maiores diferenças:

| Município | CNJ | RAIS | Diferença |
|---|---|---|---|
| Conselheiro Pena | 44 | 20 | −55% |
| Pratápolis | 14 | 33 | +136% |
| Uberaba | 244 | 169 | −31% |
| Itapecerica | 48 | 77 | +60% |

**Por que é um problema.** Uma correlação calculada sobre valores brutos é puxada pelos municípios grandes. BH sozinho (1.426 × 1.548) garante um valor alto, e a tolerância de 0,95 passa com folga sem testar nada.

**O que fazer**
- Acrescentar duas checagens: **erro percentual mediano por município** e **% de municípios dentro de ±20%** (só com ≥ 5 empregados numa das fontes, para evitar ruído).
- Calcular também a correlação em log.
- O gráfico esconde os municípios com zero numa das fontes. Mostre **quantos são** na legenda.

### C2. A distribuição do estado provavelmente infla o passivo das cidades pequenas

**O que se vê.** 716 municípios (3.119 vínculos) usam a distribuição de MG inteiro. Só 135 (7.859 vínculos) usam a própria.

**Por que é um problema.** Se a distribuição "do estado" inclui BH e as cidades grandes, ela tem salários e tempo de casa maiores que os do interior. O passivo das cidades pequenas tende a sair superestimado.

**O que fazer**
- **[VERIFICAR]** A distribuição "estado" inclui todos os vínculos de MG ou só os dos municípios abaixo do limiar?
- Testar como reserva a **região imediata do IBGE**, a mesma usada no mapa, com o mesmo limiar de 20 vínculos e o estado só se a região não alcançar.
- Mostrar na tabela de sensibilidade quanto o passivo muda.

### C3. A classe indeterminada provavelmente não é aleatória

**O que se vê.** 76 serventias com R$ 0 nos dois semestres de 2025 e 2 com valores conflitantes ficam com classe indeterminada, contando 67,8% no base.

**Por que é um problema.** Serventias com arrecadação zero provavelmente são as menores ou as quase inativas. Dar a elas a proporção média tende a superestimar o universo.

**O que fazer**
- **[VERIFICAR]** Perfil dessas 78: quantos empregados CLT, atribuição, situação.
- No cenário mínimo, usar peso **0** para as indeterminadas, se ainda não for assim.
- Documentar a escolha.

### C4. Arrecadação: tratamento de conflitos e de semestres faltantes

**O que se vê**
- Contratos: "período com valores conflitantes na fonte: **154** violações".
- Limitações: só **2** serventias ficam indeterminadas por conflito.
- Cobertura: "um_semestre: **124**".

**[VERIFICAR]**
- Como foram resolvidos os outros 152 períodos conflitantes, e com qual regra?
- Como as 124 serventias com só um semestre são classificadas, se a classe é semestral? Dobra o valor, usa o semestre disponível, outra regra?
- A fonte de arrecadação tem referência 2026-06-30, mas a classe usa 2025. Qual período alimenta a classe? Deixe isso explícito na tela.

### C5. Rastreabilidade incompleta na tabela de fontes

**O que se vê**
- **CNJ / Justiça Aberta (colaboradores):** URL de origem **"None"** e "Coletado em" só com a data (2026-10-17), sem horário. É a fonte que move o rateio e é a única sem rastro completo.
- **IBGE (malha) e IBGE (municípios):** a "data de referência" é **2026-10-18**, o dia do download. Deveria ser a versão do dado (ano da malha municipal, data da lista de municípios).
- **Colaboradores:** autodeclarados ao CNJ, sem data por serventia. Pode haver declarações antigas, o que merece aviso visível na página Qualidade e no rodapé do Mercado.

**Critério de aceite:** toda fonte com URL, data e hora de coleta e data de referência do **dado**, não do download.

### C6. Pequenas inconsistências a conferir

- **Municípios:** a distribuição cobre **851** municípios com serventia, mas MG tem **853**, e a checagem CNPJ × CNJ fala em "446 de **853** municípios". A Lei 8.935/1994 prevê ao menos um registrador civil em cada sede municipal. **[VERIFICAR]** Quais são os 2 municípios sem serventia no CNJ, e por quê? Pode ser código IBGE errado na fonte.
- **Vínculos sem salário de dezembro:** 887 vínculos ativos, por prazo indeterminado e sem remuneração de dezembro (7,2% dos 12.347). **[VERIFICAR]** São afastados de fato ou efeito do campo da RAIS (campo zerado, admissão e desligamento no mês)?
- **Universo fracionário:** a Tabela por UF mostra **1121.3** serventias no universo, por causa do peso da indeterminada. As outras telas mostram 1.121. Padronizar e explicar na tela que é um valor **esperado**.

---

## D. LGPD (antes do commit)

### D1. Tabelas e gráfico expõem municípios com 1 ou 2 serventias

**O que se vê**
- "Maiores diferenças de serventias (CNPJ − CNJ)": Lagoa Dourada (1 serventia no CNJ), Senador Firmino (2).
- "Maiores diferenças de empregados (RAIS − CNJ)": municípios pequenos como Pratápolis e Conselheiro Pena.
- O gráfico CNJ × RAIS mostra cada município ao passar o mouse.

**Por que é um problema.** Mostrar a contagem da RAIS de um município com um único cartório é, na prática, mostrar dado da RAIS de um empregador identificável, cujo titular é pessoa física.

**O que fazer:** aplicar a mesma regra de **≥ 3 serventias** nessas tabelas e no texto ao passar o mouse. Abaixo disso, agregar por região imediata ou omitir o nome.

**Critério de aceite:** um teste que falhe se qualquer saída do gold com nome de município tiver menos de 3 serventias, com exceção explícita para contagens que são do próprio cadastro público do CNJ.

### D2. Registrar uma limitação honesta (só documentação)

O rateio é proporcional aos empregados declarados ao CNJ, um número público. Qualquer pessoa consegue recalcular a estimativa de cada cartório a partir do total do município. A agregação por 3 serventias protege menos do que parece. A defesa real é que se trata de **estimativa de mercado com premissas públicas**, e não de avaliação de cartório. Acrescente isso às "Limitações declaradas".

---

## E. Apresentação

### E1. Formatação

- Legendas de mapa em R$, com notação brasileira (mil, mi), não "350k" e "2.5M".
- Sliders com vírgula decimal ("2,0%", "1,00", "0,50"); hoje usam ponto.
- "Tabela por UF" e tabela por município com R$ e separador de milhar.
- Bloco "Faixas" como tabela (mínimo, base, máximo × passivo, universo, déficit, IS, prêmio).

### E2. Fontes da página Mercado

O rodapé do Mercado não lista a **SUSEP SES**, embora a faixa de prêmio apareça na página. **[VERIFICAR]** Se o prêmio do Mercado usa só a taxa (suposição), diga isso. Se usa algo da SES, inclua a fonte.

### E3. Texto da página Início

O texto diz "passivo trabalhista de todos os prepostos", mas o modelo só considera **CLT** (estatutários, estagiários e terceirizados ficam fora, D-003). Ajuste o texto ou acrescente "(empregados CLT)".

### E4. Novo destaque: teto do mercado, sem suposições de déficit

Mostrar no Simulador ou na Início o **teto teórico**: todos do universo com déficit igual a 100% do passivo e todos escolhendo seguro.
- **Base:** R$ 256,5 mi × 2% ≈ **R$ 5,1 mi/ano**.
- **Extremo:** R$ 301,8 mi × 3,5% ≈ **R$ 10,6 mi/ano**.

Esse número não depende de nenhuma suposição sobre déficit ou escolha da garantia e torna a conclusão "o mercado de MG é pequeno" à prova de crítica. Confira os valores com o banco.

---

## O que está bom (não mexer)

- **Linhagem:** hash SHA-256 por arquivo do bronze, URL e horário de coleta (exceto C5).
- **Contratos:** 74 contratos com severidade (erro interrompe, aviso registra); 71 sem violação.
- **Coletor do CNJ:** checagem da paginação, que pede página única e confere o total.
- **Sensibilidade:** tabela de sensibilidade do rateio e da regra de classe; ideia certa, só falta corrigir A1.
- **Sanidade do passivo:** R$ 343,4 mi ÷ 12.134 ≈ R$ 28 mil por empregado, cerca de 7 a 8 salários. É plausível para o setor.
- **Conferência entre fontes:** CNJ × RAIS × CNPJ × ANOREG, com as divergências explicadas.

---

## Resumo do que espero na sua resposta

1. Respostas numéricas para todos os **[VERIFICAR]**: A1, A2, A3, A4, A5, B1, B5, C2, C3, C4, C6, E2.
2. Lista de quais itens são **erro confirmado** e quais **não eram erro** (com a explicação).
3. Plano em etapas, separando **antes do commit** (A, D, E e as verificações de C) e **ajuste de modelagem** (B), com estimativa de impacto nos números principais.
4. **Pare** e espere a minha aprovação antes de implementar.
