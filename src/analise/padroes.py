"""Padrões frequentes (notebook 03): regras de associação (Apriori, mlxtend) sobre atribuições, porte, classe,
situação e região, com foco nas regras que terminam em "obrigada". Parâmetros em config/analise.yaml (padroes)."""
from itertools import combinations

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

from src.analise import config
from src.analise.dados import ATRIBUICOES

ALVO = "obrigada"
ROTULOS_ATRIBUICOES = {"notas": "Notas", "rcpn": "RCPN", "ri": "RI", "rtd": "RTD", "rcpj": "RCPJ",
                       "protesto": "Protesto"}
DEFINIDORES = ("classe ", "situação ")   # obrigada = provida e Classe 2 ou 3: regras com esses itens são definição


def faixas_porte(cortes: list[int] | None = None) -> list[str]:
    """Rótulos das faixas de CLT: com cortes [0, 2, 9], "porte 0 CLT", "porte 1 a 2 CLT", "porte 3 a 9 CLT",
    "porte 10+ CLT"."""
    c = config()["padroes"]["porte_clt"] if cortes is None else cortes
    rotulos = [f"porte {c[0]} CLT"]
    rotulos += [f"porte {a + 1} a {b} CLT" for a, b in zip(c[:-1], c[1:])]
    return rotulos + [f"porte {c[-1] + 1}+ CLT"]


def transacoes(sv: pd.DataFrame, cortes: list[int] | None = None) -> pd.DataFrame:
    """Uma linha por serventia com classe conhecida (as indeterminadas saem: não se sabe se são obrigadas) e uma coluna
    verdadeiro/falso por item: atribuições, porte (faixa de CLT), classe, situação, região intermediária e "obrigada"
    (provida e Classe 2 ou 3, como no universo do painel). CLT vazio = sem item de porte."""
    c = config()["padroes"]["porte_clt"] if cortes is None else cortes
    s = sv[sv["classe"].isin(["1", "2", "3"])].set_index("cns")
    t = pd.DataFrame(index=s.index)
    for a in ATRIBUICOES:
        t[ROTULOS_ATRIBUICOES[a]] = s[a].astype(bool)
    porte = pd.cut(s["clt"], [-np.inf, *c, np.inf], labels=faixas_porte(c))
    for rotulo in faixas_porte(c):
        t[rotulo] = porte == rotulo
    for k in ["1", "2", "3"]:
        t[f"classe {k}"] = s["classe"] == k
    for sit in ["provida", "vaga", "outras"]:
        t[f"situação {sit}"] = s["situacao"] == sit
    for reg in sorted(s["regiao_intermediaria"].dropna().unique()):
        t[f"região {reg}"] = s["regiao_intermediaria"] == reg
    t[ALVO] = (s["situacao"] == "provida") & s["classe"].isin(["2", "3"])
    return t


def regras(trans: pd.DataFrame, suporte_min: float | None = None, confianca_min: float | None = None,
           max_itens: int | None = None) -> pd.DataFrame:
    """Todas as regras "se A, então B" (B com um item só) com suporte e confiança mínimos. Suporte = parte das
    serventias que têm A e B; confiança = das que têm A, a parte que tem B; lift = confiança ÷ frequência de B."""
    cfg = config()["padroes"]
    suporte_min = cfg["suporte_min"] if suporte_min is None else suporte_min
    confianca_min = cfg["confianca_min"] if confianca_min is None else confianca_min
    max_itens = cfg["max_itens"] if max_itens is None else max_itens
    freq = apriori(trans, min_support=suporte_min, use_colnames=True, max_len=max_itens)
    colunas = ["antecedentes", "consequente", "suporte", "confianca", "lift"]
    if freq.empty:
        return pd.DataFrame(columns=colunas)
    r = association_rules(freq, num_itemsets=len(trans), metric="confidence", min_threshold=confianca_min)
    r = r[r["consequents"].apply(len) == 1]
    out = pd.DataFrame({"antecedentes": r["antecedents"].values,
                        "consequente": [next(iter(c)) for c in r["consequents"]],
                        "suporte": r["support"].values, "confianca": r["confidence"].values,
                        "lift": r["lift"].values})
    # ordem fixa: a ordem dos itens num frozenset de textos muda a cada sessão do Python (hash aleatório)
    out["_se"] = out["antecedentes"].apply(lambda a: " + ".join(sorted(a)))
    return out.sort_values(["_se", "consequente"]).drop(columns="_se").reset_index(drop=True)


def confianca(trans: pd.DataFrame, itens: frozenset, alvo: str = ALVO) -> float:
    """Das serventias que têm todos os `itens`, a parte que tem o `alvo` (sem itens: a frequência geral do alvo)."""
    m = trans[list(itens)].all(axis=1) if itens else pd.Series(True, index=trans.index)
    return float(trans.loc[m, alvo].mean()) if m.any() else np.nan


def frequencia_por_item(trans: pd.DataFrame, itens: list[str], alvo: str = ALVO) -> pd.DataFrame:
    """A referência do notebook 03: para cada item (por exemplo, cada atribuição), quantas serventias o têm e que
    parte delas tem o alvo. É a confiança da regra de um item só, "se tem o item, então é obrigada"."""
    linhas = [{"item": i, "serventias": int(trans[i].sum()), "com_alvo": int((trans[i] & trans[alvo]).sum()),
               "frequencia": confianca(trans, frozenset([i]), alvo)} for i in itens]
    return pd.DataFrame(linhas)


def sem_definidores(antecedentes: frozenset) -> bool:
    """Verdadeiro se o "se" não tem item de classe nem de situação (os itens que definem "obrigada")."""
    return not any(i.startswith(DEFINIDORES) for i in antecedentes)


def regras_alvo(trans: pd.DataFrame, todas: pd.DataFrame, melhoria_min: float | None = None,
                alvo: str = ALVO) -> pd.DataFrame:
    """As regras que terminam no alvo, sem os itens que o definem (classe e situação), com:
    - referência: a maior frequência do alvo entre as atribuições do "se" (a frequência geral, se não houver
      atribuição); ganho = confiança ÷ referência (acima de 1: a regra diz mais que a atribuição sozinha);
    - melhoria: confiança menos a maior confiança das regras com parte dos itens do "se" (Bayardo et al., 2000).
    Ficam as regras com ganho > 1 e melhoria >= `melhoria_min`."""
    melhoria_min = config()["padroes"]["melhoria_min"] if melhoria_min is None else melhoria_min
    r = todas[(todas["consequente"] == alvo) & todas["antecedentes"].apply(sem_definidores)].copy()
    atrib = set(ROTULOS_ATRIBUICOES.values())
    geral = confianca(trans, frozenset(), alvo)
    cache: dict[frozenset, float] = {}

    def conf(itens: frozenset) -> float:
        if itens not in cache:
            cache[itens] = confianca(trans, itens, alvo)
        return cache[itens]

    def referencia(a: frozenset) -> float:
        presentes = [i for i in a if i in atrib]
        return max(conf(frozenset([i])) for i in presentes) if presentes else geral

    def melhor_parte(a: frozenset) -> float:
        partes = [frozenset(p) for k in range(len(a)) for p in combinations(sorted(a), k)]
        return max(conf(p) for p in partes)

    r["referencia"] = r["antecedentes"].apply(referencia)
    r["ganho"] = r["confianca"] / r["referencia"]
    r["melhoria"] = r["confianca"] - r["antecedentes"].apply(melhor_parte)
    r = r[(r["ganho"] > 1) & (r["melhoria"] >= melhoria_min)].copy()
    r["_se"] = r["antecedentes"].apply(lambda a: " + ".join(sorted(a)))   # desempate fixo
    return (r.sort_values(["lift", "suporte", "_se"], ascending=[False, False, True], kind="stable")
            .drop(columns="_se").reset_index(drop=True))


def estabilidade(trans: pd.DataFrame, n: int | None = None, fracao: float | None = None,
                 semente: int | None = None, **params) -> pd.Series:
    """Em quantas de `n` reamostragens (`fracao` das serventias, sem reposição) cada regra do alvo reaparece, com os
    mesmos cortes. Devolve a contagem por conjunto de itens do "se"."""
    cfg = config()
    n = cfg["padroes"]["reamostragens"] if n is None else n
    fracao = cfg["padroes"]["fracao"] if fracao is None else fracao
    semente = cfg["semente"] if semente is None else semente
    rng = np.random.default_rng(semente)
    contagem: dict[frozenset, int] = {}
    for _ in range(n):
        amostra = trans.iloc[np.sort(rng.choice(len(trans), int(round(fracao * len(trans))), replace=False))]
        todas = regras(amostra, **{k: v for k, v in params.items() if k != "melhoria_min"})
        for a in regras_alvo(amostra, todas, params.get("melhoria_min"))["antecedentes"]:
            contagem[a] = contagem.get(a, 0) + 1
    return pd.Series(contagem, dtype="int64")


def tabela_regras(r: pd.DataFrame, trans: pd.DataFrame, vezes: pd.Series, n_reamostragens: int | None = None,
                  n_principais: int | None = None) -> pd.DataFrame:
    """Desenho de gold.analise_regras: as regras do alvo, estáveis (presentes em todas as reamostragens), na ordem do
    lift, com a posição, o texto da regra e as medidas. Só as `n_principais` primeiras."""
    cfg = config()["padroes"]
    n_reamostragens = cfg["reamostragens"] if n_reamostragens is None else n_reamostragens
    n_principais = cfg["n_principais"] if n_principais is None else n_principais
    out = r.copy()
    out["reamostragens_com_a_regra"] = out["antecedentes"].map(vezes).fillna(0).astype(int)
    out = out[out["reamostragens_com_a_regra"] >= n_reamostragens].head(n_principais).reset_index(drop=True)
    return pd.DataFrame({
        "posicao": np.arange(1, len(out) + 1),
        "se": [" + ".join(sorted(a)) for a in out["antecedentes"]],
        "entao": out["consequente"].values,
        "n_itens_se": out["antecedentes"].apply(len).values,
        "serventias_com_se": [int(trans[list(a)].all(axis=1).sum()) for a in out["antecedentes"]],
        "serventias_com_se_e_entao": np.rint(out["suporte"].values * len(trans)).astype(int),
        "suporte": out["suporte"].values, "confianca": out["confianca"].values, "lift": out["lift"].values,
        "referencia": out["referencia"].values, "ganho_sobre_referencia": out["ganho"].values,
        "melhoria": out["melhoria"].values, "reamostragens_com_a_regra": out["reamostragens_com_a_regra"].values,
    })
