# Como contribuir

Guia para quem foi convidado a trabalhar no Radar Seguro-Garantia Cartórios. As regras completas do projeto estão em [`CLAUDE.md`](CLAUDE.md) e a especificação em [`docs/SPEC.md`](docs/SPEC.md).

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

## Dados da equipe

Cada carga oficial é um Release `carga-AAAA-MM-DD` no repositório privado, com todas as camadas, os hashes e as datas de referência no `manifesto.json`. O script baixa, junta as partes, confere **todos** os hashes e só então instala:

```
uv run python scripts/baixar_dados.py --nivel equipe --carga 2026-10-19 --camadas silver
```

Qual camada baixar para cada tarefa:

| Tarefa | Camada | Depois de baixar |
|---|---|---|
| Coletor novo ou mudança num coletor | `bronze` (e `originais`, para regerar um extrato) | `uv run pipeline.py --a-partir-de bronze`; `uv run pytest -m dados_reais tests/test_coletores.py` |
| Limpeza (bronze → silver) | `bronze` | `uv run pipeline.py --a-partir-de bronze` |
| Modelo, premissas, gold | `silver` | `uv run pipeline.py --a-partir-de silver` |
| Painel e chat | `banco` (ou `silver` e recalcular) | `uv run streamlit run app/Inicio.py` |

Observações:
- **Tamanhos:** o bronze oficial tem ≈ 78 MB comprimido (só os extratos e o `original.json` de cada fonte, D-032). Os demais: silver ≈ 3 MB, gold completo ≈ 1 MB, banco ≈ 3 MB comprimido. Pacote inteiro: ≈ 85 MB.
- **Originais grandes** (zips do CNPJ, `.7z` e `.COMT` da RAIS, `BaseCompleta.zip` da SUSEP; ≈ 9,7 GB comprimidos), só se a tarefa exigir regerar um extrato:
  - baixe com `--camadas originais`, se a carga tiver sido publicada com eles (`empacotar_dados.py --com-originais`);
  - eles vão para a pasta de originais, fora do projeto (`C:\radar_arquivo\bronze_originais`; `config/pacotes.yaml` ou `RADAR_ORIGINAIS`).
- O script nunca sobrescreve dados locais. Para trocar, use `--substituir`.
- **Plano B:** se o GitHub estiver fora do ar, o autor pode passar o pacote numa pasta (OneDrive, pendrive). Instale com `--origem <pasta> --camadas ...`.
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

Análise exploratória, mineração de dados e modelos preditivos ficam em `notebooks/` (detalhes em [`notebooks/README.md`](notebooks/README.md)):
- **Uma vez no seu clone:** `uv run nbstripout --install`. O git passa a limpar as saídas dos notebooks no commit; o `tests/test_notebooks.py` falha se algum notebook versionado tiver saída.
- **Notebook lê, não escreve:** dados só por `src/notebooks.py` (`conectar()` e `ler()`, somente leitura); nunca gravar em bronze, silver ou gold.
- **`interno_*` só em `notebooks/privado/`** (fora do git). Saídas grandes vão em `notebooks/saidas/` e modelos em `modelos/`, também fora do git.
- **Código reutilizável** sai do notebook e vai para `src/`, com teste.
- **Nova biblioteca de modelagem** (ex.: `scikit-learn`) só com aprovação do autor.
- **Abrir:** `uv run jupyter lab`.

## Regras do projeto, em resumo

- **Todo número tem fonte e data de referência.** Premissas ficam em `config/`, com fonte. O que não tem fonte leva `fonte: suposição`.
- **Decisões** de interpretação e modelagem vão para `docs/decisoes.md`. Erros da IA vão para `docs/erros_ia.md`. Descobertas, com data, vão para `docs/diario.md`.
- **Dados nunca entram no git**, exceto o conjunto público (`data/publico/`, gerado pelo `gerar_publico.py`) e as amostras mascaradas de `data/samples/`.
- **Releases:** só o autor publica. Ninguém apaga nem substitui um Release, nem de dados nem de código.
- **Tudo gratuito e local:** nenhum serviço pago, nenhuma conta em nuvem, nenhuma chave de API com créditos.

## LGPD da equipe

- O pacote da equipe e as tabelas `interno_*` são de **uso interno**. Eles têm estimativas do modelo por serventia (passivo, déficit, probabilidade) e o bronze bruto do CNJ, com nomes de responsáveis.
- **Não publique** nada disso. Não cole em issues, PRs, prints, mensagens ou documentos.
- **Não envie** nada disso a serviços externos, **inclusive IAs online**. O chat do projeto usa um modelo local (Ollama).
- **O que pode ser público:** dados de origem já publicados pelas fontes oficiais, sem dado pessoal, e as tabelas agregadas e auditadas do conjunto público (D-030).
