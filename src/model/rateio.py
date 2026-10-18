"""Rateio do passivo municipal entre TODAS as serventias do município (inclusive interinas e Classe 1). Função pura.

Métodos (SPEC §3.3, D-005):
- por_empregados_cnj (padrão): passivo da serventia = CLT declarados × passivo médio por vínculo do município;
- arrecadacao, uniforme, peso_por_atribuicao (sensibilidade): redistribuem o MESMO total municipal
  (soma dos CLT × passivo médio) por outro peso, para isolar o efeito da escolha do método.
"""
import pandas as pd

METODOS = ("por_empregados_cnj", "arrecadacao", "uniforme", "peso_por_atribuicao")


def ratear_passivo(serventias: pd.DataFrame, medio: pd.DataFrame, metodo: str,
                   pesos_atribuicao: dict[str, float] | None = None) -> pd.DataFrame:
    """`serventias`: cns, cod_ibge, clt, receita_ref, atribuicoes. `medio`: cod_ibge, passivo_medio_vinculo.

    Devolve as serventias com a coluna `passivo` (R$).
    """
    if metodo not in METODOS:
        raise ValueError(f"método de rateio desconhecido: {metodo}")
    s = serventias.merge(medio[["cod_ibge", "passivo_medio_vinculo"]], on="cod_ibge", how="left")
    s["passivo_medio_vinculo"] = s["passivo_medio_vinculo"].fillna(0.0)
    s["_proprio"] = s["clt"].fillna(0) * s["passivo_medio_vinculo"]
    if metodo == "por_empregados_cnj":
        return s.assign(passivo=s["_proprio"]).drop(columns="_proprio")

    if metodo == "arrecadacao":
        peso = s["receita_ref"].fillna(0).clip(lower=0)
    elif metodo == "uniforme":
        peso = pd.Series(1.0, index=s.index)
    else:
        if not pesos_atribuicao:
            raise ValueError("peso_por_atribuicao precisa de pesos_atribuicao")
        peso = s["atribuicoes"].map(pesos_atribuicao).fillna(0.0)
    total_mun = s.groupby("cod_ibge")["_proprio"].transform("sum")
    soma_peso = peso.groupby(s["cod_ibge"]).transform("sum")
    n_mun = s.groupby("cod_ibge")["cns"].transform("size")
    # município sem peso nenhum (ex.: arrecadação toda zero) cai no rateio uniforme, para não perder passivo
    fracao = (peso / soma_peso).where(soma_peso > 0, 1 / n_mun)
    return s.assign(passivo=total_mun * fracao).drop(columns="_proprio")
