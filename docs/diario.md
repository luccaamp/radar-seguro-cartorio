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
  - ambiente novo da colaboradora `leticia-ribeirom` (WSL): carga 2026-10-19 da equipe instalada com `scripts/baixar_dados.py` (bronze, silver, gold, banco; hashes conferidos). Os originais grandes (`originais-2026`) não foram baixados: só são necessários para regerar um extrato do bronze;
  - `scripts/testes_metodos.py` (escrito fora do repositório e trazido pela colaboradora): compara de 3 a 7 métodos em sete pontos que dependem de estimativa (T1 empregados pela receita, T2 previsão da arrecadação, T3 subida de classe, T4 vacância, T5 salário de dezembro ausente, T6 reserva salarial, T7 faixa do prêmio), cada um contra uma referência simples e com o indicador fixado antes. Rodado três vezes (duas com bibliotecas temporárias, uma com as do projeto): `resultados.json` idêntico byte a byte. Resultados em `docs/qa/analises/testes_metodos_resultados.json`, explicados em `docs/qa/analises/testes_metodos.md`;
  - `docs/plano_projeto.md` (escrito pela colaboradora): seis etapas até a entrega, portões, riscos e as decisões do autor com a etapa de cada uma; revisado contra os documentos e o banco (os números citados batem com o `resultados.json`, exceto o T6, que dizia 143 municípios em vez de 135: corrigido), com os trechos quebrados da exportação trocados por tabelas e "Fase" trocado por "Etapa";
  - `docs/plano_mineracao.md` reescrito como detalhamento da Etapa 1, coerente com o plano do projeto (D-039); `ESTADO_ATUAL.md` aponta para os dois;
  - `uv add scikit-learn statsmodels mlxtend`;
  - escada de perguntas com 9 degraus: a pergunta do STF saiu do `plano_projeto.md` e do `entenda_o_projeto.md` (pedido da colaboradora). O cenário do STF continua no Simulador e nos riscos;
  - `notebooks/README.md` excluído a pedido da colaboradora: as regras já estavam no `CONTRIBUTING.md` (seção Notebooks) e a lista dos notebooks está no `plano_mineracao.md`. As referências vivas (README, CONTRIBUTING, notebook 00, `src/notebooks.py`, `tests/test_notebooks.py`) apontam para o CONTRIBUTING; as menções nos registros antigos ficam como estão;
  - `CONTRIBUTING.md`: qualquer colaborador pode fazer o merge na `main` (D-040, proposta), alinhando o texto à ruleset, que já não exige aprovação.
- **Decisões:** D-039 e D-040 (proposta; vale com a aprovação do autor no pull request). O teste `test_estado_atual_indica_o_documento_da_etapa` exige o prefixo `plano_`, por isso o arquivo se chama `plano_projeto.md`.
- **Suposições:** nenhuma nova. Os testes só leem dados e premissas v2.
- **Limitações encontradas:**
  - T1: nenhum método acerta o total de uma região não vista com até 5% de erro (o melhor, ~9%);
  - T2 e T3: os vencedores no passado erram para baixo em 2024–2026 (o 2026-1 parcial, R$ 3,20 bi, já passou do P90 da previsão; 218 subidas previstas × 294 reais);
  - T4: vazamento declarado (receita e CLT de vagas medidos sob interino);
  - T6: os municípios testados são os 135 maiores, que diferem mais da própria região que os pequenos;
  - T7: sem valor real para comparar; o critério é a largura e a probabilidade declarada da faixa.
- **Próximo passo:** commit e pull request da colaboradora; aprovação do autor; depois, a parte B do plano da mineração.
