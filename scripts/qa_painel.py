"""QA visual do painel: servidor próprio, estados fixos e checagens de layout no navegador (Playwright + Chromium).

Usado por scripts/prints_painel.py (galeria), tests/test_visual.py (checagens) e scripts/acessibilidade.py (axe).
- O servidor sobe o Streamlit numa porta livre sobre uma CÓPIA temporária do banco (RADAR_BANCO) e um arquivo de
  cenários temporário (RADAR_ESTADO); nada é gravado em data/ e o Streamlit do autor não é usado.
- Os estados são montados por cliques na interface, como uma pessoa faria (sem zoom manual).
- As checagens leem a página renderizada (DOM e o gráfico Plotly já desenhado), não o fig.to_dict().
"""
import contextlib
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import duckdb
import httpx

RAIZ = Path(__file__).resolve().parents[1]
BANCO_REAL = RAIZ / "data" / "radar.duckdb"
LARGURAS = {390: 844, 1280: 800, 1366: 768, 1920: 1080}   # 1366: notebook (Etapa 3, "pronto quando"); 390: celular


# ------------------------------------------------------------------ servidor
def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def servidor():
    """Sobe o painel sobre uma cópia temporária do banco e devolve (url, caminho da cópia). Derruba no fim."""
    pasta = Path(tempfile.mkdtemp(prefix="qa_painel_"))
    copia = pasta / "radar.duckdb"
    shutil.copy2(BANCO_REAL, copia)               # o banco real só é lido (copiado)
    porta = _porta_livre()
    env = os.environ | {"RADAR_BANCO": str(copia), "RADAR_ESTADO": str(pasta / "painel_estado.json"),
                        "PYTHONIOENCODING": "utf-8"}
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
        yield url, copia
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(pasta, ignore_errors=True)


# ------------------------------------------------------------------ interação
def esperar(page, extra_ms: int = 1500) -> None:
    """Espera o Streamlit terminar de rodar o script e os gráficos desenharem."""
    page.wait_for_selector('[data-testid="stApp"]', timeout=90_000)
    page.wait_for_timeout(400)
    page.wait_for_function("() => !document.querySelector('[data-testid=\"stStatusWidget\"] [data-testid=\"stStatusWidgetRunningIcon\"]')"
                           " && !document.querySelector('[data-testid=\"stSkeleton\"]')", timeout=90_000)
    page.wait_for_timeout(extra_ms)


def escolher(page, rotulo: str, opcao: str) -> None:
    """Escolhe `opcao` no selectbox cujo rótulo é `rotulo`."""
    # Streamlit 1.66: o selectbox é uma combobox (react-aria) com aria-label igual ao rótulo
    campo = page.locator(f'[data-testid="stSelectbox"] input[aria-label="{rotulo}"]').first
    campo.click()
    campo.fill(opcao)
    page.get_by_role("option", name=opcao, exact=True).first.click()
    esperar(page)


def marcar(page, opcao: str) -> None:
    """Marca a opção de rádio com o texto exato `opcao`."""
    page.locator('[data-testid="stRadio"]').get_by_text(opcao, exact=True).first.click()
    esperar(page)


def aba(page, nome: str) -> None:
    """Abre a aba (st.tabs) de texto `nome`."""
    page.get_by_role("tab", name=nome, exact=True).first.click()
    esperar(page)


def deslizar(page, rotulo: str, passos: int) -> None:
    """Move o controle deslizante de rótulo `rotulo` `passos` posições (positivo = para a direita) pelo teclado."""
    # Streamlit 1.66: slider react-aria; a alça tem um <input type="range"> visualmente escondido que recebe o teclado
    caixa = page.locator('[data-testid="stSlider"]').filter(has=page.get_by_text(rotulo, exact=True)).first
    caixa.locator('input[type="range"]').first.evaluate("el => el.focus()")
    for _ in range(abs(passos)):
        page.keyboard.press("ArrowRight" if passos > 0 else "ArrowLeft")
        page.wait_for_timeout(60)
    page.wait_for_timeout(800)
    esperar(page)


# ------------------------------------------------------------------ estados fixos
@dataclass
class Estado:
    nome: str
    pagina: str                     # caminho da URL ("" = Início)
    acoes: Callable = lambda page: None
    rolar_ate: str | None = None    # texto de um título para enquadrar (prints de seção)
    municipio: bool = False         # checar o enquadramento do polígono do município


def municipio_pequeno(copia: Path) -> str:
    with duckdb.connect(str(copia), read_only=True) as con:
        return con.execute("SELECT municipio FROM gold.dim_municipio WHERE n_serventias BETWEEN 1 AND 2 "
                           "ORDER BY municipio LIMIT 1").fetchone()[0]


def estados(copia: Path) -> list[Estado]:
    """Estados da terceira rodada (D-051): as cinco páginas da história e o município no mapa. O Simulador saiu da
    navegação (app/simulador.py roda à parte) e o Mercado não tem mais filtros por atribuição, situação e classe."""
    pequeno = municipio_pequeno(copia)
    mun = lambda nome: (lambda p: escolher(p, "Município", nome))  # noqa: E731
    mercado = "Onde_está_o_mercado"
    return [Estado("01_resposta", ""),
            Estado("02_quao_certo", "Quão_certo_é"),
            Estado("03_mercado", mercado),
            Estado("03_mercado_bh", mercado, mun("Belo Horizonte"), municipio=True),
            Estado("03_mercado_almenara", mercado, mun("Almenara"), municipio=True),
            Estado("03_mercado_pequeno", mercado, mun(pequeno), municipio=True),
            Estado("03_mercado_campo_azul", mercado, mun("Campo Azul")),
            Estado("04_para_onde_vai", "Para_onde_vai"),
            Estado("05_sobre_os_dados", "Sobre_os_dados")]


def abrir(page, url: str, estado: Estado, erros_console: list) -> None:
    erros_console.clear()
    page.goto(f"{url}/{estado.pagina}")
    esperar(page, 2500)
    estado.acoes(page)
    esperar(page, 2000)


def altura_conteudo(page) -> int:
    """Altura total do conteúdo (o Streamlit rola dentro de um contêiner, não do documento)."""
    return int(page.evaluate("""() => { const m = document.querySelector('[data-testid="stMain"]') ||
                                document.querySelector('section.main'); return m ? m.scrollHeight + 80 : 2000; }"""))


# ------------------------------------------------------------------ checagens (DOM / gráfico renderizado)
# Páginas onde a rolagem horizontal das tabelas é aceita (sem a checagem de "última coluna visível"):
# a Qualidade dos dados é técnica, de auditoria, e as tabelas são largas por natureza (decisão do autor, 2026-10-19).
PAGINAS_COM_ROLAGEM = {"Qualidade_dos_dados"}
JS_CHECAGENS = r"""
(opcoes) => {
  const falhas = [];
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  // 1) texto cortado: elemento visível com scrollWidth > clientWidth (rótulos, cabeçalhos, KPIs)
  const sel = ['[data-testid="stMetricLabel"] p', '[data-testid="stMetricLabel"] div', '[data-testid="stMetricValue"] div',
               '[data-testid="stWidgetLabel"] p', 'h1', 'h2', 'h3', '[data-testid="stTable"] th', '[data-testid="stTable"] td',
               '[data-testid="stExpander"] summary p', '[data-testid="stButton"] p'];
  for (const el of document.querySelectorAll(sel.join(','))) {
    if (vis(el) && el.scrollWidth > el.clientWidth + 1)
      falhas.push(['texto cortado', (el.innerText || '').slice(0, 60)]);
  }
  // 2) tabelas: a última coluna dentro da área visível do contêiner (sem rolagem horizontal).
  //    Não vale na página Qualidade dos dados (opcoes.rolagem_ok): página técnica de auditoria, com tabelas largas
  //    por natureza; a rolagem horizontal ali foi aceita pelo autor (diário, 2026-10-19).
  for (const df of document.querySelectorAll('[data-testid="stDataFrame"]')) {
    if (!vis(df) || opcoes.rolagem_ok) continue;
    const sc = df.querySelector('.dvn-scroller');
    if (sc && sc.scrollWidth > sc.clientWidth + 2)
      falhas.push(['tabela com coluna fora da área visível', `largura ${sc.scrollWidth} > ${sc.clientWidth}`]);
  }
  for (const tb of document.querySelectorAll('[data-testid="stTable"]')) {
    const t = tb.querySelector('table');
    if (t && vis(tb) && !opcoes.rolagem_ok && t.getBoundingClientRect().right > tb.getBoundingClientRect().right + 2)
      falhas.push(['tabela com coluna fora da área visível', (t.querySelector('th:last-child') || {}).innerText || '']);
  }
  // gráficos Plotly já desenhados
  // (_fullData/calcdata: em gd.data os vetores numéricos chegam codificados em binário e não têm .length)
  for (const gd of document.querySelectorAll('.js-plotly-plot')) {
    if (!vis(gd) || !gd._fullData) continue;
    const caixa = gd.getBoundingClientRect();
    const tipos = gd._fullData.map(t => t.type);
    // 3) ranking: toda barra com rótulo, rótulo inteiro dentro da área do gráfico (só nos gráficos de barra com
    //    rótulo de valor; os de grupos e o tornado da Etapa 3 usam a dica do mouse e a tabela de download)
    //    Terceira rodada: o texto esperado é comparado sem as marcas HTML (<b>), e a contagem só vale para gráficos de
    //    uma série de barras (o tornado tem duas, cada uma com os seus rótulos).
    if (tipos.includes('bar') && gd._fullData[tipos.indexOf('bar')].text) {
      const ib = tipos.indexOf('bar'), bar = gd._fullData[ib];
      const uma = tipos.filter(t => t === 'bar').length === 1;
      const nbarras = (gd.calcdata && gd.calcdata[ib]) ? gd.calcdata[ib].length : 0;
      const textos = [...gd.querySelectorAll('.bartext')];
      if (uma && textos.length !== nbarras) falhas.push(['ranking com barra sem rótulo', `${textos.length} rótulos para ${nbarras} barras`]);
      const limpo = s => String(s).replace(/<[^>]+>/g, '');
      textos.forEach((t, i) => { const r = t.getBoundingClientRect();
        if (r.right > caixa.right + 1 || r.left < caixa.left - 1) falhas.push(['rótulo do ranking fora do gráfico', t.textContent]);
        if (uma && bar.text && bar.text[i] !== undefined && t.textContent !== limpo(bar.text[i]))
          falhas.push(['rótulo do ranking truncado', `${t.textContent} ≠ ${limpo(bar.text[i])}`]); });
    }
    // 4) mapa: escala de cores existe e está visível dentro da figura
    if (tipos.includes('choroplethmap')) {
      const cb = gd.querySelector('.colorbar');
      if (!cb) { falhas.push(['mapa sem escala de cores', '']); }
      else { const r = cb.getBoundingClientRect();
        if (r.width < 5 || r.left < caixa.left - 1 || r.right > caixa.right + 1)
          falhas.push(['escala de cores fora da figura', `${Math.round(r.left)}–${Math.round(r.right)} × ${Math.round(caixa.left)}–${Math.round(caixa.right)}`]); }
      // 5) filtro de município: polígono destacado inteiro dentro do enquadramento
      if (opcoes.municipio) {
        const dest = gd._fullData.find(t => t.marker && t.marker.line && t.marker.line.width >= 2 && t.type === 'choroplethmap');
        const m = gd._fullLayout.map, sz = gd._fullLayout._size;
        if (!dest) { falhas.push(['município sem destaque', '']); }
        else {
          const ids = new Set(Array.from(dest.locations || []).map(String));
          const feats = (dest.geojson.features || []).filter(f => ids.has(String(f.id)));
          const escala = 512 * Math.pow(2, m.zoom);
          const px = lon => (lon + 180) / 360 * escala;
          const py = lat => { const s = Math.sin(lat * Math.PI / 180); return (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * escala; };
          const cx = px(m.center.lon), cy = py(m.center.lat);
          let fora = 0, total = 0;
          for (const f of feats) {
            const polys = f.geometry.type === 'MultiPolygon' ? f.geometry.coordinates : [f.geometry.coordinates];
            for (const p of polys) for (const [lon, lat] of p[0]) {
              total++; const x = px(lon) - cx + sz.w / 2, y = py(lat) - cy + sz.h / 2;
              if (x < 0 || x > sz.w || y < 0 || y > sz.h) fora++; } }
          if (!total) falhas.push(['município destacado sem geometria', '']);
          else if (fora) falhas.push(['polígono do município fora do enquadramento', `${fora} de ${total} vértices`]);
        }
      }
    }
  }
  // 6) erros do Streamlit na página
  for (const el of document.querySelectorAll('[data-testid="stException"], [data-testid="stAlertContentError"]'))
    if (vis(el)) falhas.push(['caixa de erro do Streamlit', (el.innerText || '').slice(0, 80)]);
  return falhas;
}
"""


def ouvir_console(page, erros: list) -> None:
    """Junta erros do console e exceções da página. Ignora os 404 de /_stcore/ que o próprio Streamlit gera ao
    abrir uma página por endereço profundo (ex.: /Mercado/_stcore/health, /Mercado/_stcore/host-config): o front
    tenta o caminho relativo antes do da raiz; não vêm do nosso código e a página funciona."""
    def console(m):
        if m.type == "error" and "/_stcore/" not in (m.location or {}).get("url", ""):
            erros.append(m.text)
    page.on("console", console)
    page.on("pageerror", lambda e: erros.append(str(e)))


def checar(page, estado: Estado, largura: int, erros_console: list) -> list[tuple[str, int, str, str]]:
    """Falhas de layout do estado aberto: (estado, largura, elemento/motivo, detalhe)."""
    falhas = page.evaluate(JS_CHECAGENS, {"municipio": estado.municipio,
                                          "rolagem_ok": estado.pagina in PAGINAS_COM_ROLAGEM})
    out = [(estado.nome, largura, motivo, detalhe) for motivo, detalhe in falhas]
    out += [(estado.nome, largura, "erro no console do navegador", e[:120]) for e in erros_console]
    return out
