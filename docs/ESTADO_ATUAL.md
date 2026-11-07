# Estado atual do projeto

> Leia primeiro. Atualizado ao fim de cada sessão (regra do `CLAUDE.md`). Última atualização: **2026-11-06**.
> O histórico detalhado até 2026-10-31 (Etapas 1 a 3, mineração, chat, cargas) está em [`historico/ESTADO_ATUAL_ate_2026-10-31.md`](historico/ESTADO_ATUAL_ate_2026-10-31.md) e no [`diario.md`](diario.md).

## O que é
Radar Seguro-Garantia Cartórios: projeto de portfólio, 100% gratuito.
- **Painel:** cartórios de Minas Gerais, com dados públicos reais, em torno de uma pergunta: "quanto dinheiro o seguro obrigatório dos cartórios pode movimentar em MG, e quão certo é esse número?" (D-051). Páginas: Início → Quão certo é → Onde está o mercado → Para onde vai → Sobre os dados → Chat. O Simulador está fora da navegação (`app/simulador.py`).
- **Chat com fontes:** página Chat, com o Gemini no nível gratuito (D-060 a D-069); sem a chave, só a aba de perguntas prontas.
- **Para leigos:** [`entenda_o_projeto.md`](entenda_o_projeto.md).
- **Objetivo final** (do autor, 2026-10-31): todos os estados, num painel público que se atualiza sozinho (pipeline agendado que coleta das fontes). **Agora:** deixar MG pronto e conferido, para que um estado novo seja só dado novo.

## Repositório
- **GitHub:** `luccaamp/radar-seguro-cartorio`, só a `main`. A história recomeçou na "Versão final" (`3c99a3a`, 2026-10-30), que juntou as branches de trabalho; a correção de coerência que tinha ficado de fora voltou em `7b5cc73` (2026-10-31).
- **Local:** `main` = `origin/main`. A `main` de antes da versão final ficou na branch local `main-antiga` (`1810f98`), só como cópia; as outras branches locais (`etapa-3-painel`, `etapa-5-chat`, `notebooks-*`) são dessa história antiga, sem ancestral comum com a `main`.
- **Releases:** `dados-2026-10-19` (público: silver e manifesto); `carga-2026-10-19` e `originais-2026` (privados, em `luccaamp/radar-seguro-cartorio-dados`: bronze por fonte, banco e originais). O bronze fica no privado porque tem nome de pessoa (D-030); a procedência dele está no git em `data/procedencia/` (D-070).
- **Rodar a partir de um clone** (conferido em 2026-10-31): modo demonstração em 2 min; modo completo (README, seção 1b) em ≈ 4 min, com o gold **idêntico** ao do banco real (39 de 39 tabelas) e os 10 números iguais.

## Etapa atual: Fase 1 (MG completo)
**Plano oficial: [`plano_projeto.md`](plano_projeto.md) (D-071, 2026-11-05)**, com 10 fases, de MG completo ao Brasil inteiro publicado e atualizado sozinho. A IA propõe cada passo e segue com a aprovação do autor.

**Fase 1, andamento (2026-11-06):** PR #3 (`fase-1-simulador`) juntado na `main` (`fd66b03`); o ano projetado segue na branch `fase-1-explorar-2027`. Item 1, o Simulador:
- [x] lugar: área "Explorar", separada da história (D-077); menu com duas seções por `st.navigation` em `app/Inicio.py` (mesmos endereços de antes; "Início" com acento);
- [x] página `app/pages/6_Explorar.py` refeita no padrão visual: atalhos de pergunta, controles de cenário e mercado, grupo avançado, resultado com a escada, **faixa por sorteio** e **tornado ao vivo** ao redor dos valores escolhidos (`src/painel/explorar.py`), seguradora hipotética e salvar cenário. No padrão, repete o painel (prêmio R$ 341,1 mil, faixa R$ 215,0 a 687,1 mil); taxa de 3% → R$ 511,6 mil; tornado e sorteios em menos de 1 s (teste);
- [x] **ano 2026/2027 (projeção) e limite fixo × corrigido** (branch `fase-1-explorar-2027`): a `gold.analise_previsao` passa a gravar os totais por faixa de déficit (147 linhas; as 107 antigas iguais), e o Explorar ganha "Mercado de" (Hoje, 2026, 2027) e "Limite da Classe 1". Conferido numa cópia: no padrão, 2027 dá R$ 349,1 mil (fixo) e R$ 343,6 mil (corrigido), os centrais gravados (< 0,03%). Suíte padrão 329 passed; `ruff` sem erro.
- [x] **PR #3 vermelho no "Dados reais"** (2026-11-06): o MAPE do SARIMA deu 10,47376 no Linux do CI contra 10,4748 do T2 gravado no Windows (tolerância era 0,001). Corrigido por outra sessão no commit `378945b` (tolerância de 0,01 ponto, só essa linha); o PR #3 entrou na `main` às 04:39.
- [x] **Carga oficial 2026-11-06** (pedido do autor): backup em `C:\radar_arquivo\antes_carga_2026-11-06_2027\` (banco `c935a190…`, silver, gold, público, completo); `uv run pipeline.py --a-partir-de silver` sem erro (log em `C:\radar_arquivo\carga_2026-11-06_2027.log`); banco novo `dd6fc158…`. As 39 tabelas do gold iguais às de antes, menos a `analise_previsao` (+40 linhas, nenhuma perdida); os 10 números iguais. `data/publico` (39 arquivos, 0,89 MB, auditor sem vazamento) e `data/completo` regerados.
- [x] **PR #4 juntado na `main`** (05:37, `e40ee08`): item 1 completo (testes do SPEC §3 e recálculo < 1 s cobertos).

**Item 2 (D-038, fase 2; D-078), na branch `fase-1-d038-fase2`:** plano em [`plano_fase1_item2.md`](plano_fase1_item2.md), aprovado pelo autor em 2026-11-06 com as 4 recomendações.
- [x] premissas v4 (sem `limiar_agregacao_lgpd`); gold com os 851 municípios no mapa, no ranking e nas tabelas por município; saem as 6 tabelas da supressão e o auditor; painel com a posição do município e os 10 maiores; chat sem "suprimida".
- [x] conferido numa cópia (pipeline `--a-partir-de silver`): os 10 números iguais; as `analise_*` e as demais tabelas iguais; mudaram só as esperadas (mapa, ranking, por município, `mercado_filtro_uf` com as 7 combinações antes suprimidas, `rec_municipio`, `execucao` sem `limiar_lgpd`, `checagens`); contratos do gold 0 erros. Conjunto público gerado da cópia numa pasta temporária: 35 arquivos, 0,72 MB, sem dado pessoal. Painel no navegador (cópia): mapa com 851 municípios, Santana do Paraíso (1 cartório) com os números dele e "179º de 851"; sem rolagem horizontal em 390 px.
- [x] suíte padrão: 317 passed e 3 falhas esperadas em `test_publico.py` (leem o `data/publico` versionado, ainda da carga anterior); com `RADAR_PUBLICO_TESTE` apontando o conjunto novo, os testes do modo demonstração passam.
- [x] **carga oficial 2026-11-07** (pedido do autor: "continue a fase 1 toda [...] e acabe ela toda"): backup em `C:\radar_arquivo\antes_carga_2026-11-07_d078\` (banco `dd6fc158…`, silver, gold, público, completo); `uv run pipeline.py --a-partir-de silver` sem erro (log `C:\radar_arquivo\carga_2026-11-07_d078.log`); banco novo `7f528a8c…`, premissas v4. Contra o backup: o mesmo resultado da cópia (só as tabelas esperadas mudaram; os 10 números iguais). `data/publico` (35 arquivos, 0,72 MB, sem dado pessoal) e `data/completo` (33 tabelas do gold) regerados. Suíte padrão 320 passed; `ruff` sem erro.

**Fase 0 cumprida em 2026-11-06:**
- [x] item 1: plano novo (D-071) e SPEC, ROADMAP, `CLAUDE.md` e `CONTRIBUTING.md` alinhados;
- [x] item 2: D-072 (GitHub Actions, Hugging Face, Kaggle), D-073 (branch por bloco e pull request; substitui o push direto da D-041) e D-074 (Streamlit Community Cloud), aprovadas;
- [x] item 3: decisões pendentes de MG em lote (D-076, 2026-11-06);
- [x] item 4: chave do Gemini trocada pelo autor (2026-11-06); a IA conferiu que a nova responde, sem exibi-la;
- [x] item 5: CI no GitHub Actions (PR #2, juntado pelo auto-merge em 2026-11-06, merge `8055866`: "Testes e ruff" em 36 s e "Dados reais" em 22 min, no Linux do GitHub). `main` protegida pelo CI e auto-merge no repositório (D-075);
- [x] item 6: bloco A e estes documentos na `main` (PR #1, juntado em 2026-11-05, merge `1ed46db`). Backup de MG antes dele: branch `backup-MG` e tag `mg-backup-2026-11-05` (`7b5cc73`).

A lista de fechamento de MG, combinada com o autor em 2026-10-31, foi distribuída no plano novo (o bloco A na Fase 0; B, C e D nas Fases 0, 1 e 3). Os quatro blocos:

- **A. Correções técnicas** — **feito em 2026-11-05** (A1 a A6; detalhes no `diario.md`):
  - testes dos extratos do coletor pulam sem o extrato no bronze (antes falhavam num clone na máquina com os originais);
  - procedência do bronze no git (D-070);
  - README explica os testes que precisam do bronze;
  - `ruff` sem erro;
  - este documento reescrito; pendências antigas resolvidas tiradas do ROADMAP.
  - **Falta o A7:** avaliação do chat com a API real (depois do B1 e do bloco C).
- **B. Decisões e ações do autor:** lista em "O que depende do autor", abaixo.
- **C. Preparar para outros estados:** tirar do código o que só vale para MG (códigos e pacotes por UF nos coletores, `uf = 'MG'` nos contratos e no gold, "fator de MG" na previsão, textos do painel e do chat) e levar para a configuração por estado. Critério de pronto: com `ufs: [MG]`, o resultado idêntico ao de hoje. **Precisa de um plano antes**, a pedido do autor.
- **D. Limpeza:** apagar as branches locais antigas e as referências velhas do remoto (`git fetch --prune`), e decidir o que fazer com o `.claude/launch.json` (configuração do painel para o navegador do Claude; hoje aparece como não versionado): versionar ou pôr no `.gitignore`. Comandos de git só com pedido do autor.

## Números de referência
Carga **2026-11-07** (refeita do silver da carga 2026-10-19: dados coletados em 17 e 18/10; mesmos números da carga 2026-10-28), premissas **v4** (a v3 da D-046 sem o limiar de 3 serventias, D-078), regra base (Classe 1 até R$ 300 mil, Prov. 243), nível base, regra do STF mantida. Esta tabela é a fonte dos valores.

| 1. Serventias ativas | 2. Empregados CLT | 3. Obrigadas (Prov. 227) | 4. Passivo (todas) | 5. Passivo (obrigadas) |
|---|---|---|---|---|
| 2.525 | 12.134 | ≈ 1.121 | R$ 311,9 mi | R$ 238,1 mi |

| 6. Com déficit (esperado) | 7. Déficit | 8. IS do mercado | 9. Prêmio anual | 10. Teto teórico |
|---|---|---|---|---|
| ≈ 148 | R$ 34,1 mi | R$ 17,1 mi | R$ 341,1 mil | R$ 4,76 mi |

Faixa provável do prêmio (P5–P95): R$ 215 a 687 mil. Linha de base: `~/radar_arquivo/baseline_2026-10-28_d048/linha_de_base.json` (WSL). Banco real desta máquina: SHA-256 `7f528a8c…` (carga 2026-11-07; antes, `dd6fc158…` e `c935a190…`).

**Última decisão:** D-078 (D-038, fase 2: sem o limiar de 3 serventias, premissas v4, 2026-11-06); antes, D-077 (Simulador na área "Explorar") e D-076 (aprovação em lote das decisões de MG e das premissas `fonte: suposição`). Não há decisão proposta à espera do autor. As faixas D-053 a D-059 (painel) e D-060 a D-069 (chat) estão reservadas ou usadas; as próximas seguem de D-079 ([`decisoes.md`](decisoes.md)).

## Testes (2026-11-07)
- Suíte padrão (`uv run pytest`): 320 passed. Não usa a API do Gemini nem a internet. `uv run ruff check .`: sem erro.
- Dados reais (`uv run pytest -m dados_reais`, ≈ 25 min, sempre numa cópia do banco): 55 passed, 0 skipped nesta máquina (2026-11-07, depois da carga oficial da D-078; saíram os testes do auditor). Num clone com o modo completo, os de bronze → silver são pulados ("bronze ausente").

## O que depende do autor
1. ~~Trocar a chave do Gemini.~~ Feito em 2026-11-06; a nova responde (conferido pela IA sem exibi-la).
2. ~~Aprovar as decisões propostas pela IA e as premissas `fonte: suposição` de `config/analise.yaml`.~~ Feito em 2026-11-06 (D-076): D-042, D-049, D-051, D-052, D-064, D-069 e D-070 aprovadas; D-039 virou histórico; as 24 premissas aprovadas como estão (continuam marcadas `fonte: suposição`).
3. **STF:** o painel supõe "a regra do Provimento como publicada". Conferir a ADI 8015 na véspera da demo e atualizar `config/painel.yaml`; com liminar, o número principal precisa de aviso.
4. **D-038, fase 2:** aprovada em 2026-11-06 (D-078); falta pedir a carga oficial.
5. ~~Lugar do Simulador.~~ Decidido em 2026-11-06: área "Explorar", separada da história (D-077).
6. **Chat:** conferir os limites da chave no AI Studio; depois do item 1, rodar a avaliação (`uv run python scripts/avaliar_chat.py --versoes c --limite 5`, depois sem `--limite`; Fase 1); publicar no Streamlit Community Cloud com `GEMINI_API_KEY` em *Settings → Secrets* (Fase 2).
7. **Pequenas:** conferir a LGPD do zip do silver público; convidar os colegas e mandar o `CONTRIBUTING.md`; e-mail "noreply" do GitHub nos commits; destino de `docs/qa/depois/`; preencher a "Linha de base" do `diario.md`; apagar a pasta antiga no OneDrive.

As demais pendências técnicas estão no [`historico/ROADMAP.md`](historico/ROADMAP.md), §7.
