"""Testes de premissas, déficit, demanda, receita e cenários. Dados SINTÉTICOS."""
import copy

import pandas as pd
import pytest

from src.model.cenario import aplicar_cenario_stf
from src.model.mercado import deficit, demanda_seguro, receita
from src.model.premissas import PremissaInvalida, com_novo_base, resolver, validar, validar_escolha_garantia


def test_semente_valida(semente):
    validar(semente)


def test_escolha_garantia_precisa_somar_1(semente):
    validar_escolha_garantia({"bens_proprios": 0.3, "fianca": 0.2, "seguro": 0.5})
    with pytest.raises(PremissaInvalida):
        validar_escolha_garantia({"bens_proprios": 0.3, "fianca": 0.2, "seguro": 0.6})
    ruim = copy.deepcopy(semente)
    ruim["premissas"]["escolha_garantia"]["valores"]["base"]["seguro"] = 0.9
    with pytest.raises(PremissaInvalida):
        validar(ruim)


def test_resolver_niveis(semente):
    assert resolver(semente, "min")["fap"] == 0.5
    assert resolver(semente, "max")["prob_deficit"]["classe_3"] == \
        semente["premissas"]["prob_deficit"]["valores"]["classe_3"]["max"]
    assert resolver(semente, "base", {"taxa_seguro_anual": 0.03})["taxa_seguro_anual"] == 0.03


def test_nova_versao_muda_so_o_base(semente):
    novo, diff = com_novo_base(semente, {"taxa_seguro_anual": 0.025, "prob_deficit": {"classe_2": 0.6},
                                         "fap": 1.0, "fracao_exigencia_garantia": 0.5})
    assert novo["premissas"]["taxa_seguro_anual"]["valores"] == {"min": 0.010, "base": 0.025, "max": 0.035}
    assert novo["premissas"]["prob_deficit"]["valores"]["classe_2"]["base"] == 0.6
    assert novo["premissas"]["prob_deficit"]["valores"]["classe_3"]["base"] == \
        semente["premissas"]["prob_deficit"]["valores"]["classe_3"]["base"]   # a faixa não ajustada fica como estava
    assert set(diff) == {"taxa_seguro_anual", "prob_deficit"}   # fap não mudou; fração do cenário não é premissa
    assert semente["premissas"]["taxa_seguro_anual"]["valores"]["base"] == 0.020   # semente intacta


def test_nova_versao_ignora_ruido_de_ponto_flutuante(semente):
    _, diff = com_novo_base(semente, {"market_share_hipotetico": 5.2 / 100, "sinistralidade": 10.9 / 100})
    assert diff == {}


def _serv():
    return pd.DataFrame({"passivo": [100_000.0, 200_000.0, 50_000.0], "classe": ["2", "3", "indeterminada"],
                         "peso_universo": [1.0, 1.0, 0.0]})


def test_deficit_por_faixa(p_base):
    d = deficit(_serv(), p_base)
    pr, pc = p_base["prob_deficit"], p_base["pct_descoberto"]
    assert d["n_deficit"].tolist() == pytest.approx([pr["classe_2"], pr["classe_3"], 0.0])
    assert d["valor_descoberto"].tolist() == pytest.approx([pr["classe_2"] * pc["classe_2"] * 100_000,
                                                            pr["classe_3"] * pc["classe_3"] * 200_000, 0.0])


def test_passivo_zero_nao_conta_como_deficit(p_base):
    """D-021: serventia do universo sem empregado CLT (passivo 0) não entra em 'com déficit'."""
    s = pd.DataFrame({"passivo": [0.0, 100_000.0], "classe": ["2", "2"], "peso_universo": [1.0, 1.0]})
    d = deficit(s, p_base)
    pr, pc = p_base["prob_deficit"]["classe_2"], p_base["pct_descoberto"]["classe_2"]
    assert d["n_deficit"].tolist() == pytest.approx([0.0, pr])
    assert d["valor_descoberto"].tolist() == pytest.approx([0.0, pr * pc * 100_000])


def test_cenario_suspende_8_17_zera_demanda(p_base, cenarios):
    p = aplicar_cenario_stf(p_base, cenarios, "suspende_8_17")
    assert demanda_seguro(1_000_000.0, p).importancia_segurada == 0
    assert demanda_seguro(1_000_000.0, aplicar_cenario_stf(p_base, cenarios, "mantem")).importancia_segurada == \
        pytest.approx(500_000.0)


def test_cenario_parcial_fica_entre(p_base, cenarios):
    p = aplicar_cenario_stf(p_base, cenarios, "parcial", {"fracao_exigencia_garantia": 0.3})
    assert demanda_seguro(1_000_000.0, p).importancia_segurada == pytest.approx(150_000.0)
    with pytest.raises(ValueError):
        aplicar_cenario_stf(p_base, cenarios, "parcial", {"fracao_exigencia_garantia": 1.5})


def test_premio_monotonico_na_taxa(p_base):
    dem = demanda_seguro(1_000_000.0, p_base)
    premios = [receita(dem, {**p_base, "taxa_seguro_anual": t})["mercado"].premio_emitido for t in (0.01, 0.02, 0.035)]
    assert premios == sorted(premios) and premios[0] < premios[-1]


@pytest.mark.parametrize("nivel", ["p_min", "p_base", "p_max"])
def test_mercado_maior_ou_igual_a_seguradora(nivel, request):
    p = request.getfixturevalue(nivel)
    r = receita(demanda_seguro(1_000_000.0, p), p)
    for campo in ("importancia_segurada", "premio_emitido", "sinistro_esperado"):
        assert getattr(r["mercado"], campo) >= getattr(r["seguradora"], campo)


def test_resultado_tecnico(p_base):
    r = receita(demanda_seguro(1_000_000.0, p_base), p_base)["mercado"]
    assert r.premio_emitido == pytest.approx(500_000 * 0.02)
    assert r.resultado_tecnico == pytest.approx(r.premio_emitido * (1 - 0.109 - 0.171 - 0.08))
