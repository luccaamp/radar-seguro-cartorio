"""Silver → gold: tabelas de negócio para o painel, calculadas pelo motor (src/motor.py) com a versão vigente das premissas.

Tabelas públicas (o painel lê só estas):
- gold.dim_municipio, gold.fato_passivo_municipio, gold.fato_mercado_municipio_publico (agregação LGPD),
  gold.fato_mercado_uf (níveis × regra de classe × cenário do STF), gold.sensibilidade_rateio,
  gold.diferenca_regra_classe, gold.execucao (versão das premissas e parâmetros da carga).
Tabelas internas (nunca exibidas por serventia, SPEC §6): gold.interno_serventia, gold.interno_insumo_*.
"""
import datetime as dt

import duckdb
import pandas as pd
import yaml

from src import estado
from src.model.distribuicao import fator_correcao_inpc
from src.model.lgpd import agregar_lgpd
from src.model.premissas import NIVEIS, validar
from src.model.rateio import METODOS
from src.model.universo import classificar, receita_referencia
from src.motor import Insumos, calcular_serventias, peso_indeterminada, premissas_nivel, resumo_mercado
from src.transform.silver import CONFIG, RAIZ

GOLD = RAIZ / "data" / "gold"
ANO_ENQUADRAMENTO = 2025  # média dos semestres do exercício anterior (D-010)
REGRAS = ("v2", "v1")


def carregar_insumos(con) -> Insumos:
    serv = con.sql("""
        SELECT s.cns, s.uf, s.cod_ibge, s.situacao_juridica, s.tipo_cartorio, s.atribuicoes,
               s.notas, s.rcpn, s.ri, s.rtd, s.rcpj, s.protesto, k.clt
        FROM silver.serventia s LEFT JOIN silver.serventia_colaboradores k USING (cns)
        WHERE s.status = 'Ativo'""").df()
    rec = receita_referencia(con.sql("SELECT * FROM silver.serventia_arrecadacao").df(), ANO_ENQUADRAMENTO)
    serv = serv.merge(rec, on="cns", how="left")
    serv["origem_receita"] = serv["origem_receita"].fillna("sem_serie")
    serv["clt"] = serv["clt"].astype("float")
    fator, mes = fator_correcao_inpc(con.sql("SELECT * FROM silver.indice_preco").df(), 202512)
    return Insumos(rais=con.sql("SELECT * FROM silver.rais_vinculo").df(), serventias=serv, fator_inpc=fator, mes_inpc=mes)


def _gravar(con, nome: str, df: pd.DataFrame) -> int:
    con.register("_df", df)
    con.execute(f"CREATE OR REPLACE TABLE gold.{nome} AS SELECT * FROM _df")
    con.unregister("_df")
    if not nome.startswith("interno_"):
        con.execute(f"COPY gold.{nome} TO '{(GOLD / f'{nome}.parquet').as_posix()}' (FORMAT parquet)")
    return len(df)


def construir(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    GOLD.mkdir(parents=True, exist_ok=True)
    con.execute("CREATE SCHEMA IF NOT EXISTS gold")
    estado.garantir_tabelas(con)
    estado.carregar_log_decisoes(con)
    semente, versao = estado.premissas_vigentes(con)
    validar(semente)
    regras = yaml.safe_load((CONFIG / "regras_classificacao.yaml").read_text(encoding="utf-8"))
    cenarios = yaml.safe_load((CONFIG / "cenarios_stf.yaml").read_text(encoding="utf-8"))
    ins = carregar_insumos(con)
    mun = con.sql("SELECT cod_ibge, nome AS municipio, mesorregiao, populacao FROM silver.municipio_ibge").df()

    servs, medios, ufs, execucao = [], [], [], []
    for regra in REGRAS:
        limites = regras["versoes"][regra]["limites"]
        peso = peso_indeterminada(ins.serventias, limites)
        execucao.append({"regra_classe": regra, "peso_classe_indeterminada_base": peso})
        for nivel in NIVEIS:
            p = premissas_nivel(semente, nivel, peso)
            serv, medio = calcular_serventias(ins, p, limites)
            servs.append(serv.assign(nivel=nivel, regra_classe=regra))
            if regra == REGRAS[0]:  # o passivo médio não depende da regra de classe
                medios.append(medio.assign(nivel=nivel))
            for cen in cenarios["cenarios"]:
                ufs.append({"uf": "MG", "nivel": nivel, "regra_classe": regra, "cenario_stf": cen,
                            **resumo_mercado(serv, p, cenarios, cen)})

    interno = pd.concat(servs, ignore_index=True)
    cont = {"interno_serventia": _gravar(con, "interno_serventia", interno)}

    # municípios: agregação de todas as serventias ativas, depois agrupamento LGPD para exibição
    por_mun = (interno.assign(_pu=interno["passivo"] * interno["peso_universo"])
               .groupby(["nivel", "regra_classe", "cod_ibge"])
               .agg(n_serventias=("cns", "size"), clt=("clt", "sum"), passivo_todas=("passivo", "sum"),
                    n_universo=("peso_universo", "sum"), passivo_universo=("_pu", "sum"),
                    n_deficit=("n_deficit", "sum"), valor_descoberto=("valor_descoberto", "sum"))
               .reset_index().merge(mun[["cod_ibge", "municipio"]], on="cod_ibge", how="left"))
    limiar = int(semente["premissas"]["limiar_agregacao_lgpd"]["valor"])
    publico = pd.concat([agregar_lgpd(g.drop(columns=["nivel", "regra_classe"]), limiar)
                         .assign(nivel=n, regra_classe=r) for (n, r), g in por_mun.groupby(["nivel", "regra_classe"])],
                        ignore_index=True)
    cont["fato_mercado_municipio_publico"] = _gravar(con, "fato_mercado_municipio_publico", publico)

    medio = pd.concat(medios, ignore_index=True).merge(mun[["cod_ibge", "municipio"]], on="cod_ibge", how="left")
    cont["fato_passivo_municipio"] = _gravar(con, "fato_passivo_municipio", medio)
    cont["fato_mercado_uf"] = _gravar(con, "fato_mercado_uf", pd.DataFrame(ufs))

    # sensibilidade ao método de rateio (base, regra v2, cenário mantém)
    lim2 = regras["versoes"]["v2"]["limites"]
    p_base = premissas_nivel(semente, "base", execucao[0]["peso_classe_indeterminada_base"])
    sens = [{"metodo_rateio": m, **resumo_mercado(calcular_serventias(ins, p_base, lim2, m)[0], p_base, cenarios,
                                                  "mantem")} for m in METODOS]
    cont["sensibilidade_rateio"] = _gravar(con, "sensibilidade_rateio", pd.DataFrame(sens))

    # diferença v2 (base) × v1 (sensibilidade), SPEC §3.4
    uf = pd.DataFrame(ufs)
    dif = (uf[uf["cenario_stf"] == "mantem"]
           .pivot_table(index="nivel", columns="regra_classe",
                        values=["n_universo", "passivo_universo", "mercado_importancia_segurada",
                                "mercado_premio_emitido"]))
    dif.columns = [f"{v}_{r}" for v, r in dif.columns]
    cont["diferenca_regra_classe"] = _gravar(con, "diferenca_regra_classe", dif.reset_index())

    # classes por serventia (uso interno) e dimensão de município (pública)
    dim = ins.serventias.copy()
    for regra in REGRAS:
        dim[f"classe_{regra}"] = [classificar(r, regras["versoes"][regra]["limites"]) for r in dim["receita_ref"]]
    cont["interno_dim_serventia"] = _gravar(con, "interno_dim_serventia", dim)
    dim_mun = (mun.merge(dim.groupby("cod_ibge").agg(n_serventias=("cns", "size"), clt=("clt", "sum")).reset_index(),
                         on="cod_ibge", how="left").fillna({"n_serventias": 0, "clt": 0}))
    cont["dim_municipio"] = _gravar(con, "dim_municipio", dim_mun)

    exe = pd.DataFrame(execucao).assign(
        versao_premissas=versao, executado_em=dt.datetime.now().replace(microsecond=0),
        fator_inpc=ins.fator_inpc, mes_inpc_final=ins.mes_inpc, ano_enquadramento=ANO_ENQUADRAMENTO,
        metodo_rateio=semente["premissas"]["metodo_rateio_padrao"]["valor"], limiar_lgpd=limiar)
    cont["execucao"] = _gravar(con, "execucao", exe)
    return cont
