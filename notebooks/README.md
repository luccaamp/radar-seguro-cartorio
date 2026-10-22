# Notebooks

Análise exploratória, mineração de dados e modelos preditivos. Regras (também no `CLAUDE.md` e no `CONTRIBUTING.md`):

1. **Nomes numerados e descritivos:** `01_exploracao_arrecadacao.ipynb`, `02_modelo_prob_deficit.ipynb`.
2. **Notebook lê, não escreve.** Dados só por `src/notebooks.py` (`conectar()` e `ler()`, somente leitura); nunca gravar em bronze, silver ou gold.
3. **Código que vira reutilizável sai do notebook** e vai para `src/`, com teste em `tests/`.
4. **Saídas sempre limpas antes do commit.** Rode uma vez no seu clone: `uv run nbstripout --install`, e o git passa a limpar as saídas ao commitar. O `tests/test_notebooks.py` falha se algum `.ipynb` versionado tiver saída.
5. **Todos os notebooks vão para o git** (D-037), inclusive os que leem tabelas `interno_*`: vai só o código e o texto, sem saídas, e os dados por serventia continuam só no banco local e no pacote da equipe. **O texto nunca cita um cartório específico** (nome, CNS ou valor de um cartório); interpretações só com números agregados. Saídas grandes vão em `notebooks/saidas/` e modelos treinados em `modelos/`, ambos fora do git.

Para abrir:
```
uv run jupyter lab
```

| Notebook | O que faz |
|---|---|
| `00_exemplo_leitura.ipynb` | Conecta (somente leitura) e mostra os 10 números de referência a partir das tabelas **públicas**. |
