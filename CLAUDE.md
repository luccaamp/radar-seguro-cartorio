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
- Nunca apagar dado do bronze, silver ou gold sem aprovação explícita; para retirar, **mover** para `C:\radar_arquivo`. Arquivos grandes (bronze, banco, pacotes) nunca vão para o git e ficam fora do OneDrive.
- Edite código só com a ferramenta de edição de arquivos, nunca por script de substituição de texto (`docs/erros_ia.md`).

## LGPD
- Nenhum nome, CPF, e-mail ou telefone de pessoa física em painel, resposta do chat, notebook ou log de saída.
- **Mínimo de 3 serventias:** toda estimativa publicada por área só aparece se a área tiver 3 ou mais serventias e passar no auditor de ataque por diferença (D-026, D-027); partições internas da mesma visão seguem a D-028.
- **Público (repositório e Release públicos):** nenhuma ESTIMATIVA do modelo no nível de serventia (passivo, déficit, probabilidade, IS, prêmio); dados de origem já publicados pelas fontes oficiais podem ir, sem dado pessoal (D-030).
- **Pacote da equipe:** `interno_*`, o banco `.duckdb` e o pacote da equipe só existem localmente ou no repositório privado `radar-seguro-cartorio-dados` (D-030). Nunca no repositório público, em issues, PRs, prints ou serviços externos (inclusive IAs online).
- Painel e chat só leem tabelas públicas; `interno_*` é proibido fora do pipeline e dos notebooks (`tests/test_app_codigo.py`, `tests/test_chat.py`).
- **Notebooks:** todos vão para o git, **sem saídas** (`nbstripout`; `tests/test_notebooks.py`) e **sem citar um cartório específico** (nome, CNS ou valor de um cartório) no texto; interpretações só com números agregados (D-037).
