"""src/analise (mineração, docs/plano_mineracao.md): estatística, leitura do BI do CNJ e formatos. Dados SINTÉTICOS."""
import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from src.analise import dados, estatistica, graficos  # noqa: E402


def test_resumo_e_cauda_longa():
    r = estatistica.resumo(pd.Series([1, 2, 3, 4, 90, None]))   # sintético: um valor grande puxa a média
    assert r["n"] == 5 and r["mediana"] == 3 and r["media"] == 20 and r["soma"] == 100
    assert r["q1"] == 2 and r["q3"] == 4 and r["media_sobre_mediana"] == pytest.approx(20 / 3)


def test_resumo_por_grupo_soma_um():
    df = pd.DataFrame({"g": ["a", "a", "b"], "v": [1.0, 3.0, 4.0]})
    out = estatistica.resumo_por_grupo(df, "v", "g")
    assert list(out.index) == ["a", "b"] and out["pct_soma"].sum() == pytest.approx(1)
    assert out.loc["a", "mediana"] == 2


def test_faltantes():
    out = estatistica.faltantes({"vazio": pd.Series([True, False, False, False])})
    assert out.iloc[0].to_dict() == {"problema": "vazio", "n": 1, "total": 4, "pct": 0.25}


def test_cercas_de_tukey_na_escala_original_e_no_log():
    s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 100])   # sintético
    inf, sup = estatistica.cercas_iqr(s, k=1.5, log=False)
    assert (inf, sup) == (-3.0, 13.0)              # Q1 = 3, Q3 = 7, IQR = 4: 3 − 6 e 7 + 6
    assert estatistica.atipicos(s, k=1.5, log=False).tolist() == [False] * 8 + [True]
    inf_log, sup_log = estatistica.cercas_iqr(pd.Series([10, 100, 1000, 10000, 100000]), k=1.5, log=True)
    assert inf_log == pytest.approx(10 ** -1) and sup_log == pytest.approx(10 ** 7)   # Q1 = 2, Q3 = 4 em log10


def test_atipicos_ignora_zero_e_vazio_no_log():
    m = estatistica.atipicos(pd.Series([0, None, 10, 100, 1000, 10 ** 9]), k=1.5, log=True)
    assert m.tolist() == [False, False, False, False, False, True]   # o zero é contado à parte, não como atípico


def test_saltos_marcam_semestre_fora_do_historico():
    """Sintético: a serventia A salta 100 vezes no 6º semestre; a B cresce devagar; zeros não entram."""
    linhas = [("A", 2020 + i // 2, i % 2 + 1, v) for i, v in enumerate([10, 12, 11, 0, 13, 1300, 12])]
    linhas += [("B", 2020 + i // 2, i % 2 + 1, v) for i, v in enumerate([10, 12, 14, 16, 18, 20, 22])]
    df = pd.DataFrame(linhas, columns=["cns", "ano", "semestre", "arrecadacao"])
    out = estatistica.saltos(df, janela=4, fator=10)
    assert out[["cns", "ano", "semestre"]].values.tolist() == [["A", 2022, 2]]
    assert out["mediana_anterior"].iloc[0] == 11.5 and out["razao"].iloc[0] == pytest.approx(1300 / 11.5)
    corrigida = estatistica.sem_saltos(df, out)
    assert corrigida["arrecadacao"].sum() == df["arrecadacao"].sum() - 1300 + 11.5 and len(corrigida) == len(df)


def test_classe_pela_receita_usa_os_limites_da_v2():
    from src.analise import enquadramento
    c1, c2 = enquadramento.limites_classe("v2")
    out = enquadramento.classe_pela_receita(pd.Series([c1, c1 + 0.01, c2, c2 + 0.01, None]))
    assert out.tolist()[:4] == ["1", "2", "2", "3"] and pd.isna(out.iloc[4])


def test_receita_sem_saltos():
    """Sintético: A salta no 2º semestre do ano (fica o 1º); B salta nos dois (vale a média do ano anterior)."""
    from src.analise import enquadramento
    serie = pd.DataFrame([("A", 2024, 1, 10.0), ("A", 2024, 2, 20.0), ("A", 2025, 1, 30.0), ("A", 2025, 2, 900.0),
                          ("B", 2024, 1, 40.0), ("B", 2024, 2, 0.0), ("B", 2025, 1, 800.0), ("B", 2025, 2, 700.0),
                          ("C", 2025, 1, 5.0)], columns=["cns", "ano", "semestre", "arrecadacao"])
    saltos = pd.DataFrame([("A", 2025, 2), ("B", 2025, 1), ("B", 2025, 2)], columns=["cns", "ano", "semestre"])
    assert enquadramento.receita_sem_saltos(serie, saltos, 2025).to_dict() == {"A": 30.0, "B": 40.0}


def test_fatores_reais_por_semestre():
    """Sintético: índice 100 no 1º semestre, 110 no 2º; base = dez (110). Semestre incompleto fica fora."""
    indice = pd.DataFrame({"ano_mes": [202501 + i for i in range(12)] + [202601],
                           "numero_indice": [100.0] * 6 + [110.0] * 6 + [120.0]})
    f = estatistica.fatores_reais(indice, 202512)
    assert f.to_dict() == {"2025-1": pytest.approx(1.1), "2025-2": pytest.approx(1.0)}


def test_correlacao_de_spearman_monotona():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [1, 4, 9, 16, 1000], "z": [5, 4, 3, 2, 1]})
    out = estatistica.correlacoes(df, ["x", "y", "z"]).set_index(["a", "b"])["rho"]
    assert out[("x", "y")] == pytest.approx(1) and out[("x", "z")] == pytest.approx(-1)


def test_participacao_topo_e_crescimento():
    assert estatistica.participacao_topo(pd.Series([10, 1, 1, 1, 1, 1, 1, 1, 1, 2]), 0.1) == pytest.approx(0.5)
    assert estatistica.crescimento_medio(pd.Series([100, 110, 121])) == pytest.approx(0.1)


def test_arrecadacao_bi_le_o_formato_do_cnj(tmp_path):
    """CSV sintético no formato da exportação do BI: CNS 00.005-9, vírgula decimal, '-' vazio, anual e por atribuição."""
    csv = tmp_path / "bi.csv"
    cab = "CNS\tDat. início do período\tDat. final período\tValor Custeio\tAtribuição\t" \
          "Quantidade de atos praticados\tValor arrecadação\tValor repasse"
    linhas = [cab,
              "00.005-9\t01/01/2006\t31/12/2006\t-\t-\t10\t9.999,00\t0,00",           # anual: fica fora
              "00.005-9\t01/01/2025\t30/06/2025\t-\t-\t10\t1.000,50\t100,00",
              "00.005-9\t01/07/2025\t31/12/2025\t-\tNT\t10\t2.000,00\t-",
              "00.005-9\t01/07/2025\t31/12/2025\t-\tRCPN\t10\t500,25\t50,00",
              "00.005-9\t-\t-\t-\tNT\t-\t-\t-"]                                          # sem data: fica fora
    csv.write_bytes(("\r\n".join(linhas) + "\r\n").encode("utf-8"))   # write_text trocaria \n por \r\n no Windows
    with duckdb.connect() as con:
        df = dados.arrecadacao_bi(con, csv).sort_values(["ano", "semestre"])
    assert df[["cns", "ano", "semestre"]].values.tolist() == [["000059", 2025, 1], ["000059", 2025, 2]]
    assert df["arrecadacao_bi"].tolist() == [1000.5, 2500.25] and df["repasse_bi"].tolist() == [100.0, 50.0]


def test_formatos_brasileiros():
    assert graficos.num(2525) == "2.525" and graficos.num(0.5, 1) == "0,5"
    assert graficos.pct(0.123) == "12,3%"
    assert graficos.reais(311_866_700) == "R$ 311,9 mi" and graficos.reais(368_700) == "R$ 368,7 mil"
    assert graficos.reais(950) == "R$ 950"
    t = graficos.tabela(pd.DataFrame({"n": [2525, None], "p": [0.5, 0.25]}), {"n": "int", "p": "pct"})
    assert t.values.tolist() == [["2.525", "50,0%"], ["—", "25,0%"]]


def test_salvar_grava_png(tmp_path, monkeypatch):
    monkeypatch.setattr(graficos, "RAIZ", tmp_path)
    graficos.estilo()
    fig, ax = plt.subplots()
    ax.plot([1, 2], [1, 2])
    caminho = graficos.salvar(fig, "teste")
    plt.close(fig)
    assert caminho.parent.relative_to(tmp_path).as_posix() == "docs/qa/analises"
    assert caminho.read_bytes()[:4] == b"\x89PNG"
