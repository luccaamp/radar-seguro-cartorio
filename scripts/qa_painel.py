"""QA visual do painel: servidor próprio, estados fixos e checagens de layout no navegador (Playwright + Chromium).

Usado por scripts/prints_painel.py (galeria), tests/test_visual.py (checagens) e scripts/acessibilidade.py (axe).
- O servidor sobe o Streamlit numa porta livre sobre uma CÓPIA temporária do banco (RADAR_BANCO); nada é gravado em
  data/ e o Streamlit do autor não é usado.
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
LARGURAS = {1280: 800, 1920: 1080}


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
    env = os.environ | {"RADAR_BANCO": str(copia), "PYTHONIOENCODING": "utf-8"}
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
    pequeno = municipio_pequeno(copia)
    filtro = lambda tipo, valor: (lambda p: (escolher(p, "Filtrar por", tipo), escolher(p, "Valor", valor)))  # noqa: E731
    mun = lambda nome: (lambda p: escolher(p, "Município", nome))  # noqa: E731
    out = [Estado("01_inicio", "")]
    for i, (rot, opc) in enumerate([("deficit", "Déficit (base)"), ("passivo", "Passivo de todas as ativas (base)"),
                                    ("serventias", "Serventias ativas"), ("empregados", "Empregados CLT")]):
        out.append(Estado(f"02_mercado_{rot}", "Mercado", (lambda o: lambda p: marcar(p, o))(opc)))
    for c in ("1", "2", "3", "Indeterminada"):
        valor = f"Classe {c}" if c != "Indeterminada" else c
        out.append(Estado(f"03_classe_{c.lower()}", "Mercado", filtro("Classe (Prov. 213, regra base)", valor)))
    out += [Estado("04_situacao_provida", "Mercado", filtro("Situação", "Provida (titular)")),
            Estado("04_situacao_vaga", "Mercado", filtro("Situação", "Vaga (interino)")),
            Estado("05_atribuicao_notas", "Mercado", filtro("Atribuição", "Notas")),
            Estado("05_atribuicao_ri", "Mercado", filtro("Atribuição", "Registro de Imóveis")),
            Estado("06_municipio_bh", "Mercado", mun("Belo Horizonte"), municipio=True),
            Estado("06_municipio_almenara", "Mercado", mun("Almenara"), municipio=True),
            Estado("06_municipio_pequeno", "Mercado", mun(pequeno), municipio=True),
            Estado("06_municipio_campo_azul", "Mercado", mun("Campo Azul")),
            Estado("07_bh_classe_3", "Mercado", lambda p: (mun("Belo Horizonte")(p),
                                                          filtro("Classe (Prov. 213, regra base)", "Classe 3")(p))),
            Estado("08_regra_100_mil", "Mercado", lambda p: marcar(p, "R$ 100 mil")),
            Estado("09_simulador_padrao", "Simulador"),
            Estado("09_simulador_taxa_3", "Simulador",
                   lambda p: deslizar(p, "Taxa anual (% da importância segurada)", 10)),
            Estado("09_simulador_stf_suspende", "Simulador", lambda p: marcar(p, "STF suspende arts. 8º a 17")),
            Estado("09_simulador_decisao_parcial", "Simulador", lambda p: marcar(p, "Decisão parcial")),
            Estado("10_qualidade_topo", "Qualidade_dos_dados"),
            Estado("10_qualidade_grafico", "Qualidade_dos_dados", rolar_ate="Conferência entre fontes"),
            Estado("10_qualidade_limitacoes", "Qualidade_dos_dados", rolar_ate="Limitações declaradas")]
    return out


def abrir(page, url: str, estado: Estado, erros_console: list) -> None:
    erros_console.clear()
    page.goto(f"{url}/{estado.pagina}")
    esperar(page, 2500)
    estado.acoes(page)
    esperar(page, 2000)
    if estado.pagina == "Mercado":   # abre a tabela por área/região (expansor) para entrar no print e nas checagens
        for s in page.locator('[data-testid="stExpander"] details:not([open]) > summary').all():
            s.click()
        page.wait_for_timeout(800)


def altura_conteudo(page) -> int:
    """Altura total do conteúdo (o Streamlit rola dentro de um contêiner, não do documento)."""
    return int(page.evaluate("""() => { const m = document.querySelector('[data-testid="stMain"]') ||
                                document.querySelector('section.main'); return m ? m.scrollHeight + 80 : 2000; }"""))


# ------------------------------------------------------------------ checagens (DOM / gráfico renderizado)
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
  // 2) tabelas: a última coluna dentro da área visível do contêiner (sem rolagem horizontal)
  for (const df of document.querySelectorAll('[data-testid="stDataFrame"]')) {
    if (!vis(df)) continue;
    const sc = df.querySelector('.dvn-scroller');
    if (sc && sc.scrollWidth > sc.clientWidth + 2)
      falhas.push(['tabela com coluna fora da área visível', `largura ${sc.scrollWidth} > ${sc.clientWidth}`]);
  }
  for (const tb of document.querySelectorAll('[data-testid="stTable"]')) {
    const t = tb.querySelector('table');
    if (t && vis(tb) && t.getBoundingClientRect().right > tb.getBoundingClientRect().right + 2)
      falhas.push(['tabela com coluna fora da área visível', (t.querySelector('th:last-child') || {}).innerText || '']);
  }
  // gráficos Plotly já desenhados
  // (_fullData/calcdata: em gd.data os vetores numéricos chegam codificados em binário e não têm .length)
  for (const gd of document.querySelectorAll('.js-plotly-plot')) {
    if (!vis(gd) || !gd._fullData) continue;
    const caixa = gd.getBoundingClientRect();
    const tipos = gd._fullData.map(t => t.type);
    // 3) ranking: toda barra com rótulo, rótulo inteiro dentro da área do gráfico
    if (tipos.includes('bar')) {
      const ib = tipos.indexOf('bar'), bar = gd._fullData[ib];
      const nbarras = (gd.calcdata && gd.calcdata[ib]) ? gd.calcdata[ib].length : 0;
      const textos = [...gd.querySelectorAll('.bartext')];
      if (textos.length !== nbarras) falhas.push(['ranking com barra sem rótulo', `${textos.length} rótulos para ${nbarras} barras`]);
      textos.forEach((t, i) => { const r = t.getBoundingClientRect();
        if (r.right > caixa.right + 1 || r.left < caixa.left - 1) falhas.push(['rótulo do ranking fora do gráfico', t.textContent]);
        if (bar.text && bar.text[i] !== undefined && t.textContent !== String(bar.text[i]))
          falhas.push(['rótulo do ranking truncado', `${t.textContent} ≠ ${bar.text[i]}`]); });
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
    falhas = page.evaluate(JS_CHECAGENS, {"municipio": estado.municipio})
    out = [(estado.nome, largura, motivo, detalhe) for motivo, detalhe in falhas]
    out += [(estado.nome, largura, "erro no console do navegador", e[:120]) for e in erros_console]
    return out
