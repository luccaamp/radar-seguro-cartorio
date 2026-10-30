"""Comparação de métodos de estimação para o Radar Seguro-Garantia Cartórios (MG).

Roda sobre o silver da carga 2026-10-19 e as funções do repositório (src/model). Só lê dados.
Cada teste declara antes: a pergunta, os métodos, a validação e O INDICADOR que decide o vencedor.
Semente fixa. Explicação e resultados: docs/qa/analises/testes_metodos.md (D-039).
Uso: uv run python -I scripts/testes_metodos.py data/silver . <pasta_saida>
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
SILVER, REPO, SAIDA = map(Path, sys.argv[1:4])
SAIDA.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO))
from src.model.passivo import passivo_vinculos            # noqa: E402
from src.model.premissas import resolver                  # noqa: E402

from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor  # noqa: E402
from sklearn.linear_model import LogisticRegression, PoissonRegressor  # noqa: E402
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score  # noqa: E402
from sklearn.model_selection import GroupKFold, KFold, StratifiedKFold  # noqa: E402
from sklearn.pipeline import make_pipeline                 # noqa: E402
from sklearn.preprocessing import StandardScaler           # noqa: E402
import statsmodels.api as sm                               # noqa: E402
from statsmodels.tsa.holtwinters import ExponentialSmoothing  # noqa: E402
from statsmodels.tsa.statespace.sarimax import SARIMAX      # noqa: E402

SEED = 42
LIMITE = 300_000.0
ATR = ["notas", "rcpn", "ri", "rtd", "rcpj", "protesto"]
R = {}  # resultados


def ler(t):
    return pd.read_parquet(SILVER / f"{t}.parquet")


serv = ler("serventia")
serv = serv[(serv.uf == "MG") & (serv.status == "Ativo")].copy()
col = ler("serventia_colaboradores")
mun = ler("municipio_ibge")
arr = ler("serventia_arrecadacao")
arr = arr[(arr.versao == 1) & arr.semestre.notna() & arr.cns.isin(serv.cns)].copy()
arr["semestre"] = arr.semestre.astype(int)
rais = ler("rais_vinculo")

# receita de referência 2025 (D-010/D-023: média dos semestres de 2025 com valor > 0; conflito = indeterminada)
a25 = arr[arr.ano == 2025]
conf = set(a25.loc[a25.conflito_fonte, "cns"])
rec = a25[a25.arrecadacao > 0].groupby("cns").arrecadacao.mean().rename("receita")
base = (serv.merge(col[["cns", "clt", "informado"]], on="cns", how="left")
        .merge(rec, on="cns", how="left")
        .merge(mun[["cod_ibge", "regiao_imediata", "regiao_intermediaria", "populacao"]], on="cod_ibge", how="left"))
base.loc[base.cns.isin(conf), "receita"] = np.nan
for a in ATR:
    base[a] = base[a].fillna(False).astype(int)
base["log_receita"] = np.log(base.receita)
base["log_pop"] = np.log(base.populacao)
base["vago"] = (base.situacao_juridica == "VAGO").astype(int)
print(f"serventias ativas: {len(base)} | com receita 2025 válida: {base.receita.notna().sum()} | CLT total: {base.clt.sum():.0f}")


def kpi(nome, metodos, indicador, menor_melhor=True, extra=None):
    df = pd.DataFrame(metodos).T
    df = df.sort_values(indicador, ascending=menor_melhor)
    R[nome] = {"indicador": indicador, "menor_melhor": menor_melhor, "vencedor": df.index[0],
               "tabela": df.round(4).reset_index(names="metodo").to_dict("records"), **(extra or {})}
    print(f"\n=== {nome} | indicador: {indicador} | vencedor: {df.index[0]}")
    print(df.round(4).to_string())
    return df


# ---------------------------------------------------------------------------------------------------------------
# T1 — Empregados CLT a partir da receita (notebook 06a; uso: estados sem a contagem do CNJ)
# Indicador: MAE por serventia na validação "deixa uma região intermediária de fora" (simula um lugar não visto).
# Restrição: erro do total agregado |Σprev−Σreal|/Σreal ≤ 5% (o passivo usa o total).
# ---------------------------------------------------------------------------------------------------------------
t1 = base[base.receita.notna() & base.clt.notna() & base.regiao_intermediaria.notna()].reset_index(drop=True)
X_cols = ["log_receita", "n_atribuicoes", *ATR]
y = t1.clt.to_numpy(float)


def m_mediana_faixa(tr, te):
    q = np.quantile(tr.log_receita, np.linspace(0, 1, 11)[1:-1])
    btr, bte = np.digitize(tr.log_receita, q), np.digitize(te.log_receita, q)
    med = pd.Series(tr.clt.to_numpy()).groupby(btr).median()
    return med.reindex(bte).fillna(tr.clt.median()).to_numpy()


def m_razao(tr, te):
    return te.receita.to_numpy() * tr.clt.sum() / tr.receita.sum()


def m_ols_log(tr, te):
    Xtr, Xte = sm.add_constant(tr[X_cols].astype(float)), sm.add_constant(te[X_cols].astype(float), has_constant="add")
    fit = sm.OLS(np.log1p(tr.clt), Xtr).fit()
    smear = np.mean(np.exp(fit.resid))  # retransformação de Duan
    return np.clip(np.exp(fit.predict(Xte)) * smear - 1, 0, None)


def m_poisson(tr, te):
    m = make_pipeline(StandardScaler(), PoissonRegressor(alpha=1e-4, max_iter=1000)).fit(tr[X_cols], tr.clt)
    return m.predict(te[X_cols])


def m_negbin(tr, te):
    Xtr, Xte = sm.add_constant(tr[X_cols].astype(float)), sm.add_constant(te[X_cols].astype(float), has_constant="add")
    fit = sm.GLM(tr.clt, Xtr, family=sm.families.NegativeBinomial(alpha=0.5)).fit()
    return fit.predict(Xte)


def m_rf(tr, te):
    return RandomForestRegressor(400, min_samples_leaf=5, random_state=SEED, n_jobs=-1).fit(tr[X_cols], tr.clt).predict(te[X_cols])


def m_hgb(tr, te):
    return HistGradientBoostingRegressor(loss="poisson", max_iter=300, learning_rate=0.05, min_samples_leaf=20,
                                         random_state=SEED).fit(tr[X_cols], tr.clt).predict(te[X_cols])


M1 = {"referência: mediana por decil de receita": m_mediana_faixa, "razão (CLT por R$ de receita)": m_razao,
      "OLS log-log + smearing": m_ols_log, "Poisson (GLM)": m_poisson, "Binomial negativa (GLM)": m_negbin,
      "Floresta aleatória": m_rf, "Gradient boosting (Poisson)": m_hgb}


def cv_reg(splitter, groups=None):
    out = {}
    for nome, f in M1.items():
        pred = np.zeros(len(t1))
        agg = []
        for tr_i, te_i in splitter.split(t1, groups=groups):
            p = f(t1.iloc[tr_i], t1.iloc[te_i])
            pred[te_i] = p
            agg.append(abs(p.sum() - y[te_i].sum()) / y[te_i].sum())
        out[nome] = {"MAE": np.mean(np.abs(pred - y)), "RMSE": np.sqrt(np.mean((pred - y) ** 2)),
                     "R2": 1 - np.sum((pred - y) ** 2) / np.sum((y - y.mean()) ** 2),
                     "erro_total_medio_pct": 100 * np.mean(agg)}
    return out


cv10 = cv_reg(KFold(10, shuffle=True, random_state=SEED))
loro = cv_reg(GroupKFold(t1.regiao_intermediaria.nunique()), groups=t1.regiao_intermediaria)
t1tab = {k: {"MAE_regiao_fora": loro[k]["MAE"], "MAE_10fold": cv10[k]["MAE"], "RMSE_regiao_fora": loro[k]["RMSE"],
             "R2_regiao_fora": loro[k]["R2"], "erro_total_regiao_fora_pct": loro[k]["erro_total_medio_pct"]} for k in M1}
kpi("T1_empregados_pela_receita", t1tab, "MAE_regiao_fora",
    extra={"n": len(t1), "n_regioes": int(t1.regiao_intermediaria.nunique()), "media_clt": float(y.mean())})

# ---------------------------------------------------------------------------------------------------------------
# T2 — Previsão da arrecadação semestral de MG (notebook 07)
# Indicador: MAPE médio em origem móvel (treina até 2019-2, 2020-2, ..., 2023-2; prevê 4 semestres à frente).
# Também o teste do plano: treina até 2023-2 e prevê 2024-1 a 2025-2.
# ---------------------------------------------------------------------------------------------------------------
ser = arr.groupby(["ano", "semestre"]).arrecadacao.sum().sort_index()
ser.index = [f"{a}-{s}" for a, s in ser.index]
hist = ser.loc[:"2025-2"]          # 2026-1 tem 57 "não informado": só conferência
y2 = np.log(hist.to_numpy())
H = 4


def f_naive(z, h):
    return np.repeat(z[-1], h)


def f_snaive(z, h):
    return np.array([z[-2 + (i % 2)] for i in range(h)])


def f_snaive_drift(z, h):
    g = (z[-1] - z[-3] + z[-2] - z[-4]) / 2            # crescimento anual médio (log) do último ano
    return np.array([z[-2 + (i % 2)] + g * (1 + i // 2) for i in range(h)])


def _tend(z, h, janela=None):
    zz = z[-janela:] if janela else z
    n = len(zz); t = np.arange(n); s2 = (np.arange(len(z))[-n:] % 2)
    X = np.column_stack([np.ones(n), t, s2]); b = np.linalg.lstsq(X, zz, rcond=None)[0]
    tf = np.arange(n, n + h); sf = (np.arange(len(z), len(z) + h) % 2)
    return np.column_stack([np.ones(h), tf, sf]) @ b


def f_tend_tudo(z, h):
    return _tend(z, h)


def f_tend_8(z, h):
    return _tend(z, h, 8)


def f_hw(z, h):
    return ExponentialSmoothing(z, trend="add", damped_trend=True, seasonal="add", seasonal_periods=2,
                                initialization_method="estimated").fit().forecast(h)


def f_sarima(z, h):
    return SARIMAX(z, order=(0, 1, 1), seasonal_order=(0, 1, 1, 2)).fit(disp=False).forecast(h)


M2 = {"referência: último semestre": f_naive, "sazonal ingênuo (mesmo semestre do ano anterior)": f_snaive,
      "sazonal + crescimento do último ano": f_snaive_drift, "tendência log-linear (toda a série)": f_tend_tudo,
      "tendência log-linear (últimos 8 semestres)": f_tend_8, "Holt-Winters amortecido (log)": f_hw,
      "SARIMA(0,1,1)(0,1,1)2 (log)": f_sarima}
idx = list(hist.index)
origens = [idx.index(o) for o in ["2019-2", "2020-2", "2021-2", "2022-2", "2023-2"]]
escala = np.mean(np.abs(np.diff(hist.to_numpy(), 2)))   # MASE: erro do sazonal ingênuo no treino
t2, erros_rel = {}, {}
for nome, f in M2.items():
    apes, mases, rel = [], [], []
    for o in origens:
        real = hist.to_numpy()[o + 1:o + 1 + H]
        prev = np.exp(f(y2[:o + 1], H))[:len(real)]
        apes += list(np.abs(prev - real) / real); mases.append(np.mean(np.abs(prev - real)) / escala)
        rel.append((real - prev) / prev)
    o = idx.index("2023-2")
    prev = np.exp(f(y2[:o + 1], H)); real = hist.to_numpy()[o + 1:o + 5]
    t2[nome] = {"MAPE_origem_movel_pct": 100 * np.mean(apes), "MASE_origem_movel": np.mean(mases),
                "MAPE_treino_ate_2023_pct": 100 * np.mean(np.abs(prev - real) / real),
                "vies_2024_2025_pct": 100 * np.mean((prev - real) / real)}
    erros_rel[nome] = np.concatenate(rel)
real_26 = float(ser.get("2026-1", np.nan))
for nome, f in M2.items():   # conferência extra: 2026-1 já saiu (parcial, 57 "não informado" = piso)
    t2[nome]["prev_2026_1_bi"] = float(np.exp(f(y2, 1))[0]) / 1e9
    t2[nome]["realizado_parcial_acima_da_prev_pct"] = 100 * (real_26 / np.exp(f(y2, 1))[0] - 1)
d2 = kpi("T2_previsao_arrecadacao_MG", t2, "MAPE_origem_movel_pct")
venc2 = d2.index[0]
fut = np.exp(M2[venc2](y2, 4))
e = erros_rel[venc2]                       # faixa empírica: quantis dos erros relativos do teste no passado
faixa = [(float(v * (1 + np.quantile(e, 0.1))), float(v), float(v * (1 + np.quantile(e, 0.9)))) for v in fut]
R["T2_previsao_arrecadacao_MG"]["previsao_2026_2027_bi"] = {
    p: [round(x / 1e9, 3) for x in f3] for p, f3 in zip(["2026-1", "2026-2", "2027-1", "2027-2"], faixa)}
R["T2_previsao_arrecadacao_MG"]["realizado_2026_1_parcial_bi"] = round(float(ser.get("2026-1", np.nan)) / 1e9, 3)
R["T2_previsao_arrecadacao_MG"]["serie_bi"] = {k: round(v / 1e9, 4) for k, v in hist.items()}
print("previsão (P10, central, P90), R$ bi:", R["T2_previsao_arrecadacao_MG"]["previsao_2026_2027_bi"],
      "| 2026-1 realizado (parcial):", R["T2_previsao_arrecadacao_MG"]["realizado_2026_1_parcial_bi"])

# ---------------------------------------------------------------------------------------------------------------
# T3 — Subida de classe: a serventia abaixo de R$ 300 mil no ano t−1 passa do limite no ano t? (notebook 05b)
# Validação temporal: treina com t ≤ 2023, testa em t = 2024 e 2025. Sem variável do próprio ano t.
# Indicador: Brier (erro quadrático da probabilidade) — porque a projeção SOMA probabilidades para contar
# quantas sobem. Também: AP (precisão média), AUC e o erro da contagem prevista.
# ---------------------------------------------------------------------------------------------------------------
anual = arr[arr.arrecadacao > 0].groupby(["cns", "ano"]).arrecadacao.agg(["mean", "max"]).reset_index()
piv = anual.pivot(index="cns", columns="ano", values="mean")
pmax = anual.pivot(index="cns", columns="ano", values="max")
info = base.set_index("cns")[["n_atribuicoes", *ATR, "log_pop"]]
linhas = []
for t in range(2011, 2026):
    if t - 2 not in piv.columns:
        continue
    m1, m2, m3 = piv[t - 1], piv[t - 2], piv.get(t - 3)
    ok = m1.notna() & m2.notna() & (m1 <= LIMITE) & piv[t].notna()
    d = pd.DataFrame({"ano": t, "log_m1": np.log(m1[ok]), "log_m2": np.log(m2[ok]),
                      "cresc": np.log(m1[ok] / m2[ok]), "dist_limite": np.log(LIMITE / m1[ok]),
                      "log_max1": np.log(pmax[t - 1][ok]),
                      "cresc2": np.log(m2[ok] / m3[ok]) if m3 is not None else np.nan,
                      "y": (piv[t][ok] > LIMITE).astype(int)})
    linhas.append(d.join(info, how="left"))
t3 = pd.concat(linhas).reset_index(names="cns").fillna({"cresc2": 0})
F3 = ["log_m1", "log_m2", "cresc", "dist_limite", "log_max1", "cresc2", "n_atribuicoes", *ATR, "log_pop"]
t3 = t3.dropna(subset=F3)
tr3, te3 = t3[t3.ano <= 2023], t3[t3.ano >= 2024]
taxa_hist = tr3[tr3.ano >= 2019].y.mean()
g_ult = tr3[tr3.ano == 2023].cresc.median()


def avalia_clf(p, ytrue):
    return {"Brier": brier_score_loss(ytrue, p), "AP": average_precision_score(ytrue, p),
            "AUC": roc_auc_score(ytrue, p) if len(set(ytrue)) > 1 else np.nan,
            "previstas": float(np.sum(p)), "reais": int(np.sum(ytrue))}


regra = (te3.log_m1 + te3.cresc >= np.log(LIMITE)).astype(float)
cal = tr3[tr3.ano >= 2019]
p_regra = np.where(regra == 1, ((cal.log_m1 + cal.cresc >= np.log(LIMITE)) & (cal.y == 1)).sum()
                   / max(1, (cal.log_m1 + cal.cresc >= np.log(LIMITE)).sum()),
                   ((cal.log_m1 + cal.cresc < np.log(LIMITE)) & (cal.y == 1)).sum()
                   / max(1, (cal.log_m1 + cal.cresc < np.log(LIMITE)).sum()))
mods3 = {"Regressão logística": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0)),
         "Floresta aleatória": RandomForestClassifier(500, min_samples_leaf=10, random_state=SEED, n_jobs=-1),
         "Gradient boosting": HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, min_samples_leaf=30,
                                                             random_state=SEED)}
t3tab = {"referência: taxa histórica (2019–2023)": avalia_clf(np.full(len(te3), taxa_hist), te3.y),
         "referência: regra 'repete o crescimento'": avalia_clf(p_regra, te3.y)}
for nome, m in mods3.items():
    m.fit(tr3[F3], tr3.y)
    t3tab[nome] = avalia_clf(m.predict_proba(te3[F3])[:, 1], te3.y)
kpi("T3_subida_de_classe", t3tab, "Brier",
    extra={"n_treino": len(tr3), "n_teste": len(te3), "taxa_base_teste": float(te3.y.mean())})

# ---------------------------------------------------------------------------------------------------------------
# T4 — Vacância: a serventia ativa está vaga? (notebook 05a). Só providas × vagas.
# Validação cruzada estratificada 5×3 (repetida). Indicador: AUC (o plano pede AUC; base 32% vagas, não é raro).
# Vazamento declarado: a receita e o CLT de uma vaga são medidos já sob interino.
# ---------------------------------------------------------------------------------------------------------------
t4 = base[base.situacao_juridica.isin(["PROVIDO", "VAGO"]) & base.receita.notna() & base.clt.notna()].copy()
t4["log_clt"] = np.log1p(t4.clt)
t4 = pd.concat([t4, pd.get_dummies(t4.regiao_intermediaria, prefix="ri_", dtype=int)], axis=1)
F4 = ["log_receita", "log_clt", "n_atribuicoes", *ATR, "log_pop", *[c for c in t4 if c.startswith("ri__")]]
t4 = t4.dropna(subset=F4)
mods4 = {"referência: proporção de vagas": None, **mods3}
res4 = {k: [] for k in mods4}
for rep in range(3):
    for tr_i, te_i in StratifiedKFold(5, shuffle=True, random_state=SEED + rep).split(t4, t4.vago):
        tr, te = t4.iloc[tr_i], t4.iloc[te_i]
        for nome, m in mods4.items():
            p = np.full(len(te), tr.vago.mean()) if m is None else m.fit(tr[F4], tr.vago).predict_proba(te[F4])[:, 1]
            res4[nome].append(avalia_clf(p, te.vago.to_numpy()))
t4tab = {k: {m: float(np.nanmean([d[m] for d in v])) for m in ["AUC", "AP", "Brier"]} for k, v in res4.items()}
kpi("T4_vacancia", t4tab, "AUC", menor_melhor=False, extra={"n": len(t4), "pct_vagas": float(t4.vago.mean())})

# ---------------------------------------------------------------------------------------------------------------
# T5 — Salário de dezembro ausente (D-015: 887 vínculos excluídos). Imputar ou excluir?
# Teste: esconde 20% dos salários CONHECIDOS (5 repetições) e mede o erro no PASSIVO por vínculo
# (função oficial passivo_vinculos, premissas v002 base). Indicador: erro absoluto médio % do passivo.
# Observação: só 154 dos 887 têm rem_media > 0; os outros 733 não têm nenhum salário no ano.
# ---------------------------------------------------------------------------------------------------------------
sem = yaml.safe_load((REPO / "config/premissas/premissas_v002.yaml").read_text(encoding="utf-8"))
P = resolver(sem, "base")
v = rais[rais.ativo_31_12 & rais.tipo_vinculo.isin([10, 15, 20, 25])].copy()
v["meses"] = v.tempo_emprego_meses.fillna(0)
v = v.merge(mun[["cod_ibge", "regiao_imediata"]], on="cod_ibge", how="left")
conh = v[v.rem_dezembro > 0].reset_index(drop=True)
rng = np.random.default_rng(SEED)
pv = lambda sal, mes: passivo_vinculos(pd.DataFrame({"salario": sal, "meses_servico": mes}), P).to_numpy()
t5 = {k: [] for k in ["referência: excluir (D-015) = média do grupo", "mediana da região imediata",
                      "rem_media × razão dez/média", "regressão (tempo, região, rem_media)"]}
for rep in range(5):
    msk = rng.random(len(conh)) < 0.2
    tr, te = conh[~msk], conh[msk]
    real = pv(te.rem_dezembro.to_numpy(), te.meses.to_numpy())
    # excluir = os escondidos ficam com o passivo médio do resto do município (é o que o rateio faz na prática)
    pm = pd.Series(pv(tr.rem_dezembro.to_numpy(), tr.meses.to_numpy()), index=tr.index).groupby(tr.cod_ibge).mean()
    p_exc = te.cod_ibge.map(pm).fillna(pm.mean()).to_numpy()
    med_reg = tr.groupby("regiao_imediata").rem_dezembro.median()
    s_reg = te.regiao_imediata.map(med_reg).fillna(tr.rem_dezembro.median()).to_numpy()
    razao = (tr.rem_dezembro / tr.rem_media).median()
    s_raz = np.where(te.rem_media > 0, te.rem_media * razao, s_reg)
    Xr = lambda d: np.column_stack([d.meses, np.log1p(d.rem_media.fillna(0)),
                                    d.regiao_imediata.astype("category").cat.codes])
    hgb = HistGradientBoostingRegressor(max_iter=300, random_state=SEED).fit(Xr(tr), np.log(tr.rem_dezembro))
    s_hgb = np.exp(hgb.predict(Xr(te)))
    for nome, prev in zip(t5, [p_exc, pv(s_reg, te.meses.to_numpy()), pv(s_raz, te.meses.to_numpy()),
                               pv(s_hgb, te.meses.to_numpy())]):
        t5[nome].append({"erro_abs_medio_pct": 100 * np.mean(np.abs(prev - real)) / np.mean(real),
                         "vies_total_pct": 100 * (prev.sum() - real.sum()) / real.sum()})
t5tab = {k: {m: float(np.mean([d[m] for d in vv])) for m in ["erro_abs_medio_pct", "vies_total_pct"]} for k, vv in t5.items()}
z = v[~(v.rem_dezembro > 0)].copy()
# efeito no passivo médio por vínculo de MG se os 887 entrassem: salário = rem_media × razão (154) ou mediana da
# região imediata (733), com o tempo de casa REAL deles (mediana 85 meses, maior que a dos demais)
razao = (conh.rem_dezembro / conh.rem_media).median()
med_reg = conh.groupby("regiao_imediata").rem_dezembro.median()
z["sal"] = np.where(z.rem_media > 0, z.rem_media * razao, z.regiao_imediata.map(med_reg).fillna(conh.rem_dezembro.median()))
pm_sem = conh.passivo.mean() if "passivo" in conh else pv(conh.rem_dezembro.to_numpy(), conh.meses.to_numpy()).mean()
p_z = pv(z.sal.to_numpy(), z.meses.to_numpy())
pm_com = (pv(conh.rem_dezembro.to_numpy(), conh.meses.to_numpy()).sum() + p_z.sum()) / (len(conh) + len(z))
kpi("T5_salario_dezembro_ausente", t5tab, "erro_abs_medio_pct",
    extra={"n_conhecidos": len(conh), "n_sem_dezembro": len(z), "n_sem_dezembro_com_rem_media": int((z.rem_media > 0).sum()),
           "mediana_meses_sem_dezembro": float(z.meses.median()), "mediana_meses_conhecidos": float(conh.meses.median()),
           "passivo_medio_vinculo_MG_excluindo": float(pm_sem), "passivo_medio_vinculo_MG_incluindo_imputado": float(pm_com),
           "efeito_incluir_pct": float(100 * (pm_com / pm_sem - 1))})
print("efeito de incluir os 887 imputados no passivo médio por vínculo de MG: %+.1f%%" % R["T5_salario_dezembro_ausente"]["efeito_incluir_pct"])

# ---------------------------------------------------------------------------------------------------------------
# T6 — Reserva da distribuição salarial para município com poucos vínculos (D-008, D-022)
# Teste: nos municípios com ≥ 20 vínculos, finge que só se viu uma amostra de k vínculos (k = 5 e 10, 30 sorteios)
# e prevê o passivo médio REAL do município (todos os vínculos). Indicador: erro absoluto médio % (ponderado
# pelo nº de vínculos), com k = 5 (o caso típico: mediana de 4 vínculos por município em MG).
# ---------------------------------------------------------------------------------------------------------------
conh["passivo"] = pv(conh.rem_dezembro.to_numpy(), conh.meses.to_numpy())
cnt = conh.groupby("cod_ibge").size()
grandes = cnt[cnt >= 20].index
t6res = {k: {} for k in [5, 10]}
for k in [5, 10]:
    acc = {n: [] for n in ["amostra do próprio município", "estado (sem o município)",
                           "região imediata (sem o município) = D-022", "encolhimento: amostra → região (Bayes empírico)"]}
    for cod in grandes:
        g = conh[conh.cod_ibge == cod]; real = g.passivo.mean(); w = len(g)
        resto = conh[conh.cod_ibge != cod]
        reg = g.regiao_imediata.iloc[0]
        rr = resto[resto.regiao_imediata == reg].passivo
        reg_m = rr.mean() if len(rr) >= 20 else resto.passivo.mean()
        # variâncias estimadas SEM o município testado (nada dele entra no peso, além da amostra de k)
        outros = conh[conh.cod_ibge.isin(grandes) & (conh.cod_ibge != cod)]
        tau2 = max(outros.groupby("cod_ibge").passivo.mean().var(), 1e-9)      # entre municípios
        sig2 = outros.groupby("cod_ibge").passivo.var().mean()                  # dentro do município (média)
        for _ in range(30):
            s = g.passivo.sample(k, random_state=int(rng.integers(1e9)))
            lam = tau2 / (tau2 + sig2 / k)
            prevs = [s.mean(), resto.passivo.mean(), reg_m, lam * s.mean() + (1 - lam) * reg_m]
            for n, p_ in zip(acc, prevs):
                acc[n].append((abs(p_ - real) / real, w))
    t6res[k] = {n: 100 * np.average([a for a, _ in l], weights=[b for _, b in l]) for n, l in acc.items()}
t6tab = {n: {"erro_pct_k5": t6res[5][n], "erro_pct_k10": t6res[10][n]} for n in t6res[5]}
kpi("T6_reserva_distribuicao_salarial", t6tab, "erro_pct_k5", extra={"n_municipios_teste": len(grandes)})

# ---------------------------------------------------------------------------------------------------------------
# T7 — Propagação da incerteza das suposições (passos 5 a 8 da escada)
# Não há valor real para comparar (patrimônio e taxa não são públicos). Então o critério NÃO é acurácia:
# compara como cada método monta a faixa. Atual: todos no min / todos no max ("cantos").
# Alternativa: Monte Carlo (cada suposição sorteada de forma independente entre min e max).
# Indicador: probabilidade de o resultado cair fora da faixa publicada, ou seja, quão "honesta" é a faixa.
# Passivo fixo no nível base (gold.simulador_base_classe, variante 1).
# ---------------------------------------------------------------------------------------------------------------
bc = pd.read_parquet(REPO / "data/publico/gold.simulador_base_classe.parquet").query("variante_id == 1").set_index("faixa")
PP = {f: float(bc.at[f, "passivo_ponderado"]) for f in ["classe_2", "classe_3"]}
pr = sem["premissas"]
tri = {"prob2": pr["prob_deficit"]["valores"]["classe_2"], "prob3": pr["prob_deficit"]["valores"]["classe_3"],
       "pct2": pr["pct_descoberto"]["valores"]["classe_2"], "pct3": pr["pct_descoberto"]["valores"]["classe_3"],
       "seguro": {n: pr["escolha_garantia"]["valores"][n]["seguro"] for n in ["min", "base", "max"]},
       "taxa": pr["taxa_seguro_anual"]["valores"]}


def premio(x):
    defi = x["prob2"] * x["pct2"] * PP["classe_2"] + x["prob3"] * x["pct3"] * PP["classe_3"]
    return defi, defi * x["seguro"], defi * x["seguro"] * x["taxa"]


cantos = {n: premio({k: tri[k][n] for k in tri}) for n in ["min", "base", "max"]}
N = 200_000
rng = np.random.default_rng(SEED)
t7 = {}


def inv_tri(u, a, m, b):
    c = (m - a) / (b - a)
    return np.where(u < c, a + np.sqrt(u * (b - a) * (m - a)), b - np.sqrt((1 - u) * (b - a) * (b - m)))


for dist in ["triangular", "uniforme", "PERT", "triangular, patrimônio correlacionado"]:
    x = {}
    u_pat = rng.random(N)   # um sorteio só para as 4 suposições de patrimônio (prob e pct das duas classes)
    for k, d in tri.items():
        a, m, b = d["min"], d["base"], d["max"]
        if dist == "triangular":
            x[k] = rng.triangular(a, m, b, N)
        elif dist == "uniforme":
            x[k] = rng.uniform(a, b, N)
        elif dist == "PERT":
            al = 1 + 4 * (m - a) / (b - a); be = 1 + 4 * (b - m) / (b - a)
            x[k] = a + (b - a) * rng.beta(al, be, N)
        else:
            x[k] = inv_tri(u_pat if k.startswith(("prob", "pct")) else rng.random(N), a, m, b)
    _, is_, pm_ = premio(x)
    t7[f"Monte Carlo {dist}"] = {"P5_mil": np.quantile(pm_, .05) / 1e3, "P50_mil": np.median(pm_) / 1e3,
                                 "P95_mil": np.quantile(pm_, .95) / 1e3,
                                 "largura_P5_P95_mil": (np.quantile(pm_, .95) - np.quantile(pm_, .05)) / 1e3,
                                 "pct_sorteios_ate_2x_canto_min": 100 * np.mean(pm_ <= 2 * cantos["min"][2]),
                                 "pct_sorteios_acima_metade_canto_max": 100 * np.mean(pm_ >= cantos["max"][2] / 2)}
t7["Cantos (todos min / todos max) — atual"] = {"P5_mil": cantos["min"][2] / 1e3, "P50_mil": cantos["base"][2] / 1e3,
                                                "P95_mil": cantos["max"][2] / 1e3,
                                                "largura_P5_P95_mil": (cantos["max"][2] - cantos["min"][2]) / 1e3,
                                                "pct_sorteios_ate_2x_canto_min": np.nan,
                                                "pct_sorteios_acima_metade_canto_max": np.nan}
# tornado: cada suposição sozinha do min ao max, as outras no base
torn = {}
for k in tri:
    lo = premio({kk: tri[kk]["base"] for kk in tri} | {k: tri[k]["min"]})[2]
    hi = premio({kk: tri[kk]["base"] for kk in tri} | {k: tri[k]["max"]})[2]
    torn[k] = {"min_mil": lo / 1e3, "max_mil": hi / 1e3, "amplitude_mil": (hi - lo) / 1e3}
R["T7_incerteza_premio"] = {"indicador": "largura e cobertura declarada da faixa (sem valor real para acurácia)",
                            "tabela": pd.DataFrame(t7).T.round(2).reset_index(names="metodo").to_dict("records"),
                            "cantos_conferencia_mil": {n: round(c[2] / 1e3, 1) for n, c in cantos.items()},
                            "tornado": pd.DataFrame(torn).T.sort_values("amplitude_mil", ascending=False).round(1)
                            .reset_index(names="suposicao").to_dict("records")}
print("\n=== T7"); print(pd.DataFrame(t7).T.round(1).to_string()); print(pd.DataFrame(torn).T.sort_values("amplitude_mil").round(1))
print("cantos (R$ mil):", R["T7_incerteza_premio"]["cantos_conferencia_mil"])

(SAIDA / "resultados.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
print("\nok ->", SAIDA / "resultados.json")