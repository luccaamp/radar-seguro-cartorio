"""Pacotes de dados (D-030): zip, partes, manifesto e instalação conferida. Dados SINTÉTICOS, em pastas temporárias."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from src import pacotes

RAIZ = Path(__file__).resolve().parents[1]


def pacote_sintetico(tmp: Path, tamanho_parte: int | None = None) -> Path:
    """SINTÉTICO: uma 'camada silver' com dois arquivos (um numa subpasta) empacotada como o empacotador faz."""
    origem = tmp / "origem"
    (origem / "sub").mkdir(parents=True)
    (origem / "a.parquet").write_bytes(b"conteudo sintetico A" * 1000)
    (origem / "sub" / "b.txt").write_text("conteudo sintetico B" * 500, encoding="utf-8")
    saida = tmp / "pacote"
    saida.mkdir()
    zip_ = saida / "silver-2026-01-01.zip"
    lista = pacotes.zipar(origem, sorted(p for p in origem.rglob("*") if p.is_file()), zip_)
    a = {"camada": "silver", "nome": "silver", "zip": zip_.name, "bytes_zip": zip_.stat().st_size,
         "sha256_zip": pacotes.sha256(zip_), "destino": "data/silver", "arquivos": lista, "excluidos": []}
    a["partes"] = pacotes.dividir(zip_, tamanho_parte) if tamanho_parte else []
    man = {"nivel": "publico", "carga": "2026-01-01", "versao_premissas": 2, "commit": None, "artefatos": [a]}
    (saida / pacotes.MANIFESTO).write_text(json.dumps(man), encoding="utf-8")
    return saida


UTF8 = {**os.environ, "PYTHONIOENCODING": "utf-8"}   # a saída tem acentos; no Windows o padrão do console é cp1252


def instalar(origem: Path, raiz: Path, *extra, camadas: str = "silver") -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(RAIZ / "scripts" / "baixar_dados.py"), "--origem", str(origem),
                           "--camadas", camadas, "--raiz", str(raiz), *extra], capture_output=True, text=True,
                          encoding="utf-8", env=UTF8)


@pytest.mark.parametrize("tamanho_parte", [None, 4000])   # sem partes e com várias partes
def test_instala_na_estrutura_certa_e_confere(tmp_path, tamanho_parte):
    pac = pacote_sintetico(tmp_path, tamanho_parte)
    if tamanho_parte:
        assert len(list(pac.glob("*.part*"))) > 1 and not list(pac.glob("*.zip"))
    raiz = tmp_path / "clone"
    r = instalar(pac, raiz)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (raiz / "data/silver/a.parquet").exists() and (raiz / "data/silver/sub/b.txt").exists()
    info = json.loads((raiz / "data/carga_atual.json").read_text(encoding="utf-8"))
    assert info["carga"] == "2026-01-01" and info["nivel"] == "publico"


def test_nao_sobrescreve_sem_substituir(tmp_path):
    pac = pacote_sintetico(tmp_path)
    raiz = tmp_path / "clone"
    (raiz / "data/silver").mkdir(parents=True)
    (raiz / "data/silver/meu.parquet").write_bytes(b"dado local")
    r = instalar(pac, raiz)
    assert r.returncode != 0 and "--substituir" in r.stdout + r.stderr
    assert (raiz / "data/silver/meu.parquet").read_bytes() == b"dado local"
    assert instalar(pac, raiz, "--substituir").returncode == 0
    assert not (raiz / "data/silver/meu.parquet").exists() and (raiz / "data/silver/a.parquet").exists()


@pytest.mark.parametrize("carga", ["banco", "gold"])
def test_nao_grava_carga_atual_onde_ha_banco_ou_gold(tmp_path, carga):
    """SINTÉTICO: onde já há banco ou gold, instalar recusaria trocar o data/carga_atual.json da carga em uso (achado
    de 2026-10-19: instalação feita da pasta errada criou o arquivo no projeto real). Só com --substituir."""
    pac = pacote_sintetico(tmp_path)
    raiz = tmp_path / "projeto"
    (raiz / "data" / "gold").mkdir(parents=True)
    existente = raiz / "data" / ("radar.duckdb" if carga == "banco" else "gold/fato.parquet")
    existente.write_bytes(b"carga em uso")
    r = instalar(pac, raiz)
    assert r.returncode != 0 and "--substituir" in r.stdout + r.stderr and "carga_atual" in r.stdout + r.stderr
    assert not (raiz / "data" / "carga_atual.json").exists() and not (raiz / "data" / "silver").exists()
    r = instalar(pac, raiz, "--substituir")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (raiz / "data" / "carga_atual.json").exists() and (raiz / "data" / "silver" / "a.parquet").exists()
    assert existente.read_bytes() == b"carga em uso"   # instalar o silver não mexe no banco nem no gold


def test_arquivo_corrompido_falha(tmp_path):
    pac = pacote_sintetico(tmp_path)
    z = next(pac.glob("*.zip"))
    z.write_bytes(z.read_bytes()[:-10] + b"0123456789")
    r = instalar(pac, tmp_path / "clone")
    assert r.returncode != 0 and "hash" in (r.stdout + r.stderr)
    assert not (tmp_path / "clone/data/silver").exists()


def test_camada_que_nao_existe_no_pacote_publico(tmp_path):
    pac = pacote_sintetico(tmp_path)
    r = instalar(pac, tmp_path / "clone", camadas="bronze")
    assert r.returncode != 0 and "dados da equipe" in (r.stdout + r.stderr)
