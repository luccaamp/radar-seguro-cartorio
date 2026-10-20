# Notebooks

Análise exploratória, mineração de dados e modelos preditivos. Regras (também no `CLAUDE.md` e no `CONTRIBUTING.md`):

1. **Nomes numerados e descritivos:** `01_exploracao_arrecadacao.ipynb`, `02_modelo_prob_deficit.ipynb`.
2. **Notebook lê, não escreve.** Dados só por `src/notebooks.py` (`conectar()` e `ler()`, somente leitura); nunca gravar em bronze, silver ou gold.
3. **Código que vira reutilizável sai do notebook** e vai para `src/`, com teste em `tests/`.
4. **Saídas sempre limpas antes do commit.** Rode uma vez no seu clone: `uv run nbstripout --install`, e o git passa a limpar as saídas ao commitar. O `tests/test_notebooks.py` falha se algum `.ipynb` versionado tiver saída.
5. **`interno_*` (dados por serventia) só em `notebooks/privado/`**, que fica fora do git. Saídas grandes vão em `notebooks/saidas/` e modelos treinados em `modelos/`, ambos fora do git.
6. **Bibliotecas de modelagem** (ex.: `scikit-learn`) só quando o primeiro notebook precisar, com aprovação do autor.

Para abrir:
```
uv run jupyter lab
```

| Notebook | O que faz |
|---|---|
| `00_exemplo_leitura.ipynb` | Conecta (somente leitura) e mostra os 10 números de referência a partir das tabelas **públicas**. |
