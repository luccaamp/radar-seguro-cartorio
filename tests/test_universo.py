"""Testes de receita de referência, classe e universo. Serventias SINTÉTICAS."""
import pandas as pd
import pytest

from src.model.universo import classificar, fracao_fora_classe_1, receita_referencia, universo


def _semestres():
    linhas = [  # cns, semestre, valor, informado, conflito
        ("dois", 1, 200_000.0, True, False), ("dois", 2, 600_000.0, True, False),
        ("um_zero", 1, 0.0, True, False), ("um_zero", 2, 500_000.0, True, False),
        ("zeros", 1, 0.0, True, False), ("zeros", 2, 0.0, True, False),
        ("conflito", 1, 100.0, True, True), ("conflito", 1, 900_000.0, True, True), ("conflito", 2, 1.0, True, False),
        ("ni", 1, None, False, False), ("ni", 2, None, False, False),
    ]
    df = pd.DataFrame(linhas, columns=["cns", "semestre", "arrecadacao", "informado", "conflito_fonte"])
    return df.assign(ano=2025)


def test_receita_referencia_regras_d010_d013_d014():
    r = receita_referencia(_semestres(), 2025).set_index("cns")
    assert r.at["dois", "receita_ref"] == pytest.approx(400_000)
    assert r.at["um_zero", "receita_ref"] == pytest.approx(500_000)
    assert r.at["um_zero", "origem_receita"] == "um_semestre"
    assert pd.isna(r.at["zeros", "receita_ref"]) and r.at["zeros", "origem_receita"] == "zero_nos_dois_semestres"
    assert pd.isna(r.at["conflito", "receita_ref"]) and r.at["conflito", "origem_receita"] == "conflito_fonte"
    assert pd.isna(r.at["ni", "receita_ref"]) and r.at["ni", "origem_receita"] == "nao_informado"


def test_classificar(regras):
    v2 = regras["versoes"]["v2"]["limites"]
    assert classificar(300_000.0, v2) == "1"
    assert classificar(300_000.01, v2) == "2"
    assert classificar(1_500_000.01, v2) == "3"
    assert classificar(None, v2) == "indeterminada"


def _serv():
    return pd.DataFrame({
        "cns": list("abcdefg"),
        "situacao_juridica": ["PROVIDO", "PROVIDO", "VAGO", "SOB INTERVENÇÃO", "CONVERSÃO EM DILIGÊNCIA", "PROVIDO", "VAGO"],
        "receita_ref": [200_000.0, 2_000_000.0, 5_000_000.0, 800_000.0, 800_000.0, None, None]})


@pytest.mark.parametrize("nivel", ["p_min", "p_base", "p_max"])
def test_universo_nunca_contem_interino(nivel, regras, request):
    p = request.getfixturevalue(nivel)
    u = universo(_serv(), regras["versoes"]["v2"]["limites"], p)
    assert (u.loc[u["situacao_juridica"] == "VAGO", "peso_universo"] == 0).all()


def test_trocar_versao_da_regra_muda_o_universo(regras, p_base):
    u2 = universo(_serv(), regras["versoes"]["v2"]["limites"], p_base).set_index("cns")
    u1 = universo(_serv(), regras["versoes"]["v1"]["limites"], p_base).set_index("cns")
    assert u2.at["a", "peso_universo"] == 0      # R$ 200 mil: Classe 1 na v2
    assert u1.at["a", "peso_universo"] == 1      # Classe 2 na v1
    assert u2["peso_universo"].sum() != u1["peso_universo"].sum()


def test_indeterminada_fora_no_min_e_dentro_no_max(regras, p_min, p_base, p_max):
    lim = regras["versoes"]["v2"]["limites"]
    peso = {n: universo(_serv(), lim, p).set_index("cns").at["f", "peso_universo"] for n, p in
            (("min", p_min), ("base", p_base), ("max", p_max))}
    assert peso["min"] == 0 and peso["max"] == 1 and 0 < peso["base"] < 1


def test_intervencao_e_diligencia_fora_no_base_e_dentro_no_max(regras, p_base, p_max):
    lim = regras["versoes"]["v2"]["limites"]
    base = universo(_serv(), lim, p_base).set_index("cns")
    mx = universo(_serv(), lim, p_max).set_index("cns")
    assert base.at["d", "peso_universo"] == 0 and base.at["e", "peso_universo"] == 0
    assert mx.at["d", "peso_universo"] == 1 and mx.at["e", "peso_universo"] == 1


def test_fracao_fora_classe_1():
    s = pd.DataFrame({"situacao_juridica": ["PROVIDO", "PROVIDO", "PROVIDO", "VAGO"],
                      "classe": ["1", "2", "indeterminada", "3"]})
    assert fracao_fora_classe_1(s) == pytest.approx(0.5)
