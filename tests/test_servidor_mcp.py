"""Servidor MCP (src/agent/servidor_mcp.py): o protocolo (initialize, tools/list, tools/call, erros) e as respostas com os
números do conjunto público versionado, iguais aos do chat do painel. Sobe o servidor como processo, como um cliente
MCP faria (stdio, uma mensagem JSON por linha). Não usa a API do Gemini nem a internet."""
import io
import json
import subprocess
import sys

import pytest

from apoio_painel import RAIZ
from src.agent import ferramentas, servidor_mcp as mcp


def _conversar(mensagens: list[dict]) -> list[dict]:
    entrada = "".join(json.dumps(m, ensure_ascii=False) + "\n" for m in mensagens)
    r = subprocess.run([sys.executable, "-m", "src.agent.servidor_mcp"], input=entrada.encode("utf-8"),
                       capture_output=True, cwd=RAIZ, timeout=300)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    return [json.loads(x) for x in r.stdout.decode("utf-8").splitlines() if x.strip()]


@pytest.fixture(scope="module")
def sessao():
    """Uma sessão completa num processo só: inicialização, lista, 3 chamadas e 2 erros."""
    return _conversar([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "teste", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "consultar_numeros", "arguments": {"analise": "numeros_oficiais"}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
         "params": {"name": "consultar_numeros", "arguments": {"analise": "faixa_d042", "medida": "premio"}}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
         "params": {"name": "consultar_numeros", "arguments": {"analise": "nao_existe"}}},
        {"jsonrpc": "2.0", "id": 6, "method": "metodo/inexistente"},
        {"jsonrpc": "2.0", "id": 7, "method": "ping"},
    ])


def test_inicializa_e_lista_as_5_ferramentas_do_chat(sessao):
    por_id = {r["id"]: r for r in sessao}
    assert len(sessao) == 7                                   # a notificação não tem resposta
    init = por_id[1]["result"]
    assert init["protocolVersion"] == "2025-06-18"
    assert init["capabilities"] == {"tools": {"listChanged": False}}
    assert init["serverInfo"]["name"] == "radar-seguro-cartorio"
    tools = por_id[2]["result"]["tools"]
    assert [t["name"] for t in tools] == ferramentas.FERRAMENTAS
    for t, e in zip(tools, ferramentas.ESQUEMAS):
        assert t["inputSchema"] == e["parameters"] and t["description"] == e["description"]
        assert t["annotations"]["readOnlyHint"] is True


def test_chamada_devolve_os_numeros_do_painel_com_a_fonte(sessao):
    por_id = {r["id"]: r for r in sessao}
    oficiais = por_id[3]["result"]
    assert oficiais["isError"] is False
    texto = oficiais["content"][0]["text"]
    assert json.loads(texto) == oficiais["structuredContent"]
    assert "R$ 341,1 mil" in texto and "2.525" in texto       # prêmio anual e serventias (ESTADO_ATUAL)
    assert "citar" in oficiais["structuredContent"]
    assert "valores" not in oficiais["structuredContent"]     # os números crus não saem (como no chat)
    faixa = por_id[4]["result"]["structuredContent"]
    assert "R$ 215,0 mil" in json.dumps(faixa, ensure_ascii=False)


def test_erros_viram_resposta_e_o_servidor_segue(sessao):
    por_id = {r["id"]: r for r in sessao}
    assert por_id[5]["result"]["isError"] is True and "nao_existe" in por_id[5]["result"]["content"][0]["text"]
    assert por_id[6]["error"]["code"] == mcp.ERRO_METODO
    assert por_id[7]["result"] == {}                          # depois dos erros, o servidor continua respondendo


def test_sem_dado_pessoal_nas_respostas(sessao):
    import re
    texto = json.dumps(sessao, ensure_ascii=False)
    assert not re.search(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", texto)   # formato de CPF


def test_mensagens_invalidas_no_proprio_processo():
    saida = io.StringIO()
    mcp.servir(io.StringIO('não é json\n{"jsonrpc": "1.0", "id": 9, "method": "ping"}\n'
                           '{"jsonrpc": "2.0", "id": 10, "method": "tools/call", "params": {"arguments": {}}}\n'),
               saida)
    respostas = [json.loads(x) for x in saida.getvalue().splitlines()]
    assert [r["error"]["code"] for r in respostas] == [mcp.ERRO_PARSE, mcp.ERRO_PEDIDO, mcp.ERRO_PARAMETROS]


def test_ferramenta_inexistente_e_versao_de_protocolo_desconhecida():
    r = mcp.chamar(None, "apagar_tudo", {})
    assert r["isError"] is True
    init = mcp.responder(lambda: None, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                        "params": {"protocolVersion": "1999-01-01"}})
    assert init["result"]["protocolVersion"] == mcp.VERSAO_PROTOCOLO
