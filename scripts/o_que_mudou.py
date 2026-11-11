"""O que mudou de uma carga para a outra (src/agent/o_que_mudou.py): compara o conjunto público publicado antes com o
novo e grava o relatório (e, com a chave do Gemini, um resumo de 2 a 4 frases, com cada número conferido).

`--antes` aceita uma pasta ou uma referência do git (tag, commit, branch): nesse caso, o `data/publico` daquela versão
é extraído numa pasta temporária. Rodar depois de cada carga oficial (e, na Fase 4, pelo pipeline agendado).

Uso:
  uv run python scripts/o_que_mudou.py --antes v1.0                      # contra a Release v1.0
  uv run python scripts/o_que_mudou.py --antes HEAD --saida docs/o_que_mudou.md
  uv run python scripts/o_que_mudou.py --antes v1.0 --sem-ia            # só o relatório, sem chamar a API
"""
import argparse
import io
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import publico  # noqa: E402
from src.agent import o_que_mudou  # noqa: E402


def pasta_da_versao(ref: str) -> Path:
    """`data/publico` da versão `ref` do git, extraído numa pasta temporária."""
    pasta_rel = Path(publico.CONFIG["pasta"]).as_posix()
    tar = subprocess.run(["git", "archive", "--format=tar", ref, pasta_rel], cwd=RAIZ, capture_output=True, check=True)
    destino = Path(tempfile.mkdtemp(prefix="radar_antes_"))
    with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as t:
        t.extractall(destino, filter="data")
    return destino / pasta_rel


def main() -> None:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--antes", required=True, help="pasta do conjunto anterior ou referência do git (ex.: v1.0)")
    a.add_argument("--depois", default=str(publico.PASTA), help="pasta do conjunto novo (padrão: data/publico)")
    a.add_argument("--saida", help="arquivo Markdown (padrão: só imprime)")
    a.add_argument("--sem-ia", action="store_true", help="não chama o Gemini (só o relatório)")
    args = a.parse_args()
    antes = Path(args.antes) if Path(args.antes).is_dir() else pasta_da_versao(args.antes)
    d = o_que_mudou.comparar(antes, Path(args.depois))
    base, resumo = o_que_mudou.resumir(d, gerar=(lambda s, t: "") if args.sem_ia else None)
    texto = o_que_mudou.markdown(d, resumo, base)
    if args.saida:
        Path(args.saida).write_text(texto, encoding="utf-8")
        print(f"gravado em {args.saida}" + (" (com o resumo da IA)" if resumo else " (sem resumo da IA)"))
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(texto)


if __name__ == "__main__":
    main()
