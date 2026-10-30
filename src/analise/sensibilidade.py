"""Sensibilidade (notebook 08): tornado e Monte Carlo das suposições (teste T7), sensibilidades do passivo (testes T5
e T6) e a receita líquida do Prov. 213 (art. 2º, XXIV). Só análise: nada muda a base nem os 10 números oficiais.

O prêmio sai sempre das funções do modelo (src/model, src/motor.py): `simulador.resumo_por_totais` para as suposições
de déficit, garantia e taxa, e `motor.calcular_serventias` quando o passivo ou o universo mudam. O Monte Carlo usa a
mesma conta em forma vetorial (`premio_vetorial`), conferida contra `resumo_por_totais` em tests/test_analise.py.
"""
import numpy as np
import pandas as pd

from src.analise import config
from src.model.distribuicao import TIPOS_INDETERMINADO, passivo_medio_por_municipio, preparar_vinculos
from src.model.mercado import deficit
from src.model.passivo import passivo_vinculos
from src.model.rateio import ratear_passivo
from src.model.simulador import FAIXAS, resumo_por_totais
from src.model.universo import universo
from src.motor import Insumos, calcular_serventias, premissas_nivel, resumo_mercado

# As seis suposições do T7 (passos 5 a 8 da escada), na ordem do teste
SUPOSICOES = {"taxa": "Taxa do seguro", "seguro": "Parte do déficit que escolhe seguro",
              "pct_3": "Parte descoberta, Classe 3", "prob_3": "Chance de déficit, Classe 3",
              "pct_2": "Parte descoberta, Classe 2", "prob_2": "Chance de déficit, Classe 2"}
PATRIMONIO = ("prob_2", "prob_3", "pct_2", "pct_3")   # as quatro que dependem do patrimônio do titular


# ---------------------------------------------------------------- suposições: tornado e Monte Carlo (T7)

def faixas_suposicoes(semente: dict) -> pd.DataFrame:
    """Mínimo, base e máximo das seis suposições do T7, lidos da semente das premissas (config/premissas/)."""
    pr = semente["premissas"]
    linhas = []
    for nome, rotulo in SUPOSICOES.items():
        if nome == "taxa":
            v = pr["taxa_seguro_anual"]["valores"]
        elif nome == "seguro":
            v = {n: pr["escolha_garantia"]["valores"][n]["seguro"] for n in ("min", "base", "max")}
        else:
            chave, faixa = ("prob_deficit" if nome.startswith("prob") else "pct_descoberto"), f"classe_{nome[-1]}"
            v = pr[chave]["valores"][faixa]
        linhas.append({"suposicao": nome, "rotulo": rotulo, "min": v["min"], "base": v["base"], "max": v["max"]})
    return pd.DataFrame(linhas).set_index("suposicao")


def com_suposicoes(p: dict, valores: dict) -> dict:
    """Cópia das premissas resolvidas com algumas suposições trocadas (nomes de SUPOSICOES). A parte do seguro troca
    a escolha de garantia inteira: o que sobra é dividido entre bens próprios e fiança na proporção do base (só o
    seguro entra no prêmio)."""
    out = dict(p, prob_deficit=dict(p["prob_deficit"]), pct_descoberto=dict(p["pct_descoberto"]))
    for nome, v in valores.items():
        if nome == "taxa":
            out["taxa_seguro_anual"] = v
        elif nome == "seguro":
            e = p["escolha_garantia"]
            resto = e["bens_proprios"] + e["fianca"]
            out["escolha_garantia"] = {"bens_proprios": (1 - v) * e["bens_proprios"] / resto,
                                       "fianca": (1 - v) * e["fianca"] / resto, "seguro": v}
        else:
            chave = "prob_deficit" if nome.startswith("prob") else "pct_descoberto"
            out[chave][f"classe_{nome[-1]}"] = v
    return out


def tornado(totais: dict, faixas: pd.DataFrame, p_base: dict, cenarios: dict, cenario: str = "mantem") -> pd.DataFrame:
    """Cada suposição sozinha no mínimo e no máximo, as outras no base: prêmio anual do mercado pelo modelo."""
    def premio(valores):
        return resumo_por_totais(totais, com_suposicoes(p_base, valores), cenarios, cenario)["mercado_premio_emitido"]
    base = premio({})
    linhas = [{"suposicao": n, "rotulo": f["rotulo"], "valor_min": f["min"], "valor_base": f["base"],
               "valor_max": f["max"], "premio_no_min": premio({n: f["min"]}), "premio_base": base,
               "premio_no_max": premio({n: f["max"]})} for n, f in faixas.iterrows()]
    out = pd.DataFrame(linhas)
    out["amplitude"] = (out["premio_no_max"] - out["premio_no_min"]).abs()
    return out.sort_values("amplitude", ascending=False).reset_index(drop=True)


def premio_vetorial(totais: dict, x: dict, fracao_exigencia: float = 1.0) -> dict:
    """A conta de `resumo_por_totais` para muitos sorteios de uma vez: déficit = Σ prob × pct × passivo ponderado da
    faixa; IS = déficit × exigência × parte do seguro; prêmio = IS × taxa. `x`: arrays com os nomes de SUPOSICOES."""
    defi = sum(x[f"prob_{f[-1]}"] * x[f"pct_{f[-1]}"] * totais[f"passivo_ponderado_{f}"] for f in FAIXAS)
    is_ = defi * fracao_exigencia * x["seguro"]
    return {"deficit": defi, "importancia_segurada": is_, "premio": is_ * x["taxa"]}


def _triangular_inversa(u, a, m, b):
    """Valor da distribuição triangular (mínimo a, moda m, máximo b) no quantil u."""
    c = (m - a) / (b - a)
    return np.where(u < c, a + np.sqrt(u * (b - a) * (m - a)), b - np.sqrt((1 - u) * (b - a) * (b - m)))


def sortear(faixas: pd.DataFrame, n: int | None = None, semente: int | None = None, juntas: tuple = ()) -> dict:
    """Sorteios triangulares (mínimo, base como o valor mais provável, máximo) de cada suposição, independentes entre
    si. As suposições em `juntas` usam o mesmo sorteio de quantil: andam juntas (se uma vai ao alto, todas vão)."""
    cfg = config()
    n = n or cfg["sensibilidade"]["sorteios"]
    rng = np.random.default_rng(cfg["semente"] if semente is None else semente)
    u_juntas = rng.random(n)
    return {nome: _triangular_inversa(u_juntas if nome in juntas else rng.random(n), f["min"], f["base"], f["max"])
            for nome, f in faixas.iterrows()}


def resumo_sorteios(valores: dict, percentis: list | None = None) -> pd.DataFrame:
    """Média e percentis de cada medida dos sorteios (déficit, IS, prêmio)."""
    percentis = percentis or config()["sensibilidade"]["percentis"]
    linhas = []
    for medida, v in valores.items():
        q = np.quantile(v, percentis)
        linhas.append({"medida": medida, "media": float(np.mean(v)),
                       **{f"p{round(100 * p):02d}": float(x) for p, x in zip(percentis, q)}})
    return pd.DataFrame(linhas)


def tabela_monte_carlo(resumos: dict[str, pd.DataFrame], cantos: dict[str, dict], n: int, semente: int
                       ) -> pd.DataFrame:
    """Desenho da gold.analise_monte_carlo: uma linha por variante (independentes; patrimônio junto) e medida, com
    os percentis dos sorteios e os cantos (tudo no mínimo / base / tudo no máximo) da mesma conta, ao lado."""
    linhas = []
    for variante, r in resumos.items():
        for _, row in r.iterrows():
            m = row["medida"]
            linhas.append({"variante": variante, "medida": m, **row.drop("medida").to_dict(),
                           "canto_min": cantos["min"][m], "valor_base": cantos["base"][m], "canto_max": cantos["max"][m],
                           "n_sorteios": n, "semente": semente, "distribuicao": "triangular (mín, base, máx)"})
    return pd.DataFrame(linhas)


def tabela_tornado(t: pd.DataFrame) -> pd.DataFrame:
    """Desenho da gold.analise_tornado: uma linha por premissa, com o prêmio no mínimo, no base e no máximo. Os valores
    das premissas sim/não (incidências, situações especiais) ficam como 1 e 0, para a coluna ter um tipo só."""
    cols = ["suposicao", "rotulo", "grupo", "valor_min", "valor_base", "valor_max", "premio_no_min", "premio_base",
            "premio_no_max", "amplitude"]
    valores = {c: "float64" for c in ("valor_min", "valor_base", "valor_max")}
    return t.reindex(columns=cols).astype(valores).assign(ordem=range(1, len(t) + 1))


# ---------------------------------------------------------------- premissas do passivo e do universo (recálculo)

PREMISSAS_RECALCULO = {"fracao_ferias_vencidas_pendentes": "Férias vencidas pendentes (fração)",
                       "incidencias": "INSS sobre o aviso prévio",
                       "fap": "FAP (multiplicador do RAT)",
                       "peso_classe_indeterminada_base": "Peso das serventias de classe indeterminada",
                       "situacoes_especiais_dentro": "Intervenção e diligência dentro do universo"}


def tornado_recalculo(ins: Insumos, semente: dict, peso_base: float, limites: dict, cenarios: dict,
                      cenario: str = "mantem") -> pd.DataFrame:
    """Premissas que mudam o passivo ou o universo, uma por vez no mínimo e no máximo das premissas, com o resto no
    base: o prêmio é recalculado pelo motor (calcular_serventias e resumo_mercado), serventia por serventia."""
    p_base = premissas_nivel(semente, "base", peso_base)

    def premio(p):
        return resumo_mercado(calcular_serventias(ins, p, limites, limites_faixa=limites)[0], p, cenarios,
                              cenario)["mercado_premio_emitido"]

    def rotulo_valor(nome, v):
        return v["aviso_previo_indenizado"]["inss"] if nome == "incidencias" else v
    base = premio(p_base)
    linhas = []
    for nome, rotulo in PREMISSAS_RECALCULO.items():
        ext = {}
        for nivel in ("min", "max"):
            v = premissas_nivel(semente, nivel, peso_base)[nome]
            ext[nivel] = (v, premio(premissas_nivel(semente, "base", peso_base, {nome: v})))
        linhas.append({"suposicao": nome, "rotulo": rotulo, "valor_min": rotulo_valor(nome, ext["min"][0]),
                       "valor_base": rotulo_valor(nome, p_base[nome]), "valor_max": rotulo_valor(nome, ext["max"][0]),
                       "premio_no_min": ext["min"][1], "premio_base": base, "premio_no_max": ext["max"][1]})
    out = pd.DataFrame(linhas)
    out["amplitude"] = (out["premio_no_max"] - out["premio_no_min"]).abs()
    return out.sort_values("amplitude", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------- passivo: salário ausente (T5) e reserva (T6)

def rais_com_salario_estimado(rais: pd.DataFrame, regioes: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sensibilidade do T5: os vínculos que entrariam no passivo (ativos em 31/12, prazo indeterminado) mas ficam fora
    por não ter salário de dezembro (D-015) recebem um salário estimado. Com remuneração no ano: remuneração média ×
    a razão mediana dezembro ÷ média dos vínculos conhecidos (o vencedor do T5). Sem nenhuma remuneração: a mediana
    de dezembro da região imediata (a do estado, se a região não tiver nenhum). Devolve a RAIS alterada e os
    vínculos estimados, com o método usado."""
    r = rais.copy()
    elegivel = r["ativo_31_12"] & r["tipo_vinculo"].isin(TIPOS_INDETERMINADO)
    conh = r[elegivel & (r["rem_dezembro"].fillna(0) > 0)]
    falta = elegivel & ~(r["rem_dezembro"].fillna(0) > 0)
    com_media = conh[conh["rem_media"] > 0]
    razao = float((com_media["rem_dezembro"] / com_media["rem_media"]).median())
    med_reg = conh.assign(reg=conh["cod_ibge"].map(regioes)).groupby("reg")["rem_dezembro"].median()
    z = r[falta].copy()
    tem_media = z["rem_media"].fillna(0) > 0
    pela_regiao = z["cod_ibge"].map(regioes).map(med_reg).fillna(conh["rem_dezembro"].median())
    z["rem_dezembro"] = np.where(tem_media, z["rem_media"] * razao, pela_regiao)
    z["metodo"] = np.where(tem_media, "remuneracao_media_x_razao", "mediana_regiao_imediata")
    r.loc[z.index, "rem_dezembro"] = z["rem_dezembro"]
    return r, z.assign(razao=razao)


def medio_com_encolhimento(vinculos: pd.DataFrame, municipios: list[int], p: dict, limiar: int,
                           regioes: dict) -> pd.DataFrame:
    """Sensibilidade do T6: o município com 1 a `limiar` − 1 vínculos deixa de usar só a região imediata e passa a
    usar a mistura λ × (média do município) + (1 − λ) × (média da região), com λ = τ² ÷ (τ² + σ²/n) (encolhimento,
    ou Bayes empírico): τ² é a variância do passivo médio entre os municípios grandes (limiar ou mais vínculos) e σ²,
    a variância média dentro deles. Município sem vínculo e município grande ficam como na base (D-008, D-022)."""
    base = passivo_medio_por_municipio(vinculos, municipios, p, limiar, regioes)
    v = vinculos.assign(_passivo=passivo_vinculos(vinculos, p))
    grandes = v.groupby("cod_ibge").filter(lambda g: len(g) >= limiar).groupby("cod_ibge")["_passivo"]
    tau2, sig2 = grandes.mean().var(), grandes.var().mean()
    por_mun = v.groupby("cod_ibge")["_passivo"].agg(["mean", "size"])
    out = base.copy()
    pequenos = (out["n_vinculos_rais"] >= 1) & (out["n_vinculos_rais"] < limiar) & (out["origem_distribuicao"] == "regiao")
    n = out.loc[pequenos, "n_vinculos_rais"]
    lam = tau2 / (tau2 + sig2 / n)
    proprio = out.loc[pequenos, "cod_ibge"].map(por_mun["mean"])
    out.loc[pequenos, "passivo_medio_vinculo"] = lam * proprio + (1 - lam) * out.loc[pequenos, "passivo_medio_vinculo"]
    out.loc[pequenos, "origem_distribuicao"] = "encolhimento"
    out["lambda"] = np.nan
    out.loc[pequenos, "lambda"] = lam
    return out.assign(tau2=tau2, sigma2=sig2)


def calcular_com_medio(ins: Insumos, p: dict, limites: dict, medio: pd.DataFrame) -> pd.DataFrame:
    """O resto do motor (rateio → universo → déficit) com um passivo médio por município dado de fora."""
    rat = ratear_passivo(ins.serventias, medio, p["metodo_rateio_padrao"])
    return deficit(universo(rat, limites, p, limites), p)


def vinculos_base(ins: Insumos, p: dict) -> pd.DataFrame:
    """Os vínculos que o motor usa no passivo (D-009, D-015), com a remuneração e a correção das premissas."""
    fator = 1.0 if p["correcao_salarial_rais"] == "sem_correcao" else ins.fator_inpc
    return preparar_vinculos(ins.rais, p["base_remuneracao_rais"], fator)


# ---------------------------------------------------------------- receita líquida do Prov. 213 (art. 2º, XXIV)

def receita_ref_bi(bi: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Receita de referência pelo BI do CNJ, com a mesma regra do pipeline (média dos semestres do ano com valor > 0):
    pela arrecadação e pela arrecadação menos o repasse. O semestre com repasse maior que a arrecadação (erro de
    declaração provável) fica com receita líquida zero e é contado em `semestres_repasse_maior`.
    `bi`: saída de dados.arrecadacao_bi."""
    b = bi[(bi["ano"] == ano) & (bi["arrecadacao_bi"] > 0)].copy()
    b["repasse_maior"] = b["repasse_bi"].fillna(0) > b["arrecadacao_bi"]
    b["liquida_bi"] = (b["arrecadacao_bi"] - b["repasse_bi"].fillna(0)).clip(lower=0)
    out = b.groupby("cns").agg(arrecadacao_bi=("arrecadacao_bi", "mean"), liquida_bi=("liquida_bi", "mean"),
                               repasse_bi=("repasse_bi", "mean"), semestres_bi=("semestre", "nunique"),
                               semestres_repasse_maior=("repasse_maior", "sum")).reset_index()
    out["fracao_repasse"] = 1 - out["liquida_bi"] / out["arrecadacao_bi"]
    return out


def insumos_receita_liquida(ins: Insumos, ref_bi: pd.DataFrame) -> Insumos:
    """Insumos do motor com a receita de referência da API descontada da fração de repasse que a mesma serventia
    tem no BI em 2025 (receita × (1 − fração)). Serventia ausente do BI fica com a receita da API, sem desconto."""
    s = ins.serventias.merge(ref_bi[["cns", "fracao_repasse"]], on="cns", how="left")
    s["receita_ref"] = s["receita_ref"] * (1 - s["fracao_repasse"].fillna(0))
    return Insumos(rais=ins.rais, serventias=s.drop(columns="fracao_repasse"), fator_inpc=ins.fator_inpc,
                   mes_inpc=ins.mes_inpc, regioes=ins.regioes)


def com_faixa_da_base(serv: pd.DataFrame, serv_base: pd.DataFrame, p: dict) -> pd.DataFrame:
    """Refaz o déficit de `serv` com a faixa de déficit (classe_faixa) que cada serventia tem na base, como na D-019:
    a leitura alternativa muda só quem entra no universo, não a chance de déficit de quem fica."""
    faixa = serv_base.set_index("cns")["classe_faixa"]
    s = serv.drop(columns=["n_deficit", "valor_descoberto"]).assign(classe_faixa=serv["cns"].map(faixa))
    return deficit(s, p)
