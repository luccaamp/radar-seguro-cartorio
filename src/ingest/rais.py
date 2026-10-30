"""RAIS (PDET, FTP público): baixa o pacote de vínculos, extrai e filtra o CNAE 6912-5/00 da UF.

Idempotente: não baixa se o .7z já está completo e não filtra se o CSV filtrado já existe.
D-032: o .7z e a extração completa (.COMT) ficam na pasta de originais, FORA do OneDrive (config/pacotes.yaml);
o bronze oficial guarda só o extrato filtrado (poucos MB, o que o silver lê) e o original.json (URL, SHA-256, tamanho,
data e hora de coleta).
Saída: <originais>/rais/<ano>/{<pacote>.7z, extraido/<pacote>.COMT}
       data/bronze/rais/<ano>/{original.json, extraido/<pacote>_CNAE6912500_<UF>.csv}

Uso: uv run python -m src.ingest.rais 2025 MG
"""
import csv
import ftplib
import sys
import time
from pathlib import Path

import py7zr

from src.ingest.comum import BRONZE, bronze_de, gravar_meta, ler_original, originais, registrar_original

FTP_HOST = "ftp.mtps.gov.br"
PACOTE_UF = {"MG": "RAIS_VINC_PUB_MG_ES_RJ.7z"}
COD_UF_IBGE = {"MG": "31"}
CNAE = "6912500"


def baixar(ano: str, nome: str) -> Path:
    dest = originais() / "rais" / ano
    dest.mkdir(parents=True, exist_ok=True)
    alvo = dest / nome
    reg = ler_original(BRONZE / "rais" / ano, nome)
    if reg and alvo.exists() and alvo.stat().st_size == reg["bytes"]:
        print(f"{nome}: já baixado ({dest})")
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
    registrar_original(alvo, f"ftp://{FTP_HOST}/pdet/microdados/RAIS/{ano}/{nome}")
    return alvo


def separador(linha: str) -> str:
    """Separador do arquivo da RAIS, pelo cabeçalho: o PDET já publicou com `;` e com `,` (entre aspas).
    Fixar um dos dois quebrou a coleta duas vezes (docs/erros_ia.md, 2026-10-17 e 2026-10-19)."""
    return ";" if linha.count(";") > linha.count(",") else ","


def filtrar(pacote: Path, uf: str, saida_extrato: Path | None = None, pasta_extracao: Path | None = None) -> Path:
    """Extrai o .7z (na pasta dos originais, fora do OneDrive) e grava o extrato do CNAE 6912-5/00 da UF no bronze.

    `saida_extrato` e `pasta_extracao` existem para o teste de reprodutibilidade (gerar noutra pasta e comparar o
    SHA-256 com o extrato do bronze); no uso normal, são a pasta do bronze e a dos originais."""
    extracao = pasta_extracao or pacote.parent / "extraido"
    saida = saida_extrato or bronze_de(pacote) / "extraido"
    extracao.mkdir(parents=True, exist_ok=True)
    saida.mkdir(parents=True, exist_ok=True)
    with py7zr.SevenZipFile(pacote, "r") as z:
        nomes = z.getnames()
        faltam = [n for n in nomes if not (extracao / n).exists()]
    filtrados = [saida / (Path(n).stem + f"_CNAE{CNAE}_{uf}.csv") for n in nomes]
    if all(p.exists() for p in filtrados):
        print(f"filtrado de {uf}: já existe")
        return filtrados[0]
    if faltam:
        with py7zr.SevenZipFile(pacote, "r") as z:
            z.extract(path=extracao, targets=faltam)
    for n, destino in zip(nomes, filtrados):
        with open(extracao / n, encoding="latin-1", newline="") as f, \
                open(destino, "w", encoding="utf-8", newline="") as fo:
            sep = separador(f.readline())
            f.seek(0)
            rd = csv.reader(f, delimiter=sep)
            cab = [c.strip() for c in next(rd)]
            i_cnae, i_mun = cab.index("CNAE 2.0 Subclasse - Codigo"), cab.index("Município - Código")
            w = csv.writer(fo, delimiter=";")
            w.writerow(cab)
            for row in rd:
                if row[i_cnae].strip() == CNAE and row[i_mun].strip().startswith(COD_UF_IBGE[uf]):
                    w.writerow([x.strip() for x in row])
        if saida_extrato is None:
            gravar_meta(destino, origem=f"rais/{pacote.parent.name}/{pacote.name}",
                        filtro=f"CNAE {CNAE}, município da UF {uf}", codificacao="utf-8 (bruto em latin-1)",
                        separador_original=sep)
    return filtrados[0]


if __name__ == "__main__":
    ano, uf = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("2025", "MG")
    print("filtrado:", filtrar(baixar(ano, PACOTE_UF[uf]), uf))
