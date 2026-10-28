"""Gráficos do painel (Plotly): um template único e uma função por gráfico, que recebe o resultado de
src/painel/analises.py (nunca consulta o banco). Padrão em docs/painel/padrao_visual.md (segunda rodada).

Regras do template: fonte Inter; título à esquerda, na borda do cartão, dizendo a conclusão; subtítulo com o que está
plotado e a unidade; rótulos diretos no fim das linhas e na ponta das barras (legenda só quando não há como rotular, e
então colada ao subtítulo); duas séries se diferenciam por cor, traço e marcador; anotação encostada no que anota;
grade leve; rodapé com fonte e data; números no formato brasileiro; sem eixo duplo, sem 3D e sem pizza; escala log só
quando indispensável, e então dita no subtítulo.
"""
import math
import re

import plotly.graph_objects as go
import plotly.io as pio

from src.agent.ferramentas import _br, aprox, brl, pct

# cores com significado fixo. Pares que aparecem juntos testados em escala de cinza, deuteranopia e protanopia
# (tests/test_cores.py; tabela em docs/painel/padrao_visual.md)
COR = {
    "marca": "#13294b", "marca_2": "#1f4e86",
    "observado": "#1f5bb8",     # dado observado e valor base
    "projecao": "#f07f26",      # projeção (sempre tracejada ou com faixa)
    "suposicao": "#17a398",     # resultado que depende de suposição
    "comparacao": "#cdcbc4",    # leitura de comparação e extremos (traço tracejado ou marcador vazado)
    "ganho": "#0b6e4f", "perda": "#f0826e",      # lucro × prejuízo
    "reduz": "#0b5563", "aumenta": "#f2a541",    # abaixo × acima da base (tornado e sensibilidades)
    "alerta": "#c0392b",
    "texto": "#16202e", "texto_2": "#4a5363", "mudo": "#6b7280",
    "grade": "#e8ecf2", "eixo": "#c5ccd6", "superficie": "#ffffff",
}
FAIXA_OBS = "rgba(31,91,184,0.18)"       # banda de incerteza do valor base (P5–P95)
FAIXA_OBS_FORTE = "rgba(31,91,184,0.40)"  # metade central (P25–P75)
FAIXA_PROJ = "rgba(240,127,38,0.20)"     # banda de incerteza da projeção (P10–P90)
FONTE = "Inter, system-ui, -apple-system, 'Segoe UI', sans-serif"
BORDA = 18      # px entre a borda do cartão e o título / rodapé
TOPO = 74       # px do título + subtítulo
TOPO_LEGENDA = 104

pio.templates["radar"] = go.layout.Template(layout=go.Layout(
    font=dict(family=FONTE, size=13, color=COR["texto"]),
    title=dict(font=dict(size=17, color=COR["texto"]), x=0, xanchor="left", xref="container", y=1, yref="container",
               yanchor="top", pad=dict(t=16, l=BORDA)),
    paper_bgcolor=COR["superficie"], plot_bgcolor=COR["superficie"], separators=",.",
    colorway=[COR["observado"], COR["projecao"], COR["suposicao"], COR["comparacao"]],
    xaxis=dict(automargin=True, showgrid=False, linecolor=COR["eixo"], ticks="outside", tickcolor=COR["eixo"],
               zeroline=False, title=dict(font=dict(size=12, color=COR["texto_2"])),
               tickfont=dict(color=COR["texto_2"])),
    yaxis=dict(automargin=True, showgrid=True, gridcolor=COR["grade"], gridwidth=1, zeroline=False,
               linecolor=COR["eixo"], title=dict(font=dict(size=12, color=COR["texto_2"])),
               tickfont=dict(color=COR["texto_2"])),
    legend=dict(orientation="h", font=dict(size=12, color=COR["texto_2"]), bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor="#ffffff", bordercolor=COR["eixo"], font=dict(family=FONTE, size=13, color=COR["texto"])),
    margin=dict(l=BORDA, r=BORDA, t=TOPO, b=64), bargap=0.4, showlegend=False,
))
pio.templates.default = "radar"


def _fig(titulo: str, subtitulo: str, rodape: str, altura: int = 360, legenda: bool = False) -> go.Figure:
    """Figura com título (a conclusão), subtítulo (o que está plotado e a unidade) e rodapé (fonte e data). Com
    `legenda`, a legenda fica logo abaixo do subtítulo, sem vão."""
    # template e fundo explícitos: o Streamlit troca o template padrão do Plotly ao ser importado
    fig = go.Figure(layout=dict(template="radar", paper_bgcolor=COR["superficie"], plot_bgcolor=COR["superficie"]))
    fig.update_layout(height=altura, showlegend=legenda, margin=dict(t=TOPO_LEGENDA if legenda else TOPO),
                      title=dict(text=f"<b>{titulo}</b><br><span style='font-size:12.5px;color:{COR['texto_2']}'>"
                                      f"{subtitulo}</span>"))
    if legenda:
        fig.update_layout(legend=dict(xref="container", x=0.012, xanchor="left", yref="container",
                                      y=1 - (TOPO - 6) / altura, yanchor="top"))
    fig.add_annotation(text=rodape, name="rodape", xref="paper", yref="paper", x=0, y=0, xanchor="left",
                       yanchor="bottom", showarrow=False, align="left", font=dict(size=11, color=COR["mudo"]))
    return fig


def finalizar(fig: go.Figure) -> go.Figure:
    """Põe o rodapé de fonte no pé da figura, alinhado à esquerda com o título (pelas margens finais do gráfico)."""
    b = fig.layout.margin.b if fig.layout.margin.b is not None else 64
    l_ = fig.layout.margin.l if fig.layout.margin.l is not None else BORDA
    fig.update_annotations(selector=dict(name="rodape"), yshift=-(b - 6), xshift=-(l_ - BORDA))
    return fig


def rodape(r: dict) -> str:
    """Rodapé curto de um resultado: fonte, carga e versão das premissas."""
    return f"Fonte: {r['fonte']} · carga {r['carga']} · premissas v{r['versao_premissas']}"


def _cor_txt(cor: str, texto: str) -> str:
    """Trecho de subtítulo na cor da série (marca ■ antes), para a legenda ficar dentro do subtítulo."""
    return f"<span style='color:{cor}'>■</span> {texto}"


def _margem(rotulos: list[str], px: float = 7.2) -> int:
    """Margem esquerda que cabe o rótulo mais longo de um eixo de categorias (sem as tags HTML)."""
    return int(max(len(re.sub(r"<[^>]+>", "", str(r))) for r in rotulos) * px) + BORDA + 10


def _passo(amplitude: float, n: int = 5) -> float:
    """Passo "redondo" (1, 2, 2,5 ou 5 × 10^k) para cerca de n marcas no eixo."""
    bruto = amplitude / n
    ordem = 10 ** math.floor(math.log10(bruto))
    return next(m * ordem for m in (1, 2, 2.5, 5, 10) if m * ordem >= bruto)


def _ticks(lo: float, hi: float, n: int = 5) -> list[float]:
    p = _passo(hi - lo, n)
    return [i * p for i in range(math.ceil(lo / p), math.floor(hi / p) + 1)]


# ------------------------------------------------------------------ Início
def escada(r: dict) -> go.Figure:
    t = r["tabela"]
    vezes = _br(t[0]["valor"] / t[-1]["valor"], 0)
    fig = _fig(f"O prêmio é {r['premio_sobre_teto']} do teto: o seguro cobre uma fatia pequena da dívida",
               f"Do passivo trabalhista ao prêmio anual, nível base, em R$ · {_cor_txt(COR['observado'], 'dado público')}"
               f" · {_cor_txt(COR['suposicao'], 'depende de suposições')} · escala log: o passivo é {vezes} vezes o "
               "prêmio", rodape(r), 320)
    cores = [COR["observado"] if x["natureza"] == "dado" else COR["suposicao"] for x in t]
    rot = [x["degrau"] for x in t]
    fig.add_trace(go.Bar(y=rot, x=[x["valor"] for x in t], orientation="h", marker_color=cores,
                         text=[f"<b>{x['valor_txt']}</b> · {x['pct_txt']}" for x in t], textposition="outside",
                         cliponaxis=False, width=0.62, textfont=dict(color=COR["texto"]),
                         customdata=[[x["valor_txt"], x["pct_txt"], x["natureza"]] for x in t],
                         hovertemplate="<b>%{y}</b><br>%{customdata[0]}<br>%{customdata[1]} do passivo das obrigadas"
                                       "<br>%{customdata[2]}<extra></extra>"))
    lo, hi = min(x["valor"] for x in t), max(x["valor"] for x in t)
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="")
    fig.update_xaxes(type="log", showticklabels=False, showline=False, ticks="",
                     range=[math.log10(lo) - 0.6, math.log10(hi) + 0.55])
    fig.update_layout(margin=dict(l=_margem(rot), r=BORDA, b=44))
    return fig


FAIXA_TXT = "faixa provável (P5–P95, faixa dentro das suposições)"


def faixa_d042(r: dict) -> go.Figure:
    """Uma linha, rotulada no próprio gráfico: extremos (cinza, nas pontas) > P5–P95 (banda) > P25–P75 > valor base
    (ponto azul) e mediana dos sorteios (anel)."""
    v = r["valores"]
    fig = _fig(f"{r['medida']}: provavelmente entre {r['faixa_provavel']}",
               f"Valor base, {FAIXA_TXT} e extremos teóricos, em R$", rodape(r), 250)
    y = [0, 0]
    fig.add_trace(go.Scatter(x=[v["extremo_min"], v["extremo_max"]], y=y, mode="lines+markers",
                             line=dict(color=COR["comparacao"], width=2, dash="dot"),
                             marker=dict(symbol="line-ns-open", size=16, color=COR["texto_2"], line=dict(width=2)),
                             hovertemplate=f"Extremos teóricos: {r['extremos']}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[v["p05"], v["p95"]], y=y, mode="lines", line=dict(color=FAIXA_OBS, width=30),
                             hovertemplate=f"Faixa provável (P5–P95): {r['faixa_provavel_exata']}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[v["p25"], v["p75"]], y=y, mode="lines", line=dict(color=FAIXA_OBS_FORTE, width=30),
                             hovertemplate=f"P25–P75: {brl(v['p25'])} a {brl(v['p75'])}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[v["p50"]], y=[0], mode="markers",
                             marker=dict(symbol="circle-open", size=13, color=COR["texto"], line=dict(width=2.5)),
                             hovertemplate=f"Mediana dos sorteios: {r['mediana_sorteios']}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[v["base"]], y=[0], mode="markers",
                             marker=dict(size=15, color=COR["observado"], line=dict(width=2, color="#ffffff")),
                             hovertemplate=f"Valor base: {r['valor_base']}<extra></extra>"))
    rot = dict(showarrow=False, yref="y", y=0, font=dict(size=12, color=COR["texto_2"]))
    fig.add_annotation(x=v["base"], text=f"<b>valor base {r['valor_base']}</b>", yshift=30, xanchor="center",
                       **rot | dict(font=dict(size=12.5, color=COR["observado"])))
    fig.add_annotation(x=v["p95"], text="faixa provável (P5–P95)", yshift=30, xanchor="left", xshift=6, **rot)
    fig.add_annotation(x=v["p50"], text=f"mediana {r['mediana_sorteios']}", yshift=-30, xanchor="left", xshift=-6,
                       **rot)
    fig.add_annotation(x=v["extremo_min"], text="extremo mín.", yshift=-30, xanchor="left", xshift=-4, **rot)
    fig.add_annotation(x=v["extremo_max"], text="extremo máx.", yshift=-30, xanchor="right", xshift=4, **rot)
    tv = _ticks(0, v["extremo_max"])
    fig.update_xaxes(tickvals=tv, ticktext=[brl(t) for t in tv], showgrid=True, gridcolor=COR["grade"],
                     range=[0, v["extremo_max"] * 1.04], showline=False)
    fig.update_yaxes(showticklabels=False, showgrid=False, range=[-1, 1])
    fig.update_layout(margin=dict(l=BORDA, r=BORDA + 8, b=58))
    return fig


# ------------------------------------------------------------------ Análises
def tornado(r: dict) -> go.Figure:
    t = r["tabela"]
    base = t[0]["premio_base"]
    fig = _fig("Taxa e adesão ao seguro decidem o tamanho do mercado",
               f"Prêmio anual com cada suposição no mínimo e no máximo, as outras no valor base ({r['premio_base']}) · "
               f"{_cor_txt(COR['reduz'], 'reduz o prêmio')} · {_cor_txt(COR['aumenta'], 'aumenta o prêmio')} · "
               "barras claras: premissas do passivo e do universo", rodape(r), 470)
    rot = [x["rotulo"] for x in t]
    lo = [min(x["premio_no_min"], x["premio_no_max"]) for x in t]
    hi = [max(x["premio_no_min"], x["premio_no_max"]) for x in t]
    opac = [1 if x["grupo"].startswith("suposição") else 0.5 for x in t]
    for lado, cor, xs in (("reduz", COR["reduz"], lo), ("aumenta", COR["aumenta"], hi)):
        fig.add_trace(go.Bar(y=rot, x=[x - base for x in xs], base=base, orientation="h", width=0.62,
                             marker=dict(color=cor, opacity=opac),
                             text=[brl(x) if abs(x - base) / base > 0.004 else "" for x in xs],
                             textposition="outside", cliponaxis=False, textfont=dict(size=11.5, color=COR["texto"]),
                             customdata=[[brl(a), brl(b)] for a, b in zip(lo, hi)],
                             hovertemplate="<b>%{y}</b><br>prêmio de %{customdata[0]} a %{customdata[1]}"
                                           "<extra></extra>"))
    fig.add_vline(x=base, line=dict(color=COR["texto"], width=1.5))
    fig.add_annotation(x=base, y=1, yref="paper", text=f"base {brl(base)}", showarrow=False, xanchor="left",
                       yanchor="bottom", xshift=4, font=dict(size=11.5, color=COR["texto"]))
    x0, x1 = min(lo), max(hi)
    folga = (x1 - x0) * 0.16
    tv = _ticks(x0 - folga, x1 + folga)
    fig.update_xaxes(tickvals=tv, ticktext=[brl(x) for x in tv], showgrid=True, gridcolor=COR["grade"],
                     range=[x0 - folga, x1 + folga], title="prêmio anual (R$)")
    fig.update_yaxes(categoryorder="array", categoryarray=rot[::-1], showgrid=False, ticks="")
    fig.update_layout(barmode="overlay", margin=dict(l=_margem(rot), r=BORDA, b=84))
    return fig


def previsao_arrecadacao(r: dict) -> go.Figure:
    t = [x for x in r["tabela"] if "principal" in x["variante"]]
    per = [x["periodo"] for x in t]
    fig = _fig("PROJEÇÃO · A arrecadação de MG segue crescendo, mas o 2026-1 já passou da faixa",
               "Arrecadação semestral de MG, em R$ bilhões: projeção central e faixa P10–P90 (tendência do teste T2)",
               rodape(r) + " · projeção, não número oficial", 380)
    fig.add_trace(go.Scatter(x=per + per[::-1], y=[x["p90"] / 1e9 for x in t] + [x["p10"] / 1e9 for x in t][::-1],
                             mode="lines", fill="toself", fillcolor=FAIXA_PROJ, line=dict(width=0), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=per, y=[x["central"] / 1e9 for x in t], mode="lines+markers",
                             line=dict(color=COR["projecao"], width=2.5, dash="dash"),
                             marker=dict(size=9, symbol="diamond", color=COR["projecao"]),
                             customdata=[[brl(x["central"]), brl(x["p10"]), brl(x["p90"])] for x in t],
                             hovertemplate="<b>%{x}</b> (projeção)<br>central %{customdata[0]}<br>P10–P90 "
                                           "%{customdata[1]} a %{customdata[2]}<extra></extra>"))
    real = [x for x in t if x["realizado"] is not None]
    fig.add_trace(go.Scatter(x=[x["periodo"] for x in real], y=[x["realizado"] / 1e9 for x in real], mode="markers",
                             marker=dict(size=13, color=COR["observado"], line=dict(width=2, color="#ffffff")),
                             text=[brl(x["realizado"]) for x in real],
                             hovertemplate="<b>%{x}</b> realizado (observado, parcial)<br>%{text}<extra></extra>"))
    ult = t[-1]
    fig.add_annotation(x=per[-1], y=ult["central"] / 1e9, text=f"<b>projeção central</b><br>{brl(ult['central'])}",
                       showarrow=False, xanchor="left", xshift=12, align="left",
                       font=dict(size=12, color=COR["projecao"]))
    fig.add_annotation(x=per[-1], y=ult["p10"] / 1e9, text="faixa P10–P90", showarrow=False, xanchor="left",
                       xshift=12, yanchor="top", font=dict(size=11.5, color=COR["texto_2"]))
    for x in real:
        fig.add_annotation(x=x["periodo"], y=x["realizado"] / 1e9, text=f"<b>realizado</b> {brl(x['realizado'])}<br>"
                           "(observado, parcial)", showarrow=False, xanchor="left", xshift=12, yanchor="bottom",
                           yshift=4, align="left", font=dict(size=12, color=COR["observado"]))
    fig.update_yaxes(title="R$ bilhões por semestre", tickformat=",.1f", rangemode="tozero")
    fig.update_xaxes(title="semestre", type="category")
    fig.update_layout(margin=dict(l=72, r=150, b=92))
    return fig


def universo_projetado(r: dict, outra: dict | None = None) -> go.Figure:
    """Obrigadas em 2025 (base, observado) e projetadas em 2026–27: leitura principal do limite (laranja, linha cheia,
    com P10–P90) e a outra leitura (cinza tracejado com marcador vazado, comparação)."""
    tab = r["tabela"]
    princ, comp = r["leitura_do_limite"], r["comparacao"]
    base = r["valores"]["base_2025"]["n_universo"]
    fig = _fig("PROJEÇÃO · O universo de obrigadas cresce até 2027",
               f"Serventias obrigadas (universo), base 2025 e projeção 2026–27 com faixa P10–P90 · leitura em uso: "
               f"{princ}", rodape(r) + " · projeção, não número oficial", 380)
    finais = []
    for leitura, cor, traco, simb, nome in (
            (princ, COR["projecao"], "solid", "circle", f"{princ} (em uso)"),
            (comp, COR["texto_2"], "dash", "square-open", f"{comp} (comparação)")):
        d = sorted([x for x in tab if x["cenario_limite"] == leitura and x["medida"] == "n_universo"],
                   key=lambda x: x["periodo"])
        xs = ["2025"] + [x["periodo"] for x in d]
        ys = [base] + [x["central"] for x in d]
        cor_linha = cor if leitura == princ else COR["comparacao"]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines+markers", line=dict(color=cor_linha, width=2.5, dash=traco),
            marker=dict(size=10, symbol=simb, color=cor, line=dict(width=2, color=cor if "open" in simb else "#ffffff")),
            error_y=dict(type="data", symmetric=False, array=[0] + [x["p90"] - x["central"] for x in d],
                         arrayminus=[0] + [x["central"] - x["p10"] for x in d], color=cor_linha, thickness=1.5,
                         width=6) if leitura == princ else None,
            customdata=[[aprox(base), "base 2025 (número oficial)"]] +
                       [[aprox(x["central"]), f"P10–P90 {aprox(x['p10'])} a {aprox(x['p90'])}"] for x in d],
            hovertemplate=f"<b>%{{x}}</b> · {leitura}<br>%{{customdata[0]}} obrigadas<br>%{{customdata[1]}}<extra></extra>"))
        finais.append((xs[-1], ys[-1], f"<b>{aprox(ys[-1])}</b> {nome}", cor))
    (xa, ya, ta, ca), (xb, yb, tb, cb) = finais
    em_cima = ya >= yb
    for x, y_, txt, cor, sobe in ((xa, ya, ta, ca, em_cima), (xb, yb, tb, cb, not em_cima)):
        fig.add_annotation(x=x, y=y_, text=txt, showarrow=False, xanchor="left", xshift=14,
                           yshift=10 if sobe else -10, font=dict(size=12, color=cor))
    fig.add_trace(go.Scatter(x=["2025"], y=[base], mode="markers",
                             marker=dict(size=14, color=COR["observado"], line=dict(width=2, color="#ffffff")),
                             hovertemplate=f"<b>2025</b> base (número oficial): {aprox(base)}<extra></extra>"))
    fig.add_annotation(x="2025", y=base, text=f"<b>{aprox(base)}</b> em 2025<br>(observado)", showarrow=False,
                       xanchor="left", xshift=12, yshift=-18, align="left", font=dict(size=12, color=COR["observado"]))
    fig.update_yaxes(title="serventias obrigadas", tickformat=",.0f")
    fig.update_xaxes(type="category", title="ano da receita (a classe vale para o ano seguinte)")
    fig.update_layout(margin=dict(l=72, r=230, b=92))
    return fig


def subidas(r: dict) -> go.Figure:
    """Subidas da Classe 1 para a 2 em 2026: 07 (principal, com P10–P90), 07 na outra leitura e a faixa do 05b."""
    v = r["valores"]
    l7 = list(v["07"])
    pr, co = l7[0], l7[1]
    lo, hi = v["05b_faixa"]
    fig = _fig(f"PROJEÇÃO · Quantas sobem da Classe 1 para a 2 em {r['ano']}: os métodos divergem",
               "Subidas esperadas (serventias) · principal: notebook 07 · comparação: 07 na outra leitura do limite e "
               "05b", rodape(r), 290)
    rot = [f"07 · {pr} (principal)", f"07 · {co} (comparação)", "05b · sem e com recalibração (comparação)"]
    c7 = v["07"][pr]
    fig.add_trace(go.Scatter(x=[c7["central"]], y=[rot[0]], mode="markers+text", marker=dict(size=13, color=COR["projecao"]),
                             text=[f"<b>{aprox(c7['central'])}</b>"], textposition="top center",
                             textfont=dict(color=COR["projecao"]),
                             error_x=dict(type="data", symmetric=False, array=[c7["p90"] - c7["central"]],
                                          arrayminus=[c7["central"] - c7["p10"]], color=COR["projecao"], thickness=2.5,
                                          width=8),
                             hovertemplate=f"07 ({pr}): {aprox(c7['central'])}; P10–P90 "
                                           f"{aprox(c7['p10'])} a {aprox(c7['p90'])}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[v["07"][co]["central"]], y=[rot[1]], mode="markers+text",
                             marker=dict(size=11, symbol="square-open", color=COR["texto_2"], line=dict(width=2)),
                             text=[aprox(v["07"][co]["central"])], textposition="middle right",
                             textfont=dict(color=COR["texto_2"]),
                             hovertemplate=f"07 ({co}): {aprox(v['07'][co]['central'])}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[lo, hi], y=[rot[2]] * 2, mode="lines+markers+text",
                             line=dict(color=COR["comparacao"], width=7),
                             marker=dict(size=11, symbol="square-open", color=COR["texto_2"], line=dict(width=2)),
                             text=[_br(lo, 0), _br(hi, 0)], textposition=["middle left", "middle right"],
                             textfont=dict(color=COR["texto_2"]),
                             hovertemplate=f"05b: {_br(lo, 0)} a {_br(hi, 0)} subidas<extra></extra>"))
    fig.update_yaxes(categoryorder="array", categoryarray=rot[::-1], showgrid=False, ticks="")
    fig.update_xaxes(title="subidas em " + str(r["ano"]), range=[0, max(hi, c7["p90"]) * 1.12], showgrid=True,
                     gridcolor=COR["grade"])
    fig.update_layout(margin=dict(l=_margem(rot), r=BORDA + 10, b=86))
    return fig


def lorenz(r: dict) -> go.Figure:
    v = r["valores"]
    fig = _fig(f"Os {r['topo']} maiores concentram {r['parte_dos_maiores_no_passivo']} do passivo das obrigadas",
               "Curva de concentração (Lorenz): parte acumulada do total × parte das serventias, da menor para a maior",
               rodape(r), 420)
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(color=COR["eixo"], width=1.2),
                             hoverinfo="skip"))
    fig.add_annotation(x=0.5, y=0.5, text="igualdade (todos iguais)", textangle=-27, showarrow=False, yshift=12,
                       font=dict(size=11.5, color=COR["mudo"]))
    series = {"passivo das obrigadas": (COR["observado"], "solid", f"passivo das obrigadas (dado) · Gini {r['gini_passivo']}", 18),
              "déficit esperado": (COR["suposicao"], "dash", f"déficit esperado (suposição) · Gini {r['gini_deficit']}", -18)}
    for medida, (cor, traco, nome, ys) in series.items():
        c = [x for x in r["curva"] if x["medida"] == medida]
        fig.add_trace(go.Scatter(x=[x["fracao_unidades"] for x in c], y=[x["fracao_valor"] for x in c], mode="lines",
                                 line=dict(color=cor, width=2.8, dash=traco),
                                 hovertemplate="%{x:.0%} das serventias somam %{y:.1%} do total<extra></extra>"))
        p = min(c, key=lambda x: abs(x["fracao_unidades"] - 0.55))
        fig.add_annotation(x=p["fracao_unidades"], y=p["fracao_valor"], text=f"<b>{nome}</b>", showarrow=False,
                           xanchor="right" if ys > 0 else "left", xshift=-8 if ys > 0 else 10, yshift=ys,
                           font=dict(size=12, color=cor))
    x90 = 1 - v["topo"]
    fig.add_vline(x=x90, line=dict(color=COR["texto_2"], width=1, dash="dot"))
    fig.add_annotation(x=x90, y=0.97, yref="paper", text=f"os {r['topo']} maiores →", showarrow=False, xanchor="left",
                       xshift=6, font=dict(size=11.5, color=COR["texto_2"]))
    fig.update_xaxes(tickformat=".0%", title="parte das serventias obrigadas (da menor para a maior)", range=[0, 1])
    fig.update_yaxes(tickformat=".0%", title="parte acumulada do total", range=[0, 1.02])
    fig.update_layout(margin=dict(l=72, r=BORDA + 8, b=92))
    return fig


def pergunta_9(r: dict) -> go.Figure:
    t = r["tabela"]
    fig = _fig("Lucro ou prejuízo depende de quem paga quando a delegação termina",
               "Custo da seguradora para cada R$ 1 de prêmio (índice combinado: sinistros + comissão + despesas ÷ "
               "prêmio), pela chance de a delegação terminar no ano", rodape(r), 400)
    topo = max(x["indice_combinado"] for x in t) * 1.12
    fig.add_hrect(y0=1, y1=topo, fillcolor=COR["perda"], opacity=0.08, line_width=0)
    fig.add_hline(y=1, line=dict(color=COR["texto_2"], width=1.2, dash="dot"))
    fig.add_annotation(x=0, xref="paper", y=1, text="100% = empate", showarrow=False, xanchor="left", yanchor="bottom",
                       xshift=4, yshift=2, font=dict(size=11.5, color=COR["texto_2"]))
    fig.add_annotation(x=0, xref="paper", y=topo, text="acima: prejuízo", showarrow=False, xanchor="left",
                       yanchor="top", xshift=4, font=dict(size=11.5, color=COR["texto_2"]))
    fig.add_annotation(x=0, xref="paper", y=1, text="abaixo: lucro", showarrow=False, xanchor="left", yanchor="top",
                       xshift=4, yshift=-4, font=dict(size=11.5, color=COR["texto_2"]))
    for prefixo, cor, traco, simb, nome in (
            ("com", COR["ganho"], "solid", "circle", "com a M1:<br>o titular paga com a renda"),
            ("sem", COR["perda"], "dash", "diamond", "sem a M1:<br>o titular não paga nada")):
        d = sorted([x for x in t if x["leitura"].startswith(prefixo)], key=lambda x: x["p_fim"])
        fig.add_trace(go.Scatter(
            x=[x["p_fim"] for x in d], y=[x["indice_combinado"] for x in d], mode="lines+markers",
            line=dict(color=cor, width=2.8, dash=traco), marker=dict(size=11, symbol=simb, color=cor),
            customdata=[[pct(x["indice_combinado"]),
                         ("lucro de " if x["resultado_tecnico"] >= 0 else "prejuízo de ") + brl(abs(x["resultado_tecnico"]))]
                        for x in d],
            hovertemplate="P(fim) %{x:.1%}<br>índice combinado %{customdata[0]}<br>resultado técnico: "
                          "%{customdata[1]} por ano<extra></extra>"))
        u = d[-1]
        fig.add_annotation(x=u["p_fim"], y=u["indice_combinado"], text=f"<b>{pct(u['indice_combinado'])}</b> {nome}",
                           showarrow=False, xanchor="left", xshift=12, align="left", font=dict(size=12, color=cor))
    fig.update_xaxes(tickformat=".1%", title="chance de a delegação terminar no ano (notebook 05c)",
                     tickvals=sorted({x["p_fim"] for x in t}))
    fig.update_yaxes(tickformat=".0%", title="índice combinado", range=[0, topo])
    fig.update_layout(margin=dict(l=72, r=200, b=92))
    return fig


# ------------------------------------------------------------------ Mercado
def grupos(r: dict) -> go.Figure:
    t = r["tabela"]
    alvo = r["valores"]["alvo"]
    rot = [f"<b>{x['nome_grupo']}</b>" if x["grupo"] == alvo else x["nome_grupo"] for x in t]
    fig = _fig("As providas grandes são o cliente do seguro",
               "Parte de MG em cada tipo de cartório (k-means do notebook 04), em % · valores escritos no grupo-alvo",
               rodape(r), 450, legenda=True)
    series = [("pct_serventias", "das serventias", COR["comparacao"], ""),
              ("pct_passivo_obrigadas_mg", "do passivo das obrigadas (dado)", COR["observado"], ""),
              ("pct_deficit_mg", "do déficit (suposição)", COR["suposicao"], "/")]
    for col, nome, cor, padrao in series:
        fig.add_trace(go.Bar(y=rot, x=[x[col] for x in t], orientation="h", name=nome,
                             marker=dict(color=cor, pattern=dict(shape=padrao, fgcolor="#ffffff", size=6, solidity=0.25)),
                             text=[pct(x[col]) if x["grupo"] == alvo else "" for x in t], textposition="outside",
                             cliponaxis=False, textfont=dict(size=11.5, color=COR["texto"]),
                             customdata=[pct(x[col]) for x in t],
                             hovertemplate="%{y}<br>%{customdata} " + nome + "<extra></extra>"))
    topo = max(max(x[c] for x in t) for c, *_ in series)
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="")
    fig.update_xaxes(tickformat=".0%", range=[0, topo * 1.14], showgrid=True, gridcolor=COR["grade"])
    fig.update_layout(barmode="group", bargap=0.28, bargroupgap=0.06, margin=dict(l=_margem(rot), r=BORDA, b=64))
    return fig


def quem_e_obrigado(r: dict) -> go.Figure:
    t = r["tabela"]
    fig = _fig("Registro de Imóveis e 3 ou mais empregados: quase sempre obrigado",
               "Parte das serventias de classe conhecida que é obrigada, por atribuição e por porte", rodape(r), 420)
    rot = [f"{x['item']}" for x in t]
    fig.add_trace(go.Bar(y=rot, x=[x["pct"] for x in t], orientation="h", marker_color=COR["observado"], width=0.6,
                         text=[pct(x["pct"]) for x in t], textposition="outside", cliponaxis=False,
                         textfont=dict(color=COR["texto"]),
                         customdata=[[_br(x["serventias"], 0), _br(x["obrigadas"], 0), x["tipo"]] for x in t],
                         hovertemplate="<b>%{y}</b> (%{customdata[2]})<br>%{customdata[1]} obrigadas de "
                                       "%{customdata[0]}<extra></extra>"))
    media = r["valores"]["media"]
    fig.add_vline(x=media, line=dict(color=COR["texto_2"], width=1.2, dash="dot"))
    fig.add_annotation(x=media, y=1, yref="paper", text=f"média de MG {r['media_obrigadas']}", showarrow=False,
                       xanchor="left", yanchor="bottom", xshift=4, font=dict(size=11.5, color=COR["texto_2"]))
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="")
    fig.update_xaxes(tickformat=".0%", range=[0, 1.08], showgrid=True, gridcolor=COR["grade"])
    fig.update_layout(margin=dict(l=_margem(rot), r=BORDA, b=64))
    return fig


# ------------------------------------------------------------------ Qualidade dos dados
def _divergente(rot: list[str], valores: list[float], textos: list[str], custom: list, hover: str) -> go.Bar:
    """Barras de sensibilidade em torno de zero: abaixo da base na cor "reduz", acima na cor "aumenta"."""
    return go.Bar(y=rot, x=valores, orientation="h", width=0.55,
                  marker_color=[COR["reduz"] if v < 0 else COR["aumenta"] for v in valores], text=textos,
                  textposition="outside", cliponaxis=False, textfont=dict(color=COR["texto"]), customdata=custom,
                  hovertemplate=hover)


def escolhas_metodo(r: dict) -> go.Figure:
    t = sorted(r["tabela"], key=lambda x: x["efeito_passivo"])
    fig = _fig(f"{r['bloco']} · o passivo varia de {t[0]['efeito_txt']} a {t[-1]['efeito_txt']}",
               f"Efeito no passivo de todas as ativas, em % da base (sensibilidade) · "
               f"{_cor_txt(COR['reduz'], 'reduz')} · {_cor_txt(COR['aumenta'], 'aumenta')}", rodape(r), 290)
    curto = {"t5_salario_estimado": "T5: salário estimado para os vínculos sem dezembro",
             "t6_encolhimento": "T6: reserva por encolhimento (município pequeno)",
             "sem_regiao": "Reserva = MG inteiro (sem a região)"}
    rot = [curto.get(x["chave"], x["rotulo"]) for x in t]
    fig.add_trace(_divergente(rot, [x["efeito_passivo"] for x in t], [x["efeito_txt"] for x in t],
                              [[x["rotulo"], brl(x["passivo_todas"])] for x in t],
                              "%{customdata[0]}<br>passivo %{customdata[1]} (%{text})<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=COR["texto"], width=1))
    m = max(abs(x["efeito_passivo"]) for x in t) * 1.4
    fig.update_xaxes(tickformat="+.0%", range=[-m, m], showgrid=True, gridcolor=COR["grade"])
    fig.update_yaxes(showgrid=False, ticks="")
    fig.update_layout(margin=dict(l=_margem(rot), r=BORDA + 10, b=64))
    return fig


def leitura_literal(r: dict) -> go.Figure:
    t = r["tabela"]
    fig = _fig("Ao pé da letra, sai 1 em cada 5 obrigadas, mas o prêmio quase não muda",
               "Variação com a receita líquida do repasse (art. 2º, XXIV, do Prov. 213), em % da base (sensibilidade)",
               rodape(r), 290)
    rot = [x["medida"] for x in t]
    fig.add_trace(_divergente(rot, [x["variacao"] for x in t], [x["variacao_txt"] for x in t],
                              [[x["base_txt"], x["literal_txt"]] for x in t],
                              "<b>%{y}</b><br>base %{customdata[0]} → %{customdata[1]} (%{text})<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=COR["texto"], width=1))
    m = max(abs(x["variacao"]) for x in t) * 1.4
    fig.update_xaxes(tickformat="+.0%", range=[-m, m * 0.15], showgrid=True, gridcolor=COR["grade"])
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="")
    fig.update_layout(margin=dict(l=_margem(rot), r=BORDA + 10, b=64))
    return fig
