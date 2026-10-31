# Diário do projeto

Registro cronológico de decisões, suposições, limitações e descobertas. Cada entrada nova é acrescentada **no fim** do arquivo (as primeiras entradas, de 17 e 18/10, ficaram em ordem decrescente no começo).

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
- **Fatos verificados pelo autor** (a IA vai confirmá-los no texto oficial na Fase 0): Prov. 227/2026 publicado em 11/06/2026 e em vigor desde 10/08/2026; Prov. 243/2026 alterou as classes do 213; ADI 8015 ajuizada pela ANOREG em set/2026 contra os arts. 8º a 17, com relator já designado; primeira declaração 30 dias após a vigência, depois ciclo anual; passivo = demissão de todos sem justa causa.
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

## 2026-10-18 (noite) — Etapa 1 dos ajustes finais da Fase 1 executada
- **O que foi feito:** os 11 passos de `docs/aprovacao_etapa1_fase1.md`, na ordem, com a suíte rodada ao fim de cada um.
  - **Passo 1 (item 5):** o painel lê o banco pela variável `RADAR_BANCO`; os testes usam uma cópia temporária, refazem o gold nela e conferem no fim que o banco real não mudou. Banco real antes e depois da suíte: 2026-10-18T09:52:40, 11.022.336 bytes (iguais). A "versão 2 espúria" já não existia: tinha sido apagada à mão às 09:51 e o banco foi refeito às 09:52, então nada foi removido.
  - **Passos 2 a 6:** D-021 (passivo zero), D-019 (faixas pela classe da regra base, peso por regra), D-020 (`premissas_v002.yaml`, data-base 31/12/2025), D-022 (reserva pela região imediata), D-023 (leituras alternativas só na sensibilidade, `src/model/leituras.py`) e D-024 (dois contratos de total de controle).
  - **Passo 7 (D1, D2):** `qualidade.rec_municipio` e `gold.fato_passivo_municipio` passaram a ser públicas e agregadas; as versões completas viraram `interno_*`. Teste que varre todas as colunas de texto das tabelas públicas, e as tabelas e gráficos das 4 páginas, procurando nomes dos municípios com menos de 3 serventias.
  - **Passo 8:** C1 (3 checagens novas), C5 (metadados dos colaboradores no bronze, URL e coleta da SUSEP herdadas do pacote, malha do IBGE = 2022 conferida por hash) e C6 (limitações).
  - **Passos 9 e 10:** texto da decisão parcial, rótulo da sinistralidade e painel (A5, E1 a E4).
  - **Passo 11:** pipeline a partir do bronze em 9 s, 0 erros; 99 testes; banco real antes e depois da suíte: 2026-10-18T15:18:30, 28.061.696 bytes (iguais).
- **Descobertas:**
  - a malha municipal servida sem `periodo` pela API v3 do IBGE é a de **2022** (mesmo SHA-256; 2023 a 2025 dão erro 500);
  - com o peso por regra, a sensibilidade v1 no base dá prêmio de R$ 404,7 mil contra R$ 368,7 mil da v2 (monotonicidade vale em min, base e max);
  - leituras da regra dos R$ 300 mil no silver (providos acima do limite): principal 1.103; zero conta como zero 1.087; dois semestres 967 (BI 928); algum semestre 1.170 (BI 1.161). Efeito no prêmio: −0,8%, −3,9% e +0,2%;
  - C1: correlação em log 0,965, erro mediano 13,2% e 69,1% dos municípios dentro de ±20%; esta última fica abaixo da tolerância proposta (75%) e acusa aviso;
  - cadastro do BI **não** mede vacância: as datas são de recadastramento (decisão do autor; D-025 continua proposta).
- **Totais de controle Brasil (BI do CNJ, 2025), guardados para a Fase 2:** arrecadação R$ 36,23 bi; repasse R$ 12,34 bi; custeio R$ 13,26 bi; 11.866 ativos no BI contra 12.121 no Justiça Aberta.
- **Ponte com o estudo externo (material de slide, fora do painel):** 461,7 → 281,2 (método −180,5) → 234,5 (premissas −46,7) → 256,5 (universo +22,0), em R$ mi, com os números de antes da Etapa 1.
- **Próximos passos aprovados em princípio (Etapa 2), por ordem:**
  1. B6 + F6: probabilidade de déficit por faixa de passivo ÷ saldo anual, lado a lado com a versão por classe; exige coletor do CSV e silver de custeio e repasse, com contrato para o custeio repetido por atribuição;
  2. B3: apólices, prêmio médio, prêmio mínimo e custo fixo por apólice;
  3. B2: índice combinado, resultado técnico antes de impostos e capital, PIS/COFINS com alíquota conferida na lei;
  4. B4: tornado e cenários coerentes "otimista" e "pessimista para a seguradora";
  5. opcional: B1 completo e Monte Carlo.
- **Próximo passo:** conferência do painel pelo autor.

## 2026-10-18 (noite) — Bloco 1 do plano de qualidade (tela e engenharia, sem mudar número)
- **O que foi feito:** itens 1.1 a 1.7 de `docs/plano_qualidade_e_correcoes.md`.
  - 1.1 `md_seguro` e dois testes; 1.2 mapa com geometria dissolvida no gold (`geopandas`, gratuito); 1.3 rótulo "Resultado técnico (antes de impostos, resseguro e capital)" e a linha da margem; 1.4 "≈" nos valores esperados; 1.5 rótulos curtos, espaço no Simulador e detalhe do contrato de conflitos; 1.6 fontes; 1.7 carga atômica, regra do `interno_*`, teste de reprodutibilidade.
- **Números:** nenhum número do modelo mudou (cascata "Bloco 1 final" = Etapa 1: passivo R$ 311,9 / 238,1 mi; déficit R$ 36,87 mi; prêmio R$ 368,7 mil).
- **Descobertas:**
  - **IPCA:** coletado e carregado no silver, mas não entra em nenhuma conta (só o INPC, na sensibilidade). Saiu dos rodapés; na tabela de fontes aparece "coletado, não usado";
  - **unidade da SES:** o dicionário que vem no pacote (`Ses_campos.csv`) não informa unidade e não há outro dicionário no ZIP. Continua inferida (R$). Nenhum valor absoluto da SES aparece na tela (só razões e fatias de mercado);
  - **carga atômica:** o banco caiu de 28,1 MB para 13,4 MB e não cresce mais entre cargas; as versões de premissas e os cenários salvos são copiados do banco anterior;
  - **mapa:** 4 regiões imediatas tinham municípios pequenos somando menos de 3 serventias; nesses casos o grupo foi dissolvido junto com o menor município da região que já tinha 3 ou mais;
  - **ano de enquadramento** (2025) saiu do código e foi para `config/escopo.yaml`.
- **Pendente de decisão do autor:** a página Mercado ainda lê `gold.interno_serventia` para os filtros (atribuição, situação, classe). Exceção temporária e explícita no teste `test_painel_nao_le_tabelas_internas`.
- **Próximo passo:** Parada 1 (conferência do painel e commit da Fase 1 pelo autor); depois, o diagnóstico do Bloco 2.

## 2026-10-18 (noite) — Revisão do painel com filtros (revisao_painel_filtros.md)
- **O que foi feito:**
  - D-026 aplicada (opção B e grupos pela intermediária) e D-027 proposta;
  - E1 a E10, U1 e U2;
  - auditoria própria (`tests/test_auditoria_painel.py`, 44 estados e checagens).
- **Contagem do mapa (2.3):**
  - das 70 regiões imediatas, todas têm municípios pequenos; 62 mantêm o próprio grupo (498 municípios);
  - 8 viraram 4 grupos de região intermediária (34 municípios: as 4 com menos de 3 serventias somadas ao menor grupo de outra região da mesma intermediária);
  - 319 municípios com 3+ serventias + 66 grupos = 385 áreas; 319 + 498 + 34 = 851 municípios com serventia, mais 2 sem serventia = 853.
- **Visões com filtro:** convergem em 3 iterações do auditor (973 células publicadas); a troca de filtro leva ~0,3 s no AppTest.
- **E9 (Campo Azul):** a serventia "…de Campo Azul" está cadastrada no CNJ com o município de Ubaí, provavelmente o de origem antes da emancipação. A correção do dado é o Q5 do Bloco 2.
- **E10 (Mutum):** 6 serventias indeterminadas, todas zeradas em 2025. Improvável ser acaso (declaração ou coleta). Verificar se há dado em 2024 no Q1 do Bloco 2.
- **Leituras de seguros (só registro, revisao_painel_filtros.md §6):**
  1. a Classe 2 pesa por causa da suposição: 26% do passivo dos obrigados e 42% do déficit (fator suposto 25% × 12% da Classe 3); argumento central para o B6;
  2. prêmio por apólice muito baixo: déficit médio de quem tem déficit ≈ R$ 41,5 mil (Classe 2) e ≈ R$ 197 mil (Classe 3); a 2%, ≈ R$ 830 e ≈ R$ 3,9 mil por ano. O B3 tende a mostrar que o mercado real é quase só a Classe 3 (~100 cartórios em MG);
  3. concentração: BH ≈ 17% do déficit e ≈ 22% do passivo dos obrigados; pede limite por risco e resseguro;
  4. Classe 1: 46% das serventias, 13% dos empregados e 9% do passivo; por isso v1 × v2 muda pouco;
  5. o leste escuro em "Serventias ativas" é real (muitos distritos com registro civil), não efeito da agregação.
- **Números de referência:** inalterados (2.525; 12.134; ≈ 1.121; R$ 311,9 / 238,1 mi; ≈ 486; R$ 36,9 mi; IS R$ 18,4 mi; prêmio R$ 368,7 mil; teto R$ 4,76 mi).
- **Próximo passo:** conferência do painel pelo autor; aprovação da D-027 e da captura de telas com o Playwright.

## 2026-10-18/19 — Correções C1–C4 e QA visual (correcoes_e_qa_visual.md)
- **Aprovações registradas:** D-027 aprovada e D-028 (partições internas de uma visão não são suprimidas) em `docs/decisoes.md`; frases novas em Limitações (D2 e auditoria de diferenças); SPEC Fase 2 (medir o auditor com 27 UFs) e Fase 3 (chat só devolve visões públicas auditadas). Pacotes de dev: `playwright` (só Chromium) e `axe-playwright-python`.
- **Ferramentas de QA (novas):** `scripts/qa_painel.py` (sobe o próprio Streamlit numa porta livre com cópia temporária do banco, 25 estados fixos, checagens pelo DOM), `scripts/prints_painel.py` (galeria em 1280 × 800 e 1920 × 1080), `tests/test_visual.py` (`uv run pytest -m visual`, fora da suíte padrão) e `scripts/acessibilidade.py` (axe → `docs/qa/acessibilidade.md`). `docs/qa/` fica fora do git.
- **Descobertas da galeria "antes" (182 falhas, das quais 100 eram ruído):**
  - 84 eram 404 internos do Streamlit em `/<Página>/_stcore/health` e `/host-config` (o front tenta o caminho relativo antes do da raiz ao abrir uma página por endereço profundo; não vem do nosso código). A checagem agora ignora erros de console vindos de `/_stcore/`;
  - 24 eram erro da própria checagem (contava barras em `gd.data`, que no Plotly 6 vem codificado em binário); agora usa `gd.calcdata`.
- **Defeitos reais achados além do C1–C4:** KPIs do Início cortados em 1280 (5 colunas); rótulo "Serventias com déficit (esperado)" cortado no Simulador; botão "Limpar filtros" cortado; **mapa do município sem o destaque no enquadramento** (Almenara e município pequeno: o zoom aproximava demais e não incluía a geometria do destaque). Corrigidos (ver relatório).
- **C4:** o "Juíz de Fora" vem errado da API do IBGE (só a região intermediária 3106); corrigido no silver via `config/correcoes_nomes.yaml`, com a coluna `nome_regiao_corrigido_por`. O bronze não foi tocado.
- **Pipeline rodado** para o C4: 58/58 contratos ok; foto de linhas e somas numéricas de 37 tabelas silver/gold/qualidade antes × depois: 0 diferenças.
- **Acessibilidade:** 6 regras violadas. Todo contraste vem de cores do tema padrão do Streamlit (legenda `st.caption` #83858c, widget desabilitado, cor primária no slider) e `heading-order` vem de `st.subheader` após `st.title`. Nada de contraste ou rótulo em cor ou texto nosso; ficam como sugestões.
- **Pendente de decisão do autor:** 8 tabelas largas na página Qualidade dos dados (fontes, conferência, divergências, sensibilidade, contratos) passam da largura em 1280 (e 2 delas em 1920). Fora do escopo C1–C4; `pytest -m visual` falha só nelas.
- **Próximo passo:** conferência da galeria pelo autor e decisão sobre as tabelas da Qualidade; depois, o Bloco 2.

## 2026-10-19 — Pendências do QA visual e diagnóstico do repositório reproduzível
- **Tabelas largas da Qualidade (decisão do autor):** rolagem horizontal aceita nessa página. `scripts/qa_painel.py` tira a página da checagem de "última coluna visível" (`PAGINAS_COM_ROLAGEM`, com o motivo no código: página técnica de auditoria, tabelas largas por natureza).
- **Acessibilidade (decisão do autor):** corrigidos a ordem dos títulos (`st.header` nas seções; o `####` do Simulador virou `###`) e o seletor "Valor" do Mercado (escondido quando o filtro é "Nenhum"). **Limitação conhecida:** o contraste das cores padrão do Streamlit (legenda `st.caption` e valor do slider) fica como está.
- **Resultado:** galeria e checagens com 0 falhas de layout nas duas larguras; `uv run pytest -m visual`: 2 passed; axe: só as 2 regras de contraste do tema.
- **Auditoria do histórico (8 commits, 174 blobs), antes de qualquer mudança:**
  - sem segredos (o `.env.example` só tem o endereço local do Ollama);
  - sem bronze, silver, gold, banco ou CSV do BI; maior arquivo 150 KB;
  - a amostra `data/samples/cnj_justica_aberta/lista_serventias_MG_amostra20.json` tem os campos responsável, substitutos, e-mail e telefone, mas todos com `<OCULTO>` (mascarados na Fase 0);
  - os metadados dos commits mostram o e-mail do autor;
  - `docs/prompts.md` mostra o nome do usuário do Windows num caminho.
  - Nada de gravidade (c).
- **Descoberta:** `luccaamp/radar-seguro-cartorio` **já está público** (consulta `gh repo view`, só leitura); o repositório de dados está privado.
- **Clone limpo (antes):**
  - o painel abre, mas as 4 páginas mostram "Banco não encontrado";
  - `uv run pytest`: 93 passed, 67 skipped (sem banco nem bronze);
  - `pipeline.py --help` trocava o banco por um vazio (registrado em erros_ia.md);
  - na máquina do autor, o `uv sync` num clone fora do OneDrive falha com hardlink (erro 396 do OneDrive no cache do uv); `UV_LINK_MODE=copy` resolve.
- **Descobertas para o desenho:**
  - o gold lê a malha do IBGE direto do bronze (não dá para recalcular só com o silver);
  - `gold.execucao.executado_em` muda a cada carga, então "hash idêntico" precisa de um hash de conteúdo, separado do hash do arquivo;
  - uma rodada do motor leva 0,22 s.

## 2026-10-19 — Repositório reproduzível (docs/repositorio_reproduzivel.md), seções 2.1 a 2.7
- **Feito:** D-029 e D-030 (`docs/decisoes.md`).
  - **Conjunto público:** `data/publico/`, 25 Parquet, 0,61 MB, mais o manifesto. Gerado por `scripts/gerar_publico.py`: auditor com 989 células e 0 vazamentos; LGPD com 3.213 CNS e 3.840 nomes do cadastro procurados, 0 achados.
  - **Modo demonstração** no painel.
  - **Simulador sem dados internos:** totais por faixa, mais a grade de 80 variantes do passivo.
  - **Pipeline:** `--a-partir-de bronze|silver` e malha no silver.
  - **Pacotes e instalação:** `scripts/empacotar_dados.py` e `scripts/baixar_dados.py`.
  - **Documentação:** README ("Como rodar", fontes, licença), `CONTRIBUTING.md`, `docs/publicacao.md`, LICENSE MIT.
- **Testes:**
  - a suíte padrão roda sem dados reais (painel no modo demonstração e conjunto público);
  - o que precisa do banco, do silver ou do bronze virou `dados_reais` (`uv run pytest -m dados_reais`), fora da suíte padrão.
  - Equivalência do Simulador por totais com o motor completo: dados sintéticos (padrão) e dados reais (`dados_reais`), nas premissas padrão e em 5 combinações aleatórias, tolerância relativa de 1e-9.
- **Decisões do autor nesta rodada:**
  - licença MIT;
  - silver no Release público, com a regra de LGPD corrigida (nenhuma *estimativa* do modelo por serventia; dados de origem sem dado pessoal), no documento e no CLAUDE.md;
  - exceção `gold.dim_municipio.n_serventias` aprovada.
- **Conferência pedida pelo autor:** o silver não tem campo derivado do modelo; nada foi retirado do pacote público. O empacotador retiraria automaticamente qualquer coluna que casasse com `estimativas_do_modelo`.
- **LGPD corrigida no caminho:** `qualidade.rec_municipio` (já publicada no painel) tinha 4 grupos de região imediata com 1 ou 2 serventias, que mostravam o CLT delas. Agora viram uma linha "Outras regiões". Os números de referência não mudam.
- **Achado na prova de reprodutibilidade:** o texto de um detalhe da reconciliação mudava de ordem entre cargas (`GROUP BY` sem `ORDER BY`). Corrigido; os números já eram iguais.
- **Tamanhos:**
  - gold público versionado: 0,61 MB;
  - pacote público: silver com 2,8 MB;
  - pacote da equipe: 8,4 GB em 15 arquivos. Bronze 8.435 MB (CNPJ 6,8 GB em 4 partes; RAIS 0,9 GB; SUSEP 0,58 GB; os `.COMT` extraídos, 6,2 GB, ficam fora); silver 2,8 MB; gold completo 1,2 MB; banco 17,8 MB, 2,8 MB no zip.
- **Limitação do ambiente:** o projeto está no OneDrive.
  - O pacote da equipe é gerado fora dele (`--saida`).
  - Trocar pastas exigiu substituir arquivo por arquivo.
  - Num clone fora do OneDrive, o `uv sync` desta máquina precisa de `UV_LINK_MODE=copy`. O motivo é o cache do uv, e um estranho não tem isso.
- **Próximo passo:** o autor publica (passo a passo em `docs/publicacao.md`). Depois, Bloco 2.

## 2026-10-19 — Limpeza do projeto (docs/limpeza_projeto.md): seção 2 e Etapa 1 (inventário)
- **Seção 2 feita:**
  - `CLAUDE.md` com 5 regras restauradas ou acrescentadas, mais as linhas do `ESTADO_ATUAL.md`;
  - usuário do Windows trocado por `<usuario>` em `docs/prompts.md` (único arquivo versionado com o padrão);
  - D-031: 6 colunas da RAIS fora do silver público; prova: 25/25 tabelas idênticas a partir do pacote público novo;
  - registro completo da Fase 1: 8 erros novos em `erros_ia.md`, mais a seção "Erros do revisor"; status de D-028 a D-030; seção "Fase 1" no `prompts.md`;
  - `docs/ESTADO_ATUAL.md` criado.
- **Linha de base:** em `C:\radar_arquivo\baseline\`: hash de conteúdo das 25 tabelas do gold e das 25 públicas, 10 números de referência, listas de testes (125 / 70 / 2), cópia da galeria, tamanhos.
- **Ferramentas de dev instaladas:** ruff, vulture, coverage, deptry.
- **Testes de ausência:** numa cópia completa fora do OneDrive, 12 rodadas (item retirado → pipeline a partir do bronze → suíte padrão). Todas deram gold 25/25 e números iguais. P3 (`BaseCompleta.zip` da SUSEP) e a combinação da D-032 mudam só `silver.fonte_metadados`: a URL e a hora de coleta da SUSEP vêm hoje dos metadados do zip original.
- **Teste de extração da D-032:** CNPJ e SUSEP regeneram o extrato com o mesmo SHA-256. A RAIS não: o coletor lê o original com o separador errado (registrado em `erros_ia.md`).
- **Coverage** (pipeline do bronze + 3 suítes): nenhum módulo morto. O que não roda é coleta (precisa de internet), scripts de linha de comando chamados como subprocesso e callbacks de botão. Sobras pontuais: `CINZA_AGREGADO`, `lim_v2`, `import json` no gold, dois imports em testes, `passivo.como_dict` e `Checagem.ok`.
- **deptry:** `pydantic` sem uso; `numpy` usado sem estar declarado.
- **Dados reais:** intactos (assinatura igual antes e depois).
- **Próximo passo:** aprovação do autor na Parada 1.

## 2026-10-19 (noite) — Limpeza do projeto, Etapa 2 (execução aprovada) e D-032
- **Feito, por área:**
  - **docs:** 8 documentos de rodada para `docs/historico/` (`git mv`), com `INDICE.md`; atualizados os links vivos (README, `config/simulador_demo.yaml`, docstring do teste, `ESTADO_ATUAL.md`); teste novo de links quebrados nos `.md`.
  - **scripts:** `scripts/verificacao_fase1/` para `scripts/arquivo/` (`git mv`), com README; a raiz do `comum.py` arquivado foi ajustada (`parents[3]`).
  - **código:** removidas as 5 sobras e os imports sem uso dos testes.
  - **dependências:** `pydantic` removido (o SPEC prevê para a Fase 3; volta quando o chat existir) e `numpy` declarado. Dev: + `jupyterlab`, `ipykernel`, `nbstripout`; − `vulture`, `deptry`, `coverage`; o `ruff` fica como padrão.
  - **`.gitignore`:** links do guia de Streamlit, trava do Claude Code, `notebooks/privado`, `notebooks/saidas` e `modelos`.
  - **notebooks:** `notebooks/` com README, `00_exemplo_leitura.ipynb` sem saída, `src/notebooks.py` somente leitura e `tests/test_notebooks.py`; regras no `CLAUDE.md`, no `CONTRIBUTING.md` e no SPEC; seção "Estrutura do projeto" no README.
  - **dados locais:** `pacotes/` e `docs/qa/antes/` para `C:\radar_arquivo\` (com `MANIFESTO.md`); a saída padrão do empacotador passou para `C:\radar_pacotes`.
- **D-032 (bronze enxuto):**
  - coletor da RAIS corrigido (detecta o separador);
  - coletores baixam os originais fora do OneDrive e gravam no bronze o extrato e o `original.json`; o silver lê o `original.json`;
  - 27 originais (14,76 GB) movidos para `C:\radar_arquivo\bronze_originais\`;
  - `--com-originais` no empacotador e camada `originais` no instalador;
  - bronze oficial de 14,9 GB para 144 MB.
- **Provas:**
  - pipeline do zero a partir do bronze enxuto: gold 25/25 e público 25/25 idênticos à linha de base, os 10 números iguais, `data/publico` 26/26 intacto;
  - ausência do P3 e a combinada da D-032 (na cópia): 25/25 e 25/25, suíte 133 passed;
  - regerar os extratos de RAIS, SUSEP e CNPJ dá o mesmo SHA-256;
  - auditor com 989 células e 0 vazamentos; LGPD com 0 problemas;
  - galeria: 0 falhas de layout, e a diferença de pixels é só a hora da carga no rodapé;
  - clone simulado, nos 5 caminhos: 25/25 a partir do silver público e do bronze enxuto;
  - suítes: padrão 133 (125 + 8 novos), `dados_reais` 73 (70 + 3 novos), visual 2; nenhum teste removido.
- **Pacotes em `C:\radar_pacotes`:** público 2,7 MB; equipe 84,6 MB (12 arquivos; antes 8,4 GB); equipe com originais 9,76 GB (19 arquivos).
- **Erros da IA nesta etapa** (registrados em `erros_ia.md`):
  - originais movidos para dentro de pastas com o próprio nome;
  - testes novos dependentes de repositório git;
  - remoção do `pydantic` que deixou pacotes pela metade no `.venv`;
  - script da prova que rodou comandos no projeto real, com os dados verificados intactos.
- **Conversas:** `e12eda2b` convertida para `conversas/2026-10-18-fase1-parte1.md`; esta sessão (`784e4eca`) será convertida ao fim.
- **Próximo passo:** revisão do autor na Parada 2, commit e publicação.

## 2026-10-20 — Ajustes depois da Parada 2 (pedido do autor)
- **Falha da linha de base registrada** em `erros_ia.md`: a de 2026-10-19 não listava os arquivos soltos de `data/` e não provava a ausência do `carga_atual.json`.
- **Linha de base versionada:** `scripts/linha_de_base.py` registra todos os arquivos de `data/` (caminho, tamanho, data, SHA-256), os hashes de conteúdo e os 10 números. Testado só com leitura: 191 arquivos, e o único solto na raiz é o `radar.duckdb`.
- **Proteção no `baixar_dados.py`:** recusa gravar o `data/carga_atual.json` onde já há banco ou gold, antes de baixar qualquer coisa, salvo com `--substituir`. Teste: `tests/test_pacotes.py::test_nao_grava_carga_atual_onde_ha_banco_ou_gold` (banco e gold). Suíte padrão: 135 passed.
- **Achado:** o comando de lint documentado como padrão falha com as regras padrão do ruff (103 avisos de estilo). Registrado em `erros_ia.md`, com proposta, aguardando o autor.

## 2026-10-20 — Pacote de originais separado (Release originais-<ano>)
- **Conferência pedida pelo autor ("19 arquivos, 9,76 GB × 27 originais, 14,07 GB"):** nenhum original ficava de fora. Os 27 estavam no pacote (CNPJ 22, RAIS 4, SUSEP 1). "19" contava os arquivos publicados (12 da carga mais 7 zips ou partes de originais), e a diferença de tamanho era compressão: os `.COMT` são texto e os 7,4 GB da RAIS viravam 2,3 GB.
- **Decisão do autor:**
  - excluir os `.COMT` da RAIS (`config/pacotes.yaml`, `originais_excluir`), porque saem do `.7z` e a regeneração foi provada;
  - separar os originais num Release próprio, publicado uma vez (`originais-<ano>`), e deixar o `carga-<carga>` sempre enxuto.
- **Feito:**
  - `empacotar_dados.py --nivel originais` (o `--com-originais` saiu);
  - `baixar_dados.py --nivel originais --ano AAAA`: instala na pasta de originais e não grava o `carga_atual.json` (não é uma carga) nem é bloqueado pela trava de banco ou gold;
  - testes em `tests/test_pacotes.py` (instalação dos originais e tag por ano);
  - `docs/publicacao.md` com os três Releases; `CONTRIBUTING.md` e `ESTADO_ATUAL.md` atualizados.
- **Pacotes em `C:\radar_pacotes`:**
  - público: 2,7 MB;
  - carga (equipe): 84,6 MB, 12 arquivos;
  - originais: 25 originais (8,29 GB) em 6 arquivos mais o manifesto; fora, os 2 `.COMT` (6,47 GB).
- **Nota:** a IA escreveu "≈ 3,5 GB" para o pacote de originais no `publicacao.md` antes de medir; corrigido para ≈ 8,3 GB (os zips do CNPJ já são comprimidos).

## 2026-10-20 — Fechamento da Fase 1 (antes do Bloco 2)
- **Conversa:** a sessão `784e4eca` foi convertida para `conversas/2026-10-18-fase1-parte2.md` (45 mensagens do autor, 1.350 ferramentas, 445 KB). Ela começou como continuação da `e12eda2b`, então as 9 primeiras mensagens (18/10, 00:53 a 09:50) repetem o início da parte 1. Conferência: nenhum e-mail além do `noreply@anthropic.com` da assinatura de commit, nenhum CPF, telefone ou token; "rafae" só aparece em caminhos de pasta do Windows e "luccaamp" é o usuário público do GitHub.
- **Releases conferidos (só leitura, `gh release list`):** `dados-2026-10-19` (público), `carga-2026-10-19` e `originais-2026` (privado), todos publicados.
- **`main` protegida:** ruleset `main protegida` ativa (Restrict deletions, PR com 0 aprovações, Block force pushes), com o dono do repositório na Bypass list por escolha própria. `docs/publicacao.md`, seção 4, reescrita como situação atual.
- **Mudança de pasta (D-033):** o projeto vai para `C:\projetos\radar-seguro-cartorio`, fora do OneDrive. Atualizados `CLAUDE.md` (regra "Disco e pastas"), `README.md`, `CONTRIBUTING.md`, `docs/publicacao.md`, `docs/SPEC.md` (riscos), `docs/prompts.md` (pasta de sessões do Claude Code) e o comentário de `config/pacotes.yaml`. O histórico (diário, erros, `docs/historico/`, conversas) ficou como estava.
- **Caminhos absolutos:** nenhum caminho com "OneDrive" ou "Área de Trabalho" em `src/`, `app/`, `tests/`, `scripts/`, `config/` nem no `pipeline.py`; só comentários dizendo "fora do OneDrive". O único caminho absoluto antigo está em `.claude/settings.local.json` (duas permissões de `git -C`), que não quebra nada, só deixa de valer.
- **Nova ordem das etapas** (decisão do autor) no `docs/SPEC.md` (§8) e no `docs/ESTADO_ATUAL.md`: Bloco 2 (começando pelo Q4), Bloco 3, mineração de MG em notebooks, redesenho do painel de MG, chat com a UF como parâmetro, estudo da ordem dos estados e expansão estado por estado.
- **Próximo passo:** commit do autor, mudança de pasta e Bloco 2, item Q4.

## 2026-10-20 — Verificação completa da pasta nova (C:\projetos\radar-seguro-cartorio)
- **Contexto:** primeira sessão na pasta nova (D-033). Pendências feitas pelo autor fora da sessão: backup externo de `C:\radar_arquivo` em `E:\radar_arquivo` (203 arquivos, 0 falhas) e `nbstripout --install` neste clone.
- **Ambiente:** `git status` limpo, `origin` = `luccaamp/radar-seguro-cartorio`, ramo `main`, último commit `21303e2`. Filtro do `nbstripout` configurado (`.git/config` aponta para o `.venv` da pasta nova; `.git/info/attributes` com `*.ipynb filter=nbstripout`). `UV_LINK_MODE=copy` gravada nas variáveis do usuário, mas ausente nos processos desta sessão (VS Code aberto antes); passada à mão em cada comando.
- **Dados:** 191 arquivos em `data/` (bronze 144,2 MB, silver 2,8 MB, gold 0,6 MB, público 0,6 MB, banco 17,8 MB de 19/10 23:10, amostras 0,1 MB); nenhum `carga_atual.json`. Bate com o registrado em 2026-10-20 (191 arquivos, só o banco solto na raiz).
- **Linha de base nova** (pedido do autor): `C:\radar_arquivo\baseline_2026-10-20\linha_de_base.json`, gerada com `scripts/linha_de_base.py`. Os 10 números e os hashes de conteúdo (gold 25/25, público 25/25) são iguais aos da linha de base de 19/10; o `data/publico/manifesto.json` bate em conteúdo (25/25) e em arquivo (25/25). É a referência do "antes" do Bloco 2.
- **Caminhos antigos:** nenhum caminho absoluto antigo no código, na configuração nem nos testes; só comentários "fora do OneDrive" (ainda verdadeiros) e um exemplo de plano B em `scripts/baixar_dados.py`. O que precisa mudar: a linha do `ESTADO_ATUAL.md` (corrigida) e as duas permissões de `.claude/settings.local.json` (decisão do autor). Histórico (diário, erros, decisões, `docs/historico/`, conversas) fica.
- **Testes (numa cópia completa do projeto, fora do projeto real):** padrão 137 passed; `dados_reais` 73 passed; visual 2 passed. A assinatura do projeto real (191 arquivos com SHA-256 e data) ficou igual antes e depois.
- **Reprodução (na cópia):** `pipeline.py --a-partir-de silver`: contratos do gold 62/62, gold 25/25 e público 25/25 iguais à linha de base, os 10 números iguais, `data/publico` 26/26 arquivos iguais.
- **Achado:** com a saída redirecionada (pipe), o pipeline caiu com `UnicodeEncodeError` (cp1252 não tem "≥"). Com `PYTHONIOENCODING=utf-8`, rodou sem erro. Registrado em `erros_ia.md`.
- **Galeria (na cópia, `--checar`):** 52 prints, 0 falhas de layout e 0 erros de console. Contra `docs/qa/atual`: 4 prints idênticos; nos outros 48, a diferença é só o carimbo "carga de 20/10/2026 12:33" (o pipeline da cópia regravou o banco) e um ponto de 3 × 4 px na borda do mapa do Mercado.
- **Modo demonstração (cópia sem banco, bronze, silver nem gold):** as 4 páginas abrem sem exceção, com a faixa "Modo demonstração" e "Carga 2026-10-19", e mostram os números de referência. Os únicos 404 são os `/_stcore/health` e `/_stcore/host-config` do próprio Streamlit ao abrir a página pelo endereço direto (os mesmos que o `qa_painel.py` ignora).
- **Observação:** o painel abre o banco para gravação (cria as tabelas de estado; "Salvar cenário" grava). Para conferir sem mexer no banco real, abrir com `RADAR_BANCO` apontando para uma cópia.
- **Docs:** `ESTADO_ATUAL.md` (pasta nova, commit `21303e2`, pendências), data de revisão do `SPEC.md` e cabeçalho do diário (entradas novas no fim).
- **Depois da verificação (aprovado pelo autor):**
  - saída em UTF-8 no `pipeline.py` e nos 7 scripts que imprimem, com `tests/test_saida_utf8.py`: 9 testes de varredura na suíte padrão e 1 `dados_reais`, que roda o pipeline numa cópia com `PYTHONIOENCODING=cp1252`. Ele falha com o código antigo e passa com o novo;
  - suíte padrão 146 passed (137 + 9); lint ok;
  - retiradas do `.claude/settings.local.json` as duas permissões com o caminho do OneDrive (ficaram `python --version` e `uv --version`).
- **Próximo passo:** plano do Q4 (e do Q8, do qual depende), para aprovação do autor.

## 2026-10-20 — Painel só leitura (D-034)
- **Pedido do autor:** o banco do pipeline deve ser só leitura para o painel.
- **Levantamento:** o painel abria o banco para gravação, criava as tabelas de estado ao abrir e, no "Salvar", gravava o cenário e uma versão nova de premissas, que viraria a vigente da carga seguinte (`docs/erros_ia.md`; D-034). O banco real só tinha as sementes v1 e v2 e nenhum cenário: nada a migrar e nenhum número afetado.
- **Feito (tudo numa cópia do projeto; depois, levado ao projeto real para a prova final):**
  - `app/comum.py`: conexão `read_only=True`, sem `garantir_tabelas`;
  - `src/cenarios.py` (novo): `data/painel_estado.json` (JSON, gravação atômica, aviso se corrompido, arquivo ruim movido para `.corrompido-…`), variável `RADAR_ESTADO`;
  - Simulador: salva no arquivo, com a versão vigente e o diff; não cria versão de premissas;
  - `src/estado.py`: saíram `salvar_versao` e `salvar_cenario`;
  - `pipeline.py`: `em_uso()` (abertura exclusiva no Windows) para a carga antes de começar se o banco estiver aberto; mensagem da troca final explica os Parquet;
  - `.gitignore`, `scripts/qa_painel.py` (arquivo de cenários temporário), testes, SPEC §2.1 e §2.4, `dicionario_dados.md`, `README.md` (seção 5, roteiro sem cópia do banco), `ESTADO_ATUAL.md`.
- **Experimento de travas (DuckDB × Windows, cópia):**
  - o painel antigo (gravação) impedia qualquer outro leitor;
  - com o painel só leitura, dois leitores convivem, mas a troca do banco no fim da carga falha (`WinError 5`);
  - o arquivo com atributo de somente leitura abre normalmente em `read_only`.
- **Concorrência (servidor Streamlit real × pipeline, cópia):**
  - painel aberto → carga para em cerca de 1 s, "Nada foi alterado";
  - salvar → banco igual e cenário no arquivo; reiniciar → o cenário continua;
  - painel aberto no meio da carga → banco anterior intacto e sem `.novo`; só `data/gold/execucao.parquet` mudou (limitação na D-034);
  - painel fechado → carga normal (35 s).
- **Testes:**
  - suíte padrão 155 passed (146 + 9 novos);
  - `dados_reais` do painel 59 passed (cópia) e 63 passed (projeto real, com `test_pipeline` e `test_saida_utf8`);
  - visual 2 passed;
  - galeria `--checar`: 52 prints, 0 falhas; diferença de pixels só no carimbo da hora da carga;
  - lint ok.
- **Prova final (projeto real, banco real, cenários num arquivo do scratchpad):** as 4 páginas abrem com "dados completos", salvar e reiniciar mantêm o cenário, o SHA-256 do banco e a assinatura dos 191 arquivos de `data/` ficam iguais, e nenhum `data/painel_estado.json` foi criado.
- **Tropeço do script de prova (não do painel):** a primeira versão esperava um elemento `stCaption`, que nesta versão do Streamlit tem outro nome, e métricas na página Qualidade, que não tem nenhuma; deu tempo esgotado duas vezes. O diagnóstico mostrou as 4 páginas sem exceção. Os servidores que ficaram abertos foram encerrados, e os dados reais foram conferidos intactos nas duas vezes.
- **Decisões abertas para o autor:** ativar "Salvar" no modo demonstração; retirar a tabela antiga `estado.cenarios_salvos`.
- **Próximo passo:** commit do autor e a Parte 2 (plano do Q4 e do Q8).

## 2026-10-20 — Ajustes da D-034 (pedido do autor)
- **73 → 63 explicado:**
  - os 63 eram uma rodada parcial (4 arquivos), não a suíte `dados_reais`;
  - a lista coletada mostra 73 no commit `21303e2` e 76 depois da D-034: saiu `test_app.py::test_simulador_salva_cenario_sem_nova_versao` (substituído sem aprovação, `erros_ia.md`); entraram `test_saida_utf8.py::test_pipeline_com_saida_redirecionada` e 3 testes do painel (SHA-256, reinício, banco somente leitura);
  - o teste da Fase 1 voltou com o nome original;
  - suíte `dados_reais` inteira: **77 passed** (73 + 1 + 3).
- **Testes com verificação alterada:**
  - `test_simulador_salva_cenario_sem_nova_versao`: o cenário é conferido no arquivo, não na tabela antiga;
  - `test_pipeline.py::test_carga_preserva_estado_nao_cresce_e_e_reprodutivel`: deixou de inserir um cenário na tabela antiga e confere que ela some e que as versões de premissas são preservadas.
- **`estado.cenarios_salvos`:** o pipeline a criava (`estado.criar_tabelas`) e a copiava a cada carga (`TABELAS_ESTADO`). Ajustado: não cria nem copia mais. Não foi apagada do banco real (decisão do autor); some na próxima carga. Prova na cópia (`--a-partir-de silver`): tabelas do `estado` antes `cenarios_salvos`, `log_decisoes`, `premissas_versoes`; depois só as duas últimas, com v1 e v2; 10 números, gold 25/25, público 25/25 e `data/publico` 26/26 iguais.
- **Pendências registradas** (`ESTADO_ATUAL.md` e D-034): Parquet numa pasta temporária, com troca no fim (Bloco 2); "Salvar" no modo demonstração (redesenho do painel).
- **Suítes no projeto real:** padrão 155 passed; `dados_reais` 77 passed; lint ok; `data/` real igual (191 arquivos, SHA-256 e data).
- **Próximo passo:** commit do autor e a Parte 2 (plano do Q4 e do Q8).

## 2026-10-21 — ROADMAP e harmonização dos documentos (D-035)
- **Rodadas anteriores do dia (registradas aqui):**
  - análise de contradições entre o `docs/ROADMAP.md` (entregue pelo revisor do autor) e os demais documentos, só leitura: C1 a C15 e F1 a F8;
  - E2 do ROADMAP reescrita (S1 a S6, premissas sem fonte, SES, regras do Prov. 227; premissas achadas no código: `fracao_exigencia_garantia`, faixa da indeterminada e da Classe 1 na v1, sinistralidade sobre o prêmio emitido, `comissao` = despesa de comercialização inteira, teto com IS = passivo, limites dos controles do Simulador);
  - `docs/README.md` criado; linha no `CLAUDE.md`; teste do índice em `tests/test_links_docs.py` (provado com um índice sem o `viabilidade.md`).
- **Achados conferidos no projeto (só leitura):**
  - a `BaseCompleta.zip` da SES nos originais tem todos os ramos (`Ses_ramos.csv`), um `SES_UF2.csv` (471 MB, recorte por UF a conferir), o `Ses_campos.csv` (dicionário) e um `ses_contatos.csv` (não extrair);
  - o CSV do BI do CNJ tem 11.866 CNS (sem coluna de UF);
  - o extrato do CNPJ tem todas as UFs (20.006 linhas);
  - empregados e arrecadação pela API do CNJ só existem para MG;
  - o README do repositório de dados existe e já traz "nunca apague nem substitua um Release";
  - a pasta de sessões do Claude Code na pasta nova é `c--projetos-radar-seguro-cartorio`.
- **Harmonização (pedido do autor, lista fechada):**
  - núcleo: `CLAUDE.md` (ordem de leitura, papéis, "etapa por vez, na ordem do ROADMAP", regra da cópia do banco, suítes, próximo passo pelo ROADMAP); `ROADMAP.md` (números só com nome, §3 com ramo pelo autor e conferência das normas, E1 com o fluxo e as regras do plano, E3 e E3b só interpretam o S5 e o S6, E3.5 com o que já existe, E5 com o SPEC §7 e §5.2, Radar opcional, entrega por marco, listas de corte, E6 com os dados por UF, pendências no §7, verificação de contradições no §8); `ESTADO_ATUAL.md` (etapa atual E1, sem a ordem das etapas, pendências só do autor);
  - referência: `SPEC.md` (§1.2, §2.2, §2.3, §5.1, §5.2, §6, §8 resumido, §9, §10, data de revisão); `decisoes.md` (cabeçalho e D-035); `dicionario_dados.md` (malha, as 20 tabelas do gold com a marca de pública, `origem_distribuicao`, `execucao`, conjunto público); nota no topo do plano de qualidade;
  - registros: cabeçalho e entrada do revisor no `erros_ia.md`; esta entrada;
  - pontuais: `publicacao.md` (backup, repositório de dados sem ruleset, checklist de nova carga), `CONTRIBUTING.md` (salvar a conversa), `README.md` (marco), `docs/README.md` (níveis);
  - histórico: `docs/prompts.md` e `docs/viabilidade.md` movidos com `git mv` para `docs/historico/`, com nota no topo; links atualizados.
- **Conferido no banco (só leitura) para o dicionário:** o gold tem 25 tabelas (20 + 5 internas); 18 públicas; `fato_mercado_municipio_publico` e `fato_passivo_municipio` não estão no conjunto público; o `gold.execucao` ainda tem `fator_inpc` e `mes_inpc_final` (usados só na sensibilidade e no texto do Início); `origem_distribuicao` na carga atual só tem `municipio` e `regiao`.
- **Não alterado (decisão do autor):** referências ao caminho antigo do `viabilidade.md` no texto do painel (`app/pages/3_Qualidade_dos_dados.py`), no campo `fonte` das sementes versionadas (`config/premissas/premissas_v001.yaml` e `v002.yaml`) e num comentário de `config/qualidade.yaml`.
- **Testes:** links e índice 2 passed; suíte padrão 156 passed; lint ok.
- **Próximo passo:** revisão do autor, commit e o plano da E1 (ROADMAP).

## 2026-10-21 — Ajustes finais da D-035 e enxugamento dos documentos
- **Ajustes finais (pedido do autor):** SPEC (cabeçalho, §1.1 com a fonte escolhida na Fase 0, §2.1, §2.3 como estrutura alvo, §3 com a reserva município → região imediata → estado, §9 com o Prov. 243, §10 sem "monitorado pelo radar"); CLAUDE.md (a carga oficial no banco real só com pedido explícito do autor; "fim da etapa"); ROADMAP (E5 e Radar com remissão ao SPEC §5.2, §5.3 e §7); `config/qualidade.yaml` com o caminho novo do `viabilidade.md`; o texto do painel virou pendência no ROADMAP §7; as sementes ficaram com o caminho antigo (registro do que foi gravado no banco).
- **Enxugamento (sem perder informação):** a lista de documentos ficou só no `docs/README.md` (sem as colunas "quando consultar" e "quem atualiza"); o `ESTADO_ATUAL.md` ficou com o que é, etapa, ramo, próximo passo, os 10 números, a última decisão e o que depende do autor; o SPEC ficou com o cabeçalho curto, o §8 em duas linhas (critérios das Fases 0 e 1 no `historico/viabilidade.md`, §6, e na entrada "Aceite da Fase 1" deste diário) e os riscos resolvidos no fim do §10; a seção 0 do `publicacao.md` em 3 linhas.
- **Registro que só estava no ESTADO_ATUAL:** em 2026-10-20, depois de o autor reabrir o VS Code, o `UV_LINK_MODE=copy` passou a valer nos terminais da sessão.

## 2026-10-21 — Bloco 1: chat de IA no painel (E5 reduzida, D-036)
- **Ollama:** instalado (cliente 0.32.6), com `qwen3:8b` e `llama3.1`. O servidor não estava rodando; o `ollama list` o iniciou. O `qwen3:8b` chamou a ferramenta certa no primeiro teste (cerca de 14 s, com o carregamento).
- **Feito:** `config/llm.yaml`; `src/llm.py` (interface única, só `httpx`); `src/agent/` (`ferramentas.py` com 5 ferramentas sobre o conjunto público e a UF como parâmetro; `chat.py` com o laço de ferramentas; `avaliacao.py` com a correção automática); `app/pages/4_Chat.py` (desativada sem Ollama); `eval/gabarito_chat.csv` (20 perguntas: 8 números, 4 simulação, 4 normas, 4 armadilhas, conferidas no conjunto público e no texto das normas); `scripts/avaliar_chat.py`; `tests/test_chat.py`; a página Chat entrou na lista `PAGINAS` dos testes do painel, com o Ollama apontado para uma porta vazia.
- **Avaliação (banco de demonstração, nunca o real), em três rodadas sobre o mesmo gabarito:**
  - rodada 1: (a) sem ferramentas 1/20; (c) com ferramentas 15/20. Falhas: contagem com filtro inventado (1, 2), valor "vago/interino" copiado da descrição (8), só a faixa sem o valor base (5), norma sem busca (15);
  - rodada 2 (descrições das ferramentas, valor base junto da faixa, prompt das normas): (c) 17/20. Falhas: resposta vazia (1), filtro inventado (2), recusa indevida de "cartórios vagos" (8);
  - rodada 3 (parâmetro `recorte` obrigatório com lista fechada, nova tentativa quando a resposta vem vazia, contagens por situação explicadas como totais, proibição de faixa inventada, e a correção passou a reprovar número que não veio de ferramenta): (a) 1/20, com número inventado em 2; (c) **20/20**, sem número inventado, com fonte em 19/20, 17 s em média.
  - **Cuidado:** as rodadas 2 e 3 vieram de ajustes feitos olhando as falhas das mesmas 20 perguntas; o 100% mostra que funciona neste conjunto, não é uma avaliação às cegas. O gabarito é rascunho, a revisar e congelar pelo autor (SPEC §7.1).
- **Achado no caminho:** entre a rodada 2 e a 3, o modelo inventou faixas para contagens que não têm faixa ("2.480 a 2.570" serventias), porque o prompt mandava dar sempre a faixa; corrigido no prompt e passou a ser medido como alucinação.
- **Suítes:** padrão passando (166 antes dos ajustes finais); `dados_reais` do painel 61 passed; visual 2 passed; galeria `--checar` com 0 falhas de layout (o menu ganhou o item Chat).
- **Relatório do bloco:** a sessão terminou antes de o relatório final ser entregue ao autor; os resultados acima são o registro.

## 2026-10-22 — Limpeza dos documentos (D-037)
- **Pedido do autor:** cada sessão lê só o `CLAUDE.md`, o `ESTADO_ATUAL.md` e o documento da etapa (hoje, `docs/plano_mineracao.md`).
- **Feito:**
  - `git mv` de `docs/ROADMAP.md` e `docs/plano_qualidade_e_correcoes.md` para `docs/historico/`, com nota de histórico no topo, links internos corrigidos e entrada no `historico/INDICE.md`; o `docs/README.md` (índice) foi apagado pelo autor;
  - `CLAUDE.md` só com as regras de segurança (git, 100% gratuito, dados, cópia do banco, LGPD) e a regra "siga o documento da etapa; se ele traz o plano, execute sem pedir aprovação e pare no fim da parte pedida"; saíram a ordem do ROADMAP, os notebooks privados e a biblioteca só com aprovação; mantidos, por segurança, a edição só com a ferramenta de edição e a regra de atualizar ESTADO, diário e erros ao parar;
  - regra nova dos notebooks (todos no git, sem saídas, sem citar cartório) no `CLAUDE.md`, `notebooks/README.md`, `CONTRIBUTING.md` e `src/notebooks.py`; `notebooks/privado/` saiu do `.gitignore` e da lista de pastas dos testes;
  - `tests/test_notebooks.py`: o teste "notebook versionado não usa `interno_*`" virou "texto e código não citam o CNS de um cartório" (provado numa cópia: um notebook com "CNS 048108" no texto faz o teste falhar);
  - `tests/test_links_docs.py`: o teste do índice de `docs/` virou o do índice do histórico mais "o ESTADO_ATUAL aponta para `docs/plano_<etapa>.md`";
  - `ESTADO_ATUAL.md`: etapa atual = mineração de MG, próximo passo = parte A, última decisão D-037, pendências do autor trazidas do ROADMAP §7;
  - `plano_mineracao.md`: D-036 → D-037 e a tarefa de mudar as regras saiu da parte A (feita agora);
  - SPEC, `README.md`, `publicacao.md` e `historico/INDICE.md`: caminhos do ROADMAP e do plano de qualidade corrigidos; a cascata dos números passa a ser registrada no diário e no ESTADO_ATUAL.
- **Próximo passo:** commit do autor e a parte A do `docs/plano_mineracao.md`.

## 2026-10-22 — D-038 (estudo público) e parte A da mineração
- **D-038 (decisão do autor):** saem as restrições de publicação; ficam só "sem commit/push sem pedido", "não apagar dados", "100% gratuito" e "sem nome nem CPF de pessoa física". `uv run nbstripout --uninstall` rodado (o `.git/info/attributes` ficou vazio). Regras reescritas no `CLAUDE.md`, `CONTRIBUTING.md`, `notebooks/README.md`, `docs/plano_mineracao.md` (§2 e §6) e `src/notebooks.py`. Testes: saem "notebook sem saída", "texto não cita CNS" e as checagens de `interno_*` do painel e do chat; entra "nenhum CPF nos notebooks, inclusive nas saídas"; fica a checagem de que o chat só lê tabelas do conjunto público (funcional: o chat roda também no banco de demonstração). Pipeline, auditor e `gerar_publico.py` sem mudança.
- **Ollama:** cliente 0.32.6; `qwen3:8b` respondeu "Belo Horizonte" em 13 s (com carga a frio), 100% na GPU; reserva `llama3.1` instalada.
- **Base `src/analise/`:** `dados.py` (serventias com o resultado do modelo, série semestral, BI do CNJ por serventia, reconciliação por município, RAIS, IPCA, malha), `estatistica.py` (resumo, faltantes, cercas de Tukey em log, saltos na série, série sem saltos, Spearman, concentração, deflator), `enquadramento.py` (classe pela receita, receita sem saltos), `graficos.py` (estilo, formatos brasileiros, PNG). Parâmetros em `config/analise.yaml` (com fonte). `tests/test_analise.py`: 14 testes, dados sintéticos. Nova dependência: `matplotlib`.
- **Notebook 01 (qualidade):**
  - receita de referência de 2025: 92,0% com os dois semestres, 4,9% com um, 3,1% indeterminadas (76 zero, 2 conflito); as vagas concentram 61% dos zeros;
  - zeros declarados sobem em 2025 (5,3% e 5,7%, contra 1% a 2% de 2018 a 2024-1); "não informado" só em 2026-1 (57);
  - 316 serventias (12,5%) com zero CLT, 258 delas vagas; 887 vínculos da RAIS (7,5%) sem salário de dezembro, com tempo de casa mediano de 85 meses (contra 35); 64 municípios com CLT no CNJ e sem RAIS; 0 serventias sem município;
  - CNJ × RAIS: 1,8% no total e Spearman 0,93 por município; CNPJ +15,8% (esperado); API × BI: igual em mais de 99% das serventias presentes nas duas fontes; 168 faltam no BI em 2025-2; 10 serventias com o dobro no BI em 2024-1;
  - **achados:** (a) a serventia 042986 (Turmalina, vaga, zero CLT) declarou R$ 108,1 mi em 2025-2, contra R$ 10 a 40 mil nos outros semestres: erro quase certo, fora do universo, sem efeito nos 10 números, mas +3,5% no total de MG de 2025-2; (b) a 035030 (Candeias) tem R$ 360 mil na API e R$ 93 mil no BI em 2025-2: pela API é Classe 2 (obrigada), pelo BI seria Classe 1; (c) 45 saltos de 10× ou mais em 43 serventias em 2025, muitos depois de dois semestres zerados; se todos fossem erro, 12 obrigadas virariam Classe 1 (universo −1,1%, déficit −0,7%).
- **Notebook 02 (exploratória):** receita mediana de R$ 324 mil por semestre (colada no limite de R$ 300 mil); os 10% maiores têm 62% da receita e 61% do passivo; a Classe 3 (16% das serventias) tem 66% do passivo e 57% do déficit; RI com mediana de R$ 2,4 mi e 93% fora da Classe 1; região de BH com 36% do passivo das obrigadas, 418 municípios sem obrigadas; crescimento real de 8,2% ao ano (1º semestres de 2019 a 2025, IPCA); os saltos são 5,4% do total de 2025-2 e 11,5% do de 2026-1; providas acima de R$ 300 mil: 112 em 2007, 1.087 em 2025; Spearman receita × CLT 0,83.
- **PNGs:** 16 em `docs/qa/analises/` (6 do 01, 10 do 02), agora versionados (`.gitignore`).
- **Suíte padrão:** 178 passed, 80 deselected; ruff sem erro.
- **Sugestões para o autor (nada mudado no painel):** checagem de saltos no pipeline (aviso); regra para semestre com salto grosseiro no enquadramento; conferir 042986 e 035030 no Justiça Aberta.

## 2026-10-22 — Revisão da parte A da mineração (correções)
- **Origem:** revisão de cientista de dados (só leitura, números recalculados numa cópia do banco, sem usar `src/analise/`). Os 11 números principais bateram; o veredito foi "precisa corrigir", por frases e gráficos. O autor pediu a correção só dos itens da revisão.
- **Notebook 02:**
  - vagas: "24% não são Classe 1" contava as 48 indeterminadas; agora **150 vagas de Classe 2 ou 3 (18,1%)** e mercado futuro de **R$ 35,4 mi** (antes, R$ 50 mi = passivo de todas as vagas);
  - crescimento real como **faixa de ≈ 7% a 10% ao ano**: ponta a ponta 8,2%, reta de tendência 9,7%, 2021→2025 7,9%, 2022→2025 6,5%, mesmas 2.372 serventias 8,0%, sem mudanças de mais de 10× 7,8%, série sem saltos 8,2%; IPCA 5,7% ao ano. Os saltos não explicam a taxa dos 1º semestres (nos 2º, 10,5% → 9,5%);
  - contagem acima do limite rotulada como ilustração; nova série com o limite corrigido pelo IPCA (ancorado em R$ 300 mil em 2025; R$ 214 mil em 2019): providas acima 756 → 1.087 (+331) contra 589 → 1.087 (+498) com o limite fixo, ou seja, **34% do aumento é só inflação** (a revisão estimou 761 com a âncora em dez/2025; a âncora em 2025 deixa as duas séries iguais no fim);
  - mapa: **417 municípios sem obrigada** (2 sem serventia) e 1 com obrigada de passivo zero, em amarelo; 436 com alguma obrigada (antes, "418 sem obrigadas", contando pelo passivo);
  - concentração com a base dita: 10% maiores = 60,5% do passivo de todas e **53,5% do passivo das obrigadas**; Classe 3 = 65,9% do passivo de todas e **73,2% do das obrigadas**; 106 providas a menos de 10% do limite;
  - correlações: "prevê" virou "está associada"; CLT × passivo alto por construção; a previsão fica para o notebook 06;
  - gráficos: 2026-1 marcado como preliminar (57 não informaram); CLT com uma barra por número de empregados; eixo x do gráfico do limite só com anos inteiros; uma linha explicando por que o número de obrigadas é fracionário.
- **Notebook 01:**
  - §5: a checagem de município passou a ser feita no `silver.serventia` (a de antes era circular: `dados.serventias()` usava INNER JOIN com o município); resultado igual, 0 de 2.525;
  - §7b: as duas direções; 12 obrigadas saem e 1 entra (047001, Caldas, cujo salto foi em 2025-1): **efeito líquido −11 (≈ −1,0%)**, déficit −0,7%; ESTADO_ATUAL atualizado;
  - §1: 276 dos 571 zeros de 2007 vêm antes do 1º valor declarado pela serventia; em 2025, nenhum;
  - §4: "sem remuneração de dezembro (vazio)": os 887 têm o campo vazio, nenhum com R$ 0; §8: a explicação dos +15,8% do CNPJ virou hipótese;
  - gráfico dos saltos: os R$ 0 saíram do eixo em reais e foram para uma faixa separada.
- **Código e testes:** `dados.serventias()` com LEFT JOIN no município; `estatistica.saltos()` com `is None` (janela 0 ou fator ≤ 1 dá erro, em vez de virar o padrão); `crescimento_medio(periodos=)` e `crescimento_tendencia()` novos. `tests/test_analise.py`: +5 testes sintéticos (salto para baixo e histórico curto; janela/fator inválidos; serventia sem município não some; tendência; só as pontas) e 1 `dados_reais` (as somas de `serventias()` batem com `gold.fato_mercado_uf`, numa cópia do banco).
- **Como foi editado:** notebooks pela ferramenta de notebook. Para poder abri-los na ferramenta, as saídas foram limpas com `jupyter nbconvert --clear-output` e depois refeitas com `jupyter nbconvert --execute --inplace` (os notebooks só leem o banco, em modo somente leitura). PNGs conferidos um a um.
- **Suítes:** padrão 182 passed, 81 deselected; `dados_reais` de `test_analise.py` 1 passed (cópia do banco).

## 2026-10-22 — Documento "Entenda o projeto" para leigos
- **O que foi feito:** `docs/entenda_o_projeto.md`, para quem não conhece seguro nem o Prov. 227: o problema e a regra, o básico de seguro-garantia (tomador, segurado, seguradora; ramos 0775/0776 da SUSEP), as perguntas do projeto com o que é dado real e o que é suposição, e um glossário (cartórios, direitos trabalhistas, seguro, dados, parte técnica, estatística). Link no topo do README e do `CONTRIBUTING.md` e no `ESTADO_ATUAL.md`.
- **Decisões:** documento próprio em `docs/`, com link no topo do README (a primeira coisa que se lê no GitHub), para o README continuar curto.
- **Suposições:** o exemplo numérico do documento é ilustrativo (taxa de 2% = premissa base, `fonte: suposição`).
- **Limitações encontradas:** o "porquê" da regra cita só o que a norma diz (art. 13, § 1º); a norma da SUSEP sobre seguro-garantia não foi citada, porque não está entre as normas baixadas em `data/bronze/normas/`.
- **README corrigido no mesmo dia:** "Proteção de dados" passou a seguir a D-038 (antes citava a D-030), dizendo que o conjunto público e o painel ainda seguem a regra antiga; escopo "do Brasil" virou "hoje só MG"; o "será completado com: problema" aponta para o novo documento; `docs/qa/analises/` aparece como versionado (antes "docs/qa/ fora do git"); notebooks "com as saídas"; a recusa do chat por serventia explicada pelo conjunto público. O prompt do chat (`src/agent/chat.py`) ainda diz que os dados por serventia "não são publicados": não foi mexido.
- **Próximo passo:** segue a parte B do plano de mineração.

## 2026-10-23 — Plano do projeto, testes de métodos T1 a T7 e D-039
- **O que foi feito:**
  - ambiente novo no WSL: carga 2026-10-19 da equipe instalada com `scripts/baixar_dados.py` (bronze, silver, gold, banco; hashes conferidos). Os originais grandes (`originais-2026`) não foram baixados: só são necessários para regerar um extrato do bronze;
  - `scripts/testes_metodos.py` (escrito fora do repositório): compara de 3 a 7 métodos em sete pontos que dependem de estimativa (T1 empregados pela receita, T2 previsão da arrecadação, T3 subida de classe, T4 vacância, T5 salário de dezembro ausente, T6 reserva salarial, T7 faixa do prêmio), cada um contra uma referência simples e com o indicador fixado antes. Rodado três vezes (duas com bibliotecas temporárias, uma com as do projeto): `resultados.json` idêntico byte a byte. Resultados em `docs/qa/analises/testes_metodos_resultados.json`, explicados em `docs/qa/analises/testes_metodos.md`;
  - `docs/plano_projeto.md`: seis etapas até a entrega, portões, riscos e as decisões do autor com a etapa de cada uma; revisado contra os documentos e o banco (os números citados batem com o `resultados.json`, exceto o T6, que dizia 143 municípios em vez de 135: corrigido), com os trechos quebrados da exportação trocados por tabelas e "Fase" trocado por "Etapa";
  - `docs/plano_mineracao.md` reescrito como detalhamento da Etapa 1, coerente com o plano do projeto (D-039); `ESTADO_ATUAL.md` aponta para os dois;
  - `uv add scikit-learn statsmodels mlxtend`;
  - escada de perguntas com 9 degraus: a pergunta do STF saiu do `plano_projeto.md` e do `entenda_o_projeto.md`. O cenário do STF continua no Simulador e nos riscos;
  - `notebooks/README.md` excluído: as regras já estavam no `CONTRIBUTING.md` (seção Notebooks) e a lista dos notebooks está no `plano_mineracao.md`. As referências vivas (README, CONTRIBUTING, notebook 00, `src/notebooks.py`, `tests/test_notebooks.py`) apontam para o CONTRIBUTING; as menções nos registros antigos ficam como estão;
  - `CONTRIBUTING.md`: qualquer colaborador pode fazer o merge na `main` (D-040, proposta), alinhando o texto à ruleset, que já não exige aprovação.
- **Decisões:** D-039 e D-040 (proposta; vale com a aprovação do autor no pull request). O teste `test_estado_atual_indica_o_documento_da_etapa` exige o prefixo `plano_`, por isso o arquivo se chama `plano_projeto.md`.
- **Suposições:** nenhuma nova. Os testes só leem dados e premissas v2.
- **Limitações encontradas:**
  - T1: nenhum método acerta o total de uma região não vista com até 5% de erro (o melhor, ~9%);
  - T2 e T3: os vencedores no passado erram para baixo em 2024–2026 (o 2026-1 parcial, R$ 3,20 bi, já passou do P90 da previsão; 218 subidas previstas × 294 reais);
  - T4: vazamento declarado (receita e CLT de vagas medidos sob interino);
  - T6: os municípios testados são os 135 maiores, que diferem mais da própria região que os pequenos;
  - T7: sem valor real para comparar; o critério é a largura e a probabilidade declarada da faixa.
- **Próximo passo:** commit e pull request; aprovação do autor; depois, a parte B do plano da mineração.

## 2026-10-23 — Push direto na main e Claude sem restrição de git (D-041)
- **O que foi feito:** a pedido de um colaborador, `CLAUDE.md` (seção Git), `CONTRIBUTING.md` (Fluxo de trabalho) e `docs/publicacao.md` (seção 4) passam a dizer que qualquer colaborador dá commit e push direto na `main`, sem PR, e que o Claude executa `commit`, `push`, `merge` e demais comandos de `git`/`gh` pedidos na mensagem atual. Decisão D-041 (aprovação do autor pendente).
- **Conferência no GitHub:** `gh api .../rulesets` retornou lista vazia e `branches/main/protection` retornou "Branch not protected". Não há ruleset ativa, então o push direto de colaboradores com permissão de escrita já funciona (a ruleset de 2026-10-20 não existe mais). `docs/publicacao.md`, seção 4, ficou com essa conferência.
- **Ruleset recriada** a pedido do autor, via `gh api` (id 25761192): `main protegida`, ativa, regras `deletion` e `non_fast_forward`, sem PR obrigatório e sem Bypass list.
- **Correção:** `plano_projeto.md` citava "D-041 em diante" como próxima decisão; passou a "D-042 em diante".

## 2026-10-23 — Parte B da mineração: notebooks 03, 04 e 05 (e revisão)
- **Ramo:** `notebooks-03-04-05`. Tudo rodado numa **cópia** do banco: `src/notebooks.py` passou a aceitar `RADAR_BANCO` (como o painel), com teste. O banco real ficou com o mesmo SHA-256 da linha de base (`3e055af4…`); os 10 números da cópia batem com `linha_de_base.json`.
- **Código novo em `src/analise/`:** `padroes.py` (itens, Apriori, referência por atribuição, ganho, melhoria mínima, estabilidade, `tabela_regras`), `grupos.py` (matriz em log, padronização, k-means, Ward, silhueta/cotovelo/ARI, perfil, grupo-alvo, `tabela_grupos`), `classificacao.py` (modelos e métricas, validação cruzada 5 × 3, permutação, logística, painel da subida, recalibração de Platt, origem móvel, faixas, `tabela_subidas`). `graficos.py`: formato `num3`. Premissas novas em `config/analise.yaml` (`padroes`, `grupos`, `classificacao`), cada uma com fonte; as sem fonte estão marcadas `fonte: suposição`. Testes: `tests/test_analise_modelos.py` (15, sintéticos).
- **Notebook 03 (padrões):** 2.447 serventias com classe conhecida (as 78 indeterminadas fora), 1.103 obrigadas (45,1%; + 18,3 do peso das indeterminadas = 1.121,3 do painel). Referência: 84,1% das serventias com RI são obrigadas; RCPN 25,3%. RTD e RCPJ andam sempre juntos (lift 8,8). Regras com classe ou situação no "se" (91) saem por serem definição. 14 regras passam no ganho e na melhoria; 11 são estáveis nas 2 reamostragens de 80%. As 10 principais: RI + 3 a 9 CLT (87,6%, lift 1,94), porte 10+ CLT (82,2%), 3 a 9 CLT (73,7%), regiões de Divinópolis, Pouso Alegre e BH. Desenho da `gold.analise_regras`.
- **Notebook 04 (grupos):** 2.444 serventias (81 fora, com 1,5% do déficit). Silhueta máxima em k = 6 (0,500; k = 2 dá 0,496); Ward com ARI 0,935; outras sementes dão os mesmos grupos. Grupos: vagas pequenas (688), providas pequenas de Notas/RCPN (634), providas médias de uma atribuição (578), registro completo RI/RTD/RCPJ (188), vagas grandes (91, R$ 32 mi de passivo, mercado futuro) e **providas grandes (265): grupo-alvo**, 11% das serventias, 24% das obrigadas e 54,6% do déficit (49% a 59% do mínimo ao máximo das premissas), R$ 77 mil de déficit por obrigada. Desenho da `gold.analise_grupos` (por serventia).
- **Notebook 05a (vacância, T4):** 2.406 serventias; floresta AUC 0,884 (T4 0,886), logística 0,849 (T4 0,848), referência 0,500; Brier 0,123. Sem receita e CLT (vazamento declarado), AUC 0,817. A receita é a variável que mais pesa; as vagas não achadas são as grandes (mediana R$ 365 mil). Leitura de associação.
- **Notebook 05b (subida, T3):** 24.416 casos de treino e 2.692 de teste; floresta Brier 0,068 (T3 0,068), AUC 0,88, 217,7 subidas previstas × 294 reais. Recalibração de Platt com 2022–23: 249,3 (−15%), Brier 0,0676. **Origem móvel (10 janelas):** a recalibração erra mais em média (67,9 × 53,3 subidas) e melhora o Brier em 4 de 10; a taxa de subida dobra em 2021–22 (inflação). Mantido o método do plano, com a faixa tirada dos erros da origem móvel. **Projeção (não oficial):** 2026: 145 subidas (P10–P90 96 a 265), ≈ 100 entre as providas; até 2027: 210 (153 a 468). Conferência: 97 das 1.158 já passaram do limite no 2026-1 parcial.
- **PNGs (10):** `03_referencia_obrigadas_por_atribuicao`, `03_regras_obrigada_principais`, `04_escolha_k_silhueta_cotovelo`, `04_grupos_receita_clt`, `04_grupos_participacao_deficit`, `05a_vacancia_roc_matriz_confusao`, `05a_vacancia_importancia`, `05b_subida_calibracao_teste`, `05b_subida_origem_movel`, `05b_subidas_projecao_2026_2027`.
- **Revisão (cientista de dados), correções feitas:** (1) ordem das regras dependia do hash dos textos da sessão (Notas→RCPN e RCPN→Notas trocavam de lugar): ordenação fixa em `padroes.regras`/`regras_alvo` e no notebook, com teste e prova rodando com `PYTHONHASHSEED` 1 e 2; (2) rótulos do gráfico de projeção trocados (`"recal" in "sem recalibração"`); (3) texto da calibração dizia que a subestimação estava nas faixas altas (está nas baixas e médias); (4) "metade das janelas" → 4 de 10; (5) "dois terços do déficit no máximo" → 49% a 59%, agora calculado no notebook; (6) Varginha citada entre as 10 principais (é a 11ª); (7) faixas de taxa de subida e de queda da inércia corrigidas; (8) afirmação "as vagas não achadas são as grandes" sem número: agora com a receita de VP, FN e FP; (9) matriz de confusão que faltava no 05b; (10) "Limitações" que faltavam em 7 seções; (11) gráficos: legendas e rótulos sobrepostos (03, 04, 05a), eixo log com marcas confusas, limite de R$ 300 mil fixo no código trocado por `limites_classe()`; (12) tabelas de Brier e importância com 3 casas (com 2, tudo virava 0,07 ou 0,00); (13) frase sobre a lei de organização judiciária sem fonte, retirada.
- **Reprodutibilidade:** os três notebooks rodados do zero duas vezes (saídas limpas antes): saídas de texto e os 10 PNGs idênticos byte a byte.
- **Dados pessoais:** nenhum nome nem CPF; cartório só por CNS (tabela de grupos) e regiões do IBGE.
- **Suítes:** padrão 198 passed, 81 deselected; `dados_reais` de `test_analise.py` e `test_notebooks.py` 23 passed (cópia); ruff sem erro. Nenhuma biblioteca nova.
- **Para o autor decidir:** recalibração do 05b (manter, tirar ou usar as duas como faixa); premissas `fonte: suposição` novas; `gold.analise_grupos` por serventia ou por grupo; o 05b não tem tabela `gold.analise_*` no plano (a tabela de subidas fica como insumo do 07).
- **Como foi editado:** os notebooks foram montados a partir de um texto com as células (no scratchpad da sessão) e executados com `jupyter nbconvert --execute --inplace`; nas próximas edições, usar a ferramenta de notebook.
- **Próximo passo:** notebook 06 (fecha a parte B).
- **Commit:** `84e0c75`, a pedido do autor.

## 2026-10-23 — Validação dos notebooks 00 a 05 e notebook extra 05c (vacância no tempo)
- **Validação:** os notebooks 00 a 05 rodados de novo do zero numa cópia do banco (`RADAR_BANCO`). Saídas de 01 a 05 idênticas às do commit `84e0c75`; os 26 PNGs `01_*` a `05*` idênticos byte a byte. O 00 está versionado sem saídas (é o exemplo); rodado, mostra os 10 números iguais à linha de base. Banco real com o mesmo SHA-256 da linha de base.
- **Notebook 05c (extra, pedido do autor):** a taxa de vacância a partir das datas do cadastro do Justiça Aberta (bronze, coleta de 17/10/2026, 27 UFs). Nova função `dados.cadastro_cnj` (lê só CNS, UF, status, situação, data da decisão, data de ingresso e tipo do responsável; nome, substitutos e contatos não são lidos; teste com bronze sintético) e `src/analise/vacancia.py` (lotes, estoque de providas reconstruído, taxa por ano, por UF e por classe). Parâmetros novos em `config/analise.yaml` (`vacancia`: `lote_min` 10, `fonte: suposição`; `inicio_confiavel` 2011; `ano_recadastro` 2024, da D-025). Testes: +3 em `tests/test_analise_modelos.py`.
- **Achados:**
  - datas: 1.008 das 2.525 ativas de MG têm decisão em 2010 (983 em dois dias: carga do sistema, hipótese); os lotes de 2011–2014, junho de 2021 e setembro de 2025 são provimentos (ondas de concurso); 65% das ativas de MG têm ingresso do responsável em 2024 (recadastramento; mediana de 54% nas UFs), como já dizia a D-025;
  - taxa de vacância observada em MG: ≈ 1% ou menos até 2020 e ≈ 2% em 2021–23 (pisos, por viés de sobrevivência), 12,5% em 2024 (contaminada: 226 das 250 vagas têm ingresso do interino em 2024), 7,5% em 2025 (coerente: interino entra, em mediana, 4 dias antes da decisão) e 4,0% em 2026 anualizado;
  - por classe (receita do ano anterior, antes de vagar, sem o vazamento do 05a): em 2025, Classe 1 12,0%, Classe 2 3,3%, Classe 3 5,3%; Classes 2 e 3 juntas 3,9% (39 de 1.000; intervalo de 95% de 2,7% a 5,1%);
  - UFs em 2025: mediana 11,1%, de 0 a 60% (AL): atos locais, não uma taxa comum;
  - **faixa proposta ao autor** para a P(fim da delegação no ano) da D-025: 2% / 4% / 7,5% (≈ 20 / 44 / 84 fins de delegação por ano entre as ≈ 1.121 obrigadas). Nada foi mudado nas premissas.
- **PNGs (4):** `05c_decisoes_por_ano`, `05c_taxa_vacancia_mg_por_ano`, `05c_taxa_vacancia_por_uf`, `05c_taxa_vacancia_por_classe`.
- **Revisão feita antes de parar:** números do texto conferidos contra as saídas (corrigidos: 983 → 1.008 em 2010, mediana das UFs 60% → 54%, 2024 por classe, intervalo de 95% passou a ser calculado no notebook, ≈ 45 → 44); a afirmação "o interino entra pouco antes da decisão" passou a ter conta (mediana de 4 dias); nota no gráfico das UFs sobre as UFs com menos de 50 providas; limite da Classe 1 no rótulo vindo de `limites_classe()`. Rodado duas vezes do zero (uma com `PYTHONHASHSEED` 7): saídas e PNGs idênticos. Sem nome nem CPF: as datas aparecem só somadas.
- **Suítes:** padrão 201 passed, 81 deselected; `dados_reais` de `test_analise.py` 1 passed (cópia); ruff sem erro.
- **Para o autor decidir:** adotar ou não a faixa do 05c na D-025; fazer uma segunda coleta do cadastro do CNJ (mesma API, gratuita) para medir as mudanças de situação entre duas datas; o nome "05c" (extra, fora da numeração do plano) pode mudar.
- **Próximo passo:** notebooks 06, 07 e 08.

## 2026-10-23 — Notebooks 06 (regressão) e 08 (sensibilidade e concentração), com revisão
- **O que foi feito** (só os notebooks 06 e 08; o 08 é da parte C e foi adiantado; 03, 04, 05, 07 e 09 ficam para depois):
  - **Código:** `src/analise/regressao.py` (recorte e variáveis do T1, referência por decil, floresta, Poisson, validação "região de fora", fatores do Poisson com IC robusto, `tabela_clt_modelo`; distribuição salarial usada por município, divisão da variância do log, Shapley do R², regressão log-log com validação em dobras por grupo) e `src/analise/sensibilidade.py` (faixas das seis suposições, tornado por `simulador.resumo_por_totais`, tornado do passivo e do universo por `motor.calcular_serventias`, Monte Carlo triangular vetorial, `tabela_tornado`, `tabela_monte_carlo`, salário estimado do T5, encolhimento do T6, receita líquida do BI). `estatistica.py`: `curva_lorenz` e `gini`. `src/notebooks.py`: `conectar()` aceita `RADAR_BANCO` (a mesma variável do painel), para rodar os notebooks numa cópia; nota no `CONTRIBUTING.md`. Parâmetros novos em `config/analise.yaml` (seções `regressao` e `sensibilidade`), todos com fonte (o script e o documento dos testes ou o plano da mineração).
  - **Testes:** `tests/test_analise_modelos.py`, 16 sintéticos (Gini e Lorenz; recorte; referência; a validação nunca treina na região testada; métricas; floresta e Poisson; tabela; variância do log; Shapley soma o R² e a log-log recupera elasticidades; distribuição usada; Monte Carlo vetorial igual ao `resumo_por_totais`; escolha de garantia somando 1; tornado; sorteios na faixa, repetíveis e "juntos"; salário estimado; encolhimento só nos pequenos; receita líquida nunca negativa) e 1 `dados_reais` (o motor refeito dá o prêmio oficial e o tornado repete o T7).
  - **Notebook 06:** (a) floresta com a região de fora: **MAE 1,86** (referência 2,34, −20%), R² 0,75, erro do total de uma região 9,3% (de −19% a +26%; 7 das 13 fora de ±10%); soma de MG prevista de fora −2,5%. Poisson: receita 2× → +67% de CLT; Notas, RI, RTD e Protesto −34% a −51% com a mesma receita. Igual ao T1 nas casas mostradas. (b) passivo = CLT × passivo médio por vínculo: a quantidade explica 75% a 79% da diferença entre serventias, o salário 18% e o tempo de casa 6% (R² 0,992, igual fora da amostra); multa do FGTS = 48,5% do passivo; ≈ 72% do passivo cresce com o tempo de casa. Desenho da `gold.analise_clt_modelo`.
  - **Notebook 08:** tornado (taxa R$ 184–645 mil; escolha do seguro R$ 184–516 mil; premissas do passivo e do universo abaixo de ±10%), igual ao T7; Monte Carlo **P5–P95 R$ 206–736 mil** (T7: 207–737), com o patrimônio junto R$ 155–906 mil, e 0,05% dos sorteios acima da metade do canto máximo; T5 +1,0% no passivo médio por vínculo e **+0,6% no passivo total**; T6 **−1,6%**; Gini 0,74 (receita), 0,71 (passivo), 0,63 (passivo das obrigadas), 0,52 (déficit esperado); receita líquida do repasse: 873 providas acima de R$ 300 mil (1.103 pela arrecadação), universo −20%, prêmio −8,5% com a faixa de déficit da base (ver o ajuste abaixo; +3,3% com a faixa pela receita líquida). Desenho da `gold.analise_tornado` e da `gold.analise_monte_carlo`.
  - **PNGs:** 11 em `docs/qa/analises/` (`06_clt_erro_por_metodo`, `06_clt_declarado_x_previsto`, `06_clt_erro_total_por_regiao`, `06_clt_poisson_fatores`, `06_passivo_decomposicao`, `06_passivo_residuos`, `08_tornado_premio`, `08_monte_carlo_premio`, `08_sensibilidade_passivo`, `08_concentracao_lorenz`, `08_receita_liquida_providas`).
- **Como foi feito:** tudo numa cópia do banco (`RADAR_BANCO` no scratchpad da sessão); o banco real ficou com o mesmo SHA-256 (`3e055af4…`) e a mesma data (23/10 15:55) do começo. Os notebooks foram **gerados inteiros** por um script construtor no scratchpad (nbformat) e executados com `jupyter nbconvert --execute --inplace`; nenhum arquivo do repositório foi editado por substituição de texto.
- **Revisão (como a da parte A):** conteúdo × plano, números × saídas e banco, gráficos, texto, reprodutibilidade e dado pessoal. Correções:
  1. leitura do 06: mediana do resíduo por decil entre −0,55 e +0,02 (o texto dizia −0,6 e +0,1);
  2. maiores resíduos: 36 a 65 empregados (dizia 40 a 65);
  3. CLT zero: no recorte são 285 (229 vagas), com previsão mediana de 0,9 (o texto citava as 316 de MG e "1 ou 2");
  4. "três quartos do passivo crescem com o tempo de casa" → ≈ 72%, com a conta por verba;
  5. leitura do 08: os 10% maiores contratos têm ≈ 43% da IS (dizia "quase metade"); cantos 4,4 vezes mais largos que a P5–P95 (dizia 4,5);
  6. tabela de migração de classe acrescentada à §5 do 08, para explicar por que o prêmio sobe com a receita líquida;
  7. gráficos: legendas sobre as barras (06 métodos, 08 tornado e passivo), eixos com ponto decimal, escala log do Poisson com rótulos sobrepostos, marcadores enormes na legenda do resíduo, "R$ … a R$ …" virando fórmula do matplotlib (dois `$`), nota de fonte colada no título do eixo;
  8. número fixo (2.444) tirado da nota do gráfico do Poisson; CLT declarado formatado como inteiro.
- **Reprodutibilidade:** os dois notebooks gerados e executados duas vezes do zero: saídas (sem contadores de execução) e os 11 PNGs com o mesmo SHA-256.
- **Suítes:** padrão 197 passed, 2 skipped (só Windows), 82 deselected; `dados_reais` de `test_analise.py` e `test_analise_modelos.py` 2 passed (cópia do banco); ruff sem erro.
- **Decisões:** D-042 (proposta depois da revisão, com aprovação do autor pendente): hierarquia base > P5–P95 > cantos na faixa do prêmio; receita líquida como sensibilidade com a faixa de déficit da base; T5 e T6 só na tabela de sensibilidade; CLT de outros estados só como total estadual, com ±10% como piso e a RAIS como conferência. Detalhes decididos pela IA, conforme o plano: o tornado inclui também as premissas do passivo e do universo que têm mínimo ≠ máximo; no Monte Carlo, a escolha do seguro sorteada redistribui o resto entre bens e fiança na proporção do base; na receita líquida, semestre com repasse > arrecadação fica com zero e a serventia sem BI fica sem desconto; a validação da log-log agrupa as serventias pela distribuição salarial usada.
- **Suposições:** nenhuma nova (todos os parâmetros novos vêm do script dos testes ou do plano).
- **Limitações encontradas:** T1 com erro de até 26% numa região; a decomposição do 06b usa salário e tempo da distribuição, não da serventia; o Monte Carlo mede a incerteza dentro das faixas das suposições, que não têm fonte; a receita líquida não desconta os valores "por conta de terceiros" (inciso XXV, sem fonte pública); 36 providas com repasse zero e 8 semestres com repasse maior que a arrecadação no BI.
- **Ajuste (mesmo dia):** a §5 do 08 passou a usar a **faixa de déficit da classe da base** (como na D-019: a leitura alternativa muda só quem entra no universo), com a função nova `sensibilidade.com_faixa_da_base` e o teste `test_faixa_da_base_muda_so_o_deficit`. Resultado exato: universo −20,3% (1.121,3 → 893,6), déficit R$ 36,9 → 33,7 mi, prêmio R$ 368,7 → **337,4 mil (−8,5%)**. A estimativa de cabeça era ≈ −8% (R$ 338 mil); a diferença é o peso das indeterminadas, que cai de 0,678 para 0,542 (−R$ 0,1 mi de déficit). A versão com a faixa pela receita líquida (+3,3%) ficou como nota. O 08 rodou duas vezes do zero com as mesmas saídas e PNGs; suíte padrão 198 passed.
- **Próximo passo:** notebooks 03, 04 e 05 (parte B); depois 07 e 09 (parte C).

## 2026-10-24 — Junção dos ramos dos notebooks 03 a 05 e 06/08
- **O quê:** a pedido do autor, ramo novo `notebooks-03-04-05-06-08`, criado a partir de `notebooks-03-04-05` (`c18ce95`), com merge de `origin/notebooks-06-08` (`8a7f86b`).
- **Conflitos resolvidos:** `src/notebooks.py` (as duas versões de `conectar()` faziam o mesmo com `RADAR_BANCO`; ficou a do ramo `notebooks-06-08`); `tests/test_analise_modelos.py` (os dois ramos criaram o arquivo: imports juntados e os testes dos dois mantidos, sem nomes repetidos); `docs/ESTADO_ATUAL.md`, `docs/diario.md` e `docs/erros_ia.md` (entradas dos dois ramos mantidas).
- **Com isso:** parte B concluída (03 a 06 e 05c); o 08 da parte C adiantado. Nenhum notebook rodado de novo nesta junção. Suíte padrão: 218 passed, 82 deselected; ruff sem erro.
- **Próximo passo:** notebooks 07 e 09 (parte C); enviar o ramo e juntar na `main`, quando o autor pedir.

## 2026-10-27 — Notebook 07 (previsão do mercado)
- **O que foi feito** (pedido do autor: o notebook 07, seguindo o `plano_mineracao.md`):
  - **Código:** `src/analise/previsao.py`: série de MG, os 7 métodos do T2 com os mesmos nomes, origem móvel (MAPE, MASE, viés), faixa empírica, completar um semestre incompleto, teste da quebra de nível (statsmodels), fatores de crescimento de MG, erros anuais, desvios de cada serventia em relação a MG, sorteio das receitas, limites corrigidos pela inflação, mercado projetado pelas funções do modelo (`universo`, `peso_indeterminada`, `resumo_por_totais`), teste no passado da contagem acima do limite e `tabela_previsao` (desenho da `gold.analise_previsao`). Parâmetros novos em `config/analise.yaml`, seção `previsao`.
  - **Testes:** `tests/test_analise_previsao.py`, 12 sintéticos (tendência exata, origem móvel sem olhar o futuro, faixa, quebra recuperada, completar só quem não informou, fatores e erros anuais, desvios sem saltos e na banda, sorteio mantém vazio, mercado sem mudança = modelo, subidas, descidas, § 3º e Classe 2 → 3, inflação, colunas da tabela) e 1 `dados_reais` (a origem móvel repete o MAPE do T2 e o mercado sem mudança dá o prêmio oficial).
  - **Notebook 07** (8 seções):
    - série: os saltos grosseiros somam R$ 161 mi no 2025-2 e R$ 330 mi no 2026-1, quase todos das serventias 059816 (R$ 157 mi), 042986 (R$ 108 mi) e 046219 (R$ 94 mi); sem eles, o 2026-1 parcial cai de R$ 3,20 bi para R$ 2,87 bi; a arrecadação limpa acelerou (+14% a +21% sobre o ano anterior desde 2024-2);
    - origem móvel: MAPE e viés dos 7 métodos iguais aos do T2 (tendência 7,4%, SARIMA 10,5%, referência 14,8%);
    - previsão (projeção): R$ 5,92 bi em 2026 (+7,3%) e R$ 6,71 bi em 2027; faixa e central iguais às do T2; SARIMA: R$ 6,51 bi em 2026;
    - quebra em 2025-2: +7,6% (IC 95% −8,7% a +26,7%; valor-p 0,37) sem saltos e com o 2026-1 completado; sem evidência; o 2026-1 limpo e completado (R$ 2,90 bi) fica dentro da faixa (R$ 2,38 a 2,93 bi);
    - projeção por serventia (receita de 2025 × crescimento de MG × desvio sorteado), com teste no passado (anos-base 2019 a 2024): erro médio de 40 e 36 serventias a 1 e 2 anos, contra 99 e 204 da referência "repete o ano-base"; com o crescimento real de MG, 15 e 17; a faixa P10–P90 é estreita (17% e 40% de cobertura);
    - mercado (variante principal; central e P10–P90): obrigadas 1.147 em 2026 e 1.204 em 2027 com o limite fixo, 1.124 e 1.161 com o limite corrigido pelo IPCA (4,58% em 12 meses), 1.190 e 1.244 com a quebra; prêmio entre R$ 366 e 369 mil em todas (passivo de 2025; quem entra é pequeno, e 51 a 98 serventias passam da Classe 2 para a 3); 78 subidas em 2026 contra 145 da floresta recalibrada do 05b (105 sem recalibração);
    - desenho da `gold.analise_previsao` (107 linhas: 19 da arrecadação e 88 do mercado, todas com o rótulo "projeção"; corrigido em 2026-10-28, antes dizia 99 e 80, ver `erros_ia.md`).
  - **PNGs (5):** `07_serie_arrecadacao_saltos`, `07_origem_movel_tendencia`, `07_previsao_arrecadacao_2026_2027`, `07_teste_contagem_acima_do_limite`, `07_projecao_universo_premio`.
- **Como foi feito:** tudo numa cópia do banco (`RADAR_BANCO` no scratchpad); o banco real ficou com o mesmo SHA-256 da linha de base (`3e055af4…`). O notebook foi gerado por um script construtor no scratchpad (nbformat) e executado com `jupyter nbconvert --execute --inplace`; rodado duas vezes do zero: saídas e PNGs idênticos (um PNG mudou depois só por um ajuste de rótulo, com as saídas de novo iguais). Os números do texto foram escritos depois da execução e conferidos contra as saídas.
- **Detalhes decididos sozinho** (conforme o plano): o central da projeção usa o crescimento central de MG, e a faixa também sorteia o crescimento (com o crescimento sorteado também no central, a mediana caía para baixo nos anos-base antigos, por causa dos erros de 2013 a 2017); a faixa de déficit segue os limites do cenário (no corrigido, os limites corrigidos valem para tudo); o 2026-1 completado e a série sem saltos entram só nas sensibilidades; o passivo de cada serventia fica o de 2025.
- **Suposições novas** (`fonte: suposição` em `config/analise.yaml`, `previsao`): completar o 2026-1 com o próprio 2025-1 × o crescimento de quem informou; desvios só de serventias entre L/3 e 3L e dos 6 anos-base mais recentes; 500 sorteios; o IPCA dos últimos 12 meses do banco como inflação de cada ano futuro (o índice vem da redação original do art. 16, § 2º; a do Prov. 243 não nomeia índice).
- **Achados para o autor:** ver `docs/ESTADO_ATUAL.md`, "O que depende do autor agora" (regra do salto, coleta nova do 2026-1, limite fixo × corrigido, suposições novas). O MASE do T2 estava com o divisor errado (nota acrescentada em `testes_metodos.md`; o vencedor não muda).
- **Suítes:** padrão 230 passed, 83 deselected; `dados_reais` de `test_analise_previsao.py` 1 passed (cópia do banco); ruff sem erro.
- **Próximo passo:** notebook 09 (conclusões e lacunas), que fecha a parte C.

## 2026-10-27 — Validação de todos os notebooks (confiança e lacunas)
- **Reexecução (Portão 1):** os notebooks 01 a 08 (com o 05c) rodados do zero no ramo juntado, numa cópia do banco: as saídas de todas as células são **iguais às commitadas**. Os 11 PNGs do 06 e do 08 mudaram byte a byte, mas são idênticos pixel a pixel (só metadados); foram restaurados. Banco real com o mesmo SHA-256 da linha de base.
- **Confiança por degrau da escada:** 1 a 4 altos (fontes coerentes; passivo robusto: T5 +0,6%, T6 −1,6%, premissas abaixo de ±10%); 3 com a maior incerteza dos dados: a leitura literal da receita (art. 2º, XXIV) tira 20% do universo, mais que todos os problemas de dado; 5 a 8 só suposições (P5–P95 do prêmio R$ 206–736 mil); 9 (resultado da seguradora) **sem nenhum notebook**: a sinistralidade vai de 1,7% a 73,9% (SES, ramos 0775/0776, carteira de obras e contratos).
- **Lacunas encontradas para o 09 e para o autor:**
  - pergunta 9 sem análise: conta indicativa com a P(fim da delegação) do 05c (≈ 4% ao ano nas Classes 2 e 3) e taxa de 2%: sinistralidade ≈ 2 × q, sendo q a parte da IS que vira sinistro por delegação encerrada (suposição); a base da SES (10,9%) equivale a q ≈ 5,5%, e o resultado técnico zera com q ≈ 37%;
  - cenário do STF (ADI 8015) fora do Monte Carlo: "suspende" zera a demanda;
  - previsão do 07 provavelmente conservadora: a principal supõe +7,3% em 2026, mas o 2026-1 limpo e completado já está +22% sobre o 2025-1 e o crescimento recente foi de 14% a 21% ao ano; as subidas de 2026 divergem entre o 07 (78) e o 05b (145);
  - faixas das projeções mal calibradas (07: 17% a 40% de cobertura; 05b: recalibração pior na origem móvel);
  - prêmio projetado com o passivo de 2025 (sem reajuste de salário).
- Nada foi alterado no código nem nos notebooks.
- **Depois, a pedido do autor ("registre, mas não faça ainda o 9"):** propostas de melhoria para cada ponto de baixa confiança (M1 a M10), na seção nova "Melhorias de confiança" do `plano_mineracao.md`. A mais importante reaproveita a medida F6 de 18/10: passivo ÷ saldo anual do titular (arrecadação − repasse − custeio do BI) para calibrar o déficit dos passos 5 e 6 e, junto com a P(fim) do 05c, estimar o sinistro da pergunta 9. Uma conta rápida desta sessão somou o custeio repetido por atribuição do 2025-2 e deu saldos negativos demais; ela foi descartada, e os números citados são os de 18/10.

## 2026-10-28 — Fase A: revisão do notebook 07 e notebook 09 (conclusões e lacunas)
- **Pedido:** concluir a mineração (07 e 09) e executar a Etapa 2, em modo autônomo, com as decisões registradas aqui à medida que são tomadas. Tudo numa cópia do banco (`RADAR_BANCO` no scratchpad); o banco real não foi aberto (só o `sha256sum` e a cópia de bytes).
- **Checagem 1 dos 10 números (início):** banco real com o SHA-256 da linha de base (`3e055af4…`, 23/10 15:55); na cópia, os 10 números iguais aos do `ESTADO_ATUAL.md` e as 25 tabelas do gold com hash de conteúdo registrado. A linha de base `C:\radar_arquivo\baseline_2026-10-20\linha_de_base.json` não existe neste WSL; a referência foi o SHA-256 do banco (o mesmo das sessões anteriores) e a tabela do `ESTADO_ATUAL.md`.
- **Estado encontrado:** o 07 já estava feito e commitado (`f2986e5`); o 09 não existia. O `docs/plano_projeto.md` foi alterado por outra pessoa durante a sessão (01:21; seção da Etapa 3 reescrita): mantido como está.
- **Revisão do 07 (cientista de dados):** rodado do zero num kernel limpo (390 s): saídas de todas as células iguais às commitadas. Os 5 PNGs: título, eixos com unidade e fonte com data; legíveis. Um dos 5 PNGs saiu diferente só no antisserrilhado (no máximo 5/255 por pixel), e os 5 foram restaurados da cópia do commit. Os números do texto conferem com as saídas. Erro achado: o diário de 27/10 dizia que a `gold.analise_previsao` tinha 99 linhas (19 + 80); a saída do notebook mostra 107 (19 + 88 = 11 medidas × 2 anos × 2 variantes × 2 cenários). Corrigido acima.
- **Código novo para o 09 e para a Etapa 2:**
  - `src/analise/tabelas.py`: uma função por tabela `gold.analise_*`, que repete, na mesma ordem e com a mesma semente, as células dos notebooks 03, 04, 06, 07 e 08. **Conferência:** os 5 notebooks rodados de novo numa cópia, com uma célula no fim que salva a tabela desenhada; as 6 tabelas do módulo são **idênticas** às dos notebooks (`assert_frame_equal` exato), salvo a `analise_clt_modelo` (diferença de 1,4e-14 na previsão da floresta, ver a decisão abaixo).
  - `src/analise/conclusoes.py`: os números dos achados (10 números nos três níveis, concentração, perfil dos grupos com o passivo, erro do CLT por região, receita líquida, saltos por semestre) e `carregar` (lê as `gold.analise_*` do banco ou as calcula pelas funções do pipeline).
  - `src/analise/grupos.py`: `nomes_grupos` (os nomes do notebook 04 passam para `config/analise.yaml`, `grupos.nomes`, com as conferências do perfil que estavam no notebook).
- **Notebook 09** (`notebooks/09_conclusoes_lacunas.ipynb`, 5 seções): os 10 números; **10 achados**, cada um com pergunta, cálculo, número, gráfico, frase para a apresentação e limitação; **tabela de lacunas** (8 linhas: patrimônio do titular, taxa, adesão, P(fim da delegação), sinistros/pergunta 9, 2026-1 completo, saltos, CLT em outros estados), com fonte nova, se é pública e gratuita, se existe para todos os estados e quanto muda a análise; **recomendação para o painel** (achado × gráfico × página). 10 PNGs `09_*`. Rodado duas vezes do zero numa cópia sem as tabelas `analise_*` (cálculo completo, ≈ 5,5 min): saídas iguais e PNGs iguais byte a byte. Números principais: prêmio R$ 368,7 mil = 7,7% do teto; P5–P95 R$ 206,1–736,2 mil (5,2 vezes mais estreita que os cantos oficiais); taxa R$ 184–645 mil e adesão R$ 184–516 mil no tornado; os 10% maiores têm 53,5% do passivo das obrigadas (Gini 0,63); grupo 6 com 67,4% do passivo das obrigadas e 54,6% do déficit; RI 84,1% obrigadas, média 45,1%; receita líquida −20,3% no universo e −8,5% no prêmio; universo 1.147/1.204 (limite fixo) em 2026/2027, prêmio R$ 366–369 mil; saltos 5,1% (2025-2) e 10,3% (2026-1) do total; CLT: 7 de 13 regiões fora de ±10%, MG −2,5%.
- **Revisão do 09:** gráficos conferidos um a um; corrigidos o título do achado 10 (eu tinha escrito "erro de até ±10% na maioria das regiões", mas 7 de 13 passam de 10%; agora o título é calculado), rótulos com casas demais (R$ 736,19 mil), eixo x sobreposto e legenda sobre uma barra no tornado, texto sobre o título na concentração, legenda sobre a barra de 10+ CLT e rótulos negativos de 2023 colidindo com o eixo nos saltos (a série começa em 2024). Os números do texto foram escritos depois da execução e conferidos contra as saídas.
- **Dados pessoais (busca ativa):** os 3.840 nomes de pessoa do cadastro do CNJ (`publico.nomes_do_cadastro`) e o padrão de CPF procurados em todos os notebooks (código, texto e saídas), no código novo e nos logs da sessão: nenhum achado. Os PNGs só têm rótulos escritos pelo código (grupos, regiões, atribuições, CNS de serventia no 07).
- **Decisões:**
  - *Módulo de tabelas compartilhado pelo 09 e pelo pipeline.* Alternativas: o 09 ler PNGs ou números dos outros notebooks (não recalcula, não confere com o banco), ou ler só do banco (as tabelas só existem depois da Etapa 2). Base: as 6 tabelas do módulo são iguais às dos notebooks. Impacto: o 09 roda sozinho, e o pipeline grava exatamente o que os notebooks desenharam.
  - *Previsão da floresta sem paralelo* (`regressao.prever_floresta`: ajuste com `n_jobs=-1`, previsão com `n_jobs=None`). Alternativas: arredondar a coluna; aceitar a variação. Base: a mesma função, chamada duas vezes, dava previsões diferentes na 15ª casa (1,4e-14), o que muda o hash da `gold.analise_clt_modelo` a cada carga. Impacto: resultado igual bit a bit; o notebook 06 rodado de novo deu as mesmas saídas e os mesmos PNGs.
  - *Nomes dos grupos na config, com conferência do perfil e "grupo N" se o perfil mudar.* Alternativa: parar o pipeline (uma carga nova travaria por causa de um rótulo). Impacto: só o rótulo.
  - *09 lê do banco quando as tabelas existem.* A primeira linha da saída diz a origem; a versão commitada é a calculada (o banco oficial ainda não tem as tabelas).
  - *Achado 5 também em passivo (dado)*, além do déficit (suposição): atende parte da M10.
- **Suposições:** nenhuma premissa numérica nova. Os nomes dos grupos (`config/analise.yaml`, `grupos.nomes`) têm fonte no notebook 04. Citados sem recalcular, com a fonte: "−11 obrigadas" (notebook 01) e "+22% do 2026-1 limpo sobre o 2025-1" (notebook 07).
- **Portão da Fase A:** suíte padrão 234 passed, 2 skipped, 84 deselected (com os 6 testes novos de `tests/test_analise_tabelas.py`); checagem 2 dos 10 números igual à 1 (25/25 hashes do gold iguais; banco real com o mesmo SHA-256). Ruff: 3 avisos F401 em arquivos que não foram mexidos (notebooks 02 e 03, `scripts/arquivo/`), anteriores a esta sessão.

## 2026-10-28 — Fase B: Etapa 2 (pipeline com as tabelas `gold.analise_*`)
- **O que foi feito** (os 5 passos da Etapa 2 do `plano_projeto.md`):
  1. **Cálculo em `src/analise/` com teste:** `tabelas.py` (uma função por tabela; conferido igual aos notebooks na Fase A), `conclusoes.py`, `grupos.nomes_grupos`; testes em `tests/test_analise_tabelas.py` (7 sintéticos e 1 `dados_reais`).
  2. **Gerar as tabelas:** `pipeline.etapa_analise`, chamada depois de `etapa_gold` nas etapas `all`, `gold` e `--a-partir-de silver`; grava com o `gold._gravar` (respeita o `exportar_parquet` da carga).
  3. **Pipeline do zero numa cópia:** `pipeline.main("gold_de_parquet", banco=<scratchpad>, exportar_parquet=False)` (≈ 6 min). A primeira tentativa parou ao gravar a `analise_tornado` (tipo misto; `erros_ia.md`) e a carga atômica não deixou nada pela metade; depois da correção: **25 de 25 tabelas antigas com o mesmo hash de conteúdo da checagem 1**, as 6 `analise_*` **iguais** às conferidas contra os notebooks, os 10 números iguais. `data/silver` e `data/gold` intactos (listagem com data e tamanho igual antes e depois). O notebook 09 rodado sobre esse banco (lendo as tabelas do pipeline) deu as mesmas saídas e PNGs da versão calculada na hora; só muda a linha que diz de onde as tabelas vieram.
  4. **`gerar_publico.py` e manifesto:** o script ganhou `--banco` e `--destino` (para conferir numa cópia). Com as 4 tabelas agregadas acrescentadas só na memória, a geração num diretório do scratchpad passou no auditor (989 células, 0 vazamentos), nos contratos de LGPD (3.213 CNS e 3.840 nomes procurados; nenhum) e no limite de tamanho (29 arquivos, 0,63 MB). 24 das 25 tabelas públicas com o mesmo conteúdo do manifesto versionado; a `qualidade.reconciliacoes` difere em 2,8e-15 numa correlação (ver as decisões). O `data/publico/` e o `config/publico.yaml` não mudaram.
  5. **Documentos:** `dicionario_dados.md` (seção nova das `analise_*`), `SPEC.md` §3, `ESTADO_ATUAL.md`, `plano_projeto.md` (status), `plano_mineracao.md` (09 e parte C), `decisoes.md` (D-043).
- **Decisões** (detalhes na D-043):
  - *"Do zero" = a partir do silver em Parquet* (D-029), num banco novo. Alternativas: a partir do bronze (regravaria `data/silver`, que é dado da carga, e os originais grandes do bronze não estão neste WSL); só `gold` sobre uma cópia (não é "do zero"). Base: é a prova "recalcular dá o mesmo" já usada em 19 e 20/10. Impacto: nenhum arquivo de `data/` tocado.
  - *Conjunto público: não regerar agora.* Alternativas: regerar `data/publico/` da cópia (o manifesto carimbaria "carga 2026-10-28", sem carga oficial nova); acrescentar as tabelas ao `config/publico.yaml` sem regerar (quebra `test_publico::test_manifesto_e_arquivos_batem`, que confere config × manifesto; o teste não foi desativado: a mudança foi desfeita). Base: o manifesto deve descrever o banco oficial; a carga oficial só roda com pedido do autor. Impacto: as tabelas novas ficam no gold da equipe até a próxima carga oficial.
  - *Só as 4 tabelas agregadas vão ao público*; `analise_grupos` e `analise_clt_modelo` têm CNS (o `config/publico.yaml` proíbe a coluna `cns`), e a D-038 ainda não chegou ao `gerar_publico.py`.
  - *A `sensibilidade_premissas` fica como está*, apesar da D-042 (proposta): mudá-la quebraria o "25 de 25 iguais" do Portão 2, e o plano vale em conflito.
  - *A diferença de 2,8e-15 na `qualidade.reconciliacoes` não foi corrigida:* vem do código de qualidade que já existia (`np.log(...).corr(...)` depende da ordem das linhas, e o silver lido do Parquet chega em outra ordem); não toca no gold nem nos números; arredondar mudaria o hash de uma tabela pública oficial. Fica como questão para o autor.
- **Suposições:** nenhuma nova.
- **Revisão de cientista de dados dos entregáveis:** conteúdo = os passos do plano (o 4 em parte, pelo motivo acima); números conferidos (10 números, 25 hashes, 6 tabelas); sem gráfico novo nesta fase; texto dos documentos escrito para quem não conhece o projeto; reprodutível (pipeline do zero + 09 sobre o banco do pipeline); dados pessoais: as travas do `gerar_publico.py` na cópia, além da busca da Fase A.
- **Testes:** suíte padrão 235 passed, 2 skipped, 84 deselected; ruff sem erro no código mudado (os 3 F401 antigos continuam, em arquivos não tocados). `dados_reais` de `test_pipeline.py`, `test_analise_tabelas.py` e `test_analise_previsao.py` (recargas numa cópia, 22 min): 4 passed, 1 failed. A falha é `test_a_partir_do_silver_parquet_reproduz_o_conjunto_publico`, pela `qualidade.reconciliacoes` (2,8e-15); **o mesmo teste falha no código do commit `7122a28`** (exportado com `git archive` para o scratchpad e rodado com o mesmo silver), então não vem desta sessão. O teste não foi alterado nem desativado. Passou o teste de carga reprodutível (`gold` duas vezes numa cópia, mesmo hash de todas as tabelas públicas do gold, inclusive as `analise_*`).
- **Checagem 3 dos 10 números (fim):** banco real com o mesmo SHA-256 e a mesma data (23/10 15:55); na cópia, os 10 números e os 25 hashes iguais aos da checagem 1; no banco do pipeline do zero, idem. `data/silver`, `data/gold` e `data/publico` intactos.
- **Próximo passo:** o autor decide a D-043 e pede a carga oficial; depois, a Etapa 3 (painel), começando pelo inventário de achados (seção 4 do notebook 09).

## 2026-10-28 — Decisões da Etapa 2 (D-044)
- **Pedido:** tomar as quatro decisões recomendadas no fim da Fase B (aprovar a D-043 e pedir a carga; linhas da D-042 numa tabela `analise_*` nova; arredondar a `qualidade.reconciliacoes`; no público, só o perfil agregado dos grupos), explicar por que um teste com dados reais falhava e entregar um relatório da sessão em Markdown.
- **Carga oficial não rodada.** O `CLAUDE.md` permite a carga no `data/radar.duckdb` real só com pedido explícito **do autor** na mensagem atual, e o pedido desta sessão não incluía a carga. Por isso não rodaram a carga, a regeração do `data/publico/` nem a linha de base nova. Tudo ficou pronto e conferido numa cópia; os comandos estão no `ESTADO_ATUAL.md`.
- **O que foi feito:**
  1. `src/quality/reconciliacao.py` (`_linha`): `valor_a`, `valor_b` e `indicador` arredondados a 10 casas; o status continua com o valor sem arredondar. Causa medida: a consulta por município não tem ordem fixa, e a correlação em log sai diferente no 16º dígito conforme a ordem das linhas (20 ordens sorteadas: 8 valores distintos, até 1,0e-15 de diferença). Alternativa: `ORDER BY` na consulta (resolveria a ordem, mas não diferenças de plataforma; o arredondamento cobre as duas).
  2. `src/analise/tabelas.py`: `sensibilidade_metodo` (gold.analise_sensibilidade_metodo, 5 linhas: base, receita líquida com a faixa da base, T5, T6 e a reserva no estado inteiro copiada da `sensibilidade_premissas`) e `grupos_perfil` (gold.analise_grupos_perfil, 6 linhas, sem CNS). `construir` passa a dar 8 tabelas. Valores iguais aos do notebook 08: receita líquida com universo 893,6 (−20,3%) e prêmio R$ 337,4 mil (−8,5%); T5 +0,6% no passivo de todas; T6 −1,6%; estado inteiro +5,9%. Os grupos têm de 91 a 688 serventias.
  3. `config/publico.yaml`: lista nova `tabelas_da_proxima_carga` com as 6 tabelas agregadas. Fora de `tabelas` porque o `test_publico` exige manifesto = config (o teste não foi mudado).
  4. Testes: 2 sintéticos (`grupos_perfil`; arredondamento da reconciliação) e 1 `dados_reais` (`sensibilidade_metodo` repete o notebook 08).
  5. Docs: D-044 nova e status da D-043 (`decisoes.md`), `dicionario_dados.md` (2 tabelas novas, 33 no gold; nota do arredondamento), `SPEC.md` §3, `ESTADO_ATUAL.md`; relatório da sessão em `docs/historico/sessao_2026-10-28_mineracao_e_etapa2.md`.
- **Pipeline do zero numa cópia** (`gold_de_parquet`, sem exportar Parquet): os 10 números iguais; 25 de 25 tabelas antigas com o mesmo hash da checagem 1; as 6 da D-043 com o mesmo hash da Fase B; as 2 novas gravadas (6 e 5 linhas); `qualidade.reconciliacoes` igual à do banco real arredondada, com os mesmos status. O `data/` não mudou (md5 dos 197 arquivos) e o banco real manteve o SHA-256 `3e055af4…`.
- **Conjunto público numa pasta do scratchpad** (com as 6 tabelas da próxima carga): auditor 989 células, 0 vazamentos; busca de 3.213 CNS e 3.840 nomes do cadastro sem achado; contratos de LGPD ok; 31 arquivos, 0,63 MB. O `data/publico/` não mudou.
- **Suposições:** nenhuma nova.
- **Testes:** suíte padrão 237 passed, 2 skipped, 85 deselected; ruff sem erro no código mudado. `dados_reais` (`test_pipeline.py`, `test_analise_tabelas.py`, `test_analise_previsao.py`, numa cópia; 23 min): 5 passed, 1 failed, `test_a_partir_do_silver_parquet_reproduz_o_conjunto_publico`, ainda só na `qualidade.reconciliacoes`. Esperado: o lado recalculado já sai arredondado e o manifesto do `data/publico/` ainda não. Passa depois da regeração do público na carga oficial. O teste não foi mudado.
- **Checagem final:** banco real com o SHA-256 `3e055af4…` (o mesmo do início); `data/` e `data/publico/` sem mudança.
- **Próximo passo:** o autor pede a carga oficial (passos no `ESTADO_ATUAL.md`); depois, a Etapa 3 (painel).

## 2026-10-28 — Carga oficial 2026-10-28 (Etapa 2)
- **Pedido** (autor): apagar o ramo `design-painel` (criado minutos antes, sem commit próprio), voltar ao `notebooks-07-09` e rodar a carga oficial.
- **O que foi feito:**
  1. Ramo `design-painel` apagado (`git branch -d`; estava em `f50c0f8`, o mesmo commit do `notebooks-07-09`).
  2. Cópia de segurança em `~/radar_arquivo/antes_carga_2026-10-28/` (banco `3e055af4…`, `carga_atual.json` e o `data/gold` antigo) e linha de base de antes em `~/radar_arquivo/baseline_2026-10-28_antes/`.
  3. `uv run pipeline.py --a-partir-de silver` no banco real, sem erro (log em `~/radar_arquivo/carga_2026-10-28.log`). Banco novo: SHA-256 `4941cffa…`. Os 10 números iguais; 25 de 25 tabelas antigas com o mesmo hash de conteúdo; as 33 do gold iguais às da carga na cópia.
  4. `config/publico.yaml`: as 6 tabelas agregadas passaram para `tabelas`, e a lista `tabelas_da_proxima_carga` saiu. `scripts/gerar_publico.py`: 31 arquivos, 0,63 MB, auditor com 0 vazamentos, LGPD ok. Contra o manifesto anterior, só a `qualidade.reconciliacoes` mudou de conteúdo (arredondamento da D-044); entraram as 6 tabelas novas.
  5. Linha de base nova em `~/radar_arquivo/baseline_2026-10-28/` (211 arquivos em `data/`, 33 tabelas do gold).
- **Testes depois da carga:** suíte padrão 237 passed. Todos os `dados_reais` (31 min): 79 passed, 3 skipped, 1 failed. O teste do silver em Parquet (`test_a_partir_do_silver_parquet_reproduz_o_conjunto_publico`), que falhava desde antes da sessão, **voltou a passar**. A falha nova foi em `test_saida_utf8.py::test_pipeline_com_saida_redirecionada`: a `analise_sensibilidade_metodo` lia o CSV do BI no bronze, e o pipeline a partir do silver parava sem ele (erro da IA, `erros_ia.md`). Corrigido: sem o CSV, a linha da receita líquida sai com aviso. Com o CSV, o resultado é idêntico ao do banco oficial (mesmo hash), então a carga não precisou ser refeita. Depois da correção: o teste passou (6,7 min), mais o teste novo `test_sensibilidade_metodo_sem_o_bi_nao_para` e a suíte padrão (237 passed).
- **Não feito:** nenhuma Release nova; o `data/carga_atual.json` ainda descreve o pacote de 19/10.

## 2026-10-28 — Melhorias de confiança M1 a M10 e correção dos pontos da validação (em andamento)
- **Pedido:** fazer as melhorias de confiança, ver se falta algo do `plano_mineracao.md`, corrigir os pontos da validação de 27/10, atualizar os notebooks e o 09 e, se precisar, rodar com a carga toda.
- **Plano adotado:** um notebook novo, **10 (melhorias de confiança)**, com uma seção por melhoria, no formato da seção 3 do `plano_mineracao.md`. O cálculo fica em `src/analise/melhorias.py` (com teste) e as tabelas em `src/analise/tabelas.py` (`melhorias`, `previsao_atualizada`). Os notebooks 04, 05c, 07 e 08 ganham só uma nota apontando para o 10, sem mudar as saídas. O 09 é refeito com os resultados. Alternativa descartada: reescrever o 07 com o 2026-1 completo. Isso exigiria trocar o snapshot oficial das arrecadações, e com isso mudariam as saídas de 01, 02, 05 e 07. Fica como recomendação para a próxima coleta oficial.
- **Coleta nova (M3 a, M6 c, M9),** gratuita, pela API pública do Justiça Aberta, no bronze em `data/bronze/cnj_justica_aberta/2026-10-28/`: cadastro de MG (3.213 registros; 2.517 ativas) e arrecadações das ativas. O `config/escopo.yaml` não mudou, e o pipeline continua com os snapshots de 17 e 18/10. A data da coleta está em `config/analise.yaml`, `melhorias.coleta_conferencia`.
- **Decisões e resultados até aqui:**
  - *M1 (capacidade de pagar):* saldo anual = arrecadação − repasse − custeio do BI de 2025. O custeio repetido por atribuição no 2025-2 conta uma vez (8.183 períodos); custeio diferente entre as linhas é somado (6). Com um semestre só, o valor é anualizado (94 obrigadas). Horizonte de 12 meses de saldo (`fonte: suposição`; sensibilidade 6 e 24). Resultado: o déficit total quase não muda (R$ 34,5 mi contra R$ 36,9 mi), mas a composição sim. A chance de déficit pela M1 é de 6,9% na Classe 2 e 9,6% na Classe 3 (o modelo supõe 50% e 30%), e a parte descoberta é maior (68% e 91%). As faixas diferem do F6 de 18/10 (810/205/35/50/30 contra 708/260/41/47/74) por convenção: a anualização de um semestre e o custeio contado uma vez. 64% do déficit da M1 vem das 50 obrigadas com saldo ≤ 0, provável erro de declaração do custeio.
  - *M2 (pergunta 9):* sinistralidade = P(fim) × q ÷ taxa. Com q pela M1 (12,3%), fica entre 12% e 46% (base 25%), e o resultado técnico é positivo. Sem a M1 (q = 1), vai de 100% a 375%. O resultado zera com q = 37,5%.
  - *M3:* (b) no teste desde 2012, o SARIMA e o Holt-Winters erram menos que a tendência (10,5% a 10,7% contra 14,1%). Na janela recente, a tendência continua melhor (7,4%), e a regra do plano (escolher pela janela recente) mantém a tendência. A média tendência + SARIMA fica no meio. (c) A faixa da arrecadação cobre 86% (honesta, 28 casos); a da contagem acima do limite no 07, só 27%. A faixa calibrada pelos erros passados cobre 60% (5 casos). (a) Com o 2026-1 completo: ver o fim desta entrada.
  - *M4:* o desvio condicionado não melhora (erro médio de 33,9 contra 33,5 subidas). Com o fator real de MG, o erro cai para 18,5: o erro das subidas vem da previsão de MG (M3), não da dispersão. A M4 foi rejeitada, com o motivo registrado no notebook.
  - *M5:* o passivo sobe 14,6% em 2026 e 28,5% em 2027 (INPC de 4,29% em 12 meses até 09/2026, repetido em 2027: suposição). O prêmio projetado passa de ≈ R$ 368 mil para ≈ R$ 423 mil e ≈ R$ 472 mil.
  - *M7:* prêmio por cenário do STF (mantém; parcial = metade; suspende = zero). Andamento conferido no portal do STF em 28/10, só leitura: duas decisões monocráticas "Deferido" em 22/10, com certidão incluindo dois sindicatos no registro do processo (leitura: admissão de terceiros interessados, não liminar); concluso ao relator em 27/10. O rito do art. 12 continua.
  - *M8:* (a) a SES **não** publica a importância segurada. Conferido no índice do `BaseCompleta.zip` (40 tabelas) e no dicionário `Ses_campos.csv`, baixado por intervalo de bytes, sem baixar os 577 MB. A taxa média não sai da SES. (b) Grade taxa × adesão: de R$ 92 mil a R$ 903 mil.
  - *M9:* 5 vacâncias novas no cadastro em 11 dias; 3 com decisão de semanas ou anos antes (o cadastro é atualizado com atraso); 2 dentro da janela, e as duas viraram inativas (Classe 1). Duas coletas próximas medem o atraso de registro, não a taxa.
  - *M10:* pela M1, o grupo "providas grandes" tem 85% do déficit (55% no modelo; 68% do passivo).
- **Fechamento (continuação da mesma entrada):**
  - *M3 a (coleta completa, 2.517 de 2.517 ativas; 2 falhas de rede refeitas):* o 2026-1 quase não mudou (2.425 serventias com valor, eram 2.414); 2025 com 14 de 5.034 pares diferentes e a mesma soma. O 2026-1 real ficou 18,3% acima do central do 07 e acima do P90. Com o treino até ele, MG cresce +16,6% em 2026 (07: +7,3%) e +23,3% em 2027.
  - *M6 c:* nenhum valor das 4 serventias mudou: os saltos continuam declarados.
  - *Projeção atualizada (`analise_previsao_atualizada`):* limite fixo, 1.188 obrigadas e ≈ R$ 422 mil em 2026 (07: 1.147 e ≈ R$ 368 mil); 1.210 e ≈ R$ 472 mil em 2027. Subidas de 2026: 115, entre as 78 do 07 e as 145 do 05b.
  - *Pipeline do zero numa cópia:* os 10 números iguais; as 33 tabelas anteriores com o mesmo hash; 6 novas (39 no gold); `data/` intacto (md5, fora a pasta nova da coleta). Conjunto público numa pasta temporária, com as 6 novas: 37 arquivos, 0,65 MB, auditor com 0 vazamentos, LGPD ok.
  - *Notebooks:* 10 novo e 09 refeito, rodados duas vezes do zero na cópia, com as mesmas saídas e os mesmos PNGs (3 `10_*`; 11 `09_*`, um novo: `09_pergunta_9`). Notas no fim de 04, 05c, 07 e 08, sem mudar as saídas. Revisão dos gráficos: no `09_pergunta_9`, os rótulos do eixo x estavam errados (o índice da tabela se repetia) e o eixo log mostrava "3×10²"; corrigidos. Duas notas de rodapé longas foram quebradas em duas linhas.
  - *Busca de dado pessoal:* 1.986 nomes de responsáveis do cadastro e o padrão de CPF, nos notebooks 09 e 10, no código novo e nos docs: nada. O nome do relator da ADI não foi escrito. Ele já aparecia numa linha antiga do diário (18/10), deixada como estava e levada ao autor.
  - *Premissas novas:* `config/analise.yaml`, `melhorias` (D-045).
  - *Testes:* suíte padrão 245 passed, 2 skipped; ruff sem erro. Todos os `dados_reais` numa cópia (39 min): 81 passed, 3 skipped, 0 failed. O banco oficial ainda não tem as 6 tabelas da D-045: elas esperam a próxima carga oficial (pedido do autor).

## 2026-10-28 — D-046: premissas v3, regra do salto, dados só até 18/10 e carga oficial (tarde)
- **Pedidos** (autor): decidir os três pontos seguindo a recomendação da IA; carga oficial com as tabelas novas; trocar o nome do relator da ADI nos documentos. Depois, no meio do trabalho: "não quero nada do dia 28/10, só os dados até dia 17/10".
- **Nome do relator:** tirado de `docs/diario.md` (linha de 18/10), `docs/SPEC.md` e `app/Inicio.py` (texto da página inicial). Nenhuma outra ocorrência no repositório.
- **Coleta de 28/10:** a IA começou a coletar os colaboradores de MG (que faltavam na coleta da manhã) e parou a pedido, com 1.219 de 2.517. Tudo de 28/10 (cadastro, arrecadações e a coleta parcial) foi **movido** para `~/radar_arquivo/coleta_2026-10-28_retirada/` e, depois, **apagado** a pedido ("pode inclusive excluir a coleta"; 13 MB). O `config/escopo.yaml` ficou como estava (17 e 18/10). Também a pedido, **nenhuma Release nova**: o pacote da equipe chegou a ser gerado em `~/radar_pacotes/equipe/` (pasta de saída do empacotador), mas não foi publicado. Saíram a `analise_previsao_atualizada`, a `melhorias.coleta_conferencia`, as `serventias_conferir` e as partes M3 a, M6 c e M9 do notebook 10.
- **Regra do salto:** valor declarado mantido; aviso novo `contratos.saltos_arrecadacao` (SQL, a mesma conta de `estatistica.saltos`: 45 semestres de 2025 em 43 serventias, R$ 168,9 mi, igual ao notebook 01); linha `sem_saltos` na `analise_sensibilidade_metodo` (−11,3 obrigadas, −1,0%; prêmio −0,8% com a v3).
- **Conferência das 50 obrigadas com saldo ≤ 0:** BI × API dentro de 12% em todas; repasse e custeio medianos de 55% e 56% da arrecadação (37% e 24% nas outras obrigadas); saldo mediano de −8% da arrecadação; todas providas, 30 da Classe 2 e 20 da Classe 3, 7 com um semestre só no BI. Dado plausível.
- **Premissas v3:** pela fórmula do motor (déficit = Σ prob × pct × passivo), a chance pela contagem (6,9% e 9,6%) exigiria parte descoberta acima de 100% para dar o déficit da M1. A chance foi ponderada pelo passivo (10,8% e 18,6%), com a parte descoberta da M1 (68,3% e 90,7%); mínimo e máximo pelos horizontes de 24 e 6 meses (a parte descoberta, do menor ao maior entre os três; o sorteio triangular não aceita mínimo igual ao máximo). `src/estado.py` aponta para a v3.
- **Cópia antes da carga** (`--a-partir-de silver`, gold e Parquet só no scratchpad; `data/` intacto por md5): números 1 a 5 e 10 iguais; 6 a 9 novos; 17 tabelas iguais, 16 com conteúdo novo (todas ligadas ao déficit), 5 novas; conjunto público de teste com 36 arquivos e 0 vazamentos.
- **Carga oficial** (pedido do autor): backup em `~/radar_arquivo/antes_carga_2026-10-28_d046/` (banco `4941cffa…`, silver, gold, público); `uv run pipeline.py --a-partir-de silver` sem erro (log em `~/radar_arquivo/carga_2026-10-28_d046.log`); banco novo `f318a92b…`, idêntico à cópia (os 10 números e as 38 tabelas); v3 registrada em `estado.premissas_versoes`. `config/publico.yaml` com as 5 tabelas; `scripts/gerar_publico.py`: 36 arquivos, 0,64 MB, auditor sem vazamento. Linha de base em `~/radar_arquivo/baseline_2026-10-28_d046/`.
- **Números novos:** com déficit ≈ 148 (era ≈ 486); déficit R$ 34,1 mi (36,9); IS R$ 17,1 mi (18,4); prêmio R$ 341,1 mil (368,7). P5–P95 do prêmio R$ 215 a 687 mil; cantos R$ 51,7 mil a R$ 1,93 mi. Pergunta 9 com a M1: sinistralidade de 16% a 59%, resultado técnico de R$ 54 a 202 mil por ano. Leitura literal da receita: −20,3% no universo, mas só −2,7% no prêmio.
- **Painel:** o simulador arredondava a chance e a parte descoberta para porcentagem inteira (erro da IA, `erros_ia.md`); agora usa uma casa decimal. `README.md` (roteiro) e `eval/gabarito_chat.csv` (perguntas 5, 6, 9, 10 e 12) com os valores novos.
- **Notebooks:** 10 refeito sem as partes de 28/10, rodado na cópia de antes da D-046 (premissas v2 fixadas no código), com as mesmas saídas e PNGs nas seções que ficaram (só o rótulo "modelo (premissas vigentes)" mudou). 09 refeito no banco novo, duas vezes, com as mesmas saídas e PNGs (8 dos 10 PNGs `09_*` mudaram); o achado 8 voltou à projeção do 07, com o passivo de cada ano (M5) ao lado. Nota da D-046 no fim de 01 a 08; as notas do 05c e do 07 perderam a coleta de 28/10.
- **Testes:** suíte padrão 246 passed, 2 skipped (teste novo da checagem do salto). Todos os `dados_reais` (34 min): 77 passed, 3 skipped, **4 failed**, todos por valores da v2 fixados nos testes ou pela linha nova `sem_saltos`: P5–P95 do Monte Carlo (agora R$ 215,0 a 687,1 mil), prêmio da receita líquida (−2,7%, era −8,5%), lista de linhas da `analise_sensibilidade_metodo` e o tornado do T7 (feito com a v2: o teste passou a usar a semente v2 nessa parte, que confere o método). Testes atualizados (mais um: a linha `sem_saltos` dá −11,3 obrigadas, como o notebook 01); os 4 passaram (2 min).
- **D-048** (pedido: resolver as pendências do pipeline antes da Etapa 3; o autor pediu a D-038 no pipeline): branch `etapa-3-painel` criada e desfeita a pedido (idêntica à `notebooks-07-09`, apagada aqui e no GitHub). Fase 1 da D-038: `gold.serventia_publico` (2.525 linhas; soma = `fato_mercado_uf`, contrato novo), `analise_grupos` e `analise_clt_modelo` no público, CNS permitido só nas tabelas `por_serventia`, chat com `consultar_serventia`; aviso `classe_api_x_bi` (10 serventias, 6 iriam para a Classe 1, entre elas a 035030); nenhum dos 4.441 nomes do cadastro no silver. Cópia conferida (10 números e 38 tabelas iguais, +1); carga oficial igual à cópia (banco `c0919011…`, backup em `~/radar_arquivo/antes_carga_2026-10-28_d048/`); `data/publico/` com 39 tabelas, 0,89 MB, auditor sem vazamento; linha de base em `~/radar_arquivo/baseline_2026-10-28_d048/`. Testes: suíte padrão 247 passed (2 novos: CNS só nas tabelas por serventia; `consultar_serventia`); `dados_reais`: 80 passed, 3 skipped e 1 falha (`test_app.py::test_lgpd_tabelas_publicas_do_gold_e_da_qualidade`, que ainda cobrava o limiar de 3 serventias na `serventia_publico`; erro da IA, ver `erros_ia.md`); com a tabela na lista de exceções do teste, passou. Gabarito do chat (17 e 18) e README atualizados.
- **D-047** (aprovada pelo autor): P(fim da delegação no ano) de 2% / 4% / 7,5% (notebook 05c, com a limitação do viés de sobrevivência); `analise_grupos` por serventia no gold e só o perfil agregado no público; subidas do 05b como faixa de 105 a 145 em 2026 (sem e com recalibração), rotulada "projeção". Nada recalculado.

## 2026-10-28 — Etapa 3: painel refeito (inventário, arquitetura, padrão visual, construção e revisão)
- **Pedido:** executar a Etapa 3 do `plano_projeto.md` em modo autônomo, com o design refeito, registrando cada decisão aqui; parar só se um dos 10 números mudasse.
- **Fase 1, inventário** (`docs/painel/inventario_achados.md`): 34 achados dos notebooks 01 a 10 e da Etapa 2, com origem, número, fonte, importância, lugar, formato e a função de `src/painel/`. Fora do painel: 3 (crescimento real e decomposição do passivo, importância baixa; a fase 2 da D-038, que exige carga oficial). Nenhum de importância alta ficou de fora.
- **Fase 2, arquitetura** (`docs/painel/arquitetura.md`): pergunta e três níveis de leitura por página; ordem Início → Mercado → Análises → Qualidade → Simulador → Chat.
  - *Decisão: Análises como página nova.* Alternativa: seções no fim do Mercado. Base: 11 achados para ela, 6 de importância alta, todos de MG inteiro (os filtros por área do Mercado não valem para a projeção nem para o Monte Carlo). Impacto: uma página a mais na navegação; o Mercado fica com "onde e quem".
  - *Decisão: sem filtro global.* O contexto fixo (carga, premissas, regra, nível, STF) vira uma faixa de selos no topo de cada página; filtros só no Mercado (os da D-026) e na aba Projeção (ano e leitura do limite). Alternativa: um seletor de cenário do STF global (descartada: o cenário muda só o prêmio e já aparece no Início e no Simulador).
- **Fase 3, diagnóstico e padrão** (`docs/painel/padrao_visual.md`): 53 capturas do painel antigo em `docs/qa/painel/antes/` (1280 e 1920 px). Problemas: sem manchete, 5 dos 10 números, faixa dos cantos como única incerteza (contra a D-042), cores sem significado, gráficos poucos e pequenos, ADI com data fixa no código.
  - *Decisão: direção sóbria e editorial* (fundo off-white, cartões brancos, uma cor de destaque, números grandes, manchete com o número). Alternativas: painel escuro de "fintech" (pior em projetor e com a paleta a validar duas vezes); manter o padrão do Streamlit com ajustes (não resolve hierarquia).
  - *Decisão: cores com significado fixo* — azul = observado/base, laranja = projeção, violeta = suposição/sensibilidade, cinza = comparação/extremos, vermelho só como alerta com ícone. Validadas para daltonismo com o script da skill de visualização (todas as checagens passaram; pior par ΔE 24,7).
  - *Decisão: fonte Inter (Google Fonts) pelo tema* (`.streamlit/config.toml`); sem internet, cai para a sans do sistema. *Sem biblioteca nova de interface* (streamlit-extras e streamlit-elements descartadas: ganho pequeno, risco de quebrar com a versão do Streamlit). *Sem modo escuro* nesta etapa.
- **Fase 4, construção:**
  - `src/painel/analises.py`: 22 funções no formato das ferramentas do chat (valor formatado, `conta`, `rotulo` da D-042, `fonte`, `data_referencia`, `carga`, `versao_premissas`, `citar`, mais `valores` e `tabela` crus); `artefatos.py` (lê tabelas gravadas na saída dos notebooks); `graficos.py` (template Plotly `radar` e 12 gráficos); `ui.py` e `estilo.css` (componentes e CSS único). As páginas só exibem o que essas funções devolvem; as ferramentas atuais do chat não mudaram.
  - *Decisão (D-049): limite fixo como leitura principal da projeção*, corrigido pelo IPCA como comparação sempre visível. A questão (c) do notebook 07 estava pendente do autor desde 27/10, sem decisão registrada; base: o limite fixo é a regra em vigor e a correção exige supor o índice. Impacto: −43 obrigadas em 2027 na outra leitura; o leitor troca a leitura num controle.
  - *Decisão (D-049): extremos da D-042 = cantos oficiais* (`gold.fato_mercado_uf`, mín. e máx.), como manda a D-042; os cantos do Monte Carlo (`analise_monte_carlo.canto_min/max`, passivo fixo na base) ficam numa nota. A tarefa dizia "extremos da `analise_monte_carlo`", mas a D-042 é explícita sobre os cantos oficiais; vai para "Questões".
  - *Decisão (D-049): 05b, lacunas do 09 e M5 do 10 lidos da saída gravada dos notebooks*, porque não estão em tabela e o modo demonstração não tem o silver para refazê-los. Alternativas: tabela nova no pipeline (exige carga oficial) ou números em `config/` (cópia à mão).
  - *Decisão: ADI 8015 em `config/painel.yaml`* com a conferência de 28/10/2026 (diário, M7); deve ser conferida de novo na véspera da demo.
  - *Decisão: Mercado com o mesmo conteúdo e os mesmos widgets* (chaves e rótulos preservados para os testes de LGPD e da auditoria); a tabela de mín./máx. do recorte passou a se chamar "extremos teóricos do recorte" (D-042). A fase 2 da D-038 não foi feita (exige carga oficial).
  - *Decisão: gráficos lado a lado só quando cabem.* Em 1366 px, dois gráficos em colunas cortavam os títulos; Mercado e Qualidade passaram a empilhar os gráficos novos em largura total.
  - O texto de "Déficit" nas limitações da Qualidade foi atualizado para a D-046 (dizia "suposições, D-016"); o caminho do `viabilidade.md` foi corrigido para `docs/historico/` (pendência antiga).
  - Arquivos das páginas renomeados para a nova ordem (`4_Simulador.py`, `5_Chat.py`, `2_Análises.py` nova); testes e `scripts/qa_painel.py` acompanham (1366 px entrou nas larguras das capturas).
- **Suposições:** nenhuma premissa numérica nova. A fonte Inter vem do Google Fonts (gratuito; sem internet, o navegador usa a sans do sistema).
- **Desempenho** (AppTest, banco completo numa cópia e modo demonstração): 1ª abertura de 0,8 a 1,5 s por página (Simulador, fora desta etapa: 4,2 s com o banco completo); com cache, 0,4 a 0,8 s.
- **Testes e auditoria:** a auditoria visual (`tests/test_auditoria_painel.py`) falhou em 34 casos na primeira rodada: procurava o ranking pela posição do gráfico e os KPIs em `st.metric`, que viraram HTML. Passou a achar o ranking pelo título ("15 maiores") e a ler os KPIs do HTML; a tabela dos grupos foi cortada a 7 colunas. Final: suíte padrão 259 passed, 2 skipped; `dados_reais` e `visual` de app, chat, painel e auditoria 63 passed; ruff sem erro nos arquivos da etapa (o único aviso do repositório está em `scripts/arquivo/`, intocado). Os testes do chat (`tests/test_chat.py`) passaram sem mudança nas ferramentas.
- **Fase 5, revisão por três leitores** (prints de `docs/qa/painel/depois/`, 95 capturas em 1280, 1366 e 1920 px; checagens de layout: 0 falhas):
  - *Cientista de dados:* a ordem da D-042 está em todo cartão (base → faixa provável → extremos) e as sensibilidades ficam abaixo; a nota de que o valor base fica abaixo da mediana dos sorteios está na Análises; projeções com selo laranja e P10–P90. Correção: o eixo da leitura literal tinha limites fixos no código (−30% a +5%); passou a ser calculado dos dados.
  - *Designer:* o último rótulo do eixo do tornado e o título do gráfico de escolhas de método eram cortados a 1366 px (margem direita maior; título curto com o rótulo D-042 e a frase no subtítulo). A tabela de lacunas cortava as três colunas (`st.dataframe` não quebra linha): virou `st.table`, com o cifrão escapado (o `st.table` lia "R$ … R$" como fórmula).
  - *Leigo:* a manchete do Início responde à pergunta em uma frase com o número; o glossário "Termos em uma linha" cobre CLT, déficit, IS, prêmio, faixa provável, projeção e sensibilidade. Sem correção.
  - Inventário: coluna **Revisão** marcada (24 achados conferidos na tela, 7 dentro de expansores conferidos pelos testes; 3 fora do painel).
- **Conferência final:** `data/radar.duckdb` intacto (SHA-256 `c0919011…`, igual ao do início); os 10 números iguais aos do `ESTADO_ATUAL` (teste `tests/test_painel.py`). Sem commit (pedido do autor).

## 2026-10-28 — D-050: dados do painel no git (`data/completo/`)
- **Pedido:** levar ao GitHub os dados que o painel da Etapa 3 usa e as dependências, para rodar de lá. O `data/publico/` (modo demonstração) já estava no git; faltava o modo completo. Escolha: gold completo + silver limpo (D-050).
- **Feito:** `scripts/exportar_completo.py` grava `data/completo/` (13 MB): silver sem as 6 colunas da RAIS da D-031 (contrato "sem dado pessoal": 0 problemas, 3.840 nomes procurados), as 39 tabelas do gold e o CSV do BI do CNJ em gzip; `--instalar` põe o silver e o CSV em `data/` conferindo o SHA-256. `tests/test_completo.py` (5 testes). README seção 1b, `CLAUDE.md` (exceção na seção Git).
- **Dependência achada no teste:** a primeira rodada do clone (só silver) gravou 36 tabelas: sem o CSV do BI, saem `analise_capacidade_calibracao`, `analise_capacidade_faixas`, `analise_sinistro` e a linha da receita líquida da `analise_sensibilidade_metodo` (páginas Análises: M1 e pergunta 9). O CSV entrou.
- **Conferência num clone** (só os arquivos do git, sem bronze, silver nem banco): `--instalar` + `pipeline.py --a-partir-de silver` em 7 min; 39 de 39 tabelas do gold com o mesmo conteúdo de `data/completo/gold` (a `execucao` só difere na hora); `dados_reais` de `test_app` e `test_painel` no clone: 18 passed. Suíte padrão aqui: 265 passed, 2 skipped. Banco real intacto (SHA-256 `c0919011…`).

## 2026-10-28 — Etapa 5: chat com o Gemini (nível gratuito), parte de código (D-060 a D-066)
- **Pedido:** chat com o Gemini no nível gratuito, para o link público e a demo; o Ollama sai. Respostas ao plano: meta de acerto de 85%; limite de 20 perguntas por sessão; `.env` lido com `python-dotenv`.
- **O que foi feito:**
  - `src/llm.py` reescrito para o Gemini: REST com `httpx`, chave no cabeçalho, reserva em caso de 429 ou erro, mensagens sem a chave;
  - `config/llm.yaml` com modelo, reserva, limite por sessão, perguntas prontas, meta e hash do gabarito, cada valor com fonte;
  - 5 ferramentas em `src/agent/ferramentas.py` sobre as funções de `src/painel/analises.py`, mais as consultas próprias do chat;
  - `src/agent/chat.py` com as versões (a), (b) e (c) e a resposta sem modelo;
  - página `app/pages/5_Chat.py`: aviso de dados pessoais, perguntas prontas, limite, cota;
  - normas em `data/normas/` (`scripts/exportar_normas.py`);
  - gabarito de 52 perguntas e `scripts/avaliar_chat.py`;
  - testes: `tests/test_chat.py` (22) e `tests/test_chat_cobertura.py` (5 na suíte padrão e 1 `dados_reais`);
  - a avaliação antiga do Ollama foi para `eval/historico/`.
- **Prompt do agente:** salvo em `config/prompts/agente_sistema.md` (versão 1). Troca dos nomes entre colchetes: `[ferramenta_numeros]` → `consultar_numeros`, `[ferramenta_mercado]` → `consultar_mercado`, `[ferramenta_analises]` → `consultar_analises`, `[ferramenta_qualidade]` → `consultar_qualidade`, `[ferramenta_decisoes]` → `consultar_decisoes`. O fim do prompt ganhou o bloco "Regras do projeto". Fora isso, o texto ficou como foi escrito. Os placeholders da linha "Fonte: [fonte] · referência: [data] · premissas: [versão]" ficaram, porque são instruções de formato para o modelo, não nomes de ferramenta.
- **Modelo (conferido na documentação do Google em 2026-10-28):** `gemini-3.8-flash` (estável, nível gratuito, chama ferramentas; raciocínio low, medium ou high) e a reserva `gemini-3.5-flash-lite` (nível gratuito). Os limites de uso do nível gratuito não estão na documentação: cada conta vê os seus no AI Studio. No nível gratuito, o conteúdo pode ser usado pelo Google; por isso a página tem o aviso.
- **Decisões:** D-060 (Gemini no lugar do Ollama; Ollama removido, não aposentado); D-061 (exceção ao "100% gratuito", também no `CLAUDE.md`); D-062 (5 ferramentas e teste de cobertura); D-063 (perguntas prontas e 20 por sessão); D-064 (normas versionadas sem assinatura); D-065 (gabarito congelado, meta de 85% e nenhum número inventado nas armadilhas); D-066 (prompt v1).
- **Conferências:**
  - as 30 consultas rodam sem erro no modo demonstração e, numa cópia do banco, no modo completo (`-m dados_reais`, 1 passed);
  - todo número esperado do gabarito sai de uma ferramenta;
  - `analises.py` sem mudança; banco real com o mesmo SHA-256 antes e depois;
  - a página abre sem chave (aviso e perguntas prontas), com um modelo falso, no limite da sessão e com a cota esgotada.
- **Suposições** (`fonte: suposição` no `config/llm.yaml`): temperatura 0, `timeout_s` 60, histórico de 6 mensagens, pausa de 15 s entre perguntas da avaliação e espera de 65 s depois de um 429.
- **Limitações:**
  - a IA não tem chave do Gemini, então **nenhuma rodada com a API real foi feita**. O formato da chamada e das ferramentas está testado contra um servidor simulado, não contra o Google;
  - a primeira rodada com a chave real é que confirma, por exemplo, se o esquema das ferramentas é aceito como está.
- **Próximo passo:** rodar `uv run python scripts/avaliar_chat.py --versoes c --limite 5` com a chave real, depois a avaliação inteira; se a meta não for cumprida, ajustar o prompt (nova versão) ou as ferramentas e registrar.
- **Testes rodados (2026-10-28, WSL):**
  - antes das mudanças: `uv run pytest` com 265 passed e 2 skipped;
  - depois: `uv run pytest` com **286 passed, 2 skipped**, sem chave e sem rede (a `GEMINI_API_KEY` vazia e a rede do `src/llm.py` trocada por uma que falha, em `tests/conftest.py`); `uv run pytest -m dados_reais tests/test_chat_cobertura.py` com 1 passed, numa cópia do banco;
  - a primeira rodada da suíte inteira teve 2 falhas: (1) `test_painel.py::test_ferramentas_do_chat_nao_mudaram`, a trava da Etapa 3 sobre as 6 ferramentas antigas, que agora são `PROPRIAS` (o teste foi ajustado para o nome novo e confere também que as 6 continuam alcançáveis); (2) `scripts/exportar_normas.py` sem `sys.stdout.reconfigure` (corrigido);
  - `ruff`: só o aviso antigo em `scripts/arquivo/`.
- **Para juntar com o painel:**
  - `tests/test_painel.py` (função `test_ferramentas_do_chat_nao_mudaram`) e `tests/apoio_painel.py` (variável do Ollama trocada pela `GEMINI_API_KEY` vazia; `git ls-files -z`) mudaram nesta branch: na hora de juntar, a versão da `etapa-5-chat` é a que vale nesses trechos;
  - `analises.py` e `comum.py` não mudaram;
  - o commit `ee9278a` ("fiz o começo do prompt mas não terminei") não tem nada do prompt do chat: é uma segunda rodada do visual (tema novo em `.streamlit/config.toml`, faixa do topo com o número principal em `comum.pagina`/`ui.cabecalho`, `ui.secao`, cores novas em `graficos.py` e `estilo.css`). Ficou na branch do painel. O que falta nele: o `docs/painel/padrao_visual.md` ainda traz as cores antigas (`#184f95`), só o Início usa `ui.secao` e as capturas de `docs/qa/painel/` são da primeira rodada.

## 2026-10-28 — Chat: primeiro uso com a chave real, demora do Gemini e prompt v2 (D-067, D-068)
- **O que aconteceu:** com a chave real, rodou o teste curto da avaliação. A pergunta 1 deu certo (7,2 s, ferramenta certa, 2.525 com fonte), o que confirma que o formato da chamada e das ferramentas é aceito pelo Google. Depois, no painel, uma pergunta sem dado devolveu "Não foi possível falar com o Gemini (ReadTimeout)".
- **Diagnóstico** (poucas chamadas, com a chave do `.env`, sem imprimir a chave):
  - a rede está boa: o host do Google respondeu em 0,4 s;
  - o `gemini-3.8-flash` não respondeu nem a um "oi" em 150 s; o `gemini-3.5-flash-lite` respondeu em 1,9 s. O problema era o principal travado no nível gratuito, não a pergunta;
  - depois, o principal passou a devolver erro e cota esgotada (429).
- **Feito:**
  - reserva também em caso de demora, com tempo-limite de 30 s e só a reserva por 10 minutos depois de uma falha (D-068);
  - prompt v2 (D-067): "Não possuo esse dado no momento." e nenhuma linha de fonte sem ferramenta.
- **Teste real depois:**
  - "inflação de 2027" (4,1 s) e "prêmio em 2030" (23,8 s) começam com "Não possuo esse dado no momento."; a segunda oferece 2027 rotulado como projeção;
  - "qntos cartorio tem em minas??": 2.525, com a fonte certa (12,1 s).
  - Observação para a avaliação: na resposta de 2030, a faixa P10–P90 da projeção foi chamada de "faixa provável", o nome que a D-042 reserva para o P5–P95.
- **Testes:** `uv run pytest` com 288 passed e 2 skipped, sem chave e sem rede.
- **Próximo passo:** trocar a chave (ver `docs/erros_ia.md`, mesmo dia) e rodar a avaliação completa com o prompt v2. Com o principal fora, a avaliação mede a reserva: o relatório diz o modelo de cada rodada só pelo `config/llm.yaml`, então vale anotar no diário qual modelo respondeu.

## 2026-10-28/29 — Chat: perguntas prontas em aba, frase sem dado, interface e velocidade (D-069)
- **Pedido** (modo autônomo): perguntas prontas como aba própria, resposta sem dado ("Não foi possível encontrar essa resposta nos dados do painel."), interface (9 problemas da captura) e velocidade (medir, corrigir, medir de novo).
- **Feito:**
  - **Abas** Chat e Perguntas prontas. As prontas são 16, em 5 temas, em expansores, com selos e a fonte numa linha pequena. A frase única de indisponível aparece na tela e o motivo vai para o log.
  - **Prompt v3** com a frase nova e "P10–P90 não é faixa provável"; o detector de "não sei" aceita a frase e variações. O gabarito e a meta não mudaram.
  - **Página nova:**
    - cabeçalho compacto e campo em destaque, com o CSS em `src/agent/chat.css`;
    - aviso de uma linha e contador só no modo demonstração;
    - 4 sugestões na conversa vazia;
    - expansor "Fontes e datas", com o modelo e a versão do prompt.
  - **Velocidade:**
    - primeira chamada sem streaming e as seguintes em streaming;
    - cliente HTTP único;
    - ferramentas com cache e em paralelo;
    - tempo-limite de 10 s no principal;
    - tabelas formatadas antes de irem ao modelo.
  - **Correções achadas no caminho:**
    - os extremos teóricos agora têm o nome certo para o modelo, e a consulta de mercado traz a faixa provável do painel;
    - a resposta interrompida por uma pergunta nova não se perde mais;
    - a "mágica" do Streamlit mostrava um objeto interno na tela.
  - **Ferramentas novas:** `scripts/medir_latencia_chat.py` (latência por etapa) e `scripts/prints_chat.py` (capturas em 1366 px e 390 px, nos dois modos, mais o contraste pelo axe).
- **Latência** (5 perguntas de fumaça, API real, quem respondeu foi sempre a reserva, porque o principal estava com a cota esgotada):

  | Medida | Antes | Depois | Meta |
  |---|---|---|---|
  | Primeiro texto (mediana) | 4,6 s | 2,7 s | 3 s |
  | Resposta completa (mediana) | 4,6 s | 3,0 s | 10 s |

  Na tela, as respostas levaram de 3,6 a 5,7 s antes e de 2,4 a 6,3 s depois. A primeira pergunta de um servidor novo pode levar mais 10 s, quando o principal está travado.
  
  O serviço oscila muito: no mesmo dia, a reserva respondeu a mesma chamada em 0,7 s e em 12 s. Por isso as metas só valem na mediana e dependem da hora.
- **Contraste:** 0 textos abaixo de 4,5:1 nos 8 estados (dois modos × vazia, prontas, conversa, indisponível). Antes, a legenda das prontas e a da fonte tinham 3:1.
- **Testes rodados (2026-10-29, WSL):** `uv run pytest` com 296 passed e 2 skipped, sem chave e sem rede; `uv run pytest -m dados_reais tests/test_chat_cobertura.py tests/test_painel.py tests/test_app.py` com 19 passed, numa cópia do banco (os 10 números conferidos contra o ESTADO_ATUAL). O banco real continua com o mesmo SHA-256. `data/publico`, `data/completo`, `src/painel` e `config/premissas` sem mudança. `ruff`: só o aviso antigo de `scripts/arquivo/`.
- **Chamadas reais gastas:** cerca de 150 no dia, entre medições, capturas e diagnósticos, todas na chave do `.env`.
- **Próximo passo:** **refazer a avaliação com o prompt v3** (`uv run python scripts/avaliar_chat.py`); as respostas guardadas da v1 não valem.
- **Antes do push (2026-10-29):**
  - passo a passo para criar o `.env` com a própria chave, com os comandos de Windows e WSL, no `CONTRIBUTING.md` (seção "Chat com o Gemini") e com link no README;
  - `uv run pytest`: 296 passed, 2 skipped, sem chave e sem rede;
  - ficaram fora do commit `eval/respostas/` e `eval/resultado_avaliacao.md`, da rodada de 5 perguntas com o prompt v2, que não vale para o v3.

## 2026-10-29 — Etapa 3, terceira rodada: o painel em torno de uma pergunta só (D-051)
- **Pedido** (autor, modo autônomo): o painel tinha informação demais e não informava nada. Refazer em torno da pergunta "quanto dinheiro o seguro obrigatório dos cartórios pode movimentar em MG, e quão certo é esse número?"; o que não responde "quanto" ou "quão certo" sai do painel e fica no chat.
- **Escada usada:** cartórios ativos (2.525) → obrigados (≈ 1.121) → sem bens suficientes (≈ 148) → déficit (R$ 34,1 mi) → vira seguro (R$ 17,1 mi) → **prêmio anual (R$ 341,1 mil)**; quão certo: faixa provável R$ 215 mil a R$ 687 mil, taxa e adesão com 58,4% da incerteza; até 2027: prêmio ≈ R$ 349,0 mil com a dívida de 2025, e a dívida +28,5%. O passivo, o CLT e o teto ficam só na tabela de "Sobre os dados".
- **Corte** (`docs/painel/corte.md`): 71 elementos: 17 ficam, 8 vão para "Sobre os dados", 31 para o chat, 15 saem. 7 itens do chat ainda sem ferramenta.
- **Páginas e manchetes:**

  | Página | Manchete | Números em destaque | Gráficos | Teste dos 5 segundos (o que um leigo entende) |
  |---|---|---|---|---|
  | A resposta (Início) | "Quanto dinheiro o seguro obrigatório dos cartórios pode movimentar em Minas Gerais, e quão certo é esse número?" | 1 (o prêmio, com a faixa embaixo) | 1 (funil) | "As seguradoras ganhariam uns R$ 341 mil por ano, provavelmente entre 215 e 687 mil; poucos cartórios precisam do seguro." ✓ |
  | Quão certo é | "Quão certo é o número?" | 2 | 2 (faixa; 5 suposições) | "O número é incerto porque ninguém sabe a taxa nem quantos vão escolher seguro." ✓ |
  | Onde está o mercado | "Onde está o dinheiro?" | 3 | 1 (mapa) | "Um quarto está em Belo Horizonte; o resto se espalha pelas cidades maiores." ✓ |
  | Para onde vai | "Para onde vai o mercado até 2027?" | 2 (projeção) | 1 | "Até 2027 o prêmio quase não muda, a não ser que a dívida trabalhista cresça." ✓ |
  | Sobre os dados | "Sobre os dados" | 0 (tabelas) | 0 | "De onde vêm os números e o que eles não sabem." ✓ |

  Texto: no máximo 2 frases por bloco em todas. Limites, ausência de termos técnicos fora de "Sobre os dados" (carga, versão, nível, UF, STF, IDs, tabelas, notebooks) e número repetido entre páginas testados em `tests/test_app_demo.py`.
- **Visual** (terceira rodada do `docs/painel/padrao_visual.md`): sem a faixa azul-escura; fundo `#f7f8fa`, cartões brancos com borda fina, destaque `#3366e6`, comparação `#e08a1e` (validados com o script da skill de visualização e em escala de cinza), grade de 12 colunas, espaçamento em múltiplos de 8 px, navegação branca com o item ativo em fundo leve. Títulos de gráfico quebrados para caber no celular; no tornado, o nome da suposição fica acima da barra.
- **Capturas:** `docs/qa/painel/rodada3_antes/` (31 estados da segunda rodada, 1280/1366/1920 px, tiradas de uma cópia exata do último commit) e `docs/qa/painel/rodada3_depois/` (9 estados em 390, 1280, 1366 e 1920 px; `checagens.md` com **0 falhas**). O verificador de layout (`scripts/qa_painel.py`) passou a comparar os rótulos sem as marcas `<b>` e a contar barras só em gráficos de uma série.
- **Conferências:** os 10 números iguais aos da tabela de referência (lidos do banco real só para leitura; SHA-256 igual ao do início da sessão); pipeline, premissas, gold, `data/publico/` e `data/completo/` sem mudança; modo demonstração abre sem o banco (todas as páginas, na suíte padrão).
- **Erros da IA** (no `docs/erros_ia.md`): o erro de direção da segunda rodada; um script de substituição de texto no `app/comum.py`; capturas "antes" contaminadas por rodar junto com a reescrita; contagem do corte escrita antes de contar.
- **Branch:** feita na `etapa-5-chat` (a ativa na sessão). Nada foi commitado.

## 2026-10-29 — Visual do painel no padrão do "Raio-X do Cartório" (D-052)
- **Pedido** (autor): painel esteticamente igual ao artefato "Raio-X do Cartório"; ver como melhorar estrutura e gráficos na ideia dele; levantar o que as versões antigas do painel mostravam e saiu.
- **Feito (só aparência; estrutura da D-051 mantida):** tema e CSS novos (IBM Plex Sans e Newsreader, fundo `#eceff3`, faixa azul-marinho com traço dourado, cartões com sombra que sobem sobre a faixa, número principal em quadro azul-claro, conclusão em quadro dourado-claro, selos por significado, perguntas ao chat em pílulas, tabela no desenho do demonstrativo); gráficos na paleta do artefato, título em serifa e subtítulo no campo próprio do Plotly; escala do mapa no azul do painel. Detalhe em `docs/painel/padrao_visual.md`, seção 9.
- **Conferido no navegador** (1366 px e 375 px): as 6 páginas. Corrigido na conferência: rótulo do topo escondido sob a barra do Streamlit; frase de conclusão quebrada em colunas (flex com negrito); filtro do Mercado sobre o azul-marinho; título de seção de "Sobre os dados" sobre a faixa; título do Chat escondido sob a barra; emenda da faixa no celular (degradê trocado por cor sólida); azul-marinho no fim da escala do mapa.
- **Testes:** suíte padrão 307 passed, 2 failed (`test_completo` e `test_publico`, o ruído de ponto flutuante entre máquinas: esta branch não tem o commit `bb12465` da `etapa-3-painel`); `dados_reais` de `test_app`, `test_painel` e `test_auditoria_painel`: todos passam depois de atualizar as cores do mapa no teste; ruff sem erro em `src/painel` e `app`.
- **Propostas de estrutura inspiradas no artefato (não feitas; decisão do autor):** (1) **busca por cartório** (CNS ou município) no topo, com a ficha da serventia: obrigada ou não, passivo, chance de déficit (já na `gold.serventia_publico`), sem nome de pessoa (D-038); (2) **série por ano** da arrecadação de MG (ou da serventia) com o crescimento anual composto, como o demonstrativo do artefato; (3) **posição relativa** ("entre os 10% maiores em passivo") na ficha; (4) **avisos de qualidade por ano** visíveis na tabela da serventia (salto grosseiro, semestre faltando).
- **O que saiu nas versões antigas** (lista completa, elemento a elemento, em `docs/painel/corte.md`): STF e ADI 8015 (cenários e situação); simulador (fora da navegação, em `app/simulador.py`); os 10 números como cartões no Início (hoje tabela em "Sobre os dados"); glossário; 3 cartões D-042; ranking dos 15 maiores, filtros por atribuição, situação e classe, métricas do mapa (passivo, serventias, CLT), tabela por área; gráficos dos grupos e de "quem é obrigado"; tornado com 11 suposições (hoje 5); projeção do universo, da arrecadação e das subidas; concentração (Gini e curva de Lorenz); pergunta 9 (lucro da seguradora); qualidade detalhada (escolhas de método, leitura literal da norma, saltos, conferência CNJ × RAIS, contratos); downloads de CSV. Da Fase 1 (20/10), além disso: salvar cenário e a tabela por UF do simulador.
- **Branch:** feito na `etapa-5-chat` (a ativa na sessão), sem commit.

## 2026-10-29 — D-052, segunda passada: tokens idênticos aos do Raio-X
- **Pedido** (autor): o visual da primeira passada "não estava legal"; quer o painel inteiro com o mesmo fundo, texto, cores de gráfico e de mapa do Raio-X, a ponto de uma página dele caber no painel sem emenda.
- **Feito:** `src/painel/estilo.css` reescrito com os tokens e as medidas do Raio-X em px (faixa em degradê `#0f2447` → `#183564`, cartão de 14 px, quadro do agregado, veredito, badge, `.btn2`, `table.st`); tema com `baseFontSize = 14` e superfície-2 `#f5f7fa`; gráficos com marcas em `#45506a`, eixo `#c2c9d6`, barras com borda branca de 2 px, título Newsreader 600 sem `<b>`, funil em s1 com o prêmio em s2; mapa de `#e8eef8` a `#183564` passando por s1 (`graficos.SEQUENCIAL`, usado pela página do Mercado); `src/agent/chat.css` só com as cores e a fonte do título trocadas. Tabela de tokens e componentes em `docs/painel/padrao_visual.md`, seção 9.
- **Conferido no navegador** (1366 px, por medição no DOM, porque a janela ficou oculta e as capturas travaram): fundo `rgb(236,239,243)`, corpo 14 px, título 42 px em Newsreader, barras s1/s2 com borda branca de 2 px, títulos dos gráficos Newsreader 600 `#0f1c33`, subtítulos IBM Plex `#6b7590`, marcas `#45506a`, cartões de 14 px; sem rolagem horizontal e com a navegação no lugar.
- **Erro achado e corrigido:** o pseudo-elemento largo da faixa fez o contêiner do Streamlit rolar para o lado e esconder a navegação; trocado por `border-image` com recuo (ver `docs/erros_ia.md`).
- **Testes:** suíte padrão 307 passed, 2 failed (os dois de coerência, ruído de ponto flutuante: falta o `bb12465` nesta branch); `dados_reais` de `test_app`, `test_painel`, `test_auditoria_painel` e `test_chat`: 33 passed (o teste do título da projeção passou a aceitar o título sem `<b>`); ruff sem erro.

## 2026-10-29 — D-052, terceira passada: o tema escuro do Raio-X
- **Pedido** (autor, com capturas do Raio-X): "nada mudou"; o fundo e as cores têm de ser os do Raio-X.
- **Causa:** (1) o painel do autor (porta 8501) foi aberto às 21:48, antes das mudanças, e o Streamlit só lê o tema e o código dos gráficos ao iniciar; (2) o sistema do autor está no **modo escuro**, e o Raio-X segue o sistema: as capturas são do tema escuro dele (fundo `#0c1018`, cartões `#141a25`), e o painel só tinha os tokens claros.
- **Feito:** `[theme.light]` e `[theme.dark]` no `.streamlit/config.toml`; tokens escuros do Raio-X no `estilo.css`, escolhidos pelo marcador de tema de `ui.estilo()` (`st.context.theme`) ou, sem ele, por `prefers-color-scheme`; gráficos e mapa trocam de cor no escuro em `graficos.finalizar()` (`ESCURO`, escala do mapa invertida, fundo do mapa escuro); `chat.css` nas variáveis de tema; `5_Chat.py` lê a cor de marca da seção nova do tema. Item ativo da navegação com o texto na cor do texto (o azul-marinho sumia no escuro).
- **Conferido no navegador** com o esquema escuro e o claro (1366 px): as 6 páginas, inclusive o mapa e o Chat. O "Map error" no console do mapa aparece nos dois temas (não vem desta mudança).
- **Testes:** suíte padrão 307 passed, 2 failed (os de coerência, ruído de ponto flutuante: falta o `bb12465`); `dados_reais` de app, painel, auditoria e chat: 33 passed; ruff sem erro.

## 2026-10-31 — Estado depois da versão final e tolerância de coerência na `main`
- **Git:** `origin` = `github.com/luccaamp/radar-seguro-cartorio`; no remoto só a `main` (um commit, `3c99a3a`, "Versão final") e a tag `dados-2026-10-19`. O checkout estava em HEAD destacado na `origin/main`; as branches locais são da história antiga, sem ancestral comum com ela.
- **Testes na versão final:** suíte padrão 307 passed, 2 failed (`test_gold_completo_coerente_com_o_gold_local`, `test_publico_coerente_com_o_gold_local`), em `analise_clt_modelo` (diferença relativa máxima 1,5e-11) e `analise_previsao` (5,5e-5): o mesmo ruído entre máquinas de 2026-10-28. A versão final tinha ficado sem o `bb12465`.
- **Feito (a pedido do autor):** a correção do `bb12465` reaplicada com a ferramenta de edição, igual ao original (`git diff bb12465` vazio nos 5 arquivos): `config/publico.yaml` (`tolerancia_coerencia: 1.0e-4`, fonte: suposição), `src/publico.py` (`mesmo_conteudo`, `tabela_coerente`), `tests/test_completo.py`, `tests/test_publico.py` (mais o teste sintético) e `tests/test_pipeline.py`.
- **Testes:** suíte padrão 310 passed. Banco real só lido (SHA-256 `c935a190…` antes e depois). `data/publico/` e `data/completo/` não mudaram. Sem commit.

## 2026-10-31 — `main` alinhada com o GitHub e conferência do projeto com os dados reais e num clone
- **Git (pedido do autor):** cópia da `main` antiga em `main-antiga` (`1810f98`); `git switch -C main origin/main`, com as mudanças acima mantidas na pasta; a `main` rastreia a `origin/main`.
- **Dados reais no projeto:** `uv run pytest -m dados_reais`: 57 passed em 24 min (os testes montam uma cópia do banco, `tests/apoio_painel.py`). SHA-256 do banco e dos Parquet de `data/silver` e `data/gold` iguais antes e depois.
- **Clone novo** (`git clone` do GitHub numa pasta temporária, fora do OneDrive, sem nada desta máquina):
  - `uv sync` em 1,5 min; suíte padrão: 307 passed, 2 skipped (os de coerência, sem banco);
  - modo demonstração (seção 1 do README): as 7 páginas abrem sem exceção (AppTest);
  - modo completo (seção 1b): `exportar_completo.py --instalar` (10 tabelas e o CSV do BI, hash conferido) e `pipeline.py --a-partir-de silver` em ≈ 4 min; contratos do silver com 0 erros e 4 avisos, contratos do gold com 0 erros e 1 aviso (os avisos já conhecidos);
  - gold do clone × banco real: **39 de 39 tabelas com o mesmo hash de conteúdo**; os 10 números iguais aos do `ESTADO_ATUAL` (`linha_de_base.py`);
  - painel do clone no navegador: as 6 páginas abrem; sem a chave, o chat mostra "indisponível" e as perguntas prontas funcionam. Os 404 do console são o Streamlit pedindo `<página>/_stcore/health` ao abrir a URL de uma página direto (inofensivo);
  - coerência no clone: sem a correção da tolerância, `test_publico`/`test_completo` falham nas mesmas 2 tabelas; com ela, 12 passed;
  - `dados_reais` no clone (com a correção): 45 passed, 9 skipped (bronze ausente), 3 failed: `test_rais_`, `test_susep_` e `test_cnpj_extrato_regenerado_igual` acham os originais em `C:\radar_arquivo` (fora do projeto) e depois leem o extrato oficial do bronze do clone, que não existe. Num PC sem os originais, eles são pulados. Fica a melhoria opcional: pular também quando falta o extrato no bronze.
