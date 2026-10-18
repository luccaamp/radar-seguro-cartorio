"""Cenários do STF como diff sobre as premissas (SPEC §3.8). Função pura."""


def aplicar_cenario_stf(premissas: dict, cenarios: dict, nome: str, ajustes_extras: dict | None = None) -> dict:
    """Devolve uma cópia das premissas resolvidas com os ajustes do cenário `nome` (de cenarios_stf.yaml) aplicados.

    `ajustes_extras` (ex.: fração escolhida no simulador para o cenário parcial) vale por cima do cenário.
    """
    if nome not in cenarios["cenarios"]:
        raise ValueError(f"cenário desconhecido: {nome}")
    out = dict(premissas)
    out.update(cenarios["cenarios"][nome].get("ajustes") or {})
    out.update(ajustes_extras or {})
    if not 0 <= out.get("fracao_exigencia_garantia", 1.0) <= 1:
        raise ValueError("fracao_exigencia_garantia precisa estar entre 0 e 1")
    return out
