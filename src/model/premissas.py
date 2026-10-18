"""Validação das premissas e resolução de um nível (min / base / max) em valores escalares. Sem I/O."""
from typing import Any

NIVEIS = ("min", "base", "max")
TOLERANCIA_SOMA = 1e-9


class PremissaInvalida(ValueError):
    pass


def validar_escolha_garantia(escolha: dict[str, float]) -> None:
    """As três parcelas (bens próprios, fiança, seguro) precisam somar 1 (SPEC §3.6)."""
    chaves = {"bens_proprios", "fianca", "seguro"}
    if set(escolha) != chaves:
        raise PremissaInvalida(f"escolha_garantia precisa ter exatamente {sorted(chaves)}")
    if any(v < 0 for v in escolha.values()):
        raise PremissaInvalida("escolha_garantia não aceita parcela negativa")
    if abs(sum(escolha.values()) - 1) > TOLERANCIA_SOMA:
        raise PremissaInvalida(f"escolha_garantia soma {sum(escolha.values()):.6f}, deveria somar 1")


def validar(semente: dict) -> None:
    """Confere a estrutura da semente: toda premissa tem fonte e valor(es); escolha_garantia soma 1 em cada nível."""
    if "versao" not in semente or "premissas" not in semente:
        raise PremissaInvalida("semente sem 'versao' ou 'premissas'")
    for nome, p in semente["premissas"].items():
        if "fonte" not in p:
            raise PremissaInvalida(f"{nome}: sem fonte")
        if not ({"valor", "valores", "indice"} & set(p)):
            raise PremissaInvalida(f"{nome}: sem valor nem valores")
    for nivel in NIVEIS:
        validar_escolha_garantia(semente["premissas"]["escolha_garantia"]["valores"][nivel])


def _no_nivel(valores: Any, nivel: str) -> Any:
    """Se `valores` é {min, base, max}, devolve o do nível; se é dicionário de faixas, resolve cada faixa."""
    if isinstance(valores, dict) and set(valores) == set(NIVEIS):
        return valores[nivel]
    if isinstance(valores, dict):
        return {k: _no_nivel(v, nivel) for k, v in valores.items()}
    return valores


def resolver(semente: dict, nivel: str = "base", ajustes: dict | None = None) -> dict[str, Any]:
    """Valores escalares de todas as premissas num nível, com ajustes (cenário do STF ou simulador) por cima."""
    if nivel not in NIVEIS:
        raise PremissaInvalida(f"nível desconhecido: {nivel}")
    out = {}
    for nome, p in semente["premissas"].items():
        out[nome] = p["valor"] if "valor" in p else _no_nivel(p.get("valores"), nivel)
    out.setdefault("fracao_exigencia_garantia", 1.0)
    out.update(ajustes or {})
    validar_escolha_garantia(out["escolha_garantia"])
    return out
