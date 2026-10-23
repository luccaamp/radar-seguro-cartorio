# Estado atual do projeto

> Leia primeiro. Atualizado ao fim de cada sessão (regra do `CLAUDE.md`). Última atualização: **2026-10-22**.

## O que é
Radar Seguro-Garantia Cartórios: projeto de portfólio, 100% gratuito e local.
- **Painel:** cartórios de Minas Gerais, com dados públicos reais.
- **Simulador:** mercado de seguro-garantia criado pelo Provimento CNJ 227/2026.
- **Chat com fontes:** versão reduzida no painel (página Chat, Ollama local, `qwen3:8b`; D-036).

## Etapa atual
- **Mineração dos dados de MG.** Documento da etapa: [`plano_mineracao.md`](plano_mineracao.md) (siga só ele; regra do `CLAUDE.md`).
- **Parte A feita em 2026-10-22** (Ollama ok; `src/analise/`; notebooks 01 e 02 com saídas; 16 PNGs em `docs/qa/analises/`) e **revisada no mesmo dia** (revisão de cientista de dados: 16 correções de texto, gráfico, código e testes; nenhum dos 10 números mudou). Resumo no `docs/diario.md`.
- **Próximo passo:** a **parte B** do plano (notebooks 03, 04, 05 e 06).
- **Ramo atual:** `main` (último commit `cdd87ca`; a D-038 e a parte A ainda sem commit).
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

**Última decisão:** D-038. **Próxima:** D-039 (ver [`decisoes.md`](decisoes.md)).

## O que depende do autor agora
- Commit da D-038, da parte A e da revisão da parte A; revisar o gabarito-rascunho do chat (`eval/gabarito_chat.csv`).
- Achados da parte A para decidir (nenhum número mudou): conferir as serventias 042986 (R$ 108 mi em 2025-2) e 035030 (API ≠ BI em 2025-2; muda a classe) no Justiça Aberta; se quer uma checagem de "saltos" no pipeline e uma regra para semestre com salto grosseiro no enquadramento (efeito máximo: −11 obrigadas, ≈ −1,0%; 12 saem e 1 entra).
- Se e quando levar a D-038 ao pipeline, ao auditor e ao `gerar_publico.py` (hoje o painel ainda suprime áreas pequenas).
- Conferência de nome de pessoa no zip do silver público (`dados-2026-10-19`).
- Convidar os colegas para os dois repositórios e mandar o `CONTRIBUTING.md`.
- E-mail "noreply" do GitHub nos commits.
- Destino de `docs/qa/depois/` (manter ou mover para `C:\radar_arquivo`).
- Preencher a seção "Linha de base" do `docs/diario.md`.
- Apagar a pasta antiga do projeto no OneDrive, depois de 1 a 2 semanas de uso da pasta nova.

As demais pendências técnicas (Parquet com troca no fim, `estado.cenarios_salvos` na próxima carga, ruff, texto da página Qualidade com o caminho antigo do `viabilidade.md`, ajustes do painel e o resto do chat) estão em `docs/historico/ROADMAP.md`, §7 e E4/E5.
