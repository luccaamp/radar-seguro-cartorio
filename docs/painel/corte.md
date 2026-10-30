# Corte do painel (Etapa 3, terceira rodada)

29/10/2026 · D-051. O painel responde a **uma** pergunta:

> **Quanto dinheiro o seguro obrigatório dos cartórios (Prov. CNJ 227/2026) pode movimentar em Minas Gerais, e quão certo é esse número?**

Regra de corte: se um elemento não ajuda a responder "quanto" ou "quão certo", ele sai do painel. O que sai continua no chat, que responde a qualquer pergunta sobre os dados. **O painel é a história; o chat é o detalhe.**

## 1. A escada de perguntas

Cada degrau é uma parte do anterior. Valores da carga 2026-10-28 (premissas v3, regra base, nível base), lidos do banco por `src/painel/analises.py`; nenhum mudou nesta rodada.

| # | Pergunta | Resposta | Onde aparece |
|---|---|---|---|
| 1 | Quantos cartórios estão ativos em MG? | 2.525 | funil (A resposta) |
| 2 | Quantos são obrigados pelo Prov. 227? | ≈ 1.121 | funil |
| 3 | Quantos não têm bens que cubram a dívida trabalhista? | ≈ 148 | funil |
| 4 | Quanto falta cobrir, somando todos (déficit)? | R$ 34,1 mi | funil |
| 5 | Quanto disso vira seguro (importância segurada)? | R$ 17,1 mi | funil |
| 6 | **Quanto as seguradoras recebem por ano (prêmio)?** | **R$ 341,1 mil** | número grande (A resposta) |
| 7 | Quão certo? Faixa provável (P5–P95) | R$ 215 mil a R$ 687 mil | logo abaixo do número (A resposta) e no gráfico (Quão certo é) |
| 8 | Quão certo? O que mais pesa | taxa do seguro e adesão ao seguro: 58,4% da incerteza | Quão certo é |
| 9 | E até 2027? (projeção) | prêmio ≈ R$ 349,0 mil com a dívida de 2025; a dívida sobe 28,5% | Para onde vai |

**Ajuste em relação à escada proposta:** nenhum na ordem. O degrau "passivo trabalhista" (R$ 238,1 mi das obrigadas) não entra no funil: ele é a base de onde sai o déficit, mas é ~7 vezes o déficit e esmagaria as barras em reais; fica na tabela dos 10 números ("Sobre os dados") e no chat. Os empregados CLT (nº 2) e o teto teórico (nº 10) também ficam só lá.

## 2. Tabela de corte, página por página

Decisões: **fica** (responde "quanto" ou "quão certo"), **chat** (útil, mas é detalhe; o chat responde), **sai** (repetido, técnico ou sem relação). "Sobre" = vai para a página "Sobre os dados" (detalhe técnico que precisa ficar visível).

### Início (antes)

| Elemento | Decisão | Motivo |
|---|---|---|
| Faixa azul-escura do topo (sobretítulo, título, manchete, número em destaque) | fica, refeita | a pergunta vira o título; o prêmio vira o número grande; sem a faixa colorida (Fase 3) |
| Etiquetas do topo (Dados/carga, Premissas, Classe 1, Nível, STF, UF) | Sobre | técnicas; nenhuma muda a leitura de um leigo |
| Parágrafo sobre o Prov. 227 (art. 13, art. 19) | sai | jurídico; a pergunta já nomeia a norma; o texto da norma está no chat (`buscar_norma`) |
| "Termos em uma linha" (glossário, 10 termos) | tooltip / chat | os termos usados no funil e no número ganham explicação curta ao passar o mouse; o resto, no chat |
| 3 cartões D-042 (déficit, IS, prêmio) | sai (repetidos) | déficit e IS viram degraus do funil; o prêmio vira o número grande |
| "Como ler a faixa provável e os extremos" | chat | detalhe do Monte Carlo (`faixa_d042`: mediana, cantos, patrimônio junto) |
| "Sensibilidades: o que mais mexe no prêmio" | sai (repetido) | é a página "Quão certo é" |
| Os 10 números oficiais (10 cartões) | Sobre | tabela compacta em "Sobre os dados"; os 6 da escada estão no funil |
| Gráfico "escada" (passivo → prêmio, escala log) | fica, refeito | vira o funil serventias → obrigadas → com déficit → déficit → IS → prêmio, sem escala log |
| "Dados do gráfico e método" + download CSV | chat | `escada` e `numeros_oficiais` |
| Situação regulatória: ADI 8015 (achado, data) | chat | STF sai do painel inteiro (diretriz); `situacao_adi` |
| Cartões do prêmio por cenário do STF | chat | idem; `premio_por_cenario_stf` |
| Peso da classe indeterminada; salário sem correção | Sobre | técnico (limitação) |
| Rodapé longo (fontes, versão, carga, data-base) | fica, curto | só fonte e data; versão e carga em "Sobre os dados" |

### Mercado (antes)

| Elemento | Decisão | Motivo |
|---|---|---|
| Manchete "providas grandes são o cliente" | fica, refeita | manchete passa a dizer onde está o dinheiro (BH e as 10 maiores áreas) |
| Aviso "estimativa, não avaliação de cartório; classe aproximada (D-002)" | Sobre | limitação; o ID da decisão sai da tela |
| Controle "Classe 1 até" (regra v1 × v2) | chat (parcial) | sensibilidade técnica; só o total estadual tem a regra v1 (`diferenca_regra_classe` não está nas ferramentas: recado) |
| Município | fica | é o filtro principal: "onde" |
| "Filtrar por" atribuição / situação / classe e "Valor" | chat (parcial) | detalhe; o chat conta por recorte em MG (`contar_serventias`), mas não tem o recorte por região (recado) |
| Botão Limpar | sai | com um filtro só, basta voltar a "Todos" |
| Etiquetas de contexto (filtros ativos, nível do mapa, regra) | sai | técnicas; o aviso de agregação (LGPD) continua quando acontece |
| 7 KPIs do recorte (serventias, CLT, obrigadas, com déficit, passivos, déficit) | sai / chat | os de MG repetem o funil; os da área viram 3 números ao lado do mapa |
| "% de MG" embaixo de cada KPI | fica (1 número) | "parte do déficit de MG" responde "onde está o dinheiro" |
| Tabela de extremos teóricos do recorte | chat | `numeros_oficiais` (mínimo e máximo de MG); o "quão certo" está na página própria |
| Rodapé longo | fica, curto | só fonte e data |
| Rádio "Métrica do mapa" (déficit, passivo, serventias, CLT) | sai | o mapa mostra o déficit, que é o que vira seguro; as outras métricas não respondem "quanto" |
| Mapa | fica, em destaque | largura inteira, ~560 px de altura |
| Legenda longa do mapa | fica, curta | uma linha: cor = déficit; cinza = agregado ou sem dado |
| Ranking dos 15 maiores | sai | repete o mapa; as 10 maiores viram um número |
| Tabela por área (expansor) | chat (parcial) | o chat lista as serventias de um município (`consultar_serventia`), não a tabela por área (recado) |
| Destaque do município: tabela de métricas e posição no ranking | sai / fica (1) | sobra "serventias na área", que explica a agregação |
| "Ver MG inteiro" | sai | voltar a "Todos" faz o mesmo |
| "Quem é o cliente": achado do grupo-alvo | fica, numa frase | a concentração e o grupo-alvo viram a frase abaixo do mapa |
| Gráfico dos grupos (k-means) | chat | `grupos` |
| Gráfico "quem é obrigado" (atribuição e porte) | chat | `quem_e_obrigado` |
| Perfil dos grupos, regras de associação, downloads | chat | `grupos`, `quem_e_obrigado` |

### Análises (antes)

| Elemento | Decisão | Motivo |
|---|---|---|
| Manchete (taxa e adesão; obrigadas em 2027) | fica, dividida | a primeira metade vai para "Quão certo é", a segunda para "Para onde vai" |
| 4 achados em uma frase | sai (repetidos) | cada um é a manchete de uma página nova ou vai para o chat |
| Abas (4) | sai | viram páginas; nenhuma página nova tem abas |
| 3 cartões D-042 | sai (repetidos) | estavam no Início também |
| Gráfico da faixa (base, P5–P95, extremos) | fica | gráfico 1 de "Quão certo é", com os extremos discretos |
| Nota da mediana e dos cantos do Monte Carlo | chat | `faixa_d042` |
| Tornado (11 suposições) | fica, com 5 | só as 5 que mais pesam, com o valor na ponta; as do passivo e do universo viram um número ("mexem no máximo 16,4%") |
| Grade taxa × adesão, método do Monte Carlo e do tornado, downloads | chat | `grade_taxa_adesao`, `tornado`, `faixa_d042` |
| Ano da receita (2026 × 2027) e leitura do limite (fixo × corrigido) | chat | a página "Para onde vai" mostra 2026 e 2027 juntos, no limite fixo; o corrigido muda o prêmio em −R$ 5,4 mil e fica no chat (`previsao_mercado`, `leitura_limite`) |
| Achado "PROJEÇÃO para 2027 · leitura do limite" | sai | técnico; o selo "projeção" fica |
| 4 cartões de projeção e comparação | fica (2) | obrigadas e prêmio em 2027, com o selo "projeção" |
| Gráfico do universo projetado | chat | a página mostra o prêmio projetado (é a pergunta "quanto"); as obrigadas viram um número |
| Nota do passivo projetado (M5) | fica, numa frase e num número | é o que muda o prêmio até 2027 |
| Gráfico da arrecadação 2026–27 | chat | `previsao_arrecadacao`: insumo, não resposta |
| Gráfico das subidas da Classe 1 (07 × 05b) | chat | `subidas_comparacao`: detalhe de método |
| Método, limitações, downloads da projeção | chat | `previsao_mercado` |
| Concentração: 3 cartões (Gini), curva de Lorenz | chat / frase | a parte dos 10% maiores vira frase no Mercado; Gini e curva no chat (`concentracao`) |
| "A seguradora tem lucro?" (pergunta 9) | chat | rentabilidade não muda "quanto" o mercado movimenta (o prêmio é o mesmo com lucro ou prejuízo); `pergunta_9`, `capacidade_pagar` |
| Rodapé longo com nomes de tabela e notebook | fica, curto | só fonte e data |

### Qualidade dos dados (antes)

| Elemento | Decisão | Motivo |
|---|---|---|
| Página inteira | vira "Sobre os dados" | discreta, por último |
| Lacunas (tabela de 8) | Sobre (resumo) / chat | as principais viram 4 tópicos de limitação; a tabela completa no chat (`lacunas`) |
| Escolhas de método do passivo (gráfico) | chat | `escolhas_metodo_passivo` (mexe no máximo poucos %) |
| Leitura literal da norma (gráfico) | chat | `leitura_literal_receita` |
| Saltos na declaração | chat | `saltos_declaracao` |
| Extremos e sorteios do Monte Carlo (tabela) | chat | `faixa_d042` |
| Empregados de outros estados | chat | `clt_outros_estados` (o painel é só MG) |
| Decisões que mudam a leitura (IDs D-0xx) | chat | `decisoes`; IDs fora da tela |
| Fontes e datas de referência | Sobre | tabela compacta: fonte e data (sem SHA, arquivo e URL) |
| Conferência entre fontes (tabela) | chat (resumo) | `qualidade_fontes` dá o placar (ok × aviso); o detalhe por checagem não (recado) |
| Gráfico CNJ × RAIS e maiores diferenças | chat (falta) | sem ferramenta (recado) |
| Regra da Classe 1, rateio, premissas do passivo, INPC, distribuição | chat (falta) | sem ferramenta (recado) |
| Contratos das tabelas | chat (resumo) | `qualidade_fontes` |
| Limitações declaradas (13 tópicos) | Sobre (5 tópicos) | as que mudam a leitura do número; o resto no chat (recado: texto sem ferramenta) |
| Rodapé com todas as fontes | Sobre | a tabela de fontes já é o rodapé |

### Simulador

| Elemento | Decisão | Motivo |
|---|---|---|
| Página inteira (15 controles, STF, seguradora hipotética, salvar cenário) | sai da navegação | não responde "quão certo" melhor que o gráfico de sensibilidades: o leitor teria de mexer em 15 controles para descobrir o que o tornado mostra de uma vez; tem STF e a rentabilidade da seguradora. O arquivo continua em `app/simulador.py` (roda à parte, para a Etapa 4) e o chat simula taxa e market share (`simular`) |

### Chat
Fica como está. Recebe as perguntas sugeridas das outras páginas pelo link (`?pergunta=`).

## 3. Contagem

Contada pela primeira palavra da decisão de cada linha (as linhas mistas, como "sai / chat", contam pela primeira):

| Decisão | Elementos |
|---|---|
| fica (como está ou refeito; inclui a Qualidade, que vira "Sobre os dados") | 17 |
| vai para "Sobre os dados" | 8 |
| vai para o chat (inteiro ou em parte; inclui o glossário, que vira dica do mouse) | 31 |
| sai (repetido, técnico ou sem relação) | 15 |
| **total** | **71** |

Os itens que foram para o chat sem ferramenta que os responda (ou só em parte) são 7 linhas da tabela acima, a resolver na Etapa 5 (chat).
