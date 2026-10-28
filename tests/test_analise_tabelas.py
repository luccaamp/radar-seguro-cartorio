"""src/analise/tabelas.py (tabelas gold.analise_* da Etapa 2), src/analise/conclusoes.py (notebook 09) e a etapa de
análises do pipeline. Dados SINTÉTICOS, salvo o teste `dados_reais`, que roda numa cópia do banco."""
import duckdb
import numpy as np
import pandas as pd
import pytest

from src.analise import conclusoes as cc, grupos as gr, regressao as rg, tabelas

NOMES_ANALISE = ["analise_regras", "analise_grupos", "analise_clt_modelo", "analise_previsao", "analise_tornado",
                 "analise_monte_carlo"]   # as seis que o notebook 09 lê (as da D-044 ficam fora de conclusoes.carregar)


def _perfil(trocas: dict | None = None) -> pd.DataFrame:
    """Perfil sintético com o formato descrito pelos nomes do notebook 04 (k = 6). `trocas`: {(coluna, grupo): valor}."""
    p = pd.DataFrame({"pct_vagas": [0.95, 0.01, 0.02, 0.10, 0.97, 0.03], "pct_ri": [0, 0, 0.1, 0.8, 0.2, 0.5],
                      "atribuicoes_medianas": [1, 2, 1, 3, 1, 2], "receita_mediana": [1, 2, 3, 4, 5, 6.0]},
                     index=pd.Index(range(1, 7), name="grupo"))
    for (col, g), v in (trocas or {}).items():
        p.loc[g, col] = v
    return p


def test_nomes_grupos_conferem_o_perfil():
    nomes, confere = gr.nomes_grupos(_perfil())
    assert confere and nomes[6] == "providas grandes" and nomes[1] == "vagas pequenas"
    nomes, confere = gr.nomes_grupos(_perfil({("pct_vagas", 1): 0.5}))     # o grupo 1 deixou de ser de vagas
    assert not confere and nomes == {i: f"grupo {i}" for i in range(1, 7)}
    nomes, confere = gr.nomes_grupos(_perfil().iloc[:5])                   # outro k
    assert not confere and set(nomes) == set(range(1, 6))


def test_floresta_preve_igual_duas_vezes():
    """Sem paralelo na previsão, o resultado é o mesmo bit a bit (o hash da gold.analise_clt_modelo não muda)."""
    rng = np.random.default_rng(1)
    df = pd.DataFrame({c: rng.integers(0, 2, 300) for c in rg.VARIAVEIS_CLT})
    df["log_receita"] = rng.normal(13, 1, 300)
    df["clt"] = rng.poisson(np.exp(df["log_receita"] - 12))
    a = rg.prever_floresta(df.iloc[:200], df.iloc[200:])
    b = rg.prever_floresta(df.iloc[:200], df.iloc[200:])
    assert np.array_equal(a, b)


def test_tabela_tornado_grava_no_duckdb_com_premissa_sim_nao():
    """Premissa sim/não (situações especiais) no meio das numéricas: os valores viram 1/0 e o DuckDB aceita a tabela
    (a mistura de bool e número parou a primeira carga da Etapa 2, docs/erros_ia.md, 2026-10-28)."""
    from src.analise import sensibilidade as se
    t = pd.DataFrame({"suposicao": ["taxa", "situacoes_especiais_dentro"], "rotulo": ["a", "b"], "grupo": ["x", "y"],
                      "valor_min": [0.01, False], "valor_base": [0.02, False], "valor_max": [0.035, True],
                      "premio_no_min": [1.0, 2.0], "premio_base": [2.0, 2.0], "premio_no_max": [3.0, 2.5],
                      "amplitude": [2.0, 0.5]}).astype({"valor_min": object, "valor_base": object, "valor_max": object})
    out = se.tabela_tornado(t)
    assert out["valor_max"].tolist() == [0.035, 1.0] and list(out["ordem"]) == [1, 2]
    with duckdb.connect() as con:
        con.register("t", out)
        assert con.execute("SELECT typeof(valor_min) FROM t LIMIT 1").fetchone()[0] == "DOUBLE"


def test_concentracao_e_erro_clt():
    sv = pd.DataFrame({"peso_universo": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0], "passivo": [100.0] + [10.0] * 9 + [999.0],
                       "valor_descoberto": [10.0] * 10 + [0.0]})
    c = cc.concentracao(sv, 0.1).set_index("medida")
    assert c.loc["passivo das obrigadas", "parte_do_topo"] == pytest.approx(100 / 190)
    assert c.loc["déficit esperado", "gini"] == pytest.approx(0)          # todos iguais
    tab = pd.DataFrame({"regiao_intermediaria": ["A", "A", "B"], "clt_declarado": [10, 10, 5],
                        "clt_previsto_floresta": [11, 11, 5.0], "clt_previsto_poisson": [10, 10, 5.0],
                        "clt_previsto_referencia": [9, 9, 9.0]})
    m, reg = cc.erro_clt(tab)
    assert m.loc["Poisson", "MAE"] == 0 and m.loc["floresta aleatória", "MAE"] == pytest.approx(2 / 3)
    assert reg.loc["A", "erro_total_pct"] == pytest.approx(10) and reg.loc["B", "erro_total_pct"] == 0


def test_saltos_por_semestre():
    linhas = [{"cns": "1", "ano": a, "semestre": s, "arrecadacao": 100.0, "informado": True}
              for a in (2022, 2023, 2024) for s in (1, 2)]   # a regra olha os 4 semestres anteriores
    linhas[-1]["arrecadacao"] = 10_000.0                                  # 2024-2: 100 vezes a mediana anterior
    serie = pd.DataFrame(linhas).assign(periodo=lambda d: d.ano.astype(str) + "-" + d.semestre.astype(str))
    s = cc.saltos_por_semestre(serie, 2024)
    assert list(s.index) == ["2024-1", "2024-2"]
    assert s.loc["2024-2", "saltos"] == 1 and s.loc["2024-2", "excesso"] == pytest.approx(9_900)
    assert s.loc["2024-1", "saltos"] == 0 and s.loc["2024-2", "pct_do_total"] == pytest.approx(0.99)


def test_grupos_perfil_so_agregado(monkeypatch):
    """O perfil público dos grupos (D-044): uma linha por grupo, sem CNS, com as contagens e as partes de MG."""
    from src.analise.dados import ATRIBUICOES
    sv = pd.DataFrame({"cns": list("abcdef"), "receita_ref": [1, 2, 3, 4, 5, 6.0], "clt": [1, 1, 2, 2, 3, 3.0],
                       "n_atribuicoes": [1, 1, 2, 2, 1, 1], "situacao": ["vaga", "provida"] * 3,
                       "peso_universo": [0, 1, 0, 1, 1, 1.0], "passivo": [10.0] * 6, "n_deficit": [0, 0.5] * 3,
                       "valor_descoberto": [0, 2.0] * 3, **{a: [True, False] * 3 for a in ATRIBUICOES}})
    monkeypatch.setattr(tabelas.dados, "serventias", lambda con: sv)
    tab = pd.DataFrame({"cns": list("abcdef"), "grupo": [1, 1, 2, 2, 2, 2], "nome_grupo": ["x", "x"] + ["y"] * 4,
                        "grupo_alvo": [False, False] + [True] * 4})
    p = tabelas.grupos_perfil(None, tab).set_index("grupo")
    assert "cns" not in p.columns and list(p.n_serventias) == [2, 4]
    assert p.loc[2, "nome_grupo"] == "y" and p.loc[2, "grupo_alvo"]
    assert p.loc[2, "pct_obrigadas_mg"] == pytest.approx(3 / 4) and p.loc[1, "pct_vagas"] == pytest.approx(0.5)
    assert p.loc[2, "pct_passivo_obrigadas_mg"] == pytest.approx(30 / 40)


def test_reconciliacao_arredonda_a_10_casas():
    """D-044: a correlação mudava no 15º dígito conforme a ordem das linhas; com 10 casas, o hash público é o mesmo."""
    from src.quality import reconciliacao as rc
    a = rc._linha("c", "x", 0.9123456789012345, None, None, 0.5, "minimo")
    b = rc._linha("c", "x", 0.9123456789012373, None, None, 0.5, "minimo")
    assert a == b and a["indicador"] == 0.9123456789 and a["valor_b"] is None
    d = rc._linha("d", "x", 105, "y", 100, 0.1)
    assert d["indicador"] == pytest.approx(0.05) and d["status"] == "ok"


def test_carregar_le_do_banco_quando_existe(tmp_path, monkeypatch):
    banco = tmp_path / "x.duckdb"
    with duckdb.connect(str(banco)) as con:
        con.execute("CREATE SCHEMA gold")
        for t in cc.NOMES_09:
            con.execute(f"CREATE TABLE gold.{t} AS SELECT 1 AS x")
    monkeypatch.setattr(tabelas, "construir", lambda con: pytest.fail("não devia recalcular"))
    with duckdb.connect(str(banco), read_only=True) as con:
        tabs, origem = cc.carregar(con)
    assert set(tabs) == set(cc.NOMES_09) and set(NOMES_ANALISE) <= set(tabs) and origem.startswith("banco")
    with duckdb.connect(str(banco)) as con:
        con.execute("DROP TABLE gold.analise_regras")
    monkeypatch.setattr(tabelas, "construir", lambda con: {"calculado": pd.DataFrame()})
    with duckdb.connect(str(banco), read_only=True) as con:
        assert cc.carregar(con)[1].startswith("calculadas")


def test_etapa_analise_grava_as_tabelas_sem_parquet(tmp_path, monkeypatch):
    """A etapa grava cada tabela de tabelas.construir no gold; com exportar_parquet=False (definido pelo gold), não
    toca em data/gold."""
    import pipeline
    from src.transform import gold
    monkeypatch.setattr(tabelas, "construir", lambda con: {t: pd.DataFrame({"a": [1, 2]}) for t in NOMES_ANALISE})
    monkeypatch.setattr(gold, "_EXPORTAR_PARQUET", False)
    monkeypatch.setattr(gold, "GOLD", tmp_path / "nao_deve_existir")
    with duckdb.connect(str(tmp_path / "x.duckdb")) as con:
        con.execute("CREATE SCHEMA gold")
        pipeline.etapa_analise(con)
        feitas = {t for (t,) in con.execute("SELECT table_name FROM information_schema.tables "
                                            "WHERE table_schema = 'gold'").fetchall()}
    assert feitas == set(NOMES_ANALISE) and not (tmp_path / "nao_deve_existir").exists()


@pytest.mark.dados_reais
def test_tabelas_rapidas_e_numeros_oficiais(_copia_real):
    """Numa CÓPIA do banco: os números oficiais do 09 são os do gold, e as tabelas rápidas repetem os notebooks 03,
    06 e 08 (10 regras; MAE da floresta 1,86; P5–P95 do prêmio R$ 215–687 mil com as premissas v3, D-046; com a v2,
    R$ 206–736 mil)."""
    with duckdb.connect(str(_copia_real["copia"]), read_only=True) as con:
        of = cc.numeros_oficiais(con)
        premio = con.execute("SELECT mercado_premio_emitido FROM gold.fato_mercado_uf WHERE nivel = 'base' AND "
                             "regra_classe = 'v2' AND cenario_stf = 'mantem'").fetchone()[0]
        regras = tabelas.regras(con)
        clt = tabelas.clt_modelo(con)
        tor, mc = tabelas.tornado_e_monte_carlo(con)
    assert of.loc["prêmio anual", "base"] == premio and len(of) == 10
    assert of.loc["teto teórico", "base"] == pytest.approx(of.loc["passivo (obrigadas)", "base"] * 0.02)
    assert len(regras) == 10 and (regras.entao == "obrigada").all()
    assert cc.erro_clt(clt)[0].loc["floresta aleatória", "MAE"] == pytest.approx(1.86, abs=0.005)
    p = mc[(mc.variante == "independentes") & (mc.medida == "premio")].iloc[0]
    assert p.p05 == pytest.approx(215_000, rel=1e-3) and p.p95 == pytest.approx(687_100, rel=1e-3)
    assert tor.iloc[0].suposicao == "taxa" and len(tor) == 11


@pytest.mark.dados_reais
def test_sensibilidade_metodo_repete_o_notebook_08(_copia_real):
    """Numa CÓPIA do banco: a gold.analise_sensibilidade_metodo (D-042, D-044) tem a base igual aos números oficiais e
    as variações do notebook 08 (receita líquida: universo −20%; T5 +0,6%; T6 −1,6%; MG inteiro +5,9% no passivo) e a
    regra do salto (D-046: −11,3 obrigadas, como no notebook 01). O prêmio da receita líquida cai 2,7% com as premissas v3
    (−8,5% com a v2, no notebook 08)."""
    with duckdb.connect(str(_copia_real["copia"]), read_only=True) as con:
        s = tabelas.sensibilidade_metodo(con).set_index("chave")
        of = cc.numeros_oficiais(con)
    assert s.loc["base", "mercado_premio_emitido"] == pytest.approx(of.loc["prêmio anual", "base"])
    assert s.loc["receita_liquida", "n_universo"] == pytest.approx(893.6, abs=0.05)
    assert s.loc["receita_liquida", "var_mercado_premio_emitido"] == pytest.approx(-0.027, abs=0.0005)
    assert s.loc["sem_saltos", "n_universo"] - s.loc["base", "n_universo"] == pytest.approx(-11.3, abs=0.05)
    assert s.loc["t5_salario_estimado", "var_passivo_todas"] == pytest.approx(0.006, abs=0.0005)
    assert s.loc["t6_encolhimento", "var_passivo_todas"] == pytest.approx(-0.016, abs=0.0005)
    assert s.loc["sem_regiao", "var_passivo_todas"] == pytest.approx(0.059, abs=0.0005)


@pytest.mark.dados_reais
def test_sensibilidade_metodo_sem_o_bi_nao_para(_copia_real, tmp_path, monkeypatch):
    """O CSV do BI é opcional (fica no bronze, fora do pacote público): sem ele, só a linha da receita líquida sai, com
    aviso, e o pipeline a partir do silver não para (docs/erros_ia.md, 2026-10-28)."""
    monkeypatch.setattr(tabelas.dados, "arquivo_bi", lambda: tmp_path / "nao_existe.csv")
    with duckdb.connect(str(_copia_real["copia"]), read_only=True) as con, pytest.warns(UserWarning, match="BI"):
        s = tabelas.sensibilidade_metodo(con)
    assert list(s.chave) == ["base", "sem_saltos", "t5_salario_estimado", "t6_encolhimento", "sem_regiao"]
