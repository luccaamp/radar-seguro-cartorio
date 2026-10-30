# Verificação final da Fase 1 — painel de MG

> **Para o Claude Code.** Atue como **engenheiro de dados e cientista de dados sênior, especialista em seguros (seguro-garantia e subscrição)**. Esta é a verificação de fechamento da Fase 1, e você ainda **não implementa nada**: só investiga, mede e propõe.
>
> Este documento **complementa** `revisao_fase1.md`, que traz o detalhe dos blocos A a E. O que há de novo aqui é o **bloco F**: a conferência contra um arquivo baixado do BI do CNJ em 18/10/2026, com totais de controle que já calculei fora do projeto. Se um número seu divergir dos meus, **não ajuste para bater**. Explique a diferença.

> ### ⚠️ Não apagar nem refazer nada
> - **Nada do que já existe pode ser apagado, sobrescrito ou refeito**: código, testes, contratos, tabelas do banco, arquivos do bronze, silver ou gold, documentos em `docs/` e o painel.
> - Esta etapa é de **leitura e comparação**. O arquivo novo do BI **é só uma referência a mais**: ele **não substitui** nenhuma fonte, coletor ou tabela atual.
> - Única escrita permitida nesta etapa:
>   1. guardar o arquivo novo no bronze, numa **pasta nova**, com a linhagem;
>   2. **acrescentar** registros (no fim) em `docs/diario.md`, `docs/erros_ia.md` e `docs/decisoes.md`, sem editar nem remover registros antigos;
>   3. scripts de conferência **novos** e separados (por exemplo, em `scripts/` ou numa pasta de análises), que só **leem** o banco.
> - Se achar que algo precisa ser apagado ou refeito, **escreva isso no plano** e espere a minha aprovação.

---

## 0. Regras (valem para tudo)

- Siga o `CLAUDE.md`.
- **Nunca** faça commit nem push. No fim, só liste os arquivos alterados e sugira a mensagem de commit.
- Tudo gratuito e local. Nada de nuvem.
- Todo número que você citar precisa vir do banco ou dos arquivos, com **fonte e data de referência**. Não estime de cabeça.
- **LGPD:** nenhum nome, CPF ou e-mail de titular ou substituto fora do bronze. Nenhuma estimativa no nível de um cartório identificável (municípios com menos de 3 serventias são agregados).
- Registre **na hora**: cada erro confirmado em `docs/erros_ia.md`, cada descoberta em `docs/diario.md` e cada decisão nova (proposta, ainda não aprovada) em `docs/decisoes.md`, marcada como "PROPOSTA".
- **Os testes não gravam no banco real.** Para qualquer consulta exploratória, abra o DuckDB em **modo somente leitura**.

## 1. Como proceder

1. Leia este documento e `revisao_fase1.md` inteiros antes de rodar qualquer coisa.
2. Coloque o arquivo novo no bronze, numa pasta nova (seção 2), e registre a linhagem.
3. Responda a **todos** os [VERIFICAR] dos blocos A a F, com números.
4. Classifique cada item como **ERRO CONFIRMADO**, **NÃO ERA ERRO** (com explicação) ou **INCONCLUSIVO** (com o que falta saber).
5. Proponha um plano em etapas, com estimativa de impacto nos números principais. Depois **pare** e espere a minha aprovação.

---

## 2. Arquivo novo: entrada no bronze

Vou copiar para a pasta do projeto um arquivo exportado do **Painel de Dados Estatísticos das Serventias Extrajudiciais (CNJ)**:
`https://paineisanalytics.cnj.jus.br/single/?appid=6ae52b4b-f6fb-4e06-8f8a-19c0656b1408&sheet=8413120e-2be0-4713-ae80-8152be891d36`

| Arquivo | Conteúdo | Formato |
|---|---|---|
| `atos_arrecadacoes_custeio_e_repasse.csv` | Por CNS e semestre: arrecadação, repasse, custeio, quantidade de atos e atribuição. De 2005 ao 1º semestre de 2026. 524.712 linhas. **Não tem UF nem situação**: junte pelo CNS com o **cadastro que já existe no projeto** (Justiça Aberta). | TAB, UTF-8, CRLF, decimal com vírgula, milhar com ponto, `-` = vazio |

O cadastro do BI (lista de serventias) **não será usado**: o projeto já tem essas informações pelo Justiça Aberta, e ele traz nomes e e-mails de titulares. Os números de referência do cadastro neste documento (F1, F7) vêm dele e servem só para comparar com o seu cadastro.

**O que fazer**
- Guardar o arquivo **sem alteração** no bronze, numa **pasta nova**, seguindo a convenção que já existe, com hash SHA-256, URL de origem, data e hora da exportação (18/10/2026, manual) e **data de referência do dado** (último período completo: 2º semestre de 2025).
- Não use o arquivo no modelo nem crie tabela nova no silver ou no gold. Nesta etapa, ele é **só para conferência**, lido por scripts separados.

**Armadilhas conhecidas do CSV** (confira e confirme):

1. **Mudança de formato no 2º semestre de 2025.**
   - Até o 1º semestre de 2025: uma linha por CNS e período, com `Atribuição = "-"`.
   - A partir do 2º semestre de 2025: **uma linha por atribuição**.
   - Arrecadação, repasse e atos vêm **divididos** entre as linhas.
   - O **custeio vem repetido inteiro em todas as linhas** do mesmo CNS. Em 8.183 CNS do Brasil (1.445 em MG), o custeio é idêntico em todas as linhas.
   - Somar o custeio dá R$ 15,86 bi no 2º semestre de 2025. Com um valor por CNS, dá **R$ 7,30 bi**.
2. **1º semestre de 2026 em formato misto:**
   - o repasse vem em linhas separadas, com `Atribuição = "-"` e arrecadação zero;
   - o custeio está vazio.
   - **Não usar 2026** para classe nem para margem.
3. **952 linhas sem data** (341 CNS, arrecadação zero), **4 custeios negativos** e **6 CNS com 2 linhas** no 1º semestre de 2025, com valores diferentes (conflito real).
4. **Quantidade de atos truncada** em alguns períodos (ex.: 251 entre vizinhos de ~250 mil, em 2012). Atos não são usados no modelo; só registre.

---

## F. Conferência com o BI do CNJ (novo, antes do commit)

> Os valores de referência abaixo foram calculados assim. Universo = CNS com `Status = Ativo` no cadastro do BI (sem duplicatas), juntado ao CSV pelo CNS, com a UF desse cadastro. Você deve usar **o seu cadastro** (Justiça Aberta) no lugar dele. A arrecadação de um semestre é a soma de **todas** as linhas do CNS no período. O custeio é **um** valor por CNS e período: no 2º semestre de 2025, o valor repetido; no 1º semestre de 2025, a soma das linhas, com nulo se todas forem nulas. Reproduza com a sua própria leitura.

### F1. Universo de MG

| Indicador | Referência (BI) | Seu banco |
|---|---|---|
| Serventias ativas em MG | 2.525 | ? |
| Providas | 1.654 | ? |
| Vagas | 830 | ? |
| Conversão em diligência | 28 | ? |
| Sob intervenção | 13 | ? |

**[VERIFICAR]** Os números do seu cadastro batem com a referência? Quantos CNS de MG do seu cadastro **não aparecem** no CSV, e quantos do CSV não estão no seu cadastro? Não publique o nome do cartório na resposta.

### F2. Arrecadação de 2025 em MG: o teste mais importante

| Período | Referência (BI), todas as ativas de MG |
|---|---|
| 1º sem/2025 | **R$ 2.373,9 mi** |
| 2º sem/2025 | **R$ 3.067,7 mi** |
| Total 2025 | **R$ 5.441,6 mi** |

**[VERIFICAR]**
- A soma da arrecadação de MG no seu silver, por semestre, para as mesmas 2.525.
- **Se o 2º semestre vier menor que a referência**, o coletor pode estar pegando **uma linha só** por CNS e período, quando a API devolve várias por atribuição. Nesse caso a classe Classe 1 × Classe 2 de muitos cartórios está errada. Isso é um **erro grave** e deve ir para `erros_ia.md`.
- Mostre como o coletor trata a API quando há mais de um registro para o mesmo CNS e período: soma, primeiro, último ou conflito. Aponte o trecho do código.
- Compare CNS a CNS (agregado): quantas serventias de MG divergem mais de 1% entre o seu silver e o CSV em cada semestre?

**Critério de aceite:** diferença total abaixo de 0,5% por semestre, ou explicação documentada (por exemplo, data diferente de extração). Crie um **contrato de qualidade novo** que confira o total de MG por semestre contra um total de controle registrado.

### F3. Conflitos de arrecadação (responde ao C4)

Referência: em MG há **151 pares CNS-período** com mais de uma linha total (`Atribuição = "-"`). Por ano:
- 2014: 47 e 2015: 51;
- 2024: 15;
- **2025: 2**;
- os demais espalhados.

**[VERIFICAR]**
- O seu contrato "período com valores conflitantes" acusa 154. Explique a diferença de 3.
- Confirme que só **2** conflitos caem em 2025, os mesmos 2 indeterminados.
- Confirme que conflitos de anos antigos **não afetam** nada do modelo.
- Diga qual regra resolve cada conflito.

### F4. Semestre faltando no 2º semestre de 2025

Referência para MG:

| Situação | 1º sem/2025 | 2º sem/2025 |
|---|---|---|
| Sem nenhuma linha | 0 | **168** |
| Linha com arrecadação zero | 148 | 68 |
| Zero nos dois semestres | 81 | |
| Valor positivo em só um semestre | 222 | |

Contexto: o CNJ prorrogou até 15/04/2026 o envio do 2º semestre de 2025 por causa da troca de sistema, e no fim de março só ~50% tinham enviado (fonte: IRIB, 01/04/2026).

**[VERIFICAR]**
- Compare com os seus números (76 indeterminadas por zero nos dois semestres; 124 com só um semestre). Explique as diferenças: data de extração, regra de "zero" × "ausente" etc.
- Para cada caso (falta o 1º semestre, falta o 2º, zero nos dois), diga **como a classe é decidida hoje**.
- Quantas serventias **com o 1º semestre acima de R$ 300 mil e sem o 2º** existem em MG? Elas estão sendo classificadas como obrigadas?
- Proponha a regra: tratar ausência como "desconhecido" e não como zero, e decidir pelo semestre disponível com aviso. Registre como PROPOSTA.

### F5. A regra dos R$ 300 mil semestrais (Prov. 213/2026, alterado pelo 243/2026)

Referência (providos de MG, 2025, ausente = não passa):

| Leitura | Serventias | Arrecadação |
|---|---|---|
| Acima de R$ 300 mil nos **dois** semestres | 928 | R$ 4,02 bi |
| Média anual acima de R$ 600 mil | 1.065 | R$ 4,17 bi |
| Acima de R$ 300 mil no 2º semestre | 1.106 | R$ 4,16 bi |
| **Seu universo base** | **1.121** | ? |
| Acima de R$ 300 mil em **algum** semestre | 1.161 | R$ 4,22 bi |

**[VERIFICAR]**
- Qual leitura o código usa hoje? Em que arquivo e linha?
- Cite o texto literal do Prov. 213/243 que define a Classe 1 (período de apuração: semestre anterior, último semestre ou ano). Diga se a sua leitura segue o texto.
- Proponha uma leitura principal com justificativa e inclua **as outras na tabela de sensibilidade**, como já existe para v1 × v2.

### F6. Custeio e repasse: viabilidade para o B6 (só medir)

Referência para os providos de MG em "algum semestre acima de R$ 300 mil" (1.161), em 2025:

| Item | Valor |
|---|---|
| Arrecadação | R$ 4.218,4 mi |
| Repasse | R$ 1.697,6 mi |
| Custeio (um valor por CNS e período) | R$ 1.115,9 mi |
| **Saldo (arrecadação − repasse − custeio)** | **R$ 1.404,9 mi** |
| Saldo negativo | 55 serventias |
| Custeio nulo ou zero | 22 |
| Custeio maior que a arrecadação | 3 |

**[VERIFICAR]**
- A API do Justiça Aberta que o coletor já usa traz repasse e custeio? Se trouxer, os totais conferem com o CSV? Se não, o CSV do BI é a fonte.
- **Coerência entre fontes, agregada por município com ≥ 3 serventias ou por região imediata:** o custeio anual precisa ser **maior** que a folha anual RAIS com encargos dos mesmos cartórios. Quantas áreas violam isso? Uma violação indica custeio mal declarado ou rateio da RAIS errado.
- Razão **passivo dos obrigados ÷ saldo anual** no agregado de MG e a distribuição por faixas (menos de 3 meses, 3 a 12 meses, mais de 12 meses, saldo negativo). Mostre só **contagens e somas por faixa**, nunca o cartório.

**Não implemente o B6.** Traga os números para eu decidir.

### F7. Totais Brasil (preparação da Fase 2)

Registre no diário como totais de controle futuros (BI CNJ, 2025):

| Indicador | Valor |
|---|---|
| CNS distintos no cadastro / ativos | 11.867 / 11.866 |
| Providos ativos | 8.378 |
| Arrecadação 2025 (todos com dado) | R$ 36,23 bi |
| Repasse 2025 | R$ 12,34 bi |
| Custeio 2025 (deduplicado) | R$ 13,26 bi |
| Base "completa" (arrecadação nos dois semestres e custeio > 0) | 10.638 serventias; arrecadação R$ 35,29 bi; 88,1% com saldo positivo; margem mediana 34,1% |
| ANOREG (referência atual do projeto) | 12.210 serventias |

**[VERIFICAR]** Explique em uma frase a diferença entre 11.866 (CNJ) e 12.210 (ANOREG), ou marque como INCONCLUSIVO.

### F8. Estudo externo: só comparação, nunca fonte

Recebi um estudo de mercado de terceiros com estes números: 15.867 cartórios, 5.335 elegíveis, arrecadação de R$ 29,15 bi, passivo de R$ 3,36 bi, prêmio de R$ 7,83 mi/ano no Brasil e passivo de MG de R$ 461,5 mi.

Ele foi reproduzido em grande parte com o CSV:
- **"15.867" é quase certamente erro de digitação de 11.867**;
- o passivo dele é **≈ 11,5% da arrecadação** em todas as UFs (3,36 ÷ 29,15 e 461,5 ÷ 4.018), ou seja, deriva da receita e não de vínculos;
- usa IS = 100% do passivo, 70% de adesão e taxa de 1%.

**O que fazer**
- Registrar no `diario.md` como descoberta.
- **[VERIFICAR]** Montar a "ponte" numérica do passivo de MG entre o estudo externo e o seu modelo:

  | Etapa | Valor |
  |---|---|
  | Passivo do estudo externo | R$ 461,5 mi |
  | Diferença de universo | ? |
  | Diferença de método (receita × vínculo) | ? |
  | Diferença de premissas (10 anos fixos, INSS em verbas indenizadas, RAT 2%) | ? |
  | Seu passivo dos obrigados | R$ 256,5 mi |

  Depois, a ponte do prêmio: passivo → déficit → escolha pelo seguro → taxa.
- Não citar o estudo como fonte de nenhum número do painel.

---

## A–E. Itens de `revisao_fase1.md` (detalhe lá; aqui, o que precisa vir na resposta)

**A. Prováveis erros (antes do commit)**
- **A1:** classe usada nas faixas de déficit por regra (v1 × v2) e se o peso da indeterminada (67,8%) é recalculado. Teste de **monotonicidade** (universo maior → déficit, IS e prêmio maiores ou iguais) em min, base e max.
- **A2:** data-base de cada componente (tempo de casa, 13º, férias, aviso, correção INPC) e a proposta de **uma única data-base** coerente com o art. 5º do Prov. 227 e a regra da primeira declaração.
- **A3:** como o 13º entra hoje, com um vínculo de exemplo calculado à mão. Em demissão em 31/12, o 13º do ano normalmente já foi pago.
- **A4:** quantas das 1.121 têm **zero CLT** e quanto pesam nas 490 "com déficit". Passivo zero precisa contribuir com zero.
- **A5:** por que as correções 2, 3, 4 e 6 não aparecem no painel (não implementadas ou Streamlit não reiniciado). Item 5: data de modificação do DuckDB real antes e depois de rodar os testes.

**D. LGPD (antes do commit)**
- **D1:** tabelas de conferência e o texto ao passar o mouse mostram municípios com 1 ou 2 serventias. Teste que falhe se qualquer saída do gold com nome de município tiver menos de 3 serventias, com exceção explícita para contagens do cadastro público do CNJ.
- **D2:** acrescentar às limitações que o rateio por empregados declarados é recalculável por terceiros.

**C. Qualidade (verificações antes do commit)**
- **C1:** correlação em log, erro percentual mediano por município, % de municípios dentro de ±20% (com ≥ 5 empregados) e quantos ficam com zero numa das fontes.
- **C2:** a distribuição "estado" inclui BH? Impacto de usar a região imediata como reserva.
- **C3:** perfil das indeterminadas (CLT, atribuição, situação); peso zero no cenário mínimo. Junte com o F4.
- **C4:** respondido pelo F2, F3 e F4.
- **C5:** URL, data e hora e data de referência do **dado** em toda fonte, incluindo o arquivo novo.
- **C6:** os 2 municípios de MG sem serventia (851 × 853); os 887 vínculos sem salário de dezembro; o universo fracionário (1121,3).

**B. Modelo de seguro (só diagnóstico; não implementar)**

Como especialista em seguros, responda e proponha, sem mexer no código:
- **B1:** período da SES usado para 10,9% e 73,9%; se é sinistro sobre prêmio ganho ou emitido; média de vários anos. Que dado de vacância existe no bronze para estimar **P(delegação termina no ano)**?
  - O seu cadastro (Justiça Aberta) tem alguma data de vacância, de ingresso do responsável ou de decisão da situação? Se tiver, mostre quantas serventias de MG viraram vagas por ano, **só agregado**. Se não tiver, diga. O cadastro do BI tem essas datas, e eu decido depois se vale trazê-lo.
- **B2:** índice combinado completo, incluindo PIS/COFINS sobre prêmio (com fonte), e o rótulo "resultado técnico antes de impostos e capital".
- **B3:** número de apólices, prêmio médio e importância segurada média no mercado e na fatia hipotética; impacto de um **prêmio mínimo** e de um **custo fixo por apólice** (suposições com faixa).
- **B4:** proposta de gráfico tornado (uma premissa por vez) e de cenários coerentes "otimista" e "pessimista para a seguradora".
- **B5:** fonte das férias vencidas (0,50 período); definição da "decisão parcial" da ADI 8015; trava entre os sliders seguro + fiança ≤ 100%; rótulo emitido × ganho.
- **B6:** usar o F6 para propor faixas de **passivo ÷ saldo anual** no lugar da probabilidade fixa por classe. Deixe claro que o Prov. 227 mede solvência por **bens livres de ônus**, e que o saldo é só um indicador aproximado.
- **Confirmar o conceito de IS:** a importância segurada é a **parte descoberta (déficit)**, e não o passivo inteiro. O prêmio é IS × taxa, anual. Responda se o código segue isso em todos os pontos.

**E. Apresentação (junto com o bloco A)**
- Formatação brasileira (R$, mil, mi, vírgula decimal) em mapas, sliders e tabelas.
- SUSEP SES no rodapé do Mercado, se for usada.
- "Empregados CLT" no texto da Início.
- **Teto teórico:** R$ 256,5 mi × 2% ≈ R$ 5,1 mi/ano no base; R$ 301,8 mi × 3,5% ≈ R$ 10,6 mi/ano no extremo. Confira com o banco.

---

## 3. Formato da sua resposta

1. **Tabela de [VERIFICAR]:** item | número do banco | número de referência | bate? | explicação.
2. **Classificação:** ERRO CONFIRMADO / NÃO ERA ERRO / INCONCLUSIVO, com uma linha de justificativa cada.
3. **Impacto estimado** de cada erro confirmado nos números principais de MG:
   - serventias ativas e obrigadas;
   - passivo de todas as ativas e dos obrigados;
   - déficit;
   - importância segurada;
   - prêmio de mercado.
4. **Plano em etapas:**
   - **Etapa 1 (antes do commit):** A, D, E, F2 a F5 e as verificações de C.
   - **Etapa 2 (ajuste de modelagem, depende de aprovação):** B, F6 e o uso do CSV como fonte.

   Cada etapa com os arquivos que mudam e os testes novos. Para cada mudança, diga se ela **acrescenta** algo ou **altera** algo que já existe. Alterações precisam da minha aprovação item a item.
5. **Registros feitos** em `erros_ia.md`, `diario.md` e `decisoes.md` (lista dos itens adicionados).
6. **Pare.** Não implemente nada antes da minha aprovação.
