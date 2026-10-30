"""Melhorias de confiança M1 a M10 (docs/plano_mineracao.md; notebook 10). Só sensibilidade e projeção: nada aqui
muda a base nem os 10 números oficiais. Parâmetros em config/analise.yaml (melhorias).

- M1, capacidade de pagar: o passivo de cada obrigada contra o saldo anual do titular no BI do CNJ (arrecadação −
  repasse − custeio). Saldo é renda, não patrimônio: calibra a chance de déficit (suposição) com um dado, sem trocar a
  regra do art. 8º, § 1º.
- M2, pergunta 9: sinistro esperado = P(fim da delegação no ano) × parte da IS que o titular não paga com a renda × IS.
- M7 e M8: o prêmio por cenário do STF e numa grade taxa × adesão.
- M10: os grupos do notebook 04 também pelo déficit da M1.
"""
import numpy as np
import pandas as pd

from src.analise import config
from src.model.mercado import FAIXA_POR_CLASSE

FAIXAS_MESES = ["< 3 meses", "3 a 12 meses", "> 12 meses", "saldo ≤ 0", "sem dado"]


def _cfg(parte: str) -> dict:
    return config()["melhorias"][parte]


def faixa_meses(meses: pd.Series, saldo: pd.Series, cortes: list[float] | None = None) -> pd.Series:
    """Faixa de "meses de saldo" (passivo ÷ saldo mensal) do F6 de 18/10: < 3, 3 a 12, > 12, saldo ≤ 0, sem dado."""
    c1, c2 = _cfg("capacidade")["cortes_meses"] if cortes is None else cortes
    out = pd.Series(np.select([saldo.isna(), saldo <= 0, meses < c1, meses <= c2],
                              ["sem dado", "saldo ≤ 0", "< 3 meses", "3 a 12 meses"], "> 12 meses"), index=meses.index)
    return pd.Categorical(out, FAIXAS_MESES, ordered=True)


def capacidade(sv: pd.DataFrame, saldo: pd.DataFrame, horizonte: float | None = None) -> pd.DataFrame:
    """As obrigadas (peso do universo > 0) com o saldo anual do titular (dados.saldo_bi), os meses de saldo que o
    passivo consome, a faixa e, com `horizonte` meses de saldo dedicados ao passivo: a capacidade (saldo × horizonte ÷
    12, nunca negativa), se o passivo passa dela (`nao_cobre`) e o que sobra sem pagar (`descoberto_m1`). Sem dado do
    BI, `nao_cobre` e `descoberto_m1` ficam vazios."""
    h = _cfg("capacidade")["horizonte_meses"] if horizonte is None else horizonte
    o = sv[sv["peso_universo"] > 0].merge(saldo, on="cns", how="left")
    o["meses_de_saldo"] = o["passivo"] / (o["saldo_anual"] / 12).where(o["saldo_anual"] > 0)
    o["faixa_meses"] = faixa_meses(o["meses_de_saldo"], o["saldo_anual"])
    o["capacidade"] = o["saldo_anual"].clip(lower=0) * h / 12
    o["nao_cobre"] = (o["passivo"] > o["capacidade"]).where(o["saldo_anual"].notna())
    o["descoberto_m1"] = (o["passivo"] - o["capacidade"]).clip(lower=0).where(o["saldo_anual"].notna())
    o["faixa_deficit"] = o["classe_faixa" if "classe_faixa" in o else "classe"].map(FAIXA_POR_CLASSE)
    return o


def tabela_faixas(cap: pd.DataFrame) -> pd.DataFrame:
    """Obrigadas (soma dos pesos), passivo das obrigadas e déficit do modelo por faixa de meses de saldo."""
    t = cap.assign(obr=cap["peso_universo"], pas=cap["passivo"] * cap["peso_universo"])
    g = t.groupby("faixa_meses", observed=False).agg(serventias=("cns", "size"), obrigadas=("obr", "sum"),
                                                     passivo_obrigadas=("pas", "sum"),
                                                     deficit_modelo=("valor_descoberto", "sum"))
    g["pct_obrigadas"] = g["obrigadas"] / g["obrigadas"].sum()
    g["pct_deficit_modelo"] = g["deficit_modelo"] / g["deficit_modelo"].sum()
    return g


def calibracao(cap: pd.DataFrame, p: dict) -> pd.DataFrame:
    """Chance de déficit e parte descoberta por faixa de déficit (Classe 2 e Classe 3): a suposição do modelo (nível
    base) ao lado da medida pela capacidade de pagar (M1), só entre as obrigadas com dado do BI, ponderadas pelo peso
    do universo. Déficit: o do modelo e o da M1 (sem dado, a M1 usa o do modelo)."""
    linhas = []
    for f, g in cap.groupby("faixa_deficit"):
        d = g[g["saldo_anual"].notna() & (g["passivo"] > 0)]
        w = d["peso_universo"]
        nc = d["nao_cobre"].astype(bool)
        linhas.append({
            "faixa_deficit": f, "obrigadas": g["peso_universo"].sum(), "com_dado_bi": w.sum(),
            "prob_deficit_modelo": p["prob_deficit"][f], "prob_deficit_m1": (w * nc).sum() / w.sum(),
            "pct_descoberto_modelo": p["pct_descoberto"][f],
            "pct_descoberto_m1": ((w * d["descoberto_m1"])[nc].sum() / (w * d["passivo"])[nc].sum()
                                  if nc.any() else np.nan),
            "deficit_modelo": g["valor_descoberto"].sum(), "deficit_m1": deficit_m1(g)})
    return pd.DataFrame(linhas).set_index("faixa_deficit")


def deficit_m1(cap: pd.DataFrame) -> float:
    """Déficit pela capacidade de pagar: Σ peso × descoberto_m1; sem dado do BI, o déficit do modelo."""
    sem = cap["descoberto_m1"].isna()
    return float((cap["peso_universo"] * cap["descoberto_m1"])[~sem].sum() + cap.loc[sem, "valor_descoberto"].sum())


def mercado_por_deficit(deficit: float, p: dict, fracao_exigencia: float = 1.0) -> dict:
    """A conta dos passos 7 e 8 a partir de um déficit: IS = déficit × exigência × parte que escolhe o seguro;
    prêmio = IS × taxa."""
    is_ = deficit * fracao_exigencia * p["escolha_garantia"]["seguro"]
    return {"deficit": deficit, "importancia_segurada": is_, "premio": is_ * p["taxa_seguro_anual"]}


def deficit_por_horizonte(sv: pd.DataFrame, saldo: pd.DataFrame, p: dict, horizontes: list[float] | None = None
                          ) -> pd.DataFrame:
    """Déficit, IS e prêmio pela M1 para cada horizonte de meses de saldo, ao lado do modelo (nível base)."""
    hs = _cfg("capacidade")["horizontes"] if horizontes is None else horizontes
    obr = sv[sv["peso_universo"] > 0]
    linhas = [{"leitura": "modelo (premissas vigentes)", "horizonte_meses": np.nan,
               **mercado_por_deficit(float(obr["valor_descoberto"].sum()), p)}]
    for h in hs:
        linhas.append({"leitura": f"M1: {h:g} meses de saldo", "horizonte_meses": h,
                       **mercado_por_deficit(deficit_m1(capacidade(sv, saldo, h)), p)})
    return pd.DataFrame(linhas)


def parte_nao_paga(cap: pd.DataFrame, p: dict) -> pd.Series:
    """Por obrigada: a parte do déficit do modelo (pct_descoberto × passivo, dado que há déficit) que o titular não
    paga com `horizonte` meses de saldo. Sem dado do BI, 1 (o titular não paga nada: conservador para a seguradora)."""
    pct = cap["faixa_deficit"].map(lambda f: p["pct_descoberto"][f])
    d = pct * cap["passivo"]
    q = ((d - cap["capacidade"]).clip(lower=0) / d.where(d > 0)).where(cap["saldo_anual"].notna(), 1.0)
    return q.fillna(0.0)


def sinistro(cap: pd.DataFrame, p: dict, p_fim: dict | None = None) -> pd.DataFrame:
    """M2 (pergunta 9): sinistro esperado por frequência × severidade. A seguradora paga quando a delegação termina
    (P(fim) no ano, notebook 05c) e o titular não paga o descoberto com a renda. Severidade q = parte da IS que vira
    sinistro: 1 sem a M1 (ninguém paga) e a média de `parte_nao_paga` ponderada pelo déficit com a M1. Sinistralidade
    = P(fim) × q ÷ taxa; resultado técnico e índice combinado com a comissão e a despesa das premissas (nível base);
    apólices (B3) = Σ n_deficit × parte que escolhe o seguro."""
    pf = _cfg("sinistro")["p_fim"] if p_fim is None else p_fim
    q_m1 = float((cap["valor_descoberto"] * parte_nao_paga(cap, p)).sum() / cap["valor_descoberto"].sum())
    m = mercado_por_deficit(float(cap["valor_descoberto"].sum()), p)
    apolices = float(cap["n_deficit"].sum() * p["escolha_garantia"]["seguro"])
    linhas = []
    for leitura, q in (("sem a M1: o titular não paga nada", 1.0), ("com a M1: paga até o horizonte de saldo", q_m1)):
        for nivel, f in pf.items():
            sin = f * q * m["importancia_segurada"]
            sinistralidade = sin / m["premio"]
            comb = sinistralidade + p["comissao"] + p["despesa_administrativa"]
            linhas.append({"leitura": leitura, "nivel_p_fim": nivel, "p_fim": f, "severidade_q": q,
                           "premio": m["premio"], "sinistro_esperado": sin, "sinistralidade": sinistralidade,
                           "indice_combinado": comb, "resultado_tecnico": m["premio"] * (1 - comb),
                           "apolices": apolices, "premio_medio": m["premio"] / apolices,
                           "sinistralidade_ses_base": p["sinistralidade"]})
    return pd.DataFrame(linhas)


def premio_por_cenario(mc: pd.DataFrame, cenarios: dict) -> pd.DataFrame:
    """M7: o prêmio (base e P5–P95 do Monte Carlo, variante independentes) em cada cenário do STF. A demanda é
    proporcional à fração exigida (fracao_exigencia_garantia), então o prêmio de cada cenário é o do "mantém" × a
    fração. `mc`: gold.analise_monte_carlo."""
    r = mc[(mc["variante"] == "independentes") & (mc["medida"] == "premio")].iloc[0]
    linhas = []
    for nome, c in cenarios["cenarios"].items():
        f = float(c.get("ajustes", {}).get("fracao_exigencia_garantia", 1.0))
        linhas.append({"cenario": nome, "fracao_exigida": f, "premio_base": r["valor_base"] * f,
                       "premio_p05": r["p05"] * f, "premio_p50": r["p50"] * f, "premio_p95": r["p95"] * f,
                       "descricao": " ".join(str(c["descricao"]).split())})
    return pd.DataFrame(linhas)


def grade_taxa_adesao(deficit: float, semente: dict, fracao_exigencia: float = 1.0) -> pd.DataFrame:
    """M8 (b): o prêmio numa grade taxa × parte que escolhe o seguro, com o déficit fixo, nos mínimos, bases e
    máximos das premissas (config/premissas). Uma linha por taxa, uma coluna por adesão."""
    taxa = semente["premissas"]["taxa_seguro_anual"]["valores"]
    ades = {n: v["seguro"] for n, v in semente["premissas"]["escolha_garantia"]["valores"].items()}
    linhas = [{"taxa": t, **{f"adesao_{a:.0%}": deficit * fracao_exigencia * a * t for a in ades.values()}}
              for t in taxa.values()]
    return pd.DataFrame(linhas).set_index("taxa")


def grupos_com_m1(cap: pd.DataFrame, tab_grupos: pd.DataFrame) -> pd.DataFrame:
    """M10: a parte de cada grupo do notebook 04 nas obrigadas, no passivo das obrigadas (dado), no déficit do modelo
    (suposição) e no déficit pela capacidade de pagar (M1, 12 meses de saldo)."""
    t = cap.merge(tab_grupos[["cns", "grupo", "nome_grupo"]], on="cns", how="inner")
    t["passivo_obr"] = t["passivo"] * t["peso_universo"]
    t["def_m1"] = np.where(t["descoberto_m1"].isna(), t["valor_descoberto"],
                           t["peso_universo"] * t["descoberto_m1"].fillna(0))
    g = t.groupby(["grupo", "nome_grupo"]).agg(obrigadas=("peso_universo", "sum"), passivo_obrigadas=("passivo_obr", "sum"),
                                               deficit_modelo=("valor_descoberto", "sum"), deficit_m1=("def_m1", "sum"))
    for c in list(g.columns):
        g[f"pct_{c}"] = g[c] / g[c].sum()
    return g.reset_index()


# ---------------------------------------------------------------- M3: teste no passado mais longo e faixa calibrada

def cobertura_faixa(erros: pd.DataFrame, metodo: str, quantis: tuple[float, float], minimo_origens: int = 5
                    ) -> pd.DataFrame:
    """Cobertura honesta da faixa da previsão: para cada origem a partir da `minimo_origens`-ésima, a faixa sai só dos
    erros das origens anteriores (quantis dados) e confere se o real de cada horizonte ficou dentro. `erros`: saída de
    previsao.origem_movel. Devolve uma linha por origem e horizonte, com `dentro`."""
    e = erros[erros["metodo"] == metodo].sort_values(["origem", "horizonte"])
    origens = sorted(e["origem"].unique(), key=lambda o: (int(o[:4]), int(o[-1])))
    linhas = []
    for k, o in enumerate(origens):
        if k < minimo_origens:
            continue
        passado = e[e["origem"].isin(origens[:k])]["erro_rel"].to_numpy()
        lo, hi = np.quantile(passado, quantis)
        for r in e[e["origem"] == o].itertuples():
            linhas.append({"origem": o, "horizonte": r.horizonte, "erro_rel": r.erro_rel, "lo": lo, "hi": hi,
                           "dentro": lo <= r.erro_rel <= hi})
    return pd.DataFrame(linhas)


def f_media_tendencia_sarima(z, h):
    """M3 (b): a média, em log, da tendência do T2 e do SARIMA (as duas melhores em janelas diferentes)."""
    from src.analise import previsao as pv
    return (pv.f_tendencia(z, h) + pv.f_sarima(z, h)) / 2


def cobertura_contagem(bt: pd.DataFrame, quantis: tuple[float, float], minimo: int = 4) -> pd.DataFrame:
    """M3 (c): faixa calibrada da contagem de serventias acima do limite (previsao.teste_contagem). Para cada linha, a
    faixa é o central × (1 + quantis dos erros relativos real ÷ central − 1 das linhas cujo ano previsto já tinha
    acontecido no ano-base dela), com pelo menos `minimo` erros; confere se o real ficou dentro."""
    b = bt.sort_values(["ano_base", "h"]).assign(erro_rel=lambda d: d["acima_real"] / d["acima_central"] - 1)
    linhas = []
    for r in b.itertuples():
        passado = b.loc[b["ano"] <= r.ano_base, "erro_rel"].to_numpy()
        if len(passado) < minimo:
            continue
        lo, hi = np.quantile(passado, quantis)
        linhas.append({"ano_base": r.ano_base, "ano": r.ano, "h": r.h, "acima_real": r.acima_real,
                       "lo": r.acima_central * (1 + lo), "hi": r.acima_central * (1 + hi),
                       "dentro": r.acima_central * (1 + lo) <= r.acima_real <= r.acima_central * (1 + hi),
                       "dentro_faixa_original": r.dentro_da_faixa})
    return pd.DataFrame(linhas)


def quantis_para_cobertura(erros: pd.DataFrame, metodo: str, alvo: float | None = None, minimo_origens: int = 5
                           ) -> tuple[tuple[float, float], float]:
    """Os quantis simétricos (q, 1 − q) mais estreitos cuja cobertura honesta (cobertura_faixa) chega a `alvo`.
    Devolve os quantis e a cobertura obtida."""
    alvo = _cfg("previsao")["cobertura_alvo"] if alvo is None else alvo
    for q in np.arange(0.10, -0.001, -0.01):
        qs = (round(float(q), 2), round(float(1 - q), 2))
        cob = cobertura_faixa(erros, metodo, qs, minimo_origens)["dentro"].mean()
        if cob >= alvo:
            return qs, float(cob)
    return (0.0, 1.0), float(cobertura_faixa(erros, metodo, (0.0, 1.0), minimo_origens)["dentro"].mean())


# ---------------------------------------------------------------- M4: desvio condicionado ao crescimento recente

def _crescimento_anterior(media: pd.DataFrame, b: int) -> pd.Series:
    if b - 1 not in media.columns:
        return pd.Series(dtype=float)
    par = media[[b - 1, b]].dropna()
    par = par[(par[b - 1] > 0) & (par[b] > 0)]
    return np.log(par[b] / par[b - 1])


def desvios_condicionados(media: pd.DataFrame, saltos: pd.DataFrame, anos_base: list[int], h: int, limite: float
                          ) -> pd.DataFrame:
    """Os desvios de previsao.desvios_individuais com o crescimento da própria serventia no ano anterior ao ano-base
    (log de r_b ÷ r_b−1), para sortear o desvio entre as que cresceram parecido (M4)."""
    from src.analise import previsao as pv
    d = pv.desvios_individuais(media, saltos, anos_base, h, limite)
    partes = []
    for b, g in d.groupby("ano_base"):
        c = _crescimento_anterior(media, b)
        partes.append(g.assign(cresc_anterior=g["cns"].map(c)))
    return pd.concat(partes, ignore_index=True)


def sortear_condicionado(receita: pd.Series, cresc: pd.Series, fatores: np.ndarray, pool: pd.DataFrame, grupos: int,
                         rng: np.random.Generator) -> np.ndarray:
    """Como previsao.sortear_receitas, mas o desvio de cada serventia é sorteado só entre os desvios do `pool` com o
    crescimento anterior no mesmo tercil (`grupos` faixas pelos quantis do pool). Sem crescimento anterior (serventia
    nova ou sem um dos anos), o desvio vem do pool inteiro."""
    p = pool.dropna(subset=["cresc_anterior"])
    cortes = np.quantile(p["cresc_anterior"], np.linspace(0, 1, grupos + 1)[1:-1])
    g_pool = np.searchsorted(cortes, p["cresc_anterior"].to_numpy())
    g_alvo = np.where(cresc.isna().to_numpy(), -1, np.searchsorted(cortes, cresc.fillna(0).to_numpy()))
    r = np.asarray(receita, dtype=float)
    d = rng.choice(pool["desvio"].to_numpy(), size=(len(fatores), len(r)))
    for k in range(grupos):
        alvo = g_alvo == k
        if alvo.any():
            d[:, alvo] = rng.choice(p["desvio"].to_numpy()[g_pool == k], size=(len(fatores), int(alvo.sum())))
    return r[None, :] * np.asarray(fatores, dtype=float)[:, None] * np.exp(d)


def teste_subidas(y: pd.Series, media: pd.DataFrame, saltos: pd.DataFrame, origens: list[int], limite: float,
                  n: int | None = None, semente: int | None = None) -> pd.DataFrame:
    """Teste no passado das subidas de classe (M4), com o mesmo desenho de previsao.teste_contagem (fator central de MG
    da tendência treinada até b, desvios dos anos-base até b − h): a contagem de subidas com o desvio sorteado do pool
    inteiro (o método do 07) e com o desvio condicionado ao crescimento anterior, contra a contagem real."""
    from src.analise import previsao as pv
    cfg = config()
    pc = cfg["previsao"]
    grupos = _cfg("subidas")["grupos_crescimento"]
    n = pc["sorteios"] if n is None else n
    rng = np.random.default_rng(cfg["semente"] if semente is None else semente)
    max_ano = int(pv.totais_anuais(y).index.max())
    linhas = []
    for b in origens:
        yb = y.loc[:f"{b}-2"]
        fat = pv.fatores_ano(pv.prever(yb, pv.PRINCIPAL, 4), yb, b)
        cresc_b = _crescimento_anterior(media, b)
        for h in (1, 2):
            if b + h > max_ano:
                continue
            par = media[[b, b + h]].dropna()
            par = par[(par[b] > 0) & (par[b + h] > 0)]
            anos_d = list(range(b - h - pc["desvios"]["anos"] + 1, b - h + 1))
            pool = desvios_condicionados(media, saltos, anos_d, h, limite)
            abaixo = (par[b].to_numpy() <= limite)[None, :]
            f = np.full(n, float(fat[b + h]))
            sub_i = (abaixo & (pv.sortear_receitas(par[b], f, pool["desvio"].to_numpy(), rng) > limite)).sum(axis=1)
            sub_c = (abaixo & (sortear_condicionado(par[b], par.index.to_series().map(cresc_b), f, pool, grupos, rng)
                               > limite)).sum(axis=1)
            linhas.append({"ano_base": b, "ano": b + h, "h": h,
                           "subidas_real": int(((par[b] <= limite) & (par[b + h] > limite)).sum()),
                           "subidas_pool_inteiro": float(np.median(sub_i)),
                           "subidas_condicionado": float(np.median(sub_c))})
    out = pd.DataFrame(linhas)
    for c in ("pool_inteiro", "condicionado"):
        out[f"erro_{c}"] = out[f"subidas_{c}"] - out["subidas_real"]
    return out


# ---------------------------------------------------------------- M5: passivo projetado

def rais_projetada(rais: pd.DataFrame, anos: int, inflacao: float) -> pd.DataFrame:
    """Os vínculos da RAIS `anos` anos depois: tempo de casa + 12 meses por ano (conta da lei) e remuneração corrigida
    pela inflação de cada ano. Contratações e desligamentos ficam fora (mesmos vínculos)."""
    r = rais.copy()
    r["tempo_emprego_meses"] = r["tempo_emprego_meses"].fillna(0) + 12 * anos
    for c in ("rem_dezembro", "rem_media"):
        r[c] = r[c] * (1 + inflacao) ** anos
    return r


def passivo_projetado(ins, p: dict, limites: dict, inflacao: float, anos: list[int]) -> pd.DataFrame:
    """M5: passivo de todas e das obrigadas (universo e classes da base) em 31/12 de cada ano projetado, pelas funções
    do modelo, e o fator sobre a base (o déficit, a IS e o prêmio do modelo são proporcionais ao passivo com o universo
    fixo). `anos`: anos depois da data-base (1 = 2026)."""
    from src.motor import Insumos, calcular_serventias
    base = calcular_serventias(ins, p, limites, limites_faixa=limites)[0]
    linhas = [{"anos_depois": 0, "passivo_todas": base["passivo"].sum(),
               "passivo_universo": (base["passivo"] * base["peso_universo"]).sum(),
               "valor_descoberto": base["valor_descoberto"].sum()}]
    for k in anos:
        ins_k = Insumos(rais=rais_projetada(ins.rais, k, inflacao), serventias=ins.serventias,
                        fator_inpc=ins.fator_inpc, mes_inpc=ins.mes_inpc, regioes=ins.regioes)
        s = calcular_serventias(ins_k, p, limites, limites_faixa=limites)[0]
        linhas.append({"anos_depois": k, "passivo_todas": s["passivo"].sum(),
                       "passivo_universo": (s["passivo"] * s["peso_universo"]).sum(),
                       "valor_descoberto": s["valor_descoberto"].sum()})
    out = pd.DataFrame(linhas)
    out["fator"] = out["valor_descoberto"] / out["valor_descoberto"].iloc[0]
    return out
