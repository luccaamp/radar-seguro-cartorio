# Radar Seguro-Garantia Cartórios: Especificação do Projeto

> Documento de referência para a IA de código (Claude Code) que constrói o projeto.
> Leia tudo antes de escrever código. Siga as fases em ordem e não pule os critérios de aceite.
> Última revisão: 2026-10-18 (início da Fase 1: rateio `por_empregados_cnj` como padrão, D-005). Revisão anterior: 2026-10-17 (fatos normativos conferidos no texto oficial). Esta versão torna o projeto **100% gratuito** e muda a prioridade para **painel e chat**. Histórico no `docs/diario.md`; decisões com opções e justificativa em `docs/decisoes.md`.

## 0. Contexto e objetivo

**Problema de negócio.** O Provimento CNJ 227, de 09/06/2026, foi publicado no DJe/CNJ nº 133 de 11/06/2026 e está em vigor desde 10/08/2026 (art. 20: 60 dias após a publicação). Ele obriga os delegatários de cartórios a:

- declarar o passivo trabalhista de **todos os prepostos em atividade** (arts. 3º e 4º). No primeiro ano, as declarações de passivo **e de solvência** venceram 30 dias após a vigência, por volta de 09/09/2026 (art. 18). Depois o ciclo é anual, com base em 31/12 e entrega até 31/03 (art. 4º);
- demonstrar solvência com bens livres de ônus e não impenhoráveis (arts. 8º a 10).

Se houver déficit de cobertura, o delegatário é notificado e tem 60 dias para regularizar a solvência ou apresentar garantia (art. 13):

- **fiança bancária** emitida por instituição classificada como **S1 ou S2** pelo Banco Central; ou
- **seguro-garantia** de seguradora habilitada pela SUSEP.

A garantia cobre **100% do déficit**, vale no mínimo 1 ano, tem a renovação comprovada 30 dias antes do vencimento e o valor atualizado anualmente (art. 13, §2º). É liberada quando os bens voltam a cobrir o passivo (art. 13, §3º).

**Definição de passivo (arts. 2º, I, 5º e 6º).** O passivo é o montante das verbas rescisórias e dos encargos devidos a todos os prepostos em atividade. Na prática, é o custo de demitir todos sem justa causa (art. 5º, IV). É exatamente esse ponto que a ANOREG critica na ADI. Composição:

- aviso prévio indenizado, com a proporcionalidade da Lei 12.506/2011;
- férias vencidas e proporcionais + 1/3, **inclusive sobre o aviso prévio indenizado**;
- 13º proporcional, **inclusive sobre o aviso prévio indenizado**;
- multa de 40% do FGTS;
- outras verbas de acordo ou convenção coletiva;
- encargos do empregador: INSS patronal, RAT × FAP e FGTS mensal (parágrafo único do art. 5º).

**Base de cálculo (art. 6º):** a maior remuneração fixa do preposto, mais a média duodecimal das parcelas variáveis dos últimos 12 meses. O saldo de salário **não** consta do art. 5º.

**Segurado.** O texto **não define quem é o segurado** (beneficiário) da garantia. Diz apenas que ela é "apta a elidir a presunção de risco à continuidade do serviço público" (art. 13, §1º). Isso é tratado como risco (§10).

**Natureza do mercado.** O mercado já existe, porque o primeiro ciclo já venceu, e se renova todo ano. A receita é tratada como **anual e recorrente** (renovação da garantia).

Ficam fora da norma (art. 19):

- as serventias da **Classe 1 do Provimento 213/2026**. O art. 19 do 227 escreve "Classe I", mas o 213 numera as classes como 1, 2 e 3, e "Subclasse I" é uma faixa da Classe 3. O projeto lê "Classe I" como Classe 1 (ver `docs/decisoes.md`);
- as serventias **sob interinidade**.

**Critério da Classe 1 (art. 16 do 213, com a redação do Prov. 243, de 21/07/2026, publicado em 23/07/2026 e em vigor desde 22/08/2026):** **receita bruta semestral** de até **R$ 300.000,00**. Antes do 243, o limite era R$ 100.000,00. Detalhes:

- **receita bruta semestral** (art. 2º, XXIV): emolumentos e outras receitas do serviço, incluindo o ressarcimento de atos gratuitos e a complementação de renda mínima. Deduz só os valores arrecadados por conta de terceiros e os repasses legais obrigatórios. Não deduz despesas nem tributos;
- **enquadramento** reavaliado anualmente pela média das receitas brutas semestrais do exercício anterior (§1º), com regra de 10% e dois ciclos para migrar de classe (§3º);
- **limites** atualizados a cada ano de vigência, com divulgação pela Corregedoria Nacional (§2º). O 243 retirou a referência ao IPCA.

**Base e sensibilidade:** o limite de R$ 300 mil é a base, e o de R$ 100 mil é a sensibilidade. As duas versões ficam em `config/regras_classificacao.yaml`. Como a arrecadação das fontes públicas pode não coincidir com a receita bruta do art. 2º, XXIV, a classificação é sempre marcada como **aproximada**.

**Arts. 8º a 17.** Esses artigos contêm a declaração de solvência (8º a 10), a avaliação e a obrigação de garantia (11 a 14) e a fiscalização, o Regime Especial e as penalidades (15 a 17). Se forem suspensos, a declaração de passivo (arts. 3º a 7º) continua formalmente, mas sem a sanção do art. 17.

**ADI 8015.** A ANOREG/BR ajuizou a ação contra os **arts. 8º a 17**. Situação em 17/10/2026:

- protocolada e distribuída em 08/09/2026; relator Min. Flávio Dino;
- em 18/09, o relator adotou o **rito do art. 12 da Lei 9.868/1999**, ou seja, sem liminar separada e com julgamento direto do mérito;
- informações do CNJ em 30/09; manifestação da AGU em 07/10; processo com vista à PGR;
- em 13/10, foi indeferido o pedido de amicus curiae da Ad Notare;
- **não há liminar.**

> Fatos confirmados pela IA no texto oficial (atos.cnj.jus.br e portal do STF) em 2026-10-17, na Fase 0. Cópias em `data/bronze/normas/` e `data/bronze/stf/`.

**O que o projeto entrega, em ordem de prioridade:**

1. **Painel de cartórios do Brasil** (principal): quantos cartórios existem por UF, município, tipo e situação; arrecadação; funcionários; passivo trabalhista estimado; déficit provável; e um **simulador** de mercado de seguro-garantia. Com **dados reais, atuais e corretos**, em volume suficiente para análise.
2. **Chat de perguntas** (principal): responde perguntas como "quantos cartórios em MG teriam déficit se o STF suspender os arts. 8º a 17?", sempre com o número, a conta e a fonte.
3. **Radar de notícias e normas** (opcional): avisa quando há mudança nas regras. Primeiro numa versão simples, sem IA. Só é feito se o painel e o chat estiverem prontos e bem feitos.

**Uso final.** Projeto de portfólio para entrevista: 5 minutos, 5 slides e demo ao vivo, rodando no computador do autor.

**Mínimo da demo**, que não pode faltar:

1. painel com as páginas Mercado e Simulador funcionando, começando por MG;
2. o chat respondendo perguntas sobre os dados com número, conta e fonte.

O radar é **bônus**.

**Restrições inegociáveis.**

1. **100% gratuito.** Nenhum serviço pago, nenhum cartão de crédito, nenhuma chave de API com créditos, nenhum cadastro em nuvem (Google Cloud, AWS, Azure, MotherDuck etc.). Tudo roda no computador do autor, com fontes públicas e programas gratuitos. Se alguma etapa parecer exigir algo pago ou um cadastro, a IA **para e pergunta** antes.
2. **Dados reais.** Os números do painel vêm de fontes oficiais públicas, com a data de referência visível. Dados sintéticos só em `tests/`.
3. Só dados públicos. Nenhuma precificação interna de qualquer seguradora. O market share é de uma **seguradora hipotética** (`fonte: suposição`).
4. Nenhum número fixo no código. Toda premissa é versionada e tem fonte.
5. Nenhum dado pessoal exposto em nível individual (ver §6, LGPD).
6. Todo número mostrado ao usuário carrega a fonte, a data de referência e a versão das premissas.

## 1. Fontes de dados (todas gratuitas e sem cadastro)

O painel cruza várias fontes, porque nenhuma traz tudo sozinha. A qualidade dos dados é o ponto principal do projeto.

### 1.1 Mapa de fontes

| Entidade | Fonte primária | Conferência / plano B | Granularidade | Risco |
|---|---|---|---|---|
| Universo de serventias (CNS, UF, município, atribuição, titular/interino) | **Painel de Dados Estatísticos das Serventias Extrajudiciais do CNJ** (dados do Justiça Aberta, exportação em .csv/.xlsx) | **Dados abertos de CNPJ da Receita Federal** (download mensal, filtrar pelo CNAE 6912-5/00); listagens das corregedorias estaduais (TJs); painel de vacâncias da Corregedoria Nacional (serventias vagas, que indicam interinidade) | Serventia | **Alto**: o Justiça Aberta migrou de plataforma em 2026 e é preciso confirmar se o painel público continua disponível e com quais campos |
| Arrecadação | Painel do CNJ / Justiça Aberta (pode vir **por faixa**) | Editais de concurso e sorteio dos TJs, que trazem a classe da serventia | Serventia (valor ou faixa) | **Alto** |
| Vínculos, salários e tempo de emprego | **Microdados da RAIS no PDET** (Ministério do Trabalho), download direto, filtrar pelo CNAE 6912-5/00. Começar só por MG | Novo CAGED (também no PDET) para a tendência recente | Município × faixas | **Alto**: defasagem de 1 a 2 anos, não identifica a serventia e pode **não captar vínculos registrados no CPF/CEI do titular** (ver §10) |
| Totais de controle do setor | Relatório **"Cartório em Números"** (ANOREG) | — | Brasil | Baixo. Serve só para conferir totais (serventias e empregados) |
| Contexto | IBGE (população, PIB municipal) | — | Município | Baixo |
| Seguro-garantia | SUSEP SES (consulta pública de prêmios e sinistros dos ramos de garantia) | Publicações setoriais com faixas de taxa | Ramo/mês | Médio: não traz importância segurada, então serve para sinistralidade, não para taxa |
| Normas | atos.cnj.jus.br (Provimentos 227, 213, 243 e posteriores); STF (ADI 8015) | Sites das associações (ANOREG, Arpen, IRTDPJ, IRIB, CNB) | Documento/artigo | Médio: o portal do STF costuma bloquear coleta automática |
| Proposições legislativas (só se houver radar) | APIs de dados abertos da Câmara e do Senado | — | Proposição | Baixo |

**Fora do projeto:** BigQuery/Base dos Dados (exige conta no Google Cloud e pode gerar cobrança), Claude API (paga por uso), MotherDuck, GitHub Actions e qualquer outro serviço em nuvem.

### 1.2 Regras para as fontes

- Toda coleta grava o **bruto imutável** em `data/bronze/<fonte>/<data_coleta>/`, com metadados: URL, data, hash e versão do coletor.
- Arquivos grandes (RAIS, CNPJ) são baixados uma vez, filtrados logo na leitura (só o CNAE 6912-5/00 e as UFs em uso) e gravados filtrados em Parquet. O arquivo bruto completo pode ser apagado depois, mantendo o hash e a URL de origem registrados.
- Respeitar o robots.txt e os termos de uso, com intervalo entre requisições e User-Agent identificável.
- Quando uma fonte não puder ser coletada automaticamente, **aceitar download manual** feito pelo autor e registrar a origem. Isso é melhor que um coletor frágil.
- Se o CNS não estiver disponível em alguma fonte, a junção usa UF, município (normalizado pelo código IBGE), atribuição e nome normalizado, com **score de match** e revisão manual dos casos ambíguos. Registrar a taxa de match.
- **Períodos de referência**: usar o dado mais recente de cada fonte. A `data_referencia` de cada fonte é registrada e **exibida no painel**. A defasagem salarial da RAIS é corrigida por uma premissa (`correcao_salarial_rais`).

## 2. Arquitetura (tudo local)

### 2.1 Camadas

- **Bronze**: o bruto como veio, particionado por data de coleta.
- **Silver**: dados limpos e tipados, com chaves normalizadas (código IBGE do município, CNS) e uma tabela por entidade. **Nome e CPF de titular são descartados aqui** (ver §6).
- **Gold**: tabelas de negócio e métricas, como `fato_mercado_uf`, `fato_passivo_municipio` e `dim_serventia`.
- **Estado do app**: no mesmo arquivo DuckDB local, em tabelas separadas: `premissas_versoes`, `cenarios_salvos`, `log_decisoes` e, se houver radar, `eventos_radar` e `aprovacoes`.

### 2.2 Stack

| Função | Escolha | Observação |
|---|---|---|
| Linguagem | Python 3.12 | gerenciado com `uv`, sem alterar o Python do sistema (3.13.3) |
| Banco | **DuckDB em arquivo local** (`data/radar.duckdb`) + Parquet | fora do git |
| Transformações | SQL em arquivos versionados | dbt-duckdb opcional |
| Orquestração | `uv run pipeline.py [etapa]` | substitui o `make` |
| Validação de dados | Pandera ou testes SQL simples | contratos por tabela |
| LLM do chat (e do radar, se houver) | **Ollama**, rodando no computador do autor, com um modelo aberto que suporte *tool calling* | escolhido na Fase 0 conforme a RAM e a GPU disponíveis. O código acessa o LLM por uma interface única (`src/llm.py`), para dar para trocar de modelo sem reescrever o chat |
| Saída estruturada do LLM | Pydantic | |
| Interface | Streamlit, rodando localmente | |
| Agendamento do radar (se houver) | execução manual (`uv run pipeline.py radar`); opcionalmente o Agendador de Tarefas do Windows | |
| Testes | pytest | |

### 2.3 Estrutura de pastas

```
radar-seguro-cartorio/
├── pipeline.py                # orquestrador único: uv run pipeline.py [etapa]
├── data/
│   ├── bronze/                # bruto (git-ignored; amostras pequenas em data/samples/)
│   ├── silver/
│   ├── gold/
│   └── radar.duckdb           # banco local (git-ignored)
├── config/
│   ├── premissas/             # semente versionada: premissas_v001.yaml ...
│   ├── regras_classificacao.yaml  # limites de Classe por norma e vigência
│   ├── cenarios_stf.yaml      # definições fixas dos cenários do STF
│   └── llm.yaml               # modelo do Ollama e parâmetros
├── src/
│   ├── llm.py                 # interface única para o LLM local
│   ├── ingest/                # um coletor por fonte, todos idempotentes
│   ├── transform/             # bronze→silver→gold
│   ├── quality/               # contratos e checagens
│   ├── model/                 # funções puras de cálculo
│   ├── agent/                 # chat
│   │   └── tools/             # camada semântica
│   ├── radar/                 # opcional
│   └── eval/
├── app/                       # Streamlit
├── tests/
├── eval/
│   ├── gabarito_chat.csv
│   └── gabarito_radar.csv     # só se houver radar
├── docs/
│   ├── SPEC.md
│   ├── diario.md
│   ├── erros_ia.md
│   ├── decisoes.md            # decisões com contexto, opções e justificativa
│   ├── viabilidade.md         # criado na Fase 0
│   └── dicionario_dados.md
└── README.md
```

**"Do zero"** significa rodar o pipeline **a partir dos snapshots do bronze**, sem coletar de novo.

### 2.4 Premissas versionadas

- **Semente**: o YAML em `config/premissas/` é a versão inicial, versionada no git.
- **Versões salvas**: ficam na tabela `premissas_versoes` do DuckDB local. Cada versão guarda o número, o diff sobre a anterior, o autor, a data e a origem (ajuste no simulador ou evento do radar). O app lê a versão vigente do banco e cai para a semente se o banco estiver vazio.
- **Cenários**: `cenarios_stf.yaml` tem as definições fixas (`mantem`, `suspende_8_17`, `parcial`). `cenarios_salvos` guarda as combinações que o usuário salva no simulador.

Cada premissa tem `valor` (ou `min`/`base`/`max`), `unidade`, `fonte` (URL ou "suposição"), `data_referencia` e `justificativa`. Exemplo:

```yaml
versao: 1
criada_em: 2026-10-17
premissas:
  prob_deficit:
    fonte: suposição
    justificativa: patrimônio do titular não é público
    valores:
      faixa_1: {min: 0.30, base: 0.50, max: 0.70}
  pct_descoberto:
    fonte: suposição
    valores:
      faixa_1: {min: ..., base: ..., max: ...}
  taxa_seguro_anual:
    fonte: <url da referência pública>
    valores: {min: ..., base: ..., max: ...}
```

Os números acima são **placeholders**. A IA não deve inventar valores. Onde não houver fonte, marcar `fonte: suposição` e pedir validação ao autor.

Premissas previstas, além dos parâmetros legais do passivo:

- `prob_deficit` e `pct_descoberto`, por faixa;
- `escolha_garantia`, com três parcelas que somam 1 (regulariza com bens próprios, fiança, seguro);
- `taxa_seguro_anual`;
- `market_share_hipotetico` (`fonte: suposição`);
- `sinistralidade`;
- `comissao`;
- `despesa_administrativa`;
- `correcao_salarial_rais`;
- `base_remuneracao_rais`: aproximação da base do art. 6º. Padrão `dezembro` (remuneração de dezembro da RAIS); alternativa `media_anual`;
- `incluir_saldo_salario`: padrão `false`, porque o saldo de salário não consta do art. 5º do 227;
- `acrescimo_cct_pct`: acréscimo percentual para as verbas de acordo ou convenção coletiva (art. 5º, V), que não são estimáveis com dados públicos. Padrão `0` (`fonte: suposição`, limitação declarada);
- `aliquotas_encargos`: INSS patronal, RAT × FAP e FGTS mensal (parágrafo único do art. 5º), com fonte legal;
- `fator_cobertura_rais` (se a RAIS captar menos empregados que o "Cartório em Números");
- `peso_classe_indeterminada_base`;
- `metodo_rateio_padrao`;
- `limiar_agregacao_lgpd`, com valor 3.

A definição de Classe 1 também é premissa. Ela fica em `regras_classificacao.yaml`, com a norma de origem e a data de vigência de cada versão dos limites:

- `v1`: Prov. 213 original, R$ 100.000,00 semestrais;
- `v2`: Prov. 243, R$ 300.000,00 semestrais, em vigor desde 22/08/2026.

A base é `v2` e a sensibilidade é `v1`. As atualizações anuais (§2º do art. 16) entram como novas versões.

## 3. Modelo de mercado (`src/model`)

Funções puras, sem I/O, cada uma com teste. Todas recebem as premissas de forma explícita. Ordem de aplicação: passivo por município → rateio sobre **todas** as serventias → universo (exclusões) → déficit → demanda → receita.

1. **`passivo_por_vinculo(salario, meses_servico, premissas)`**
   Calcula o custo de demissão sem justa causa conforme o art. 5º do Prov. 227, somando:
   - aviso prévio indenizado proporcional: 30 dias + 3 por ano completo, com teto de 90 (Lei 12.506/2011);
   - 13º proporcional, **incluindo a projeção do aviso prévio**;
   - férias vencidas e proporcionais + 1/3, **incluindo a projeção do aviso prévio**;
   - multa de 40% sobre o saldo estimado de FGTS (8% × remuneração × meses, com premissa de correção);
   - verbas de convenção coletiva: `acrescimo_cct_pct` × subtotal (padrão 0);
   - encargos do empregador (INSS patronal, RAT × FAP, FGTS mensal) conforme `aliquotas_encargos`;
   - saldo de salário só se `incluir_saldo_salario` for verdadeiro (padrão: não).

   O salário de entrada é a base do art. 6º, aproximada por `base_remuneracao_rais` (padrão: remuneração de dezembro) e corrigida por `correcao_salarial_rais`. Os parâmetros legais ficam em config.
2. **`passivo_municipio(rais_distribuicao, premissas)`**
   Aplica a função anterior a **cada célula** (faixa salarial × faixa de tempo) e depois agrega. Nunca usar média de salário ou de tempo como entrada, porque o passivo não é linear no tempo de serviço.
3. **`ratear_passivo(passivo_municipio, serventias, metodo)`**
   Rateia o passivo entre **todas as serventias do município**, inclusive interinos e Classe 1, porque a RAIS conta os empregados delas também. `metodo ∈ {por_empregados_cnj, arrecadacao, uniforme, peso_por_atribuicao}`. O padrão é **`por_empregados_cnj`** (D-005): passivo da serventia = colaboradores CLT declarados no Justiça Aberta × passivo médio por vínculo da distribuição RAIS do município (ou do estado, abaixo do limiar de vínculos, D-008). Os demais métodos são sensibilidade, e o painel mostra o efeito da escolha.
4. **`universo(serventias_com_passivo, regras_classificacao, data_ref)`**
   Remove, **depois do rateio**, os interinos e as serventias da Classe 1, conforme a versão da regra vigente em `data_ref` ou a versão escolhida explicitamente. Retorna também os excluídos, o motivo e a marca `classificacao_aproximada`, porque a arrecadação das fontes públicas aproxima, mas não é igual, a receita bruta do art. 2º, XXIV do 213.
   O pipeline calcula **as duas versões** (`v2` base e `v1` sensibilidade) e registra a diferença de universo (nº de serventias e passivo) e de mercado (IS e prêmio). Essa diferença aparece no diário e na página Qualidade dos dados.
   Se a arrecadação vier em faixa, a classificação pode ficar **indeterminada** quando a faixa cruza o limite:
   - no `min`, a indeterminada fica **fora**;
   - no `max`, fica **dentro**;
   - no `base`, entra com o peso `peso_classe_indeterminada_base`.
5. **`deficit(passivo_serventia, premissas)`**
   Usa `prob_deficit` (chance de ter déficit) e `pct_descoberto` (fração do passivo descoberta). Retorna um intervalo (min/base/max) do valor descoberto e do número de serventias com déficit. O painel sempre mostra a faixa, nunca um ponto único.
6. **`demanda_seguro(deficit, premissas)`**
   Aplica `escolha_garantia`: bens próprios, fiança ou seguro, somando 100%. A importância segurada (IS) é a parcela que escolhe seguro.
7. **`receita(demanda, premissas)`**
   Receita anual e recorrente, com quatro saídas, cada uma para o **mercado total** e para a **seguradora hipotética**:
   - importância segurada;
   - prêmio emitido = IS × taxa (× market share na visão da seguradora);
   - sinistro esperado = prêmio × sinistralidade;
   - resultado técnico = prêmio − sinistro − comissão − despesa administrativa.
8. **`aplicar_cenario_stf(premissas, cenario)`**
   - `mantem`: regra integral.
   - `suspende_8_17`: uma liminar suspende os arts. 8º a 17, a obrigação de garantia cai e a demanda tende a zero (a declaração de passivo continua).
   - `parcial`: parâmetros configuráveis.

   Cada cenário é um diff sobre as premissas, definido em `cenarios_stf.yaml`.

**Testes mínimos**:

- sem vínculos, o passivo é zero;
- o aviso prévio respeita o teto de 90 dias;
- o universo nunca contém interino;
- trocar a versão da regra de classe muda o universo;
- a soma rateada é igual ao passivo do município (no `por_empregados_cnj`, igual a CLT declarados × passivo por vínculo);
- a classe indeterminada fica fora no `min` e dentro no `max`;
- as três parcelas de `escolha_garantia` somam 1, e a validação falha se não somarem;
- o cenário `suspende_8_17` zera a demanda de garantia;
- o prêmio emitido é monotônico na taxa;
- o mercado total é sempre maior ou igual à visão da seguradora hipotética.

## 4. Qualidade de dados (prioridade do projeto)

Cada tabela silver e gold tem um contrato com:

- chaves únicas e campos não nulos;
- domínios válidos (UF existente, código IBGE com 7 dígitos);
- faixas plausíveis de valores;
- ausência de nome e CPF de titular nas tabelas silver e gold;
- **checagens de reconciliação entre fontes**:
    - total de serventias por UF: painel do CNJ × CNPJ da Receita × "Cartório em Números", com tolerância configurável;
    - serventias presentes numa fonte e ausentes na outra, listadas para revisão;
    - total de vínculos RAIS do CNAE × total de empregados do "Cartório em Números" (detecta vínculos no CPF/CEI do titular e alimenta `fator_cobertura_rais`);
    - cobertura do Justiça Aberta (% de serventias com arrecadação preenchida).

O pipeline **falha** quando há violação de chave ou tipo e **avisa** quando há divergência entre fontes. As divergências aparecem numa página **"Qualidade dos dados"** do painel e no diário. Mostrar ao usuário o quanto os dados são confiáveis faz parte do produto.

## 5. Painel e chat

### 5.1 Painel (Streamlit)

Páginas:

1. **Mercado**: mapa e ranking por UF; filtros por UF, município, atribuição e situação (titular/interino/Classe 1); total de serventias, empregados, passivo estimado e déficit (em faixa).
2. **Simulador**: controles para cada premissa, seletor de cenário do STF, receita do mercado total e da seguradora hipotética lado a lado, por UF; botão para salvar o cenário.
3. **Qualidade dos dados**: data de referência de cada fonte, cobertura e divergências entre fontes.
4. **Chat**.
5. **Radar** (só se for feito).

### 5.2 Chat (`src/agent`)

O LLM local **não calcula números**. Ele entende a pergunta, chama as ferramentas da camada semântica e explica o resultado. É isso que permite usar um modelo gratuito e menos capaz sem perder a precisão.

Ferramentas:

- `contar_serventias(uf?, municipio?, atribuicao?, classe?, situacao?)`
- `estimar_passivo(uf?, municipio?, versao_premissas?)`
- `estimar_deficit(uf?, cenario?, versao_premissas?)`
- `simular(ajustes_premissas, cenario)`
- `buscar_normas(pergunta)`: devolve trechos com norma, artigo e data
- `consultar_qualidade(fonte?)`: data de referência e cobertura das fontes
- `consultar_decisoes(tema)`: lê o log de decisões
- `sql_readonly(query)`: só como fallback, com allowlist de views já agregadas (§6), LIMIT 1000 e timeout

Regras do prompt do chat:

- **Nenhum número sem chamada de ferramenta.** Toda resposta numérica mostra a conta, a fonte, a data de referência e a versão das premissas.
- **Estimativas em faixa** sempre que a premissa for uma faixa.
- **"Não sei"** quando a informação não estiver na base. Nunca completar com conhecimento geral sobre números do setor.
- **Perguntas jurídicas** (ex.: "fiança substitui o seguro?"): responder citando o texto da norma e deixar claro que não é parecer jurídico.

As normas (227, 213, 243) são poucas e curtas. Primeiro, testar colocar o texto inteiro do artigo relevante no prompt. RAG com embeddings locais (também pelo Ollama) só entra se o eval mostrar ganho.

### 5.3 Radar (`src/radar`): opcional

Feito só depois de o painel e o chat estarem prontos.

- **Lista de monitoramento, por prioridade:**
  1. **normas estaduais** que regulamentam o 227 (ex.: Provimento COGEX/TJBA 18/2026, citado pela Arpen-BA; norma da CGJ/RS de 27/08/2026, a confirmar na fonte oficial);
  2. andamento da ADI 8015;
  3. **atualização anual dos limites de classe** divulgada pela Corregedoria Nacional (art. 16, §2º, do 213);
  4. novas alterações dos Provimentos 213, 227 e 243.
- **Versão simples (sem IA):** coletores do CNJ, das corregedorias estaduais, das associações e do andamento da ADI 8015; filtro por palavras-chave e pela lista de normas monitoradas; deduplicação por hash de URL e texto e por chave de evento (norma + tipo + data de publicação do ato original); lista de eventos na página Radar com link e trecho.
- **Versão com IA (se sobrar tempo):** o LLM local classifica o evento pela taxonomia abaixo e extrai os campos, com citação obrigatória verificada como substring do texto normalizado. Sugere uma mudança de cenário com status `proposto`, que o autor aprova ou rejeita na página Radar.
- O radar **nunca aplica nada sozinho**. O texto coletado é dado, nunca instrução (isolado no prompt, saída validada por schema).

Taxonomia de `tipo_evento` (aprovada em 2026-10-17): `norma_nova`, `norma_alteracao`, `norma_revogacao`, `prazo_vigencia`, `regulamentacao_estadual`, `decisao_judicial`, `andamento_processual`, `proposicao_legislativa`, `comunicado_setorial`.

## 6. LGPD e ética

- Nome e CPF de titulares são **descartados na passagem bronze → silver** e não aparecem no silver, no gold, no painel nem nas respostas do chat. O bronze fica fora do git.
- Estimativas de déficit nunca saem em nível de serventia identificável. O menor nível exibido é o município, e municípios com **menos de 3 serventias** (`limiar_agregacao_lgpd`) entram agregados.
- O README declara que os números são estimativas de mercado com premissas públicas, e não avaliação de nenhum cartório, e que o market share é de uma seguradora hipotética.

## 7. Avaliação (`src/eval`)

### 7.1 Gabarito do chat (prioridade)

- 40 a 60 perguntas de 4 tipos: números, normas, simulação e armadilhas (que devem receber "não sei" ou recusa). Cada uma com resposta esperada e fonte esperada.
- As respostas numéricas são conferidas contra consultas SQL diretas no banco, e o gabarito fixa a versão das premissas.
- O gabarito é rotulado pelo autor **antes** de ajustar o prompt e é congelado com hash e data. Mudanças viram nova versão, com justificativa no diário.

### 7.2 Métricas do chat

- % de respostas corretas;
- % de alucinações (número ou norma inexistente);
- % de respostas sem fonte;
- % de "não sei" corretos e incorretos;
- latência por pergunta (o custo é zero, e isso aparece nos slides).

**Comparação de versões** (o gráfico principal): (a) LLM local sem ferramentas, (b) com o texto das normas no prompt, (c) com ferramentas. RAG entra como (d) só se for feito.

### 7.3 Radar (só se houver)

Gabarito de 40 a 60 documentos reais, com pelo menos 10 relevantes. Métricas: precisão e recall da relevância, alarmes falsos, duplicatas não detectadas.

**Limitação declarada**: os gabaritos são rotulados por uma pessoa só, então o intervalo de confiança é largo.

## 8. Fases e critérios de aceite

### Fase 0: Viabilidade (1 a 2 dias)

- Instalar o `uv` e o Python 3.12 por meio dele, sem alterar o Python do sistema.
- Verificar a RAM e a GPU do computador e **propor o modelo do Ollama** (o autor instala o Ollama se ainda não tiver). Testar se o modelo faz *tool calling* com uma ferramenta de exemplo.
- Baixar os Provimentos 227, 213 e 243 em atos.cnj.jus.br e confirmar: os arts. 8º a 17, a definição de passivo, o prazo do primeiro ano, os critérios da Classe I e quem é o segurado da garantia.
- Conferir o andamento da ADI 8015.
- Testar cada fonte do §1.1 e registrar formato, campos, cobertura, data de referência e se há download em massa. Em especial:
  - se o painel do CNJ está acessível e quais campos exporta (titular/interino, arrecadação, empregados);
  - o tamanho do download da RAIS de MG no PDET e se o filtro pelo CNAE funciona;
  - o download do CNPJ da Receita e quantos estabelecimentos com o CNAE 6912-5/00 existem por UF.
- Comparar os totais entre as fontes (serventias e empregados) e com o "Cartório em Números".
- **Aceite**: `docs/viabilidade.md` com uma linha por fonte (ok / parcial / bloqueada + plano B), a fonte escolhida para o universo e o modelo do Ollama escolhido. Nenhuma fonte usada pode exigir pagamento ou cadastro.

### Fase 1: Painel de MG

- Ingestão, silver e gold só para MG.
- Modelo completo (§3), com testes.
- Páginas Mercado, Simulador e Qualidade dos dados para MG.
- **Aceite**: `uv run pipeline.py` gera tudo a partir dos snapshots do bronze, os testes passam e todo número na tela tem fonte, data de referência e versão.

### Fase 2: Brasil inteiro e qualidade

- Expandir para todas as UFs disponíveis, com contratos e reconciliações (§4).
- **Aceite**: página Qualidade dos dados completa e divergências documentadas no diário.

### Fase 3: Chat

- Ordem: gabarito (rotulado pelo autor) → ferramentas → integração com o Ollama → página Chat → eval das versões.
- **Aceite**: o chat responde o gabarito com as métricas do §7.2 e o gráfico de comparação das versões.

### Fase 4: Radar (opcional)

- Primeiro a versão simples sem IA. A versão com IA só se sobrar tempo.
- **Aceite**: um evento real aparece na página Radar com link e trecho.

### Fase 5: Entrega

- README com o problema, a arquitetura em diagrama, como rodar, os resultados do eval, as limitações e a frase "custo zero: tudo roda localmente com dados públicos".
- Medida de antes e depois: tempo da tarefa manual (linha de base no diário) vs. com o sistema.
- Slides (5): problema, arquitetura, demo, onde a IA errou e o que mudou, resultados com o gráfico das versões.
- Demo: painel de MG, simulador mudando de cenário do STF e o chat respondendo com a fonte.
- **Robustez da demo**: o app roda sem internet (dados já no banco local e Ollama local). Gravar um vídeo de backup.
- Na véspera: conferir o andamento da ADI 8015.

**Se o tempo apertar, cortar nesta ordem**:

1. o radar inteiro (Fase 4);
2. o RAG;
3. o Monte Carlo;
4. a expansão para o Brasil inteiro (fica MG e as UFs que já estiverem prontas).

**Nunca cortar**: a Fase 0, os testes do modelo, a página Qualidade dos dados, o eval do chat, o mínimo da demo (§0) e o diário de erros.

## 9. Como a IA deve trabalhar neste projeto

- **Ritmo**: fase por fase, parando ao fim de cada uma para revisão do autor.
- **Coletores**: antes de escrever um, inspecionar uma amostra real da fonte e mostrar os campos encontrados.
- **Nada inventado**: nunca inventar valores de premissa, URLs, números de normas ou dados apresentados como reais.
- **Nada pago**: nunca sugerir, instalar ou configurar serviço pago, conta em nuvem ou chave de API com créditos.
- **Diário**: registrar em `docs/diario.md` toda limitação, suposição e decisão, com data.
- **Falhas de fonte**: quando uma fonte falhar, propor o plano B em vez de contornar em silêncio.
- **Regulação atual**: no início do trabalho, conferir o status da ADI 8015 e se houve novas alterações nos Provimentos 213 e 227.

## 10. Riscos conhecidos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Painel do CNJ indisponível ou incompleto após a migração do Justiça Aberta | Sem universo confiável | Plano B: CNPJ da Receita + listagens dos TJs + painel de vacâncias; download manual pelo autor se preciso |
| RAIS não capta vínculos registrados no CPF/CEI do titular | Passivo subestimado | Comparar com o "Cartório em Números" na Fase 0 e usar `fator_cobertura_rais` |
| Arquivos da RAIS e do CNPJ são grandes | Download lento e falta de espaço em disco | Baixar só as UFs em uso, filtrar na leitura e guardar só o filtrado |
| Computador sem RAM suficiente para um bom modelo local | Chat lento ou ruim | Modelo menor; o chat depende das ferramentas para os números, não da força do modelo |
| Modelo local erra a escolha da ferramenta | Respostas erradas | Ferramentas com nomes e descrições claros, poucos parâmetros, e o eval medindo isso |
| Passivo concentrado em cartórios grandes | O rateio uniforme distorce o déficit | Rateio por arrecadação como padrão candidato e sensibilidade no painel |
| **Segurado indefinido**: o art. 13 do 227 não diz quem é o beneficiário da garantia; o tomador é pessoa física (o delegatário) | Taxa e sinistralidade sem referência direta; o desenho do produto pode mudar por norma estadual | Premissa (`fonte: suposição`), limitação no README e prioridade no radar para normas estaduais que definam o beneficiário |
| Classificação da Classe 1 aproximada (arrecadação pública ≠ receita bruta do art. 2º, XXIV) | Universo errado perto do limite | Marca `classificacao_aproximada`, classe indeterminada (§3.4) e sensibilidade `v1` × `v2` |
| Base do art. 6º (maior remuneração fixa) não existe na RAIS | Passivo subestimado ou superestimado | `base_remuneracao_rais` (dezembro × média anual) e sensibilidade no painel |
| Limites de classe mudam todo ano (art. 16, §2º, do 213) | Universo desatualizado | Nova versão em `regras_classificacao.yaml`; monitorado pelo radar |
| Concorrência com regularização por bens próprios e com fiança | Demanda superestimada | Premissa `escolha_garantia` |
| Liminar na ADI 8015 perto da entrevista | Muda a narrativa da demo | Cenário `suspende_8_17` pronto; conferir na véspera |
| Projeto dentro do OneDrive (decisão do autor) | Sincronização pode travar `.venv` e DuckDB | Se ocorrer, mover o `.venv` para fora com `UV_PROJECT_ENVIRONMENT` e registrar no diário |
| Corte de conhecimento da IA anterior às normas | A IA pode inventar artigos | Confirmar todo artigo no texto oficial; registrar erros em `erros_ia.md` |
