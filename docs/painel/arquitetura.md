# Arquitetura da informação do painel (Etapa 3)

> **Substituída em 29/10/2026 pela D-051** (terceira rodada): o painel responde a uma pergunta só, em cinco páginas (A resposta → Quão certo é → Onde está o mercado → Para onde vai → Sobre os dados → Chat). A estrutura nova está no `docs/plano_projeto.md` (Etapa 3) e o corte elemento a elemento em `docs/painel/corte.md`. O texto abaixo é da segunda rodada e fica como histórico.

28/10/2026 · Fase 2 da Etapa 3. Base: o inventário (`inventario_achados.md`) e a Etapa 3 do `plano_projeto.md`.

## A pergunta do projeto, dividida em páginas

O projeto pergunta: **quanto dinheiro o seguro obrigatório dos cartórios (Prov. CNJ 227/2026) pode movimentar em Minas Gerais, e quão certo é esse número?** Cada página responde a um pedaço:

| Ordem | Página | O leitor chega perguntando | Sai sabendo |
|---|---|---|---|
| 1 | **Início** | "Quanto é esse mercado?" | O prêmio base, a faixa provável e os 10 números; que o mercado é pequeno diante da dívida; que o STF pode zerá-lo |
| 2 | **Mercado** | "Onde estão os cartórios obrigados, e quem é o cliente?" | O mapa por município ou região, os seis tipos de cartório e o grupo-alvo (providas grandes) |
| 3 | **Análises** | "Quão certo é o número e como ele muda até 2027?" | Que taxa e adesão pesam mais; a projeção 2026–27 (com a leitura do limite); a concentração; se a seguradora tem lucro |
| 4 | **Qualidade dos dados** | "Posso confiar nos dados?" | De onde vem cada dado e quando; o que não tem fonte (lacunas); as escolhas de método e a leitura literal da norma |
| 5 | Simulador | "E se a taxa for outra?" | (Etapa 4; nesta etapa só recebe o tema novo) |
| 6 | Chat | "Pergunte em português" | (Etapa 5; lugar reservado na navegação, a página reduzida da D-036 continua igual) |

**Por que "Análises" é uma página nova, e não seções do Mercado.** O inventário dá 11 achados à Análises (6 de importância alta: faixa, tornado, previsão, universo 2026–27, 2026-1 acima do P90, pergunta 9, concentração). A pergunta do Mercado é "onde e quem", respondida com mapa e filtros por área; a da Análises é "quão certo e como muda", respondida para MG inteiro, sem filtro de área. Juntar as duas obrigaria o leitor a rolar por baixo do mapa para achar a incerteza, e os filtros do Mercado (que não valem para a projeção) pareceriam valer. O notebook 09 (§4) já recomendava "Análises (página nova)".

## Três níveis de leitura por página

| Página | 10 segundos (manchete) | 1 minuto (centro) | 5 minutos (detalhe) |
|---|---|---|---|
| Início | Manchete com o prêmio base e a faixa provável; selo "regra mantida" | Cartões D-042 (déficit, IS, prêmio), os 10 números, a escada do passivo ao prêmio, a faixa do STF | Expansores: "Como ler a faixa", "Sensibilidades" (tornado resumido), "De onde vêm os números" |
| Mercado | Manchete: "As providas grandes são o cliente do seguro" com o número do grupo-alvo | Barra de filtros, KPIs do recorte, mapa e ranking; grupos (barras de participação) | Expansores: tabela por área, faixas do recorte, quem é obrigado (atribuição e porte), regras |
| Análises | Manchete: o que mais pesa (taxa e adesão) e a projeção 2027 | Abas: Incerteza (faixa + tornado) · Projeção 2026–27 · Concentração · Pergunta 9 | Dentro de cada aba, um expansor "Método e limitações" |
| Qualidade | Manchete: "As dúvidas estão nas suposições, não nos dados" com as lacunas | Lacunas (tabela), passivo: escolhas de método, leitura literal da norma | Expansores: fontes, conferências, sensibilidades antigas, contratos, decisões, limitações |

## Filtros e estado

- **Contexto fixo do painel (vale para todas as páginas):** carga, versão das premissas, regra de classe base (Classe 1 até R$ 300 mil), nível base e cenário do STF "regra mantida". Não é filtro: é a **faixa de contexto** no topo de cada página, sempre visível, e o rodapé de fonte repete a carga e a versão das premissas.
- **Mercado (filtros só desta página, como hoje):** regra da Classe 1 (só nos totais de MG), município, um filtro por vez (atribuição, situação ou classe) e a métrica do mapa. O estado aparece na linha "Filtros ativos" logo abaixo dos controles, com botão "Limpar". Os filtros não passam para outras páginas, porque o recorte por área (D-026) não existe para a projeção nem para o Monte Carlo.
- **Análises:** dois controles que mudam algo relevante na aba Projeção: o **ano** (2026 ou 2027) e a **leitura do limite** (fixo, principal; corrigido pelo IPCA, comparação). A leitura escolhida aparece no selo do cartão; a outra aparece ao lado, rotulada "comparação".
- **Início e Qualidade:** sem filtros (são leituras de MG inteiro).

## Navegação e lugar do chat

Barra lateral do Streamlit (páginas por arquivo), na ordem da tabela acima. O Chat fica por último, com a página atual (Etapa 5 reduzida, D-036); a Etapa 5 completa entra nesse mesmo lugar. Todas as análises exibidas saem de `src/painel/analises.py`, no mesmo formato das ferramentas do chat (`src/agent/ferramentas.py`), para o chat reaproveitar sem recalcular.

## Downloads

Cada gráfico das páginas Início, Análises e Qualidade tem, no expansor de detalhe, o botão "Baixar dados (CSV)" com a tabela agregada que o desenha, mais a fonte, a carga e a versão das premissas no nome e nas colunas. Nenhum download tem nome de pessoa; o Mercado já mostra só áreas agregadas.
