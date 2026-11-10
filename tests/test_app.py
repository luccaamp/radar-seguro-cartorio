"""Fumaça do painel no MODO COMPLETO: cada página roda sem exceção e mostra fonte e versão.

Os testes rodam sobre uma CÓPIA TEMPORÁRIA do banco gerado pelo pipeline (variável RADAR_BANCO, lida por app/comum.py).
O banco real (data/radar.duckdb) nunca é aberto para escrita aqui; o último teste confere que ele não mudou.
O painel abre o banco só para leitura (D-034); os cenários salvos vão para um arquivo temporário (RADAR_ESTADO).
dados_reais (fora da suíte padrão): precisam do banco completo, com silver e interno_*. O modo demonstração, que roda
em qualquer clone, está em test_app_demo.py.
"""
import hashlib
import os
import re
import shutil
import stat
from pathlib import Path

import duckdb
import pytest

from apoio_painel import BANCO_REAL, HISTORIA, MERCADO, PAGINAS, RAIZ, SIMULADOR, SOBRE, assinatura_real as _assinatura

# a cópia temporária do banco (fixture `banco_temporario`, em conftest.py) vale para todos os testes deste módulo
pytestmark = [pytest.mark.dados_reais, pytest.mark.skipif(not BANCO_REAL.exists(), reason="rode uv run pipeline.py antes"),
              pytest.mark.usefixtures("banco_temporario")]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_roda_e_tem_rodape(pagina):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / pagina), default_timeout=120).run()
    assert not at.exception, at.exception
    if pagina in HISTORIA and pagina != SOBRE:   # D-051: só a linha de fonte (fonte e data)
        import json   # o JSON do gráfico escapa os acentos: lê as anotações já decodificadas
        textos = "\n".join(m.value for m in at.markdown) + "".join(
            a["text"] for g in at.get("plotly_chart") for a in json.loads(g.proto.spec)["layout"].get("annotations", []))
        assert "Fonte: CNJ, Justiça Aberta (" in textos
        return
    rodapes = [c.value for c in at.caption if "Fontes:" in c.value]
    assert rodapes and all("Premissas:" in r and "ref." in r for r in rodapes)


def test_app_usa_a_copia(banco_temporario):
    from streamlit.testing.v1 import AppTest
    AppTest.from_file(str(RAIZ / "app/Inicio.py"), default_timeout=120).run()
    import comum  # importado pelo app durante o AppTest
    assert comum.caminho_banco() == banco_temporario["copia"] and comum.modo() == "completo"


def test_simulador_suspende_zera_premio():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / SIMULADOR), default_timeout=120).run()
    at.radio(key="x_cenario").set_value("suspende_8_17").run()
    assert not at.exception
    premios = [m.value for m in at.metric if m.label == "Prêmio emitido"]
    assert premios and all(v == "R$ 0" for v in premios)   # zero sem centavos (E8)


@pytest.mark.parametrize("limite", ["limite fixo", "limite corrigido pelo IPCA"])
def test_explorar_2027_no_padrao_repete_a_projecao(banco_temporario, limite):
    """Fase 1, item 1: no ano projetado, com as suposições no padrão, o prêmio do Explorar é o central da
    gold.analise_previsao (até 0,1%: o Explorar refaz o prêmio com a mediana de cada total, e a tabela grava a
    mediana do prêmio). Pula numa carga anterior aos totais por faixa de déficit."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / SIMULADOR), default_timeout=120).run()
    if "2027 (projeção)" not in at.radio(key="x_ano").options:   # o AppTest devolve as opções já formatadas
        pytest.skip("carga sem os totais da projeção (gold.analise_previsao antiga)")
    at.radio(key="x_ano").set_value(2027).run()
    at.radio(key="x_limite").set_value(limite).run()
    assert not at.exception, at.exception
    with duckdb.connect(str(banco_temporario["copia"]), read_only=True) as con:
        central = con.execute("SELECT central FROM gold.analise_previsao WHERE bloco = 'mercado' AND periodo = '2027' "
                              "AND cenario_limite = ? AND medida = 'mercado_premio_emitido' AND variante = "
                              "'tendência do T2 (principal)'", [limite]).fetchone()[0]
    import comum
    premio = [m.value for m in at.metric if m.label == "Prêmio emitido"][0]
    assert premio == comum.brl(central) or abs(_valor_brl(premio) / central - 1) < 1e-3, (premio, central)


def _valor_brl(texto: str) -> float:
    """'R$ 349,1 mil' → 349100.0 (só para comparar com tolerância)."""
    n, *u = texto.replace("R$", "").strip().split()
    mult = {"mil": 1e3, "mi": 1e6, "bi": 1e9}.get(u[0] if u else "", 1)
    return float(n.replace(".", "").replace(",", ".")) * mult


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _salvar_pelo_simulador(nome: str):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / SIMULADOR), default_timeout=120).run()
    at.text_input[0].set_value(nome).run()
    next(b for b in at.button if b.label == "Salvar").click().run()   # os atalhos do Explorar vêm antes (D-077)
    assert not at.exception and any("salvo" in s.value for s in at.success)


def _nomes_na_tabela_de_salvos() -> list[str]:
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / SIMULADOR), default_timeout=120).run()
    assert not at.exception
    return [n for df in (d.value for d in at.dataframe) if "nome" in df.columns for n in df["nome"]]


def test_simulador_salva_cenario_sem_nova_versao(banco_temporario):
    """Salvar sem mexer em premissa grava o cenário e não cria versão nova. Teste da Fase 1 mantido; desde a D-034 o
    cenário fica no arquivo RADAR_ESTADO (antes, em estado.cenarios_salvos do banco)."""
    from src import cenarios
    copia = str(banco_temporario["copia"])
    with duckdb.connect(copia, read_only=True) as db:
        antes_v = db.sql("SELECT max(versao) FROM estado.premissas_versoes").fetchone()[0]
    antes_c = max((c["id"] for c in cenarios.ler()[0]), default=0)
    _salvar_pelo_simulador("teste automatico")
    with duckdb.connect(copia, read_only=True) as db:
        assert db.sql("SELECT max(versao) FROM estado.premissas_versoes").fetchone()[0] == antes_v
    novos = [(c["nome"], c["versao_premissas"]) for c in cenarios.ler()[0] if c["id"] > antes_c]
    assert novos == [("teste automatico", antes_v)]


def test_abrir_o_painel_e_salvar_cenario_nao_altera_o_banco(banco_temporario):
    """D-034: abrir todas as páginas e salvar um cenário deixam o SHA-256 do banco igual. O cenário vai para o arquivo
    RADAR_ESTADO (ao lado da cópia, nunca em data/), sobre a versão de premissas vigente no banco, que não muda."""
    from streamlit.testing.v1 import AppTest
    from src import cenarios
    copia = banco_temporario["copia"]
    antes = _sha256(copia)
    for pagina in PAGINAS:
        assert not AppTest.from_file(str(RAIZ / pagina), default_timeout=120).run().exception
    _salvar_pelo_simulador("teste do sha256")
    with duckdb.connect(str(copia), read_only=True) as db:
        vigente = db.sql("SELECT max(versao) FROM estado.premissas_versoes").fetchone()[0]
    salvos, aviso = cenarios.ler()
    assert aviso is None and cenarios.caminho().parent == copia.parent
    assert [(c["nome"], c["versao_premissas"], c["premissas_alteradas"]) for c in salvos][-1] == \
        ("teste do sha256", vigente, {})
    assert _sha256(copia) == antes


def test_cenario_salvo_continua_depois_de_reiniciar_o_painel(banco_temporario):
    """Reiniciar = caches do Streamlit vazios e conexão nova: a tabela de salvos lê o arquivo de novo."""
    from apoio_painel import _limpar_caches
    _salvar_pelo_simulador("antes de reiniciar")
    _limpar_caches()
    assert "antes de reiniciar" in _nomes_na_tabela_de_salvos()


def test_painel_com_banco_marcado_somente_leitura(banco_temporario, tmp_path):
    """Com o atributo 'somente leitura' do Windows no arquivo do banco, todas as páginas abrem e salvar funciona."""
    from streamlit.testing.v1 import AppTest
    from apoio_painel import apontar_painel, restaurar
    ro = tmp_path / "radar.duckdb"
    shutil.copy2(banco_temporario["copia"], ro)
    os.chmod(ro, stat.S_IREAD)   # no Windows, liga o atributo "somente leitura"
    anterior = apontar_painel(ro)
    try:
        for pagina in PAGINAS:
            at = AppTest.from_file(str(RAIZ / pagina), default_timeout=120).run()
            assert not at.exception, (pagina, at.exception)
        _salvar_pelo_simulador("banco somente leitura")
        assert (tmp_path / "painel_estado.json").exists()
    finally:
        restaurar(anterior)
        os.chmod(ro, stat.S_IREAD | stat.S_IWRITE)


def test_mercado_municipio_pequeno_aparece_sozinho(banco_temporario):
    """D-078 (D-038, fase 2): um município com 1 serventia tem área própria no mapa, os números dele e a posição no
    ranking, sem aviso de agregação."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / MERCADO), default_timeout=120).run()
    with duckdb.connect(str(banco_temporario["copia"]), read_only=True) as con:  # mesma configuração da conexão do app
        nome, cod = con.sql("SELECT municipio, cod_ibge FROM gold.dim_municipio WHERE n_serventias = 1 "
                            "ORDER BY municipio LIMIT 1").fetchone()
        pos, total = con.execute("SELECT posicao, n_municipios FROM gold.ranking_municipio_publico "
                                 "WHERE metrica = 'valor_descoberto' AND cod_ibge = ?", [cod]).fetchone()
        com_serv = con.sql("SELECT count(*) FROM gold.dim_municipio WHERE n_serventias > 0").fetchone()[0]
    at.selectbox[0].set_value(nome).run()
    assert not at.exception
    assert not any("agregad" in i.value for i in at.info)
    tela = "\n".join(m.value for m in at.markdown).replace("&#36;", "$")
    assert f"Déficit em {nome}" in tela
    assert re.findall(r'Cartórios no município</div><div class="rd-num">([^<]+)<', tela) == ["1"]
    assert f"{pos}º de {total:,}".replace(",", ".") + " municípios no déficit" in tela
    assert f"<td>{nome}</td>" in tela   # a linha dele no ranking, abaixo dos 10 primeiros
    from apoio_painel import mapa_componente
    locais = [a["id"] for a in mapa_componente(at)["areas"]]
    assert len(locais) == total == com_serv and str(cod) in locais


def test_tabelas_por_municipio_tem_todos_os_municipios(banco_temporario):
    """D-078 (D-038, fase 2): o mapa, o ranking, a tabela de mercado por município, o passivo por município e a
    reconciliação pública trazem todos os municípios com serventia, sem linha agregada."""
    with duckdb.connect(str(banco_temporario["copia"]), read_only=True) as con:
        q = lambda s: con.sql(s).fetchone()[0]  # noqa: E731
        com_serv = q("SELECT count(*) FROM gold.dim_municipio WHERE n_serventias > 0")
        assert com_serv > 800 and q("SELECT count(*) FROM gold.dim_municipio WHERE n_serventias BETWEEN 1 AND 2") > 400
        assert q("SELECT count(*) FROM gold.geo_mapa_publico") == com_serv
        assert q("SELECT count(*) FROM gold.mercado_area_publico WHERE tipo = 'municipio'") == com_serv
        assert q("SELECT count(DISTINCT cod_ibge) FROM gold.ranking_municipio_publico") == com_serv
        assert q("SELECT count(*) FROM gold.fato_mercado_municipio_publico WHERE cod_ibge IS NOT NULL") == com_serv
        assert q("SELECT count(*) FROM gold.fato_mercado_municipio_publico") == com_serv
        assert q("SELECT count(DISTINCT cod_ibge) FROM gold.fato_passivo_municipio") == com_serv
        assert q("SELECT count(*) FROM qualidade.rec_municipio") == q("SELECT count(*) FROM silver.municipio_ibge")
        # as somas por município fecham o total de MG (nível e regra base, STF mantém)
        assert q("SELECT sum(valor_descoberto) FROM gold.mercado_area_publico") == pytest.approx(
            q("SELECT valor_descoberto FROM gold.fato_mercado_uf WHERE nivel = 'base' AND regra_classe = 'v2' "
              "AND cenario_stf = 'mantem'"), rel=1e-9)


def test_sem_formula_latex_nos_textos(banco_temporario):
    """1.1: nenhum texto renderizado tem dois '$' sem escape (o Streamlit os leria como fórmula LaTeX)."""
    import re
    from streamlit.testing.v1 import AppTest
    latex = re.compile(r"(?<!\\)\$[^$]+(?<!\\)\$")
    for pagina in PAGINAS:
        at = AppTest.from_file(str(RAIZ / pagina), default_timeout=120).run()
        textos = [m.value for m in at.markdown] + [c.value for c in at.caption]
        ruins = [t[:80] for t in textos if latex.search(t)]
        assert not ruins, (pagina, ruins)


def test_etapa_3_no_banco_completo(banco_temporario):
    """As conferências da Etapa 3 de tests/test_painel.py, agora no modo completo (cópia do banco real): 10 números
    = ESTADO_ATUAL, D-042 = analise_monte_carlo e fato_mercado_uf (na ordem base > faixa > extremos), sensibilidades
    = analise_sensibilidade_metodo, 05b do notebook, projeção rotulada, ADI com data e formato das ferramentas."""
    import comum
    import test_painel as tp
    assert comum.modo() == "completo"
    banco = {"banco": banco_temporario["copia"]}
    tp.test_funcoes_no_formato_das_ferramentas_do_chat(banco)
    tp.test_inicio_mostra_os_10_numeros_do_estado_atual(banco)
    for medida in ("deficit", "importancia_segurada", "premio"):
        tp.test_d042_bate_com_as_tabelas_e_segue_a_ordem(banco, medida)
    tp.test_sensibilidades_da_d042_batem_com_a_tabela(banco)
    tp.test_05b_vem_do_notebook_e_aparece_como_faixa_de_comparacao(banco)
    tp.test_analises_rotula_projecao_e_a_leitura_do_limite(banco)
    tp.test_adi_8015_com_data_da_conferencia()


def test_banco_real_intacto(banco_temporario):
    """Roda por último no módulo: data de modificação e tamanho do banco real iguais aos do início."""
    assert _assinatura(BANCO_REAL) == banco_temporario["real_antes"]
