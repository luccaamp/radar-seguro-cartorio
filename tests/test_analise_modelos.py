"""src/analise dos notebooks 03, 04, 05 e 05c (padrões, grupos, classificação e vacância), 06 (regressão) e 08
(sensibilidade e concentração). Dados SINTÉTICOS, salvo o teste `dados_reais`, que roda numa cópia do banco."""
import json

import duckdb
import numpy as np
import pandas as pd
import pytest
import yaml

from src import estado
from src.analise import (RAIZ, classificacao as cl, dados, estatistica, grupos as gr, padroes, regressao,
                         sensibilidade, vacancia as va)
from src.model.premissas import resolver
from src.model.simulador import resumo_por_totais

CENARIOS = yaml.safe_load((RAIZ / "config" / "cenarios_stf.yaml").read_text(encoding="utf-8"))
TOTAIS = {"passivo_ponderado_classe_2": 6.0e7, "passivo_ponderado_classe_3": 1.7e8,   # sintéticos
          "peso_com_passivo_classe_2": 700.0, "peso_com_passivo_classe_3": 350.0, "n_serventias_ativas": 10,
          "clt": 50.0, "passivo_todas": 3e8, "n_universo": 1000.0, "n_indeterminadas_universo": 0,
          "passivo_universo": 2.3e8}


def _serventias(n_por_tipo: int = 40) -> pd.DataFrame:
    """Sintético: 3 tipos de cartório. RI grande provido (obrigado), Notas médio provido Classe 2 e RCPN pequeno vago."""
    linhas = []
    tipos = [("ri", 15, "3", "PROVIDO", 3e6), ("notas", 4, "2", "PROVIDO", 5e5), ("rcpn", 1, "1", "VAGO", 5e4)]
    for t, clt, classe, sit, rec in tipos:
        for i in range(n_por_tipo):
            linhas.append({"cns": f"{t}{i:03d}", **{a: a == t for a in ["notas", "rcpn", "ri", "rtd", "rcpj", "protesto"]},
                           "clt": clt + i % 3, "classe": classe, "situacao": {"PROVIDO": "provida", "VAGO": "vaga"}[sit],
                           "regiao_intermediaria": "Norte" if i % 2 else "Sul", "receita_ref": rec * (1 + i / 100),
                           "n_atribuicoes": 1, "peso_universo": float(classe != "1" and sit == "PROVIDO"),
                           "passivo": clt * 1e4, "n_deficit": 0.3 * (classe != "1"), "valor_descoberto": clt * 1e3 * (classe != "1"),
                           "populacao": 1e4 * (1 + i)})
    linhas.append({**linhas[0], "cns": "ind001", "classe": "indeterminada"})   # sai da mineração
    return pd.DataFrame(linhas)


# --------------------------------------------------------------------------------------------------- padrões (03)
def test_transacoes_itens_e_obrigada():
    t = padroes.transacoes(_serventias(), cortes=[0, 2, 9])
    assert "ind001" not in t.index and len(t) == 120
    assert t.loc["ri000", ["RI", "porte 10+ CLT", "classe 3", "situação provida", "região Sul", "obrigada"]].all()
    assert not t.loc["rcpn000", "obrigada"] and t.loc["rcpn000", "porte 1 a 2 CLT"]
    porte = [c for c in t if c.startswith("porte")]
    assert (t[porte].sum(axis=1) == 1).all()   # cada serventia tem exatamente uma faixa de porte


def test_medidas_da_regra_e_referencia():
    t = padroes.transacoes(_serventias(), cortes=[0, 2, 9])
    assert padroes.confianca(t, frozenset(["RI"])) == 1.0
    assert padroes.confianca(t, frozenset()) == pytest.approx(80 / 120)
    ref = padroes.frequencia_por_item(t, ["RI", "RCPN"]).set_index("item")
    assert ref.loc["RI", "frequencia"] == 1.0 and ref.loc["RCPN", "com_alvo"] == 0
    todas = padroes.regras(t, suporte_min=0.1, confianca_min=0.5, max_itens=3)
    texto = [" + ".join(sorted(a)) for a in todas.antecedentes]
    assert texto == sorted(texto)   # ordem fixa, que não depende do hash dos textos na sessão
    r = todas[(todas.consequente == "obrigada") & (todas.antecedentes == frozenset(["RI"]))].iloc[0]
    assert r.suporte == pytest.approx(40 / 120) and r.confianca == 1.0 and r.lift == pytest.approx(1.5)


def test_regras_alvo_tiram_definicao_e_regra_sem_ganho():
    t = padroes.transacoes(_serventias(), cortes=[0, 2, 9])
    todas = padroes.regras(t, suporte_min=0.1, confianca_min=0.5, max_itens=3)
    alvo = padroes.regras_alvo(t, todas, melhoria_min=0.02)
    assert alvo.antecedentes.apply(padroes.sem_definidores).all()
    assert frozenset(["RI"]) not in set(alvo.antecedentes)              # é a própria referência: ganho = 1
    assert frozenset(["RI", "região Sul"]) not in set(alvo.antecedentes)  # a região não melhora a confiança
    assert frozenset(["porte 10+ CLT"]) in set(alvo.antecedentes)         # sem atribuição: referência = 2/3


def test_tabela_regras_so_estaveis_e_na_ordem():
    t = padroes.transacoes(_serventias(), cortes=[0, 2, 9])
    todas = padroes.regras(t, suporte_min=0.1, confianca_min=0.5, max_itens=3)
    alvo = padroes.regras_alvo(t, todas, melhoria_min=0.02)
    vezes = pd.Series({a: 2 for a in alvo.antecedentes})
    vezes.iloc[0] = 1
    tab = padroes.tabela_regras(alvo, t, vezes, n_reamostragens=2, n_principais=10)
    assert len(tab) == len(alvo) - 1 and tab.posicao.tolist() == list(range(1, len(tab) + 1))
    assert (tab.reamostragens_com_a_regra == 2).all() and tab.lift.is_monotonic_decreasing
    assert {"se", "entao", "suporte", "confianca", "lift", "referencia", "ganho_sobre_referencia"} <= set(tab.columns)


def test_estabilidade_repete_com_a_mesma_semente():
    t = padroes.transacoes(_serventias(), cortes=[0, 2, 9])
    p = dict(suporte_min=0.1, confianca_min=0.5, max_itens=3, melhoria_min=0.02)
    a = padroes.estabilidade(t, n=2, fracao=0.8, semente=1, **p)
    assert a.equals(padroes.estabilidade(t, n=2, fracao=0.8, semente=1, **p)) and a.max() <= 2


# ---------------------------------------------------------------------------------------------------- grupos (04)
def test_grupos_separam_os_tipos_e_acham_o_alvo():
    sv = _serventias()
    x = gr.matriz(sv)
    assert "ind001" in x.index and list(x.columns) == gr.VARIAVEIS
    z = gr.padronizar(x)
    assert np.allclose(z.mean(axis=0), 0)
    r = gr.ordenar_por_receita(gr.kmeans(z, 3, semente=1, n_init=5), x.log_receita)
    g = pd.Series(r, index=x.index)
    assert g[x.index.str.startswith("rcpn")].eq(1).all() and g[x.index.str.startswith("ri")].eq(3).all()
    p = gr.perfil(sv, g)
    assert p.serventias.sum() == len(x) and p.loc[1, "pct_vagas"] == 1.0 and gr.grupo_alvo(p) == 3
    tab = gr.tabela_grupos(g, {1: "a", 2: "b", 3: "c"}, 3, 3, 1)
    assert tab.grupo_alvo.sum() == (g == 3).sum() and set(tab.columns) == {"cns", "grupo", "nome_grupo", "grupo_alvo",
                                                                           "k", "semente"}


def test_escolha_k_tem_silhueta_e_ward():
    z = gr.padronizar(gr.matriz(_serventias()))
    e = gr.escolha_k(z, 2, 4, semente=1)
    assert e.k.tolist() == [2, 3, 4] and e.silhueta.between(-1, 1).all() and e.inercia.is_monotonic_decreasing
    assert e.loc[e.k == 3, "rand_ajustado_kmeans_ward"].iloc[0] == pytest.approx(1)   # 3 tipos bem separados


# ------------------------------------------------------------------------------------------- classificação (05)
def test_metricas_matriz_de_confusao():
    m = cl.metricas(np.array([0.9, 0.8, 0.3, 0.6, 0.1]), np.array([1, 0, 1, 1, 0]), limiar=0.5)
    assert (m["vp"], m["fp"], m["fn"], m["vn"]) == (2, 1, 1, 1)
    assert m["precisao"] == pytest.approx(2 / 3) and m["recall"] == pytest.approx(2 / 3)
    assert m["Brier"] == pytest.approx(np.mean([0.01, 0.64, 0.49, 0.16, 0.01])) and m["previstos"] == pytest.approx(2.7)


def test_base_vacancia_sem_variaveis_que_vazam():
    x, y = cl.base_vacancia(_serventias())
    assert y.sum() == 40 and len(x) == 121
    proibidas = {"peso_universo", "motivo", "data_situacao", "n_deficit", "valor_descoberto", "passivo", "classe"}
    assert not proibidas & set(x.columns)


def _painel_sintetico():
    """Sintético: 200 serventias de 2010 a 2025; variam de −2% a +10% ao ano a partir de R$ 80 mil a 290 mil."""
    rng = np.random.default_rng(0)
    cns = [f"S{i:03d}" for i in range(200)]
    base = rng.uniform(80_000, 290_000, 200)
    cresc = rng.uniform(0.98, 1.10, 200)
    media = pd.DataFrame({a: base * cresc ** (a - 2010) for a in range(2010, 2026)}, index=cns)
    info = pd.DataFrame({"n_atribuicoes": 1.0, **{a: 0 for a in ["notas", "rcpn", "ri", "rtd", "rcpj", "protesto"]},
                         "log_pop": 9.0}, index=cns)
    return media, media * 1.1, info


def test_casos_subida_so_usam_o_passado():
    media, maximo, info = _painel_sintetico()
    c = cl.casos_subida(media, maximo, info, 2015, 300_000, horizonte=1)
    assert (np.exp(c.log_m1) <= 300_000).all()
    assert c.y.tolist() == (media.loc[c.cns, 2015] > 300_000).astype(int).tolist()
    assert c.log_m1.tolist() == pytest.approx(np.log(media.loc[c.cns, 2014]).tolist())
    c2 = cl.casos_subida(media, maximo, info, 2027, 300_000, horizonte=2, com_resposta=False)
    assert c2.log_m1.tolist() == pytest.approx(np.log(media.loc[c2.cns, 2025]).tolist()) and c2.y.isna().all()


def test_prever_subidas_nao_usa_o_futuro():
    media, maximo, info = _painel_sintetico()
    painel = cl.painel_subida(media, maximo, info, range(2012, 2026), 300_000)
    r = cl.prever_subidas(painel, painel[painel.ano >= 2024], horizonte=1, n_cal=2, semente=1)
    assert r["fim_treino"] == 2023 and r["anos_cal"] == [2022, 2023]
    assert len(r["p"]) == len(r["p_recal"]) and ((r["p_recal"] >= 0) & (r["p_recal"] <= 1)).all()
    painel2 = cl.painel_subida(media, maximo, info, range(2013, 2026), 300_000, horizonte=2)
    r2 = cl.prever_subidas(painel2, painel2[painel2.ano >= 2024], horizonte=2, n_cal=2, semente=1)
    assert r2["fim_treino"] == 2022 and r2["anos_cal"] == [2021, 2022]


def test_recalibracao_corrige_probabilidade_baixa_demais():
    rng = np.random.default_rng(0)
    p = rng.uniform(0.05, 0.5, 4000)
    y = (rng.random(4000) < np.clip(2 * p, 0, 1)).astype(int)    # sintético: a verdade é o dobro do previsto
    corrigida = cl.aplicar(cl.recalibrador(p, y), p)
    assert corrigida.sum() == pytest.approx(y.sum(), rel=0.03) and p.sum() < 0.6 * y.sum()


def test_faixas_da_contagem():
    lo, c, hi = cl.faixa_por_erros(100.0, pd.Series([0.5, 1.0, 1.5]), faixa=[0.0, 1.0])
    assert (lo, c, hi) == (50.0, 100.0, 150.0)
    lo, c, hi = cl.faixa_contagem(np.full(500, 0.2), np.r_[np.ones(100), np.zeros(400)], np.full(50, 0.2), n=50,
                                  faixa=[0.1, 0.9], semente=1)
    assert lo <= c <= hi and c == pytest.approx(10, rel=0.05)


def test_tabela_subidas_colunas():
    t = cl.tabela_subidas([{"ano": 2026, "horizonte": 1, "recorte": "todas", "abaixo_do_limite_no_ano_base": 10,
                            "p10": 1.0, "esperado": 2.0, "p90": 3.0, "modelo": "m", "anos_recalibracao": "2024–2025"}])
    assert t.columns.tolist()[:4] == ["ano", "horizonte", "recorte", "abaixo_do_limite_no_ano_base"] and len(t) == 1


# ------------------------------------------------------------------------------------------- vacância (05c)
def _cadastro() -> pd.DataFrame:
    """Sintético: 10 providas desde 2015; 3 vagaram (2024, 2025 e 2025, esta num lote de 2 com outra vaga);
    1 vaga desde 2020 provida em 2025; 1 inativa."""
    linhas = [(f"P{i}", "PROVIDO", "2015-03-01") for i in range(10)]
    linhas += [("V1", "VAGO", "2024-05-01"), ("V2", "VAGO", "2025-02-01"), ("V3", "VAGO", "2025-06-01"),
               ("V4", "VAGO", "2025-06-01"), ("N1", "PROVIDO", "2025-08-01")]
    df = pd.DataFrame(linhas, columns=["cns", "situacao_juridica", "data_decisao"]).assign(uf="MG", status="Ativo")
    df = pd.concat([df, pd.DataFrame([{"cns": "X1", "situacao_juridica": "VAGO", "data_decisao": "2025-01-01",
                                       "uf": "MG", "status": "Inativo"}])], ignore_index=True)
    df["data_decisao"] = pd.to_datetime(df["data_decisao"])
    return df


def test_estoque_e_taxa_de_vacancia():
    cad = _cadastro()
    est = va.estoque_providas(cad, 2025)
    assert set(cad.cns[est]) == {f"P{i}" for i in range(10)} | {"V2", "V3", "V4"}   # N1 estava vaga; V1 já vagara
    t = va.taxa_vacancia(cad, 2025).iloc[0]
    assert (t.providas_no_inicio, t.vacancias) == (13, 3) and t.taxa == pytest.approx(3 / 13)
    lote = va.em_lote(cad, minimo=2)
    assert set(cad.cns[lote]) == {"V3", "V4"} | {f"P{i}" for i in range(10)}
    sem = va.taxa_vacancia(cad, 2025, fora=lote).iloc[0]
    assert (sem.providas_no_inicio, sem.vacancias) == (13, 1)   # o lote sai das vacâncias, não do estoque
    por = va.taxa_vacancia(cad, 2025, grupo=pd.Series(np.where(cad.cns.str.startswith("V"), "a", "b"), index=cad.index))
    assert por.loc["a", "vacancias"] == 3 and por.loc["b", "vacancias"] == 0


def test_taxas_por_ano_e_decisoes():
    cad = _cadastro()
    t = va.taxas_por_ano(cad, range(2024, 2026), sem_lote=False).set_index("ano")
    assert t.loc[2024, "vacancias"] == 1 and t.loc[2024, "providas_no_inicio"] == 14
    d = va.decisoes_por_ano(cad)
    assert d.loc[2025, "VAGO"] == 3 and d.loc[2025, "PROVIDO"] == 1 and d.values.sum() == 15   # a inativa fica fora
    assert va.anos_desde(pd.Series(pd.to_datetime(["2024-10-17"])), pd.Timestamp("2026-10-17")).iloc[0] == \
        pytest.approx(2, abs=0.01)


def test_cadastro_cnj_nao_le_campos_pessoais(tmp_path, monkeypatch):
    """Bronze SINTÉTICO: o nome do responsável e os contatos não saem da leitura."""
    pasta = tmp_path / "data" / "bronze" / "cnj_justica_aberta" / "2026-10-17"
    pasta.mkdir(parents=True)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "escopo.yaml").write_text("snapshots:\n  cnj_justica_aberta: '2026-10-17'\n",
                                                       encoding="utf-8")
    reg = {"cns": "000001", "uf": "MG", "status": "Ativo", "email": "x@y", "telefone": "1",
           "situacao_juridica_cartorio": {"descricao": "VAGO", "data_decisao": "2025-02-01"},
           "responsavel": {"nome": "Pessoa Sintética", "data_ingresso": "Invalid DateTime",
                           "situacao_juridica_responsavel": "Interino"}, "substitutos": "Outra Pessoa"}
    (pasta / "serventias_MG.json").write_text(json.dumps({"meta": {}, "data": [reg]}), encoding="utf-8")
    (pasta / "serventias_MG.meta.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(dados, "RAIZ", tmp_path)
    df = dados.cadastro_cnj()
    assert len(df) == 1 and df.loc[0, "data_decisao"] == pd.Timestamp("2025-02-01") and pd.isna(df.loc[0, "data_ingresso"])
    assert not {"nome", "substitutos", "email", "telefone"} & set(df.columns)
    assert "Pessoa" not in df.to_string()



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
    """Numa CÓPIA do banco: o motor refeito pelo notebook 08 dá o prêmio oficial, e o tornado repete o do T7, que foi
    feito com as premissas v2 (D-046 trocou a semente; o método do tornado é o mesmo)."""
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
    sem2 = yaml.safe_load((RAIZ / "config" / "premissas" / "premissas_v002.yaml").read_text(encoding="utf-8"))
    t = sensibilidade.tornado(simulador.totais(sv), sensibilidade.faixas_suposicoes(sem2), premissas_nivel(sem2, "base", peso),
                              CENARIOS)
    t7 = json.loads((RAIZ / "docs/qa/analises/testes_metodos_resultados.json").read_text(encoding="utf-8"))
    taxa = next(r for r in t7["T7_incerteza_premio"]["tornado"] if r["suposicao"] == "taxa")
    assert t.set_index("suposicao").loc["taxa", "premio_no_min"] / 1e3 == pytest.approx(taxa["min_mil"], abs=0.1)
    assert t.set_index("suposicao").loc["taxa", "premio_no_max"] / 1e3 == pytest.approx(taxa["max_mil"], abs=0.1)
