"""Baixa o texto oficial (Planalto) das leis trabalhistas e previdenciárias usadas no cálculo do passivo (art. 5º do Prov. 227).

Idempotente. Saída: data/bronze/normas/<data>/<nome>.html (+ .meta.json)

Uso: uv run python -m src.ingest.legislacao
"""
import time

from src.ingest.comum import BRONZE, cliente, gravar_meta, hoje, sha256_bytes

LEIS = {
    "lei_12506_2011_aviso_previo": "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12506.htm",
    "lei_4090_1962_13_salario": "https://www.planalto.gov.br/ccivil_03/leis/l4090.htm",
    "lei_8036_1990_fgts": "https://www.planalto.gov.br/ccivil_03/leis/l8036consol.htm",
    "lei_8212_1991_custeio_previdencia": "https://www.planalto.gov.br/ccivil_03/leis/l8212cons.htm",
    "decreto_3048_1999_regulamento_previdencia": "https://www.planalto.gov.br/ccivil_03/decreto/d3048.htm",
    # Anexo V: relação de atividades preponderantes (CNAE) e alíquota RAT (link do próprio decreto)
    "decreto_3048_1999_anexo_v": "https://www.planalto.gov.br/ccivil_03/decreto/D3048anexov-vol1.htm",
    "clt_decreto_lei_5452_1943": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452.htm",
}


def coletar() -> None:
    destino = BRONZE / "normas" / hoje()
    destino.mkdir(parents=True, exist_ok=True)
    with cliente(timeout=180) as c:
        for nome, url in LEIS.items():
            arq = destino / f"{nome}.html"
            if arq.exists():
                print(f"{nome}: já existe")
                continue
            r = c.get(url)
            print(f"{nome}: {r.status_code} {len(r.content):,} bytes")
            if r.status_code == 200:
                arq.write_bytes(r.content)
                gravar_meta(arq, url=url, metodo="GET", bytes=len(r.content), sha256=sha256_bytes(r.content))
            time.sleep(2)


if __name__ == "__main__":
    coletar()
