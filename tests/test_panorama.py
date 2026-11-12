"""Panorama do Início (V5, D-082; bloco "painel de MG rumo ao V5", item 3): os 6 indicadores com uma linha de
contexto (src/painel/analises.panorama). Roda no modo demonstração (conjunto público versionado)."""
import duckdb
import pytest

from apoio_painel import HISTORIA, RAIZ

pytestmark = pytest.mark.usefixtures("painel_demo")
INICIO = HISTORIA[0]
ROTULOS = ["Cartórios ativos", "Arrecadação anual", "Obrigados à garantia", "Empregados CLT", "Déficit de cobertura",
           "Prêmio anual estimado"]


@pytest.fixture
def con(painel_demo):
    with duckdb.connect(str(painel_demo["banco"]), read_only=True) as c:
        yield c


def test_seis_indicadores_batem_com_os_numeros_oficiais(con):
    from src.painel import analises
    r = analises.panorama(con, "MG")
    assert [k["rotulo"] for k in r["kpis"]] == ROTULOS
    assert all(k["valor"] and k["nota"] for k in r["kpis"])
    of = {x["chave"]: x["valor"] for x in analises.numeros_oficiais(con, "MG")["numeros"]}
    k = {x["chave"]: x["valor"] for x in r["kpis"]}
    assert k["serventias"] == of["serventias"] and k["clt"] == of["clt"] and k["obrigadas"] == of["obrigadas"]
    assert k["deficit"] == of["deficit"] and k["premio"] == of["premio"]
    faixa = analises.faixa_d042(con, "MG", medida="premio")["faixa_provavel"]
    assert r["kpis"][-1]["nota"] == f"provavelmente de {faixa}"


def test_arrecadacao_anual_aproximada_e_explicada(con):
    from src.painel import analises
    r = analises.panorama(con, "MG")
    soma = con.execute("SELECT sum(receita_ref) FROM gold.serventia_publico WHERE uf = 'MG'").fetchone()[0]
    assert r["valores"]["arrecadacao"] == pytest.approx(2 * soma)
    assert r["kpis"][1]["valor"].startswith("≈ R$ ")                    # aproximada, e o painel diz
    um = con.execute("SELECT count(*) FROM gold.serventia_publico WHERE semestres_validos = 1 AND uf = 'MG'"
                     ).fetchone()[0]
    assert r["valores"]["cartorios_um_semestre"] == um and str(um) in r["observacao"]
    assert "receita de referência" in r["conta"]


def test_chat_alcanca_o_panorama():
    from src.agent import ferramentas
    assert "panorama" in ferramentas.CONSULTAS["consultar_numeros"]


def test_inicio_mostra_os_seis_indicadores():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / INICIO), default_timeout=120).run()
    assert not at.exception
    tela = "\n".join(m.value for m in at.markdown)
    assert tela.count('<div class="rd-card">') == 6
    posicoes = [tela.find(f'<div class="rd-rot">{r}') for r in ROTULOS]
    assert all(p >= 0 for p in posicoes) and posicoes == sorted(posicoes)
