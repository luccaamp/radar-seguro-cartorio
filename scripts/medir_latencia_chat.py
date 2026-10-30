"""Latência do chat, etapa por etapa, com a API REAL do Gemini (fora da suíte de testes; gasta poucas chamadas).

Roda as perguntas de fumaça de config/llm.yaml (`latencia.perguntas_fumaca`, fora do gabarito) no banco de
demonstração (nunca o banco real) e mede: dados (montar e abrir o banco), cliente HTTP, cada chamada ao modelo (com
os tokens de raciocínio que a API informa), cada ferramenta, esperas por cota (429) e montagem da resposta. Grava uma
tabela em markdown.

Uso:
  uv run python scripts/medir_latencia_chat.py --saida docs/qa/chat/latencia_depois.md
"""
import argparse
import datetime as dt
import statistics
import sys
import time
from pathlib import Path

import duckdb
import httpx

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import llm, publico  # noqa: E402
from src.agent import chat, ferramentas  # noqa: E402

etapas: list[dict] = []


def _instrumentar() -> None:
    """Embrulha a rede do src/llm.py e as ferramentas para cronometrar cada passo (só neste processo)."""
    envia = httpx.Client.send

    def send(self, request, *a, **kw):
        t = time.perf_counter()
        modelo = request.url.path.rsplit("/", 1)[-1].split(":")[0]
        try:
            r = envia(self, request, *a, **kw)
        except httpx.HTTPError as e:   # tempo-limite ou rede: também é espera (antes passava sem registro)
            etapas.append({"etapa": "modelo (até a resposta começar)", "detalhe": modelo,
                           "s": time.perf_counter() - t, "status": type(e).__name__})
            raise
        if "generativelanguage" in str(request.url):
            etapas.append({"etapa": "modelo (até a resposta começar)", "detalhe": modelo, "s": time.perf_counter() - t,
                           "status": r.status_code})
        return r
    httpx.Client.send = send
    executar = ferramentas.executar

    def executar_medido(con, nome, argumentos):
        t = time.perf_counter()
        r = executar(con, nome, argumentos)
        etapas.append({"etapa": "ferramenta", "detalhe": (argumentos or {}).get("analise", nome),
                       "s": time.perf_counter() - t})
        return r
    ferramentas.executar = executar_medido


def medir(perguntas: list[str]) -> tuple[list[dict], dict]:
    t = time.perf_counter()
    con = duckdb.connect(str(publico.banco_demonstracao(publico.PASTA)), read_only=True)
    con.execute("SELECT * FROM gold.execucao").fetchall()
    dados = time.perf_counter() - t
    t = time.perf_counter()
    httpx.Client().close()
    cliente = time.perf_counter() - t
    linhas = []
    for p in perguntas:
        etapas.clear()
        primeiro = None
        inicio = time.perf_counter()
        try:
            if hasattr(chat, "responder_em_partes"):   # versão com streaming
                for tipo, valor in chat.responder_em_partes(p, con):
                    if tipo == "texto" and valor and primeiro is None:
                        primeiro = time.perf_counter() - inicio
                    if tipo == "fim":
                        r = valor
            else:
                r = chat.responder(p, con)
            erro = ""
        except llm.LLMIndisponivel as e:
            r, erro = chat.Resposta(""), e.motivo
        t = time.perf_counter()
        if hasattr(chat, "separar_fonte"):
            chat.separar_fonte(r.texto)
        montar = time.perf_counter() - t
        total = time.perf_counter() - inicio
        linhas.append({"pergunta": p, "etapas": list(etapas), "montar": montar, "total": total,
                       "primeiro": primeiro if primeiro is not None else total, "erro": erro,
                       "resposta": r.texto})
        print(f"{total:5.1f}s  {p}  {erro or r.texto[:80]!r}", flush=True)
    return linhas, {"dados": dados, "cliente": cliente}


def relatorio(linhas: list[dict], fixos: dict, saida: Path, titulo: str) -> None:
    c = llm.config()
    out = [f"# {titulo} ({dt.datetime.now():%Y-%m-%d %H:%M})", "",
           f"Modelo `{c['modelo']}` (reserva `{c['reserva']}`), raciocínio `{c['nivel_raciocinio']}`, prompt "
           f"v{c['versao_prompt']}, banco de demonstração (`data/publico`). Medido por `scripts/medir_latencia_chat.py` "
           "no WSL, com a API real. As chamadas ao modelo medem até a resposta começar a chegar (cabeçalhos HTTP); com "
           "streaming, o resto do texto chega depois, dentro do total.", "",
           "## Etapas fixas (uma vez por sessão)", "", "| Etapa | Tempo |", "|---|---|",
           f"| Dados: montar e abrir o banco de demonstração (já montado no disco) | {fixos['dados']:.2f} s |",
           f"| Criar o cliente HTTP do Gemini | {fixos['cliente'] * 1000:.0f} ms |", "",
           "## Por pergunta", "", "| Pergunta | Chamadas ao modelo | Ferramentas | Esperas (429, erro, tempo-limite) | Montar | "
           "Primeiro texto | Total |", "|---|---|---|---|---|---|---|"]
    for ln in linhas:
        mod = [e for e in ln["etapas"] if e["etapa"].startswith("modelo")]
        ok = [e for e in mod if e["status"] == 200]
        falhas = [e for e in mod if e["status"] != 200]
        ferr = [e for e in ln["etapas"] if e["etapa"] == "ferramenta"]
        out.append(f"| {ln['pergunta']} | {len(ok)} × ({' + '.join(f'{e['s']:.1f}' for e in ok)} s) | "
                   f"{len(ferr)} ({sum(e['s'] for e in ferr) * 1000:.0f} ms) | "
                   f"{len(falhas)} ({sum(e['s'] for e in falhas):.1f} s) | {ln['montar'] * 1000:.1f} ms | "
                   f"{ln['primeiro']:.1f} s | {ln['total']:.1f} s{' (' + ln['erro'] + ')' if ln['erro'] else ''} |")
    feitas = [ln for ln in linhas if not ln["erro"]]
    if feitas:
        out += ["", f"**Medianas** (perguntas sem erro, {len(feitas)} de {len(linhas)}): primeiro texto "
                    f"{statistics.median(ln['primeiro'] for ln in feitas):.1f} s; resposta completa "
                    f"{statistics.median(ln['total'] for ln in feitas):.1f} s."]
    modelos = sorted({e["detalhe"] for ln in linhas for e in ln["etapas"] if e["etapa"].startswith("modelo")
                      and e["status"] == 200})
    out += ["", f"Modelos que responderam: {', '.join(modelos) or 'nenhum'}.", "", "## Respostas", ""]
    out += [f"- **{ln['pergunta']}** — {(ln['erro'] or ln['resposta']).replace(chr(10), ' ')[:300]}" for ln in linhas]
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    a = argparse.ArgumentParser()
    a.add_argument("--saida", required=True)
    a.add_argument("--titulo", default="Latência do chat")
    x = a.parse_args()
    if not llm.situacao()[0]:
        raise SystemExit(llm.MENSAGENS["sem_chave"])
    _instrumentar()
    perguntas = llm.config().get("latencia", {}).get("perguntas_fumaca") or [
        "quantos cartórios de protesto tem em MG?", "qual o prêmio anual do cartório de CNS 048256?",
        "quais são os seis tipos de cartório?", "qual a data de referência dos dados da RAIS?",
        "qual artigo fala do regime especial?"]
    linhas, fixos = medir(perguntas)
    relatorio(linhas, fixos, RAIZ / x.saida, x.titulo)
