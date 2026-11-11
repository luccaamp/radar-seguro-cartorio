"""Agente "o que mudou" a cada carga: compara dois conjuntos públicos (o publicado antes e o novo) e escreve o que
mudou para quem lê o painel.

Duas camadas, para que a IA nunca invente um número:
1. **Comparação determinística** (sem IA): data da carga, versão das premissas, datas de referência das fontes, os 10
   números oficiais antes e depois (pelas mesmas funções do painel) e as tabelas novas, retiradas ou com conteúdo
   diferente (pelo hash de conteúdo do manifesto). É o relatório de verdade.
2. **Resumo em linguagem simples (opcional, Gemini no nível gratuito):** o modelo recebe só o relatório da camada 1 e
   escreve 2 a 4 frases. Cada número do resumo precisa aparecer no relatório; se um não aparecer (número inventado
   ou recalculado), o resumo é descartado e fica só o relatório. Sem chave, também fica só o relatório.

Uso: scripts/o_que_mudou.py. Testes: tests/test_o_que_mudou.py (sem a API: o modelo é um dublê).
"""
import re
from pathlib import Path
from typing import Callable

import duckdb

from src import publico

NUMERO = re.compile(r"\d+(?:[.,]\d+)*")
SISTEMA = (
    "Você resume, para um leitor leigo, o que mudou entre duas cargas de dados de um painel público sobre o seguro "
    "obrigatório dos cartórios de Minas Gerais. Escreva de 2 a 4 frases em português do Brasil, sem títulos nem listas. "
    "Use SOMENTE os números que aparecem no relatório, copiados exatamente como estão (não arredonde, não some, não "
    "calcule percentuais novos). Se nada mudou nos 10 números, diga isso primeiro. Não cite nomes de pessoas.")


def _numeros(pasta: Path) -> list[dict]:
    from src.painel import analises
    con = duckdb.connect(str(publico.banco_demonstracao(pasta)), read_only=True)
    try:
        return analises.numeros_oficiais(con)["numeros"]
    finally:
        con.close()


def _colunas(arquivo: Path) -> list[str]:
    if not arquivo.exists():
        return []
    with duckdb.connect() as con:
        return [d[0] for d in con.execute(f"SELECT * FROM read_parquet('{arquivo.as_posix()}') LIMIT 0").description]


def comparar(antes: Path, depois: Path, numeros: Callable[[Path], list[dict]] = _numeros) -> dict:
    """O que mudou de `antes` para `depois` (pastas de conjunto público, cada uma com o manifesto)."""
    ma, md = publico.ler_manifesto(antes), publico.ler_manifesto(depois)
    if not ma or not md:
        raise FileNotFoundError("as duas pastas precisam do manifesto.json do conjunto público")
    ta = {a["tabela"]: a for a in ma["arquivos"]}
    td = {a["tabela"]: a for a in md["arquivos"]}
    mudaram = []
    for t in sorted(ta.keys() & td.keys()):
        if ta[t].get("sha256_conteudo") == td[t].get("sha256_conteudo"):
            continue
        ca, cd = _colunas(antes / ta[t]["arquivo"]), _colunas(depois / td[t]["arquivo"])
        mudaram.append({"tabela": t, "linhas_antes": ta[t].get("linhas"), "linhas_depois": td[t].get("linhas"),
                        "colunas_novas": [c for c in cd if c not in ca], "colunas_retiradas": [c for c in ca if c not in cd]})
    fa = {f["fonte"]: f.get("data_referencia") for f in ma.get("fontes", [])}
    fd = {f["fonte"]: f.get("data_referencia") for f in md.get("fontes", [])}
    fontes = [{"fonte": f, "antes": fa.get(f), "depois": fd.get(f)} for f in sorted(fa.keys() | fd.keys())
              if fa.get(f) != fd.get(f)]
    na = {n["chave"]: n for n in numeros(antes)}
    nd = {n["chave"]: n for n in numeros(depois)}
    dez = []
    for chave, n in nd.items():
        a = na.get(chave)
        base_a, base_d = (a or {}).get("base_cru"), n.get("base_cru")
        var = (base_d / base_a - 1) if base_a not in (None, 0) and base_d is not None else None
        dez.append({"numero": n["numero"], "rotulo": n["rotulo"], "antes": (a or {}).get("valor"),
                    "depois": n["valor"], "mudou": a is None or a.get("valor") != n["valor"],
                    "variacao": var})
    return {"carga": (ma.get("carga"), md.get("carga")),
            "premissas": (ma.get("versao_premissas"), md.get("versao_premissas")),
            "numeros": dez, "fontes": fontes,
            "tabelas_novas": sorted(td.keys() - ta.keys()), "tabelas_retiradas": sorted(ta.keys() - td.keys()),
            "tabelas_mudaram": mudaram}


def _pct(v: float) -> str:
    return f"{v * 100:+.1f}%".replace(".", ",")


def relatorio(d: dict) -> str:
    """O relatório determinístico em Markdown (a camada 1)."""
    (ca, cd), (pa, pd_) = d["carga"], d["premissas"]
    mudaram = [n for n in d["numeros"] if n["mudou"]]
    linhas = [f"Carga de **{cd}**, comparada com a de **{ca}**. Premissas: versão {pd_}"
              + (f" (antes, {pa})." if pa != pd_ else " (a mesma)."), ""]
    linhas.append(f"**Os 10 números oficiais:** {len(mudaram)} mudaram." if mudaram
                  else "**Os 10 números oficiais:** nenhum mudou.")
    if mudaram:
        linhas += ["", "| # | Número | Antes | Depois | Variação |", "|---|---|---|---|---|"]
        linhas += [f"| {n['numero']} | {n['rotulo']} | {n['antes'] or '—'} | {n['depois']} | "
                   f"{_pct(n['variacao']) if n['variacao'] is not None else '—'} |" for n in mudaram]
    if d["fontes"]:
        linhas += ["", "**Datas de referência das fontes que mudaram:**"]
        linhas += [f"- {f['fonte']}: {f['antes'] or '—'} → {f['depois'] or '—'}" for f in d["fontes"]]
    t = d["tabelas_mudaram"]
    linhas += ["", f"**Tabelas publicadas:** {len(t)} com conteúdo diferente"
               + (f", {len(d['tabelas_novas'])} novas" if d["tabelas_novas"] else "")
               + (f", {len(d['tabelas_retiradas'])} retiradas" if d["tabelas_retiradas"] else "") + "."]
    for x in t:
        extra = "".join(f"; coluna{'s' if len(cs) > 1 else ''} {rot}: {', '.join(f'`{c}`' for c in cs)}"
                        for cs, rot in ((x.get("colunas_novas"), "nova"), (x.get("colunas_retiradas"), "retirada"))
                        if cs)
        linhas.append(f"- `{x['tabela']}`: {x['linhas_antes']} → {x['linhas_depois']} linhas{extra}")
    linhas += [f"- `{x}`: nova" for x in d["tabelas_novas"]] + [f"- `{x}`: retirada" for x in d["tabelas_retiradas"]]
    return "\n".join(linhas)


def numeros_sem_apoio(resumo: str, base: str) -> list[str]:
    """Números do resumo que não aparecem, inteiros, entre os números do relatório (a trava contra número inventado:
    "3" não passa só porque o relatório tem "341,1")."""
    do_relatorio = set(NUMERO.findall(base))
    return [n for n in NUMERO.findall(resumo) if n not in do_relatorio]


def resumir(d: dict, gerar: Callable[[str, str], str] | None = None) -> tuple[str, str | None]:
    """(relatório, resumo da IA ou None). `gerar(sistema, texto)` devolve o texto do modelo; sem ela, usa o Gemini
    (src/llm.py) se houver chave. Resumo com número sem apoio no relatório é descartado."""
    base = relatorio(d)
    if gerar is None:
        from src import llm
        if not llm.situacao()[0]:
            return base, None

        def gerar(sistema, texto):
            return llm.texto(llm.conversar([{"role": "user", "parts": [{"text": texto}]}], sistema))
    try:
        resumo = (gerar(SISTEMA, base) or "").strip()
    except Exception:   # a IA é opcional: indisponível, fica só o relatório
        return base, None
    if not resumo or numeros_sem_apoio(resumo, base):
        return base, None
    return base, resumo


def markdown(d: dict, resumo: str | None, base: str) -> str:
    cab = f"# O que mudou na carga de {d['carga'][1]}\n\n"
    ia = (f"> {resumo}\n>\n> *Resumo escrito pela IA (Gemini) a partir do relatório abaixo; cada número dele foi "
          f"conferido no relatório.*\n\n") if resumo else ""
    return cab + ia + base + "\n"
