"""Coleta a listagem de serventias de uma UF no Justiça Aberta (POST /serventias, página única).

A paginação da API é instável (perdeu 374 CNS de MG na Fase 0): por isso pede tudo numa página e confere
a integridade (meta.total = registros = CNS distintos). Idempotente: não coleta de novo se o arquivo do dia existe.
Saída: data/bronze/cnj_justica_aberta/<data>/serventias_<UF>.json (+ .meta.json)

Uso: uv run python -m src.ingest.cnj_serventias MG
"""
import sys

from src import estados_config
from src.ingest.comum import BRONZE, cliente, gravar_meta, hoje, pedir, sha256_bytes

URL = "https://justicaabertaapi.cnj.jus.br/v1/api/serventias"
HEADERS = {"Origin": "https://justicaaberta.cnj.jus.br", "Referer": "https://justicaaberta.cnj.jus.br/"}
POR_PAGINA = 10000


def coletar(uf: str, pasta=None, tolerancia: int = 0) -> None:
    """`pasta`: onde gravar (padrão data/bronze/cnj_justica_aberta/<data>; o pipeline do Brasil passa a dele).
    `tolerancia`: quantos registros a API pode entregar a menos que o meta.total dela, sem CNS repetido (SP: a API
    informa 1.680 e entrega 1.679 desde a Fase 0; conferido de novo em 2026-11-11). A diferença fica no .meta.json."""
    destino = (pasta or BRONZE / "cnj_justica_aberta" / hoje()) / f"serventias_{uf}.json"
    if destino.exists():
        print(f"{destino.name}: já existe, mantido")
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    corpo = {"cidade_id": 0, "uf": uf, "cns": None}
    params = {"assignments": "", "page": 1, "perPage": POR_PAGINA, "search": ""}
    with cliente(timeout=300, conectar=30, **HEADERS) as c:
        r = pedir(c, "POST", URL, params=params, json=corpo)   # 3 tentativas, também para erro de rede
    r.raise_for_status()
    d = r.json()
    itens = d["data"]
    faltando = integridade(d["meta"]["total"], [i["cns"] for i in itens], tolerancia)
    if faltando is None:
        raise RuntimeError(f"{uf}: integridade falhou (meta.total={d['meta']['total']}, registros={len(itens)})")
    destino.write_bytes(r.content)
    gravar_meta(destino, url=URL, metodo="POST", params=params, corpo=corpo, registros=len(itens),
                meta_total=d["meta"]["total"], faltando_na_api=faltando, sha256=sha256_bytes(r.content))
    print(f"{uf}: {len(itens)} registros, integridade ok" + (f" ({faltando} a menos que o meta.total)" if faltando else ""))


def integridade(meta_total: int, cns: list[str], tolerancia: int = 0) -> int | None:
    """Quantos registros faltam em relação ao meta.total da API, se a coleta é aceitável; None se não é (CNS repetido,
    registros a mais ou faltando mais que a `tolerancia`)."""
    faltando = meta_total - len(cns)
    if len(set(cns)) != len(cns) or not 0 <= faltando <= tolerancia:
        return None
    return faltando


if __name__ == "__main__":
    coletar(sys.argv[1] if len(sys.argv) > 1 else estados_config.uf_padrao())
