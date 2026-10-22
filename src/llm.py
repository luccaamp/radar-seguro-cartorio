"""Interface única com o LLM local (Ollama). Nenhum outro módulo fala com o Ollama (CLAUDE.md, "Padrões de código").

Configuração em config/llm.yaml; a variável RADAR_OLLAMA_URL troca o endereço (os testes apontam para uma porta
vazia para simular "sem Ollama"). Sem dependência nova: só httpx, que o projeto já usa nos coletores.
"""
import os
from pathlib import Path

import httpx
import yaml

RAIZ = Path(__file__).resolve().parents[1]


class LLMIndisponivel(RuntimeError):
    """O Ollama não está rodando ou o modelo não está instalado."""


def config() -> dict:
    c = yaml.safe_load((RAIZ / "config" / "llm.yaml").read_text(encoding="utf-8"))
    c["url"] = os.environ.get("RADAR_OLLAMA_URL") or c["url"]
    return c


def situacao() -> tuple[bool, str]:
    """(disponível?, explicação curta). Nunca levanta exceção: o painel usa isto para desativar o chat."""
    c = config()
    try:
        r = httpx.get(f"{c['url']}/api/tags", timeout=3)
        r.raise_for_status()
    except httpx.HTTPError:
        return False, (f"O Ollama não está rodando em {c['url']}. Instale em https://ollama.com, rode "
                       f"`ollama pull {c['modelo']}` e abra o Ollama.")
    nomes = {m.get("name") for m in r.json().get("models", [])}
    if c["modelo"] not in nomes:
        return False, f"O modelo {c['modelo']} não está instalado. Rode `ollama pull {c['modelo']}`."
    return True, f"{c['modelo']} no Ollama local"


def conversar(mensagens: list[dict], ferramentas: list[dict] | None = None) -> dict:
    """Uma chamada ao modelo (sem streaming). Devolve a mensagem do assistente: `content` e, se houver,
    `tool_calls`. Levanta LLMIndisponivel se o Ollama não responder."""
    c = config()
    corpo = {"model": c["modelo"], "messages": mensagens, "stream": False, "think": bool(c["think"]),
             "options": {"num_ctx": int(c["num_ctx"]), "temperature": float(c["temperatura"])}}
    if ferramentas:
        corpo["tools"] = ferramentas
    try:
        r = httpx.post(f"{c['url']}/api/chat", json=corpo, timeout=float(c["timeout_s"]))
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise LLMIndisponivel(f"falha ao chamar o Ollama em {c['url']}: {e}") from e
    return r.json()["message"]
