"""SUSEP SES (BaseCompleta.zip): baixa a base e extrai as linhas dos ramos de garantia em vigor (0775 e 0776).

Idempotente: não baixa se o ZIP do dia existe e não extrai se o CSV filtrado já existe.
Saída: data/bronze/susep_ses/<data>/{BaseCompleta.zip, _metadados.json, ses_seguros_garantia.csv, ses_cias.csv}

Uso: uv run python -m src.ingest.susep
"""
import csv
import io
import json
import zipfile
from pathlib import Path

import httpx

from src.ingest.comum import BRONZE, USER_AGENT, VERSAO_COLETOR, agora, gravar_meta, hoje, sha256_arquivo

URL = "https://www2.susep.gov.br/redarq.asp?arq=BaseCompleta%2ezip"
RAMOS = ("0775", "0776")  # Garantia Segurado - Setor Público / Setor Privado (Ses_ramos.csv)


def baixar() -> Path:
    existentes = sorted((BRONZE / "susep_ses").glob("*/BaseCompleta.zip"))
    if existentes:
        print(f"BaseCompleta.zip: usando {existentes[-1].parent.name}")
        return existentes[-1]
    dest = BRONZE / "susep_ses" / hoje()
    dest.mkdir(parents=True, exist_ok=True)
    alvo = dest / "BaseCompleta.zip"
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=httpx.Timeout(60, read=600),
                      follow_redirects=True) as c, c.stream("GET", URL) as r:
        r.raise_for_status()
        with open(alvo, "wb") as f:
            for b in r.iter_bytes(1 << 20):
                f.write(b)
    (dest / "_metadados.json").write_text(json.dumps({"BaseCompleta.zip": {
        "url": URL, "bytes": alvo.stat().st_size, "sha256": sha256_arquivo(alvo), "coletado_em": agora(),
        "versao_coletor": VERSAO_COLETOR}}, indent=1), encoding="utf-8")
    return alvo


def filtrar(zpath: Path) -> Path:
    out = zpath.parent / "ses_seguros_garantia.csv"
    z = zipfile.ZipFile(zpath)
    if not out.exists():
        with z.open("Ses_seguros.csv") as f, open(out, "w", encoding="utf-8", newline="") as fo:
            rd = csv.reader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";")
            cab = [c.strip().lower() for c in next(rd)]
            i_ramo = cab.index("coramo")
            w = csv.writer(fo, delimiter=";")
            w.writerow(cab)
            for row in rd:
                if row[i_ramo].strip() in RAMOS:
                    w.writerow([x.strip() for x in row])
        gravar_meta(out, origem=str(zpath.relative_to(BRONZE)), filtro=f"Ses_seguros.csv, coramo em {RAMOS}",
                    unidade="R$ (valores com centavos e vírgula decimal; inferido, o Ses_campos não declara unidade)")
    cias = zpath.parent / "ses_cias.csv"
    if not cias.exists():
        cias.write_text(z.read("Ses_cias.csv").decode("latin-1"), encoding="utf-8")
        gravar_meta(cias, origem=str(zpath.relative_to(BRONZE)), arquivo="Ses_cias.csv")
    return out


if __name__ == "__main__":
    print("filtrado:", filtrar(baixar()))
