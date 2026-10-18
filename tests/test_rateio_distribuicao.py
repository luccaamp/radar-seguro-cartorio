"""Testes da distribuição (limiar município/estado) e do rateio. Dados SINTÉTICOS."""
import pandas as pd
import pytest

from src.model.distribuicao import fator_correcao_inpc, passivo_medio_por_municipio, preparar_vinculos
from src.model.rateio import METODOS, ratear_passivo


def _rais():
    return pd.DataFrame({
        "cod_ibge": [1, 1, 1, 1, 2],
        "ativo_31_12": [True, True, True, False, True],
        "tipo_vinculo": [15, 65, 10, 15, 25],      # 65 = CLT por prazo determinado (fora, D-009)
        "rem_dezembro": [3000.0, 3000.0, 0.0, 3000.0, 2000.0],  # 0 = sem remuneração (fora, D-015)
        "rem_media": [2900.0, 2900.0, 2500.0, 2900.0, 2000.0],
        "tempo_emprego_meses": [64.0, 10.0, 30.0, 12.0, 5.0]})


def test_preparar_vinculos_filtra_indeterminado_ativo_e_com_salario():
    v = preparar_vinculos(_rais(), "dezembro", 1.10)
    assert list(v["cod_ibge"]) == [1, 2]
    assert v["salario"].tolist() == pytest.approx([3300.0, 2200.0])


def test_fator_inpc():
    idx = pd.DataFrame({"indice": ["INPC", "INPC", "IPCA"], "ano_mes": [202512, 202609, 202609],
                        "numero_indice": [100.0, 103.0, 999.0]})
    assert fator_correcao_inpc(idx, 202512) == (pytest.approx(1.03), 202609)


def test_origem_da_distribuicao_respeita_o_limiar(p_base):
    v = pd.DataFrame({"cod_ibge": [1] * 20 + [2] * 19, "salario": [3000.0] * 20 + [1000.0] * 19,
                      "meses_servico": [64] * 39})
    m = passivo_medio_por_municipio(v, [1, 2, 3], p_base, limiar=20).set_index("cod_ibge")
    assert m.at[1, "origem_distribuicao"] == "municipio"
    assert m.at[2, "origem_distribuicao"] == "estado"
    assert m.at[3, "origem_distribuicao"] == "estado"        # município sem nenhum vínculo na RAIS
    assert m.at[2, "passivo_medio_vinculo"] == pytest.approx(m.at[3, "passivo_medio_vinculo"])
    assert m.at[1, "passivo_medio_vinculo"] > m.at[2, "passivo_medio_vinculo"]


def _serventias():
    return pd.DataFrame({"cns": ["a", "b", "c", "d"], "cod_ibge": [1, 1, 1, 2], "clt": [4, 1, 0, 3],
                         "receita_ref": [900_000.0, 100_000.0, None, 0.0],
                         "atribuicoes": ["Registro de Imóveis", "Notas", "Notas", "Notas"]})


MEDIO = pd.DataFrame({"cod_ibge": [1, 2], "passivo_medio_vinculo": [10_000.0, 8_000.0]})


@pytest.mark.parametrize("metodo", METODOS)
def test_soma_rateada_igual_ao_passivo_do_municipio(metodo):
    r = ratear_passivo(_serventias(), MEDIO, metodo, {"Registro de Imóveis": 3.0, "Notas": 1.0})
    por_mun = r.groupby("cod_ibge")["passivo"].sum()
    assert por_mun[1] == pytest.approx(5 * 10_000)
    assert por_mun[2] == pytest.approx(3 * 8_000)            # município 2 sem arrecadação: cai no uniforme


def test_por_empregados_cnj_usa_clt_da_serventia():
    r = ratear_passivo(_serventias(), MEDIO, "por_empregados_cnj").set_index("cns")
    assert r.at["a", "passivo"] == pytest.approx(40_000)
    assert r.at["c", "passivo"] == 0


def test_metodo_desconhecido():
    with pytest.raises(ValueError):
        ratear_passivo(_serventias(), MEDIO, "chute")
