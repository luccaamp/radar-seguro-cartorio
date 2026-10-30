"""Déficit, demanda de garantia e receita do seguro (SPEC §3.5 a §3.7). Funções puras.

Cada função recebe as premissas resolvidas num nível (min, base ou max). O intervalo é obtido rodando os três níveis.
"""
from dataclasses import asdict, dataclass

import pandas as pd

from src.model.premissas import validar_escolha_garantia


FAIXA_POR_CLASSE = {
    "2": "classe_2",
    "3": "classe_3",
    "indeterminada": "classe_2",   # D-011
    "1": "classe_2",               # D-019: na sensibilidade v1, serventias Classe 1 pela v2 recebem a faixa da Classe 2
}


def _faixa(classe: str) -> str:
    """Faixa de prob_deficit e pct_descoberto a partir da classe pela regra BASE (coluna classe_faixa; D-011, D-019)."""
    if classe not in FAIXA_POR_CLASSE:
        raise ValueError(f"classe sem faixa de déficit: {classe!r}")
    return FAIXA_POR_CLASSE[classe]


def deficit(serventias: pd.DataFrame, p: dict) -> pd.DataFrame:
    """Valor esperado do déficit por serventia. `serventias`: passivo, peso_universo e classe_faixa (classe pela regra
    base, D-019; se ausente, usa `classe`).

    n_deficit = peso_universo × prob_deficit × [passivo > 0]; valor_descoberto = n_deficit × pct_descoberto × passivo.
    Serventia sem passivo (sem empregado CLT) não tem déficit nem conta como "com déficit" (D-021).
    """
    s = serventias.copy()
    faixa = s["classe_faixa" if "classe_faixa" in s else "classe"].map(_faixa)
    prob = faixa.map(lambda f: p["prob_deficit"][f])
    pct = faixa.map(lambda f: p["pct_descoberto"][f])
    s["n_deficit"] = s["peso_universo"] * prob * (s["passivo"] > 0)
    s["valor_descoberto"] = s["n_deficit"] * pct * s["passivo"]
    return s


@dataclass(frozen=True)
class Demanda:
    deficit_total: float
    bens_proprios: float
    fianca: float
    importancia_segurada: float


def demanda_seguro(valor_descoberto: float, p: dict) -> Demanda:
    """Divide o déficit entre bens próprios, fiança e seguro (somam 1). A IS é a parcela do seguro (100% do déficit,
    art. 13, § 2º, I). `fracao_exigencia_garantia` vem do cenário do STF (1 = mantém, 0 = arts. 8º a 17 suspensos)."""
    e = p["escolha_garantia"]
    validar_escolha_garantia(e)
    exigido = valor_descoberto * p["fracao_exigencia_garantia"]
    return Demanda(deficit_total=valor_descoberto, bens_proprios=exigido * e["bens_proprios"],
                   fianca=exigido * e["fianca"], importancia_segurada=exigido * e["seguro"])


@dataclass(frozen=True)
class Receita:
    importancia_segurada: float
    premio_emitido: float
    sinistro_esperado: float
    comissao: float
    despesa_administrativa: float
    resultado_tecnico: float

    def como_dict(self) -> dict:
        return asdict(self)


def _receita(is_: float, fatia: float, p: dict) -> Receita:
    premio = is_ * p["taxa_seguro_anual"] * fatia
    sinistro = premio * p["sinistralidade"]
    comissao = premio * p["comissao"]
    desp = premio * p["despesa_administrativa"]
    return Receita(importancia_segurada=is_ * fatia, premio_emitido=premio, sinistro_esperado=sinistro,
                   comissao=comissao, despesa_administrativa=desp, resultado_tecnico=premio - sinistro - comissao - desp)


def receita(demanda: Demanda, p: dict) -> dict[str, Receita]:
    """Receita anual e recorrente (renovação da garantia) do mercado total e da seguradora hipotética."""
    return {"mercado": _receita(demanda.importancia_segurada, 1.0, p),
            "seguradora": _receita(demanda.importancia_segurada, p["market_share_hipotetico"], p)}
