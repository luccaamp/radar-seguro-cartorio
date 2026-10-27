"""Previsão do mercado (notebook 07): arrecadação de MG em 2026 e 2027 (teste T2) e a projeção do universo, do
passivo, da IS e do prêmio. Só análise e sempre PROJEÇÃO: nada muda a base nem os 10 números oficiais.

Os métodos de previsão trabalham no log da série semestral (que começa num 1º semestre). O universo e o prêmio saem
das funções do modelo (src/model/universo.py e src/model/simulador.py), sobre as serventias do motor com a receita
de referência projetada; o passivo de cada serventia fica o da base (D-005: o rateio padrão, por empregados do CNJ,
não depende da receita).
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

from src.analise import config
from src.model.simulador import resumo_por_totais, totais
from src.model.universo import universo
from src.motor import peso_indeterminada, premissas_nivel

PRINCIPAL = "tendência log-linear (toda a série)"
REFERENCIA = "referência: último semestre"


# ---------------------------------------------------------------- série de MG

def serie_mg(serie: pd.DataFrame) -> pd.Series:
    """Arrecadação total de MG por semestre ("2025-2"), em ordem. `serie`: saída de dados.serie_arrecadacao."""
    t = serie.groupby(["ano", "semestre"])["arrecadacao"].sum().sort_index()
    t.index = [f"{a}-{s}" for a, s in t.index]
    return t.rename("arrecadacao")


def completar_semestre(serie: pd.DataFrame, periodo: str, referencia: str) -> tuple[pd.DataFrame, dict]:
    """Sensibilidade: quem não informou o `periodo` recebe o próprio valor do `referencia` multiplicado pelo
    crescimento de quem informou os dois (soma no `periodo` ÷ soma no `referencia`). Devolve a série alterada e um
    resumo (quantas serventias, o crescimento usado e o valor acrescentado)."""
    s = serie.copy()
    ref = s[s["periodo"] == referencia].set_index("cns")["arrecadacao"]
    alvo = s["periodo"] == periodo
    faltam = alvo & ~s["informado"]
    ambos = s[alvo & s["informado"]].set_index("cns")["arrecadacao"]
    comuns = ambos.index.intersection(ref[ref > 0].index)
    cresc = float(ambos[comuns].sum() / ref[comuns].sum())
    novo = s.loc[faltam, "cns"].map(ref).fillna(0) * cresc
    acrescimo = float((novo - s.loc[faltam, "arrecadacao"].fillna(0)).sum())
    s.loc[faltam, "arrecadacao"] = novo
    return s, {"serventias": int(faltam.sum()), "crescimento": cresc, "acrescimo": acrescimo}


# ---------------------------------------------------------------- métodos do T2 (log da série; z começa num 1º semestre)

def _tendencia(z: np.ndarray, h: int, janela: int | None = None, quebra: int | None = None) -> np.ndarray:
    """Reta no log com efeito de semestre: log(y) = a + b·t + c·(2º semestre) [+ d·(t ≥ quebra)], por mínimos
    quadrados. Com `quebra` (posição na série), a previsão continua no nível novo."""
    n0 = len(z)
    t = np.arange(n0)
    if janela:
        t = t[-janela:]
    def x(tt):
        cols = [np.ones(len(tt)), tt, tt % 2]
        if quebra is not None:
            cols.append((tt >= quebra).astype(float))
        return np.column_stack(cols)
    b = np.linalg.lstsq(x(t), z[t], rcond=None)[0]
    return x(np.arange(n0, n0 + h)) @ b


def f_naive(z, h):
    return np.repeat(z[-1], h)


def f_snaive(z, h):
    return np.array([z[-2 + (i % 2)] for i in range(h)])


def f_snaive_drift(z, h):
    g = (z[-1] - z[-3] + z[-2] - z[-4]) / 2            # crescimento anual médio (log) do último ano
    return np.array([z[-2 + (i % 2)] + g * (1 + i // 2) for i in range(h)])


def f_tendencia(z, h):
    return _tendencia(z, h)


def f_tendencia_8(z, h):
    return _tendencia(z, h, janela=8)


def f_holt_winters(z, h):
    return ExponentialSmoothing(z, trend="add", damped_trend=True, seasonal="add", seasonal_periods=2,
                                initialization_method="estimated").fit().forecast(h)


def f_sarima(z, h):
    return SARIMAX(z, order=(0, 1, 1), seasonal_order=(0, 1, 1, 2)).fit(disp=False).forecast(h)


# Os nomes são os do T2 (scripts/testes_metodos.py), para comparar com testes_metodos_resultados.json
METODOS = {REFERENCIA: f_naive, "sazonal ingênuo (mesmo semestre do ano anterior)": f_snaive,
           "sazonal + crescimento do último ano": f_snaive_drift, PRINCIPAL: f_tendencia,
           "tendência log-linear (últimos 8 semestres)": f_tendencia_8, "Holt-Winters amortecido (log)": f_holt_winters,
           "SARIMA(0,1,1)(0,1,1)2 (log)": f_sarima}


def prever(y: pd.Series, metodo, h: int) -> pd.Series:
    """Previsão em R$ dos `h` semestres depois do último de `y`, com um método de METODOS (ou outra função z, h)."""
    f = METODOS[metodo] if isinstance(metodo, str) else metodo
    return pd.Series(np.exp(f(np.log(y.to_numpy()), h)), index=proximos_periodos(y.index[-1], h))


def proximos_periodos(ultimo: str, h: int) -> list[str]:
    a, s = map(int, ultimo.split("-"))
    out = []
    for _ in range(h):
        a, s = (a, 2) if s == 1 else (a + 1, 1)
        out.append(f"{a}-{s}")
    return out


def origem_movel(y: pd.Series, metodos: dict | None = None, origens: list[str] | None = None,
                 h: int | None = None, teste: str = "2023-2") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Teste no passado com origem móvel (T2): para cada origem, treina até ela e prevê os `h` semestres seguintes.
    Indicadores por método: MAPE médio (%), MASE (erro médio ÷ erro médio do sazonal ingênuo no histórico), MAPE e
    viés do treino até `teste` (o teste do plano: 2024–25). Devolve a tabela e os erros, um por origem e horizonte
    (erro relativo = real ÷ previsto − 1, a base da faixa)."""
    cfg = config()["previsao"]
    metodos = METODOS if metodos is None else metodos
    origens = cfg["origens"] if origens is None else origens
    h = cfg["horizonte"] if h is None else h
    v = y.to_numpy()
    escala = np.mean(np.abs(v[2:] - v[:-2]))      # sazonal ingênuo: cada semestre repete o do ano anterior
    idx = list(y.index)
    linhas, erros = [], []
    for nome, f in metodos.items():
        apes, mases = [], []
        for o in origens:
            i = idx.index(o)
            real = v[i + 1:i + 1 + h]
            prev = np.exp(f(np.log(v[:i + 1]), h))[:len(real)]
            apes += list(np.abs(prev - real) / real)
            mases.append(np.mean(np.abs(prev - real)) / escala)
            erros += [{"metodo": nome, "origem": o, "horizonte": k + 1, "periodo": idx[i + 1 + k], "previsto": p,
                       "real": r, "erro_rel": r / p - 1} for k, (p, r) in enumerate(zip(prev, real))]
        i = idx.index(teste)
        real = v[i + 1:i + 1 + h]
        prev = np.exp(f(np.log(v[:i + 1]), h))[:len(real)]
        linhas.append({"metodo": nome, "MAPE_origem_movel_pct": 100 * np.mean(apes), "MASE_origem_movel": np.mean(mases),
                       "MAPE_teste_pct": 100 * np.mean(np.abs(prev - real) / real),
                       "vies_teste_pct": 100 * np.mean((prev - real) / real)})
    tab = pd.DataFrame(linhas).sort_values("MAPE_origem_movel_pct").set_index("metodo")
    return tab, pd.DataFrame(erros)


def faixa(previsao: pd.Series, erros_rel: pd.Series, quantis: list[float] | None = None) -> pd.DataFrame:
    """Faixa empírica (T2): a previsão multiplicada por (1 + os quantis dos erros relativos do teste no passado)."""
    q = config()["previsao"]["faixa"] if quantis is None else quantis
    lo, hi = np.quantile(pd.Series(erros_rel, dtype=float), q)
    return pd.DataFrame({"p10": previsao * (1 + lo), "central": previsao, "p90": previsao * (1 + hi)})


def quebra_de_nivel(y: pd.Series, inicio: str) -> dict:
    """Testa uma quebra de nível na tendência do T2: log(y) = a + b·t + c·(2º semestre) + d·(t ≥ `inicio`), por
    mínimos quadrados (statsmodels). Devolve o salto d como variação (e^d − 1), o intervalo de 95%, o valor-p e a
    função de previsão com a quebra."""
    z = np.log(y.to_numpy())
    pos = list(y.index).index(inicio)
    t = np.arange(len(z))
    x = np.column_stack([np.ones(len(z)), t, t % 2, (t >= pos).astype(float)])
    m = sm.OLS(z, x).fit()
    lo, hi = m.conf_int()[3]
    return {"salto": float(np.exp(m.params[3]) - 1), "ic95": (float(np.exp(lo) - 1), float(np.exp(hi) - 1)),
            "valor_p": float(m.pvalues[3]), "semestres_depois": int(len(z) - pos),
            "funcao": lambda zz, h: _tendencia(zz, h, quebra=pos)}


# ---------------------------------------------------------------- do total de MG para cada serventia

def totais_anuais(y: pd.Series) -> pd.Series:
    """Soma dos dois semestres de cada ano (só anos completos)."""
    a = pd.Series(y.to_numpy(), index=[int(p[:4]) for p in y.index])
    n = a.groupby(level=0).size()
    return a.groupby(level=0).sum()[n == 2]


def fatores_ano(previsao: pd.Series, y: pd.Series, ano_base: int) -> pd.Series:
    """Crescimento de MG de `ano_base` para cada ano previsto: soma prevista dos semestres ÷ soma real do ano-base."""
    return totais_anuais(previsao) / totais_anuais(y)[ano_base]


def erros_anuais(erros: pd.DataFrame, metodo: str) -> pd.DataFrame:
    """Erro relativo de cada ano previsto na origem móvel (soma real ÷ soma prevista dos 2 semestres − 1), por origem
    e ano à frente (1 = horizontes 1 e 2; 2 = horizontes 3 e 4)."""
    e = erros[erros["metodo"] == metodo].assign(ano_frente=lambda d: (d["horizonte"] + 1) // 2)
    g = e.groupby(["origem", "ano_frente"]).agg(real=("real", "sum"), previsto=("previsto", "sum"), n=("real", "size"))
    g = g[g["n"] == 2]
    return (g["real"] / g["previsto"] - 1).rename("erro_rel").reset_index()


def desvios_individuais(media: pd.DataFrame, saltos: pd.DataFrame, anos_base: list[int], h: int, limite: float,
                        banda: float | None = None) -> pd.DataFrame:
    """Quanto cada serventia cresceu acima ou abaixo de MG em `h` anos: log(r_i,b+h ÷ r_i,b) − log(R_b+h ÷ R_b), com
    r = a média dos semestres > 0 da serventia no ano (D-010) e R = a soma de r das serventias com os dois anos. Só
    serventias entre limite ÷ banda e limite × banda no ano-base e sem salto grosseiro (estatistica.saltos) em nenhum
    ano de b a b+h. `media`: CNS × ano (classificacao.receita_anual)."""
    banda = config()["previsao"]["desvios"]["banda"] if banda is None else banda
    com_salto = saltos.groupby("cns")["ano"].apply(set)
    partes = []
    for b in anos_base:
        if b not in media.columns or b + h not in media.columns:
            continue
        par = media[[b, b + h]].dropna()
        par = par[(par[b] > 0) & (par[b + h] > 0)]
        g = np.log(par[b + h].sum() / par[b].sum())
        anos = set(range(b, b + h + 1))
        limpo = [not (anos & com_salto.get(c, set())) for c in par.index]
        sel = par[limpo]
        sel = sel[sel[b].between(limite / banda, limite * banda)]
        partes.append(pd.DataFrame({"cns": sel.index, "ano_base": b, "h": h,
                                    "desvio": np.log(sel[b + h] / sel[b]) - g}))
    return pd.concat(partes, ignore_index=True)


def sortear_receitas(receita: pd.Series, fatores: np.ndarray, desvios: np.ndarray,
                     rng: np.random.Generator) -> np.ndarray:
    """Receitas projetadas, uma linha por sorteio: receita do ano-base × fator de MG do sorteio × e^(desvio sorteado
    para cada serventia). Receita vazia (classe indeterminada) continua vazia."""
    r = np.asarray(receita, dtype=float)
    d = rng.choice(np.asarray(desvios, dtype=float), size=(len(fatores), len(r)))
    return r[None, :] * np.asarray(fatores, dtype=float)[:, None] * np.exp(d)


def sortear_fatores(central: float, erros_rel: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """Fator de MG de cada sorteio: o central × (1 + um erro anual da origem móvel, sorteado)."""
    return central * (1 + rng.choice(np.asarray(erros_rel, dtype=float), size=n))


# ---------------------------------------------------------------- mercado projetado (funções do modelo)

def limites_corrigidos(limites: dict, inflacao: float, anos: int) -> dict:
    """Limites das classes atualizados por `anos` anos de inflação (art. 16, § 2º, do Prov. 213)."""
    return {k: v * (1 + inflacao) ** anos for k, v in limites.items()}


def inflacao_recente(indice: pd.DataFrame, meses: int | None = None) -> tuple[float, int]:
    """Variação do índice nos últimos `meses` meses do banco e o último mês (AAAAMM). `indice`: dados.indice_preco."""
    meses = config()["previsao"]["inflacao_meses"] if meses is None else meses
    i = indice.sort_values("ano_mes")
    return float(i["numero_indice"].iloc[-1] / i["numero_indice"].iloc[-1 - meses] - 1), int(i["ano_mes"].iloc[-1])


def mercado(serv: pd.DataFrame, receita: np.ndarray, limites: dict, semente: dict, cenarios: dict,
            cenario: str = "mantem", consolidacao: float | None = None) -> dict:
    """Universo e mercado com uma receita de referência projetada, pelas funções do modelo: classe e universo
    (universo), peso das indeterminadas recalculado como no pipeline (peso_indeterminada) e prêmio por
    resumo_por_totais, no nível base. A faixa de déficit segue a classe pelos mesmos `limites` (no cenário com
    correção, os limites corrigidos valem para tudo). `serv`: saída de motor.calcular_serventias na base (com
    passivo). Também conta as subidas e descidas em relação à classe da base, as subidas que ficam até
    `consolidacao` acima do limite (art. 16, § 3º: precisam de dois ciclos) e as que passam da Classe 2 para a 3."""
    consolidacao = config()["previsao"]["consolidacao"] if consolidacao is None else consolidacao
    s = serv.assign(receita_ref=receita)
    p = premissas_nivel(semente, "base", peso_indeterminada(s, limites))
    u = universo(s, limites, p, limites)
    r = resumo_por_totais(totais(u), p, cenarios, cenario)
    antes, depois = serv["classe"].to_numpy(), u["classe"].to_numpy()
    sobe = (antes == "1") & np.isin(depois, ["2", "3"])
    lim = limites["classe_1_max"]
    return {"acima_do_limite": int(np.isin(depois, ["2", "3"]).sum()),
            "providas_acima": int(((u["situacao_juridica"] == "PROVIDO") & u["classe"].isin(["2", "3"])).sum()),
            "subidas": int(sobe.sum()), "descidas": int((np.isin(antes, ["2", "3"]) & (depois == "1")).sum()),
            "subidas_ate_consolidacao": int((sobe & (np.asarray(receita) <= lim * (1 + consolidacao))).sum()),
            "classe_2_para_3": int(((antes == "2") & (depois == "3")).sum()),
            "n_universo": r["n_universo"], "passivo_universo": r["passivo_universo"], "n_deficit": r["n_deficit"],
            "valor_descoberto": r["valor_descoberto"], "mercado_importancia_segurada": r["mercado_importancia_segurada"],
            "mercado_premio_emitido": r["mercado_premio_emitido"], "peso_indeterminada": p["peso_classe_indeterminada_base"]}


def projetar_mercado(serv: pd.DataFrame, receitas: np.ndarray, limites: dict, semente: dict, cenarios: dict,
                     cenario: str = "mantem") -> pd.DataFrame:
    """`mercado` para cada sorteio (linha de `receitas`)."""
    return pd.DataFrame([mercado(serv, r, limites, semente, cenarios, cenario) for r in receitas])


def resumo_projecao(sorteios: pd.DataFrame, quantis: list[float] | None = None) -> pd.DataFrame:
    """P10, mediana (central), P90 e média de cada medida nos sorteios."""
    q = config()["previsao"]["faixa"] if quantis is None else quantis
    return pd.DataFrame({"p10": sorteios.quantile(q[0]), "central": sorteios.median(), "p90": sorteios.quantile(q[1]),
                         "media": sorteios.mean()})


# ---------------------------------------------------------------- teste no passado da projeção por serventia

def teste_contagem(y: pd.Series, media: pd.DataFrame, saltos: pd.DataFrame, origens: list[int], limite: float,
                   n: int | None = None, semente: int | None = None, max_ano: int | None = None) -> pd.DataFrame:
    """Teste no passado da projeção do universo: com o ano-base b (só o que se sabia no fim de b), projeta 1 e 2 anos
    à frente quantas serventias passam do `limite`, entre as que têm receita em b e no ano previsto, e compara com a
    contagem real e com a referência "repete a contagem do ano-base". Central: o fator central de MG e os desvios
    sorteados; faixa: também o fator sorteado. Diagnóstico: a contagem com o fator real de MG (quanto do erro vem da
    previsão de MG e quanto da dispersão entre serventias). O fator de MG vem da tendência treinada até o
    2º semestre de b, com o erro anual de uma origem móvel que também só usa o passado (5 origens, a última em
    b − 2, para que os 4 semestres previstos já tenham acontecido em b); os desvios, dos anos-base até b − h."""
    cfg = config()
    pc = cfg["previsao"]
    n = pc["sorteios"] if n is None else n
    rng = np.random.default_rng(cfg["semente"] if semente is None else semente)
    max_ano = int(totais_anuais(y).index.max()) if max_ano is None else max_ano
    linhas = []
    for b in origens:
        yb = y.loc[:f"{b}-2"]
        fat = fatores_ano(prever(yb, PRINCIPAL, 4), yb, b)
        orig = [f"{a}-2" for a in range(b - 6, b - 1)]
        _, err = origem_movel(yb, {PRINCIPAL: METODOS[PRINCIPAL]}, orig, 4, teste=orig[-1])
        ea = erros_anuais(err, PRINCIPAL)
        for h in (1, 2):
            if b + h > max_ano:
                continue
            par = media[[b, b + h]].dropna()
            par = par[(par[b] > 0) & (par[b + h] > 0)]
            anos_d = [a for a in range(b - h - pc["desvios"]["anos"] + 1, b - h + 1)]
            d = desvios_individuais(media, saltos, anos_d, h, limite)["desvio"].to_numpy()
            abaixo = (par[b].to_numpy() <= limite)[None, :]

            def contar(fatores):
                rec = sortear_receitas(par[b], fatores, d, rng)
                return (rec > limite).sum(axis=1), (abaixo & (rec > limite)).sum(axis=1)
            cont_c, sobe_c = contar(np.full(n, float(fat[b + h])))
            cont, _ = contar(sortear_fatores(float(fat[b + h]), ea.loc[ea["ano_frente"] == h, "erro_rel"].to_numpy(),
                                             n, rng))
            g_real = float(totais_anuais(y)[b + h] / totais_anuais(y)[b])   # só diagnóstico: o fator real de MG
            cont_g, sobe_g = contar(np.full(n, g_real))
            linhas.append({"ano_base": b, "ano": b + h, "h": h, "serventias": len(par),
                           "acima_real": int((par[b + h] > limite).sum()), "acima_referencia": int((par[b] > limite).sum()),
                           "acima_p10": float(np.quantile(cont, pc["faixa"][0])), "acima_central": float(np.median(cont_c)),
                           "acima_p90": float(np.quantile(cont, pc["faixa"][1])),
                           "subidas_real": int(((par[b] <= limite) & (par[b + h] > limite)).sum()),
                           "subidas_central": float(np.median(sobe_c)), "fator_mg": float(fat[b + h]),
                           "fator_mg_real": g_real, "acima_central_fator_real": float(np.median(cont_g)),
                           "subidas_central_fator_real": float(np.median(sobe_g))})
    out = pd.DataFrame(linhas)
    out["dentro_da_faixa"] = out["acima_real"].between(out["acima_p10"], out["acima_p90"])
    return out


# ---------------------------------------------------------------- tabela para o painel (Etapa 2)

def tabela_previsao(arrecadacao: pd.DataFrame, mercado_proj: pd.DataFrame) -> pd.DataFrame:
    """Desenho da gold.analise_previsao: uma linha por bloco, período, variante, cenário do limite e medida, com a
    faixa P10–P90 e o central, e o rótulo "projeção". `arrecadacao`: periodo, variante, p10, central, p90, realizado
    (opcional). `mercado_proj`: ano, variante, cenario_limite, medida, p10, central, p90."""
    a = arrecadacao.assign(bloco="arrecadacao_mg", cenario_limite="—", medida="arrecadacao_semestral")
    m = mercado_proj.assign(bloco="mercado", periodo=mercado_proj["ano"].astype(str), realizado=np.nan)
    cols = ["bloco", "periodo", "variante", "cenario_limite", "medida", "p10", "central", "p90", "realizado"]
    if "realizado" not in a:
        a["realizado"] = np.nan
    return pd.concat([a[cols], m[cols]], ignore_index=True).assign(rotulo="projeção")
