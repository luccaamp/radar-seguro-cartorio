"""Galeria de prints do painel (QA visual) e, opcionalmente, as checagens de layout.

Sobe o Streamlit sozinho (porta livre, cópia temporária do banco), percorre os estados fixos em 1280 × 800 e
1920 × 1080, tira um print de página inteira de cada um, gera a galeria e derruba o servidor.

Uso:
  uv run python scripts/prints_painel.py                      # galeria em docs/qa/atual/
  uv run python scripts/prints_painel.py --saida docs/qa/depois --checar
"""
import argparse
import datetime as dt
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright  # noqa: E402

from qa_painel import LARGURAS, RAIZ, abrir, altura_conteudo, checar, estados, ouvir_console, servidor  # noqa: E402


def print_estado(page, estado, largura: int, altura: int, arquivo: Path) -> None:
    if estado.rolar_ate:   # print de uma seção: rola até o título e fotografa a janela
        page.get_by_text(estado.rolar_ate, exact=True).first.scroll_into_view_if_needed()
        page.wait_for_timeout(800)
        page.screenshot(path=str(arquivo))
        return
    alto = max(altura, altura_conteudo(page))   # página inteira: o Streamlit rola dentro de um contêiner
    page.set_viewport_size({"width": largura, "height": alto})
    page.wait_for_timeout(1200)
    page.screenshot(path=str(arquivo), full_page=True)
    page.set_viewport_size({"width": largura, "height": altura})


def galeria(saida: Path, itens: list[dict]) -> None:
    linhas = []
    for it in itens:
        linhas.append(f"""<figure><a href="{it['arquivo']}"><img src="{it['arquivo']}" loading="lazy"></a>
<figcaption><b>{html.escape(it['estado'])}</b> · {it['largura']} px · {it['quando']}</figcaption></figure>""")
    (saida / "galeria.html").write_text(f"""<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<title>Galeria do painel</title><style>
body{{font-family:system-ui,sans-serif;margin:16px;background:#f6f6f4;color:#1d1d1b}}
.grade{{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:16px}}
figure{{margin:0;background:#fff;border:1px solid #ddd;border-radius:6px;padding:8px}}
img{{width:100%;height:420px;object-fit:cover;object-position:top;border:1px solid #eee}}
figcaption{{font-size:13px;margin-top:6px}}</style>
<h1>Galeria do painel</h1><p>{len(itens)} prints · gerada em {dt.datetime.now():%d/%m/%Y %H:%M} · clique para ampliar</p>
<div class="grade">{''.join(linhas)}</div></html>""", encoding="utf-8")


def rodar(saida: Path, checar_layout: bool) -> list:
    saida.mkdir(parents=True, exist_ok=True)
    itens, falhas = [], []
    with servidor() as (url, copia), sync_playwright() as p:
        lista = estados(copia)   # antes de abrir páginas: depois disso o Streamlit segura o arquivo da cópia
        nav = p.chromium.launch()
        for largura, altura in LARGURAS.items():
            page = nav.new_page(viewport={"width": largura, "height": altura}, color_scheme="light")
            erros = []
            ouvir_console(page, erros)
            for est in lista:
                abrir(page, url, est, erros)
                if checar_layout:
                    falhas += checar(page, est, largura, erros)
                arq = saida / f"{est.nome}_{largura}.png"
                print_estado(page, est, largura, altura, arq)
                itens.append({"estado": est.nome, "largura": largura, "arquivo": arq.name,
                              "quando": dt.datetime.now().strftime("%d/%m/%Y %H:%M:%S")})
                print(f"  {est.nome} @ {largura}", flush=True)
            page.close()
        nav.close()
    galeria(saida, itens)
    if checar_layout:
        md = ["# Checagens de layout", "", f"Gerado em {dt.datetime.now():%d/%m/%Y %H:%M}. {len(falhas)} falhas.", "",
              "| Estado | Largura | Elemento / motivo | Detalhe |", "|---|---|---|---|"]
        md += [f"| {e} | {w} | {m} | {html.escape(str(d))} |" for e, w, m, d in falhas]
        (saida / "checagens.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return falhas


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    sys.stderr.reconfigure(encoding="utf-8")
    a = argparse.ArgumentParser()
    a.add_argument("--saida", default=str(RAIZ / "docs" / "qa" / "atual"))
    a.add_argument("--checar", action="store_true", help="também roda as checagens de layout (checagens.md)")
    args = a.parse_args()
    f = rodar(Path(args.saida), args.checar)
    print(f"galeria: {Path(args.saida) / 'galeria.html'}" + (f" | falhas de layout: {len(f)}" if args.checar else ""))
