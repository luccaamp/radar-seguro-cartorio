"""Cores do painel nos dois temas (regra do autor, 2026-11-10): nenhuma cor de dado (mapa, quadro de calor, séries dos
gráficos) pode se confundir com o fundo ou com as superfícies. Critério: contraste ≥ 3:1 (WCAG 2.1, 1.4.11, elementos
gráficos). O fundo do tema escuro é cinza neutro, sem o matiz azul dos dados. Lê estilo.css, config.toml e graficos.py."""
import re
import tomllib

import pytest

from apoio_painel import RAIZ
from src.painel import graficos

CSS = (RAIZ / "src" / "painel" / "estilo.css").read_text(encoding="utf-8")
TOML = tomllib.loads((RAIZ / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
DADOS = ["mapa-zero", "mapa-1", "mapa-2", "mapa-3", "mapa-4", "mapa-5", "mapa-6", "s1", "s2", "s3", "ref"]
FUNDOS = ["fundo", "superficie", "superficie-2"]
ESCURO = ':root[data-rd-tema="escuro"]'   # início do bloco do tema escuro no estilo.css


def _lum(h: str) -> float:
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contraste(a: str, b: str) -> float:
    la, lb = sorted([_lum(a), _lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _tokens(bloco: str) -> dict[str, str]:
    return {k: v.lower() for k, v in re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})\b", bloco)}


def _blocos() -> dict[str, dict[str, str]]:
    claro = _tokens(CSS.split(ESCURO)[0])
    escuro = _tokens(CSS.split(ESCURO)[1].split("@media")[0])
    sistema = _tokens(CSS.split("@media (prefers-color-scheme: dark)")[1].split("} }")[0])
    return {"claro": claro, "escuro": {**claro, **escuro}, "sistema": {**claro, **sistema}}


TEMAS = _blocos()


def test_escuro_pelo_marcador_e_pelo_sistema_sao_iguais():
    assert TEMAS["escuro"] == TEMAS["sistema"]


@pytest.mark.parametrize("tema", ["claro", "escuro"])
@pytest.mark.parametrize("cor", DADOS)
def test_cor_de_dado_se_destaca_do_fundo_e_das_superficies(tema, cor):
    t = TEMAS[tema]
    for f in FUNDOS:
        assert contraste(t[cor], t[f]) >= 3.0, (tema, cor, t[cor], f, t[f], round(contraste(t[cor], t[f]), 2))


@pytest.mark.parametrize("tema", ["claro", "escuro"])
def test_municipio_sem_cartorio_tem_tom_proprio(tema):
    t = TEMAS[tema]
    for outra in [*FUNDOS, "mapa-zero"]:
        assert contraste(t["mapa-sem"], t[outra]) >= 1.3, (tema, outra)


@pytest.mark.parametrize("tema", ["claro", "escuro"])
def test_faixas_do_mapa_em_ordem_de_luminancia(tema):
    lums = [_lum(TEMAS[tema][f"mapa-{i}"]) for i in range(1, 7)]
    assert lums == (sorted(lums) if tema == "escuro" else sorted(lums, reverse=True))   # no escuro, maior = mais claro
    assert all(contraste(TEMAS[tema][f"mapa-{i}"], TEMAS[tema][f"mapa-{i + 1}"]) >= 1.25 for i in range(1, 6))


def test_fundo_do_escuro_e_cinza_neutro():
    for f in FUNDOS:
        r, g, b = (int(TEMAS["escuro"][f][i:i + 2], 16) for i in (1, 3, 5))
        assert max(r, g, b) - min(r, g, b) <= 6, (f, TEMAS["escuro"][f])


@pytest.mark.parametrize("tema, chave", [("claro", "light"), ("escuro", "dark")])
def test_tema_do_streamlit_igual_ao_do_css(tema, chave):
    t = TOML["theme"][chave]
    assert t["backgroundColor"].lower() == TEMAS[tema]["fundo"]
    assert t["secondaryBackgroundColor"].lower() == TEMAS[tema]["superficie-2"]
    assert [c.lower() for c in t["chartCategoricalColors"]] == [TEMAS[tema][s] for s in ("s1", "s2", "s3", "ref")]


def test_graficos_com_as_mesmas_cores_e_contraste():
    cores = ["destaque", "comparacao", "terceira", "extremo", "neutro"]
    for nome in cores:
        claro = graficos.COR[nome]
        escuro = graficos.ESCURO[claro]
        assert contraste(claro, graficos.COR["superficie"]) >= 3.0, nome
        assert contraste(escuro, graficos.ESCURO[graficos.COR["superficie"]]) >= 3.0, nome
    assert graficos.ESCURO["#ffffff"] == TEMAS["escuro"]["superficie"]
    assert graficos.SEQUENCIAL == [TEMAS["claro"][f"mapa-{i}"] for i in range(1, 7)]
    assert graficos.SEQUENCIAL_ESCURO == [TEMAS["escuro"][f"mapa-{i}"] for i in range(1, 7)]
