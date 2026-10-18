"""Fixtures dos testes. As premissas vêm da semente versionada; os dados de serventias e vínculos são SINTÉTICOS."""
from pathlib import Path

import pytest
import yaml

from src.model.premissas import resolver

CONFIG = Path(__file__).resolve().parents[1] / "config"
PESO_INDETERMINADA_TESTE = 0.656  # valor fixo para teste (no pipeline é calculado a cada carga)


@pytest.fixture(scope="session")
def semente() -> dict:
    return yaml.safe_load((CONFIG / "premissas" / "premissas_v001.yaml").read_text(encoding="utf-8"))


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
