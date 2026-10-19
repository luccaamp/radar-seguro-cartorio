"""1.2 e D-026: áreas públicas do mapa geral. Municípios e geometrias SINTÉTICOS."""
import json

import pandas as pd

from src.transform.geo import areas_do_mapa, geometria_publica


def _municipios():
    return pd.DataFrame({
        "cod_ibge": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "nome": ["Grande", "Mini A", "Mini B", "Vazio", "Outra Grande", "Só Um", "Mini C", "Mini D", "Ilhada"],
        "regiao_imediata": ["R1", "R1", "R1", "R1", "R2", "R2", "R3", "R3", "R9"],
        "regiao_intermediaria": ["I1", "I1", "I1", "I1", "I1", "I1", "I1", "I1", "I9"],
        "n_serventias": [10, 2, 1, 0, 8, 1, 2, 2, 1]})


def _sem_ilhada():
    return _municipios().iloc[:8]


def test_pequenos_viram_uma_area_por_regiao_e_vazio_fica_fora():
    sem_so_um = _sem_ilhada().query("nome != 'Só Um'")         # sem grupo que precise subir
    a = areas_do_mapa(sem_so_um, 3).set_index("cod_ibge")
    assert 4 not in a.index                                   # sem serventia: fora da geometria
    assert a.at[1, "tipo"] == "municipio" and a.at[1, "area_id"] == "1"
    assert a.at[2, "area_id"] == a.at[3, "area_id"] == "RI-R1"  # 2 + 1 = 3 serventias: grupo da região imediata
    assert a.at[2, "area_nome"].startswith("Região imediata de R1 — 2 municípios")


def test_grupo_abaixo_do_limiar_sobe_para_a_intermediaria_sem_nomear_municipio():
    a = areas_do_mapa(_sem_ilhada(), 3).set_index("cod_ibge")
    # R2: só "Só Um" (1). Sobe para a intermediária I1 e soma-se ao MENOR grupo que passa (R1 = 3, R3 = 4): R1
    assert a.at[6, "area_id"] == a.at[2, "area_id"] == a.at[3, "area_id"] == "RINT-I1"
    assert a.at[6, "area_nome"].startswith("Região intermediária de I1 — 3 municípios")
    assert a.at[5, "area_id"] == "5" and a.at[5, "area_nome"] == "Outra Grande"   # município grande intacto
    assert a.at[7, "area_id"] == "RI-R3"
    assert not any(n in nome for nome in a["area_nome"] if nome.startswith("Região") for n in ("Grande", "Só Um"))


def test_ultimo_caso_junta_a_municipio_com_rotulo_mais_n():
    m = pd.DataFrame({"cod_ibge": [1, 2], "nome": ["Sede", "Ilhada"], "regiao_imediata": ["R", "R"],
                      "regiao_intermediaria": ["I", "I"], "n_serventias": [5, 1]})
    a = areas_do_mapa(m, 3).set_index("cod_ibge")
    assert a.at[1, "area_id"] == a.at[2, "area_id"]
    assert a.at[1, "area_nome"] == "Município Sede + 1 municípios pequenos"


def _quadrado(x, cod):
    return {"type": "Feature", "properties": {"codarea": str(cod)},
            "geometry": {"type": "Polygon", "coordinates": [[[x, 0], [x + 1, 0], [x + 1, 1], [x, 1], [x, 0]]]}}


def test_geometria_dissolvida_e_contagem_por_area():
    m = _sem_ilhada()
    areas = areas_do_mapa(m, 3)
    malha = {"type": "FeatureCollection", "features": [_quadrado(i, c) for i, c in enumerate(m["cod_ibge"])]}
    g = geometria_publica(malha, areas, m.set_index("cod_ibge")["n_serventias"]).set_index("area_id")
    assert set(g.index) == {"1", "RINT-I1", "5", "RI-R3"}
    assert (g["n_serventias"] >= 3).all()                     # nenhuma área pública abaixo do limiar
    assert g.at["RINT-I1", "n_municipios"] == 3 and g.at["RINT-I1", "n_serventias"] == 4
    assert json.loads(g.at["RI-R3", "geometria"])["type"] == "Polygon"   # quadrados vizinhos viram um polígono só
