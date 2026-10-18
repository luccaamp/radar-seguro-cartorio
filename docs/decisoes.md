# Registro de decisões

Cada decisão de interpretação ou de modelagem que afeta números do painel ou do chat. Mais recente no topo.
O `docs/diario.md` conta o que aconteceu; este arquivo explica **por que** cada escolha foi feita.

Formato:

```
## D-NNN — título
- **Data:**
- **Contexto:**
- **Opções:**
- **Decisão:**
- **Justificativa:**
- **Consequências / onde aparece:**
- **Fonte:**
```

---

## D-017 — Fórmula do passivo por vínculo: parâmetros legais e interpretações
- **Data:** 2026-10-18
- **Status:** parâmetros legais conferidos no texto oficial; **três interpretações (marcadas com ⚠) aguardam o autor**.
- **Contexto:** o art. 5º do 227 lista as verbas, mas não diz como calcular cada uma com os dados da RAIS (salário de dezembro e tempo de emprego em 31/12).
- **Parâmetros legais (texto conferido em `data/bronze/normas/2026-10-18/`):**
  - aviso prévio: 30 dias + 3 por ano completo, até 90 (Lei 12.506/2011, art. 1º);
  - a projeção do aviso conta como tempo de serviço (CLT, art. 487, § 1º), por isso gera 13º e férias;
  - fração de 15 dias ou mais = 1/12 (Lei 4.090/1962, art. 1º, § 2º; CLT, art. 146, parágrafo único);
  - férias proporcionais na despedida sem justa causa, mesmo com menos de 12 meses (CLT, arts. 146 e 147), + 1/3 (art. 5º, II, do 227);
  - FGTS: 8% da remuneração, incluindo o 13º (Lei 8.036/1990, art. 15); não incide sobre as parcelas do § 9º do art. 28 da Lei 8.212, como as férias indenizadas (art. 15, § 6º);
  - multa de 40% sobre todos os depósitos do contrato (Lei 8.036, art. 18, § 1º);
  - INSS patronal de 20% (Lei 8.212/1991, art. 22, I), com o titular pessoa física equiparado a empresa (art. 15, parágrafo único); o 13º integra (art. 28, § 7º) e as férias indenizadas não (art. 28, § 9º, d);
  - RAT de **1%** para o CNAE 6912-5/00 Cartórios (Decreto 3.048/1999, Anexo V, redação do Decreto 10.410/2020); FAP entre 0,5 e 2,0 (art. 202-A, § 1º), com base 1,0.
- **Interpretações propostas pela IA:**
  - ⚠ **13º na posição de 31/12:** o 13º do ano já foi pago em dezembro, então resta só o 13º da projeção do aviso (art. 4º do 227 + Lei 4.090, art. 1º);
  - ⚠ **INSS não incide sobre o aviso prévio indenizado.** A lei não o exclui expressamente; a não incidência vem da jurisprudência do STJ (REsp 1.230.957/RS, repetitivo), **citada de memória, a confirmar**. O FGTS incide sobre o aviso (ele não está no § 9º do art. 28);
  - ⚠ **férias vencidas não gozadas:** a RAIS não informa se o último período foi gozado. Premissa nova `fracao_ferias_vencidas_pendentes` (min 0, base 0,5, max 1; `fonte: suposição`), com base no prazo de 12 meses do art. 134 da CLT.
- **Suposição de cálculo:** o saldo do FGTS é estimado como 8% × salário atual × meses × 13⅓/12 (12 salários + 13º + 1/3 de férias), com `fator_correcao_saldo_fgts` = 1,0 (`fonte: suposição`). O salário atual superestima os depósitos antigos e a falta de juros os subestima; os efeitos se compensam em parte.
- **Fonte:** leis citadas (Planalto, coletadas em 2026-10-18); Prov. 227/2026, arts. 4º a 6º.

## D-016 — Valores das premissas de mercado (versão 1)
- **Data:** 2026-10-18
- **Contexto:** tabela proposta pela IA no ponto de parada (a), conforme D-012.
- **Decisão (aprovada pelo autor):**

  | Premissa | min | base | max | Fonte |
  |---|---|---|---|---|
  | `prob_deficit` Classe 2 / Classe 3 | 30% / 15% | 50% / 30% | 70% / 50% | suposição |
  | `pct_descoberto` Classe 2 / Classe 3 | 30% / 20% | 50% / 40% | 80% / 70% | suposição |
  | `escolha_garantia` (bens / fiança / seguro) | 50/25/25 | 30/20/50 | 15/15/70 | suposição |
  | `taxa_seguro_anual` (% da IS) | 1,0% | 2,0% | 3,5% | suposição |
  | `despesa_administrativa` (% do prêmio) | 5% | 8% | 12% | suposição |
  | `market_share_hipotetico` | 3,9% (10ª) | 5,2% (5ª) | 16,4% (**líder atual**) | SES, 12 meses até ago/2026 |
  | `peso_classe_indeterminada_base` | 0 | 65,6% | 1 | fração fora da Classe 1 (v2) entre as não vagas com receita conhecida |
  | `sinistralidade` | **1,7%** (menor janela anual do 0775, set/2021–ago/2022) | **10,9%** (0775, set/2020–ago/2026) | **73,9%** (0776, set/2020–ago/2026) | SES |
  | `comissao` (despesa de comercialização ÷ prêmio emitido) | 14,3% | 17,1% | 21,9% | SES |
  | `correcao_salarial_rais` | sem correção | INPC dez/2025 → mês mais recente | — | IBGE/SIDRA, tabela 1736 |

- **Justificativa da sinistralidade (autor):** base no ramo 0775 (setor público) pelo art. 13, §1º, do 227 ("apta a elidir a presunção de risco à continuidade do serviço público"); o 0776 fica como máximo.
- **Consequências:** o painel deixa claro que o máximo do market share é a **fatia do líder atual**. `desp_com` do SES é despesa de comercialização inteira, não só comissão (limitação declarada). O `peso_classe_indeterminada_base` é recalculado pelo pipeline a cada carga: 65,6% na prévia do ponto (a) e **67,8%** depois de aplicar as regras de zero e conflito (D-013, D-014).
- **Fonte:** decisão do autor em 2026-10-18; números do SES em `docs/diario.md` (2026-10-18).

## D-015 — Vínculos sem remuneração de dezembro fora da distribuição
- **Data:** 2026-10-18
- **Contexto:** 887 dos 11.865 vínculos ativos por prazo indeterminado na RAIS 2025 de MG têm remuneração de dezembro zerada (mediana de 85 meses de casa; provável afastamento).
- **Decisão:** ficam **fora da distribuição de salário × tempo**. A contagem de empregados continua vindo do CNJ (D-005).
- **Limitação:** supõe que os afastados têm o mesmo perfil dos demais.
- **Fonte:** RAIS 2025; aprovado pelo autor em 2026-10-18.

## D-014 — Valores conflitantes na fonte = classe indeterminada
- **Data:** 2026-10-18
- **Contexto:** a API do Justiça Aberta traz, para algumas serventias, o mesmo período com valores diferentes. Em 2025: CNS 048108 e 053439 (1º semestre).
- **Decisão:** se algum semestre de 2025 tem conflito, a serventia fica com **classe indeterminada** (D-004).
- **Fonte:** silver `serventia_arrecadacao.conflito_fonte`; aprovado pelo autor em 2026-10-18.

## D-013 — Arrecadação zero em 2025
- **Data:** 2026-10-18
- **Contexto:** em 2025 não há "NÃO INFORMADO", mas 76 ativas de MG declaram R$ 0 nos dois semestres. Uma serventia em funcionamento sem arrecadação é improvável; o zero provavelmente significa "não declarado".
- **Decisão:** zero nos dois semestres → **classe indeterminada**; zero em um só → usa o outro semestre (mesma regra de "um semestre informado" de D-010).
- **Fonte:** silver `serventia_arrecadacao`; aprovado pelo autor em 2026-10-18.

## D-012 — Premissas sem fonte pública × premissas da SUSEP
- **Data:** 2026-10-18
- **Contexto:** várias premissas do §2.4 não têm fonte pública (`prob_deficit`, `pct_descoberto`, `escolha_garantia`, `taxa_seguro_anual`, `market_share_hipotetico`, `despesa_administrativa`, `peso_classe_indeterminada_base`).
- **Decisão:**
  - para essas, a IA propõe uma tabela com `min`/`base`/`max` e justificativa, marcada `fonte: suposição`, e **o autor aprova antes de entrar no YAML**;
  - `sinistralidade` e `comissao` **não são suposição**: vêm do SUSEP SES já baixado (`data/bronze/susep_ses/2026-10-17/`), ramos 0775 e 0776, calculadas no pipeline.
- **Fonte:** decisão do autor em 2026-10-18.

## D-011 — Faixas do `prob_deficit` e do `pct_descoberto` = Classes 2 e 3 do Prov. 213
- **Data:** 2026-10-18
- **Contexto:** o SPEC prevê essas premissas "por faixa", sem dizer qual faixa.
- **Decisão:** as faixas são as **Classes 2 e 3** do Prov. 213 (a Classe 1 já está fora do universo pelo art. 19 do 227), calculadas com a mesma regra de classe (v2 base, v1 sensibilidade). Classe indeterminada usa os valores da Classe 2.
- **Justificativa:** a classe já é calculada para o universo e é a medida de porte que a própria norma usa.
- **Fonte:** Prov. 213/2026, art. 16; decisão do autor em 2026-10-18. *O uso dos valores da Classe 2 para a indeterminada é proposta da IA, a confirmar.*

## D-010 — Enquadramento da classe pela média dos semestres de 2025
- **Data:** 2026-10-18
- **Contexto:** o art. 16, §1º, do 213 enquadra pela média das receitas brutas semestrais do exercício anterior. Para o ciclo de 2026, o exercício anterior é 2025.
- **Decisão:** receita de referência = média dos dois semestres de 2025 informados no Justiça Aberta. Se só um estiver informado, usa esse (marca `receita_um_semestre`). Se nenhum estiver, classe indeterminada (D-004).
- **Consequências:** o 1º semestre de 2026 não entra no enquadramento; fica só como informação no painel.
- **Fonte:** Prov. 213/2026, art. 16, §1º (redação do 243). Aprovado pelo autor em 2026-10-18.

## D-009 — Distribuição de salário e tempo só com vínculos por prazo indeterminado
- **Data:** 2026-10-18
- **Contexto:** na RAIS 2025 de MG há, entre os vínculos ativos, contratos por prazo determinado (402) e aprendizes (68), cuja rescisão segue regras diferentes (em geral sem aviso prévio nem multa de 40% ao fim do prazo).
- **Decisão:** a distribuição de salário × tempo usa só **`Tipo Vínculo` ∈ {10, 15, 20, 25}** (CLT urbano/rural, empregador PJ/PF, prazo indeterminado). A **contagem** de empregados continua vindo do CNJ (D-005).
- **Conferência do código:** layout `RAIS_vinculos_layout2020.xls` (aba "RAISD - layout", linhas 292–311): 10 CLT U/PJ IND, 15 CLT U/PF IND, 20 CLT R/PJ IND, 25 CLT R/PF IND, 30–35 estatutário, 40 avulso, 50 temporário, 55 aprendiz, 60–75 CLT prazo determinado, 80 diretor, 90–97 contratos por prazo/tempo determinado e leis estaduais/municipais.
- **Consequências:** em MG ficam **11.865** vínculos ativos (consulta ao `silver.rais_vinculo`; 15: 11.558, 10: 258, 25: 48, 20: 1); saem 402 (65), 68 (55) e 4 (90). Limitação: supõe que os empregados declarados ao CNJ têm o mesmo perfil dos indeterminados.
- **Fonte:** layout RAIS 2020 (`data/bronze/rais/layouts/`); RAIS 2025. Aprovado pelo autor em 2026-10-18.

## D-008 — Limiar de vínculos para usar a distribuição de salário e tempo do município
- **Data:** 2026-10-18
- **Status:** **aprovada pelo autor em 2026-10-18** (limiar 20 base; 10 e 30 sensibilidade). A contagem do limiar passa a usar só os vínculos de D-009.
- **Contexto:** a RAIS não identifica a serventia. O passivo de um município é calculado com a distribuição (faixa salarial × faixa de tempo de emprego) dos vínculos da RAIS. Com poucos vínculos, a distribuição da cidade é ruído (ex.: 3 vínculos não dizem nada sobre o perfil salarial). Em MG, a RAIS 2025 tem 12.347 vínculos ativos em 757 municípios, com mediana de 4 vínculos por município (p75 = 15, p90 = 33, máximo = 1.366 em BH). O CNJ tem serventias ativas em 851 municípios.
- **Opções** (contagem com vínculos ativos e remuneração de dezembro > 0):

  | limiar | municípios com distribuição própria | % dos vínculos de MG cobertos | municípios do CNJ que usam a de MG (≈) |
  |---|---|---|---|
  | 10 | 268 | 88,4% | ≈ 583 |
  | **20** | **143** | **73,2%** | **≈ 708** |
  | 30 | 89 | 62,1% | ≈ 762 |

- **Decisão:** limiar **20** como base, **10** e **30** como sensibilidade, em `config/premissas/` (`limiar_vinculos_distribuicao_municipal`, `fonte: suposição`). Com 20 vínculos, o erro da média de passivo por vínculo fica em torno de 20% (supondo coeficiente de variação ~1); com 10, ~30%.
- **Consequências:** os 143 municípios mais populosos capturam a diferença regional de salário (BH × interior); os demais usam a distribuição de MG. A coluna `origem_distribuicao` (municipio/estado) aparece no gold e na página Qualidade dos dados.
- **Fonte:** RAIS 2025, `data/bronze/rais/2025/` (análise de 2026-10-18). A coluna "≈" é aproximada porque a junção CNJ × IBGE por código ainda não foi feita.

## D-007 — Situações "SOB INTERVENÇÃO" e "CONVERSÃO EM DILIGÊNCIA"
- **Data:** 2026-10-18
- **Status:** **aprovada pelo autor em 2026-10-18.**
- **Contexto:** o art. 19 do 227 exclui as serventias "sob interinidade". A API do CNJ traz, além de PROVIDO e VAGO, duas situações que não são nem uma coisa nem outra. MG (ativas): 13 sob intervenção (46 CLT) e 28 em conversão em diligência (238 CLT, 9 delas de Registro de Imóveis/RTD/RCPJ).
- **Opções:** (a) tratar como interinidade (fora); (b) tratar como providas (dentro); (c) categoria à parte: fora no `min` e no `base`, dentro no `max`.
- **Decisão:** (c). Fora no `min` e no `base`, dentro no `max`.
- **Fonte:** API do Justiça Aberta, `serventias_MG.json` e `dados_complementares_MG.jsonl` (2026-10-17). O significado jurídico de cada situação está explicado no diário (2026-10-18) e é interpretação da IA a confirmar: a API não tem documentação.

## D-006 — `fator_cobertura_rais` = 1,0 em MG
- **Data:** 2026-10-18
- **Contexto:** o risco do §10 era a RAIS não captar vínculos no CPF do titular. Em MG ela capta (98% dos vínculos em CAEPF), e RAIS (12.347) e CNJ (12.134 CLT) diferem 1,8%, com correlação de 0,996 por município.
- **Decisão:** `fator_cobertura_rais` = 1,0 para MG. Revisar na Fase 2, quando o Brasil inteiro mostrar RAIS/ANOREG = 1,12.
- **Justificativa:** com o rateio `por_empregados_cnj` (D-005), o número de vínculos vem do CNJ, e a RAIS dá só a distribuição de salário e tempo. O fator só importaria se a RAIS for usada como contagem.
- **Fonte:** `docs/viabilidade.md`, §2 (conferência de empregados). Aprovado pelo autor em 2026-10-18.

## D-005 — Rateio padrão `por_empregados_cnj`
- **Data:** 2026-10-18
- **Contexto:** a RAIS não identifica a serventia, e o município do vínculo tem ruído (vínculo registrado no endereço do CAEPF do titular). O CNJ declara os colaboradores CLT de cada serventia (99,8% das ativas de MG preenchidas).
- **Opções:** `arrecadacao`, `uniforme`, `peso_por_atribuicao` (SPEC original) ou o novo `por_empregados_cnj`.
- **Decisão:** padrão `por_empregados_cnj`: passivo da serventia = CLT declarados × passivo médio por vínculo da distribuição RAIS aplicável (D-008). Os outros três métodos ficam como sensibilidade. SPEC §3.3 atualizado.
- **Justificativa:** usa a informação mais próxima da serventia; a correlação de 0,996 entre CNJ e RAIS por município mostra que a contagem do CNJ é coerente.
- **Consequências:** serventias com 0 CLT declarado (316 em MG) ficam com passivo zero. A soma rateada deixa de ser "igual ao passivo RAIS do município" e passa a ser "igual a CLT_CNJ × passivo por vínculo"; o teste do §3 é ajustado para isso.
- **Fonte:** `docs/viabilidade.md`, §2. Aprovado pelo autor em 2026-10-18.

## D-004 — Arrecadação "NÃO INFORMADO" = classe indeterminada
- **Data:** 2026-10-18
- **Contexto:** cerca de 10% da amostra do CNJ tem arrecadação "NÃO INFORMADO" no semestre.
- **Decisão:** a serventia sem arrecadação no período de enquadramento fica com **classe indeterminada**: fora no `min`, dentro no `max` e com peso `peso_classe_indeterminada_base` no `base` (§3.4 do SPEC).
- **Fonte:** amostra de 30 serventias, `data/samples/cnj_justica_aberta/cobertura_MG_amostra30.json`. Aprovado pelo autor em 2026-10-18.

## D-003 — Só colaboradores CLT entram no passivo
- **Data:** 2026-10-18
- **Contexto:** o art. 5º do 227 fala de verbas rescisórias (aviso prévio, férias, 13º, multa do FGTS), que são da CLT. O CNJ separa CLT, estatutários, estagiários e terceirizados.
- **Decisão:** só os CLT. Ficam fora, como **limitação declarada**: estatutários (178 em MG), estagiários (86) e terceirizados (135).
- **Justificativa:** estatutários seguem regime próprio (serventias oficializadas), estágio não é vínculo empregatício e terceirizados são empregados de outra empresa.
- **Fonte:** Prov. 227/2026, art. 5º; contagens de `dados_complementares_MG.jsonl` (2026-10-17). Aprovado pelo autor em 2026-10-18.

## D-002 — Limite da Classe 1: R$ 300 mil (Prov. 243) × R$ 100 mil (Prov. 213 original)
- **Data:** 2026-10-17
- **Contexto:** o Prov. 227 entrou em vigor em 10/08/2026. Nessa data, o limite da Classe 1 era a receita semestral de até R$ 100.000,00 (art. 16, I, do 213 original). O Prov. 243 elevou o limite para R$ 300.000,00 de receita bruta semestral e entrou em vigor em 22/08/2026 (art. 2º do 243: 30 dias após a publicação no DJe de 23/07/2026). A entrega do 1º ciclo venceu por volta de 09/09/2026, já sob o 243. O texto não diz qual versão vale para o 1º ciclo.
- **Opções:**
  1. R$ 100 mil, a regra vigente na entrada em vigor do 227;
  2. R$ 300 mil, a regra vigente no prazo de entrega do 1º ciclo e hoje;
  3. as duas, uma como base e a outra como sensibilidade.
- **Decisão:** opção 3. **Base `v2` = R$ 300 mil** (Prov. 243) e **sensibilidade `v1` = R$ 100 mil**. As duas versões ficam em `config/regras_classificacao.yaml`, com as datas de vigência.
- **Justificativa:** a regra vigente no prazo de entrega e nos ciclos anuais seguintes é a do 243. Mostrar a versão anterior deixa visível o tamanho do efeito da mudança.
- **Consequências / onde aparece:**
  - o pipeline calcula as duas versões e registra a **diferença de universo** (nº de serventias, passivo) e de **mercado** (IS, prêmio) no diário e na página Qualidade dos dados;
  - a classificação é marcada como **aproximada**, porque a receita bruta do art. 2º, XXIV do 213 (inclui o ressarcimento de atos gratuitos e a complementação de renda mínima; deduz os valores de terceiros e os repasses legais) pode não coincidir com a arrecadação publicada nas fontes públicas;
  - os limites são atualizados todo ano (art. 16, §2º, do 213). Cada atualização vira uma nova versão, e a divulgação entra na lista de monitoramento do radar.
- **Fonte:** Prov. 213/2026, art. 2º, XXIV, e art. 16 (texto compilado); Prov. 243/2026, art. 2º; Prov. 227/2026, arts. 18 a 20. Cópias em `data/bronze/normas/2026-10-17/`.

## D-001 — "Classe I" (art. 19 do 227) = Classe 1 do Prov. 213
- **Data:** 2026-10-17
- **Contexto:** o art. 19 do Prov. 227 exclui "as serventias extrajudiciais enquadrada[s] na Classe I do Provimento nº 213/2026". O 213 numera as classes em algarismos arábicos (Classe 1, 2 e 3) e usa letras para as subclasses (A a J). Uma dessas subclasses é a **Subclasse I**, dentro da Classe 3: receita acima de 6 e até 12 vezes o teto da Classe 2.
- **Opções:**
  1. "Classe I" = Classe 1, as menores serventias;
  2. "Classe I" = Subclasse I da Classe 3, serventias grandes.
- **Decisão:** opção 1.
- **Justificativa:**
  - o art. 19 diz "Classe", e não "Subclasse";
  - o algarismo romano I equivale ao arábico 1;
  - excluir as menores serventias está de acordo com a lógica de proporcionalidade do 213 (art. 2º, III; art. 16, §4º);
  - a opção 2 isentaria uma faixa intermediária de serventias grandes, o que não tem lógica regulatória aparente.
- **Consequências / onde aparece:** `universo()` exclui a Classe 1. A interpretação é citada no chat quando a pergunta envolver as exclusões. Se uma norma ou decisão posterior esclarecer o ponto, esta decisão é revista (monitorado pelo radar).
- **Fonte:** Prov. 227/2026, art. 19; Prov. 213/2026, art. 16 (texto compilado).
