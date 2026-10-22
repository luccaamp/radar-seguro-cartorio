# Roteiro do projeto (ROADMAP)

> **Histórico (D-037, 2026-10-22).** Não é mais a fonte do plano: cada etapa tem o seu documento, indicado no `docs/ESTADO_ATUAL.md`. Fica como referência das etapas, das pendências (§7) e da E2 detalhada.

> **Fonte única do plano daqui em diante.** O `docs/ESTADO_ATUAL.md` diz em que etapa estamos; este arquivo diz o que cada etapa precisa entregar e como saber que terminou.
> Em conflito, vale o `CLAUDE.md` (regras), depois este roteiro, depois o `SPEC.md` (desenho técnico).
> Criado em 2026-10-21, ao fim da Fase 1 (MG publicado, carga 2026-10-19). Harmonizado com os demais documentos em 2026-10-21 (D-035).

---

## 1. Os 10 números de referência

As etapas dizem quais números mudam por esta numeração. **Os valores atuais ficam no [`ESTADO_ATUAL.md`](../ESTADO_ATUAL.md#números-de-referência)**, a fonte dos valores; onde o projeto está também fica lá.

| # | Número |
|---|---|
| 1 | Serventias ativas |
| 2 | Empregados CLT |
| 3 | Obrigadas (Prov. 227) |
| 4 | Passivo (todas) |
| 5 | Passivo (obrigadas) |
| 6 | Com déficit (esperado) |
| 7 | Déficit |
| 8 | IS do mercado |
| 9 | Prêmio anual |
| 10 | Teto teórico |

Toda etapa que mudar um desses números registra a mudança na **cascata** (seção 6).

---

## 2. Visão geral

| Etapa | Nome | Pergunta central | Muda os números? | Depende de |
|---|---|---|---|---|
| **E1** | Qualidade dos dados | Os dados de entrada estão certos? | Sim (provável) | — |
| **E2** | Premissas do seguro e da garantia | Cada premissa do seguro tem fonte? | Pode mudar | E1 |
| **E3** | Mineração, 1ª rodada | O que os dados atuais mostram e justificam? | Pode mudar (premissas v3) | E1, E2 |
| **E3.5** | Lacunas e novas fontes | O que falta para responder, e onde buscar? | Não, por si só | E3 |
| **E3b** | Mineração, 2ª rodada | Que grupos, padrões e estimativas os dados permitem? | Pode mudar | E3.5 |
| **E4** | Redesenho do painel | Como contar a história em 5 minutos? | Não | E3b |
| **E5** | Agente de IA no painel | Que perguntas o chat responde, e com que acerto? | Não | E4 |
| **Radar** | Radar de normas (**opcional**) | Uma mudança nas regras aparece sozinha? | Não | E5 |
| **E6** | Ordem dos estados | Em que ordem expandir, e por quê? | Não | E3b (pode começar junto da E5) |
| **E7** | Expansão estado por estado | O modelo de MG vale para a UF nova? | Sim (novas UFs) | E5, E6 |

**Marcos de portfólio:**

| Marco | Quando | O que é |
|---|---|---|
| `v1.0` | Fim da E4 | MG completo, com premissas justificadas e painel redesenhado |
| `v1.1` | Fim da E5 | `v1.0` + chat de IA |
| `v2.x` | A cada UF da E7 | Uma UF nova publicada |

**Entrega por marco** (não é uma etapa só no fim; conteúdo da antiga Fase 5 do SPEC): um pacote mínimo no `v1.0`, atualizado no `v1.1` e a cada UF.
- **README final:** o problema, a arquitetura em diagrama, como rodar, os resultados da avaliação (a partir do `v1.1`), as limitações e a frase "custo zero: tudo roda localmente com dados públicos".
- **Medida de antes e depois:** tempo da tarefa manual × com o sistema, usando a seção "Linha de base" do `diario.md` (o autor ainda vai preencher).
- **5 slides:** problema, arquitetura, demo, onde a IA errou e o que mudou, resultados (com o gráfico de comparação das versões do chat, a partir do `v1.1`).
- **Demo:** o painel de MG, o simulador mudando de cenário do STF e, a partir do `v1.1`, o chat respondendo com a fonte; roda **sem internet** (dados no banco local e Ollama local).
- **Vídeo de reserva** da demo.
- **Na véspera da apresentação:** conferir o andamento da ADI 8015.

**Se o tempo apertar, cortar nesta ordem** (do SPEC §8, com os nomes das etapas):
1. o Radar inteiro;
2. o RAG do chat (E5);
3. o Monte Carlo (E2, S5);
4. a expansão (E7): fica MG e as UFs que já estiverem prontas.

**Nunca cortar:** os testes do modelo, a página Qualidade dos dados, a avaliação do chat (E5), o mínimo da demo (SPEC §0: painel com as páginas Mercado e Simulador; chat respondendo com número, conta e fonte) e o registro de erros da IA (`erros_ia.md`).

---

## 3. Como cada etapa anda

1. **Ramo próprio**, com o nome da etapa (ex.: `e1-qualidade`), **criado pelo autor**. Nunca direto na `main`.
2. **Conferência das normas no início da etapa:** a IA confere o andamento da ADI 8015 e se houve alterações nos Provimentos 213, 227 e 243 (SPEC §9), e registra o resultado no `diario.md`. Isso substitui o monitoramento que a D-001, a D-002 e o SPEC §10 atribuíam ao radar.
3. **Plano primeiro.** A IA lê este roteiro, o `ESTADO_ATUAL.md` e o que a etapa pede, e propõe o plano **sem executar**: o que faz, de onde vêm os dados, quais testes, o que pode mudar nos números e como vai provar.
4. **Aprovação do autor.** Nada é executado antes.
5. **Execução com paradas.** A IA para em cada ponto marcado como "decisão do autor" e no fim, com o relatório.
6. **Prova:** suíte padrão, `dados_reais`, `visual` quando o painel mudar, comparação com a linha de base e cascata dos números.
7. **Registro:** decisões novas no `decisoes.md` (a próxima livre é a **D-036**), o `diario.md`, o `erros_ia.md` e o `ESTADO_ATUAL.md`.
8. **Commit e merge pelo autor.** Nova linha de base em `C:\radar_arquivo\baseline_AAAA-MM-DD\` sempre que os números mudarem.

**Regras que valem em todas as etapas:** as do [`CLAUDE.md`](../../CLAUDE.md) (git, dados, gratuito, LGPD, cópia do banco), sem repetir aqui.

---

## 4. Modelo de etapa

Toda etapa abaixo segue estes campos. Ao começar uma etapa, a IA completa o que estiver em aberto.

- **Objetivo:** uma frase.
- **Perguntas a responder.**
- **Entradas:** dados e decisões de que depende.
- **Entregáveis:** arquivos, tabelas, notebooks, telas.
- **Critério de pronto:** como saber que terminou.
- **Decisões do autor:** os pontos em que a IA para e espera.
- **Riscos.**
- **Efeito nos números:** se muda os 10 números e como vai ser provado.

---

## 5. As etapas

### E1. Qualidade dos dados (Bloco 2)

- **Objetivo:** garantir que os dados de entrada estão certos antes de qualquer análise.
- **Perguntas a responder:**
  - A "receita bruta" que define a Classe 1 (art. 2º, XXIV, do Prov. 213) inclui ou exclui os repasses legais (taxas e fundos que não ficam com o cartório)? Citar o **texto literal** da cópia oficial no bronze.
  - Quanto o universo de obrigadas muda se os repasses forem excluídos? O plano estima, pelo BI, de 1.095 para 874 providos acima de R$ 300 mil (cerca de 20% a menos); recalcular com o silver.
  - Os demais itens do plano de qualidade se confirmam?
- **Itens** (o detalhe fica no [`plano_qualidade_e_correcoes.md`](plano_qualidade_e_correcoes.md), Bloco 2):
  - **Q1** classe das indeterminadas pelo ano anterior (cascata 2025 → 2024 → 2023);
  - **Q2** semestre faltante e sazonalidade;
  - **Q3** estabilidade da classe e zona de fronteira;
  - **Q4** receita bruta × arrecadação × arrecadação menos repasse;
  - **Q5** serventia registrada no município errado;
  - **Q6** RAIS × CNJ na unidade certa (região imediata);
  - **Q7** plausibilidade dos colaboradores declarados;
  - **Q8** custeio e repasse no silver (`silver.serventia_financeiro`, a partir do CSV do BI);
  - **Q9** remuneração do art. 6º e os 887 vínculos sem salário de dezembro;
  - **Q10** CNPJ × CNJ (casamento por nome);
  - **Q11** monitoramento das fontes (atualidade).
- **Fluxo (do plano de qualidade):**
  1. **diagnóstico** de Q1 a Q11, **só leitura**, com scripts em `scripts/qualidade_fase1/`;
  2. **uma parada** com a tabela "item × efeito em universo, passivo dos obrigados, déficit e prêmio", o número de referência do BI quando houver e a decisão proposta para cada item;
  3. **aprovação item a item** pelo autor;
  4. **implementação** do que for aprovado, com **Q8 e Q4 primeiro**.
- **Regras do Bloco 2:**
  - correções nunca alteram o bronze;
  - correções ficam em **tabelas de correção versionadas** (`config/*.yaml`), aplicadas no silver com uma coluna de marcação (`corrigido_por`, `imputado`);
  - os números do BI servem só como **ordem de grandeza**: recalcular com o silver; "se der diferente, explique, sem ajustar para bater".
- **Entradas:** bronze atual (BI do CNJ, Justiça Aberta, normas), linha de base de 20/10.
- **Entregáveis:** a tabela do diagnóstico; silver e gold corrigidos; testes de contrato e de reconciliação novos; o `docs/dicionario_dados.md` gerado por script a partir do banco; cascata dos números; decisões D-036 em diante.
- **Critério de pronto:** todos os itens do plano de qualidade fechados (corrigido, ou registrado como limitação); suítes passando; cascata explicada no `diario.md`.
- **Decisões do autor:** leitura principal da "receita bruta" (com ou sem repasses) ou só como sensibilidade; o que fazer com cada item do plano de qualidade.
- **Riscos:** o BI e o Justiça Aberta podem divergir; a mudança no universo de obrigadas propaga para todos os números seguintes.
- **Efeito nos números:** **provável** nos números **3 a 10**; o **4** também pode mudar (Q5 e Q9, se adotados).
- **Pendência herdada:** avaliar se o pipeline deve gravar também os Parquet numa pasta temporária e trocar só no fim, como já faz com o banco (D-034).

### E2. Premissas do seguro e da garantia (Bloco 3)

- **Objetivo:** tudo o que é premissa do lado do seguro e da garantia com fonte, ou declarado como suposição, e o modelo de seguro completo (S1 a S6).
- **Entradas:** E1 concluída (o S2 precisa do repasse e do custeio do Q8); `config/premissas/premissas_v002.yaml`; D-011, D-012, D-016, D-019 e D-025; SES (extrato no bronze e `BaseCompleta.zip` nos originais); normas no bronze (`data/bronze/normas/2026-10-17/`).

**Parte A — itens S1 a S6 do `docs/plano_qualidade_e_correcoes.md` (Bloco 3), como estão lá:**
- **S1** índice combinado honesto: sinistralidade + comercialização + administrativa + PIS/COFINS (alíquota conferida no texto legal) + custo de resseguro (suposição com faixa); resultado e margem com o rótulo completo.
- **S2** probabilidade de déficit pelo saldo (arrecadação − repasse − custeio, do Q8), em faixas de passivo ÷ saldo anual, lado a lado com o modelo por classe; deixar claro que o Prov. 227 mede bens livres de ônus e o saldo é só um indicador.
- **S3** sinistro por frequência × severidade (D-025): P(delegação termina no ano) × P(titular não paga | déficit) × parte paga − recuperação; frequência pelas listas semestrais de vagas do TJMG, se houver acesso, ou suposição com faixa (2% a 8%); a SES fica como comparação.
- **S4** escala: número de apólices, prêmio médio, prêmio mínimo por apólice e custo fixo por apólice (suposições com faixa).
- **S5** incerteza, **construída no modelo**: gráfico de tornado (uma premissa por vez, do mínimo ao máximo) e Monte Carlo com semente fixa, sorteando juntas as premissas de seguro e as escolhas de dados da E1, com faixa de 90%. Substitui a leitura de "mínimo e máximo com tudo no extremo".
- **S6** concentração do risco, **construída no modelo**: curva de concentração do passivo e da IS, só em percentis (sem identificar ninguém).

**Parte B — premissas do simulador ainda sem fonte (D-012, D-016):** conferir cada uma e buscar fonte; o que não tiver fica como suposição declarada.
- `prob_deficit` e `pct_descoberto` por classe (Classes 2 e 3);
- `escolha_garantia` (bens próprios, fiança, seguro);
- `taxa_seguro_anual`;
- `sinistralidade` e `comissao` (vêm da SES, mas dependem do ramo escolhido: Parte C);
- `despesa_administrativa`;
- `market_share_hipotetico` (a posição da seguradora hipotética é suposição);
- prêmio mínimo por apólice: **não existe hoje no código**; entra com o S4.

**Premissas que existem no código e não estavam na lista acima** (incluídas na E2):
- `fracao_exigencia_garantia` (cenários do STF): 1,0 quando o cenário não diz nada (`src/model/premissas.py`); 0,0 no "suspende"; 0,5 no "parcial", suposição (`config/cenarios_stf.yaml`);
- faixa de déficit da classe indeterminada e da Classe 1 na sensibilidade v1 = valores da Classe 2 (`FAIXA_POR_CLASSE` em `src/model/mercado.py`; D-011, "proposta da IA, a confirmar"; D-019, suposição);
- a sinistralidade da SES (sinistro ÷ prêmio **ganho**) é aplicada ao prêmio **emitido** do ano (`src/model/mercado.py`; aproximação declarada no Simulador);
- `comissao` = despesa de comercialização inteira da SES (`desp_com`), não só a comissão (limitação da D-016);
- o teto teórico supõe IS igual ao passivo dos obrigados (`app/Inicio.py`, `app/pages/2_Simulador.py`);
- os limites dos controles do Simulador (por exemplo, taxa de 0,5% a 5%, market share de 1% a 30%), fixos no código em `app/pages/2_Simulador.py`: justificar ou levar para `config/`.

**Parte C — a SES:**
- ramo do produto: 0775 (setor público) × 0776 (setor privado); a base atual é o 0775 (D-016), e a escolha depende do segurado (Parte D);
- unidade dos valores, a confirmar no dicionário de campos (`Ses_campos.csv`, dentro da `BaseCompleta.zip`);
- outros ramos para comparação (taxa, sinistralidade e despesas), sem coleta nova: o extrato do bronze só tem o 0775 e o 0776, mas a `BaseCompleta.zip` (em `C:\radar_arquivo\bronze_originais\susep_ses\2026-10-17\`) tem todos (`Ses_ramos.csv`); um extrato novo segue a D-032 (regerável a partir do original);
- recorte por UF: a `BaseCompleta.zip` tem um `SES_UF2.csv` (471 MB); conferir se ele traz ramo × UF (insumo também da E6);
- LGPD: a `BaseCompleta.zip` tem também um `ses_contatos.csv`; não extrair.

**Parte D — regras do produto no Prov. 227, conferidas no texto literal** (`data/bronze/normas/2026-10-17/prov_227_2026_pagina.txt`, citando artigo e parágrafo):
- valor da garantia (100% do déficit? atualização anual?);
- prazo (mínimo de 1 ano? renovação comprovada antes do vencimento?), que sustenta a receita "anual e recorrente";
- segurado ou beneficiário (o texto define? o que isso implica para o ramo 0775 × 0776);
- o que dispara o sinistro (fim da delegação, não pagamento das verbas, outro evento?) e quando a garantia é liberada.

- **Entregável principal:** a **tabela de premissas**, uma linha por premissa (Partes A a D), com valor (mín/base/máx), fonte, data de referência, **nível de evidência** (**A:** dado oficial; **B:** mercado, comparação ou literatura; **C:** suposição) e **quais dos 10 números ela afeta** (mais o resultado técnico). Ponto de partida, conferido no código:

  | Premissa | Afeta |
  |---|---|
  | `prob_deficit` | 6, 7, 8, 9 e resultado |
  | `pct_descoberto` | 7, 8, 9 e resultado |
  | faixa da indeterminada e da Classe 1 (v1) | 6, 7, 8, 9 e resultado |
  | `escolha_garantia` | 8, 9 e resultado |
  | `fracao_exigencia_garantia` | 8 e 9 só nos cenários "suspende" e "parcial" (os 10 números são do "mantém") |
  | `taxa_seguro_anual` | 9, 10 e resultado |
  | `sinistralidade`, `comissao`, `despesa_administrativa`, S1, S3, S4 | só o resultado técnico |
  | `market_share_hipotetico` | só a visão da seguradora hipotética |
  | S2 (déficit pelo saldo) | 6, 7, 8, 9 e resultado |
  | S5, S6 | nenhum número: mostram a faixa e a concentração |

- **Outros entregáveis:** S1 a S6 no modelo (com testes) e no painel; a versão 3 das premissas, se algum valor mudar; as suposições (nível C) nas Limitações do painel.
- **Critério de pronto:** nenhuma premissa sem nível de evidência; cada regra da Parte D com o texto literal citado; S1 a S6 implementados ou registrados como limitação; suítes passando; cascata dos números explicada.
- **Decisões do autor:** aceitar ou trocar cada valor; o ramo (0775 × 0776) depois da Parte D; quais itens S entram no painel; criar a versão 3 das premissas.
- **Riscos:** o mercado do Prov. 227 é novo e não tem histórico próprio; o segurado pode não estar definido na norma; a SES é de obras e contratos, não deste produto.
- **Efeito nos números:** **6 a 10**, mais o resultado técnico.

### E3. Mineração de dados, 1ª rodada (notebooks)

- **Objetivo:** entender os dados atuais e **justificar as premissas fixas do modelo e do simulador**.
- **Perguntas a responder:**
  - **Exploração:** como se distribuem receita, empregados e passivo? Que diferenças existem por classe, atribuição, situação (provida ou vaga) e região? Há valores atípicos?
  - **Justificativa:** o que os dados dizem sobre cada premissa fixa (probabilidade de déficit, parte descoberta, escolha do seguro, taxa)?
  - **Sensibilidade, incerteza e concentração:** interpretar o gráfico de tornado, o Monte Carlo e a curva de concentração **construídos na E2** (S5, S6): quais premissas mais mexem no resultado, qual a faixa provável de cada resultado, quanto do passivo está em poucos cartórios.
  - **Validação externa:** os números batem com a ANOREG, com a reconciliação RAIS × CNJ e com o total do BI do CNJ?
- **Entradas:** E1 e E2 concluídas; tabelas do gold e do silver, só leitura, via `src/notebooks.py`.
- **Entregáveis:**
  - notebooks numerados em `notebooks/` (sem saídas no git), e os que usam `interno_*` em `notebooks/privado/`;
  - **relatório de evidências** (o que foi achado, com gráfico e fonte);
  - a **versão 3 das premissas**, se alguma mudar;
  - a **lista priorizada** de gráficos e informações para o painel (insumo da E4);
  - a **lista de lacunas** (insumo da E3.5).
- **Critério de pronto:** cada premissa fixa com uma justificativa, ou com a frase "não há dado para validar"; lista de lacunas fechada.
- **Decisões do autor:** quais premissas mudam; quais achados entram no painel.
- **Cuidado de método:** o modelo é uma **estimativa de mercado**, não uma previsão de quais cartórios terão déficit. Onde não há dado para validar, o notebook diz isso explicitamente, em vez de forçar uma estatística preditiva.
- **Efeito nos números:** pode mudar, via premissas v3.

### E3.5. Lacunas e novas fontes

- **Objetivo:** decidir se é preciso buscar mais dados, e quais.
- **Perguntas a responder:**
  - O que a E3 não conseguiu responder, por quê e com que impacto?
  - Para cada lacuna, existe uma fonte pública que ajude?
- **O que já existe no projeto** (sem coleta nova):
  - todos os ramos da SES na `BaseCompleta.zip` dos originais (o extrato do bronze só tem o 0775 e o 0776), para comparar taxa, sinistralidade e despesas com ramos como garantia judicial, garantia de obrigações e fiança locatícia (a conferir no `Ses_ramos.csv`);
  - o CSV do BI do CNJ (`data/bronze/cnj_bi_painel/2026-10-18/`), com arrecadação, repasse, custeio e atos de 11.866 CNS;
  - o extrato do CNPJ com todas as UFs;
  - o PIB municipal, com o acesso testado na Fase 0 (SIDRA, tabela 5938, PIB de 2023; [`historico/viabilidade.md`](viabilidade.md)), mas ainda não coletado.
- **Fontes candidatas a investigar:**
  - mais campos do CNJ (Justiça Aberta e BI) sobre os cartórios;
  - dados municipais do IBGE (PIB, renda, população), para explicar a receita dos cartórios pela economia local;
  - tabelas de emolumentos do tribunal de cada estado;
  - estudos e relatórios públicos sobre o mercado de seguro-garantia;
  - as citadas no SPEC §1.1: Novo CAGED (tendência recente do emprego), listas dos TJs (vacâncias e editais) e o painel de vacâncias da Corregedoria Nacional.
- **Antes de escrever um coletor:** inspecionar uma amostra real da fonte e mostrar os campos encontrados ao autor (`CLAUDE.md`).
- **Critérios para aceitar uma fonte:**
  - pública e gratuita;
  - sem dado pessoal, ou com como retirá-lo;
  - disponível para todos os estados (pensando na E7);
  - atualizada com regularidade;
  - custo de coleta razoável.
- **Entregáveis:** **tabela de lacunas**, cada uma marcada como:
  - **resolvida com fonte nova** (com a decisão registrada);
  - **resolvida com suposição declarada;**
  - **fica como limitação** (um resultado válido: mostra onde o modelo é fraco).
- **Critério de pronto:** tabela de lacunas fechada; cada fonte aceita **coletada e conferida como na E1** (coletor, contratos, reconciliação, LGPD) antes de entrar em qualquer análise.
- **Decisões do autor:** quais fontes entram.
- **Riscos:** fontes que existem para MG mas não para os outros estados.
- **Efeito nos números:** não por si só; a fonte nova só muda números via E3b.

### E3b. Mineração de dados, 2ª rodada

- **Objetivo:** grupos, padrões e estimativas mais ricas, com as fontes novas.
- **Perguntas a responder:**
  - **Grupos de cartórios:** existem perfis claros (por receita, empregados, passivo, atribuição, região)? Quantos cartórios há em cada um, qual o passivo médio e a chance de déficit? Para quais perfis o seguro faz mais sentido?
  - **Prêmio:** o que a **distribuição** do prêmio do mercado, gerada pelo Monte Carlo da E2 (S5), diz quando as fontes novas entram?
  - **Modelos que têm dado para treinar:** por exemplo, explicar a receita ou o número de empregados de um cartório por fatores do município. Isso pode ser treinado e testado de verdade, e ajuda a estimar estados com dados piores.
- **Cuidado de método sobre "predição de prêmio":** o mercado do Prov. 227 ainda não existe, então **não há histórico de prêmios** para treinar um modelo clássico. O que é defensável:
  - estimar por **comparação** com ramos parecidos (fontes da E3.5);
  - usar a **incerteza simulada** na E2 (Monte Carlo) para mostrar a distribuição, em vez de um número só;
  - treinar e testar só onde há dado observado (receita, empregados).
- **LGPD:** o grupo de cada cartório e a "chance de déficit" de cada um são estimativas por serventia: **só uso interno**. No público entram só os perfis dos grupos, agregados, com 3 ou mais serventias, depois do auditor.
- **Entregáveis:** notebooks; perfis dos grupos; modelos com a métrica de teste; atualização da lista do painel; premissas v3 (ou v4), se for o caso.
- **Critério de pronto:** cada modelo com métrica em dados de teste, ou declarado como simulação; perfis públicos aprovados pelo auditor.
- **Decisões do autor:** quais grupos e estimativas entram no painel.
- **Efeito nos números:** pode mudar, via premissas.

### E4. Redesenho do painel (conteúdo e visual)

- **Objetivo:** contar a história que a E3 e a E3b encontraram, numa demonstração de 5 minutos.
- **Passos:**
  1. **Roteiro da demonstração:** o que mostrar, em que ordem, em 5 minutos.
  2. **Rascunho de cada página:** o que entra, o que sai, de onde vem cada número.
  3. **Escolha do modelo visual** pelo autor.
  4. Implementação.
  5. Conferência com a galeria de prints, as checagens de layout e a acessibilidade.
- **Pendências que entram aqui:**
  - carregar um cenário salvo nos controles do Simulador (hoje o "Salvar" só registra);
  - "Salvar cenário" no modo demonstração;
  - a contagem `premissas_alteradas`, que mostra alterações quando os controles voltam ao padrão (deveria ser 0): **confirmar primeiro; se for erro no dado salvo, avaliar antes da E4**;
  - a tabela de cenários salvos e a Tabela por UF passando da largura da tela;
  - acrescentar à galeria um estado "Simulador com cenário salvo".
- **Entregáveis:** o painel novo; a galeria nova; o roteiro da demonstração.
- **Critério de pronto:** galeria sem falhas de layout; acessibilidade sem violações graves no nosso código; números iguais aos do gold; demonstração ensaiada em 5 minutos.
- **Decisões do autor:** o roteiro, o modelo visual e a aprovação final pela galeria.
- **Efeito nos números:** nenhum.
- **Marco:** `v1.0` (com o pacote de entrega da seção 2).

### E5. Agente de IA no painel

- **Objetivo:** um chat dentro do painel que responde perguntas sobre o mercado, com fonte.
- **Situação (2026-10-21, D-036): E5 reduzida feita, antes da E1, a pedido do autor.** Feito: `src/llm.py`, `config/llm.yaml`, 5 ferramentas (SPEC §5.2), página Chat (desativada sem Ollama), gabarito-rascunho de 20 perguntas e avaliação (a) × (c) em `eval/resultado_avaliacao.md`. Falta: gabarito de 40 a 60 perguntas revisado e congelado pelo autor, versão (b) com as normas no prompt, as ferramentas de qualidade e de decisões, o acerto mínimo e o gráfico de comparação.
- **Modelo local:** Ollama, gratuito, sem nuvem. Ponto de partida: **`qwen3:8b`** (escolhido na Fase 0: 4 de 4 no teste de chamada de ferramentas, 100% na GPU), com reserva **`llama3.1:8b`** ([`historico/viabilidade.md`](viabilidade.md), §3). O LLM é acessado só por `src/llm.py`; `num_ctx` e `think` ficam em `config/llm.yaml` (a criar).
- **Saída estruturada:** o Pydantic foi removido na limpeza da Fase 1; a decisão de trazê-lo de volta fica para o plano desta etapa.
- **Ordem de trabalho:** gabarito (rotulado pelo autor) → ferramentas → integração com o Ollama → chat no painel → avaliação das versões.
- **Desenho no SPEC:** as ferramentas e as regras do chat estão no **SPEC §5.2**; o gabarito, as métricas e o gráfico de comparação das versões, no **SPEC §7** (§7.1 e §7.2).
- **O que é desta etapa:**
  - as ferramentas recebem a **UF como parâmetro** desde o início (para a E7 entrar sem mexer no agente); v1, mínimo e máximo só nos totais da UF; o código do chat entra na varredura de `tests/test_app_codigo.py` (nada de `interno_*`);
  - **sem Ollama instalado** (ex.: quem clonou o repositório público), o chat aparece desativado, com uma explicação, sem quebrar o painel;
  - **teste de extração por serventia**, somado ao gabarito do SPEC §7: tentativas de extrair dados por serventia, em que nenhuma resposta pode trazer dado proibido pela LGPD.
- **Entregáveis:** o chat; o gabarito congelado; o relatório da avaliação (SPEC §7); a documentação de instalação.
- **Critério de pronto:** o chat responde o gabarito com as métricas e o gráfico de comparação das versões do SPEC §7; acerto mínimo definido pelo autor no plano da etapa; nenhuma resposta com dado proibido no teste de extração; painel funcionando sem Ollama.
- **Decisões do autor:** confirmar ou trocar o modelo; o gabarito; o acerto mínimo; trazer ou não o Pydantic.
- **Riscos:** respostas inventadas pelo modelo; desempenho em computador comum.
- **Efeito nos números:** nenhum.
- **Marco:** `v1.1` (com o pacote de entrega da seção 2 atualizado).

### Radar de normas (opcional, depois da E5)

- **Opcional:** é a **primeira coisa a cortar** se o tempo apertar. Enquanto não existir, a conferência manual do início de cada etapa (seção 3) cobre a ADI 8015 e os provimentos.
- **Desenho no SPEC:** a lista de monitoramento, as versões simples e com IA, a taxonomia e a regra "nunca aplica nada sozinho" estão no **SPEC §5.3**; a avaliação, no **SPEC §7.3**.
- **Ordem:** primeiro a versão simples, sem IA; a versão com IA só se sobrar tempo.
- **Critério de pronto:** um evento real aparece na página Radar com link e trecho.
- **Efeito nos números:** nenhum.

### E6. Ordem dos estados (notebook)

- **Objetivo:** decidir a ordem de expansão com evidência.
- **Ponto de partida:** o bronze já tem o cadastro das 27 UFs (`serventias_XX.json`), então o estudo começa sem coleta nova.
- **Dados por UF que já existem:**
  - o cadastro das 27 UFs (`data/bronze/cnj_justica_aberta/2026-10-17/`);
  - o extrato do CNPJ com todas as UFs;
  - o CSV do BI do CNJ com 11.866 CNS (sem coluna de UF; casa com o cadastro pelo CNS);
  - os totais do Brasil da Fase 0 (CNJ, CNPJ, RAIS e ANOREG; [`historico/viabilidade.md`](viabilidade.md), §2);
  - empregados e arrecadação pela API do CNJ: **só MG** foi coletado;
  - a SES por UF: **a conferir** (`SES_UF2.csv`, na `BaseCompleta.zip`; ver a E2, Parte C).
- **Achado a levar em conta:** a RAIS do Brasil tem 12% mais vínculos que a ANOREG (106.524 × 95.099 CLT), com causa desconhecida (datas diferentes, cadastro desatualizado ou empresas que não são cartório usando o CNAE em outras UFs; `historico/viabilidade.md`, §2). Em MG, RAIS e CNJ concordam (1,8%).
- **Critérios candidatos para a nota combinada:**
  - **tamanho:** número de serventias e de empregados;
  - **mercado:** passivo estimado e déficit;
  - **viabilidade:** qualidade e disponibilidade dos dados de cada UF (CNJ, RAIS) e esforço de coleta;
  - **adoção:** presença de seguradoras e mercado de garantia na UF (SUSEP).
- **Entregáveis:** notebook com a nota, o **teste de sensibilidade** (a ordem muda quando os pesos mudam?) e a **validação com MG** (a nota acerta o tamanho do mercado de MG?); decisão registrada.
- **Critério de pronto:** ordem estável para os primeiros estados sob variação razoável de pesos, ou instabilidade explicada.
- **Decisões do autor:** os pesos e a ordem final.
- **Efeito nos números:** nenhum.
- **Observação:** pode ser feita em paralelo com a E5.

### E7. Expansão estado por estado

- **Objetivo:** levar o modelo a cada UF, na ordem da E6.
- **Roteiro por UF** (igual para todas):
  1. coleta das fontes da UF (antes de escrever ou adaptar um coletor, inspecionar uma amostra real e mostrar os campos ao autor);
  2. contratos e reconciliações (como na E1; SPEC §4);
  3. revisão das regras específicas da UF (normas da corregedoria local, se houver);
  4. auditor de LGPD;
  5. números da UF revisados e registrados;
  6. painel e chat com a UF nova (o gabarito do chat ganha perguntas da UF);
  7. pacotes e Releases.
- **Pendência herdada do SPEC:** medir o tempo do auditor com as 27 UFs.
- **Riscos das fontes** ([`historico/viabilidade.md`](viabilidade.md), §4): API do CNJ sem documentação oficial; a consulta do Brasil inteiro numa requisição dá timeout (coletar por UF); layout oficial da RAIS desatualizado; grafia de municípios diferente entre fontes.
- **Critério de pronto por UF:** suítes passando; reconciliações dentro da tolerância ou explicadas; divergências entre fontes documentadas no `diario.md` e na página Qualidade dos dados; auditor sem vazamento.
- **Marco:** `v2.x` a cada UF (com o pacote de entrega da seção 2 atualizado).

---

## 6. Cascata dos números

Toda etapa que mudar um dos 10 números acrescenta uma linha aqui (o detalhe vai no `diario.md`):

| Data | Etapa | Decisão | Número | Antes | Depois | Por quê |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

---

## 7. Pendências transversais

As pendências vivem aqui. O `ESTADO_ATUAL.md` só aponta para as que dependem do autor agora (marcadas **[autor]**).

- **[autor]** Conferência de LGPD do zip do silver público (Release `dados-2026-10-19`): nenhum nome, CPF, e-mail ou telefone de pessoa física, nenhuma estimativa do modelo por serventia (D-030, D-031).
- **[autor]** Convidar os colegas para os dois repositórios (depois de 21/10) e mandar o `CONTRIBUTING.md`.
- **[autor]** Configurar o e-mail "noreply" do GitHub nos commits.
- **[autor]** Decidir o destino de `docs/qa/depois/` (galeria de uma rodada anterior, 18 MB, fora do git, imagens diferentes das de `docs/qa/atual/`): manter ou mover para `C:\radar_arquivo`.
- **[autor]** Preencher a seção "Linha de base" do `diario.md` (medida do "antes", usada na entrega).
- **[autor]** Apagar a pasta antiga do projeto no OneDrive, depois de 1 a 2 semanas de uso da pasta nova.
- Pasta de sessões do Claude Code na pasta nova: `c--projetos-radar-seguro-cartorio` (conferida em 2026-10-21); o procedimento de salvar conversas está no `CONTRIBUTING.md`.
- Backup de `conversas/` e de novas linhas de base em `E:\radar_arquivo` a cada etapa.
- A tabela antiga `estado.cenarios_salvos` some do banco na próxima carga (D-034); conferir depois da carga.
- Regras de estilo do `ruff` (hoje só as regras `F`; as padrão acusam cerca de 100 avisos de estilo).
- Na próxima mudança do painel: o texto da página Qualidade dos dados ainda cita `docs/viabilidade.md` (`app/pages/3_Qualidade_dos_dados.py:45`); trocar por `docs/historico/viabilidade.md`. As sementes `config/premissas/premissas_v001.yaml` e `v002.yaml` ficam com o caminho antigo, porque são o registro do que foi gravado no banco.
- Para a E4: a descrição da página Mercado no SPEC §5.1 é a do plano original ("mapa e ranking por UF"); reescrever com a página real (municípios de MG, áreas agregadas, um filtro por vez, D-026).
- Para a E4: o nome `gold.fato_mercado_municipio_publico` engana, porque a tabela não está no conjunto público (`docs/dicionario_dados.md`); avaliar renomear ou retirar.
- D-025 continua como proposta (entra na E2, S3).

---

## 8. Como atualizar este roteiro

- Ao **começar** uma etapa: a IA completa os campos em aberto e o autor aprova.
- Ao **terminar** uma etapa: marcar como concluída, com a data e o commit, e mover as pendências que sobraram para a etapa certa.
- Ao **fechar** cada etapa, antes do commit: verificação de contradições entre os documentos dos níveis 1 e 2 (núcleo e referência; ver `docs/README.md`).
- Cada etapa atualiza, de forma curta, só a parte do `SPEC.md` que ela toca.
- Mudança de ordem ou de escopo: só com decisão registrada no `decisoes.md`.
