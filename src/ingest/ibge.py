"""Coleta do IBGE: municípios de uma UF, população estimada, malha municipal (GeoJSON) e índices de preço (IPCA, INPC).

Idempotente: se o arquivo do dia já existe, não baixa de novo.
Saída: data/bronze/ibge/<data>/{municipios_<UF>.json, populacao_<UF>.json, malha_<UF>.geojson, ipca.json, inpc.json}

Uso: uv run python -m src.ingest.ibge MG
"""
import sys
import time

from src.ingest.comum import BRONZE, cliente, gravar_meta, hoje, sha256_bytes

COD_UF = {"MG": 31}
SIDRA = "https://apisidra.ibge.gov.br/values"


def urls(uf: str) -> dict[str, str]:
    cod = COD_UF[uf]
    return {
        f"municipios_{uf}.json": f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{cod}/municipios",
        # tabela 6579 = estimativas de população; variável 9324 = população residente estimada
        f"populacao_{uf}.json": f"{SIDRA}/t/6579/n6/in%20n3%20{cod}/v/9324/p/last%201",
        f"malha_{uf}.geojson": (f"https://servicodados.ibge.gov.br/api/v3/malhas/estados/{cod}"
                                "?formato=application/vnd.geo+json&intrarregiao=municipio&qualidade=minima"),
        # tabela 1737 / variável 2266 = IPCA número-índice; tabela 1736 / variável 2289 = INPC número-índice
        "ipca.json": f"{SIDRA}/t/1737/n1/all/v/2266/p/201901-209912",
        "inpc.json": f"{SIDRA}/t/1736/n1/all/v/2289/p/201901-209912",
    }


def coletar(uf: str) -> None:
    destino = BRONZE / "ibge" / hoje()
    destino.mkdir(parents=True, exist_ok=True)
    with cliente(timeout=180) as c:
        for nome, url in urls(uf).items():
            arq = destino / nome
            if arq.exists():
                print(f"{nome}: já existe, mantido")
                continue
            r = c.get(url)
            if r.status_code != 200:
                print(f"{nome}: FALHOU {r.status_code} {r.text[:200]}")
                continue
            arq.write_bytes(r.content)
            gravar_meta(arq, url=url, metodo="GET", bytes=len(r.content), sha256=sha256_bytes(r.content))
            print(f"{nome}: {len(r.content):,} bytes")
            time.sleep(1)


if __name__ == "__main__":
    coletar(sys.argv[1] if len(sys.argv) > 1 else "MG")
