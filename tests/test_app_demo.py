"""Painel no MODO DEMONSTRAÇÃO (D-029): sem banco local, só com o conjunto público versionado em data/publico.

Roda em qualquer clone (suíte padrão). O banco de demonstração é temporário, montado a partir dos Parquet públicos.
"""
import hashlib
import json
import re

import duckdb
import pytest

from apoio_painel import HISTORIA, MERCADO, PAGINAS, RAIZ, SIMULADOR, SOBRE

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
    cada uma com o link para o chat com a pergunta preenchida."""
    at = rodar(pagina)
    tela = html(at)
    assert tela.count("<h1>") == 1
    destaque = tela.count('<div class="rd-card">') + tela.count('<div class="rd-resposta">')
    assert destaque <= 3 and len(figuras(at)) <= 2, (destaque, len(figuras(at)))
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
                           "AND cenario_stf = 'mantem'").iloc[0]
    m = {x.label: x for x in at.metric}
    assert m["Obrigadas (universo)"].value == aprox(ref["n_universo"])
    assert m["Passivo dos obrigados"].value == brl(ref["passivo_universo"])
    assert m["Com déficit (esperado)"].value == aprox(ref["n_deficit"])
    assert m["Déficit de cobertura"].value == brl(ref["valor_descoberto"])
    assert not [x for x in at.metric if x.delta], [(x.label, x.delta) for x in at.metric if x.delta]  # sem seta


def test_simulador_suspende_zera_premio():
    at = rodar(SIMULADOR)
    at.radio[0].set_value("suspende_8_17").run()
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
                           "metodo_rateio = 'por_empregados_cnj' AND premissa_variada = 'fap' AND fap = 2.0")
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
    assert at.button[0].disabled and at.text_input[0].disabled
    assert any("Desativado no modo demonstração" in c.value for c in at.caption)


def test_abrir_as_paginas_nao_altera_o_banco_de_demonstracao(painel_demo):
    """D-034: o painel abre o banco só para leitura, também no modo demonstração."""
    antes = hashlib.sha256(painel_demo["banco"].read_bytes()).hexdigest()
    for pagina in PAGINAS:
        rodar(pagina)
    assert hashlib.sha256(painel_demo["banco"].read_bytes()).hexdigest() == antes


def test_mercado_municipio_pequeno_aparece_agregado(painel_demo):
    d = ler(painel_demo, """SELECT d.municipio, p.n_serventias FROM gold.dim_municipio d JOIN gold.geo_area_municipio a
                            USING (cod_ibge) JOIN gold.mercado_area_publico p USING (area_id)
                            WHERE d.n_serventias = 1 ORDER BY d.municipio LIMIT 1""").iloc[0]
    at = rodar(MERCADO)
    at.selectbox(key="f_mun").set_value(d["municipio"]).run()
    assert not at.exception
    assert any("agregado" in i.value and "LGPD" in i.value for i in at.info)
    tela = html(at)   # o cartão "Cartórios na área" mostra a área agregada, nunca o município pequeno
    assert f'Cartórios na área</div><div class="rd-num">{d["n_serventias"]}</div>' in tela


def test_lgpd_nenhum_municipio_pequeno_nas_tabelas_e_graficos(painel_demo):
    """D1 no modo demonstração: nenhuma tabela nem texto de gráfico mostra município com menos de 3 serventias."""
    limiar = int(ler(painel_demo, "SELECT max(limiar_lgpd) FROM gold.execucao").iloc[0, 0])
    peq = ler(painel_demo, "SELECT municipio, cod_ibge FROM gold.dim_municipio WHERE n_serventias < ?", [limiar])
    nomes, codigos = set(peq["municipio"]), {str(c) for c in peq["cod_ibge"]}
    assert len(nomes) > 400
    figuras = 0
    for pagina in PAGINAS:
        at = rodar(pagina)
        for df in (d.value for d in at.dataframe):
            textos = {v for c in df.columns if df[c].dtype == object for v in df[c].dropna()}
            assert not (textos & nomes), (pagina, sorted(textos & nomes)[:5])
        for g in at.get("plotly_chart"):
            figuras += 1
            spec = json.loads(g.proto.spec)
            valores = set()
            for t in spec["data"]:
                for campo in ("hovertext", "text", "y", "locations"):
                    valores |= {str(x) for x in (t.get(campo) or []) if isinstance(x, (str, int))}
                for linha in t.get("customdata") or []:
                    valores |= {str(x) for x in (linha if isinstance(linha, list) else [linha])
                                if isinstance(x, (str, int))}
            assert not (valores & (nomes | codigos)), (pagina, sorted(valores & (nomes | codigos))[:5])
    assert figuras >= 3


def test_sem_formula_latex_nos_textos():
    latex = re.compile(r"(?<!\\)\$[^$]+(?<!\\)\$")
    for pagina in PAGINAS:
        at = rodar(pagina)
        ruins = [t[:80] for t in [m.value for m in at.markdown] + [c.value for c in at.caption] if latex.search(t)]
        assert not ruins, (pagina, ruins)
