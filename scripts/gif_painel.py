"""GIF do painel para o README (docs/img/painel_tour.gif): uma volta pelas telas principais, no MODO DEMONSTRAÇÃO
(só o conjunto público versionado, sem banco nem chave), como o link público. Reproduzível: qualquer clone gera o mesmo
percurso. Precisa do Chromium do Playwright (`uv run playwright install chromium`).

Percurso: Início (resposta e 6 indicadores) → Quão certo é (grade Taxa × adesão) → Onde está o mercado (mapa) →
clique em Belo Horizonte (quadro dos cartórios) → mapa em % de obrigados → Para onde vai → Sobre os dados → o mapa
no tema escuro (D-084). Também grava a imagem do Início do README (docs/img/painel_inicio.png, 1280 × 880, tema claro).

Uso: uv run python scripts/gif_painel.py [--saida docs/img/painel_tour.gif] [--largura 900]
                                         [--imagem docs/img/painel_inicio.png]
"""
import argparse
import io
import os
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import httpx
from PIL import Image
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
VIEWPORT = {"width": 1280, "height": 800}
SEGUNDOS = 2.2          # tempo de cada tela no GIF
BH = "3106200"          # Belo Horizonte (código IBGE)


@contextmanager
def painel_demo():
    """Sobe o painel no modo demonstração numa porta livre (banco apontado para um arquivo que não existe)."""
    pasta = Path(tempfile.mkdtemp(prefix="gif_painel_"))
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
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
        proc.wait(timeout=20)


def _quadro(page, largura: int) -> Image.Image:
    img = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
    return img.resize((largura, round(img.height * largura / img.width)), Image.LANCZOS)


def _ir(page, url: str, espera: str, rolar_ate: str | None = None) -> None:
    page.goto(url)
    page.get_by_text(espera).first.wait_for(timeout=60_000)
    if rolar_ate:
        page.locator(rolar_ate).first.scroll_into_view_if_needed()
    page.wait_for_timeout(1200)


def _clicar_municipio(page, area_id: str) -> None:
    alvo = page.locator(f'.rd-areas path[data-id="{area_id}"]')
    alvo.scroll_into_view_if_needed()
    ponto = alvo.evaluate("""p => {
        const b = p.getBBox(), m = p.getScreenCTM(), q = p.ownerSVGElement.createSVGPoint(), r = p.getRootNode();
        for (const i of [10, 8, 12, 6, 14]) for (const j of [10, 8, 12, 6, 14]) {
            q.x = b.x + b.width * i / 20; q.y = b.y + b.height * j / 20; const s = q.matrixTransform(m);
            if (r.elementFromPoint(s.x, s.y) === p) return [s.x, s.y]; }
        return null; }""")
    page.mouse.click(*ponto)


def gravar(saida: Path, largura: int, imagem: Path | None = None) -> int:
    quadros = []
    with painel_demo() as url, sync_playwright() as p:
        nav = p.chromium.launch()
        if imagem:   # imagem do Início do README, na resolução da tela
            pag = nav.new_page(viewport={"width": 1280, "height": 880}, color_scheme="light")
            _ir(pag, url + "/", "Prêmio anual estimado")
            imagem.parent.mkdir(parents=True, exist_ok=True)
            pag.screenshot(path=str(imagem))
            pag.close()
        page = nav.new_page(viewport=VIEWPORT, color_scheme="light")
        _ir(page, url + "/", "Prêmio anual estimado")
        quadros.append(_quadro(page, largura))
        page.locator(".rd-grade").first.scroll_into_view_if_needed()   # o Streamlit rola um contêiner, não a janela
        page.wait_for_timeout(600)
        quadros.append(_quadro(page, largura))
        _ir(page, url + "/Quão_certo_é", "Taxa × adesão", "table.rd-calor")
        quadros.append(_quadro(page, largura))
        _ir(page, url + "/Onde_está_o_mercado", "Os maiores déficits", ".rd-mapa svg")
        quadros.append(_quadro(page, largura))
        _clicar_municipio(page, BH)
        page.get_by_role("heading", name="Os cartórios de Belo Horizonte").wait_for(timeout=60_000)
        page.locator(".rd-mapa svg").first.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        quadros.append(_quadro(page, largura))
        page.get_by_role("heading", name="Os cartórios de Belo Horizonte").scroll_into_view_if_needed()
        page.wait_for_timeout(600)
        quadros.append(_quadro(page, largura))
        _ir(page, url + "/Onde_está_o_mercado", "Os maiores déficits", ".rd-mapa svg")
        page.get_by_role("radio", name="% obrigados").click()
        page.get_by_text("dos cartórios de MG são obrigados").first.wait_for(timeout=60_000)
        page.locator('[data-testid="stButtonGroup"]').first.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        quadros.append(_quadro(page, largura))
        _ir(page, url + "/Para_onde_vai", "Para onde")
        quadros.append(_quadro(page, largura))
        _ir(page, url + "/Sobre_os_dados", "Os 10 números oficiais")
        quadros.append(_quadro(page, largura))
        # o mapa no tema escuro: fundo neutro e cores de dado com 3:1 ou mais (D-084)
        escuro = nav.new_page(viewport=VIEWPORT, color_scheme="dark")
        _ir(escuro, url + "/Onde_está_o_mercado", "Os maiores déficits", ".rd-mapa svg")
        escuro.wait_for_timeout(800)
        quadros.append(_quadro(escuro, largura))
        nav.close()
    paleta = [q.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for q in quadros]
    saida.parent.mkdir(parents=True, exist_ok=True)
    paleta[0].save(saida, save_all=True, append_images=paleta[1:], duration=int(SEGUNDOS * 1000), loop=0,
                   optimize=True)
    return len(quadros)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    a = argparse.ArgumentParser()
    a.add_argument("--saida", default=str(RAIZ / "docs" / "img" / "painel_tour.gif"))
    a.add_argument("--largura", type=int, default=900)
    a.add_argument("--imagem", default=str(RAIZ / "docs" / "img" / "painel_inicio.png"),
                   help="imagem do Início do README ('' para não gravar)")
    x = a.parse_args()
    n = gravar(Path(x.saida), x.largura, Path(x.imagem) if x.imagem else None)
    if x.imagem:
        print(f"{x.imagem}: {Path(x.imagem).stat().st_size / 1e3:.0f} kB")
    with Image.open(x.saida) as gif:   # quadros iguais em seguida viram um só no GIF: conta o que ficou
        print(f"{x.saida}: {n} telas capturadas, {gif.n_frames} quadros, {Path(x.saida).stat().st_size / 1e6:.2f} MB")
