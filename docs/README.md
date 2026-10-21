# Índice da documentação

Mapa dos documentos do projeto: o que é cada um e se é **vivo** (muda com o projeto) ou **histórico** (registro de uma época, não se reescreve). Os papéis e os níveis foram definidos na D-035.

## Ordem de leitura para quem chega agora

**Pessoa** (colega, avaliador):
1. [`../README.md`](../README.md): o que é o projeto e como rodar o painel.
2. Este índice.
3. [`ESTADO_ATUAL.md`](ESTADO_ATUAL.md): onde o projeto está agora.
4. [`ROADMAP.md`](ROADMAP.md): as etapas e o que cada uma entrega.
5. [`SPEC.md`](SPEC.md), §0: o problema e as normas.
6. Se for trabalhar no código: [`../CONTRIBUTING.md`](../CONTRIBUTING.md).

**IA** (início de toda sessão):
1. [`../CLAUDE.md`](../CLAUDE.md): as regras.
2. [`ESTADO_ATUAL.md`](ESTADO_ATUAL.md): etapa atual, ramo, números e o que depende do autor.
3. [`ROADMAP.md`](ROADMAP.md): a etapa atual e o que ela pede.
4. [`SPEC.md`](SPEC.md): o desenho técnico da parte que vai mexer.
5. [`decisoes.md`](decisoes.md) antes de mexer em premissa ou regra; o fim do [`diario.md`](diario.md) e do [`erros_ia.md`](erros_ia.md).

## Em caso de conflito

**`CLAUDE.md` > `ROADMAP.md` > `SPEC.md`.** As regras da IA valem acima de tudo; o roteiro decide etapas e ordem; o SPEC decide o desenho técnico. Os demais documentos registram ou detalham, e não mudam essas três fontes sem decisão no `decisoes.md`. Ao fechar cada etapa, antes do commit, a IA verifica contradições entre os documentos dos níveis 1 e 2.

## Nível 1 — Núcleo (lido no início de toda sessão; vivos)

| Documento | O que é |
|---|---|
| [`../CLAUDE.md`](../CLAUDE.md) | Regras permanentes da IA: como trabalhar, regras inegociáveis (git, gratuito, dados reais, LGPD, pastas, cópia do banco), padrões de código. Sem plano e sem números. Só o autor muda; a IA propõe. |
| [`ESTADO_ATUAL.md`](ESTADO_ATUAL.md) | A foto de agora: etapa e ramo atuais, próximo passo, os valores dos 10 números (fonte dos valores) e o que depende do autor. |
| [`ROADMAP.md`](ROADMAP.md) | O plano: etapas E1 a E7 (e o Radar, opcional), ordem, entregáveis, critério de pronto, decisões do autor, entrega por marco, cascata dos números e as pendências. |

## Nível 2 — Referência (consultada quando a etapa toca no assunto; vivos)

| Documento | O que é |
|---|---|
| [`SPEC.md`](SPEC.md) | Desenho técnico: problema e normas (§0), fontes (§1), arquitetura (§2), modelo (§3), qualidade (§4), painel e chat (§5), LGPD (§6), avaliação (§7), riscos (§10). |
| [`decisoes.md`](decisoes.md) | Decisões D-001 em diante (contexto, opções, decisão, justificativa, data). Só acrescenta: as antigas não são editadas. |
| [`dicionario_dados.md`](dicionario_dados.md) | Tabelas do banco (silver, gold, qualidade, estado), o conjunto público e o arquivo de cenários do painel, com as colunas e o que é público. |
| [`plano_qualidade_e_correcoes.md`](plano_qualidade_e_correcoes.md) | Plano do autor com os itens Q1 a Q11 (E1) e S1 a S6 (E2). Só na E1 e na E2; vira histórico depois. |

## Nível 3 — Registros (só acrescentam; vivos)

| Documento | O que é |
|---|---|
| [`diario.md`](diario.md) | Diário cronológico: o que foi feito, decidido e descoberto, com data. Entradas novas no fim. |
| [`erros_ia.md`](erros_ia.md) | Erros da IA e do revisor e as correções; fonte do slide "onde a IA errou". |

## Nível 4 — Pontuais (consultados para uma tarefa específica; vivos)

| Documento | O que é |
|---|---|
| [`publicacao.md`](publicacao.md) | Passo a passo do autor para os Releases, a `main` protegida, a entrada da equipe e o checklist de nova carga. |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Como a equipe trabalha: acesso, dados da equipe, ramos e PRs, notebooks, salvar a conversa com a IA, LGPD. |
| [`../README.md`](../README.md) | Para o público: o projeto, como rodar e o roteiro de conferência do painel. |
| [`../notebooks/README.md`](../notebooks/README.md) | Regras dos notebooks (só leitura, saídas limpas, `interno_*` só em `notebooks/privado/`). |
| `README.md` (este índice) | Papéis, níveis e ordem de leitura dos documentos (o `tests/test_links_docs.py` confere que todos estão aqui). |

## Históricos (`historico/`; não se reescrevem)

| Documento | O que é |
|---|---|
| [`historico/INDICE.md`](historico/INDICE.md) | Índice da pasta de histórico, com a data e o objetivo de cada documento (todos os arquivos da pasta estão lá; o `tests/test_links_docs.py` confere). |
| [`historico/viabilidade.md`](historico/viabilidade.md) | Resultado da Fase 0; ainda consultado na E2 (SES), na E5 (modelo do Ollama), na E6 (totais do Brasil) e na E7 (planos B das fontes). |

## Pastas fora do git

| Pasta | O que é |
|---|---|
| `docs/qa/` | QA visual: `atual/` (galeria vigente, a referência de comparação), `depois/` (galeria de uma rodada anterior, destino a decidir; ROADMAP §7), `acessibilidade.md` e os relatórios dos testes. Gerada por `scripts/prints_painel.py` e `scripts/acessibilidade.py`. |
| `conversas/` | Transcrições das conversas com a IA, para uso pessoal do autor (procedimento no `CONTRIBUTING.md`; backup em `E:\radar_arquivo\conversas`). Histórico. |
