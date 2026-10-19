"""Pacotes de dados para Releases do GitHub (D-030): zip por camada, partes abaixo de 2 GiB, manifesto com hashes.

Formato do manifesto (pacotes/<nivel>/manifesto.json):
  nivel, carga, executado_em, versao_premissas, commit, fontes (data de referência de cada fonte), artefatos: lista de
  {camada, nome, zip, bytes_zip, sha256_zip, partes: [{arquivo, bytes, sha256}], destino, arquivos: [{caminho, bytes,
  sha256}], excluidos: [{padrao, motivo, n, bytes}]}.
Um artefato sem partes é publicado como o próprio zip; com partes, só as partes (o zip é remontado na instalação).
"""
import fnmatch
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((RAIZ / "config" / "pacotes.yaml").read_text(encoding="utf-8"))
MANIFESTO = "manifesto.json"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while bloco := f.read(1 << 22):
            h.update(bloco)
    return h.hexdigest()


def tag(nivel: str, carga: str) -> str:
    return CONFIG["tag"][nivel].format(carga=carga)


def excluido(rel: str, regras: list[dict]) -> dict | None:
    return next((r for r in regras if fnmatch.fnmatch(rel, r["padrao"])), None)


def zipar(origem: Path, arquivos: list[Path], destino: Path) -> list[dict]:
    """Zip dos `arquivos` (caminhos relativos a `origem` dentro do zip). Arquivos já comprimidos vão sem nova
    compressão. Devolve a lista {caminho, bytes, sha256} dos originais."""
    ja = tuple(CONFIG["ja_comprimidos"])
    lista = []
    with zipfile.ZipFile(destino, "w", allowZip64=True) as z:
        for p in arquivos:
            rel = p.relative_to(origem).as_posix()
            modo = zipfile.ZIP_STORED if p.suffix.lower() in ja else zipfile.ZIP_DEFLATED
            z.write(p, rel, compress_type=modo, compresslevel=6 if modo == zipfile.ZIP_DEFLATED else None)
            lista.append({"caminho": rel, "bytes": p.stat().st_size, "sha256": sha256(p)})
    return lista


def dividir(zip_: Path, tamanho: int = CONFIG["tamanho_parte_bytes"]) -> list[dict]:
    """Divide o zip em partes de até `tamanho` bytes (.part001, .part002...) e apaga o zip inteiro. Se couber em um
    arquivo só, não divide (lista vazia)."""
    if zip_.stat().st_size <= tamanho:
        return []
    partes = []
    with open(zip_, "rb") as f:
        i = 0
        while bloco := f.read(tamanho):
            i += 1
            p = zip_.with_name(f"{zip_.name}.part{i:03d}")
            p.write_bytes(bloco)
            partes.append({"arquivo": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)})
    zip_.unlink()
    return partes


def arquivos_publicados(a: dict) -> list[dict]:
    """Arquivos do Release de um artefato: as partes ou o próprio zip."""
    return a["partes"] or [{"arquivo": a["zip"], "bytes": a["bytes_zip"], "sha256": a["sha256_zip"]}]


def remontar(a: dict, pasta: Path) -> Path:
    """Confere o hash de cada parte, junta e confere o hash do zip. Erro se algo não bater."""
    for parte in arquivos_publicados(a):
        p = pasta / parte["arquivo"]
        if not p.exists():
            raise FileNotFoundError(f"falta {parte['arquivo']}")
        if p.stat().st_size != parte["bytes"] or sha256(p) != parte["sha256"]:
            raise ValueError(f"{parte['arquivo']}: hash diferente do manifesto (download incompleto ou corrompido)")
    zip_ = pasta / a["zip"]
    if a["partes"]:
        with open(zip_, "wb") as saida:
            for parte in a["partes"]:
                with open(pasta / parte["arquivo"], "rb") as f:
                    shutil.copyfileobj(f, saida, 1 << 22)
                (pasta / parte["arquivo"]).unlink()
    if sha256(zip_) != a["sha256_zip"]:
        raise ValueError(f"{a['zip']}: hash do zip remontado diferente do manifesto")
    return zip_


def extrair_conferindo(a: dict, zip_: Path, destino: Path) -> None:
    """Extrai para `destino` e confere o hash de cada arquivo original."""
    with zipfile.ZipFile(zip_) as z:
        z.extractall(destino)
    for arq in a["arquivos"]:
        p = destino / arq["caminho"]
        if not p.exists() or p.stat().st_size != arq["bytes"] or sha256(p) != arq["sha256"]:
            raise ValueError(f"{a['nome']}/{arq['caminho']}: hash diferente do manifesto")


def ler_manifesto(pasta: Path) -> dict:
    return json.loads((pasta / MANIFESTO).read_text(encoding="utf-8"))
