"""src/analise/previsao.py (notebook 07: previsão da arrecadação e projeção do mercado). Dados SINTÉTICOS, salvo o
teste `dados_reais`, que roda numa cópia do banco."""
import json

import duckdb
import numpy as np
import pandas as pd
import pytest
import yaml

from src import estado
from src.analise import RAIZ, previsao as pv
from src.model.simulador import resumo_por_totais, totais
from src.model.universo import universo
from src.motor import premissas_nivel

CENARIOS = yaml.safe_load((RAIZ / "config" / "cenarios_stf.yaml").read_text(encoding="utf-8"))
LIMITES = {"classe_1_max": 300_000.0, "classe_2_max": 1_500_000.0}


def _serie_mg(n: int = 30, cresc: float = 0.05, efeito_2: float = 0.15) -> pd.Series:
    """Sintética: log-linear exata, começando em 2007-1, com o 2º semestre `efeito_2` acima (no log)."""
    t = np.arange(n)
    idx = [f"{2007 + i // 2}-{i % 2 + 1}" for i in range(n)]
    return pd.Series(np.exp(20 + cresc * t + efeito_2 * (t % 2)), index=idx)


def test_proximos_periodos_e_tendencia_exata():
    assert pv.proximos_periodos("2025-2", 3) == ["2026-1", "2026-2", "2027-1"]
    y = _serie_mg()
    prev = pv.prever(y, pv.PRINCIPAL, 4)
    certo = _serie_mg(34).iloc[-4:]
    assert list(prev.index) == list(certo.index)
    assert prev.to_numpy() == pytest.approx(certo.to_numpy(), rel=1e-9)


def test_origem_movel_sem_erro_na_serie_exata():
    y = _serie_mg(38)            # 2007-1 a 2025-2
    tab, err = pv.origem_movel(y, {pv.PRINCIPAL: pv.METODOS[pv.PRINCIPAL], pv.REFERENCIA: pv.METODOS[pv.REFERENCIA]})
    assert tab.loc[pv.PRINCIPAL, "MAPE_origem_movel_pct"] == pytest.approx(0, abs=1e-8)
    assert tab.index[0] == pv.PRINCIPAL and tab.loc[pv.REFERENCIA, "MAPE_origem_movel_pct"] > 1
    assert len(err) == 2 * 5 * 4                       # 2 métodos × 5 origens × 4 horizontes
    assert set(err["periodo"]) <= set(y.index)        # só compara com o que já aconteceu


def test_faixa_multiplica_pelos_erros():
    prev = pd.Series([100.0, 200.0], index=["2026-1", "2026-2"])
    f = pv.faixa(prev, pd.Series([-0.2, -0.1, 0.0, 0.1, 0.2]), [0.0, 1.0])
    assert f["p10"].tolist() == pytest.approx([80, 160]) and f["p90"].tolist() == pytest.approx([120, 240])


def test_quebra_de_nivel_recupera_o_salto():
    y = _serie_mg(38)
    pos = list(y.index).index("2024-1")
    y.iloc[pos:] *= 1.2
    q = pv.quebra_de_nivel(y, "2024-1")
    assert q["salto"] == pytest.approx(0.2, rel=1e-6) and q["semestres_depois"] == 4
    prev = pv.prever(y, q["funcao"], 2)
    assert prev.to_numpy() == pytest.approx(_serie_mg(40).iloc[-2:].to_numpy() * 1.2, rel=1e-6)


def test_completar_semestre_so_quem_nao_informou():
    s = pd.DataFrame({"cns": ["a", "b", "c", "a", "b", "c"], "periodo": ["2025-1"] * 3 + ["2026-1"] * 3,
                      "arrecadacao": [100.0, 200.0, 50.0, 120.0, 240.0, 0.0],
                      "informado": [True, True, True, True, True, False]})
    out, info = pv.completar_semestre(s, "2026-1", "2025-1")
    assert info["serventias"] == 1 and info["crescimento"] == pytest.approx(1.2)
    assert out.loc[(out.cns == "c") & (out.periodo == "2026-1"), "arrecadacao"].item() == pytest.approx(60)
    assert out.loc[out.cns != "c", "arrecadacao"].tolist() == s.loc[s.cns != "c", "arrecadacao"].tolist()


def test_fatores_e_erros_anuais():
    y = pd.Series([10.0, 10.0], index=["2025-1", "2025-2"])
    prev = pd.Series([11.0, 11.0, 12.0, 13.0], index=["2026-1", "2026-2", "2027-1", "2027-2"])
    assert pv.fatores_ano(prev, y, 2025).to_dict() == pytest.approx({2026: 1.1, 2027: 1.25})
    err = pd.DataFrame({"metodo": "m", "origem": "o", "horizonte": [1, 2, 3, 4], "previsto": [10.0, 10, 10, 10],
                        "real": [11.0, 9, 12, 12]})
    ea = pv.erros_anuais(err, "m").set_index("ano_frente")["erro_rel"]
    assert ea.to_dict() == pytest.approx({1: 0.0, 2: 0.2})


def test_desvios_tiram_saltos_e_ficam_na_banda():
    media = pd.DataFrame({2020: [300e3, 300e3, 300e3, 10e3], 2021: [330e3, 600e3, 300e3, 20e3]},
                         index=["igual", "dobra", "salto", "longe"])
    saltos = pd.DataFrame({"cns": ["salto"], "ano": [2021]})
    d = pv.desvios_individuais(media, saltos, [2020], 1, 300e3, banda=3).set_index("cns")["desvio"]
    assert set(d.index) == {"igual", "dobra"}          # "salto" teve salto; "longe" fica fora da banda
    g = np.log(media[2021].sum() / media[2020].sum())
    assert d["dobra"] == pytest.approx(np.log(2) - g) and d["igual"] == pytest.approx(np.log(1.1) - g)


def test_sortear_receitas_mantem_vazio_e_fator():
    rng = np.random.default_rng(0)
    r = pv.sortear_receitas(pd.Series([100.0, np.nan, 50.0]), np.array([1.0, 2.0]), np.array([0.0]), rng)
    assert r.shape == (2, 3) and np.isnan(r[:, 1]).all()
    assert r[1, [0, 2]].tolist() == pytest.approx([200, 100])
    f = pv.sortear_fatores(1.1, np.array([-0.1, 0.1]), 1000, rng)
    assert set(np.round(f, 6)) == {round(1.1 * 0.9, 6), round(1.1 * 1.1, 6)}


def _serv() -> pd.DataFrame:
    """Sintético: saída do motor na base (classe, passivo, situação)."""
    s = pd.DataFrame({"cns": list("abcdef"), "situacao_juridica": ["PROVIDO"] * 4 + ["VAGO", "PROVIDO"],
                      "receita_ref": [100e3, 290e3, 800e3, 3e6, 500e3, np.nan], "clt": [1, 2, 5, 20, 3, 1],
                      "passivo": [1e4, 3e4, 1e5, 9e5, 5e4, 1e4]})
    p = premissas_nivel(estado.ler_semente(), "base", 0.5)
    return universo(s, LIMITES, p, LIMITES)


def test_mercado_sem_mudanca_e_o_modelo():
    serv = _serv()
    m = pv.mercado(serv, serv["receita_ref"].to_numpy(), LIMITES, estado.ler_semente(), CENARIOS)
    p = premissas_nivel(estado.ler_semente(), "base", 0.5)     # 2 das 4 não vagas com classe conhecida fora da 1
    r = resumo_por_totais(totais(universo(serv, LIMITES, p, LIMITES)), p, CENARIOS, "mantem")
    assert m["mercado_premio_emitido"] == pytest.approx(r["mercado_premio_emitido"])
    assert m["peso_indeterminada"] == pytest.approx(0.5)
    assert (m["subidas"], m["descidas"], m["acima_do_limite"], m["providas_acima"]) == (0, 0, 3, 2)


def test_mercado_conta_subidas_descidas_e_consolidacao():
    serv = _serv()
    rec = np.array([320e3, 400e3, 250e3, 3e6, 500e3, np.nan])   # a sobe até 10% acima; b sobe; c desce
    m = pv.mercado(serv, rec, LIMITES, estado.ler_semente(), CENARIOS)
    assert (m["subidas"], m["descidas"], m["subidas_ate_consolidacao"], m["classe_2_para_3"]) == (2, 1, 1, 0)
    rec[2] = 2e6                                                  # c passa da Classe 2 para a 3
    assert pv.mercado(serv, rec, LIMITES, estado.ler_semente(), CENARIOS)["classe_2_para_3"] == 1
    corr = pv.limites_corrigidos(LIMITES, 0.10, 2)
    assert corr["classe_1_max"] == pytest.approx(363e3) and corr["classe_2_max"] == pytest.approx(1.815e6)
    assert pv.mercado(serv, rec, corr, estado.ler_semente(), CENARIOS)["subidas"] == 1


def test_inflacao_recente():
    ind = pd.DataFrame({"ano_mes": [202501 + i for i in range(9)], "numero_indice": [100.0 + i for i in range(9)]})
    v, mes = pv.inflacao_recente(ind, 4)
    assert v == pytest.approx(108 / 104 - 1) and mes == 202509


def test_tabela_previsao_rotula_projecao():
    a = pd.DataFrame({"periodo": ["2026-1"], "variante": ["x"], "p10": [1.0], "central": [2.0], "p90": [3.0],
                      "realizado": [2.5]})
    m = pd.DataFrame({"ano": [2026], "variante": ["x"], "cenario_limite": ["fixo"], "medida": ["n_universo"],
                      "p10": [1.0], "central": [2.0], "p90": [3.0]})
    t = pv.tabela_previsao(a, m)
    assert list(t.columns) == ["bloco", "periodo", "variante", "cenario_limite", "medida", "p10", "central", "p90",
                               "realizado", "rotulo"]
    assert t["rotulo"].eq("projeção").all() and t["periodo"].tolist() == ["2026-1", "2026"]


@pytest.mark.dados_reais
def test_previsao_reproduz_o_t2_e_a_base(_copia_real):
    """Numa CÓPIA do banco: a origem móvel repete o MAPE do T2, e o mercado sem mudança na receita dá o prêmio
    oficial."""
    from src.analise import dados
    from src.motor import calcular_serventias
    from src.transform.gold import carregar_insumos
    sem = estado.ler_semente()
    lim = yaml.safe_load((RAIZ / "config" / "regras_classificacao.yaml").read_text(encoding="utf-8"))["versoes"]["v2"]
    with duckdb.connect(str(_copia_real["copia"]), read_only=True) as con:
        peso = con.execute("SELECT peso_classe_indeterminada_base FROM gold.execucao WHERE regra_classe = 'v2'"
                           ).fetchone()[0]
        premio = con.execute("SELECT mercado_premio_emitido FROM gold.fato_mercado_uf WHERE nivel = 'base' AND "
                             "regra_classe = 'v2' AND cenario_stf = 'mantem'").fetchone()[0]
        serie, ins = dados.serie_arrecadacao(con), carregar_insumos(con)
    y = pv.serie_mg(serie).loc[:"2025-2"]
    tab, _ = pv.origem_movel(y)
    t2 = json.loads((RAIZ / "docs/qa/analises/testes_metodos_resultados.json").read_text(encoding="utf-8"))
    t2 = {r["metodo"]: r for r in t2["T2_previsao_arrecadacao_MG"]["tabela"]}
    for m in tab.index:
        assert tab.loc[m, "MAPE_origem_movel_pct"] == pytest.approx(t2[m]["MAPE_origem_movel_pct"], abs=1e-3)
    p = premissas_nivel(sem, "base", peso)
    serv = calcular_serventias(ins, p, lim["limites"], limites_faixa=lim["limites"])[0]
    m = pv.mercado(serv, serv["receita_ref"].to_numpy(), lim["limites"], sem, CENARIOS)
    assert m["mercado_premio_emitido"] == pytest.approx(premio) and m["subidas"] == 0
