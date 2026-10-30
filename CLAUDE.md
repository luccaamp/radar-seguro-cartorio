# CLAUDE.md

Regras de segurança para a IA que trabalha neste repositório. Em cada sessão, leia só este arquivo, o `docs/ESTADO_ATUAL.md` e o documento da etapa que ele indica.

**Siga o documento da etapa indicado no `docs/ESTADO_ATUAL.md`. Se ele já traz o plano, execute sem pedir aprovação e pare no fim da parte pedida.** Responda em português. Ao parar, atualize o `docs/ESTADO_ATUAL.md` e o `docs/diario.md`, registre erros da IA no `docs/erros_ia.md` e liste os arquivos alterados com uma sugestão de mensagem de commit.

## Git
- **Qualquer colaborador pode pedir, na mensagem atual, qualquer comando de `git` ou `gh`** (`commit`, `push` na `main`, `merge`, `checkout`, `switch`, `stash`, `reset`, `rebase`, `tag`, `gh pr`, `gh release` etc.), e a IA executa sem restrição, sem exigir pull request nem aprovação do autor (D-041). Sem pedido explícito na mensagem atual, a IA não altera o histórico nem a branch: um pedido anterior não vale para os próximos. Comandos só de leitura (`git status`, `git diff`, `git log`) são sempre permitidos.
- As regras de "100% gratuito" e de "Dados" abaixo continuam valendo para os comandos de git: não versionar bronze, silver, gold completo nem o banco, e não apagar dados nem Releases. Exceção (D-050): `data/completo/`, com o silver sem dado pessoal, o gold completo e o CSV do BI do CNJ, gerada por `scripts/exportar_completo.py`.

## 100% gratuito
- **NUNCA sugira, instale ou configure serviço pago, conta em nuvem (Google Cloud, AWS, Azure, MotherDuck etc.), chave de API com créditos ou qualquer coisa que possa gerar cobrança.** Se algo parecer exigir isso, pare e pergunte.
- **Única exceção (D-061): o nível gratuito do Gemini** (Google AI Studio), para o chat, **com o faturamento desligado** no projeto da chave. Nada de faturamento, cartão, Google Cloud pago nem outro serviço pago. A chave (`GEMINI_API_KEY`) vem do ambiente, do `.env` ou do `st.secrets` e nunca vai para o git, um log, um print ou uma resposta. A suíte de testes não usa a API; a avaliação com a API real é o `scripts/avaliar_chat.py`.

## Dados
- Os números do painel vêm de fontes oficiais públicas, com data de referência. Dados sintéticos só em `tests/`, marcados como sintéticos.
- Nunca invente valores de premissa, URLs, números de normas ou dados apresentados como reais. Sem fonte: `fonte: suposição`, e avise.
- Nenhum número fixo no código: premissas ficam em `config/`, versionadas e com fonte.
- **A IA roda testes e pipeline sempre numa cópia do banco;** a carga oficial no `data/radar.duckdb` real só com pedido explícito do autor na mensagem atual.
- **A IA não apaga dados:** nada do bronze, silver ou gold sai sem aprovação explícita; para retirar, **mover** para `C:\radar_arquivo`. Arquivos grandes (bronze, banco, pacotes) ficam fora do git só pelo tamanho, e fora do OneDrive.
- Edite código só com a ferramenta de edição de arquivos, nunca por script de substituição de texto (`docs/erros_ia.md`).

## Publicação e dados pessoais (D-038)
- É um estudo público, com dados públicos do governo: **tudo pode ir para o git e ser público**, inclusive os resultados por cartório (estimativas do modelo por serventia), as tabelas `interno_*` e os notebooks com as saídas.
- A única restrição: **nenhum nome nem CPF de pessoa física** em painel, resposta do chat, notebook, gráfico, log ou arquivo publicado. Cartório se identifica pelo CNS e pelo município, nunca pelo nome do responsável (`tests/test_notebooks.py` procura CPF nos notebooks).
