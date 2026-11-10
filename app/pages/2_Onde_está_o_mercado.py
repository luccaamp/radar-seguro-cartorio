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
from src.painel.mapa import dados_mapa, mapa_clicavel, pct_curto

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
# o que o mapa mostra (V5, D-082): o déficit em R$ ou um indicador de classe em % (o mapa da aba Classes)
INDICADORES = {"Déficit (R$)": None, "% obrigados": "obrigados", "% na Classe 3": "classe_3"}
escolha = st.segmented_control("Mostrar no mapa", list(INDICADORES), default="Déficit (R$)", key="f_indicador")
indicador = INDICADORES.get(escolha or "Déficit (R$)")
nomes = dict(zip(areas["area_id"], areas["area_nome"]))
if indicador is None:
    valores = dict(zip(areas["area_id"], areas[METRICA]))
    textos = {r.area_id: f"Cartórios: {num(r.n_serventias)} · Déficit: {r.valor_txt} ({r.pct_txt} de MG)"
              for r in areas.itertuples()}
    # resumo em uma frase (V5): o que o mapa mostra no recorte que está na tela
    n_zero = int((areas[METRICA] <= 0).sum())
    tres = areas.sort_values(METRICA, ascending=False)["area_nome"].head(3).tolist()
    resumo = (f"Os maiores déficits estão em {tres[0]}, {tres[1]} e {tres[2]}; {num(n_zero)} dos {num(len(areas))} "
              "municípios com cartório têm déficit zero (em cinza). Clique num município para ver os números dele.")
    extra = dict(titulo_legenda="Déficit de cobertura do município")
    nota_cor = "Cor = déficit do município (suposição do modelo)"
else:
    pc = analise("percentual_por_municipio", indicador=indicador)
    valores = {a: pc["valores"].get(a) for a in areas["area_id"]}
    textos = {r.area_id: f"Cartórios: {num(r.n_serventias)} · {pc['titulo']}: {pct(pc['valores'].get(r.area_id, 0))}"
              for r in areas.itertuples()}
    resumo = (f"{pc['frase_estado']}; {num(pc['zeros'])} dos {num(pc['areas'])} municípios com cartório têm 0% (em "
              f"cinza). Com 5 ou mais cartórios, os maiores: {', '.join(pc['maiores_com_5_ou_mais'])}.")
    # sem rótulos: muitos municípios pequenos empatam em 100%, e o rótulo apontaria um deles ao acaso
    extra = dict(titulo_legenda=f"{pc['titulo']} (% dos cartórios do município)", fmt_legenda=pct_curto,
                 teto_fixo=1.0, rotulos=0)
    nota_cor = f"Cor = {pc['titulo'].lower()} (% dos cartórios do município; classe aproximada)"
if mun is not None:
    resumo = (f"Região de {mun['regiao_intermediaria']}, com {mun_nome} em destaque (contorno dourado). As cores "
              "seguem a mesma escala de Minas Gerais inteira.")
mapa_clicavel(dados_mapa(geo_dados, valores, nomes, textos, fundo=geo_sem.values(),
                         selecionado=foco["area_id"] if foco is not None else None, enquadrar=ids_int,
                         resumo=resumo, legenda_fundo="Sem cartório no cadastro do CNJ", **extra),
              key="mapa_mg", ao_escolher=_escolher)
ui.fonte(fonte_linha(["cnj_serventias", "rais_vinculos", "ibge_malha"], nota_cor))

# ------------------------------------------------------------------ quadro do município (V5, D-082): os cartórios dele
if mun is not None:
    quadro = analise("cartorios_do_municipio", municipio=mun_nome)
    st.header(f"Os cartórios de {mun_nome}")
    ui.frase(f"**{quadro['n_cartorios']}** cartórios ativos, **{quadro['obrigados']}** obrigados pelo Prov. 227; "
             f"déficit esperado de **{quadro['deficit_esperado']}** e prêmio de **{quadro['premio_anual']}** por ano. "
             "Cada cartório aparece pelo CNS, do maior para o menor déficit.")
    ui.tabela(["CNS", "Atribuições", "Classe", "Obrigado", "Empregados", "Déficit esperado", "Prêmio por ano"],
              [[c["cns"], c["atribuicoes"], f"{c['classe']} ({c['situacao']})", c["obrigado"], c["empregados_clt"],
                c["deficit_esperado"], c["premio_anual"]] for c in quadro["cartorios"]],
              numericas={4, 5, 6}, mudas={1}, so_no_computador={3, 4, 6})
    ui.fonte(fonte_linha(["cnj_serventias", "rais_vinculos"],
                         "Déficit e prêmio por cartório: estimativas do modelo (nível base); classe aproximada"))

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
if mun is None:
    ui.sugestoes(["Quais cartórios de Uberaba são obrigados?", "Que tipo de cartório é obrigado pelo Prov. 227?",
                  "Quantos cartórios vagos (interinos) há em MG?"], pagina="Onde está o mercado")
else:   # "Perguntar sobre este município" (V5): o chat recebe a página e o município aberto
    ui.sugestoes([f"Quais cartórios de {mun_nome} são obrigados e quanto é o déficit deles?",
                  "Por que o déficit deste município é desse tamanho?",
                  "Como este município se compara com o resto de MG?"],
                 pagina="Onde está o mercado", municipio=mun_nome)
