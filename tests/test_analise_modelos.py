"""src/analise: regressão (notebook 06), sensibilidade (notebook 08) e concentração. Dados SINTÉTICOS, salvo o teste
`dados_reais`, que roda numa cópia do banco."""
import json

import duckdb
import numpy as np
import pandas as pd
import pytest
import yaml

from src import estado
from src.analise import RAIZ, estatistica, regressao, sensibilidade
from src.model.premissas import resolver
from src.model.simulador import resumo_por_totais

CENARIOS = yaml.safe_load((RAIZ / "config" / "cenarios_stf.yaml").read_text(encoding="utf-8"))
TOTAIS = {"passivo_ponderado_classe_2": 6.0e7, "passivo_ponderado_classe_3": 1.7e8,   # sintéticos
          "peso_com_passivo_classe_2": 700.0, "peso_com_passivo_classe_3": 350.0, "n_serventias_ativas": 10,
          "clt": 50.0, "passivo_todas": 3e8, "n_universo": 1000.0, "n_indeterminadas_universo": 0,
          "passivo_universo": 2.3e8}


# ---------------------------------------------------------------- concentração

def test_gini_e_curva_de_lorenz():
    assert estatistica.gini(pd.Series([5, 5, 5, 5])) == pytest.approx(0)
    assert estatistica.gini(pd.Series([0, 0, 0, 1, None])) == pytest.approx(0.75)    # (n − 1) ÷ n com n = 4
    c = estatistica.curva_lorenz(pd.Series([1, 1, 2]))
    assert c["fracao_unidades"].tolist() == pytest.approx([0, 1 / 3, 2 / 3, 1])
    assert c["fracao_valor"].tolist() == pytest.approx([0, 0.25, 0.5, 1])


# ---------------------------------------------------------------- 06a

def _serventias_sinteticas(n=60, semente=0):
    rng = np.random.default_rng(semente)
    receita = np.exp(rng.uniform(np.log(5e4), np.log(5e6), n))
    df = pd.DataFrame({"cns": [f"{i:06d}" for i in range(n)], "cod_ibge": 3100000 + np.arange(n) % 7,
                       "regiao_intermediaria": np.array(["A", "B", "C"])[np.arange(n) % 3], "receita_ref": receita,
                       "clt": np.round(receita / 2e5), "n_atribuicoes": 1 + np.arange(n) % 3})
    for a in ["notas", "rcpn", "ri", "rtd", "rcpj", "protesto"]:
        df[a] = rng.random(n) < 0.4
    return df


def test_base_clt_filtra_e_cria_variaveis():
    df = _serventias_sinteticas(6)
    df.loc[0, "receita_ref"] = 0
    df.loc[1, "clt"] = None
    df.loc[2, "regiao_intermediaria"] = None
    b = regressao.base_clt(df)
    assert len(b) == 3 and set(regressao.VARIAVEIS_CLT) <= set(b.columns)
    assert b["log_receita"].tolist() == pytest.approx(np.log(b["receita_ref"]).tolist())
    assert b["notas"].isin([0, 1]).all()


def test_mediana_por_faixa_preve_a_mediana_da_faixa():
    tr = pd.DataFrame({"log_receita": np.log([1, 2, 3, 4, 10, 20, 30, 40.0]), "clt": [1, 1, 3, 3, 5, 5, 9, 9]})
    te = pd.DataFrame({"log_receita": np.log([1.5, 35.0])})
    assert regressao.prever_mediana_faixa(tr, te, faixas=2).tolist() == [2, 7]   # metades de baixo e de cima


def test_validacao_grupo_fora_nunca_treina_no_grupo():
    df = _serventias_sinteticas()
    media = {"média do treino": lambda tr, te: np.full(len(te), tr["clt"].mean())}
    prev, m, por = regressao.validar_grupo_fora(df, media)
    for g in "ABC":
        esperado = df.loc[df["regiao_intermediaria"] != g, "clt"].mean()
        assert prev.loc[df["regiao_intermediaria"] == g, "média do treino"].eq(esperado).all()
    assert len(por) == 3 and m.loc["média do treino", "MAE"] == pytest.approx(
        np.mean(np.abs(prev["média do treino"] - df["clt"])))


def test_metricas_e_margem():
    m = regressao.metricas([1, 2, 3], [1, 2, 6])
    assert m["MAE"] == pytest.approx(1) and m["RMSE"] == pytest.approx(np.sqrt(3)) and m["R2"] == pytest.approx(-3.5)
    assert regressao.total_com_margem(100, 0.1) == pytest.approx((90, 110))


def test_floresta_e_poisson_seguem_a_receita_e_tabela_do_modelo():
    df = regressao.base_clt(_serventias_sinteticas(90))
    prev, m, _ = regressao.validar_grupo_fora(df, regressao.METODOS_CLT)
    assert set(m.index) == set(regressao.METODOS_CLT) and prev.notna().all().all()
    assert np.corrcoef(prev["Floresta aleatória"], df["clt"])[0, 1] > 0.8
    t = regressao.tabela_clt_modelo(df, prev)
    assert len(t) == len(df) and (t["residuo_floresta"] == t["clt_declarado"] - t["clt_previsto_floresta"]).all()
    coef = regressao.coeficientes_poisson(df)
    assert coef.loc["log_receita", "fator"] > 1


# ---------------------------------------------------------------- 06b

def test_partes_da_variancia_do_log_somam_um():
    clt = pd.Series([1, 2, 4, 8.0])
    p = regressao.partes_variancia_log(clt, pd.Series([10.0] * 4))          # passivo médio igual: só a quantidade
    assert p["quantidade"] == pytest.approx(1) and p["passivo_medio_vinculo"] == pytest.approx(0)
    p = regressao.partes_variancia_log(clt, pd.Series([1, 3, 2, 5.0]))
    assert p["quantidade"] + p["passivo_medio_vinculo"] == pytest.approx(1)


def test_shapley_soma_o_r2_e_regressao_loglog_recupera_elasticidades():
    rng = np.random.default_rng(1)
    df = pd.DataFrame({"a": np.exp(rng.normal(size=200)), "b": np.exp(rng.normal(size=200))})
    df["y"] = 2 * df["a"] * df["b"] ** 0.5 * np.exp(rng.normal(scale=0.05, size=200))
    X, y = np.log(df[["a", "b"]]), np.log(df["y"])
    partes = regressao.shapley_r2(X, y)
    r = regressao.regressao_loglog(df, "y", ["a", "b"], dobras=5)
    assert partes.sum() == pytest.approx(r["r2"]) and partes["a"] > partes["b"]
    assert r["coeficientes"].loc["a", "elasticidade"] == pytest.approx(1, abs=0.02)
    assert r["coeficientes"].loc["b", "elasticidade"] == pytest.approx(0.5, abs=0.02)
    assert 0.98 < r["r2_validacao"] <= r["r2"] + 1e-9


def test_distribuicao_usada_segue_a_origem():
    v = pd.DataFrame({"cod_ibge": [1, 1, 2, 3], "salario": [1000.0, 3000.0, 5000.0, 7000.0],
                      "meses_servico": [10.0, 30.0, 50.0, 70.0]})
    medio = pd.DataFrame({"cod_ibge": [1, 2, 4], "origem_distribuicao": ["municipio", "regiao", "estado"]})
    d = regressao.distribuicao_usada(v, medio, {1: "R1", 2: "R2", 3: "R2", 4: "R3"}).set_index("cod_ibge")
    assert d.loc[1, "salario_medio"] == 2000 and d.loc[1, "chave_distribuicao"] == "municipio:1"
    assert d.loc[2, "salario_medio"] == 6000 and d.loc[2, "n_vinculos_distribuicao"] == 2   # região R2 = municípios 2 e 3
    assert d.loc[4, "salario_medio"] == 4000 and d.loc[4, "chave_distribuicao"] == "estado"


# ---------------------------------------------------------------- 08: suposições

def _premissas():
    return resolver(estado.ler_semente(), "base", {"peso_classe_indeterminada_base": 0.5})


def test_premio_vetorial_igual_ao_modelo():
    p, faixas = _premissas(), sensibilidade.faixas_suposicoes(estado.ler_semente())
    x = sensibilidade.sortear(faixas, n=5, semente=3)
    vet = sensibilidade.premio_vetorial(TOTAIS, x)
    for i in range(5):
        r = resumo_por_totais(TOTAIS, sensibilidade.com_suposicoes(p, {k: v[i] for k, v in x.items()}), CENARIOS,
                              "mantem")
        assert vet["premio"][i] == pytest.approx(r["mercado_premio_emitido"])
        assert vet["importancia_segurada"][i] == pytest.approx(r["mercado_importancia_segurada"])


def test_com_suposicoes_mantem_a_escolha_somando_um():
    e = sensibilidade.com_suposicoes(_premissas(), {"seguro": 0.7})["escolha_garantia"]
    assert sum(e.values()) == pytest.approx(1) and e["seguro"] == 0.7
    assert e["bens_proprios"] / e["fianca"] == pytest.approx(0.30 / 0.20)   # proporção do base


def test_tornado_ordena_pela_amplitude():
    t = sensibilidade.tornado(TOTAIS, sensibilidade.faixas_suposicoes(estado.ler_semente()), _premissas(), CENARIOS)
    assert t["amplitude"].is_monotonic_decreasing and len(t) == 6
    assert (t["premio_no_min"] <= t["premio_base"]).all() and (t["premio_base"] <= t["premio_no_max"]).all()
    assert t.iloc[0]["suposicao"] == "taxa"
    assert list(sensibilidade.tabela_tornado(t.assign(grupo="suposição"))["ordem"]) == list(range(1, 7))


def test_sorteios_ficam_na_faixa_se_repetem_e_andam_juntos():
    faixas = sensibilidade.faixas_suposicoes(estado.ler_semente())
    a = sensibilidade.sortear(faixas, n=2000, semente=7)
    b = sensibilidade.sortear(faixas, n=2000, semente=7)
    for k, f in faixas.iterrows():
        assert (a[k] >= f["min"]).all() and (a[k] <= f["max"]).all() and np.array_equal(a[k], b[k])
    j = sensibilidade.sortear(faixas, n=2000, semente=7, juntas=sensibilidade.PATRIMONIO)
    postos = pd.DataFrame({k: j[k] for k in sensibilidade.PATRIMONIO}).rank()
    assert (postos.corr() > 0.999).all().all()
    assert abs(np.corrcoef(a["prob_2"], a["prob_3"])[0, 1]) < 0.1
    r = sensibilidade.resumo_sorteios({"premio": np.arange(101.0)}, [0.05, 0.5, 0.95])
    assert r.iloc[0][["p05", "p50", "p95"]].tolist() == [5, 50, 95]


# ---------------------------------------------------------------- 08: passivo e receita líquida

def test_salario_estimado_so_para_quem_falta():
    rais = pd.DataFrame({"ativo_31_12": [True] * 5 + [False], "tipo_vinculo": [10, 10, 10, 10, 10, 10],
                         "rem_dezembro": [2000.0, 3000.0, None, 0.0, None, None],
                         "rem_media": [1000.0, 1500.0, 500.0, 0.0, None, 800.0], "cod_ibge": [1, 2, 1, 2, 9, 1]})
    r, z = sensibilidade.rais_com_salario_estimado(rais, {1: "R1", 2: "R2", 9: "R9"})
    assert z.index.tolist() == [2, 3, 4]                       # o inativo (5) fica de fora
    assert r.loc[2, "rem_dezembro"] == pytest.approx(1000)    # 500 × razão 2
    assert r.loc[3, "rem_dezembro"] == 3000                    # sem remuneração: mediana da região R2
    assert r.loc[4, "rem_dezembro"] == 2500                    # região sem conhecido: mediana do estado
    assert r.loc[:1, "rem_dezembro"].tolist() == [2000, 3000] and pd.isna(r.loc[5, "rem_dezembro"])


def test_encolhimento_so_mexe_nos_pequenos():
    p = _premissas()
    rng = np.random.default_rng(2)
    linhas = [(cod, s, m) for cod, n in [(1, 25), (2, 25), (3, 3), (4, 0)]
              for s, m in zip(rng.uniform(1500, 6000, n), rng.uniform(1, 200, n))]
    v = pd.DataFrame(linhas, columns=["cod_ibge", "salario", "meses_servico"])
    regioes = {1: "R", 2: "R", 3: "R", 4: "R"}
    base = sensibilidade.passivo_medio_por_municipio(v, [1, 2, 3, 4], p, 20, regioes).set_index("cod_ibge")
    enc = sensibilidade.medio_com_encolhimento(v, [1, 2, 3, 4], p, 20, regioes).set_index("cod_ibge")
    assert enc.loc[[1, 2, 4], "passivo_medio_vinculo"].tolist() == pytest.approx(
        base.loc[[1, 2, 4], "passivo_medio_vinculo"].tolist())
    assert enc.loc[3, "origem_distribuicao"] == "encolhimento" and 0 < enc.loc[3, "lambda"] < 1
    proprio = sensibilidade.passivo_vinculos(v[v.cod_ibge == 3], p).mean()
    lam = enc.loc[3, "lambda"]
    assert enc.loc[3, "passivo_medio_vinculo"] == pytest.approx(lam * proprio + (1 - lam) * base.loc[3,
                                                                "passivo_medio_vinculo"])


def test_faixa_da_base_muda_so_o_deficit():
    p = _premissas()
    base = pd.DataFrame({"cns": ["a", "b"], "classe_faixa": ["3", "2"]})
    alt = pd.DataFrame({"cns": ["a", "b"], "classe": ["2", "1"], "classe_faixa": ["2", "1"], "passivo": [100.0, 50.0],
                        "peso_universo": [1.0, 0.0], "n_deficit": [9.0, 9.0], "valor_descoberto": [9.0, 9.0]})
    out = sensibilidade.com_faixa_da_base(alt, base, p)
    assert out["classe_faixa"].tolist() == ["3", "2"] and out["classe"].tolist() == ["2", "1"]
    pd_3, pct_3 = p["prob_deficit"]["classe_3"], p["pct_descoberto"]["classe_3"]
    assert out["valor_descoberto"].tolist() == pytest.approx([pd_3 * pct_3 * 100, 0])


def test_receita_bi_liquida_nunca_negativa():
    bi = pd.DataFrame({"cns": ["a", "a", "b", "c"], "ano": [2025, 2025, 2025, 2024], "semestre": [1, 2, 1, 1],
                       "arrecadacao_bi": [100.0, 300.0, 50.0, 10.0], "repasse_bi": [20.0, 60.0, 80.0, 1.0]})
    r = sensibilidade.receita_ref_bi(bi, 2025).set_index("cns")
    assert list(r.index) == ["a", "b"]
    assert r.loc["a", "arrecadacao_bi"] == 200 and r.loc["a", "liquida_bi"] == 160
    assert r.loc["a", "fracao_repasse"] == pytest.approx(0.2)
    assert r.loc["b", "liquida_bi"] == 0 and r.loc["b", "semestres_repasse_maior"] == 1


# ---------------------------------------------------------------- dados reais (cópia do banco)

@pytest.mark.dados_reais
def test_sensibilidade_reproduz_a_base_e_o_t7(_copia_real):
    """Numa CÓPIA do banco: o motor refeito pelo notebook 08 dá o prêmio oficial, e o tornado repete o do T7."""
    from src.analise import dados
    from src.model import simulador
    from src.motor import calcular_serventias, premissas_nivel, resumo_mercado
    from src.transform.gold import carregar_insumos
    sem = estado.ler_semente()
    lim = yaml.safe_load((RAIZ / "config" / "regras_classificacao.yaml").read_text(encoding="utf-8"))["versoes"]["v2"]
    with duckdb.connect(str(_copia_real["copia"]), read_only=True) as con:
        peso = con.execute("SELECT peso_classe_indeterminada_base FROM gold.execucao WHERE regra_classe = 'v2'"
                           ).fetchone()[0]
        premio = con.execute("SELECT mercado_premio_emitido FROM gold.fato_mercado_uf WHERE nivel = 'base' AND "
                             "regra_classe = 'v2' AND cenario_stf = 'mantem'").fetchone()[0]
        sv, ins = dados.serventias(con), carregar_insumos(con)
    p = premissas_nivel(sem, "base", peso)
    recalc = resumo_mercado(calcular_serventias(ins, p, lim["limites"], limites_faixa=lim["limites"])[0], p, CENARIOS,
                            "mantem")
    assert recalc["mercado_premio_emitido"] == pytest.approx(premio)
    t = sensibilidade.tornado(simulador.totais(sv), sensibilidade.faixas_suposicoes(sem), p, CENARIOS)
    t7 = json.loads((RAIZ / "docs/qa/analises/testes_metodos_resultados.json").read_text(encoding="utf-8"))
    taxa = next(r for r in t7["T7_incerteza_premio"]["tornado"] if r["suposicao"] == "taxa")
    assert t.set_index("suposicao").loc["taxa", "premio_no_min"] / 1e3 == pytest.approx(taxa["min_mil"], abs=0.1)
    assert t.set_index("suposicao").loc["taxa", "premio_no_max"] / 1e3 == pytest.approx(taxa["max_mil"], abs=0.1)
