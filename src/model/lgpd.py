"""Agregação para exibição (SPEC §6): municípios com menos de `limiar` serventias entram num grupo único. Função pura."""
import pandas as pd

ROTULO_AGREGADO = "Outros municípios (menos de {n} serventias)"


def agregar_lgpd(df: pd.DataFrame, limiar: int, col_n: str = "n_serventias", col_nome: str = "municipio",
                 col_cod: str = "cod_ibge") -> pd.DataFrame:
    """Soma as colunas numéricas dos municípios com `col_n` < `limiar` numa linha só, com cod_ibge nulo.

    As linhas dos demais municípios ficam como estão. A coluna `agregado_lgpd` marca a linha agrupada.
    """
    pequenos = df[col_n] < limiar
    grandes = df[~pequenos].assign(agregado_lgpd=False)
    if not pequenos.any():
        return grandes.reset_index(drop=True)
    num = df.select_dtypes("number").columns.drop(col_cod, errors="ignore")
    linha = df.loc[pequenos, num].sum().to_frame().T
    linha[col_nome] = ROTULO_AGREGADO.format(n=limiar)
    linha[col_cod] = pd.NA
    linha["n_municipios_agregados"] = int(pequenos.sum())
    linha["agregado_lgpd"] = True
    return pd.concat([grandes, linha], ignore_index=True)
