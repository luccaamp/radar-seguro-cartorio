# Radar Seguro-Garantia Cartórios: Especificação do Projeto

> Documento para entregar a uma IA de código (ex.: Claude Code) como briefing do projeto.
> Leia tudo antes de escrever código. Siga as fases em ordem e não pule os critérios de aceite.
> Última revisão: 2026-10-17 (decisões registradas no `docs/diario.md`).

## 0. Contexto e objetivo

**Problema de negócio.** O Provimento CNJ 227/2026 foi publicado em 11/06/2026 e está em vigor desde 10/08/2026. Ele obriga os delegatários de cartórios a:

- declarar o passivo trabalhista. No primeiro ano, a declaração vence 30 dias após a vigência (por volta de 09/09/2026). Depois o ciclo é anual, com base em 31/12 e entrega até 31/03;
- demonstrar solvência com bens livres de ônus.

Se houver déficit de cobertura, o delegatário tem 60 dias para regularizar ou apresentar **fiança bancária ou seguro-garantia** no valor descoberto.

**Definição de passivo.** O passivo é o custo de demitir todos os empregados sem justa causa. É exatamente esse ponto que a ANOREG critica na ADI. *A confirmar no texto da norma na Fase 0.*

**Natureza do mercado.** O mercado já existe, porque o primeiro ciclo já venceu, e se renova todo ano. Por isso a receita é tratada como **anual e recorrente** (renovação da garantia).

Ficam fora da norma:

- as serventias da **Classe I do Provimento 213/2026**, alterado pelo Provimento 243/2026 (jul/2026);
- as serventias **sob interinidade**.

A ANOREG/BR ajuizou a **ADI 8015** contra os **arts. 8º a 17**, que são justamente os que criam a exigência de garantia. O relator é o Min. Flávio Dino, e a ação foi distribuída em setembro de 2026.

> Os fatos acima foram verificados pelo autor em 2026-10-17. A IA tem corte de conhecimento anterior a eles e **deve confirmar os artigos no texto oficial** (atos.cnj.jus.br) na Fase 0, antes de usá-los em premissas, testes ou no chat.

**Objetivo do projeto.** Três coisas, todas só com dados públicos:

- estimar o tamanho do mercado potencial de seguro-garantia criado por essa norma;
- acompanhar a evolução regulatória automaticamente;
- responder perguntas em linguagem natural, com respostas rastreáveis.

**Uso final.** Projeto de portfólio para entrevista: 5 minutos, 5 slides e demo ao vivo. Isso define as prioridades: **uma fatia vertical funcionando de ponta a ponta vale mais que cinco módulos pela metade.**

**Mínimo da demo**, que não pode faltar:

1. páginas Mercado e Simulador funcionando para MG;
2. o radar detectando um evento real;
3. a aprovação desse evento mudando o simulador.

O chat é **bônus**.

**Restrições inegociáveis.**

1. Só dados públicos. Nenhuma precificação interna de qualquer seguradora. O market share é de uma **seguradora hipotética** (`fonte: suposição`).
2. Nenhum número fixo no código. Toda premissa é versionada e tem fonte.
3. Nenhum dado pessoal exposto em nível individual (ver §6, LGPD).
4. Todo número mostrado ao usuário carrega a fonte, a data de referência e a versão das premissas.

## 1. Fontes de dados

### 1.1 Mapa de fontes

| Entidade | Fonte primária | Reconciliação / fallback | Granularidade | Risco |
|---|---|---|---|---|
| Universo de serventias (CNS, UF, município, atribuição, titular/interino) | Justiça Aberta (nova plataforma, justicaaberta.cnj.jus.br) | Listagens das corregedorias estaduais (TJs); CNPJ da Receita (CNAE 6912-5/00) via dados abertos ou Base dos Dados; relatório "Cartório em Números" (ANOREG) para totais de controle | Serventia | **Alto**: formato, cobertura e download incertos |
| Arrecadação | Justiça Aberta (declarada **por faixa**) | Editais de concurso e sorteio dos TJs que trazem a classe da serventia; totais agregados das associações | Serventia (faixa) | **Alto** |
| Vínculos, salários e tempo de emprego | Microdados da RAIS (Base dos Dados / BigQuery), CNAE 6912-5/00 | Novo CAGED para a tendência recente; "Cartório em Números" para o total de empregados | Município × faixas | **Alto**: defasagem de 1 a 2 anos, não identifica a serventia e pode **não captar vínculos registrados no CPF/CEI do titular** (ver §10) |
| Contexto | IBGE (população, PIB municipal) | — | Município | Baixo |
| Seguro-garantia | SUSEP SES (prêmios e sinistros dos ramos de garantia) | Publicações setoriais com faixas de taxa | Ramo/seguradora/mês | Médio: **não traz importância segurada**, então serve para sinistralidade, não para taxa. É um proxy fraco para este risco específico |
| Normas | atos.cnj.jus.br (Provimentos 227, 213, 243 e posteriores); STF (ADI 8015); DJe | Sites das associações (ANOREG, Arpen, IRTDPJ, IRIB, CNB) | Documento/artigo | Médio: o portal do STF costuma bloquear scraping |
| Proposições legislativas | APIs de dados abertos da Câmara e do Senado | — | Proposição | Baixo |

### 1.2 Regras para as fontes

- Toda coleta grava o **bruto imutável** em `data/bronze/<fonte>/<data_coleta>/`, com metadados: URL, data, hash e versão do coletor.
- Respeitar o robots.txt e os termos de uso, com intervalo entre requisições e User-Agent identificável.
- Quando uma fonte não puder ser coletada automaticamente, **aceitar upload manual** do arquivo e registrar a origem. Isso é melhor que um scraper frágil.
- Se o CNS não estiver disponível em alguma fonte, a junção usa UF, município (normalizado pelo código IBGE), atribuição e nome normalizado, com **score de match** e revisão manual dos casos ambíguos. Registrar a taxa de match.
- **Períodos de referência**: usar o dado mais recente de cada fonte. A `data_referencia` de cada fonte é registrada e **exibida no dashboard**, e as fontes não são forçadas a um período comum. A defasagem salarial da RAIS é corrigida por uma premissa (`correcao_salarial_rais`).
- **BigQuery**: usar só a cota gratuita. Toda consulta filtra por CNAE e ano e define `maximum_bytes_billed`, com o limite lido de config. Nenhuma consulta sem filtro nos microdados.

## 2. Arquitetura

### 2.1 Camadas

- **Bronze**: o bruto como veio, particionado por data de coleta.
- **Silver**: dados limpos e tipados, com chaves normalizadas (código IBGE do município, CNS) e uma tabela por entidade. **Nome e CPF de titular são descartados aqui** (ver §6).
- **Gold**: tabelas de negócio e métricas, como `fato_mercado_uf`, `fato_passivo_municipio` e `dim_serventia`.
- **Estado operacional**: fica fora do pipeline analítico, em banco persistente (MotherDuck). Inclui `eventos_radar`, `aprovacoes`, `premissas_versoes`, `cenarios_salvos` e `log_decisoes`.

### 2.2 Stack

| Função | Escolha | Observação |
|---|---|---|
| Linguagem | Python 3.12 | gerenciar com `uv` |
| Processamento analítico | DuckDB + Parquet | gold publicado em Parquet |
| Transformações | SQL em arquivos versionados (dbt-duckdb **opcional**) | com dbt, os testes de schema vêm de graça |
| Estado persistente | **MotherDuck (free)** | decidido em 2026-10-17. Runners do GitHub Actions e o disco do Streamlit Cloud são efêmeros |
| Local do gold no deploy | **MotherDuck**, no mesmo banco do estado | decidido em 2026-10-17. O Parquet local continua como saída do pipeline e é carregado no MotherDuck |
| Orquestração | um script único, `uv run pipeline.py` | substitui o `make`, que não vem instalado no Windows |
| Validação de dados | Pandera ou testes SQL simples | contratos por tabela |
| Saída estruturada do LLM | Pydantic | schema com campo de citação obrigatório |
| LLM | Claude API com tool use | registrar modelo, versão do prompt e custo por chamada |
| Interface | Streamlit | lê o gold e o estado persistente |
| Agendamento | GitHub Actions (cron) | grava no armazenamento persistente, nunca no runner |
| Testes | pytest | testes de unidade nas funções de cálculo |

### 2.3 Estrutura de pastas

```
radar-seguro-cartorio/
├── pipeline.py                # orquestrador único: uv run pipeline.py [etapa]
├── data/
│   ├── bronze/                # bruto imutável (git-ignored; amostras pequenas em data/samples/)
│   ├── silver/
│   └── gold/
├── config/
│   ├── premissas/             # semente versionada: premissas_v001.yaml ...
│   ├── regras_classificacao.yaml  # limites de Classe por norma e vigência
│   └── cenarios_stf.yaml      # definições fixas dos cenários do STF
├── src/
│   ├── ingest/                # um coletor por fonte, todos idempotentes
│   ├── transform/             # bronze→silver→gold
│   ├── quality/               # contratos e checagens
│   ├── model/                 # funções puras de cálculo
│   ├── radar/
│   ├── agent/
│   │   └── tools/             # camada semântica
│   └── eval/
├── app/                       # Streamlit
├── tests/
├── eval/
│   ├── gabarito_radar.csv
│   └── gabarito_chat.csv
├── docs/
│   ├── diario.md              # decisões e limitações, com data
│   ├── erros_ia.md
│   └── dicionario_dados.md
└── README.md
```

**"Do zero"** significa rodar o pipeline **a partir dos snapshots do bronze**, sem coletar de novo.

### 2.4 Premissas versionadas

- **Semente**: o YAML em `config/premissas/` é a versão inicial, versionada no git.
- **Versões aprovadas**: vivem no banco, na tabela `premissas_versoes`. Cada versão guarda o número, o diff sobre a anterior, o autor, a data e o evento do radar que a originou. O app e o pipeline leem a versão vigente do banco e caem para a semente se o banco estiver vazio.
- **Cenários**: `cenarios_stf.yaml` tem as definições fixas dos cenários (`mantem`, `suspende_8_17`, `parcial`). `cenarios_salvos` (no banco) guarda as combinações de ajustes que o usuário salva no simulador.

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

Os números acima são **placeholders**. A IA não deve inventar valores. Onde não houver fonte, marcar `fonte: suposição` e pedir validação humana.

Premissas previstas, além dos parâmetros legais do passivo:

- `prob_deficit` e `pct_descoberto`, por faixa;
- `escolha_garantia`, com três parcelas que somam 1 (regulariza com bens próprios, fiança, seguro);
- `taxa_seguro_anual`;
- `market_share_hipotetico` (`fonte: suposição`);
- `sinistralidade`;
- `comissao`;
- `despesa_administrativa`;
- `correcao_salarial_rais`;
- `peso_classe_indeterminada_base`;
- `metodo_rateio_padrao`;
- `limiar_agregacao_lgpd`, com valor 3;
- desenho do produto: quem é o tomador (o delegatário, pessoa física) e quem é o segurado (a confirmar). Ver §10.

A definição de Classe I também é premissa. Ela fica em `regras_classificacao.yaml`, com a norma de origem e a data de vigência de cada versão dos limites.

## 3. Modelo de mercado (`src/model`)

Funções puras, sem I/O, cada uma com teste. Todas recebem as premissas de forma explícita. Ordem de aplicação: passivo por município → rateio sobre **todas** as serventias → universo (exclusões) → déficit → demanda → receita.

1. **`passivo_por_vinculo(salario, meses_servico, premissas)`**
   Calcula o custo de demissão sem justa causa somando os itens abaixo:
   - saldo de salário (opcional);
   - aviso prévio proporcional: 30 dias + 3 por ano completo, com teto de 90 (Lei 12.506/2011);
   - 13º proporcional;
   - férias vencidas e proporcionais + 1/3;
   - multa de 40% sobre o saldo estimado de FGTS (8% × remuneração × meses, com premissa de correção);
   - encargos.

   Os parâmetros legais ficam em config. O salário da RAIS é corrigido por `correcao_salarial_rais`.
2. **`passivo_municipio(rais_distribuicao, premissas)`**
   Aplica a função anterior a **cada célula** (faixa salarial × faixa de tempo) e depois agrega. Nunca usar média de salário ou de tempo como entrada, porque o passivo não é linear no tempo de serviço.
3. **`ratear_passivo(passivo_municipio, serventias, metodo)`**
   Rateia o passivo entre **todas as serventias do município**, inclusive interinos e Classe I, porque a RAIS conta os empregados delas também. `metodo ∈ {arrecadacao_ponto_medio_faixa, uniforme, peso_por_atribuicao}`. O padrão é definido em premissa, e o dashboard mostra a sensibilidade a essa escolha.
4. **`universo(serventias_com_passivo, regras_classificacao, data_ref)`**
   Remove, **depois do rateio**, os interinos e as serventias da Classe I, conforme a versão da regra vigente em `data_ref`. Também retorna os excluídos e o motivo, para auditoria.
   Como a arrecadação vem em faixa, a classificação pode ficar **indeterminada** quando a faixa cruza o limite. Ela é tratada como categoria própria e aparece no dashboard:
   - no `min`, a indeterminada fica **fora**;
   - no `max`, fica **dentro**;
   - no `base`, entra com o peso `peso_classe_indeterminada_base`.
5. **`deficit(passivo_serventia, premissas)`**
   Usa duas premissas separadas:
   - `prob_deficit`: a chance de uma serventia ter déficit;
   - `pct_descoberto`: a fração do passivo descoberta quando há déficit.

   Retorna um intervalo (min/base/max) do valor descoberto e do número de serventias com déficit. É a variável mais incerta do modelo, por isso o dashboard sempre mostra a faixa e nunca um ponto único. Se der tempo, fazer um Monte Carlo simples.
6. **`demanda_seguro(deficit, premissas)`**
   Aplica `escolha_garantia`, uma premissa única com três parcelas que somam 100%: regulariza com bens próprios, fiança ou seguro. A importância segurada (IS) é a parcela que escolhe seguro.
7. **`receita(demanda, premissas)`**
   Receita anual e recorrente. Retorna **quatro saídas separadas**, cada uma para o **mercado total** e para a **seguradora hipotética** (× `market_share_hipotetico`):
   - importância segurada;
   - prêmio emitido = IS × taxa (× market share na visão da seguradora);
   - sinistro esperado = prêmio × sinistralidade;
   - resultado técnico = prêmio − sinistro − comissão − despesa administrativa.

   Não há fator de "adesão" aqui, porque a escolha já foi aplicada em `demanda_seguro`.
8. **`aplicar_cenario_stf(premissas, cenario)`**
   - `mantem`: regra integral.
   - `suspende_8_17`: uma liminar suspende os arts. 8º a 17, a obrigação de garantia cai e a demanda tende a zero (a declaração de passivo continua).
   - `parcial`: parâmetros configuráveis, por exemplo só alguns artigos ou um prazo maior.

   Cada cenário é um diff sobre as premissas, definido em `cenarios_stf.yaml`, e não um YAML inteiro copiado.

**Testes mínimos**:

- sem vínculos, o passivo é zero;
- o aviso prévio respeita o teto de 90 dias;
- o universo nunca contém interino;
- trocar a versão da regra de classe muda o universo;
- o rateio usa todas as serventias do município, e a exclusão vem depois (a soma rateada é igual ao passivo do município);
- a classe indeterminada fica fora no `min` e dentro no `max`;
- as três parcelas de `escolha_garantia` somam 1, e a validação falha se não somarem;
- o cenário `suspende_8_17` zera a demanda de garantia;
- o **prêmio emitido** é monotônico na taxa;
- o mercado total é sempre maior ou igual à visão da seguradora hipotética.

## 4. Qualidade de dados

Cada tabela silver e gold tem um contrato com:

- chaves únicas e campos não nulos;
- domínios válidos (UF existente, código IBGE com 7 dígitos);
- faixas plausíveis de valores;
- ausência de nome e CPF de titular nas tabelas silver e gold;
- **checagens de reconciliação**:
    - total de serventias por UF comparado ao total de controle de outra fonte, com tolerância configurável. Uma divergência gera alerta no diário, nunca falha silenciosa;
    - total de vínculos RAIS do CNAE comparado à soma por município;
    - total de vínculos RAIS do CNAE comparado ao total de empregados do "Cartório em Números", para detectar vínculos registrados no CPF/CEI do titular;
    - cobertura do Justiça Aberta (% de serventias com faixa de arrecadação preenchida), exibida no dashboard.

O pipeline **falha** quando há violação de chave ou tipo e **avisa** quando há violação de reconciliação.

## 5. Agentes

### 5.1 Radar regulatório (`src/radar`)

**Montar o gabarito (§7) antes de escrever o prompt.**

**Taxonomia de `tipo_evento`** (aprovada em 2026-10-17; mudanças exigem nova aprovação e registro no diário):

| tipo_evento | Exemplo |
|---|---|
| `norma_nova` | novo provimento do CNJ sobre o tema |
| `norma_alteracao` | provimento que altera o 227 ou o 213 (como o 243) |
| `norma_revogacao` | revogação total ou parcial |
| `prazo_vigencia` | prorrogação de prazo ou adiamento de vigência |
| `regulamentacao_estadual` | provimento ou ato de corregedoria de TJ que regulamenta a norma |
| `decisao_judicial` | liminar, referendo ou mérito na ADI 8015 ou em outra ação |
| `andamento_processual` | distribuição, pauta, parecer da PGR, pedido de vista, ingresso de amicus |
| `proposicao_legislativa` | projeto de lei ou PDL sobre o tema |
| `comunicado_setorial` | nota ou orientação de associação, sem força normativa |

Pipeline:

1. **Coleta.** Um coletor por fonte: atos do CNJ, DJe, associações, APIs da Câmara e do Senado, andamento da ADI 8015. Cada item guarda URL, data de publicação, data de coleta, texto e hash.
2. **Filtro barato.** Palavras-chave e lista de normas monitoradas (227, 213, 243, ADI 8015 e as que vierem depois).
3. **Classificação.** O LLM classifica a relevância, com saída Pydantic e justificativa curta.
4. **Extração.** O LLM extrai `tipo_evento`, `norma`, `artigos`, `uf`, `vigencia`, `efeito_demanda` (aumenta / reduz / neutro / incerto) e `trecho_citado`.
   - A citação é obrigatória e é verificada como substring do texto de origem. Se não bater, o evento é rejeitado.
   - Antes da comparação, os dois textos são **normalizados**: Unicode NFKC, espaços colapsados, hifenização de quebra de linha removida e aspas e travessões unificados. A regra de normalização é versionada e testada.
5. **Deduplicação em dois níveis.** Primeiro hash de URL e texto. Depois uma **chave de evento** (norma + tipo + **data de publicação do ato original**, e não da notícia), porque a mesma notícia sai em várias associações com textos diferentes.
6. **Sugestão.** Uma mudança de premissa ou cenário é gravada com status `proposto`. **O radar nunca aplica nada sozinho.**
7. **Aprovação humana.** Feita no app, grava em `aprovacoes` com autor e data e gera uma nova versão em `premissas_versoes`.
8. **Resumo diário.** Em markdown, com links e trechos citados, enviado por e-mail ou Slack (canal a decidir).

**Segurança contra prompt injection**: o texto coletado é dado, nunca instrução.

- No prompt, ele vai isolado dentro de delimitadores, com uma instrução explícita para ignorar comandos contidos nele.
- A saída é validada pelo schema Pydantic, com domínios fechados para `tipo_evento` e `efeito_demanda`, e pela checagem de citação.
- O radar não tem nenhuma ferramenta com efeito colateral.

**Fallback do STF**: se o portal bloquear a coleta, monitorar a cobertura da ADI nas associações e notícias e marcar o status como "não verificado na fonte primária".

### 5.2 Agente de dúvidas (`src/agent`): bônus da demo

Ferramentas da camada semântica:

- `contar_serventias(uf?, municipio?, atribuicao?, classe?, situacao?)`
- `estimar_passivo(uf?, municipio?, versao_premissas?)`
- `estimar_deficit(uf?, cenario?, versao_premissas?)`
- `simular(ajustes_premissas, cenario)`
- `buscar_normas(pergunta)`: devolve trechos com norma, artigo e data
- `listar_eventos(filtro)`
- `consultar_decisoes(tema)`: lê o log de decisões do time
- `sql_readonly(query)`: só como fallback, com allowlist de views, LIMIT 1000 e timeout. As views da allowlist já aplicam a agregação da LGPD (§6)

Regras do system prompt:

- **Nenhum número sem chamada de ferramenta.** Toda resposta numérica mostra a conta, a fonte, a data de referência e a versão das premissas.
- **Estimativas em faixa** sempre que a premissa for uma faixa.
- **"Não sei"** quando a informação não estiver na base. Nunca completar com conhecimento geral sobre números do setor.
- **Perguntas jurídicas** (ex.: "fiança substitui o seguro?"): responder citando o texto da norma e deixar claro que não é parecer jurídico.

## 6. LGPD e ética

- Nome e CPF de titulares são **descartados na passagem bronze → silver** e não aparecem no silver, no gold, no dashboard nem nas respostas do chat. O bronze fica fora do git.
- Estimativas de déficit nunca saem em nível de serventia identificável. O menor nível exibido é o município, e municípios com **menos de 3 serventias** (`limiar_agregacao_lgpd`, em config) entram agregados.
- O README declara que os números são estimativas de mercado com premissas públicas, e não avaliação de nenhum cartório. Declara também que o market share é de uma seguradora hipotética, sem dado interno de nenhuma empresa.

## 7. Avaliação (`src/eval`)

### 7.1 Gabaritos (rotulados à mão, antes dos prompts)

- **Radar**: 60 a 100 documentos reais, estratificados:
  - **pelo menos 10 relevantes**, cobrindo cada `tipo_evento` aprovado. Se faltarem documentos sobre o 227, completar com normas anteriores do setor de cartórios;
  - duplicatas (a mesma notícia em fontes diferentes);
  - itens "quase relevantes" (normas de cartório sem relação com passivo trabalhista).
- **Chat**: 40 a 60 perguntas de 4 tipos (números, normas, simulação e armadilhas), cada uma com resposta esperada e fonte esperada. O gabarito **fixa a versão das premissas** usada nas respostas numéricas.
- **Congelamento**: o gabarito é congelado com hash e data. Não editar depois de ver as saídas do modelo. Qualquer mudança vira uma nova versão do gabarito, com justificativa no diário.

### 7.2 Métricas

- **Radar**: precisão e recall da relevância, com intervalo de confiança; acurácia por campo extraído; taxa de citações válidas; duplicatas não detectadas; latência entre a publicação e o alerta.
- **Chat**: % de respostas corretas; % de alucinações (número ou norma inexistente); % de respostas sem fonte; % de "não sei" corretos e incorretos.
- **Comparação de versões**: (a) sem contexto, (b) norma inteira no prompt, (c) RAG, (d) RAG + ferramentas. O corpus de normas é pequeno, então a versão (b) pode competir com o RAG, e o eval decide.
- **Custo e latência**: tokens e R$ por execução, e tempo de resposta.
- **Forma de avaliar**: por regra sempre que possível (o número bate? a citação existe?). Usar LLM-as-judge só onde for inevitável, com uma amostra conferida à mão.
- **Limitação declarada**: o gabarito é rotulado por uma pessoa só, então o intervalo de confiança é largo e isso aparece nos slides.

## 8. Fases e critérios de aceite

### Fase 0: Viabilidade (timebox de 1 a 2 dias)

- Instalar o `uv` e o Python 3.12 por meio dele, **sem alterar o Python do sistema** (3.13.3).
- Baixar os textos dos Provimentos 227, 213 e 243 em atos.cnj.jus.br e confirmar:
  - os arts. 8º a 17;
  - a definição de passivo (demissão sem justa causa);
  - o prazo do primeiro ano;
  - os critérios da Classe I;
  - quem é o segurado da garantia.
- Conferir o andamento da ADI 8015.
- Testar o acesso real a cada fonte do §1.1 e registrar no diário o formato, os campos, a cobertura e se há download em massa.
- Comparar o total de vínculos RAIS do CNAE 6912-5/00 com o total de empregados do "Cartório em Números" (risco de vínculos no CPF/CEI do titular).
- Decidir a fonte do universo e o plano B.
- Validar o MotherDuck, já escolhido para o estado e o gold: conexão local, a partir do GitHub Actions e a partir do Streamlit Cloud, e os limites do plano free.
- **Aceite**: `docs/viabilidade.md` com uma linha por fonte (ok / parcial / bloqueada + plano B). Se o universo não puder ser obtido para todo o Brasil, o projeto segue com as UFs disponíveis e declara isso.

### Fase 1: Fatia vertical com 1 UF (sugestão: MG)

- Ingestão, silver e gold só para MG.
- Modelo completo (§3), com testes.
- Páginas "Mercado" e "Simulador" básicas, com o mercado total e a seguradora hipotética lado a lado e a `data_referencia` de cada fonte visível.
- **Aceite**: `uv run pipeline.py`, rodado a partir dos snapshots do bronze, gera o dashboard de MG, os testes passam e todo número na tela tem fonte e versão.

### Fase 2: Brasil inteiro e qualidade

- Expandir para todas as UFs disponíveis, com contratos e reconciliação (§4).
- **Aceite**: relatório de qualidade gerado e divergências documentadas.

### Fase 3: Radar

- Ordem de construção: gabarito, coletores, pipeline, aprovação, resumo diário e agendamento.
- **Aceite**: métricas do radar no relatório, e um evento real passa pela aprovação, gera uma versão em `premissas_versoes` e muda o simulador.

### Fase 4: Agente de dúvidas (bônus)

- Ordem de construção: gabarito, ferramentas, as 4 versões e a integração na página Chat.
- **Aceite**: métricas do chat e o gráfico comparando as 4 versões.

### Fase 5: Entrega

- Deploy (Streamlit Community Cloud) apontando para o armazenamento persistente.
- README com o problema, a arquitetura em diagrama, como rodar, os resultados do eval e as limitações. Inclui o desenho do produto (tomador pessoa física, segurado) como premissa e limitação.
- Medida de antes e depois: tempo da tarefa manual (linha de base no diário) vs. com o sistema, e atraso entre a publicação de uma norma e o alerta.
- Slides (5): problema, arquitetura, demo, onde a IA errou e o que mudou, resultados com o gráfico das versões.
- Demo de 1 minuto, seguindo o mínimo do §0: uma norma real entra, o radar detecta, você aprova e o simulador recalcula. Se o chat estiver pronto, ele responde com a fonte.
- **Robustez da demo**: cache das respostas do LLM e das consultas usadas na demo, para ela rodar sem rede e sem limite de API. Gravar um vídeo de backup.
- Na véspera: conferir o andamento da ADI 8015 e rodar o radar.

**Se o tempo apertar, cortar nesta ordem**:

1. o agente de dúvidas (Fase 4), que é bônus;
2. os projetos de lei no radar;
3. o Monte Carlo;
4. a versão RAG (se o chat existir, mantendo o contexto longo com ferramentas);
5. por último, o deploy (roda local).

**Nunca cortar**: a Fase 0, os testes do modelo, o eval do radar, o mínimo da demo (§0) e o diário de erros.

## 9. Como a IA deve trabalhar neste projeto

- **Ritmo**: trabalhar fase por fase e parar ao fim de cada uma para revisão humana.
- **Coletores**: antes de escrever um, inspecionar uma amostra real da fonte e mostrar os campos encontrados.
- **Nada inventado**: nunca inventar valores de premissa, URLs de fonte, números de normas ou dados de exemplo apresentados como reais. Dados sintéticos só em `tests/`, marcados como tal.
- **Diário**: registrar em `docs/diario.md` toda limitação, suposição e decisão, com data.
- **Falhas de fonte**: quando uma fonte falhar, propor o plano B em vez de contornar o problema em silêncio.
- **Regulação atual**: no início do trabalho, conferir o status da ADI 8015 e se houve novas alterações nos Provimentos 213 e 227, porque o cenário regulatório muda rápido.

## 10. Riscos conhecidos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| RAIS não capta vínculos registrados no CPF/CEI do titular (fora do CNAE 6912-5/00) | Passivo subestimado | Checar na Fase 0 contra o "Cartório em Números" e, se a diferença for grande, tratar como premissa de fator de cobertura |
| Passivo concentrado em cartórios grandes | O rateio uniforme distorce o déficit | Rateio por arrecadação como padrão candidato e sensibilidade ao método no dashboard |
| Desenho do produto incerto (tomador pessoa física, segurado indefinido, modalidade SUSEP) | Taxa e sinistralidade sem referência direta | Registrar como premissa (`fonte: suposição`) e como limitação no README |
| Sinistralidade do SES é proxy fraco | Resultado técnico pouco confiável | Mostrar sempre em faixa e declarar o proxy |
| Concorrência com regularização por bens próprios e com fiança | Demanda superestimada | Premissa `escolha_garantia` com três parcelas |
| Liminar na ADI 8015 perto da entrevista | Muda a narrativa da demo | Cenário `suspende_8_17` pronto; conferir o andamento na véspera |
| Prompt injection em textos coletados | O radar classifica ou extrai errado | Texto isolado no prompt, saída validada por schema e citação, sem ferramentas com efeito colateral |
| Custo do BigQuery | Gasto inesperado | Só a cota gratuita, filtro por CNAE e ano e `maximum_bytes_billed` em toda consulta |
| Fragilidade da demo ao vivo (rede, limite de API, cold start do Streamlit) | A demo falha | Cache das respostas e vídeo de backup |
| Gabarito rotulado por uma pessoa e com poucos documentos relevantes | Intervalo de confiança largo | Declarar nos slides; completar com normas anteriores do setor |
| Projeto dentro do OneDrive (decisão tomada) | Sincronização pode travar ou corromper `.venv`, DuckDB e Parquet | Monitorar; se ocorrer, mover o `.venv` para fora com `UV_PROJECT_ENVIRONMENT` e registrar no diário |
| Corte de conhecimento da IA anterior às normas | A IA pode inventar artigos | Confirmar todo artigo no texto oficial antes de usar; registrar erros em `erros_ia.md` |
| Escopo grande para 5 minutos | Fases incompletas | Mínimo da demo definido no §0 e ordem de corte no §8 |
