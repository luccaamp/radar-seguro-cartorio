# Diário do projeto

Registro cronológico de decisões, suposições, limitações e descobertas. Entrada mais recente no topo.

Formato de cada entrada:

```
## AAAA-MM-DD — título curto
- **O que foi feito:**
- **Decisões:** (o que foi escolhido e por quê)
- **Suposições:** (o que foi assumido sem fonte)
- **Limitações encontradas:**
- **Próximo passo:**
```

---

## Linha de base

Medida do "antes", usada na comparação final dos slides. O autor já fez a medição e vai preencher aqui.

- **Tarefa medida:**
- **Data:**
- **Tempo gasto:**
- **Fontes consultadas:**
- **O que foi difícil:**

---

## 2026-10-18 — Fase 1, etapa (c): gold, qualidade e painel
- **O que foi feito:**
  - `src/motor.py`: encadeia o modelo, e o pipeline e o Simulador usam o mesmo código (o Simulador reproduz o cenário base do gold com diferença zero);
  - `src/transform/gold.py`: 3 níveis × 2 regras de classe × 3 cenários do STF, sensibilidade do rateio, diferença v1 × v2, agregação LGPD;
  - `src/estado.py`: `premissas_versoes` (semente = versão 1), `cenarios_salvos` e `log_decisoes` (espelho de `docs/decisoes.md`, para o chat);
  - `src/quality/reconciliacao.py` e `config/qualidade.yaml`: 6 reconciliações e 28 contratos do gold;
  - função pura `src/model/lgpd.py` com teste;
  - painel em `app/`: Início, Mercado (filtros, mapa, ranking, faixas), Simulador (controles, cenário do STF, mercado × seguradora, salvar) e Qualidade dos dados. Todo número tem rodapé com fonte, data de referência e versão das premissas;
  - testes do painel com o executor de testes do Streamlit;
  - conferência visual por captura de tela.
- **Aceite da Fase 1 (SPEC §8):**
  - `uv run pipeline.py` reconstruiu banco, silver e gold do zero, a partir dos snapshots do bronze, em 6 s e sem internet;
  - 75 testes passando;
  - rodapé de fonte, data e versão conferido em todas as páginas (teste automático).
- **Resultados (MG, regra v2, regra mantida; min / base / max):**
  - passivo de todas as ativas: R$ 302,7 / 343,4 / 390,5 mi;
  - universo do Prov. 227: 1.103 / 1.121 / 1.159 serventias;
  - déficit: R$ 10,5 / 40,4 / 124,2 mi;
  - IS: R$ 2,6 / 20,2 / 86,9 mi;
  - prêmio do mercado: R$ 26 mil / 404 mil / 3,0 mi por ano; seguradora hipotética: R$ 1,0 mil / 21,0 mil / 499 mil;
  - **resultado técnico negativo no máximo** (−R$ 237 mil): sinistralidade de 73,9% + comissão de 21,9% + despesa de 12% passam de 100%.
- **Descobertas:**
  - as reconciliações reproduziram de forma independente os números da Fase 0 (CNPJ +15,8%; RAIS × CNJ +1,8%; correlação 0,996);
  - **v1 dá déficit menor que v2**, mesmo com um universo maior (1.545 contra 1.121 no base; prêmio de R$ 383 mil contra R$ 404 mil). Na v1, o teto da Classe 2 cai para R$ 500 mil, e as serventias entre R$ 500 mil e R$ 1,5 mi viram Classe 3, com `prob_deficit` e `pct_descoberto` menores (D-011 usa a classe da mesma regra). Pergunta para o autor;
  - **método de rateio:** por empregados R$ 40,4 mi; por arrecadação 40,3; uniforme 36,4; por atribuição 37,0. O número de serventias com déficit não muda, porque depende só do universo;
  - **LGPD:** 532 dos 851 municípios com serventia têm menos de 3 e entram agregados; o mapa mostra estimativa para 319;
  - metadados de coleta da Fase 0 em dois padrões de nome (`<stem>.meta.json` e `_metadados.json`): o silver passou a ler os dois, e os arquivos filtrados herdam os metadados do pacote de origem.
- **Erros da IA:** 2 novos (`docs/erros_ia.md`): ponto flutuante no salvar e "R$"/mapa no painel.
- **Próximo passo:** revisão do autor (ponto c); depois a Fase 2 (Brasil inteiro e qualidade).

## 2026-10-18 — Fase 1, revisão do ponto (b) pelo autor
- **O que foi feito:**
  - D-017 aprovada com ajustes;
  - D-018 nova (terceiros);
  - páginas oficiais do STJ (Temas 478 e 1228) salvas no bronze por `src/ingest/legislacao.py`.
- **Descobertas:**
  - **Tema 478 do STJ confirmado no site oficial:** não incide INSS sobre o aviso prévio indenizado. A tese foi mantida na retratação de 13/05/2026; o que mudou foi só o terço de férias gozadas, que passou a ter INSS patronal (Tema 985/STF). Isso não afeta a rescisão, porque nela as férias são indenizadas;
  - **Tema 1228 do STJ** (julgado em 20/08/2026, sem trânsito): o titular pessoa física não paga salário-educação. Para o Sistema S não foi encontrada fonte oficial;
  - **erro da IA no 13º**, achado pelo autor: a contagem é pelo calendário, então 45 dias a partir de 31/12 dão 1/12, e não 2/12. Exemplo corrigido: **R$ 16.161,17**.
- **Próximo passo:** ponto (c).

## 2026-10-18 — Fase 1, etapa (b): modelo e testes
- **O que foi feito:**
  - respostas do autor ao ponto (a) registradas: D-013 (zero), D-014 (conflito), D-015 (vínculos sem salário de dezembro) e D-016 (premissas, com sinistralidade base no 0775 e máximo do market share = líder atual). "Responda sempre em português" no CLAUDE.md;
  - **textos legais baixados do Planalto** (`src/ingest/legislacao.py`): Lei 12.506/2011, Lei 4.090/1962, Lei 8.036/1990, Lei 8.212/1991, Decreto 3.048/1999 com o Anexo V e a CLT. Cada parâmetro do passivo foi conferido no texto (D-017);
  - `config/premissas/premissas_v001.yaml` (semente) e `config/cenarios_stf.yaml`;
  - modelo em `src/model/`: `premissas`, `passivo`, `distribuicao`, `rateio`, `universo`, `mercado`, `cenario`;
  - 56 testes passando, inclusive os 10 mínimos do SPEC e o **exemplo feito à mão** (`tests/test_passivo.py::test_exemplo_feito_a_mao`).
- **Descobertas:**
  - **o RAT de cartórios é 1%** (Anexo V do Decreto 3.048, CNAE 6912-5/00);
  - o art. 16, § 4º, do próprio Prov. 227 cita "a medida cautelar de suspensão prevista no art. 36 da Lei nº 8.935/1994, com a consequente designação de interventor". Isso confirma, no texto oficial, a explicação sobre intervenção que a IA deu de memória no início da Fase 1;
  - a Lei 8.212 não exclui expressamente o aviso prévio indenizado do salário de contribuição; a não incidência do INSS vem da jurisprudência (a confirmar);
  - **prévia do modelo nos dados reais de MG** (não é o gold; v2, rateio por empregados do CNJ, cenário "mantém"):
    - INPC dez/2025 → set/2026: fator 1,0401;
    - 10.978 vínculos na distribuição; 135 municípios com distribuição própria (a contagem do limiar já sem os vínculos de D-009 e D-015);
    - passivo de todas as ativas: R$ 303 mi (min) / R$ 344 mi (base) / R$ 372 mi (max);
    - universo: 1.103 / 1.121 / 1.159 serventias (com peso);
    - déficit: R$ 10,5 / 40,5 / 118,4 mi;
    - IS: R$ 2,6 / 20,2 / 82,9 mi;
    - prêmio do mercado: R$ 0,03 / 0,40 / 2,90 mi por ano;
    - **o mercado de MG é pequeno.** A faixa é larga porque as suposições de déficit se multiplicam.
- **Suposições novas (aguardando o autor):** as três interpretações de D-017 e `fator_correcao_saldo_fgts` = 1,0.
- **Próximo passo:** aprovação de D-017 pelo autor; depois o ponto (c): gold, qualidade e páginas do painel.

## 2026-10-18 — Fase 1, etapa (a): coletas e silver
- **O que foi feito:**
  - decisões D-007 a D-012 registradas (D-007 e D-008 aprovadas; D-009 a D-012 novas);
  - **código do tipo de vínculo conferido no layout da RAIS** (`RAIS_vinculos_layout2020.xls`, aba "RAISD - layout"): prazo indeterminado = 10, 15, 20, 25. Os códigos citados pela IA na sessão anterior estavam certos;
  - dependências adicionadas com `uv add`: duckdb, pandas, pyyaml, pydantic, streamlit, plotly, py7zr (todas gratuitas e abertas);
  - coletores em `src/ingest/` (idempotentes): `cnj_serventias`, `cnj_complementares`, `cnj_arrecadacoes` (novo), `ibge` (novo), `rais`, `cnpj`, `susep`. Os de RAIS, CNPJ e SUSEP reaproveitam os scripts da Fase 0 e só pulam o que já existe no bronze;
  - coleta nova: IBGE (853 municípios de MG, população 2026, malha municipal, IPCA e INPC até set/2026) e arrecadação semestral das 2.525 ativas de MG (em andamento);
  - `src/transform/silver.py`, `src/quality/contratos.py` e `pipeline.py`; `config/escopo.yaml` (UFs e snapshots) e `config/apelidos_municipios.yaml`.
- **Descobertas:**
  - **junção de municípios:** CNJ × IBGE por nome normalizado casa 100% (3.213 registros). CNPJ × IBGE casa tudo menos 9 registros de 2 grafias ("BRASOPOLIS" = Brazópolis 3108909; "AMPARO DA SERRA" = Amparo do Serra 3102506), resolvidos na tabela de apelidos. A RAIS usa o código IBGE de 6 dígitos (sem o dígito verificador);
  - **arrecadação duplicada na fonte:** a API repete períodos de algumas serventias. Cópias idênticas foram reduzidas a uma linha; períodos com **valores diferentes** ficam marcados com `conflito_fonte` (ex.: CNS 048108, 1º sem/2025: R$ 2.343.813,15 × R$ 479.828,50). O contrato de chave única pegou isso;
  - `atos_praticados` também pode vir "NÃO INFORMADO" (a primeira execução do silver quebrou por isso);
  - **SUSEP:** os valores do `Ses_seguros.csv` têm centavos e vírgula decimal (ex.: `350407,58`), o que indica **reais**, e não milhares. Isso resolve a pendência de unidade da Fase 0 (inferência; o `Ses_campos.csv` não declara a unidade);
  - tipo de cartório das ativas de MG: 1.442 privatizados, 1.074 oficializados, 9 públicos;
  - 887 vínculos ativos e por prazo indeterminado estão sem remuneração de dezembro na RAIS (de 11.865); mediana de 85 meses de casa, só 154 têm remuneração média anual. Hipótese: afastados (licença, INSS). A decidir com o autor;
  - **arrecadação coletada:** 2.525 de 2.525 ativas, integridade 100%, 0 erros de rede (~70 min). 103.602 linhas no silver (série desde 2005);
  - **2025 sem "NÃO INFORMADO":** todas as ativas têm os dois semestres de 2025. O "NÃO INFORMADO" aparece só no 1º sem/2026 (57 serventias). A classe indeterminada de D-004 quase não ocorre em 2025;
  - **mas há zeros:** 76 ativas declaram **R$ 0 nos dois semestres de 2025** (135 e 143 zeros por semestre). Zero cairia na Classe 1 e sairia do universo. 13 das 28 em diligência têm zero. Pergunta aberta para o autor;
  - conflitos de valor em 2025: só 2 serventias (CNS 048108 e 053439, 1º semestre);
  - prévia de classe (v2, média 2025, sem os conflitos): Classe 1 = 1.263, Classe 2 = 863, Classe 3 = 399. Com v1 (R$ 100 mil): Classe 1 = 647. Entre providas, intervenção e diligência, 65,6% ficam fora da Classe 1 na v2 e 90,6% na v1;
  - SUSEP (set/2020 a ago/2026, agregado): sinistro ÷ prêmio ganho = 10,9% (0775) e 73,9% (0776); despesa de comercialização ÷ prêmio emitido = 17,1% e 18,9%. 50 seguradoras emitiram nos últimos 12 meses; líder com 16,4%, 5ª com 5,2%, 10ª com 3,9%.
- **Próximo passo:** ponto de parada (a) com o autor: decisões sobre zeros, conflitos e vínculos sem remuneração; aprovação da tabela de premissas.

## 2026-10-18 — Início da Fase 1: decisões pendentes da Fase 0
- **O que foi feito:** respostas do autor às 6 pendências do `viabilidade.md` registradas em `docs/decisoes.md` (D-003 a D-008); SPEC §3.3 atualizado com o rateio `por_empregados_cnj`. Análise exploratória do bronze (CNJ e RAIS de MG) para as pendências 2 e 4.
- **Decisões (aprovadas pelo autor):**
  - D-003: só CLT no passivo; estatutários (178), estagiários (86) e terceirizados (135) de MG ficam fora, como limitação;
  - D-004: arrecadação "NÃO INFORMADO" = classe indeterminada;
  - D-005: rateio padrão `por_empregados_cnj`;
  - D-006: `fator_cobertura_rais` = 1,0 em MG, a revisar na Fase 2.
- **Propostas aguardando o autor:**
  - D-007: intervenção e diligência fora no `min`/`base` e dentro no `max` (proposta do autor, pendente de confirmação depois da explicação);
  - D-008: limiar de 20 vínculos para usar a distribuição do município (10 e 30 como sensibilidade).
- **Descobertas:**
  - situação jurídica das ativas de MG: PROVIDO 1.654 (9.745 CLT, 5,9 por serventia), VAGO 830 (2.105 CLT, 2,5), CONVERSÃO EM DILIGÊNCIA 28 (238 CLT, 8,5), SOB INTERVENÇÃO 13 (46 CLT, 3,5);
  - as intervenções são recentes (9 de 13 decididas em 2026); as diligências vêm de 2024 a 2026 e incluem 9 serventias de Registro de Imóveis/RTD/RCPJ, que costumam ser grandes;
  - RAIS 2025 MG: 12.347 vínculos ativos em 757 municípios, mediana de 4 por município; 910 sem remuneração de dezembro;
  - **tipos de vínculo na RAIS:** 11.558 CLT por prazo indeterminado com empregador pessoa física (código 15), 402 CLT por prazo determinado (65), 258 CLT PJ indeterminado (10), 68 aprendizes (55), 48 rural PF (25), 4 outros (90). Códigos lidos pela IA; os rótulos foram conferidos no layout de 2020, mas a correspondência código → rótulo precisa ser confirmada. Prazo determinado e aprendiz têm rescisão diferente: pergunta aberta para o autor;
  - **arrecadação de MG não foi coletada em massa na Fase 0** (só a amostra de 30) e o **IBGE não está no bronze**: as duas coletas entram na Fase 1.
- **Interpretação das situações (IA, a confirmar):**
  - *Sob intervenção*: o titular continua sendo o delegatário, mas foi afastado preventivamente durante um processo disciplinar, e um interventor nomeado pelo juiz responde pela serventia (Lei 8.935/1994, art. 36, citado de memória pela IA, a conferir no texto). Não é interinidade no sentido estrito, porque a delegação não está vaga.
  - *Conversão em diligência*: termo processual ("o julgamento foi suspenso para colher mais informações"). No cadastro do CNJ, a hipótese da IA é que a situação provido/vago da serventia está sob verificação. Não há documentação da API que confirme.
- **Próximo passo:** autor confirma D-007 e D-008, responde as perguntas do plano da Fase 1 e aprova o plano.

## 2026-10-17 a 2026-10-18 — Fase 0 (viabilidade) concluída
- **O que foi feito:**
  - **Ambiente:** uv 0.13.1 e Python 3.12.15 instalados pelo uv, com o sistema mantido em 3.13.3. `pyproject.toml` mínimo (httpx; pytest como dev), `.python-version` e `uv.lock`.
  - **Computador:** i5-11400, 32 GB de RAM, Radeon RX 580 com 8 GB (o Windows mostra 4 GB; o valor real veio do registro). O Ollama 0.32.6 já estava instalado e usa a GPU via Vulkan.
  - **LLM:** teste de tool calling com uma ferramenta de exemplo (resultado sintético). `qwen3:8b` acertou 4/4 e `llama3.1:8b` 3/4. Os dois rodam 100% na GPU, com 2 a 5 s por pergunta.
  - **Normas:**
    - Prov. 227, 213 (original e compilado) e 243 baixados de atos.cnj.jus.br para `data/bronze/normas/`;
    - ADI 8015 consultada no portal do STF (`data/bronze/stf/`);
    - SPEC atualizado com as diferenças encontradas (decisões D-001 e D-002 em `docs/decisoes.md`; `config/regras_classificacao.yaml` com `v1` e `v2`).
  - **Fontes:** todas as do §1.1 testadas (ver `docs/viabilidade.md`); 13,8 GB de brutos no bronze, com hash; amostras em `data/samples/`.
  - **Conferência entre fontes:** em MG e no Brasil, em total e por município.
- **Descobertas:**
  - **Prov. 227:**
    - os arts. 8º a 17 incluem a declaração de solvência, a garantia (art. 13) e as penalidades;
    - o passivo inclui a projeção do aviso prévio sobre férias e 13º, e os encargos INSS, RAT × FAP e FGTS;
    - a base é a maior remuneração fixa (art. 6º);
    - fiança só de bancos S1/S2;
    - **o segurado não é definido**.
  - **Classe 1 (Prov. 243, texto do próprio ato):**
    - receita bruta semestral de até R$ 300 mil (antes, R$ 100 mil); em vigor desde 22/08/2026;
    - limites atualizados todo ano pela Corregedoria Nacional;
    - o art. 19 do 227 escreve "Classe I" e o 213 usa "Classe 1" (D-001).
  - **ADI 8015:** rito do art. 12 da Lei 9.868/1999 (sem liminar separada); informações do CNJ e da AGU já prestadas; vista à PGR; amicus da Ad Notare indeferido em 13/10/2026. **Não há liminar.**
  - **CNJ / Justiça Aberta:**
    - a API pública do novo sistema traz cadastro, situação jurídica, arrecadação semestral (até o 1º sem/2026) e **colaboradores por serventia**, sem cadastro;
    - MG tem 2.525 ativas (1.654 providas, 830 vagas, 28 em diligência, 13 sob intervenção); o Brasil tem 12.121;
    - **a paginação é instável:** a coleta paginada perdeu 374 CNS de MG; a coleta em página única por UF tem checagem de integridade (SP: 1.680 informados, 1.679 entregues).
  - **CNPJ:** mudou de endereço para o SERPRO+ (WebDAV público). Pacote 2026-10: MG tem 2.923 ativos com CNAE 6912-5/00, todos com natureza 3034.
  - **RAIS 2025** (publicada em 13/05/2026):
    - MG tem 12.347 vínculos ativos no CNAE; **98% em CAEPF** (CPF do titular), que a RAIS **capta**;
    - remuneração de dezembro com mediana de R$ 2.600 e média de R$ 3.640;
    - tempo de emprego com mediana de 32 meses e média de 61; 2.002 vínculos com 10 anos ou mais.
  - **ANOREG (7ª ed., 2025):** 12.210 serventias e 96.740 empregados (95.099 CLT). Só Brasil; a fonte é o próprio CNJ.
  - **SUSEP SES** (até ago/2026): ramos de garantia em vigor 0775 (setor público) e 0776 (setor privado). Sinistro ÷ prêmio ganho em 12 meses: ~14% e ~59%; comissão: ~16% e ~22% (unidade a confirmar).
  - **Conferência:**
    - serventias: CNJ 2.525 × CNPJ 2.923 (+15,8%) em MG; 61% do excesso do CNPJ coincide com serventias inativas no CNJ (CNPJ não baixado);
    - Brasil: CNJ 12.121 × ANOREG 12.210 (+0,7%; mesma origem);
    - empregados em MG: RAIS 12.347 × CNJ 12.134 CLT (razão 1,018; **correlação de 0,996 por município**); no Brasil, RAIS/ANOREG = 1,12 (causa desconhecida).
- **Decisões:**
  - **Universo:** CNJ / Justiça Aberta (API pública), com o CNPJ como conferência.
  - **LLM:** `qwen3:8b`, com `llama3.1:8b` de reserva.
  - **Classe 1:** `v2` = R$ 300 mil como base e `v1` = R$ 100 mil como sensibilidade; classificação sempre aproximada (D-002).
  - **Passivo:** base do art. 6º aproximada pela remuneração de dezembro da RAIS (média anual como alternativa); saldo de salário desligado; `acrescimo_cct_pct` = 0.
  - **Radar:** prioridade para normas estaduais e para a atualização anual dos limites de classe.
- **Propostas que dependem do autor:**
  - **rateio `por_empregados_cnj`** como padrão, pesando cada serventia pelos CLT declarados no Justiça Aberta (muda o §3.3 do SPEC);
  - `fator_cobertura_rais` = 1,0 como base em MG.
- **Pendentes para a Fase 1:**
  1. usar só colaboradores CLT no passivo;
  2. tratamento das situações "sob intervenção" e "conversão em diligência";
  3. arrecadação "NÃO INFORMADO" como classe indeterminada;
  4. distribuição de salário e tempo do município só com vínculos suficientes, e a do estado nos demais (limiar como premissa).
- **Suposições:**
  - vigência do 213 original em 09/04/2026 pela LINDB (o ato não tem cláusula de vigência);
  - CNPJ novo a cada titular (hipótese para o excesso do CNPJ);
  - valores do SES em reais.
- **Limitações encontradas:**
  - API do CNJ sem documentação oficial;
  - colaboradores autodeclarados e sem data;
  - ~10% de arrecadação "NÃO INFORMADO";
  - layout da RAIS no FTP desatualizado (2018/2020);
  - ANOREG sem UF;
  - painéis do CNJ (Qlik) e de vacâncias (Power BI) sem download automático;
  - lista do TJMG não localizada;
  - RAIS +12% no Brasil sem explicação.
- **Erros da IA:** 11 nesta sessão e 3 da Sessão 0, registrados em `docs/erros_ia.md`. Os principais: paginação instável que esconderia 12% de MG, RAIS filtrando 0 vínculos e endereços do CNPJ desatualizados.
- **Próximo passo:** Fase 1 (painel de MG), começando pelo plano curto e pelas decisões pendentes acima.

## 2026-10-17 — Projeto passa a ser 100% gratuito e muda de prioridade
- **O que foi feito:** o SPEC, o CLAUDE.md e o `prompts.md` foram reescritos.
- **Decisões:**
  - **Custo zero.** Nada pago, nenhum cadastro em nuvem, nenhuma chave de API com créditos. Tudo roda no computador do autor.
  - **Nova prioridade:** (1) painel de cartórios com dados reais e (2) chat são o centro do projeto. O radar virou opcional, primeiro numa versão simples sem IA.
  - **Mínimo da demo:** painel (Mercado e Simulador) de MG e o chat respondendo com fonte.
  - **Fontes:** universo pelo Painel de Dados Estatísticos das Serventias Extrajudiciais do CNJ, conferido com os dados abertos de CNPJ da Receita, as listagens dos TJs e o painel de vacâncias. RAIS pelo download direto no PDET. "Cartório em Números" (ANOREG) como total de controle.
  - **LLM:** Ollama local, com modelo escolhido na Fase 0 conforme a RAM e a GPU. Acesso por uma interface única (`src/llm.py`).
  - **Banco:** DuckDB em arquivo local para os dados e para o estado do app.
  - **Nova página "Qualidade dos dados"** no painel, porque a confiabilidade dos dados é o ponto principal.
  - **Ordem das fases:** 0 viabilidade, 1 painel de MG, 2 Brasil e qualidade, 3 chat, 4 radar (opcional), 5 entrega.
- **Decisões que deixaram de valer:** Claude API, BigQuery/Base dos Dados, MotherDuck, GitHub Actions, deploy obrigatório no Streamlit Cloud e envio de resumo por e-mail ou Slack. As pendências sobre conta GCP, orçamento e canal do resumo foram encerradas.
- **Pendências do autor:** data da entrevista; preencher a linha de base acima.
- **Próximo passo:** Fase 0.

## 2026-10-17 — Decisões da Sessão 0 que continuam valendo
- **Fatos verificados pelo autor** (a IA vai confirmá-los no texto oficial na Fase 0): Prov. 227/2026 publicado em 11/06/2026 e em vigor desde 10/08/2026; Prov. 243/2026 alterou as classes do 213; ADI 8015 ajuizada pela ANOREG em set/2026 contra os arts. 8º a 17, relator Min. Flávio Dino; primeira declaração 30 dias após a vigência, depois ciclo anual; passivo = demissão de todos sem justa causa.
- **Modelo:** `prob_deficit` e `pct_descoberto` separados; `escolha_garantia` com três parcelas que somam 100%; receita = IS × taxa × market share, anual e recorrente; market share de seguradora hipotética; resultado técnico com comissão e despesa administrativa; rateio sobre todas as serventias e exclusões depois; classe indeterminada fora no min, dentro no max e com peso no base.
- **Dados:** dado mais recente de cada fonte, com data de referência visível; correção salarial da RAIS como premissa.
- **Premissas:** YAML como semente no git; versões salvas no banco (`premissas_versoes`); `cenarios_stf.yaml` com as definições fixas e `cenarios_salvos` com as combinações do usuário.
- **Orquestração:** `uv run pipeline.py` no lugar do `make`; "do zero" = a partir dos snapshots do bronze.
- **LGPD:** nome e CPF descartados na passagem bronze → silver; limiar de agregação de 3 serventias.
- **Radar (se for feito):** taxonomia de `tipo_evento` aprovada; dedup pela data do ato original; citação normalizada; texto coletado isolado no prompt.
- **Ambiente:** o projeto fica no OneDrive (decisão do autor). Python 3.12 instalado pelo `uv`, sem mexer no 3.13.3 do sistema. `docs/plano_radar_seguro_cartorio.html` foi removido de propósito (era duplicata do SPEC).

## 2026-10-17 — Início do projeto
- **O que foi feito:** SPEC, CLAUDE.md e estrutura de documentação criados; repositório publicado em `luccaamp/radar-seguro-cartorio`.
- **Próximo passo:** Sessão 0 (revisão do SPEC pela IA).

---

## 2026-10-18 (tarde) — Verificação final da Fase 1 (só leitura e comparação)
- **O que foi feito:**
  - leitura de `docs/revisao_fase1.md` e `docs/verificacao_final_fase1.md`;
  - CSV do BI do CNJ movido, sem alteração, para `data/bronze/cnj_bi_painel/2026-10-18/` (524.712 linhas; SHA-256 `5797a96a26d80d06…`; linhagem no `.meta.json`; hora da exportação não informada, cópia para o projeto às 13:43). Não tem dado pessoal. Só conferência: não entra no silver nem no gold;
  - scripts novos, só de leitura, em `scripts/verificacao_fase1/` (DuckDB em memória sobre o CSV, os Parquet de `data/silver` e `data/gold` e o bronze). O banco real estava travado pelo Streamlit aberto pelo autor (PID 26744, desde 13:27) e não foi aberto; o recálculo em memória reproduz o gold de 09:52 com diferença zero;
  - `data/radar.duckdb` antes e depois: 2026-10-18T09:52:40, 11.022.336 bytes (sem mudança). A suíte de testes não foi rodada porque grava no banco real (ver `erros_ia.md`).
- **Descobertas:**
  - **armadilhas do CSV confirmadas:** 2º sem/2025 com 28.308 linhas por atribuição para 11.066 CNS; custeio idêntico em todas as linhas de 8.183 CNS (1.445 em MG): soma ingênua R$ 15,86 bi, um por CNS R$ 7,30 bi; 1º sem/2026 misto e sem custeio; 952 linhas sem data (341 CNS, arrecadação 0); 4 custeios negativos; 6 CNS com 2 linhas no 1º sem/2025;
  - **F1:** cadastro igual ao BI (2.525; 1.654; 830; 28; 13). Todas as 2.525 estão no CSV; 1 CNS do CSV não existe em nenhum cadastro do Justiça Aberta;
  - **F2: o coletor não perde linhas.** A API devolve uma linha por CNS e semestre (o BI é que divide por atribuição). Silver × BI, 2.525 ativas: 1º sem/2025 R$ 2.379,6 × 2.373,9 mi (+0,24%); 2º sem/2025 R$ 3.133,9 × 3.067,7 mi (+2,16%). A diferença do 2º semestre vem de 168 CNS que a API já tem (R$ 62,7 mi) e o BI ainda não; sem eles, +0,11%. CNS a CNS: 16 divergem > 1% no 1º sem e 6 no 2º sem;
  - **F3:** o "154" do contrato são 154 **linhas** = 77 pares CNS-período com conflito no silver (a API e o BI duplicam períodos diferentes: BI 151 pares). Em 2025 há 2 conflitos nas duas fontes, os mesmos 2 CNS. Conflitos de anos antigos não entram no modelo (só 2025 é usado);
  - **F4:** no silver não falta semestre de 2025 (0 ausentes; zeros: 135 no 1º e 143 no 2º); no BI faltam 168 no 2º sem. Com o 1º sem > R$ 300 mil e o 2º ausente ou zero: BI 45 providos, silver 14 (classificados pelo 1º semestre, entram no universo);
  - **F5:** leitura atual = média dos semestres com valor > 0 (1.103 providos no silver; 1.095 aplicando a mesma regra ao BI). Literal com zero (média dos dois) = 1.087 no silver. Referências do BI conferidas: 928 / 1.065 / 1.106 / 1.161;
  - **F6:** a API do Justiça Aberta não traz repasse nem custeio (só período, atos e arrecadação), então o CSV do BI é a fonte. Custeio 2025 das ativas de MG R$ 1.406 mi × folha RAIS com encargos R$ 713 mi; 29 de 389 áreas com custeio menor que a folha. Passivo dos obrigados ÷ saldo anual 2025 (base v2): < 3 meses 708 serventias; 3 a 12 meses 260; > 12 meses 41; saldo ≤ 0 47; sem dado 74. Agregado: 1,94 mês de saldo;
  - **F7 (controle da Fase 2):** BI 2025 R$ 36,23 bi de arrecadação, R$ 12,34 bi de repasse e R$ 13,26 bi de custeio (conferem). O Justiça Aberta tem 12.121 ativas e o BI 11.866: 256 ativas do Justiça Aberta não têm linha no BI, quase todas sem situação jurídica (RJ 80, SE 35, ES 25). A diferença para a ANOREG (12.210, dez/2025, mesma base do CNJ) segue inconclusiva;
  - **F8:** o estudo externo usa o universo "dois semestres > R$ 300 mil" (928 providos; R$ 4.015 mi × 11,5% = R$ 461,7 mi). Ponte: com o nosso método por vínculos e as premissas do estudo (10 anos fixos, INSS no aviso e nas férias, RAT 2%), o passivo desse universo é R$ 281,2 mi; com as nossas premissas, R$ 234,5 mi; no nosso universo (esperado), R$ 256,5 mi. Prêmio do estudo para MG: 461,5 × 100% × 70% × 1% = R$ 3,23 mi/ano, contra R$ 0,40 mi no nosso base. Não usar o estudo como fonte;
  - **C1:** correlação bruta 0,996 (0,985 sem BH); em log 0,965; erro mediano 13,2%; 69,1% dentro de ±20% (376 municípios com ≥ 5); escondidos no log: 64 com RAIS 0 e 2 com CNJ 0;
  - **C6:** os 2 municípios sem serventia no CNJ são Campo Azul e Senador José Bento (0 registros no CNJ, 1 CNPJ ativo do CNAE em cada): inconclusivo. Dos 887 vínculos sem remuneração de dezembro, 714 têm também remuneração média zero e 12+ meses de casa (afastados o ano todo, provável) e só 4 foram admitidos em dezembro;
  - **E4 (teto):** passivo do universo × taxa = R$ 5,13 mi/ano no base (2%) e R$ 10,56 mi/ano no máximo (3,5%), conferindo as contas do autor;
  - **B3:** 245 apólices no base (seguradora 12,7), IS média R$ 82,6 mil e prêmio médio R$ 1.651.
- **Próximo passo:** aprovação do autor, item a item, do plano da verificação final. Nada foi implementado.
