"""Vacância no tempo (notebook 05c): o que as datas do cadastro do Justiça Aberta permitem dizer sobre a frequência de
fim da delegação (lacuna da D-025). Só análise: nenhuma premissa do modelo muda. Parâmetros em config/analise.yaml
(vacancia)."""
import numpy as np
import pandas as pd

from src.analise import config


def em_lote(cad: pd.DataFrame, minimo: int | None = None) -> pd.Series:
    """Verdadeiro para as serventias cuja data de decisão é um dia com `minimo` ou mais decisões na mesma UF (um ato
    coletivo, como a outorga de um concurso, ou uma data de carga do sistema)."""
    minimo = config()["vacancia"]["lote_min"] if minimo is None else minimo
    n = cad.groupby(["uf", "data_decisao"])["cns"].transform("size")
    return cad["data_decisao"].notna() & (n >= minimo)


def decisoes_por_ano(cad: pd.DataFrame) -> pd.DataFrame:
    """Serventias ativas por ano da decisão da situação atual e situação (linhas: ano; colunas: situação)."""
    a = cad[(cad["status"] == "Ativo") & cad["data_decisao"].notna()]
    return a.groupby([a["data_decisao"].dt.year.rename("ano"), "situacao_juridica"]).size().unstack(fill_value=0)


def estoque_providas(cad: pd.DataFrame, ano: int) -> pd.Series:
    """Quem estava provida no início do `ano`, aproximado pelo cadastro de hoje: as providas, menos as que foram
    providas no `ano` ou depois (estavam vagas), mais as vagas cuja vacância foi decidida no `ano` ou depois (estavam
    providas). Devolve uma máscara sobre as serventias ativas. Aproximação: ignora quem mudou de situação mais de uma
    vez no período e quem foi para intervenção ou diligência."""
    ativo = cad["status"] == "Ativo"
    depois = cad["data_decisao"].dt.year >= ano
    providas_antes = (cad["situacao_juridica"] == "PROVIDO") & ~depois
    vagaram_depois = (cad["situacao_juridica"] == "VAGO") & depois
    return ativo & (providas_antes | vagaram_depois)


def taxa_vacancia(cad: pd.DataFrame, ano: int, grupo: pd.Series | None = None,
                  fora: pd.Series | None = None) -> pd.DataFrame:
    """Vacâncias decididas no `ano` (serventias hoje vagas com decisão nesse ano) ÷ providas no início do ano
    (`estoque_providas`), no total ou por `grupo` (uma série alinhada a `cad`, como a UF ou a classe). As serventias
    marcadas em `fora` (por exemplo, decisões em lote) não contam como vacância, mas continuam no estoque."""
    estoque = estoque_providas(cad, ano)
    vagou = estoque & (cad["situacao_juridica"] == "VAGO") & (cad["data_decisao"].dt.year == ano)
    if fora is not None:
        vagou &= ~fora
    g = pd.Series("total", index=cad.index) if grupo is None else grupo
    out = pd.DataFrame({"providas_no_inicio": estoque.groupby(g).sum(), "vacancias": vagou.groupby(g).sum()})
    out["taxa"] = out["vacancias"] / out["providas_no_inicio"].replace(0, np.nan)
    return out


def taxas_por_ano(cad: pd.DataFrame, anos: range, sem_lote: bool = True) -> pd.DataFrame:
    """`taxa_vacancia` do recorte dado (por exemplo, MG) para cada ano; com `sem_lote`, as vacâncias decididas em
    lote não contam (o estoque fica igual)."""
    linhas = []
    lote = em_lote(cad) if sem_lote else None
    for ano in anos:
        t = taxa_vacancia(cad, ano, fora=lote).iloc[0]
        linhas.append({"ano": ano, **t.to_dict()})
    return pd.DataFrame(linhas)


def anos_desde(datas: pd.Series, referencia: pd.Timestamp) -> pd.Series:
    """Anos (com fração) entre cada data e a data de referência."""
    return (pd.Timestamp(referencia) - pd.to_datetime(datas)).dt.days / 365.25
