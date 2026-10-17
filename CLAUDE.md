# CLAUDE.md

Instruções permanentes para a IA que trabalha neste repositório. Leia este arquivo e o `docs/SPEC.md` no início de toda sessão.

## Contexto em uma frase
Projeto de portfólio que estima, só com dados públicos, o mercado de seguro-garantia criado pelo Provimento CNJ 227/2026 para cartórios, com radar regulatório e chat com fontes. A especificação completa está em `docs/SPEC.md`.

## Onde está cada coisa
- `docs/SPEC.md`: especificação completa. É a fonte da verdade sobre escopo, arquitetura e fases.
- `docs/diario.md`: decisões, suposições e limitações, com data. Ler antes de começar e atualizar ao terminar.
- `docs/erros_ia.md`: erros da IA encontrados e o que foi feito para corrigir.
- `docs/viabilidade.md`: resultado da Fase 0 (criado durante a Fase 0).

## Como trabalhar
- Trabalhe **uma fase por vez**, na ordem do SPEC. Pare ao cumprir o critério de aceite da fase e me mostre o resultado antes de seguir.
- Antes de codar algo grande, apresente um plano curto e espere minha confirmação.
- Antes de escrever um coletor, inspecione uma amostra real da fonte e me mostre os campos encontrados.
- Quando algo no SPEC estiver ambíguo ou se mostrar errado na prática, **pergunte** ou proponha a alteração no SPEC. Não decida em silêncio.
- Se uma fonte falhar, proponha o plano B e registre no diário.

## Regras inegociáveis
- Nunca invente valores de premissa, URLs, números de normas ou dados apresentados como reais. Onde não houver fonte, use `fonte: suposição` e me avise.
- Nenhum número fixo no código. Premissas ficam em `config/`, versionadas e com fonte.
- Dados sintéticos só em `tests/`, marcados como sintéticos.
- Nenhum nome ou CPF de titular em dashboard, resposta do chat ou log de saída.
- Nunca commitar segredos. Chaves ficam no `.env` (fora do git); o modelo está em `.env.example`.
- O estado (eventos, aprovações, cenários) vai para o armazenamento persistente definido na Fase 0, nunca para o disco do runner ou do Streamlit.

## Padrões de código
- Python 3.12, dependências gerenciadas com `uv`.
- Funções de cálculo em `src/model` são puras (sem I/O) e têm teste em `tests/`.
- Rode `pytest` antes de declarar uma fase concluída.
- Commits pequenos e com mensagem descritiva em português.

## Ao terminar cada sessão
1. Atualize `docs/diario.md` com o que foi feito, decidido e descoberto.
2. Se a IA errou algo relevante, registre em `docs/erros_ia.md`.
3. Diga qual é o próximo passo segundo o SPEC.
