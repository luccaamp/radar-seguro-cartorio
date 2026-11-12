"""Mapa clicável do painel (D-083): um componente do Streamlit (`st.components.v2`) que desenha os municípios em SVG e
devolve ao Python o município clicado.

Divisão de trabalho, para que quase tudo seja testado em Python (tests/test_mapa.py):
- aqui, em Python: a projeção das geometrias em caminhos SVG, o enquadramento, a faixa de cor de cada município (com o
  zero numa cor neutra), a legenda e a conferência do valor que volta do navegador;
- em src/painel/componentes/mapa.js: só desenhar o que recebe e avisar o clique (testes em tests/js/mapa.test.mjs);
- em src/painel/componentes/mapa.css: as cores de cada faixa, pelos tokens do painel (tema claro e escuro).

O JavaScript nunca monta HTML com texto dos dados (só textContent e atributos), e o Python só aceita de volta um código
que esteja no próprio mapa.
"""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Callable, Iterable

from src.agent.ferramentas import brl

PASTA = Path(__file__).parent / "componentes"
LARGURA = 1000.0          # largura do viewBox; a altura sai da proporção do estado
CASAS = 1                 # casas decimais das coordenadas no viewBox (0,1 de 1000 é menos de 1 px na tela)
N_FAIXAS = 6              # faixas de cor acima de zero (tokens --mapa-1 … --mapa-6 em src/painel/estilo.css)
QUANTIL_TETO = 0.95       # a cor satura no percentil 95, como no mapa anterior (Plotly)
FOLGA = 0.06              # margem em volta do enquadramento, em fração do lado maior
N_ROTULOS = 3             # rótulos com o nome nas áreas de maior valor, com o estado inteiro na tela (V5, D-082)
N_ROTULOS_RECORTE = 8     # numa região (município escolhido): mais nomes, a área é menor (autor, 2026-11-10)
N_CANDIDATOS = 30         # candidatos em ordem de valor; o JS pula os que se sobrepõem e, com zoom, mostra mais
TAMANHO_ROTULO = 0.022    # letra do rótulo em fração da largura do enquadramento, só se o JS não medir a tela


# ------------------------------------------------------------------ projeção
def _aneis(geom: dict) -> list[list[list[float]]]:
    """Todos os anéis (contorno e furos) de um Polygon ou MultiPolygon do GeoJSON."""
    if geom["type"] == "Polygon":
        return list(geom["coordinates"])
    if geom["type"] == "MultiPolygon":
        return [anel for poligono in geom["coordinates"] for anel in poligono]
    raise ValueError(f"geometria sem suporte no mapa: {geom['type']}")


class Projecao:
    """Equiretangular com a longitude encolhida pelo cosseno da latitude média: para um estado, a distorção é pequena
    e o cálculo cabe numa linha. x cresce para o leste e y para o sul (como no SVG)."""

    def __init__(self, geometrias: Iterable[dict], largura: float = LARGURA):
        pts = [p for g in geometrias for anel in _aneis(g) for p in anel]
        if not pts:
            raise ValueError("mapa sem geometrias")
        lons, lats = [p[0] for p in pts], [p[1] for p in pts]
        self.lon0, self.lat1 = min(lons), max(lats)
        self.k = math.cos(math.radians((min(lats) + max(lats)) / 2))
        largura_graus = max((max(lons) - self.lon0) * self.k, 1e-9)
        self.escala = largura / largura_graus
        self.largura = largura
        self.altura = round((self.lat1 - min(lats)) * self.escala, CASAS)

    def xy(self, lon: float, lat: float) -> tuple[float, float]:
        return (round((lon - self.lon0) * self.k * self.escala, CASAS), round((self.lat1 - lat) * self.escala, CASAS))

    def caminho(self, geom: dict) -> str:
        """Caminho SVG ("M x y L … Z" por anel), sem pontos repetidos depois do arredondamento. Anéis que viram um
        ponto só somem; o furo fica com fill-rule evenodd (no CSS)."""
        partes = []
        for anel in _aneis(geom):
            pts: list[tuple[float, float]] = []
            for lon, lat, *_ in anel:
                p = self.xy(lon, lat)
                if not pts or p != pts[-1]:
                    pts.append(p)
            if len(pts) > 1 and pts[0] == pts[-1]:
                pts.pop()
            if len(pts) < 3:
                continue
            partes.append("M" + "L".join(f"{_n(x)} {_n(y)}" for x, y in pts) + "Z")
        return "".join(partes)

    def caixa(self, geometrias: Iterable[dict]) -> tuple[float, float, float, float]:
        """Caixa (x, y, largura, altura) das geometrias no viewBox, com folga, sem sair do estado."""
        pts = [self.xy(p[0], p[1]) for g in geometrias for anel in _aneis(g) for p in anel]
        if not pts:
            return (0.0, 0.0, self.largura, self.altura)
        x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
        y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
        f = FOLGA * max(x1 - x0, y1 - y0, 1.0)
        x0, y0 = max(0.0, x0 - f), max(0.0, y0 - f)
        x1, y1 = min(self.largura, x1 + f), min(self.altura, y1 + f)
        return (round(x0, CASAS), round(y0, CASAS), round(x1 - x0, CASAS), round(y1 - y0, CASAS))


def _n(v: float) -> str:
    """Número curto no SVG: sem ".0" e sem "-0"."""
    s = f"{v:.{CASAS}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ------------------------------------------------------------------ cor
def faixas(valores: dict[str, float | None], n: int = N_FAIXAS, quantil: float = QUANTIL_TETO,
           fmt: Callable[[float], str] | None = None,
           teto_fixo: float | None = None) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Faixa de cor de cada área e a legenda.

    A escala é calculada só com os valores recebidos (o recorte que está na tela). Zero tem a faixa "zero" (cor neutra,
    fora da escala); sem valor, "sem". Acima de zero, faixas de largura igual a um passo REDONDO, o primeiro que cobre
    o teto (percentil `quantil` dos valores positivos) com as n − 1 primeiras faixas; a última fica para o que passa
    disso ("mais de …"). `fmt` escreve os limites (padrão: R$ curto). Com `teto_fixo` (ex.: 1 para um percentual),
    nada passa do teto: o passo redondo cobre o teto com as n faixas, e a última diz "até …" (sem "mais de 100%")."""
    fmt = fmt or brl_curto
    positivos = sorted(v for v in valores.values() if v is not None and v > 0)
    if teto_fixo is not None:
        passo = passo_redondo(teto_fixo / n) if teto_fixo > 0 else 0.0
        n = min(n, math.ceil(teto_fixo / passo - 1e-9)) if passo > 0 else n
        teto = teto_fixo
    else:
        teto = _quantil(positivos, quantil) if positivos else 0.0
        passo = passo_redondo(teto / max(n - 1, 1)) if teto > 0 else 0.0
    out: dict[str, str] = {}
    for area, v in valores.items():
        if v is None or (isinstance(v, float) and math.isnan(v)):
            out[area] = "sem"
        elif v <= 0:
            out[area] = "zero"
        else:
            out[area] = str(min(n, max(1, math.ceil(v / passo)))) if passo > 0 else str(n)
    legenda = [{"faixa": "zero", "texto": "Zero"}]
    if passo > 0:
        legenda += [{"faixa": str(i), "texto": f"até {fmt(passo * i)}"} for i in range(1, n)]
        legenda.append({"faixa": str(n), "texto": f"até {fmt(min(passo * n, teto))}" if teto_fixo is not None
                        else f"mais de {fmt(passo * (n - 1))}"})
    return out, legenda


def passo_redondo(x: float) -> float:
    """O menor número "redondo" (1; 1,5; 2; 2,5; 3; 4; 5; 6 ou 8 vezes uma potência de 10) maior ou igual a x > 0."""
    if x <= 0:
        raise ValueError("passo precisa ser positivo")
    base = 10 ** math.floor(math.log10(x))
    for m in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if m * base >= x * (1 - 1e-12):
            return m * base
    return 10 * base


def brl_curto(v: float) -> str:
    """R$ sem o ",0" dos números redondos da legenda ("R$ 50 mil", não "R$ 50,0 mil")."""
    return re.sub(r",0(?= )", "", brl(v))


def pct_curto(v: float) -> str:
    """Percentual (0,25 → "25%"; 0,125 → "12,5%") para a legenda dos mapas em %."""
    s = f"{100 * v:.1f}".replace(".", ",")
    return (s[:-2] if s.endswith(",0") else s) + "%"


def _quantil(ordenados: list[float], q: float) -> float:
    """Quantil com interpolação linear (o mesmo do pandas), sem depender do pandas."""
    if len(ordenados) == 1:
        return ordenados[0]
    pos = (len(ordenados) - 1) * q
    i = int(math.floor(pos))
    j = min(i + 1, len(ordenados) - 1)
    return ordenados[i] + (ordenados[j] - ordenados[i]) * (pos - i)


# ------------------------------------------------------------------ rótulos
def _area_e_centro(anel: list[list[float]]) -> tuple[float, float, float]:
    """Área (com sinal, fórmula do laço) e centroide de um anel."""
    a = cx = cy = 0.0
    for (x0, y0, *_), (x1, y1, *_) in zip(anel, anel[1:] + anel[:1]):
        c = x0 * y1 - x1 * y0
        a += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    if abs(a) < 1e-15:
        xs, ys = [p[0] for p in anel], [p[1] for p in anel]
        return 0.0, sum(xs) / len(xs), sum(ys) / len(ys)
    return a / 2, cx / (3 * a), cy / (3 * a)


def _dentro(x: float, y: float, aneis: list[list[list[float]]]) -> bool:
    """Ponto dentro do polígono (contorno e furos), pela regra par-ímpar."""
    dentro = False
    for anel in aneis:
        for (x0, y0, *_), (x1, y1, *_) in zip(anel, anel[1:] + anel[:1]):
            if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
                dentro = not dentro
    return dentro


def ponto_interno(geom: dict) -> tuple[float, float]:
    """Um ponto (lon, lat) DENTRO do maior pedaço da geometria, para o rótulo: o centroide, se cair dentro; senão, o
    ponto de uma grade 21 × 21 na caixa do pedaço que fica dentro e mais perto do centroide (município côncavo)."""
    poligonos = [geom["coordinates"]] if geom["type"] == "Polygon" else list(geom["coordinates"])
    maior = max(poligonos, key=lambda p: abs(_area_e_centro(p[0])[0]))
    _, cx, cy = _area_e_centro(maior[0])
    if _dentro(cx, cy, maior):
        return cx, cy
    xs, ys = [p[0] for p in maior[0]], [p[1] for p in maior[0]]
    candidatos = [(x0 + (x1 - x0) * i / 20, y0 + (y1 - y0) * j / 20)
                  for x0, x1, y0, y1 in [(min(xs), max(xs), min(ys), max(ys))] for i in range(1, 20) for j in range(1, 20)]
    dentro = [p for p in candidatos if _dentro(p[0], p[1], maior)]
    return min(dentro, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2) if dentro else (cx, cy)


# ------------------------------------------------------------------ dados do componente
def dados_mapa(geometrias: dict[str, dict], valores: dict[str, float | None], nomes: dict[str, str],
               textos: dict[str, str], *, fundo: Iterable[dict] = (), selecionado: str | None = None,
               enquadrar: Iterable[str] | None = None, titulo_legenda: str = "", resumo: str = "",
               legenda_fundo: str = "", rotulos: int | None = None, rotulo_inteiro: str = "Ver o estado inteiro",
               fmt_legenda: Callable[[float], str] | None = None, teto_fixo: float | None = None,
               legenda_sem: str = "", rotular_todas: bool = False) -> dict[str, Any]:
    """O que o componente recebe (JSON): viewBox, áreas com caminho, faixa, nome e texto do balão, áreas de fundo
    (não clicáveis), legenda, o selecionado e os rótulos. `enquadrar` limita o viewBox a essas áreas (zoom num
    recorte); `viewBoxInteiro` é o estado inteiro, para o botão `rotulo_inteiro` e os limites do zoom e do arrastar.
    Rótulos: até N_CANDIDATOS áreas de maior valor do recorte (as enquadradas, ou todas), em ordem; o JS mostra as
    `rotulos` primeiras que estão na tela e não se sobrepõem (sem `rotulos`: N_ROTULOS no estado inteiro,
    N_ROTULOS_RECORTE numa região; com zoom, o JS mostra mais), com a letra de tamanho fixo em px (`tamanhoRotulo` é
    só a reserva, proporcional à largura do enquadramento)."""
    fundo = list(fundo)
    proj = Projecao(list(geometrias.values()) + fundo)
    cor, legenda = faixas({a: valores.get(a) for a in geometrias}, fmt=fmt_legenda, teto_fixo=teto_fixo)
    no_recorte = [a for a in (enquadrar or []) if a in geometrias]
    alvo = [geometrias[a] for a in no_recorte]
    caixa = proj.caixa(alvo) if alvo else (0.0, 0.0, proj.largura, proj.altura)
    sel = selecionado if selecionado in geometrias else None
    if rotulos is None:
        rotulos = N_ROTULOS_RECORTE if no_recorte else N_ROTULOS
    def _maiores(ids) -> list[str]:
        if rotular_todas:   # todas as áreas, as de maior valor primeiro (o mapa do Brasil, D-088: o nome de cada UF)
            return sorted(ids, key=lambda a: (-(_valor(valores.get(a)) or 0), a))[:max(rotulos, 0)]
        com_valor = [a for a in ids if (_valor(valores.get(a)) or 0) > 0]
        return sorted(com_valor, key=lambda a: (-float(valores[a]), a))[:N_CANDIDATOS if rotulos > 0 else 0]

    def _rotulos(ids) -> list[dict]:
        return [{"id": a, "texto": nomes.get(a, a), **dict(zip(("x", "y"), proj.xy(*ponto_interno(geometrias[a]))))}
                for a in ids]

    maiores = _maiores(no_recorte or geometrias)
    # com o estado inteiro na tela (botão "Ver o estado inteiro"), os nomes são os maiores do estado
    maiores_estado = _maiores(geometrias) if no_recorte else []
    return {
        "viewBox": " ".join(_n(v) for v in caixa),
        "viewBoxInteiro": " ".join(_n(v) for v in (0.0, 0.0, proj.largura, proj.altura)),
        "rotuloInteiro": rotulo_inteiro,
        "areas": [{"id": a, "d": proj.caminho(g), "faixa": cor[a], "valor": _valor(valores.get(a)),
                   "nome": nomes.get(a, a), "texto": textos.get(a, "")} for a, g in geometrias.items()],
        "fundo": [{"d": proj.caminho(g)} for g in fundo],
        "selecionado": sel,
        # áreas sem valor (o mapa do Brasil: as UFs sem o estudo do seguro) ganham um item na legenda, em hachura
        "legenda": legenda + ([{"faixa": "sem", "texto": legenda_sem}] if legenda_sem else []),
        "tituloLegenda": titulo_legenda,
        "legendaFundo": legenda_fundo,
        "resumo": resumo,
        "rotulos": _rotulos(maiores),
        "maxRotulos": max(0, rotulos),
        "rotulosInteiro": _rotulos(maiores_estado),
        "maxRotulosInteiro": N_ROTULOS if rotulos > 0 else 0,
        "tamanhoRotulo": round(caixa[2] * TAMANHO_ROTULO, 1),
    }


def _valor(v: float | None) -> float | None:
    """Valor em JSON: None no lugar de NaN (o JSON não tem NaN), arredondado ao centavo."""
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else round(float(v), 2)


def clique_valido(valor: Any, ids: Iterable[str]) -> str | None:
    """O código clicado, só se for uma área do mapa (o valor vem do navegador: nunca confiar sem conferir)."""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        valor = str(int(valor))
    return valor if isinstance(valor, str) and valor in set(ids) else None


# ------------------------------------------------------------------ componente do Streamlit
_componente = None


def _registrar():
    global _componente
    if _componente is None:
        import streamlit as st
        _componente = st.components.v2.component(
            "radar_mapa",
            html='<div class="rd-mapa"></div>',
            css=(PASTA / "mapa.css").read_text(encoding="utf-8"),
            js=(PASTA / "mapa.js").read_text(encoding="utf-8"),
        )
    return _componente


def mapa_clicavel(dados: dict[str, Any], key: str, ao_escolher: Callable[[str], None] | None = None) -> str | None:
    """Mostra o mapa e devolve o código da área clicada nesta execução (ou None). `ao_escolher` roda antes da página
    ser executada de novo, então pode mudar o valor de outro widget (por exemplo, o seletor de município)."""
    import streamlit as st
    ids = [a["id"] for a in dados["areas"]]

    def _ao_mudar() -> None:
        escolhido = clique_valido((st.session_state.get(key) or {}).get("municipio"), ids)
        if escolhido and ao_escolher:
            ao_escolher(escolhido)

    resultado = _registrar()(data=dados, key=key, on_municipio_change=_ao_mudar)
    return clique_valido(getattr(resultado, "municipio", None), ids)
