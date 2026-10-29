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
