# Pedidos por fase

> **Histórico.** Superado pelo ROADMAP (D-035). Não usar os pedidos por fase: a ordem mudou. O procedimento de salvar conversas foi para o `CONTRIBUTING.md`.

Pedidos prontos para usar com a IA. Abra uma conversa nova para cada fase: o SPEC, o CLAUDE.md e o diário carregam o contexto.

---

## Fase 0: viabilidade (testar se os dados existem)

> Leia @CLAUDE.md, @docs/SPEC.md e @docs/diario.md e execute só a Fase 0.
> Explique em linguagem simples o que vai fazer antes de cada etapa.
> 1. Instale o uv e o Python 3.12 pelo uv.
> 2. Veja a RAM e a GPU do computador e me diga qual modelo do Ollama você recomenda. Se eu precisar instalar o Ollama, me diga como.
> 3. Baixe os Provimentos 227, 213 e 243 e confirme os pontos listados na Fase 0.
> 4. Teste cada fonte do §1.1, salve uma amostra pequena em data/samples/ e me mostre os campos encontrados.
> 5. Crie docs/viabilidade.md com uma linha por fonte.
> Pare e me mostre o resultado antes de qualquer decisão que mude o SPEC.

---

## Fase 1: painel de MG

> Execute só a Fase 1 do SPEC, usando as decisões de docs/viabilidade.md e do diário.
> Antes de codar, me mostre o plano: arquivos que vai criar, tabelas e funções do modelo.
> Comece pelas funções de src/model com testes, depois a ingestão de MG, depois as páginas Mercado, Simulador e Qualidade dos dados.
> Pare quando o critério de aceite da Fase 1 for cumprido e me diga como abrir o painel.

---

## Fase 2: Brasil inteiro e qualidade

> Execute só a Fase 2 do SPEC. Expanda para todas as UFs disponíveis e implemente as reconciliações do §4.
> Me mostre as divergências encontradas entre as fontes.

---

## Fase 3: chat

> Execute só a Fase 3 do SPEC.
> Primeiro passo: me ajude a montar eval/gabarito_chat.csv com perguntas dos 4 tipos. Eu confirmo as respostas esperadas. Não ajuste o prompt do chat antes de eu congelar o gabarito.

(depois do gabarito congelado)

> O gabarito está congelado. Implemente as ferramentas, a integração com o Ollama e a página Chat. Rode o eval das versões e me mostre a comparação.

---

## Fase 4: radar (opcional)

> Execute só a Fase 4 do SPEC, começando pela versão simples sem IA.

---

## Fase 5: entrega

> Execute a Fase 5 do SPEC: README completo e relatório final do eval.
> Separe do docs/erros_ia.md os 2 ou 3 casos mais interessantes para os slides e me explique por quê.

---

## Pedidos úteis a qualquer momento

- **Retomar:** "Leia o CLAUDE.md, o SPEC e o diário. Em que ponto estamos e qual é o próximo passo?"
- **Entender:** "Me explique em linguagem simples o que você acabou de fazer e por quê."
- **Revisar:** "Revise o que foi feito nesta fase contra o critério de aceite do SPEC. O que falta ou está frágil?"
- **Fechar a sessão:** "Atualize o diário e o erros_ia.md com o que aconteceu nesta sessão. Não faça commit."

---

## Salvar a conversa ao fim de cada fase

As conversas ficam gravadas pelo Claude Code em arquivos `.jsonl`. O script `scripts/jsonl_para_md.py` converte um desses arquivos num Markdown legível em `conversas/`, pasta que fica fora do git.

O Markdown traz:
- todas as mensagens do autor e todas as respostas da IA, na ordem, com data e hora de Brasília;
- as ferramentas em uma linha cada, só com a ação, sem o resultado;
- as notificações automáticas e os avisos do editor como notas de uma linha.

Rode os comandos no terminal, dentro da pasta do projeto. O Claude Code guarda as sessões numa pasta cujo nome é o caminho do projeto com `\`, `:`, espaços e acentos trocados por `-`. No caso do autor, o caminho é `C:\projetos\radar-seguro-cartorio` (D-033), e a pasta fica como nos comandos abaixo (confira o nome exato com `Get-ChildItem "$env:USERPROFILE\.claude\projects"`; a letra do disco pode vir minúscula). As sessões até 2026-10-20 ficam na pasta do caminho antigo, `c--Users-<usuario>-OneDrive--rea-de-Trabalho-Projeto-Nubank`; troque `<usuario>` pelo seu usuário do Windows.

1. Veja qual é o arquivo da conversa. O mais recente aparece primeiro:
   ```powershell
   Get-ChildItem "$env:USERPROFILE\.claude\projects\c--projetos-radar-seguro-cartorio\*.jsonl" | Sort-Object LastWriteTime -Descending | Select-Object Name, LastWriteTime
   ```
2. Converta, trocando `<id>` pelo nome do arquivo e escolhendo o nome da saída e o título:
   ```powershell
   uv run python scripts\jsonl_para_md.py "$env:USERPROFILE\.claude\projects\c--projetos-radar-seguro-cartorio\<id>.jsonl" "conversas\AAAA-MM-DD-nome.md" "Conversa — título"
   ```

O comando recebe três argumentos, nesta ordem: o `.jsonl` de origem, o `.md` de saída e o título. No fim, ele mostra quantas mensagens, respostas, ferramentas e notificações converteu.

Observações:
- Converta **depois** que a conversa terminar. O `.jsonl` cresce durante a sessão, e uma conversão feita no meio sai incompleta; se acontecer, é só rodar de novo.
- Se o arquivo de saída já existir, ele é substituído.
- O raciocínio interno da IA não fica gravado no `.jsonl`, então não aparece no Markdown.
- Exemplos já gerados: `conversas/2026-10-17-sessao0.md` e `conversas/2026-10-18-fase0.md`.

---

## Fase 1 — documentos de pedido usados (registro, acrescentado em 2026-10-19)

A Fase 1 foi conduzida por documentos de pedido escritos pelo autor (e um de resposta da IA), lidos inteiros pela IA a cada rodada. Caminho final: `docs/historico/`, depois da limpeza (`docs/limpeza_projeto.md`, Etapa 2; até lá, os arquivos estão em `docs/`). O `plano_qualidade_e_correcoes.md` continua em `docs/`, porque o Bloco 2 ainda será executado.

| Ordem | Data | Documento (caminho final) | Objetivo |
|---|---|---|---|
| 1 | 2026-10-18 | `docs/historico/revisao_fase1.md` | Revisão crítica do painel aberto (carga das 09:52, premissas v1), blocos A a E. |
| 2 | 2026-10-18 | `docs/historico/verificacao_final_fase1.md` | Verificação de fechamento: bloco F, conferência contra o CSV do BI do CNJ; só leitura, com [VERIFICAR]. |
| 3 | 2026-10-18 | `docs/historico/resposta_verificacao_final_fase1.md` | Resposta da IA aos dois documentos acima (medições e propostas D-019 a D-025), sem implementar nada. |
| 4 | 2026-10-18 | `docs/historico/aprovacao_etapa1_fase1.md` | Aprovação item a item das propostas e execução da Etapa 1 dos ajustes finais. |
| 5 | 2026-10-18 | `docs/plano_qualidade_e_correcoes.md` (fica em `docs/`) | Plano de correções e qualidade; Bloco 1 executado (tela e engenharia, sem mudar número); Bloco 2 pendente. |
| 6 | 2026-10-18 | `docs/historico/revisao_painel_filtros.md` | Revisão do painel com filtros: decisões D-026/D-027, erros E1 a E10, U1, auditoria própria. |
| 7 | 2026-10-18 | (`auditoria_painel_v3.md`, substituído e não executado; não está no projeto) | — |
| 8 | 2026-10-18/19 | `docs/historico/correcoes_e_qa_visual.md` | Aprovações (D-027, D-028), correções C1 a C4 e QA visual automático (Playwright e axe). |
| 9 | 2026-10-19 | `docs/historico/repositorio_reproduzivel.md` | Repositório reproduzível: conjunto público, modo demonstração, pacotes de dados (D-029, D-030). |
| 10 | 2026-10-19 | `docs/historico/limpeza_projeto.md` | Ajustes finais (D-031, registro da Fase 1, `ESTADO_ATUAL.md`) e limpeza do projeto em duas paradas. |

### Mensagens curtas de envio mais usadas
- "Leia @docs/X.md por inteiro. Execute somente o BLOCO 1 e pare na Parada 1 com o relatório pedido. Não comece o Bloco 2. Nada de commit ou push."
- "Leia @docs/X.md por inteiro. Ele substitui o Y.md (não execute aquele). Siga a ordem: … → relatório da seção 6. Nada de commit ou push. Não comece o Bloco 2."
- "Leia @docs/X.md por inteiro antes de começar. Comece respondendo ao [VERIFICAR] da seção N. Depois execute a etapa na ordem da seção M, respeitando os pontos de parada. Nada de commit ou push. No fim, entregue o relatório da seção K e PARE."
- "Peça aprovação antes de instalar qualquer pacote." / "Peça minha aprovação antes de converter as conversas."
- Pendências da rodada anterior no começo da mensagem, numeradas, antes do "Leia @docs/…" ("Antes de tudo, as pendências da rodada anterior: 1. … 2. … 3. …").
