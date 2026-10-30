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


def passivo_medio_por_municipio(vinculos: pd.DataFrame, municipios: list[int], p: dict, limiar: int,
                                regioes: dict[int, str] | None = None) -> pd.DataFrame:
    """Passivo médio por vínculo para cada município, pela primeira distribuição com `limiar` vínculos ou mais:
    o próprio município (D-008), a região imediata do IBGE (`regioes`: cod_ibge -> região; D-022) ou o estado inteiro.
    Coluna `origem_distribuicao` = 'municipio', 'regiao' ou 'estado'."""
    por_mun = passivo_municipio(vinculos, p).set_index("cod_ibge")
    estado = passivo_municipio(vinculos.assign(_uf=0), p, chave="_uf")
    medio_estado = float(estado["passivo_medio_vinculo"].iloc[0]) if len(estado) else 0.0
    regioes = regioes or {}
    por_reg = (passivo_municipio(vinculos.assign(_reg=vinculos["cod_ibge"].map(regioes)).dropna(subset=["_reg"]), p,
                                 chave="_reg").set_index("_reg") if regioes else pd.DataFrame())
    linhas = []
    for cod in municipios:
        n = int(por_mun["n_vinculos"].get(cod, 0))
        reg = regioes.get(cod)
        if n >= limiar:
            linhas.append((cod, "municipio", n, float(por_mun.at[cod, "passivo_medio_vinculo"])))
        elif reg is not None and reg in por_reg.index and int(por_reg.at[reg, "n_vinculos"]) >= limiar:
            linhas.append((cod, "regiao", n, float(por_reg.at[reg, "passivo_medio_vinculo"])))
        else:
            linhas.append((cod, "estado", n, medio_estado))
    return pd.DataFrame(linhas, columns=["cod_ibge", "origem_distribuicao", "n_vinculos_rais", "passivo_medio_vinculo"])
