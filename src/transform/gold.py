"""Silver → gold: tabelas de negócio para o painel, calculadas pelo motor (src/motor.py) com a versão vigente das premissas.

Tabelas públicas (o painel lê só estas):
- gold.dim_municipio, gold.fato_passivo_municipio, gold.fato_mercado_municipio_publico (todos os municípios, D-078),
  gold.fato_mercado_uf (níveis × regra de classe × cenário do STF), gold.sensibilidade_rateio,
  gold.diferenca_regra_classe, gold.execucao (versão das premissas e parâmetros da carga),
  gold.serventia_publico (resultado do modelo por serventia, nível e regra base; D-038, fase 1).
Tabelas internas (todos os níveis e regras, insumos e auditoria): gold.interno_serventia, gold.interno_insumo_*.
"""
import datetime as dt

import duckdb
import pandas as pd
import yaml

from src import estado
from src.model.distribuicao import fator_correcao_inpc
from src.model import simulador
from src.model.cenario import aplicar_cenario_stf
from src.model.mercado import demanda_seguro
from src.model.premissas import NIVEIS, validar
from src.model.rateio import METODOS
from src.model.leituras import LEITURAS, receita_referencia_alternativa
from src.model.universo import classificar, receita_referencia
from src.motor import Insumos, calcular_serventias, peso_indeterminada, premissas_nivel, resumo_mercado
from src.transform import visoes
from src.transform.geo import areas_do_mapa, dissolver, geometria_publica
from src.transform.silver import CONFIG, RAIZ, malha_do_silver

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


COLUNAS_SERVENTIA_PUBLICO = ["cns", "uf", "cod_ibge", "situacao_juridica", "tipo_cartorio", "atribuicoes", "clt",
                             "receita_ref", "origem_receita", "semestres_validos", "classe", "classificacao_aproximada",
                             "motivo", "peso_universo", "passivo", "passivo_medio_vinculo", "n_deficit",
                             "valor_descoberto"]


def serventia_publico(interno: pd.DataFrame, p_base: dict, cenarios: dict, regra_base: str,
                      municipios: pd.DataFrame) -> pd.DataFrame:
    """gold.serventia_publico (D-038, fase 1): o resultado do modelo por serventia ativa, no nível base e na regra
    base, com o município e as regiões. O cartório é identificado pelo CNS e pelo município, nunca pelo nome do
    responsável (que o silver nem lê). IS e prêmio no cenário do STF "mantém", pelas funções do mercado: somados, dão
    os de gold.fato_mercado_uf."""
    s = interno[(interno["nivel"] == "base") & (interno["regra_classe"] == regra_base)]
    outras = interno[(interno["nivel"] == "base") & (interno["regra_classe"] != regra_base)]
    pc = aplicar_cenario_stf(p_base, cenarios, "mantem")
    is_por_real = demanda_seguro(1.0, pc).importancia_segurada   # a IS é proporcional ao déficit
    out = s[COLUNAS_SERVENTIA_PUBLICO].merge(municipios, on="cod_ibge", how="left")
    for regra, g in outras.groupby("regra_classe"):
        out[f"classe_{regra}"] = out["cns"].map(g.set_index("cns")["classe"])
    out["importancia_segurada"] = out["valor_descoberto"] * is_por_real
    out["premio_emitido"] = out["importancia_segurada"] * pc["taxa_seguro_anual"]
    return out.sort_values("cns").reset_index(drop=True)


def _metricas(df: pd.DataFrame) -> dict:
    """Somas exibidas no Mercado para um conjunto de serventias (nível base, regra base)."""
    return {"n_serventias": int(len(df)), "clt": float(df["clt"].fillna(0).sum()), "passivo": float(df["passivo"].sum()),
            "passivo_universo": float((df["passivo"] * df["peso_universo"]).sum()),
            "n_universo": float(df["peso_universo"].sum()), "n_deficit": float(df["n_deficit"].sum()),
            "valor_descoberto": float(df["valor_descoberto"].sum())}


def construir_visoes_mercado(con, interno: pd.DataFrame, reg: pd.DataFrame, areas: pd.DataFrame,
                             regra_base: str, ps: dict, cenarios: dict) -> dict[str, int]:
    """Tabelas públicas do Mercado: visão geral por município (mapa), totais estaduais por filtro e ranking de todos
    os municípios com serventia. Sem limiar nem supressão desde a D-078 (D-038, fase 2). O painel não lê interno_*."""
    por_rn = {(r, n): g.drop(columns=["nivel", "regra_classe"]) for (n, r), g in interno.groupby(["nivel", "regra_classe"])}
    base = por_rn[(regra_base, "base")]
    ag = base[["cns", "cod_ibge"]].merge(areas[["cod_ibge", "area_id"]], on="cod_ibge")[["cns", "area_id"]]
    cont = {}

    # visão geral por área (o mapa): uma área por município com serventia
    info = areas.groupby("area_id").agg(area_nome=("area_nome", "first"), tipo=("tipo", "first"),
                                        n_municipios=("cod_ibge", "size")).reset_index()
    geral = [{"area_id": a, **_metricas(g)} for a, g in base.merge(ag, on="cns").groupby("area_id")]
    cont["mercado_area_publico"] = _gravar(con, "mercado_area_publico", info.merge(pd.DataFrame(geral), on="area_id"))

    # totais estaduais de cada filtro (chat): todas as combinações regra × nível
    uf = []
    for filtro, valor, visao in visoes.filtros():
        for (r, n), df in por_rn.items():
            sub = df[visoes.mascara(df, filtro, valor)]
            uf.append({"visao": visao, "filtro": filtro, "valor": valor, "regra_classe": r, "nivel": n,
                       **resumo_mercado(sub, ps[(r, n)], cenarios, "mantem")})
    cont["mercado_filtro_uf"] = _gravar(con, "mercado_filtro_uf", pd.DataFrame(uf))

    # posição de cada município com serventia no ranking estadual (U1), inclusive os de 1 ou 2 serventias
    todos_mun = pd.DataFrame([{"cod_ibge": c, **_metricas(g)} for c, g in base.groupby("cod_ibge")])
    rk = []
    for met in ("valor_descoberto", "passivo", "n_serventias", "clt"):
        pos = todos_mun[met].rank(ascending=False, method="min").astype(int)
        total = float(todos_mun[met].sum())
        rk.append(pd.DataFrame({"cod_ibge": todos_mun["cod_ibge"], "metrica": met, "valor": todos_mun[met],
                                "posicao": pos, "n_municipios": len(todos_mun),
                                "pct_mg": todos_mun[met] / total if total else 0.0}))
    rk = pd.concat(rk, ignore_index=True).merge(reg[["cod_ibge", "nome"]], on="cod_ibge")
    cont["ranking_municipio_publico"] = _gravar(con, "ranking_municipio_publico", rk.rename(columns={"nome": "municipio"}))
    return cont


def construir_simulador(con, ins: Insumos, semente: dict, regras: dict, execucao: list[dict],
                        lim_base: dict) -> dict[str, int]:
    """Tabelas públicas do Simulador no modo demonstração (D-029):
    - gold.simulador_variantes: uma linha por variante (regra × método de rateio × uma premissa do passivo por vez,
      pontos em config/simulador_demo.yaml), com os totais de MG que não dependem das premissas de seguro;
    - gold.simulador_base_classe: por variante e faixa de déficit (classe_2, classe_3), os totais A_f e B_f de
      src/model/simulador.py. Só totais de MG."""
    pontos = yaml.safe_load((CONFIG / "simulador_demo.yaml").read_text(encoding="utf-8"))["pontos"]
    peso_regra = {x["regra_classe"]: x["peso_classe_indeterminada_base"] for x in execucao}
    p_padrao = premissas_nivel(semente, "base", peso_regra[REGRAS[0]])
    variantes, faixas = [], []
    vid = 0
    for regra in REGRAS:
        limites = regras["versoes"][regra]["limites"]
        for metodo in METODOS:
            for variou, valores in simulador.grade(p_padrao, pontos):
                vid += 1
                p = premissas_nivel(semente, "base", peso_regra[regra], simulador.ajustes_passivo(p_padrao, valores))
                serv = calcular_serventias(ins, p, limites, metodo, limites_faixa=lim_base)[0]
                t = simulador.totais(serv)
                variantes.append({"variante_id": vid, "regra_classe": regra, "metodo_rateio": metodo,
                                  "premissa_variada": variou, **valores,
                                  **{k: v for k, v in t.items() if not k.startswith(("peso_com", "passivo_pond"))}})
                for f in simulador.FAIXAS:
                    faixas.append({"variante_id": vid, "faixa": f, "peso_com_passivo": t[f"peso_com_passivo_{f}"],
                                   "passivo_ponderado": t[f"passivo_ponderado_{f}"]})
    return {"simulador_variantes": _gravar(con, "simulador_variantes", pd.DataFrame(variantes)),
            "simulador_base_classe": _gravar(con, "simulador_base_classe", pd.DataFrame(faixas))}


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
            if regra == regras["versao_base"] and nivel == "base":
                p_base = p
            serv, medio = calcular_serventias(ins, p, limites, limites_faixa=lim_base)
            servs.append(serv.assign(nivel=nivel, regra_classe=regra))
            if regra == REGRAS[0]:  # o passivo médio não depende da regra de classe
                medios.append(medio.assign(nivel=nivel))
            for cen in cenarios["cenarios"]:
                ufs.append({"uf": "MG", "nivel": nivel, "regra_classe": regra, "cenario_stf": cen,
                            **resumo_mercado(serv, p, cenarios, cen)})

    interno = pd.concat(servs, ignore_index=True)
    cont = {"interno_serventia": _gravar(con, "interno_serventia", interno)}
    mun_reg = con.sql("SELECT cod_ibge, nome AS municipio, regiao_imediata, regiao_intermediaria "
                      "FROM silver.municipio_ibge").df()
    cont["serventia_publico"] = _gravar(con, "serventia_publico",
                                        serventia_publico(interno, p_base, cenarios, regras["versao_base"], mun_reg))

    # municípios: soma das serventias ativas de cada um, todos os municípios com serventia (sem agrupar, D-078);
    # só nível base e regra base, como antes
    por_mun = (interno.assign(_pu=interno["passivo"] * interno["peso_universo"])
               .groupby(["nivel", "regra_classe", "cod_ibge"])
               .agg(n_serventias=("cns", "size"), clt=("clt", "sum"), passivo_todas=("passivo", "sum"),
                    n_universo=("peso_universo", "sum"), passivo_universo=("_pu", "sum"),
                    n_deficit=("n_deficit", "sum"), valor_descoberto=("valor_descoberto", "sum"))
               .reset_index().merge(mun[["cod_ibge", "municipio"]], on="cod_ibge", how="left"))
    por_mun = por_mun[(por_mun["nivel"] == "base") & (por_mun["regra_classe"] == regras["versao_base"])]
    colunas = [c for c in por_mun.columns if c not in ("nivel", "regra_classe")] + ["nivel", "regra_classe"]
    cont["fato_mercado_municipio_publico"] = _gravar(con, "fato_mercado_municipio_publico",
                                                     por_mun[colunas].reset_index(drop=True))

    medio = pd.concat(medios, ignore_index=True).merge(mun[["cod_ibge", "municipio"]], on="cod_ibge", how="left")
    cont["interno_passivo_municipio"] = _gravar(con, "interno_passivo_municipio", medio)
    # versão pública: todos os municípios com serventia (antes, só os com 3 ou mais; D-078)
    n_serv = ins.serventias.groupby("cod_ibge").size()
    cont["fato_passivo_municipio"] = _gravar(con, "fato_passivo_municipio",
                                             medio[medio["cod_ibge"].map(n_serv).fillna(0) > 0])
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

    # geometria pública do mapa (1.2): uma área por município com serventia (D-078)
    reg = con.sql("SELECT cod_ibge, nome, regiao_imediata, regiao_intermediaria FROM silver.municipio_ibge").df()
    reg = reg.merge(dim_mun[["cod_ibge", "n_serventias"]], on="cod_ibge", how="left").fillna({"n_serventias": 0})
    areas = areas_do_mapa(reg)
    malha = malha_do_silver(con)   # do silver, não do bronze: o gold se recalcula só com o silver (D-029)
    cont["geo_area_municipio"] = _gravar(con, "geo_area_municipio", areas[["cod_ibge", "area_id"]])
    cont["geo_mapa_publico"] = _gravar(con, "geo_mapa_publico",
                                       geometria_publica(malha, areas, reg.set_index("cod_ibge")["n_serventias"]))
    sem_serv = reg.loc[reg["n_serventias"] == 0, "cod_ibge"]
    cont["geo_sem_serventia"] = _gravar(con, "geo_sem_serventia", dissolver(   # sem nome (não há cartório)
        malha, {int(c): f"SEM-{i + 1}" for i, c in enumerate(sem_serv)}))

    # visões do Mercado: geral por município, totais de MG por filtro e ranking (sem supressão desde a D-078)
    regra_base = regras["versao_base"]
    ps = {(r, n): premissas_nivel(semente, n, next(x["peso_classe_indeterminada_base"] for x in execucao
                                                   if x["regra_classe"] == r)) for r in REGRAS for n in NIVEIS}
    cont |= construir_visoes_mercado(con, interno, reg, areas, regra_base, ps, cenarios)

    # Simulador sem dados internos (modo demonstração, D-029): totais por faixa e grade de variantes do passivo
    cont |= construir_simulador(con, ins, semente, regras, execucao, lim_base)

    exe = pd.DataFrame(execucao).assign(
        versao_premissas=versao, executado_em=dt.datetime.now().replace(microsecond=0),
        fator_inpc=ins.fator_inpc, mes_inpc_final=ins.mes_inpc, ano_enquadramento=ANO_ENQUADRAMENTO,
        metodo_rateio=semente["premissas"]["metodo_rateio_padrao"]["valor"])
    cont["execucao"] = _gravar(con, "execucao", exe)
    return cont
