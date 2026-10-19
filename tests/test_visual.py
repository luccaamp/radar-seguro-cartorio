"""QA visual no navegador (Playwright + Chromium), fora da suíte padrão: `uv run pytest -m visual`.

Sobe o Streamlit sozinho numa porta livre, com cópia temporária do banco, abre os estados fixos de
scripts/qa_painel.py nas duas larguras e confere pelo DOM: texto cortado, última coluna das tabelas visível,
rótulo em toda barra do ranking, escala de cores do mapa visível, polígono do município dentro do enquadramento,
nenhuma caixa de erro do Streamlit e nenhum erro no console. Cada falha diz estado, largura, elemento e motivo.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
playwright = pytest.importorskip("playwright.sync_api")
from qa_painel import LARGURAS, abrir, checar, estados, ouvir_console, servidor  # noqa: E402

pytestmark = pytest.mark.visual


@pytest.fixture(scope="module")
def painel():
    with servidor() as (url, copia), playwright.sync_playwright() as p:
        lista = estados(copia)   # antes de abrir páginas: depois disso o Streamlit segura o arquivo da cópia
        nav = p.chromium.launch()
        yield url, lista, nav
        nav.close()


@pytest.mark.parametrize("largura", list(LARGURAS))
def test_layout_sem_falhas(painel, largura):
    url, lista, nav = painel
    page = nav.new_page(viewport={"width": largura, "height": LARGURAS[largura]}, color_scheme="light")
    erros = []
    ouvir_console(page, erros)
    falhas = []
    for est in lista:
        abrir(page, url, est, erros)
        falhas += checar(page, est, largura, erros)
    page.close()
    assert not falhas, f"{len(falhas)} falhas de layout:\n" + "\n".join(
        f"  [{e} @ {w} px] {motivo}: {detalhe}" for e, w, motivo, detalhe in falhas)
