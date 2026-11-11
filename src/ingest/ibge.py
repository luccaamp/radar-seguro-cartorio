"""Coleta do IBGE: municípios de uma UF, população estimada, malha municipal (GeoJSON) e índices de preço (IPCA, INPC).

Idempotente: se o arquivo do dia já existe, não baixa de novo.
Saída: data/bronze/ibge/<data>/{municipios_<UF>.json, populacao_<UF>.json, malha_<UF>.geojson, ipca.json, inpc.json}

Uso: uv run python -m src.ingest.ibge MG
"""
import sys
import time

from src import estados_config
from src.ingest.comum import BRONZE, cliente, gravar_meta, hoje, pedir, sha256_bytes

SIDRA = "https://apisidra.ibge.gov.br/values"


def urls(uf: str) -> dict[str, str]:
    cod = estados_config.cod_ibge(uf)   # config/estados.yaml (Fase 3, D-081)
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


def urls_brasil() -> dict[str, str]:
    """O que a visão do Brasil (camada 1, D-087) usa do IBGE: estados, todos os municípios, população estimada por UF e
    a malha dos estados."""
    return {
        "brasil_estados.json": "https://servicodados.ibge.gov.br/api/v1/localidades/estados",
        "brasil_municipios.json": "https://servicodados.ibge.gov.br/api/v1/localidades/municipios",
        # n3 = unidade da federação; tabela 6579 / variável 9324, como em urls()
        "brasil_populacao.json": f"{SIDRA}/t/6579/n3/all/v/9324/p/last%201",
        "brasil_malha_uf.geojson": ("https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
                                    "?formato=application/vnd.geo+json&intrarregiao=UF&qualidade=minima"),
    }


def coletar_brasil(destino=None) -> None:
    """Coleta urls_brasil() em data/bronze/ibge/<data>/ (ou `destino`). Idempotente; falha com erro (o pipeline
    agendado não pode publicar com um arquivo faltando)."""
    _baixar(urls_brasil(), destino or BRONZE / "ibge" / hoje(), obrigatorio=True)


def _baixar(alvos: dict[str, str], destino, obrigatorio: bool = False) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    with cliente(timeout=180, conectar=20) as c:
        for nome, url in alvos.items():
            arq = destino / nome
            if arq.exists():
                print(f"{nome}: já existe, mantido")
                continue
            r = pedir(c, "GET", url)   # 3 tentativas, também para erro de rede (o erro final sobe)
            if r.status_code != 200:
                if obrigatorio:
                    raise RuntimeError(f"IBGE {nome}: HTTP {r.status_code} {r.text[:200]}")
                print(f"{nome}: FALHOU {r.status_code} {r.text[:200]}")
                continue
            arq.write_bytes(r.content)
            gravar_meta(arq, url=url, metodo="GET", bytes=len(r.content), sha256=sha256_bytes(r.content))
            print(f"{nome}: {len(r.content):,} bytes")
            time.sleep(1)


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
    alvo = sys.argv[1] if len(sys.argv) > 1 else estados_config.uf_padrao()
    coletar_brasil() if alvo == "BR" else coletar(alvo)   # "BR": a visão do Brasil (D-087)
