"""Acessibilidade (axe-core) das quatro páginas do painel → docs/qa/acessibilidade.md, por gravidade.

Sobe o Streamlit sozinho (mesma rotina dos prints: porta livre, cópia temporária do banco) e roda o axe em
Início, Mercado, Simulador e Qualidade dos dados, em 1280 × 800. Separa o que vem do nosso código (texto, rótulos)
do que vem do próprio Streamlit / Plotly (componentes de terceiros), que fica só como sugestão.

Uso: uv run python scripts/acessibilidade.py
"""
import datetime as dt
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from axe_playwright_python.sync_playwright import Axe  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from qa_painel import RAIZ, esperar, servidor  # noqa: E402

PAGINAS = {"Início": "", "Mercado": "Mercado", "Simulador": "Simulador", "Qualidade dos dados": "Qualidade_dos_dados"}
ORDEM = ["critical", "serious", "moderate", "minor"]
NOME = {"critical": "Crítica", "serious": "Séria", "moderate": "Moderada", "minor": "Menor"}
# regras que o nosso código controla (texto e rótulos); o resto é componente de terceiros
NOSSAS = {"color-contrast", "label", "aria-input-field-name", "select-name", "image-alt", "link-name", "button-name",
          "heading-order", "empty-heading", "page-has-heading-one"}
# contraste: cores que vêm do tema padrão do Streamlit, não de cor escolhida no nosso código
CORES_DO_TEMA = {"#83858c": "cor de legenda do tema (st.caption)", "#adadb2": "rótulo de widget desabilitado",
                 "#ff4b4b": "cor primária do tema (valor do slider)"}
CAUSA = {"heading-order": "st.subheader (h3) logo após st.title (h1), sem h2"}


def _origem(v: dict) -> tuple[bool, str]:
    """(é do nosso código?, causa). Contraste com cor do tema padrão conta como terceiros (sugestão)."""
    if v["id"] == "color-contrast":
        msgs = " ".join((n.get("any") or [{}])[0].get("message", "") for n in v["nodes"])
        causas = sorted({c for cor, c in CORES_DO_TEMA.items() if f"foreground color: {cor}" in msgs})
        if causas:
            return False, "; ".join(causas)
    return v["id"] in NOSSAS, CAUSA.get(v["id"], "")


def rodar(saida: Path) -> list[dict]:
    achados = []
    with servidor() as (url, _), sync_playwright() as p:
        nav = p.chromium.launch()
        page = nav.new_page(viewport={"width": 1280, "height": 800}, color_scheme="light")
        axe = Axe()
        for nome, caminho in PAGINAS.items():
            page.goto(f"{url}/{caminho}")
            esperar(page, 3000)
            for v in axe.run(page).response["violations"]:
                nossa, causa = _origem(v)
                achados.append({"pagina": nome, "regra": v["id"], "gravidade": v.get("impact") or "minor",
                                "descricao": v["help"], "n": len(v["nodes"]), "causa": causa, "nossa": nossa})
        nav.close()
    grupos = defaultdict(list)
    for a in achados:
        grupos[a["gravidade"]].append(a)
    md = ["# Acessibilidade (axe-core)", "",
          f"Gerado em {dt.datetime.now():%d/%m/%Y %H:%M}, 1280 × 800, tema claro. {len(achados)} regras violadas "
          "(somando as páginas). \"Origem\": **nosso** = texto ou rótulo que o nosso código controla; "
          "**terceiros** = componente ou cor do tema padrão do Streamlit / Plotly (fica como sugestão).", ""]
    for g in ORDEM:
        if not grupos[g]:
            continue
        md += [f"## {NOME[g]} ({len(grupos[g])})", "", "| Página | Regra | O que é | Ocorrências | Origem | Causa |",
               "|---|---|---|---|---|---|"]
        md += [f"| {a['pagina']} | `{a['regra']}` | {a['descricao']} | {a['n']} | "
               f"{'nosso' if a['nossa'] else 'terceiros'} | {a['causa']} |" for a in grupos[g]]
        md.append("")
    md += ["## Limitação conhecida (decisão do autor, 2026-10-19)", "",
           "- O contraste das cores padrão do Streamlit (legenda `st.caption`, cor primária no valor do slider) fica "
           "como está. Caminho possível no futuro: um tema próprio no `.streamlit/config.toml`.",
           "- Já corrigidos em 2026-10-19: ordem dos títulos (`st.header` nas seções) e o seletor \"Valor\" do Mercado "
           "(escondido quando o filtro é \"Nenhum\", em vez de desabilitado).", ""]
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text("\n".join(md) + "\n", encoding="utf-8")
    return achados


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    sys.stderr.reconfigure(encoding="utf-8")
    r = rodar(RAIZ / "docs" / "qa" / "acessibilidade.md")
    print(f"{len(r)} violações; nossas: {sum(a['nossa'] for a in r)} → docs/qa/acessibilidade.md")
    for a in r:
        print(f"  [{a['gravidade']}] {a['pagina']}: {a['regra']} ×{a['n']} ({'nosso' if a['nossa'] else 'terceiros'})"
              f" {a['causa']}")
