"""Dados abertos do CNPJ (Receita Federal, compartilhamento público WebDAV do SERPRO+): baixa e filtra o CNAE 6912-5/00.

Idempotente e retomável. O filtrado (`estabelecimentos_cnae6912500.json`) não guarda razão social, nome fantasia
nem contatos; é o que o silver lê. Os ZIPs completos podem ser apagados depois (hash no _metadados.json).

Uso: uv run python -m src.ingest.cnpj 2026-10
"""
import csv
import io
import json
import re
import sys
import time
import zipfile
from pathlib import Path

import httpx

from src.ingest.comum import BRONZE, USER_AGENT, VERSAO_COLETOR, agora, gravar_meta, sha256_arquivo

TOKEN_PUBLICO = "gn672Ad4CF8N6TK"  # token do link público de compartilhamento (não é credencial pessoal)
BASE = "https://arquivos.receitafederal.gov.br/public.php/webdav/Dados/Cadastros/CNPJ"
ARQUIVOS = ([f"Estabelecimentos{i}.zip" for i in range(10)] + [f"Empresas{i}.zip" for i in range(10)]
            + ["Municipios.zip", "Naturezas.zip"])
CNAE = "6912500"
# posições do layout de Estabelecimentos (metadados da Receita), validadas na primeira linha
CNPJB, MATFIL, SIT, DT_INI, CNAE1, CNAE2, UF, MUN = 0, 3, 5, 10, 11, 12, 19, 20


def baixar(mes: str) -> Path:
    dest = BRONZE / "cnpj" / mes
    dest.mkdir(parents=True, exist_ok=True)
    meta_path = dest / "_metadados.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    with httpx.Client(headers={"User-Agent": USER_AGENT}, auth=(TOKEN_PUBLICO, ""),
                      timeout=httpx.Timeout(60, read=300), follow_redirects=True) as c:
        for n in ARQUIVOS:
            if meta.get(n, {}).get("completo"):
                continue
            url, alvo = f"{BASE}/{mes}/{n}", dest / n
            for tentativa in range(5):
                try:
                    ini = alvo.stat().st_size if alvo.exists() else 0
                    with c.stream("GET", url, headers={"Range": f"bytes={ini}-"} if ini else {}) as r:
                        if r.status_code == 416:
                            break
                        r.raise_for_status()
                        with open(alvo, "ab" if r.status_code == 206 else "wb") as f:
                            for bloco in r.iter_bytes(1 << 20):
                                f.write(bloco)
                    break
                except Exception as e:
                    print(f"{n}: erro {type(e).__name__} (tentativa {tentativa + 1})", flush=True)
                    time.sleep(15)
            meta[n] = {"url": url, "bytes": alvo.stat().st_size, "sha256": sha256_arquivo(alvo), "completo": True,
                       "coletado_em": agora(), "versao_coletor": VERSAO_COLETOR}
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{n}: baixado", flush=True)
    return dest


def _linhas(zpath: Path):
    with zipfile.ZipFile(zpath) as z:
        for n in z.namelist():
            with z.open(n) as f:
                yield from csv.reader(io.TextIOWrapper(f, encoding="latin-1", newline=""), delimiter=";")


def filtrar(dest: Path) -> Path:
    out = dest / "estabelecimentos_cnae6912500.json"
    if out.exists():
        print(f"{out.name}: já existe")
        return out
    mun_rfb = {r[0]: r[1] for r in _linhas(dest / "Municipios.zip")}
    sel, validado = [], False
    for i in range(10):
        for row in _linhas(dest / f"Estabelecimentos{i}.zip"):
            if not validado:
                assert re.fullmatch(r"\d{8}", row[CNPJB]) and re.fullmatch(r"\d{7}", row[CNAE1]), "layout mudou"
                validado = True
            secundario = CNAE in row[CNAE2].split(",")
            if row[CNAE1] == CNAE or secundario:
                sel.append({"cnpj_basico": row[CNPJB], "matriz_filial": row[MATFIL], "situacao": row[SIT],
                            "cnae_principal": row[CNAE1], "cnae_6912500_secundario": secundario, "uf": row[UF],
                            "mun_rfb": row[MUN], "municipio": mun_rfb.get(row[MUN]), "data_inicio": row[DT_INI]})
    basicos = {s["cnpj_basico"] for s in sel}
    natj = {}
    for i in range(10):
        for row in _linhas(dest / f"Empresas{i}.zip"):
            if row[0] in basicos:
                natj[row[0]] = row[2]
    for s in sel:
        s["natureza_juridica"] = natj.get(s["cnpj_basico"])
    out.write_text(json.dumps(sel, ensure_ascii=False), encoding="utf-8")
    gravar_meta(out, origem=f"cnpj/{dest.name}", filtro=f"CNAE {CNAE} principal ou secundário",
                campos_descartados="razão social, nome fantasia, endereço, telefone, e-mail")
    return out


if __name__ == "__main__":
    print("filtrado:", filtrar(baixar(sys.argv[1] if len(sys.argv) > 1 else "2026-10")))
