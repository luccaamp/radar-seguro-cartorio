"""Mapa em % (V5, D-082, o mapa da aba Classes; bloco "painel de MG rumo ao V5", item 5): parte dos cartórios de cada
município obrigada pelo Prov. 227 ou na Classe 3 (src/painel/analises.percentual_por_municipio), na página "Onde está
o mercado" com o seletor "Mostrar no mapa". Modo demonstração; uma parte com faixas SINTÉTICAS."""
import duckdb
import pytest

from apoio_painel import MERCADO, RAIZ, mapa_componente
from src.painel import mapa as m


@pytest.fixture
def con(painel_demo):
    with duckdb.connect(str(painel_demo["banco"]), read_only=True) as c:
        yield c


@pytest.mark.parametrize("indicador, coluna", [("obrigados", "sum(peso_universo)"),
                                               ("classe_3", "count(*) FILTER (WHERE classe = '3')")])
def test_percentual_por_municipio_confere_com_a_tabela(con, indicador, coluna):
    from src.painel import analises
    r = analises.percentual_por_municipio(con, "MG", indicador)
    n_areas = con.execute("SELECT count(*) FROM gold.geo_area_municipio WHERE uf = 'MG'").fetchone()[0]
    assert len(r["valores"]) == r["areas"] == n_areas
    assert all(0 <= v <= 1 for v in r["valores"].values())
    bh = con.execute(f"SELECT {coluna} / count(*) FROM gold.serventia_publico WHERE municipio = 'Belo Horizonte'"
                     ).fetchone()[0]
    assert r["valores"]["3106200"] == pytest.approx(bh)
    total = con.execute(f"SELECT {coluna} / count(*) FROM gold.serventia_publico WHERE uf = 'MG'").fetchone()[0]
    assert r["estado"] == f"{100 * total:.1f}%".replace(".", ",")
    assert r["zeros"] == sum(v <= 0 for v in r["valores"].values())
    assert len(r["maiores_com_5_ou_mais"]) == 3 and r["citar"].startswith("Fonte:")


def test_obrigados_bate_com_o_numero_oficial(con):
    """44% dos ativos: a mesma conta do Panorama (≈ 1.121 de 2.525)."""
    from src.painel import analises
    r = analises.percentual_por_municipio(con, "MG", "obrigados")
    of = analises.numeros_oficiais(con, "MG")["valores"]
    assert r["estado"] == f"{100 * of['obrigadas'] / of['serventias']:.1f}%".replace(".", ",")


def test_indicador_invalido_e_outra_uf(con):
    from src.painel import analises
    assert "erro" in analises.percentual_por_municipio(con, "MG", "classe_9")
    assert analises.percentual_por_municipio(con, "BA").get("erro")   # fora do estudo completo (D-088)


def test_chat_alcanca_o_mapa_em_percentual():
    from src.agent import ferramentas
    assert "percentual_por_municipio" in ferramentas.CONSULTAS["consultar_mercado"]
    esquema = next(e for e in ferramentas.ESQUEMAS if e["name"] == "consultar_mercado")
    assert esquema["parameters"]["properties"]["indicador"]["enum"] == ["obrigados", "classe_3"]


def test_faixas_com_teto_fixo_nao_tem_mais_de_100():
    cor, leg = m.faixas({"a": 0.0, "b": 0.1, "c": 0.2, "d": 0.21, "e": 0.99, "f": 1.0}, fmt=m.pct_curto, teto_fixo=1.0)
    assert cor == {"a": "zero", "b": "1", "c": "1", "d": "2", "e": "5", "f": "5"}
    assert [x["texto"] for x in leg] == ["Zero", "até 20%", "até 40%", "até 60%", "até 80%", "até 100%"]
    assert not any("mais de" in x["texto"] for x in leg)


def test_pagina_troca_o_mapa_pelo_seletor(painel_demo):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / MERCADO), default_timeout=120)
    at.session_state["f_indicador"] = "% obrigados"
    at.session_state["escopo"] = "MG"   # o recorte de MG (o padrão é o Sudeste, D-088)
    at.run()
    assert not at.exception
    d = mapa_componente(at)
    assert d["tituloLegenda"].startswith("Cartórios obrigados pelo Prov. 227")
    assert d["legenda"][-1]["texto"] == "até 100%" and d["rotulos"] == []
    assert d["resumo"].startswith("44,4% dos cartórios de MG são obrigados")
    at.session_state["f_indicador"] = "Déficit (R$)"
    at.run()
    assert mapa_componente(at)["tituloLegenda"] == "Déficit de cobertura do município"
