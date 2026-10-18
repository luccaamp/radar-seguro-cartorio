# CLAUDE.md

Instruções permanentes para a IA que trabalha neste repositório. Leia este arquivo e o `docs/SPEC.md` no início de toda sessão.

## Contexto em uma frase
Projeto de portfólio, 100% gratuito e rodando localmente, com um painel de cartórios do Brasil feito com dados públicos reais, um simulador do mercado de seguro-garantia criado pelo Provimento CNJ 227/2026 e um chat que responde com fontes. A especificação completa está em `docs/SPEC.md`.

## Onde está cada coisa
- `docs/SPEC.md`: especificação completa. É a fonte da verdade sobre escopo, arquitetura e fases.
- `docs/diario.md`: decisões, suposições e limitações, com data. Ler antes de começar e atualizar ao terminar.
- `docs/decisoes.md`: decisões de interpretação e modelagem (contexto, opções, decisão, justificativa, data). Ler antes de mexer em premissas ou regras.
- `docs/erros_ia.md`: erros da IA encontrados e o que foi feito para corrigir.
- `docs/viabilidade.md`: resultado da Fase 0 (criado durante a Fase 0).
- `docs/prompts.md`: pedidos que o autor usa em cada fase.

## Como trabalhar
- Trabalhe **uma fase por vez**, na ordem do SPEC. Pare ao cumprir o critério de aceite da fase e me mostre o resultado antes de seguir.
- Antes de codar algo grande, apresente um plano curto e espere minha confirmação.
- Antes de escrever um coletor, inspecione uma amostra real da fonte e me mostre os campos encontrados.
- Quando algo no SPEC estiver ambíguo ou se mostrar errado na prática, **pergunte** ou proponha a alteração no SPEC. Não decida em silêncio.
- Se uma fonte falhar, proponha o plano B e registre no diário.
- Explique o que vai fazer em linguagem simples. O autor está aprendendo e quer entender cada passo.
- Registre cada erro da IA no docs/erros_ia.md e cada descoberta importante no docs/diario.md no momento em que acontecerem, não no fim da fase. Inclua a correção, inclusive quando ela vier do autor.

## Regras inegociáveis
- **Git: NUNCA rode `git commit`, `git push` ou qualquer comando que altere o histórico ou a branch (`reset`, `rebase`, `merge`, `checkout`, `switch`, `stash`, `tag`) sem eu pedir explicitamente na mensagem atual.** Um pedido anterior não vale para os próximos. Ao terminar uma etapa, apenas avise que há alterações prontas para commit e sugira uma mensagem. Comandos só de leitura (`git status`, `git diff`, `git log`) são permitidos.
- **100% gratuito: NUNCA sugira, instale ou configure serviço pago, conta em nuvem (Google Cloud, AWS, Azure, MotherDuck etc.), chave de API com créditos ou qualquer coisa que possa gerar cobrança.** Se uma etapa parecer exigir isso, pare e me pergunte antes.
- **Dados reais:** os números do painel vêm de fontes oficiais públicas, com data de referência. Dados sintéticos só em `tests/`, marcados como sintéticos.
- Nunca invente valores de premissa, URLs, números de normas ou dados apresentados como reais. Onde não houver fonte, use `fonte: suposição` e me avise.
- Nenhum número fixo no código. Premissas ficam em `config/`, versionadas e com fonte.
- Nenhum nome ou CPF de titular em painel, resposta do chat ou log de saída.
- Arquivos grandes (bronze, banco DuckDB) nunca vão para o git.

## Padrões de código
- Python 3.12, dependências gerenciadas com `uv`.
- Funções de cálculo em `src/model` são puras (sem I/O) e têm teste em `tests/`.
- O LLM é acessado só por `src/llm.py` (Ollama local).
- Rode `pytest` antes de declarar uma fase concluída.

## Ao terminar cada sessão
1. Atualize `docs/diario.md` com o que foi feito, decidido e descoberto.
2. Se a IA errou algo relevante, registre em `docs/erros_ia.md`.
3. Se houver alterações pendentes, liste os arquivos alterados e sugira uma mensagem de commit. **Não faça o commit.**
4. Diga qual é o próximo passo segundo o SPEC.
