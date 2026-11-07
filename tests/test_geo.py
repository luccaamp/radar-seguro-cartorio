"""1.2 e D-078: áreas públicas do mapa geral, uma por município com serventia. Municípios e geometrias SINTÉTICOS."""
import json

import pandas as pd

from src.transform.geo import areas_do_mapa, geometria_publica


def _municipios():
    return pd.DataFrame({
        "cod_ibge": [1, 2, 3, 4, 5],
        "nome": ["Grande", "Mini A", "Mini B", "Vazio", "Só Um"],
        "regiao_imediata": ["R1", "R1", "R1", "R1", "R2"],
        "regiao_intermediaria": ["I1", "I1", "I1", "I1", "I1"],
        "n_serventias": [10, 2, 1, 0, 1]})


def test_cada_municipio_com_serventia_e_uma_area_e_o_vazio_fica_fora():
    a = areas_do_mapa(_municipios()).set_index("cod_ibge")
    assert 4 not in a.index                                   # sem serventia: fora da geometria
    assert list(a.index) == [1, 2, 3, 5]                      # os de 1 ou 2 serventias com área própria (D-078)
    assert (a["tipo"] == "municipio").all()
    assert a.at[3, "area_id"] == "3" and a.at[3, "area_nome"] == "Mini B"


def _quadrado(x, cod):
    return {"type": "Feature", "properties": {"codarea": str(cod)},
            "geometry": {"type": "Polygon", "coordinates": [[[x, 0], [x + 1, 0], [x + 1, 1], [x, 1], [x, 0]]]}}


def test_geometria_e_contagem_por_municipio():
    m = _municipios()
    areas = areas_do_mapa(m)
    malha = {"type": "FeatureCollection", "features": [_quadrado(i, c) for i, c in enumerate(m["cod_ibge"])]}
    g = geometria_publica(malha, areas, m.set_index("cod_ibge")["n_serventias"]).set_index("area_id")
    assert set(g.index) == {"1", "2", "3", "5"}
    assert (g["n_municipios"] == 1).all()
    assert g.at["3", "n_serventias"] == 1 and g.at["1", "n_serventias"] == 10
    assert json.loads(g.at["2", "geometria"])["type"] == "Polygon"
