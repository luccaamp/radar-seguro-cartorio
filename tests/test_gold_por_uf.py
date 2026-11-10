"""Fase 3, bloco 2 (D-081): o motor do gold roda por UF. Dados SINTÉTICOS (UFs 'AA' e 'BB' inventadas)."""
import pandas as pd

from src import estados_config
from src.motor import Insumos
from src.transform.gold import _com_uf, insumos_da_uf


def _insumos() -> Insumos:
    serv = pd.DataFrame({"cns": ["1", "2", "3"], "uf": ["AA", "BB", "AA"], "cod_ibge": [1100001, 2200001, 1100002]})
    rais = pd.DataFrame({"id_vinculo": [1, 2, 3, 4], "cod_ibge": [1100001, 2200001, 2200001, 1100002],
                         "uf": ["AA", "BB", "BB", "AA"]})
    return Insumos(rais=rais, serventias=serv, fator_inpc=1.1, mes_inpc=202601, regioes={1100001: "r1"})


def test_insumos_da_uf_separa_serventias_e_rais():
    a = insumos_da_uf(_insumos(), "AA")
    assert a.serventias["cns"].tolist() == ["1", "3"]
    assert a.rais["id_vinculo"].tolist() == [1, 4]   # a "UF inteira" da reserva salarial é só a AA (D-022)
    assert (a.fator_inpc, a.mes_inpc, a.regioes) == (1.1, 202601, {1100001: "r1"})
    assert insumos_da_uf(_insumos(), "BB").rais["id_vinculo"].tolist() == [2, 3]


def test_coluna_uf_na_frente_sem_mudar_o_resto():
    df = pd.DataFrame({"cod_ibge": [1, 2], "valor": [3.0, 4.0]})
    assert _com_uf(df, "AA").columns.tolist() == ["uf", "cod_ibge", "valor"]
    assert _com_uf(df, "AA")["uf"].tolist() == ["AA", "AA"]
    ja_tem = pd.DataFrame({"cns": ["1"], "uf": ["XX"], "v": [1]})
    assert _com_uf(ja_tem, "AA").to_dict("records") == [{"uf": "AA", "cns": "1", "v": 1}]


def test_premissas_de_mg_sao_as_vigentes_e_as_de_outra_uf_herdadas(monkeypatch):
    semente = {"premissas": {}}
    assert estados_config.premissas_da_uf("MG", semente) == (semente, False)
    monkeypatch.setattr(estados_config, "estado", lambda uf: {"nome": "sintética"})
    assert estados_config.premissas_da_uf("ZZ", semente) == (semente, True)
