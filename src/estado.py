"""Estado do app no DuckDB (SPEC §2.1 e §2.4): versões das premissas, cenários salvos e log de decisões.

- `premissas_versoes`: a semente YAML entra como versão 1; o Simulador grava as seguintes com o diff.
- O app e o pipeline usam a versão vigente (a mais recente) e caem para a semente se o banco estiver vazio.
- `log_decisoes`: espelho de docs/decisoes.md, recarregado a cada execução do pipeline (fonte para o chat).
"""
import datetime as dt
import json
import re
from pathlib import Path

import duckdb
import yaml

RAIZ = Path(__file__).resolve().parents[1]
SEMENTE = RAIZ / "config" / "premissas" / "premissas_v001.yaml"
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


def garantir_tabelas(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("CREATE SCHEMA IF NOT EXISTS estado")
    con.execute("""CREATE TABLE IF NOT EXISTS estado.premissas_versoes (
        versao INTEGER PRIMARY KEY, criada_em TIMESTAMP, autor VARCHAR, origem VARCHAR,
        diff_json VARCHAR, conteudo_json VARCHAR)""")
    con.execute("""CREATE TABLE IF NOT EXISTS estado.cenarios_salvos (
        id INTEGER PRIMARY KEY, nome VARCHAR, criado_em TIMESTAMP, versao_premissas INTEGER,
        cenario_stf VARCHAR, regra_classe VARCHAR, metodo_rateio VARCHAR, nivel VARCHAR,
        ajustes_json VARCHAR, resultado_json VARCHAR)""")
    if con.execute("SELECT count(*) FROM estado.premissas_versoes").fetchone()[0] == 0:
        s = ler_semente()
        con.execute("INSERT INTO estado.premissas_versoes VALUES (?, now(), 'semente', ?, '{}', ?)",
                    [int(s["versao"]), f"config/premissas/{SEMENTE.name}", _json(s)])


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


def salvar_versao(con, conteudo: dict, diff: dict, autor: str, origem: str) -> int:
    nova = con.execute("SELECT coalesce(max(versao), 0) + 1 FROM estado.premissas_versoes").fetchone()[0]
    conteudo = {**conteudo, "versao": nova, "criada_em": dt.date.today().isoformat(), "origem": origem}
    con.execute("INSERT INTO estado.premissas_versoes VALUES (?, now(), ?, ?, ?, ?)",
                [nova, autor, origem, _json(diff), _json(conteudo)])
    return int(nova)


def salvar_cenario(con, nome: str, versao: int, cenario: str, regra: str, metodo: str, nivel: str,
                   ajustes: dict, resultado: dict) -> int:
    novo = con.execute("SELECT coalesce(max(id), 0) + 1 FROM estado.cenarios_salvos").fetchone()[0]
    con.execute("INSERT INTO estado.cenarios_salvos VALUES (?, ?, now(), ?, ?, ?, ?, ?, ?, ?)",
                [novo, nome, versao, cenario, regra, metodo, nivel, _json(ajustes), _json(resultado)])
    return int(novo)


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
