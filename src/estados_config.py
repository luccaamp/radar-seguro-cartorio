"""Configuração por estado (Fase 3, D-081): lê config/estados.yaml e a lista de UFs de config/escopo.yaml.

Tudo o que só vale para uma UF (código IBGE, pacote da RAIS, apelidos de municípios, totais de controle) vem daqui,
em vez de ficar fixo no código. Um estado novo é uma entrada a mais no YAML.
"""
from functools import cache
from pathlib import Path

import yaml

CONFIG = Path(__file__).resolve().parents[1] / "config"


@cache
def _ler(nome: str) -> dict:
    return yaml.safe_load((CONFIG / nome).read_text(encoding="utf-8")) or {}


def ufs() -> list[str]:
    """UFs que o pipeline processa (config/escopo.yaml, `ufs`)."""
    return list(_ler("escopo.yaml")["ufs"])


def uf_padrao() -> str:
    """A primeira UF do escopo: o padrão dos coletores e do painel quando nenhuma UF é dada."""
    return ufs()[0]


def estado(uf: str) -> dict:
    """Entrada da UF em config/estados.yaml. Erro claro se a UF não estiver configurada."""
    todos = _ler("estados.yaml")
    if uf not in todos:
        raise KeyError(f"UF {uf!r} sem entrada em config/estados.yaml (configuradas: {', '.join(sorted(todos))})")
    return todos[uf]


def cod_ibge(uf: str) -> int:
    return int(estado(uf)["cod_ibge"])


def pacote_rais(uf: str) -> str:
    return estado(uf)["pacote_rais"]


def apelidos_municipios(uf: str) -> dict[str, int]:
    return dict(estado(uf).get("apelidos_municipios") or {})


def controle_arrecadacao(uf: str) -> dict | None:
    """Totais de controle da arrecadação da UF (F2, D-024), ou None se a UF ainda não tem."""
    return estado(uf).get("controle_arrecadacao")
