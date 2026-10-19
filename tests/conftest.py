"""Fixtures dos testes. As premissas vêm da semente versionada; os dados de serventias e vínculos são SINTÉTICOS."""
from pathlib import Path

import pytest
import yaml

from src.model.premissas import resolver

CONFIG = Path(__file__).resolve().parents[1] / "config"
PESO_INDETERMINADA_TESTE = 0.656  # valor fixo para teste (no pipeline é calculado a cada carga)


@pytest.fixture(scope="session")
def banco_temporario(tmp_path_factory):
    """Cópia do banco real, com o gold refeito pelo código atual, para os testes do painel e da auditoria (uma vez por
    sessão). Confere no fim que o banco real e os Parquet de data/ não mudaram."""
    from apoio_painel import BANCO_REAL, apontar_painel, assinatura_real, preparar_copia, restaurar
    if not BANCO_REAL.exists():
        pytest.skip("rode uv run pipeline.py antes")
    antes = assinatura_real()
    copia = preparar_copia(tmp_path_factory.mktemp("banco"))
    anterior = apontar_painel(copia)
    yield {"copia": copia, "real_antes": antes}
    restaurar(anterior)
    assert assinatura_real() == antes, "o banco real ou os Parquet de data/ mudaram durante os testes"


@pytest.fixture(scope="session")
def semente() -> dict:
    from src.estado import ler_semente   # a mesma semente que o pipeline usa (hoje premissas_v002.yaml)
    return ler_semente()


@pytest.fixture(scope="session")
def regras() -> dict:
    return yaml.safe_load((CONFIG / "regras_classificacao.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def cenarios() -> dict:
    return yaml.safe_load((CONFIG / "cenarios_stf.yaml").read_text(encoding="utf-8"))


def _nivel(semente, nivel):
    return resolver(semente, nivel, {"peso_classe_indeterminada_base": {"min": 0.0, "base": PESO_INDETERMINADA_TESTE,
                                                                        "max": 1.0}[nivel]})


@pytest.fixture(scope="session")
def p_base(semente):
    return _nivel(semente, "base")


@pytest.fixture(scope="session")
def p_min(semente):
    return _nivel(semente, "min")


@pytest.fixture(scope="session")
def p_max(semente):
    return _nivel(semente, "max")
