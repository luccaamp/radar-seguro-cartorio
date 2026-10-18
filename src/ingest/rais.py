"""RAIS (PDET, FTP público): baixa o pacote de vínculos, extrai e filtra o CNAE 6912-5/00 da UF.

Idempotente: não baixa se o .7z já está completo e não filtra se o CSV filtrado já existe.
O arquivo filtrado (poucos MB) é o que o silver lê; o bruto completo pode ser apagado depois (hash fica no metadado).
Saída: data/bronze/rais/<ano>/{<pacote>.7z, _metadados.json, extraido/<pacote>_CNAE6912500_<UF>.csv}

Uso: uv run python -m src.ingest.rais 2025 MG
"""
import csv
import ftplib
import json
import sys
import time
from pathlib import Path

import py7zr

from src.ingest.comum import BRONZE, agora, gravar_meta, sha256_arquivo, VERSAO_COLETOR

FTP_HOST = "ftp.mtps.gov.br"
PACOTE_UF = {"MG": "RAIS_VINC_PUB_MG_ES_RJ.7z"}
COD_UF_IBGE = {"MG": "31"}
CNAE = "6912500"


def baixar(ano: str, nome: str) -> Path:
    dest = BRONZE / "rais" / ano
    dest.mkdir(parents=True, exist_ok=True)
    alvo, meta_path = dest / nome, dest / "_metadados.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    if nome in meta and alvo.exists() and alvo.stat().st_size == meta[nome]["bytes"]:
        print(f"{nome}: já baixado")
        return alvo
    for tentativa in range(5):
        try:
            f = ftplib.FTP(FTP_HOST, timeout=300, encoding="latin-1")
            f.login()
            f.cwd(f"/pdet/microdados/RAIS/{ano}")
            f.voidcmd("TYPE I")
            total = f.size(nome)
            ini = alvo.stat().st_size if alvo.exists() else 0
            if ini < total:
                with open(alvo, "ab") as out:
                    f.retrbinary(f"RETR {nome}", out.write, blocksize=1 << 20, rest=ini or None)
            f.quit()
            if alvo.stat().st_size >= total:
                break
        except Exception as e:
            print(f"{nome}: erro {type(e).__name__} (tentativa {tentativa + 1})", flush=True)
            time.sleep(20)
    meta[nome] = {"url": f"ftp://{FTP_HOST}/pdet/microdados/RAIS/{ano}/{nome}", "bytes": alvo.stat().st_size,
                  "sha256": sha256_arquivo(alvo), "coletado_em": agora(), "versao_coletor": VERSAO_COLETOR}
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return alvo


def filtrar(pacote: Path, uf: str) -> Path:
    saida = pacote.parent / "extraido"
    saida.mkdir(exist_ok=True)
    with py7zr.SevenZipFile(pacote, "r") as z:
        nomes = z.getnames()
        faltam = [n for n in nomes if not (saida / n).exists()]
    filtrados = [saida / (Path(n).stem + f"_CNAE{CNAE}_{uf}.csv") for n in nomes]
    if all(p.exists() for p in filtrados):
        print(f"filtrado de {uf}: já existe")
        return filtrados[0]
    if faltam:
        with py7zr.SevenZipFile(pacote, "r") as z:
            z.extract(path=saida, targets=faltam)
    for n, destino in zip(nomes, filtrados):
        with open(saida / n, encoding="latin-1", newline="") as f, open(destino, "w", encoding="utf-8", newline="") as fo:
            rd = csv.reader(f, delimiter=";")
            cab = [c.strip() for c in next(rd)]
            i_cnae, i_mun = cab.index("CNAE 2.0 Subclasse - Codigo"), cab.index("Município - Código")
            w = csv.writer(fo, delimiter=";")
            w.writerow(cab)
            for row in rd:
                if row[i_cnae].strip() == CNAE and row[i_mun].strip().startswith(COD_UF_IBGE[uf]):
                    w.writerow([x.strip() for x in row])
        gravar_meta(destino, origem=str(pacote.relative_to(BRONZE)), filtro=f"CNAE {CNAE}, município da UF {uf}",
                    codificacao="utf-8 (bruto em latin-1)")
    return filtrados[0]


if __name__ == "__main__":
    ano, uf = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("2025", "MG")
    print("filtrado:", filtrar(baixar(ano, PACOTE_UF[uf]), uf))
