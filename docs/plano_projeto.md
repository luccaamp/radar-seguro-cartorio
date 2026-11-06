# Plano do projeto — Radar Seguro-Garantia Cartórios

05/11/2026

> **Plano oficial do projeto (D-071, aprovado pelo autor em 2026-11-05).** Substitui o plano de 2026-10-23 (D-039), que levava MG até uma demo local; aquele plano, com as Etapas 1 a 3 cumpridas, está em [`historico/plano_projeto_ate_2026-11-05.md`](historico/plano_projeto_ate_2026-11-05.md). O detalhamento da mineração (Etapa 1, concluída) continua no [`plano_mineracao.md`](plano_mineracao.md). Em conflito, vale este plano. **Modo de trabalho:** a IA propõe cada passo e segue com a aprovação do autor.

## Aonde chegar

Um **painel público**, aberto a qualquer pessoa, com os cartórios dos **27 estados**:
- o mesmo conteúdo que MG tem hoje (cartórios, classes, obrigados, passivo trabalhista, déficit, prêmio, faixa de incerteza, projeções, mapa por município), para cada estado e para o Brasil somado;
- alimentado por um **pipeline automático**, que coleta das fontes oficiais de tempos em tempos e só publica se os contratos de qualidade passarem;
- com um **agente de IA** que responde com fonte e nunca inventa número, avaliado com rigor e acessível também por **MCP**;
- tudo gratuito, reproduzível a partir de um clone e documentado, inclusive como o projeto foi construído dirigindo uma IA (`decisoes.md`, `erros_ia.md`, `diario.md`).

**Onde a fonte de um estado for mais fraca que a de MG, o painel avisa** com o selo "dado da fonte" ou "estimado":
- empregados: onde o CNJ não traz a contagem, um modelo estima (erro declarado de ±10% no total, T1);
- capacidade de pagar do titular (premissas v3): planilha do BI do CNJ, que só sai por exportação manual (atualização manual, não pelo robô);
- normas da corregedoria local: até alguém conferir, vale a regra nacional, marcada `fonte: suposição`;
- RAIS: sai uma vez por ano (carga anual, manual).

## Padrões que valem em todas as fases

- **Qualidade:** cada mudança entra por pull request com o CI verde; código novo com teste; `ruff` sem erro.
- **Reprodutibilidade:** um clone reproduz os números publicados (hoje: 39 de 39 tabelas idênticas, conferido em 2026-10-31); cada publicação tem manifesto com SHA-256.
- **Dados:** só fontes oficiais, com data de referência; premissa sem fonte é `fonte: suposição`; nenhum número fixo no código (`CLAUDE.md`).
- **Dados pessoais (D-038):** nenhum nome nem CPF de pessoa física em painel, chat, MCP, dataset, log ou artigo; o auditor e os testes conferem em cada publicação.
- **Custo zero:** só níveis gratuitos, sem cartão; cada serviço novo é uma exceção registrada (Fase 0).
- **Registro:** cada escolha vira decisão (`decisoes.md`); cada erro da IA, uma entrada no `erros_ia.md`; cada sessão, no `diario.md`.
- **Versões:** `v1.0` = MG público; `v2.0` = Brasil, camada 1, atualizado sozinho; `v2.x` = cada estado que entra na camada 2; `v3.0` = Brasil completo.

## As fases

| Status | Fase | O que entrega | Versão |
|---|---|---|---|
| 🔄 | 0 — Fundamentos | regras do jogo, decisões pendentes, chave nova, CI | — |
| ⬜ | 1 — MG completo | tudo do plano antigo fechado, sem nada pela metade | — |
| ⬜ | 2 — MG publicado | painel no ar, README de vitrine, página de saúde | `v1.0` |
| ⬜ | 3 — Código por estado | um estado novo vira configuração e dado | — |
| ⬜ | 4 — Brasil, camada 1 | 27 UFs (cartórios, classes, arrecadação) e pipeline agendado | `v2.0` |
| ⬜ | 5 — Ordem dos estados | notebook que decide por onde seguir | — |
| ⬜ | 6 — Brasil, camada 2 | modelo completo estado por estado | `v2.x` → `v3.0` |
| ⬜ | 7 — Agentes e integrações | chat nacional, avaliação contínua, MCP, radar de normas, API | — |
| ⬜ | 8 — Publicações | Hugging Face, Kaggle, artigos, documentação em inglês | — |
| ⬜ | 9 — Apresentação | roteiro de demo e números medidos | — |

Cada fase só começa quando a anterior cumpre o seu "pronto quando", salvo as que o autor liberar em paralelo (por exemplo, a Fase 5 com a 6, ou partes da 8 depois da 2).

### Fase 0 — Fundamentos

1. **Este plano** (D-071) e o alinhamento do SPEC e do ROADMAP a ele.
2. **Decisões de governança:**
   - **D-072:** exceções ao "100% gratuito" para **GitHub Actions**, **Hugging Face** e **Kaggle** (níveis gratuitos, sem cartão; hoje o SPEC §1 põe o GitHub Actions "fora do projeto");
   - **D-073:** fluxo de trabalho: uma branch por bloco, pull request, CI obrigatório, `main` sempre publicável, uma branch aberta por vez (a correção perdida do `bb12465` veio de branches longas e paralelas);
   - **D-074:** hospedagem do painel (Streamlit Community Cloud ou Hugging Face Spaces) e onde ficam os dados publicados (repositório, Releases ou Parquet remoto).
3. **Decisões pendentes de MG, em lote:** D-039 (vira histórico com a D-071), D-042, D-049, D-051, D-052, D-064, D-069, D-070 e as premissas `fonte: suposição` de `config/analise.yaml`.
4. **Segurança:** chave do Gemini trocada (a atual apareceu num log em 2026-10-28); chaves só como *secrets* do GitHub e do serviço do painel.
5. **CI:** `pytest` e `ruff` em cada pull request, com o selo no README; os testes de dados reais num job separado, com os dados de `data/completo/`.
6. **Bloco A do fechamento de MG** (feito em 2026-11-05, na branch `fechamento-mg-a`): juntar na `main`.

**Pronto quando:** decisões registradas; CI verde na `main`; chave nova em uso; bloco A na `main`.

### Fase 1 — MG completo

1. **Simulador** (a antiga Etapa 4, completa): controles de ano (2026 base, 2027 projeção), limite de classe fixo ou corrigido e faixa por sorteio (Monte Carlo); tornado ao vivo; os três cenários do STF; redesenho no padrão visual atual; decisão do autor sobre o lugar dele no painel (navegação ou página "explorar"). **Pronto quando:** os testes do SPEC §3 passam e o recálculo leva menos de 1 s.
2. **D-038, fase 2:** sem o limiar de 3 serventias e sem as áreas agregadas (premissas v4, pipeline e carga oficial); mapa e ranking por município, inclusive os pequenos.
3. **Notebooks 01 a 10** rodados de novo do zero numa cópia, com os imports sem uso corrigidos e a mesma saída (sai o `per-file-ignores` do `pyproject.toml`).
4. **Chat:** avaliação completa nas 52 perguntas, versões (a), (b) e (c); se a meta da D-065 não for atingida, corrigir o agente e rodar de novo, com cada versão do prompt registrada; relatório com acerto por tipo, alucinação nas armadilhas, respostas sem fonte e latência; a pergunta preenchida pelo link (`?pergunta=`) funcionando.
5. **Pendências do ROADMAP §7:** SPEC §5.1 reescrito; o nome de `gold.fato_mercado_municipio_publico`; regras de estilo do `ruff`; fonte do painel embutida no repositório (licença OFL).
6. **Revisão final:** dados pessoais; os 10 números contra a linha de base; capturas em 390, 1366 e 1920 px, nos temas claro e escuro; acessibilidade (contraste e leitor de tela).

**Pronto quando:** cada item acima cumpre o seu critério e a nova linha de base de MG está registrada.

### Fase 2 — MG publicado (`v1.0`)

1. **Painel no ar** no serviço da D-074, lendo o conjunto público, com o chat e o limite de perguntas por sessão.
2. **README de vitrine:** link, GIF, diagrama da arquitetura (fontes → bronze → silver → gold → público → painel, chat e MCP), números medidos, como reproduzir, limitações e licença.
3. **Página de saúde:** data dos dados, versão das premissas, resultado dos contratos; estatísticas de visitantes do serviço de hospedagem.
4. **Release `v1.0`** com o pacote de dados e as notas.

**Pronto quando:** o link público abre o painel de MG no modo completo, o chat responde e um clone reproduz os números.

### Fase 3 — Código por estado

1. Tirar o que só vale para MG: códigos e pacotes da RAIS por UF nos coletores; o total do estado no gold e nas visões; `uf = 'MG'` nos contratos e nas reconciliações; o "fator de MG" na previsão; textos do painel, do chat e do prompt.
2. **Configuração por estado:** totais de controle, premissas (a de MG como ponto de partida, `fonte: suposição` nos outros estados até a calibração), normas locais, apelidos de municípios.
3. **Seletor de estado** no painel e no chat, e a visão "Brasil".

**Pronto quando:** com `ufs: [MG]`, o resultado é idêntico ao de hoje (as 39 tabelas e os 10 números) e um teste com dois estados sintéticos passa.

### Fase 4 — Brasil, camada 1, atualizado sozinho (`v2.0`)

**Camada 1** = o que as fontes nacionais dão sem o modelo de passivo: cartórios, situação, atribuições, classe, obrigados pela regra e arrecadação, por estado e município.

1. **Coleta das 27 UFs:** o cadastro já está no bronze (2026-10-17); arrecadação e colaboradores pela API do CNJ, por UF (a consulta do Brasil inteiro numa requisição dá timeout); IBGE (municípios, malhas, população); CNPJ; SES por UF.
2. **Contratos e reconciliações nacionais:** CNJ × BI × ANOREG por UF, com as divergências documentadas (a RAIS do Brasil tem 12% mais vínculos que a ANOREG, causa a investigar).
3. **Pipeline agendado (GitHub Actions):** frequência de cada fonte conforme a atualização dela (CNJ e CNPJ mensais, SES mensal, RAIS anual e manual, IBGE quando mudar); coleta → contratos → gold → auditor → publicação; **qualquer falha bloqueia a publicação e abre uma issue**; cada publicação gera manifesto novo e Release datada.
4. **Agente de atualização:** depois de cada carga, escreve "o que mudou nesta atualização" nas notas da Release e no painel, com a regra do chat (todo número vem de uma ferramenta, com fonte).
5. **No painel:** mapa do Brasil, comparação entre estados, selo "atualizado em".

**Pronto quando:** as 27 UFs publicadas; o job agendado roda um ciclo completo sozinho; uma falha simulada bloqueia a publicação e abre a issue; auditor sem vazamento.

### Fase 5 — Ordem dos estados

1. Notebook com a nota combinada: tamanho (serventias, empregados), mercado, viabilidade dos dados de cada UF e adoção (seguradoras e garantia na SES), com os dados da camada 1.
2. Teste de sensibilidade dos pesos e validação com MG.
3. Decisão registrada com a ordem.

**Pronto quando:** a ordem é estável para os primeiros estados sob variação razoável dos pesos (ou a instabilidade está explicada) e a decisão está registrada.

### Fase 6 — Brasil, camada 2, estado por estado (`v2.x` → `v3.0`)

**Camada 2** = o modelo completo: passivo trabalhista (RAIS), déficit, IS, prêmio, sensibilidades e projeções.

1. **Roteiro igual para cada UF:** amostra real da fonte mostrada ao autor antes de escrever ou adaptar um coletor; coleta, contratos e reconciliações; normas da corregedoria local; auditor; números revisados e registrados; painel e chat (o gabarito ganha perguntas da UF); Release.
2. **Modelo de empregados em produção:** onde o CNJ não traz a contagem, a floresta do T1 estima; o modelo é versionado, retreinado a cada carga, com monitoramento de deriva e validação nos estados que têm a contagem.
3. **Análises por UF** (regras, grupos, previsão, tornado, Monte Carlo) pelo pipeline, como em MG; um notebook novo compara os estados (os notebooks de MG continuam contando a história de MG).

**Pronto quando:** cada UF cumpre o roteiro; as 27 estão na camada 2 (`v3.0`).

### Fase 7 — Agentes e integrações

1. **Chat nacional:** ferramentas por UF e comparação entre estados; gabarito ampliado e congelado de novo, com a meta fixada antes de rodar.
2. **Avaliação contínua:** job agendado com a chave como *secret*; histórico de acerto por versão do prompt; alerta quando o acerto cai. A suíte padrão continua sem API.
3. **Servidor MCP:** as mesmas ferramentas do chat, para qualquer agente consultar os dados; documentado, testado e com o mesmo controle de dados pessoais.
4. **Radar de normas:** monitora os Provimentos do CNJ e a ADI 8015 no STF; primeiro sem IA, depois com um agente que resume o que mudou e o que afeta no modelo. Nunca muda uma premissa sozinho: abre uma issue para decisão.
5. **API pública estática:** dados agregados em JSON e Parquet, versionados.

**Pronto quando:** cada peça com teste e documentação; a avaliação contínua rodou ao menos um ciclo.

### Fase 8 — Publicações

1. **Hugging Face:** dataset dos cartórios do Brasil (agregado, sem dado pessoal, com data card) e o modelo de empregados (com model card: dados, métrica, limites).
2. **Kaggle:** o mesmo dataset, com um notebook de análise.
3. **Artigos técnicos:** avaliação de um agente que não pode inventar número; pipeline de dados públicos que só publica quando passa nos contratos; desenvolver um projeto inteiro dirigindo uma IA (decisões e erros registrados).
4. **Documentação** em português e em inglês: o `entenda_o_projeto.md` para leigos e um guia de arquitetura.

**Pronto quando:** cada item publicado, com link no README e revisão de dados pessoais.

### Fase 9 — Apresentação

1. **Roteiro de demo de 5 minutos:** o problema → o painel ao vivo → o chat ao vivo → o pipeline (histórico do Actions) → os números da avaliação → o papel do autor (decisões e erros da IA) → próximos passos.
2. **Números medidos de verdade:** estados cobertos, acerto do chat, armadilhas sem número inventado, tempo e frequência do pipeline, testes, custo, visitantes e o tempo para responder perguntas do gabarito com e sem o chat (teste feito pelo autor). Nenhum número estimado apresentado como medido.
3. **Manutenção:** o pipeline continua atualizando o painel depois da entrega.

## Riscos e o que fazer

| Risco | Efeito | O que fazer |
|---|---|---|
| API do CNJ instável ou sem documentação | coleta falha ou incompleta | coleta por UF, contratos de contagem, publicação bloqueada na falha |
| Limites dos níveis gratuitos (memória do painel, cota do Gemini, disco do Actions) | painel lento, chat indisponível, job quebrado | painel lendo tabelas agregadas; limite por sessão e perguntas prontas sem o modelo; RAIS fora do job agendado |
| Estado com fonte fraca | número menos certo que o de MG | selo "estimado" e faixa declarada; validação nos estados com contagem |
| Liminar na ADI 8015 | mercado vai a zero no cenário "suspende" | cenário no simulador; radar de normas; aviso no painel |
| Escopo crescendo sem fim | nada fica pronto | cada fase só termina com o seu "pronto quando"; o que surgir no meio vira item de fase |
| Dado pessoal vazando num estado novo | violação da D-038 | auditor em toda publicação; teste de nomes do cadastro por UF |

## Decisões que dependem do autor

| Decisão | Quando |
|---|---|
| [x] Plano novo (D-071) | 2026-11-05 |
| [x] D-072 (exceções: Actions, Hugging Face, Kaggle), D-073 (fluxo de branches e PR), D-074 (Streamlit Community Cloud, dados no repositório) | 2026-11-05 |
| [ ] Decisões pendentes de MG em lote (lista na Fase 0, item 3) | Fase 0 |
| [ ] Lugar do Simulador no painel | Fase 1 |
| [ ] Premissas v4 (D-038, fase 2) | Fase 1 |
| [ ] Pesos e ordem dos estados | Fase 5 |
| [ ] Premissas de cada estado novo | Fase 6, por UF |
