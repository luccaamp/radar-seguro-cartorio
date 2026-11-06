# Estado atual do projeto

> Leia primeiro. Atualizado ao fim de cada sessão (regra do `CLAUDE.md`). Última atualização: **2026-11-05**.
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

## Etapa atual: Fase 0 (Fundamentos)
**Plano oficial: [`plano_projeto.md`](plano_projeto.md) (D-071, 2026-11-05)**, com 10 fases, de MG completo ao Brasil inteiro publicado e atualizado sozinho. A IA propõe cada passo e segue com a aprovação do autor.

**Fase 0, andamento (2026-11-05):**
- [x] item 1: plano novo (D-071) e SPEC, ROADMAP, `CLAUDE.md` e `CONTRIBUTING.md` alinhados;
- [x] item 2: D-072 (GitHub Actions, Hugging Face, Kaggle), D-073 (branch por bloco e pull request; substitui o push direto da D-041) e D-074 (Streamlit Community Cloud), aprovadas;
- [ ] item 3: decisões pendentes de MG em lote;
- [ ] item 4: trocar a chave do Gemini (autor);
- [ ] item 5: CI no GitHub Actions;
- [ ] item 6: bloco A e estes documentos na `main` (branch `fechamento-mg-a`, sem commit).

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
Carga **2026-10-28 (tarde)** (refeita do silver da carga 2026-10-19: dados coletados em 17 e 18/10), premissas **v3** (D-046), regra base (Classe 1 até R$ 300 mil, Prov. 243), nível base, regra do STF mantida. Esta tabela é a fonte dos valores.

| 1. Serventias ativas | 2. Empregados CLT | 3. Obrigadas (Prov. 227) | 4. Passivo (todas) | 5. Passivo (obrigadas) |
|---|---|---|---|---|
| 2.525 | 12.134 | ≈ 1.121 | R$ 311,9 mi | R$ 238,1 mi |

| 6. Com déficit (esperado) | 7. Déficit | 8. IS do mercado | 9. Prêmio anual | 10. Teto teórico |
|---|---|---|---|---|
| ≈ 148 | R$ 34,1 mi | R$ 17,1 mi | R$ 341,1 mil | R$ 4,76 mi |

Faixa provável do prêmio (P5–P95): R$ 215 a 687 mil. Linha de base: `~/radar_arquivo/baseline_2026-10-28_d048/linha_de_base.json` (WSL). Banco real desta máquina: SHA-256 `c935a190…`.

**Última decisão:** D-074 (painel no Streamlit Community Cloud); D-071 a D-074 aprovadas em 2026-11-05; D-070 (procedência do bronze no git) ainda proposta. As faixas D-053 a D-059 (painel) e D-060 a D-069 (chat) estão reservadas ou usadas; as próximas seguem de D-075 ([`decisoes.md`](decisoes.md)).

## Testes (2026-11-05)
- Suíte padrão (`uv run pytest`): 315 passed. Não usa a API do Gemini nem a internet. `uv run ruff check .`: sem erro.
- Dados reais (`uv run pytest -m dados_reais`, ≈ 25 min, sempre numa cópia do banco): 57 passed nesta máquina (2026-10-31). Num clone com o modo completo, os de bronze → silver são pulados ("bronze ausente").

## O que depende do autor
1. **Trocar a chave do Gemini** (revogar a atual e criar outra no AI Studio): ela apareceu na saída de um comando da IA em 2026-10-28 (`erros_ia.md`). É a mais urgente.
2. **Aprovar ou ajustar as decisões propostas pela IA:** D-039 (plano do projeto), D-042 (faixa do prêmio e sensibilidades), D-049 (limite fixo na projeção, extremos, Simulador só com o tema), D-051 (painel em torno de uma pergunta; Simulador fora da navegação), D-052 (visual), D-064 (normas sem a assinatura), D-069 (ajustes do chat), D-070 (procedência no git). Questões abertas de cada uma: no [`historico/ESTADO_ATUAL_ate_2026-10-31.md`](historico/ESTADO_ATUAL_ate_2026-10-31.md), "O que depende do autor agora".
3. **Aprovar as premissas com `fonte: suposição`** em `config/analise.yaml`: cortes do Apriori, `n_init`, limiar 0,5, permutação, bootstrap, faixa P10–P90; seção `previsao`; seção `melhorias` (horizonte de 12 meses de saldo, base das premissas v3, e tercis da M4).
4. **STF:** o painel supõe "a regra do Provimento como publicada". Conferir a ADI 8015 na véspera da demo e atualizar `config/painel.yaml`; com liminar, o número principal precisa de aviso.
5. **D-038, fase 2:** tirar o limiar de 3 serventias e as áreas agregadas (premissas v4, mudança no pipeline e carga oficial).
6. **Etapa 4 (Simulador):** volta para a navegação, com o redesenho planejado, ou fica fora (D-051)?
7. **Chat:** conferir os limites da chave no AI Studio; depois do item 1, rodar a avaliação (`uv run python scripts/avaliar_chat.py --versoes c --limite 5`, depois sem `--limite`); publicar no Streamlit Community Cloud com `GEMINI_API_KEY` em *Settings → Secrets*.
8. **Pequenas:** conferir a LGPD do zip do silver público; convidar os colegas e mandar o `CONTRIBUTING.md`; e-mail "noreply" do GitHub nos commits; destino de `docs/qa/depois/`; preencher a "Linha de base" do `diario.md`; apagar a pasta antiga no OneDrive.

As demais pendências técnicas estão no [`historico/ROADMAP.md`](historico/ROADMAP.md), §7.
