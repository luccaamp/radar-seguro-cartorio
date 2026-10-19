"""Silver → gold: tabelas de negócio para o painel, calculadas pelo motor (src/motor.py) com a versão vigente das premissas.

Tabelas públicas (o painel lê só estas):
- gold.dim_municipio, gold.fato_passivo_municipio, gold.fato_mercado_municipio_publico (agregação LGPD),
  gold.fato_mercado_uf (níveis × regra de classe × cenário do STF), gold.sensibilidade_rateio,
  gold.diferenca_regra_classe, gold.execucao (versão das premissas e parâmetros da carga).
Tabelas internas (nunca exibidas por serventia, SPEC §6): gold.interno_serventia, gold.interno_insumo_*.
"""
import datetime as dt
import json

import duckdb
import pandas as pd
import yaml

from src import estado
from src.model.distribuicao import fator_correcao_inpc
from src.model.lgpd import agregar_lgpd
from src.model.premissas import NIVEIS, validar
from src.model.rateio import METODOS
from src.model.leituras import LEITURAS, receita_referencia_alternativa
from src.model.universo import classificar, receita_referencia
from src.motor import Insumos, calcular_serventias, peso_indeterminada, premissas_nivel, resumo_mercado
from src.transform import visoes
from src.transform.geo import areas_do_mapa, dissolver, geometria_publica
from src.transform.silver import CONFIG, RAIZ

GOLD = RAIZ / "data" / "gold"
# média dos semestres do exercício anterior (D-010); valor em config/escopo.yaml
ANO_ENQUADRAMENTO = int(yaml.safe_load((CONFIG / "escopo.yaml").read_text(encoding="utf-8"))["ano_enquadramento"])
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
    regioes = dict(con.execute("SELECT cod_ibge, regiao_imediata FROM silver.municipio_ibge").fetchall())
    return Insumos(rais=con.sql("SELECT * FROM silver.rais_vinculo").df(), serventias=serv, fator_inpc=fator,
                   mes_inpc=mes, regioes=regioes)


_EXPORTAR_PARQUET = True   # definido por construir(); os testes refazem o gold sem tocar em data/gold


def _gravar(con, nome: str, df: pd.DataFrame) -> int:
    con.register("_df", df)
    con.execute(f"CREATE OR REPLACE TABLE gold.{nome} AS SELECT * FROM _df")
    con.unregister("_df")
    if _EXPORTAR_PARQUET and not nome.startswith("interno_"):
        con.execute(f"COPY gold.{nome} TO '{(GOLD / f'{nome}.parquet').as_posix()}' (FORMAT parquet)")
    return len(df)


def _metricas(df: pd.DataFrame) -> dict:
    """Somas exibidas no Mercado para um conjunto de serventias (nível base, regra base)."""
    return {"n_serventias": int(len(df)), "clt": float(df["clt"].fillna(0).sum()), "passivo": float(df["passivo"].sum()),
            "passivo_universo": float((df["passivo"] * df["peso_universo"]).sum()),
            "n_universo": float(df["peso_universo"].sum()), "n_deficit": float(df["n_deficit"].sum()),
            "valor_descoberto": float(df["valor_descoberto"].sum())}


def construir_visoes_mercado(con, interno: pd.DataFrame, reg: pd.DataFrame, areas: pd.DataFrame, malha: dict,
                             limiar: int, regra_base: str, ps: dict, cenarios: dict) -> dict[str, int]:
    """Tabelas públicas do Mercado (D-026): visão geral por área, visões filtradas por região (um filtro por vez),
    totais estaduais por filtro, ranking dos municípios com 3+ serventias e geometrias. O painel não lê interno_*."""
    geo_mun = reg[["cod_ibge", "regiao_imediata", "regiao_intermediaria"]]
    por_rn = {(r, n): g.drop(columns=["nivel", "regra_classe"]).merge(geo_mun, on="cod_ibge")
              for (n, r), g in interno.groupby(["nivel", "regra_classe"])}
    base = por_rn[(regra_base, "base")]
    ag = base[["cns", "cod_ibge"]].merge(areas[["cod_ibge", "area_id"]], on="cod_ibge")[["cns", "area_id"]]
    res = visoes.construir(base, por_rn, ag, limiar, regra_base)
    cont = {}

    # visão geral por área (mapa, ranking e tabela sem filtro)
    info = areas.groupby("area_id").agg(area_nome=("area_nome", "first"), tipo=("tipo", "first"),
                                        n_municipios=("cod_ibge", "size")).reset_index()
    geral = [{"area_id": a, **_metricas(g)} for a, g in base.merge(ag, on="cns").groupby("area_id")]
    cont["mercado_area_publico"] = _gravar(con, "mercado_area_publico", info.merge(pd.DataFrame(geral), on="area_id"))

    # visões filtradas: células publicadas, mapeamento região -> área e geometria dos grupos de intermediária
    linhas, mapa_reg, grupos_geo = [], [], {}
    for filtro, valor, visao in visoes.filtros():
        rec = base[visoes.mascara(base, filtro, valor)]
        destino = res.destinos[visao]
        for area in sorted(set(destino.values())):
            ris = [ri for ri, a in destino.items() if a == area]
            g = rec[rec["regiao_imediata"].isin(ris)]
            n_tot = int(base["regiao_imediata"].isin(ris).sum())
            publicada = area != visoes.OUTRAS or visoes.passa(len(g), n_tot, limiar)
            for ri in ris:
                mapa_reg.append({"visao": visao, "regiao_imediata": ri, "area_id": area if publicada else None})
            if not publicada:
                continue
            if area.startswith("RI:"):
                nome, nivel_area = f"Região imediata de {area[3:]}", "regiao_imediata"
            elif area.startswith("RG:"):
                nome, nivel_area = f"Região intermediária de {area[3:]} — {len(ris)} regiões imediatas somadas", \
                    "regiao_intermediaria"
                grupos_geo[(visao, area)] = set(ris)
            else:
                nome, nivel_area = f"Outras regiões — {len(ris)} regiões imediatas somadas (sem mapa)", "outras"
            linhas.append({"visao": visao, "filtro": filtro, "valor": valor, "area_id": area, "area_nome": nome,
                           "nivel_area": nivel_area, "n_regioes": len(ris), **_metricas(g)})
    cont["mercado_filtro_area"] = _gravar(con, "mercado_filtro_area", pd.DataFrame(linhas))
    cont["mercado_filtro_regiao"] = _gravar(con, "mercado_filtro_regiao", pd.DataFrame(mapa_reg))
    ri_por_mun = dict(zip(reg["cod_ibge"].astype(int), reg["regiao_imediata"]))
    geo_ri = dissolver(malha, {c: f"RI:{r}" for c, r in ri_por_mun.items()})
    cont["geo_regiao_imediata"] = _gravar(con, "geo_regiao_imediata", geo_ri)
    geo_rg = []
    for (visao, area), ris in grupos_geo.items():
        d = dissolver(malha, {c: area for c, r in ri_por_mun.items() if r in ris})
        geo_rg.append(d.assign(visao=visao))
    cont["geo_mapa_filtro"] = _gravar(con, "geo_mapa_filtro", pd.concat(geo_rg, ignore_index=True))

    # totais estaduais de cada filtro (KPIs e Faixas): só as combinações regra × nível que o auditor aprovou
    uf = []
    for filtro, valor, visao in visoes.filtros():
        for (r, n), df in por_rn.items():
            ok = res.estaduais[(visao, r, n)]
            sub = df[visoes.mascara(df, filtro, valor)]
            uf.append({"visao": visao, "filtro": filtro, "valor": valor, "regra_classe": r, "nivel": n, "publicado": ok,
                       **(resumo_mercado(sub, ps[(r, n)], cenarios, "mantem") if ok else {})})
    cont["mercado_filtro_uf"] = _gravar(con, "mercado_filtro_uf", pd.DataFrame(uf))

    # posição dos municípios com 3+ serventias no ranking estadual (U1); os menores não aparecem
    todos_mun = reg[["cod_ibge"]].merge(
        pd.DataFrame([{"cod_ibge": c, **_metricas(g)} for c, g in base.groupby("cod_ibge")]), on="cod_ibge", how="left"
    ).fillna(0)
    rk = []
    for met in ("valor_descoberto", "passivo", "n_serventias", "clt"):
        pos = todos_mun[met].rank(ascending=False, method="min").astype(int)
        total = float(todos_mun[met].sum())
        rk.append(pd.DataFrame({"cod_ibge": todos_mun["cod_ibge"], "metrica": met, "valor": todos_mun[met],
                                "posicao": pos, "n_municipios": len(todos_mun),
                                "pct_mg": todos_mun[met] / total if total else 0.0,
                                "n_serv": todos_mun["n_serventias"]}))
    rk = pd.concat(rk, ignore_index=True)
    rk = rk[rk["n_serv"] >= limiar].drop(columns="n_serv").merge(reg[["cod_ibge", "nome"]], on="cod_ibge")
    cont["ranking_municipio_publico"] = _gravar(con, "ranking_municipio_publico", rk.rename(columns={"nome": "municipio"}))

    # células publicadas, para a auditoria independente nos testes (uso interno)
    cel = [{"visao": c.visao, "area_id": c.area_id, "conjunto": conj, "cns": cns}
           for c in res.celulas for conj in ("todos", "universo") for cns in getattr(c, conj)]
    cont["interno_celulas_publicadas"] = _gravar(con, "interno_celulas_publicadas", pd.DataFrame(cel))
    con.execute("CREATE OR REPLACE TABLE gold.interno_auditoria AS SELECT ? AS iteracoes, ? AS celulas",
                [res.iteracoes, len(res.celulas)])
    return cont


def construir(con: duckdb.DuckDBPyConnection, exportar_parquet: bool = True) -> dict[str, int]:
    """Silver -> gold. `exportar_parquet=False` só grava no banco da conexão (usado pelos testes, numa cópia)."""
    global _EXPORTAR_PARQUET
    _EXPORTAR_PARQUET = exportar_parquet
    if exportar_parquet:
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

    lim_base = regras["versoes"][regras["versao_base"]]["limites"]  # classe das faixas de déficit (D-019)
    servs, medios, ufs, execucao = [], [], [], []
    for regra in REGRAS:
        limites = regras["versoes"][regra]["limites"]
        peso = peso_indeterminada(ins.serventias, limites)
        execucao.append({"regra_classe": regra, "peso_classe_indeterminada_base": peso})
        for nivel in NIVEIS:
            p = premissas_nivel(semente, nivel, peso)
            serv, medio = calcular_serventias(ins, p, limites, limites_faixa=lim_base)
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
    # só nível base e regra base: trocar regra ou nível muda quem entra no universo, e a diferença por município
    # isolaria 1 ou 2 serventias (E1-b)
    por_mun = por_mun[(por_mun["nivel"] == "base") & (por_mun["regra_classe"] == regras["versao_base"])]
    publico = pd.concat([agregar_lgpd(g.drop(columns=["nivel", "regra_classe"]), limiar)
                         .assign(nivel=n, regra_classe=r) for (n, r), g in por_mun.groupby(["nivel", "regra_classe"])],
                        ignore_index=True)
    cont["fato_mercado_municipio_publico"] = _gravar(con, "fato_mercado_municipio_publico", publico)

    medio = pd.concat(medios, ignore_index=True).merge(mun[["cod_ibge", "municipio"]], on="cod_ibge", how="left")
    cont["interno_passivo_municipio"] = _gravar(con, "interno_passivo_municipio", medio)
    # versão pública (D1): só municípios com pelo menos `limiar` serventias; os demais ficam só na interna
    n_serv = ins.serventias.groupby("cod_ibge").size()
    publico_medio = medio[medio["cod_ibge"].map(n_serv).fillna(0) >= limiar]
    cont["fato_passivo_municipio"] = _gravar(con, "fato_passivo_municipio", publico_medio)
    cont["fato_mercado_uf"] = _gravar(con, "fato_mercado_uf", pd.DataFrame(ufs))

    # sensibilidade ao método de rateio (base, regra v2, cenário mantém)
    p_base = premissas_nivel(semente, "base", execucao[0]["peso_classe_indeterminada_base"])
    sens = [{"metodo_rateio": m, **resumo_mercado(calcular_serventias(ins, p_base, lim_base, m)[0], p_base, cenarios,
                                                  "mantem")} for m in METODOS]
    cont["sensibilidade_rateio"] = _gravar(con, "sensibilidade_rateio", pd.DataFrame(sens))

    # sensibilidade a premissas e leituras (base, regra base, cenário mantém): uma mudança por linha
    mes = str(ins.mes_inpc)
    variacoes = [
        ("base", "Cenário base (data-base 31/12/2025)", {}),
        ("inpc", f"INPC até {mes[4:]}/{mes[:4]} (data-base da 1ª declaração)", {"correcao_salarial_rais": "inpc"}),
    ]
    def linha_sens(chave: str, rotulo: str, ins_v: Insumos, aj: dict | None = None) -> dict:
        peso_v = peso_indeterminada(ins_v.serventias, lim_base)
        p_v = premissas_nivel(semente, "base", peso_v, aj)
        s_v = calcular_serventias(ins_v, p_v, lim_base)[0]
        providos = int(((s_v["situacao_juridica"] == "PROVIDO") & s_v["classe"].isin(["2", "3"])).sum())
        return {"chave": chave, "variacao": rotulo, "providos_acima_limite": providos,
                "peso_classe_indeterminada_base": peso_v, **resumo_mercado(s_v, p_v, cenarios, "mantem")}

    sp = [linha_sens(chave, rotulo, ins, aj) for chave, rotulo, aj in variacoes]
    # reserva da distribuição salarial direto no estado, sem a região imediata (como era antes da D-022)
    sem_regiao = Insumos(rais=ins.rais, serventias=ins.serventias, fator_inpc=ins.fator_inpc, mes_inpc=ins.mes_inpc)
    sp.append(linha_sens("sem_regiao", "Reserva da distribuição = MG inteiro", sem_regiao))
    # leituras alternativas da regra dos R$ 300 mil (D-023); a principal é a do cenário base
    arrec = con.sql("SELECT * FROM silver.serventia_arrecadacao").df()
    for leitura, rotulo in LEITURAS.items():
        alt = receita_referencia_alternativa(arrec, ANO_ENQUADRAMENTO, leitura)
        serv_alt = ins.serventias.drop(columns=["receita_ref", "origem_receita", "semestres_validos"], errors="ignore"
                                       ).merge(alt, on="cns", how="left")
        serv_alt["origem_receita"] = serv_alt["origem_receita"].fillna("sem_serie")
        ins_alt = Insumos(rais=ins.rais, serventias=serv_alt, fator_inpc=ins.fator_inpc, mes_inpc=ins.mes_inpc,
                          regioes=ins.regioes)
        sp.append(linha_sens(f"leitura_{leitura}", f"Regra: {rotulo}", ins_alt))
    cont["sensibilidade_premissas"] = _gravar(con, "sensibilidade_premissas", pd.DataFrame(sp))

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

    # geometria pública do mapa (1.2, D-026): municípios pequenos dissolvidos por região imediata ou intermediária
    reg = con.sql("SELECT cod_ibge, nome, regiao_imediata, regiao_intermediaria FROM silver.municipio_ibge").df()
    reg = reg.merge(dim_mun[["cod_ibge", "n_serventias"]], on="cod_ibge", how="left").fillna({"n_serventias": 0})
    areas = areas_do_mapa(reg, limiar)
    arq_malha = con.sql("SELECT arquivo FROM silver.fonte_metadados WHERE fonte = 'ibge_malha'").fetchone()[0]
    malha = json.loads((RAIZ / "data" / "bronze" / arq_malha).read_text(encoding="utf-8"))
    cont["geo_area_municipio"] = _gravar(con, "geo_area_municipio", areas[["cod_ibge", "area_id"]])
    cont["geo_mapa_publico"] = _gravar(con, "geo_mapa_publico",
                                       geometria_publica(malha, areas, reg.set_index("cod_ibge")["n_serventias"]))
    sem_serv = reg.loc[reg["n_serventias"] == 0, "cod_ibge"]
    cont["geo_sem_serventia"] = _gravar(con, "geo_sem_serventia", dissolver(   # sem nome (não há cartório)
        malha, {int(c): f"SEM-{i + 1}" for i, c in enumerate(sem_serv)}))

    # visões do Mercado (D-026): geral por área e um filtro por vez por região, com supressão e auditoria (E1)
    regra_base = regras["versao_base"]
    ps = {(r, n): premissas_nivel(semente, n, next(x["peso_classe_indeterminada_base"] for x in execucao
                                                   if x["regra_classe"] == r)) for r in REGRAS for n in NIVEIS}
    cont |= construir_visoes_mercado(con, interno, reg, areas, malha, limiar, regra_base, ps, cenarios)

    exe = pd.DataFrame(execucao).assign(
        versao_premissas=versao, executado_em=dt.datetime.now().replace(microsecond=0),
        fator_inpc=ins.fator_inpc, mes_inpc_final=ins.mes_inpc, ano_enquadramento=ANO_ENQUADRAMENTO,
        metodo_rateio=semente["premissas"]["metodo_rateio_padrao"]["valor"], limiar_lgpd=limiar)
    cont["execucao"] = _gravar(con, "execucao", exe)
    return cont
