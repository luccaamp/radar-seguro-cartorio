"""Área "Explorar" do painel (D-077): o Simulador ao vivo. Funções puras, sobre os totais do modelo.

O ponto de partida é o mesmo da página "Quão certo é", mas centrado nos valores que o leitor escolhe:
- `tornado`: cada uma das seis suposições do T7 sozinha no mínimo e no máximo, as outras nos valores escolhidos;
- `faixa_por_sorteio`: o Monte Carlo do notebook 08 (sorteios triangulares), com o valor mais provável de cada
  suposição no valor escolhido.
As faixas de cada suposição são as da semente das premissas (config/premissas/); se o leitor escolher um valor fora
delas, a faixa se estende até ele (o sorteio nunca sai do intervalo entre o mínimo e o máximo). O prêmio sai sempre
das contas do modelo (`resumo_por_totais` e `premio_vetorial`, conferidos entre si em tests/test_analise.py).
"""
import numpy as np
import pandas as pd

from src.analise import config
from src.analise.sensibilidade import SUPOSICOES, com_suposicoes, premio_vetorial, sortear
from src.model.cenario import aplicar_cenario_stf
from src.model.simulador import resumo_por_totais


def valores(p: dict) -> dict:
    """Os valores das seis suposições do T7 nas premissas resolvidas `p` (nomes de SUPOSICOES)."""
    return {"taxa": p["taxa_seguro_anual"], "seguro": p["escolha_garantia"]["seguro"],
            "pct_3": p["pct_descoberto"]["classe_3"], "prob_3": p["prob_deficit"]["classe_3"],
            "pct_2": p["pct_descoberto"]["classe_2"], "prob_2": p["prob_deficit"]["classe_2"]}


def faixas_ao_redor(faixas: pd.DataFrame, p: dict) -> pd.DataFrame:
    """As faixas da semente (saída de sensibilidade.faixas_suposicoes) com o valor mais provável no valor escolhido em
    `p`; o mínimo e o máximo se estendem para incluir esse valor."""
    v = valores(p)
    out = faixas.copy()
    out["base"] = [v[n] for n in out.index]
    out["min"] = np.minimum(out["min"], out["base"])
    out["max"] = np.maximum(out["max"], out["base"])
    return out


def _premio(totais: dict, p: dict, cenarios: dict, cenario: str, extra: dict | None) -> float:
    return resumo_por_totais(totais, p, cenarios, cenario, extra)["mercado_premio_emitido"]


def tornado(totais: dict, p: dict, faixas: pd.DataFrame, cenarios: dict, cenario: str = "mantem",
            extra: dict | None = None) -> list[dict]:
    """Cada suposição sozinha no mínimo e no máximo da faixa, as outras nos valores escolhidos em `p`; em ordem de
    amplitude (a que mais mexe primeiro). Formato das linhas de `analises.tornado`, para o mesmo gráfico."""
    f = faixas_ao_redor(faixas, p)
    base = _premio(totais, p, cenarios, cenario, extra)
    linhas = []
    for nome, r in f.iterrows():
        no_min = _premio(totais, com_suposicoes(p, {nome: r["min"]}), cenarios, cenario, extra)
        no_max = _premio(totais, com_suposicoes(p, {nome: r["max"]}), cenarios, cenario, extra)
        linhas.append({"suposicao": nome, "rotulo": SUPOSICOES[nome], "valor_min": float(r["min"]),
                       "valor_escolhido": float(r["base"]), "valor_max": float(r["max"]), "premio_no_min": no_min,
                       "premio_base": base, "premio_no_max": no_max, "amplitude": abs(no_max - no_min)})
    return sorted(linhas, key=lambda x: -x["amplitude"])


def faixa_por_sorteio(totais: dict, p: dict, faixas: pd.DataFrame, cenarios: dict, cenario: str = "mantem",
                      extra: dict | None = None, n: int | None = None, semente: int | None = None) -> dict:
    """Monte Carlo das seis suposições ao redor dos valores escolhidos (triangular: mínimo, valor escolhido, máximo;
    independentes, como a variante principal do notebook 08). Devolve P5, mediana e P95 do prêmio, do déficit e da
    IS, os extremos teóricos (todas no mínimo e todas no máximo) e o prêmio nos valores escolhidos."""
    f = faixas_ao_redor(faixas, p)
    exigencia = aplicar_cenario_stf(p, cenarios, cenario, extra).get("fracao_exigencia_garantia", 1.0)
    x = sortear(_sem_faixa_nula(f), n, semente)
    r = premio_vetorial(totais, x, exigencia)
    q = config()["sensibilidade"]["percentis"]
    i5, i50, i95 = q.index(0.05), q.index(0.50), q.index(0.95)
    out = {}
    for medida, v in r.items():
        qs = np.quantile(v, q)
        out[medida] = {"p05": float(qs[i5]), "mediana": float(qs[i50]), "p95": float(qs[i95])}
    cantos = {nivel: premio_vetorial(totais, {k: np.asarray(f.loc[k, nivel]) for k in f.index}, exigencia)["premio"]
              for nivel in ("min", "max")}
    out["premio"].update(escolhido=_premio(totais, p, cenarios, cenario, extra),
                         extremo_min=float(cantos["min"]), extremo_max=float(cantos["max"]))
    out["n_sorteios"] = len(next(iter(x.values())))
    return out


def _sem_faixa_nula(f: pd.DataFrame) -> pd.DataFrame:
    """A triangular divide por (máximo − mínimo): uma suposição sem faixa (mínimo = máximo, por exemplo um valor
    escolhido igual aos dois) ganha uma faixa desprezível em volta do valor, para o sorteio devolver o próprio valor."""
    g = f.copy()
    nula = g["max"] <= g["min"]
    g.loc[nula, "max"] = g.loc[nula, "min"] + 1e-12
    return g
