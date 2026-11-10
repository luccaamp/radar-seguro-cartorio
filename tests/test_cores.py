"""Cores do painel nos dois temas (visual do V5, D-082; regras do autor de 2026-11-10). Lê estilo.css, config.toml e
graficos.py.

- Séries dos gráficos: contraste ≥ 3:1 contra o fundo e as superfícies (WCAG 2.1, 1.4.11, elementos gráficos).
- Mapa e quadro de calor: a escala do V5 muda de cor (amarelo-claro → verde → azul), não só de claridade. Faixas
  vizinhas separadas por ΔE ≥ 15 (CIE 1976; a D-084 errou com faixas do mesmo azul, ≈ 1,3:1), a primeira faixa e o zero
  longe do fundo (ΔE ≥ 20), a ordem de luminosidade certa (no escuro, o maior é o mais claro) e o texto de cada faixa
  legível (≥ 4,5:1). As áreas do mapa têm contorno, então a faixa clara não precisa de 3:1 contra o fundo.
- A interface (verde-petróleo) não se confunde com os dados: o acento fica longe de todas as faixas.
- O fundo do escuro é neutro (sem o matiz dos dados)."""
import re
import tomllib

import pytest

from apoio_painel import RAIZ
from src.painel import graficos

CSS = (RAIZ / "src" / "painel" / "estilo.css").read_text(encoding="utf-8")
TOML = tomllib.loads((RAIZ / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
SERIES = ["s1", "s2", "s3", "ref"]
FAIXAS = [f"mapa-{i}" for i in range(1, 7)]
FUNDOS = ["fundo", "superficie", "superficie-2"]
ESCURO = ':root[data-rd-tema="escuro"]'   # início do bloco do tema escuro no estilo.css


def _lin(h: str) -> list[float]:
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def _lum(h: str) -> float:
    r, g, b = _lin(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a: str, b: str) -> float:
    la, lb = sorted([_lum(a), _lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _lab(h: str) -> tuple[float, float, float]:
    r, g, b = _lin(h)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116  # noqa: E731
    fy = f(_lum(h))
    return 116 * fy - 16, 500 * (f(x) - fy), 200 * (fy - f(z))


def delta_e(a: str, b: str) -> float:
    return sum((p - q) ** 2 for p, q in zip(_lab(a), _lab(b))) ** 0.5


def _tokens(bloco: str) -> dict[str, str]:
    return {k: v.lower() for k, v in re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})\b", bloco)}


def _blocos() -> dict[str, dict[str, str]]:
    claro = _tokens(CSS.split(ESCURO)[0])
    escuro = _tokens(CSS.split(ESCURO)[1].split("\n}")[0])
    return {"claro": claro, "escuro": {**claro, **escuro}}


TEMAS = _blocos()


@pytest.mark.parametrize("tema", ["claro", "escuro"])
@pytest.mark.parametrize("cor", SERIES)
def test_serie_se_destaca_do_fundo_e_das_superficies(tema, cor):
    t = TEMAS[tema]
    for f in FUNDOS:
        assert contraste(t[cor], t[f]) >= 3.0, (tema, cor, t[cor], f, t[f], round(contraste(t[cor], t[f]), 2))


@pytest.mark.parametrize("tema", ["claro", "escuro"])
def test_faixas_vizinhas_do_mapa_se_distinguem(tema):
    t = TEMAS[tema]
    for a, b in zip(["mapa-zero", *FAIXAS], FAIXAS):
        assert delta_e(t[a], t[b]) >= 15, (tema, a, b, round(delta_e(t[a], t[b]), 1))


@pytest.mark.parametrize("tema", ["claro", "escuro"])
def test_primeira_faixa_e_zero_longe_do_fundo(tema):
    t = TEMAS[tema]
    for cor in ("mapa-zero", "mapa-1"):
        for f in FUNDOS:
            assert delta_e(t[cor], t[f]) >= 20, (tema, cor, f, round(delta_e(t[cor], t[f]), 1))


@pytest.mark.parametrize("tema", ["claro", "escuro"])
def test_faixas_do_mapa_em_ordem_de_luminancia(tema):
    lums = [_lum(TEMAS[tema][f]) for f in FAIXAS]
    assert lums == (sorted(lums) if tema == "escuro" else sorted(lums, reverse=True))   # no escuro, maior = mais claro


@pytest.mark.parametrize("tema", ["claro", "escuro"])
@pytest.mark.parametrize("faixa", ["zero", *range(1, 7)])
def test_texto_legivel_em_cada_faixa(tema, faixa):
    t = TEMAS[tema]
    assert contraste(t[f"mapa-{faixa}"], t[f"mapa-tinta-{faixa}"]) >= 4.5, (tema, faixa)


@pytest.mark.parametrize("tema", ["claro", "escuro"])
def test_municipio_sem_cartorio_tem_tom_proprio(tema):
    t = TEMAS[tema]
    for outra in ["mapa-zero", *FAIXAS]:
        assert delta_e(t["mapa-sem"], t[outra]) >= 10, (tema, outra)


@pytest.mark.parametrize("tema", ["claro", "escuro"])
def test_interface_nao_se_confunde_com_os_dados(tema):
    """O verde-petróleo da interface (menu ativo, links, destaques) fica longe de todas as faixas do mapa."""
    t = TEMAS[tema]
    for f in ["mapa-zero", *FAIXAS]:
        assert delta_e(t["acento"], t[f]) >= 15, (tema, f, round(delta_e(t["acento"], t[f]), 1))


def test_fundo_do_escuro_e_neutro():
    for f in FUNDOS:
        r, g, b = (int(TEMAS["escuro"][f][i:i + 2], 16) for i in (1, 3, 5))
        assert max(r, g, b) - min(r, g, b) <= 6, (f, TEMAS["escuro"][f])


@pytest.mark.parametrize("tema", ["claro", "escuro"])
def test_texto_apagado_legivel(tema):
    t = TEMAS[tema]
    for f in FUNDOS:
        assert contraste(t["mudo"], t[f]) >= 4.5, (tema, f)


@pytest.mark.parametrize("tema, chave", [("claro", "light"), ("escuro", "dark")])
def test_tema_do_streamlit_igual_ao_do_css(tema, chave):
    t = TOML["theme"][chave]
    assert t["backgroundColor"].lower() == TEMAS[tema]["fundo"]
    assert t["secondaryBackgroundColor"].lower() == TEMAS[tema]["superficie-2"]
    assert t["primaryColor"].lower() == TEMAS[tema]["acento"]
    assert [c.lower() for c in t["chartCategoricalColors"]] == [TEMAS[tema][s] for s in SERIES]


def test_graficos_com_as_mesmas_cores_e_contraste():
    cores = ["destaque", "comparacao", "terceira", "extremo", "neutro"]
    for nome in cores:
        claro = graficos.COR[nome]
        escuro = graficos.ESCURO[claro]
        assert contraste(claro, graficos.COR["superficie"]) >= 3.0, nome
        assert contraste(escuro, graficos.ESCURO[graficos.COR["superficie"]]) >= 3.0, nome
    assert graficos.ESCURO["#ffffff"] == TEMAS["escuro"]["superficie"]
    assert graficos.SEQUENCIAL == [TEMAS["claro"][f] for f in FAIXAS]
    assert graficos.SEQUENCIAL_ESCURO == [TEMAS["escuro"][f] for f in FAIXAS]
    assert [graficos.COR[n] for n in ("destaque", "comparacao", "terceira")] == [TEMAS["claro"][s] for s in SERIES[:3]]
