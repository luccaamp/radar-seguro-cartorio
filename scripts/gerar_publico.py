"""Gera o conjunto público (data/publico/, versionado no repositório público; D-029).

Passos (qualquer falha interrompe e não troca a pasta atual):
1. exporta as tabelas de config/publico.yaml (sem as colunas removidas) para Parquet;
2. monta um banco só com esses Parquet e roda os contratos de "sem dado pessoal", procurando também os códigos CNS
   fora das tabelas por serventia e os nomes de pessoas do cadastro (nada disso é impresso; só contado);
3. confere que o hash de conteúdo do Parquet é igual ao do banco e que o total fica abaixo do limite de tamanho;
4. grava manifesto.json (fontes, carga, premissas, commit, hash e tamanho de cada arquivo) e troca a pasta.
Sem auditor de ataque por diferença nem limiar de serventias desde a D-078 (D-038, fase 2).

Uso: uv run python scripts/gerar_publico.py [--banco CÓPIA --destino PASTA]   (as opções: conferir numa cópia)
Lê data/radar.duckdb só para leitura. Precisa do banco completo (com interno_*), que só existe em quem roda o pipeline.
"""
import datetime as dt
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import duckdb
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import publico  # noqa: E402
from src.transform.silver import BANCO, BRONZE  # noqa: E402


def commit_atual() -> dict:
    def git(*a):
        r = subprocess.run(["git", "-C", str(RAIZ), *a], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    return {"commit": git("rev-parse", "HEAD"), "alteracoes_sem_commit": bool(git("status", "--porcelain"))}


def main(banco: Path = BANCO, destino: Path = publico.PASTA) -> None:
    """`banco` e `destino` mudam só para conferir numa cópia (a IA não lê o banco real; CLAUDE.md)."""
    if not banco.exists():
        raise SystemExit(f"Banco completo não encontrado ({banco}). Rode o pipeline antes.")
    novo = destino.with_name(destino.name + ".novo")
    publico.remover_pasta(novo)
    novo.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(banco), read_only=True) as con:
        cns = {str(x) for (x,) in con.execute("SELECT cns FROM silver.serventia").fetchall()}
        nomes = publico.nomes_do_cadastro(con, BRONZE)
        print(f"procurando {len(cns)} códigos CNS e {len(nomes)} nomes do cadastro no conjunto público")
        arquivos = []
        for tabela, op in publico.tabelas().items():
            p = novo / publico.arquivo(tabela)
            con.execute(f"COPY ({publico.consulta_exportacao(tabela)}) TO '{p.as_posix()}' (FORMAT parquet)")
            arquivos.append({"tabela": tabela, "arquivo": p.name, "comparar": op.get("comparar", True),
                             "sem_hash": op.get("sem_hash") or [],
                             "linhas": con.execute(f"SELECT count(*) FROM ({publico.consulta_exportacao(tabela)})").fetchone()[0],
                             "sha256_conteudo": publico.hash_conteudo_tabela(con, tabela)})
        exe = con.sql("SELECT * FROM gold.execucao").df()
        fontes = con.sql("SELECT fonte, data_referencia, coletado_em, sha256 AS sha256_bronze, url "
                         "FROM silver.fonte_metadados ORDER BY fonte").df()

    for a in arquivos:
        p = novo / a["arquivo"]
        a["bytes"] = p.stat().st_size
        a["sha256_arquivo"] = publico.sha256_arquivo(p)
    executado = pd.Timestamp(exe["executado_em"].iloc[0])
    man = {"descricao": "Conjunto público do Radar Seguro-Garantia Cartórios (D-029, D-038, D-048): as tabelas que o "
                        "painel lê e o resultado do modelo por serventia (identificada pelo CNS e pelo município). "
                        "Sem dado de pessoa física.",
           "carga": executado.strftime("%Y-%m-%d"), "executado_em": executado.isoformat(),
           "versao_premissas": int(exe["versao_premissas"].iloc[0]),
           **commit_atual(), "gerado_em": dt.datetime.now().replace(microsecond=0).isoformat(),
           "fontes": json.loads(fontes.to_json(orient="records", force_ascii=False)),
           "arquivos": arquivos}

    # contratos sobre um banco montado só com o conjunto público, e conferência dos hashes
    (novo / publico.MANIFESTO).write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        banco = publico.montar_banco(novo, Path(tmp) / "publico.duckdb")
        with duckdb.connect(str(banco), read_only=True) as con:
            problemas = publico.checar(con, cns, nomes)
            for a in arquivos:
                esq, nome = a["tabela"].split(".")
                rel = "estado.premissas_versoes" if a["tabela"] == "estado.premissas_vigente" else a["tabela"]
                if publico.hash_conteudo(con, rel, a["sem_hash"]) != a["sha256_conteudo"]:
                    problemas.append(f"{a['tabela']}: conteúdo do Parquet diferente do banco")
    total = sum(a["bytes"] for a in arquivos)
    if total > publico.CONFIG["limite_mb"] * 1e6:
        problemas.append(f"conjunto com {total / 1e6:.1f} MB (limite {publico.CONFIG['limite_mb']} MB)")
    if problemas:
        publico.remover_pasta(novo)
        raise SystemExit("Publicação bloqueada:\n  " + "\n  ".join(problemas))
    publico.trocar_conteudo(novo, destino)   # só depois de tudo validado
    print("contratos de 'sem dado pessoal': ok")
    onde = destino.relative_to(RAIZ) if destino.is_relative_to(RAIZ) else destino
    print(f"{len(arquivos)} arquivos, {total / 1e6:.2f} MB em {onde} · carga {man['carga']} · "
          f"commit {str(man['commit'])[:7]}{' + alterações sem commit' if man['alteracoes_sem_commit'] else ''}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    sys.stderr.reconfigure(encoding="utf-8")
    import argparse
    a = argparse.ArgumentParser(prog="uv run python scripts/gerar_publico.py")
    a.add_argument("--banco", type=Path, default=BANCO, help="banco completo (padrão: data/radar.duckdb)")
    a.add_argument("--destino", type=Path, default=publico.PASTA, help="pasta do conjunto (padrão: data/publico)")
    args = a.parse_args()
    main(args.banco.resolve(), args.destino.resolve())
