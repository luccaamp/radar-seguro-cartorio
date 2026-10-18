"""Mercado: serventias, empregados, passivo e déficit de MG por município, com filtros, mapa e ranking."""
import json

import pandas as pd
import plotly.express as px
import streamlit as st

from comum import (ATRIBUICOES, AZUL_SEQUENCIAL, AZUL_SERIE, RAIZ, SITUACOES, aviso_estimativa, brl, consulta,
                   execucao, md, num, rodape)
from src.model.lgpd import agregar_lgpd

st.set_page_config(page_title="Mercado", page_icon="🗺️", layout="wide")
st.title("Mercado — Minas Gerais")
aviso_estimativa()
LIMIAR = int(execucao().limiar_lgpd)


@st.cache_data
def base() -> pd.DataFrame:
    return consulta("""SELECT i.*, m.nome AS municipio FROM gold.interno_serventia i
                       LEFT JOIN silver.municipio_ibge m USING (cod_ibge)""")


@st.cache_data
def malha() -> dict:
    arq = consulta("SELECT arquivo FROM silver.fonte_metadados WHERE fonte = 'ibge_malha'").iloc[0, 0]
    return json.loads((RAIZ / "data" / "bronze" / arq).read_text(encoding="utf-8"))


@st.cache_data
def razoes() -> pd.DataFrame:
    """IS e prêmio por real de déficit (são lineares no déficit), por nível e regra, no cenário 'mantém'."""
    u = consulta("SELECT * FROM gold.fato_mercado_uf WHERE cenario_stf = 'mantem'")
    u["is_por_deficit"] = u["mercado_importancia_segurada"] / u["valor_descoberto"]
    u["premio_por_deficit"] = u["mercado_premio_emitido"] / u["valor_descoberto"]
    return u.set_index(["nivel", "regra_classe"])


df = base()
# ---- filtros (uma linha acima dos gráficos)
f1, f2, f3, f4, f5 = st.columns([1.2, 2, 2.2, 2.4, 1.6])
regra = f1.radio("Classe 1 até", ["v2", "v1"],
                 format_func=lambda r: {"v2": "R$ 300 mil", "v1": "R$ 100 mil"}[r],
                 help="v2 = Prov. 243 (base); v1 = Prov. 213 original (sensibilidade)")
municipios = sorted(df["municipio"].dropna().unique())
mun = f2.selectbox("Município", ["Todos"] + municipios)
atrib = f3.multiselect("Atribuição", list(ATRIBUICOES), format_func=ATRIBUICOES.get, placeholder="Todas",
                       help="Serventias com pelo menos uma das atribuições escolhidas")
sit = f4.multiselect("Situação", list(SITUACOES), format_func=SITUACOES.get, placeholder="Todas")
classe = f5.multiselect("Classe (Prov. 213)", ["1", "2", "3", "indeterminada"], placeholder="Todas")

sel = df[df["regra_classe"] == regra]
if mun != "Todos":
    sel = sel[sel["municipio"] == mun]
if atrib:
    sel = sel[sel[atrib].any(axis=1)]
if sit:
    sel = sel[sel["situacao_juridica"].isin(sit)]
if classe:
    sel = sel[sel["classe"].isin(classe)]

n_serv = sel[sel["nivel"] == "base"]["cns"].nunique()
if n_serv == 0:
    st.warning("Nenhuma serventia no recorte escolhido.")
    st.stop()


def total(nivel: str, col: str) -> float:
    return float(sel.loc[sel["nivel"] == nivel, col].sum())


r = razoes()
pode_estimar = n_serv >= LIMIAR
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Serventias ativas", num(n_serv))
k2.metric("Empregados CLT declarados", num(total("base", "clt")))
if pode_estimar:
    k3.metric("Passivo estimado", brl(total("base", "passivo")),
              help=f"Faixa {brl(total('min', 'passivo'))} a {brl(total('max', 'passivo'))}. Todas as serventias do recorte.")
    k4.metric("Serventias com déficit (esperado)", num(total("base", "n_deficit")),
              help=f"Faixa {num(total('min', 'n_deficit'))} a {num(total('max', 'n_deficit'))}. Só o universo do Prov. 227.")
    k5.metric("Déficit estimado", brl(total("base", "valor_descoberto")),
              help=f"Faixa {brl(total('min', 'valor_descoberto'))} a {brl(total('max', 'valor_descoberto'))}")
    st.markdown(md(
        f"**Faixas (mínimo — base — máximo).** Passivo: {brl(total('min', 'passivo'))} — **{brl(total('base', 'passivo'))}** — "
        f"{brl(total('max', 'passivo'))}. Universo do Prov. 227: {num(total('min', 'peso_universo'))} — "
        f"**{num(total('base', 'peso_universo'))}** — {num(total('max', 'peso_universo'))} serventias. "
        f"Déficit: {brl(total('min', 'valor_descoberto'))} — **{brl(total('base', 'valor_descoberto'))}** — "
        f"{brl(total('max', 'valor_descoberto'))}. Importância segurada (regra mantida): "
        f"{brl(total('min', 'valor_descoberto') * r.at[('min', regra), 'is_por_deficit'])} — "
        f"**{brl(total('base', 'valor_descoberto') * r.at[('base', regra), 'is_por_deficit'])}** — "
        f"{brl(total('max', 'valor_descoberto') * r.at[('max', regra), 'is_por_deficit'])}. Prêmio anual: "
        f"{brl(total('min', 'valor_descoberto') * r.at[('min', regra), 'premio_por_deficit'])} — "
        f"**{brl(total('base', 'valor_descoberto') * r.at[('base', regra), 'premio_por_deficit'])}** — "
        f"{brl(total('max', 'valor_descoberto') * r.at[('max', regra), 'premio_por_deficit'])}."))
else:
    st.warning(f"O recorte tem menos de {LIMIAR} serventias: as estimativas não são exibidas (LGPD, SPEC §6).")
rodape(["cnj_serventias", "cnj_colaboradores", "cnj_arrecadacao", "rais_vinculos", "ibge_inpc"],
       "Passivo do art. 5º do Prov. 227 (custo de demissão sem justa causa em 31/12/2025, salário corrigido pelo INPC); "
       "déficit = prob. de déficit × parte descoberta (suposições, D-016).")

# ---- por município (agregação LGPD)
METRICAS = {"valor_descoberto": "Déficit estimado (base)", "passivo": "Passivo estimado (base)",
            "n_serventias": "Serventias ativas", "clt": "Empregados CLT"}
b = sel[sel["nivel"] == "base"]
por_mun = (b.groupby(["cod_ibge", "municipio"])
           .agg(n_serventias=("cns", "size"), clt=("clt", "sum"), passivo=("passivo", "sum"),
                n_deficit=("n_deficit", "sum"), valor_descoberto=("valor_descoberto", "sum"))
           .reset_index())
pub = agregar_lgpd(por_mun, LIMIAR)
metrica = st.radio("Métrica do mapa e do ranking", list(METRICAS), format_func=METRICAS.get, horizontal=True)
estimada = metrica in ("valor_descoberto", "passivo")

c_mapa, c_rank = st.columns([3, 2])
with c_mapa:
    mapa = por_mun.copy()
    if estimada:  # municípios agregados ficam sem cor no mapa
        mapa.loc[mapa["n_serventias"] < LIMIAR, metrica] = None
    mapa["codarea"] = mapa["cod_ibge"].astype(int).astype(str)
    mapa["valor_txt"] = [brl(v) if estimada else num(v) for v in mapa[metrica]]
    # choropleth_map (MapLibre) com fundo branco: sem mapa de ruas, funciona offline na demo
    fig = px.choropleth_map(mapa, geojson=malha(), locations="codarea", featureidkey="properties.codarea",
                            color=metrica, color_continuous_scale=AZUL_SEQUENCIAL, hover_name="municipio",
                            hover_data={"codarea": False, metrica: False, "valor_txt": True, "n_serventias": True},
                            labels={"valor_txt": METRICAS[metrica], "n_serventias": "Serventias"},
                            map_style="white-bg", center={"lat": -18.4, "lon": -44.6}, zoom=5.1, opacity=0.95,
                            # BH concentra a escala; a cor satura no percentil 95 para os demais ficarem legíveis
                            range_color=(0, float(mapa[metrica].quantile(0.95))))
    fig.update_traces(marker_line_width=0.3, marker_line_color="#fcfcfb")
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=470,
                      coloraxis_colorbar=dict(title="", thickness=12, len=0.6))
    st.plotly_chart(fig, width="stretch")
    st.caption("A cor satura no percentil 95 (os maiores municípios ficam no tom mais escuro); valores exatos no "
               "ranking, na tabela e ao passar o mouse."
               + (f" Municípios em branco: menos de {LIMIAR} serventias no recorte (estimativa agregada, LGPD)."
                  if estimada else ""))
with c_rank:
    top = pub[~pub["agregado_lgpd"]].nlargest(15, metrica).sort_values(metrica)
    top["valor_txt"] = [brl(v) if estimada else num(v) for v in top[metrica]]
    fig2 = px.bar(top, x=metrica, y="municipio", orientation="h", text="valor_txt",
                  hover_data={"valor_txt": True, metrica: False, "n_serventias": True},
                  labels={"municipio": "", metrica: METRICAS[metrica], "valor_txt": METRICAS[metrica]})
    fig2.update_traces(marker_color=AZUL_SERIE, textposition="outside", cliponaxis=False)
    fig2.update_layout(margin=dict(l=0, r=40, t=30, b=0), height=470, title=f"15 maiores — {METRICAS[metrica]}",
                       xaxis=dict(showgrid=False, showticklabels=False, title=""))
    st.plotly_chart(fig2, width="stretch")

with st.expander("Tabela por município (com agregação LGPD)"):
    t = pub.sort_values(["agregado_lgpd", "valor_descoberto"], ascending=[True, False])
    st.dataframe(t[["municipio", "n_serventias", "clt", "passivo", "n_deficit", "valor_descoberto"]].rename(columns={
        "municipio": "Município", "n_serventias": "Serventias", "clt": "CLT", "passivo": "Passivo (R$, base)",
        "n_deficit": "Com déficit (esperado)", "valor_descoberto": "Déficit (R$, base)"}),
        hide_index=True, width="stretch",
        column_config={c: st.column_config.NumberColumn(format="%.0f") for c in
                       ["Passivo (R$, base)", "Déficit (R$, base)", "Com déficit (esperado)"]})
rodape(["cnj_serventias", "cnj_colaboradores", "rais_vinculos", "ibge_malha"])
