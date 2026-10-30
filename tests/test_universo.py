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


def _carteira_sintetica():
    """Serventias SINTÉTICAS cobrindo as faixas das duas regras (v1: Classe 1 até 100 mil; v2: até 300 mil)."""
    receitas = [50_000.0, 150_000.0, 250_000.0, 350_000.0, 800_000.0, 1_200_000.0, 2_000_000.0, None, None]
    situacoes = ["PROVIDO"] * 7 + ["PROVIDO", "VAGO"]
    return pd.DataFrame({"cns": [f"s{i}" for i in range(len(receitas))], "receita_ref": receitas,
                         "situacao_juridica": situacoes, "passivo": [80_000.0 + 10_000 * i for i in range(len(receitas))]})


@pytest.mark.parametrize("nivel", ["min", "base", "max"])
def test_monotonicidade_v1_contem_v2(nivel, regras, semente):
    """D-019: universo_v1 ⊇ universo_v2 ⇒ déficit, IS e prêmio da v1 ≥ v2; o peso da indeterminada é o de cada regra."""
    from src.model.mercado import deficit, demanda_seguro, receita
    from src.model.premissas import resolver
    s = _carteira_sintetica()
    lim_base = regras["versoes"][regras["versao_base"]]["limites"]
    out = {}
    for regra in ("v1", "v2"):
        lim = regras["versoes"][regra]["limites"]
        peso = fracao_fora_classe_1(s.assign(classe=[classificar(r, lim) for r in s["receita_ref"]]))
        p = resolver(semente, nivel, {"peso_classe_indeterminada_base": {"min": 0.0, "base": peso, "max": 1.0}[nivel]})
        d = deficit(universo(s, lim, p, lim_base), p)
        dem = demanda_seguro(d["valor_descoberto"].sum(), p)
        out[regra] = (d, dem.importancia_segurada, receita(dem, p)["mercado"].premio_emitido)
    d1, is1, pr1 = out["v1"]
    d2, is2, pr2 = out["v2"]
    assert (d1["peso_universo"] >= d2["peso_universo"]).all()
    assert d1["valor_descoberto"].sum() >= d2["valor_descoberto"].sum()
    assert is1 >= is2 and pr1 >= pr2
    # as faixas seguem a classe da regra base nas duas regras; Classe 1 pela v2 usa a faixa da Classe 2
    assert (d1["classe_faixa"] == d2["classe_faixa"]).all()
    entra_so_v1 = (d1["peso_universo"] > 0) & (d2["peso_universo"] == 0)
    assert entra_so_v1.any() and (d1.loc[entra_so_v1, "classe_faixa"] == "1").all()


def test_faixa_da_classe_1_e_a_da_classe_2():
    from src.model.mercado import FAIXA_POR_CLASSE, _faixa
    assert _faixa("1") == _faixa("2") == "classe_2" and _faixa("3") == "classe_3"
    assert set(FAIXA_POR_CLASSE) == {"1", "2", "3", "indeterminada"}
    with pytest.raises(ValueError):
        _faixa("4")


def test_leituras_alternativas_da_regra(regras):
    """D-023: as leituras alternativas só mudam o valor comparado ao limite; conflito e zero nos dois seguem indeterminados."""
    from src.model.leituras import receita_referencia_alternativa
    lim = regras["versoes"]["v2"]["limites"]
    classes = {}
    for leitura in ("literal", "dois_semestres", "algum_semestre"):
        r = receita_referencia_alternativa(_semestres(), 2025, leitura).set_index("cns")
        classes[leitura] = {c: classificar(v, lim) for c, v in r["receita_ref"].items()}
        assert pd.isna(r.at["conflito", "receita_ref"]) and pd.isna(r.at["zeros", "receita_ref"])
    # "um_zero" (0 e 500 mil): principal usa 500 mil (Classe 2); literal 250 mil e dois semestres 0 -> Classe 1
    assert classes["literal"]["um_zero"] == "1" and classes["dois_semestres"]["um_zero"] == "1"
    assert classes["algum_semestre"]["um_zero"] == "2"
    # "dois" (200 mil e 600 mil): literal 400 mil (2), dois semestres 200 mil (1), algum 600 mil (2)
    assert (classes["literal"]["dois"], classes["dois_semestres"]["dois"], classes["algum_semestre"]["dois"]) == ("2", "1", "2")
