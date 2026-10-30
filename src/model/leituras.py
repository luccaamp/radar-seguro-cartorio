"""Leituras ALTERNATIVAS da regra dos R$ 300 mil (art. 16, § 1º, do Prov. 213, com a redação do 243). Funções puras.

Servem só para a tabela de sensibilidade (D-023). A leitura principal continua em
`universo.receita_referencia` (média dos semestres com valor > 0).
Em todas: conflito na fonte e zero nos dois semestres continuam indeterminados (D-013, D-014); semestre ausente conta 0.
"""
import pandas as pd

LEITURAS = {
    "literal": "zero conta como zero (média literal dos dois semestres)",
    "dois_semestres": "acima de R$ 300 mil nos dois semestres",
    "algum_semestre": "acima de R$ 300 mil em algum semestre",
}


def receita_referencia_alternativa(semestres: pd.DataFrame, ano: int, leitura: str) -> pd.DataFrame:
    """Valor comparado ao limite semestral da Classe 1 em cada leitura: média dos dois (literal), o menor (dois
    semestres) ou o maior (algum semestre). Colunas: cns, receita_ref, origem_receita."""
    if leitura not in LEITURAS:
        raise ValueError(f"leitura desconhecida: {leitura}")
    s = semestres[(semestres["ano"] == ano) & semestres["semestre"].notna()]
    linhas = []
    for cns, g in s.groupby("cns"):
        if g["conflito_fonte"].any():
            linhas.append((cns, None, "conflito_fonte"))
            continue
        val = {int(sem): float(v) if inf and pd.notna(v) else 0.0
               for sem, v, inf in zip(g["semestre"], g["arrecadacao"], g["informado"])}
        s1, s2 = val.get(1, 0.0), val.get(2, 0.0)
        if s1 <= 0 and s2 <= 0:
            linhas.append((cns, None, "zero_nos_dois_semestres"))
            continue
        ref = {"literal": (s1 + s2) / 2, "dois_semestres": min(s1, s2), "algum_semestre": max(s1, s2)}[leitura]
        linhas.append((cns, ref, leitura))
    return pd.DataFrame(linhas, columns=["cns", "receita_ref", "origem_receita"])
