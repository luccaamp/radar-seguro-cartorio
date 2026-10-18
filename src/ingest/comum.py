"""Utilidades comuns aos coletores: caminhos do bronze, cliente HTTP identificável, hash e metadados."""
import datetime as dt
import hashlib
import json
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parents[2]
BRONZE = RAIZ / "data" / "bronze"
VERSAO_COLETOR = "fase1-0.1"
USER_AGENT = "Mozilla/5.0 (compatible; radar-seguro-cartorio/0.1; projeto de portfolio)"


def hoje() -> str:
    return dt.date.today().isoformat()


def agora() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def cliente(timeout: float = 60, **headers) -> httpx.Client:
    return httpx.Client(headers={"User-Agent": USER_AGENT, **headers}, timeout=timeout, follow_redirects=True)


def sha256_bytes(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def sha256_arquivo(caminho: Path, bloco: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        while parte := f.read(bloco):
            h.update(parte)
    return h.hexdigest()


def gravar_meta(caminho: Path, **campos) -> None:
    """Grava <arquivo>.meta.json ao lado do bruto, com URL, data, hash e versão do coletor."""
    meta = {"coletado_em": agora(), "versao_coletor": VERSAO_COLETOR, **campos}
    if caminho.exists() and "sha256" not in meta:
        meta["sha256"] = sha256_arquivo(caminho)
    caminho.with_name(caminho.name + ".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


def snapshot_mais_recente(fonte: str, padrao: str) -> Path:
    """Arquivo mais recente que casa com `padrao` em data/bronze/<fonte>/<data>/."""
    candidatos = sorted((BRONZE / fonte).glob(f"*/{padrao}"))
    if not candidatos:
        raise FileNotFoundError(f"nenhum snapshot de {fonte}/{padrao} no bronze")
    return candidatos[-1]
