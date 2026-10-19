"""Baixa e instala camadas de dados de uma carga (D-030), conferindo todos os hashes.

  # dados públicos (qualquer pessoa, sem login): silver da carga
  uv run python scripts/baixar_dados.py --nivel publico --camadas silver --carga 2026-10-19
  # dados da equipe (colaboradores convidados; gh autenticado): qualquer camada
  uv run python scripts/baixar_dados.py --nivel equipe --camadas bronze,silver,gold,banco --carga 2026-10-19
  # plano B: de uma pasta local (OneDrive, pendrive) com o manifesto e os arquivos do pacote
  uv run python scripts/baixar_dados.py --origem D:/pacotes/equipe --camadas bronze

Junta as partes, confere o hash de cada parte, do zip e de cada arquivo, e só então instala em data/<camada>/.
Nunca sobrescreve dados locais sem --substituir. Grava data/carga_atual.json (carga e nível em uso; o painel mostra
no rodapé).
"""
import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import pacotes  # noqa: E402

ACESSO = ("Sem acesso ao repositório de dados da equipe ({repo}). Para pedir acesso: fale com o autor (ver "
          "CONTRIBUTING.md, 'Como pedir acesso'); depois instale o GitHub CLI (https://cli.github.com) e rode "
          "'gh auth login'. Detalhe: {erro}")


class Fonte:
    """De onde vêm os arquivos: pasta local, Release público (URL sem login) ou Release privado (gh)."""

    def __init__(self, nivel: str, carga: str | None, origem: Path | None):
        self.nivel, self.carga, self.origem = nivel, carga, origem
        self.repo = pacotes.CONFIG["repositorios"][nivel]
        if not origem and not carga:
            raise SystemExit("Informe --carga AAAA-MM-DD (ou --origem <pasta>).")
        if nivel == "equipe" and not origem:
            r = subprocess.run(["gh", "release", "view", pacotes.tag(nivel, carga), "--repo", self.repo],
                               capture_output=True, text=True)
            if r.returncode != 0:
                raise SystemExit(ACESSO.format(repo=self.repo, erro=(r.stderr or r.stdout).strip()[:300]))

    def baixar(self, nome: str, pasta: Path) -> Path:
        destino = pasta / nome
        if self.origem:
            shutil.copy2(self.origem / nome, destino)
        elif self.nivel == "publico":
            url = f"https://github.com/{self.repo}/releases/download/{pacotes.tag('publico', self.carga)}/{nome}"
            with httpx.stream("GET", url, follow_redirects=True, timeout=120) as r:
                if r.status_code != 200:
                    raise SystemExit(f"Não foi possível baixar {url} (HTTP {r.status_code}). Confira a carga em "
                                     f"https://github.com/{self.repo}/releases")
                with open(destino, "wb") as f:
                    for bloco in r.iter_bytes(1 << 20):
                        f.write(bloco)
        else:
            r = subprocess.run(["gh", "release", "download", pacotes.tag("equipe", self.carga), "--repo", self.repo,
                                "--pattern", nome, "--dir", str(pasta), "--clobber"], capture_output=True, text=True)
            if r.returncode != 0:
                raise SystemExit(ACESSO.format(repo=self.repo, erro=(r.stderr or r.stdout).strip()[:300]))
        return destino


def tem_dados(p: Path) -> bool:
    return p.is_file() or (p.is_dir() and any(p.iterdir()))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nivel", choices=["publico", "equipe"], help="padrão: o do manifesto de --origem, ou publico")
    ap.add_argument("--carga", help="AAAA-MM-DD (a tag do Release)")
    ap.add_argument("--camadas", required=True, help="lista separada por vírgula: bronze,silver,gold,banco")
    ap.add_argument("--origem", type=Path, help="pasta local com manifesto.json e os arquivos do pacote (plano B)")
    ap.add_argument("--substituir", action="store_true", help="substitui dados locais que já existem")
    ap.add_argument("--raiz", type=Path, default=RAIZ, help=argparse.SUPPRESS)   # testes: instalar noutra pasta
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="radar_baixar_") as tmp:
        tmp = Path(tmp)
        nivel = args.nivel or (pacotes.ler_manifesto(args.origem)["nivel"] if args.origem else "publico")
        fonte = Fonte(nivel, args.carga, args.origem)
        man = json.loads(fonte.baixar(pacotes.MANIFESTO, tmp).read_text(encoding="utf-8"))
        if man["nivel"] != nivel or (args.carga and man["carga"] != args.carga):
            raise SystemExit(f"O pacote é do nível {man['nivel']}, carga {man['carga']}: não bate com o pedido.")
        camadas = [c.strip() for c in args.camadas.split(",") if c.strip()]
        possiveis = sorted({a["camada"] for a in man["artefatos"]})
        fora = [c for c in camadas if c not in possiveis]
        if fora:
            dica = " O gold público já vem no repositório (data/publico)." if nivel == "publico" else ""
            raise SystemExit(f"Camadas {fora} não existem no pacote {nivel} (tem: {possiveis}).{dica} Bronze, gold "
                             "completo e banco são dos dados da equipe (CONTRIBUTING.md).")
        artefatos = [a for a in man["artefatos"] if a["camada"] in camadas]
        # nada é baixado se algum destino já tiver dados e não houver --substituir
        ocupados = [a["destino"] for a in artefatos if a["camada"] != "banco" and tem_dados(args.raiz / a["destino"])]
        ocupados += [f"{a['destino']}/{f['caminho']}" for a in artefatos if a["camada"] == "banco"
                     for f in a["arquivos"] if (args.raiz / a["destino"] / f["caminho"]).exists()]
        if ocupados and not args.substituir:
            raise SystemExit(f"Já há dados locais em {ocupados}. Nada foi alterado. Use --substituir para trocar.")

        total = sum(p["bytes"] for a in artefatos for p in pacotes.arquivos_publicados(a))
        print(f"carga {man['carga']} · nível {nivel} · {len(artefatos)} artefatos · {total / 1e6:,.1f} MB")
        for a in artefatos:
            print(f"  {a['nome']}: baixando e conferindo ...", flush=True)
            for parte in pacotes.arquivos_publicados(a):
                fonte.baixar(parte["arquivo"], tmp)
            zip_ = pacotes.remontar(a, tmp)
            extr = tmp / f"extr_{a['nome']}"
            pacotes.extrair_conferindo(a, zip_, extr)
            zip_.unlink()
            destino = args.raiz / a["destino"]
            if a["camada"] != "banco" and tem_dados(destino):   # só chega aqui com --substituir
                shutil.rmtree(destino)
            for f in a["arquivos"]:   # arquivo por arquivo: os já conferidos, na mesma estrutura de pastas
                alvo = destino / f["caminho"]
                alvo.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(extr / f["caminho"]), str(alvo))
            print(f"     ok: {len(a['arquivos'])} arquivos conferidos em {a['destino']}")

    info = {"carga": man["carga"], "nivel": nivel, "camadas": camadas, "versao_premissas": man["versao_premissas"],
            "commit_da_carga": man.get("commit"), "instalado_em": dt.datetime.now().replace(microsecond=0).isoformat()}
    (args.raiz / "data").mkdir(exist_ok=True)
    (args.raiz / "data" / "carga_atual.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print("data/carga_atual.json atualizado. Próximo passo: uv run pipeline.py --a-partir-de "
          f"{'bronze' if 'bronze' in camadas else 'silver'} (ver README)." if "banco" not in camadas else
          "Banco instalado: uv run streamlit run app/Inicio.py")


if __name__ == "__main__":
    main()
