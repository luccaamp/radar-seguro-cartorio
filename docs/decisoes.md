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

## D-018 — Contribuições de terceiros (salário-educação, Sistema S) fora do passivo
- **Data:** 2026-10-18
- **Contexto:** o autor perguntou se as contribuições de terceiros se aplicam ao titular que contrata pelo CPF/CAEPF (98% dos vínculos de MG).
- **O que a fonte oficial diz:**
  - **Salário-educação:** STJ, **Tema Repetitivo 1228**, tese firmada: "não é exigível da pessoa física que exerce serviço notarial ou registral, a qual não se enquadra na definição de contribuinte trazida na legislação que rege o tributo". Julgado em 20/08/2026, acórdão publicado em 09/10/2026, **sem trânsito em julgado** (página do STJ em `data/bronze/normas/2026-10-18/stj_tema_repetitivo_1228.html`);
  - **Sistema S (SESC, SENAC etc.):** nenhuma fonte oficial (tema repetitivo, lei ou norma da Receita) foi localizada para o titular pessoa física. A exclusão do salário-educação não se estende automaticamente ao Sistema S.
- **Decisão:** `contribuicoes_terceiros` = 0 no passivo.
- **Justificativa:** independentemente da cobrança, o Prov. 227 fecha a lista: o parágrafo único do art. 5º inclui os "encargos previdenciários e fundiários devidos pelo empregador (INSS, RAT + FAP e FGTS mensal)". Contribuições de terceiros não são previdenciárias nem fundiárias.
- **Limitação:** a situação do Sistema S para o titular pessoa física fica em aberto; não afeta o passivo do art. 5º.
- **Fonte:** Prov. 227/2026, art. 5º, parágrafo único; STJ, Tema 1228.

## D-017 — Fórmula do passivo por vínculo: parâmetros legais e interpretações
- **Data:** 2026-10-18
- **Status:** **aprovada pelo autor em 2026-10-18**, com os ajustes abaixo.
- **Ajustes do autor e da conferência:**
  - INSS sobre o aviso prévio indenizado **confirmado no site oficial do STJ**: Tema Repetitivo 478 (REsp 1.230.957/RS, relator Min. Marco Aurélio Bellizze), tese "não incide contribuição previdenciária sobre os valores pagos a título de aviso prévio indenizado, por não se tratar de verba salarial", **mantida** no juízo de retratação de 13/05/2026 (que reformou só o terço de férias gozadas, pelo Tema 985/STF). **Base e min sem INSS no aviso; max com INSS no aviso** (decisão do autor);
  - 13º da projeção do aviso contado **pelo calendário** a partir de 31/12 (correção pedida pelo autor; ver `docs/erros_ia.md`). Nas férias, o mês de 30 dias continua, como aproximação declarada;
  - 13º quitado em 31/12, férias pendentes 0 / 0,5 / 1 e `fator_correcao_saldo_fgts` = 1,0 (suposição): aprovados.
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
  - ⚠ **INSS não incide sobre o aviso prévio indenizado.** A lei não o exclui expressamente; a não incidência vem da jurisprudência do STJ (Tema 478, confirmado depois; ver ajustes acima). O FGTS incide sobre o aviso (ele não está no § 9º do art. 28);
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

---

> Propostas acrescentadas em 2026-10-18 (tarde), na verificação final da Fase 1. **Nenhuma está aprovada nem implementada.** Números: `scripts/verificacao_fase1/` (Parquet de 09:52; motor reproduz o gold com diferença zero).

## D-019 — PROPOSTA: faixas de déficit sempre pela classe v2; a regra v1 só muda o universo
- **Data:** 2026-10-18
- **Contexto:** A1. Hoje a v1 reclassifica Classe 2/3 e recalcula o peso da indeterminada (0,932 × 0,678), e o prêmio cai com o universo maior.
- **Proposta:** `deficit()` recebe a classe v2 para as faixas; o peso da indeterminada é o da v2 nas duas regras; a v1 só decide quem entra. Teste de monotonicidade em min, base e max.
- **Impacto (base, mantém):** v2 sem mudança; v1: universo 1.545,2 → 1.538,3, déficit R$ 38,3 → 44,9 mi, prêmio R$ 382,9 → 448,8 mil.

## D-020 — PROPOSTA: data-base única 31/12/2025
- **Data:** 2026-10-18
- **Contexto:** A2. Art. 4º do 227: declaração "com base na posição de 31 de dezembro do exercício anterior". Art. 18: no primeiro ano só muda o **prazo** de entrega (30 dias da vigência), não a posição.
- **Proposta:** tudo em 31/12/2025 (tempo de casa e salário da RAIS, aviso, 13º quitado, férias); INPC dez/2025 → set/2026 vira sensibilidade ("valor atualizado para a data da declaração"), fora da base. Empregados seguem do CNJ (out/2026) por falta de contagem em 31/12/2025, como limitação (RAIS 31/12/2025 difere 1,8%). Rodapé com "data-base 31/12/2025".
- **Impacto (base v2):** −3,86% em passivo (R$ 343,4 → 330,1 mi todas; 256,5 → 246,6 mi obrigados), déficit (40,4 → 38,9), IS (20,2 → 19,4) e prêmio (404 → 389 mil).

## D-021 — PROPOSTA: probabilidade de déficit só onde o passivo é maior que zero
- **Data:** 2026-10-18
- **Proposta:** `n_deficit = peso × prob × [passivo > 0]`. **Impacto:** "com déficit" base 489,9 → 486,1 (min 277,8 → 275,7; max 738,3 → 732,0). Valores em R$ não mudam.

## D-022 — PROPOSTA: reserva da distribuição salarial pela região imediata do IBGE
- **Data:** 2026-10-18
- **Contexto:** C2. A distribuição "estado" usa todos os 10.978 vínculos de MG, com BH: R$ 24.951 por vínculo, contra R$ 13.842 nos municípios abaixo do limiar.
- **Proposta:** município (≥ 20 vínculos) → região imediata (≥ 20) → estado. Com isso os 716 municípios hoje "estado" passam todos a usar a região.
- **Impacto:** passivo de todas as ativas R$ 343,4 → 324,4 mi (−5,5%); só nos 716 municípios, R$ 90,0 → 71,0 mi. O efeito no universo será medido na implementação.

## D-023 — PROPOSTA: leitura do art. 16, § 1º, do 213 (receita para a Classe 1)
- **Data:** 2026-10-18
- **Texto (Prov. 243, art. 1º):** "O enquadramento da serventia será reavaliado anualmente, com base na média das receitas brutas semestrais do exercício imediatamente anterior". Classe 1: "receita bruta semestral não superior a R$ 300.000,00".
- **Leitura atual (`src/model/universo.py:24-30`):** média só dos semestres de 2025 com valor > 0; zero nos dois → indeterminada. Providos acima de R$ 300 mil: 1.103 (silver).
- **Proposta:** principal = média literal dos dois semestres de 2025, com o zero declarado contando como zero (1.087 providos no silver; −16); semestre **ausente** = desconhecido, usa o disponível com aviso; zero nos dois e conflito continuam indeterminados (D-013, D-014). Sensibilidade, na mesma tabela de v1 × v2: leitura atual, "dois semestres", "2º semestre", "algum semestre" (BI: 928 / 1.106 / 1.161 providos).

## D-024 — PROPOSTA: contrato de total de controle da arrecadação de MG
- **Data:** 2026-10-18
- **Contexto:** F2. Silver × BI (18/10/2026): 1º sem/2025 +0,24%; 2º sem/2025 +2,16%, dos quais R$ 62,7 mi vêm de 168 CNS que a API já tem e o BI ainda não (prazo prorrogado até 15/04/2026). Sem esses 168: +0,11%.
- **Proposta:** `config/qualidade.yaml` com o total de controle do BI por semestre; o contrato compara os CNS presentes nas duas fontes (tolerância 0,5%, erro) e lista à parte os CNS só na API (aviso).

## D-025 — PROPOSTA (etapa 2, discutir): sinistro por frequência × severidade
- **Data:** 2026-10-18
- **Contexto:** B1. A SES (0775/0776) é carteira de obras e contratos; o produto tem seleção adversa e o risco é o fim da delegação sem pagamento.
- **Proposta:** sinistro = P(fim da delegação no ano) × P(não paga | déficit) × parte paga da IS − recuperação; a SES fica como comparação. Para a P(fim), o cadastro do Justiça Aberta só tem a data da decisão da **situação atual** (VAGO por ano da decisão em MG: 2019 66; 2020 13; 2021 37; 2022 34; 2023 36; 2024 250; 2025 133), o que não basta para uma taxa (falta o histórico de quem voltou a ser provido). O cadastro do BI tem as datas; decisão do autor.

---

> Decisões finais sobre as propostas D-019 a D-025, conforme `docs/aprovacao_etapa1_fase1.md` (2026-10-18). O texto de cada proposta continua acima, sem alteração.

### D-019 — decisão final: APROVADA COM AJUSTE (2026-10-18)
- A classe usada nas faixas de déficit é sempre a da regra base (`versao_base` de `config/regras_classificacao.yaml`, hoje v2): coluna `classe_faixa` em `universo()`, usada por `deficit()`.
- **O peso da indeterminada continua recalculado por regra** (v1 0,932 × v2 0,678): ele mede a chance de uma serventia sem dado passar no corte de cada regra. A proposta de unificar o peso foi rejeitada pelo autor, com razão.
- **Suposição: na sensibilidade v1, serventias Classe 1 pela v2 recebem a faixa da Classe 2** (`FAIXA_POR_CLASSE` em `src/model/mercado.py`). Antes, isso acontecia por um padrão implícito da função `_faixa`; agora está explícito e testado.
- Monotonicidade testada em min, base e max (teste sintético e contrato no gold). Resultado com o peso por regra, base: prêmio v1 R$ 451,4 mil ≥ v2 R$ 404,4 mil (antes da A2 e da C2).

### D-020 — decisão final: APROVADA (2026-10-18)
- Texto literal do Prov. CNJ 227/2026 (cópia oficial em `data/bronze/normas/2026-10-17/prov_227_2026_pagina.txt`):
  - art. 4º: "A declaração do passivo trabalhista será apresentada até o dia 31 de março de cada ano, com base na posição de 31 de dezembro do exercício anterior, abrangendo todos os prepostos em atividade na serventia."
  - art. 18: "Excepcionalmente, no primeiro ano de vigência deste Provimento, as declarações de passivo trabalhista e de solvência trabalhista, previstas, respectivamente, nos arts. 4º e 8º, deverão ser apresentadas no prazo de 30 (trinta) dias contados da data de sua entrada em vigor."
- Data-base única **31/12/2025** em `config/premissas/premissas_v002.yaml` (a v001 fica no lugar). O INPC sai dos três níveis (min, base e max) e vira a linha "se a data-base fosse a da 1ª declaração" na tabela de sensibilidade (+4,01%).
- Escolha da IA a conferir pelo autor: o INPC também saiu do **máximo**, para que todos os níveis tenham a mesma data-base.
- Limitação: os empregados por serventia são a declaração ao CNJ de out/2026; servem só como peso do rateio.

### D-021 — decisão final: APROVADA (2026-10-18)
- `n_deficit = peso × prob × [passivo > 0]`. Base: 489,9 → 486,0 (arredondamento; esperado 486,1). Valores em R$ inalterados.

### D-022 — decisão final: APROVADA (2026-10-18)
- Reserva da distribuição: município (≥ 20 vínculos) → região imediata do IBGE (≥ 20) → estado. Medido depois da D-020: passivo de todas as ativas R$ 330,1 → 311,9 mi (−5,5%); **passivo dos obrigados R$ 246,6 → 238,1 mi (−3,4%)**; prêmio R$ 388,8 → 368,7 mil (−5,2%). A versão anterior (reserva direto no estado) fica como linha da tabela de sensibilidade.

### D-023 — decisão final: APROVADA COM AJUSTE (2026-10-18)
- **A leitura principal continua a atual** (média dos semestres com valor > 0, `src/model/universo.py:24-30`); o código do universo não foi alterado.
- Justificativa do autor: o texto mede a receita bruta real do exercício anterior, e o dado é a declaração ao CNJ, em que zero muitas vezes significa "não declarou" (168 CNS de MG ausentes do BI no 2º sem/2025; prazo prorrogado até 15/04/2026; ~50% enviado no fim de março, IRIB, 01/04/2026). Contar esse zero como receita erra para baixo e tira do universo serventias provavelmente obrigadas. Ignorar o semestre zerado e fazer a média dos semestres com valor é a melhor estimativa da receita real.
- Texto literal (Prov. 213, art. 16, § 1º, com a redação do Prov. 243): "O enquadramento da serventia será reavaliado anualmente, com base na média das receitas brutas semestrais do exercício imediatamente anterior, produzindo efeitos para o período subsequente, observados os prazos de adaptação previstos neste Provimento."
- As leituras alternativas ("zero conta como zero", "nos dois semestres", "em algum semestre") entram na tabela de sensibilidade (`src/model/leituras.py`). Limitação: 14 providos com 1º semestre > R$ 300 mil e 2º semestre zerado entram no universo pelo 1º semestre.

### D-024 — decisão final: APROVADA COM AJUSTE (2026-10-18)
- Contrato 1 (erro): o total de MG por semestre no silver não pode cair mais de 0,5% em relação ao registrado em `config/qualidade.yaml` (1º sem/2025 R$ 2.379.639.987,32; 2º sem/2025 R$ 3.133.904.766,00).
- Contrato 2 (aviso): silver × BI do CNJ (1º sem R$ 2.373.919.679,17, tolerância 1%; 2º sem R$ 3.067.663.494,52, tolerância 3%, porque o BI estava incompleto: 168 CNS de MG ausentes em 18/10/2026). Valores do BI no YAML com fonte, arquivo do bronze e data.

### D-025 — nota (2026-10-18): continua PROPOSTA (Etapa 2)
- O cadastro do BI **não** será trazido: as datas são de recadastramento (1.066 dos 1.654 providos de MG com ingresso em 2024; 250 vagas "decididas" em 2024) e o arquivo tem dados pessoais.
- A frequência de término da delegação será suposição com faixa. As 133 serventias de MG com decisão de vacância em 2025 (≈ 7% dos providos) entram só como indicador fraco de teto, não como estimativa.

## D-026 — Visões do Mercado com filtro e grupos do mapa (decisão do autor, revisao_painel_filtros.md)
- **Data:** 2026-10-18
- **Contexto:** a página Mercado lia `gold.interno_serventia` para os filtros, e a revisão achou vazamento por subtração entre visões (E1: BH 34 serventias × BH Classe 3 33 isolava 1 cartório).
- **Decisão (opção B, aprovada):**
  - sem filtro: municípios com 3+ serventias e grupos de municípios pequenos;
  - com filtro (um por vez): nível da região imediata, pré-agregado no gold, com supressão primária (recorte >= 3 **e** complemento 0 ou >= 3), hierárquica (região intermediária -> "outras regiões") e secundária (auditor de ataque por diferença, em ciclo até zerar; a carga falha se não zerar);
  - filtro de município: destaque com contexto (U1); município com menos de 3 mostra a área agregada a que pertence; município + filtro mostra só o nível regional;
  - o painel só lê tabelas públicas (exceção do Mercado removida do teste).
- **Grupos pequenos demais (2.2):** os 4 grupos de região imediata com menos de 3 serventias sobem para a região intermediária, somando-se ao menor grupo de pequenos de outra região imediata da mesma intermediária; não se juntam a município nomeado. O último caso ("Município X + N municípios pequenos") está implementado, mas não acontece em MG.
- **Ajuste da IA, achado pelo auditor:** RTD e RCPJ viram um só valor do filtro ("Títulos e Documentos / Pessoa Jurídica"). Em separado, a diferença entre os totais de MG isolava 2 serventias que têm RCPJ sem RTD.
- **Fonte:** `docs/revisao_painel_filtros.md`, seções 2.1 e 2.2; `src/model/supressao.py`, `src/transform/visoes.py`, `src/transform/geo.py`.

## D-027 — PROPOSTA: regra v1 e mínimo/máximo só nos totais de MG (vazamento E1-b)
- **Data:** 2026-10-18
- **Contexto:** a auditoria própria (seção 5) achou um segundo vetor do mesmo ataque: trocar a regra (v1 × v2) ou o nível (mínimo × base × máximo) muda QUEM entra no universo. A mesma área nas duas regras, subtraída, isola as serventias entre R$ 100 mil e R$ 300 mil; máximo − base isola as de intervenção/diligência; base − mínimo, as indeterminadas.
- **Decisão aplicada (aguarda confirmação do autor):** mapa, ranking e tabelas por área usam só o nível base e a regra base. A regra v1 e o mínimo/máximo aparecem só nos totais de MG (sem filtro e por filtro), e só onde o auditor aprovou. Suprimidos pelo auditor: Registro de Imóveis (v1 base, v2 mínimo, v2 máximo), Conversão em diligência (v2 máximo), indeterminada (v1 base, v1 máximo, v2 máximo). `gold.fato_mercado_municipio_publico` passou a ter só base e regra base.
- **Consequência:** a classe do filtro é sempre a da regra base (D-019); com a regra v1 escolhida, o painel avisa quando o filtro não pode mostrá-la.

### D-027 — decisão final: APROVADA (2026-10-18)
- Aprovada pelo autor como está (`docs/correcoes_e_qa_visual.md`, seção 1): por área, só nível base e regra v2; regra v1, mínimo e máximo só nos totais de MG, onde o auditor aprovar.

## D-028 — Partições internas de uma mesma visão não são suprimidas
- **Data:** 2026-10-18
- **Contexto:** numa mesma área, "passivo (todas)" − "passivo (obrigados)" dá o passivo das não obrigadas; outras partições internas da mesma visão permitem contas parecidas.
- **Decisão (do autor):** essas partições internas não serão suprimidas. O auditor de ataque por diferença continua como está (pares de visões e resto das partições dos filtros), sem ampliar.
- **Justificativa:** os insumos são públicos (contagens, empregados declarados e arrecadação do CNJ), e a limitação D2 já declara que a estimativa de cada cartório é recalculável a partir deles. A defesa do projeto é tratar-se de estimativa de mercado com premissas públicas.
- **Consequência:** frase acrescentada à limitação D2 na página Qualidade.
- **Fonte:** `docs/correcoes_e_qa_visual.md`, seção 1.2.

## D-029 — Conjunto público versionado e modo demonstração
- **Data:** 2026-10-19
- **Contexto:** quem clona o repositório público precisa ver o painel com os mesmos números da carga oficial, sem rodar a coleta (docs/repositorio_reproduzivel.md, 2.1 a 2.3).
- **Opções:** (a) versionar a própria `data/gold/`, com `interno_*` e `.duckdb` no `.gitignore`; (b) uma pasta `data/publico/`, atualizada de propósito por script.
- **Decisão (da IA, pela regra "a mais simples"):** opção (b).
  - Abaixo, (2) e (3) são os motivos de escolher (b) e não (a).
  - (1) Simplicidade: o painel também lê tabelas fora do gold (`silver.fonte_metadados`, `silver.municipio_ibge`, `qualidade.*` e a versão vigente das premissas), que a opção (a) não cobriria.
  - (2) Atualizar o conjunto público vira um ato explícito: o `scripts/gerar_publico.py` roda o auditor de ataque por diferença, os contratos de "sem dado pessoal" e de limiar e o limite de 20 MB. Ele procura os códigos CNS e os nomes do cadastro e grava o manifesto (carga, fontes, premissas, commit, SHA-256 do arquivo e do conteúdo).
  - (3) Os binários não mudam no git a cada carga de desenvolvimento.
- **Hash de conteúdo:** linhas ordenadas, sem os carimbos de execução. É diferente do hash do arquivo: compara números entre bancos gravados em horas diferentes. O `tests/test_publico.py` avisa "dados públicos desatualizados: rode scripts/gerar_publico.py" se o gold local mudar.
- **Ajustes exigidos pelo próprio gerador:**
  - `gold.dim_municipio` vai sem a coluna `clt`;
  - `qualidade.rec_municipio` deixou de publicar grupos de região imediata com 1 ou 2 serventias (4 grupos viraram uma linha "Outras regiões");
  - **exceção ao limiar** `gold.dim_municipio.n_serventias` (contagem do cadastro público, sem valor): **aprovada pelo autor** em 2026-10-19.
- **Modo demonstração:**
  - sem banco local, o painel monta um DuckDB temporário a partir de `data/publico`, com faixa e rodapé "demonstração";
  - "Salvar cenário" fica desativado.
- **Simulador sem dados internos:**
  - seguro, déficit e STF são recalculados exatamente a partir de totais por faixa (`gold.simulador_base_classe`, `src/model/simulador.py`);
  - o passivo usa uma grade de 80 variantes: regra × rateio × uma premissa do passivo por vez (`gold.simulador_variantes`, pontos em `config/simulador_demo.yaml`, fonte: suposição);
  - as células novas entram no auditor (0 vazamentos).
- **Pipeline:**
  - a malha do IBGE passou para o silver (`silver.malha_municipio`), para o gold se recalcular só com o silver;
  - `pipeline.py --a-partir-de bronze|silver`, com `--help` de verdade.
- **Fonte:** `docs/repositorio_reproduzivel.md` (2.1 a 2.4); `config/publico.yaml`; `src/publico.py`.

## D-030 — Dados da equipe e dados públicos em Releases; regra de LGPD do público corrigida
- **Data:** 2026-10-19
- **Desenho (decidido pelo autor):**
  - Release público `dados-AAAA-MM-DD` em `luccaamp/radar-seguro-cartorio`, com o silver e o manifesto;
  - Release privado `carga-AAAA-MM-DD` em `luccaamp/radar-seguro-cartorio-dados`, com o pacote completo: bronze por fonte, silver, gold com `interno_*` e banco, em partes abaixo de 2 GiB, com hashes.
- **Conflito achado:** a regra 0 do documento proibia "dado no nível de serventia" no público, mas o silver (arrecadação e CLT por CNS, vínculos da RAIS por município) ia no Release público.
- **Decisão do autor:** publicar o silver como está. A regra passa a ser: "no repositório e no Release públicos, nenhuma ESTIMATIVA do modelo no nível de serventia (passivo, déficit, probabilidade, IS, prêmio); dados de origem já publicados pelas fontes oficiais (CNJ, RAIS/PDET, Receita, IBGE, SUSEP) podem ir, desde que sem dado pessoal". Corrigida no documento e no `CLAUDE.md`.
- **Conferência pedida pelo autor:**
  - **sem dado pessoal:** 0 problemas, com 3.840 nomes do cadastro procurados;
  - **campos derivados do modelo:** nenhum no silver. Os mais próximos são bandeiras de limpeza, não estimativas, e ficam: `prazo_indeterminado` (do tipo de vínculo, D-009), `conflito_fonte`, `n_atribuicoes`. O empacotador retira automaticamente do pacote público qualquer coluna que case com `estimativas_do_modelo` (`config/publico.yaml`) e registra no manifesto.
- **Pacote da equipe:**
  - os `.COMT` extraídos da RAIS (6,2 GB) ficam fora, porque são deriváveis do `.7z`, que vai no pacote;
  - é gerado fora do OneDrive (cota gratuita).
- **Licença do código:** MIT (escolha do autor).
- **Fonte:** `docs/repositorio_reproduzivel.md` (2.5); `config/pacotes.yaml`; `scripts/empacotar_dados.py`; `scripts/baixar_dados.py`; `docs/publicacao.md`.

> Status conferido em 2026-10-19 (`docs/limpeza_projeto.md` 2.4): D-019 a D-024 têm decisão final; D-025 continua PROPOSTA (Etapa 2); D-026 e D-027 APROVADAS. As notas abaixo deixam explícito o status das três últimas, que não tinham linha própria.

### D-028 — status: APROVADA (decisão do autor, 2026-10-18)
- Decidida pelo autor em `docs/correcoes_e_qa_visual.md`, seção 1.2; texto da decisão acima.

### D-029 — decisão final: APROVADA (2026-10-19)
- Proposta e aplicada pela IA (opção b, `data/publico/`); aprovada pelo autor em `docs/limpeza_projeto.md`, seção 1, junto com os dois ajustes de LGPD (`rec_municipio` e `dim_municipio`) e a exceção do `dim_municipio.n_serventias`.

### D-030 — status: APROVADA (decisão do autor, 2026-10-19)
- Desenho decidido pelo autor em `docs/repositorio_reproduzivel.md` 2.5; regra de LGPD do público corrigida pelo autor; licença MIT aprovada (`docs/limpeza_projeto.md`, seção 1).

## D-031 — Vínculos da RAIS no silver público, só com as colunas que o pipeline usa
- **Data:** 2026-10-19
- **Contexto:** o `silver.rais_vinculo` vai no pacote público (D-030). Não tem nome nem CPF, mas, num município com 1 cartório e 1 empregado, o vínculo revela o salário daquela pessoa.
- **Decisão (do autor):** manter no público. O mesmo dado já está nos microdados públicos da RAIS (PDET), filtráveis por CNAE e município; redistribuir não acrescenta exposição (mesma lógica da D-028).
- **Condição (do autor):** o pacote público leva só as colunas que o pipeline usa.
- **Conferência da IA:**
  - colunas do silver: `id_vinculo`, `ano_base`, `ativo_31_12`, `tipo_vinculo`, `tipo_estabelecimento`, `rem_dezembro`, `rem_media`, `tempo_emprego_meses`, `horas_contratadas`, `mes_admissao`, `mes_desligamento`, `cbo`, `prazo_indeterminado`, `cod_ibge`;
  - não há CNPJ, CAEPF, data de nascimento, raça nem sexo (o filtro do silver já descartava esses campos do arquivo da RAIS);
  - o pipeline usa 8: `id_vinculo` (contrato de chave), `cod_ibge`, `ativo_31_12`, `tipo_vinculo`, `prazo_indeterminado` (contrato), `rem_dezembro`, `rem_media` e `tempo_emprego_meses` (`src/model/distribuicao.py`, `src/quality/contratos.py`, `src/quality/reconciliacao.py`);
  - saem do pacote público as outras 6: `ano_base`, `tipo_estabelecimento`, `horas_contratadas`, `mes_admissao`, `mes_desligamento` e `cbo`. Ocupação e meses de admissão e desligamento ajudam a identificar a pessoa num município pequeno e não entram em nenhuma conta.
- **Onde:** `config/publico.yaml` (`silver_publico_remover`), aplicado por `scripts/empacotar_dados.py`. O silver interno, o do pacote da equipe e o banco ficam iguais.
- **Prova:** pacote público novo → `pipeline.py --a-partir-de silver` num clone fora do OneDrive → 25 de 25 tabelas com o mesmo hash de conteúdo do conjunto público.
- **Ajuste necessário:** a lista de contratos do silver não pode depender das colunas presentes (ver `docs/erros_ia.md`, 2026-10-19).

## D-032 — Bronze enxuto: extrato + registro do original; originais fora do OneDrive
- **Data:** 2026-10-19
- **Contexto:** o bronze tinha 14,9 GB, dos quais 14,76 GB eram originais grandes (zips do CNPJ, `.7z` e `.COMT` da RAIS, `BaseCompleta.zip` da SUSEP). O silver lê só os extratos filtrados, e o pacote da equipe chegava a 8,4 GB.
- **Decisão (aprovada pelo autor em 2026-10-19, `docs/historico/limpeza_projeto.md`, Parada 1):**
  - **(a) Coletor da RAIS corrigido:** passa a detectar o separador, porque o `.COMT` de 2025 vem separado por vírgula. Exceção aprovada ao princípio 5 da limpeza.
  - **(b) Originais fora do bronze oficial:** os coletores de RAIS, CNPJ e SUSEP baixam os originais para uma pasta fora do OneDrive, configurável (`config/pacotes.yaml`, `pastas.originais`; padrão `C:\radar_arquivo\bronze_originais\`; variável `RADAR_ORIGINAIS`). No bronze gravam só o extrato e o `original.json` (URL oficial, SHA-256, tamanho, data e hora de coleta, onde foi guardado). O silver lê a URL e a hora de coleta do `original.json` quando o original não está no bronze.
  - **(c) Originais movidos, não apagados:** 27 arquivos (14.757,5 MB) foram para `C:\radar_arquivo\bronze_originais\`, com o `MANIFESTO.md`. O SHA-256 de cada um foi conferido depois de mover.
  - **(d) Pacote com originais:** `empacotar_dados.py --com-originais` inclui os originais (camada `originais`, em partes abaixo de 2 GiB). O `baixar_dados.py` os instala na pasta de originais.
  - **(e)** registro desta decisão.
- **Provas:**
  - regerar cada extrato a partir do original guardado dá o mesmo SHA-256 (RAIS, SUSEP e CNPJ; `tests/test_coletores.py`, `dados_reais`);
  - pipeline do zero a partir do bronze enxuto: 25/25 tabelas do gold e 25/25 públicas idênticas à linha de base, os 10 números iguais e `data/publico` intacto (26/26 arquivos);
  - ausência do P3 e a combinada da D-032, numa cópia: 25/25 e 25/25, com o `fonte_metadados` igual graças ao `original.json`.
- **Tamanhos:** bronze oficial de 14,9 GB para 144 MB. Os originais (14,8 GB) passam a ter **uma única cópia local**, em `C:\radar_arquivo\`; as fontes podem trocar o arquivo publicado. **Backup externo a cargo do autor.**
- **Mantidos no bronze:** ANOREG, normas, STF (fontes do chat, Fase 3), CSV do BI do CNJ (verificações), cadastros das outras 26 UFs (Fase 2), layouts da RAIS, os `_metadados.json` originais e o `ses_cias.csv`.
