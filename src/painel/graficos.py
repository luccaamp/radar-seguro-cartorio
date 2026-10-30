"""Gráficos do painel (Plotly): um template único e uma função por gráfico, que recebe o resultado de
src/painel/analises.py (nunca consulta o banco). Padrão em docs/painel/padrao_visual.md (terceira rodada).

Regras do template: fonte IBM Plex Sans e título em Newsreader (D-052); fundo branco e grade quase invisível; título à
esquerda que diz a conclusão; subtítulo
com o que está plotado e a unidade; rótulos diretos nos dados em vez de legenda; uma linha pequena de fonte embaixo, só
com a fonte e a data; uma cor de destaque para a série principal e uma segunda cor só para comparação; números no
formato brasileiro; sem eixo duplo, sem 3D, sem pizza e sem escala log.
"""
import json
import math
import re

import plotly.graph_objects as go
import plotly.io as pio

from src.agent.ferramentas import brl

# tokens do "Raio-X do Cartório" (D-052), com os mesmos valores: séries s1 (azul), s2 (laranja), s3 (verde) e ref
# (cinza); texto ink / ink-2 / muted; grade grid / grid-strong; laranja sempre com rótulo direto (contraste < 3:1)
COR = {
    "destaque": "#2a78d6", "destaque_claro": "#c3d1e8", "comparacao": "#eb6834", "terceira": "#1baf7a",
    "neutro": "#2a78d6",          # degraus que levam à resposta: a série s1; o último (o prêmio) vai em s2
    "extremo": "#8d97ab",         # extremos teóricos: discretos (ref)
    "titulo": "#0f1c33", "texto": "#0f1c33", "texto_2": "#45506a", "mudo": "#6b7590",
    "grade": "#e6e9ef", "eixo": "#c2c9d6", "superficie": "#ffffff", "linha": "#dde2ea",
}
FAIXA = "rgba(42,120,214,0.18)"          # faixa provável (P5–P95) e faixa da projeção (P10–P90): s1 translúcido
BARRA = dict(line=dict(color="#ffffff", width=2), cornerradius=4)   # barras do Raio-X: borda branca de 2 px, cantos de 4 px
# mapa: do azul-claro do agregado ao azul-marinho da faixa, passando pela série s1
SEQUENCIAL = ["#e8eef8", "#c3d1e8", "#8fb3e6", "#5a94e0", "#2a78d6", "#2056a8", "#183564"]

# tema escuro do Raio-X: cada cor clara acima e a equivalente escura (--surface, --ink, --line, --s1 … do artefato).
# No mapa a escala se inverte em luminosidade: no escuro, o valor maior é o azul mais claro.
ESCURO = {
    "#ffffff": "#141a25", "#f5f7fa": "#1a2130", "#0f1c33": "#e9edf5", "#45506a": "#b2bccd", "#6b7590": "#8793a8",
    "#dde2ea": "#262e3d", "#e6e9ef": "#222a38", "#c2c9d6": "#3a4558",
    "#2a78d6": "#3987e5", "#eb6834": "#d95926", "#1baf7a": "#199e70", "#8d97ab": "#7b869b",
    "#e8eef8": "#1d2840", "#c3d1e8": "#2c3d62", "#8fb3e6": "#2a5aa0", "#5a94e0": "#3373c8", "#2056a8": "#74aef0",
    "#183564": "#b4d3f8",
    "rgba(42,120,214,0.18)": "rgba(57,135,229,0.24)", "rgba(255,255,255,0.85)": "rgba(20,26,37,0.85)",
}
_COR_RE = re.compile(r"#[0-9a-fA-F]{6}\b|rgba\([^)]*\)")


def _escurecer(fig: go.Figure) -> go.Figure:
    """A mesma figura com as cores do tema escuro do Raio-X (troca única, sem encadear) e o fundo do mapa escuro."""
    troca = lambda m: ESCURO.get(m.group(0).lower().replace(" ", ""), m.group(0))  # noqa: E731
    fig = go.Figure(json.loads(_COR_RE.sub(troca, fig.to_json())))
    if fig.layout.map and fig.layout.map.style == "white-bg":   # sem mapa de fundo: só a cor da superfície
        fig.update_layout(map_style={"version": 8, "sources": {}, "layers": [
            {"id": "fundo", "type": "background", "paint": {"background-color": ESCURO["#ffffff"]}}]})
    return fig
FONTE = "'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
FONTE_TITULO = "Newsreader, Georgia, 'Times New Roman', serif"
BORDA = 24      # px entre a borda do cartão e o título / rodapé (múltiplo de 8)
TOPO = 80       # px do título + subtítulo

pio.templates["radar"] = go.layout.Template(layout=go.Layout(
    font=dict(family=FONTE, size=12, color=COR["texto_2"]),
    title=dict(font=dict(family=FONTE_TITULO, size=18, weight=600, color=COR["titulo"]), x=0, xanchor="left",
               xref="container", y=1, yref="container",
               yanchor="top", pad=dict(t=BORDA, l=BORDA)),
    paper_bgcolor=COR["superficie"], plot_bgcolor=COR["superficie"], separators=",.",
    colorway=[COR["destaque"], COR["comparacao"], COR["terceira"], COR["extremo"]],
    xaxis=dict(automargin=True, showgrid=False, linecolor=COR["eixo"], ticks="", zeroline=False,
               title=dict(font=dict(size=12, color=COR["texto_2"])), tickfont=dict(color=COR["texto_2"], size=12)),
    yaxis=dict(automargin=True, showgrid=True, gridcolor=COR["grade"], gridwidth=1, zeroline=False, showline=False,
               title=dict(font=dict(size=12, color=COR["texto_2"])), tickfont=dict(color=COR["texto_2"], size=12)),
    hoverlabel=dict(bgcolor=COR["superficie"], bordercolor=COR["linha"], font=dict(family=FONTE, size=13, color=COR["texto"])),
    margin=dict(l=BORDA, r=BORDA, t=TOPO, b=56), bargap=0.35, showlegend=False,
))
pio.templates.default = "radar"


def _linhas(texto: str, n: int) -> list[str]:
    """Quebra o texto em linhas de até `n` caracteres, nas palavras (o Plotly não quebra título nem anotação)."""
    linhas, atual = [], ""
    for p in texto.split():
        if atual and len(atual) + 1 + len(p) > n:
            linhas.append(atual)
            atual = p
        else:
            atual = f"{atual} {p}".strip()
    return linhas + ([atual] if atual else [])


# caracteres por linha que cabem no celular (390 px de tela, ~350 px de figura) no tamanho de cada texto
CABE = {"titulo": 38, "subtitulo": 52, "fonte": 62}


def _fig(titulo: str, subtitulo: str, fonte: str, altura: int = 360) -> go.Figure:
    """Figura com título (a conclusão), subtítulo (o que está plotado e a unidade) e a linha de fonte embaixo. Os três
    textos já vêm quebrados para caber no celular; a altura cresce com as linhas a mais."""
    t, s, f = (_linhas(titulo, CABE["titulo"]), _linhas(subtitulo, CABE["subtitulo"]), _linhas(fonte, CABE["fonte"]))
    topo = BORDA + 23 * len(t) + 18 * len(s) + 16
    # template e fundo explícitos: o Streamlit troca o template padrão do Plotly ao ser importado
    fig = go.Figure(layout=dict(template="radar", paper_bgcolor=COR["superficie"], plot_bgcolor=COR["superficie"]))
    # o subtítulo vai no campo próprio: o Plotly não aceita trocar a fonte (serifa → sem serifa) dentro do título
    fig.update_layout(height=altura + (topo - TOPO) + 15 * (len(f) - 1), margin=dict(t=topo), title=dict(
        text="<br>".join(t),   # peso 600 no template (h2 do Raio-X); <b> daria 700 sintético na Newsreader
        subtitle=dict(text="<br>".join(s), font=dict(family=FONTE, size=12.5, color=COR["mudo"]))))
    fig.add_annotation(text="<br>".join(f), name="rodape", xref="paper", yref="paper", x=0, y=0, xanchor="left",
                       yanchor="top", showarrow=False, align="left", font=dict(size=11, color=COR["mudo"]))
    fig.update_layout(meta={"linhas_fonte": len(f)})
    return fig


def finalizar(fig: go.Figure) -> go.Figure:
    """Põe a linha de fonte no pé da figura, alinhada à esquerda com o título (pelas margens finais do gráfico); a
    margem de baixo cresce com as linhas da fonte."""
    extra = 15 * ((fig.layout.meta or {}).get("linhas_fonte", 1) - 1)
    b = (fig.layout.margin.b if fig.layout.margin.b is not None else 56) + extra
    l_ = fig.layout.margin.l if fig.layout.margin.l is not None else BORDA
    fig.update_layout(margin=dict(b=b))
    fig.update_annotations(selector=dict(name="rodape"), yshift=-(b - 24 - extra), xshift=-(l_ - BORDA))
    from src.painel.ui import tema
    return _escurecer(fig) if tema() == "escuro" else fig


def _margem(rotulos: list[str], px: float = 7.0) -> int:
    """Margem esquerda que cabe o rótulo mais longo de um eixo de categorias (sem as tags HTML)."""
    return int(max(len(re.sub(r"<[^>]+>", "", str(r))) for r in rotulos) * px) + BORDA + 8


def _passo(amplitude: float, n: int = 5) -> float:
    """Passo "redondo" (1, 2, 2,5 ou 5 × 10^k) para cerca de n marcas no eixo."""
    bruto = amplitude / n
    ordem = 10 ** math.floor(math.log10(bruto))
    return next(m * ordem for m in (1, 2, 2.5, 5, 10) if m * ordem >= bruto)


def _ticks(lo: float, hi: float, n: int = 5) -> list[float]:
    p = _passo(hi - lo, n)
    return [i * p for i in range(math.ceil(lo / p), math.floor(hi / p) + 1)]


# ------------------------------------------------------------------ A resposta
DEGRAUS = [  # (chave de numeros_oficiais, grupo, rótulo do degrau, explicação ao passar o mouse)
    ("serventias", "cartorios", "Cartórios ativos", "serventias extrajudiciais ativas em MG no cadastro do CNJ"),
    ("obrigadas", "cartorios", "Obrigados (Prov. 227)", "fora a Classe 1 (receita de até R$ 300 mil por semestre) "
     "e os cartórios sem titular; valor esperado"),
    ("com_deficit", "cartorios", "Sem bens suficientes", "obrigados cujo titular não consegue cobrir a dívida "
     "trabalhista com bens ou renda; valor esperado (suposição)"),
    ("deficit", "reais", "Déficit de cobertura", "a parte da dívida trabalhista que os bens do titular não cobrem: "
     "precisa de garantia (suposição)"),
    ("importancia_segurada", "reais", "Vira seguro", "importância segurada: a parte do déficit coberta por "
     "seguro-garantia; o resto vai para fiança bancária ou bens (suposição)"),
    ("premio", "reais", "Prêmio anual", "o que as seguradoras recebem por ano: importância segurada × taxa do seguro "
     "(suposição)"),
]


def funil(oficiais: dict, fonte: str) -> go.Figure:
    """O funil da escada: cartórios (3 degraus, em serventias) e dinheiro (3 degraus, em R$). Cada grupo tem a sua
    escala (barras proporcionais dentro do grupo), sem eixo de números: o rótulo de cada barra diz o valor. Os degraus
    vão na série s1 do Raio-X; o último, o prêmio, em s2, e remete ao número grande do topo (não repete o valor)."""
    n = {x["chave"]: x for x in oficiais["numeros"]}
    ref = {"cartorios": n["serventias"]["base_cru"], "reais": n["deficit"]["base_cru"]}
    fig = _fig("Poucos cartórios precisam de garantia, e o prêmio é uma fração pequena do que falta cobrir",
               "Do total de cartórios ao prêmio anual · acima da linha, cartórios; abaixo, reais (cada grupo na sua "
               "escala)",
               fonte, 420)
    rot, larg, textos, cores, dicas = [], [], [], [], []
    for chave, grupo, rotulo, dica in DEGRAUS:
        v = n[chave]
        rot.append(rotulo)
        larg.append(v["base_cru"] / ref[grupo])
        ultimo = chave == "premio"
        textos.append("<b>é o número acima</b>" if ultimo else f"<b>{v['valor']}</b>")
        cores.append(COR["comparacao"] if ultimo else COR["neutro"])
        dicas.append([v["valor"], dica])
    fig.add_trace(go.Bar(y=rot, x=larg, orientation="h", marker=dict(color=cores, **BARRA), width=0.62,
                         text=textos, textposition="outside", cliponaxis=False,
                         textfont=dict(color=COR["texto"], size=13), customdata=dicas,
                         hovertemplate="<b>%{y}</b>: %{customdata[0]}<br>%{customdata[1]}<extra></extra>"))
    fig.add_hline(y=2.5, line=dict(color=COR["eixo"], width=1, dash="dot"))   # cartórios em cima, reais embaixo
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="", tickfont=dict(color=COR["texto"], size=13))
    fig.update_xaxes(range=[0, 1.6], showticklabels=False, showline=False, showgrid=False)   # folga: celular
    fig.update_layout(margin=dict(l=_margem(rot), r=BORDA, b=56), bargap=0.3)
    return fig


# ------------------------------------------------------------------ Quão certo é
def faixa_premio(r: dict, fonte: str) -> go.Figure:
    """A faixa provável do prêmio numa linha: extremos teóricos discretos (cinza, nas pontas) > faixa P5–P95 (banda)
    > valor base (ponto). Os valores da faixa e da base já estão no topo do Início; aqui o gráfico mostra a posição,
    e os extremos (que não aparecem em outro lugar) levam o valor."""
    v = r["valores"]
    fig = _fig("Em 9 de cada 10 simulações, o prêmio fica na faixa azul",
               "Prêmio anual do mercado, em R$ · faixa provável (P5–P95) entre os extremos teóricos", fonte, 260)
    y = [0, 0]
    fig.add_trace(go.Scatter(x=[v["extremo_min"], v["extremo_max"]], y=y, mode="lines+markers",
                             line=dict(color=COR["extremo"], width=1.5, dash="dot"),
                             marker=dict(symbol="line-ns-open", size=14, color=COR["extremo"], line=dict(width=1.5)),
                             hovertemplate=f"Extremos teóricos: {r['extremos']}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[v["p05"], v["p95"]], y=y, mode="lines", line=dict(color=FAIXA, width=28),
                             hovertemplate=f"Faixa provável (P5–P95): {r['faixa_provavel']}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[v["base"]], y=[0], mode="markers",
                             marker=dict(size=14, color=COR["destaque"], line=dict(width=2, color="#ffffff")),
                             hovertemplate=f"Valor base: {r['valor_base']}<extra></extra>"))
    rot = dict(showarrow=False, yref="y", y=0, font=dict(size=12, color=COR["texto_2"]))
    fig.add_annotation(x=v["base"], text="<b>valor base</b>", yshift=26, xanchor="center",
                       **rot | dict(font=dict(size=12, color=COR["destaque"])))
    fig.add_annotation(x=v["extremo_min"], text=f"extremo<br>{brl(v['extremo_min'])}", yshift=-30, xanchor="left",
                       xshift=-4, align="left", **rot | dict(font=dict(size=11, color=COR["mudo"])))
    fig.add_annotation(x=v["extremo_max"], text=f"extremo<br>{brl(v['extremo_max'])}", yshift=-30, xanchor="right",
                       xshift=4, align="right", **rot | dict(font=dict(size=11, color=COR["mudo"])))
    tv = _ticks(0, v["extremo_max"])
    fig.update_xaxes(tickvals=tv, ticktext=[brl(t) for t in tv], showgrid=True, gridcolor=COR["grade"],
                     range=[0, v["extremo_max"] * 1.04], showline=False)
    fig.update_yaxes(showticklabels=False, showgrid=False, range=[-1, 1])
    fig.update_layout(margin=dict(l=BORDA, r=BORDA + 8, b=64))
    return fig


CURTOS = {"Parte do déficit que escolhe seguro": "Adesão ao seguro",
          "Chance de déficit, Classe 3": "Chance de déficit (Classe 3)",
          "Parte descoberta, Classe 3": "Parte descoberta (Classe 3)",
          "Chance de déficit, Classe 2": "Chance de déficit (Classe 2)",
          "Parte descoberta, Classe 2": "Parte descoberta (Classe 2)"}


def tornado(r: dict, fonte: str, n: int = 5) -> go.Figure:
    """As `n` suposições que mais mexem no prêmio, uma por vez do mínimo ao máximo (as outras no valor base), com o
    prêmio na ponta de cada barra. Abaixo da base na cor de destaque; acima, na de comparação."""
    t = r["tabela"][:n]
    base = t[0]["premio_base"]
    fig = _fig("A taxa do seguro e a adesão pesam mais que todo o resto",
               "Prêmio anual com cada suposição no mínimo e no máximo, as outras no valor base, em R$", fonte,
               96 + 72 * n + 64)
    rot = [CURTOS.get(x["rotulo"], x["rotulo"]) for x in t]
    lo = [min(x["premio_no_min"], x["premio_no_max"]) for x in t]
    hi = [max(x["premio_no_min"], x["premio_no_max"]) for x in t]
    for cor, xs in ((COR["destaque"], lo), (COR["comparacao"], hi)):
        fig.add_trace(go.Bar(y=rot, x=[x - base for x in xs], base=base, orientation="h", width=0.4,
                             marker=dict(color=cor, **BARRA),
                             text=[brl(x) if abs(x - base) / base > 0.004 else "" for x in xs],
                             textposition="outside", cliponaxis=False, textfont=dict(size=11, color=COR["texto"]),
                             customdata=[[brl(a), brl(b)] for a, b in zip(lo, hi)],
                             hovertemplate="<b>%{y}</b><br>prêmio de %{customdata[0]} a %{customdata[1]}"
                                           "<extra></extra>"))
    fig.add_vline(x=base, line=dict(color=COR["texto"], width=1))
    fig.add_annotation(x=base, y=1, yref="paper", text="valor base", showarrow=False, xanchor="center",
                       yanchor="bottom", font=dict(size=11, color=COR["texto_2"]))
    x0, x1 = min(lo), max(hi)
    folga = (x1 - x0) * 0.5   # cabe o rótulo da ponta também no celular (390 px)
    fig.update_xaxes(range=[x0 - folga, x1 + folga], showticklabels=False, showline=False)
    # o nome de cada suposição fica acima da barra, alinhado à esquerda: a barra usa a largura toda (cabe no celular)
    for r_ in rot:
        fig.add_annotation(x=0, xref="paper", y=r_, yref="y", text=r_, showarrow=False, xanchor="left",
                           yanchor="bottom", yshift=14, font=dict(size=13, color=COR["texto"]))
    fig.update_yaxes(categoryorder="array", categoryarray=rot[::-1], showgrid=False, ticks="", showticklabels=False)
    fig.update_layout(barmode="overlay", bargap=0.55, margin=dict(l=BORDA, r=BORDA, b=56))
    return fig


# ------------------------------------------------------------------ Para onde vai
def projecao_premio(por_ano: dict[int, dict], fonte: str) -> go.Figure:
    """Prêmio anual de hoje (valor base, ponto cheio) e projetado para 2026 e 2027 (linha tracejada com a faixa
    P10–P90), com a dívida trabalhista de cada cartório fixa na de 2025. `por_ano`: {ano: previsao_mercado(ano)}."""
    anos = sorted(por_ano)
    ult = por_ano[anos[-1]]
    base = ult["valores"]["base_2025"]["premio"]
    p = [por_ano[a]["valores"]["principal"]["mercado_premio_emitido"] for a in anos]
    x = [anos[0] - 1] + anos   # eixo numérico (o Plotly lê "2026" em texto como número e embaralha as categorias)
    fig = _fig("PROJEÇÃO · Com a dívida trabalhista de hoje, o prêmio quase não muda até 2027",
               "Prêmio anual do mercado, em R$ mil · projeção central e faixa P10–P90",
               fonte + " · projeção, não número oficial", 360)
    fig.add_trace(go.Scatter(x=x + x[::-1], y=[base / 1e3] + [v["p90"] / 1e3 for v in p] +
                             [v["p10"] / 1e3 for v in p][::-1] + [base / 1e3], mode="lines", fill="toself",
                             fillcolor=FAIXA, line=dict(width=0), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x, y=[base / 1e3] + [v["central"] / 1e3 for v in p], mode="lines+markers",
                             line=dict(color=COR["destaque"], width=2, dash="dash"),
                             marker=dict(size=9, color=COR["destaque"], line=dict(width=2, color="#ffffff")),
                             customdata=[["valor base de hoje", ""]] +
                                        [[f"projeção: {brl(v['central'])}", f"P10–P90 {brl(v['p10'])} a {brl(v['p90'])}"]
                                         for v in p],
                             hovertemplate="<b>%{x}</b><br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>"))
    fig.add_annotation(x=x[0], y=base / 1e3, text="valor base", showarrow=False, yshift=18,
                       font=dict(size=12, color=COR["texto_2"]))
    for a, v in zip(anos, p):
        fig.add_annotation(x=a, y=v["p90"] / 1e3, text=f"<b>{brl(v['central'])}</b>", showarrow=False,
                           yshift=14, font=dict(size=12, color=COR["destaque"]))
    topo = max(v["p90"] for v in p) / 1e3
    fig.update_yaxes(range=[0, topo * 1.25], tickformat=",.0f", ticksuffix=" mil")
    fig.update_xaxes(tickvals=x, ticktext=[f"hoje ({x[0]})"] + [str(a) for a in anos], range=[x[0] - 0.3, x[-1] + 0.3])
    fig.update_layout(margin=dict(l=BORDA + 48, r=BORDA, b=56))
    return fig
