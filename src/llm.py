"""Interface única com o modelo do chat: Gemini, nível gratuito do Google AI Studio (D-060, D-061). Nenhum outro
módulo fala com a API.

Configuração em config/llm.yaml. A chave vem da variável GEMINI_API_KEY: do ambiente, do arquivo .env (fora do git)
ou, no Streamlit Community Cloud, de st.secrets, nesta ordem. Uma variável definida vazia vale como "sem chave" (os
testes usam isso para nunca chamar a API). A chave vai só no cabeçalho da chamada: nunca em URL, log, erro ou resposta.

Chamada REST `models/{modelo}:generateContent` com o httpx, que o projeto já usa; `_transporte` deixa os testes
trocarem a rede por um servidor simulado (httpx.MockTransport).
"""
import json
import os
import time
from pathlib import Path

import httpx
import yaml

RAIZ = Path(__file__).resolve().parents[1]
_transporte: httpx.BaseTransport | None = None   # só os testes trocam
_principal_fora_ate = 0.0   # depois de uma falha do principal, as chamadas vão direto para a reserva até esta hora


class LLMIndisponivel(RuntimeError):
    """O Gemini não respondeu. `motivo`: sem_chave, sem_internet, lento, cota ou erro."""

    def __init__(self, motivo: str, mensagem: str):
        super().__init__(mensagem)
        self.motivo = motivo


MENSAGENS = {
    "sem_chave": "O chat com o Gemini não está configurado nesta máquina (falta a chave GEMINI_API_KEY; veja o README).",
    "sem_internet": "Não foi possível falar com o Gemini (sem internet ou serviço fora do ar).",
    "lento": "O Gemini demorou demais para responder (serviço sobrecarregado). Tente de novo em alguns minutos.",
    "cota": "A cota gratuita do Gemini acabou por agora. Tente de novo mais tarde.",
    "erro": "O Gemini devolveu um erro.",
}


def config() -> dict:
    return yaml.safe_load((RAIZ / "config" / "llm.yaml").read_text(encoding="utf-8"))


def chave() -> str | None:
    """A chave do Gemini, ou None. Nunca imprima o resultado."""
    nome = config()["variavel_chave"]
    if nome not in os.environ:
        from dotenv import load_dotenv
        load_dotenv(RAIZ / ".env", override=False)
    if nome in os.environ:
        return os.environ[nome].strip() or None
    try:
        import streamlit as st
        return str(st.secrets.get(nome, "")).strip() or None
    except Exception:   # sem secrets.toml, ou fora do Streamlit
        return None


def situacao() -> tuple[bool, str]:
    """(configurado?, explicação curta para o log). Não chama a API (não gasta cota); nunca levanta exceção."""
    c = config()
    if not chave():
        return False, MENSAGENS["sem_chave"]
    return True, f"{c['modelo']} (Gemini, nível gratuito; reserva {c['reserva']}; prompt v{c['versao_prompt']})"


def _limpo(texto: str, segredo: str | None) -> str:
    return texto.replace(segredo, "***") if segredo else texto


_clientes: dict = {}


def cliente(c: dict | None = None) -> httpx.Client:
    """Um cliente HTTP só por processo (por transporte), reaproveitado entre perguntas: a conexão TLS com o Google fica
    aberta e as chamadas seguintes não pagam o aperto de mão de novo."""
    c = c or config()
    chave_ = (_transporte, float(c["timeout_s"]))   # o próprio objeto (não o id, que se repete depois de liberado)
    if chave_ not in _clientes:
        _clientes[chave_] = httpx.Client(transport=_transporte, timeout=float(c["timeout_s"]))
    return _clientes[chave_]


def _erro_http(r: httpx.Response, segredo: str) -> LLMIndisponivel:
    if r.status_code == 429:
        return LLMIndisponivel("cota", MENSAGENS["cota"])
    try:
        detalhe = r.json().get("error", {}).get("message", "")
    except ValueError:
        detalhe = ""
    return LLMIndisponivel("erro", _limpo(f"{MENSAGENS['erro']} (HTTP {r.status_code}) {detalhe}".strip(), segredo))


def _falha_de_rede(e: httpx.HTTPError, segredo: str) -> LLMIndisponivel:
    if isinstance(e, httpx.TimeoutException):
        return LLMIndisponivel("lento", MENSAGENS["lento"])
    return LLMIndisponivel("sem_internet", _limpo(f"{MENSAGENS['sem_internet']} ({type(e).__name__})", segredo))


def _limite_leitura(modelo: str, c: dict) -> float:
    """O principal tem um tempo-limite de leitura curto (inclusive até o primeiro byte): travado, vai logo para a
    reserva (D-069). A reserva usa o timeout_s."""
    return float(c.get("timeout_principal_s") or c["timeout_s"]) if modelo == c["modelo"] else float(c["timeout_s"])


def _chamar(modelo: str, corpo: dict, segredo: str, c: dict) -> dict:
    url = f"{c['api']}/models/{modelo}:generateContent"
    try:
        r = cliente(c).post(url, json=corpo, headers={"x-goog-api-key": segredo},
                            timeout=httpx.Timeout(float(c["timeout_s"]), read=_limite_leitura(modelo, c)))
    except httpx.HTTPError as e:
        raise _falha_de_rede(e, segredo) from None
    if r.status_code >= 400:
        raise _erro_http(r, segredo)
    candidatos = r.json().get("candidates") or []
    if not candidatos or "content" not in candidatos[0]:
        raise LLMIndisponivel("erro", f"{MENSAGENS['erro']} (resposta vazia)")
    return candidatos[0]["content"]


def _chamar_em_partes(modelo: str, corpo: dict, segredo: str, c: dict):
    """Streaming (`streamGenerateContent?alt=sse`): devolve ("texto", trecho) a cada pedaço de texto e, no fim,
    ("fim", content), com todas as partes na ordem em que chegaram (o histórico precisa delas como vieram)."""
    url = f"{c['api']}/models/{modelo}:streamGenerateContent?alt=sse"
    partes: list[dict] = []
    try:
        with cliente(c).stream("POST", url, json=corpo, headers={"x-goog-api-key": segredo},
                               timeout=httpx.Timeout(float(c["timeout_s"]), read=_limite_leitura(modelo, c))) as r:
            if r.status_code >= 400:
                r.read()
                raise _erro_http(r, segredo)
            for linha in r.iter_lines():
                if not linha.startswith("data:"):
                    continue
                pedaco = json.loads(linha[5:])
                for p in ((pedaco.get("candidates") or [{}])[0].get("content") or {}).get("parts", []):
                    partes.append(p)
                    if p.get("text") and not p.get("thought"):
                        yield "texto", p["text"]
    except httpx.HTTPError as e:
        raise _falha_de_rede(e, segredo) from None
    if not partes:
        raise LLMIndisponivel("erro", f"{MENSAGENS['erro']} (resposta vazia)")
    yield "fim", {"role": "model", "parts": partes}


def _do_modelo(corpo: dict, modelo: str, c: dict) -> dict:
    """O corpo com o nível de raciocínio daquele modelo (`nivel_raciocinio` e `nivel_raciocinio_reserva`)."""
    nivel = c.get("nivel_raciocinio_reserva") if modelo == c.get("reserva") else None
    gc = {**corpo["generationConfig"], "thinkingConfig": {"thinkingLevel": nivel or c["nivel_raciocinio"]}}
    return {**corpo, "generationConfig": gc}


def _corpo(conteudos: list[dict], sistema: str, ferramentas: list[dict] | None, sem_ferramenta_agora: bool,
           c: dict) -> dict:
    corpo = {"systemInstruction": {"parts": [{"text": sistema}]}, "contents": conteudos,
             "generationConfig": {"temperature": float(c["temperatura"])}}
    if ferramentas:
        corpo["tools"] = [{"functionDeclarations": ferramentas}]
        if sem_ferramenta_agora:
            corpo["toolConfig"] = {"functionCallingConfig": {"mode": "NONE"}}
    return corpo


def _modelos(c: dict) -> list[str]:
    """Na ordem de tentativa. Se o principal falhou há pouco, só a reserva: não perde tempo com ele, e o histórico já
    tem respostas da reserva, que o principal recusa."""
    if c.get("reserva") and time.monotonic() < _principal_fora_ate:
        return [c["reserva"]]
    return [c["modelo"], c["reserva"]] if c.get("reserva") else [c["modelo"]]


def _principal_falhou(c: dict) -> None:
    global _principal_fora_ate
    _principal_fora_ate = time.monotonic() + float(c["reserva_por_s"])


def conversar(conteudos: list[dict], sistema: str, ferramentas: list[dict] | None = None,
              sem_ferramenta_agora: bool = False) -> dict:
    """Uma chamada ao modelo. `conteudos`: o histórico no formato do Gemini ({"role": "user"|"model", "parts": [...]}).
    Devolve o `content` do modelo como veio (com as assinaturas de raciocínio, que voltam no histórico seguinte).
    `sem_ferramenta_agora`: as ferramentas seguem declaradas (o histórico tem chamadas), mas o modelo tem de responder
    em texto. Com cota esgotada, demora (o principal às vezes trava no nível gratuito) ou erro no modelo principal,
    tenta a reserva uma vez."""
    c = config()
    segredo = chave()
    if not segredo:
        raise LLMIndisponivel("sem_chave", MENSAGENS["sem_chave"])
    corpo = _corpo(conteudos, sistema, ferramentas, sem_ferramenta_agora, c)
    modelos = _modelos(c)
    for i, modelo in enumerate(modelos):
        try:
            return _chamar(modelo, _do_modelo(corpo, modelo, c), segredo, c)
        except LLMIndisponivel as e:
            if e.motivo not in ("cota", "lento", "erro") or i == len(modelos) - 1:
                raise
            _principal_falhou(c)


def conversar_em_partes(conteudos: list[dict], sistema: str, ferramentas: list[dict] | None = None,
                        sem_ferramenta_agora: bool = False):
    """Como `conversar`, em streaming: ("texto", trecho) enquanto o texto chega e ("fim", content) no fim. A reserva
    só entra se o principal falhar antes do primeiro trecho de texto."""
    c = config()
    segredo = chave()
    if not segredo:
        raise LLMIndisponivel("sem_chave", MENSAGENS["sem_chave"])
    corpo = _corpo(conteudos, sistema, ferramentas, sem_ferramenta_agora, c)
    modelos = _modelos(c)
    for i, modelo in enumerate(modelos):
        deu_texto = False
        try:
            for tipo, valor in _chamar_em_partes(modelo, _do_modelo(corpo, modelo, c), segredo, c):
                deu_texto = deu_texto or tipo == "texto"
                yield tipo, valor
            return
        except LLMIndisponivel as e:
            if deu_texto or e.motivo not in ("cota", "lento", "erro") or i == len(modelos) - 1:
                raise
            _principal_falhou(c)


def texto(conteudo: dict) -> str:
    """O texto da resposta (sem as partes de raciocínio)."""
    return "".join(p.get("text", "") for p in conteudo.get("parts", []) if not p.get("thought")).strip()


def chamadas(conteudo: dict) -> list[dict]:
    """Os pedidos de ferramenta da resposta: [{"id", "name", "args"}]."""
    return [p["functionCall"] for p in conteudo.get("parts", []) if "functionCall" in p]
