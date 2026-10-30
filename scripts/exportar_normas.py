"""Copia o texto dos Provimentos CNJ 227, 213 e 243 do bronze para data/normas/ (versionado), para o chat buscar as
normas no link público e num clone, sem o bronze (D-064).

O texto é o oficial (atos.cnj.jus.br, coletado em 2026-10-17), sem nenhuma mudança além de tirar a linha de
assinatura ("Ministro ..."), que traz nome de pessoa física (D-038). tests/test_chat.py confere as duas coisas.

Uso: uv run python scripts/exportar_normas.py
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.agent.ferramentas import NORMAS, NORMAS_BRONZE, NORMAS_DIR  # noqa: E402

ASSINATURA = re.compile(r"(?m)^Minist(?:ro|ra) .*$\n?")


def sem_assinatura(texto: str) -> str:
    return ASSINATURA.sub("", texto)


def main() -> None:
    NORMAS_DIR.mkdir(parents=True, exist_ok=True)
    for arquivo, _ in NORMAS.values():
        origem = NORMAS_BRONZE / arquivo
        if not origem.exists():
            raise SystemExit(f"falta {origem.relative_to(RAIZ)} (bronze): baixe os dados antes (README)")
        (NORMAS_DIR / arquivo).write_text(sem_assinatura(origem.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"{arquivo}: ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    main()
