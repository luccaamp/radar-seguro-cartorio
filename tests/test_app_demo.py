"""Painel no MODO DEMONSTRAÇÃO (D-029): sem banco local, só com o conjunto público versionado em data/publico.

Roda em qualquer clone (suíte padrão). O banco de demonstração é temporário, montado a partir dos Parquet públicos.
"""
import hashlib
import json
import re

import duckdb
import pytest

from apoio_painel import (HISTORIA, MERCADO, PAGINAS, RAIZ, SELETOR_MUNICIPIO_MG, SIMULADOR, SOBRE, mapa_componente,
                          pagina_em_mg)

pytestmark = pytest.mark.usefixtures("painel_demo")


def rodar(pagina: str):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / pagina), default_timeout=120).run()
    assert not at.exception, at.exception
    return at


def ler(painel_demo, sql: str, params: list | None = None):
    # mesma configuração da conexão do painel (o DuckDB não abre o mesmo arquivo com configurações diferentes no
    # mesmo processo); é o banco temporário de demonstração, não o banco real
    with duckdb.connect(str(painel_demo["banco"]), read_only=True) as con:
        return con.execute(sql, params or []).df()


def html(at) -> str:
    return "\n".join(m.value for m in at.markdown).replace("&#36;", "$")


def figuras(at) -> list[dict]:
    return [json.loads(g.proto.spec) for g in at.get("plotly_chart")]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_roda_com_faixa_e_carga_no_rodape(pagina):
    """D-051: o aviso do modo demonstração e o rodapé com versão e carga ficam em "Sobre os dados" (e no chat e no
    Simulador, que não mudaram); as páginas da história têm só a linha de fonte (fonte e data)."""
    at = rodar(pagina)
    import comum
    assert comum.modo() == "demonstracao"
    if pagina in HISTORIA and pagina != SOBRE:
        textos = html(at) + "".join(a["text"] for f in figuras(at) for a in f["layout"].get("annotations", []))
        assert "Fonte: CNJ, Justiça Aberta (" in textos
        return
    assert any("Modo demonstração" in c.value and "Como rodar" in c.value for c in at.caption)
    rodapes = [c.value for c in at.caption if "Fontes:" in c.value]
    assert rodapes and all("Premissas:" in r and "· demonstração" in r for r in rodapes)


# ------------------------------------------------------------------ terceira rodada do painel (D-051)
TECNICO = re.compile(r"premissas v\d|versão \d|\bv\d\b|\bD-0\d\d\b|gold\.|silver\.|notebook|\bcarga\b|\bnível\b|"
                     r"\bUF\b|\bSTF\b|ADI 8015", re.I)


@pytest.mark.parametrize("pagina", [p for p in HISTORIA if p != SOBRE])
def test_nada_tecnico_fora_de_sobre_os_dados(pagina):
    """Etiquetas técnicas (carga, versão de premissas, nível, UF), IDs de decisão, nomes de tabela e de notebook e o
    STF só aparecem em "Sobre os dados" (ou no chat)."""
    at = rodar(pagina)
    textos = [html(at)] + [c.value for c in at.caption] + [
        f["layout"].get("title", {}).get("text", "") + " ".join(a["text"] for a in f["layout"].get("annotations", []))
        for f in figuras(at)]
    achados = [m.group(0) for t in textos for m in TECNICO.finditer(re.sub(r"<style>.*?</style>", "", t, flags=re.S))]
    assert not achados, achados


@pytest.mark.parametrize("pagina", HISTORIA)
def test_limites_da_pagina(pagina):
    """Uma manchete (h1), no máximo 3 números em destaque, no máximo 2 gráficos e de 2 a 3 perguntas para o chat,
    cada uma com o link para o chat com a pergunta preenchida. Exceção (D-082, 2026-11-10): o Início é o Panorama do
    V5, com a resposta e os 6 indicadores (7 destaques); as outras páginas seguem o limite de 3 da D-051."""
    at = rodar(pagina)
    tela = html(at)
    assert tela.count("<h1>") == 1
    destaque = tela.count('<div class="rd-card">') + tela.count('<div class="rd-resposta">')
    limite = 7 if pagina == HISTORIA[0] else 3
    assert destaque <= limite and len(figuras(at)) <= 2, (destaque, len(figuras(at)))
    links = re.findall(r'href="Chat\?pergunta=([^"]+)"', tela)
    assert 2 <= len(links) <= 3


def test_nenhum_cartao_repete_numero_entre_paginas():
    """Nenhum número em destaque (cartão ou resposta) aparece em duas páginas da história."""
    vistos: dict[str, str] = {}
    for pagina in HISTORIA:
        for v in re.findall(r'<div class="rd-num">([^<]+)', html(rodar(pagina))):
            assert v.strip() not in vistos, (v, pagina, vistos.get(v.strip()))
            vistos[v.strip()] = pagina


def test_simulador_padrao_igual_ao_cenario_base_do_painel(painel_demo):
    """Nas premissas padrão, o Simulador de demonstração mostra os números do gold (sem seta de diferença)."""
    at = rodar(SIMULADOR)
    from comum import aprox, brl
    ref = ler(painel_demo, "SELECT * FROM gold.fato_mercado_uf WHERE nivel = 'base' AND regra_classe = 'v2' "
                           "AND cenario_stf = 'mantem' AND uf = 'MG'").iloc[0]   # o Simule abre em MG
    m = {x.label: x for x in at.metric}
    assert m["Obrigadas (universo)"].value == aprox(ref["n_universo"])
    assert m["Passivo dos obrigados"].value == brl(ref["passivo_universo"])
    assert m["Com déficit (esperado)"].value == aprox(ref["n_deficit"])
    assert m["Déficit de cobertura"].value == brl(ref["valor_descoberto"])
    assert not [x for x in at.metric if x.delta], [(x.label, x.delta) for x in at.metric if x.delta]  # sem seta


def test_simulador_suspende_zera_premio():
    at = rodar(SIMULADOR)
    at.radio(key="x_cenario").set_value("suspende_8_17").run()
    assert not at.exception
    premios = [m.value for m in at.metric if m.label == "Prêmio emitido"]
    assert premios and all(v == "R$ 0" for v in premios)


def test_simulador_uma_premissa_do_passivo_usa_a_grade(painel_demo):
    from comum import brl
    at = rodar(SIMULADOR)
    fap = next(s for s in at.select_slider if s.label.startswith("FAP"))
    fap.set_value(2.0).run()
    assert not at.exception and not at.warning
    var = ler(painel_demo, "SELECT passivo_universo FROM gold.simulador_variantes WHERE regra_classe = 'v2' AND "
                           "metodo_rateio = 'por_empregados_cnj' AND premissa_variada = 'fap' AND fap = 2.0 "
                           "AND uf = 'MG'")
    assert len(var) == 1
    assert [m.value for m in at.metric if m.label == "Passivo dos obrigados"] == [brl(var.iloc[0, 0])]


def test_simulador_duas_premissas_do_passivo_avisa_e_nao_calcula():
    at = rodar(SIMULADOR)
    next(s for s in at.select_slider if s.label.startswith("FAP")).set_value(2.0).run()
    next(s for s in at.select_slider if s.label.startswith("Férias")).set_value(1.0).run()
    assert not at.exception
    assert any("mais de uma premissa do passivo" in w.value for w in at.warning)
    assert not [m for m in at.metric if m.label == "Prêmio emitido"]


def test_salvar_cenario_desativado():
    at = rodar(SIMULADOR)
    assert next(b for b in at.button if b.label == "Salvar").disabled and at.text_input[0].disabled
    assert any("Desativado no modo demonstração" in c.value for c in at.caption)


def _premio_mercado(at) -> str:
    return [m.value for m in at.metric if m.label == "Prêmio emitido"][0]


def test_explorar_mostra_faixa_por_sorteio_e_tornado_ao_redor_do_padrao():
    """D-077: com os controles no padrão, a faixa por sorteio e o tornado aparecem, e o prêmio é o do painel."""
    at = rodar(SIMULADOR)
    titulos = [f["layout"]["title"]["text"].replace("<br>", " ") for f in figuras(at)]   # título quebrado em linhas
    assert any("faixa azul" in t for t in titulos) and any("o que mais mexe no prêmio" in t for t in titulos)
    assert "o mesmo valor do painel" in html(at)


def test_explorar_atalho_da_taxa_e_voltar_ao_base():
    at = rodar(SIMULADOR)
    base = _premio_mercado(at)
    next(b for b in at.button if b.label == "E se a taxa fosse 3%?").click().run()
    assert not at.exception
    assert at.select_slider(key="x_taxa").value == 3.0
    assert _premio_mercado(at) != base and "em relação ao painel" in html(at)
    next(b for b in at.button if b.label == "Voltar ao cenário base").click().run()
    assert _premio_mercado(at) == base


def test_explorar_suspensao_sem_faixa_nem_tornado():
    at = rodar(SIMULADOR)
    next(b for b in at.button if b.label == "E se o STF suspender a obrigação?").click().run()
    assert not at.exception and at.radio(key="x_cenario").value == "suspende_8_17"
    assert _premio_mercado(at) == "R$ 0" and not figuras(at) and "o prêmio é zero" in html(at)


def test_explorar_adesao_alta_reduz_a_fianca_que_nao_cabe():
    """A fiança cabe no que sobra da adesão: com 90% no seguro, a fiança vai a no máximo 10%, sem erro."""
    at = rodar(SIMULADOR)
    at.slider(key="x_seguro").set_value(90).run()
    assert not at.exception and at.slider(key="x_fianca").value <= 10


def test_abrir_as_paginas_nao_altera_o_banco_de_demonstracao(painel_demo):
    """D-034: o painel abre o banco só para leitura, também no modo demonstração."""
    antes = hashlib.sha256(painel_demo["banco"].read_bytes()).hexdigest()
    for pagina in PAGINAS:
        rodar(pagina)
    assert hashlib.sha256(painel_demo["banco"].read_bytes()).hexdigest() == antes


def test_mercado_municipio_pequeno_aparece_sozinho(painel_demo):
    """D-078 (D-038, fase 2): no modo demonstração, um município com 1 serventia mostra os números dele e entra no
    mapa com área própria, sem aviso de agregação."""
    d = ler(painel_demo, """SELECT d.municipio, d.cod_ibge FROM gold.dim_municipio d
                            WHERE d.n_serventias = 1 AND d.uf = 'MG' ORDER BY d.municipio LIMIT 1""").iloc[0]
    com_serv = int(ler(painel_demo, "SELECT count(*) FROM gold.dim_municipio WHERE n_serventias > 0 AND uf = 'MG'"
                       ).iloc[0, 0])
    at = pagina_em_mg(MERCADO)
    at.selectbox(key=SELETOR_MUNICIPIO_MG).set_value(d["municipio"]).run()
    assert not at.exception
    assert not any("agregad" in i.value for i in at.info)
    tela = html(at)
    assert f"Déficit em {d['municipio']}" in tela
    assert 'Cartórios no município</div><div class="rd-num">1</div>' in tela
    mapa = mapa_componente(at)
    locais = [a["id"] for a in mapa["areas"]]
    assert len(locais) == com_serv and str(d["cod_ibge"]) in locais and mapa["selecionado"] == str(d["cod_ibge"])


def test_sem_formula_latex_nos_textos():
    latex = re.compile(r"(?<!\\)\$[^$]+(?<!\\)\$")
    for pagina in PAGINAS:
        at = rodar(pagina)
        ruins = [t[:80] for t in [m.value for m in at.markdown] + [c.value for c in at.caption] if latex.search(t)]
        assert not ruins, (pagina, ruins)


def test_sobre_os_dados_mostra_a_saude_dos_dados(painel_demo):
    """Fase 2, página de saúde: data dos dados, premissas, contratos, conferências e a versão publicada."""
    at = rodar(SOBRE)
    assert "Saúde dos dados" in [h.value for h in at.header]
    texto = html(at)
    for trecho in ("Contratos de qualidade", "Conferências entre fontes", "Conjunto publicado em", "commit "):
        assert trecho in texto, trecho
    erros = ler(painel_demo, "SELECT count(*) AS n FROM qualidade.checagens WHERE severidade = 'erro' AND violacoes > 0")
    assert f"{int(erros.n[0])} erro" in texto
