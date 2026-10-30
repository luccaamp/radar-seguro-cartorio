"""Avaliação do chat com a API REAL do Gemini (D-065; fora da suíte de testes, que nunca usa a API).

Compara (a) o modelo sem ferramentas, (b) com as normas no prompt e (c) com as 5 ferramentas (a versão do painel):
acertos, alucinações (número sem apoio nas ferramentas, na pergunta ou no prompt), respostas sem fonte, "não sei"
corretos (fora do escopo, armadilhas e dados pessoais) e latência. A meta (config/llm.yaml, `avaliacao`) foi fixada
antes da primeira rodada: (c) com acerto ≥ meta e nenhum número inventado nas armadilhas.

Cuida da cota gratuita: pausa entre as perguntas, uma nova tentativa depois de um 429 e respostas guardadas em
eval/respostas/ (uma linha por pergunta e versão): rodar de novo só chama a API para o que falta. As respostas
guardadas valem para o mesmo gabarito, modelo e versão do prompt; `--refazer` ignora o que foi guardado.

Usa o banco de demonstração montado a partir do conjunto público (`data/publico`), nunca o banco real. Precisa da
chave GEMINI_API_KEY (ambiente ou .env; ver README). A chave nunca é gravada nem impressa.

Uso:
  uv run python scripts/avaliar_chat.py                  # (a), (b) e (c)
  uv run python scripts/avaliar_chat.py --versoes c      # só (c)
  uv run python scripts/avaliar_chat.py --limite 5       # só as 5 primeiras perguntas (teste rápido da cota)
  uv run python scripts/avaliar_chat.py --relatorio      # só refaz o relatório com as respostas guardadas
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
RESPOSTAS = RAIZ / "eval" / "respostas"
SAIDA = RAIZ / "eval" / "resultado_avaliacao.md"
TIPOS_NAO_SEI = {"fora_escopo", "armadilha", "dado_pessoal"}


def chave_cache(c: dict, versao: str, sha: str) -> dict:
    return {"gabarito": sha[:12], "modelo": c["modelo"], "versao": versao,
            "prompt": c["versao_prompt"] if versao == "c" else 0}


def ler_cache(versao: str, marca: dict) -> dict[str, dict]:
    arquivo = RESPOSTAS / f"{versao}.jsonl"
    if not arquivo.exists():
        return {}
    linhas = [json.loads(x) for x in arquivo.read_text(encoding="utf-8").splitlines() if x.strip()]
    return {r["id"]: r for r in linhas if all(r.get(k) == v for k, v in marca.items())}


def guardar(versao: str, registro: dict) -> None:
    RESPOSTAS.mkdir(parents=True, exist_ok=True)
    with (RESPOSTAS / f"{versao}.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def perguntar(p: dict, versao: str, con, c: dict) -> dict:
    """Uma pergunta com uma nova tentativa depois de cota esgotada. Levanta LLMIndisponivel se não der."""
    for tentativa in range(2):
        t = time.time()
        try:
            r = chat.responder(p["pergunta"], con, versao=versao)
            return {"resposta": r.texto, "segundos": round(time.time() - t, 1), "apoio": chat.apoio(r),
                    "ferramentas": [{"ferramenta": x["ferramenta"], "argumentos": x["argumentos"]} for x in r.chamadas]}
        except llm.LLMIndisponivel as e:
            if e.motivo != "cota" or tentativa:
                raise
            espera = int(c["avaliacao"]["espera_cota_s"])
            print(f"   cota esgotada; esperando {espera} s para tentar de novo", flush=True)
            time.sleep(espera)


def corrigir(p: dict, r: dict, versao: str) -> dict:
    inventados = avaliacao.numeros_sem_apoio(r["resposta"], " ".join([r["apoio"], p["pergunta"],
                                                                     chat.prompt_sistema(versao)]))
    return {**r, "numeros_inventados": inventados, "fonte": avaliacao.tem_fonte(r["resposta"]),
            "certo": avaliacao.corrigir(r["resposta"], p["criterio"], p["esperado"]) and not inventados}


def main(versoes: list[str], limite: int | None, refazer: bool, so_relatorio: bool) -> None:
    c = llm.config()
    sha = hashlib.sha256(GABARITO.read_bytes()).hexdigest()
    if sha != c["avaliacao"]["gabarito_sha256"]:
        raise SystemExit("eval/gabarito_chat.csv mudou depois de congelado: o hash não bate com config/llm.yaml "
                         "(avaliacao.gabarito_sha256). Registre a decisão e atualize o hash antes de avaliar.")
    ok, explicacao = llm.situacao()
    if not ok and not so_relatorio:
        raise SystemExit(explicacao)
    with GABARITO.open(encoding="utf-8") as f:
        perguntas = list(csv.DictReader(f, delimiter=";"))[:limite]
    con = duckdb.connect(str(publico.banco_demonstracao(publico.PASTA)), read_only=True)
    resultados = {v: {} for v in versoes}
    parou = None
    for v in versoes:
        marca = chave_cache(c, v, sha)
        guardadas = {} if refazer else ler_cache(v, marca)
        for p in perguntas:
            if p["id"] in guardadas:
                resultados[v][p["id"]] = corrigir(p, guardadas[p["id"]], v)
                continue
            if so_relatorio or parou:
                continue
            try:
                r = perguntar(p, v, con, c)
            except llm.LLMIndisponivel as e:
                parou = f"{e} (parou na pergunta {p['id']} da versão {v}; rode de novo depois: o que foi feito ficou guardado)"
                print(parou, flush=True)
                continue
            guardar(v, {**marca, "id": p["id"], "em": f"{dt.datetime.now():%Y-%m-%d %H:%M}", **r})
            resultados[v][p["id"]] = corrigir(p, r, v)
            x = resultados[v][p["id"]]
            print(f"{p['id']:>2} {v} {'ok ' if x['certo'] else 'ERR'} {x['segundos']:5.1f}s {x['resposta'][:90]!r}",
                  flush=True)
            time.sleep(float(c["avaliacao"]["pausa_s"]))
    relatorio(perguntas, resultados, versoes, sha, c, parou)


def _pct(a: int, b: int) -> str:
    return f"{a}/{b} ({100 * a / b:.0f}%)" if b else "—"


def relatorio(perguntas: list[dict], resultados: dict, versoes: list[str], sha: str, c: dict,
              parou: str | None) -> None:
    av = c["avaliacao"]
    tipos = list(dict.fromkeys(p["tipo"] for p in perguntas))
    linhas = [f"# Avaliação do chat ({dt.date.today():%Y-%m-%d})", "",
              f"Modelo `{c['modelo']}` (Gemini, nível gratuito; reserva `{c['reserva']}`), raciocínio "
              f"`{c['nivel_raciocinio']}`, temperatura {c['temperatura']}, prompt do agente v{c['versao_prompt']}. "
              f"Gabarito `eval/gabarito_chat.csv` congelado (SHA-256 {sha[:12]}…, {len(perguntas)} perguntas). Dados do "
              "conjunto público (`data/publico`). Correção automática (`src/agent/avaliacao.py`): número a até 1% do "
              "esperado, palavras obrigatórias, recusa sem valor em R$; resposta com número sem apoio nas ferramentas, "
              "na pergunta ou no prompt conta como alucinação e como erro.", "",
              f"**Meta (fixada antes da primeira rodada, D-065):** versão (c) com acerto ≥ {av['meta_acerto']:.0%} e "
              "nenhum número inventado nas armadilhas.", ""]
    if parou:
        linhas += [f"> **Rodada incompleta:** {parou}", ""]
    linhas += ["## Resumo", "", "| Medida | " + " | ".join(chat.VERSOES[v] for v in versoes) + " |",
               "|---|" + "---|" * len(versoes)]

    def medida(rotulo, f):
        linhas.append(f"| {rotulo} | " + " | ".join(f(resultados[v]) for v in versoes) + " |")
    feitas = lambda rs: [rs[p["id"]] for p in perguntas if p["id"] in rs]  # noqa: E731
    medida("Respondidas", lambda rs: f"{len(feitas(rs))}/{len(perguntas)}")
    medida("Acertos", lambda rs: _pct(sum(r["certo"] for r in feitas(rs)), len(feitas(rs))))
    medida("Com número inventado", lambda rs: _pct(sum(bool(r["numeros_inventados"]) for r in feitas(rs)),
                                                   len(feitas(rs))))
    medida("Sem a linha \"Fonte\"", lambda rs: _pct(sum(not r["fonte"] for r in feitas(rs)), len(feitas(rs))))
    nao_sei = [p["id"] for p in perguntas if p["tipo"] in TIPOS_NAO_SEI]
    medida("\"Não sei\" corretos", lambda rs: _pct(sum(rs[i]["certo"] for i in nao_sei if i in rs),
                                                   sum(i in rs for i in nao_sei)))
    medida("Latência média", lambda rs: f"{sum(r['segundos'] for r in feitas(rs)) / max(len(feitas(rs)), 1):.1f} s")
    if "c" in versoes and len(resultados["c"]) == len(perguntas):
        rc = resultados["c"]
        acerto = sum(r["certo"] for r in rc.values()) / len(rc)
        armadilhas = [p["id"] for p in perguntas if p["tipo"] == "armadilha"]
        inventou = [i for i in armadilhas if rc[i]["numeros_inventados"]]
        ok = acerto >= av["meta_acerto"] and not inventou
        linhas += ["", f"**Meta {'cumprida' if ok else 'NÃO cumprida'}:** (c) acertou {acerto:.0%} "
                       f"(meta {av['meta_acerto']:.0%}); armadilhas com número inventado: {inventou or 'nenhuma'}."]
    linhas += ["", "## Acerto por tipo", "", "| Tipo | " + " | ".join(chat.VERSOES[v] for v in versoes) + " |",
               "|---|" + "---|" * len(versoes)]
    for t in tipos:
        ids = [p["id"] for p in perguntas if p["tipo"] == t]
        linhas.append(f"| {t} | " + " | ".join(_pct(sum(resultados[v][i]["certo"] for i in ids if i in resultados[v]),
                                                   sum(i in resultados[v] for i in ids)) for v in versoes) + " |")
    linhas += ["", "## Pergunta a pergunta", "", "| # | Tipo | Pergunta | Esperado | " +
               " | ".join(chat.VERSOES[v] for v in versoes) + " |", "|---|---|---|---|" + "---|" * len(versoes)]
    for p in perguntas:
        celulas = []
        for v in versoes:
            r = resultados[v].get(p["id"])
            celulas.append("—" if r is None else ("✅ " if r["certo"] else "❌ ") +
                           r["resposta"].replace("\n", " ").replace("|", "/")[:160])
        linhas.append(f"| {p['id']} | {p['tipo']} | {p['pergunta']} | {p['esperado'] or p['criterio']} | "
                      + " | ".join(celulas) + " |")
    SAIDA.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas[:40]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    sys.stderr.reconfigure(encoding="utf-8")
    a = argparse.ArgumentParser()
    a.add_argument("--versoes", default="abc", help="a (sem ferramentas), b (normas no prompt), c (com ferramentas)")
    a.add_argument("--limite", type=int, help="só as N primeiras perguntas")
    a.add_argument("--refazer", action="store_true", help="ignora as respostas guardadas em eval/respostas/")
    a.add_argument("--relatorio", action="store_true", help="só refaz o relatório com as respostas guardadas")
    x = a.parse_args()
    main([v for v in x.versoes if v in chat.VERSOES], x.limite, x.refazer, x.relatorio)
