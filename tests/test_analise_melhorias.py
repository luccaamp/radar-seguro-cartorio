"""src/analise/melhorias.py (notebook 10, melhorias de confiança M1 a M10) e dados.saldo_bi. Dados SINTÉTICOS."""
import duckdb
import numpy as np
import pandas as pd
import pytest

from src.analise import dados, melhorias as mh

P = {"prob_deficit": {"classe_2": 0.5, "classe_3": 0.3}, "pct_descoberto": {"classe_2": 0.5, "classe_3": 0.4},
     "escolha_garantia": {"bens_proprios": 0.3, "fianca": 0.2, "seguro": 0.5}, "taxa_seguro_anual": 0.02,
     "comissao": 0.17, "despesa_administrativa": 0.08, "sinistralidade": 0.109}


def _sv():
    """Quatro obrigadas: uma com folga de saldo, uma apertada, uma com saldo ≤ 0 e uma sem dado do BI."""
    return pd.DataFrame({"cns": ["a", "b", "c", "d"], "peso_universo": [1.0, 1.0, 1.0, 0.5],
                         "passivo": [120.0, 1200.0, 100.0, 80.0], "classe_faixa": ["2", "3", "2", "indeterminada"],
                         "valor_descoberto": [30.0, 144.0, 25.0, 10.0], "n_deficit": [0.5, 0.3, 0.5, 0.25]})


def _saldo():
    return pd.DataFrame({"cns": ["a", "b", "c"], "saldo_anual": [1200.0, 600.0, -50.0], "semestres": [2, 2, 1]})


def test_saldo_bi_conta_o_custeio_repetido_uma_vez(tmp_path):
    """No 2º semestre o BI repete o custeio em cada linha de atribuição: conta uma vez; um semestre só é anualizado."""
    csv = tmp_path / "bi.csv"
    cab = "CNS\tDat. início do período\tDat. final período\tValor Custeio\tAtribuição\tQuantidade de atos praticados" \
          "\tValor arrecadação\tValor repasse\n"
    linhas = ["00.001-1\t01/01/2025\t30/06/2025\t100,00\t-\t1\t1.000,00\t200,00",
              "00.001-1\t01/07/2025\t31/12/2025\t300,00\tNotas\t1\t800,00\t100,00",
              "00.001-1\t01/07/2025\t31/12/2025\t300,00\tRCPN\t1\t400,00\t100,00",
              "00.002-2\t01/01/2025\t30/06/2025\t50,00\t-\t1\t500,00\t50,00"]
    csv.write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")
    with duckdb.connect() as con:
        s = dados.saldo_bi(con, 2025, csv).set_index("cns")
    assert s.loc["000011", "custeio_bi"] == 400            # 100 + 300 (e não 100 + 300 + 300)
    assert s.loc["000011", "saldo_anual"] == pytest.approx(2200 - 400 - 400)
    assert s.loc["000022", "saldo_anual"] == pytest.approx((500 - 50 - 50) * 2)   # um semestre, anualizado


def test_capacidade_faixas_e_descoberto():
    cap = mh.capacidade(_sv(), _saldo(), horizonte=12).set_index("cns")
    assert list(cap["faixa_meses"].astype(str)) == ["< 3 meses", "> 12 meses", "saldo ≤ 0", "sem dado"]
    assert cap.loc["a", "meses_de_saldo"] == pytest.approx(1.2) and not cap.loc["a", "nao_cobre"]
    assert cap.loc["b", "descoberto_m1"] == pytest.approx(600) and cap.loc["b", "nao_cobre"]
    assert cap.loc["c", "descoberto_m1"] == pytest.approx(100)     # saldo ≤ 0: o passivo inteiro fica descoberto
    assert np.isnan(cap.loc["d", "descoberto_m1"]) and cap.loc["d", "faixa_deficit"] == "classe_2"


def test_deficit_m1_usa_o_modelo_sem_dado_e_calibracao():
    cap = mh.capacidade(_sv(), _saldo(), horizonte=12)
    assert mh.deficit_m1(cap) == pytest.approx(0 + 600 + 100 + 10)   # "d" sem dado: déficit do modelo
    cal = mh.calibracao(cap, P)
    assert cal.loc["classe_2", "prob_deficit_m1"] == pytest.approx(0.5)    # a cobre, c não (pesos 1 e 1)
    assert cal.loc["classe_3", "pct_descoberto_m1"] == pytest.approx(0.5)
    assert cal.loc["classe_2", "prob_deficit_modelo"] == 0.5


def test_sinistro_frequencia_vezes_severidade():
    cap = mh.capacidade(_sv(), _saldo(), horizonte=12)
    s = mh.sinistro(cap, P, p_fim={"base": 0.04})
    sem, com = s.iloc[0], s.iloc[1]
    assert sem.sinistralidade == pytest.approx(0.04 / 0.02)          # q = 1: P(fim) ÷ taxa
    # parte não paga: a cobre (q 0), b paga 600 de 480 descobertos (q 0), c e d não pagam (q 1)
    assert com.severidade_q == pytest.approx((25 + 10) / (30 + 144 + 25 + 10))
    assert com.indice_combinado == pytest.approx(com.sinistralidade + 0.25)
    assert com.resultado_tecnico == pytest.approx(com.premio * (1 - com.indice_combinado))


def test_premio_por_cenario_e_grade():
    mc = pd.DataFrame({"variante": ["independentes"], "medida": ["premio"], "valor_base": [100.0], "p05": [50.0],
                       "p50": [110.0], "p95": [200.0]})
    cen = {"cenarios": {"mantem": {"descricao": "x", "ajustes": {}},
                        "parcial": {"descricao": "y", "ajustes": {"fracao_exigencia_garantia": 0.5}}}}
    t = mh.premio_por_cenario(mc, cen).set_index("cenario")
    assert t.loc["parcial", "premio_p95"] == 100 and t.loc["mantem", "premio_base"] == 100
    sem = {"premissas": {"taxa_seguro_anual": {"valores": {"min": 0.01, "base": 0.02}},
                         "escolha_garantia": {"valores": {"min": {"seguro": 0.25}, "base": {"seguro": 0.5}}}}}
    g = mh.grade_taxa_adesao(1000.0, sem)
    assert g.loc[0.02, "adesao_50%"] == pytest.approx(10.0) and g.shape == (2, 2)


def test_cobertura_da_faixa_so_com_o_passado():
    erros = pd.DataFrame({"metodo": "m", "origem": [f"{2010 + i}-2" for i in range(7)], "horizonte": 1,
                          "erro_rel": [0.0, 0.01, -0.01, 0.02, -0.02, 0.5, 0.0]})
    c = mh.cobertura_faixa(erros, "m", (0.1, 0.9), minimo_origens=5)
    assert list(c["origem"]) == ["2015-2", "2016-2"] and list(c["dentro"]) == [False, True]
    qs, cob = mh.quantis_para_cobertura(erros, "m", alvo=0.5, minimo_origens=5)
    assert cob >= 0.5 and qs[0] < qs[1]


def test_rais_projetada_soma_tempo_e_corrige_salario():
    r = pd.DataFrame({"tempo_emprego_meses": [10.0, None], "rem_dezembro": [1000.0, 2000.0], "rem_media": [900.0, 1800.0]})
    out = mh.rais_projetada(r, 2, 0.05)
    assert list(out["tempo_emprego_meses"]) == [34.0, 24.0]
    assert out["rem_dezembro"].iloc[0] == pytest.approx(1000 * 1.05 ** 2) and r["tempo_emprego_meses"].iloc[0] == 10
