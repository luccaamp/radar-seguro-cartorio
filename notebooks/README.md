# Notebooks

Análise exploratória, mineração de dados e modelos preditivos. Regras (também no `CLAUDE.md` e no `CONTRIBUTING.md`):

1. **Nomes numerados e descritivos:** `01_exploracao_arrecadacao.ipynb`, `02_modelo_prob_deficit.ipynb`.
2. **Notebook lê, não escreve.** Dados só por `src/notebooks.py` (`conectar()` e `ler()`, somente leitura); nunca gravar em bronze, silver ou gold.
3. **Código que vira reutilizável sai do notebook** e vai para `src/`, com teste em `tests/`.
4. **Todos os notebooks vão para o git com as saídas** (D-038): é um estudo público, com dados públicos. Podem ler qualquer tabela (inclusive `interno_*`) e mostrar resultados por cartório. Quem tinha o filtro do `nbstripout` desfaz com `uv run nbstripout --uninstall`.
5. **Nenhum nome nem CPF de pessoa física** no texto ou nas saídas. O cartório aparece pelo CNS e pelo município. O `tests/test_notebooks.py` procura CPF.
6. **Gráficos também em PNG** em `docs/qa/analises/` (vão para o git). Arquivos grandes vão em `notebooks/saidas/` e modelos treinados em `modelos/`, ambos fora do git só pelo tamanho.

Para abrir:
```
uv run jupyter lab
```

| Notebook | O que faz |
|---|---|
| `00_exemplo_leitura.ipynb` | Conecta (somente leitura) e mostra os 10 números de referência a partir das tabelas **públicas**. |
| `01_qualidade_dados_faltantes.ipynb` | Mineração, parte A: o que falta em cada fonte, valores atípicos, saltos na série de cada serventia e consistência entre CNJ, BI do CNJ, RAIS e CNPJ. |
| `02_analise_exploratoria.ipynb` | Mineração, parte A: distribuições, recortes por classe, situação, atribuição e região, mapa, série histórica e correlações. |

Funções reutilizáveis da mineração: `src/analise/` (testes em `tests/test_analise.py`; parâmetros em `config/analise.yaml`).
