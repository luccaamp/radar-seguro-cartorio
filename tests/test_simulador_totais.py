"""Simulador por totais (modo demonstração, src/model/simulador.py) = motor completo (src/motor.py).

- Com dados SINTÉTICOS (suíte padrão): resumo_por_totais(totais(s)) == resumo_mercado(deficit(s)) nas premissas
  padrão e em 5 combinações aleatórias das premissas de seguro e do cenário do STF.
- Com os dados reais (dados_reais): o motor completo, rodado do zero sobre o silver, contra as tabelas públicas
  gold.simulador_* lidas do banco, na variante padrão e em 5 combinações aleatórias (passivo da grade + seguro).
"""
import math
import random

import duckdb
import numpy as np
import pandas as pd
import pytest
import yaml

from src.model import simulador
from src.model.mercado import deficit
from src.motor import resumo_mercado

TOL = 1e-9   # só a ordem das somas muda: diferença de arredondamento do ponto flutuante


def iguais(a: dict, b: dict) -> list[str]:
    return [k for k in a if not math.isclose(float(a[k]), float(b[k]), rel_tol=TOL, abs_tol=1e-6)]


def combinacao(rng: random.Random, p: dict, cenarios: dict) -> tuple[dict, str, dict | None]:
    seg = rng.uniform(0, 1)
    fia = rng.uniform(0, 1 - seg)
    q = {**p, "prob_deficit": {"classe_2": rng.uniform(0, 1), "classe_3": rng.uniform(0, 1)},
         "pct_descoberto": {"classe_2": rng.uniform(0, 1), "classe_3": rng.uniform(0, 1)},
         "escolha_garantia": {"seguro": seg, "fianca": fia, "bens_proprios": 1 - seg - fia},
         "taxa_seguro_anual": rng.uniform(0.005, 0.05), "market_share_hipotetico": rng.uniform(0.01, 0.3),
         "sinistralidade": rng.uniform(0, 1), "comissao": rng.uniform(0, 0.4),
         "despesa_administrativa": rng.uniform(0, 0.3)}
    cen = rng.choice(list(cenarios["cenarios"]))
    extra = {"fracao_exigencia_garantia": rng.uniform(0, 1)} if cen == "parcial" else None
    return q, cen, extra


def serventias_sinteticas(n: int = 400, semente: int = 7) -> pd.DataFrame:
    """SINTÉTICO: serventias inventadas com as colunas que o motor produz (classe, faixa, peso, passivo, CLT)."""
    g = np.random.default_rng(semente)
    classe = g.choice(["1", "2", "3", "indeterminada"], n)
    peso = np.where(classe == "1", 0.0, np.where(classe == "indeterminada", 0.6, 1.0)) * (g.random(n) > 0.1)
    passivo = np.where(g.random(n) < 0.15, 0.0, g.gamma(2, 80_000, n))
    return pd.DataFrame({"cns": [f"S{i}" for i in range(n)], "classe": classe, "classe_faixa": classe,
                         "peso_universo": peso, "passivo": passivo, "clt": g.integers(0, 40, n).astype(float)})


def test_totais_reproduzem_o_motor_com_dados_sinteticos(p_base, cenarios):
    s = serventias_sinteticas()
    t = simulador.totais(s)
    rng = random.Random(2026)
    casos = [(p_base, "mantem", None)] + [combinacao(rng, p_base, cenarios) for _ in range(5)]
    for p, cen, extra in casos:
        completo = resumo_mercado(deficit(s, p), p, cenarios, cen, extra)
        rapido = simulador.resumo_por_totais(t, p, cenarios, cen, extra)
        assert set(completo) == set(rapido)
        assert not iguais(completo, rapido), (cen, iguais(completo, rapido))


def test_grade_tem_a_base_e_uma_premissa_por_vez(p_base):
    pontos = yaml.safe_load(open("config/simulador_demo.yaml", encoding="utf-8"))["pontos"]
    g = simulador.grade(p_base, pontos)
    base = simulador.valores_base(p_base)
    assert g[0] == ("base", base)
    for variou, v in g[1:]:
        assert [k for k in v if v[k] != base[k]] == [variou]


@pytest.mark.dados_reais
def test_tabelas_publicas_reproduzem_o_motor_completo(cenarios):
    """Motor completo sobre o silver do banco real (só leitura) × gold.simulador_* (o que o modo demonstração usa)."""
    from apoio_painel import BANCO_REAL
    from src import estado
    from src.motor import calcular_serventias, premissas_nivel
    from src.transform.gold import carregar_insumos
    regras = yaml.safe_load(open("config/regras_classificacao.yaml", encoding="utf-8"))
    lim_base = regras["versoes"][regras["versao_base"]]["limites"]
    with duckdb.connect(str(BANCO_REAL), read_only=True) as con:
        ins = carregar_insumos(con)
        semente, _ = estado.premissas_vigentes(con)
        var = con.sql("SELECT * FROM gold.simulador_variantes").df()
        fx = con.sql("SELECT * FROM gold.simulador_base_classe").df()
        peso = dict(con.execute("SELECT regra_classe, peso_classe_indeterminada_base FROM gold.execucao").fetchall())
    rng = random.Random(19)
    padrao = var[(var.premissa_variada == "base") & (var.regra_classe == "v2") & (var.metodo_rateio == "por_empregados_cnj")]
    linhas = [padrao.iloc[0]] + [var.iloc[rng.randrange(len(var))] for _ in range(5)]
    p_padrao = premissas_nivel(semente, "base", peso["v2"])
    for i, v in enumerate(linhas):
        valores = {k: v[k] for k in simulador.PREMISSAS_PASSIVO}
        p = premissas_nivel(semente, "base", peso[v.regra_classe], simulador.ajustes_passivo(p_padrao, valores))
        p, cen, extra = (p, "mantem", None) if i == 0 else combinacao(rng, p, cenarios)
        serv = calcular_serventias(ins, p, regras["versoes"][v.regra_classe]["limites"], v.metodo_rateio,
                                   limites_faixa=lim_base)[0]
        completo = resumo_mercado(serv, p, cenarios, cen, extra)
        t = {k: v[k] for k in ("n_serventias_ativas", "clt", "passivo_todas", "n_universo", "n_indeterminadas_universo",
                               "passivo_universo")}
        for f in fx[fx.variante_id == v.variante_id].itertuples():
            t[f"peso_com_passivo_{f.faixa}"], t[f"passivo_ponderado_{f.faixa}"] = f.peso_com_passivo, f.passivo_ponderado
        rapido = simulador.resumo_por_totais(t, p, cenarios, cen, extra)
        assert not iguais(completo, rapido), (int(v.variante_id), cen, iguais(completo, rapido))
