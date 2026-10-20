"""Empacota os dados de uma carga para os Releases do GitHub (D-030). Só gera arquivos locais em
C:\\radar_pacotes\\<nivel>\\ (fora do OneDrive; config/pacotes.yaml); quem publica é o autor (docs/publicacao.md).

  uv run python scripts/empacotar_dados.py --nivel publico     # silver + manifesto (Release público dados-<carga>)
  uv run python scripts/empacotar_dados.py --nivel equipe      # bronze oficial (enxuto), silver, gold completo, banco
                                                               # (Release privado carga-<carga>, sempre enxuto)
  uv run python scripts/empacotar_dados.py --nivel originais   # originais grandes, menos os .COMT (Release privado
                                                               # originais-<ano>, publicado uma vez; D-032)

--carga AAAA-MM-DD: confere que é a carga do banco atual (padrão: a data da carga em gold.execucao).
O pacote público só sai se o contrato de "sem dado pessoal" passar sobre o silver.
"""
import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import pacotes, publico  # noqa: E402
from src.transform.silver import BANCO, BRONZE, SILVER  # noqa: E402

DATA = RAIZ / "data"


def commit() -> dict:
    def git(*a):
        r = subprocess.run(["git", "-C", str(RAIZ), *a], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    return {"commit": git("rev-parse", "HEAD"), "alteracoes_sem_commit": bool(git("status", "--porcelain"))}


def artefato(camada: str, nome: str, origem: Path, arquivos: list[Path], destino_rel: str, saida: Path, carga: str,
             excluidos: list[dict] | None = None) -> dict:
    zip_ = saida / f"{nome}-{carga}.zip"
    print(f"  {nome}: {len(arquivos)} arquivos, {sum(p.stat().st_size for p in arquivos) / 1e6:,.1f} MB ...", flush=True)
    lista = pacotes.zipar(origem, arquivos, zip_)
    a = {"camada": camada, "nome": nome, "zip": zip_.name, "bytes_zip": zip_.stat().st_size,
         "sha256_zip": pacotes.sha256(zip_), "destino": destino_rel, "arquivos": lista, "excluidos": excluidos or []}
    a["partes"] = pacotes.dividir(zip_)
    print(f"     zip {a['bytes_zip'] / 1e6:,.1f} MB" + (f" em {len(a['partes'])} partes" if a["partes"] else ""))
    return a


def silver_sem_dado_pessoal(con) -> None:
    """[VERIFICAR] da seção 2.5: o pacote público só sai se o contrato de 'sem dado pessoal' passar sobre o silver."""
    nomes = publico.nomes_do_cadastro(con, BRONZE)
    with tempfile.TemporaryDirectory() as tmp:
        with duckdb.connect(str(Path(tmp) / "conferencia.duckdb")) as s:   # nome do arquivo != nome do schema
            s.execute("CREATE SCHEMA silver")
            for p in sorted(SILVER.glob("*.parquet")):
                s.execute(f"CREATE TABLE silver.{p.stem} AS SELECT * FROM read_parquet('{p.as_posix()}')")
            problemas = publico.checar_sem_dado_pessoal(s, nomes)
    print(f"  contrato 'sem dado pessoal' no silver: {len(problemas)} problemas ({len(nomes)} nomes do cadastro procurados)")
    if problemas:
        raise SystemExit("Pacote público bloqueado:\n  " + "\n  ".join(problemas))


def silver_publico(pasta: Path) -> tuple[list[Path], list[str]]:
    """Silver do pacote público (D-030, D-031): os Parquet do silver sem nenhuma coluna de estimativa do modelo
    (config/publico.yaml, estimativas_do_modelo) e sem as colunas de silver_publico_remover. Devolve os arquivos e as
    colunas retiradas (tabela.coluna)."""
    padrao = re.compile(publico.CONFIG["estimativas_do_modelo"], re.IGNORECASE)
    remover = publico.CONFIG.get("silver_publico_remover") or {}   # D-031: colunas que o pipeline não usa
    pasta.mkdir(parents=True)
    arquivos, retiradas = [], []
    with duckdb.connect() as con:
        for p in sorted(SILVER.glob("*.parquet")):
            cols = [c for (c,) in con.execute(f"SELECT name FROM parquet_schema('{p.as_posix()}') WHERE name <> 'duckdb_schema'").fetchall()]
            fora = [c for c in cols if padrao.search(c) or c in remover.get(p.stem, [])]
            retiradas += [f"silver.{p.stem}.{c}" for c in fora]
            destino = pasta / p.name
            if fora:
                excl = ", ".join(f'"{c}"' for c in fora)
                con.execute(f"COPY (SELECT * EXCLUDE ({excl}) FROM read_parquet('{p.as_posix()}')) TO "
                            f"'{destino.as_posix()}' (FORMAT parquet)")
            else:
                shutil.copy2(p, destino)
            arquivos.append(destino)
    return arquivos, retiradas


def gold_completo(con, pasta: Path) -> list[Path]:
    """Todas as tabelas do gold (inclusive interno_*) em Parquet, exportadas do banco."""
    pasta.mkdir(parents=True)
    out = []
    for (t,) in con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'gold' "
                            "ORDER BY 1").fetchall():
        p = pasta / f"{t}.parquet"
        con.execute(f"COPY gold.{t} TO '{p.as_posix()}' (FORMAT parquet)")
        out.append(p)
    return out


def empacotar_originais(args) -> None:
    """Release próprio dos originais grandes (D-032), publicado uma vez: tudo da pasta de originais, menos o que
    config/pacotes.yaml (originais_excluir) deixa de fora. O manifesto guarda os registros original.json do bronze, para
    conferir que os originais são os da carga."""
    ano = args.ano
    if not ano:
        if not BANCO.exists():
            raise SystemExit("Informe --ano (não há banco para ler o ano da carga).")
        with duckdb.connect(str(BANCO), read_only=True) as con:
            ano = f"{con.sql('SELECT max(executado_em) FROM gold.execucao').fetchone()[0]:%Y}"
    orig = pacotes.pasta("originais")
    saida = args.saida or pacotes.pasta("pacotes") / "originais"
    saida.mkdir(parents=True, exist_ok=True)
    for p in saida.iterdir():
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    print(f"empacotando originais ({orig}), tag {pacotes.tag('originais', ano)} -> {saida}")
    regras = pacotes.CONFIG.get("originais_excluir") or []
    artefatos = []
    for fonte in sorted(p for p in orig.iterdir() if p.is_dir()):
        todos = sorted(p for p in fonte.rglob("*") if p.is_file())
        excl = {}
        fica = []
        for p in todos:
            r = pacotes.excluido(p.relative_to(orig).as_posix(), regras)
            if r:
                e = excl.setdefault(r["padrao"], {"padrao": r["padrao"], "motivo": r["motivo"], "n": 0, "bytes": 0,
                                                  "arquivos": []})
                e["n"] += 1
                e["bytes"] += p.stat().st_size
                e["arquivos"].append(p.relative_to(orig).as_posix())
            else:
                fica.append(p)
        if fica:
            artefatos.append(artefato("originais", f"originais-{fonte.name}", fonte, fica,
                                      f"{pacotes.DESTINO_ORIGINAIS}/{fonte.name}", saida, ano, list(excl.values())))
    registros = {p.parent.relative_to(BRONZE).as_posix(): json.loads(p.read_text(encoding="utf-8"))["arquivos"]
                 for p in sorted(BRONZE.rglob("original.json"))}
    man = {"nivel": "originais", "carga": ano, "ano": ano, "tag": pacotes.tag("originais", ano),
           "repositorio": pacotes.CONFIG["repositorios"]["originais"], **commit(),
           "gerado_em": dt.datetime.now().replace(microsecond=0).isoformat(),
           "registros_original_json": registros, "artefatos": artefatos}
    (saida / pacotes.MANIFESTO).write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    n_orig = sum(len(a["arquivos"]) for a in artefatos)
    b_orig = sum(f["bytes"] for a in artefatos for f in a["arquivos"])
    pub = [f for a in artefatos for f in pacotes.arquivos_publicados(a)]
    fora = [e for a in artefatos for e in a["excluidos"]]
    print(f"\n  originais no pacote: {n_orig} arquivos, {b_orig / 1e6:,.1f} MB -> {len(pub)} arquivos publicados, "
          f"{sum(f['bytes'] for f in pub) / 1e6:,.1f} MB + manifesto.json (Release {man['tag']} em {man['repositorio']})")
    for e in fora:
        print(f"  fora do pacote: {e['n']} arquivos, {e['bytes'] / 1e6:,.1f} MB ({e['padrao']}): {e['arquivos']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nivel", choices=["publico", "equipe", "originais"], required=True,
                    help="publico (dados-<carga>), equipe (carga-<carga>, sempre enxuto) ou originais (originais-<ano>, "
                         "Release próprio, publicado uma vez; D-032)")
    ap.add_argument("--carga", help="AAAA-MM-DD (padrão: a carga do banco atual)")
    ap.add_argument("--ano", help="só no nível originais: o ano da tag originais-<ano> (padrão: o ano da carga atual)")
    ap.add_argument("--saida", type=Path, help="pasta de saída (padrão: C:\\radar_pacotes\\<nivel>, fora do OneDrive; "
                                               "config/pacotes.yaml)")
    args = ap.parse_args()
    if args.nivel == "originais":
        empacotar_originais(args)
        return
    if not BANCO.exists():
        raise SystemExit("Banco completo não encontrado (data/radar.duckdb).")
    saida = args.saida or pacotes.pasta("pacotes") / args.nivel   # fora do OneDrive (config/pacotes.yaml)
    with duckdb.connect(str(BANCO), read_only=True) as con:
        exe = con.sql("SELECT * FROM gold.execucao").df()
        carga_banco = f"{exe['executado_em'].iloc[0]:%Y-%m-%d}"
        carga = args.carga or carga_banco
        if carga != carga_banco:
            raise SystemExit(f"--carga {carga} diferente da carga do banco atual ({carga_banco}).")
        fontes = con.sql("SELECT fonte, data_referencia, coletado_em FROM silver.fonte_metadados ORDER BY fonte").df()
        if args.nivel == "publico":
            silver_sem_dado_pessoal(con)
        saida.mkdir(parents=True, exist_ok=True)
        for p in saida.iterdir():   # esvazia a pasta de saída sem apagá-la (o OneDrive segura pastas)
            shutil.rmtree(p) if p.is_dir() else p.unlink()
        print(f"empacotando nível {args.nivel}, carga {carga} -> {saida}")
        artefatos = []
        camadas = pacotes.CONFIG["camadas"][args.nivel]
        if "bronze" in camadas:
            regras = pacotes.CONFIG["bronze_excluir"]
            for fonte in sorted(p for p in BRONZE.iterdir() if p.is_dir()):
                todos = sorted(p for p in fonte.rglob("*") if p.is_file())
                fora = [(p, pacotes.excluido(p.relative_to(BRONZE).as_posix(), regras)) for p in todos]
                excl = {}
                for p, r in fora:
                    if r:
                        e = excl.setdefault(r["padrao"], {"padrao": r["padrao"], "motivo": r["motivo"], "n": 0, "bytes": 0})
                        e["n"] += 1
                        e["bytes"] += p.stat().st_size
                artefatos.append(artefato("bronze", f"bronze-{fonte.name}", fonte, [p for p, r in fora if not r],
                                          f"data/bronze/{fonte.name}", saida, carga, list(excl.values())))
        retiradas = []
        if "silver" in camadas and args.nivel == "publico":
            with tempfile.TemporaryDirectory() as tmp:
                pasta = Path(tmp) / "silver"
                arquivos, retiradas = silver_publico(pasta)
                print(f"  colunas retiradas do silver público (estimativas do modelo e D-031): {retiradas or 'nenhuma'}")
                artefatos.append(artefato("silver", "silver", pasta, arquivos, "data/silver", saida, carga))
        elif "silver" in camadas:
            artefatos.append(artefato("silver", "silver", SILVER, sorted(SILVER.glob("*.parquet")), "data/silver",
                                      saida, carga))
        if "gold" in camadas:
            with tempfile.TemporaryDirectory() as tmp:
                pasta = Path(tmp) / "gold"
                artefatos.append(artefato("gold", "gold", pasta, gold_completo(con, pasta), "data/gold", saida, carga))
    if "banco" in camadas:   # depois de fechar a conexão de leitura
        artefatos.append(artefato("banco", "banco", DATA, [BANCO], "data", saida, carga))

    man = {"nivel": args.nivel, "carga": carga, "tag": pacotes.tag(args.nivel, carga),
           "repositorio": pacotes.CONFIG["repositorios"][args.nivel],
           "executado_em": f"{exe['executado_em'].iloc[0]:%Y-%m-%dT%H:%M:%S}",
           "versao_premissas": int(exe["versao_premissas"].iloc[0]), **commit(),
           "gerado_em": dt.datetime.now().replace(microsecond=0).isoformat(),
           "fontes": json.loads(fontes.to_json(orient="records", force_ascii=False)),
           "colunas_retiradas_do_publico": retiradas, "artefatos": artefatos}
    (saida / pacotes.MANIFESTO).write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nTamanhos por camada (originais -> publicados):")
    for camada in camadas:
        a = [x for x in artefatos if x["camada"] == camada]
        orig = sum(f["bytes"] for x in a for f in x["arquivos"])
        pub = sum(f["bytes"] for x in a for f in pacotes.arquivos_publicados(x))
        print(f"  {camada:7} {orig / 1e6:12,.1f} MB -> {pub / 1e6:12,.1f} MB")
    total = sum(f["bytes"] for x in artefatos for f in pacotes.arquivos_publicados(x))
    n = sum(len(pacotes.arquivos_publicados(x)) for x in artefatos)
    print(f"  total do pacote: {total / 1e6:,.1f} MB em {n} arquivos + manifesto.json (Release {man['tag']} em "
          f"{man['repositorio']})")


if __name__ == "__main__":
    main()
