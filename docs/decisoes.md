# Registro de decisões

Cada decisão de interpretação ou de modelagem que afeta números do painel ou do chat. **Ordem:** a D-001 a D-018 ficaram com a mais recente no topo; da D-019 em diante, cada decisão nova entra **no fim** do arquivo (as notas de decisão final e de status ficam logo depois das propostas a que se referem). Nada é reordenado.
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

## D-033 — Projeto sai do OneDrive para `C:\projetos\radar-seguro-cartorio`
- **Data:** 2026-10-20
- **Contexto:** desde a Sessão 0, o projeto ficava em `C:\Users\<usuario>\OneDrive\Área de Trabalho\<pasta-antiga>` (decisão do autor; `docs/diario.md`, Fase 0). O OneDrive causou problemas repetidos na Fase 1 e na limpeza:
  - segurou pastas recém-alteradas e impediu renomear e apagar (WinError 183 e 5; `docs/erros_ia.md`, 2026-10-19);
  - negou acesso a pastas do `.venv` durante o `uv remove` (`docs/erros_ia.md`);
  - o "Á" de "Área de Trabalho" quebrou um `.ps1` no PowerShell 5.1 (`docs/erros_ia.md`);
  - deixou pastas vazias que não puderam ser apagadas (`pacotes/`, `docs/qa/antes/`, `data/publico.antigo/`, `data/publico.novo/`);
  - obrigou a gerar pacotes e originais fora do projeto para não estourar a cota gratuita.
- **Opções:** (a) manter no OneDrive e contornar caso a caso (risco já previsto no SPEC, §riscos); (b) mover o `.venv` para fora com `UV_PROJECT_ENVIRONMENT`; (c) mover o projeto inteiro para uma pasta local sem sincronização.
- **Decisão (do autor):** (c). O projeto passa para `C:\projetos\radar-seguro-cartorio`: caminho curto, sem espaço, sem acento e fora do OneDrive.
- **O que não muda:**
  - pacotes em `C:\radar_pacotes` e originais em `C:\radar_arquivo\bronze_originais` (`config/pacotes.yaml`), fora da pasta do projeto, para o clone continuar leve e nada grande ser adicionado ao git por engano;
  - a regra de nunca apagar dado do bronze, silver ou gold sem aprovação (retirar = mover para `C:\radar_arquivo`);
  - o código: não há caminho absoluto do projeto em `src/`, `app/`, `tests/`, `scripts/` nem `config/` (conferido em 2026-10-20).
- **Como mover:** clone novo do GitHub na pasta nova, mais a cópia, com `robocopy`, do que não está no git (dados, banco, notebooks privados, `docs/qa/`, `conversas/`, `.claude/settings.local.json`). O `.venv` não é copiado: é recriado com `uv sync` (se falhar com hardlink, `UV_LINK_MODE=copy`, `docs/diario.md`).
- **Justificativa:** o OneDrive não faz parte da reprodutibilidade (o backup do código é o GitHub; o dos dados, os Releases e o backup externo de `C:\radar_arquivo\`), e os bloqueios de sincronização já custaram retrabalho e erros registrados.
- **Histórico:** as menções a "fora do OneDrive" em `docs/diario.md`, `docs/erros_ia.md`, `docs/historico/` e nas conversas ficam como estão, porque descrevem o que aconteceu na época.

## D-034 — O painel só lê o banco do pipeline; cenários salvos em arquivo próprio
- **Data:** 2026-10-20
- **Contexto:** o painel abria `data/radar.duckdb` para gravação (`app/comum.py`, `_abrir`). Levantamento do que ele gravava (linhas do commit `eba593b`, antes da mudança):
  - ao abrir qualquer página: `estado.garantir_tabelas` (cria o esquema `estado` e as tabelas `premissas_versoes` e `cenarios_salvos`, e insere a semente se faltasse; `app/comum.py:72` → `src/estado.py:51-61`);
  - no botão "Salvar" do Simulador: `estado.salvar_versao` (uma **versão nova de premissas** quando algum controle mudou; `app/pages/2_Simulador.py:282` → `src/estado.py:77-83`) e `estado.salvar_cenario` (`2_Simulador.py:283` → `src/estado.py:86-91`).
- **Consequências achadas:**
  - a versão criada pelo Simulador virava a "vigente": a **carga seguinte** calcularia o gold oficial com ela (`src/transform/gold.py:220`), o Início mostraria o teto com a taxa do cenário, o conjunto público publicaria essa versão (`config/publico.yaml`, `estado.premissas_vigente`) e a linha de base leria essa taxa. Não aconteceu: o banco real só tem as sementes v1 e v2 e nenhum cenário salvo (conferido em 2026-10-20);
  - com o painel aberto para gravação, nenhum outro programa conseguia ler o banco (o pipeline falhava logo no início, e também os notebooks, o empacotador e a linha de base).
- **Opções para o arquivo:** (a) JSON; (b) SQLite; (c) outro DuckDB.
- **Decisão (pedido do autor; formato proposto pela IA):**
  - o painel abre o banco sempre com `read_only=True`, também no modo demonstração;
  - os cenários salvos vão para **`data/painel_estado.json`** (opção a; variável `RADAR_ESTADO` para testes e galeria), no `.gitignore` e fora dos pacotes (camadas explícitas em `config/pacotes.yaml`) e do conjunto público. Formato e regras em `src/cenarios.py`;
  - arquivo ausente: o painel cria no primeiro "Salvar". Arquivo corrompido: o painel abre com um aviso e a lista vazia; no próximo "Salvar", o arquivo ruim é **movido** (não apagado) para `painel_estado.json.corrompido-AAAAMMDD-HHMMSS`. A gravação é atômica (temporário + troca), com uma trava por processo;
  - **o painel não cria mais versão de premissas.** O cenário guarda a versão vigente do banco e o diff das premissas alteradas sobre ela. Só o pipeline grava versões, a partir das sementes de `config/premissas/`;
  - o pipeline confere **antes de começar** se o banco está aberto por outro programa (`pipeline.em_uso`, só no Windows: abertura exclusiva que não altera nada). Se estiver, para sem gravar banco nem Parquet.
- **Justificativa:** o banco é o resultado reproduzível do pipeline; estado pessoal dentro dele mudava o SHA-256 a cada uso e podia mudar os números oficiais. JSON porque são poucos registros, só um gravador (o painel), leitura fácil, biblioteca padrão e detecção simples de corrupção. SQLite e DuckDB resolveriam a concorrência entre processos, mas é um caso raro aqui.
- **Concorrência (medida na cópia, 2026-10-20):**
  - painel aberto → pipeline: para em cerca de 1 s com "feche e rode de novo. Nada foi alterado";
  - pipeline rodando → painel aberto no meio: o painel abre normalmente (lê o banco anterior); no fim, a troca do banco falha (Windows), o banco anterior fica intacto e o temporário é apagado;
  - painel fechado → pipeline: normal;
  - dois leitores (painel e notebook) ao mesmo tempo: ok.
- **Limitações:**
  - no segundo caso, os Parquet de `data/silver` e `data/gold` já foram regravados pela carga que não trocou o banco. A mensagem avisa, e rodar de novo com o painel fechado os iguala. **Pendência do Bloco 2 (decisão do autor):** avaliar se o pipeline deve gravar também os Parquet numa pasta temporária e só trocar no fim, como já faz com o banco;
  - o painel aberto impede a carga até ser fechado;
  - dois processos do painel salvando no mesmo instante podem perder um dos dois cenários (a trava é por processo), mas o arquivo nunca fica pela metade.
- **Tabela antiga `estado.cenarios_salvos` (decisão do autor):** não é apagada do banco agora. O pipeline deixou de criá-la (`estado.criar_tabelas`) e de copiá-la do banco anterior (`estado.TABELAS_ESTADO` = só `premissas_versoes`), então ela some na próxima carga. Provado numa cópia: antes da carga, `cenarios_salvos`, `log_decisoes` e `premissas_versoes`; depois, só as duas últimas, com os 10 números e os 25 + 25 hashes iguais. Teste: `tests/test_pipeline.py::test_carga_preserva_estado_nao_cresce_e_e_reprodutivel`.
- **Modo demonstração:** sem mudança de comportamento ("Salvar" continua desativado). Ativar fica para o **redesenho do painel** (decisão do autor).
- **SPEC:** §2.1 e §2.4 atualizados (estado do app fora do banco).
- **Testes:**
  - `tests/test_cenarios.py`: ausente, corrompido, reinício, gravação atômica;
  - `tests/test_app_codigo.py`: toda conexão do painel é `read_only` e não há SQL que grava;
  - `tests/test_pipeline_cli.py`: `em_uso` e a carga que para antes de começar;
  - `tests/test_app_demo.py`: SHA-256 do banco de demonstração igual;
  - `tests/test_app.py` (`dados_reais`): SHA-256 igual depois de abrir as páginas e salvar, cenário presente depois de reiniciar, banco com atributo de somente leitura; `test_simulador_salva_cenario_sem_nova_versao` (Fase 1) mantido, com as verificações apontando para o arquivo de cenários;
  - `tests/test_pipeline.py::test_carga_preserva_estado_nao_cresce_e_e_reprodutivel` (`dados_reais`): mantido; em vez de um cenário na tabela antiga, confere que as versões de premissas são preservadas e que `estado.cenarios_salvos` não existe depois da carga.

## D-035 — ROADMAP como fonte do plano; papéis e níveis dos documentos
- **Data:** 2026-10-21
- **Contexto:** o autor criou o `docs/ROADMAP.md`. A análise de contradições pedida pelo autor (C1 a C15, F1 a F8), revisada pelo revisor do autor, mostrou que o `CLAUDE.md`, o `SPEC.md` (§8), o `ESTADO_ATUAL.md` e o plano de qualidade ainda diziam outra coisa sobre a ordem e o papel de cada documento.
- **Decisão (do autor):**
  - **o ROADMAP é a fonte do plano** (etapas, ordem, entregáveis, critério de pronto, pendências); o SPEC é o desenho técnico; o ESTADO_ATUAL é a foto de agora e a fonte dos valores dos 10 números;
  - **hierarquia em caso de conflito:** `CLAUDE.md` > `ROADMAP.md` > `SPEC.md`;
  - **níveis dos documentos:**
    1. núcleo, lido no início de toda sessão: `CLAUDE.md`, `docs/ESTADO_ATUAL.md`, `docs/ROADMAP.md`;
    2. referência, consultada quando a etapa toca no assunto: `docs/SPEC.md`, `docs/decisoes.md`, `docs/dicionario_dados.md`, `docs/plano_qualidade_e_correcoes.md` (só na E1 e na E2; vira histórico depois);
    3. registros, só acrescentam: `docs/diario.md`, `docs/erros_ia.md`;
    4. pontuais: `docs/publicacao.md`, `CONTRIBUTING.md`, `README.md` (raiz), `notebooks/README.md`, `docs/README.md` (índice);
    - históricos: `docs/historico/`;
  - **ordem das etapas:** E1 → E2 → E3 → E3.5 → E3b → E4 → E5, com a E6 em paralelo com a E5, e depois a E7; substitui a "nova ordem" do SPEC §8 (2026-10-20);
  - **Radar:** etapa **opcional** depois da E5, a primeira a cortar;
  - **Entrega:** não é uma etapa só no fim; é um pacote por marco (mínimo no `v1.0`, atualizado no `v1.1` e a cada UF);
  - **fluxo da E1:** diagnóstico de Q1 a Q11 (só leitura) → uma parada com a tabela de efeitos → aprovação item a item → implementação, com Q8 e Q4 primeiro;
  - **normas:** no início de cada etapa, a IA confere a ADI 8015 e alterações nos Provimentos 213, 227 e 243; isso substitui o monitoramento que a D-001, a D-002 e o SPEC §10 atribuíam ao radar;
  - **histórico:** `docs/prompts.md` (superado pelo ROADMAP; o procedimento de salvar conversas foi para o `CONTRIBUTING.md`) e `docs/viabilidade.md` (resultado da Fase 0) foram para `docs/historico/` (`git mv`);
  - ao fechar cada etapa, antes do commit, verificação de contradições entre os documentos dos níveis 1 e 2.
- **Justificativa:** um plano só, em um lugar, evita que a ordem e as pendências fiquem desatualizadas em vários documentos; cada documento passa a ter um papel e um nível de leitura.
- **Consequências / onde aparece:** `CLAUDE.md`, `docs/ROADMAP.md`, `docs/ESTADO_ATUAL.md`, `docs/SPEC.md` (§8 resumido), `docs/README.md` (índice), `docs/plano_qualidade_e_correcoes.md` (nota no topo), `CONTRIBUTING.md`, `docs/historico/`. As decisões da E1 começam na **D-036**.
- **Fonte:** pedido do autor em 2026-10-21 ("rodada de harmonização dos documentos").

## D-036 — Chat no painel antes da E1 (E5 reduzida) e o desenho das ferramentas
- **Data:** 2026-10-21
- **Contexto:** o autor pediu o chat de IA no painel como o primeiro bloco depois da harmonização ("Bloco 1: chat de IA no painel (E5 reduzida)"), antes da E1, e passou a trabalhar com um bloco por sessão e uma parada só no fim.
- **Decisão (do autor):** a E5 reduzida vem antes da E1. O restante da E5 (gabarito de 40 a 60 perguntas congelado, versão (b) com as normas no prompt, as duas ferramentas que faltam, o acerto mínimo) continua na E5 do ROADMAP. A primeira decisão da E1 passa a ser a D-037.
- **Escolhas da IA nos detalhes (o autor pediu que decida sozinha os detalhes pequenos):**
  - modelo `qwen3:8b` no Ollama local, sem raciocínio longo (`think: false`), temperatura 0, contexto 8.192 (`config/llm.yaml`, suposição de partida); reserva `llama3.1:8b`;
  - acesso ao Ollama só por `src/llm.py`, com `httpx` (sem dependência nova; o Pydantic continua fora);
  - 5 ferramentas (SPEC §5.2), todas sobre tabelas do conjunto público, com a UF como parâmetro, valores já formatados e a linha "Fonte" (carga e versão das premissas) em cada resultado; a busca de normas é por palavras, sem embeddings, sobre o texto oficial do bronze;
  - sem Ollama, a página Chat aparece desativada com a explicação, e o resto do painel segue;
  - a avaliação usa o banco de demonstração montado a partir do `data/publico` (nunca o banco real) e uma correção automática simples (`src/agent/avaliacao.py`); o gabarito de 20 perguntas é rascunho, a revisar pelo autor.
- **LGPD:** as ferramentas não recebem CNS nem nome de cartório e só leem tabelas publicadas; o teste `tests/test_chat.py` falha se o código do chat citar uma tabela fora do `config/publico.yaml` ou uma tabela interna.
- **Fonte:** pedido do autor em 2026-10-21; `docs/historico/viabilidade.md`, §3 (modelo).

## D-037 — Documentos simplificados; o documento da etapa manda
- **Data:** 2026-10-22
- **Contexto:** os documentos de plano (ROADMAP, plano de qualidade, índice de `docs/`) cresceram e se repetiam; cada sessão precisava ler muita coisa antes de trabalhar. O autor escreveu o `docs/plano_mineracao.md` como documento único da etapa seguinte.
- **Decisão (do autor):**
  - em cada sessão, a IA lê só o `CLAUDE.md`, o `docs/ESTADO_ATUAL.md` e **o documento da etapa** que o ESTADO_ATUAL indica (hoje, `docs/plano_mineracao.md`); se o documento já traz o plano, a IA executa sem pedir aprovação e para no fim da parte pedida;
  - o `CLAUDE.md` fica só com as regras de segurança (git, 100% gratuito, dados, cópia do banco, LGPD); saem as regras de "ordem do ROADMAP", de "notebooks privados" e de "biblioteca só com aprovação";
  - **todos os notebooks vão para o git**, inclusive os que leem `interno_*`, sem saídas (`nbstripout`) e sem citar um cartório específico no texto (nome, CNS ou valor de um cartório); a pasta `notebooks/privado/` deixa de existir;
  - `docs/ROADMAP.md` e `docs/plano_qualidade_e_correcoes.md` vão para `docs/historico/` (`git mv`); não há mais `docs/README.md` (índice);
  - ficam vivos: `SPEC.md`, `dicionario_dados.md`, `publicacao.md` e os registros (`decisoes.md`, `diario.md`, `erros_ia.md`).
- **Consequências / onde aparece:** `CLAUDE.md`, `docs/ESTADO_ATUAL.md`, `docs/plano_mineracao.md`, `notebooks/README.md`, `CONTRIBUTING.md`, `src/notebooks.py`, `.gitignore`, `tests/test_notebooks.py` (o teste "notebook versionado não usa `interno_*`" virou "o texto não cita o CNS de um cartório"), `tests/test_links_docs.py` (o teste do índice de `docs/` virou o do índice do histórico mais "o ESTADO_ATUAL aponta para o documento da etapa"). Substitui a parte da D-035 sobre o ROADMAP como fonte do plano e os níveis dos documentos. A D-036 dizia que a primeira decisão da E1 seria a D-037; com esta decisão, a próxima livre é a **D-038**.
- **Fonte:** pedido do autor em 2026-10-22 ("limpeza dos documentos").

## D-038 — Estudo público: sem restrições de publicação, exceto nome e CPF
- **Data:** 2026-10-22
- **Contexto:** as regras de publicação (D-026 a D-030, D-037) tratavam as estimativas por serventia como dado interno. O autor decidiu que o projeto é um estudo público, feito com dados públicos do governo.
- **Decisão (do autor):** saem dos documentos as restrições de publicação: mínimo de 3 serventias, auditor obrigatório para coisa nova, proibição de `interno_*` no painel e no chat, "nada por serventia no público", notebooks sem saída e a separação entre o público e a equipe. Tudo pode ir para o git e ser público, inclusive os resultados por cartório. Ficam só estas regras:
  - a IA não faz commit nem push sem pedido do autor;
  - a IA não apaga dados;
  - 100% gratuito;
  - não mostrar nome nem CPF de pessoa física.
- **Escopo desta sessão:** só documentos e testes. O pipeline, o auditor e o `gerar_publico.py` ficam como estão (o painel continua com a supressão de áreas pequenas e o conjunto público atual) até um pedido do autor; mudar agora quebraria o painel.
- **Escolhas da IA nos detalhes:** as regras de qualidade dos dados do `CLAUDE.md` (fonte em todo número, premissas em `config/`, cópia do banco, ferramenta de edição) continuam, porque não são restrições de publicação; o cartório é identificado pelo CNS e pelo município, nunca pelo nome do responsável (o bronze do CNJ traz esses nomes); os PNGs de `docs/qa/analises/` passam a ir para o git; o `nbstripout` continua como dependência de dev, sem o filtro instalado.
- **Consequências / onde aparece:** `CLAUDE.md`, `CONTRIBUTING.md`, `notebooks/README.md`, `docs/plano_mineracao.md` (§2 e §6), `src/notebooks.py` (docstring), `.gitignore`, `tests/test_notebooks.py` (saem "sem saída" e "não cita o CNS"; entra "nenhum CPF no texto, no código e nas saídas"), `tests/test_app_codigo.py` e `tests/test_chat.py` (saem as checagens de `interno_*`; fica a do chat ler só tabelas do conjunto público, porque o chat também roda no banco de demonstração). Filtro do git removido com `uv run nbstripout --uninstall`. Substitui, nas partes de publicação, a D-026, a D-027, a D-028, a D-030 e a D-037.
- **Fonte:** pedido do autor em 2026-10-22.

## D-039 — Plano do projeto como plano oficial; o plano da mineração vira o detalhamento da Etapa 1
- **Data:** 2026-10-23
- **Contexto:** depois da parte A da mineração, foi escrito o `docs/plano_projeto.md`: o caminho até a entrega em seis etapas (mineração, pipeline, painel, simulador, chat, entrega), com portões, riscos e as decisões do autor com o momento de cada uma. Antes, foram testados de 3 a 7 métodos para cada um dos sete pontos que dependem de estimativa (testes T1 a T7, `scripts/testes_metodos.py`, semente 42), com os dados reais de MG e um indicador fixado antes de rodar. Os resultados estão em `docs/qa/analises/testes_metodos.md` e no `testes_metodos_resultados.json` ao lado, e se reproduzem byte a byte.
- **Decisão (proposta; vale com a aprovação do autor no pull request):**
  - o `docs/plano_projeto.md` passa a ser o **plano oficial** do projeto; o `ESTADO_ATUAL.md` aponta para ele e para o documento da etapa em curso;
  - o `docs/plano_mineracao.md` **não é arquivado**: vira o detalhamento da Etapa 1 (regras, formato dos notebooks, critérios de qualidade, partes A, B e C), coerente com o plano do projeto; em conflito, vale o `plano_projeto.md`;
  - os métodos dos notebooks 05 a 08 são os vencedores dos testes: floresta aleatória no 05a (T4), no 05b (T3, recalibrada com 2022–23) e no 06a (T1); tendência log-linear com semestre no 07 (T2); Monte Carlo triangular e tornado no 08 (T7); as alternativas da D-015 (T5) e da D-022 (T6) entram como sensibilidade;
  - o 06b passa de "regressão do passivo pela receita e pelos empregados" para a decomposição do passivo em quantidade, salário e tempo de casa;
  - as tabelas `gold.analise_*` são desenhadas nos notebooks (função em `src/analise/` com teste) e geradas pelo pipeline na Etapa 2 (antes, na parte C da mineração);
  - entram no projeto o `scikit-learn`, o `statsmodels` e o `mlxtend`.
- **Efeito nos 10 números:** nenhum. Os testes só leem dados; toda mudança de base continua exigindo uma decisão nova do autor.
- **Consequências / onde aparece:** `docs/plano_projeto.md` (novo), `docs/plano_mineracao.md` (reescrito), `docs/ESTADO_ATUAL.md`, `docs/qa/analises/testes_metodos.md` e `testes_metodos_resultados.json` (novos), `scripts/testes_metodos.py` (novo), `pyproject.toml` e `uv.lock`. O `docs/historico/ROADMAP.md` continua como referência; as etapas E3.5, E3b, E6 e E7 dele passam a "depois da entrega, opcional" no plano do projeto. Substitui a parte da D-037 que dizia que o `plano_mineracao.md` era o documento único da etapa.
- **Fonte:** pedido em 2026-10-23; aprovação do autor pendente.

## D-040 — Qualquer colaborador pode fazer o merge na `main`
- **Data:** 2026-10-23
- **Contexto:** o `CONTRIBUTING.md` dizia que "o merge é feito pelo autor depois da revisão", mas a ruleset `main protegida` já exige só um pull request, com 0 aprovações (`docs/publicacao.md`, seção 4), e os colaboradores têm permissão de escrita. A regra escrita era mais restrita que a técnica.
- **Decisão (proposta; vale com a aprovação do autor no pull request):** qualquer colaborador pode fazer o merge de um PR na `main`, inclusive do próprio, depois de cumprir a lista "Antes de abrir o PR" do `CONTRIBUTING.md`. Continuam: nada de push direto nem force-push na `main`; mudar um dos 10 números exige decisão nova do autor (`plano_projeto.md`, Etapa 2).
- **Consequências / onde aparece:** `CONTRIBUTING.md` ("Fluxo de trabalho", item 2). Nenhuma mudança no GitHub: a ruleset já permite. O `CLAUDE.md` não muda: a IA continua sem fazer merge nem `gh pr merge`.
- **Fonte:** pedido em 2026-10-23; aprovação do autor pendente.

## D-041 — Push direto na `main` e Claude sem restrição de git a pedido do colaborador
- **Data:** 2026-10-23
- **Contexto:** a D-040 manteve "nada de push direto na `main`" e o `CLAUDE.md` proibia a IA de fazer `merge`, `gh pr merge` e outros comandos sem pedido do autor. O grupo quer um fluxo mais direto.
- **Decisão:** (1) qualquer colaborador pode dar commit e push direto na `main`, sem pull request; branch e PR continuam opcionais. (2) Quando um colaborador pedir na mensagem atual, o Claude pode executar `commit`, `push`, `merge` e qualquer outro comando de `git` ou `gh` pedido, sem restrição. Sem pedido na mensagem atual, a IA não altera histórico nem branch. As regras de gratuidade e de dados do `CLAUDE.md` continuam. Substitui a parte da D-040 sobre push direto e o trecho "a IA continua sem fazer merge".
- **Consequências / onde aparece:** `CLAUDE.md` (seção Git), `CONTRIBUTING.md` ("Fluxo de trabalho"), `docs/publicacao.md` (seção 4, aviso). Conferido em 2026-10-23 pela API do GitHub: não há ruleset nem proteção ativa na `main`, então o push direto já é possível; a ruleset `main protegida` de 2026-10-20 não aparecia mais. Foi recriada no mesmo dia só com *Restrict deletions* e *Block force pushes* (ver `docs/publicacao.md`, seção 4).
- **Fonte:** pedido do colaborador na conversa com a IA em 2026-10-23; aprovação do autor pendente.

## D-042 — Como os resultados dos notebooks 06 e 08 entram no painel
- **Data:** 2026-10-23
- **Contexto:** os notebooks 06 (regressão) e 08 (sensibilidade e concentração) deixaram quatro achados que mudam a forma de mostrar os números, sem mudar nenhum deles: a faixa P5–P95 do Monte Carlo (R$ 206 a 736 mil) é cerca de 4,4 vezes mais estreita que os cantos; a receita líquida do repasse (Prov. 213, art. 2º, XXIV) tira 20% do universo; as alternativas do T5 e do T6 mexem menos de 2% no passivo; e o CLT estimado pela receita erra 9,3% no total de uma região (até 26%), mas só 2,5% no total de MG.
- **Decisão (proposta; vale com a aprovação do autor):**
  1. **Faixa do prêmio: base > P5–P95 > cantos.** O valor base continua em destaque (é um dos 10 números). Logo abaixo, a "faixa provável" P5–P95 arredondada (R$ 210–740 mil), rotulada "faixa dentro das suposições", nunca "intervalo de confiança": mede a incerteza dentro das faixas da D-016, não o risco de elas estarem erradas. Vale para o déficit, a IS e o prêmio (números 7, 8 e 9). Variante principal: suposições independentes; a "patrimônio junto" (R$ 155–906 mil) fica na tabela de sensibilidade. Os cantos viram nota secundária (tooltip ou página Qualidade), como "extremos teóricos (todas as suposições no limite ao mesmo tempo)", com os **cantos oficiais** (R$ 24,7 mil a R$ 2,79 mi); o rodapé explica que o Monte Carlo segura o passivo no nível base, e por isso os cantos dele (R$ 27 mil a R$ 2,37 mi) são outros. O tooltip explica que o base fica abaixo da mediana (R$ 403 mil) e que 59% dos sorteios dão mais que ele.
  2. **Receita líquida como sensibilidade, com a faixa de déficit da classe da base**, como na D-019: a leitura alternativa muda só quem entra no universo, não a chance de déficit de quem fica (com a faixa pela receita líquida, universo menor daria prêmio maior, contra o teste de monotonicidade da D-019). Resultado: universo 1.121 → 894 (−20%), prêmio R$ 337,4 mil (−8,5%). A versão com a faixa pela receita líquida (+3,3%) fica só como nota no notebook. No painel, entra na página Qualidade, rotulada "leitura literal do art. 2º, XXIV (aproximada: o repasse do BI cobre só o inciso XXVI; o inciso XXV não tem fonte, então mais serventias sairiam)". Não vai para a base (falta o inciso XXV e o BI de 2025-2 está incompleto; D-002 mantida).
  3. **T5 e T6 só na tabela de sensibilidade**, sem controle no Simulador, num bloco "Passivo: escolhas de método" com três linhas: T5 (+0,6%), T6 (−1,6%) e a reserva no estado inteiro (+5,9%, já no gold). Frase do bloco: "o passivo varia de −1,6% a +5,9% conforme o método; a escolha da reserva pesa mais que os detalhes". Nota do T5: dos 887 vínculos, 733 não têm remuneração no ano e podem ser afastados que nem deveriam entrar no passivo. D-015 e D-022 continuam na base.
  4. **Empregados de outros estados: só o total estadual**, com ±10% tratado como **piso**, não garantia (vem de MG prevendo MG; um estado com capital grande pode sair baixo, como a região de BH, −18%). Nenhum mapa nem ranking estimado. Ao lado, o total de vínculos da RAIS (CNAE 6912) como conferência; se os dois divergirem mais de 10%, o painel avisa (em MG, RAIS × CNJ difere 1,8%, D-006; no Brasil, RAIS ÷ ANOREG dá 1,12, então em outros estados a RAIS pode contar a mais). A regra vale desde já, mas a expansão continua para depois da entrega.
- **Efeito nos 10 números:** nenhum. Os itens 1 a 3 mudam a apresentação e a tabela de sensibilidade; o item 4 só vale fora de MG.
- **Consequências / onde aparece:** `notebooks/08_sensibilidade_concentracao.ipynb` (§5 com a faixa da base), `src/analise/sensibilidade.py` (`com_faixa_da_base`), `docs/ESTADO_ATUAL.md`. Na Etapa 2, o pipeline grava `analise_tornado` e `analise_monte_carlo` e as linhas novas da `gold.sensibilidade_premissas` (receita líquida, T5, T6); nas etapas 3 e 4, o painel e o simulador seguem os itens 1 a 3.
- **Fonte:** respostas na conversa com a IA em 2026-10-23, depois da revisão dos notebooks 06 e 08; aprovação do autor pendente.

## D-043 — Tabelas `gold.analise_*` no pipeline (Etapa 2)
- **Data:** 2026-10-28
- **Contexto:** a Etapa 2 do `plano_projeto.md` leva ao pipeline o que a mineração provou, em tabelas novas ao lado das 25 atuais, sem mudar nenhuma delas nem os 10 números (Portão 2). Duas regras pendentes do autor tocam nisso: a D-038 (resultado por serventia pode ser público) ainda não chegou ao pipeline nem ao `gerar_publico.py`, e a D-042 (ainda proposta) previa linhas novas na `gold.sensibilidade_premissas`.
- **Decisão (tomada pela IA em modo autônomo; vale com a aprovação do autor):**
  1. **Seis tabelas novas**, gravadas por `pipeline.etapa_analise` depois do gold (nas etapas `all`, `gold` e `--a-partir-de silver`), com as funções de `src/analise/tabelas.py`: `analise_regras` (03), `analise_grupos` (04), `analise_clt_modelo` (06a), `analise_previsao` (07), `analise_tornado` e `analise_monte_carlo` (08). O cálculo é o dos notebooks, com a mesma semente; conferido igual em 2026-10-28. Custo: a carga leva ≈ 6 minutos a mais (a projeção do 07 é a parte longa).
  2. **A `gold.sensibilidade_premissas` não muda nesta etapa.** As linhas da D-042 (receita líquida, T5, T6) mudariam uma das 25 tabelas, contra o Portão 2 (o plano vale em conflito). Elas podem entrar depois como tabela nova (`analise_sensibilidade_passivo`, por exemplo) ou junto da aprovação da D-042.
  3. **Conjunto público:** só as 4 tabelas agregadas (`analise_regras`, `analise_previsao`, `analise_tornado`, `analise_monte_carlo`) devem entrar no `config/publico.yaml`, **na próxima carga oficial**. Elas não foram acrescentadas agora porque o `data/publico/` precisa sair do banco oficial (o manifesto carimba a carga), e a carga oficial só roda com pedido do autor. A geração foi conferida numa cópia (29 arquivos, 0,63 MB, auditor e contratos de LGPD sem problema). As 2 tabelas por serventia (`analise_grupos`, `analise_clt_modelo`, com CNS) ficam só no gold da equipe até o autor levar a D-038 ao pipeline.
  4. **Determinismo:** a previsão da floresta do 06a passou a ser sequencial (o ajuste continua em paralelo), para a `analise_clt_modelo` ter o mesmo hash a cada carga; os valores sim/não da `analise_tornado` ficam como 1/0.
- **Efeito nos 10 números:** nenhum. Pipeline do zero (`--a-partir-de silver`) numa cópia: as 25 tabelas antigas com o mesmo hash de conteúdo da carga 2026-10-19, e as 6 novas iguais às dos notebooks.
- **Consequências / onde aparece:** `pipeline.py` (`etapa_analise`), `src/analise/tabelas.py` e `conclusoes.py` (novos), `src/analise/grupos.py` (`nomes_grupos`), `src/analise/regressao.py`, `src/analise/sensibilidade.py`, `config/analise.yaml` (`grupos.nomes`), `scripts/gerar_publico.py` (opções `--banco` e `--destino`, para conferir numa cópia), `tests/test_analise_tabelas.py`, `docs/dicionario_dados.md`, `docs/SPEC.md` §3, notebook 09.
- **Fonte:** pedido na conversa com a IA em 2026-10-28 ("execute a Etapa 2 completa").
- **Status (2026-10-28):** aprovada (D-044), com as questões dos itens 2 e 3: as linhas da D-042 vão para a tabela nova `analise_sensibilidade_metodo`, e o público leva também o perfil agregado dos grupos (`analise_grupos_perfil`). A carga oficial espera o pedido do autor.

## D-044 — Respostas às questões da Etapa 2: sensibilidades da D-042, perfil público dos grupos e reconciliação arredondada
- **Data:** 2026-10-28
- **Contexto:** a Etapa 2 (D-043) deixou quatro questões, decididas na conversa com a IA seguindo a recomendação dada: aprovar a D-043 e pedir a carga oficial; levar as linhas da D-042 para uma tabela `analise_*` nova; arredondar a `qualidade.reconciliacoes`; publicar só o perfil agregado dos grupos.
- **Decisão (a carga oficial e a regeração do público esperam o pedido do autor, regra do `CLAUDE.md`):**
  1. **D-043 aprovada.** O código está pronto e conferido numa cópia. A carga no `data/radar.duckdb` real, a regeração do `data/publico/` e a linha de base nova **não** foram rodadas pela IA: o `CLAUDE.md` exige pedido do autor (`luccaamp`) para a carga oficial. Os comandos ficam no `docs/ESTADO_ATUAL.md`, "Próximo passo".
  2. **Linhas da D-042 numa tabela nova, `gold.analise_sensibilidade_metodo`**, e não na `gold.sensibilidade_premissas` (que fica como está, uma das 25 tabelas da linha de base). Cinco linhas, nível base, regra v2, STF mantém: base; receita líquida do repasse com a faixa de déficit da base (bloco "universo: leitura do Prov. 213"; universo 1.121,3 → 893,6, −20,3%; prêmio R$ 337,4 mil, −8,5%); T5 (+0,6% no passivo de todas), T6 (−1,6%) e a reserva no estado inteiro copiada da `sensibilidade_premissas` (+5,9%) (bloco "passivo: escolhas de método"). Valores iguais aos do notebook 08. A versão da receita líquida com a faixa pela própria receita líquida continua só como nota no notebook (D-042, item 2).
  3. **`qualidade.reconciliacoes` arredondada a 10 casas** (`valor_a`, `valor_b` e `indicador`, em `src/quality/reconciliacao.py`, `_linha`). Motivo: a consulta por município não tem ordem fixa, e a soma em ponto flutuante da correlação muda no 15º ou 16º dígito conforme a ordem das linhas (até 1e-15 em 20 ordens sorteadas; 2,8e-15 entre a carga de 19/10 e o gold refeito do Parquet). O hash de conteúdo é exato, então o teste `test_a_partir_do_silver_parquet_reproduz_o_conjunto_publico` falhava. O status (ok/aviso) continua calculado com o valor sem arredondar. Muda o hash dessa tabela pública: vale a partir da próxima carga oficial (o `data/publico/` atual ainda tem o valor sem arredondar).
  4. **Grupos no público: só o perfil agregado**, na tabela nova `gold.analise_grupos_perfil` (uma linha por grupo: nome, se é o grupo-alvo, nº de serventias, medianas de receita, CLT e atribuições, % de vagas, obrigadas, passivo, déficit e a parte de MG de cada um, % de cada atribuição). Nenhum CNS. Os grupos têm de 91 a 688 serventias, acima do limiar. A `analise_grupos` e a `analise_clt_modelo` (uma linha por serventia) continuam só no gold da equipe; a D-038 não foi levada ao `gerar_publico.py`.
  5. **Conjunto público da próxima carga:** seis tabelas, listadas em `config/publico.yaml`, `tabelas_da_proxima_carga` (lista que nenhum código lê): `analise_regras`, `analise_grupos_perfil`, `analise_previsao`, `analise_tornado`, `analise_monte_carlo`, `analise_sensibilidade_metodo`. Elas não entraram em `tabelas` agora porque o teste do manifesto exige que o `data/publico/` tenha exatamente as tabelas da config, e regerar o público a partir de uma cópia carimbaria uma carga que não aconteceu.
- **Efeito nos 10 números:** nenhum. Pipeline do zero numa cópia (ver `docs/diario.md`, 2026-10-28, "Decisões da Etapa 2").
- **Consequências / onde aparece:** `src/analise/tabelas.py` (`grupos_perfil`, `sensibilidade_metodo`; `construir` passa a dar 8 tabelas), `src/quality/reconciliacao.py`, `config/publico.yaml`, `tests/test_analise_tabelas.py`, `docs/dicionario_dados.md`, `docs/SPEC.md` §3.
- **Fonte:** pedido na conversa com a IA em 2026-10-28 ("Tome todas essas decisões que você propôs").
- **Carga oficial (2026-10-28):** feita no mesmo dia, a pedido do autor. `--a-partir-de silver` no banco real: os 10 números iguais, 25 de 25 tabelas antigas iguais, 8 `analise_*` novas; `config/publico.yaml` com as 6 tabelas agregadas em `tabelas` (a lista `tabelas_da_proxima_carga` saiu); `data/publico/` regerado (só a `qualidade.reconciliacoes` mudou de conteúdo). Banco anterior em `~/radar_arquivo/antes_carga_2026-10-28/`.

## D-045 — Melhorias de confiança M1 a M10 (notebook 10) e as tabelas delas no pipeline
- **Data:** 2026-10-28
- **Contexto:** a validação de 27/10 apontou os pontos de baixa confiança e propôs as melhorias M1 a M10 (`docs/plano_mineracao.md`). O notebook 09 foi feito antes delas. Foram pedidas as dez melhorias, a correção dos pontos da validação e a atualização dos notebooks.
- **Decisão (tomada pela IA; vale com a aprovação do autor):**
  1. **Um notebook novo, `10_melhorias_confianca`**, com uma seção por melhoria e o cálculo em `src/analise/melhorias.py` (com teste). Os notebooks 04, 05c, 07 e 08 ganharam só uma nota no fim, apontando para o 10, sem mudar as saídas. O 09 foi refeito com as melhorias: os achados 4 e 5 viraram um só (concentração e cliente, agora com a M1), o achado 5 passou a ser a pergunta 9 (M1 e M2), e o achado 8 usa a projeção atualizada. Alternativa descartada: reescrever o 07 com o treino até o 2026-1. Isso exigiria trocar o snapshot oficial das arrecadações e mudaria as saídas de 01, 02, 05 e 07; fica para a próxima carga oficial.
  2. **Coleta de conferência** em 28/10/2026, gratuita, pela API pública do Justiça Aberta: cadastro e arrecadações de MG, no bronze (`cnj_justica_aberta/2026-10-28/`). **O `config/escopo.yaml` não mudou**, e o pipeline continua com os snapshots de 17 e 18/10. A coleta só entra nas análises de conferência (M3 a, M6 c, M9) e na `analise_previsao_atualizada` (`config/analise.yaml`, `melhorias.coleta_conferencia`).
  3. **Seis tabelas novas** em `pipeline.etapa_analise` (`tabelas.melhorias` e `tabelas.previsao_atualizada`): `analise_capacidade_faixas` e `analise_capacidade_calibracao` (M1), `analise_sinistro` (M2), `analise_premio_cenarios` (M7), `analise_premio_grade` (M8) e `analise_previsao_atualizada` (M3 a, M3 c, M5). Todas agregadas. As da M1, da M2 e a projeção atualizada dependem de arquivos opcionais do bronze (o CSV do BI e a coleta de conferência): sem eles, ficam de fora, com aviso.
  4. **M4 rejeitada:** o desvio condicionado não melhora o teste no passado. O método do 07 continua.
  5. **Premissas novas** em `config/analise.yaml`, seção `melhorias`: horizonte de 12 meses de saldo (`fonte: suposição`; sensibilidade 6 e 24), P(fim) de 2% / 4% / 7,5% (fonte: notebook 05c), origens do teste longo e cobertura-alvo de 80% (fonte: plano M3), tercis da M4 (`fonte: suposição`), data da coleta de conferência e as 4 serventias a conferir.
- **Efeito nos 10 números:** nenhum. Pipeline do zero numa cópia: os 10 números iguais, as 33 tabelas anteriores com o mesmo hash, mais as 6 novas.
- **Propostas para o autor (não aplicadas):**
  - recalibrar a chance e a parte descoberta do déficit pela M1 (D-016), depois de conferir as 50 obrigadas com saldo ≤ 0;
  - fazer uma carga oficial com a coleta de 28/10 e refazer o 07 com o treino até o 2026-1;
  - repetir a coleta do cadastro a cada carga, com meses de distância (M9);
  - decidir a regra do salto (M6 b), que ficou mais urgente;
  - no painel: o prêmio condicionado ao cenário do STF (M7), a grade taxa × adesão (M8), a projeção com o passivo do ano (M5) e a pergunta 9 com as duas leituras (M2).
- **Consequências / onde aparece:** `notebooks/10_melhorias_confianca.ipynb` (novo), `notebooks/09_conclusoes_lacunas.ipynb`, notas no fim de 04, 05c, 07 e 08, `src/analise/melhorias.py` (novo), `src/analise/dados.py` (`saldo_bi`; `cadastro_cnj` com `snapshot`), `src/analise/tabelas.py`, `src/analise/conclusoes.py` (`NOMES_09`), `config/analise.yaml`, `config/publico.yaml` (`tabelas_da_proxima_carga`), `tests/test_analise_melhorias.py`, `docs/dicionario_dados.md`, `docs/plano_mineracao.md`.
- **Fonte:** pedido na conversa com a IA em 2026-10-28 ("Faça então as melhorias de confiança [...] corrija todos também").
- **Status (2026-10-28, tarde):** aprovada pelo autor, com as mudanças da D-046: sem a coleta de 28/10, a `analise_previsao_atualizada` saiu (ficam 5 tabelas novas) e as partes M3 a, M6 c e M9 saíram do notebook 10.

## D-046 — Recalibração do déficit pela capacidade de pagar (premissas v3), regra do salto e dados só até 18/10
- **Data:** 2026-10-28
- **Contexto:** três decisões que a D-045 deixou com o autor: recalibrar a chance e a parte descoberta do déficit pela M1, a regra do semestre com salto grosseiro e usar ou não a coleta de 28/10 na carga oficial. O autor decidiu "seguir o que a IA recomenda", com uma mudança pedida em seguida: nada da coleta de 28/10, só os dados que já estavam no projeto.
- **Decisão (do autor):**
  1. **Dados até 18/10.** O `config/escopo.yaml` continua com o cadastro e os colaboradores de 17/10 e as arrecadações de 18/10. A coleta de 28/10 (cadastro e arrecadações de MG, mais uma coleta de colaboradores interrompida no meio) saiu do bronze e foi movida para `~/radar_arquivo/`; depois, **apagada** a pedido. Também a pedido, não há Release `carga-2026-10-28`: o projeto trabalha com os dados de 17 e 18/10, os mesmos da Release `carga-2026-10-19`. Saem junto a `analise_previsao_atualizada`, a `melhorias.coleta_conferencia` e as `serventias_conferir` do `config/analise.yaml`, e as partes M3 a, M6 c e M9 do notebook 10. O que ficou com data de 28/10 são só consultas de leitura (andamento da ADI no portal do STF e índice da SES da SUSEP), sem dado gravado.
  2. **Regra do salto: o valor declarado fica na classe.** É dado oficial, declarado pelo cartório ao CNJ, e trocá-lo seria inventar um número. Duas coisas novas:
     - checagem de **aviso** no pipeline (`contratos.saltos_arrecadacao`, em `qualidade.checagens`): semestres do ano de enquadramento 10 vezes acima ou abaixo da mediana dos 4 semestres anteriores com valor > 0 da mesma serventia (a regra do notebook 01, parâmetros em `config/analise.yaml`, `saltos`). Em 2025: 45 semestres em 43 serventias, R$ 168,9 mi;
     - linha **"sem os saltos"** na `gold.analise_sensibilidade_metodo`: a receita de quem tem salto vira a média dos semestres sem salto (notebook 01, §7b), com a faixa de déficit da base. Efeito: universo −1,0% (≈ −11 obrigadas), prêmio −0,6%.
  3. **Premissas v3** (`config/premissas/premissas_v003.yaml`; a v1 e a v2 ficam no lugar), só com `prob_deficit` e `pct_descoberto` novos, pela M1 (saldo do titular = arrecadação − repasse − custeio de 2025 no BI do CNJ):
     - **antes, a conferência das 50 obrigadas com saldo ≤ 0** (64% do déficit da M1): a arrecadação do BI bate com a da API em todas (diferença máxima de 12%); o saldo ≤ 0 vem de repasse e custeio altos (medianas de 55% e 56% da arrecadação, contra 37% e 24% nas demais obrigadas); a mediana do saldo é −8% da arrecadação, perto de zero. Dado declarado plausível, não erro de leitura: a M1 vale;
     - **chance de déficit ponderada pelo passivo**, e não pela contagem. A conta do motor é déficit = Σ prob × pct × passivo da faixa. Com a chance pela contagem (6,9% e 9,6%), a parte descoberta teria de passar de 100% para dar o déficit da M1, porque quem não paga são justamente os de passivo grande. Ponderada pelo passivo, o déficit em reais é o da M1. Custo: a contagem "com déficit" (número 6) fica acima da contada pela M1;
     - valores: chance **10,8% (Classe 2) e 18,6% (Classe 3)** na base (12 meses de saldo), com mínimo e máximo de 24 e 6 meses (6,9% a 21,3%; 18,5% a 34,9%); parte descoberta **68,3% e 90,7%** na base, com mínimo e máximo do menor e do maior valor entre 6, 12 e 24 meses (56,5% a 89,1%; 62,4% a 90,7%). O horizonte de saldo continua `fonte: suposição`. A classe indeterminada segue com os valores da Classe 2 (D-011).
- **Alternativas descartadas:** trocar o valor do semestre com salto pela mediana na base (mexe em dado oficial sem prova de erro); a chance pela contagem (não reproduz o déficit em reais); um déficit por serventia pela M1 dentro do motor (o CSV do BI é opcional e não vai no pacote público, então o pipeline a partir do silver deixaria de reproduzir o resultado, D-029).
- **Efeito nos 10 números** (carga oficial de 2026-10-28, tarde, a partir do silver, a pedido do autor): os números 1 a 5 e o 10 não mudam. **6. com déficit: ≈ 486 → ≈ 148; 7. déficit: R$ 36,9 mi → R$ 34,1 mi; 8. IS: R$ 18,4 mi → R$ 17,1 mi; 9. prêmio: R$ 368,7 mil → R$ 341,1 mil** (−7,5%). O déficit fica perto dos R$ 34,5 mi da M1 (a diferença vem das 21 obrigadas, em peso, sem dado do BI). Faixa P5–P95 do prêmio: R$ 215 a 687 mil (era R$ 206 a 736 mil); cantos: R$ 51,7 mil a R$ 1,93 mi. A linha "sem os saltos" dá −11,3 obrigadas (−1,0%) e prêmio −0,8%. 38 tabelas no gold (as 33 anteriores, 16 delas com conteúdo novo, mais 5 da D-045); conjunto público com 36 arquivos e auditor sem vazamento. O simulador do painel passou a mostrar a chance e a parte descoberta com uma casa decimal, para o padrão repetir a base.
- **Consequências / onde aparece:** `config/premissas/premissas_v003.yaml` (novo), `src/estado.py` (`SEMENTE`), `src/quality/contratos.py` (`saltos_arrecadacao`), `src/analise/tabelas.py` (linha `sem_saltos`; sai `previsao_atualizada`), `src/analise/melhorias.py` (rótulo do modelo), `src/analise/conclusoes.py` (`NOMES_09`), `config/analise.yaml`, `config/publico.yaml`, `app/pages/2_Simulador.py` (controles com uma casa decimal), `eval/gabarito_chat.csv`, `README.md`, `tests/test_contratos.py`, `tests/test_mercado.py`, notebooks 09 e 10 (refeitos) e notas no fim de 01 a 08.
- **Fonte:** pedidos na conversa com a IA em 2026-10-28: decidir os três pontos seguindo a recomendação e, depois, não usar nada do dia 28/10.

## D-047 — Pendências antigas dos notebooks: P(fim da delegação), grupos por serventia e subidas do 05b
- **Data:** 2026-10-28
- **Contexto:** três questões dos notebooks 04, 05b e 05c, abertas desde 2026-10-23. A IA recomendou uma resposta para cada; o autor aprovou as três.
- **Decisão (do autor):**
  1. **P(fim da delegação no ano), D-025: faixa de 2% / 4% / 7,5% (mínimo / base / máximo)**, fonte notebook 05c (taxa de vacância observada no cadastro do CNJ). É a única estimativa com dado. **Limitação, sempre junto:** o cadastro só mostra a situação atual, então a taxa tem viés de sobrevivência e provavelmente está baixa; por isso a faixa vai até 7,5%. Usada na pergunta 9 (M2, `gold.analise_sinistro`); a sinistralidade do modelo continua a da SES (D-016).
  2. **`gold.analise_grupos` por serventia** no gold da equipe, e no público só o perfil agregado (`gold.analise_grupos_perfil`), como na D-044. Por serventia, o painel pode filtrar e mostrar no mapa o grupo de cada cartório (Etapa 3). Revisitar quando a D-038 for levada ao pipeline.
  3. **Subidas da Classe 1 para a 2 no 05b: as duas leituras como faixa** (sem e com a recalibração de Platt: 105 a 145 em 2026), sempre rotulada "projeção". A evidência é dividida (a recalibração acerta mais em 2024–25 e erra mais na média da origem móvel: 67,9 × 53,3). A projeção principal de 2026–27 continua a do notebook 07; o 05b entra como comparação.
- **Efeito nos 10 números:** nenhum. Nada é recalculado: os itens 1 e 2 já estavam em uso, e o 3 é a forma de mostrar no painel.
- **Consequências / onde aparece:** `config/analise.yaml` (nota de aprovação em `melhorias.sinistro.p_fim`), `docs/ESTADO_ATUAL.md`; o item 3 vale para a Etapa 3 (painel).
- **Fonte:** pedido na conversa com a IA em 2026-10-28, seguindo as recomendações dadas.

## D-048 — D-038 no pipeline, fase 1 (resultado por serventia no público) e checagem API × BI (serventia 035030)
- **Data:** 2026-10-28
- **Contexto:** a D-038 (22/10) tirou as restrições de publicação, menos nome e CPF de pessoa física, mas deixou o pipeline, o auditor e o `gerar_publico.py` como estavam até um pedido do autor. Antes da Etapa 3, o autor pediu para levar a D-038 ao pipeline. A serventia 035030 tinha R$ 360 mil em 2025-2 na API (Classe 2) e R$ 93 mil no BI do CNJ (Classe 1).
- **Decisão (do autor; plano recomendado pela IA):**
  1. **Fase 1 agora** (nenhum número muda; o painel atual continua igual):
     - tabela nova **`gold.serventia_publico`**: o resultado do modelo por serventia ativa (nível base, regra base, STF mantém): município e regiões, situação, atribuições, CLT, receita de referência, classe, se é obrigada, passivo, déficit esperado, IS e prêmio. Somada, dá o `fato_mercado_uf` (contrato novo do gold). Identifica o cartório pelo CNS e pelo município, nunca pelo nome do responsável;
     - no conjunto público entram a `serventia_publico`, a `analise_grupos` e a `analise_clt_modelo` (muda o item 2 da D-047: os grupos por serventia agora também são públicos);
     - travas do público (`config/publico.yaml`, `publico.checar`): o CNS deixa de ser proibido nas tabelas por serventia (lista `por_serventia`) e continua erro nas agregadas; nome de pessoa do cadastro, CPF, e-mail e colunas de dado pessoal continuam barrados em todas;
     - chat: ferramenta nova `consultar_serventia` (pelo CNS ou pelo município) e prompt sem a recusa de "cartório específico"; nome de pessoa continua proibido.
  2. **Fase 2 na Etapa 3**, junto com o painel novo: o limiar de 3 serventias cai (premissas v4), as áreas agregadas saem do mapa, do ranking e das visões, e o auditor de ataque por diferença deixa de ser obrigatório. Agora, isso quebraria o painel e os testes atuais.
  3. **035030:** a classe continua pela API (D-010). Aviso novo no gold (`reconciliacao.classe_api_x_bi`): serventias cuja classe mudaria se a receita de 2025 viesse do BI. Na carga: 10 de 2.442 (6 iriam para a Classe 1, entre elas a 035030; 4 trocariam entre a 2 e a 3). O CSV do BI é opcional: sem ele, o aviso sai com 0 e o motivo.
- **Também conferido:** nenhum dos 4.441 nomes de responsáveis e substitutos do cadastro aparece no silver (o zip público `dados-2026-10-19` é esse silver com menos colunas); nenhuma tabela do silver tem coluna de nome. A pendência "conferência de nome de pessoa no zip do silver público" foi fechada.
- **Efeito nos 10 números:** nenhum. Carga oficial a partir do silver (cópia conferida antes): os 10 números e as 38 tabelas anteriores com o mesmo conteúdo, mais a `serventia_publico` (39 no gold). `data/publico/` com 39 tabelas, auditor sem vazamento.
- **Consequências / onde aparece:** `src/transform/gold.py` (`serventia_publico`), `src/quality/reconciliacao.py` (contratos novos e `classe_api_x_bi`), `src/publico.py`, `config/publico.yaml`, `scripts/gerar_publico.py` (descrição do manifesto), `src/agent/ferramentas.py` e `chat.py`, `eval/gabarito_chat.csv` (perguntas 17 e 18), `README.md`, `tests/test_publico.py`, `tests/test_chat.py`, `docs/dicionario_dados.md`.
- **Fonte:** pedidos na conversa com a IA em 2026-10-28: resolver as pendências do pipeline antes da Etapa 3, com as respostas "D-038 no pipeline", "Fase 1 agora, Fase 2 na Etapa 3" e "Manter API + checagem" (035030).

## D-049 — Painel da Etapa 3: leitura do limite na projeção, extremos da D-042, artefatos dos notebooks e página Análises
- **Data:** 2026-10-28
- **Contexto:** a Etapa 3 (painel) precisava de quatro escolhas que nenhum documento fechava: (a) a leitura principal do limite da Classe 1 na projeção 2026–27 (questão (c) do notebook 07, pendente do autor desde 27/10); (b) de onde vêm os "extremos" da D-042, já que a `gold.analise_monte_carlo` traz os cantos do próprio Monte Carlo (passivo fixo na base) e a D-042 manda mostrar os cantos oficiais; (c) como ler no painel resultados que só existem na saída de um notebook (subidas do 05b, lacunas do 09, M5 do 10), inclusive no modo demonstração; (d) se "Análises" é página nova.
- **Decisão (tomada pela IA em modo autônomo; vale com a aprovação do autor):**
  1. **Projeção com o limite fixo como leitura principal** (R$ 300 mil do Prov. 243) e o limite corrigido pelo IPCA como comparação rotulada, sempre visível ao lado (cartão cinza e linha tracejada). Base: o limite fixo é a regra em vigor; a atualização anual do art. 16, § 2º, ainda não foi divulgada pela Corregedoria e a redação do Prov. 243 não nomeia índice, então corrigir exige supor o IPCA (`fonte: suposição` no `config/analise.yaml`). A escolha muda pouco: −43 obrigadas em 2027 (1.204 × 1.161) e −R$ 5,4 mil no prêmio. Parâmetro em `config/painel.yaml` (`projecao.leitura_limite_principal`); o leitor troca a leitura num controle da página Análises.
  2. **Extremos da D-042 = cantos oficiais** (nível mínimo e máximo do `gold.fato_mercado_uf`), como diz a D-042, e não os cantos do Monte Carlo; estes aparecem na nota "o Monte Carlo segura o passivo no nível base, por isso os cantos dele são outros". A faixa P5–P95, a mediana e a sensibilidade "patrimônio junto" vêm da `gold.analise_monte_carlo`.
  3. **Resultados só de notebook são lidos da saída gravada** (`src/painel/artefatos.py`): a tabela HTML que o notebook gravou, achada pelo trecho de código da célula (`config/painel.yaml`, `artefatos`). Alternativas: tabela nova no pipeline (exige carga oficial, só a pedido do autor) ou números em `config/` (seria copiar à mão). Se o notebook for refeito e a célula mudar, o painel avisa em vez de mostrar número velho.
  4. **Análises é página nova** (ordem: Início → Mercado → Análises → Qualidade dos dados → Simulador → Chat), pelo inventário: 11 achados, 6 de importância alta, todos de MG inteiro, sem os filtros por área do Mercado (`docs/painel/arquitetura.md`).
  5. **Situação da ADI 8015 em `config/painel.yaml`**, com a data da conferência (28/10/2026), em vez de texto no código.
- **Efeito nos 10 números:** nenhum. O painel só lê o banco e os notebooks.
- **Consequências / onde aparece:** `config/painel.yaml` (novo), `src/painel/` (novo: `analises.py`, `artefatos.py`, `graficos.py`, `ui.py`, `estilo.css`), `.streamlit/config.toml` (novo), `app/` (páginas refeitas; `2_Simulador.py` → `4_Simulador.py`, `4_Chat.py` → `5_Chat.py`, `2_Análises.py` nova), `tests/test_painel.py` (novo), `tests/test_app.py`, `scripts/qa_painel.py`, `docs/painel/` (inventário, arquitetura, padrão visual).
- **Fonte:** pedido na conversa com a IA em 2026-10-28 ("Tarefa: Etapa 3 — Painel", modo autônomo).

## D-050 — Silver sem dado pessoal e gold completo no git (`data/completo/`)
- **Data:** 2026-10-28
- **Contexto:** o painel da Etapa 3 já rodava de um clone em modo demonstração (`data/publico/`, 39 tabelas), mas o modo completo (Simulador sem grade, "Salvar cenário") pedia o banco, que só vinha das Releases. O `CLAUDE.md` proibia versionar o silver, o gold completo e o banco.
- **Decisão:** versionar em `data/completo/` (≈ 13 MB) o silver da carga oficial, sem dado pessoal, e o gold completo (39 tabelas, inclusive `interno_*`), com um manifesto de SHA-256. O banco (22 MB) continua fora: quem clona roda `uv run python scripts/exportar_completo.py --instalar` e `uv run pipeline.py --a-partir-de silver` (README, seção 1b). **Dependência achada no teste do clone:** sem o CSV do BI do CNJ (`data/bronze/cnj_bi_painel/2026-10-18/`, exportação manual, público, sem dado pessoal), o pipeline não grava `analise_capacidade_calibracao`, `analise_capacidade_faixas` e `analise_sinistro`, e tira a linha da receita líquida da `analise_sensibilidade_metodo` (os 10 números não mudam). Por isso o CSV também entra, em gzip (33,7 MB → 9,1 MB), com o `.meta.json` dele. O silver sai como no pacote público: sem as 6 colunas da RAIS da D-031 e só se o contrato de "sem dado pessoal" passar. Exceção registrada na seção Git do `CLAUDE.md`.
- **Efeito nos 10 números:** nenhum (só cópia de dados).
- **Consequências / onde aparece:** `scripts/exportar_completo.py` (novo; regrava a pasta depois de cada carga oficial), `data/completo/`, `tests/test_completo.py` (novo: hashes, colunas da D-031, nomes do cadastro e CPF, coerência com o gold local), `README.md`, `CLAUDE.md`.
- **Fonte:** pedido na conversa com a IA em 2026-10-28: levar ao git os dados usados no painel da Etapa 3 e as dependências, com a resposta "Gold completo + silver limpo".

## D-051 — Painel em torno de uma pergunta só: "o painel é a história; o chat é o detalhe"
- **Data:** 2026-10-29
- **Contexto:** a segunda rodada da Etapa 3 (D-049) pôs no painel todos os achados do projeto: 10 cartões e mais 3 cartões D-042 no Início (repetidos na Análises), ADI 8015, glossário, 4 abas, 11 suposições no tornado, 4 gráficos de projeção, a Qualidade com 6 tabelas. O painel tinha informação demais e, por isso, não informava nada; o visual era pesado (faixa azul-escura no topo, etiquetas técnicas em todas as páginas) e o mapa se perdia.
- **Decisão (tomada pela IA em modo autônomo, a pedido do autor, na conversa de 2026-10-29; vale com a aprovação dele):**
  1. **O painel responde a uma pergunta:** quanto dinheiro o seguro obrigatório dos cartórios (Prov. CNJ 227/2026) pode movimentar em MG, e quão certo é esse número. Regra de corte: o que não ajuda a responder "quanto" ou "quão certo" sai do painel e fica no chat. Corte elemento a elemento, com o motivo, em `docs/painel/corte.md` (71 elementos: 17 ficam, 8 vão para "Sobre os dados", 31 para o chat, 15 saem).
  2. **Cinco páginas e o chat:** A resposta (Início) → Quão certo é → Onde está o mercado → Para onde vai → Sobre os dados → Chat. "Para onde vai" não foi juntada com "Quão certo é" porque a página ficaria com 3 gráficos (o limite é 2). Sem abas.
  3. **Limites por página:** uma manchete, até 3 números em destaque, até 2 gráficos, até 2 frases por bloco; nenhum número em destaque em duas páginas (a tabela dos 10 números em "Sobre os dados" é a exceção); 2 a 3 perguntas sugeridas para o chat em cada página, como link `Chat?pergunta=`. Testados em `tests/test_app_demo.py`.
  4. **STF e ADI 8015 fora do painel inteiro** (etiquetas, cenários, cartões, textos); o chat continua com `situacao_adi` e `premio_por_cenario_stf`. Os números continuam no cenário "regra mantida", agora dito como "supõe a regra do Provimento como publicada".
  5. **Etiquetas técnicas e IDs fora da tela principal:** carga, versão das premissas, nível, classe, UF, nomes de tabela, de notebook e IDs de decisão só em "Sobre os dados" (ou no chat). A fonte de cada gráfico fica numa linha discreta, só com a fonte e a data (`comum.fonte_linha`).
  6. **Simulador fora da navegação:** ele não responde "quão certo" melhor que o gráfico das 5 suposições que mais pesam (com 15 controles, o leitor teria de descobrir sozinho o que o gráfico mostra de uma vez) e trazia o STF e a rentabilidade da seguradora. O arquivo foi para `app/simulador.py` (roda com `uv run streamlit run app/simulador.py`) e continua testado; a Etapa 4 decide o destino.
  7. **Rentabilidade da seguradora (pergunta 9) no chat:** o prêmio que o mercado movimenta é o mesmo com lucro ou com prejuízo, então ela não muda a resposta.
  8. **Projeção:** um gráfico do prêmio com a faixa P10–P90, só na leitura principal do limite (fixo, D-049 item 1). A leitura corrigida pelo IPCA (−R$ 5,4 mil no prêmio de 2027) deixa de aparecer "sempre ao lado" e fica no chat (`previsao_mercado`, `leitura_limite`): muda o item 1 da D-049 na parte da exibição.
  9. **Glossário vira dica do mouse** nos rótulos dos cartões e nas barras do funil; o resto, no chat. Os downloads de CSV saem do painel (o chat devolve as tabelas).
  10. **Visual claro** (terceira rodada do `docs/painel/padrao_visual.md`): sem a faixa azul-escura; fundo `#f7f8fa`, cartões brancos com borda fina, uma cor de destaque (`#3366e6`) e uma de comparação só nos gráficos (`#e08a1e`), grade de 12 colunas e espaçamento em múltiplos de 8 px.
- **Efeito nos 10 números:** nenhum. Pipeline, premissas, gold, `data/publico/` e `data/completo/` não mudaram; o painel só exibe outra seleção do que `src/painel/analises.py` devolve.
- **Consequências / onde aparece:** `app/` (páginas novas: `1_Quão_certo_é.py`, `2_Onde_está_o_mercado.py`, `3_Para_onde_vai.py`, `4_Sobre_os_dados.py`; o Simulador em `app/simulador.py`), `app/comum.py` (`pagina`, `fonte_linha`), `src/painel/ui.py`, `graficos.py`, `estilo.css`, `.streamlit/config.toml`, `scripts/qa_painel.py` (estados novos e a largura de celular), testes de exibição (`tests/test_app*.py`, `test_auditoria_painel.py`, partes de `test_painel.py` que abrem páginas, `apoio_painel.py`; piso do `test_chat_cobertura.py`), `docs/painel/corte.md`, `docs/plano_projeto.md` (Etapa 3).
- **Fonte:** pedido do autor na conversa com a IA em 2026-10-29 ("Tarefa: Etapa 3 — refazer o painel em torno de uma única pergunta", modo autônomo).

> Numeração: D-051 a D-059 ficam com o painel (branch `etapa-3-painel`); D-060 a D-069 com o chat (branch `etapa-5-chat`), para não colidirem.

## D-060 — Chat com o Gemini (nível gratuito) no lugar do Ollama; substitui a D-036
- **Data:** 2026-10-28
- **Contexto:** o chat da D-036 rodava no Ollama local (`qwen3:8b`), que não funciona no link público (Streamlit Community Cloud, sem GPU nem servidor do Ollama) e exigia instalar o Ollama e o modelo em cada PC. A Etapa 5 pede o chat no link público e na demo dos dois PCs (Windows, com `uv`).
- **Decisão:**
  1. **O modelo é só o Gemini**, no nível gratuito do Google AI Studio (exceção ao "100% gratuito" na D-061). Principal `gemini-3.8-flash` e reserva `gemini-3.5-flash-lite`, usada quando o principal devolve cota esgotada ou erro. Fonte: documentação do Google conferida em 2026-10-28 (`ai.google.dev/gemini-api/docs/models` e `/pricing`): os dois são estáveis, têm nível gratuito e o principal chama ferramentas. Os nomes ficam em `config/llm.yaml`, nunca no código.
  2. **O Ollama sai do projeto. Removido, não aposentado:** o código de `src/llm.py` foi reescrito para o Gemini, e saem a variável `RADAR_OLLAMA_URL`, o teste "painel abre sem Ollama" e o `OLLAMA_HOST` do `.env.example`. O código antigo fica no histórico do git (até o commit `4ab4500`). Motivo: manter dois modelos dobraria os testes e a avaliação sem uso real, e um código aposentado pode ser chamado por engano.
  3. **Cliente:** chamada REST `models/{modelo}:generateContent` com o `httpx`, que o projeto já usa (sem SDK novo); a chave vai só no cabeçalho `x-goog-api-key`. Os testes trocam a rede por um servidor simulado (`httpx.MockTransport`). A única dependência nova é o `python-dotenv` (leitura do `.env`), adicionada com `uv add` e com o `uv.lock` versionado.
  4. A avaliação antiga (Ollama, 2026-10-21) foi para `eval/historico/` (`git mv`).
- **Efeito nos 10 números:** nenhum. O chat só lê.
- **Consequências / onde aparece:** `src/llm.py`, `config/llm.yaml`, `src/agent/chat.py`, `app/pages/5_Chat.py`, `tests/apoio_painel.py`, `tests/conftest.py`, `pyproject.toml`, `uv.lock`, `.env.example`, `README.md`, `CONTRIBUTING.md`, `docs/plano_projeto.md` (Etapa 5), `docs/SPEC.md` (nota no §5).
- **Fonte:** pedido na conversa com a IA em 2026-10-28 ("Tarefa: Etapa 5 — Chat com Gemini (nível gratuito), para o link público").

## D-061 — Exceção ao "100% gratuito": nível gratuito do Gemini, com o faturamento desligado
- **Data:** 2026-10-28
- **Decisão:** a única exceção à regra "100% gratuito" do `CLAUDE.md` é o nível gratuito do Gemini (Google AI Studio), **com o faturamento desligado** no projeto da chave. Nada de faturamento, cartão, Google Cloud pago nem outro serviço pago. Cada pessoa pode usar a própria chave, sempre com o mesmo nome de variável.
- **A chave:** variável `GEMINI_API_KEY`, lida nesta ordem: ambiente, arquivo `.env` (fora do git; nome documentado no `.env.example`) e, no Cloud, `st.secrets`. Uma variável definida vazia vale como "sem chave" (é assim que a suíte de testes garante que nunca chama a API). A chave nunca vai para o git, para um log, para um print, para uma mensagem de erro nem para a resposta do chat (`tests/test_chat.py` procura chaves do Google nos arquivos versionáveis e confere que os erros não a repetem).
- **Dados pessoais:** no nível gratuito, o Google pode usar as conversas para melhorar os produtos (página de preços, conferida em 2026-10-28). A página do chat avisa: "não digite dados pessoais".
- **Consequências / onde aparece:** `CLAUDE.md` (seção "100% gratuito"), `src/llm.py`, `.env.example`, `.gitignore` (já tinha `.env` e `.streamlit/secrets.toml`), `README.md`.
- **Fonte:** pedido em 2026-10-28 (item 5 da base combinada).

## D-062 — Cinco ferramentas do chat sobre as funções do painel, com teste de cobertura
- **Data:** 2026-10-28
- **Decisão (detalhes da IA):**
  1. O chat tem **5 ferramentas**, com os nomes do prompt do agente: `consultar_numeros`, `consultar_mercado`, `consultar_analises`, `consultar_qualidade` e `consultar_decisoes`. Cada uma recebe o campo `analise`, que escolhe a consulta numa lista fechada (30 ao todo, `src/agent/ferramentas.py`, `CONSULTAS`).
  2. **O chat vê o que o painel vê:** as consultas das páginas chamam as mesmas funções de `src/painel/analises.py` (`PARA_O_CHAT`, `SEM_CONEXAO` e `passivo_m5`) que as páginas usam via `comum.analise`, sem refazer contas. As 6 consultas próprias do chat (D-036, D-048) continuam e entram nas ferramentas do tema (contagens, passivo, déficit, simular → números; cartório por CNS ou município → mercado; normas → decisões). Os nomes antigos continuam aceitos por `executar`.
  3. **O modelo recebe só valores formatados:** sem os números crus (`valores`, colunas `*_cru`), sem a `tabela` quando ela repete outro campo e com as listas cortadas em 25 linhas (a curva de Lorenz tinha 44 mil caracteres).
  4. **Teste de cobertura** (`tests/test_chat_cobertura.py`): falha quando uma página chama `analise("x")`, ou quando surge uma função em `PARA_O_CHAT`/`SEM_CONEXAO`, que o chat não alcança e não está em `EXCECOES` com o motivo (hoje vazia: as 21 análises das páginas estão no chat). As 30 consultas rodam sem erro no modo demonstração e, com `-m dados_reais`, numa cópia do banco.
- **`analises.py` não mudou** (nenhuma função nova nem alterada); os 10 números continuam iguais.
- **Fonte:** pedido em 2026-10-28 (itens 2 e 3 da base combinada e o prompt do agente).

## D-063 — Saída sem o modelo e limite de 20 perguntas por sessão
- **Data:** 2026-10-28
- **Decisão:**
  1. **Sem Gemini, o chat não quebra:** quando falta a chave ou a internet, a cota acaba ou a API falha, a página diz o motivo e oferece **10 perguntas prontas** (`config/llm.yaml`, `perguntas_prontas`), respondidas direto pelas ferramentas, sem modelo, com os mesmos números e fontes do painel (`chat.responder_sem_modelo`). As perguntas prontas também ficam à vista quando o modelo está disponível (não gastam cota).
  2. **Limite de 20 perguntas ao modelo por sessão** (`limite_perguntas_sessao`). Motivo: a cota gratuita é por projeto da chave, não por pessoa; no link público, todos os visitantes dividem a mesma chave, e o limite impede que uma pessoa gaste a cota do dia de todos. Com a cota esgotada (HTTP 429, mesmo na reserva), a sessão para de chamar o modelo.
- **Fonte:** pedido em 2026-10-28 (item 7 da base combinada), com a resposta "Se sim, deixa 20".

## D-064 — Texto das normas versionado em `data/normas/`, sem a assinatura
- **Data:** 2026-10-28
- **Contexto:** a busca de normas lia o texto dos Provimentos 227, 213 e 243 do bronze, que fica fora do git. No Cloud e num clone, a busca não funcionaria.
- **Decisão (da IA; vale com a aprovação do autor):** `scripts/exportar_normas.py` copia o texto oficial (atos.cnj.jus.br, coletado em 2026-10-17) para `data/normas/2026-10-17/` (≈ 145 KB, versionado), sem nenhuma mudança além de tirar a linha de assinatura ("Ministro ..."), que traz nome de pessoa física (D-038). `tests/test_chat.py` confere que não há assinatura e que, onde houver o bronze, o texto é o oficial menos essa linha. O bronze não muda.
- **Consequências / onde aparece:** `src/agent/ferramentas.py` (`NORMAS_DIR`), `data/normas/`, `scripts/exportar_normas.py`; a versão (b) da avaliação também lê daqui.

## D-065 — Gabarito de 52 perguntas congelado, meta de 85% e avaliação (a) × (b) × (c)
- **Data:** 2026-10-28
- **Decisão (gabarito redigido pela IA):**
  1. **Meta, fixada antes de qualquer rodada com o Gemini:** a versão (c) acerta **pelo menos 85%** do gabarito e **não inventa número em nenhuma armadilha** (critério do `plano_projeto.md`). Em `config/llm.yaml`, `avaliacao.meta_acerto`.
  2. **Gabarito** `eval/gabarito_chat.csv` (substitui o rascunho de 20 perguntas da D-036): 52 perguntas em 11 tipos, escritas como as pessoas escrevem (informais, com erro de digitação, vagas), mais as de fora do escopo, armadilhas para inventar número, normas, explicação de gráfico do painel, qualidade dos dados e dados pessoais (sem nenhum nome nem CPF no arquivo). **Congelado com SHA-256** em `config/llm.yaml` (`gabarito_sha256`); o teste e o script de avaliação recusam um gabarito diferente. `tests/test_chat.py` confere que todo número esperado sai de uma ferramenta.
  3. **Avaliação com a API real** (`scripts/avaliar_chat.py`, fora da suíte de testes): versões (a) sem ferramentas, (b) com as normas no prompt e (c) com ferramentas; mede acertos, alucinações, respostas sem fonte, "não sei" corretos e latência. Cuida da cota: pausa de 15 s entre perguntas, uma nova tentativa depois de um 429 e as respostas guardadas em `eval/respostas/` (rodar de novo não repete chamadas).
  4. Critério novo de correção, `recusa_com_dados`: recusa a parte pedida (o nome de uma pessoa), mas pode trazer o resultado do cartório pelo CNS.
- **Fonte:** pedido em 2026-10-28, com a resposta "Meta de acerto é 85%".

## D-066 — Prompt do agente, versão 1
- **Data:** 2026-10-28
- **Decisão:** o prompt do sistema é `config/prompts/agente_sistema.md` (versão 1, `config/llm.yaml`, `versao_prompt`): o texto original do prompt, com os nomes entre colchetes trocados pelos nomes reais das ferramentas, e um bloco final "Regras do projeto" com as regras da tarefa (só MG, cartório só por CNS ou município, normas por `buscar_norma`, "erro" vira "o painel não tem essa informação", qual consulta corresponde a cada gráfico). Qualquer outra mudança no texto gera uma versão nova, registrada na avaliação (as respostas guardadas valem só para a mesma versão). As versões (a) e (b) usam `config/prompts/sem_ferramentas.md`.
- **Fonte:** pedido em 2026-10-28 ("Prompt do agente").

## D-067 — Prompt do agente, versão 2: "Não possuo esse dado no momento"
- **Data:** 2026-10-28
- **Decisão:** quando nenhuma ferramenta tem o dado, quando a ferramenta devolve erro ou quando a pergunta é de um tema fora do painel, a resposta começa com **"Não possuo esse dado no momento."**, seguida, se ajudar, do que o painel tem de mais próximo. A resposta sem modelo (perguntas prontas) usa a mesma frase. Junto, a pedido da IA: sem ferramenta usada, a resposta não traz linha de fonte (no teste real, o modelo inventou "Fonte: Painel ... referência: dados atuais").
- **Versão:** `config/llm.yaml`, `versao_prompt: 2`. As respostas guardadas da versão 1 (1 pergunta) não valem para a v2. A correção da avaliação aceita "não possuo" como recusa (`src/agent/avaliacao.py`); o gabarito e o hash não mudaram.
- **Fonte:** pedido em 2026-10-28: "se ele não tiver a informação, responda que não possui esse dado no momento".

## D-068 — Demora do modelo principal: reserva depois de 30 s, e só a reserva por 10 minutos
- **Data:** 2026-10-28
- **Contexto:** no teste real, o `gemini-3.8-flash` respondeu em 7 s às 22h44 e, mais tarde, não respondeu nem a um "oi" em 150 s; a reserva `gemini-3.5-flash-lite` respondeu em 1 a 4 s. O código só ia para a reserva em cota esgotada ou erro HTTP, então a página mostrava "sem internet (ReadTimeout)". Depois que uma resposta vinha da reserva, o principal recusava o histórico (HTTP 400).
- **Decisão (da IA, a partir do problema relatado no uso real):** demora vira motivo próprio (`lento`, com a mensagem "serviço sobrecarregado"), o tempo-limite por chamada cai de 60 para 30 s, e a demora também passa para a reserva. Depois de qualquer falha do principal, as chamadas vão direto para a reserva por 10 minutos (`reserva_por_s: 600`), sem perder 30 s a cada rodada de ferramenta. Valores com `fonte: suposição` no `config/llm.yaml`.
- **Resultado no teste real:** perguntas respondidas em 4 a 24 s, todas pela reserva (o principal estava com a cota gratuita esgotada ou travado).
- **Consequências / onde aparece:** `src/llm.py`, `config/llm.yaml`, `tests/test_chat.py` (`test_llm_principal_lento_vai_para_a_reserva`).

## D-069 — Chat: aba de perguntas prontas, frase sem dado (prompt v3), interface e velocidade
- **Data:** 2026-10-28
- **Contexto:** pedido "Etapa 5 — ajustes no chat", em modo autônomo, para a IA decidir e registrar. É o último número da faixa do chat (D-060 a D-069): a próxima decisão do chat precisa de uma faixa nova.
- **Decisões:**
  1. **Perguntas prontas numa aba própria.** A página tem duas abas, Chat e Perguntas prontas. As prontas foram de 10 para 16, em cinco temas (números gerais, mercado, previsão, qualidade dos dados, decisões e normas), cada uma num expansor com a resposta das ferramentas, a conta, os selos e a fonte numa linha pequena. Saíram da tela os termos "sem o modelo", "respondidas direto pelo painel" e parecidos. Sem o Gemini (sem chave, sem internet, cota, erro), a aba Chat mostra só "O chat está indisponível no momento. Veja as respostas na aba Perguntas prontas."; o motivo vai para o log (`logging`, `radar.chat`).
  2. **Sem dado ou fora do escopo:** "Não foi possível encontrar essa resposta nos dados do painel." Entra no prompt **v3** (regra 3, "fora do painel" e "erro") e nas perguntas prontas, e o detector de "não sei" da avaliação passou a aceitar a frase e variações. No mesmo v3: o P10–P90 da projeção não se chama "faixa provável" (no teste real, o modelo usou o nome da D-042 para ele). O gabarito, o hash e a meta não mudaram. **A avaliação precisa ser refeita com o v3.**
  3. **Interface** (CSS só da página, em `src/agent/chat.css`):
     - cabeçalho compacto, com as etiquetas de dados e premissas;
     - campo de digitação em destaque (fundo branco, borda de 2 px na cor de marca, anel de foco, botão de enviar na cor de marca);
     - aviso de dados pessoais numa linha acima do campo;
     - contador "x de 20 perguntas nesta sessão" só no modo demonstração (é o modo do link público, sem banco);
     - 4 sugestões clicáveis na conversa vazia;
     - fonte numa linha pequena abaixo de cada resposta e selos do painel (projeção, faixa provável, sensibilidade);
     - "Fontes e datas" num expansor no fim, com o modelo, a versão do prompt e a explicação completa sobre dados pessoais;
     - nada técnico na tela (nomes de ferramentas, JSON, erros);
     - contraste: nenhum texto abaixo de 4,5:1 nos 8 estados medidos com o axe.
  4. **Velocidade** (medido antes e depois com 5 perguntas de fumaça fora do gabarito, `scripts/medir_latencia_chat.py`):
     - **primeira chamada sem streaming e as seguintes em streaming:** a chamada que só pede a ferramenta levou 0,8 s sem streaming e 3,4 s com ele (medianas de 4 repetições); a que escreve a resposta, 1,0 s até o primeiro texto em streaming;
     - cliente HTTP único por processo (a conexão com o Google fica aberta);
     - cache das ferramentas por argumentos e várias ferramentas da mesma rodada em paralelo, cada uma num cursor do DuckDB;
     - tempo-limite de leitura de 10 s no principal (`timeout_principal_s`): travado, ele custava 30 s antes da reserva;
     - raciocínio `low` nos dois modelos: `minimal` na reserva deu mediana de 7,4 s, contra 2,3 s com `low`;
     - saídas das ferramentas sem números crus: as tabelas vão ao modelo já formatadas pelo código (ele tinha convertido 0,2815 em "28,15%" sozinho);
     - nenhum `st.rerun` no caminho da pergunta (só em "Limpar conversa").
     
     Metas em `config/llm.yaml`, `latencia` (suposição): primeiro texto em até 3 s e resposta em até 10 s, na mediana.
  5. **Extremos com o nome certo:** as consultas antigas do chat (passivo, déficit, mercado) devolviam os extremos teóricos como "faixa: x a y", e o modelo os chamou de "faixa provável (P5–P95)" na captura do modo completo. O texto agora diz "extremos teóricos: x a y; não é a faixa provável". Os números não mudaram.
  6. **Resposta interrompida:** a pergunta entra no histórico logo no início e a resposta no `finally`. Uma pergunta nova no meio do streaming interrompe a execução, e antes a pergunta anterior sumia da conversa.
- **Efeito nos 10 números:** nenhum (o chat só lê; `analises.py`, o pipeline, as premissas, o gold, `data/publico/` e `data/completo/` sem mudança).
- **Consequências / onde aparece:** `app/pages/5_Chat.py`, `src/agent/chat.py`, `src/agent/chat.css` (novo), `src/agent/ferramentas.py`, `src/agent/avaliacao.py`, `src/llm.py`, `config/llm.yaml`, `config/prompts/agente_sistema.md` (v3), `scripts/medir_latencia_chat.py` e `scripts/prints_chat.py` (novos), `docs/qa/chat/`, `tests/test_chat.py`.
- **Fonte:** pedido na conversa com a IA em 2026-10-28; medições em `docs/qa/chat/latencia_antes.md`, `latencia_depois.md` e `interface_*/`.

## D-052 — Visual do painel no padrão do "Raio-X do Cartório" (quarta rodada do padrão visual)
- **Data:** 2026-10-29
- **Contexto:** o autor comparou o painel com o artefato "Raio-X do Cartório" (ficha financeira de cada serventia do Brasil, feita à parte) e pediu o painel "esteticamente igual" a ele. A D-051 (item 10) tinha tirado a faixa azul-escura do topo por achar o visual pesado.
- **Decisão (pedido do autor na conversa de 2026-10-29):** adotar a estética do artefato: IBM Plex Sans e Newsreader, faixa azul-marinho no topo com traço dourado, cartões brancos com sombra que sobem sobre a faixa, número principal num quadro azul-claro, conclusão num quadro dourado-claro, selos por significado e a paleta de gráficos do artefato. Detalhe em `docs/painel/padrao_visual.md`, seção 9. **Muda o item 10 da D-051** (visual claro sem faixa); os itens 1 a 9 continuam (estrutura, limites por página, corte).
- **Efeito nos 10 números:** nenhum (só CSS, tema e cores dos gráficos).
- **Segunda passada (mesmo dia, pedido do autor):** tokens, medidas e componentes **idênticos** aos do Raio-X (fundo, texto, linhas, faixa em degradê, cartões, agregado, veredito, badges, botões, tabela, séries s1/s2/s3/ref nos gráficos, mapa de `#e8eef8` a `#183564`), para uma página do Raio-X caber no painel sem emenda; inclui as cores da página do Chat. **Terceira passada:** os dois temas do Raio-X (claro e escuro), escolhidos pelo tema do Streamlit ou do sistema, como no artefato; gráficos e mapa trocam de cor no escuro.
- **Consequências / onde aparece:** `.streamlit/config.toml`, `src/painel/estilo.css`, `src/painel/ui.py` (`cabecalho` com o traço dourado), `src/painel/graficos.py` (paleta, fontes, subtítulo, `SEQUENCIAL` do mapa), `app/pages/2_Onde_está_o_mercado.py` (escala do mapa), `app/comum.py` (paleta antiga alinhada), `src/agent/chat.css` (só cores e fonte do título), `tests/test_auditoria_painel.py` (cores do mapa), `tests/test_painel.py` (título da projeção sem `<b>`), `docs/painel/padrao_visual.md`.
- **Fonte:** pedido do autor (`luccaamp`) na conversa com a IA em 2026-10-29; artefato de referência: claude.ai/artifact/QGughrBBriyQjiw5Pywy4Y (privado).
