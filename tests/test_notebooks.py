"""Notebooks (notebooks/README.md): saídas limpas, acesso somente leitura e o exemplo funcionando.

Roda em qualquer clone: o exemplo usa o conjunto público (modo demonstração) se não houver banco local.
"""
import json
from pathlib import Path

import duckdb
import pytest

from apoio_painel import RAIZ, arquivos_versionaveis


def notebooks_versionaveis() -> list[Path]:
    return arquivos_versionaveis("*.ipynb")


def test_notebooks_versionados_sem_saida():
    """Saída de notebook pode carregar dado interno para o repositório público: nada de saída nem contagem."""
    sujos = []
    for nb in notebooks_versionaveis():
        for i, c in enumerate(json.loads(nb.read_text(encoding="utf-8"))["cells"]):
            if c.get("cell_type") == "code" and (c.get("outputs") or c.get("execution_count") is not None):
                sujos.append(f"{nb.relative_to(RAIZ).as_posix()} célula {i}")
    assert notebooks_versionaveis(), "o notebook de exemplo deveria existir"
    assert not sujos, f"rode `uv run nbstripout <arquivo>` (ou `uv run nbstripout --install` uma vez): {sujos}"


def test_notebooks_versionados_nao_usam_interno():
    """Nenhuma célula de CÓDIGO de notebook versionado lê tabela interno_* (o texto explicativo pode citar a regra)."""
    def codigo(nb: Path) -> str:
        return "\n".join("".join(c["source"]) for c in json.loads(nb.read_text(encoding="utf-8"))["cells"]
                         if c["cell_type"] == "code")
    ruins = [nb.name for nb in notebooks_versionaveis() if "interno_" in codigo(nb)]
    assert not ruins, f"interno_* só em notebooks/privado/ (fora do git): {ruins}"


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
