"""Várias visitas ao mesmo tempo (D-089). No link público, logo depois do Reboot, a página Início mostrou um TypeError:
todas as visitas usavam a mesma conexão do DuckDB (st.cache_resource), e uma consulta lia o resultado da outra. E duas
montagens do banco de demonstração disputavam o mesmo arquivo temporário. Roda em qualquer clone (só o conjunto
público versionado).
"""
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from apoio_painel import RAIZ
from src import publico


def test_montagem_do_banco_de_demonstracao_em_paralelo(tmp_path, monkeypatch):
    """8 visitas abrindo juntas, sem banco montado: todas recebem o mesmo arquivo, sem erro e sem sobra."""
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    with ThreadPoolExecutor(8) as ex:
        caminhos = list(ex.map(lambda _: publico.banco_demonstracao(), range(8)))
    assert len(set(caminhos)) == 1 and caminhos[0].exists()
    assert [p.name for p in tmp_path.iterdir()] == [caminhos[0].name]   # nenhum temporário .novo ficou para trás


def test_consultas_simultaneas_no_painel(painel_demo):
    """8 threads (as visitas) consultando pela conexão do painel ao mesmo tempo: todas recebem a resposta certa."""
    sys.path.insert(0, str(RAIZ / "app"))
    import comum
    esperado = comum.consulta("SELECT count(*) AS n FROM gold.fato_mercado_uf")["n"].iloc[0]
    assert comum.conexao() is not comum.conexao()   # um cursor por chamada, nunca a conexão compartilhada

    def visita(_):
        resultados = []
        for _ in range(40):
            con = comum.conexao()
            n = con.execute("SELECT count(*) FROM gold.fato_mercado_uf").fetchone()[0]
            resultados.append(n)
            resultados.append(comum.consulta("SELECT count(*) AS n FROM gold.fato_mercado_uf")["n"].iloc[0])
        return resultados

    with ThreadPoolExecutor(8) as ex:
        todos = [n for r in ex.map(visita, range(8)) for n in r]
    assert todos == [esperado] * len(todos)


def test_falha_ao_abrir_o_banco_vira_mensagem_e_nao_traceback(monkeypatch, tmp_path):
    """Se o banco não abre, o visitante lê uma mensagem; nenhum traceback (D-089)."""
    from streamlit.testing.v1 import AppTest
    from apoio_painel import apontar_painel, restaurar

    def quebra(*_a, **_k):
        raise RuntimeError("simulado")
    anterior = apontar_painel(tmp_path / "nao_existe.duckdb", publico.PASTA)
    monkeypatch.setattr(publico, "banco_demonstracao", quebra)
    try:
        at = AppTest.from_file(str(RAIZ / "app" / "paginas" / "1_Quão_certo_é.py"), default_timeout=60).run()
    finally:
        restaurar(anterior)
    assert not at.exception
    assert any("sendo preparados" in i.value for i in at.info)


def test_config_esconde_os_detalhes_do_erro():
    import tomllib
    cfg = tomllib.loads(Path(RAIZ / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert cfg["client"]["showErrorDetails"] == "none"


@pytest.fixture(autouse=True)
def _sem_cache_do_streamlit():
    """A conexão de _abrir fica no cache_resource; limpa entre os testes (outro modo, outro arquivo)."""
    yield
    try:
        sys.path.insert(0, str(RAIZ / "app"))
        import comum
        comum._abrir.clear()
    except Exception:   # noqa: BLE001
        pass
