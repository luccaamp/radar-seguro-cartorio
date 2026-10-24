"""Estatística descritiva para os notebooks: resumo de distribuições, dados faltantes, valores atípicos, correlação e
concentração. Funções puras (recebem e devolvem pandas), testadas em tests/test_analise.py."""
import numpy as np
import pandas as pd

from src.analise import config


def resumo(serie: pd.Series) -> pd.Series:
    """Quantos valores, média, mediana, quartis, percentil 90, máximo e a razão média ÷ mediana (acima de 1: cauda
    longa à direita, poucos valores grandes puxam a média)."""
    s = pd.Series(serie, dtype="float64").dropna()
    q1, med, q3, p90 = s.quantile([0.25, 0.5, 0.75, 0.9]) if len(s) else [np.nan] * 4
    return pd.Series({"n": len(s), "media": s.mean(), "mediana": med, "q1": q1, "q3": q3, "p90": p90,
                      "maximo": s.max(), "soma": s.sum(), "media_sobre_mediana": s.mean() / med if med else np.nan})


def resumo_por_grupo(df: pd.DataFrame, valor: str, grupo: str) -> pd.DataFrame:
    """`resumo()` de uma coluna em cada grupo, mais a participação de cada grupo na soma."""
    out = df.groupby(grupo, observed=True)[valor].apply(resumo).unstack()
    out["pct_soma"] = out["soma"] / out["soma"].sum()
    return out.sort_values("soma", ascending=False)


def faltantes(mascaras: dict[str, pd.Series]) -> pd.DataFrame:
    """Tabela de problemas: para cada nome, quantas linhas a máscara marca (True) e a % do total."""
    linhas = [{"problema": nome, "n": int(m.sum()), "total": len(m), "pct": m.mean()} for nome, m in mascaras.items()]
    return pd.DataFrame(linhas)


def cercas_iqr(serie: pd.Series, k: float | None = None, log: bool | None = None) -> tuple[float, float]:
    """Limites de Tukey: Q1 − k·IQR e Q3 + k·IQR (IQR = Q3 − Q1). Com `log`, a conta é feita em log10 dos valores
    positivos e os limites voltam para a escala original. Padrões em config/analise.yaml."""
    cfg = config()["outliers"]
    k = cfg["k_iqr"] if k is None else k
    log = (cfg["escala"] == "log10") if log is None else log
    s = pd.Series(serie, dtype="float64").dropna()
    if log:
        s = np.log10(s[s > 0])
    q1, q3 = s.quantile([0.25, 0.75])
    inf, sup = q1 - k * (q3 - q1), q3 + k * (q3 - q1)
    return (10 ** inf, 10 ** sup) if log else (inf, sup)


def atipicos(serie: pd.Series, k: float | None = None, log: bool | None = None) -> pd.Series:
    """Máscara dos valores fora das cercas de `cercas_iqr`. Vazios nunca são atípicos; no log, o zero também não (ele
    não tem logaritmo e é contado à parte, como zero declarado)."""
    log = (config()["outliers"]["escala"] == "log10") if log is None else log
    inf, sup = cercas_iqr(serie, k, log)
    s = pd.Series(serie, dtype="float64")
    fora = (s < inf) | (s > sup)
    return fora & (s > 0) if log else fora


def saltos(serie: pd.DataFrame, janela: int | None = None, fator: float | None = None) -> pd.DataFrame:
    """Semestres em que o valor de uma serventia fica `fator` vezes acima (ou abaixo) da mediana dos `janela` semestres
    anteriores dela. Recebe cns, ano, semestre e arrecadacao (uma linha por período); zeros ficam fora da conta (são
    tratados à parte). Devolve as linhas marcadas, com a mediana anterior e a razão."""
    cfg = config()["saltos"]
    janela = cfg["janela"] if janela is None else janela
    fator = cfg["fator"] if fator is None else fator
    if janela < 1 or fator <= 1:
        raise ValueError(f"janela ({janela}) precisa ser >= 1 e fator ({fator}) > 1")
    s = serie[serie["arrecadacao"] > 0].sort_values(["cns", "ano", "semestre"]).copy()
    s["mediana_anterior"] = s.groupby("cns")["arrecadacao"].transform(
        lambda v: v.shift(1).rolling(janela, min_periods=janela).median())
    s["razao"] = s["arrecadacao"] / s["mediana_anterior"]
    return s[(s["razao"] >= fator) | (s["razao"] <= 1 / fator)]


def sem_saltos(serie: pd.DataFrame, marcados: pd.DataFrame) -> pd.DataFrame:
    """Cópia da série com o valor de cada semestre marcado por `saltos()` trocado pela mediana anterior da serventia
    (só para medir quanto os saltos pesam nos totais; não é correção oficial)."""
    chave = ["cns", "ano", "semestre"]
    out = serie.merge(marcados[chave + ["mediana_anterior"]], on=chave, how="left")
    out["arrecadacao"] = out["mediana_anterior"].combine_first(out["arrecadacao"])
    return out.drop(columns="mediana_anterior")


def correlacoes(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    """Correlação de Spearman (pelos postos: mede se "quando um sobe, o outro sobe", sem supor linha reta e sem ser
    dominada pelos maiores valores), em formato longo: par, rho e n."""
    linhas = []
    for i, a in enumerate(colunas):
        for b in colunas[i + 1:]:
            par = df[[a, b]].dropna()
            postos = par.rank()   # Spearman = correlação de Pearson dos postos (sem depender do scipy)
            linhas.append({"a": a, "b": b, "rho": postos[a].corr(postos[b]), "n": len(par)})
    return pd.DataFrame(linhas)


def participacao_topo(serie: pd.Series, fracao: float) -> float:
    """Que parte da soma está nos `fracao` maiores valores (por exemplo, 0,1 = os 10% maiores)."""
    s = pd.Series(serie, dtype="float64").dropna().sort_values(ascending=False)
    n = max(1, int(round(len(s) * fracao)))
    return s.iloc[:n].sum() / s.sum()


def curva_lorenz(serie: pd.Series) -> pd.DataFrame:
    """Curva de concentração (Lorenz): ordena do menor para o maior e acumula. Cada ponto diz que os `fracao_unidades`
    menores somam `fracao_valor` do total; começa em (0, 0) e termina em (1, 1). Vazios ficam fora."""
    s = np.sort(pd.Series(serie, dtype="float64").dropna().to_numpy())
    return pd.DataFrame({"fracao_unidades": np.arange(len(s) + 1) / len(s),
                         "fracao_valor": np.concatenate([[0.0], np.cumsum(s)]) / s.sum()})


def gini(serie: pd.Series) -> float:
    """Índice de Gini: 0 = todos iguais; perto de 1 = quase tudo numa só unidade. É o dobro da área entre a linha
    da igualdade e a curva de Lorenz: G = Σ (2i − n − 1)·x_i ÷ (n·Σx), com x em ordem crescente (i = 1..n)."""
    s = np.sort(pd.Series(serie, dtype="float64").dropna().to_numpy())
    n = len(s)
    return float(np.sum((2 * np.arange(1, n + 1) - n - 1) * s) / (n * s.sum()))


def fatores_reais(indice: pd.DataFrame, base_ano_mes: int) -> pd.Series:
    """Fator que leva um valor de cada semestre a preços do mês-base: índice do mês-base ÷ média do índice nos 6 meses
    do semestre. Recebe ano_mes (AAAAMM) e numero_indice; só semestres com os 6 meses. Índice: "2025-2"."""
    i = indice.assign(ano=indice["ano_mes"] // 100, semestre=(indice["ano_mes"] % 100 > 6).astype(int) + 1)
    g = i.groupby(["ano", "semestre"])["numero_indice"].agg(["mean", "size"])
    g = g[g["size"] == 6]
    base = indice.loc[indice["ano_mes"] == base_ano_mes, "numero_indice"].iloc[0]
    fator = base / g["mean"]
    fator.index = [f"{a}-{s}" for a, s in fator.index]
    return fator.rename("fator")


def crescimento_medio(valores: pd.Series, periodos: int | None = None) -> float:
    """Taxa média de crescimento por período entre o primeiro e o último valor: (último ÷ primeiro)^(1/períodos) − 1.
    Sem `periodos`, a série tem um valor por período (períodos = n − 1); com ele, bastam as duas pontas."""
    v = pd.Series(valores, dtype="float64").dropna()
    periodos = len(v) - 1 if periodos is None else periodos
    return (v.iloc[-1] / v.iloc[0]) ** (1 / periodos) - 1


def crescimento_tendencia(valores: pd.Series) -> float:
    """Taxa média de crescimento por período pela reta de tendência: ajusta log(valor) = a + b·t (t = 0, 1, 2...) por
    mínimos quadrados e devolve e^b − 1. Usa todos os pontos, então depende menos do primeiro e do último."""
    v = pd.Series(valores, dtype="float64").dropna()
    b = np.polyfit(np.arange(len(v)), np.log(v.values), 1)[0]
    return float(np.exp(b) - 1)
