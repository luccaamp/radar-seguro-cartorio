"""Fumaça do painel no MODO COMPLETO: cada página roda sem exceção e mostra fonte e versão.

Os testes rodam sobre uma CÓPIA TEMPORÁRIA do banco gerado pelo pipeline (variável RADAR_BANCO, lida por app/comum.py).
O banco real (data/radar.duckdb) nunca é aberto para escrita aqui; o último teste confere que ele não mudou.
dados_reais (fora da suíte padrão): precisam do banco completo, com silver e interno_*. O modo demonstração, que roda
em qualquer clone, está em test_app_demo.py.
"""
from pathlib import Path

import duckdb
import pytest

from apoio_painel import BANCO_REAL, PAGINAS, RAIZ, assinatura_real as _assinatura

# a cópia temporária do banco (fixture `banco_temporario`, em conftest.py) vale para todos os testes deste módulo
pytestmark = [pytest.mark.dados_reais, pytest.mark.skipif(not BANCO_REAL.exists(), reason="rode uv run pipeline.py antes"),
              pytest.mark.usefixtures("banco_temporario")]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_roda_e_tem_rodape(pagina):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / pagina), default_timeout=120).run()
    assert not at.exception, at.exception
    rodapes = [c.value for c in at.caption if "Fontes:" in c.value]
    assert rodapes and all("Premissas:" in r and "ref." in r for r in rodapes)


def test_app_usa_a_copia(banco_temporario):
    from streamlit.testing.v1 import AppTest
    AppTest.from_file(str(RAIZ / "app/Inicio.py"), default_timeout=120).run()
    import comum  # importado pelo app durante o AppTest
    assert comum.caminho_banco() == banco_temporario["copia"] and comum.modo() == "completo"


def test_simulador_suspende_zera_premio():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / "app/pages/2_Simulador.py"), default_timeout=120).run()
    at.radio[0].set_value("suspende_8_17").run()
    assert not at.exception
    premios = [m.value for m in at.metric if m.label == "Prêmio emitido"]
    assert premios and all(v == "R$ 0" for v in premios)   # zero sem centavos (E8)


def test_simulador_salva_cenario_sem_nova_versao(banco_temporario):
    """Salvar sem mexer em premissa grava o cenário (na cópia) e não cria versão nova."""
    from streamlit.testing.v1 import AppTest
    copia = str(banco_temporario["copia"])
    at = AppTest.from_file(str(RAIZ / "app/pages/2_Simulador.py"), default_timeout=120).run()
    with duckdb.connect(copia) as db:
        antes_v = db.sql("SELECT max(versao) FROM estado.premissas_versoes").fetchone()[0]
        antes_c = db.sql("SELECT coalesce(max(id), 0) FROM estado.cenarios_salvos").fetchone()[0]
    at.text_input[0].set_value("teste automatico").run()
    at.button[0].click().run()
    assert not at.exception
    assert any("salvo" in s.value for s in at.success)
    with duckdb.connect(copia) as db:
        assert db.sql("SELECT max(versao) FROM estado.premissas_versoes").fetchone()[0] == antes_v
        novos = db.sql(f"SELECT nome, versao_premissas FROM estado.cenarios_salvos WHERE id > {antes_c}").fetchall()
        assert novos == [("teste automatico", antes_v)]


def test_mercado_filtro_pequeno_esconde_estimativa(banco_temporario):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / "app/pages/1_Mercado.py"), default_timeout=120).run()
    # um município com 1 ou 2 serventias: as estimativas não podem aparecer (LGPD)
    with duckdb.connect(str(banco_temporario["copia"])) as con:  # mesma configuração da conexão do app
        nome = con.sql("SELECT municipio FROM gold.dim_municipio WHERE n_serventias = 1 ORDER BY municipio LIMIT 1"
                       ).fetchone()[0]
        area = con.execute("""SELECT p.n_serventias FROM gold.mercado_area_publico p JOIN gold.geo_area_municipio a
                              USING (area_id) JOIN gold.dim_municipio d USING (cod_ibge) WHERE d.municipio = ?""",
                           [nome]).fetchone()[0]
    at.selectbox[0].set_value(nome).run()
    assert not at.exception
    # U1: o município pequeno nunca aparece sozinho; os números são os da área agregada a que ele pertence
    assert any("agregado" in i.value and "LGPD" in i.value for i in at.info)
    serv = [m.value for m in at.metric if m.label == "Serventias ativas"]
    assert serv == [str(area)] and area >= 3


# exceções explícitas da regra de 3 serventias (D1): contagens do cadastro público do CNJ e dados do IBGE
EXCECOES_LGPD = {"gold.dim_municipio": "contagens do cadastro público do CNJ (serventias, CLT declarados) e população do IBGE"}


def _municipios_pequenos(con, com_codigos: bool = False) -> set[str]:
    """Nomes (e, se pedido, códigos IBGE em texto) dos municípios de MG com menos serventias ativas que o limiar LGPD,
    inclusive os sem serventia."""
    limiar = con.sql("SELECT max(limiar_lgpd) FROM gold.execucao").fetchone()[0]
    linhas = con.execute("""
        SELECT m.nome, m.cod_ibge FROM silver.municipio_ibge m LEFT JOIN
          (SELECT cod_ibge, count(*) n FROM silver.serventia WHERE status = 'Ativo' GROUP BY 1) s USING (cod_ibge)
        WHERE coalesce(s.n, 0) < ?""", [limiar]).fetchall()
    return {n for n, _ in linhas} | ({str(c) for _, c in linhas} if com_codigos else set())


def _valores_das_figuras(spec: dict) -> set[str]:
    """Todo texto que uma figura Plotly mostra ou carrega: hovertext, text, y, locations e customdata (achatado)."""
    out = set()
    for trace in spec["data"]:
        for campo in ("hovertext", "text", "y", "locations"):
            out |= {str(x) for x in (trace.get(campo) or []) if isinstance(x, (str, int))}
        for linha in trace.get("customdata") or []:
            out |= {str(x) for x in (linha if isinstance(linha, list) else [linha]) if isinstance(x, (str, int))}
    return out


def test_lgpd_tabelas_publicas_do_gold_e_da_qualidade(banco_temporario):
    """D1: nenhuma tabela pública (gold e qualidade, fora as 'interno_*' e as exceções) tem nome de município com
    menos de 3 serventias."""
    with duckdb.connect(str(banco_temporario["copia"])) as con:
        pequenos = _municipios_pequenos(con)
        cols = con.execute("""SELECT table_schema || '.' || table_name, column_name FROM information_schema.columns
                              WHERE table_schema IN ('gold', 'qualidade') AND data_type = 'VARCHAR'
                                AND table_name NOT LIKE 'interno_%'""").fetchall()
        achados = {}
        for tabela, coluna in cols:
            if tabela in EXCECOES_LGPD:
                continue
            valores = {r[0] for r in con.execute(f'SELECT DISTINCT "{coluna}" FROM {tabela}').fetchall()}
            if valores & pequenos:
                achados[f"{tabela}.{coluna}"] = len(valores & pequenos)
    assert len(pequenos) > 400 and not achados, achados


def test_lgpd_tabelas_e_graficos_do_painel(banco_temporario):
    """D1: nenhuma tabela nem texto de gráfico do painel mostra nome de município com menos de 3 serventias
    (o mapa do Mercado agrega esses municípios pela região imediata)."""
    import json
    from streamlit.testing.v1 import AppTest
    with duckdb.connect(str(banco_temporario["copia"])) as con:
        pequenos = _municipios_pequenos(con)
        pequenos_e_codigos = _municipios_pequenos(con, com_codigos=True)
    figuras_vistas = 0
    for pagina in PAGINAS:
        at = AppTest.from_file(str(RAIZ / pagina), default_timeout=120).run()
        for df in (d.value for d in at.dataframe):
            textos = {v for c in df.columns if df[c].dtype == object for v in df[c].dropna()}
            assert not (textos & pequenos), (pagina, sorted(textos & pequenos)[:5])
        for g in at.get("plotly_chart"):
            figuras_vistas += 1
            valores = _valores_das_figuras(json.loads(g.proto.spec))
            assert not (valores & pequenos_e_codigos), (pagina, sorted(valores & pequenos_e_codigos)[:5])
    assert figuras_vistas >= 3   # mapa e ranking do Mercado, gráfico da Qualidade


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


def test_banco_real_intacto(banco_temporario):
    """Roda por último no módulo: data de modificação e tamanho do banco real iguais aos do início."""
    assert _assinatura(BANCO_REAL) == banco_temporario["real_antes"]
