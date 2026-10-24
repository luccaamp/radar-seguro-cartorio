"""Regressão (notebook 06): empregados CLT pela receita (teste T1) e decomposição do passivo por serventia.

Métodos e parâmetros do teste T1 (docs/qa/analises/testes_metodos.md; scripts/testes_metodos.py), lidos de
config/analise.yaml. Funções puras (recebem e devolvem pandas), testadas em tests/test_analise.py.
"""
from itertools import combinations
from math import factorial

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import PoissonRegressor
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.analise import config
from src.analise.dados import ATRIBUICOES

VARIAVEIS_CLT = ["log_receita", "n_atribuicoes", *ATRIBUICOES]


# ---------------------------------------------------------------- 06a: empregados CLT pela receita (T1)

def base_clt(sv: pd.DataFrame) -> pd.DataFrame:
    """Serventias com receita de referência > 0, CLT informado e região intermediária (o recorte do T1), com as
    variáveis do modelo: log da receita, número de atribuições e uma coluna 0/1 por atribuição."""
    df = sv[(sv["receita_ref"] > 0) & sv["clt"].notna() & sv["regiao_intermediaria"].notna()].copy()
    df["log_receita"] = np.log(df["receita_ref"])
    for a in ATRIBUICOES:
        df[a] = df[a].fillna(False).astype(int)
    return df.reset_index(drop=True)


def prever_mediana_faixa(tr: pd.DataFrame, te: pd.DataFrame, faixas: int | None = None) -> np.ndarray:
    """Referência do T1: divide o treino em `faixas` faixas de receita com o mesmo número de serventias (decis) e
    prevê, para cada serventia do teste, a mediana de CLT da faixa em que a receita dela cai."""
    faixas = faixas or config()["regressao"]["faixas_referencia"]
    cortes = np.quantile(tr["log_receita"], np.linspace(0, 1, faixas + 1)[1:-1])
    f_tr, f_te = np.digitize(tr["log_receita"], cortes), np.digitize(te["log_receita"], cortes)
    med = pd.Series(tr["clt"].to_numpy()).groupby(f_tr).median()
    return med.reindex(f_te).fillna(tr["clt"].median()).to_numpy()


def prever_floresta(tr: pd.DataFrame, te: pd.DataFrame, semente: int | None = None) -> np.ndarray:
    """Vencedor do T1: floresta aleatória (média de muitas árvores de decisão, cada uma treinada numa reamostragem)."""
    cfg = config()
    f = cfg["regressao"]["floresta"]
    m = RandomForestRegressor(f["n_arvores"], min_samples_leaf=f["min_folha"], n_jobs=-1,
                              random_state=cfg["semente"] if semente is None else semente)
    return m.fit(tr[VARIAVEIS_CLT], tr["clt"]).predict(te[VARIAVEIS_CLT])


def prever_poisson(tr: pd.DataFrame, te: pd.DataFrame) -> np.ndarray:
    """Versão interpretável do T1: regressão de Poisson (log do CLT esperado = soma ponderada das variáveis)."""
    m = make_pipeline(StandardScaler(), PoissonRegressor(alpha=config()["regressao"]["poisson_alpha"], max_iter=1000))
    return m.fit(tr[VARIAVEIS_CLT], tr["clt"]).predict(te[VARIAVEIS_CLT])


METODOS_CLT = {"Referência: mediana por faixa de receita": prever_mediana_faixa,
               "Floresta aleatória": prever_floresta, "Poisson (GLM)": prever_poisson}


def metricas(real, previsto) -> dict:
    """MAE (erro absoluto médio), RMSE (raiz do erro quadrático médio) e R² (1 − erro quadrático ÷ variância)."""
    y, p = np.asarray(real, float), np.asarray(previsto, float)
    return {"MAE": float(np.mean(np.abs(p - y))), "RMSE": float(np.sqrt(np.mean((p - y) ** 2))),
            "R2": float(1 - np.sum((p - y) ** 2) / np.sum((y - y.mean()) ** 2))}


def validar_grupo_fora(df: pd.DataFrame, metodos: dict, grupo: str = "regiao_intermediaria", alvo: str = "clt"
                       ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validação "deixa um grupo de fora": cada grupo (região) é previsto por um modelo treinado só nos outros.

    Devolve (previsões fora da amostra, uma coluna por método; métricas por método, com o erro médio do total por
    grupo em %; total real e previsto em cada grupo)."""
    prev = pd.DataFrame(index=df.index, columns=list(metodos), dtype=float)
    linhas = []
    for g in sorted(df[grupo].unique()):
        te = df[grupo] == g
        for nome, f in metodos.items():
            p = f(df[~te], df[te])
            prev.loc[te, nome] = p
            real = float(df.loc[te, alvo].sum())
            linhas.append({grupo: g, "metodo": nome, "n": int(te.sum()), "real": real, "previsto": float(p.sum()),
                           "erro_total_pct": 100 * (p.sum() - real) / real})
    por_grupo = pd.DataFrame(linhas)
    m = pd.DataFrame({nome: metricas(df[alvo], prev[nome]) for nome in metodos}).T
    m["erro_total_medio_pct"] = por_grupo.assign(a=por_grupo["erro_total_pct"].abs()).groupby("metodo")["a"].mean()
    return prev, m.sort_values("MAE"), por_grupo


def coeficientes_poisson(df: pd.DataFrame) -> pd.DataFrame:
    """Poisson (statsmodels) em todas as serventias, com as variáveis na escala original, para ler os pesos:
    exp(coef) é o fator que multiplica o CLT esperado quando a variável sobe 1 (no log da receita: receita × e ≈ 2,7).
    Intervalo de 95% com erro-padrão robusto (HC0), porque a variância do CLT é maior que a média."""
    X = sm.add_constant(df[VARIAVEIS_CLT].astype(float))
    fit = sm.GLM(df["clt"], X, family=sm.families.Poisson()).fit(cov_type="HC0")
    ic = fit.conf_int()
    return pd.DataFrame({"coef": fit.params, "fator": np.exp(fit.params), "fator_ic_inf": np.exp(ic[0]),
                         "fator_ic_sup": np.exp(ic[1]), "p_valor": fit.pvalues})


def total_com_margem(total: float, margem: float | None = None) -> tuple[float, float]:
    """Faixa de publicação de um total estimado pelo modelo (±10% no T1; config/analise.yaml)."""
    margem = config()["regressao"]["margem_total"] if margem is None else margem
    return total * (1 - margem), total * (1 + margem)


def tabela_clt_modelo(df: pd.DataFrame, previsoes: pd.DataFrame) -> pd.DataFrame:
    """Desenho da gold.analise_clt_modelo: uma linha por serventia do recorte do T1, com o CLT declarado ao CNJ e as
    previsões fora da amostra (região de fora) da floresta, do Poisson e da referência."""
    out = df[["cns", "cod_ibge", "regiao_intermediaria", "receita_ref", "n_atribuicoes", "clt"]].rename(
        columns={"clt": "clt_declarado"})
    out["clt_previsto_floresta"] = previsoes["Floresta aleatória"].to_numpy()
    out["clt_previsto_poisson"] = previsoes["Poisson (GLM)"].to_numpy()
    out["clt_previsto_referencia"] = previsoes["Referência: mediana por faixa de receita"].to_numpy()
    out["residuo_floresta"] = out["clt_declarado"] - out["clt_previsto_floresta"]
    out["validacao"] = "regiao_intermediaria_fora"
    return out


# ---------------------------------------------------------------- 06b: decomposição do passivo

def distribuicao_usada(vinculos: pd.DataFrame, medio: pd.DataFrame, regioes: dict) -> pd.DataFrame:
    """Para cada município, o salário médio, o tempo de casa médio (meses) e o número de vínculos da distribuição
    que o modelo usou (`origem_distribuicao` de gold.interno_passivo_municipio: o próprio município, a região
    imediata ou o estado). `vinculos`: cod_ibge, salario, meses_servico (src.model.distribuicao.preparar_vinculos)."""
    v = vinculos.assign(regiao=vinculos["cod_ibge"].map(regioes))
    por = {"municipio": v.groupby("cod_ibge"), "regiao": v.groupby("regiao")}
    agg = {o: g.agg(salario_medio=("salario", "mean"), meses_medio=("meses_servico", "mean"),
                    n_vinculos_distribuicao=("salario", "size")) for o, g in por.items()}
    estado = {"salario_medio": v["salario"].mean(), "meses_medio": v["meses_servico"].mean(),
              "n_vinculos_distribuicao": len(v)}
    linhas = []
    for cod, origem in zip(medio["cod_ibge"], medio["origem_distribuicao"]):
        chave = cod if origem == "municipio" else regioes.get(cod)
        r = agg[origem].loc[chave] if origem in agg else pd.Series(estado)
        linhas.append({"cod_ibge": cod, "origem_distribuicao": origem,
                       "chave_distribuicao": f"{origem}:{chave}" if origem in agg else "estado", **r.to_dict()})
    return pd.DataFrame(linhas)


def partes_variancia_log(clt: pd.Series, medio: pd.Series) -> dict:
    """Divide a variância de log(passivo) = log(CLT) + log(passivo médio por vínculo) entre as duas parcelas.

    Var(a + b) = Var(a) + Var(b) + 2·Cov(a, b); a covariância é dividida meio a meio (é a divisão de Shapley para
    uma soma). Devolve a parte de cada parcela (somam 1) e a correlação entre elas."""
    a, b = np.log(np.asarray(clt, float)), np.log(np.asarray(medio, float))
    va, vb, cov = a.var(), b.var(), np.cov(a, b, ddof=0)[0, 1]
    total = va + vb + 2 * cov
    return {"quantidade": (va + cov) / total, "passivo_medio_vinculo": (vb + cov) / total,
            "correlacao": cov / np.sqrt(va * vb) if va * vb > 0 else np.nan, "variancia_total": total}


def _r2(X: pd.DataFrame, y: np.ndarray) -> float:
    if X.shape[1] == 0:
        return 0.0
    return float(sm.OLS(y, sm.add_constant(X, has_constant="add")).fit().rsquared)


def shapley_r2(X: pd.DataFrame, y) -> pd.Series:
    """Parte do R² de uma regressão linear atribuída a cada variável (valor de Shapley): a média do ganho de R² ao
    incluir a variável, sobre todas as ordens de entrada. As partes somam o R² do modelo completo."""
    y = np.asarray(y, float)
    cols = list(X.columns)
    n = len(cols)
    r2 = {s: _r2(X[list(s)], y) for k in range(n + 1) for s in combinations(cols, k)}
    peso = lambda k: factorial(k) * factorial(n - k - 1) / factorial(n)   # noqa: E731
    out = {}
    for c in cols:
        outros = [x for x in cols if x != c]
        out[c] = sum(peso(k) * (r2[tuple(x for x in cols if x in set(s) | {c})] - r2[s])
                     for k in range(n) for s in combinations(outros, k))
    return pd.Series(out)


def regressao_loglog(df: pd.DataFrame, y: str, xs: list[str], grupos: pd.Series | None = None,
                     dobras: int | None = None) -> dict:
    """Regressão linear de log(y) nos log(xs) (cada coeficiente é uma elasticidade: +1% em x → +coef% em y), com o
    R² no próprio ajuste e o R² fora da amostra em `dobras` dobras. Com `grupos`, as linhas do mesmo grupo ficam na
    mesma dobra (nenhum grupo aparece no treino e no teste ao mesmo tempo)."""
    dobras = dobras or config()["regressao"]["dobras_passivo"]
    Y = np.log(df[y].to_numpy(float))
    X = np.log(df[xs].astype(float))
    fit = sm.OLS(Y, sm.add_constant(X)).fit()
    g = grupos.to_numpy() if grupos is not None else np.arange(len(df))
    oof = np.zeros(len(df))
    for tr, te in GroupKFold(dobras).split(X, Y, g):
        f = sm.OLS(Y[tr], sm.add_constant(X.iloc[tr])).fit()
        oof[te] = f.predict(sm.add_constant(X.iloc[te], has_constant="add"))
    r2_cv = 1 - np.sum((Y - oof) ** 2) / np.sum((Y - Y.mean()) ** 2)
    coefs = pd.DataFrame({"elasticidade": fit.params, "ic_inf": fit.conf_int()[0], "ic_sup": fit.conf_int()[1]})
    return {"coeficientes": coefs, "r2": float(fit.rsquared), "r2_validacao": float(r2_cv),
            "residuo_validacao": pd.Series(Y - oof, index=df.index), "previsto_validacao": pd.Series(oof, index=df.index)}
