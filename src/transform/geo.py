"""Geometria pública do mapa (1.2): uma área por município com serventia, inclusive os de 1 ou 2 (D-078, D-038 fase 2;
antes, os municípios com menos de 3 serventias eram dissolvidos por região, D-026). Município sem serventia no
cadastro fica fora da geometria (estado próprio no mapa, com legenda, em gold.geo_sem_serventia).
"""
import json

import geopandas as gpd
import pandas as pd


def areas_do_mapa(municipios: pd.DataFrame) -> pd.DataFrame:
    """`municipios`: cod_ibge, nome, n_serventias. Devolve cod_ibge -> area_id (o código IBGE em texto), area_nome
    (o nome do município) e tipo ('municipio'), só dos municípios com serventia. Função pura (sem geometria)."""
    m = municipios[municipios["n_serventias"] > 0].copy()
    m["area_id"] = m["cod_ibge"].astype(int).astype(str)
    m["area_nome"] = m["nome"]
    m["tipo"] = "municipio"
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
