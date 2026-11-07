"""Recortes do Mercado (D-026): um filtro por vez (atribuição, situação ou classe), para os totais de MG de cada recorte
em gold.mercado_filtro_uf.

Desde a D-078 (D-038, fase 2) não há limiar de serventias nem supressão: todo recorte sai, em toda regra e nível.
"""
import pandas as pd

# RTD e RCPJ vêm juntos em quase todo cartório e continuam como um valor só do filtro (D-026), para a tabela manter
# os mesmos recortes de antes.
ATRIBUICOES = {"notas": "Notas", "rcpn": "Registro Civil (PN)", "ri": "Registro de Imóveis",
               "rtd_rcpj": "Títulos e Documentos / Pessoa Jurídica", "protesto": "Protesto"}
COLUNAS_ATRIBUICAO = {"rtd_rcpj": ("rtd", "rcpj")}
SITUACOES = ["PROVIDO", "VAGO", "SOB INTERVENÇÃO", "CONVERSÃO EM DILIGÊNCIA"]
CLASSES = ["1", "2", "3", "indeterminada"]


def filtros() -> list[tuple[str, str, str]]:
    """(filtro, valor, id da visão). Atribuição não particiona (uma serventia tem várias)."""
    out = [("atribuicao", a, f"atribuicao={a}") for a in ATRIBUICOES]
    out += [("situacao", s, f"situacao={s}") for s in SITUACOES]
    out += [("classe", c, f"classe={c}") for c in CLASSES]
    return out


def mascara(df: pd.DataFrame, filtro: str, valor: str) -> pd.Series:
    if filtro == "atribuicao":
        cols = list(COLUNAS_ATRIBUICAO.get(valor, (valor,)))
        return df[cols].fillna(False).astype(bool).any(axis=1)
    if filtro == "situacao":
        return df["situacao_juridica"] == valor
    return df["classe_faixa"] == valor   # classe pela regra base (D-019)
