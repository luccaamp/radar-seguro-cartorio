"""Conjunto público de dados (D-029): lista de tabelas, hash de conteúdo, banco de demonstração e checagens LGPD.

- Hash do ARQUIVO (sha256 dos bytes): confere download e integridade.
- Hash de CONTEÚDO (sha256 das linhas ordenadas, sem os carimbos de execução): diz se dois bancos têm os mesmos
  números, mesmo que os Parquet tenham sido gravados em outra hora ou em outra ordem. É o que a prova
  "recalcular dá o mesmo resultado" compara.
"""
import hashlib
import json
import re
import tempfile
from pathlib import Path

import duckdb
import yaml

RAIZ = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((RAIZ / "config" / "publico.yaml").read_text(encoding="utf-8"))
PASTA = RAIZ / CONFIG["pasta"]
MANIFESTO = "manifesto.json"
CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def tabelas() -> dict[str, dict]:
    return {k: (v or {}) for k, v in CONFIG["tabelas"].items()}


def arquivo(tabela: str) -> str:
    return f"{tabela}.parquet"


def consulta_exportacao(tabela: str) -> str:
    """SQL que gera o conteúdo público de `tabela` (sem as colunas removidas)."""
    op = tabelas()[tabela]
    origem = f"({op['sql']})" if op.get("sql") else tabela
    remover = op.get("remover") or []
    return f"SELECT * EXCLUDE ({', '.join(remover)}) FROM {origem}" if remover else f"SELECT * FROM {origem}"


def hash_conteudo(con: duckdb.DuckDBPyConnection, relacao: str, sem_hash: list[str] | None = None) -> str:
    """sha256 das linhas ordenadas de `relacao` (tabela ou subconsulta entre parênteses), sem as colunas `sem_hash`."""
    exclui = f" EXCLUDE ({', '.join(sem_hash)})" if sem_hash else ""
    cur = con.execute(f"SELECT *{exclui} FROM {relacao} ORDER BY ALL")
    h = hashlib.sha256(json.dumps([d[0] for d in cur.description]).encode())
    while lote := cur.fetchmany(5000):
        for linha in lote:
            h.update(json.dumps(linha, default=str, ensure_ascii=False).encode())
    return h.hexdigest()


def hash_conteudo_tabela(con, tabela: str) -> str:
    """Hash de conteúdo da versão pública de `tabela` lida de um banco completo (com as colunas removidas)."""
    op = tabelas()[tabela]
    return hash_conteudo(con, f"({consulta_exportacao(tabela)})", op.get("sem_hash"))


def sha256_arquivo(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while bloco := f.read(1 << 20):
            h.update(bloco)
    return h.hexdigest()


def remover_pasta(p: Path, tentativas: int = 5) -> bool:
    """Apaga uma pasta com novas tentativas: o OneDrive segura pastas recém-alteradas por alguns segundos."""
    import shutil
    import time
    for _ in range(tentativas):
        shutil.rmtree(p, ignore_errors=True)
        if not p.exists():
            return True
        time.sleep(1)
    return False


def trocar_conteudo(novo: Path, destino: Path) -> None:
    """Põe em `destino` exatamente os arquivos de `novo` (já validados), arquivo por arquivo: renomear pastas falha
    quando a pasta está sincronizada pelo OneDrive. Apaga `novo` no fim."""
    import os
    destino.mkdir(parents=True, exist_ok=True)
    nomes = {p.name for p in novo.iterdir() if p.is_file()}
    for p in destino.iterdir():
        if p.is_file() and p.name not in nomes:
            p.unlink()
    for nome in sorted(nomes - {MANIFESTO}) + [MANIFESTO] if MANIFESTO in nomes else sorted(nomes):
        os.replace(novo / nome, destino / nome)   # manifesto por último: só aponta para arquivos já no lugar
    remover_pasta(novo)


def ler_manifesto(pasta: Path = PASTA) -> dict | None:
    m = pasta / MANIFESTO
    return json.loads(m.read_text(encoding="utf-8")) if m.exists() else None


def montar_banco(pasta: Path, destino: Path) -> Path:
    """Banco DuckDB a partir dos Parquet de `pasta` (um por schema.tabela, como no manifesto). Confere o hash de cada
    arquivo antes de carregar."""
    man = ler_manifesto(pasta)
    if not man:
        raise FileNotFoundError(f"sem {MANIFESTO} em {pasta}")
    destino.unlink(missing_ok=True)
    with duckdb.connect(str(destino)) as con:
        for a in man["arquivos"]:
            p = pasta / a["arquivo"]
            if sha256_arquivo(p) != a["sha256_arquivo"]:
                raise ValueError(f"{a['arquivo']}: hash diferente do manifesto (arquivo corrompido ou desatualizado)")
            esq, nome = a["tabela"].split(".")
            if esq == "estado" and nome == "premissas_vigente":
                esq, nome = "estado", "premissas_versoes"   # vira a tabela de estado que o painel lê
            con.execute(f"CREATE SCHEMA IF NOT EXISTS {esq}")
            con.execute(f"CREATE TABLE {esq}.{nome} AS SELECT * FROM read_parquet('{p.as_posix()}')")
        con.execute("CHECKPOINT")
    return destino


def banco_demonstracao(pasta: Path = PASTA) -> Path:
    """Banco temporário do modo demonstração, fora do repositório. Remontado só quando o manifesto muda."""
    man = ler_manifesto(pasta)
    chave = hashlib.sha256(json.dumps(man, sort_keys=True).encode()).hexdigest()[:12]
    destino = Path(tempfile.gettempdir()) / f"radar_demonstracao_{chave}.duckdb"
    if not destino.exists():
        temp = destino.with_name(destino.name + ".novo")
        montar_banco(pasta, temp)
        temp.replace(destino)
    return destino


def nomes_do_cadastro(con: duckdb.DuckDBPyConnection, bronze: Path) -> set[str]:
    """Nomes de responsáveis e substitutos no bronze do CNJ, só em memória, para procurar nos conjuntos a publicar.
    Vazio se o bronze não estiver na máquina."""
    nomes = set()
    for (a,) in con.execute("SELECT arquivo FROM silver.fonte_metadados WHERE fonte = 'cnj_serventias'").fetchall():
        p = bronze / a
        if not p.exists():
            continue
        dados = json.loads(p.read_text(encoding="utf-8"))
        for s in (dados.get("data") or dados.get("dados") if isinstance(dados, dict) else dados) or []:
            resp = s.get("responsavel")   # objeto {nome, data_ingresso, situacao_juridica_responsavel}
            candidatos = [resp.get("nome") if isinstance(resp, dict) else resp]
            candidatos += re.split(r"[;,]", str(s.get("substitutos") or ""))   # texto, às vezes com vários nomes
            for n in candidatos:
                n = str(n or "").strip().upper()
                if len(n) >= 10 and " " in n:
                    nomes.add(n)
    return nomes


COLUNAS_PESSOAIS = re.compile(r"(^|_)(cpf|email|e_mail|telefone|responsavel|substitutos?|titular|delegatario|endereco|"
                              r"cep|nome_pessoa|nascimento|pis|nis)($|_)", re.IGNORECASE)


def checar_sem_dado_pessoal(con: duckdb.DuckDBPyConnection, nomes: set[str] | None = None) -> list[str]:
    """Contrato de "sem dado pessoal" do pacote público do silver (D-030): nenhuma coluna de dado de pessoa, nenhum
    texto com formato de CPF ou e-mail e nenhum nome de responsável ou substituto do cadastro. O CNS da serventia é
    permitido (identifica o cartório, não uma pessoa)."""
    problemas = []
    for esq, nome in con.execute("SELECT table_schema, table_name FROM information_schema.tables ORDER BY 1, 2").fetchall():
        t = f"{esq}.{nome}"
        for c, tipo in con.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = ? "
                                   "AND table_name = ?", [esq, nome]).fetchall():
            if COLUNAS_PESSOAIS.search(c):
                problemas.append(f"{t}.{c}: coluna de dado pessoal")
            if tipo != "VARCHAR" or c in ("feature_json",):
                continue
            textos = [x for (x,) in con.execute(f'SELECT DISTINCT "{c}" FROM {t} WHERE "{c}" IS NOT NULL').fetchall()]
            if any(CPF.search(x) for x in textos):
                problemas.append(f"{t}.{c}: texto com formato de CPF")
            if any(EMAIL.search(x) for x in textos):
                problemas.append(f"{t}.{c}: texto com formato de e-mail")
            if nomes:
                achou = sum(1 for x in textos for n in nomes if n in x.upper())
                if achou:
                    problemas.append(f"{t}.{c}: {achou} ocorrências de nome de pessoa do cadastro")
    return problemas


def checar(con: duckdb.DuckDBPyConnection, limiar: int, cns: set[str] | None = None,
           nomes: set[str] | None = None) -> tuple[list[str], list[str]]:
    """Contratos de "sem dado pessoal" e de limiar sobre um banco montado só com o conjunto público.

    Devolve (problemas, exceções usadas). `cns` e `nomes` (opcionais, só na máquina de quem gera): códigos de serventia
    e nomes de pessoas do cadastro, procurados em todo texto do conjunto (nada é impresso, só contado)."""
    problemas, excecoes = [], []
    proibida = re.compile(CONFIG["colunas_proibidas"], re.IGNORECASE)
    contagens = set(CONFIG["contagem_de_serventias"])
    aprovadas = CONFIG.get("excecoes_limiar") or {}
    rel = con.execute("SELECT table_schema, table_name FROM information_schema.tables ORDER BY 1, 2").fetchall()
    for esq, nome in rel:
        t = f"{esq}.{nome}"
        if "interno_" in nome:
            problemas.append(f"{t}: tabela interna no conjunto público")
        cols = con.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = ? "
                           "AND table_name = ?", [esq, nome]).fetchall()
        for c, tipo in cols:
            if proibida.search(c):
                problemas.append(f"{t}.{c}: nome de coluna proibido no público")
            if c in contagens:
                n = con.execute(f'SELECT count(*) FROM {t} WHERE "{c}" > 0 AND "{c}" < ?', [limiar]).fetchone()[0]
                if n:
                    chave = f"{t}.{c}"
                    if chave in aprovadas:
                        excecoes.append(f"{chave}: {n} linhas entre 1 e {limiar - 1} ({aprovadas[chave].get('status')})")
                    else:
                        problemas.append(f"{chave}: {n} linhas com 1 a {limiar - 1} serventias (abaixo do limiar)")
            if tipo == "VARCHAR":
                textos = [x for (x,) in con.execute(f'SELECT DISTINCT "{c}" FROM {t} WHERE "{c}" IS NOT NULL').fetchall()]
                if c != "geometria" and any(CPF.search(x) for x in textos):
                    problemas.append(f"{t}.{c}: texto com formato de CPF")
                if any(EMAIL.search(x) for x in textos):
                    problemas.append(f"{t}.{c}: texto com formato de e-mail")
                if cns and any(x.strip() in cns for x in textos):
                    problemas.append(f"{t}.{c}: código CNS de serventia")
                if nomes and c != "geometria":
                    achou = sum(1 for x in textos for n in nomes if n in x.upper())
                    if achou:
                        problemas.append(f"{t}.{c}: {achou} ocorrências de nome de pessoa do cadastro")
            elif tipo in ("BIGINT", "INTEGER") and cns:
                valores = {str(x) for (x,) in con.execute(f'SELECT DISTINCT "{c}" FROM {t}').fetchall()}
                if c not in ("cod_ibge", "cod_ibge6") and len(valores & cns) > 5:
                    problemas.append(f"{t}.{c}: valores que coincidem com códigos CNS")
    return problemas, excecoes
