"""Classificação (notebook 05): (a) vacância, como associação (teste T4), e (b) subida de classe no ano seguinte
(teste T3), com validação temporal, recalibração e a contagem esperada de subidas com faixa. Os modelos e parâmetros
são os dos testes (scripts/testes_metodos.py), lidos de config/analise.yaml (classificacao)."""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.analise import RAIZ, config
from src.analise.dados import ATRIBUICOES

VARIAVEIS_SUBIDA = ["log_m1", "log_m2", "cresc", "dist_limite", "log_max1", "cresc2", "n_atribuicoes", *ATRIBUICOES,
                    "log_pop"]


# ---------------------------------------------------------------------------------------------------------------
# Modelos e métricas
# ---------------------------------------------------------------------------------------------------------------
def modelos(semente: int | None = None) -> dict:
    """A referência (None = prever a proporção de "sim" do treino para todos), a regressão logística (variáveis
    padronizadas) e a floresta aleatória, com os parâmetros dos testes T3 e T4."""
    cfg = config()
    semente = cfg["semente"] if semente is None else semente
    c = cfg["classificacao"]
    return {"referência": None,
            "Regressão logística": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000,
                                                                                      C=c["logistica_c"])),
            "Floresta aleatória": RandomForestClassifier(c["floresta"]["n_arvores"],
                                                         min_samples_leaf=c["floresta"]["folha_min"],
                                                         random_state=semente, n_jobs=-1)}


def metricas(p: np.ndarray, y: np.ndarray, limiar: float | None = None) -> dict:
    """AUC, precisão média (AP), Brier e, com o `limiar`, a matriz de confusão (vp, fp, fn, vn), a precisão (dos
    chamados de "sim", quantos são) e o recall (dos "sim" de verdade, quantos foram achados)."""
    limiar = config()["classificacao"]["limiar"] if limiar is None else limiar
    p, y = np.asarray(p, dtype=float), np.asarray(y, dtype=int)
    prev = p >= limiar
    vp, fp = int((prev & (y == 1)).sum()), int((prev & (y == 0)).sum())
    fn, vn = int((~prev & (y == 1)).sum()), int((~prev & (y == 0)).sum())
    return {"AUC": roc_auc_score(y, p) if len(set(y)) > 1 else np.nan, "AP": average_precision_score(y, p),
            "Brier": brier_score_loss(y, p), "precisao": vp / (vp + fp) if vp + fp else np.nan,
            "recall": vp / (vp + fn) if vp + fn else np.nan, "vp": vp, "fp": fp, "fn": fn, "vn": vn,
            "previstos": float(p.sum()), "reais": int(y.sum())}


def validacao_cruzada(x: pd.DataFrame, y: pd.Series, dobras: int | None = None, repeticoes: int | None = None,
                      semente: int | None = None) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """Validação cruzada estratificada repetida: em cada repetição, as serventias são divididas em `dobras` partes com
    a mesma proporção de "sim"; cada parte é prevista por um modelo treinado nas outras. Devolve a média das métricas
    por modelo e as probabilidades "fora da dobra" da 1ª repetição (cada serventia prevista sem ter sido vista)."""
    cfg = config()
    dobras = cfg["classificacao"]["dobras"] if dobras is None else dobras
    repeticoes = cfg["classificacao"]["repeticoes"] if repeticoes is None else repeticoes
    semente = cfg["semente"] if semente is None else semente
    res: dict[str, list] = {}
    oof = {nome: np.zeros(len(y)) for nome in modelos(semente)}
    for rep in range(repeticoes):
        for tr, te in StratifiedKFold(dobras, shuffle=True, random_state=semente + rep).split(x, y):
            for nome, m in modelos(semente).items():
                p = (np.full(len(te), y.iloc[tr].mean()) if m is None
                     else m.fit(x.iloc[tr], y.iloc[tr]).predict_proba(x.iloc[te])[:, 1])
                res.setdefault(nome, []).append(metricas(p, y.iloc[te].to_numpy()))
                if rep == 0:
                    oof[nome][te] = p
    tab = pd.DataFrame({n: pd.DataFrame(v)[["AUC", "AP", "Brier", "precisao", "recall"]].mean()
                        for n, v in res.items()}).T
    return tab, oof


def importancia_permutacao(modelo, x: pd.DataFrame, y: pd.Series, grupos: dict[str, list[str]],
                           dobras: int | None = None, repeticoes: int | None = None, semente: int | None = None,
                           metrica: str = "AUC") -> pd.DataFrame:
    """Importância por permutação, medida fora da amostra: em cada dobra, o modelo treinado nas outras prevê a dobra
    com um grupo de colunas embaralhado (as linhas trocadas entre si); a importância é quanto a métrica piora
    (AUC: cai; Brier: sobe). Colunas de um mesmo grupo (por exemplo, as 13 regiões) são embaralhadas juntas."""
    cfg = config()
    dobras = cfg["classificacao"]["dobras"] if dobras is None else dobras
    repeticoes = cfg["classificacao"]["permutacao_repeticoes"] if repeticoes is None else repeticoes
    semente = cfg["semente"] if semente is None else semente
    rng = np.random.default_rng(semente)
    perdas: dict[str, list[float]] = {g: [] for g in grupos}
    for tr, te in StratifiedKFold(dobras, shuffle=True, random_state=semente).split(x, y):
        m = modelo.fit(x.iloc[tr], y.iloc[tr])
        _permutar(m, x.iloc[te], y.iloc[te].to_numpy(), grupos, repeticoes, rng, metrica, perdas)
    return _tabela_perdas(perdas)


def importancia_no_teste(modelo_ajustado, x_teste: pd.DataFrame, y_teste: pd.Series, grupos: dict[str, list[str]],
                         repeticoes: int | None = None, semente: int | None = None,
                         metrica: str = "Brier") -> pd.DataFrame:
    """A mesma importância por permutação, para a validação temporal: o modelo já treinado no passado prevê o
    período de teste com cada grupo de colunas embaralhado."""
    cfg = config()
    repeticoes = cfg["classificacao"]["permutacao_repeticoes"] if repeticoes is None else repeticoes
    rng = np.random.default_rng(cfg["semente"] if semente is None else semente)
    perdas: dict[str, list[float]] = {g: [] for g in grupos}
    _permutar(modelo_ajustado, x_teste, np.asarray(y_teste), grupos, repeticoes, rng, metrica, perdas)
    return _tabela_perdas(perdas)


def _permutar(m, xt: pd.DataFrame, yt: np.ndarray, grupos: dict, repeticoes: int, rng, metrica: str,
              perdas: dict) -> None:
    base = metricas(m.predict_proba(xt)[:, 1], yt)[metrica]
    for g, cols in grupos.items():
        for _ in range(repeticoes):
            xp = xt.copy()
            xp[cols] = xt[cols].to_numpy()[rng.permutation(len(xt))]
            valor = metricas(m.predict_proba(xp)[:, 1], yt)[metrica]
            perdas[g].append(base - valor if metrica == "AUC" else valor - base)


def _tabela_perdas(perdas: dict) -> pd.DataFrame:
    out = pd.DataFrame({"variavel": list(perdas), "perda_media": [np.mean(v) for v in perdas.values()],
                        "perda_dp": [np.std(v) for v in perdas.values()]})
    return out.sort_values("perda_media", ascending=False).reset_index(drop=True)


def coeficientes_logistica(x: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """Pesos da regressão logística com as variáveis padronizadas, ajustada em todas as linhas: o peso é a mudança no
    log da chance para 1 desvio padrão a mais na variável; a razão de chances (e^peso) diz por quanto a chance
    ("sim" ÷ "não") é multiplicada."""
    m = modelos()["Regressão logística"].fit(x, y)
    coef = m[-1].coef_[0]
    out = pd.DataFrame({"variavel": x.columns, "peso": coef, "razao_de_chances": np.exp(coef),
                        "desvio_padrao": x.std().values})
    return out.reindex(out["peso"].abs().sort_values(ascending=False).index).reset_index(drop=True)


# ---------------------------------------------------------------------------------------------------------------
# (a) Vacância
# ---------------------------------------------------------------------------------------------------------------
def base_vacancia(sv: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """As serventias providas ou vagas com receita de referência e CLT informados, como no T4: log da receita, log(1 +
    CLT), número de atribuições, as seis atribuições (0/1), log da população do município e a região intermediária
    (uma coluna 0/1 por região). Alvo: 1 = vaga."""
    s = sv[sv["situacao"].isin(["provida", "vaga"]) & (sv["receita_ref"] > 0) & sv["clt"].notna()
           & sv["populacao"].notna()].set_index("cns")
    x = pd.DataFrame({"log_receita": np.log(s["receita_ref"]), "log_clt": np.log1p(s["clt"]),
                      "n_atribuicoes": s["n_atribuicoes"].astype(float)})
    for a in ATRIBUICOES:
        x[a] = s[a].astype(int)
    x["log_pop"] = np.log(s["populacao"])
    x = pd.concat([x, pd.get_dummies(s["regiao_intermediaria"], prefix="regiao", dtype=int)], axis=1)
    return x, (s["situacao"] == "vaga").astype(int).rename("vaga")


# ---------------------------------------------------------------------------------------------------------------
# (b) Subida de classe
# ---------------------------------------------------------------------------------------------------------------
def receita_anual(serie: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Média e máximo dos semestres com valor > 0 de cada serventia em cada ano (a média é a receita de referência
    da D-010 aplicada ano a ano), em tabelas CNS × ano."""
    a = serie[serie["arrecadacao"] > 0].groupby(["cns", "ano"])["arrecadacao"].agg(["mean", "max"]).reset_index()
    return a.pivot(index="cns", columns="ano", values="mean"), a.pivot(index="cns", columns="ano", values="max")


def casos_subida(media: pd.DataFrame, maximo: pd.DataFrame, info: pd.DataFrame, ano: int, limite: float,
                 horizonte: int = 1, com_resposta: bool = True) -> pd.DataFrame:
    """Os casos de um ano-alvo: serventias com receita no ano `ano − horizonte` (e no anterior) até o `limite`. As
    variáveis vêm só desses anos (log da receita nos dois anos, crescimento, distância ao limite, log do maior
    semestre, crescimento do ano anterior) e da serventia (atribuições, população). Resposta: 1 se a receita do
    `ano` passa do limite. Com `com_resposta=False`, o ano-alvo pode ainda não ter dado (projeção)."""
    b = ano - horizonte
    if b - 1 not in media.columns or b not in media.columns:
        return pd.DataFrame()
    m1, m2 = media[b], media[b - 1]
    m3 = media[b - 2] if b - 2 in media.columns else pd.Series(np.nan, index=media.index)
    ok = m1.notna() & m2.notna() & (m1 <= limite)
    if com_resposta:
        if ano not in media.columns:
            return pd.DataFrame()
        ok &= media[ano].notna()
    d = pd.DataFrame({"ano": ano, "log_m1": np.log(m1[ok]), "log_m2": np.log(m2[ok]), "cresc": np.log(m1[ok] / m2[ok]),
                      "dist_limite": np.log(limite / m1[ok]), "log_max1": np.log(maximo[b][ok]),
                      "cresc2": np.log(m2[ok] / m3[ok]).fillna(0)})
    d["y"] = (media[ano][ok] > limite).astype(int) if com_resposta else np.nan
    d = d.join(info, how="left").reset_index(names="cns")
    return d.dropna(subset=VARIAVEIS_SUBIDA)


def info_serventias(sv: pd.DataFrame) -> pd.DataFrame:
    """Características fixas usadas na subida de classe: número de atribuições, as seis atribuições (0/1) e o log da
    população do município, por CNS."""
    s = sv.set_index("cns")
    out = pd.DataFrame({"n_atribuicoes": s["n_atribuicoes"].astype(float)})
    for a in ATRIBUICOES:
        out[a] = s[a].astype(int)
    out["log_pop"] = np.log(s["populacao"])
    return out


def painel_subida(media: pd.DataFrame, maximo: pd.DataFrame, info: pd.DataFrame, anos: range, limite: float,
                  horizonte: int = 1) -> pd.DataFrame:
    """`casos_subida` para vários anos-alvo, empilhados."""
    partes = [casos_subida(media, maximo, info, a, limite, horizonte) for a in anos]
    return pd.concat([p for p in partes if len(p)], ignore_index=True)


def floresta(semente: int | None = None) -> RandomForestClassifier:
    return modelos(semente)["Floresta aleatória"]


def _logito(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p)).reshape(-1, 1)


def recalibrador(p: np.ndarray, y: np.ndarray) -> LogisticRegression:
    """Recalibração de Platt: uma regressão logística com o logito da probabilidade do modelo como única variável
    (corrige o nível e a inclinação das probabilidades). Ajustada em anos que o modelo não viu no treino."""
    return LogisticRegression(C=1e6, max_iter=1000).fit(_logito(p), np.asarray(y, dtype=int))


def aplicar(cal: LogisticRegression, p: np.ndarray) -> np.ndarray:
    return cal.predict_proba(_logito(p))[:, 1]


def prever_subidas(painel: pd.DataFrame, casos: pd.DataFrame, horizonte: int = 1, n_cal: int | None = None,
                   semente: int | None = None) -> dict:
    """Prevê a probabilidade de subida dos `casos` sem usar nada posterior ao que se saberia na época. Com K = o
    primeiro ano-alvo dos casos − `horizonte` (o último ano com dado):
    - a floresta treina com os anos-alvo até K;
    - a recalibração usa os `n_cal` anos-alvo até K (por exemplo, 2022–23 para prever 2024), previstos por uma
      floresta treinada só com o que se sabia antes deles (anos-alvo até o 1º deles − `horizonte`).
    Devolve as probabilidades do modelo ("p") e recalibradas ("p_recal") e os casos da recalibração."""
    n_cal = config()["classificacao"]["subida"]["anos_calibracao"] if n_cal is None else n_cal
    k = int(casos["ano"].min()) - horizonte
    tr = painel[painel["ano"] <= k]
    p = floresta(semente).fit(tr[VARIAVEIS_SUBIDA], tr["y"]).predict_proba(casos[VARIAVEIS_SUBIDA])[:, 1]
    anos_cal = list(range(k - n_cal + 1, k + 1))
    cal = painel[painel["ano"].isin(anos_cal)]
    tr_cal = painel[painel["ano"] <= anos_cal[0] - horizonte]
    pc = floresta(semente).fit(tr_cal[VARIAVEIS_SUBIDA], tr_cal["y"]).predict_proba(cal[VARIAVEIS_SUBIDA])[:, 1]
    return {"p": p, "p_recal": aplicar(recalibrador(pc, cal["y"]), p), "cal_p": pc, "cal_y": cal["y"].to_numpy(),
            "anos_cal": anos_cal, "fim_treino": k}


def origem_movel_subida(painel: pd.DataFrame, inicios: range, horizonte: int = 1, n_anos: int = 2,
                        semente: int | None = None) -> pd.DataFrame:
    """Teste no passado com origem móvel: para cada ano de início, prevê os `n_anos` anos-alvo a partir dele (como em
    `prever_subidas`) e compara as subidas previstas (soma das probabilidades, com e sem recalibração) com as reais."""
    linhas = []
    for a in inicios:
        casos = painel[painel["ano"].between(a, a + n_anos - 1)]
        if casos["ano"].nunique() < n_anos:
            continue
        r = prever_subidas(painel, casos, horizonte, semente=semente)
        linhas.append({"anos": f"{a}–{a + n_anos - 1}", "inicio": a, "casos": len(casos), "reais": int(casos["y"].sum()),
                       "previstas_modelo": r["p"].sum(), "previstas_recalibradas": r["p_recal"].sum(),
                       "brier_modelo": brier_score_loss(casos["y"], r["p"]),
                       "brier_recalibrado": brier_score_loss(casos["y"], r["p_recal"])})
    out = pd.DataFrame(linhas)
    out["razao_modelo"] = out["reais"] / out["previstas_modelo"]
    out["razao_recalibrada"] = out["reais"] / out["previstas_recalibradas"]
    return out


def faixa_por_erros(central: float, razoes: pd.Series, faixa: list[float] | None = None) -> tuple[float, float, float]:
    """Faixa a partir dos erros do teste no passado (como a do T2): o central multiplicado pelos percentis da razão
    "reais ÷ previstas" das janelas da origem móvel. Devolve (P10, central, P90) com a faixa de config."""
    faixa = config()["classificacao"]["subida"]["faixa"] if faixa is None else faixa
    lo, hi = np.quantile(pd.Series(razoes, dtype=float).dropna(), faixa)
    return float(central * lo), float(central), float(central * hi)


def faixa_contagem(cal_p: np.ndarray, cal_y: np.ndarray, p_novos: np.ndarray, n: int | None = None,
                   faixa: list[float] | None = None, semente: int | None = None) -> tuple[float, float, float]:
    """Contagem esperada de subidas (soma das probabilidades recalibradas) e a faixa: em cada uma de `n` rodadas, os
    casos da recalibração são reamostrados com reposição (incerteza do ajuste) e cada serventia "sobe ou não" por
    sorteio com a sua probabilidade (acaso). Devolve (P10, central, P90) com a faixa de config."""
    cfg = config()
    sc = cfg["classificacao"]["subida"]
    n = sc["bootstrap"] if n is None else n
    faixa = sc["faixa"] if faixa is None else faixa
    semente = cfg["semente"] if semente is None else semente
    rng = np.random.default_rng(semente)
    cal_p, cal_y = np.asarray(cal_p), np.asarray(cal_y)
    central = float(aplicar(recalibrador(cal_p, cal_y), p_novos).sum())
    contagens = []
    for _ in range(n):
        i = rng.integers(0, len(cal_p), len(cal_p))
        p = aplicar(recalibrador(cal_p[i], cal_y[i]), p_novos)
        contagens.append((rng.random(len(p)) < p).sum())
    lo, hi = np.quantile(contagens, faixa)
    return float(lo), central, float(hi)


def resultado_do_teste(chave: str) -> pd.DataFrame:
    """A tabela de um teste de métodos (por exemplo, "T4_vacancia") em docs/qa/analises/testes_metodos_resultados.json,
    para o notebook comparar o seu resultado com o do teste."""
    arquivo = RAIZ / config()["graficos"]["pasta"] / "testes_metodos_resultados.json"
    return pd.DataFrame(json.loads(arquivo.read_text(encoding="utf-8"))[chave]["tabela"]).set_index("metodo")


def tabela_subidas(linhas: list[dict]) -> pd.DataFrame:
    """Tabela da entrega do 05b (insumo do notebook 07): por ano projetado, quantas serventias estavam abaixo do
    limite no ano-base, a contagem esperada de subidas e a faixa, em todas e só nas providas."""
    return pd.DataFrame(linhas, columns=["ano", "horizonte", "recorte", "abaixo_do_limite_no_ano_base", "p10",
                                         "esperado", "p90", "modelo", "anos_recalibracao"])
