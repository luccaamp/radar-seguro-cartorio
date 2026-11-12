"""Procedência do bronze versionada em data/procedencia (D-070): sem dado pessoal e igual ao bronze local.

O conteúdo e a ausência de dado pessoal rodam em qualquer clone; a coerência com o bronze precisa do bronze local.
"""
import json
import re
import sys

import pytest

from apoio_painel import RAIZ
from src import publico
from src.ingest.comum import BRONZE

sys.path.insert(0, str(RAIZ / "scripts"))
import exportar_procedencia  # noqa: E402

PASTA = RAIZ / "data" / "procedencia"
ARQUIVOS = sorted(p for p in PASTA.rglob("*") if p.is_file())
HASH = re.compile(r"[0-9a-f]{64}")
URL = re.compile(r"(https?|ftp)://\S+")


def _textos(no):
    """Todos os textos de um JSON (chaves e valores), em qualquer profundidade."""
    if isinstance(no, dict):
        for k, v in no.items():
            yield k
            yield from _textos(v)
    elif isinstance(no, list):
        for v in no:
            yield from _textos(v)
    elif isinstance(no, str):
        yield no


def test_so_arquivos_de_registro():
    assert ARQUIVOS, "data/procedencia vazia: rode `uv run python scripts/exportar_procedencia.py`"
    assert all(p.name in ("original.json", "_metadados.json") or p.name.endswith(".meta.json") for p in ARQUIVOS)


def test_cada_arquivo_registra_url_e_hash():
    """Todo registro traz a URL oficial ou, num extrato, a `origem`: o original, com a URL no original.json da pasta."""
    for p in ARQUIVOS:
        dados = json.loads(p.read_text(encoding="utf-8"))
        if "origem" in dados and not any(URL.fullmatch(t) for t in _textos(dados)):
            # o original.json fica na pasta da coleta; o extrato pode estar numa subpasta (rais/2025/extraido, D-088)
            pasta = next(d for d in (p.parent, *p.parent.parents) if (d / "original.json").exists())
            original = json.loads((pasta / "original.json").read_text(encoding="utf-8"))["arquivos"]
            dados = original[dados["origem"].replace("\\", "/").rsplit("/", 1)[-1]]
        assert any(URL.fullmatch(t) for t in _textos(dados)), p.relative_to(PASTA)
        assert any(HASH.fullmatch(t) for t in _textos(dados)) or "url" in dados, p.relative_to(PASTA)


def test_sem_dado_pessoal():
    """Nenhum CPF nem e-mail fora dos hashes e das URLs oficiais (os dígitos de um SHA-256 ou do id de um documento na
    URL casam com o padrão de CPF)."""
    for p in ARQUIVOS:
        textos = list(_textos(json.loads(p.read_text(encoding="utf-8"))))
        cpf = [t for t in textos if not HASH.fullmatch(t) and not URL.fullmatch(t) and publico.CPF.search(t)]
        assert not cpf + [t for t in textos if publico.EMAIL.search(t)], p.relative_to(PASTA)


@pytest.mark.skipif(not exportar_procedencia.arquivos(), reason="sem bronze local: nada a comparar")
def test_igual_ao_bronze_local():
    """Compara as pastas de coleta (fonte/snapshot) que existem no bronze local: um clone com o --instalar do
    exportar_completo.py tem só a do BI do CNJ."""
    no_bronze = {p.relative_to(BRONZE).as_posix(): p.read_bytes() for p in exportar_procedencia.arquivos()}
    pastas = {k.rsplit("/", 1)[0] for k in no_bronze}
    versionado = {k: p.read_bytes() for p in ARQUIVOS
                  if (k := p.relative_to(PASTA).as_posix()).rsplit("/", 1)[0] in pastas}
    diferentes = sorted(set(no_bronze) ^ set(versionado) | {k for k in no_bronze.keys() & versionado.keys()
                                                            if no_bronze[k] != versionado[k]})
    assert not diferentes, f"data/procedencia desatualizada: rode `uv run python scripts/exportar_procedencia.py` ({diferentes[:5]})"
