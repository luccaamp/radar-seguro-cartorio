"""Tabelas gravadas na saída dos notebooks (artefatos das etapas anteriores), para o painel ler sem recalcular.

Alguns resultados só existem na saída de um notebook (o 05b, que treina uma floresta sobre o silver; a tabela de
lacunas do 09; a M5 do 10): o modo demonstração não tem o silver para refazê-los. Os notebooks vão para o git com as
saídas (D-038), então a tabela HTML que o `display()` gravou é a fonte. Cada artefato é achado pelo trecho de código
da célula (`config/painel.yaml`, `artefatos`), não pela posição, e o número volta como texto pt-BR convertido.
"""
import json
import re
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]


class _Tabela(HTMLParser):
    """Lê a primeira <table> de um HTML do pandas: cabeçalho (thead) e linhas (tbody), sem a coluna do índice."""

    def __init__(self):
        super().__init__()
        self.cab, self.linhas, self._linha, self._celula, self._em, self._parte = [], [], None, None, None, None

    def handle_starttag(self, tag, attrs):
        if tag in ("thead", "tbody"):
            self._parte = tag
        elif tag == "tr":
            self._linha = []
        elif tag in ("th", "td"):
            self._em, self._celula = tag, ""

    def handle_endtag(self, tag):
        if tag in ("th", "td") and self._linha is not None:
            self._linha.append((self._em, self._celula.strip()))
            self._em, self._celula = None, None
        elif tag == "tr" and self._linha is not None:
            if self._parte == "thead" and not self.cab:
                self.cab = [t for _, t in self._linha]
            elif self._parte == "tbody":
                self.linhas.append([t for k, t in self._linha if k == "td"])
            self._linha = None

    def handle_data(self, data):
        if self._celula is not None:
            self._celula += data


def numero_br(texto: str) -> float | None:
    """'1.158' → 1158; '144,9' → 144.9; 'R$ 2,3 mi' → 2.3e6; '10,3%' → 0.103; o que não é número → None."""
    t = str(texto).strip()
    m = re.fullmatch(r"(R\$\s*)?(-?[\d.]+(?:,\d+)?)\s*(mil|mi|bi|%)?", t)
    if not m:
        return None
    v = float(m.group(2).replace(".", "").replace(",", "."))
    return v * {"mil": 1e3, "mi": 1e6, "bi": 1e9, "%": 0.01, None: 1}[m.group(3)]


def tabela_html(html: str) -> pd.DataFrame:
    p = _Tabela()
    p.feed(html)
    cab = [c for c in p.cab if c != ""] if p.linhas and len(p.cab) == len(p.linhas[0]) + 1 else p.cab
    return pd.DataFrame(p.linhas, columns=cab)


def ler_notebook(notebook: str) -> dict:
    return json.loads((RAIZ / notebook).read_text(encoding="utf-8"))


def tabela_do_notebook(notebook: str, marcador: str, ordem: int = 0) -> pd.DataFrame:
    """A `ordem`-ésima tabela HTML gravada na saída da célula cujo código contém `marcador`. Erro claro se o notebook
    mudou e o marcador sumiu (o painel avisa, em vez de mostrar número velho)."""
    for celula in ler_notebook(notebook)["cells"]:
        if celula["cell_type"] == "code" and marcador in "".join(celula["source"]):
            htmls = ["".join(o["data"]["text/html"]) for o in celula.get("outputs", [])
                     if "text/html" in o.get("data", {})]
            if len(htmls) > ordem:
                return tabela_html(htmls[ordem])
            raise LookupError(f"{notebook}: a célula de '{marcador}' não tem a tabela {ordem} na saída (rode o notebook)")
    raise LookupError(f"{notebook}: nenhuma célula com '{marcador}'")


def texto_do_notebook(notebook: str, marcador: str) -> str:
    """O texto impresso (print) na saída da célula cujo código contém `marcador`."""
    for celula in ler_notebook(notebook)["cells"]:
        if celula["cell_type"] == "code" and marcador in "".join(celula["source"]):
            return "".join("".join(o.get("text", "")) for o in celula.get("outputs", []))
    raise LookupError(f"{notebook}: nenhuma célula com '{marcador}'")
