# Plano de melhorias do painel: auditoria de UX, textos, mapas e visual

**Para:** a IA que vai corrigir o projeto (Claude Code, com acesso ao repositório `radar-seguro-cartorio`).
**Base da auditoria:** commit `bdf2bd2` da `main` (12/11/2026), painel rodado localmente em modo demonstração, fotografado em desktop (1440 px), celular (390 px) e tema escuro.
**Veredito atual:** engenharia de nível sênior; interface, textos e mapas de nível **pleno alto**. O objetivo deste plano é levar a parte visível ao nível dos melhores painéis de dados do Brasil (mapa de apuração do G1, Mapa Eleitoral, Resultados Eleições 2026, Solon Data), sem perder o que o projeto já faz melhor que eles: a incerteza explicada e a procedência de cada número.

---

## 0. Como usar este documento (leia antes de começar)

1. **Siga o `CLAUDE.md`.** Ele continua valendo: português, 100% gratuito, nenhum número fixo no código, nunca inventar dado, editar código só com a ferramenta de edição, testes numa cópia do banco, nenhum nome ou CPF de pessoa física.
2. **Registre a decisão.** Antes do primeiro bloco, crie a próxima decisão no registro de decisões do projeto (ex.: D-089, "Auditoria de UX de 12/11/2026"), aponte para este arquivo e copie-o para `docs/painel/auditoria_ux_2026-11-12.md`.
3. **Trabalhe em blocos, um pull request por bloco** (fluxo da D-073). A ordem está na seção 5. Cada bloco termina com os testes verdes, as capturas de tela da seção 6 e a atualização de `docs/ESTADO_ATUAL.md` e `docs/diario.md`.
4. **Cada item tem quatro partes:** *onde* (arquivo e função), *problema*, *correção* e *aceite*. Um item só está pronto quando o aceite é verdadeiro.
5. **Não mude números nem o modelo.** Este plano é só de apresentação: textos, layout, cores, mapa, gráficos e robustez da página. Se uma correção exigir dado novo (ex.: mapa municipal de outros estados), está marcada como **[precisa de dado]**: faça só se o pipeline já tiver o dado; senão, registre como pendência.
6. **Quando um item pedir uma escolha do autor**, está marcado como **[decisão do autor]**: implemente a opção recomendada e registre a escolha no diário, para o autor poder reverter.

---

## 1. Diagnóstico em uma página

| Área | Situação | Gravidade |
|---|---|---|
| Primeira visita mostra um erro técnico (traceback do DuckDB) | Corrida na montagem do banco de demonstração | **Crítica** |
| Mapa do Sudeste sem as divisas dos estados | Só o contorno externo da região é desenhado | **Crítica** |
| Termos internos na tela (D-0xx, commit, README, P5–P95, Monte Carlo, S1/S2, IS) | Textos de desenvolvimento vazando | **Alta** |
| Cor do "zero" mais escura que as primeiras faixas | Ordem visual invertida no mapa | **Alta** |
| Página Brasil abre num indicador que só 4 UFs têm | 23 estados cinza na primeira vista | **Alta** |
| Seletor "Estado" muda de página para página; link `?estado=` inconsistente | Navegação imprevisível | **Alta** |
| Funil do Início mistura cartórios e reais na mesma régua | Gráfico induz comparação errada | **Alta** |
| Tooltip do mapa é o nativo do navegador (só o nome, não existe no celular) | Interação abaixo das referências | Média |
| Sem busca de município no mapa | Abaixo das referências | Média |
| Títulos de gráfico quebrados em 3 linhas numa coluna estreita | Aparência amadora | Média |
| Tabelas esticadas, sem ordenação nem barras | Aparência padrão do Streamlit | Média |
| Nome do produto não aparece no topo; favicon é emoji | Identidade fraca | Média |
| Menu do celular vira um "»" sem rótulo | Navegação escondida | Média |
| Mesmo conceito com vários nomes | Confunde o leitor | Média |
| "Atualizado em" só na página Brasil | Falta sinal de atualidade | Média |

**O que manter (não mexer sem motivo):** a paleta sequencial do mapa (família YlGnBu, segura para daltonismo) e a versão escura dela; a separação entre "zero" e "sem dado"; a frase-resumo acima do mapa; o cartão-resposta do Início; os selos "Calibrado" e "Estimativa preliminar"; o gráfico da faixa provável; o gráfico de sensibilidade (tornado); o quadro de calor taxa × adesão (o melhor gráfico do painel); as sugestões de perguntas ao chat no fim de cada página; o botão de tema; as fontes embutidas.

---

## 2. Regras de texto e glossário único (valem para todas as telas)

O público é qualquer pessoa: titular de cartório, jornalista, corretor, servidor. A regra é: **um conceito, um nome, em todas as telas, no chat e nos gráficos.**

### 2.1 Glossário obrigatório

| Use sempre | Nunca use na interface | Observação |
|---|---|---|
| cartório(s) | serventia(s) | "serventia extrajudicial" pode aparecer uma vez na Metodologia, como definição |
| cartórios obrigados (à garantia) | obrigadas, universo | o substantivo é "cartório", masculino |
| dívida trabalhista | passivo, passivo trabalhista | "passivo" só na Metodologia, como sinônimo explicado |
| falta cobrir (déficit) | déficit de cobertura sozinho, sem explicação | na primeira aparição de cada página: "falta cobrir (déficit)" com dica explicando |
| valor segurado | IS, importância segurada | |
| prêmio anual | prêmio emitido sem contexto | |
| faixa provável | P5–P95, P10–P90, intervalo | a dica pode dizer "9 em cada 10 simulações" |
| simulações | Monte Carlo, sorteios | |
| semestre | S1/S2 | |
| sem titular (interino) | vago, VAGO | |
| estimativa | modelo, suposição do modelo (no corpo do texto) | "suposição" fica para as premissas sem fonte, que é o termo certo |
| dados de DD/MM/AAAA | carga, Carga 2026-11-12 · demonstração | |
| Pergunte à IA (menu e título iguais) | "Pergunte ao painel" num lugar e "Pergunte à IA" no outro | |

### 2.2 O que nunca aparece para o público

Códigos de decisão (`D-0xx`), `commit`, `README`, "Como rodar", "modo demonstração", "cópia do repositório", "Release", "a publicação mensal não respondeu", "premissas v4", nomes de tabela ou de arquivo, nomes de variável. **Lugar desses detalhes:** a página Sobre os dados, dentro de um bloco recolhido "Detalhes técnicos" no fim da página.

Ocorrências encontradas (corrija todas e procure outras com `grep`):

- `app/comum.py:78` e `app/comum.py:101-102`: "Modo demonstração… veja 'Como rodar' no README" (aparece em Simule, Sobre os dados e Pergunte à IA).
- `app/comum.py:221`: "Classificação de classe sempre aproximada (D-002)".
- `app/paginas/7_Brasil.py:37`: "A publicação mensal não respondeu agora; os números são da cópia guardada no repositório."
- `src/painel/brasil.py:78` e `:108`: o texto "cópia do repositório (data/brasil)" que vira o chip "Origem".
- `app/paginas/4_Sobre_os_dados.py:51`, `:55`, `:72`, `:75`: "D-088", "P5 a P95", "commit … do repositório", "(D-038)".
- `app/paginas/6_Explorar.py:158`, `:186`, `:190`, `:196`, `:262`, `:269`, `:335`, `:395`: "D-049", "D-016", "S1/S2", "D-046", "D-017", "README", "Monte Carlo".
- `src/painel/graficos.py:192`, `:199`, `:270`, `:279`: "P5–P95" e "P10–P90" em subtítulos e dicas.
- `src/painel/analises.py:30`, `:38`, `:116`: "faixa provável (P5–P95)", "O Monte Carlo…", "IS do mercado". Atenção: `analises.py` também alimenta o chat; troque o rótulo exibido sem quebrar as chaves internas nem o gabarito da avaliação (`eval/`). Rode a suíte do chat depois.

### 2.3 Regras de redação

- Títulos dizem a conclusão, não o tipo de gráfico ("Poucos cartórios precisam de garantia" e não "Funil").
- Frases curtas, voz ativa, sem siglas sem explicação na primeira vez.
- Botões começam com verbo ("Ver o Brasil inteiro", "Copiar link").
- Números sempre com unidade: "R$ 0" e não "0 mil"; "R$ 400 mil" e não "400 mil".
- Cada página mostra a data dos dados (seção 3.6).

**Aceite da seção 2:** um teste novo (ex.: em `tests/test_auditoria_painel.py`) renderiza todas as páginas em modo demonstração e falha se o texto visível contiver qualquer um destes padrões: `D-0\d\d`, `README`, `commit`, `Como rodar`, `P5`, `P10`, `P90`, `P95`, `Monte Carlo`, `S1/S2`, `IS do`, `serventia` (fora da Metodologia), `cópia do repositório`, `Release`. O conteúdo do bloco "Detalhes técnicos" fica fora da checagem.

---

## 3. Problemas transversais (valem para várias páginas)

### 3.1 Erro técnico na primeira visita — **P0**

- **Onde:** `src/publico.py`, `banco_demonstracao()` e `montar_banco()`.
- **Problema:** duas sessões que abrem ao mesmo tempo (o que acontece quando o Streamlit Cloud acorda o app) montam o mesmo arquivo temporário `radar_demonstracao_<chave>.duckdb.novo`. A segunda falha com `_duckdb.CatalogException: Table "fato_mercado_uf" already exists`, e o traceback inteiro aparece na tela.
- **Correção:**
  1. Nome temporário único por processo e chamada: `destino.with_name(f"{destino.name}.{os.getpid()}.{uuid.uuid4().hex}.novo")`.
  2. Depois de montar, `os.replace(temp, destino)` (atômico). Se `destino` já existir quando terminar, apague o temporário e use o existente.
  3. Opcional, sem dependência nova: uma trava com `os.open(trava, os.O_CREAT | os.O_EXCL)`, espera curta e nova tentativa, para só um processo montar por vez.
  4. Na página, nenhum erro técnico chega ao visitante. Em `.streamlit/config.toml`, seção `[client]`, desligue os detalhes de erro (`showErrorDetails`; confira na documentação da versão 1.66 do Streamlit o valor aceito, ex.: `"none"`). Em `app/comum.py`, envolva a abertura do banco e mostre uma mensagem amigável: "Os dados estão sendo preparados. Recarregue a página em alguns segundos."
- **Aceite:** um teste abre `banco_demonstracao()` em 4 threads ou processos ao mesmo tempo, numa pasta temporária, e todos recebem o mesmo caminho sem erro. Nenhuma página mostra traceback mesmo com o banco ausente.

### 3.2 Seletor "Estado" e link compartilhável — **P0**

- **Onde:** `app/comum.py`: `escopo()`, `seletor_escopo()`, `pagina()`.
- **Problemas:**
  1. O seletor tem "Sudeste" no Início e em Onde está o mercado, e não tem em Quão certo é, Para onde vai, Simule e Sobre os dados. O controle muda de forma de uma página para outra.
  2. O mesmo endereço `?estado=MG` abriu ora em MG, ora em Sudeste. `escopo()` apaga o parâmetro do endereço depois de ler (`del st.query_params["estado"]`), e o estado da sessão compete com o padrão da página.
- **Correção:**
  1. **Mesmo seletor em todas as páginas**, sempre com Sudeste, MG, SP, RJ, ES (e as próximas UFs quando entrarem). Nas páginas sem visão somada, "Sudeste" mostra **os estados lado a lado**: em Quão certo é, quatro faixas prováveis empilhadas; em Para onde vai, uma linha por estado; em Simule, um aviso curto ("O simulador funciona um estado por vez") com os quatro botões de estado logo abaixo. Não desabilite a opção.
  2. **O endereço é a verdade.** Ao escolher um estado, grave `st.query_params["estado"]`, e mantenha o parâmetro no endereço. Ao abrir uma página, o parâmetro vence a sessão e o padrão. O mesmo vale para o indicador do mapa (`?indicador=`) e o município selecionado (`?municipio=<código IBGE>`), para o link reproduzir a vista.
  3. Adicione um botão "Copiar link desta vista" no cabeçalho de cada página.
- **Aceite:** no teste de navegador, abrir `/Onde_está_o_mercado?estado=MG&indicador=pct_obrigados` dez vezes seguidas sempre mostra MG e o indicador pedido; trocar de página mantém o estado; o seletor tem as mesmas opções em todas as páginas.

### 3.3 Cabeçalho, marca e favicon — **P1**

- **Onde:** `app/Inicio.py` (`st.logo`, `st.navigation`), `app/comum.py:pagina()` (recebe o ícone "📊"), `app/static/marca.svg`.
- **Problemas:** o topo só tem o ícone; o nome do produto não aparece. O ícone da aba do navegador é um emoji.
- **Correção:**
  1. Logo com o nome: crie `app/static/marca_nome.svg` (ícone + "Radar Seguro Cartório" em IBM Plex Sans 600) e use em `st.logo(..., size="large")`; mantenha `marca.svg` como `icon_image` para a versão recolhida.
  2. `page_icon` de todas as páginas aponta para `app/static/marca.svg` (ou um PNG 64×64 gerado dele), não para emoji.
  3. Título da aba do navegador: "Radar Seguro Cartório · <página>".
- **Aceite:** em 1440 px e em 390 px, o nome do produto é legível no topo; nenhuma página usa emoji como ícone.

### 3.4 Menu no celular e organização das páginas — **P1**

- **Onde:** `app/Inicio.py`, `st.navigation([...], position="top")`.
- **Problema:** com 8 páginas, o menu do topo não cabe e o Streamlit o recolhe num "»" sem rótulo no celular.
- **Correção [decisão do autor]:** agrupe as páginas em seções do `st.navigation` (dicionário de seções), que o Streamlit mostra como menus suspensos no topo. Confira se a versão 1.66 faz isso no modo `top`. Proposta:
  - **Início**
  - **Mapas:** Onde está o mercado · Brasil
  - **O número:** Quão certo é · Para onde vai
  - **Ferramentas:** Simule · Pergunte à IA
  - **Sobre os dados**
  Se a versão não suportar seções no topo, reduza os rótulos ("Mercado", "Brasil", "Incerteza", "Projeção", "Simule", "IA", "Dados") e garanta pelo CSS que o botão recolhido mostre o texto "Menu".
- **Aceite:** em 390 px, o visitante vê o texto "Menu" ou as seções; nenhuma página fica escondida atrás de um ícone sem rótulo.

### 3.5 Tema — **P2 [decisão do autor]**

- **Onde:** `src/painel/componentes/tema.js`, `.streamlit/config.toml` (o comentário diz que o padrão é o claro).
- **Problema:** com o sistema em modo escuro, o painel abre claro.
- **Correção recomendada:** padrão "Sistema" para quem nunca escolheu; a escolha explícita continua gravada.
- **Aceite:** num navegador com `prefers-color-scheme: dark` e sem escolha gravada, o painel abre escuro e o botão "Sistema" aparece marcado.

### 3.6 Data dos dados em todas as páginas — **P1**

- **Onde:** `app/comum.py:pagina()` e `src/painel/ui.py:contexto()`.
- **Problema:** só a página Brasil mostra "Atualizado em". As outras mostram "Carga 2026-11-12 · demonstração" (Pergunte à IA) ou nada.
- **Correção:** todo cabeçalho de página ganha um chip "Dados de 12/11/2026", tirado do manifesto do conjunto público, com a dica "Cadastro do CNJ de 17/10/2026; RAIS de 31/12/2025". Na página Brasil, o chip "Origem" sai da vista principal e vai para "Detalhes técnicos".
- **Aceite:** todas as páginas mostram a data no cabeçalho, no mesmo lugar e no mesmo formato DD/MM/AAAA.

### 3.7 Gráficos Plotly: títulos, eixos e unidades — **P1**

- **Onde:** `src/painel/graficos.py`: `_linhas()`, `_fig()`, `faixa_premio()`, `tornado()`, `projecao_premio()`, `funil()`.
- **Problemas:**
  1. `_fig()` quebra o título e o subtítulo à mão com `_linhas(texto, n)`, num número fixo de caracteres. Num cartão de 1.300 px, o título ocupa 3 linhas num terço da largura e deixa o resto vazio.
  2. O eixo de Para onde vai mostra "0 mil", "100 mil", sem "R$".
  3. A fonte do título dos gráficos (Newsreader, serifada) difere do título da página (IBM Plex Sans).
- **Correção:**
  1. Quebre o título só acima de ~90 caracteres, ou deixe a largura do container decidir: título e subtítulo fora da figura, como HTML do cartão (via `ui.grafico`), e a figura sem `title`. Isso também melhora a leitura no celular.
  2. Formatação de eixo em reais por uma função única (`ticks_brl` já existe em `comum.py`): "R$ 0", "R$ 100 mil", "R$ 1,5 mi".
  3. **[decisão do autor]** Uma família só: IBM Plex Sans 600 também nos títulos dos gráficos.
- **Aceite:** em 1440 px, nenhum título de gráfico passa de 2 linhas; todo eixo de dinheiro tem "R$"; títulos de gráfico e de página usam a mesma família.

### 3.8 Tabelas — **P1**

- **Onde:** `src/painel/ui.py:tabela()` (HTML) e o CSS em `src/painel/estilo.css`.
- **Problemas:** colunas esticadas por toda a largura, com células enormes e vazias; "Posição" alinhada à direita, longe do nome; sem ordenação nem busca; nenhum número tem barra; tabelas longas (27 UFs, rankings) são só texto.
- **Correção:**
  1. Em `ui.tabela()`: aceite larguras por coluna (`<colgroup>`), com colunas numéricas estreitas e alinhadas à direita, a coluna de nome larga, e a posição ("1º") estreita à esquerda. Limite a largura máxima da tabela ao conteúdo (`width: auto; min-width: 60%`), não a 100% sempre.
  2. Parâmetro novo `barras={coluna}`: desenha uma barra fina proporcional dentro da célula (mesmo token de cor do mapa).
  3. Para tabelas com mais de 15 linhas (Todos os estados, rankings, lista de cartórios), use `st.dataframe` com `column_config` (`NumberColumn` com formato brasileiro, `ProgressColumn` para participação), que dá ordenação e busca prontas. Ajuste as cores pelo tema do `config.toml`.
- **Aceite:** nenhuma tabela tem coluna com mais de 3× a largura do conteúdo; as tabelas longas ordenam por clique; as colunas de participação têm barra.

### 3.9 Detalhes visuais — **P2**

- **Pergunte à IA:** o aviso "O chat está indisponível no momento" tem um retângulo interno de outra cor dentro da caixa azul (o parágrafo herda um fundo). Corrija no CSS (`.stAlert p { background: transparent; }` ou equivalente).
- **Cartões de KPI no celular:** em 390 px, a grade de 3 cartões vira 2 + 1 com um buraco cinza (Onde está o mercado). Use uma coluna só abaixo de ~480 px ou uma contagem de colunas que divida o número de cartões.
- **Contraste:** confira os tons `--mudo` e `--texto-2` sobre `--superficie` nos dois temas (mínimo 4,5:1 para texto pequeno). O teste `tests/test_cores.py` já existe; inclua estes pares.

---

## 4. O mapa (componente `src/painel/mapa.py` + `src/painel/componentes/mapa.js` + `mapa.css`)

O mapa é o centro do painel. Estas mudanças valem para as duas páginas que o usam (Onde está o mercado e Brasil).

### 4.1 Divisas dos estados — **P0**

- **Problema:** no recorte Sudeste, o componente desenha só o contorno externo da região (`.rd-contorno`, que é a mesma malha por baixo com traço grosso). Não dá para ver onde termina MG e começa SP, RJ ou ES.
- **Correção:**
  1. Em `mapa.py:dados_mapa()`, receba uma lista opcional `divisas` (geometrias das UFs do recorte). A malha das UFs já existe em `data/brasil/malha_uf.geojson`; projete-a com a mesma `Projecao` dos municípios.
  2. Em `mapa.js`, desenhe uma camada `g.rd-divisas` **acima** das áreas e abaixo dos rótulos, com `fill: none; stroke: var(--texto); stroke-width: 1.4; vector-effect: non-scaling-stroke; pointer-events: none`.
  3. Mantenha o contorno externo mais grosso (2,6) para a região.
  4. Quando um único estado está na tela, as divisas dos vizinhos aparecem em cinza claro (`--linha-2`), com o nome do vizinho, como contexto (como o G1 faz).
- **Aceite:** no recorte Sudeste, as quatro divisas são visíveis nos dois temas e em 390 px; o teste `tests/test_mapa_navegador.py` confere que a camada existe e não pega cliques.

### 4.2 Cores: zero, sem dado e faixas — **P0/P1**

- **Problema 1 (P0):** o token `--mapa-zero` (`#a9b0ab`) é mais escuro que `--mapa-1` (`#c3e6b4`) e `--mapa-2` (`#83cdb8`). O olho lê "mais escuro = mais", então os 689 municípios com zero parecem ter mais que os de R$ 150 mil, e dominam o mapa.
- **Correção:** o zero fica **mais claro** que a primeira faixa e sem matiz: um cinza bem claro (no claro, perto de `#ebede8`; no escuro, um tom pouco acima do fundo). "Sem cartório / sem dado" fica com **hachura também no mapa**, não só na legenda (hoje o mapa usa um tom chapado parecido com o zero). Ajuste os tokens em `src/painel/estilo.css` (linhas 33-35 e 55-56) e o `mapa.css`.
- **Aceite (teste em `tests/test_cores.py`):** nos dois temas, a luminância cresce monotonicamente de zero → faixa 1 → … → faixa 6 no sentido "mais = mais contraste com o fundo"; o zero é o mais próximo do fundo entre as cores com dado.

- **Problema 2 (P1):** `mapa.faixas()` usa faixas de largura igual (passo redondo até o percentil do teto). O déficit é muito concentrado (São Paulo tem 25% do Sudeste), e quase todos os municípios caem na primeira faixa: o mapa vira um "mar verde-claro".
- **Correção:** um parâmetro `metodo` em `faixas()`: `"quantil"` (faixas com o mesmo número de áreas, com limites arredondados para valores "bonitos") para indicadores em reais, e o atual para percentuais. Rótulos da legenda como intervalos ("R$ 50 a 150 mil"). A legenda mostra quantas áreas há em cada faixa (pequeno número abaixo da cor).
- **Aceite:** no indicador Déficit do Sudeste, nenhuma faixa com dado tem mais de 30% das áreas com valor positivo; os limites são valores redondos; `tests/test_mapa.py` cobre o método novo.

- **Problema 3 (P1):** a legenda não filtra.
- **Correção:** clicar numa cor da legenda destaca as áreas daquela faixa (as outras ficam a 20% de opacidade); clicar de novo desfaz. Faça no JS, sem recarregar a página.

### 4.3 Dica ao passar o mouse (tooltip) — **P1**

- **Problema:** a dica é o `<title>` do SVG: demora, mostra só o nome, não existe no celular. E cada clique recarrega a página do Streamlit antes de mostrar os números.
- **Correção:**
  1. Em `dados_mapa()`, inclua por área um objeto `dica` já formatado em Python (para não haver número calculado no JS): nome, UF, valor do indicador com unidade, posição ("3º de 1.666") e 2 ou 3 linhas extras (cartórios, cartórios obrigados, falta cobrir).
  2. Em `mapa.js`, um cartão flutuante (`div.rd-dica`) que segue o ponteiro (`pointermove`), fica dentro do mapa e nunca sai da tela; some no `pointerleave`. Com teclado: a área focada mostra a dica.
  3. No toque: o primeiro toque mostra a dica com um botão "Ver detalhes"; o botão faz a seleção (que hoje acontece no clique).
  4. Mantenha o `<title>` para leitores de tela.
- **Aceite:** passar o mouse mostra a dica em menos de 100 ms, sem recarregar a página; em 390 px, tocar mostra a dica e "Ver detalhes" seleciona.

### 4.4 Busca de município no mapa — **P1**

- **Problema:** a escolha de município é uma lista de seleção ("Município: Todos") num cartão separado, acima dos KPIs e longe do mapa.
- **Correção:** um campo "Buscar município" dentro da barra de controles do mapa (ao lado de +, − e "Ver o mapa inteiro"), com autocompletar sem acento e sem diferença de maiúsculas. Escolher um nome aproxima o mapa no município, seleciona-o e mostra a dica. Remova o cartão "Município" separado.
- **Aceite:** digitar "uber" sugere Uberaba e Uberlândia; escolher aproxima e seleciona; o cartão separado não existe mais.

### 4.5 Rótulos e zoom — **P2**

- Em larguras abaixo de 500 px, rótulos de estado só com sigla, com detecção de colisão (hoje "DF" encosta em "Minas Gerais" e "AL" fica cortado na borda).
- Rótulos de cidade nunca em cima de uma divisa ou do litoral (hoje "Rio de Janeiro" fica sobre a costa).
- Zoom pela roda do mouse com Ctrl/⌘ pressionado (para não sequestrar a rolagem da página) e pinça no celular quando o mapa já está aproximado.
- **Aceite:** em 390 px, nenhum rótulo se sobrepõe a outro nem sai da área do mapa.

---

## 5. Página por página

### 5.1 Início (`app/Inicio.py`)

**Manter:** o cartão-resposta com o valor, a faixa provável e a frase "9 em cada 10 simulações"; a tabela "Estado por estado" com os selos; as sugestões do chat.

**Problemas e correções:**

1. **Teste dos 5 segundos falha pela metade (P1).** O título é uma pergunta de duas linhas sobre "seguro obrigatório" e um provimento; só o subtítulo diz que se trata de cartórios.
   - **Correção:** eyebrow "RADAR SEGURO CARTÓRIO"; título curto com o assunto e o recorte: "Quanto o seguro obrigatório dos cartórios pode movimentar em Minas Gerais"; uma linha de contexto: "Desde o Provimento 227/2026 do CNJ, parte dos cartórios precisa garantir a dívida trabalhista com seus empregados. Esta é a estimativa desse mercado, com dados públicos." Mantenha a pergunta "e quão certo é esse número?" como título da seção do cartão-resposta.
   - **Aceite:** sem rolar, em 1440 px, aparecem o nome do produto, a palavra "cartórios", o valor e a data dos dados.
2. **Prêmio repetido (P2).** O sexto KPI ("Prêmio anual estimado") repete o cartão-resposta logo acima.
   - **Correção:** troque pelo KPI "Cartórios sem bens suficientes (≈ 148)", que hoje só aparece no funil.
3. **Funil mistura unidades (P0 de dataviz).** `graficos.funil()` põe cartórios e reais na mesma régua ("cada grupo na sua escala"): 2.525 cartórios e R$ 34,1 mi têm barras iguais. A barra "Prêmio anual" quase some e o rótulo diz "é o número acima".
   - **Correção:** dois gráficos lado a lado (uma coluna no celular):
     - **"De 2.525 cartórios, 148 precisam de seguro"**: cartórios ativos → obrigados → sem bens suficientes, em barras horizontais de contagem, com o percentual de cada passo.
     - **"De R$ 34,1 mi que falta cobrir, R$ 341 mil viram prêmio por ano"**: falta cobrir → vira seguro → prêmio anual, em reais, com escala logarítmica rotulada ou com o prêmio mostrado como "1% do valor segurado" num rótulo, nunca uma barra invisível.
   - **Aceite:** nenhum gráfico mistura unidades no mesmo eixo; todo valor tem barra visível ou rótulo explicando a proporção.
4. **Data dos dados** no cabeçalho (seção 3.6).

### 5.2 Quão certo é (`app/paginas/1_Quão_certo_é.py`)

**Manter:** o gráfico da faixa, o tornado e o quadro de calor taxa × adesão.

**Problemas e correções:**

1. **Seletor sem Sudeste (P0).** Veja a seção 3.2. No Sudeste, mostre as quatro faixas prováveis empilhadas no mesmo eixo, com o selo de cada estado.
2. **Siglas (P1).** O subtítulo diz "faixa provável (P5–P95) entre os extremos teóricos". Troque por "A faixa azul reúne 9 em cada 10 simulações; as pontas são os extremos, quando todas as suposições erram para o mesmo lado."
3. **KPI "O que vem de dado público: até 16,4%" (P2).** A frase é difícil. Reescreva: "Dívida trabalhista e número de cartórios obrigados mudam o prêmio em no máximo 16,4%."
4. **Tornado (P2).** Os nomes das suposições ficam acima das barras, desalinhados dos valores. Coloque o nome à esquerda, na mesma linha da barra; escreva "Chance de faltar bens (Classe 3)" em vez de "Chance de déficit (Classe 3)".

### 5.3 Onde está o mercado (`app/paginas/2_Onde_está_o_mercado.py`)

**Manter:** os três KPIs de concentração ("Só São Paulo: 25,0%", "Os 10 municípios com mais déficit: 50,4%", "977 de 1.666"); a frase-resumo do mapa; os três indicadores do mapa.

**Problemas e correções:**

1. **Divisas, zero, faixas, dica, busca:** seção 4 inteira. É a página onde isso mais aparece.
2. **Cartão "Município: Todos" isolado (P1):** substituído pela busca dentro do mapa (4.4).
3. **Layout (P1):** em 1440 px, o mapa ocupa o centro e sobra espaço dos lados. Use duas colunas: mapa à esquerda (~60%) e, à direita, o painel do município selecionado (ou, sem seleção, o ranking dos 10 maiores com barras). É o padrão das referências (mapa + lista lateral). No celular, a lista vai para baixo do mapa.
4. **Ranking (P1):** a tabela atual tem 4 colunas esticadas e "Posição" alinhada à direita. Use a tabela da seção 3.8 com barra na coluna "Parte do Sudeste".
5. **Frase final em texto corrido (P2):** "Parte de cada estado no déficit do Sudeste: São Paulo 67,4%; …". Troque por uma barra empilhada horizontal com os quatro estados, rotulada.
6. **Indicadores (P2):** renomeie os botões para o glossário: "Falta cobrir (R$)", "% obrigados", "% na Classe 3". A dica de "% na Classe 3" explica a classe em uma frase.

### 5.4 Para onde vai (`app/paginas/3_Para_onde_vai.py`)

**Manter:** os selos "PROJEÇÃO" e a frase que explica por que o prêmio quase não sobe.

**Problemas e correções:**

1. **Seletor sem Sudeste (P0):** seção 3.2. No Sudeste, uma linha por estado.
2. **Eixo (P1):** "0 mil", "100 mil" → "R$ 0", "R$ 100 mil". O subtítulo diz "faixa P10–P90": troque por "faixa provável".
3. **Título com prefixo em caixa alta (P2):** "PROJEÇÃO · Com a dívida trabalhista de hoje…". O selo já diz que é projeção; tire o prefixo do título.
4. **Página curta, com um gráfico só (P2):** acrescente um segundo gráfico com a evolução do número de cartórios obrigados (2025 → 2026 → 2027), que é o outro KPI da página.

### 5.5 Brasil (`app/paginas/7_Brasil.py`, `src/painel/brasil.py`)

**Manter:** a tabela das 27 UFs, os KPIs nacionais e o chip "Atualizado em".

**Problemas e correções:**

1. **Indicador inicial (P0).** `PREMIO = "Prêmio do seguro"` é o padrão do mapa (`default=PREMIO`, linha 55), mas só 4 UFs têm esse valor; 23 aparecem cinza na primeira vista, e a hachura de "só o cadastro" quase não se distingue do cinza.
   - **Correção:** o padrão passa a ser "Por 100 mil hab." (ou "Cartórios"), que cobre as 27 UFs. "Prêmio do seguro" continua como opção; quando escolhido, aparece uma faixa de aviso acima do mapa: "O estudo do seguro cobre, por enquanto, os 4 estados do Sudeste."
   - **Aceite:** a primeira vista da página Brasil tem as 27 UFs coloridas.
2. **Legenda com 7 faixas para 4 valores (P1):** quando o indicador tem menos de 8 áreas com valor, use no máximo 4 faixas ou rotule os valores direto no mapa.
3. **Textos de infraestrutura (P0):** "A publicação mensal não respondeu agora…" e o chip "Origem: cópia do repositório" saem da vista (seção 2.2). Se a Release mais recente não respondeu, o chip de data mostra a data da cópia e pronto.
4. **Rótulos (P1):** os nomes misturam nome completo e sigla. Em 1440 px, use siglas em todos os estados (como as referências) e o nome completo na dica. Corrija a colisão DF/Minas Gerais e o "AL" cortado.
5. **Tabela "Todos os estados" (P1):** `st.dataframe` com ordenação, barra em "Por 100 mil hab." e em "Sem titular", e o nome da coluna "UF" trocado por "Estado".
6. **Clique no estado (P2) [precisa de dado]:** hoje o clique mostra os números do estado. Nas referências, o clique abre o mapa dos municípios. Se o pipeline do Brasil já coleta o município de cada cartório, gere `data/brasil/brasil_municipio.csv` (contagens por município) e abra o mapa municipal do estado clicado com os mesmos indicadores de cadastro. Senão, registre como pendência no plano do projeto.

### 5.6 Simule (`app/paginas/6_Explorar.py`)

**Manter:** as perguntas prontas no topo ("E se a taxa fosse 3%?"), o cartão-resposta e a frase "Escada".

**Problemas e correções:**

1. **Jargão (P0):** "S1/S2", "Monte Carlo", "D-016", "D-017", "D-046", "D-049", "README". Seção 2.2. O interruptor "Faixa por sorteio (Monte Carlo)" vira "Calcular a faixa provável".
2. **Rótulos dos controles (P1):** "Escolhe o seguro-garantia (% do déficit)" e "Escolhe a fiança bancária" → "Parte que contrata seguro-garantia" e "Parte que usa fiança bancária". "Regulariza com bens próprios: 30% (o restante…)" vira uma barra empilhada de 3 partes (seguro, fiança, bens próprios) que se atualiza com os controles.
3. **Hierarquia (P1):** a seção "Mercado total e uma seguradora hipotética" tem 12 números grandes do mesmo tamanho. Use uma tabela de duas colunas (Mercado total · Seguradora hipotética) com 6 linhas, e destaque só "Prêmio" e "Resultado técnico".
4. **Botões das perguntas prontas (P2):** estão centralizados em botões largos com muito espaço vazio. Use pílulas do mesmo estilo das sugestões do chat.
5. **Seletor (P0):** seção 3.2.

### 5.7 Sobre os dados (`app/paginas/4_Sobre_os_dados.py`)

**Manter:** "Os 10 números oficiais", "Fontes e datas", "Saúde dos dados", "Principais limitações". É a página que mais diferencia o projeto das referências.

**Problemas e correções:**

1. **Nomes fora do glossário (P1):** "Serventias ativas" → "Cartórios ativos"; "Passivo trabalhista" → "Dívida trabalhista"; "IS do mercado" → "Valor segurado do mercado"; "Com déficit (esperado)" → "Cartórios sem bens suficientes (esperado)".
2. **Coluna "Origem" (P2):** os valores "dado público" e "suposição do modelo" viram selos coloridos (os mesmos de "Calibrado" e "Estimativa preliminar"), para ver de longe quais números são estimados.
3. **"Detalhes técnicos" recolhido (P1):** vão para dentro dele: versão das premissas, peso dos cartórios de classe indeterminada, "Versão do código (commit)", o texto da D-038, "Carga dos dados", o modo demonstração e o "Como rodar". Esta é a única área da interface onde esses termos podem aparecer.
4. **"Faixa provável: P5 a P95 de 200.000 simulações" (P1):** "Reúne 9 em cada 10 de 200.000 simulações das suposições".

### 5.8 Pergunte à IA (`app/paginas/5_Chat.py`)

**Manter:** as duas abas (Chat e Perguntas prontas) e a mensagem honesta quando o chat está fora.

**Problemas e correções:**

1. **Nome (P1):** o menu diz "Pergunte à IA" e o título diz "Pergunte ao painel". Use o mesmo nome nos dois.
2. **Chips (P1):** "Dados: Carga 2026-11-12 · demonstração" e "Premissas: v4" → um chip "Dados de 12/11/2026" (seção 3.6).
3. **Subtítulo (P2):** "serventias, passivo, déficit…" → "cartórios, dívida trabalhista, o que falta cobrir, o prêmio, projeções e as normas".
4. **Aviso com fundo duplo (P2):** seção 3.9.
5. **Quando o chat está fora (P2):** mostre logo abaixo do aviso 3 perguntas prontas clicáveis, em vez de mandar o visitante procurar a outra aba.

---

## 6. Ordem de execução (um pull request por bloco)

| Bloco | Conteúdo | Itens |
|---|---|---|
| **1. Robustez** | Erro da primeira visita, nenhum traceback na tela | 3.1 |
| **2. Textos** | Glossário, remoção de jargão, teste de texto proibido, "Detalhes técnicos", nomes do menu | 2, 5.6.1, 5.7.1, 5.7.3, 5.7.4, 5.8.1-3 |
| **3. Navegação** | Seletor igual em todas as páginas, endereço como verdade, copiar link, data dos dados | 3.2, 3.6 |
| **4. Mapa I** | Divisas, cor do zero e hachura, indicador inicial do Brasil | 4.1, 4.2 (problema 1), 5.5.1, 5.5.3 |
| **5. Mapa II** | Dica própria, busca, faixas por quantil, legenda que filtra, layout mapa + lista | 4.2 (problemas 2 e 3), 4.3, 4.4, 5.3.2-4 |
| **6. Gráficos** | Funil em dois gráficos, títulos, eixos com R$, fonte única | 3.7, 5.1.3, 5.4.2-3 |
| **7. Tabelas e visões do Sudeste** | Tabelas novas, Sudeste nas páginas sem visão somada | 3.8, 5.2.1, 5.4.1, 5.5.5 |
| **8. Identidade e celular** | Logo com nome, favicon, menu em seções, rótulos do mapa no celular, KPIs no celular | 3.3, 3.4, 3.9, 4.5 |
| **9. Acabamento** | Itens P2 restantes, tema "Sistema", segundo gráfico de Para onde vai, Simule | 3.5, 5.1.2, 5.2.3-4, 5.3.5-6, 5.4.4, 5.6.2-4, 5.8.5 |
| **10. Brasil municipal** [precisa de dado] | Mapa municipal das outras UFs | 5.5.6 |

---

## 7. Verificação ao fim de cada bloco

1. `uv run pytest` verde, inclusive `tests/test_mapa_navegador.py`, `tests/test_visual.py`, `tests/test_cores.py` e os testes de acessibilidade (axe) que o projeto já tem.
2. Os testes novos pedidos neste plano: corrida do banco (3.1), link `?estado=` (3.2), texto proibido (2), ordem de luminância das cores (4.2), divisas presentes (4.1).
3. Capturas de tela de todas as páginas em três configurações: 1440 × 900 tema claro, 1440 × 900 tema escuro, 390 × 844 tema claro. Salve em `docs/img/auditoria/<bloco>/` e confira à vista:
   - nenhum traceback, nenhum termo proibido;
   - nenhum rótulo sobreposto ou cortado;
   - nenhuma tabela ou página com rolagem lateral em 390 px;
   - o nome do produto e a data dos dados visíveis no topo;
   - as divisas dos estados visíveis no mapa.
4. **Teste dos 5 segundos** (manual, na captura do Início em 1440 px, sem rolar): dá para responder "do que é este painel?", "qual o número principal?" e "de quando são os dados?".
5. A avaliação do chat (`scripts/avaliar_chat.py`) só precisa rodar se o bloco mexer em `src/painel/analises.py`; nesse caso, o acerto não pode cair.

---

## 8. Referências para comparar (abra e use como padrão)

1. Mapa Eleitoral: https://www.mapaeleitoral.com.br/?cidade=rio&ano=2026&turno=1&cargo=GOVERNADOR&partido=PL&candidato=DOUGLAS+RUAS
   O que copiar: filtros fixos no topo, "Buscar no mapa", "Compartilhar", mapa por bairro.
2. G1, mapa de apuração: https://g1.globo.com/politica/eleicoes/2026/mapas/mapa-de-apuracao/presidente/brasil.ghtml
   O que copiar: placar resumido acima do mapa; clique no estado abre os municípios; busca de cidade; dica com os números; "atualizado às" sempre visível; divisas nítidas.
3. Solon Data: https://www.solondata.com/eleicoes-2026?estado=mg
   O que copiar: o estado no endereço (`?estado=mg`), mapa + gráficos + tabela na mesma vista.
4. Resultados Eleições 2026: https://resultadoseleicoes2026.com.br/mapa?view=2d
   O que copiar: modos do mapa com nomes de pergunta ("Quem lidera", "% apurado"); "Compartilhar no WhatsApp" e "Copiar link"; lista lateral por região que acompanha o mapa.
   O que **não** copiar: o banner de um contexto (2º turno) sobre um mapa de outro (1º turno). O equivalente aqui seria abrir a página Brasil num indicador que só o Sudeste tem.

O que o Radar já faz melhor que as quatro e deve manter em destaque: a faixa provável, o que mais pesa na incerteza, a procedência de cada número e o chat que só responde com dado do painel.
