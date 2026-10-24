"""Agrupamentos (notebook 04): k-means em escala log, com o k escolhido pela silhueta e pelo cotovelo, e o hierárquico
de Ward para comparar (índice de Rand ajustado). Parâmetros em config/analise.yaml (grupos)."""
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from src.analise import config
from src.analise.dados import ATRIBUICOES

VARIAVEIS = ["log_receita", "log_clt", "n_atribuicoes", "provida", "vaga"]


def matriz(sv: pd.DataFrame) -> pd.DataFrame:
    """As variáveis do agrupamento, uma linha por serventia com receita de referência > 0 e CLT informado: log10 da
    receita, log10(1 + CLT) (o +1 deixa o zero CLT entrar), número de atribuições e a situação em duas colunas 0/1
    (provida, vaga; "outras" = as duas em 0)."""
    s = sv[(sv["receita_ref"] > 0) & sv["clt"].notna()].set_index("cns")
    return pd.DataFrame({"log_receita": np.log10(s["receita_ref"]), "log_clt": np.log10(1 + s["clt"]),
                         "n_atribuicoes": s["n_atribuicoes"].astype(float),
                         "provida": (s["situacao"] == "provida").astype(float),
                         "vaga": (s["situacao"] == "vaga").astype(float)})


def padronizar(x: pd.DataFrame) -> np.ndarray:
    """Cada coluna vira (valor − média) ÷ desvio padrão, para todas pesarem igual na distância."""
    return StandardScaler().fit_transform(x)


def kmeans(z: np.ndarray, k: int, semente: int | None = None, n_init: int | None = None) -> np.ndarray:
    cfg = config()
    semente = cfg["semente"] if semente is None else semente
    n_init = cfg["grupos"]["n_init"] if n_init is None else n_init
    return KMeans(k, n_init=n_init, random_state=semente).fit_predict(z)


def ward(z: np.ndarray, k: int) -> np.ndarray:
    return AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(z)


def escolha_k(z: np.ndarray, k_min: int | None = None, k_max: int | None = None,
              semente: int | None = None) -> pd.DataFrame:
    """Para cada k: a silhueta (de −1 a 1: quanto cada ponto está mais perto do próprio grupo que do vizinho; maior é
    melhor), a inércia (soma das distâncias ao centro do grupo, para o cotovelo) e a concordância com o Ward (índice
    de Rand ajustado: 1 = mesmos grupos, 0 = concordância de acaso)."""
    cfg = config()["grupos"]
    k_min = cfg["k_min"] if k_min is None else k_min
    k_max = cfg["k_max"] if k_max is None else k_max
    linhas = []
    for k in range(k_min, k_max + 1):
        km = KMeans(k, n_init=cfg["n_init"], random_state=config()["semente"] if semente is None else semente).fit(z)
        linhas.append({"k": k, "silhueta": silhouette_score(z, km.labels_), "inercia": km.inertia_,
                       "silhueta_ward": silhouette_score(z, w := ward(z, k)),
                       "rand_ajustado_kmeans_ward": adjusted_rand_score(km.labels_, w)})
    return pd.DataFrame(linhas)


def ordenar_por_receita(rotulos: np.ndarray, log_receita: pd.Series) -> np.ndarray:
    """Renumera os grupos de 1 a k pela receita mediana, do menor para o maior (o número do k-means é arbitrário e
    muda com a semente; assim o grupo 1 é sempre o de menor receita)."""
    med = pd.Series(log_receita.values).groupby(rotulos).median().sort_values()
    mapa = {g: i + 1 for i, g in enumerate(med.index)}
    return np.array([mapa[g] for g in rotulos])


def perfil(sv: pd.DataFrame, grupo: pd.Series) -> pd.DataFrame:
    """Perfil de cada grupo: quantas serventias, receita, CLT e atribuições medianas, % vagas, obrigadas (soma dos
    pesos do universo), passivo, passivo das obrigadas, déficit esperado e a parte do déficit de MG, mais a % de
    serventias com cada atribuição. `grupo` é indexado pelo CNS."""
    s = sv.set_index("cns").join(grupo.rename("grupo"), how="inner")
    s["passivo_obrigadas"] = s["passivo"] * s["peso_universo"]
    out = s.groupby("grupo").agg(
        serventias=("receita_ref", "size"), receita_mediana=("receita_ref", "median"), clt_mediano=("clt", "median"),
        atribuicoes_medianas=("n_atribuicoes", "median"), pct_vagas=("situacao", lambda x: (x == "vaga").mean()),
        obrigadas=("peso_universo", "sum"), passivo=("passivo", "sum"), passivo_obrigadas=("passivo_obrigadas", "sum"),
        com_deficit=("n_deficit", "sum"), deficit=("valor_descoberto", "sum"))
    out["pct_obrigadas"] = out["obrigadas"] / out["serventias"]
    out["pct_deficit_mg"] = out["deficit"] / sv["valor_descoberto"].sum()
    out["deficit_por_obrigada"] = out["deficit"] / out["obrigadas"].replace(0, np.nan)
    for a in ATRIBUICOES:
        out[f"pct_{a}"] = s.groupby("grupo")[a].mean()
    return out


def grupo_alvo(p: pd.DataFrame) -> int:
    """O grupo-alvo do seguro: o que concentra a maior parte do déficit esperado (a parte do passivo das obrigadas
    sem bens que a cubra, que é o que o seguro garante)."""
    return int(p["pct_deficit_mg"].idxmax())


def tabela_grupos(grupo: pd.Series, nomes: dict[int, str], alvo: int, k: int, semente: int) -> pd.DataFrame:
    """Desenho de gold.analise_grupos: uma linha por serventia agrupada (CNS, número e nome do grupo, se é o
    grupo-alvo), com o k e a semente usados. O perfil de cada grupo sai de `perfil()` sobre esta tabela."""
    return pd.DataFrame({"cns": grupo.index, "grupo": grupo.values.astype(int),
                         "nome_grupo": [nomes[g] for g in grupo.values], "grupo_alvo": grupo.values == alvo,
                         "k": k, "semente": semente}).reset_index(drop=True)
