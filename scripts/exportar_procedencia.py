"""Procedência do bronze em data/procedencia/ (versionada no git, D-070): de cada arquivo coletado, a URL oficial, o
SHA-256, o tamanho e a hora de coleta, sem o dado em si.

  uv run python scripts/exportar_procedencia.py   # regrava data/procedencia/ a partir de data/bronze/

O bronze fica fora do git e do Release público porque tem nome de pessoa (D-030); estes arquivos de registro não
têm (tests/test_procedencia.py confere) e mostram de onde veio cada número sem o pacote da equipe. Copia, no mesmo
caminho relativo do bronze, os original.json (originais grandes, D-032), os _metadados.json e os *.meta.json.
Rodar depois de cada coleta, junto com o exportar_completo.py.
"""
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.ingest.comum import BRONZE  # noqa: E402

DESTINO = RAIZ / "data" / "procedencia"
PADROES = ("original.json", "_metadados.json", "*.meta.json")


def arquivos(bronze: Path = BRONZE) -> list[Path]:
    """Arquivos de registro do bronze, em ordem."""
    return sorted({p for padrao in PADROES for p in bronze.rglob(padrao) if p.is_file()})


def exportar() -> None:
    lista = arquivos()
    if not lista:
        raise SystemExit("data/bronze/ sem arquivos de registro: nada a exportar (o bronze é do pacote da equipe)")
    with tempfile.TemporaryDirectory() as tmp:
        novo = Path(tmp) / "procedencia"
        for p in lista:
            destino = novo / p.relative_to(BRONZE)
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, destino)
        if DESTINO.exists():
            shutil.rmtree(DESTINO)   # só o que este script gerou antes (versionado no git)
        shutil.copytree(novo, DESTINO)
    print(f"data/procedencia/: {len(lista)} arquivos de registro de {len({p.relative_to(BRONZE).parts[0] for p in lista})} fontes")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    exportar()
