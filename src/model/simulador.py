"""Simulador a partir de totais (modo demonstração, D-029). Funções puras.

O déficit é linear nas premissas de seguro: por faixa de déficit f (classe_2, classe_3; D-011, D-019),
  n_deficit        = Σ_f prob_deficit[f] × A_f,   A_f = Σ peso_universo das serventias da faixa com passivo > 0
  valor_descoberto = Σ_f prob_deficit[f] × pct_descoberto[f] × B_f,   B_f = Σ peso_universo × passivo (mesmas serventias)
e a demanda e a receita são contas sobre o déficit total. Então os controles de déficit, garantia, taxa, share,
sinistralidade, despesas e cenário do STF recalculam o resumo a partir de poucos totais públicos, sem dado por
serventia. Os controles do passivo (FAP, férias, INSS, vínculos mínimos, base de remuneração, regra e rateio) mudam
A_f e B_f: para eles há uma grade de variantes pré-calculadas no gold (gold.simulador_variantes).
"""
import pandas as pd

from src.model.cenario import aplicar_cenario_stf
from src.model.mercado import FAIXA_POR_CLASSE, demanda_seguro, receita

FAIXAS = ("classe_2", "classe_3")
PREMISSAS_PASSIVO = ("fap", "fracao_ferias_vencidas_pendentes", "inss_aviso_previo",
                     "limiar_vinculos_distribuicao_municipal", "base_remuneracao_rais")


def totais(serv: pd.DataFrame) -> dict:
    """Totais de um recorte (saída de motor.calcular_serventias) que bastam para resumo_por_totais."""
    faixa = serv["classe_faixa" if "classe_faixa" in serv else "classe"].map(FAIXA_POR_CLASSE)
    com_passivo = serv["passivo"] > 0
    t = {"n_serventias_ativas": int(len(serv)),
         "clt": float(serv["clt"].fillna(0).sum()),
         "passivo_todas": float(serv["passivo"].sum()),
         "n_universo": float(serv["peso_universo"].sum()),
         "n_indeterminadas_universo": int(((serv["classe"] == "indeterminada") & (serv["peso_universo"] > 0)).sum()),
         "passivo_universo": float((serv["passivo"] * serv["peso_universo"]).sum())}
    for f in FAIXAS:
        m = (faixa == f) & com_passivo
        t[f"peso_com_passivo_{f}"] = float(serv.loc[m, "peso_universo"].sum())
        t[f"passivo_ponderado_{f}"] = float((serv.loc[m, "peso_universo"] * serv.loc[m, "passivo"]).sum())
    return t


def resumo_por_totais(t: dict, p: dict, cenarios: dict, cenario: str, ajustes_cenario: dict | None = None) -> dict:
    """Mesmo dicionário de motor.resumo_mercado, calculado só com os totais `t` (ver totais())."""
    n_def = sum(p["prob_deficit"][f] * t[f"peso_com_passivo_{f}"] for f in FAIXAS)
    descoberto = sum(p["prob_deficit"][f] * p["pct_descoberto"][f] * t[f"passivo_ponderado_{f}"] for f in FAIXAS)
    pc = aplicar_cenario_stf(p, cenarios, cenario, ajustes_cenario)
    dem = demanda_seguro(float(descoberto), pc)
    rec = receita(dem, pc)
    return {
        "n_serventias_ativas": int(t["n_serventias_ativas"]),
        "clt": float(t["clt"]),
        "passivo_todas": float(t["passivo_todas"]),
        "n_universo": float(t["n_universo"]),
        "n_indeterminadas_universo": int(t["n_indeterminadas_universo"]),
        "passivo_universo": float(t["passivo_universo"]),
        "n_deficit": float(n_def),
        "valor_descoberto": float(descoberto),
        "bens_proprios": dem.bens_proprios, "fianca": dem.fianca,
        **{f"mercado_{k}": v for k, v in rec["mercado"].como_dict().items()},
        **{f"seguradora_{k}": v for k, v in rec["seguradora"].como_dict().items()},
    }


def ajustes_passivo(p_base: dict, valores: dict) -> dict:
    """Ajustes de premissas (formato do Simulador) para uma combinação dos controles do passivo."""
    aviso = {**p_base["incidencias"]["aviso_previo_indenizado"], "inss": bool(valores["inss_aviso_previo"])}
    return {"fap": float(valores["fap"]),
            "fracao_ferias_vencidas_pendentes": float(valores["fracao_ferias_vencidas_pendentes"]),
            "incidencias": {**p_base["incidencias"], "aviso_previo_indenizado": aviso},
            "limiar_vinculos_distribuicao_municipal": int(valores["limiar_vinculos_distribuicao_municipal"]),
            "base_remuneracao_rais": valores["base_remuneracao_rais"]}


def valores_base(p_base: dict) -> dict:
    """Valores dos controles do passivo nas premissas resolvidas (nível base)."""
    return {"fap": float(p_base["fap"]),
            "fracao_ferias_vencidas_pendentes": float(p_base["fracao_ferias_vencidas_pendentes"]),
            "inss_aviso_previo": bool(p_base["incidencias"]["aviso_previo_indenizado"]["inss"]),
            "limiar_vinculos_distribuicao_municipal": int(p_base["limiar_vinculos_distribuicao_municipal"]),
            "base_remuneracao_rais": p_base["base_remuneracao_rais"]}


def grade(p_base: dict, pontos: dict) -> list[tuple[str, dict]]:
    """Variantes do passivo: a base e uma premissa por vez nos pontos da grade (config/simulador_demo.yaml).
    Devolve (premissa que variou ou 'base', valores dos cinco controles)."""
    base = valores_base(p_base)
    out = [("base", base)]
    for nome in PREMISSAS_PASSIVO:
        for v in pontos[nome]:
            if v != base[nome]:
                out.append((nome, {**base, nome: v}))
    return out
