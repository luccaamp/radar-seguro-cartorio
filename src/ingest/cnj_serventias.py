"""Coleta a listagem de serventias de uma UF no Justiça Aberta (POST /serventias, página única).

A paginação da API é instável (perdeu 374 CNS de MG na Fase 0): por isso pede tudo numa página e confere
a integridade (meta.total = registros = CNS distintos). Idempotente: não coleta de novo se o arquivo do dia existe.
Saída: data/bronze/cnj_justica_aberta/<data>/serventias_<UF>.json (+ .meta.json)

Uso: uv run python -m src.ingest.cnj_serventias MG
"""
import sys
import time

from src.ingest.comum import BRONZE, cliente, gravar_meta, hoje, sha256_bytes

URL = "https://justicaabertaapi.cnj.jus.br/v1/api/serventias"
HEADERS = {"Origin": "https://justicaaberta.cnj.jus.br", "Referer": "https://justicaaberta.cnj.jus.br/"}
POR_PAGINA = 10000


def coletar(uf: str) -> None:
    destino = BRONZE / "cnj_justica_aberta" / hoje() / f"serventias_{uf}.json"
    if destino.exists():
        print(f"{destino.name}: já existe, mantido")
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    corpo = {"cidade_id": 0, "uf": uf, "cns": None}
    params = {"assignments": "", "page": 1, "perPage": POR_PAGINA, "search": ""}
    with cliente(timeout=300, **HEADERS) as c:
        for _ in range(3):
            r = c.post(URL, params=params, json=corpo)
            if r.status_code == 200:
                break
            time.sleep(10)
    r.raise_for_status()
    d = r.json()
    itens = d["data"]
    ok = d["meta"]["total"] == len(itens) == len({i["cns"] for i in itens})
    if not ok:
        raise RuntimeError(f"{uf}: integridade falhou (meta.total={d['meta']['total']}, registros={len(itens)})")
    destino.write_bytes(r.content)
    gravar_meta(destino, url=URL, metodo="POST", params=params, corpo=corpo, registros=len(itens),
                meta_total=d["meta"]["total"], sha256=sha256_bytes(r.content))
    print(f"{uf}: {len(itens)} registros, integridade ok")


if __name__ == "__main__":
    coletar(sys.argv[1] if len(sys.argv) > 1 else "MG")
