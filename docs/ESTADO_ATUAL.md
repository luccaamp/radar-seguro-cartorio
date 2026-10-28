# Estado atual do projeto

> Leia primeiro. Atualizado ao fim de cada sessão (regra do `CLAUDE.md`). Última atualização: **2026-10-28**.

## O que é
Radar Seguro-Garantia Cartórios: projeto de portfólio, 100% gratuito e local.
- **Painel:** cartórios de Minas Gerais, com dados públicos reais.
- **Simulador:** mercado de seguro-garantia criado pelo Provimento CNJ 227/2026.
- **Chat com fontes:** versão reduzida no painel (página Chat, Ollama local, `qwen3:8b`; D-036).
- **Para leigos:** [`entenda_o_projeto.md`](entenda_o_projeto.md) (problema, seguro-garantia, perguntas do projeto e glossário), com link no README e no `CONTRIBUTING.md`.

## Etapa atual
- **Plano oficial do projeto:** [`plano_projeto.md`](plano_projeto.md) (D-039, aprovação do autor pendente no pull request): seis etapas até a entrega, com portões e as decisões do autor.
- **Etapa 3 — Painel** (Etapas 1 e 2 concluídas em 2026-10-28). Documento da etapa: [`plano_projeto.md`](plano_projeto.md), seção "Etapas 3 a 5" (siga ele na execução; regra do `CLAUDE.md`). O [`plano_mineracao.md`](plano_mineracao.md) virou histórico, salvo a seção das melhorias M1 a M10.
- **Parte A feita em 2026-10-22** (Ollama ok; `src/analise/`; notebooks 01 e 02 com saídas; 16 PNGs em `docs/qa/analises/`) e **revisada no mesmo dia** (revisão de cientista de dados: 16 correções de texto, gráfico, código e testes; nenhum dos 10 números mudou). Resumo no `docs/diario.md`.
- **Testes de métodos T1 a T7 feitos em 2026-10-23** (`scripts/testes_metodos.py`; explicação em `docs/qa/analises/testes_metodos.md`): escolheram o método dos notebooks 05 a 08. Nenhum dos 10 números mudou.
- **Parte B, notebooks 03, 04 e 05 feitos e revisados em 2026-10-23** (`src/analise/padroes.py`, `grupos.py`, `classificacao.py`; 10 PNGs `03_*`, `04_*`, `05*`; rodados numa cópia do banco via `RADAR_BANCO`, duas vezes com a mesma saída). Nenhum dos 10 números mudou (banco real com o mesmo SHA-256 da linha de base). Resumo no `docs/diario.md`.
- **Validação e notebook extra 05c em 2026-10-23:** os notebooks 00 a 05 rodados de novo do zero numa cópia deram as mesmas saídas e os mesmos 26 PNGs do commit. Novo notebook **05c (vacância no tempo)**, fora do plano original, a pedido do autor: mede a taxa de vacância com as datas do cadastro do CNJ e propõe uma faixa para a P(fim da delegação no ano) da D-025 (2% a 7,5%, central ≈ 4%), sem mudar nenhuma premissa.
- **Notebooks 06 (regressão) e 08 (sensibilidade e concentração) feitos e revisados em 2026-10-23**, a pedido da colaboradora (o 08 é da parte C, adiantado): `src/analise/regressao.py` e `sensibilidade.py`, 11 PNGs `06_*` e `08_*`, desenho de `analise_clt_modelo`, `analise_tornado` e `analise_monte_carlo`. Reproduzem o T1 e o T7; rodados duas vezes do zero numa cópia do banco, com as mesmas saídas. Nenhum dos 10 números mudou. Resumo no `docs/diario.md`.
- **Parte B concluída** (notebooks 03 a 06, mais o extra 05c).
- **Notebook 07 (previsão do mercado) feito em 2026-10-27** (`src/analise/previsao.py`, `tests/test_analise_previsao.py`, 5 PNGs `07_*`, seção `previsao` em `config/analise.yaml`; rodado duas vezes do zero numa cópia do banco, com as mesmas saídas). Repete o T2 (MAPE 7,4%); MG arrecada R$ 5,92 bi em 2026 e R$ 6,71 bi em 2027 (projeção); o "2026-1 acima do P90" era, em grande parte, salto grosseiro (059816, 046219); sem evidência de quebra em 2025-2; universo de 1.121 para 1.161 a 1.244 obrigadas em 2027, prêmio ≈ R$ 367 mil (passivo de 2025). Desenho da `gold.analise_previsao`. Nenhum dos 10 números mudou. Resumo no `docs/diario.md`.
- **Validação de todos os notebooks em 2026-10-27:** 01 a 08 rodados do zero no ramo juntado, com as mesmas saídas (Portão 1 cumprido para eles). Avaliação de confiança e lacunas no `docs/diario.md` (2026-10-27): a pergunta 9 (lucro da seguradora) não tem análise, o cenário do STF fica fora da faixa e a previsão principal do 07 tende a ser conservadora.
- **Melhorias de confiança propostas em 2026-10-27** (`plano_mineracao.md`, seção "Melhorias de confiança", M1 a M10), a pedido do autor, **antes do 09**. As principais: M1, déficit pela capacidade de pagar (passivo ÷ saldo do titular, BI do CNJ); M2, a pergunta 9 por frequência × severidade (05c + M1); M5, passivo projetado; M4, subidas com desvio condicionado.
- **Notebook 09 (conclusões e lacunas) feito em 2026-10-28**, a pedido da colaboradora, antes das melhorias M1 a M10 (Fase A da sessão): 10 achados com número, gráfico e frase; tabela de 8 lacunas com a fonte que resolveria cada uma; recomendação de achado × gráfico × página para o painel; 10 PNGs `09_*`. Rodado duas vezes do zero numa cópia, com as mesmas saídas e PNGs. O 07 foi revisado (rodado do zero: as mesmas saídas). **Etapa 1 concluída; Portão 1 cumprido.**
- **Etapa 2 (pipeline) feita em 2026-10-28, numa cópia** (Fase B; D-043, proposta): `pipeline.etapa_analise` grava seis tabelas `gold.analise_*` (regras, grupos, CLT pela receita, previsão, tornado, Monte Carlo) com `src/analise/tabelas.py`, que repete os notebooks com a mesma semente (conferido igual). Pipeline do zero (`--a-partir-de silver`) numa cópia: **25 de 25 tabelas antigas com o mesmo conteúdo** da carga 2026-10-19, mais as 6 novas; os 10 números iguais. **Portão 2 cumprido na cópia.** O banco real **não** foi recarregado (carga oficial só a pedido do autor) e o `data/publico/` não mudou. As 4 tabelas agregadas entram no conjunto público na próxima carga oficial (conferido numa cópia: travas de LGPD ok); as 2 por serventia esperam a D-038 chegar ao pipeline. A carga ficou ≈ 6 minutos mais longa.
- **Decisões da Etapa 2 tomadas pela colaboradora em 2026-10-28 (D-044):** D-043 aprovada; as linhas da D-042 (receita líquida, T5, T6, reserva no estado inteiro) foram para a tabela nova `gold.analise_sensibilidade_metodo`, sem mudar a `sensibilidade_premissas`; a `qualidade.reconciliacoes` passou a ser arredondada a 10 casas (corrige a falha do teste `dados_reais` do silver em Parquet na próxima carga); no público, só o perfil agregado dos grupos (`gold.analise_grupos_perfil`). O pipeline grava agora **8** tabelas `analise_*`. Conferido numa cópia: 25 de 25 tabelas antigas iguais, os 10 números iguais, conjunto público gerado no scratchpad com auditor e LGPD sem problema (31 arquivos, 0,63 MB). **A carga oficial não foi rodada:** o `CLAUDE.md` exige pedido do autor.
- **Próximo passo concreto:** (1) **o autor (`luccaamp`) pede a carga oficial**: guardar uma cópia do banco atual fora do repositório (para o `C:\radar_arquivo` ou, no WSL, `~/radar_arquivo`); rodar `uv run pipeline.py --a-partir-de silver` no banco real; em `config/publico.yaml`, passar as 6 linhas de `tabelas_da_proxima_carga` para `tabelas` (e apagar a lista vazia); rodar `uv run python scripts/gerar_publico.py`; gravar a linha de base nova (`uv run python scripts/linha_de_base.py <pasta fora do repositório>`); rodar `uv run pytest -m dados_reais` (o teste do silver em Parquet deve voltar a passar); (2) começar a **Etapa 3 (painel)** pelo "Antes de construir" do `plano_projeto.md` (inventário de achados, a partir da seção 4 do notebook 09, arquitetura e padrão visual). As melhorias M1 a M10 continuam abertas (a M1 e a M2 dariam resposta à pergunta 9); quando uma entrar, o 09 é rodado de novo.
- **Ramo atual:** `notebooks-07-09` (a partir de `7122a28`), com o trabalho de 2026-10-28 ainda sem commit. Nada enviado ao GitHub nem juntado na `main` nesta sessão.
- **Regras de publicação (D-038):** estudo público; tudo pode ir para o git, inclusive resultados por cartório e notebooks com saídas. Só não pode nome nem CPF de pessoa física. Pipeline, auditor e `gerar_publico.py` ainda seguem as regras antigas (mudança só com pedido do autor).

## Onde estamos
- **Fase 1 (MG) concluída em 2026-10-20** (`21303e2`), em `C:\projetos\radar-seguro-cartorio` (D-033); `main` protegida (`docs/publicacao.md`, seção 4); painel só leitura (D-034).
- **Releases:** `dados-2026-10-19` (público), `carga-2026-10-19` e `originais-2026` (privados); o download dos privados foi testado em 2026-10-20 (25/25 tabelas, os 10 números e os 25 originais por SHA-256).
- **Linha de base:** `C:\radar_arquivo\baseline_2026-10-20\linha_de_base.json`.
- **Chat (D-036):** 5 ferramentas sobre o conjunto público; avaliação em `eval/resultado_avaliacao.md`.

## Números de referência
Carga **2026-10-19**, premissas **v2**, regra base (Classe 1 até R$ 300 mil, Prov. 243), nível base, regra do STF mantida. Esta tabela é a fonte dos valores.

| 1. Serventias ativas | 2. Empregados CLT | 3. Obrigadas (Prov. 227) | 4. Passivo (todas) | 5. Passivo (obrigadas) |
|---|---|---|---|---|
| 2.525 | 12.134 | ≈ 1.121 | R$ 311,9 mi | R$ 238,1 mi |

| 6. Com déficit (esperado) | 7. Déficit | 8. IS do mercado | 9. Prêmio anual | 10. Teto teórico |
|---|---|---|---|---|
| ≈ 486 | R$ 36,9 mi | R$ 18,4 mi | R$ 368,7 mil | R$ 4,76 mi |

Valores exatos na linha de base. O conjunto público (`data/publico/manifesto.json`) traz o hash de cada tabela. "Recalcular dá o mesmo" foi provado em 2026-10-19 e em 2026-10-20: 25 de 25 tabelas idênticas.

**Última decisão:** D-044 (decidida pela colaboradora; carga oficial pendente do autor). **Próxima:** D-045 (ver [`decisoes.md`](decisoes.md)).

## O que depende do autor agora
- **Etapa 2 (2026-10-28; D-043 e D-044):** pedir a carga oficial (passos no "Próximo passo" acima). As questões da etapa foram decididas pela colaboradora (D-044); o autor pode revê-las antes da carga.
- **Aprovar ou não o `plano_projeto.md` (D-039)** no pull request da branch `plano-nome-do-plano`. As decisões do autor, com a etapa em que cada uma precisa ser tomada, estão no fim do plano.
- Revisar o gabarito-rascunho do chat (`eval/gabarito_chat.csv`).
- Aprovar ou não a **D-042** (proposta pela colaboradora em 2026-10-23, a partir dos notebooks 06 e 08; nenhum número muda): faixa do prêmio com a hierarquia base > P5–P95 (R$ 210–740 mil) > cantos; receita líquida do repasse como sensibilidade com a faixa de déficit da base (universo −20%, prêmio −8,5%); T5 e T6 só na tabela de sensibilidade; CLT de outros estados só como total estadual, com ±10% como piso e a RAIS como conferência.
- Achados da parte A para decidir (nenhum número mudou): conferir as serventias 042986 (R$ 108 mi em 2025-2) e 035030 (API ≠ BI em 2025-2; muda a classe) no Justiça Aberta; se quer uma checagem de "saltos" no pipeline e uma regra para semestre com salto grosseiro no enquadramento (efeito máximo: −11 obrigadas, ≈ −1,0%; 12 saem e 1 entra).
- Questões da parte B (notebooks 03 a 05; detalhes no `docs/diario.md`, 2026-10-23): (a) manter ou não a recalibração do 05b, que ajudou em 2024–25 mas errou mais na média da origem móvel (68 × 53 subidas); (b) aprovar as premissas novas com `fonte: suposição` em `config/analise.yaml` (cortes do Apriori, `n_init`, limiar 0,5, repetições da permutação, bootstrap, faixa P10–P90); (c) se a `gold.analise_grupos` fica por serventia (proposta) ou por grupo; (d) do 05c: se a P(fim da delegação no ano) da D-025 passa a usar a faixa 2% / 4% / 7,5% (fonte: notebook 05c) e se vale fazer uma segunda coleta do cadastro do CNJ (gratuita) para medir as mudanças de situação sem viés de sobrevivência.
- Questões do notebook 07 (detalhes no `docs/diario.md`, 2026-10-27): (a) a regra do salto grosseiro ficou mais urgente: os saltos de 2025-2 e 2026-1 somam R$ 161 mi e R$ 330 mi no total de MG (serventias 059816, 042986 e 046219 para conferir no Justiça Aberta); (b) se pede uma coleta e uma carga novas para refazer o 07 com o 2026-1 completo; (c) se o painel mostra a projeção com o limite fixo, com o corrigido pela inflação ou com os dois; (d) aprovar as premissas novas com `fonte: suposição` em `config/analise.yaml`, seção `previsao` (como completar o 2026-1, banda e anos dos desvios, sorteios, IPCA dos últimos 12 meses como inflação futura).
- Se e quando levar a D-038 ao pipeline, ao auditor e ao `gerar_publico.py` (hoje o painel ainda suprime áreas pequenas). Pela D-044, enquanto isso, a análise de grupos vai ao público só como perfil agregado, e a `analise_grupos` e a `analise_clt_modelo` (por serventia) ficam no gold da equipe. Junto, ajustar o prompt do chat (`src/agent/chat.py`, "os dados por serventia não são publicados"), por decisão do autor em 2026-10-22.
- Conferência de nome de pessoa no zip do silver público (`dados-2026-10-19`).
- Convidar os colegas para os dois repositórios e mandar o `CONTRIBUTING.md`.
- E-mail "noreply" do GitHub nos commits.
- Destino de `docs/qa/depois/` (manter ou mover para `C:\radar_arquivo`).
- Preencher a seção "Linha de base" do `docs/diario.md`.
- Apagar a pasta antiga do projeto no OneDrive, depois de 1 a 2 semanas de uso da pasta nova.

As demais pendências técnicas (Parquet com troca no fim, `estado.cenarios_salvos` na próxima carga, ruff, texto da página Qualidade com o caminho antigo do `viabilidade.md`, ajustes do painel e o resto do chat) estão em `docs/historico/ROADMAP.md`, §7 e E4/E5.
