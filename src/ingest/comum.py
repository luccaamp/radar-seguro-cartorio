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


ORIGINAL_JSON = "original.json"


def originais() -> Path:
    """Pasta dos originais grandes (D-032), FORA do OneDrive: config/pacotes.yaml (`pastas.originais`) ou a
    variável RADAR_ORIGINAIS. Mesma estrutura do bronze: <fonte>/<snapshot>/<arquivo>."""
    from src import pacotes
    return pacotes.pasta("originais")


def bronze_de(original: Path) -> Path:
    """Pasta do bronze oficial que corresponde à pasta de um original (mesmo <fonte>/<snapshot>)."""
    return BRONZE / original.parent.relative_to(originais())


def registrar_original(original: Path, url: str) -> dict:
    """Acrescenta (ou atualiza) o arquivo original em <bronze>/<fonte>/<snapshot>/original.json: URL oficial,
    SHA-256, tamanho, data e hora de coleta e onde foi guardado (relativo à pasta de originais). O bronze oficial
    guarda só o extrato e este registro (D-032)."""
    pasta = bronze_de(original)
    pasta.mkdir(parents=True, exist_ok=True)
    reg_path = pasta / ORIGINAL_JSON
    reg = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else {
        "descricao": "Originais desta fonte (D-032): ficam fora do bronze oficial, na pasta de originais "
                     "(config/pacotes.yaml); aqui ficam o registro e o extrato que o silver lê.", "arquivos": {}}
    entrada = {"url": url, "bytes": original.stat().st_size, "sha256": sha256_arquivo(original),
               "coletado_em": agora(), "versao_coletor": VERSAO_COLETOR,
               "guardado_em": original.relative_to(originais()).as_posix()}
    reg["arquivos"][original.name] = entrada
    reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    return entrada


def ler_original(pasta_bronze: Path, nome: str) -> dict | None:
    """Registro de um original em <pasta_bronze>/original.json (None se não houver)."""
    p = pasta_bronze / ORIGINAL_JSON
    return json.loads(p.read_text(encoding="utf-8"))["arquivos"].get(nome) if p.exists() else None


def snapshot_mais_recente(fonte: str, padrao: str) -> Path:
    """Arquivo mais recente que casa com `padrao` em data/bronze/<fonte>/<data>/."""
    candidatos = sorted((BRONZE / fonte).glob(f"*/{padrao}"))
    if not candidatos:
        raise FileNotFoundError(f"nenhum snapshot de {fonte}/{padrao} no bronze")
    return candidatos[-1]
