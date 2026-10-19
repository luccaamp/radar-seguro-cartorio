"""Mercado: serventias, empregados, passivo e déficit de MG, com mapa, ranking e tabela no mesmo recorte.

Só lê tabelas públicas do gold (1.7). Quatro modos (D-026, U1):
- sem filtro: áreas da visão geral (municípios com 3+ serventias e grupos de municípios pequenos);
- um filtro (atribuição, situação ou classe): regiões imediatas e grupos de intermediária pré-agregados no gold, com
  supressão complementar (E1);
- município: destaque com contexto (o município, ou a área agregada a que ele pertence, se tiver menos de 3);
- município + filtro: só o nível regional do filtro.
Mapa, ranking e tabela por área usam sempre o nível base e a regra base (trocar mudaria quem entra no universo e a
diferença isolaria serventias); a regra v1 e o mínimo/máximo ficam nos totais de MG, onde o auditor aprovou.
"""
import json
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml

from comum import (AZUL_SEQUENCIAL, AZUL_SERIE, EXPLICA_NIVEIS, NIVEIS, RAIZ, aprox, aviso_estimativa, brl, consulta,
                   execucao, md_seguro, num, pct, rodape, ticks_brl)

st.set_page_config(page_title="Mercado", page_icon="🗺️", layout="wide")
st.title("Mercado — Minas Gerais")
aviso_estimativa()
LIMIAR = int(execucao().limiar_lgpd)
REGRA_BASE = yaml.safe_load((RAIZ / "config" / "regras_classificacao.yaml").read_text(encoding="utf-8"))["versao_base"]
CINZA, SEM_SERV, CONTORNO = "#c9c8c4", "#f3f2ee", "#55534e"
FILTROS = {"nenhum": "Nenhum", "atribuicao": "Atribuição", "situacao": "Situação",
           "classe": "Classe (Prov. 213, regra base)"}
VALORES = {
    "atribuicao": {"notas": "Notas", "rcpn": "Registro Civil (PN)", "ri": "Registro de Imóveis",
                   "rtd_rcpj": "Títulos e Documentos / Pessoa Jurídica", "protesto": "Protesto"},
    "situacao": {"PROVIDO": "Provida (titular)", "VAGO": "Vaga (interino)", "SOB INTERVENÇÃO": "Sob intervenção",
                 "CONVERSÃO EM DILIGÊNCIA": "Conversão em diligência"},
    "classe": {"1": "Classe 1", "2": "Classe 2", "3": "Classe 3", "indeterminada": "Indeterminada"}}
METRICAS = {"valor_descoberto": "Déficit (base)", "passivo": "Passivo de todas as ativas (base)",
            "n_serventias": "Serventias ativas", "clt": "Empregados CLT"}
EM_REAIS = {"valor_descoberto", "passivo"}
TITULO_ESCALA = {"valor_descoberto": "Déficit", "passivo": "Passivo", "n_serventias": "Serventias", "clt": "Empregados"}
TIPO = {"municipio": "município", "regiao_agregada": "grupo de municípios pequenos", "regiao_imediata": "região imediata",
        "regiao_intermediaria": "grupo de regiões (intermediária)", "outras": "outras regiões"}


# ------------------------------------------------------------------ dados (só tabelas públicas, com cache)
@st.cache_data
def tab(sql: str, params: tuple = ()) -> pd.DataFrame:
    return consulta(sql, list(params))


@st.cache_data
def geojson(sql: str, params: tuple = ()) -> dict:
    g = consulta(sql, list(params))
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": a, "properties": {}, "geometry": json.loads(x)} for a, x in zip(g["area_id"], g["geometria"])]}


def curto(nome: str) -> str:
    """Rótulo curto para ranking e tabela; o nome completo fica no texto do mouse."""
    for longo, abrev in (("Região imediata de ", "RI "), ("Região intermediária de ", "Int. ")):
        if nome.startswith(longo):
            resto = nome[len(longo):]
            base, _, det = resto.partition(" — ")
            n = det.split(" ")[0] if det else ""
            return f"{abrev}{base}" + (f" ({n} {'mun.' if 'municípios' in det else 'RI'})" if n else "")
    return nome.split(" — ")[0]


def fmt(metrica: str, v: float) -> str:
    return brl(v) if metrica in EM_REAIS else num(v)


uf_geral = tab("SELECT * FROM gold.fato_mercado_uf WHERE cenario_stf = 'mantem'").set_index(["regra_classe", "nivel"])
areas_gerais = tab("SELECT * FROM gold.mercado_area_publico")
municipios = tab("""SELECT m.cod_ibge, m.nome, m.regiao_imediata, m.regiao_intermediaria, a.area_id, d.n_serventias
                    FROM silver.municipio_ibge m JOIN gold.geo_area_municipio a USING (cod_ibge)
                    JOIN gold.dim_municipio d USING (cod_ibge) ORDER BY m.nome""")

# ------------------------------------------------------------------ controles (uma linha acima de tudo)
PADROES = {"f_regra": REGRA_BASE, "f_mun": "Todos", "f_tipo": "nenhum", "f_valor": None}
for k, v in PADROES.items():
    st.session_state.setdefault(k, v)


def limpar():
    for k, v in PADROES.items():
        st.session_state[k] = v


c1, c2, c3, c4, c5 = st.columns([1.3, 2, 2, 2.6, 1])
regra = c1.radio("Classe 1 até", ["v2", "v1"], key="f_regra",
                 format_func=lambda r: {"v2": "R$ 300 mil", "v1": "R$ 100 mil"}[r],
                 help="v2 = Prov. 243 (base); v1 = Prov. 213 original (sensibilidade, só nos totais de MG)")
sem_serventia = tab("SELECT municipio FROM gold.dim_municipio WHERE n_serventias = 0")["municipio"].tolist()
mun_nome = c2.selectbox("Município", ["Todos"] + sorted(municipios["nome"].tolist() + sem_serventia), key="f_mun")
tipo = c3.selectbox("Filtrar por", list(FILTROS), format_func=FILTROS.get, key="f_tipo",
                    help="Um filtro por vez (LGPD): o recorte é pré-agregado por região no gold.")
valor = None
if tipo != "nenhum":
    opcoes = list(VALORES[tipo])
    if st.session_state["f_valor"] not in opcoes:
        st.session_state["f_valor"] = opcoes[0]
    valor = c4.selectbox("Valor", opcoes, format_func=VALORES[tipo].get, key="f_valor")
# sem filtro, o seletor "Valor" fica escondido (o desabilitado tinha rótulo de contraste baixo; acessibilidade)
c5.button("Limpar", on_click=limpar, width="stretch", help="Limpar filtros")   # rótulo curto: cabia cortado em 1280 px

visao = f"{tipo}={valor}" if tipo != "nenhum" else None
if mun_nome in sem_serventia:
    st.info(f"{mun_nome}: sem serventia no cadastro do CNJ em out/2026 (ver Limitações na página Qualidade dos "
            "dados). Mostrando a visão geral.")
mun = (municipios[municipios["nome"] == mun_nome].iloc[0]
       if mun_nome not in ("Todos", *sem_serventia) else None)
nivel_txt = ("nível municipal" if visao is None and mun is None else
             "nível regional por LGPD" if visao else "destaque com contexto")
partes = ([f"Município: {mun_nome}"] if mun is not None else []) + ([f"{FILTROS[tipo]}: {VALORES[tipo][valor]}"] if visao else [])
st.markdown(f"**Filtros:** {' · '.join(partes) if partes else 'nenhum'} · {nivel_txt}")

# ------------------------------------------------------------------ recorte: tabelas da visão escolhida
if visao:
    v_area = tab("SELECT * FROM gold.mercado_filtro_area WHERE visao = ?", (visao,))
    v_uf = tab("SELECT * FROM gold.mercado_filtro_uf WHERE visao = ? AND publicado", (visao,)).set_index(
        ["regra_classe", "nivel"])
    v_reg = tab("SELECT * FROM gold.mercado_filtro_regiao WHERE visao = ?", (visao,))
else:
    v_area, v_uf, v_reg = None, None, None
regra_uf = regra if (visao is None or (regra, "base") in v_uf.index) else REGRA_BASE
if visao and regra_uf != regra:
    st.warning(md_seguro("A regra v1 não é exibida neste filtro: a diferença para a regra base isolaria 1 ou 2 "
                         "serventias (LGPD). Mostrando a regra base (R$ 300 mil)."))

# área destacada (modo município)
foco = None
if mun is not None:
    if visao is None:
        foco = areas_gerais[areas_gerais["area_id"] == mun["area_id"]].iloc[0]
        if foco["tipo"] != "municipio":
            st.info(md_seguro(f"{mun_nome} tem menos de {LIMIAR} serventias: aparece agregado em "
                              f"“{foco['area_nome']}” (LGPD). Os números abaixo são dessa área."))
    else:
        alvo = v_reg[v_reg["regiao_imediata"] == mun["regiao_imediata"]]
        area_id = alvo["area_id"].iloc[0] if len(alvo) else None
        if area_id is None or pd.isna(area_id):
            st.warning(f"Não há dado publicável do recorte na região de {mun_nome} (menos de {LIMIAR} serventias ou "
                       "complemento pequeno demais; LGPD).")
        else:
            foco = v_area[v_area["area_id"] == area_id].iloc[0]
            st.info(f"Município + filtro: por LGPD, só o nível regional — “{foco['area_nome']}”, que contém {mun_nome}.")


# ------------------------------------------------------------------ KPIs
def kpis(serv, clt, univ, pt, pu, nd, dfc, ref: dict | None):
    def m(col, rotulo, valor_txt, v, chave, ajuda=None):
        col.metric(rotulo, valor_txt, help=ajuda)
        if ref and ref.get(chave):
            col.caption(f"{pct(v / ref[chave])} de MG")
    k = st.columns(4)
    m(k[0], "Serventias ativas", num(serv), serv, "serv")
    m(k[1], "Empregados CLT declarados", num(clt), clt, "clt")
    m(k[2], "Obrigadas pelo Prov. 227", aprox(univ), univ, "univ",
      "Universo: sem interinos (vagas) e sem Classe 1 (art. 19); valor esperado, inclui o peso das indeterminadas.")
    m(k[3], "Com déficit (esperado)", aprox(nd), nd, "nd",
      "Valor esperado: soma das probabilidades de déficit das obrigadas (suposição, D-016).")
    k = st.columns(4)
    m(k[0], "Passivo (todas)", brl(pt), pt, "pt", "Passivo de todas as ativas: custo de demitir todos os empregados CLT.")
    m(k[1], "Passivo (obrigados)", brl(pu), pu, "pu", "Só as serventias obrigadas pelo Prov. 227.")
    m(k[2], "Déficit estimado", brl(dfc), dfc, "dfc")


g_base = uf_geral.loc[(REGRA_BASE, "base")]
ref_mg = {"serv": g_base["n_serventias_ativas"], "clt": g_base["clt"], "univ": g_base["n_universo"],
          "pt": g_base["passivo_todas"], "pu": g_base["passivo_universo"], "nd": g_base["n_deficit"],
          "dfc": g_base["valor_descoberto"]}
if foco is not None:
    kpis(foco["n_serventias"], foco["clt"], foco["n_universo"], foco["passivo"], foco["passivo_universo"],
         foco["n_deficit"], foco["valor_descoberto"], ref_mg)
elif visao:
    u = v_uf.loc[(regra_uf, "base")]
    kpis(u["n_serventias_ativas"], u["clt"], u["n_universo"], u["passivo_todas"], u["passivo_universo"],
         u["n_deficit"], u["valor_descoberto"], ref_mg)
elif mun is None:
    u = uf_geral.loc[(regra, "base")]
    kpis(u["n_serventias_ativas"], u["clt"], u["n_universo"], u["passivo_todas"], u["passivo_universo"],
         u["n_deficit"], u["valor_descoberto"], None)
if visao == "classe=1":
    st.info("A Classe 1 está fora da obrigação (Prov. 213/243; art. 19 do Prov. 227): passivo exibido, déficit e "
            "prêmio zero por definição.")
if tipo == "atribuicao":
    st.caption("Uma serventia pode ter várias atribuições: somadas, as atribuições passam do total de MG.")

# ------------------------------------------------------------------ Faixas (só nos totais de MG)
if foco is None:
    fonte_f = uf_geral if visao is None else v_uf
    linhas, passivo_todas = [], []
    for nivel in ("min", "base", "max"):
        if (regra_uf, nivel) not in fonte_f.index:
            continue
        x = fonte_f.loc[(regra_uf, nivel)]
        passivo_todas.append(f"{NIVEIS[nivel]} {brl(x['passivo_todas'])}")
        linhas.append({"Nível": NIVEIS[nivel], "Passivo (obrigados)": brl(x["passivo_universo"]),
                       "Obrigadas": aprox(x["n_universo"]), "Déficit": brl(x["valor_descoberto"]),
                       "IS": brl(x["mercado_importancia_segurada"]), "Prêmio anual": brl(x["mercado_premio_emitido"])})
    st.markdown("**Faixas** — cenário do STF: regra mantida")
    # C3: "Passivo (todas)" foi para o "?" do cabeçalho "Nível", para a tabela caber em 1280 px
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch", column_config={
        "Nível": st.column_config.TextColumn(help=md_seguro("Passivo de todas as ativas: " + "; ".join(passivo_todas))),
        "Passivo (obrigados)": st.column_config.TextColumn(help="Passivo das serventias obrigadas pelo Prov. 227"),
        "Obrigadas": st.column_config.TextColumn(help="Valor esperado (inclui o peso das indeterminadas)"),
        "IS": st.column_config.TextColumn(help="Importância segurada = déficit × fatia que escolhe seguro"),
        "Prêmio anual": st.column_config.TextColumn(help="Prêmio = importância segurada × taxa (suposição)")})
    if len(linhas) < 3:
        st.caption("Mínimo e/ou máximo não exibidos neste filtro: trocar o nível muda quem entra no universo, e a "
                   "diferença isolaria 1 ou 2 serventias (LGPD).")
    st.caption(md_seguro(EXPLICA_NIVEIS))
else:
    st.caption("Faixas (mínimo e máximo) só nos totais de MG: no nível de uma área, trocar o nível isolaria serventias "
               "(LGPD). Valores no nível base e na regra base.")
if regra != REGRA_BASE and (visao or mun is not None):
    st.caption(md_seguro("Mapa, ranking e tabela sempre na regra base (R$ 300 mil): por área, a troca de regra "
                         "isolaria serventias."))
rodape(["cnj_serventias", "cnj_colaboradores", "cnj_arrecadacao", "rais_vinculos"],
       "Passivo do art. 5º do Prov. 227 (custo de demissão sem justa causa de todos os empregados CLT); "
       "déficit = prob. de déficit × parte descoberta (suposições, D-016); prêmio = importância segurada × taxa.",
       taxa=True)

# ------------------------------------------------------------------ mapa, ranking e tabela no mesmo recorte
metrica = st.radio("Métrica do mapa e do ranking", list(METRICAS), format_func=METRICAS.get, horizontal=True)
if visao:
    dados = v_area[v_area["nivel_area"] != "outras"].copy()
    geo_dados = geojson("SELECT area_id, geometria FROM gold.geo_regiao_imediata UNION ALL "
                        "SELECT area_id, geometria FROM gold.geo_mapa_filtro WHERE visao = ?", (visao,))
    total_mg = float(v_uf.loc[(REGRA_BASE, "base")][{"valor_descoberto": "valor_descoberto", "passivo": "passivo_todas",
                                                     "n_serventias": "n_serventias_ativas", "clt": "clt"}[metrica]])
else:
    dados = areas_gerais.copy()
    dados["nivel_area"] = dados["tipo"]
    geo_dados = geojson("SELECT area_id, geometria FROM gold.geo_mapa_publico")
    total_mg = float(dados[metrica].sum())
geo_contexto = geojson("SELECT area_id, geometria FROM gold.geo_mapa_publico")
geo_sem = geojson("SELECT area_id, geometria FROM gold.geo_sem_serventia")
dados["rotulo"] = dados["area_nome"].map(curto)
dados["valor_txt"] = [fmt(metrica, v) for v in dados[metrica]]
dados["pct_txt"] = [pct(v / total_mg) if total_mg else "—" for v in dados[metrica]]
dados["tipo_txt"] = dados["nivel_area"].map(TIPO)
tudo_zero = not (dados[metrica].abs() > 0).any()


def camada(geo, ids, cor, hover, linha=0.4, cor_linha="#fcfcfb"):
    return go.Choroplethmap(geojson=geo, locations=ids, z=[1] * len(ids), colorscale=[[0, cor], [1, cor]],
                            showscale=False, marker_line_width=linha, marker_line_color=cor_linha,
                            hovertemplate=hover + "<extra></extra>")


def mapa(destaque: str | None = None, zoom_ids: list[str] | None = None) -> go.Figure:
    fig = go.Figure()
    ctx_ids = [f["id"] for f in geo_contexto["features"]]
    fig.add_trace(camada(geo_contexto, ctx_ids, CINZA, "Sem dado publicável neste recorte"))
    d = dados if destaque is None else dados[dados["area_id"] == destaque]
    vmax = float(dados[metrica].quantile(0.95)) or float(dados[metrica].max()) or 1.0
    satura = float(dados[metrica].max()) > vmax
    if metrica in EM_REAIS:
        vals, textos = ticks_brl(vmax)
    else:
        vals = [vmax * i / 4 for i in range(5)]
        textos = [num(v) for v in vals]
    if satura:
        textos[-1] = "≥ " + textos[-1]
    fig.add_trace(go.Choroplethmap(
        geojson=geo_dados, locations=d["area_id"], z=d[metrica], zmin=0, zmax=vmax, colorscale=AZUL_SEQUENCIAL,
        marker_line_width=2.5 if destaque else 0.4, marker_line_color=CONTORNO if destaque else "#fcfcfb",
        customdata=d[["area_nome", "tipo_txt", "n_serventias", "valor_txt", "pct_txt"]].to_numpy(),
        hovertemplate=("<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Serventias: %{customdata[2]}<br>"
                       f"{METRICAS[metrica]}: " "%{customdata[3]}<br>%{customdata[4]} de MG<extra></extra>"),
        # C2: escala dentro da figura, com fundo, título curto e marcas formatadas
        colorbar=dict(title=dict(text=TITULO_ESCALA[metrica], side="top"), thickness=12, len=0.62, tickvals=vals,
                      ticktext=textos, x=0.99, xanchor="right", y=0.5, bgcolor="rgba(252,252,251,0.85)",
                      outlinewidth=0)))
    # por último: o polígono de uma região imediata cobre os municípios sem serventia (terceiro estado do E5)
    fig.add_trace(camada(geo_sem, [f["id"] for f in geo_sem["features"]], SEM_SERV,
                         "Município sem serventia no cadastro do CNJ (ver Limitações)", 1.6, CONTORNO))
    centro, zoom = {"lat": -18.4, "lon": -44.6}, 5.1
    if zoom_ids:
        alvo = set(zoom_ids) | ({destaque} if destaque else set())   # o destaque sempre entra no enquadramento
        pts = [p for g in (geo_contexto, geo_dados) for f in g["features"] if f["id"] in alvo
               for p in _pontos(f["geometry"])]
        if pts:
            centro, zoom = _enquadrar([p[0] for p in pts], [p[1] for p in pts])
    fig.update_layout(map=dict(style="white-bg", center=centro, zoom=zoom), margin=dict(l=0, r=0, t=10, b=0),
                      height=470)
    return fig


def _merc(lat: float) -> float:
    s = math.sin(math.radians(lat))
    return 0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)   # y de Web Mercator em fração do mundo


def _enquadrar(lons: list[float], lats: list[float]) -> tuple[dict, float]:
    """Centro e zoom para a caixa caber no mapa. No zoom z o mundo mede 512 × 2^z px (MapLibre). Usa a largura útil
    do mapa na tela de 1280 px (coluna de 3/5, menos a escala de cores) e a altura da figura, com folga."""
    largura, altura, folga = 340, 440, 0.85
    y0, y1 = _merc(max(lats)), _merc(min(lats))
    dx, dy = max(max(lons) - min(lons), 0.05) / 360, max(y1 - y0, 0.0002)
    zoom = min(9.0, math.log2(min(largura / (512 * dx), altura / (512 * dy)) * folga))
    ym = (y0 + y1) / 2   # centro no meio da caixa em Mercator (não no meio das latitudes)
    lat_c = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ym))))
    # a escala de cores ocupa a direita: desloca o centro para o destaque ficar na parte livre
    lon_c = (min(lons) + max(lons)) / 2 + (100 / 2) / (512 * 2 ** zoom) * 360
    return {"lat": lat_c, "lon": lon_c}, zoom


def _pontos(geom: dict):
    coords = geom["coordinates"]
    polys = coords if geom["type"] == "MultiPolygon" else [coords]
    for poly in polys:
        yield from poly[0]


LEGENDA = (f"**Legenda:** azul = valor da área (a cor representa o **total** da área; áreas agregadas somam vários "
           f"municípios; a cor satura no percentil 95 e o topo da escala diz “≥”). **Cinza** = sem dado publicável "
           f"neste recorte (menos de {LIMIAR} serventias ou complemento pequeno demais; LGPD). **Claro com contorno "
           f"escuro** = município sem serventia no cadastro do CNJ (ver Limitações).")
if tudo_zero:
    st.info(f"Nesta visão, “{METRICAS[metrica]}” é zero em todas as áreas: nada a mapear ou ranquear. "
            "Escolha outra métrica.")
elif mun is not None and foco is not None:
    # U1: destaque com contexto e zoom na região intermediária do município
    ids_int = municipios.loc[municipios["regiao_intermediaria"] == mun["regiao_intermediaria"], "area_id"].unique()
    ver_tudo = st.toggle("Ver MG inteiro", value=False)
    c_mapa, c_info = st.columns([3, 2])
    with c_mapa:
        st.plotly_chart(mapa(foco["area_id"], None if ver_tudo else list(ids_int)), width="stretch")
        st.caption(md_seguro(LEGENDA))
    with c_info:
        if visao is None and foco["tipo"] == "municipio":
            rk = tab("SELECT * FROM gold.ranking_municipio_publico WHERE cod_ibge = ?", (int(mun["cod_ibge"]),))
            r = rk.set_index("metrica")
            x = r.loc[metrica]
            st.markdown(md_seguro(f"**{mun_nome}:** {fmt(metrica, x['valor'])} de {METRICAS[metrica].lower()} — "
                                  f"{pct(x['pct_mg'])} de MG; {int(x['posicao'])}º de {int(x['n_municipios'])} "
                                  "municípios."))
            # C3: nomes curtos e posição compacta, para "Posição" caber na coluna estreita em 1280 px
            st.dataframe(pd.DataFrame([{"Métrica": TITULO_ESCALA[m], "Valor": fmt(m, r.loc[m, "valor"]),
                                        "% de MG": pct(r.loc[m, "pct_mg"]),
                                        "Posição": f"{int(r.loc[m, 'posicao'])}º/{int(r.loc[m, 'n_municipios'])}"}
                                       for m in METRICAS]), hide_index=True, width="stretch", column_config={
                "Posição": st.column_config.TextColumn(
                    help=f"Posição entre os {int(x['n_municipios'])} municípios com dado publicável")})
        else:
            st.markdown(md_seguro(f"**{foco['area_nome']}:** {fmt(metrica, foco[metrica])} de "
                                  f"{METRICAS[metrica].lower()}."))
            st.caption("Posição no ranking estadual só para municípios com 3 ou mais serventias, sem filtro.")
else:
    c_mapa, c_rank = st.columns([3, 2])
    with c_mapa:
        st.plotly_chart(mapa(), width="stretch")
        st.caption(md_seguro(LEGENDA))
    with c_rank:
        top = dados.nlargest(15, metrica)
        top = top[top[metrica] > 0].sort_values(metrica)
        if len(top) <= 1:
            st.info("Ranking com uma área ou menos: nada a comparar neste recorte.")
        else:
            fig2 = go.Figure(go.Bar(
                x=top[metrica], y=top["rotulo"], orientation="h", text=top["valor_txt"], textposition="outside",
                cliponaxis=False, constraintext="none", marker_color=AZUL_SERIE,
                customdata=top[["area_nome", "pct_txt"]].to_numpy(),
                hovertemplate="<b>%{customdata[0]}</b><br>%{text}<br>%{customdata[1]} de MG<extra></extra>"))
            # C1: eixo até 1,18 × o maior valor e margem direita para o rótulo da maior barra não ser cortado
            fig2.update_layout(margin=dict(l=0, r=90, t=30, b=0), height=470,
                               title=f"15 maiores — {METRICAS[metrica]}" + (" (por região)" if visao else ""),
                               xaxis=dict(range=[0, float(top[metrica].max()) * 1.18], showgrid=False,
                                          showticklabels=False, title=""))
            st.plotly_chart(fig2, width="stretch")

titulo_tab = "Tabela por região (recorte com agregação LGPD)" if visao else "Tabela por área (com agregação LGPD)"
with st.expander(titulo_tab):
    t = (v_area if visao else dados).sort_values("valor_descoberto", ascending=False)
    # C3: sem a coluna "Tipo" (o prefixo RI / Int. no nome já diz o tipo), para "Déficit" caber em 1280 px
    linhas = [{"Área": curto(a), "Serventias": num(s), "CLT": num(c),
               "Passivo (todas)": brl(p), "Com déficit": aprox(nd), "Déficit": brl(d)}
              for a, s, c, p, nd, d in zip(t["area_nome"], t["n_serventias"], t["clt"], t["passivo"], t["n_deficit"],
                                           t["valor_descoberto"])]
    if visao:
        u = v_uf.loc[(REGRA_BASE, "base")]
        falta = int(u["n_serventias_ativas"] - t["n_serventias"].sum())
        if falta:
            linhas.append({"Área": "Não publicável (LGPD)", "Serventias": "—", "CLT": "—",
                           "Passivo (todas)": "—", "Com déficit": "—", "Déficit": "—"})
        linhas.append({"Área": "Total de MG no recorte", "Serventias": num(u["n_serventias_ativas"]),
                       "CLT": num(u["clt"]), "Passivo (todas)": brl(u["passivo_todas"]),
                       "Com déficit": aprox(u["n_deficit"]), "Déficit": brl(u["valor_descoberto"])})
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch", column_config={
        "Área": st.column_config.TextColumn(width="medium", help="Sem prefixo = município; RI = região imediata; "
                                            "Int. = grupo da região intermediária (N RI somadas) ou N municípios "
                                            "pequenos somados. Nome "
                                            "completo ao passar o mouse no mapa e no ranking."),
        "Passivo (todas)": st.column_config.TextColumn(help="Passivo de todas as ativas"),
        "Com déficit": st.column_config.TextColumn(help="Valor esperado")})
rodape(["cnj_serventias", "cnj_colaboradores", "rais_vinculos", "ibge_malha"])
