"""O Sudeste (D-088): a região somada, o escopo do painel, o mapa do Brasil e o chat por UF.

Roda no modo demonstração (o conjunto público versionado) e sem a API: com o conjunto de uma UF só, a região tem de
ser a própria UF; com o do Sudeste (RADAR_PUBLICO_TESTE), as quatro.
"""
import sys

import duckdb
import pytest

from apoio_painel import RAIZ
from src.agent import chat, ferramentas
from src.painel import analises
from src.painel.mapa import dados_mapa


@pytest.fixture(scope="module")
def con(painel_demo):
    with duckdb.connect(str(painel_demo["banco"]), read_only=True) as c:
        yield c


def test_regiao_soma_as_ufs_e_a_faixa_vem_da_simulacao_da_regiao(con):
    """Uma UF só: a região é ela (base, faixa e contagens). Mais de uma: soma das bases e a faixa da linha SUDESTE de
    gold.analise_monte_carlo (sorteio a sorteio), nunca a soma das faixas."""
    r = analises.regiao(con)
    ufs = r["estados"]
    soma = sum(analises.numeros_oficiais(con, u)["valores"]["premio"] for u in ufs)
    assert r["valores"]["premio"] == pytest.approx(soma)
    if len(ufs) == 1:
        f = analises.faixa_d042(con, ufs[0], "premio")["valores"]
        assert (r["valores"]["p05"], r["valores"]["p95"]) == (f["p05"], f["p95"])
    else:
        p05, p95 = con.execute("SELECT p05, p95 FROM gold.analise_monte_carlo WHERE uf = 'SUDESTE' AND medida = "
                               "'premio' AND variante = 'independentes'").fetchone()
        assert (r["valores"]["p05"], r["valores"]["p95"]) == (p05, p95)
    assert len(r["kpis"]) == 6 and {x["uf"] for x in r["tabela"]} == set(ufs)
    assert all(x["selo"] == ("calibrado" if x["uf"] == "MG" else "estimativa preliminar") for x in r["tabela"])
    assert "regiao" in analises.PARA_O_CHAT and "regiao" in ferramentas.alcancaveis()


def test_preposicao_do_escopo():
    sys.path.insert(0, str(RAIZ / "app"))
    import comum
    assert comum.do_escopo("SUDESTE") == "no Sudeste"
    assert comum.do_escopo("MG") == "em Minas Gerais" and comum.do_escopo("SP") == "em São Paulo"
    assert comum.do_escopo("RJ") == "no Rio de Janeiro" and comum.do_escopo("ES") == "no Espírito Santo"


def test_estados_preliminares_e_uf_fora_do_estudo():
    assert not ferramentas.preliminar("MG") and all(ferramentas.preliminar(u) for u in ("SP", "RJ", "ES"))
    erro = ferramentas._sem_uf("BA")["erro"]
    assert "consultar_brasil" in erro and "Não estime" in erro   # a Bahia só tem a contagem (camada 1)


def test_mapa_rotula_todas_as_areas_e_legenda_das_sem_valor():
    quadrado = lambda x: {"type": "Polygon", "coordinates": [[[x, 0], [x + 1, 0], [x + 1, 1], [x, 1], [x, 0]]]}  # noqa
    geo = {u: quadrado(i * 2) for i, u in enumerate(["AA", "BB", "CC"])}
    d = dados_mapa(geo, {"AA": 10.0, "BB": None, "CC": 5.0}, {u: u for u in geo}, {}, rotulos=3, rotular_todas=True,
                   legenda_sem="só o cadastro")
    assert [r["id"] for r in d["rotulos"]] == ["AA", "CC", "BB"] and d["maxRotulos"] == 3
    assert d["legenda"][-1] == {"faixa": "sem", "texto": "só o cadastro"}
    assert next(a for a in d["areas"] if a["id"] == "BB")["faixa"] == "sem"
    padrao = dados_mapa(geo, {"AA": 10.0, "BB": None, "CC": 5.0}, {u: u for u in geo}, {})
    assert "BB" not in [r["id"] for r in padrao["rotulos"]] and padrao["legenda"][-1]["faixa"] != "sem"


def test_contexto_do_chat_leva_a_uf_valida():
    t = chat.texto_contexto("Onde está o mercado", "Campinas", {"Campinas"}, "SP", ("MG", "SP"))
    assert "Campinas (SP; use uf = SP" in t
    assert "(BA" not in chat.texto_contexto(None, "Campinas", {"Campinas"}, "BA", ("MG", "SP"))   # UF fora: some


def test_situacao_nao_informada_particiona_o_total():
    """Ativas sem situação jurídica no cadastro (vazio na fonte, D-088) têm recorte próprio: a situação particiona."""
    import pandas as pd

    from src.transform import visoes
    df = pd.DataFrame({"situacao_juridica": ["PROVIDO", None, "VAGO", "", "SOB INTERVENÇÃO", "CONVERSÃO EM DILIGÊNCIA"]})
    contagem = [int(visoes.mascara(df, "situacao", s).sum()) for s in visoes.SITUACOES]
    assert sum(contagem) == len(df) and contagem[visoes.SITUACOES.index(visoes.NAO_INFORMADA)] == 2
    assert ferramentas._recorte("sem situação") == ("situacao", visoes.NAO_INFORMADA)
    assert ferramentas._recorte("não informada") == ("situacao", visoes.NAO_INFORMADA)


def test_recortes_publicados_somam_o_total_de_cada_uf(con):
    """No conjunto público: por situação e por classe, a soma dos recortes dá o total de cada UF (o mesmo que o
    contrato do gold exige na carga)."""
    tot = dict(con.execute("SELECT uf, n_serventias_ativas FROM gold.fato_mercado_uf WHERE nivel = 'base' AND "
                           "regra_classe = 'v2' AND cenario_stf = 'mantem'").fetchall())
    for filtro in ("situacao", "classe"):
        soma = dict(con.execute("SELECT uf, sum(n_serventias_ativas) FROM gold.mercado_filtro_uf WHERE filtro = ? AND "
                                "nivel = 'base' AND regra_classe = 'v2' GROUP BY uf", [filtro]).fetchall())
        assert soma == tot, filtro
