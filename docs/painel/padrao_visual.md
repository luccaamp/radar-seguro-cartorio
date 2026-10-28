# Padrão visual do painel (Etapa 3)

28/10/2026 · Fase 3 da Etapa 3. Tema em `.streamlit/config.toml`; estilo único em `src/painel/estilo.css`; componentes em `src/painel/ui.py`; template e gráficos em `src/painel/graficos.py`.

## 1. Diagnóstico do design anterior

Capturas em `docs/qa/painel/antes/` (53 estados, 1280 e 1920 px, `scripts/prints_painel.py`; galeria em `galeria.html`).

| Problema | Onde | Exemplo |
|---|---|---|
| **Hierarquia:** nenhuma manchete; a página abre com um parágrafo jurídico de 4 linhas e o número principal (prêmio) aparece no meio, do mesmo tamanho dos outros | Início | `01_inicio_1280.png` |
| **Faltam números:** o Início mostra 5 dos 10 números; déficit e teto vão em texto corrido; IS e "com déficit" não aparecem; nenhuma faixa P5–P95 (D-042) | Início | `01_inicio_1280.png` |
| **Faixa errada como principal:** "faixa R$ 20,7 a 79,0 mi" (cantos) é a única incerteza mostrada, contra a D-042 | Início, Mercado | `01_inicio_1280.png`, `02_mercado_deficit_1280.png` |
| **Espaçamento:** KPIs soltos, sem cartão; 3 colunas com a terceira vazia; caixa azul de aviso compete com os números | Início, Mercado | — |
| **Cores:** azul de alerta do Streamlit (`st.info`) usado para texto institucional; botão de rádio vermelho padrão; nenhuma cor tem significado fixo (observado × projeção) | todas | — |
| **Gráficos:** barras de ranking sem eixo, rótulos minúsculos (≈ 9 px); só 3 gráficos no painel, nenhum das análises dos notebooks 03 a 10 | Mercado, Qualidade | `02_mercado_deficit_1280.png` |
| **Densidade:** rodapés de fonte com 4 a 5 linhas em cinza claro, repetidos; tabelas largas com 7 colunas | todas | `10_qualidade_topo_1280.png` |
| **Tipografia:** fonte padrão do Streamlit, título h1 enorme e texto corrido do mesmo peso; legendas em `st.caption` com contraste baixo (limitação já registrada em 19/10) | todas | — |
| **Coerência:** cada página tem um cabeçalho diferente ("Mercado — Minas Gerais", "Simulador — ...", "Qualidade dos dados"); sem estado visível do contexto (carga, premissas, cenário) | todas | — |
| **Dados desatualizados na tela:** ADI 8015 "conferido em 17/10/2026" escrito no código | Início | `01_inicio_1280.png` |

## 2. Direção visual

**Sóbrio e editorial, com cara de relatório de consultoria:** fundo off-white, cartões brancos com borda fina, muito respiro, uma cor de destaque (azul-marinho) e números grandes. Cada página abre com uma manchete que diz a conclusão em uma frase, com o número dentro dela. A cor é reservada para significado (observado, projeção, suposição), nunca para decorar.

Por quê: o público (banca, gestores de seguradora, leigos) precisa ler o essencial em segundos e confiar no número; o tom editorial deixa a incerteza visível sem alarme, e o painel continua legível em projetor e em notebook de 1366 px.

## 3. Paleta

| Papel | Cor | Uso |
|---|---|---|
| Fundo | `#f7f7f5` | plano da página |
| Superfície | `#ffffff` | cartões, gráficos, tabelas |
| Texto | `#1b1b19` / secundário `#52514e` / mudo `#6b6964` | texto e eixos (o texto nunca usa a cor da série) |
| Destaque | `#184f95` | sobretítulo, borda dos cartões de achado, links |
| **Observado / valor base** | `#2a78d6` | dado, número oficial, realizado |
| **Projeção** | `#eb6834` | toda projeção 2026–27 (linha tracejada) |
| **Faixa de incerteza** | azul a 16% (P5–P95) · laranja a 16% (P10–P90 da projeção) | banda sombreada |
| **Suposição / sensibilidade** | `#6250d6` | resultado que depende de suposição; sensibilidades |
| **Extremos e comparação** | `#898781` | extremos teóricos, leitura de comparação (05b, limite corrigido): sempre em tom secundário |
| **Alerta** | `#d03b3b` (texto `#b42f2f`) | sempre com ícone e palavra, nunca só a cor |

**Validação para daltonismo:** azul, laranja e violeta passaram em todas as checagens do script da skill de visualização (`validate_palette.js`, modo claro, superfície `#ffffff`): banda de luminosidade, croma, separação para daltonismo (pior par ΔE 24,7, protan), piso de visão normal (33,6) e contraste ≥ 3:1. O cinza de comparação é neutro e sempre vai com segunda codificação (tracejado ou marcador vazado). Os selos usam texto escuro sobre fundo claro (contraste ≥ 4,5:1).

## 4. Tipografia

Fonte **Inter** (Google Fonts, carregada pelo tema; sem internet, o navegador cai para a sans do sistema).

| Nível | Tamanho / peso |
|---|---|
| Sobretítulo da página | 0,78 rem, 600, caixa alta, azul-marinho |
| Título (h1) | 2,05 rem, 700 |
| Manchete | 1,12 rem, 400, com o número em negrito |
| Seção (h2) | 1,35 rem, 650 |
| KPI | 1,55 rem, 700 (cartão D-042: 1,85 rem) |
| Texto | 1 rem, 400 |
| Nota e rodapé | 0,74–0,8 rem, cinza mudo |

## 5. Espaçamento e grade

Largura máxima do conteúdo 1.240 px, margens laterais de 2 rem; espaço entre seções de ≈ 1,8 rem; cartões em grade CSS de 2 a 5 colunas, que passa a 3 colunas abaixo de 1.100 px e a 1 coluna abaixo de 760 px (sem rolagem horizontal em 1.366 px). Raio de 10 px nos cartões e de 8 px nos controles.

## 6. Componentes (`src/painel/ui.py`)

- `cabecalho(sobre, titulo, manchete)`: sobretítulo, título e manchete de 10 segundos.
- `contexto()`: faixa de chips com o estado fixo (carga, premissas, regra de classe, nível, cenário do STF, modo).
- `kpi(...)`: cartão simples com rótulo, valor, selo (dado / suposição) e nota.
- `kpi_d042(resultado)`: **D-042** — valor base em destaque; logo abaixo, a "faixa provável (P5–P95)" com o subtítulo "faixa dentro das suposições"; depois, os "extremos teóricos" em nota secundária; as sensibilidades ficam num expansor próprio da página.
- `kpi_projecao(...)` e `kpi_comparacao(...)`: projeção (borda laranja, selo "projeção") e comparação (cinza, menor).
- `achado(titulo, texto, tipo)`: cartão de destaque com borda à esquerda.
- `selo(texto, tipo)`: "dado", "suposição", "projeção", "faixa provável", "sensibilidade", "comparação", "alerta".
- `fonte(resultado)`: rodapé curto de fonte, carga e versão das premissas de cada bloco; o rodapé longo da página (`comum.rodape`) continua no fim.
- `baixar(resultado, nome)`: download do CSV agregado de cada gráfico, com fonte, carga e premissas nas colunas.

## 7. Template Plotly (`graficos.py`, template `radar`)

Fonte Inter; grade horizontal de 1 px; título em negrito que diz a conclusão e subtítulo com o que está plotado e a unidade; rodapé com fonte, carga e versão das premissas dentro da figura; separadores `,.` (formato brasileiro) e textos de hover já formatados (`R$ 341,1 mil`, `≈ 1.204`, `45,1%`); banda sombreada para a incerteza; projeção em linha tracejada laranja com a palavra "PROJEÇÃO" no título; sem 3D, sem pizza, sem eixo duplo; legenda abaixo do gráfico quando há duas séries ou mais.

## 8. CSS e dependências

- Um só arquivo, `src/painel/estilo.css`, injetado por `ui.estilo()` no início de cada página (o Streamlit refaz a página a cada interação, então o carregamento é por página, mas o arquivo é um só e nenhuma página tem CSS próprio). O tema do Streamlit (`.streamlit/config.toml`) cuida das cores base, da fonte e do raio.
- **Nenhuma biblioteca nova de interface.** Alternativas consideradas: `streamlit-extras` e `streamlit-elements` (componentes prontos de cartão). Descartadas: o ganho era pequeno diante de HTML + CSS próprios, que já dão o cartão da D-042, e cada componente de terceiros é uma dependência a manter e um risco de quebrar com a versão do Streamlit.
- **Modo escuro:** fora desta etapa (o tema é só claro). Motivo: o painel é apresentado em projetor e notebook claros; o modo escuro exigiria validar a paleta também na superfície escura. Fica como melhoria.
