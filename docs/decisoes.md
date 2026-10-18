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
