# CLAUDE.md

Regras de segurança para a IA que trabalha neste repositório. Em cada sessão, leia só este arquivo, o `docs/ESTADO_ATUAL.md` e o documento da etapa que ele indica.

**Siga o documento da etapa indicado no `docs/ESTADO_ATUAL.md`. Se ele já traz o plano, execute sem pedir aprovação e pare no fim da parte pedida.** Responda em português. Ao parar, atualize o `docs/ESTADO_ATUAL.md` e o `docs/diario.md`, registre erros da IA no `docs/erros_ia.md` e liste os arquivos alterados com uma sugestão de mensagem de commit.

## Git
- **NUNCA rode `git commit`, `git push` ou qualquer comando que altere o histórico ou a branch (`reset`, `rebase`, `merge`, `checkout`, `switch`, `stash`, `tag`) sem pedido explícito do autor na mensagem atual.** Um pedido anterior não vale para os próximos. Comandos só de leitura (`git status`, `git diff`, `git log`) são permitidos.
- **Nunca** rode comandos do `gh` que criem, alterem ou apaguem algo (`gh release create/upload/delete/edit`, `gh repo edit/create/delete`, `gh pr merge`, `gh api` com escrita). Leitura é permitida. Quem publica é o autor.

## 100% gratuito
- **NUNCA sugira, instale ou configure serviço pago, conta em nuvem (Google Cloud, AWS, Azure, MotherDuck etc.), chave de API com créditos ou qualquer coisa que possa gerar cobrança.** Se algo parecer exigir isso, pare e pergunte.

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
