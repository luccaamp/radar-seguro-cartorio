"""Saída do pipeline e dos scripts em UTF-8 também quando redirecionada (docs/erros_ia.md, 2026-10-20).

Fora de um console, o Python no Windows grava a saída em cp1252, que não tem "≥" nem "−", e o pipeline caía com
UnicodeEncodeError ao imprimir as reconciliações. O teste com dados roda o pipeline numa CÓPIA temporária do projeto
(código, config, silver e cópia do banco), nunca no banco real, com PYTHONIOENCODING=cp1252 para simular o Windows
em qualquer máquina.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
ENTRADAS = [RAIZ / "pipeline.py", *sorted((RAIZ / "scripts").glob("*.py"))]


@pytest.mark.parametrize("arquivo", ENTRADAS, ids=lambda p: p.name)
def test_script_que_imprime_reconfigura_a_saida(arquivo):
    texto = arquivo.read_text(encoding="utf-8")
    if not re.search(r"\bprint\(", texto):
        return
    assert 'sys.stdout.reconfigure(encoding="utf-8")' in texto, f"{arquivo.name}: falta reconfigurar a saída"


@pytest.mark.dados_reais
@pytest.mark.skipif(not (RAIZ / "data" / "radar.duckdb").exists() or not list((RAIZ / "data" / "silver").glob("*.parquet")),
                    reason="precisa do banco e do silver (dados da equipe)")
def test_pipeline_com_saida_redirecionada(tmp_path):
    copia = tmp_path / "projeto"
    copia.mkdir()
    shutil.copy2(RAIZ / "pipeline.py", copia / "pipeline.py")
    for pasta in ("src", "config", "data/silver"):
        shutil.copytree(RAIZ / pasta, copia / pasta, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(RAIZ / "data" / "radar.duckdb", copia / "data" / "radar.duckdb")
    (copia / "docs").mkdir()
    shutil.copy2(RAIZ / "docs" / "decisoes.md", copia / "docs" / "decisoes.md")   # o gold carrega o log de decisões
    log = tmp_path / "pipeline.log"
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
    env["PYTHONIOENCODING"] = "cp1252"
    with open(log, "wb") as saida:
        r = subprocess.run([sys.executable, "pipeline.py", "--a-partir-de", "silver"], cwd=copia, env=env,
                           stdout=saida, stderr=subprocess.STDOUT, timeout=600)
    texto = log.read_bytes().decode("utf-8", errors="replace")
    assert r.returncode == 0, texto[-2000:]
    assert "≥" in texto and "contratos do gold" in texto
