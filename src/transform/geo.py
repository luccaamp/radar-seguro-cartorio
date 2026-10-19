"""Geometria pública do mapa (1.2): municípios com pelo menos `limiar` serventias ficam como estão; os menores de cada
região imediata do IBGE viram UM polígono dissolvido. Nenhuma feição pública tem menos de `limiar` serventias.

Regras (D-026, hierarquia do IBGE, como na D-022):
- município sem serventia no cadastro fica fora da geometria (estado próprio no mapa, com legenda);
- municípios pequenos de cada região imediata formam um grupo;
- grupo com menos de `limiar` sobe para os pequenos da região INTERMEDIÁRIA: soma-se aos outros grupos que falharam na
  mesma intermediária e, se ainda faltar, ao menor grupo de pequenos de outra região imediata da mesma intermediária;
- só em último caso (intermediária sem nenhum grupo de pequenos que passe) junta-se a um município, com o rótulo
  "Município X + N municípios pequenos" — nunca com o nome do município sozinho.
"""
import json

import geopandas as gpd
import pandas as pd


def _rotulo_grupo(nivel: str, regiao: str, n_mun: int, limiar: int) -> str:
    return f"Região {nivel} de {regiao} — {n_mun} municípios com menos de {limiar} serventias, somados"


def areas_do_mapa(municipios: pd.DataFrame, limiar: int) -> pd.DataFrame:
    """`municipios`: cod_ibge, nome, regiao_imediata, regiao_intermediaria, n_serventias.
    Devolve cod_ibge -> area_id, area_nome, tipo. Função pura (sem geometria)."""
    m = municipios[municipios["n_serventias"] > 0].copy()
    m["area_id"] = m["cod_ibge"].astype(int).astype(str)
    m["area_nome"] = m["nome"]
    m["tipo"] = "municipio"
    peq = m["n_serventias"] < limiar
    grupos = m[peq].groupby("regiao_imediata")["n_serventias"].sum()
    passam = set(grupos[grupos >= limiar].index)
    for reg in passam:                                   # 1) grupo da região imediata
        idx = m.index[peq & (m["regiao_imediata"] == reg)]
        m.loc[idx, ["area_id", "tipo"]] = [f"RI-{reg}", "regiao_agregada"]
        m.loc[idx, "area_nome"] = _rotulo_grupo("imediata", reg, len(idx), limiar)
    falham = m[peq & ~m["regiao_imediata"].isin(passam)]
    for rint, g in falham.groupby("regiao_intermediaria"):   # 2) pequenos da região intermediária
        idx = list(g.index)
        if m.loc[idx, "n_serventias"].sum() < limiar:
            # soma-se ao menor grupo de pequenos que passa, de outra região imediata da mesma intermediária
            vizinhos = m[peq & m["regiao_imediata"].isin(passam) & (m["regiao_intermediaria"] == rint)]
            if not vizinhos.empty:
                alvo = vizinhos.groupby("regiao_imediata")["n_serventias"].sum().idxmin()
                idx += list(vizinhos.index[vizinhos["regiao_imediata"] == alvo])
        if m.loc[idx, "n_serventias"].sum() >= limiar:
            m.loc[idx, ["area_id", "tipo"]] = [f"RINT-{rint}", "regiao_agregada"]
            m.loc[idx, "area_nome"] = _rotulo_grupo("intermediária", rint, len(idx), limiar)
            continue
        # 3) último caso: junta ao menor município grande da intermediária, com o nome dele + os pequenos
        grandes = m[~peq & (m["regiao_intermediaria"] == rint)]
        if grandes.empty:
            raise ValueError(f"intermediária {rint} sem área com {limiar} serventias")
        mun = grandes["n_serventias"].idxmin()
        nome = f"Município {m.at[mun, 'nome']} + {len(idx)} municípios pequenos"
        m.loc[idx + [mun], ["area_id", "tipo", "area_nome"]] = [f"MUN+-{m.at[mun, 'cod_ibge']}", "regiao_agregada", nome]
    return m[["cod_ibge", "area_id", "area_nome", "tipo"]].reset_index(drop=True)


def dissolver(malha: dict, grupo_por_municipio: dict[int, str]) -> pd.DataFrame:
    """Dissolve a malha municipal por um agrupamento qualquer (cod_ibge -> id do grupo). Uma linha por grupo:
    area_id, geometria (GeoJSON em texto). Municípios fora do dicionário ficam de fora."""
    gdf = gpd.GeoDataFrame.from_features(malha["features"])
    gdf["area_id"] = gdf["codarea"].astype(int).map(grupo_por_municipio)
    dis = gdf.dropna(subset=["area_id"]).dissolve(by="area_id").reset_index()
    return pd.DataFrame({"area_id": dis["area_id"], "geometria": [json.dumps(g.__geo_interface__) for g in dis.geometry]})


def geometria_publica(malha: dict, areas: pd.DataFrame, n_serventias: pd.Series) -> pd.DataFrame:
    """Dissolve a malha municipal (GeoJSON do IBGE, propriedade `codarea`) pelas áreas. Uma linha por área, com a
    geometria em GeoJSON (texto), o número de municípios e o de serventias da área."""
    gdf = gpd.GeoDataFrame.from_features(malha["features"])
    gdf["cod_ibge"] = gdf["codarea"].astype(int)
    gdf = gdf.merge(areas, on="cod_ibge", how="inner")
    gdf["n_serventias"] = gdf["cod_ibge"].map(n_serventias).fillna(0)
    dis = gdf.dissolve(by="area_id", aggfunc={"area_nome": "first", "tipo": "first", "n_serventias": "sum",
                                              "cod_ibge": "count"}).reset_index()
    dis = dis.rename(columns={"cod_ibge": "n_municipios"})
    dis["geometria"] = [json.dumps(g.__geo_interface__) for g in dis.geometry]
    return pd.DataFrame(dis[["area_id", "area_nome", "tipo", "n_municipios", "n_serventias", "geometria"]])
