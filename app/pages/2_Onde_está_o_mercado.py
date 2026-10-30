"""Onde está o mercado: o mapa do déficit de cobertura (o que vira seguro) por área, com um filtro só (município).

Só lê tabelas públicas do gold (1.7), na regra base e no nível base. Dois modos (D-026, U1):
- sem município: áreas da visão geral (municípios com 3+ serventias e grupos de municípios pequenos);
- município: destaque com contexto (o município, ou a área agregada a que ele pertence, se tiver menos de 3), com zoom
  na região intermediária.
Os filtros por atribuição, situação e classe, as outras métricas, o ranking e a tabela por área saíram do painel
(docs/painel/corte.md); o chat responde por município e por recorte.
"""
import json
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from comum import analise, brl, consulta, execucao, fonte_linha, md_seguro, num, pagina, pct, ticks_brl
from src.painel import ui
from src.painel.graficos import COR, SEQUENCIAL, finalizar

pagina("Onde está o mercado", "🗺️", "Onde está o dinheiro?",
       "O déficit de cobertura, que é o que vira seguro, se concentra nas maiores cidades. Escolha um município para "
       "ver a parte dele.", sobre="Onde está o mercado")
LIMIAR = int(execucao().limiar_lgpd)
CINZA, SEM_SERV, CONTORNO = "#dde2ea", "#f5f7fa", "#45506a"   # tokens line, surface-2 e ink-2 do Raio-X (D-052)
METRICA = "valor_descoberto"


# ------------------------------------------------------------------ dados (só tabelas públicas, com cache)
@st.cache_data
def tab(sql: str, params: tuple = ()) -> pd.DataFrame:
    return consulta(sql, list(params))


@st.cache_data
def geojson(sql: str, params: tuple = ()) -> dict:
    g = consulta(sql, list(params))
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": a, "properties": {}, "geometry": json.loads(x)} for a, x in zip(g["area_id"], g["geometria"])]}


areas = tab("SELECT * FROM gold.mercado_area_publico")
municipios = tab("""SELECT m.cod_ibge, m.nome, m.regiao_imediata, m.regiao_intermediaria, a.area_id, d.n_serventias
                    FROM silver.municipio_ibge m JOIN gold.geo_area_municipio a USING (cod_ibge)
                    JOIN gold.dim_municipio d USING (cod_ibge) ORDER BY m.nome""")
sem_serventia = tab("SELECT municipio FROM gold.dim_municipio WHERE n_serventias = 0")["municipio"].tolist()
total_mg = float(areas[METRICA].sum())
areas["valor_txt"] = areas[METRICA].map(brl)
areas["pct_txt"] = [pct(v / total_mg) for v in areas[METRICA]]

# ------------------------------------------------------------------ o filtro principal
c_filtro, _ = st.columns([4, 8])
mun_nome = c_filtro.selectbox("Município", ["Todos"] + sorted(municipios["nome"].tolist() + sem_serventia),
                              key="f_mun")
mun = municipios[municipios["nome"] == mun_nome].iloc[0] if mun_nome not in ("Todos", *sem_serventia) else None
foco = areas[areas["area_id"] == mun["area_id"]].iloc[0] if mun is not None else None
if mun_nome in sem_serventia:
    st.info(f"{mun_nome} não tem cartório no cadastro do CNJ. Mostrando Minas Gerais inteira.")
elif foco is not None and foco["tipo"] != "municipio":
    st.info(md_seguro(f"{mun_nome} tem menos de {LIMIAR} cartórios: aparece agregado em “{foco['area_nome']}”, para "
                      "proteger os dados de cada cartório (LGPD). Os números abaixo são dessa área."))

# ------------------------------------------------------------------ até 3 números
if foco is None:
    ordem = areas.sort_values(METRICA, ascending=False)
    maior = ordem.iloc[0]
    ui.grade([ui.kpi(f"Só {maior['area_nome']}", maior["pct_txt"], f"do déficit de MG ({maior['valor_txt']})"),
              ui.kpi("As 10 áreas com mais déficit", pct(ordem[METRICA].head(10).sum() / total_mg),
                     f"do déficit de MG, entre {num(len(areas))} áreas do mapa"),
              ui.kpi("Áreas com algum déficit", f"{num((areas[METRICA] > 0).sum())} de {num(len(areas))}",
                     "o déficit está espalhado, mas é pequeno fora das maiores cidades")], 3)
else:
    nome = mun_nome if foco["tipo"] == "municipio" else foco["area_nome"]
    ui.grade([ui.kpi(f"Déficit em {nome}", foco["valor_txt"], "a parte da dívida trabalhista sem bens que a cubram",
                     dica="déficit de cobertura: precisa de garantia (fiança bancária ou seguro); suposição do modelo"),
              ui.kpi("Parte do déficit de MG", foco["pct_txt"], "quanto esta área pesa no mercado do estado"),
              ui.kpi("Cartórios na área", num(foco["n_serventias"]),
                     "ativos no cadastro do CNJ" if foco["tipo"] == "municipio" else
                     "somados com os vizinhos pequenos (LGPD)")], 3)


# ------------------------------------------------------------------ mapa (largura inteira)
def camada(geo, ids, cor, hover, linha=0.4, cor_linha="#ffffff"):
    return go.Choroplethmap(geojson=geo, locations=ids, z=[1] * len(ids), colorscale=[[0, cor], [1, cor]],
                            showscale=False, marker_line_width=linha, marker_line_color=cor_linha,
                            hovertemplate=hover + "<extra></extra>")


def _merc(lat: float) -> float:
    s = math.sin(math.radians(lat))
    return 0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)   # y de Web Mercator em fração do mundo


def _enquadrar(lons: list[float], lats: list[float]) -> tuple[dict, float]:
    """Centro e zoom para a caixa caber no mapa. No zoom z o mundo mede 512 × 2^z px (MapLibre). Usa a largura útil
    do mapa na tela do celular (a figura não sabe a largura da tela; no computador, sobra contexto em volta) e a
    altura da figura, com folga."""
    largura, altura, folga = 320, 520, 0.85
    y0, y1 = _merc(max(lats)), _merc(min(lats))
    dx, dy = max(max(lons) - min(lons), 0.05) / 360, max(y1 - y0, 0.0002)
    zoom = min(9.0, math.log2(min(largura / (512 * dx), altura / (512 * dy)) * folga))
    ym = (y0 + y1) / 2   # centro no meio da caixa em Mercator (não no meio das latitudes)
    lat_c = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ym))))
    return {"lat": lat_c, "lon": (min(lons) + max(lons)) / 2}, zoom


def _pontos(geom: dict):
    coords = geom["coordinates"]
    polys = coords if geom["type"] == "MultiPolygon" else [coords]
    for poly in polys:
        yield from poly[0]


def mapa(destaque: str | None, zoom_ids: list[str] | None) -> go.Figure:
    geo_dados = geojson("SELECT area_id, geometria FROM gold.geo_mapa_publico")
    geo_sem = geojson("SELECT area_id, geometria FROM gold.geo_sem_serventia")
    fig = go.Figure(layout=dict(template="radar", paper_bgcolor=COR["superficie"]))
    vmax = float(areas[METRICA].quantile(0.95)) or float(areas[METRICA].max()) or 1.0
    vals, textos = ticks_brl(vmax)
    textos[-1] = "≥ " + textos[-1]   # a cor satura no percentil 95
    d = areas
    fig.add_trace(go.Choroplethmap(
        geojson=geo_dados, locations=d["area_id"], z=d[METRICA], zmin=0, zmax=vmax, colorscale=SEQUENCIAL,
        marker_line_width=0.4, marker_line_color="#ffffff",
        customdata=d[["area_nome", "n_serventias", "valor_txt", "pct_txt"]].to_numpy(),
        hovertemplate=("<b>%{customdata[0]}</b><br>Cartórios: %{customdata[1]}<br>Déficit: %{customdata[2]}<br>"
                       "%{customdata[3]} do déficit de MG<extra></extra>"),
        colorbar=dict(title=dict(text="Déficit", side="top", font=dict(color=COR["texto"], size=12)), thickness=10,
                      len=0.6, tickvals=vals, ticktext=textos, tickfont=dict(color=COR["texto_2"], size=12),
                      x=0.98, xanchor="right", y=0.5, bgcolor="rgba(255,255,255,0.85)", outlinewidth=0)))
    if destaque:
        f = d[d["area_id"] == destaque]
        fig.add_trace(go.Choroplethmap(geojson=geo_dados, locations=f["area_id"], z=f[METRICA], zmin=0, zmax=vmax,
                                       colorscale=SEQUENCIAL, showscale=False, marker_line_width=2.5,
                                       marker_line_color=CONTORNO, hoverinfo="skip"))
    # por último: o polígono de uma região imediata cobre os municípios sem serventia
    fig.add_trace(camada(geo_sem, [f["id"] for f in geo_sem["features"]], SEM_SERV,
                         "Município sem cartório no cadastro do CNJ", 1.2, CONTORNO))
    centro, zoom = {"lat": -18.4, "lon": -44.6}, 5.4
    if zoom_ids:
        alvo = set(zoom_ids) | {destaque}   # o destaque sempre entra no enquadramento
        pts = [p for f in geo_dados["features"] if f["id"] in alvo for p in _pontos(f["geometry"])]
        if pts:
            centro, zoom = _enquadrar([p[0] for p in pts], [p[1] for p in pts])
    fig.update_layout(map=dict(style="white-bg", center=centro, zoom=zoom), margin=dict(l=0, r=0, t=0, b=0),
                      height=560)
    return fig


ids_int = (list(municipios.loc[municipios["regiao_intermediaria"] == mun["regiao_intermediaria"], "area_id"].unique())
           if mun is not None else None)
st.plotly_chart(finalizar(mapa(foco["area_id"] if foco is not None else None, ids_int)), width="stretch", theme=None,
                config={"displayModeBar": False})
ui.fonte(fonte_linha(["cnj_serventias", "rais_vinculos", "ibge_malha"],
                     "Cor = déficit da área (suposição do modelo); áreas com menos de 3 cartórios aparecem somadas"))

conc = analise("concentracao")
grp = analise("grupos")
ui.frase(f"Os {conc['topo']} maiores cartórios obrigados têm **{conc['parte_dos_maiores_no_passivo']}** da dívida "
         f"trabalhista; o cliente típico do seguro são as **{grp['grupo_alvo'].split(': ')[1]}** "
         f"({grp['serventias_do_alvo']} cartórios, {grp['parte_do_deficit']} do déficit).")
ui.sugestoes(["Quais cartórios de Uberaba são obrigados?", "Que tipo de cartório é obrigado pelo Prov. 227?",
              "Quantos cartórios vagos (interinos) há em MG?"])
