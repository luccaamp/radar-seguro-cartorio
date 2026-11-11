"""Brasil: os cartórios das 27 UFs, camada 1 (D-087; visão "Cartórios do Brasil" do V5, D-082).

Só o que o cadastro nacional do CNJ e o IBGE dão, sem o modelo: serventias ativas, vagas, municípios com cartório e
cartórios por 100 mil habitantes. O estudo completo do seguro (prêmio, déficit, quão certo é) continua só em MG; o
mapa leva até ele. Os dados vêm da publicação mais recente do pipeline agendado (Release `brasil-*`), conferida pelo
SHA-256; sem ela, da cópia em data/brasil/. O selo diz a data e a origem.
"""
import streamlit as st

from comum import num, pagina, pct
from src.painel import brasil, ui
from src.painel.mapa import dados_mapa, mapa_clicavel, pct_curto

pagina("Brasil", "🇧🇷", "Cartórios do Brasil",
       "Quantos cartórios há em cada estado, quantos estão sem titular e onde faltam. O estudo completo do seguro, "
       "por enquanto, é o de Minas Gerais.", sobre="Brasil")


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def publicacao() -> brasil.Publicacao:
    return brasil.publicacao()


def _data(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}"


p = publicacao()
t = brasil.totais(p)
cnj = p.manifesto["fontes"]["cnj_cadastro"]["coletado_em"]
ui.contexto([("Atualizado em", _data(p.data)), ("Cadastro do CNJ de", ", ".join(_data(d) for d in cnj)),
             ("População", f"IBGE, estimativa {p.manifesto['fontes']['ibge']['populacao_estimada']}"),
             ("Origem", p.origem)])
if p.avisos:   # o motivo técnico fica em p.avisos (testes); o visitante lê só a consequência
    st.caption("A publicação mensal não respondeu agora; os números são da cópia guardada no repositório.")

ui.grade([ui.kpi("Cartórios ativos", num(t["serventias_ativas"]), "nas 27 unidades da federação"),
          ui.kpi("Sem titular", pct(t["pct_vagas"]), f"{num(t['vagas'])} vagos, respondidos por interino",
                 dica="situação jurídica VAGO no cadastro do CNJ: sem titular concursado"),
          ui.kpi("Municípios com cartório", pct(t["pct_municipios_com_cartorio"]),
                 f"{num(t['municipios_com_cartorio'])} de {num(t['municipios'])}"),
          ui.kpi("Por 100 mil habitantes", num(t["por_100mil_hab"], 1), "cartórios ativos")], 4)

# ------------------------------------------------------------------ mapa por UF (o mesmo componente do mapa de MG)
INDICADORES = {
    "Por 100 mil hab.": ("por_100mil_hab", lambda v: num(v, 1), None),
    "Cartórios": ("serventias_ativas", lambda v: num(v), None),
    "% sem titular": ("pct_vagas", pct, 1.0),
    "% municípios com cartório": ("pct_municipios_com_cartorio", pct, 1.0),
}
escolha = st.segmented_control("Mostrar no mapa", list(INDICADORES), default="Por 100 mil hab.", key="f_ind_br")
coluna, fmt, teto = INDICADORES[escolha or "Por 100 mil hab."]
por_uf = {x["uf"]: x for x in p.linhas}
valores = {uf: x[coluna] for uf, x in por_uf.items()}
textos = {uf: (f"{num(x['serventias_ativas'])} cartórios · {num(x['por_100mil_hab'], 1)} por 100 mil hab. · "
               f"{pct(x['pct_vagas'])} sem titular") for uf, x in por_uf.items()}
ordem = sorted(por_uf.values(), key=lambda x: -(x[coluna] or 0))
resumo = (f"Mais alto em {ordem[0]['nome']}, {ordem[1]['nome']} e {ordem[2]['nome']}; mais baixo em "
          f"{ordem[-1]['nome']}. Clique num estado para ver os números dele.")


def _escolher(uf: str) -> None:
    st.session_state["f_uf"] = uf


uf = st.session_state.get("f_uf")
mapa_clicavel(dados_mapa(brasil.geometrias(p), valores, {u: x["nome"] for u, x in por_uf.items()}, textos,
                         selecionado=uf, resumo=resumo, titulo_legenda=escolha or "",
                         fmt_legenda=pct_curto if teto else (lambda v: num(v, 1 if coluna == "por_100mil_hab" else 0)),
                         teto_fixo=teto, rotulo_inteiro="Ver o Brasil inteiro"),
              key="mapa_br", ao_escolher=_escolher)
ui.fonte(f"Fonte: CNJ, Justiça Aberta (cadastro de serventias, {', '.join(_data(d) for d in cnj)}); IBGE "
         f"(municípios, população estimada {p.manifesto['fontes']['ibge']['populacao_estimada']} e malha dos estados). "
         f"Cor = {(escolha or '').lower().rstrip('.')}.")

# ------------------------------------------------------------------ o estado escolhido
if uf in por_uf:
    x = por_uf[uf]
    st.header(f"Os cartórios {brasil.do_estado(uf, x['nome'])}")
    ui.frase(f"**{num(x['serventias_ativas'])}** cartórios ativos em **{num(x['municipios_com_cartorio'])}** dos "
             f"{num(x['municipios'])} municípios; **{pct(x['pct_vagas'])}** sem titular e **{num(x['oficializadas'])}** "
             f"oficializados. São **{num(x['por_100mil_hab'], 1)}** por 100 mil habitantes (Brasil: "
             f"{num(t['por_100mil_hab'], 1)}).")
    ui.tabela(["Atribuição", "Cartórios"],
              [[r, num(x[c])] for r, c in (("Notas", "notas"), ("Registro Civil das Pessoas Naturais", "rcpn"),
                                           ("Registro de Imóveis", "ri"), ("Protesto de Títulos", "protesto"),
                                           ("Títulos e Documentos", "rtd"), ("Pessoas Jurídicas", "rcpj"))],
              numericas={1})
    if uf == "MG":
        st.page_link("pages/2_Onde_está_o_mercado.py", label="Ver o estudo completo de Minas Gerais: o mercado do "
                     "seguro por município →")
    else:
        ui.frase("O prêmio do seguro e o déficit de cobertura deste estado ainda não foram calculados: exigem a RAIS "
                 "e as premissas calibradas do estado (próximas fases do projeto).")

# ------------------------------------------------------------------ todos os estados
st.header("Todos os estados")
ui.tabela(["UF", "Cartórios", "Por 100 mil hab.", "Sem titular", "Municípios com cartório"],
          [[f"{x['nome']} ({x['uf']})", num(x["serventias_ativas"]), num(x["por_100mil_hab"], 1), pct(x["pct_vagas"]),
            f"{num(x['municipios_com_cartorio'])} de {num(x['municipios'])}"]
           for x in sorted(p.linhas, key=lambda x: -x["serventias_ativas"])],
          numericas={1, 2, 3, 4}, so_no_computador={4})
ui.frase("**Sem titular** = situação jurídica VAGO no cadastro: o cartório é respondido por um interino até o "
         "concurso. **Municípios com cartório** casa a cidade do cadastro com a lista do IBGE.")
