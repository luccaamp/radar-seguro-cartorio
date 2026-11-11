"""Servidor MCP do Radar (Model Context Protocol): as mesmas 5 ferramentas do chat do painel, para qualquer cliente
MCP (Claude Desktop, Claude Code, IDEs) consultar os números do projeto com a fonte, sem calcular nada por conta própria.

- As ferramentas são as do chat (`src/agent/ferramentas.py`): mesmos nomes, descrições e esquemas de parâmetros, e o
  mesmo resultado que o Gemini recebe (`para_o_modelo`: valores já formatados em pt-BR e a linha `citar` com a fonte).
- Lê só o conjunto público versionado (`data/publico`, sem dado de pessoa física, D-038), por um banco de
  demonstração só de leitura montado fora do repositório. Nunca o banco real, nunca SQL livre.
- Transporte stdio, JSON-RPC 2.0, uma mensagem por linha (especificação MCP 2025-06-18). Implementado aqui, sem
  dependência nova: só `initialize`, `ping`, `tools/list` e `tools/call` (e as notificações, que não têm resposta).

Uso (de um clone, sem chave nem internet):
  uv run python -m src.agent.servidor_mcp
No Claude Code:  claude mcp add radar -- uv run --directory <pasta do clone> python -m src.agent.servidor_mcp
Testes: tests/test_servidor_mcp.py (sobe o servidor como processo e conversa com ele pelo protocolo).
"""
import json
import sys
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:   # rodado como script de outra pasta
    sys.path.insert(0, str(RAIZ))

from src import publico  # noqa: E402
from src.agent import ferramentas  # noqa: E402

VERSAO_PROTOCOLO = "2025-06-18"
SERVIDOR = {"name": "radar-seguro-cartorio", "title": "Radar Seguro-Garantia Cartórios", "version": "1.0.0"}
INSTRUCOES = ("Números do Radar Seguro-Garantia Cartórios (Minas Gerais, dados públicos do CNJ, RAIS e IBGE). Use as "
              "ferramentas em vez de estimar: cada resultado traz os valores já formatados e a linha `citar` com a "
              "fonte, a carga e a versão das premissas; cite-a. Cartório só pelo CNS e pelo município.")

# códigos de erro do JSON-RPC 2.0
ERRO_PARSE, ERRO_PEDIDO, ERRO_METODO, ERRO_PARAMETROS = -32700, -32600, -32601, -32602


def ferramentas_mcp() -> list[dict]:
    """As 5 ferramentas do chat no formato do MCP (o esquema do Gemini vira o `inputSchema`). Só leitura."""
    return [{"name": e["name"], "title": e["name"].replace("_", " ").capitalize(), "description": e["description"],
             "inputSchema": e["parameters"],
             "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}}
            for e in ferramentas.ESQUEMAS]


def chamar(con: duckdb.DuckDBPyConnection, nome: str, argumentos: dict | None) -> dict:
    """Resultado de `tools/call`: o JSON que o chat do painel manda ao modelo, como texto e como conteúdo estruturado.
    Erro da consulta (ferramenta ou análise inexistente, parâmetro inválido) volta com isError, nunca como exceção."""
    if nome not in ferramentas.FERRAMENTAS:
        return {"content": [{"type": "text", "text": f"ferramenta {nome!r} não existe; use {ferramentas.FERRAMENTAS}"}],
                "isError": True}
    resultado = ferramentas.executar(con, nome, argumentos or {})
    if "erro" in resultado:
        return {"content": [{"type": "text", "text": str(resultado["erro"])}], "isError": True}
    saida = ferramentas.para_o_modelo(resultado)
    return {"content": [{"type": "text", "text": json.dumps(saida, ensure_ascii=False, default=str)}],
            "structuredContent": json.loads(json.dumps(saida, ensure_ascii=False, default=str)), "isError": False}


def responder(con_fn, mensagem) -> dict | None:
    """Resposta JSON-RPC a uma mensagem (None para notificação). `con_fn` abre a conexão só na primeira consulta."""
    if not isinstance(mensagem, dict) or mensagem.get("jsonrpc") != "2.0" or "method" not in mensagem:
        return _erro(mensagem.get("id") if isinstance(mensagem, dict) else None, ERRO_PEDIDO, "pedido inválido")
    metodo, ident, params = mensagem["method"], mensagem.get("id"), mensagem.get("params") or {}
    if "id" not in mensagem:   # notificação (notifications/initialized, cancelled …): sem resposta
        return None
    if metodo == "initialize":
        pedida = params.get("protocolVersion")
        return _ok(ident, {"protocolVersion": pedida if pedida == VERSAO_PROTOCOLO else VERSAO_PROTOCOLO,
                           "capabilities": {"tools": {"listChanged": False}},
                           "serverInfo": SERVIDOR, "instructions": INSTRUCOES})
    if metodo == "ping":
        return _ok(ident, {})
    if metodo == "tools/list":
        return _ok(ident, {"tools": ferramentas_mcp()})
    if metodo == "tools/call":
        if not isinstance(params.get("name"), str):
            return _erro(ident, ERRO_PARAMETROS, "tools/call precisa de `name`")
        args = params.get("arguments") or {}
        if not isinstance(args, dict):
            return _erro(ident, ERRO_PARAMETROS, "`arguments` precisa ser um objeto")
        return _ok(ident, chamar(con_fn(), params["name"], args))
    return _erro(ident, ERRO_METODO, f"método {metodo!r} não existe neste servidor")


def _ok(ident, resultado: dict) -> dict:
    return {"jsonrpc": "2.0", "id": ident, "result": resultado}


def _erro(ident, codigo: int, mensagem: str) -> dict:
    return {"jsonrpc": "2.0", "id": ident, "error": {"code": codigo, "message": mensagem}}


def servir(entrada=None, saida=None, pasta: Path | None = None) -> None:
    """Laço do transporte stdio: lê uma mensagem JSON por linha e escreve a resposta numa linha. O que não é protocolo
    (avisos, erros) vai para o stderr, nunca para o stdout."""
    entrada = entrada or sys.stdin
    saida = saida or sys.stdout
    conexao: list[duckdb.DuckDBPyConnection] = []

    def con_fn():
        if not conexao:
            banco = publico.banco_demonstracao(pasta or publico.PASTA)
            conexao.append(duckdb.connect(str(banco), read_only=True))
        return conexao[0]

    for linha in entrada:
        if not linha.strip():
            continue
        try:
            mensagem = json.loads(linha)
        except ValueError:
            resposta = _erro(None, ERRO_PARSE, "JSON inválido")
        else:
            try:
                resposta = responder(con_fn, mensagem)
            except Exception as e:   # o servidor não cai por uma consulta: responde o erro e segue
                print(f"radar-mcp: erro inesperado: {e!r}", file=sys.stderr)
                resposta = _erro(mensagem.get("id") if isinstance(mensagem, dict) else None, -32603,
                                 "erro interno do servidor")
        if resposta is not None:
            saida.write(json.dumps(resposta, ensure_ascii=False) + "\n")
            saida.flush()
    for c in conexao:
        c.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    servir()
