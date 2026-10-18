"""Distribuição de salário × tempo usada no passivo: preparo dos vínculos da RAIS e escolha município/estado. Funções puras."""
import pandas as pd

from src.model.passivo import passivo_municipio

TIPOS_INDETERMINADO = (10, 15, 20, 25)  # layout RAIS 2020 (D-009)


def fator_correcao_inpc(indices: pd.DataFrame, mes_inicial: int, mes_final: int | None = None) -> tuple[float, int]:
    """Razão do número-índice do INPC entre `mes_final` (padrão: último disponível) e `mes_inicial`."""
    inpc = indices[indices["indice"] == "INPC"].set_index("ano_mes")["numero_indice"]
    fim = mes_final or int(inpc.index.max())
    return float(inpc.loc[fim] / inpc.loc[mes_inicial]), fim


def preparar_vinculos(rais: pd.DataFrame, base_remuneracao: str, fator_correcao: float) -> pd.DataFrame:
    """Vínculos que entram na distribuição: ativos em 31/12, prazo indeterminado (D-009) e com remuneração > 0 (D-015).

    Devolve cod_ibge, salario (remuneração escolhida × correção) e meses_servico.
    """
    col = {"dezembro": "rem_dezembro", "media_anual": "rem_media"}[base_remuneracao]
    v = rais[rais["ativo_31_12"] & rais["tipo_vinculo"].isin(TIPOS_INDETERMINADO) & (rais[col].fillna(0) > 0)]
    return pd.DataFrame({"cod_ibge": v["cod_ibge"].to_numpy(),
                         "salario": (v[col] * fator_correcao).to_numpy(),
                         "meses_servico": v["tempo_emprego_meses"].fillna(0).to_numpy()})


def passivo_medio_por_municipio(vinculos: pd.DataFrame, municipios: list[int], p: dict, limiar: int) -> pd.DataFrame:
    """Passivo médio por vínculo para cada município: o do próprio município se tiver `limiar` vínculos ou mais,
    senão o do estado inteiro (D-008). Coluna `origem_distribuicao` = 'municipio' ou 'estado'."""
    por_mun = passivo_municipio(vinculos, p)
    estado = passivo_municipio(vinculos.assign(_uf=0), p, chave="_uf")
    medio_estado = float(estado["passivo_medio_vinculo"].iloc[0]) if len(estado) else 0.0
    proprio = por_mun.set_index("cod_ibge")
    linhas = []
    for cod in municipios:
        n = int(proprio["n_vinculos"].get(cod, 0))
        if n >= limiar:
            linhas.append((cod, "municipio", n, float(proprio.at[cod, "passivo_medio_vinculo"])))
        else:
            linhas.append((cod, "estado", n, medio_estado))
    return pd.DataFrame(linhas, columns=["cod_ibge", "origem_distribuicao", "n_vinculos_rais", "passivo_medio_vinculo"])
