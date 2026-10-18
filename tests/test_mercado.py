"""Testes de premissas, déficit, demanda, receita e cenários. Dados SINTÉTICOS."""
import copy

import pandas as pd
import pytest

from src.model.cenario import aplicar_cenario_stf
from src.model.mercado import deficit, demanda_seguro, receita
from src.model.premissas import PremissaInvalida, resolver, validar, validar_escolha_garantia


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
    assert resolver(semente, "max")["prob_deficit"]["classe_3"] == 0.50
    assert resolver(semente, "base", {"taxa_seguro_anual": 0.03})["taxa_seguro_anual"] == 0.03


def _serv():
    return pd.DataFrame({"passivo": [100_000.0, 200_000.0, 50_000.0], "classe": ["2", "3", "indeterminada"],
                         "peso_universo": [1.0, 1.0, 0.0]})


def test_deficit_por_faixa(p_base):
    d = deficit(_serv(), p_base)
    assert d["n_deficit"].tolist() == pytest.approx([0.50, 0.30, 0.0])
    assert d["valor_descoberto"].tolist() == pytest.approx([0.5 * 0.5 * 100_000, 0.3 * 0.4 * 200_000, 0.0])


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
