"""Gráficos do painel (Plotly): um template único e uma função por gráfico, que recebe o resultado de
src/painel/analises.py (nunca consulta o banco). Padrão em docs/painel/padrao_visual.md.

Regras do template: fonte Inter, grade horizontal fina, título que diz a conclusão, eixo com unidade, rodapé com fonte e
data, números no formato brasileiro (separadores ",." e textos de hover já formatados), faixa de incerteza como banda
sombreada, sem eixo duplo, sem 3D e sem pizza.
"""
import plotly.graph_objects as go
import plotly.io as pio

from src.agent.ferramentas import _br, aprox, brl, pct

# cores com significado fixo (validadas para daltonismo com o script da skill de visualização; padrao_visual.md)
COR = {
    "observado": "#2a78d6",     # dado observado e valor base
    "projecao": "#eb6834",      # projeção
    "suposicao": "#6250d6",     # resultado que depende de suposição; sensibilidade
    "comparacao": "#898781",    # leitura de comparação, extremos, referência
    "alerta": "#d03b3b",        # alerta (sempre com ícone e texto)
    "texto": "#1b1b19", "texto_2": "#52514e", "mudo": "#77756f",
    "grade": "#e7e6e1", "eixo": "#c3c2b7", "superficie": "#ffffff",
}
FAIXA_OBS = "rgba(42,120,214,0.16)"     # banda de incerteza do valor base (P5–P95)
FAIXA_PROJ = "rgba(235,104,52,0.16)"    # banda de incerteza da projeção (P10–P90)
FONTE = "Inter, system-ui, -apple-system, 'Segoe UI', sans-serif"

pio.templates["radar"] = go.layout.Template(layout=go.Layout(
    font=dict(family=FONTE, size=13, color=COR["texto"]),
    title=dict(font=dict(size=16, color=COR["texto"]), x=0, xanchor="left", xref="paper", y=1, yref="container",
               yanchor="top", pad=dict(t=12)),
    paper_bgcolor=COR["superficie"], plot_bgcolor=COR["superficie"], separators=",.",
    colorway=[COR["observado"], COR["projecao"], COR["suposicao"], COR["comparacao"]],
    xaxis=dict(automargin=True, showgrid=False, linecolor=COR["eixo"], ticks="outside", tickcolor=COR["eixo"], zeroline=False,
               title=dict(font=dict(size=12, color=COR["texto_2"])), tickfont=dict(color=COR["texto_2"])),
    yaxis=dict(automargin=True, showgrid=True, gridcolor=COR["grade"], gridwidth=1, zeroline=False, linecolor=COR["eixo"],
               title=dict(font=dict(size=12, color=COR["texto_2"])), tickfont=dict(color=COR["texto_2"])),
    legend=dict(orientation="h", x=0, xanchor="left", y=1.02, yanchor="bottom", font=dict(size=12, color=COR["texto_2"]),
                bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor="#ffffff", bordercolor=COR["eixo"], font=dict(family=FONTE, size=13, color=COR["texto"])),
    margin=dict(l=8, r=16, t=118, b=72), bargap=0.45,
))
pio.templates.default = "radar"


def _fig(titulo: str, subtitulo: str, rodape: str, altura: int = 360) -> go.Figure:
    """Figura com título (a conclusão), subtítulo (o que está plotado e a unidade) e rodapé (fonte e data)."""
    # template e fundo explícitos: o Streamlit troca o template padrão do Plotly ao ser importado
    fig = go.Figure(layout=dict(template="radar", paper_bgcolor=COR["superficie"], plot_bgcolor=COR["superficie"]))
    fig.update_layout(height=altura, title=dict(text=f"<b>{titulo}</b><br><span style='font-size:12px;color:"
                                                     f"{COR['texto_2']}'>{subtitulo}</span>"))
    fig.add_annotation(text=rodape, name="rodape", xref="paper", yref="paper", x=0, y=0, xanchor="left",
                       yanchor="bottom", showarrow=False, align="left", font=dict(size=11, color=COR["mudo"]))
    return fig


def finalizar(fig: go.Figure) -> go.Figure:
    """Põe o rodapé de fonte no pé da figura (4 px acima da borda), pela margem inferior final do gráfico."""
    b = fig.layout.margin.b if fig.layout.margin.b is not None else 72
    fig.update_annotations(selector=dict(name="rodape"), yshift=-(b - 4))
    return fig


def rodape(r: dict) -> str:
    """Rodapé curto de um resultado: fonte, carga e versão das premissas."""
    return f"Fonte: {r['fonte']} · carga {r['carga']} · premissas v{r['versao_premissas']}"


# ------------------------------------------------------------------ Início
def escada(r: dict) -> go.Figure:
    t = r["tabela"]
    fig = _fig(f"O prêmio é {r['premio_sobre_teto']} do teto: o seguro cobre uma fatia pequena da dívida",
               "Do passivo trabalhista ao prêmio anual, nível base, em R$ (escala log) · azul = dado público; "
               "violeta = depende de suposições", rodape(r), 340)
    cores = [COR["observado"] if x["natureza"] == "dado" else COR["suposicao"] for x in t]
    fig.add_trace(go.Bar(y=[x["degrau"] for x in t], x=[x["valor"] for x in t], orientation="h", marker_color=cores,
                         text=[f"{x['valor_txt']} · {x['pct_txt']}" for x in t], textposition="outside",
                         cliponaxis=False, width=0.5,
                         customdata=[[x["valor_txt"], x["pct_txt"], x["natureza"]] for x in t],
                         hovertemplate="<b>%{y}</b><br>%{customdata[0]}<br>%{customdata[1]} do passivo das obrigadas"
                                       "<br>%{customdata[2]}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(type="log", showticklabels=False, showline=False, ticks="", range=[4.6, 9.3])
    fig.update_layout(margin=dict(l=8, r=40, t=88, b=64), showlegend=False)
    return fig


def faixa_d042(r: dict) -> go.Figure:
    """Uma linha: extremos (cinza fino) > P5–P95 (banda) > P25–P75 > base (ponto) e mediana (anel)."""
    v = r["valores"]
    fig = _fig(f"{r['medida']}: provavelmente entre {r['faixa_provavel']}",
               f"Valor base, {FAIXA_TXT} e extremos teóricos, em R$", rodape(r), 240)
    y = [r["medida"]]
    fig.add_trace(go.Scatter(x=[v["extremo_min"], v["extremo_max"]], y=y * 2, mode="lines+markers",
                             line=dict(color=COR["comparacao"], width=1.5), marker=dict(symbol="line-ns-open", size=14,
                             color=COR["comparacao"]), name="extremos teóricos",
                             hovertemplate=f"Extremos teóricos: {r['extremos']}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[v["p05"], v["p95"]], y=y * 2, mode="lines", line=dict(color=FAIXA_OBS, width=26),
                             name="faixa provável (P5–P95)",
                             hovertemplate=f"Faixa provável (P5–P95): {r['faixa_provavel_exata']}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[v["p25"], v["p75"]], y=y * 2, mode="lines",
                             line=dict(color="rgba(42,120,214,0.38)", width=26), name="metade central (P25–P75)",
                             hovertemplate=f"P25–P75: {brl(v['p25'])} a {brl(v['p75'])}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[v["p50"]], y=y, mode="markers", name="mediana dos sorteios",
                             marker=dict(symbol="circle-open", size=12, color=COR["texto"], line=dict(width=2)),
                             hovertemplate=f"Mediana dos sorteios: {r['mediana_sorteios']}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[v["base"]], y=y, mode="markers+text", name="valor base (número oficial)",
                             marker=dict(size=13, color=COR["observado"], line=dict(width=2, color="#ffffff")),
                             text=[r["valor_base"]], textposition="top center", textfont=dict(color=COR["texto"]),
                             hovertemplate=f"Valor base: {r['valor_base']}<extra></extra>"))
    fig.update_xaxes(type="log", tickvals=_ticks(v["extremo_min"], v["extremo_max"]),
                     ticktext=[brl(t) for t in _ticks(v["extremo_min"], v["extremo_max"])], showgrid=True,
                     gridcolor=COR["grade"])
    fig.update_yaxes(showticklabels=False, showgrid=False)
    fig.update_layout(height=290, margin=dict(l=8, r=16, t=130, b=80))
    return fig


FAIXA_TXT = "faixa provável (P5–P95, faixa dentro das suposições)"


def _ticks(lo: float, hi: float) -> list[float]:
    cand = [1e4, 2e4, 5e4, 1e5, 2e5, 5e5, 1e6, 2e6, 5e6, 1e7, 2e7, 5e7, 1e8, 2e8]
    return [c for c in cand if lo * 0.8 <= c <= hi * 1.2]


# ------------------------------------------------------------------ Análises
def tornado(r: dict) -> go.Figure:
    t = r["tabela"]
    base = t[0]["premio_base"]
    fig = _fig("Taxa e adesão ao seguro decidem o tamanho do mercado",
               f"Prêmio anual com cada suposição no mínimo e no máximo, as outras no valor base ({r['premio_base']}), "
               "em R$", rodape(r), 470)
    cor = {"suposição (passos 5 a 8)": COR["suposicao"], "passivo e universo": COR["comparacao"]}
    for grupo, c in cor.items():
        linhas = [x for x in t if x["grupo"] == grupo]
        lo = [min(x["premio_no_min"], x["premio_no_max"]) for x in linhas]
        hi = [max(x["premio_no_min"], x["premio_no_max"]) for x in linhas]
        fig.add_trace(go.Bar(y=[x["rotulo"] for x in linhas], x=[h - lo_ for lo_, h in zip(lo, hi)], base=lo,
                             orientation="h", marker_color=c, name=grupo, width=0.55,
                             customdata=[[brl(a), brl(b)] for a, b in zip(lo, hi)],
                             hovertemplate="<b>%{y}</b><br>prêmio de %{customdata[0]} a %{customdata[1]}<extra></extra>"))
    ordem = [x["rotulo"] for x in t]
    fig.add_vline(x=base, line=dict(color=COR["texto"], width=1.5))
    fig.add_annotation(x=base, y=0, yref="paper", text=f"base {brl(base)}", showarrow=False, xanchor="left",
                       yanchor="bottom", xshift=4, font=dict(size=11, color=COR["texto_2"]))
    vals = [100e3, 200e3, 300e3, 400e3, 500e3, 600e3]
    fig.update_xaxes(tickvals=vals, ticktext=[brl(x) for x in vals], showgrid=True, gridcolor=COR["grade"])
    fig.update_yaxes(categoryorder="array", categoryarray=ordem[::-1], showgrid=False)
    fig.update_layout(barmode="overlay", margin=dict(l=8, r=48, t=118, b=72))
    return fig


def previsao_arrecadacao(r: dict) -> go.Figure:
    t = [x for x in r["tabela"] if "principal" in x["variante"]]
    per = [x["periodo"] for x in t]
    fig = _fig("PROJEÇÃO · A arrecadação de MG segue crescendo, mas o 2026-1 já passou da faixa",
               "Arrecadação semestral de MG, em R$ bilhões: projeção central e faixa P10–P90 (tendência do teste T2)",
               rodape(r) + " · projeção, não número oficial", 380)
    fig.add_trace(go.Scatter(x=per + per[::-1], y=[x["p90"] / 1e9 for x in t] + [x["p10"] / 1e9 for x in t][::-1],
                             mode="lines", fill="toself", fillcolor=FAIXA_PROJ, line=dict(width=0),
                             name="faixa P10–P90 (projeção)",
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=per, y=[x["central"] / 1e9 for x in t], mode="lines+markers", name="projeção central",
                             line=dict(color=COR["projecao"], width=2, dash="dash"), marker=dict(size=8),
                             customdata=[[brl(x["central"]), brl(x["p10"]), brl(x["p90"])] for x in t],
                             hovertemplate="<b>%{x}</b> (projeção)<br>central %{customdata[0]}<br>P10–P90 "
                                           "%{customdata[1]} a %{customdata[2]}<extra></extra>"))
    real = [x for x in t if x["realizado"] is not None]
    fig.add_trace(go.Scatter(x=[x["periodo"] for x in real], y=[x["realizado"] / 1e9 for x in real],
                             mode="markers+text", name="realizado (observado, parcial)",
                             marker=dict(size=11, color=COR["observado"], line=dict(width=2, color="#ffffff")),
                             text=[f"realizado {brl(x['realizado'])}" for x in real], textposition="middle right",
                             textfont=dict(color=COR["texto"]),
                             hovertemplate="<b>%{x}</b> realizado (observado, parcial)<br>%{text}<extra></extra>"))
    fig.update_yaxes(title="R$ bilhões por semestre", tickformat=",.1f", rangemode="tozero")
    fig.update_xaxes(title="semestre", type="category")
    fig.update_layout(margin=dict(b=88))
    return fig


def universo_projetado(r: dict, outra: dict | None = None) -> go.Figure:
    """Obrigadas em 2025 (base, observado) e projetadas em 2026–27: leitura principal do limite (laranja, com P10–P90)
    e a outra leitura (cinza tracejado, comparação)."""
    tab = r["tabela"]
    princ, comp = r["leitura_do_limite"], r["comparacao"]
    base = r["valores"]["base_2025"]["n_universo"]
    fig = _fig("PROJEÇÃO · O universo de obrigadas cresce até 2027",
               f"Serventias obrigadas (universo), base 2025 e projeção 2026–27 · leitura em uso: {princ}",
               rodape(r) + " · projeção, não número oficial", 380)
    for leitura, cor, tracejado, nome in ((princ, COR["projecao"], "solid", f"{princ} (leitura em uso)"),
                                          (comp, COR["comparacao"], "dash", f"{comp} (comparação)")):
        d = sorted([x for x in tab if x["cenario_limite"] == leitura and x["medida"] == "n_universo"],
                   key=lambda x: x["periodo"])
        xs = ["2025"] + [x["periodo"] for x in d]
        ys = [base] + [x["central"] for x in d]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines+markers", name=nome, line=dict(color=cor, width=2, dash=tracejado),
            marker=dict(size=9, color=cor, line=dict(width=2, color="#ffffff")),
            error_y=dict(type="data", symmetric=False, array=[0] + [x["p90"] - x["central"] for x in d],
                         arrayminus=[0] + [x["central"] - x["p10"] for x in d], color=cor, thickness=1.5, width=6),
            customdata=[[aprox(base), "base 2025 (número oficial)"]] +
                       [[aprox(x["central"]), f"P10–P90 {aprox(x['p10'])} a {aprox(x['p90'])}"] for x in d],
            hovertemplate=f"<b>%{{x}}</b> · {leitura}<br>%{{customdata[0]}} obrigadas<br>%{{customdata[1]}}<extra></extra>"))
    fig.add_trace(go.Scatter(x=["2025"], y=[base], mode="markers", name="base 2025 (observado)",
                             marker=dict(size=12, color=COR["observado"], line=dict(width=2, color="#ffffff")),
                             hovertemplate=f"<b>2025</b> base (número oficial): {aprox(base)}<extra></extra>"))
    fig.update_yaxes(title="serventias obrigadas", tickformat=",.0f")
    fig.update_xaxes(type="category", title="ano da receita (a classe vale para o ano seguinte)")
    fig.update_layout(margin=dict(b=92))
    return fig


def subidas(r: dict) -> go.Figure:
    """Subidas da Classe 1 para a 2 em 2026: 07 (principal, com P10–P90), 07 na outra leitura e a faixa do 05b."""
    v = r["valores"]
    l7 = list(v["07"])
    pr, co = l7[0], l7[1]
    lo, hi = v["05b_faixa"]
    fig = _fig(f"PROJEÇÃO · Quantas sobem da Classe 1 para a 2 em {r['ano']}: os métodos divergem",
               "Subidas esperadas (serventias) · principal: notebook 07 · comparação: 07 na outra leitura do limite e "
               "05b", rodape(r), 300)
    rot = [f"07 · {pr} (principal)", f"07 · {co} (comparação)", "05b · sem e com recalibração (comparação)"]
    fig.add_trace(go.Scatter(x=[v["07"][pr]["central"]], y=[rot[0]], mode="markers", name="07, principal",
                             marker=dict(size=12, color=COR["projecao"]),
                             error_x=dict(type="data", symmetric=False, array=[v["07"][pr]["p90"] - v["07"][pr]["central"]],
                                          arrayminus=[v["07"][pr]["central"] - v["07"][pr]["p10"]],
                                          color=COR["projecao"], thickness=2, width=8),
                             hovertemplate=f"07 ({pr}): {aprox(v['07'][pr]['central'])}; P10–P90 "
                                           f"{aprox(v['07'][pr]['p10'])} a {aprox(v['07'][pr]['p90'])}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[v["07"][co]["central"]], y=[rot[1]], mode="markers", name="07, comparação",
                             marker=dict(size=10, color="#ffffff", line=dict(width=2, color=COR["comparacao"])),
                             hovertemplate=f"07 ({co}): {aprox(v['07'][co]['central'])}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[lo, hi], y=[rot[2]] * 2, mode="lines+markers", name="05b, faixa (comparação)",
                             line=dict(color=COR["comparacao"], width=6),
                             marker=dict(size=10, color="#ffffff", line=dict(width=2, color=COR["comparacao"])),
                             hovertemplate=f"05b: {_br(lo, 0)} a {_br(hi, 0)} subidas<extra></extra>"))
    fig.update_yaxes(categoryorder="array", categoryarray=rot[::-1], showgrid=False)
    fig.update_xaxes(title="subidas em " + str(r["ano"]), rangemode="tozero", showgrid=True, gridcolor=COR["grade"])
    fig.update_layout(showlegend=False, margin=dict(l=8, r=24, t=88, b=92))
    return fig


def lorenz(r: dict) -> go.Figure:
    v = r["valores"]
    fig = _fig(f"Os {r['topo']} maiores concentram {r['parte_dos_maiores_no_passivo']} do passivo das obrigadas",
               "Curva de concentração (Lorenz): parte acumulada do total × parte das serventias, da menor para a maior",
               rodape(r), 400)
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="igualdade (todos iguais)",
                             line=dict(color=COR["eixo"], width=1), hoverinfo="skip"))
    cores = {"passivo das obrigadas": (COR["observado"], f"passivo das obrigadas (dado) · Gini {r['gini_passivo']}"),
             "déficit esperado": (COR["suposicao"], f"déficit esperado (suposição) · Gini {r['gini_deficit']}")}
    for medida, (cor, nome) in cores.items():
        c = [x for x in r["curva"] if x["medida"] == medida]
        fig.add_trace(go.Scatter(x=[x["fracao_unidades"] for x in c], y=[x["fracao_valor"] for x in c], mode="lines",
                                 name=nome, line=dict(color=cor, width=2),
                                 hovertemplate="%{x:.0%} das serventias somam %{y:.1%} do total<extra></extra>"))
    x90 = 1 - v["topo"]
    fig.add_vline(x=x90, line=dict(color=COR["comparacao"], width=1, dash="dot"))
    fig.add_annotation(x=x90, y=0.04, text=f"os {r['topo']} maiores ficam à direita", showarrow=False, xanchor="right",
                       xshift=-6, font=dict(size=11, color=COR["texto_2"]))
    fig.update_xaxes(tickformat=".0%", title="parte das serventias obrigadas (da menor para a maior)", range=[0, 1])
    fig.update_yaxes(tickformat=".0%", title="parte acumulada do total", range=[0, 1.02])
    fig.update_layout(separators=",.", margin=dict(l=8, r=16, t=118, b=92))
    return fig


def pergunta_9(r: dict) -> go.Figure:
    t = r["tabela"]
    fig = _fig("Lucro ou prejuízo depende de quem paga quando a delegação termina",
               "Índice combinado (sinistros + comissão + despesas ÷ prêmio) pela chance de a delegação terminar no ano; "
               "acima de 100% é prejuízo", rodape(r), 380)
    for prefixo, cor, nome in (("com", COR["observado"], "com a capacidade de pagar (M1): o titular paga com a renda"),
                               ("sem", COR["suposicao"], "sem a M1: o titular não paga nada")):
        d = sorted([x for x in t if x["leitura"].startswith(prefixo)], key=lambda x: x["p_fim"])
        fig.add_trace(go.Scatter(x=[x["p_fim"] for x in d], y=[x["indice_combinado"] for x in d], mode="lines+markers",
                                 name=nome, line=dict(color=cor, width=2), marker=dict(size=9),
                                 customdata=[[pct(x["indice_combinado"]), brl(x["resultado_tecnico"])] for x in d],
                                 hovertemplate="P(fim) %{x:.1%}<br>índice combinado %{customdata[0]}<br>resultado "
                                               "técnico %{customdata[1]} por ano<extra></extra>"))
    fig.add_hline(y=1, line=dict(color=COR["alerta"], width=1, dash="dot"))
    fig.add_annotation(x=1, xref="paper", y=1, text="100% = empate", showarrow=False, xanchor="right", yshift=10,
                       font=dict(size=11, color=COR["alerta"]))
    fig.update_xaxes(tickformat=".1%", title="chance de a delegação terminar no ano (notebook 05c)",
                     tickvals=sorted({x["p_fim"] for x in t}))
    fig.update_yaxes(type="log", tickvals=[0.25, 0.5, 1, 2, 4], ticktext=["25%", "50%", "100%", "200%", "400%"],
                     title="índice combinado (escala log)")
    fig.update_layout(margin=dict(l=8, r=16, t=118, b=92))
    return fig


# ------------------------------------------------------------------ Mercado
def grupos(r: dict) -> go.Figure:
    t = r["tabela"]
    alvo = r["valores"]["alvo"]
    rot = [f"<b>{x['nome_grupo']}</b>" if x["grupo"] == alvo else x["nome_grupo"] for x in t]
    fig = _fig("As providas grandes são o cliente do seguro",
               "Parte de MG em cada tipo de cartório (k-means do notebook 04), em %", rodape(r), 420)
    series = [("pct_serventias", "das serventias", COR["comparacao"]),
              ("pct_passivo_obrigadas_mg", "do passivo das obrigadas (dado)", COR["observado"]),
              ("pct_deficit_mg", "do déficit (suposição)", COR["suposicao"])]
    for col, nome, cor in series:
        fig.add_trace(go.Bar(y=rot, x=[x[col] for x in t], orientation="h", name=nome, marker_color=cor,
                             customdata=[pct(x[col]) for x in t],
                             hovertemplate="%{y}<br>%{customdata} " + nome + "<extra></extra>"))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(tickformat=".0%", range=[0, 0.85], showgrid=True, gridcolor=COR["grade"])
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08, margin=dict(l=8, r=16, t=118, b=72))
    return fig


def quem_e_obrigado(r: dict) -> go.Figure:
    t = r["tabela"]
    fig = _fig("Registro de Imóveis e 3 ou mais empregados: quase sempre obrigado",
               f"Parte das serventias de classe conhecida que é obrigada, por atribuição e por porte (média de MG: "
               f"{r['media_obrigadas']})", rodape(r), 400)
    rot = [f"{x['item']}" for x in t]
    fig.add_trace(go.Bar(y=rot, x=[x["pct"] for x in t], orientation="h", marker_color=COR["observado"], width=0.55,
                         text=[pct(x["pct"]) for x in t], textposition="outside", cliponaxis=False,
                         customdata=[[_br(x["serventias"], 0), _br(x["obrigadas"], 0), x["tipo"]] for x in t],
                         hovertemplate="<b>%{y}</b> (%{customdata[2]})<br>%{customdata[1]} obrigadas de "
                                       "%{customdata[0]}<extra></extra>"))
    fig.add_vline(x=r["valores"]["media"], line=dict(color=COR["comparacao"], width=1, dash="dot"))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(tickformat=".0%", range=[0, 1.05], showgrid=True, gridcolor=COR["grade"])
    fig.update_layout(showlegend=False, margin=dict(l=8, r=40, t=88, b=64))
    return fig


# ------------------------------------------------------------------ Qualidade dos dados
def escolhas_metodo(r: dict) -> go.Figure:
    t = sorted(r["tabela"], key=lambda x: x["efeito_passivo"])
    fig = _fig(r["bloco"], "Efeito no passivo de todas as ativas, em % da base (sensibilidade)", rodape(r), 300)
    curto = {"t5_salario_estimado": "T5: salário estimado para os vínculos sem dezembro",
             "t6_encolhimento": "T6: reserva por encolhimento (município pequeno)",
             "sem_regiao": "Reserva = MG inteiro (sem a região)"}
    fig.add_trace(go.Bar(y=[curto.get(x["chave"], x["rotulo"]) for x in t], x=[x["efeito_passivo"] for x in t],
                         orientation="h", marker_color=COR["suposicao"], width=0.5, text=[x["efeito_txt"] for x in t],
                         textposition="outside", cliponaxis=False,
                         customdata=[[x["rotulo"], brl(x["passivo_todas"])] for x in t],
                         hovertemplate="%{customdata[0]}<br>passivo %{customdata[1]} (%{text})<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=COR["texto"], width=1))
    m = max(abs(x["efeito_passivo"]) for x in t) * 1.45
    fig.update_xaxes(tickformat="+.0%", range=[-m, m], showgrid=True, gridcolor=COR["grade"])
    fig.update_yaxes(showgrid=False)
    fig.update_layout(showlegend=False, margin=dict(l=8, r=40, t=88, b=64))
    return fig


def leitura_literal(r: dict) -> go.Figure:
    t = r["tabela"]
    fig = _fig("Ao pé da letra, sai 1 em cada 5 obrigadas, mas o prêmio quase não muda",
               "Variação com a receita líquida do repasse (art. 2º, XXIV, do Prov. 213), em % da base (sensibilidade)",
               rodape(r), 300)
    fig.add_trace(go.Bar(y=[x["medida"] for x in t], x=[x["variacao"] for x in t], orientation="h",
                         marker_color=COR["suposicao"], width=0.5, text=[x["variacao_txt"] for x in t],
                         textposition="outside", cliponaxis=False,
                         customdata=[[x["base_txt"], x["literal_txt"]] for x in t],
                         hovertemplate="<b>%{y}</b><br>base %{customdata[0]} → %{customdata[1]} (%{text})<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=COR["texto"], width=1))
    m = max(abs(x["variacao"]) for x in t) * 1.45
    fig.update_xaxes(tickformat="+.0%", range=[-m, m * 0.15], showgrid=True, gridcolor=COR["grade"])
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_layout(showlegend=False, margin=dict(l=8, r=40, t=88, b=64))
    return fig
