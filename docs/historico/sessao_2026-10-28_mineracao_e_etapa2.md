# Sessão de 2026-10-28: fim da mineração (notebooks 07 e 09), Etapa 2 e as decisões dela

Relatório da sessão com a IA. Os detalhes de cada passo estão no `docs/diario.md` (entradas de 2026-10-28), as decisões na D-043 e na D-044 (`docs/decisoes.md`) e os erros da IA no `docs/erros_ia.md`.

**Resumo:**
- A mineração terminou: o notebook 07 foi revisado e o 09 foi criado.
- O pipeline passou a gravar 8 tabelas `gold.analise_*` com o que a mineração provou.
- As quatro questões da Etapa 2 foram decididas e implementadas.
- Tudo foi rodado e conferido numa **cópia** do banco. Os 10 números não mudaram em nenhuma checagem.
- No fim do dia, a pedido do autor, rodou a **carga oficial** no banco real e o `data/publico/` foi regerado (seção 11).

## 1. Pedidos da sessão
1. **Concluir a mineração e executar a Etapa 2:**
   - Fase A: notebooks 07 e 09, com revisão de cientista de dados.
   - Fase B: Etapa 2 do `plano_projeto.md`, levando ao pipeline o que a mineração provou.
   - Regras: tudo numa cópia do banco; nenhum nome nem CPF; nenhum commit; parar se um dos 10 números mudasse.
2. **Tomar as quatro decisões recomendadas no fim**, explicar a falha do teste com dados reais e entregar este relatório.

## 2. Fase A: notebooks 07 e 09
- **Notebook 07 (previsão):** já estava feito. Rodado do zero, deu as mesmas saídas do commit. Cinco PNGs regravados pela rodada foram restaurados do original; um deles diferia só no anti-aliasing.
- **Notebook 09 (conclusões e lacunas), novo:**
  - Os 10 números oficiais lidos do banco.
  - **10 achados**, cada um com número, gráfico, frase e limitação.
  - Tabela de **8 lacunas**, com a fonte que resolveria cada uma.
  - Recomendação de achado × gráfico × página para o painel.
  - 10 PNGs `docs/qa/analises/09_*`.
  - Rodado duas vezes do zero numa cópia: saídas e PNGs idênticos.
- **Código reutilizável:**
  - `src/analise/tabelas.py`: uma função por tabela `gold.analise_*`, que repete os notebooks com a mesma semente.
  - `src/analise/conclusoes.py`: as contas do 09.
  - `src/analise/grupos.py`: `nomes_grupos`, com os nomes em `config/analise.yaml`.
- **Achados principais do 09:**
  - O prêmio base (R$ 368,7 mil) é 7,7% do teto teórico.
  - A faixa P5–P95 do Monte Carlo, de R$ 206 a 736 mil, é 5,2 vezes mais estreita que os cantos.
  - A taxa e a adesão ao seguro dominam a incerteza.
  - Os 10% maiores cartórios têm 53,5% do passivo das obrigadas.
  - O grupo "providas grandes" tem 67% do passivo das obrigadas.
  - A receita líquida do repasse tira 20% do universo.
  - Em 2027, o universo fica entre 1.124 e 1.244 obrigadas (projeção).
  - Os saltos grosseiros pesam 10% do total de 2026-1.
  - O CLT estimado pela receita erra pouco em MG inteiro (−2,5%), mas 7 das 13 regiões passam de ±10%.

## 3. Fase B: Etapa 2 (pipeline)
- **Etapa nova `pipeline.etapa_analise`**, depois do gold. Grava as tabelas `gold.analise_*` com as funções de `src/analise/tabelas.py`: o mesmo cálculo dos notebooks, conferido igual. A carga leva cerca de 6 minutos a mais.
- **Pipeline do zero numa cópia** (`--a-partir-de silver`): as 25 tabelas antigas com o mesmo hash de conteúdo e os 10 números iguais.
- **`scripts/gerar_publico.py`** ganhou `--banco` e `--destino`, para conferir o conjunto público numa cópia sem tocar no `data/publico/`.
- **Determinismo:**
  - A previsão da floresta aleatória passou a ser sequencial (antes variava no 14º dígito entre execuções).
  - Os valores sim/não da `analise_tornado` viraram 1/0 (a mistura de tipos parou a primeira carga; a troca atômica protegeu o banco).

## 4. Decisões da Etapa 2 (D-044)
| Decisão | O que foi feito | Resultado conferido na cópia |
|---|---|---|
| Aprovar a D-043 e pedir a carga oficial | D-043 aprovada. Carga oficial **não rodada** nesse momento | Carga completa numa cópia: 10 números iguais, 25 de 25 tabelas antigas iguais |
| Linhas da D-042 numa tabela `analise_*` nova | `gold.analise_sensibilidade_metodo`, 5 linhas; `sensibilidade_premissas` intacta | Receita líquida: universo 893,6 (−20,3%), prêmio R$ 337,4 mil (−8,5%). T5: +0,6%. T6: −1,6%. Reserva no estado inteiro: +5,9%. Iguais ao notebook 08 |
| Arredondar a `qualidade.reconciliacoes` a 10 casas | `valor_a`, `valor_b` e `indicador` arredondados em `src/quality/reconciliacao.py`; o status (ok/aviso) usa o valor sem arredondar | Tabela da cópia = tabela do banco real arredondada, com os mesmos status |
| No público, só o perfil agregado dos grupos | `gold.analise_grupos_perfil`, 6 linhas sem CNS; as tabelas por serventia ficam no gold da equipe | Grupos de 91 a 688 serventias; auditor e LGPD sem problema |

**Conjunto público da próxima carga.** Seis tabelas agregadas estão listadas em `config/publico.yaml`, na chave `tabelas_da_proxima_carga`:
- `analise_regras`
- `analise_grupos_perfil`
- `analise_previsao`
- `analise_tornado`
- `analise_monte_carlo`
- `analise_sensibilidade_metodo`

Gerado numa pasta temporária: 31 arquivos e 0,63 MB. O auditor de ataque por diferença achou 0 vazamentos em 989 células, a busca de CNS e de nomes do cadastro não achou nada, e as travas de LGPD passaram.

## 5. Por que um teste com dados reais falhava
O teste é `tests/test_pipeline.py::test_a_partir_do_silver_parquet_reproduz_o_conjunto_publico`. Ele refaz o gold a partir do silver em Parquet e compara o **hash exato** de cada tabela pública com o manifesto do `data/publico/`. A tabela `qualidade.reconciliacoes` saía com outro hash, por estes motivos:
- **Ordem sem garantia:** a consulta que cruza CNJ, CNPJ e RAIS por município não tem `ORDER BY`. Por isso, a ordem das linhas depende de como o DuckDB executa as junções e de como o silver foi lido (do bronze na carga de 19/10, do Parquet no teste).
- **A soma depende da ordem:** a correlação em log é uma soma em ponto flutuante, que muda no último dígito conforme a ordem dos termos. Medido: em 20 ordens sorteadas das mesmas 755 linhas, saíram 8 valores diferentes, com até 1e-15 de diferença. Entre a carga de 19/10 e o teste, a diferença foi de 2,8e-15 (0,9645209993702… nos dois casos).
- **O hash é exato:** qualquer dígito diferente muda o hash, e o teste falha, embora o valor seja o mesmo para qualquer fim prático.
- **Já existia antes desta sessão:** o código do commit `7122a28`, sem nada desta sessão, falha igual.

**Correção:** arredondar a 10 casas. **Até a carga oficial**, o teste continua falhando: o `data/publico/` versionado ainda tem o valor sem arredondar. Depois da carga e da regeração do público, os dois lados ficam arredondados e o teste passa. Os 10 números e as 25 tabelas do gold nunca foram afetados.

## 6. Números de referência
Iguais em todas as checagens: início, fim da Fase A, fim da Fase B e depois das decisões. O banco real ficou com o mesmo SHA-256 (`3e055af4…`), e os 197 arquivos de `data/`, com o mesmo md5.

| Nº | Número | Valor |
|---|---|---|
| 1 | Serventias ativas | 2.525 |
| 2 | Empregados CLT | 12.134 |
| 3 | Obrigadas | 1.121,31 |
| 4 | Passivo (todas) | R$ 311.866.725 |
| 5 | Passivo (obrigadas) | R$ 238.104.261 |
| 6 | Com déficit | 486,02 |
| 7 | Déficit | R$ 36.873.874 |
| 8 | IS do mercado | R$ 18.436.937 |
| 9 | Prêmio anual | R$ 368.738,74 |
| 10 | Teto teórico | R$ 4.762.085 |

## 7. Testes
- **Suíte padrão:** 237 aprovados, 2 ignorados e 85 fora da suíte padrão (`dados_reais`, painel e afins). Inclui `test_notebooks.py`, que procura CPF nos notebooks.
- **Testes com dados reais** (`test_pipeline.py`, `test_analise_tabelas.py`, `test_analise_previsao.py`, numa cópia): 5 aprovados (inclui o novo `test_sensibilidade_metodo_repete_o_notebook_08`) e 1 falha esperada, `test_a_partir_do_silver_parquet_reproduz_o_conjunto_publico`. A falha continua só na `qualidade.reconciliacoes`: o lado novo agora sai arredondado, e o manifesto do `data/publico/` ainda tem o valor sem arredondar. Ela some com a regeração do público na carga oficial (seção 5). O teste não foi mudado nem desativado. Duração: 23 minutos.
- **ruff:** sem erro no código mudado.

## 8. Erros da IA nesta sessão (registrados no `docs/erros_ia.md`)
- O diário dizia que a `analise_previsao` tinha 99 linhas; são 107.
- O título de um gráfico do 09 dizia "na maioria até ±10%", mas 7 das 13 regiões passam disso.
- A previsão da floresta aleatória não dava o mesmo resultado em duas execuções.
- A `analise_tornado` tinha tipo misto, o que parou a primeira carga da cópia.
- Um documento (`plano_mineracao.md`) foi editado por script de substituição, e não pela ferramenta de edição.

## 9. O que falta (para o autor)
1. **Carga oficial**, nesta ordem:
   1. guardar uma cópia do banco atual fora do repositório;
   2. rodar `uv run pipeline.py --a-partir-de silver`;
   3. no `config/publico.yaml`, passar as 6 linhas de `tabelas_da_proxima_carga` para `tabelas`;
   4. rodar `uv run python scripts/gerar_publico.py`;
   5. rodar `uv run python scripts/linha_de_base.py <pasta fora do repositório>`;
   6. rodar `uv run pytest -m dados_reais`.
2. **Etapa 3 (painel):** começar pelo inventário de achados, a partir da seção 4 do notebook 09.
3. **Pendências do autor:** aprovar a D-042 (como mostrar a faixa do prêmio) e decidir sobre as melhorias M1 a M10. A M1 e a M2 responderiam à pergunta 9, sobre o lucro da seguradora; quando uma delas entrar, o 09 é rodado de novo.

## 10. Arquivos alterados (sem commit)
- **Novos:**
  - `notebooks/09_conclusoes_lacunas.ipynb`
  - 10 PNGs `docs/qa/analises/09_*.png`
  - `src/analise/tabelas.py`
  - `src/analise/conclusoes.py`
  - `tests/test_analise_tabelas.py`
  - este relatório
- **Modificados:**
  - Código: `pipeline.py`, `scripts/gerar_publico.py`, `src/analise/grupos.py`, `src/analise/regressao.py`, `src/analise/sensibilidade.py`, `src/quality/reconciliacao.py`
  - Config: `config/analise.yaml`, `config/publico.yaml`
  - Docs: `docs/ESTADO_ATUAL.md`, `docs/diario.md`, `docs/erros_ia.md`, `docs/decisoes.md`, `docs/dicionario_dados.md`, `docs/SPEC.md`, `docs/plano_projeto.md`, `docs/plano_mineracao.md`, `docs/historico/INDICE.md`

## 11. Carga oficial 2026-10-28
Pedida pelo autor, depois do commit `f50c0f8`. As seções 4, 7 e 9 descrevem o estado de antes dela.
1. **Cópia de segurança, fora do repositório:**
   - banco anterior e `data/gold` antigo em `~/radar_arquivo/antes_carga_2026-10-28/` (SHA-256 do banco: `3e055af4…`);
   - linha de base de antes em `~/radar_arquivo/baseline_2026-10-28_antes/`.
2. **Carga:** `uv run pipeline.py --a-partir-de silver` no `data/radar.duckdb` real, sem erro. Log em `~/radar_arquivo/carga_2026-10-28.log`.
3. **Conferência da carga:**
   - os 10 números iguais;
   - as 25 tabelas antigas com o mesmo hash de conteúdo;
   - as 33 tabelas do gold iguais às da carga feita antes na cópia.
4. **Conjunto público:**
   - as 6 tabelas agregadas passaram para `tabelas` no `config/publico.yaml`, e a lista `tabelas_da_proxima_carga` saiu;
   - `uv run python scripts/gerar_publico.py`: 31 arquivos e 0,63 MB. O auditor achou 0 vazamentos em 989 células, a busca de CNS e nomes não achou nada, e as travas de LGPD passaram;
   - contra o manifesto anterior, só a `qualidade.reconciliacoes` mudou de conteúdo (arredondamento), e entraram as 6 tabelas novas.
5. **Linha de base nova:** `~/radar_arquivo/baseline_2026-10-28/linha_de_base.json` (211 arquivos em `data/`, 33 tabelas do gold).
6. **Testes depois da carga:**
   - suíte padrão: 237 aprovados;
   - todos os `dados_reais` (31 minutos): 79 aprovados, 3 ignorados e 1 falha;
   - o teste do silver em Parquet, que falhava desde antes da sessão, **voltou a passar**;
   - a falha nova foi um erro da IA (`erros_ia.md`): a `analise_sensibilidade_metodo` lia o CSV do BI do CNJ no bronze, que é opcional. Por isso, o pipeline a partir do silver parava sem o bronze;
   - corrigido: sem o CSV, a linha da receita líquida sai, com aviso. Com o CSV, o resultado é idêntico ao do banco oficial, e a carga não precisou ser refeita;
   - depois da correção, o teste passou, assim como o teste novo do caso sem o BI e a suíte padrão (237).
   - Banco oficial novo: SHA-256 `4941cffa…`.
7. **O que não foi feito:**
   - nenhuma Release nova no GitHub: `dados-2026-10-19` e `carga-2026-10-19` continuam as publicadas;
   - o `data/carga_atual.json` ainda descreve o pacote instalado de 19/10.

## 12. Melhorias de confiança M1 a M10 (D-045)
Feitas depois da carga oficial. Ficaram num notebook novo, o **10**, e o 09 foi refeito com elas. Tudo foi conferido numa cópia; o banco oficial ainda não tem as 6 tabelas novas.

| Melhoria | O que foi feito | Resultado |
|---|---|---|
| M1 capacidade de pagar | passivo × saldo anual do titular (BI do CNJ, 2025) | chance de déficit de 6,9% / 9,6% (supostos 50% / 30%); déficit total de R$ 34,5 mi (modelo: R$ 36,9 mi) |
| M2 pergunta 9 | sinistro = P(fim) × parte não paga × IS | com a M1, sinistralidade de 12% a 46% e lucro técnico; sem ela, prejuízo |
| M3 previsão | teste desde 2012, faixa calibrada, coleta de 28/10 | o 2026-1 ficou 18% acima do previsto; MG +16,6% em 2026 (07: +7,3%) |
| M4 subidas | desvio condicionado | rejeitada: o erro vem da previsão de MG |
| M5 passivo projetado | tempo de casa + 12 meses/ano, INPC | passivo +14,6% (2026) e +28,5% (2027); prêmio ≈ R$ 422 mil e ≈ R$ 472 mil |
| M6 universo e saltos | faixa entre leituras; 4 serventias conferidas | 894 a 1.121 obrigadas; saltos continuam declarados |
| M7 STF | prêmio por cenário; andamento conferido | sem liminar em 28/10; suspensão = zero |
| M8 taxa e adesão | SES conferida; grade | a SES não publica a IS; prêmio de R$ 92 mil a R$ 903 mil |
| M9 vacância | duas coletas do cadastro | o cadastro é atualizado com atraso; 11 dias não medem a taxa |
| M10 grupos | grupos pela M1 | providas grandes com 85% do déficit |

**Pontos da validação de 27/10 e o que mudou:**
- **pergunta 9 sem análise:** respondida (M2);
- **cenário do STF fora da faixa:** prêmio condicionado (M7);
- **previsão conservadora:** confirmada e corrigida na projeção atualizada (M3 a);
- **faixas mal calibradas:** a da arrecadação estava boa (86%); a da contagem, calibrada (de 27% para 60%);
- **subidas divergentes:** explicado (M4) e reduzido (115 na atualizada);
- **prêmio com o passivo de 2025:** corrigido (M5).

**Coleta nova:** cadastro e arrecadações de MG em 28/10, pela API pública e gratuita, no bronze (`cnj_justica_aberta/2026-10-28/`), só para conferência: o `config/escopo.yaml` não mudou.

**Testes:** 8 testes novos (`tests/test_analise_melhorias.py`); suíte padrão com 245 aprovados; todos os `dados_reais` numa cópia (39 minutos): 81 aprovados, 3 ignorados, nenhuma falha.

**Pendente:** as 6 tabelas novas só entram no banco oficial e no `data/publico/` na próxima carga oficial, com pedido do autor. *(Resolvido na seção 13: entraram 5, porque a sexta dependia da coleta de 28/10.)*

## 13. D-046 e a segunda carga oficial (tarde)

O autor decidiu os três pontos que a D-045 deixou abertos, seguindo a recomendação da IA. No meio do trabalho, ficou decidido não usar nada coletado em 28/10.

| Ponto | Decisão | Efeito |
|---|---|---|
| Regra do salto | valor declarado fica na classe; aviso no pipeline; linha "sem os saltos" na sensibilidade | 45 semestres de 2025 avisados; sem eles, −1,0% no universo e −0,8% no prêmio |
| Recalibrar a D-016 | premissas v3: chance de déficit (ponderada pelo passivo) e parte descoberta pela M1, depois de conferir as 50 obrigadas com saldo ≤ 0 | déficit, IS e prêmio −7,5%; "com déficit" de ≈ 486 para ≈ 148 |
| Coleta de 28/10 | não usar; dados só de 17 e 18/10 | coleta apagada (a pedido); sem Release nova; sai a `analise_previsao_atualizada`; saem M3 a, M6 c e M9 do notebook 10 |

**Números de referência novos** (premissas v3): 2.525 serventias; 12.134 CLT; ≈ 1.121 obrigadas; passivo R$ 311,9 mi e R$ 238,1 mi; **≈ 148 com déficit; déficit R$ 34,1 mi; IS R$ 17,1 mi; prêmio R$ 341,1 mil**; teto R$ 4,76 mi. Faixa provável do prêmio: R$ 215 a 687 mil.

**Carga oficial** (pedido do autor): cópia conferida antes; backup em `~/radar_arquivo/antes_carga_2026-10-28_d046/`; banco novo idêntico à cópia; 38 tabelas no gold; `data/publico/` com 36 tabelas e auditor sem vazamento; linha de base em `~/radar_arquivo/baseline_2026-10-28_d046/`.

**Também:** nome do relator da ADI tirado do diário, do SPEC e da página inicial do painel; simulador com uma casa decimal na chance e na parte descoberta (erro da IA achado pelo teste do painel); README e gabarito do chat com os valores novos; notebooks 09 e 10 refeitos; nota da D-046 no fim de 01 a 08.

## 14. D-048: pendências do pipeline antes da Etapa 3

As pendências do pipeline foram resolvidas antes do painel; o autor pediu a D-038 no pipeline.

| Pendência | Decisão | Efeito |
|---|---|---|
| D-038 (resultado por cartório público) | fase 1 agora, fase 2 na Etapa 3 | tabela pública `gold.serventia_publico` (2.525 linhas, pelo CNS e pelo município, soma igual ao total de MG); `analise_grupos` e `analise_clt_modelo` públicas; chat com `consultar_serventia` |
| 035030 (classe pela API ou pelo BI) | classe pela API, com aviso | aviso `classe_api_x_bi`: 10 serventias mudariam de classe pelo BI, 6 para a Classe 1 |
| Nomes de pessoa no silver público | conferido | nenhum dos 4.441 nomes do cadastro |

**Carga oficial** (pedido do autor): igual à cópia; 39 tabelas no gold e no `data/publico/`; os 10 números sem mudança; backup em `~/radar_arquivo/antes_carga_2026-10-28_d048/`.

**Testes:** suíte padrão com 247 testes passando; `dados_reais` com 80 passando, 3 pulados e 1 falha. A falha era um teste de LGPD que ainda cobrava o limiar de 3 serventias (erro da IA, corrigido).

**Fica para a Etapa 3:** fase 2 da D-038 (sem limiar de 3 serventias, sem áreas agregadas, mapa e ranking por município).
