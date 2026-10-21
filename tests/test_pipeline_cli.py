"""Linha de comando do pipeline: --help e argumento errado não tocam no banco (erro achado no clone limpo, 2026-10-19)."""
import hashlib
import os

import duckdb
import pytest

import pipeline

so_windows = pytest.mark.skipif(os.name != "nt", reason="a trava de arquivo aberto é do Windows")


@so_windows
def test_em_uso_detecta_banco_aberto_so_para_leitura(tmp_path):
    banco = tmp_path / "radar.duckdb"
    duckdb.connect(str(banco)).close()
    assert not pipeline.em_uso(banco) and not pipeline.em_uso(tmp_path / "nao_existe.duckdb")
    with duckdb.connect(str(banco), read_only=True):   # como o painel (D-034)
        assert pipeline.em_uso(banco)
    assert not pipeline.em_uso(banco)


@so_windows
def test_carga_com_o_banco_aberto_para_antes_de_comecar(tmp_path):
    """D-034: com o painel aberto, a carga para no início, sem banco temporário e sem regravar Parquet."""
    banco = tmp_path / "radar.duckdb"
    with duckdb.connect(str(banco)) as con:
        con.execute("CREATE TABLE t AS SELECT 1 AS x")
    antes = hashlib.sha256(banco.read_bytes()).hexdigest()
    with duckdb.connect(str(banco), read_only=True):
        with pytest.raises(SystemExit) as e:
            pipeline.main("gold", banco=banco, exportar_parquet=False)
    assert "aberto por outro programa" in str(e.value) and "Nada foi alterado" in str(e.value)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["radar.duckdb"]
    assert hashlib.sha256(banco.read_bytes()).hexdigest() == antes


def test_help_so_mostra_a_ajuda(capsys):
    with pytest.raises(SystemExit) as e:
        pipeline.argumentos(["--help"])
    assert e.value.code == 0 and "--a-partir-de" in capsys.readouterr().out


@pytest.mark.parametrize("args", [["--xyz"], ["coleta"], ["--a-partir-de", "ouro"], ["gold", "--a-partir-de", "silver"]])
def test_argumento_errado_e_erro(args):
    with pytest.raises(SystemExit) as e:
        pipeline.argumentos(args)
    assert e.value.code == 2


def test_a_partir_de():
    assert pipeline.argumentos([]) == "all"
    assert pipeline.argumentos(["--a-partir-de", "bronze"]) == "all"
    assert pipeline.argumentos(["--a-partir-de", "silver"]) == "gold_de_parquet"
    assert pipeline.argumentos(["gold"]) == "gold"


def test_etapa_desconhecida_nao_cria_banco(tmp_path):
    banco = tmp_path / "radar.duckdb"
    with pytest.raises(SystemExit):
        pipeline.main("--help", banco=banco)
    assert not banco.exists() and not list(tmp_path.iterdir())


def test_a_partir_de_silver_sem_parquet_explica(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "SILVER", tmp_path / "vazio")
    with pytest.raises(SystemExit) as e:
        pipeline._silver_de_parquet(None, tmp_path / "vazio")
    assert "baixar_dados.py" in str(e.value)
