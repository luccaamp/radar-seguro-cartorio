# Padrão visual do painel (Etapa 3)

**Terceira rodada, 29/10/2026 (D-051).** Tema em `.streamlit/config.toml`; estilo único em `src/painel/estilo.css`; componentes em `src/painel/ui.py`; template e gráficos em `src/painel/graficos.py`. Capturas antes × depois em `docs/qa/painel/rodada3_antes/` e `docs/qa/painel/rodada3_depois/`. As rodadas anteriores estão no histórico do git (`git log -- docs/painel/padrao_visual.md`).

## 1. O problema da segunda rodada

| Problema | Exemplo (rodada3_antes) |
|---|---|
| Faixa azul-escura em todo o topo, com 6 etiquetas técnicas (carga, premissas, Classe 1, nível, STF, UF) | `01_inicio_1366.png` |
| Informação demais: 10 cartões + 3 cartões D-042 + ADI + glossário no Início; os 3 cartões D-042 repetidos na Análises | `01_inicio_1366.png`, `11_analises_incerteza_1366.png` |
| Abas da Análises sem cara de aba (texto solto sobre o fundo) | `11_analises_incerteza_1366.png` |
| Mapa espremido em 3/5 da largura, entre filtros, KPIs, tabela de extremos e ranking | `02_mercado_deficit_1366.png` |
| Termos técnicos na tela principal: `gold.analise_...`, D-042, notebook 07, "premissas v3" | rodapés de todas as páginas |
| Selo colorido "VALOR BASE"/"DADO"/"SUPOSIÇÃO" em todos os cartões | `01_inicio_1366.png` |

## 2. Direção

Painel de produto (referência: Stripe, Linear, Optimizely): muito branco, hierarquia pelo tamanho da fonte, **uma** cor de destaque usada só onde importa (o número principal, o item ativo da navegação e a série principal dos gráficos), nada de blocos grandes de cor. Por quê: a pergunta do painel tem uma resposta (um número); qualquer cor fora dele compete com ele.

## 3. Paleta

| Papel | Cor | Por quê |
|---|---|---|
| Fundo da página | `#f7f8fa` | cinza muito claro: separa os cartões brancos sem borda pesada |
| Superfície (cartões, gráficos, tabelas) | `#ffffff`, borda `#e5e7eb`, sombra `0 1px 2px rgba(16,24,40,.04)` | borda fina e sombra mínima, como nos painéis de produto |
| Título | `#111827` | quase preto: a hierarquia vem do tamanho, não da cor |
| Texto / secundário / mudo | `#1f2937` / `#4b5563` / `#6b7280` | todos ≥ 4,5:1 sobre o branco e o fundo (WCAG AA) |
| **Destaque** | `#3366e6` (claro `#eef3fd`, escuro `#2450c4`) | mais leve que o azul-marinho anterior (`#1f4e86`); 5,0:1 sobre o branco, serve também para texto |
| **Comparação** (só em gráficos) | `#e08a1e` | contrasta com o destaque em cor e em escala de cinza (111 × 156 de 255) |
| Degraus neutros e extremos | `#cbd2dc`, `#9ca3af` | o que leva à resposta fica cinza; só o último degrau (o prêmio) leva o destaque |
| Faixa de incerteza | destaque a 16% | a mesma cor da série, mais clara |
| Mapa (sequencial, um tom) | `#eef3fd` → `#183a8f` (7 passos) | claro = pouco déficit, escuro = muito |

**Validação:** destaque e comparação passaram nas checagens do `validate_palette.js` da skill de visualização (modo claro: banda de luminosidade, croma, separação para daltonismo ΔE 33,2 protan, piso de visão normal 38,1). O âmbar fica abaixo de 3:1 de contraste com o branco: por isso toda barra âmbar tem o rótulo direto (valor na ponta), nunca só a cor. Em escala de cinza, o destaque fica em 111 e o âmbar em 156 (de 255): dá para separar sem cor. Um âmbar mais escuro (`#c26a12`) passaria no contraste, mas ficaria em 128 na escala de cinza, perto demais do azul.

## 4. Tipografia (Inter)

| Nível | Tamanho / peso |
|---|---|
| Rótulo da página (acima do título) | 13 px, 600, cor de destaque |
| Título (a pergunta da página) | 32 px, 700 (24 px no celular) |
| Subtítulo (uma linha) | 16 px, 400, secundário |
| Número da resposta (Início) | 56 px, 700, destaque (40 px no celular) |
| Número de cartão | 28 px, 700 |
| Seção (h2) | 20 px, 600 |
| Texto e frase de conclusão | 15–16 px |
| Rótulo de cartão, nota, fonte | 13 px / 13 px / 12 px, mudo |

## 5. Grade e espaçamento

- **12 colunas** em 1.152 px úteis (largura máxima de 1.216 px menos 32 px de margem de cada lado): coluna de 72 px e vão de 24 px. O filtro do mapa ocupa 4 colunas; cartões em 2 (6 + 6) ou 3 (4 + 4 + 4) colunas; mapa e gráficos em 12.
- **Espaçamento em múltiplos de 8 px:** 8 entre rótulo e número, 16 entre blocos e dentro dos cartões, 24 entre a linha divisória e as perguntas sugeridas, 32 de margem lateral (16 no celular).
- **Cartões da mesma linha com a mesma altura** (grade CSS com `align-items: stretch`); abaixo de 760 px, um cartão por linha.
- Título de seção, título de gráfico e conteúdo alinhados à esquerda na mesma borda (o título do gráfico fica a 24 px da borda do cartão, como o texto dos cartões).

## 6. Componentes (`src/painel/ui.py`)

- `cabecalho(titulo, subtitulo, sobre)`: título escuro sobre o fundo claro e uma linha de subtítulo; sem etiquetas.
- `resposta(...)`: só no Início: rótulo, número grande, faixa provável logo abaixo e a frase de quão certo é.
- `kpi(rotulo, valor, nota, projecao, dica)`: rótulo pequeno em cima, número grande, uma linha de contexto embaixo. Sem selo, salvo "projeção" onde houver projeção. `dica` vira a explicação ao passar o mouse (o glossário antigo).
- `grade(cartoes, colunas)`, `frase(texto)` (conclusão de um bloco), `tabela(...)` (tabela compacta de "Sobre os dados"), `fonte(texto)` (uma linha pequena), `termo(texto, explicacao)`.
- `sugestoes(perguntas)`: 2 ou 3 perguntas para o chat, como links `Chat?pergunta=...`.
- Navegação lateral: fundo branco, ícones finos (traço 1,5), item ativo com fundo `#eef3fd` e texto `#2450c4`.
- **Sem abas** nas páginas da história. Se voltarem, o padrão é controle segmentado ou sublinhado forte na ativa.

## 7. Gráficos (`graficos.py`, template `radar`)

Fundo branco e grade `#f1f2f4` (quase invisível); sem eixo de números quando o rótulo direto já diz o valor (funil e sensibilidades); título que diz a conclusão; rótulos diretos nos dados em vez de legenda; fonte numa linha pequena embaixo, só com a fonte e a data (`comum.fonte_linha`), sem versão nem nome de tabela; barras com cantos de 4 px; sem escala log, sem eixo duplo, sem pizza. A projeção leva "PROJEÇÃO" no título e "projeção, não número oficial" na fonte.

## 8. Números

Formato brasileiro sempre com a unidade (`R$ 341,1 mil`, `R$ 1,9 mi`, `≈ 1.121`). O texto dos extremos que saía cortado ("R$ 51,7 mil a R$ 1,9") vinha da largura do cartão; os extremos agora ficam no gráfico, cada um com a unidade, e na tabela de "Sobre os dados". Nenhum número em destaque aparece em duas páginas (teste `test_nenhum_cartao_repete_numero_entre_paginas`); a tabela dos 10 números em "Sobre os dados" é a exceção pedida.

## 9. Quarta rodada (D-052, 2026-10-29): o visual do "Raio-X do Cartório"

A pedido do autor, o painel usa **os mesmos tokens, medidas e componentes** do artefato "Raio-X do Cartório" (ficha de cada serventia do Brasil, feita à parte), com os mesmos valores, para que uma página dele caiba no painel sem emenda. Muda só a aparência: a estrutura da D-051 (cinco páginas, limites por página, classes HTML que os testes conferem) continua.

**Tokens (idênticos aos do Raio-X; nome original entre parênteses):** fundo `#eceff3` (bg); superfícies `#ffffff` e `#f5f7fa` (surface, surface-2); texto `#0f1c33`, `#45506a` e `#6b7590` (ink, ink-2, muted); linhas `#dde2ea`, grade `#e6e9ef` e `#c2c9d6` (line, grid, grid-strong); azul-marinho `#0f2447` → `#183564` (navy, navy-2), texto sobre ele `#f2f5fb` e `#b9c5dd`; dourado `#c9992e`, `#7a5a10` e `#fbf3df` (gold, gold-ink, gold-tint); agregado `#e8eef8` com borda `#c3d1e8` (agg, agg-line); séries `#2a78d6`, `#eb6834`, `#1baf7a` e `#8d97ab` (s1, s2, s3, ref); estados bom `#17794a`/`#e2f4ea`, alerta `#8f5f00`/`#fdf0d2` e ruim `#b42318`/`#fde7e4`; sombra `0 1px 2px rgba(15,28,51,.06), 0 6px 20px rgba(15,28,51,.05)`; IBM Plex Sans 14 px/1,5 no corpo (`baseFontSize = 14` no tema) e Newsreader nos títulos.

| Componente | Raio-X | No painel |
|---|---|---|
| Faixa do topo (`.top`) | degradê `#0f2447` → `#183564`, rótulo de 12 px em caixa alta, título Newsreader 600 de 30 a 42 px, texto `#b9c5dd`, traço dourado 44 × 3 px | `.rd-cab`, igual; o degradê vai num `border-image` com recuo lateral, que pinta até as bordas sem criar rolagem |
| Cartão (`.card`) | branco, borda `#dde2ea`, raio 14 px, sombra, 20 px de respiro; título Newsreader 600 18 px | `.rd-resposta`, `.rd-sugestoes`, os gráficos e os títulos de seção |
| Agregado (`.cagr`) | quadro `#e8eef8`, número de 40 a 54 px, peso 600 | o número principal do Início |
| Número (`.tile`) | rótulo 12 px `#6b7590`, valor 24 px peso 600, nota 12,5 px `#45506a` | `.rd-card` |
| Veredito (`.verdict`) | quadro `#fbf3df`, 13,5 px, sinal em `#7a5a10` | `.rd-frase-bloco` e a frase do Início |
| Selo (`.badge`) | pílula de 12 px; bom, alerta e ruim | `.rd-selo` (dado = bom; suposição e projeção = alerta) e as etiquetas do Chat |
| Botão (`.btn2`) | 34 px, raio 8, `#f5f7fa`, borda `#dde2ea` | as perguntas sugeridas ao chat |
| Tabela (`table.st`) | 13 px, células 7 × 9 px, cabeçalho `#f5f7fa`, linhas `#e6e9ef`, agregado em `#e8eef8` e negrito | `.rd-tabela` (a coluna de valor) |
| Gráficos (Chart.js) | séries s1/s2/s3/ref; barras com borda branca de 2 px e cantos de 4 px; marcas 12 px `#45506a`; grade `#e6e9ef`; eixo `#c2c9d6`; dica branca com borda `#dde2ea` | Plotly com os mesmos valores; título Newsreader 600 18 px e subtítulo 12,5 px `#6b7590` no campo próprio do Plotly; funil em s1 com o prêmio em s2; tornado s1 (para baixo) × s2 (para cima); faixa em s1 translúcido; extremos em ref |
| Mapa | (não tem) | escala `#e8eef8` → `#2a78d6` (s1) → `#183564` (navy-2); sem dado `#f5f7fa` com contorno `#45506a` |
| Navegação | (não tem) | superfície branca com a linha `#dde2ea`, marca em Newsreader 18 px, item ativo em `#e8eef8` com o filete dourado à esquerda (a linha agregada do demonstrativo) |
| Chat (`src/agent/chat.css`) | caixa de busca de 50 px, raio 10, sombra | só as cores e a fonte do título trocadas pelos tokens acima; campo como a caixa de busca, mensagens como cartões, sugestões como as pílulas de exemplo, botão de enviar em azul-marinho |

**Tema escuro (como o Raio-X):** o painel segue o tema do sistema, e o menu do Streamlit também troca. Tokens escuros, idênticos aos do artefato: fundo `#0c1018`; superfícies `#141a25` e `#1a2130`; texto `#e9edf5`, `#b2bccd` e `#8793a8`; linhas `#262e3d`, grade `#222a38` e `#3a4558`; azul-marinho `#0a1630` → `#12244a`; dourado `#e0b44e`, `#e8c46a` e `#2a2414`; agregado `#1d2840` com borda `#2c3d62`; séries `#3987e5`, `#d95926`, `#199e70` e `#7b869b`; estados `#4cc38a`/`#12301f`, `#e2b04a`/`#33270c` e `#ff8a7a`/`#3a1a17`; sombra `0 1px 2px rgba(0,0,0,.4), 0 6px 20px rgba(0,0,0,.25)`. Como funciona: `.streamlit/config.toml` tem `[theme.light]` e `[theme.dark]`; `ui.estilo()` põe um marcador `.rd-tema-escuro` ou `.rd-tema-claro` conforme `st.context.theme`, e o `estilo.css` troca os tokens por ele (sem marcador, vale `prefers-color-scheme`, como no artefato); o Plotly não lê CSS, então `graficos.finalizar()` troca cada cor clara pela escura (`graficos.ESCURO`), inverte a escala do mapa em luminosidade (no escuro, o valor maior é o azul mais claro) e põe o fundo do mapa na superfície escura. O `chat.css` usa as mesmas variáveis.

**Ajustes de encaixe no Streamlit:** a barra do Streamlit (60 px) fica sobre a faixa, por isso a faixa começa com 76 px de respiro e a barra fica azul-marinho só nas páginas com faixa (o Chat não tem: lá a barra fica da cor do fundo e o conteúdo desce 72 px). O primeiro bloco depois da faixa sobe 30 px sobre ela, como o `main` do Raio-X; um título de seção (Sobre os dados) não sobe, e um filtro (Mercado) vai num cartão branco.

**Fora desta rodada:** a busca por cartório e o demonstrativo por ano (ver as propostas de estrutura no `docs/diario.md`, 2026-10-29).
