"""src/analise dos notebooks 03, 04, 05 e 05c (padrões, grupos, classificação e vacância). Dados SINTÉTICOS."""
import json

import numpy as np
import pandas as pd
import pytest

from src.analise import classificacao as cl, dados, grupos as gr, padroes, vacancia as va


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
