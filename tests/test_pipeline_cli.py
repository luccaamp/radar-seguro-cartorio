"""Linha de comando do pipeline: --help e argumento errado não tocam no banco (erro achado no clone limpo, 2026-10-19)."""
import pytest

import pipeline


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
