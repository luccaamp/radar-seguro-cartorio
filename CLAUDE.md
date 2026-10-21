# CLAUDE.md

Instruções permanentes para a IA que trabalha neste repositório: só regras, sem plano e sem números.
No início de toda sessão, leia nesta ordem: este arquivo → `docs/ESTADO_ATUAL.md` (etapa, ramo, números, pendências) → `docs/ROADMAP.md` (a etapa atual) → `docs/SPEC.md` (a parte que for mexer). A mesma ordem está no `docs/README.md`. Em conflito: CLAUDE.md > ROADMAP > SPEC.

## Contexto em uma frase
Projeto de portfólio, 100% gratuito e rodando localmente, com um painel de cartórios do Brasil feito com dados públicos reais, um simulador do mercado de seguro-garantia criado pelo Provimento CNJ 227/2026 e um chat que responde com fontes. A especificação completa está em `docs/SPEC.md`.

## Onde está cada coisa
O mapa dos documentos (papel, nível e quando ler cada um) está no `docs/README.md`.

## Como trabalhar
- Responda sempre em português.
- Trabalhe **uma etapa por vez**, na ordem do ROADMAP. Pare ao cumprir o critério de pronto da etapa e me mostre o resultado antes de seguir.
- Antes de codar algo grande, apresente um plano curto e espere minha confirmação.
- Antes de escrever um coletor, inspecione uma amostra real da fonte e me mostre os campos encontrados.
- Quando algo no SPEC estiver ambíguo ou se mostrar errado na prática, **pergunte** ou proponha a alteração no SPEC. Não decida em silêncio.
- Se uma fonte falhar, proponha o plano B e registre no diário.
- Explique o que vai fazer em linguagem simples. O autor está aprendendo e quer entender cada passo.
- Edite código só com a ferramenta de edição de arquivos, nunca por script de substituição de texto (uma edição por script já falhou sem aviso; ver docs/erros_ia.md).
- Registre cada erro da IA no docs/erros_ia.md e cada descoberta importante no docs/diario.md no momento em que acontecerem, não no fim da etapa. Inclua a correção, inclusive quando ela vier do autor.

## Regras inegociáveis
- **Git: NUNCA rode `git commit`, `git push` ou qualquer comando que altere o histórico ou a branch (`reset`, `rebase`, `merge`, `checkout`, `switch`, `stash`, `tag`) sem eu pedir explicitamente na mensagem atual.** Um pedido anterior não vale para os próximos. Ao terminar uma etapa, apenas avise que há alterações prontas para commit e sugira uma mensagem. Comandos só de leitura (`git status`, `git diff`, `git log`) são permitidos. **Também nunca** rode comandos do `gh` que criem, alterem ou apaguem algo (`gh release create/upload/delete/edit`, `gh repo edit/create/delete`, `gh pr merge`, `gh api` com escrita). Leitura (`gh repo view`, `gh release list`, `gh auth status`) é permitida. Quem publica é o autor.
- **100% gratuito: NUNCA sugira, instale ou configure serviço pago, conta em nuvem (Google Cloud, AWS, Azure, MotherDuck etc.), chave de API com créditos ou qualquer coisa que possa gerar cobrança.** Se uma etapa parecer exigir isso, pare e me pergunte antes.
- **Dados reais:** os números do painel vêm de fontes oficiais públicas, com data de referência. Dados sintéticos só em `tests/`, marcados como sintéticos.
- Nunca invente valores de premissa, URLs, números de normas ou dados apresentados como reais. Onde não houver fonte, use `fonte: suposição` e me avise.
- Nenhum número fixo no código. Premissas ficam em `config/`, versionadas e com fonte.
- Nenhum nome, CPF, e-mail ou telefone de pessoa física em painel, resposta do chat ou log de saída.
- **Mínimo de 3 serventias:** toda estimativa publicada por área (município ou região) só aparece se a área tiver ≥ 3 serventias e passar no auditor de ataque por diferença (D-026, D-027); áreas menores são agregadas pela região imediata ou intermediária. Partições internas da mesma visão seguem a D-028.
- **Público (repositório e Release públicos):** nenhuma ESTIMATIVA do modelo no nível de serventia (passivo, déficit, probabilidade, IS, prêmio); dados de origem já publicados pelas fontes oficiais (CNJ, RAIS/PDET, Receita, IBGE, SUSEP) podem ir, desde que sem dado pessoal (D-030).
- Arquivos grandes (bronze, banco DuckDB) nunca vão para o git.
- **Pacote da equipe:** `interno_*`, banco `.duckdb` e o pacote da equipe só existem localmente ou no repositório privado `radar-seguro-cartorio-dados` (D-030). Nunca no repositório público, em issues, PRs, prints ou serviços externos (inclusive IAs online).
- **Disco e pastas:** o projeto fica em `C:\projetos\radar-seguro-cartorio`, **fora do OneDrive** (D-033; antes ficava no OneDrive). Arquivos grandes gerados (pacotes, cópias de bronze, arquivos de backup) continuam em pastas **fora do projeto** (ex.: `C:\radar_pacotes`, `C:\radar_arquivo`), e nada do projeto volta para o OneDrive. Nunca apagar dado do bronze, silver ou gold sem aprovação explícita; para retirar, **mover** para `C:\radar_arquivo`.
- Painel e chat só leem tabelas públicas; `gold.interno_*` (e qualquer `interno_*`) é proibido fora do pipeline (testado em `tests/test_app_codigo.py`).
- **A IA roda testes e pipeline sempre numa cópia do banco;** a carga oficial no `data/radar.duckdb` real só com pedido explícito do autor na mensagem atual.

## Padrões de código
- Python 3.12, dependências gerenciadas com `uv`.
- Funções de cálculo em `src/model` são puras (sem I/O) e têm teste em `tests/`.
- O LLM é acessado só por `src/llm.py` (Ollama local).
- **Notebooks** (`notebooks/`): leem e não escrevem (dados só por `src/notebooks.py`, somente leitura; nunca gravar em bronze, silver ou gold); saídas sempre limpas antes do commit (`nbstripout`; `tests/test_notebooks.py`); notebook que usa `interno_*` só em `notebooks/privado/` (fora do git); código reutilizável vai para `src/` com teste.
- Lint padrão: `uv run ruff check src app tests scripts pipeline.py --exclude scripts/arquivo`.
- Antes de declarar uma etapa concluída, rode as suítes do ROADMAP §3: a padrão (`uv run pytest`), a `dados_reais` (`uv run pytest -m dados_reais`) e a `visual` (`uv run pytest -m visual`) quando o painel mudar.

## Ao terminar cada sessão
1. Atualize `docs/diario.md` com o que foi feito, decidido e descoberto, e atualize `docs/ESTADO_ATUAL.md`.
2. Se a IA errou algo relevante, registre em `docs/erros_ia.md`.
3. Se houver alterações pendentes, liste os arquivos alterados e sugira uma mensagem de commit. **Não faça o commit.**
4. Diga qual é o próximo passo segundo o ROADMAP.
