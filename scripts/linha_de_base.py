"""Linha de base antes de uma limpeza ou mudança grande (só leitura): o que existe e os números, para comparar depois.

Registra:
- TODOS os arquivos de data/ (caminho, tamanho, data de modificação e SHA-256), inclusive os soltos na raiz de
  data/ (ex.: carga_atual.json). A versão de 2026-10-19 registrava só gold, silver, publico e o banco, e por isso
  não provava a ausência de um arquivo solto (docs/erros_ia.md, 2026-10-20);
- o hash de conteúdo de todas as tabelas do gold (inclusive interno_*: aqui ficam só hashes) e das tabelas públicas;
- os 10 números de referência, lidos do banco;
- o tamanho de cada pasta do projeto.

Grave fora do OneDrive e fora do repositório (os hashes do gold interno não vão para o git):
  uv run python scripts/linha_de_base.py C:\\radar_arquivo\\baseline
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import publico  # noqa: E402


def tamanho(p: Path) -> int:
    total = 0
    for d, _, fs in os.walk(p):
        for f in fs:
            try:
                total += (Path(d) / f).stat().st_size
            except OSError:
                pass
    return total


def arquivos_de_data(data: Path) -> dict[str, dict]:
    """Todo arquivo de data/, em qualquer nível, com tamanho, data de modificação e SHA-256."""
    out = {}
    for p in sorted(x for x in data.rglob("*") if x.is_file()):
        st = p.stat()
        out[p.relative_to(data).as_posix()] = {
            "bytes": st.st_size, "modificado": dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            "sha256": publico.sha256_arquivo(p)}
    return out


def main(saida: Path) -> None:
    saida.mkdir(parents=True, exist_ok=True)
    data = RAIZ / "data"
    base = {"gerado_em": dt.datetime.now().replace(microsecond=0).isoformat(), "projeto": str(RAIZ),
            "arquivos_data": arquivos_de_data(data)}
    banco = data / "radar.duckdb"
    if banco.exists():
        with duckdb.connect(str(banco), read_only=True) as con:
            tabs = [t for (t,) in con.execute("SELECT table_name FROM information_schema.tables "
                                              "WHERE table_schema = 'gold' ORDER BY 1").fetchall()]
            base["hash_conteudo_gold"] = {f"gold.{t}": publico.hash_conteudo(
                con, f"gold.{t}", ["executado_em"] if t == "execucao" else None) for t in tabs}
            base["hash_conteudo_publico"] = {t: publico.hash_conteudo_tabela(con, t) for t in publico.tabelas()}
            r = con.sql("SELECT * FROM gold.fato_mercado_uf WHERE nivel = 'base' AND regra_classe = 'v2' "
                        "AND cenario_stf = 'mantem'").df().iloc[0]
            taxa = json.loads(con.execute("SELECT conteudo_json FROM estado.premissas_versoes ORDER BY versao DESC "
                                          "LIMIT 1").fetchone()[0])["premissas"]["taxa_seguro_anual"]["valores"]["base"]
            base["numeros_referencia"] = {
                "serventias_ativas": int(r.n_serventias_ativas), "clt": float(r.clt), "obrigadas": float(r.n_universo),
                "passivo_todas": float(r.passivo_todas), "passivo_obrigadas": float(r.passivo_universo),
                "com_deficit": float(r.n_deficit), "deficit": float(r.valor_descoberto),
                "is_mercado": float(r.mercado_importancia_segurada), "premio_mercado": float(r.mercado_premio_emitido),
                "teto": float(r.passivo_universo * taxa)}
    base["tamanhos_mb"] = {p.name: round(tamanho(p) / 1e6, 2) for p in sorted(RAIZ.iterdir()) if p.is_dir()}
    base["tamanhos_data_mb"] = {p.name: round(tamanho(p) / 1e6, 2) for p in sorted(data.iterdir()) if p.is_dir()}
    (saida / "linha_de_base.json").write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
    soltos = [a for a in base["arquivos_data"] if "/" not in a]
    print(f"{len(base['arquivos_data'])} arquivos em data/ ({len(soltos)} soltos na raiz: {soltos}); "
          f"gold: {len(base.get('hash_conteudo_gold', {}))} tabelas -> {saida / 'linha_de_base.json'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    sys.stderr.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        raise SystemExit("Uso: uv run python scripts/linha_de_base.py <pasta de saída, fora do OneDrive>")
    main(Path(sys.argv[1]))
