"""Avaliação do chat com a API REAL do Gemini (D-065; fora da suíte de testes, que nunca usa a API).

Compara (a) o modelo sem ferramentas, (b) com as normas no prompt e (c) com as 5 ferramentas (a versão do painel):
acertos, alucinações (número sem apoio nas ferramentas, na pergunta ou no prompt), respostas sem fonte, "não sei"
corretos (fora do escopo, armadilhas e dados pessoais) e latência. A meta (config/llm.yaml, `avaliacao`) foi fixada
antes da primeira rodada: (c) com acerto ≥ meta e nenhum número inventado nas armadilhas.

Cuida da cota gratuita: pausa entre as perguntas, novas tentativas depois de 429, demora ou 5xx e respostas guardadas em
eval/respostas/ (uma linha por pergunta e versão): rodar de novo só chama a API para o que falta. As respostas
guardadas valem para o mesmo gabarito, modelo e versão do prompt; `--refazer` ignora o que foi guardado.

Usa o banco de demonstração montado a partir do conjunto público (`data/publico`), nunca o banco real. Precisa da
chave GEMINI_API_KEY (ambiente ou .env; ver README). A chave nunca é gravada nem impressa.

Uso:
  uv run python scripts/avaliar_chat.py                  # (a), (b) e (c)
  uv run python scripts/avaliar_chat.py --versoes c      # só (c)
  uv run python scripts/avaliar_chat.py --limite 5       # só as 5 primeiras perguntas (teste rápido da cota)
  uv run python scripts/avaliar_chat.py --relatorio      # só refaz o relatório com as respostas guardadas
  uv run python scripts/avaliar_chat.py --versoes c --refazer --exigir-meta   # o que o CI roda (avaliacao-chat.yml)

Com --exigir-meta, o código de saída diz o resultado: 0 meta cumprida, 10 meta não cumprida, 11 rodada incompleta
(Gemini indisponível; o CI espera e continua sem --refazer, aproveitando o que ficou guardado).
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


# Códigos de saída com --exigir-meta, para o CI separar o que é qualidade do chat do que é a API fora do ar. Longe de
# 1 (erro inesperado do Python) e 2 (linha de comando errada, argparse): um bug no script não vira "meta não cumprida".
META_CUMPRIDA, META_NAO_CUMPRIDA, INCOMPLETA = 0, 10, 11
MENSAGEM_SAIDA = {
    META_NAO_CUMPRIDA: "meta da avaliação NÃO cumprida: veja eval/resultado_avaliacao.md",
    INCOMPLETA: "rodada incompleta: o Gemini ficou indisponível (não mede a qualidade do chat); rode de novo sem "
                "--refazer para continuar de onde parou",
}


def codigo_de_saida(cumprida: bool | None) -> int:
    """`main` devolve True (meta cumprida), False (não cumprida) ou None (a versão (c) não ficou completa)."""
    return {True: META_CUMPRIDA, False: META_NAO_CUMPRIDA}.get(cumprida, INCOMPLETA)


def passageiro(e: llm.LLMIndisponivel) -> bool:
    """Falha que costuma passar sozinha: cota esgotada (429), demora ou servidor ocupado (HTTP 5xx, como o 503 de
    "high demand"). Outros erros (pedido inválido, chave errada) não melhoram esperando."""
    return e.motivo in ("cota", "lento") or (e.motivo == "erro" and "(HTTP 5" in str(e))


def perguntar(p: dict, versao: str, con, c: dict, dormir=None) -> dict:
    """Uma pergunta, com novas tentativas depois de falha passageira (`avaliacao.tentativas`, esperando
    `espera_cota_s` vezes o número da tentativa). Levanta LLMIndisponivel se não der."""
    tentativas = int(c["avaliacao"]["tentativas"])
    for tentativa in range(1, tentativas + 1):
        t = time.time()
        try:
            r = chat.responder(p["pergunta"], con, versao=versao)
            return {"resposta": r.texto, "segundos": round(time.time() - t, 1), "apoio": chat.apoio(r),
                    "ferramentas": [{"ferramenta": x["ferramenta"], "argumentos": x["argumentos"]} for x in r.chamadas]}
        except llm.LLMIndisponivel as e:
            if not passageiro(e) or tentativa == tentativas:
                raise
            espera = int(c["avaliacao"]["espera_cota_s"]) * tentativa
            print(f"   {e.motivo} ({tentativa}/{tentativas}); esperando {espera} s para tentar de novo", flush=True)
            (dormir or time.sleep)(espera)   # time.sleep lido na hora: os testes o trocam


def corrigir(p: dict, r: dict, versao: str) -> dict:
    inventados = avaliacao.numeros_sem_apoio(r["resposta"], " ".join([r["apoio"], p["pergunta"],
                                                                     chat.prompt_sistema(versao)]))
    return {**r, "numeros_inventados": inventados, "fonte": avaliacao.tem_fonte(r["resposta"]),
            "certo": avaliacao.corrigir(r["resposta"], p["criterio"], p["esperado"]) and not inventados}


def main(versoes: list[str], limite: int | None, refazer: bool, so_relatorio: bool) -> bool | None:
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
    return relatorio(perguntas, resultados, versoes, sha, c, parou)


def _pct(a: int, b: int) -> str:
    # uma casa decimal: 44/52 é 84.6%, abaixo da meta de 85%; arredondado, "85%" parecia cumprir (2026-11-11)
    return f"{a}/{b} ({100 * a / b:.1f}%)" if b else "—"


def _intervalo(feitas: list[dict], conf: float) -> str:
    if not feitas:
        return "—"
    lo, hi = avaliacao.intervalo_wilson(sum(r["certo"] for r in feitas), len(feitas), conf)
    return f"{100 * lo:.0f}% a {100 * hi:.0f}%"


def margem_de_erro(perguntas: list[dict], resultados: dict, versoes: list[str], conf: float,
                   margem_alvo: float) -> list[str]:
    """Seção "Margem de erro" (Miller, 2024): intervalo de Wilson, erro-padrão agrupado por tipo de pergunta,
    comparação pareada entre as versões e quantas perguntas dariam a margem alvo. Só com as versões completas."""
    completas = [v for v in versoes if len(resultados[v]) == len(perguntas)]
    if not completas:
        return []
    ids = [p["id"] for p in perguntas]
    linhas = ["", "## Margem de erro", "",
              f"Com {len(ids)} perguntas, o acerto de uma rodada tem margem de erro grande. Seguindo Miller (2024, "
              "\"Adding Error Bars to Evals\", arXiv:2411.00640): intervalo de Wilson, erro-padrão agrupado por tipo de "
              "pergunta (as do mesmo tipo não são independentes) e comparação pareada (as mesmas perguntas nas duas "
              f"versões). Nível de confiança: {conf:.0%} (`config/llm.yaml`). Uma rodada só, com temperatura 0: a "
              "variação entre rodadas do modelo ainda não está medida.", "",
              "| Versão | Acerto | Intervalo (Wilson) | Erro-padrão agrupado por tipo |", "|---|---|---|---|"]
    for v in completas:
        certos = [bool(resultados[v][i]["certo"]) for i in ids]
        grupos: dict[str, list[bool]] = {}
        for p in perguntas:
            grupos.setdefault(p["tipo"], []).append(bool(resultados[v][p["id"]]["certo"]))
        lo, hi = avaliacao.intervalo_wilson(sum(certos), len(certos), conf)
        ep = avaliacao.erro_padrao_agrupado(grupos)
        linhas.append(f"| {chat.VERSOES[v]} | {100 * sum(certos) / len(certos):.1f}% | {100 * lo:.1f}% a "
                      f"{100 * hi:.1f}% | {100 * ep:.1f} pontos |")
    if "c" in completas:
        pares = [v for v in completas if v != "c"]
        if pares:
            linhas += ["", "| Comparação (mesmas perguntas) | Diferença de acerto | Intervalo |", "|---|---|---|"]
            for v in pares:
                d, lo, hi = avaliacao.diferenca_pareada([bool(resultados[v][i]["certo"]) for i in ids],
                                                        [bool(resultados["c"][i]["certo"]) for i in ids], conf)
                linhas.append(f"| {chat.VERSOES['c']} − {chat.VERSOES[v]} | {100 * d:+.1f} pontos | "
                              f"{100 * lo:+.1f} a {100 * hi:+.1f} pontos |")
        acerto_c = sum(bool(resultados["c"][i]["certo"]) for i in ids) / len(ids)
        n = avaliacao.perguntas_para_margem(acerto_c, margem_alvo, conf)
        linhas += ["", f"Para a margem ficar em ±{100 * margem_alvo:.0f} pontos com acerto perto de "
                       f"{100 * acerto_c:.0f}%, seriam cerca de **{n} perguntas** (hoje, {len(ids)})."]
    return linhas


def relatorio(perguntas: list[dict], resultados: dict, versoes: list[str], sha: str, c: dict,
              parou: str | None) -> bool | None:
    """Grava eval/resultado_avaliacao.md. Devolve se a meta foi cumprida (None: rodada sem a versão (c) completa)."""
    ok = None
    av = c["avaliacao"]
    tipos = list(dict.fromkeys(p["tipo"] for p in perguntas))
    # data das respostas (guardadas com "em"); as feitas agora são de hoje. Refazer só o relatório não muda a data.
    hoje = f"{dt.date.today():%Y-%m-%d}"
    datas = sorted({str(r.get("em", hoje))[:10] for rs in resultados.values() for r in rs.values()}) or [hoje]
    quando = datas[0] if len(datas) == 1 else f"{datas[0]} a {datas[-1]}"
    linhas = [f"# Avaliação do chat ({quando})", "",
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
    conf = float(av["confianca"])
    medida(f"Acertos, intervalo de {conf:.0%}", lambda rs: _intervalo(feitas(rs), conf))
    if "c" in versoes and len(resultados["c"]) == len(perguntas):
        rc = resultados["c"]
        acerto = sum(r["certo"] for r in rc.values()) / len(rc)
        armadilhas = [p["id"] for p in perguntas if p["tipo"] == "armadilha"]
        inventou = [i for i in armadilhas if rc[i]["numeros_inventados"]]
        ok = acerto >= av["meta_acerto"] and not inventou
        linhas += ["", f"**Meta {'cumprida' if ok else 'NÃO cumprida'}:** (c) acertou "
                       f"{_pct(sum(r['certo'] for r in rc.values()), len(rc))} "
                       f"(meta {av['meta_acerto']:.0%}); armadilhas com número inventado: {inventou or 'nenhuma'}."]
    linhas += margem_de_erro(perguntas, resultados, versoes, conf, float(av["margem_alvo"]))
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
    return ok


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    sys.stderr.reconfigure(encoding="utf-8")
    a = argparse.ArgumentParser()
    a.add_argument("--versoes", default="abc", help="a (sem ferramentas), b (normas no prompt), c (com ferramentas)")
    a.add_argument("--limite", type=int, help="só as N primeiras perguntas")
    a.add_argument("--refazer", action="store_true", help="ignora as respostas guardadas em eval/respostas/")
    a.add_argument("--relatorio", action="store_true", help="só refaz o relatório com as respostas guardadas")
    a.add_argument("--exigir-meta", action="store_true",
                   help="sai com erro se a meta não for cumprida ou a rodada ficar incompleta (o CI usa)")
    x = a.parse_args()
    cumprida = main([v for v in x.versoes if v in chat.VERSOES], x.limite, x.refazer, x.relatorio)
    if x.exigir_meta and codigo_de_saida(cumprida):
        print(MENSAGEM_SAIDA[codigo_de_saida(cumprida)], file=sys.stderr)
        raise SystemExit(codigo_de_saida(cumprida))
