"""Estado no DuckDB do pipeline (SPEC §2.1 e §2.4): versões das premissas e log de decisões. Só o pipeline grava.

- `premissas_versoes`: cada semente YAML entra como uma versão (v001, v002...). Desde a D-034, o painel não cria
  versão: os cenários salvos (com o diff sobre a versão vigente) ficam em data/painel_estado.json (src/cenarios.py).
- O app e o pipeline usam a versão vigente (a mais recente) e caem para a semente se o banco estiver vazio.
- `cenarios_salvos`: tabela antiga, que o pipeline não cria nem copia mais (D-034); some do banco na próxima carga.
- `log_decisoes`: espelho de docs/decisoes.md, recarregado a cada execução do pipeline (fonte para o chat).
"""
import datetime as dt
import json
import re
from pathlib import Path

import duckdb
import yaml

RAIZ = Path(__file__).resolve().parents[1]
SEMENTE = RAIZ / "config" / "premissas" / "premissas_v002.yaml"   # v001 continua no lugar para comparação (D-020)
DECISOES = RAIZ / "docs" / "decisoes.md"


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, default=lambda o: o.isoformat() if hasattr(o, "isoformat") else str(o))


def _de_json(texto: str) -> dict:
    d = json.loads(texto)
    pos = d["premissas"].get("data_posicao", {})
    if isinstance(pos.get("valor"), str):
        pos["valor"] = dt.date.fromisoformat(pos["valor"])
    return d


def ler_semente() -> dict:
    return yaml.safe_load(SEMENTE.read_text(encoding="utf-8"))


TABELAS_ESTADO = ("premissas_versoes",)   # preservado entre cargas (1.7); cenarios_salvos saiu (D-034)


def criar_tabelas(con: duckdb.DuckDBPyConnection) -> None:
    """Só a estrutura das tabelas de estado (com as chaves), sem registrar a semente."""
    con.execute("CREATE SCHEMA IF NOT EXISTS estado")
    con.execute("""CREATE TABLE IF NOT EXISTS estado.premissas_versoes (
        versao INTEGER PRIMARY KEY, criada_em TIMESTAMP, autor VARCHAR, origem VARCHAR,
        diff_json VARCHAR, conteudo_json VARCHAR)""")


def garantir_tabelas(con: duckdb.DuckDBPyConnection) -> None:
    criar_tabelas(con)
    # a semente atual entra como versão própria se ainda não estiver no banco (ex.: v002 depois da v001)
    s = ler_semente()
    origem = f"config/premissas/{SEMENTE.name}"
    if con.execute("SELECT count(*) FROM estado.premissas_versoes WHERE origem = ?", [origem]).fetchone()[0] == 0:
        ocupada = con.execute("SELECT origem FROM estado.premissas_versoes WHERE versao = ?", [int(s["versao"])]).fetchone()
        if ocupada:
            raise RuntimeError(f"versão {s['versao']} já usada por '{ocupada[0]}'; renumere a semente {SEMENTE.name}")
        con.execute("INSERT INTO estado.premissas_versoes VALUES (?, now(), 'semente', ?, '{}', ?)",
                    [int(s["versao"]), origem, _json(s)])


def premissas_vigentes(con: duckdb.DuckDBPyConnection) -> tuple[dict, int]:
    """Conteúdo e número da versão mais recente; a semente, se a tabela não existir ou estiver vazia."""
    try:
        linha = con.execute("SELECT versao, conteudo_json FROM estado.premissas_versoes "
                            "ORDER BY versao DESC LIMIT 1").fetchone()
    except duckdb.CatalogException:
        linha = None
    if not linha:
        s = ler_semente()
        return s, int(s["versao"])
    return _de_json(linha[1]), int(linha[0])


def carregar_log_decisoes(con: duckdb.DuckDBPyConnection) -> int:
    """Lê as seções '## D-NNN — título' de docs/decisoes.md para estado.log_decisoes."""
    texto = DECISOES.read_text(encoding="utf-8")
    partes = re.split(r"(?m)^## (D-\d{3}) — (.+)$", texto)
    linhas = []
    for i in range(1, len(partes), 3):
        corpo = partes[i + 2].split("\n---")[0].strip()
        data = re.search(r"\*\*Data:\*\*\s*(\d{4}-\d{2}-\d{2})", corpo)
        linhas.append((partes[i], partes[i + 1].strip(), data.group(1) if data else None, corpo))
    con.execute("CREATE OR REPLACE TABLE estado.log_decisoes (id VARCHAR, titulo VARCHAR, data VARCHAR, texto VARCHAR)")
    con.executemany("INSERT INTO estado.log_decisoes VALUES (?, ?, ?, ?)", linhas)
    return len(linhas)
