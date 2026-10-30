# Ajustes finais e limpeza do projeto — antes de publicar os dados e convidar a equipe

> **Para o Claude Code.** Este documento:
> 1. responde ao seu relatório do "repositório reproduzível";
> 2. pede **ajustes rápidos** (seção 2);
> 3. define como fazer a **limpeza do projeto** (seção 3), em **duas paradas**: primeiro o inventário, que eu aprovo; depois a execução.
>
> **Situação do git:** eu já fiz o commit da rodada anterior (`be27786`), **já enviei a `main` ao GitHub (push)** e criei a branch **`limpeza-fase1`** a partir dela. Trabalhe nela. As regras do `CLAUDE.md` continuam valendo: **nada de commit, push, merge, checkout ou Release.** `git mv` e `git rm` são permitidos **só na etapa de execução (seção 3.4) e só para itens que eu aprovei**, porque preservam o histórico e eu revejo tudo antes do commit.

---

## 1. Resposta ao seu relatório

**Aprovado.** Destaques que ficam registrados:
- reprodutibilidade provada (25/25 tabelas idênticas a partir do silver público e do bronze da equipe);
- o bug do `pipeline.py --help`, que trocaria o banco real por um vazio, foi achado e corrigido;
- o auditor rodou sobre o conjunto público, e os dois ajustes de LGPD (`rec_municipio` e `dim_municipio`) estão corretos;
- `.claude/settings.local.json` no `.gitignore`: correto.

**Respostas aos seus pontos:**
- **Repositório já público:** ciente. A auditoria não achou nada sensível, então **não** vamos reescrever o histórico.
- **E-mail dos commits:** vou configurar o e-mail "noreply" do GitHub daqui em diante (faço eu). Os commits antigos ficam como estão.
- **Usuário do Windows em `docs/prompts.md`:** troque por `<usuario>` (item 2.2).
- **Pastas vazias `data/publico.antigo` e `data/publico.novo`:** eu apago à mão.
- **Licença MIT:** aprovada.

**Duas perguntas suas para responder agora:**
- **Clone: 119 passed + 1 skipped; meu ambiente: 125 passed na suíte padrão.** Explique os 5 testes de diferença: quais são, por que não rodam no clone, e se isso é esperado.
- **Silver público com vínculos da RAIS:** confirme quais colunas do `silver.rais_vinculo` vão no pacote público. Ver o item 2.3.

---

## 2. Ajustes rápidos (antes da limpeza)

### 2.1 `CLAUDE.md`: restaurar e completar regras
Comparei a versão atual com as regras do projeto. A linha nova do "Público" (D-030) está certa, mas **duas regras sumiram ou faltam**. Ajuste a seção "Regras inegociáveis" (acrescentando, sem apagar o que existe):
1. **Restaurar o mínimo de 3 serventias:** "Toda estimativa publicada por área (município ou região) só aparece se a área tiver ≥ 3 serventias e passar no auditor de ataque por diferença (D-026, D-027); áreas menores são agregadas pela região imediata ou intermediária. Partições internas da mesma visão seguem a D-028."
2. **Pacote da equipe:** "`interno_*`, banco `.duckdb` e o pacote da equipe só existem localmente ou no repositório privado `radar-seguro-cartorio-dados` (D-030). Nunca no repositório público, em issues, PRs, prints ou serviços externos (inclusive IAs online)."
3. **GitHub:** acrescentar à regra do git: "**Também nunca** rode comandos do `gh` que criem, alterem ou apaguem algo (`gh release create/upload/delete/edit`, `gh repo edit/create/delete`, `gh pr merge`, `gh api` com escrita). Leitura (`gh repo view`, `gh release list`, `gh auth status`) é permitida. Quem publica é o autor."
4. **Disco e OneDrive:** "O projeto fica no OneDrive (decisão do autor). Arquivos grandes gerados (pacotes, cópias de bronze, arquivos de backup) vão para pastas **fora do OneDrive** (ex.: `C:\radar_pacotes`, `C:\radar_arquivo`). Nunca apagar dado do bronze, silver ou gold sem aprovação explícita; para retirar, **mover** para `C:\radar_arquivo`."
5. **Dado pessoal:** trocar "Nenhum nome ou CPF de titular" por "Nenhum nome, CPF, e-mail ou telefone de pessoa física".

Mostre o `git diff CLAUDE.md` no relatório.

### 2.2 `docs/prompts.md`
Trocar o caminho com o usuário do Windows por `C:\Users\<usuario>\...`. Procure o mesmo padrão em todos os arquivos versionados (código, docs, configs, testes) e troque também.

### 2.3 Decisão D-031: vínculos da RAIS no silver público
- **Contexto:** o `silver.rais_vinculo` vai no pacote público. Não tem nome nem CPF, mas, num município com 1 cartório e 1 empregado, o vínculo revela o salário daquela pessoa.
- **Decisão (minha):** manter no público. O mesmo dado já está nos microdados públicos da RAIS (PDET), filtráveis por CNAE e município, então redistribuir não acrescenta exposição (mesma lógica da D-028).
- **Condição:** o pacote público leva **só as colunas que o pipeline usa**. Liste as colunas atuais e confirme que não há identificador de estabelecimento (CNPJ ou CAEPF), data de nascimento, raça, sexo ou outra coluna sensível que o modelo não use. Se houver, tire do silver público (não do silver interno) e explique.
- Registrar D-031 em `docs/decisoes.md`.

### 2.4 Registro completo da Fase 1 (diário, decisões, erros, prompts, conversas)
Antes de arquivar os documentos de rodada, garanta que **nada da Fase 1 se perdeu**. Tudo por **acréscimo**, sem editar registros antigos.

1. **`docs/erros_ia.md`:** confira se estes erros, encontrados nas revisões, estão registrados (com data, o que aconteceu, como foi achado e a correção). Acrescente os que faltarem:
   - correções 2, 3, 4 e 6 informadas como feitas e não implementadas (A5);
   - testes gravando no banco real e, depois, nos Parquet do gold;
   - classe das faixas de déficit trocando com a regra v1/v2 (A1); datas-base misturadas (A2); serventias sem CLT contando como "com déficit" (A4);
   - LGPD: tabelas com municípios de 1 ou 2 serventias (D1); vazamento por diferença entre visões (E1), entre regras e níveis (E1-b), RTD contido em RCPJ; `rec_municipio` com grupos de 1 ou 2;
   - "$" virando fórmula no `st.markdown`;
   - C1 a C3 declarados corrigidos com base em teste estrutural, mas sem efeito na tela (só o QA visual pegou);
   - zoom do filtro de município errado; "Juíz de Fora";
   - `pipeline.py --help` que trocaria o banco real por um vazio;
   - `GROUP BY` sem `ORDER BY`; instalador de pacotes extraindo em subpasta;
   - edição de código por script que falhou sem aviso;
   - regra do mínimo de 3 serventias removida do `CLAUDE.md` ao reescrever a regra de LGPD;
   - pacote de dados gravado dentro do OneDrive.

   Acrescente também uma seção **"Erros do revisor (assistente no chat)"**, porque o projeto registra erros de IA de qualquer origem:
   - interpretei as manchas escuras do mapa de serventias como efeito da agregação, mas eram reais (municípios com muitos distritos);
   - apontei Almenara "cortada no mapa", mas era um zoom manual do autor no momento da exportação;
   - marquei `apelidos_municipios.yaml` como vazio (o "0 KB" era arredondamento; o arquivo é usado);
   - classifiquei a partição "todas × obrigadas" (Almenara) como vazamento crítico; o autor discordou e decidiu pela D-028;
   - uma versão do plano de repositório previa um repositório só, contrariando a decisão do autor (dois repositórios).
2. **`docs/decisoes.md`:** confira que D-019 a D-030 estão registradas com o status final (APROVADA, APROVADA COM AJUSTE, PROPOSTA) e acrescente D-031 e D-032 quando forem decididas. Liste no relatório as que estiverem faltando ou com status desatualizado.
3. **`docs/diario.md`:** confira que cada rodada da Fase 1 tem uma entrada: verificação contra o BI, Etapa 1, Bloco 1, revisão dos filtros, correções e QA visual, repositório reproduzível e esta limpeza. Acrescente as que faltarem, com o resultado principal de cada uma.
4. **`docs/prompts.md`:** acrescente uma seção **"Fase 1"** com a lista, em ordem, dos documentos de pedido usados (com o caminho final em `docs/historico/` depois da limpeza), cada um com data e uma linha sobre o objetivo, e as mensagens curtas de envio mais usadas (ex.: "Leia @docs/X.md por inteiro… pare na PARADA…"). Mantenha as instruções do `jsonl_para_md.py`.
5. **`conversas/`** (local, fora do git): liste as sessões do Claude Code da Fase 1 que existem na máquina e ainda não foram convertidas. Me mostre a lista e, **com a minha aprovação**, converta-as com `scripts/jsonl_para_md.py` para `conversas/`. Não versione nada dessa pasta.

No relatório da Parada 1, mostre o que foi acrescentado em cada arquivo (resumo) e o que já estava lá.

### 2.5 Arquivo de estado do projeto (`docs/ESTADO_ATUAL.md`)
Crie um arquivo **curto** (no máximo 2 páginas) que qualquer pessoa ou IA leia primeiro para saber **onde o projeto está**:
- o que é o projeto (3 linhas);
- fase e etapa atuais, e a branch;
- os números de referência atuais, com a data da carga e a versão das premissas;
- as últimas decisões (número + uma linha cada);
- o que está em andamento e os próximos 5 passos;
- pendências que dependem do autor;
- onde está cada coisa (links para SPEC, decisões, diário, erros, publicação, CONTRIBUTING).

Acrescente ao `CLAUDE.md`, em "Ao terminar cada sessão": **"Atualize `docs/ESTADO_ATUAL.md`"**, e no início: **"Leia `docs/ESTADO_ATUAL.md` antes do SPEC"**. Ele é versionado (não pode ter `interno_*` nem dado pessoal).

---

## 3. Limpeza do projeto

### 3.1 Objetivo
Deixar o projeto **enxuto e fácil de entender** para quem chega (colegas e avaliadores), **sem perder nada** de rastreabilidade e **sem mudar nenhum número**. Também reduzir o **pacote da equipe** (hoje 8,4 GB) antes da publicação definitiva.

### 3.2 Princípios
1. **Evidência, não impressão.** Cada item só sai se houver prova de que não é usado: não é importado, não roda no pipeline nem nos testes, não é citado em nenhum doc, config ou script.
2. **Mover antes de apagar.** Código e docs: `git mv` para pastas de arquivo (o histórico fica preservado). Dados: **mover** para `C:\radar_arquivo\` (fora do OneDrive), nunca apagar.
3. **O trilho de auditoria fica intacto.** `diario.md`, `decisoes.md`, `erros_ia.md`, `SPEC.md`, `viabilidade.md` e `dicionario_dados.md` **não** são apagados nem movidos.
4. **Nenhum número muda.** A prova é o hash do gold e os 10 números de referência.
5. **A limpeza não mistura funcionalidade nova.** Se achar um bug, registre e me mostre; não corrija junto (exceto se a limpeza quebrar algo). A única estrutura nova permitida é a pasta de notebooks (3.5).
6. **Toda hipótese sobre dado é TESTADA antes de qualquer ação.** "Parece não ser usado" não basta. Para cada item de dados (P1 a P4 e qualquer outro), faça o **teste de ausência** já no inventário: numa **cópia** do projeto fora do OneDrive, retire o item (renomeie ou não copie) e rode `pipeline.py --a-partir-de bronze` + a suíte padrão. O resultado precisa ser **idêntico à linha de base** (25/25 tabelas, mesmos números, mesmos testes). Se algo mudar ou quebrar, o item é **usado** e fica. Mostre o resultado de cada teste no inventário.

### 3.2b Pré-inventário do autor (confirme com evidência; não confie só nesta lista)
Fiz um levantamento rápido dos arquivos (versionados, fora do git e tamanhos). Use como ponto de partida:

| # | Achado | Tamanho | Hipótese | O que confirmar |
|---|---|---|---|---|
| P1 | `data/bronze/rais/2025/extraido/*.COMT` | **6,3 GB** | Conteúdo descompactado dos `.7z`; regenerável | Que nada lê os `.COMT` depois de gerar `RAIS_VINC_PUB_MG_ES_RJ_CNAE6912500_MG.csv` (4 MB); se `RAIS_ESTAB_PUB` (0,14 GB `.7z` + 1,4 GB `.COMT`) é usado por algo |
| P2 | `data/bronze/cnpj/2026-10/Estabelecimentos0-9.zip` e `Empresas0-9.zip` | **6,5 GB** | Só servem para gerar `estabelecimentos_cnae6912500.json` (4,8 MB) | Se o silver lê só o JSON; se `Empresas*.zip`, `Municipios.zip` e `Naturezas.zip` são usados |
| P3 | `data/bronze/susep_ses/2026-10-17/BaseCompleta.zip` | 0,55 GB | Só serve para gerar `ses_seguros_garantia.csv` e `ses_cias.csv` | Se o silver lê só os CSV |
| P4 | `data/bronze/rais/2025/*.7z` | 0,9 GB | Só servem para gerar o extrato CSV de 4 MB | Idem P1 |
| P5 | `pacotes/` dentro do projeto (OneDrive) | 2,6 MB | Pacote público de teste gravado no lugar errado | Mover a saída padrão de `empacotar_dados.py` para fora do OneDrive (`C:\radar_pacotes`) e remover a pasta do projeto |
| P6 | `docs/qa/antes/` e `docs/qa/depois/` | ~30 MB | O "antes" já não serve | Manter só a galeria atual (ou mover a saída padrão do QA para fora do OneDrive) |
| P7 | `config/apelidos_municipios.yaml` | < 1 KB | **Não é vazio**: traz as grafias que diferem do IBGE (ex.: BRASOPOLIS, AMPARO DA SERRA). Provavelmente usado na normalização | **Manter**, a menos que a evidência mostre o contrário (o tamanho "0 KB" no meu levantamento era só arredondamento) |
| P8 | `scripts/verificacao_fase1/` (9 arquivos) | pequeno | Scripts de uso único da Fase 1 | O `comum.py` foi alterado na última rodada: algum teste ou script atual depende dele? |
| P9 | `.agents/`, `.claude/` (não versionadas) | ~0 MB | Configuração local de ferramentas | Ver tabela de áreas abaixo |
| P10 | `data/publico/` × `data/gold/` | 0,6 MB | Duplicação **proposital** (D-029) | **Manter** |

**Ampliação da D-032 (bronze = extrato + registro do original):** com P1 a P4, o bronze de que o pipeline precisa deve cair para algo perto de **150 MB** (hoje 14,2 GB no disco; o pacote da equipe hoje tem 8,4 GB). Proposta:
- o bronze oficial guarda o **extrato** de cada fonte grande (RAIS, CNPJ, SUSEP) e um `original.json` com a URL oficial, o SHA-256, o tamanho e a data de coleta do arquivo original;
- os originais e os `.COMT` vão para `C:\radar_arquivo\bronze_originais\` (mover, não apagar);
- o coletor continua baixando o original e gerando o extrato. **Teste obrigatório:** rodar a extração sobre o original guardado gera um extrato com o **mesmo hash** do bronze oficial;
- o pacote da equipe leva só o bronze oficial; `--com-originais` inclui os originais (em partes < 2 GiB);
- o `pipeline.py --a-partir-de bronze` precisa continuar dando 25/25 tabelas idênticas.

Mostre o tamanho estimado do bronze oficial e do pacote da equipe depois disso. Lembre no relatório que `C:\radar_arquivo\` vira a única cópia local dos originais, e que as fontes podem trocar o arquivo publicado. Recomende um backup externo, que eu faço.

### 3.3 Etapa 1 — INVENTÁRIO (só ler e medir; nada é movido)

**Primeiro passo: gravar a LINHA DE BASE** (antes de qualquer outra coisa), em `C:\radar_arquivo\baseline\` (fora do OneDrive):
- SHA-256 de cada tabela do gold e de cada arquivo de `data/publico/`, mais o hash de conteúdo do gold (o mesmo usado na prova de reprodutibilidade);
- os 10 números de referência, lidos do banco;
- a lista de testes que passam em cada suíte (padrão, `dados_reais`, `visual`), com os nomes;
- uma cópia da galeria de prints atual (`docs/qa/`);
- o tamanho de cada pasta do projeto e de `data/`.

Todas as provas da Etapa 2 comparam com essa linha de base.

**Sem tocar nos dados reais durante o inventário:** quando precisar rodar o pipeline (ex.: para o `coverage`), use **cópias** num diretório temporário fora do OneDrive, apontando o banco e as pastas de saída para lá (`RADAR_BANCO` ou equivalente). O banco real, o silver, o gold e o `data/publico/` não podem mudar nesta etapa: confira a data e o tamanho antes e depois.

**Ferramentas** (gratuitas; instale **só como dependência de desenvolvimento** e me diga quais):
- `ruff check --select F401,F841` (imports e variáveis sem uso);
- `vulture` (código morto; trate os achados como **candidatos**, porque há falsos positivos com Streamlit e pytest);
- `coverage` rodando **o pipeline completo a partir do bronze e a suíte inteira** (`pytest` + `-m dados_reais` + `-m visual`). O que nunca roda em nenhum dos três é candidato;
- `deptry` (dependências declaradas e não usadas, e usadas e não declaradas);
- busca textual do nome de cada arquivo em todo o repositório (código, docs, configs, `pyproject.toml`, README);
- `git ls-files` comparado com o disco (versionado, ignorado e "solto"), com o tamanho de cada pasta.

**O que inventariar:**

| Área | O que olhar | Destino típico |
|---|---|---|
| **docs de rodada** (`revisao_fase1.md`, `verificacao_final_fase1.md`, `aprovacao_etapa1_fase1.md`, `revisao_painel_filtros.md`, `correcoes_e_qa_visual.md`, `repositorio_reproduzivel.md`, `resposta_verificacao_final_fase1.md` e, ao final, este `limpeza_projeto.md`) | Ainda são instrução viva ou já são histórico? | `docs/historico/`, com um `docs/historico/INDICE.md` (arquivo · data · uma linha sobre o que foi). **`plano_qualidade_e_correcoes.md` fica em `docs/`**, porque é o plano do Bloco 2, que ainda será executado. |
| **scripts** (`scripts/verificacao_fase1/`, cascata, conferências pontuais) | Usados por algum teste, doc ou fluxo atual? | `scripts/arquivo/` (com um README curto), ou remover se o resultado já estiver no diário |
| **código** (`src/`, `app/`) | Funções, classes e módulos sem uso; sobras de v1; duplicações | Remover (com evidência) |
| **testes** | Duplicados, obsoletos, marcados `skip` para sempre | Remover ou consolidar (com motivo) |
| **config/** | Chaves e arquivos YAML que o código não lê | Remover ou marcar como "só documentação" |
| **dependências** (`pyproject.toml`) | Sem uso (deptry) | Remover |
| **data/** local | Pastas datadas do bronze que **não** são da carga oficial; Parquets intermediários; `docs/qa/` antigos; caches | Mover para `C:\radar_arquivo\` |
| **raiz** | Arquivos soltos, nomes inconsistentes | Organizar |
| **`.gitignore`** | Falta algo? Sobra regra morta? | Ajustar |
| **pastas não versionadas `.agents/` e `.claude/`** | O que há nelas (descreva sem copiar conteúdo sensível); se algo deveria ser compartilhado com a equipe (ex.: configurações comuns do Claude Code em `.claude/settings.json`) ou é pessoal (`settings.local.json`, históricos, caches) | `.gitignore` para o que é pessoal; versionar só o que for comum ao projeto, **se eu aprovar** |
| **`conversas/`** (transcrições, fora do git) | Confirmar que está no `.gitignore` | **Não mexer** |
| **links entre documentos** | Quais `.md` (README, SPEC, CONTRIBUTING, CLAUDE, docs) apontam para arquivos que vão mudar de lugar | Atualizar os links na execução |

**Item especial — bronze enxuto (D-032, proposta; ver também a ampliação na 3.2b):**
- Hoje o pacote da equipe leva o **CNPJ completo (6,8 GB)** e a **SUSEP SES completa (0,58 GB)**, mas o projeto usa só os estabelecimentos do CNAE 6912-5/00 (conferência) e os ramos 0775 e 0776.
- **Verifique primeiro:** pela tabela de fontes, o bronze **já tem** os extratos filtrados: `cnpj/2026-10/estabelecimentos_cnae6912500.json` e `susep_ses/2026-10-17/ses_seguros_garantia.csv`. Se o silver lê só esses extratos, a mudança pode ser apenas **tirar os zips originais do pacote** (mantendo o registro deles), sem mexer no coletor. Diga qual é o caso.
- **Proposta:** manter no bronze **o extrato filtrado** de cada uma (o que o silver de fato lê), junto com um registro do **arquivo original** (URL oficial, SHA-256, tamanho e data de coleta).
  - O original completo vai para `C:\radar_arquivo\` (backup local), fora do pacote.
  - O pacote da equipe passa a levar o extrato. Opção `--com-originais` no `empacotar_dados.py` para quem quiser tudo.
  - O coletor continua capaz de baixar o original e gerar o extrato. **Teste:** gerar o extrato a partir do original dá o mesmo hash do extrato guardado.
- **Mostre:**
  - o tamanho estimado do pacote da equipe depois disso;
  - se o pipeline a partir do bronze continua dando 25/25 idênticas;
  - se algum outro arquivo do bronze (RAIS, CNJ, IBGE) também tem parte grande sem uso. Para a RAIS, o `.7z` original de 0,9 GB fica, a menos que o extrato MG do CNAE seja muito menor; nesse caso, proponha o mesmo tratamento.

**Item especial — carga oficial:** a carga oficial é a referenciada em `data/carga_atual.json` e no manifesto do pacote. Qualquer pasta datada do bronze que **não** esteja nesse manifesto é candidata a mover para `C:\radar_arquivo\`; tudo o que está no manifesto **fica**.

**Item especial — ferramentas de qualidade para a equipe:** diga se vale manter alguma das ferramentas instaladas (ex.: `ruff`) como padrão do projeto, com um comando no `CONTRIBUTING.md`, ou se todas saem depois da limpeza.

### 3.5 Pasta de notebooks (estrutura nova, para mineração de dados e modelos preditivos)
O autor e a equipe vão fazer **análise exploratória, mineração de dados e algoritmos preditivos** em notebooks. Proponha no inventário, e crie na execução (se aprovado):
- **`notebooks/`** na raiz, com um `notebooks/README.md` curto:
  - nomes numerados e descritivos: `01_exploracao_arrecadacao.ipynb`, `02_modelo_prob_deficit.ipynb`;
  - **notebook lê, não escreve:** acesso aos dados só por uma função de apoio (ex.: `src/notebooks.py` com `conectar()` que abre o DuckDB **somente leitura**, ou lê os Parquet); nunca grava em bronze, silver ou gold;
  - código que virar reutilizável sai do notebook e vai para `src/` (com teste);
  - modelos treinados e saídas grandes vão para `modelos/` ou `notebooks/saidas/`, **no `.gitignore`**.
- **Proteção contra vazamento:** saída de notebook pode conter tabela `interno_*` ou dado por serventia e ir parar no repositório público.
  - **Saídas sempre limpas antes do commit:** proponha `nbstripout` (gratuito, local; dependência de dev, instalado no git de cada pessoa com `nbstripout --install`). Documente no `CONTRIBUTING.md`, e um teste que falha se algum `.ipynb` versionado tiver saída.
  - Notebooks que usam `interno_*` ficam em **`notebooks/privado/`**, no `.gitignore`.
- **Ferramentas:** `jupyterlab` e `ipykernel` como dependência de dev (gratuitos e locais). Bibliotecas de modelagem (ex.: `scikit-learn`) **só quando o primeiro notebook precisar**, com a minha aprovação.
- Acrescentar ao `CLAUDE.md` e ao `CONTRIBUTING.md` as regras dos notebooks (ler e não escrever; saídas limpas; `privado/` para `interno_*`), e uma linha na seção de estrutura do `SPEC.md`.
- Criar um notebook de exemplo **pequeno** (`00_exemplo_leitura.ipynb`), que conecta e mostra os 10 números de referência a partir das tabelas **públicas**, sem saída salva.

**Item especial — estrutura do repositório:**
- Proponha a estrutura final de pastas (árvore com uma linha por pasta) e acrescente ao README uma seção curta "**Estrutura do projeto**", para quem chega.

### ⛔ PARADA 1 — entregue o inventário e espere minha aprovação
Uma tabela, com uma linha por item:

| Item | Tipo | Tamanho | Evidência (por que sai ou move) | Ação proposta (manter / mover / arquivar / remover) | Risco |
|---|---|---|---|---|---|

Mais:
- resumo por área (quantos itens e quanto espaço);
- a proposta da D-032, com os números;
- a estrutura final proposta (incluindo `notebooks/`);
- o resultado do **teste de ausência** de cada item de dados (princípio 6);
- a lista de ferramentas instaladas.

**Não mova, não remova e não altere nenhum arquivo nesta etapa** (exceto os ajustes da seção 2 e a instalação das ferramentas de dev).

### 3.4 Etapa 2 — EXECUÇÃO (só depois da minha aprovação, item a item)
0. A minha mensagem de aprovação vai **autorizar explicitamente** o uso de `git mv` e `git rm` para os itens aprovados (o `CLAUDE.md` exige pedido explícito na mensagem atual).
1. Executar **só os itens aprovados**, nesta ordem: docs → scripts → testes → código → config → dependências → `.gitignore` → pasta de notebooks (3.5) → dados locais (mover para `C:\radar_arquivo\`) → bronze enxuto (D-032, se aprovada).
2. Antes de mover dados, gravar `C:\radar_arquivo\MANIFESTO.md` com o que foi movido, de onde, o tamanho e o SHA-256. Confira o espaço livre em `C:` antes.
2b. **Regra de parada:** depois de cada área, rode a suíte padrão. Se **qualquer** teste quebrar ou **qualquer** número de referência mudar, **pare**, desfaça o último item (código e docs: `git restore`/`git mv` de volta; dados: mover de volta) e me mostre o que aconteceu.
2c. Depois de mover docs, atualize **todos os links** que apontavam para eles, e verifique que nenhum link relativo nos `.md` versionados ficou quebrado (um teste simples que procura links para arquivos inexistentes).
3. **Provas, ao final:**
   - pipeline **do zero a partir do bronze** (o enxuto, se a D-032 for aprovada) → **hash do gold idêntico** à linha de base (25/25 tabelas), e `data/publico/` idêntico;
   - os 10 números de referência iguais;
   - `uv run pytest`, `-m dados_reais` e `-m visual` passando, com a mesma lista de testes da linha de base, exceto os removidos com aprovação (liste-os);
   - galeria de prints sem diferença visual em relação à anterior (compare as imagens; diferença de pixels = 0 ou explicada);
   - auditor e contratos de LGPD sobre `data/publico/`: 0 achados;
   - **clone simulado** fora do OneDrive: os 4 caminhos do README de novo, com os tempos;
   - pacotes **regerados** em `C:\radar_pacotes\` (fora do OneDrive), com os tamanhos novos de cada camada;
   - banco real e Parquet intactos durante as suítes.
4. Atualizar o README (estrutura do projeto e tamanhos), `CONTRIBUTING.md` e `docs/publicacao.md`, se algo mudou.
5. Registrar a limpeza em `docs/diario.md` e as decisões D-031 e D-032 em `docs/decisoes.md`.

### ⛔ PARADA 2 — relatório final
1. O que foi feito, por área (movido, removido, mantido), com o espaço liberado.
2. As provas do item 3.4.3, uma por uma.
3. Tamanho final do repositório, do pacote público e do pacote da equipe (antes × depois).
4. O `git status` resumido e a sugestão de mensagem de commit.
5. O que eu faço em seguida (resumo do `docs/publicacao.md` atualizado).

**Nada de commit, push, merge ou Release. Não comece o Bloco 2.**
