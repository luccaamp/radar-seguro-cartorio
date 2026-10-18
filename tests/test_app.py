"""Fumaça do painel: cada página roda sem exceção sobre o banco gerado pelo pipeline e mostra fonte e versão.

Usa dados REAIS do banco local; é pulado se o pipeline ainda não rodou.
"""
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (RAIZ / "data" / "radar.duckdb").exists(), reason="rode uv run pipeline.py antes")
PAGINAS = ["app/Inicio.py", "app/pages/1_Mercado.py", "app/pages/2_Simulador.py", "app/pages/3_Qualidade_dos_dados.py"]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_roda_e_tem_rodape(pagina):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / pagina), default_timeout=120).run()
    assert not at.exception, at.exception
    rodapes = [c.value for c in at.caption if "Fontes:" in c.value]
    assert rodapes and all("Premissas:" in r and "ref." in r for r in rodapes)


def test_simulador_suspende_zera_premio():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / "app/pages/2_Simulador.py"), default_timeout=120).run()
    at.radio[0].set_value("suspende_8_17").run()
    assert not at.exception
    premios = [m.value for m in at.metric if m.label == "Prêmio emitido"]
    assert premios and all(v == "R$ 0,00" for v in premios)


def test_simulador_salva_cenario_sem_nova_versao():
    """Salvar sem mexer em premissa grava o cenário e não cria versão nova. O teste apaga o que gravou."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / "app/pages/2_Simulador.py"), default_timeout=120).run()
    con = at.session_state  # noqa: F841  (garante que a página rodou)
    import duckdb
    with duckdb.connect(str(RAIZ / "data" / "radar.duckdb")) as db:
        antes_v = db.sql("SELECT max(versao) FROM estado.premissas_versoes").fetchone()[0]
        antes_c = db.sql("SELECT coalesce(max(id), 0) FROM estado.cenarios_salvos").fetchone()[0]
    at.text_input[0].set_value("teste automatico").run()
    at.button[0].click().run()
    assert not at.exception
    assert any("salvo" in s.value for s in at.success)
    with duckdb.connect(str(RAIZ / "data" / "radar.duckdb")) as db:
        assert db.sql("SELECT max(versao) FROM estado.premissas_versoes").fetchone()[0] == antes_v
        novos = db.sql(f"SELECT nome, versao_premissas FROM estado.cenarios_salvos WHERE id > {antes_c}").fetchall()
        assert novos == [("teste automatico", antes_v)]
        db.execute(f"DELETE FROM estado.cenarios_salvos WHERE id > {antes_c}")


def test_mercado_filtro_pequeno_esconde_estimativa():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / "app/pages/1_Mercado.py"), default_timeout=120).run()
    # um município com 1 ou 2 serventias: as estimativas não podem aparecer (LGPD)
    import duckdb
    with duckdb.connect(str(RAIZ / "data" / "radar.duckdb")) as con:  # mesma configuração da conexão do app
        nome = con.sql("SELECT municipio FROM gold.dim_municipio WHERE n_serventias = 1 ORDER BY municipio LIMIT 1"
                       ).fetchone()[0]
    at.selectbox[0].set_value(nome).run()
    assert not at.exception
    assert not [m for m in at.metric if m.label in ("Passivo estimado", "Déficit estimado")]
    assert any("LGPD" in w.value for w in at.warning)
