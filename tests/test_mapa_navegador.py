"""Mapa clicável (D-083) no navegador de verdade (Playwright + Chromium): o clique num município chega ao Python.

Sobe o painel no MODO DEMONSTRAÇÃO (só o conjunto público versionado, sem banco nem chave), então roda em qualquer
clone e no CI. Fora da suíte padrão: `uv run pytest -m navegador` (precisa de `uv run playwright install chromium`).

O que confere, na página "Onde está o mercado":
- as 851 áreas desenhadas, a legenda e nenhum erro no console;
- clique de mouse dentro de um município → a página roda de novo com ele escolhido (seletor, números e destaque) e o
  mapa enquadra a região dele;
- em 390 px: sem rolagem horizontal e o clique também funciona;
- no tema escuro, as faixas usam os tokens escuros.
"""
import os
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")
httpx = pytest.importorskip("httpx")

pytestmark = pytest.mark.navegador
RAIZ = Path(__file__).resolve().parents[1]
PAGINA = "/Onde_está_o_mercado"
BH = "3106200"            # Belo Horizonte (código IBGE): o maior déficit de MG
CONTAGEM = "3118601"      # vizinha de BH, na mesma região intermediária
UBERABA = "3170107"


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def painel_demo():
    pasta = Path(tempfile.mkdtemp(prefix="mapa_nav_"))
    porta = _porta_livre()
    env = os.environ | {"RADAR_BANCO": str(pasta / "nao_existe.duckdb"), "RADAR_ESTADO": str(pasta / "estado.json"),
                        "GEMINI_API_KEY": "", "PYTHONIOENCODING": "utf-8"}
    env.pop("RADAR_PUBLICO", None)
    proc = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app/Inicio.py", "--server.headless", "true",
                             "--server.port", str(porta), "--browser.gatherUsageStats", "false",
                             "--server.fileWatcherType", "none"], cwd=RAIZ, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{porta}"
    try:
        for _ in range(120):
            try:
                if httpx.get(f"{url}/_stcore/health", timeout=2).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.5)
        else:
            raise RuntimeError("o Streamlit não subiu")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="module")
def nav():
    with painel_demo() as url, playwright.sync_playwright() as p:
        b = p.chromium.launch()
        yield url, b
        b.close()


def abrir(nav, largura=1280, altura=900, tema="light"):
    url, b = nav
    page = b.new_page(viewport={"width": largura, "height": altura}, color_scheme=tema)
    erros: list[str] = []
    # ao abrir por um endereço de página, o Streamlit sonda /<página>/_stcore/health e /host-config antes da raiz e
    # recebe 404: é do próprio Streamlit, não do mapa (conferido em 2026-11-10); qualquer outro erro conta
    page.on("console", lambda m: erros.append(f"{m.text} ({m.location.get('url', '')})")
            if m.type == "error" and "/_stcore/" not in m.location.get("url", "") else None)
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.goto(url + PAGINA)
    page.locator(".rd-areas path").first.wait_for(timeout=60_000)
    return page, erros


def clicar_dentro(page, area_id: str) -> None:
    """Clique de mouse num ponto em que o próprio navegador diz que o município está por cima (o centro da caixa pode
    cair fora, em município côncavo, e a borda pode cair no vizinho)."""
    alvo = page.locator(f'.rd-areas path[data-id="{area_id}"]')
    alvo.scroll_into_view_if_needed()
    ponto = alvo.evaluate("""p => {
        const b = p.getBBox(), m = p.getScreenCTM(), q = p.ownerSVGElement.createSVGPoint(), raiz = p.getRootNode();
        for (const i of [10, 8, 12, 6, 14, 4, 16, 2, 18]) for (const j of [10, 8, 12, 6, 14, 4, 16, 2, 18]) {
            q.x = b.x + b.width * i / 20; q.y = b.y + b.height * j / 20;
            const s = q.matrixTransform(m);
            if (s.x >= 0 && s.y >= 0 && s.x < innerWidth && s.y < innerHeight && raiz.elementFromPoint(s.x, s.y) === p)
                return [s.x, s.y];
        }
        return null; }""")
    assert ponto, f"nenhum ponto dentro de {area_id}"
    page.mouse.click(*ponto)


def assert_letra_legivel(page) -> None:
    """Rótulos com letra de leitura na tela (o tamanho da letra × a escala do desenho: 11 a 13 px, como o mapa.js
    pede), e sem um rótulo em cima do outro (a escolha dos que cabem é do mapa.js)."""
    textos = page.locator(".rd-rotulos text").all()
    assert textos, "sem rótulos"
    px = [t.evaluate("t => parseFloat(t.getAttribute('font-size')) * t.getScreenCTM().a") for t in textos]
    assert all(10.5 <= v <= 13.5 for v in px), [round(v, 1) for v in px]
    caixas = [t.bounding_box() for t in textos]
    for i, a in enumerate(caixas):
        for b in caixas[i + 1:]:
            assert (a["x"] + a["width"] <= b["x"] or b["x"] + b["width"] <= a["x"] or
                    a["y"] + a["height"] <= b["y"] or b["y"] + b["height"] <= a["y"]), (a, b)


def escolhido(page, nome: str) -> None:
    page.get_by_text(f"Déficit em {nome}").first.wait_for(timeout=30_000)


def test_mapa_desenha_as_areas_e_a_legenda_sem_erro(nav):
    page, erros = abrir(nav)
    assert page.locator(".rd-areas path").count() == 851
    assert page.locator(".rd-fundo path").count() >= 1
    assert page.locator(".rd-mapa-legenda .rd-mapa-item").count() >= 3
    assert page.locator(".rd-areas path.rd-f-zero").count() > 0                  # o zero neutro aparece
    assert page.locator(".rd-contorno path").count() == 851 + page.locator(".rd-fundo path").count()
    rotulos = page.locator(".rd-rotulos text").all_text_contents()   # texto de SVG não tem innerText
    assert rotulos == ["Belo Horizonte", "Uberlândia", "Uberaba"], rotulos     # os 3 maiores déficits de MG
    # cada rótulo cai sobre o próprio município (o ponto vem de ponto_interno, em Python)
    for t in page.locator(".rd-rotulos text").all():
        alvo = t.get_attribute("data-id")
        t.scroll_into_view_if_needed()   # elementFromPoint só enxerga o que está na tela
        assert t.evaluate("""(t, id) => { const b = t.getBoundingClientRect(), r = t.getRootNode();
            t.style.display = 'none'; const e = r.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2);
            t.style.display = ''; return e && e.getAttribute('data-id') === id; }""", alvo), alvo
    assert page.locator(".rd-mapa-resumo").inner_text().startswith("Os maiores déficits estão em Belo Horizonte")
    assert_letra_legivel(page)
    assert not erros, erros
    page.close()


def test_clique_escolhe_o_municipio_e_enquadra(nav):
    page, erros = abrir(nav)
    caixa_mg = page.locator(".rd-mapa svg").get_attribute("viewBox")
    clicar_dentro(page, BH)
    escolhido(page, "Belo Horizonte")
    page.locator(f'.rd-areas path.rd-sel[data-id="{BH}"]').wait_for()
    assert page.locator('[data-testid="stSelectbox"] input[role="combobox"]').first.input_value() == "Belo Horizonte"
    assert page.locator(".rd-mapa svg").get_attribute("viewBox") != caixa_mg       # zoom na região
    assert_letra_legivel(page)                                                     # com zoom, a letra não encolhe
    # outro clique, num vizinho que fica no enquadramento, troca o município (o gatilho não fica preso no primeiro)
    clicar_dentro(page, CONTAGEM)
    escolhido(page, "Contagem")
    page.locator(f'.rd-areas path.rd-sel[data-id="{CONTAGEM}"]').wait_for()
    assert not erros, erros
    page.close()


def test_celular_390_px_sem_rolagem_horizontal_e_clique(nav):
    page, erros = abrir(nav, 390, 844)
    largura_svg = page.locator(".rd-mapa svg").evaluate("e => e.getBoundingClientRect().width")
    assert 300 < largura_svg <= 390
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    clicar_dentro(page, UBERABA)
    escolhido(page, "Uberaba")
    # o clique abre o quadro do município (item 2), e a tabela cabe no celular
    page.get_by_role("heading", name="Os cartórios de Uberaba").wait_for(timeout=30_000)
    tab = page.locator("table.rd-tabela", has=page.locator("th", has_text="CNS"))
    assert tab.evaluate("t => t.scrollWidth <= t.parentElement.clientWidth + 1")
    assert tab.locator("th:visible").all_inner_texts() == ["CNS", "Atribuições", "Classe", "Déficit esperado"]
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert not erros, erros
    page.close()


def test_tema_escuro_usa_os_tokens_escuros(nav):
    cores = {}
    for tema in ("light", "dark"):
        page, erros = abrir(nav, tema=tema)
        cores[tema] = page.locator(".rd-areas path.rd-f-6").first.evaluate("e => getComputedStyle(e).fill")
        assert not erros, erros
        page.close()
    assert cores["light"] == "rgb(18, 50, 90)"      # --mapa-6 claro  #12325a (2026-11-10)
    assert cores["dark"] == "rgb(215, 228, 246)"    # --mapa-6 escuro #d7e4f6 (2026-11-10)
