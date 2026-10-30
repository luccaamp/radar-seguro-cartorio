"""Mineração de dados de MG (docs/plano_mineracao.md): leitura das tabelas, estatística descritiva e gráficos.

Funções reutilizáveis pelos notebooks; nada aqui grava em bronze, silver ou gold. Os parâmetros ficam em
config/analise.yaml.
"""
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]


def config() -> dict:
    return yaml.safe_load((RAIZ / "config" / "analise.yaml").read_text(encoding="utf-8"))
