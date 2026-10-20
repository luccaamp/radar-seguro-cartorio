"""Gera o conjunto público (data/publico/, versionado no repositório público; D-029).

Passos (qualquer falha interrompe e não troca a pasta atual):
1. auditor de ataque por diferença sobre TODAS as células publicadas (gold.interno_celulas_publicadas);
2. exporta as tabelas de config/publico.yaml (sem as colunas removidas) para Parquet;
3. monta um banco só com esses Parquet e roda os contratos de "sem dado pessoal" e de limiar, procurando também
   os códigos CNS e os nomes de pessoas do cadastro (nada disso é impresso; só contado);
4. confere que o hash de conteúdo do Parquet é igual ao do banco e que o total fica abaixo do limite de tamanho;
5. grava manifesto.json (fontes, carga, premissas, commit, hash e tamanho de cada arquivo) e troca a pasta.

Uso: uv run python scripts/gerar_publico.py
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
from src.model.supressao import Celula  # noqa: E402
from src.transform import visoes  # noqa: E402
from src.transform.silver import BANCO, BRONZE  # noqa: E402


def commit_atual() -> dict:
    def git(*a):
        r = subprocess.run(["git", "-C", str(RAIZ), *a], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    return {"commit": git("rev-parse", "HEAD"), "alteracoes_sem_commit": bool(git("status", "--porcelain"))}


def auditar(con) -> list:
    """Auditor de ataque por diferença sobre as células publicadas (Mercado + Simulador)."""
    cel = con.sql("SELECT visao, area_id, conjunto, cns FROM gold.interno_celulas_publicadas").df()
    celulas = [Celula(v, a, frozenset(g.loc[g["conjunto"] == "todos", "cns"]),
                      frozenset(g.loc[g["conjunto"] == "universo", "cns"])) for (v, a), g in cel.groupby(["visao", "area_id"])]
    base = con.sql("""SELECT s.cns, m.regiao_imediata FROM gold.interno_dim_serventia s
                      JOIN silver.municipio_ibge m USING (cod_ibge)""").df()
    limiar = int(con.execute("SELECT max(limiar_lgpd) FROM gold.execucao").fetchone()[0])
    return visoes.auditar(celulas, base, limiar), len(celulas)


def main() -> None:
    if not BANCO.exists():
        raise SystemExit("Banco completo não encontrado (data/radar.duckdb). Rode o pipeline antes.")
    destino = publico.PASTA
    novo = destino.with_name(destino.name + ".novo")
    publico.remover_pasta(novo)
    novo.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(BANCO), read_only=True) as con:
        achados, n_cel = auditar(con)
        print(f"auditor de ataque por diferença: {n_cel} células, {len(achados)} vazamentos")
        if achados:
            raise SystemExit(f"Publicação bloqueada: vazamento por diferença {achados[:5]}")
        limiar = int(con.execute("SELECT max(limiar_lgpd) FROM gold.execucao").fetchone()[0])
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
    man = {"descricao": "Conjunto público do Radar Seguro-Garantia Cartórios (D-029): tabelas agregadas e auditadas "
                        "que o painel lê. Sem dado por serventia e sem dado pessoal.",
           "carga": executado.strftime("%Y-%m-%d"), "executado_em": executado.isoformat(),
           "versao_premissas": int(exe["versao_premissas"].iloc[0]), "limiar_lgpd": limiar,
           **commit_atual(), "gerado_em": dt.datetime.now().replace(microsecond=0).isoformat(),
           "fontes": json.loads(fontes.to_json(orient="records", force_ascii=False)),
           "excecoes_limiar": {}, "arquivos": arquivos}

    # contratos sobre um banco montado só com o conjunto público, e conferência dos hashes
    (novo / publico.MANIFESTO).write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        banco = publico.montar_banco(novo, Path(tmp) / "publico.duckdb")
        with duckdb.connect(str(banco), read_only=True) as con:
            problemas, excecoes = publico.checar(con, limiar, cns, nomes)
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
    man["excecoes_limiar"] = {e.split(":")[0]: e for e in excecoes}
    (novo / publico.MANIFESTO).write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    publico.trocar_conteudo(novo, destino)   # só depois de tudo validado
    print(f"contratos de 'sem dado pessoal' e de limiar: ok ({len(excecoes)} exceções: {excecoes})")
    print(f"{len(arquivos)} arquivos, {total / 1e6:.2f} MB em {destino.relative_to(RAIZ)} · carga {man['carga']} · "
          f"commit {str(man['commit'])[:7]}{' + alterações sem commit' if man['alteracoes_sem_commit'] else ''}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    sys.stderr.reconfigure(encoding="utf-8")
    main()
