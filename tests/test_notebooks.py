"""Notebooks (CONTRIBUTING.md, seção Notebooks): acesso somente leitura, nenhum CPF e o exemplo funcionando.

Os notebooks vão para o git com as saídas (D-038). Roda em qualquer clone: o exemplo usa o conjunto público (modo
demonstração) se não houver banco local.
"""
import json
import re
from pathlib import Path

import duckdb
import pytest

from apoio_painel import RAIZ, arquivos_versionaveis


def notebooks_versionaveis() -> list[Path]:
    return arquivos_versionaveis("*.ipynb")


CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")


def _textos(celula: dict) -> list[str]:
    textos = ["".join(celula["source"])]
    for saida in celula.get("outputs", []):
        textos.append("".join(saida.get("text", [])))
        for valor in saida.get("data", {}).values():
            if isinstance(valor, (str, list)):
                textos.append("".join(valor))
    return textos


def test_notebooks_nao_mostram_cpf():
    """D-038: nenhum CPF de pessoa física no texto, no código ou nas saídas dos notebooks."""
    assert notebooks_versionaveis(), "o notebook de exemplo deveria existir"
    ruins = []
    for nb in notebooks_versionaveis():
        for i, c in enumerate(json.loads(nb.read_text(encoding="utf-8"))["cells"]):
            if any(CPF.search(t) for t in _textos(c)):
                ruins.append(f"{nb.relative_to(RAIZ).as_posix()} célula {i}")
    assert not ruins, f"notebook mostra um CPF: {ruins}"


def test_conectar_e_somente_leitura(tmp_path):
    from src.notebooks import conectar
    banco = tmp_path / "x.duckdb"
    duckdb.connect(str(banco)).close()
    with conectar(banco) as con, pytest.raises(duckdb.Error):
        con.execute("CREATE TABLE t AS SELECT 1")


def test_exemplo_mostra_os_numeros_de_referencia(monkeypatch):
    """Executa as células de código do 00_exemplo_leitura (sem jupyter) sobre o conjunto público."""
    from src import notebooks, publico
    monkeypatch.setattr(notebooks, "BANCO", RAIZ / "nao_existe.duckdb")   # força o conjunto público
    nb = json.loads((RAIZ / "notebooks" / "00_exemplo_leitura.ipynb").read_text(encoding="utf-8"))
    ns = {}
    monkeypatch.chdir(RAIZ / "notebooks")
    for c in nb["cells"]:
        if c["cell_type"] == "code":
            exec("".join(c["source"]), ns)
    n = ns["numeros"]
    with duckdb.connect(str(publico.banco_demonstracao()), read_only=True) as con:
        ref = con.execute("SELECT n_serventias_ativas, mercado_premio_emitido FROM gold.fato_mercado_uf WHERE "
                          "nivel = 'base' AND regra_classe = 'v2' AND cenario_stf = 'mantem'").fetchone()
    assert len(n) == 10 and n["Serventias ativas"] == ref[0] and n["Prêmio anual do mercado (R$)"] == ref[1]
