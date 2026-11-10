"""Grade Taxa × adesão em "Quão certo é" (V5, D-082; bloco "painel de MG rumo ao V5", item 4): os dados
(src/painel/analises.grade_taxa_adesao), o quadro de calor em HTML (src/painel/ui.quadro_calor) e o contraste do texto
em cada cor, nos dois temas (WCAG AA: 4,5 para texto normal). Modo demonstração."""
import re

import duckdb
import pytest

from apoio_painel import HISTORIA, RAIZ

CERTO = HISTORIA[1]
CSS = (RAIZ / "src" / "painel" / "estilo.css").read_text(encoding="utf-8")


@pytest.fixture
def con(painel_demo):
    with duckdb.connect(str(painel_demo["banco"]), read_only=True) as c:
        yield c


def test_grade_3x3_com_a_celula_base_no_premio_oficial(con):
    from src.painel import analises
    g = analises.grade_taxa_adesao(con, "MG")
    assert g["taxas"] == ["1%", "2%", "3,5%"] and [x["adesao"] for x in g["quadro"]] == ["25%", "50%", "70%"]
    bases = [c for x in g["quadro"] for c in x["celulas"] if c["base"]]
    assert len(bases) == 1
    premio = {x["chave"]: x["valor"] for x in analises.numeros_oficiais(con, "MG")["numeros"]}["premio"]
    assert bases[0]["premio"] == premio == "R$ 341,1 mil"
    assert g["base"] == "taxa de 2% e adesão de 50%"
    # a cor cresce com o prêmio (linha e coluna)
    for x in g["quadro"]:
        assert [int(c["faixa"]) for c in x["celulas"]] == sorted(int(c["faixa"]) for c in x["celulas"])


def test_quadro_calor_html(monkeypatch):
    from src.painel import ui
    saida = []
    monkeypatch.setattr(ui, "_html", saida.append)
    ui.quadro_calor("Adesão", "taxa", ["1%", "2%"],
                    [("25%", [{"texto": "R$ 1", "faixa": "1"}, {"texto": "R$ 2", "faixa": "2", "base": True}]),
                     ("50%", [{"texto": "<b>x</b>", "faixa": "6"}, {"texto": "R$ 4", "faixa": "zero"}])])
    html = saida[0].replace("&#36;", "$")   # ui._t troca "$" por &#36; (o Markdown do Streamlit leria fórmula)
    assert '<th scope="row">25%</th><td class="rd-calor-1">R$ 1</td>' in html
    assert '<td class="rd-calor-2 rd-calor-base">R$ 2<span class="rd-calor-marca"> base</span></td>' in html
    assert "&lt;b&gt;x&lt;/b&gt;" in html and "<b>x</b>" not in html          # texto escapado
    assert html.count('scope="col"') == 3


def _tokens(bloco: str) -> dict[str, str]:
    return dict(re.findall(r"--(mapa-[\w-]+|titulo|superficie):\s*(#[0-9a-fA-F]{6})", bloco))


def _contraste(a: str, b: str) -> float:
    def lum(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


@pytest.mark.parametrize("tema", ["claro", "escuro"])
def test_contraste_do_texto_em_cada_cor(tema):
    """Cada faixa com o texto da sua --mapa-tinta-* (estilo.css): todas com 4,5 ou mais, nos dois temas."""
    claro = _tokens(CSS.split(':root[data-rd-tema="escuro"]')[0])
    escuro = {**claro, **_tokens(CSS.split(':root[data-rd-tema="escuro"]')[1].split("}")[0])}
    t = claro if tema == "claro" else escuro
    for f in ["zero", "1", "2", "3", "4", "5", "6"]:
        texto = t[f"mapa-tinta-{f}"]
        assert _contraste(t[f"mapa-{f}"], texto) >= 4.5, (tema, f, t[f"mapa-{f}"], texto)
        assert re.search(rf"td\.rd-calor-{f} \{{ background: var\(--mapa-{f}\); color: var\(--mapa-tinta-{f}\); \}}", CSS)


def test_pagina_mostra_a_grade(painel_demo):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / CERTO), default_timeout=120).run()
    assert not at.exception
    assert [h.value for h in at.header] == ["Taxa × adesão"]
    tela = "\n".join(m.value for m in at.markdown)
    assert tela.count('class="rd-calor-') >= 9 and "rd-calor-base" in tela
