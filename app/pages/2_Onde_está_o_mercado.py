"""Onde está o mercado: o mapa do déficit de cobertura (o que vira seguro) por município, com um filtro só (município).

Só lê tabelas públicas do gold (1.7), na regra base e no nível base. Desde a D-078 (D-038, fase 2) cada município com
cartório é uma área do mapa, inclusive os de 1 ou 2 cartórios. Dois modos (U1):
- sem município: o mapa de MG e os 10 municípios com mais déficit;
- município: destaque com contexto e zoom na região intermediária, e a posição dele no ranking de MG.
Os filtros por atribuição, situação e classe, as outras métricas e a tabela por área saíram do painel
(docs/painel/corte.md); o chat responde por município e por recorte.
"""
import json

import pandas as pd
import streamlit as st

from comum import analise, brl, consulta, fonte_linha, num, pagina, pct
from src.painel import ui
from src.painel.mapa import dados_mapa, mapa_clicavel

pagina("Onde está o mercado", "🗺️", "Onde está o dinheiro?",
       "O déficit de cobertura, que é o que vira seguro, se concentra nas maiores cidades. Escolha um município para "
       "ver a parte dele.", sobre="Onde está o mercado")
TOPO = 10   # municípios na lista do ranking
METRICA = "valor_descoberto"


# ------------------------------------------------------------------ dados (só tabelas públicas, com cache)
@st.cache_data
def tab(sql: str, params: tuple = ()) -> pd.DataFrame:
    return consulta(sql, list(params))


@st.cache_data
def geometrias(sql: str, params: tuple = ()) -> dict[str, dict]:
    g = consulta(sql, list(params))
    return {a: json.loads(x) for a, x in zip(g["area_id"], g["geometria"])}


areas = tab("SELECT * FROM gold.mercado_area_publico")
municipios = tab("""SELECT m.cod_ibge, m.nome, m.regiao_imediata, m.regiao_intermediaria, a.area_id, d.n_serventias
                    FROM silver.municipio_ibge m JOIN gold.geo_area_municipio a USING (cod_ibge)
                    JOIN gold.dim_municipio d USING (cod_ibge) ORDER BY m.nome""")
sem_serventia = tab("SELECT municipio FROM gold.dim_municipio WHERE n_serventias = 0")["municipio"].tolist()
ranking = tab("SELECT cod_ibge, municipio, valor, posicao, n_municipios FROM gold.ranking_municipio_publico "
              "WHERE metrica = ? ORDER BY posicao, municipio", (METRICA,))
total_mg = float(areas[METRICA].sum())
areas["valor_txt"] = areas[METRICA].map(brl)
areas["pct_txt"] = [pct(v / total_mg) for v in areas[METRICA]]

# ------------------------------------------------------------------ o filtro principal
c_filtro, _ = st.columns([4, 8])
mun_nome = c_filtro.selectbox("Município", ["Todos"] + sorted(municipios["nome"].tolist() + sem_serventia),
                              key="f_mun")
mun = municipios[municipios["nome"] == mun_nome].iloc[0] if mun_nome not in ("Todos", *sem_serventia) else None
foco = areas[areas["area_id"] == mun["area_id"]].iloc[0] if mun is not None else None
if mun_nome in sem_serventia:
    st.info(f"{mun_nome} não tem cartório no cadastro do CNJ. Mostrando Minas Gerais inteira.")

# ------------------------------------------------------------------ até 3 números
if foco is None:
    ordem = areas.sort_values(METRICA, ascending=False)
    maior = ordem.iloc[0]
    ui.grade([ui.kpi(f"Só {maior['area_nome']}", maior["pct_txt"], f"do déficit de MG ({maior['valor_txt']})"),
              ui.kpi(f"Os {TOPO} municípios com mais déficit", pct(ordem[METRICA].head(TOPO).sum() / total_mg),
                     f"do déficit de MG, entre {num(len(areas))} municípios com cartório"),
              ui.kpi("Municípios com algum déficit", f"{num((areas[METRICA] > 0).sum())} de {num(len(areas))}",
                     "o déficit está espalhado, mas é pequeno fora das maiores cidades")], 3)
else:
    pos = ranking[ranking["cod_ibge"] == mun["cod_ibge"]].iloc[0]
    ui.grade([ui.kpi(f"Déficit em {mun_nome}", foco["valor_txt"], "a parte da dívida trabalhista sem bens que a cubram",
                     dica="déficit de cobertura: precisa de garantia (fiança bancária ou seguro); suposição do modelo"),
              ui.kpi("Parte do déficit de MG", foco["pct_txt"],
                     f"{num(pos['posicao'])}º de {num(pos['n_municipios'])} municípios no déficit"),
              ui.kpi("Cartórios no município", num(foco["n_serventias"]), "ativos no cadastro do CNJ")], 3)


# ------------------------------------------------------------------ mapa clicável (largura inteira; D-083)
# clicar num município faz o mesmo que escolhê-lo no seletor acima (o seletor continua sendo o caminho pelo teclado)
nome_da_area = dict(zip(municipios["area_id"], municipios["nome"]))


def _escolher(area_id: str) -> None:
    if area_id in nome_da_area:
        st.session_state["f_mun"] = nome_da_area[area_id]


ids_int = (list(municipios.loc[municipios["regiao_intermediaria"] == mun["regiao_intermediaria"], "area_id"].unique())
           if mun is not None else None)
geo_dados = geometrias("SELECT area_id, geometria FROM gold.geo_mapa_publico")
geo_sem = geometrias("SELECT area_id, geometria FROM gold.geo_sem_serventia")
textos = {r.area_id: f"Cartórios: {num(r.n_serventias)} · Déficit: {r.valor_txt} ({r.pct_txt} de MG)"
          for r in areas.itertuples()}
mapa_clicavel(dados_mapa(geo_dados, dict(zip(areas["area_id"], areas[METRICA])),
                         dict(zip(areas["area_id"], areas["area_nome"])), textos, fundo=geo_sem.values(),
                         selecionado=foco["area_id"] if foco is not None else None, enquadrar=ids_int,
                         titulo_legenda="Déficit de cobertura do município",
                         legenda_fundo="Sem cartório no cadastro do CNJ"),
              key="mapa_mg", ao_escolher=_escolher)
ui.fonte(fonte_linha(["cnj_serventias", "rais_vinculos", "ibge_malha"],
                     "Cor = déficit do município (suposição do modelo)"))

# ------------------------------------------------------------------ ranking: os maiores e o município escolhido
linhas = ranking.head(TOPO)
if mun is not None and int(mun["cod_ibge"]) not in set(linhas["cod_ibge"].astype(int)):
    linhas = pd.concat([linhas, ranking[ranking["cod_ibge"] == mun["cod_ibge"]]])
ui.tabela(["Posição", "Município", "Déficit", "Parte de MG"],
          [[f"{num(r.posicao)}º", r.municipio, brl(r.valor), pct(r.valor / total_mg)] for r in linhas.itertuples()],
          numericas={0, 2, 3})

conc = analise("concentracao")
grp = analise("grupos")
ui.frase(f"Os {conc['topo']} maiores cartórios obrigados têm **{conc['parte_dos_maiores_no_passivo']}** da dívida "
         f"trabalhista; o cliente típico do seguro são as **{grp['grupo_alvo'].split(': ')[1]}** "
         f"({grp['serventias_do_alvo']} cartórios, {grp['parte_do_deficit']} do déficit).")
ui.sugestoes(["Quais cartórios de Uberaba são obrigados?", "Que tipo de cartório é obrigado pelo Prov. 227?",
              "Quantos cartórios vagos (interinos) há em MG?"])
