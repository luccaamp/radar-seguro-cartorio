"""Onde está o mercado: o mapa do déficit de cobertura (o que vira seguro) por município, com um filtro só (município).

Só lê tabelas públicas do gold (1.7), na regra base e no nível base. Desde a D-078 (D-038, fase 2) cada município com
cartório é uma área do mapa, inclusive os de 1 ou 2 cartórios. O recorte vem do seletor "Estado" (D-088): o Sudeste
(os municípios dos 4 estados, com o contorno de cada estado) ou um estado. Dois modos (U1):
- sem município: o mapa do recorte e os 10 municípios com mais déficit nele;
- município: destaque com contexto e zoom na região intermediária, e a posição dele no ranking do recorte.
Os filtros por atribuição, situação e classe, as outras métricas e a tabela por área saíram do painel
(docs/painel/corte.md); o chat responde por município e por recorte.
"""
import json

import pandas as pd
import streamlit as st

from comum import (REGIAO, analise, avisar_se_preliminar, brl, consulta, do_escopo, escopo, fonte_linha, nome_escopo,
                   num, pagina, pct, ufs)
from src.agent.ferramentas import preliminar
from src.painel import brasil, ui
from src.painel.brasil import do_estado
from src.painel.mapa import brl_curto, dados_mapa, mapa_clicavel, pct_curto

pagina("Onde está o mercado", "🗺️", "Onde está o dinheiro?",
       "O déficit de cobertura, que é o que vira seguro, se concentra nas maiores cidades. Escolha um município para "
       "ver a parte dele.", sobre="Onde está o mercado")
# V3 (D-089): o estado e o município se escolhem no próprio mapa (botões dos estados e busca, na barra dele); a página
# guarda a escolha na sessão: `escopo` (comum.escopo) e `f_mun_<recorte>` (o rótulo do município, ou "Todos")
TOPO = 10   # municípios na lista do ranking
METRICA = "valor_descoberto"
E = escopo()
UFS = ufs() if E == REGIAO else [E]
VARIAS = len(UFS) > 1
NOME = nome_escopo(E)            # "Sudeste", "Minas Gerais"…
DE = "do Sudeste" if E == REGIAO else f"de {E}"   # "do déficit do Sudeste" / "do déficit de MG"
if not VARIAS:
    avisar_se_preliminar(E)


# ------------------------------------------------------------------ dados (só tabelas públicas, com cache)
@st.cache_data
def tab(sql: str, params: tuple = ()) -> pd.DataFrame:
    return consulta(sql, list(params))


@st.cache_data
def geometrias(sql: str, params: tuple = ()) -> dict[str, dict]:
    g = consulta(sql, list(params))
    return {a: json.loads(x) for a, x in zip(g["area_id"], g["geometria"])}


EM = "uf IN (SELECT unnest(?))"   # o recorte: as UFs do escopo
areas = tab(f"SELECT * FROM gold.mercado_area_publico WHERE {EM}", (UFS,))
municipios = tab(f"""SELECT m.cod_ibge, m.uf, m.nome, m.regiao_imediata, m.regiao_intermediaria, a.area_id,
                            d.n_serventias
                     FROM silver.municipio_ibge m JOIN gold.geo_area_municipio a USING (cod_ibge)
                     JOIN gold.dim_municipio d USING (cod_ibge) WHERE m.{EM} ORDER BY m.nome, m.uf""", (UFS,))
# ranking do recorte: o déficit de cada município com cartório, do maior para o menor (no Sudeste, refeito sobre os
# 4 estados; num estado, o mesmo de gold.ranking_municipio_publico)
ranking = (areas[["area_id", "area_nome", "uf", METRICA]].rename(columns={"area_nome": "municipio", METRICA: "valor"})
           .sort_values(["valor", "municipio"], ascending=[False, True]).reset_index(drop=True))
ranking["posicao"] = ranking.index + 1
total = float(areas[METRICA].sum())
areas["valor_txt"] = areas[METRICA].map(brl)
areas["pct_txt"] = [pct(v / total) for v in areas[METRICA]]


def rotulo(nome: str, uf: str) -> str:
    """Nome do município no seletor e nas tabelas: com a UF quando o recorte tem mais de um estado (há nomes iguais)."""
    return f"{nome} ({uf})" if VARIAS else nome


municipios["rotulo"] = [rotulo(n, u) for n, u in zip(municipios["nome"], municipios["uf"])]

# ------------------------------------------------------------------ o município escolhido (no mapa: clique ou busca)
escolhido = st.session_state.get(f"f_mun_{E}", "Todos")
com_area = set(areas["area_id"])
achados = municipios[(municipios["rotulo"] == escolhido) & municipios["area_id"].isin(com_area)]
mun = achados.iloc[0] if len(achados) else None
foco = areas[areas["area_id"] == mun["area_id"]].iloc[0] if mun is not None else None
mun_nome = mun["nome"] if mun is not None else None

# ------------------------------------------------------------------ até 3 números
if foco is None:
    ordem = areas.sort_values(METRICA, ascending=False)
    maior = ordem.iloc[0]
    ui.grade([ui.kpi(f"Só {rotulo(maior['area_nome'], maior['uf'])}", maior["pct_txt"],
                     f"do déficit {DE} ({maior['valor_txt']})"),
              ui.kpi(f"Os {TOPO} municípios com mais déficit", pct(ordem[METRICA].head(TOPO).sum() / total),
                     f"do déficit {DE}, entre {num(len(areas))} municípios com cartório"),
              ui.kpi("Municípios com algum déficit", f"{num((areas[METRICA] > 0).sum())} de {num(len(areas))}",
                     "o déficit está espalhado, mas é pequeno fora das maiores cidades")], 3)
else:
    pos = ranking[ranking["area_id"] == mun["area_id"]].iloc[0]
    ui.grade([ui.kpi(f"Déficit em {mun_nome}", foco["valor_txt"], "a parte da dívida trabalhista sem bens que a cubram",
                     dica="déficit de cobertura: precisa de garantia (fiança bancária ou seguro); suposição do modelo"),
              ui.kpi(f"Parte do déficit {DE}", foco["pct_txt"],
                     f"{num(pos['posicao'])}º de {num(len(ranking))} municípios no déficit"),
              ui.kpi("Cartórios no município", num(foco["n_serventias"]), "ativos no cadastro do CNJ")], 3)


# ------------------------------------------------------------------ mapa clicável (V3, D-089): mapa num cartão e, ao lado,
# a lista dos maiores ou o município escolhido. Clique, busca e "Ver os 10…" mudam o município; os botões dos estados,
# "Ver o Sudeste inteiro" e o clique num município de outro estado mudam o recorte.
TODAS = ufs()
todas = tab("SELECT area_id, area_nome, uf FROM gold.mercado_area_publico WHERE uf IN (SELECT unnest(?))", (TODAS,))
uf_da_area = dict(zip(todas["area_id"], todas["uf"]))
nome_da_area = dict(zip(todas["area_id"], todas["area_nome"]))
rotulo_da_area = dict(zip(municipios["area_id"], municipios["rotulo"]))


def _escolher(area_id: str | None) -> None:
    if area_id is None:                       # "Ver os 10 que mais faltam cobrir"
        st.session_state[f"f_mun_{E}"] = "Todos"
    elif area_id in rotulo_da_area:
        st.session_state[f"f_mun_{E}"] = rotulo_da_area[area_id]
    elif area_id in uf_da_area:               # a busca achou um município de outro estado: o foco vai para lá
        u = uf_da_area[area_id]
        st.session_state["escopo"] = u
        st.session_state[f"f_mun_{u}"] = nome_da_area[area_id]


def _recorte(pedido: str) -> None:
    st.session_state["escopo"] = pedido


ids_int = (list(municipios.loc[(municipios["regiao_intermediaria"] == mun["regiao_intermediaria"])
                               & (municipios["uf"] == mun["uf"]), "area_id"].unique())
           if mun is not None else None)
geo_dados = geometrias(f"SELECT area_id, geometria FROM gold.geo_mapa_publico WHERE {EM}", (UFS,))
geo_sem = geometrias(f"SELECT area_id, geometria FROM gold.geo_sem_serventia WHERE {EM}", (UFS,))


@st.cache_data
def malha_ufs() -> dict[str, dict]:
    """Contorno de cada UF (malha do IBGE versionada em data/brasil): as divisas do recorte e os vizinhos em cinza."""
    return brasil.geometrias(brasil.local())


UF_GEO = malha_ufs()
OUTRAS = [u for u in TODAS if u not in UFS]   # num estado: os outros da região, em cinza e clicáveis
geo_fora = geometrias("SELECT area_id, geometria FROM gold.geo_mapa_publico WHERE uf IN (SELECT unnest(?))",
                      (OUTRAS,)) if OUTRAS else {}
DE_UF = {u: do_estado(u, nome_escopo(u)) for u in TODAS}               # "de Minas Gerais", "do Rio de Janeiro"
estados_mapa = dict(estados={u: UF_GEO[u] for u in UFS if u in UF_GEO},
                    regiao={u: UF_GEO[u] for u in OUTRAS if u in UF_GEO},
                    nomes_estados={u: nome_escopo(u) for u in TODAS},
                    vizinhos={u: g for u, g in UF_GEO.items() if u not in TODAS}, unidade_legenda="mun.",
                    fora=geo_fora,
                    fora_info={a: {"uf": uf_da_area[a], "dica": {"uf": nome_escopo(uf_da_area[a]),
                                                                 "sub": f"Clique para ver só {nome_escopo(uf_da_area[a])}"}}
                               for a in geo_fora},
                    busca=[{"id": r.area_id, "nome": r.area_nome, "uf": r.uf}
                           for r in todas.sort_values(["area_nome", "uf"]).itertuples()],
                    ufs=[{"uf": u, "nome": nome_escopo(u), "ativo": u == E} for u in TODAS],
                    escopo_regiao=REGIAO, regiao_ativa=E == REGIAO)
# o painel ao lado (V3): os 10 que mais faltam cobrir no recorte, ou os números do município escolhido
pos_da_area = dict(zip(ranking["area_id"], ranking["posicao"]))
total_regiao = float(tab("SELECT sum(valor_descoberto) AS v FROM gold.mercado_area_publico WHERE uf IN "
                         "(SELECT unnest(?))", (TODAS,))["v"].iloc[0])
total_uf = areas.groupby("uf")[METRICA].sum().to_dict()
DO_RECORTE = "do Sudeste" if E == REGIAO else DE_UF[E]
if foco is None:
    topo = ranking.head(TOPO)
    maior = float(topo["valor"].iloc[0]) or 1.0
    lado = {"titulo": f"Onde mais falta cobrir {do_escopo(E)}",
            "contexto": f"Os {TOPO} municípios somam {pct(topo['valor'].sum() / total)} do déficit {DO_RECORTE} "
                        f"({brl(total)}).",
            "lista": [{"id": r.area_id, "pos": f"{num(r.posicao)}º", "nome": rotulo(r.municipio, r.uf),
                       "valor": brl(r.valor), "frac": round(float(r.valor) / maior, 4)} for r in topo.itertuples()]}
else:
    v = float(foco[METRICA])
    lado = {"titulo": mun_nome, "contexto": nome_escopo(foco["uf"]), "valor": brl(v),
            "sub": (f"falta cobrir · {num(pos_da_area[foco['area_id']])}º de {num(len(areas))} municípios {DO_RECORTE}"
                    if v > 0 else "tem cartório, mas o modelo estima que nenhum é obrigado à garantia"),
            "linhas": [["Cartórios", num(foco["n_serventias"])], ["Empregados com carteira", num(foco["clt"])],
                       ["Obrigados à garantia", "≈ " + num(foco["n_universo"])],
                       [f"Parte do déficit {DE_UF[foco['uf']]}", pct(v / total_uf[foco["uf"]]) if v > 0 else "0%"],
                       ["Parte do déficit do Sudeste", pct(v / total_regiao, 2) if v > 0 else "0%"]],
            "voltar": f"Ver os {TOPO} que mais faltam cobrir"}
estados_mapa["lado"] = lado
# o que o mapa mostra (V5, D-082): o déficit em R$ ou um indicador de classe em % (o mapa da aba Classes)
INDICADORES = {"Déficit (R$)": None, "% obrigados": "obrigados", "% na Classe 3": "classe_3"}
escolha = st.segmented_control("Mostrar no mapa", list(INDICADORES), default="Déficit (R$)", key="f_indicador")
indicador = INDICADORES.get(escolha or "Déficit (R$)")
nomes = dict(zip(areas["area_id"], areas["area_nome"]))
if indicador is None:
    valores = dict(zip(areas["area_id"], areas[METRICA]))
    textos = {r.area_id: f"Cartórios: {num(r.n_serventias)} · Déficit: {r.valor_txt} ({r.pct_txt} {DE})"
              for r in areas.itertuples()}
    # balão de cada município (V3): valor, posição no recorte e alguns números
    dicas = {r.area_id: {"uf": nome_escopo(r.uf), "valor": brl(r.valor_descoberto),
                         "sub": (f"falta cobrir · {num(pos_da_area[r.area_id])}º de {num(len(areas))} municípios "
                                 f"{DO_RECORTE}" if r.valor_descoberto > 0
                                 else "tem cartório, mas o modelo estima que nenhum é obrigado à garantia"),
                         "linhas": [["Cartórios", num(r.n_serventias)], ["Obrigados à garantia", "≈ " + num(r.n_universo)],
                                    ["Parte do déficit do estado",
                                     pct(r.valor_descoberto / total_uf[r.uf]) if r.valor_descoberto > 0 else "0%"]]}
             for r in areas.itertuples()}
    # resumo em uma frase (V3): onde se concentra e quantos têm zero
    n_zero = int((areas[METRICA] <= 0).sum())
    tres = [rotulo(r.area_nome, r.uf) for r in areas.sort_values(METRICA, ascending=False).head(3).itertuples()]
    resumo = (f"O que falta cobrir está concentrado em {tres[0]}, {tres[1]} e {tres[2]}. Dos {num(len(areas))} "
              f"municípios com cartório, em {num(n_zero)} o modelo estima que nenhum é obrigado à garantia.")
    # protótipo V3 (D-089): legenda "150 mil a 300 mil" (o "R$" no título), zero explicado, o total num cartão e as 3
    # maiores com o valor
    extra = dict(titulo_legenda=f"Falta cobrir (déficit) no município, R$ · {NOME}",
                 fmt_legenda=lambda v: brl_curto(v).removeprefix("R$ "), texto_zero="Zero: nenhum obrigado",
                 info={"titulo": f"Falta cobrir · {NOME}", "valor": brl(total),
                       "nota": f"{num(len(areas))} municípios com cartório"},
                 destaques=3, dicas=dicas)
    nota_cor = "Valores estimados com as suposições do estudo"
else:
    por_uf = {u: analise("percentual_por_municipio", uf=u, indicador=indicador) for u in UFS}
    pc = next(iter(por_uf.values()))
    valores_pc = {a: v for p in por_uf.values() for a, v in p["valores"].items()}
    valores = {a: valores_pc.get(a) for a in areas["area_id"]}
    textos = {r.area_id: f"Cartórios: {num(r.n_serventias)} · {pc['titulo']}: {pct(valores_pc.get(r.area_id, 0))}"
              for r in areas.itertuples()}
    if VARIAS:
        resumo = (f"{pc['titulo']}, estado por estado: " + "; ".join(f"{u} {p['estado']}" for u, p in por_uf.items())
                  + f". {num(sum(p['zeros'] for p in por_uf.values()))} dos {num(len(areas))} municípios com cartório "
                  "têm 0% (em cinza).")
    else:
        resumo = (f"{pc['frase_estado']}; {num(pc['zeros'])} dos {num(pc['areas'])} municípios com cartório têm 0% "
                  f"(em cinza). Com 5 ou mais cartórios, os maiores: {', '.join(pc['maiores_com_5_ou_mais'])}.")
    # sem rótulos: muitos municípios pequenos empatam em 100%, e o rótulo apontaria um deles ao acaso
    extra = dict(titulo_legenda=f"{pc['titulo']} (% dos cartórios do município) · {NOME}", fmt_legenda=pct_curto,
                 teto_fixo=1.0, rotulos=0,
                 dicas={r.area_id: {"uf": nome_escopo(r.uf), "valor": pct(valores_pc.get(r.area_id, 0)),
                                    "sub": pc["titulo"].lower(), "linhas": [["Cartórios", num(r.n_serventias)]]}
                        for r in areas.itertuples()})
    nota_cor = f"Cor = {pc['titulo'].lower()} (% dos cartórios do município; classe aproximada)"
preliminar_txt = ("; SP, RJ e ES com as de Minas Gerais (estimativa preliminar)" if VARIAS
                  else "; com as de Minas Gerais (estimativa preliminar)" if preliminar(E) else "")
mapa_clicavel(dados_mapa(geo_dados, valores, nomes, textos, fundo=geo_sem.values(),
                         selecionado=foco["area_id"] if foco is not None else None, enquadrar=ids_int,
                         resumo=resumo, legenda_fundo="Sem cartório",
                         rotulo_inteiro="Ver o Sudeste inteiro",
                         fonte=fonte_linha(["cnj_serventias", "rais_vinculos", "ibge_malha"], nota_cor + preliminar_txt,
                                           uf=UFS[0]) + ".",
                         **estados_mapa, **extra),
              key=f"mapa_{E}", ao_escolher=_escolher, ao_estado=_recorte)

# ------------------------------------------------------------------ quadro do município (V5, D-082): os cartórios dele
if mun is not None:
    quadro = analise("cartorios_do_municipio", uf=mun["uf"], municipio=mun_nome)
    st.header(f"Os cartórios de {rotulo(mun_nome, mun['uf'])}")
    if VARIAS and preliminar(mun["uf"]):
        avisar_se_preliminar(mun["uf"])
    ui.frase(f"**{quadro['n_cartorios']}** cartórios ativos, **{quadro['obrigados']}** obrigados pelo Prov. 227; "
             f"déficit esperado de **{quadro['deficit_esperado']}** e prêmio de **{quadro['premio_anual']}** por ano. "
             "Cada cartório aparece pelo CNS, do maior para o menor déficit.")
    ui.tabela(["CNS", "Atribuições", "Classe", "Obrigado", "Empregados", "Déficit esperado", "Prêmio por ano"],
              [[c["cns"], c["atribuicoes"], f"{c['classe']} ({c['situacao']})", c["obrigado"], c["empregados_clt"],
                c["deficit_esperado"], c["premio_anual"]] for c in quadro["cartorios"]],
              numericas={4, 5, 6}, mudas={1}, so_no_computador={3, 4, 6})
    ui.fonte(fonte_linha(["cnj_serventias", "rais_vinculos"],
                         "Déficit e prêmio por cartório: estimativas do modelo (nível base); classe aproximada",
                         uf=mun["uf"]))

# (o ranking dos maiores fica no painel ao lado do mapa, V3)
if VARIAS:   # no Sudeste: a parte de cada estado no déficit
    partes = areas.groupby("uf")[METRICA].sum().sort_values(ascending=False)
    ui.frase("Parte de cada estado no déficit do Sudeste: "
             + "; ".join(f"**{nome_escopo(u)}** {pct(v / total)}" for u, v in partes.items()) + ".")
else:
    conc = analise("concentracao", uf=E)
    grp = analise("grupos", uf=E)
    ui.frase(f"Os {conc['topo']} maiores cartórios obrigados têm **{conc['parte_dos_maiores_no_passivo']}** da dívida "
             f"trabalhista; o cliente típico do seguro são as **{grp['grupo_alvo'].split(': ')[1]}** "
             f"({grp['serventias_do_alvo']} cartórios, {grp['parte_do_deficit']} do déficit).")
if mun is None:
    ui.sugestoes(["Quais cartórios de Uberaba são obrigados?", "Que tipo de cartório é obrigado pelo Prov. 227?",
                  f"Quantos cartórios vagos (interinos) há {do_escopo(E)}?"], pagina="Onde está o mercado")
else:   # "Perguntar sobre este município" (V5): o chat recebe a página, o município aberto e a UF dele
    ui.sugestoes([f"Quais cartórios de {mun_nome} são obrigados e quanto é o déficit deles?",
                  "Por que o déficit deste município é desse tamanho?",
                  f"Como este município se compara com o resto {DE}?"],
                 pagina="Onde está o mercado", municipio=mun_nome, uf=mun["uf"])
