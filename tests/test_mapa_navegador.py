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
PAGINA = "/Onde_está_o_mercado?estado=MG"   # o recorte de MG (o padrão é o Sudeste, D-088): estes testes conferem MG
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


# O botão de tema do painel grava a escolha para o Streamlit e recarrega a página uma vez quando a chave dele não bate
# (componentes/tema.js). Nos testes do mapa, a chave já vem certa, para nenhuma recarga cair no meio de um clique; o
# teste do tema abre sem isso (preparar=False) e confere a recarga.
PREPARAR_TEMA = """(() => { try {
    const t = localStorage.getItem('radar-tema') || 'claro';
    const nome = {claro: 'Light', escuro: 'Dark', sistema: 'System'}[t] || 'Light';
    localStorage.setItem('stActiveTheme-' + location.pathname + '-v2', JSON.stringify(nome));
} catch (e) {} })();"""


def abrir(nav, largura=1280, altura=900, tema="light", preparar=True):
    url, b = nav
    page = b.new_page(viewport={"width": largura, "height": altura}, color_scheme=tema)
    if preparar:
        page.add_init_script(PREPARAR_TEMA)
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
    # Com `?estado=` o Streamlit roda a página de novo logo depois de abrir e o mapa é redesenhado; no CI (mais lento)
    # a busca podia cair no meio da troca (PR #30). Tenta de novo por até 15 s; se falhar, diz o que está por cima.
    alvo = page.locator(f'.rd-areas path[data-id="{area_id}"]')
    ponto, cima = None, None
    for _ in range(30):
        alvo.scroll_into_view_if_needed()
        ponto, cima = alvo.evaluate("""p => {
            const b = p.getBBox(), m = p.getScreenCTM(), q = p.ownerSVGElement.createSVGPoint(), raiz = p.getRootNode();
            for (const i of [10, 8, 12, 6, 14, 4, 16, 2, 18]) for (const j of [10, 8, 12, 6, 14, 4, 16, 2, 18]) {
                q.x = b.x + b.width * i / 20; q.y = b.y + b.height * j / 20;
                const s = q.matrixTransform(m);
                if (s.x >= 0 && s.y >= 0 && s.x < innerWidth && s.y < innerHeight && raiz.elementFromPoint(s.x, s.y) === p)
                    return [[s.x, s.y], null];
            }
            q.x = b.x + b.width / 2; q.y = b.y + b.height / 2;
            const s = q.matrixTransform(m), e = raiz.elementFromPoint(s.x, s.y);
            return [null, e ? `${e.tagName}.${e.getAttribute('class') || ''}#${e.getAttribute('data-id') || ''} ` +
                              `em (${Math.round(s.x)}, ${Math.round(s.y)}) de ${innerWidth}×${innerHeight}` : 'nada']; }""")
        if ponto:
            break
        time.sleep(0.5)
    assert ponto, f"nenhum ponto dentro de {area_id}; no centro: {cima}"
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
    # V3 (D-089): as divisas finas dos 4 estados por cima (a de MG, em foco, mais forte); os municípios de SP, RJ e ES
    # em cinza (clicáveis: trocam o foco); os outros estados em cinza por baixo
    assert page.locator(".rd-divisas path").count() == 4 and page.locator(".rd-divisas path.rd-foco").count() == 1
    assert page.locator(".rd-fora path").count() > 700 and page.locator(".rd-vizinhos path").count() >= 1
    etiquetas = page.locator(".rd-destaque text").all_text_contents()   # texto de SVG não tem innerText
    assert [e.split(" · ")[0] for e in etiquetas] == ["▲ Belo Horizonte", "▲ Uberlândia", "▲ Uberaba"], etiquetas
    assert all(" · R$ " in e for e in etiquetas)                              # os 3 maiores déficits, com o valor
    assert page.locator(".rd-rotulos > text[data-id]").count() > 3            # e mais nomes, sem se sobrepor
    assert page.locator(".rd-mapa-info").inner_text().startswith("FALTA COBRIR · MINAS GERAIS")
    # V3: a barra (busca e estados) e, ao lado, os 10 que mais faltam cobrir
    assert page.locator(".rd-mapa-busca input").count() == 1
    assert page.locator(".rd-mapa-ufs button[aria-pressed='true']").inner_text() == "MG"
    assert page.locator(".rd-mapa-rank button").count() == 10
    # cada nome cai sobre o próprio município (o ponto vem de ponto_interno, em Python)
    for t in page.locator(".rd-rotulos > text[data-id]").all()[:8]:
        alvo = t.get_attribute("data-id")
        t.scroll_into_view_if_needed()   # elementFromPoint só enxerga o que está na tela
        assert t.evaluate("""(t, id) => { const b = t.getBoundingClientRect(), r = t.getRootNode();
            t.style.display = 'none'; const e = r.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2);
            t.style.display = ''; return e && e.getAttribute('data-id') === id; }""", alvo), alvo
    assert page.locator(".rd-mapa-resumo").inner_text().startswith("O que falta cobrir está concentrado em Belo Horizonte")
    assert_letra_legivel(page)
    assert not erros, erros
    page.close()


def test_clique_escolhe_o_municipio_e_enquadra(nav):
    page, erros = abrir(nav)
    caixa_mg = page.locator(".rd-mapa-svg").get_attribute("viewBox")
    clicar_dentro(page, BH)
    escolhido(page, "Belo Horizonte")
    page.locator(f'.rd-areas path.rd-sel[data-id="{BH}"]').wait_for()
    assert page.locator(".rd-mapa-lado h2").inner_text() == "Belo Horizonte"     # V3: os números dele ao lado
    assert page.locator(".rd-mapa-svg").get_attribute("viewBox") != caixa_mg       # zoom na região
    assert_letra_legivel(page)                                                     # com zoom, a letra não encolhe
    # outro clique, num vizinho que fica no enquadramento, troca o município (o gatilho não fica preso no primeiro)
    clicar_dentro(page, CONTAGEM)
    escolhido(page, "Contagem")
    page.locator(f'.rd-areas path.rd-sel[data-id="{CONTAGEM}"]').wait_for()
    assert not erros, erros
    page.close()


def test_celular_390_px_sem_rolagem_horizontal_e_clique(nav):
    page, erros = abrir(nav, 390, 844)
    largura_svg = page.locator(".rd-mapa-svg").evaluate("e => e.getBoundingClientRect().width")
    assert 280 < largura_svg <= 390                     # dentro do cartão do mapa (V3), com a margem dele
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    clicar_dentro(page, UBERABA)
    escolhido(page, "Uberaba")
    # o clique abre o quadro do município (item 2), e a tabela cabe no celular
    page.get_by_role("heading", name="Os cartórios de Uberaba").wait_for(timeout=30_000)
    tab = page.locator("table.rd-tabela", has=page.locator("th", has_text="CNS"))
    assert tab.evaluate("t => t.scrollWidth <= t.parentElement.clientWidth + 1")
    assert [t.lower() for t in tab.locator("th:visible").all_inner_texts()] == [   # cabeçalho em versalete (V5)
        "cns", "atribuições", "classe", "déficit esperado"]
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert not erros, erros
    page.close()


def _esperar_tema(page, esperado: str) -> None:
    """Espera o botão de tema marcar o <html> (data-rd-tema) antes de ler a cor (no CI, uma leitura logo depois de o
    mapa aparecer pegou o tema anterior; 2026-11-10)."""
    try:
        page.wait_for_function("t => document.documentElement.getAttribute('data-rd-tema') === t", arg=esperado,
                               timeout=30_000)
    except Exception:
        estado = page.evaluate("() => document.documentElement.getAttribute('data-rd-tema')")
        raise AssertionError(f"a página não ficou em {esperado!r} (data-rd-tema = {estado!r})")
    page.locator(".rd-areas path").first.wait_for(timeout=60_000)


def _cor(page, seletor: str, prop: str) -> str:
    return page.locator(seletor).first.evaluate(f"e => getComputedStyle(e).{prop}")


def test_botao_de_tema_claro_por_padrao_e_escuro_com_um_clique(nav):
    """O painel abre no claro mesmo com o sistema no escuro (o padrão, 2026-11-11); o botão "Escuro", na própria
    página (no link público o menu do Streamlit não troca o tema, D-084), passa o painel inteiro ao escuro: as faixas do
    mapa e o fundo dos componentes do Streamlit; "Sistema" segue o aparelho."""
    page, erros = abrir(nav, tema="dark", preparar=False)
    _esperar_tema(page, "claro")
    assert _cor(page, ".rd-areas path.rd-f-6", "fill") == "rgb(30, 59, 122)"      # --mapa-6 claro  #1e3b7a
    assert _cor(page, ".stApp", "backgroundColor") == "rgb(244, 245, 242)"        # --fundo claro   #f4f5f2
    assert page.evaluate("localStorage.getItem('stActiveTheme-' + location.pathname + '-v2')") == '"Light"'
    page.get_by_role("button", name="Escuro").click()
    _esperar_tema(page, "escuro")
    page.wait_for_function("() => getComputedStyle(document.querySelector('.stApp')).backgroundColor "
                           "=== 'rgb(15, 19, 18)'", timeout=30_000)                # o Streamlit também no escuro
    assert _cor(page, ".rd-areas path.rd-f-6", "fill") == "rgb(248, 251, 228)"    # --mapa-6 escuro #f8fbe4
    assert page.get_by_role("button", name="Escuro").get_attribute("aria-pressed") == "true"
    page.get_by_role("button", name="Sistema").click()
    _esperar_tema(page, "escuro")                                                  # o sistema está no escuro
    page.get_by_role("button", name="Claro").click()
    _esperar_tema(page, "claro")
    assert not erros, erros
    page.close()


MENU = """() => {
  const nav = document.querySelector('[data-testid="stTopNav"]');
  const tema = document.querySelector('.st-key-rd_tema').getBoundingClientRect();
  const itens = [...nav.querySelectorAll('.rc-overflow-item')].filter(i => getComputedStyle(i).opacity !== '0');
  const caixas = itens.map(i => ({texto: i.innerText.trim(), dir: i.getBoundingClientRect().right}));
  return {temaEsq: tema.left, caixas};
}"""


@pytest.mark.parametrize("largura", [800, 1024, 1280])
def test_menu_do_topo_nao_fica_debaixo_do_botao_de_tema(nav, largura):
    """Com 8 páginas (a "Brasil", D-087), os últimos itens do menu ficavam debaixo do botão de tema abaixo de ≈ 1.100 px
    (2026-11-11). O menu termina antes do botão e o que não cabe vai para o "… more" do Streamlit, onde "Pergunte à IA"
    continua alcançável."""
    url, b = nav
    page = b.new_page(viewport={"width": largura, "height": 800})
    page.add_init_script(PREPARAR_TEMA)
    page.goto(url + "/")
    page.locator(".rd-card").first.wait_for(timeout=60_000)
    page.wait_for_timeout(1500)
    m = page.evaluate(MENU)
    assert m["caixas"] and all(c["dir"] <= m["temaEsq"] for c in m["caixas"]), m
    textos = [c["texto"] for c in m["caixas"]]
    if "Pergunte à IA" not in textos:   # recolhido: o "… more" abre a lista com o resto
        page.locator('[data-testid="stTopNav"] .rc-overflow-item-rest').click()
        page.get_by_test_id("stTopNavDropdownLink").filter(has_text="Pergunte à IA").wait_for(timeout=10_000)
    page.close()


def test_link_direto_num_servidor_recem_ligado_usa_o_menu_do_topo(nav):
    """O Streamlit Cloud dorme e acorda o app num servidor novo. Com as páginas numa pasta chamada `pages/`, quem abria
    direto o endereço de uma página (um link do README, um link compartilhado) nesse servidor via o menu lateral antigo,
    com os nomes dos arquivos ("Inicio", "Chat", "Explorar") (2026-11-11). A pasta virou `app/paginas/`: servidor
    próprio, recém-ligado, aberto direto em /Brasil."""
    _, b = nav   # o navegador dos outros testes; o servidor, novo (o deles já está "aquecido")
    with painel_demo() as url:
        page = b.new_page(viewport={"width": 1280, "height": 800})
        page.add_init_script(PREPARAR_TEMA)
        page.goto(url + "/Brasil")
        page.locator(".rd-areas path").first.wait_for(timeout=60_000)
        page.locator('[data-testid="stTopNav"]').wait_for(timeout=30_000)
        assert page.locator('[data-testid="stSidebarNav"]').count() == 0
        assert page.get_by_role("heading", name="Cartórios do Brasil").count() == 1
        page.close()
    assert not (RAIZ / "app" / "pages").exists()
