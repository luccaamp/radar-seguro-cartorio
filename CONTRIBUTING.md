# Como contribuir

Guia para quem foi convidado a trabalhar no Radar Seguro-Garantia Cartórios. As regras completas do projeto estão em [`CLAUDE.md`](CLAUDE.md) e a especificação em [`docs/SPEC.md`](docs/SPEC.md).

**Antes de tudo, leia o [`docs/entenda_o_projeto.md`](docs/entenda_o_projeto.md):** o problema, o básico de seguro-garantia, as perguntas que o projeto responde e o glossário dos termos técnicos.

## Como pedir acesso

1. Peça ao autor (`luccaamp`) o convite para os dois repositórios:
   - `luccaamp/radar-seguro-cartorio` (código, público): para abrir branches e pull requests;
   - `luccaamp/radar-seguro-cartorio-dados` (dados da equipe, **privado**): para baixar as cargas completas.
2. Aceite os convites (chegam por e-mail e em https://github.com/notifications).
3. Instale o GitHub CLI (https://cli.github.com) e faça login:
   ```
   gh auth login
   ```
4. Instale o `uv` e as dependências (ver README, "Como rodar", passo 1).
5. Clone numa pasta local **sem sincronização** (fora do OneDrive, do Dropbox etc.), de preferência com caminho curto, sem espaço e sem acento. O autor usa `C:\projetos\radar-seguro-cartorio` (D-033): o OneDrive trava pastas e o `.venv` durante a sincronização.

## Dados da equipe

Cada carga oficial é um Release `carga-AAAA-MM-DD` no repositório privado, com todas as camadas, os hashes e as datas de referência no `manifesto.json`. O script baixa, junta as partes, confere **todos** os hashes e só então instala:

```
uv run python scripts/baixar_dados.py --nivel equipe --carga 2026-10-19 --camadas silver
```

Qual camada baixar para cada tarefa:

| Tarefa | Camada | Depois de baixar |
|---|---|---|
| Coletor novo ou mudança num coletor | `bronze` (e o Release `originais-<ano>`, para regerar um extrato) | `uv run pipeline.py --a-partir-de bronze`; `uv run pytest -m dados_reais tests/test_coletores.py` |
| Limpeza (bronze → silver) | `bronze` | `uv run pipeline.py --a-partir-de bronze` |
| Modelo, premissas, gold | `silver` | `uv run pipeline.py --a-partir-de silver` |
| Painel e chat | `banco` (ou `silver` e recalcular) | `uv run streamlit run app/Inicio.py` |

Observações:
- **Tamanhos:** o bronze oficial tem ≈ 78 MB comprimido (só os extratos e o `original.json` de cada fonte, D-032). Os demais: silver ≈ 3 MB, gold completo ≈ 1 MB, banco ≈ 3 MB comprimido. Pacote inteiro: ≈ 85 MB.
- **Originais grandes** (zips do CNPJ, `.7z` da RAIS, `BaseCompleta.zip` da SUSEP), só se a tarefa exigir regerar um extrato:
  - ficam num Release próprio, publicado uma vez (`originais-<ano>`, D-032): `uv run python scripts/baixar_dados.py --nivel originais --ano 2026`;
  - vão para a pasta de originais, fora do projeto (`C:\radar_arquivo\bronze_originais`; `config/pacotes.yaml` ou `RADAR_ORIGINAIS`), e não mexem na carga instalada;
  - os `.COMT` da RAIS não vêm no Release: o coletor os extrai do `.7z` quando faltam.
- O script nunca sobrescreve dados locais. Para trocar, use `--substituir`.
- **Plano B:** se o GitHub estiver fora do ar, o autor pode passar o pacote numa pasta (pendrive ou pasta compartilhada). Instale com `--origem <pasta> --camadas ...`.
- Sem acesso ou sem login, o script explica como pedir.
- Os testes que precisam desses dados são marcados `dados_reais` e ficam fora da suíte padrão. Rode com `uv run pytest -m dados_reais`.

## Fluxo de trabalho

1. **Uma branch por tarefa**, a partir da `main` atualizada:
   ```
   git switch main
   git pull
   git switch -c minha-tarefa
   ```
2. **Pull request** para a `main`. A `main` é protegida: não aceita push direto nem force-push, e o merge é feito pelo autor depois da revisão.
3. **Antes de abrir o PR:**
   - `uv run pytest` passando (e `uv run pytest -m dados_reais`, se você tem os dados da equipe);
   - `uv run ruff check src app tests scripts pipeline.py --exclude scripts/arquivo` sem erro (o padrão do projeto);
   - se mexeu no painel: `uv run python scripts/prints_painel.py --saida docs/qa/atual --checar`, com os prints e o `checagens.md` anexados ao PR (0 falhas de layout);
   - se mudou algum número: explique a cascata no PR (o que mudou, por quê, quanto) e regere o gold público com `uv run python scripts/gerar_publico.py`. O `tests/test_publico.py` avisa quando ele está desatualizado.

## Notebooks

Análise exploratória, mineração de dados e modelos preditivos ficam em `notebooks/` (o que cada um faz: [`docs/plano_mineracao.md`](docs/plano_mineracao.md)):
- **Notebook lê, não escreve:** dados só por `src/notebooks.py` (`conectar()` e `ler()`, somente leitura); nunca gravar em bronze, silver ou gold.
- **Todos os notebooks vão para o git com as saídas** (D-038), inclusive os que leem `interno_*` e mostram resultados por cartório. Se você tinha rodado `uv run nbstripout --install`, desfaça com `uv run nbstripout --uninstall`. Só arquivos grandes (`notebooks/saidas/`) e modelos treinados (`modelos/`) ficam fora do git.
- **Nenhum nome nem CPF de pessoa física** no texto ou nas saídas: identifique o cartório pelo CNS e pelo município (`tests/test_notebooks.py` procura CPF).
- **Código reutilizável** sai do notebook e vai para `src/`, com teste.
- **Abrir:** `uv run jupyter lab`.

## Salvar a conversa com a IA

As conversas ficam gravadas pelo Claude Code em arquivos `.jsonl`. O script `scripts/jsonl_para_md.py` converte um desses arquivos num Markdown legível em `conversas/`, pasta que fica fora do git.

O Markdown traz:
- todas as mensagens do autor e todas as respostas da IA, na ordem, com data e hora de Brasília;
- as ferramentas em uma linha cada, só com a ação, sem o resultado;
- as notificações automáticas e os avisos do editor como notas de uma linha.

Rode os comandos no terminal, dentro da pasta do projeto. O Claude Code guarda as sessões numa pasta cujo nome é o caminho do projeto com `\`, `:`, espaços e acentos trocados por `-`. Para `C:\projetos\radar-seguro-cartorio` (D-033), a pasta é `c--projetos-radar-seguro-cartorio` (conferido em 2026-10-21; confira com `Get-ChildItem "$env:USERPROFILE\.claude\projects"`). As sessões até 2026-10-20 ficam na pasta do caminho antigo, `c--Users-<usuario>-OneDrive--rea-de-Trabalho-Projeto-Nubank`; troque `<usuario>` pelo seu usuário do Windows.

1. Veja qual é o arquivo da conversa. O mais recente aparece primeiro:
   ```powershell
   Get-ChildItem "$env:USERPROFILE\.claude\projects\c--projetos-radar-seguro-cartorio\*.jsonl" | Sort-Object LastWriteTime -Descending | Select-Object Name, LastWriteTime
   ```
2. Converta, trocando `<id>` pelo nome do arquivo e escolhendo o nome da saída e o título:
   ```powershell
   uv run python scripts\jsonl_para_md.py "$env:USERPROFILE\.claude\projects\c--projetos-radar-seguro-cartorio\<id>.jsonl" "conversas\AAAA-MM-DD-nome.md" "Conversa — título"
   ```
3. Faça o backup no disco externo (só copia; não apaga nada no destino):
   ```powershell
   robocopy conversas E:\radar_arquivo\conversas
   ```

O comando de conversão recebe três argumentos, nesta ordem: o `.jsonl` de origem, o `.md` de saída e o título. No fim, ele mostra quantas mensagens, respostas, ferramentas e notificações converteu.

Observações:
- Converta **depois** que a conversa terminar. O `.jsonl` cresce durante a sessão, e uma conversão feita no meio sai incompleta; se acontecer, é só rodar de novo.
- Se o arquivo de saída já existir, ele é substituído.
- O raciocínio interno da IA não fica gravado no `.jsonl`, então não aparece no Markdown.
- Exemplos já gerados: `conversas/2026-10-17-sessao0.md` e `conversas/2026-10-18-fase0.md`.

## Regras do projeto, em resumo

- **Todo número tem fonte e data de referência.** Premissas ficam em `config/`, com fonte. O que não tem fonte leva `fonte: suposição`.
- **Decisões** de interpretação e modelagem vão para `docs/decisoes.md`. Erros da IA vão para `docs/erros_ia.md`. Descobertas, com data, vão para `docs/diario.md`.
- **Arquivos grandes de dados não entram no git** (bronze, banco, pacotes), só pelo tamanho; vão pelos Releases. No git ficam o conjunto público (`data/publico/`, gerado pelo `gerar_publico.py`), as amostras de `data/samples/`, os notebooks com saídas e os gráficos de `docs/qa/analises/`.
- **Ninguém apaga dados:** para retirar algo do bronze, silver ou gold, mova para `C:\radar_arquivo`.
- **Releases:** só o autor publica. Ninguém apaga nem substitui um Release, nem de dados nem de código.
- **Tudo gratuito e local:** nenhum serviço pago, nenhuma conta em nuvem, nenhuma chave de API com créditos.

## Publicação e dados pessoais (D-038)

- É um estudo público, com dados públicos do governo. **Tudo pode ser público**, inclusive as estimativas do modelo por cartório (passivo, déficit, probabilidade, IS, prêmio) e as tabelas `interno_*`.
- **A única restrição:** nenhum nome nem CPF de pessoa física. O bronze bruto do CNJ traz o nome dos responsáveis: ele não vai para lugar público, e nenhum painel, notebook, gráfico ou mensagem mostra esses nomes.
