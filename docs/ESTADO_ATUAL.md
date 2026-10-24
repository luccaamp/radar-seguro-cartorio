# Estado atual do projeto

> Leia primeiro. Atualizado ao fim de cada sessão (regra do `CLAUDE.md`). Última atualização: **2026-10-23**.

## O que é
Radar Seguro-Garantia Cartórios: projeto de portfólio, 100% gratuito e local.
- **Painel:** cartórios de Minas Gerais, com dados públicos reais.
- **Simulador:** mercado de seguro-garantia criado pelo Provimento CNJ 227/2026.
- **Chat com fontes:** versão reduzida no painel (página Chat, Ollama local, `qwen3:8b`; D-036).
- **Para leigos:** [`entenda_o_projeto.md`](entenda_o_projeto.md) (problema, seguro-garantia, perguntas do projeto e glossário), com link no README e no `CONTRIBUTING.md`.

## Etapa atual
- **Plano oficial do projeto:** [`plano_projeto.md`](plano_projeto.md) (D-039, aprovação do autor pendente no pull request): seis etapas até a entrega, com portões e as decisões do autor.
- **Etapa 1 — Mineração dos dados de MG.** Documento da etapa: [`plano_mineracao.md`](plano_mineracao.md) (siga ele na execução; regra do `CLAUDE.md`). Em conflito, vale o `plano_projeto.md`.
- **Parte A feita em 2026-10-22** (Ollama ok; `src/analise/`; notebooks 01 e 02 com saídas; 16 PNGs em `docs/qa/analises/`) e **revisada no mesmo dia** (revisão de cientista de dados: 16 correções de texto, gráfico, código e testes; nenhum dos 10 números mudou). Resumo no `docs/diario.md`.
- **Testes de métodos T1 a T7 feitos em 2026-10-23** (`scripts/testes_metodos.py`; explicação em `docs/qa/analises/testes_metodos.md`): escolheram o método dos notebooks 05 a 08. Nenhum dos 10 números mudou.
- **Parte B, notebooks 03, 04 e 05 feitos e revisados em 2026-10-23** (`src/analise/padroes.py`, `grupos.py`, `classificacao.py`; 10 PNGs `03_*`, `04_*`, `05*`; rodados numa cópia do banco via `RADAR_BANCO`, duas vezes com a mesma saída). Nenhum dos 10 números mudou (banco real com o mesmo SHA-256 da linha de base). Resumo no `docs/diario.md`.
- **Próximo passo:** o **notebook 06** (regressão: CLT pela receita, teste T1, e decomposição do passivo), que fecha a parte B.
- **Ramo atual:** `notebooks-03-04-05` (a partir da `main` em `1810f98`); notebooks 03 a 05 sem commit.
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

**Última decisão:** D-041. **Próxima:** D-042 (ver [`decisoes.md`](decisoes.md)).

## O que depende do autor agora
- **Aprovar ou não o `plano_projeto.md` (D-039)** no pull request da branch `plano-nome-do-plano`. As decisões do autor, com a etapa em que cada uma precisa ser tomada, estão no fim do plano.
- Revisar o gabarito-rascunho do chat (`eval/gabarito_chat.csv`).
- Achados da parte A para decidir (nenhum número mudou): conferir as serventias 042986 (R$ 108 mi em 2025-2) e 035030 (API ≠ BI em 2025-2; muda a classe) no Justiça Aberta; se quer uma checagem de "saltos" no pipeline e uma regra para semestre com salto grosseiro no enquadramento (efeito máximo: −11 obrigadas, ≈ −1,0%; 12 saem e 1 entra).
- Questões da parte B (notebooks 03 a 05; detalhes no `docs/diario.md`, 2026-10-23): (a) manter ou não a recalibração do 05b, que ajudou em 2024–25 mas errou mais na média da origem móvel (68 × 53 subidas); (b) aprovar as premissas novas com `fonte: suposição` em `config/analise.yaml` (cortes do Apriori, `n_init`, limiar 0,5, repetições da permutação, bootstrap, faixa P10–P90); (c) se a `gold.analise_grupos` fica por serventia (proposta) ou por grupo.
- Se e quando levar a D-038 ao pipeline, ao auditor e ao `gerar_publico.py` (hoje o painel ainda suprime áreas pequenas). Junto, ajustar o prompt do chat (`src/agent/chat.py`, "os dados por serventia não são publicados"), por decisão do autor em 2026-10-22.
- Conferência de nome de pessoa no zip do silver público (`dados-2026-10-19`).
- Convidar os colegas para os dois repositórios e mandar o `CONTRIBUTING.md`.
- E-mail "noreply" do GitHub nos commits.
- Destino de `docs/qa/depois/` (manter ou mover para `C:\radar_arquivo`).
- Preencher a seção "Linha de base" do `docs/diario.md`.
- Apagar a pasta antiga do projeto no OneDrive, depois de 1 a 2 semanas de uso da pasta nova.

As demais pendências técnicas (Parquet com troca no fim, `estado.cenarios_salvos` na próxima carga, ruff, texto da página Qualidade com o caminho antigo do `viabilidade.md`, ajustes do painel e o resto do chat) estão em `docs/historico/ROADMAP.md`, §7 e E4/E5.
