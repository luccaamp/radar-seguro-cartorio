"""Avaliação do chat contra o gabarito (SPEC §7): versão (a) modelo sem ferramentas e (c) com ferramentas.

Usa o banco de demonstração montado a partir do conjunto público (`data/publico`): nunca o banco real. Precisa do
Ollama rodando. Grava o relatório em eval/resultado_avaliacao.md (e as respostas completas em
eval/resultado_avaliacao.json).

Uso:
  uv run python scripts/avaliar_chat.py                # (a) e (c)
  uv run python scripts/avaliar_chat.py --versoes c    # só (c)
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import llm, publico  # noqa: E402
from src.agent import avaliacao, chat  # noqa: E402

GABARITO = RAIZ / "eval" / "gabarito_chat.csv"
NOMES = {"a": "(a) sem ferramentas", "c": "(c) com ferramentas"}


def main(versoes: list[str]) -> None:
    ok, explicacao = llm.situacao()
    if not ok:
        raise SystemExit(explicacao)
    perguntas = list(csv.DictReader(GABARITO.open(encoding="utf-8"), delimiter=";"))
    con = duckdb.connect(str(publico.banco_demonstracao(publico.PASTA)), read_only=True)
    resultados = []
    for p in perguntas:
        linha = {**p}
        for v in versoes:
            t = time.time()
            try:
                r = chat.responder(p["pergunta"], con, com_ferramentas=(v == "c"))
                texto, chamadas = r.texto, [{"ferramenta": c["ferramenta"], "argumentos": c["argumentos"]}
                                            for c in r.chamadas]
                apoio = " ".join(json.dumps(c["resultado"], ensure_ascii=False) for c in r.chamadas)
            except llm.LLMIndisponivel as e:
                texto, chamadas, apoio = f"ERRO: {e}", [], ""
            inventados = avaliacao.numeros_sem_apoio(texto, " ".join([apoio, p["pergunta"], chat.SISTEMA]))
            linha[v] = {"resposta": texto, "ferramentas": chamadas, "segundos": round(time.time() - t, 1),
                        "numeros_inventados": inventados,
                        "certo": avaliacao.corrigir(texto, p["criterio"], p["esperado"]) and not inventados,
                        "fonte": avaliacao.tem_fonte(texto)}
            print(f"{p['id']:>2} {v} {'ok ' if linha[v]['certo'] else 'ERR'} {linha[v]['segundos']:5.1f}s "
                  f"{texto[:90]!r}", flush=True)
        resultados.append(linha)
    relatorio(perguntas, resultados, versoes)


def relatorio(perguntas: list[dict], resultados: list[dict], versoes: list[str]) -> None:
    c = llm.config()
    tipos = list(dict.fromkeys(p["tipo"] for p in perguntas))
    sha = hashlib.sha256(GABARITO.read_bytes()).hexdigest()[:12]
    linhas = [f"# Avaliação do chat ({dt.date.today():%Y-%m-%d})", "",
              f"Modelo `{c['modelo']}` no Ollama local (think={c['think']}, temperatura {c['temperatura']}); gabarito "
              f"`eval/gabarito_chat.csv` (SHA-256 {sha}…, {len(perguntas)} perguntas, rascunho a revisar pelo autor); "
              "dados do conjunto público (`data/publico`). Correção automática (`src/agent/avaliacao.py`): número a até "
              "1% do esperado, palavras obrigatórias nas normas, recusa sem valor em R$ nas armadilhas; resposta com "
              "número que não veio das ferramentas nem da pergunta conta como alucinação e como erro.", "",
              "## Acerto por tipo", "", "| Tipo | " + " | ".join(NOMES[v] for v in versoes) + " |",
              "|---|" + "---|" * len(versoes)]
    for t in [*tipos, "total"]:
        sel = [r for r in resultados if t == "total" or r["tipo"] == t]
        linhas.append(f"| {t} | " + " | ".join(
            f"{sum(r[v]['certo'] for r in sel)}/{len(sel)} ({100 * sum(r[v]['certo'] for r in sel) / len(sel):.0f}%)"
            for v in versoes) + " |")
    for v in versoes:
        com_fonte = sum(r[v]["fonte"] for r in resultados)
        tempo = sum(r[v]["segundos"] for r in resultados) / len(resultados)
        alucinou = sum(bool(r[v]["numeros_inventados"]) for r in resultados)
        linhas.append(f"\n{NOMES[v]}: respostas com a linha \"Fonte\": {com_fonte}/{len(resultados)}; com número "
                      f"inventado (alucinação): {alucinou}/{len(resultados)}; tempo médio {tempo:.0f} s por pergunta.")
    linhas += ["", "## Pergunta a pergunta", "", "| # | Tipo | Pergunta | Esperado | " +
               " | ".join(NOMES[v] for v in versoes) + " |", "|---|---|---|---|" + "---|" * len(versoes)]
    for r in resultados:
        esperado = r["esperado"] or "recusa"
        celulas = [("✅ " if r[v]["certo"] else "❌ ") + r[v]["resposta"].replace("\n", " ").replace("|", "/")[:160]
                   for v in versoes]
        linhas.append(f"| {r['id']} | {r['tipo']} | {r['pergunta']} | {esperado} | " + " | ".join(celulas) + " |")
    (RAIZ / "eval" / "resultado_avaliacao.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    (RAIZ / "eval" / "resultado_avaliacao.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=1),
                                                             encoding="utf-8")
    print("\n".join(linhas[:12 + len(tipos)]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    sys.stderr.reconfigure(encoding="utf-8")
    a = argparse.ArgumentParser()
    a.add_argument("--versoes", default="ac", help="a (sem ferramentas), c (com ferramentas) ou ac")
    main([v for v in a.parse_args().versoes if v in NOMES])
