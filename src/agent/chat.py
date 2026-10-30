"""Chat do painel (E5; D-060): o Gemini entende a pergunta, chama as ferramentas e explica; nunca calcula (SPEC §5.2).

Três versões, para a avaliação (scripts/avaliar_chat.py):
- (a) "a": o mesmo modelo, sem ferramentas e sem normas;
- (b) "b": sem ferramentas, com o texto das normas no prompt (config/llm.yaml, `avaliacao.normas_no_prompt`);
- (c) "c": com as 5 ferramentas e o prompt do agente (config/prompts/agente_sistema.md). É a versão do painel.
`responder_em_partes` é a mesma resposta em streaming, para a página mostrar o texto enquanto ele chega (D-069).
`responder_sem_modelo` responde uma pergunta pronta direto pela ferramenta, com os mesmos números e fontes (D-063).
"""
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import duckdb

from src import llm
from src.agent import ferramentas

RAIZ = llm.RAIZ
VERSOES = {"a": "(a) sem ferramentas", "b": "(b) normas no prompt", "c": "(c) com ferramentas"}
SEM_DADO = "Não foi possível encontrar essa resposta nos dados do painel."   # D-069 (prompt v3)
INDISPONIVEL = "O chat está indisponível no momento. Veja as respostas na aba Perguntas prontas."


@dataclass
class Resposta:
    texto: str
    chamadas: list[dict] = field(default_factory=list)   # [{"ferramenta", "argumentos", "resultado"}]
    com_modelo: bool = True
    etapas: list[dict] = field(default_factory=list)     # [{"etapa", "s"}]: tempos, para o log e a medição


def prompt_sistema(versao: str = "c") -> str:
    c = llm.config()
    if versao == "c":
        return (RAIZ / c["prompt_sistema"]).read_text(encoding="utf-8")
    texto = (RAIZ / "config" / "prompts" / "sem_ferramentas.md").read_text(encoding="utf-8")
    if versao == "b":
        normas = [ferramentas.NORMAS_DIR / ferramentas.NORMAS[n][0] for n in c["avaliacao"]["normas_no_prompt"]]
        texto += "".join(f"\n\n=== {ferramentas.NORMAS[n][1]} ===\n{a.read_text(encoding='utf-8')}"
                         for n, a in zip(c["avaliacao"]["normas_no_prompt"], normas))
    return texto


def _historico(historico: list[dict] | None) -> list[dict]:
    """Mensagens anteriores ({"role": "user"|"assistant", "content"}) no formato do Gemini, só o texto e só as últimas
    (`historico_mensagens` em config/llm.yaml)."""
    n = int(llm.config()["historico_mensagens"])
    return [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
            for m in (historico or [])[-n:] if m.get("content")]


# ------------------------------------------------------------------ ferramentas: cache e paralelo
_cache: dict = {}
_trava = threading.Lock()
CACHE_MAXIMO = 256   # resultados guardados por processo (cada um tem poucos KB)


def executar_com_cache(con: duckdb.DuckDBPyConnection, nome: str, argumentos, banco: str = "") -> dict:
    """`ferramentas.executar` com cache por (banco, ferramenta, argumentos): a mesma consulta não roda duas vezes no
    processo. `banco` identifica os dados (a página passa o modo e o caminho), para não misturar bancos."""
    if isinstance(argumentos, str):
        try:
            argumentos = json.loads(argumentos or "{}")
        except ValueError:
            argumentos = {}
    chave = (banco or str(id(con)), nome, json.dumps(argumentos or {}, sort_keys=True, ensure_ascii=False))
    with _trava:
        if chave in _cache:
            return _cache[chave]
    resultado = ferramentas.executar(con, nome, argumentos)
    with _trava:
        if len(_cache) >= CACHE_MAXIMO:
            _cache.pop(next(iter(_cache)))
        _cache[chave] = resultado
    return resultado


def _executar_pedidos(con, pedidos: list[dict], banco: str) -> list[dict]:
    """Executa os pedidos de ferramenta do modelo; vários de uma vez rodam em paralelo, cada um num cursor próprio
    (uma conexão DuckDB não deve ser usada por duas threads ao mesmo tempo)."""
    banco = banco or str(id(con))   # a chave do cache é a da conexão, não a do cursor de cada thread

    def um(p, c):
        return executar_com_cache(c, p["name"], p.get("args"), banco)
    if len(pedidos) == 1 or con is None:
        return [um(p, con) for p in pedidos]
    cursores = [con.cursor() for _ in pedidos]
    try:
        with ThreadPoolExecutor(max_workers=min(len(pedidos), 4)) as pool:
            return list(pool.map(um, pedidos, cursores))
    finally:
        for c in cursores:
            c.close()


# ------------------------------------------------------------------ resposta
def responder_em_partes(pergunta: str, con: duckdb.DuckDBPyConnection | None, historico: list[dict] | None = None,
                        versao: str = "c", banco: str = ""):
    """A resposta em streaming: ("texto", trecho) enquanto o texto chega, ("consultando", None) quando o modelo pede
    ferramentas (o texto mostrado até ali era preâmbulo e pode ser trocado) e ("fim", Resposta) no fim. Levanta
    llm.LLMIndisponivel se o Gemini não responder (sem chave, sem internet, demora, cota)."""
    sistema = prompt_sistema(versao)
    conteudos = [*_historico(historico), {"role": "user", "parts": [{"text": pergunta}]}]
    esquemas = ferramentas.ESQUEMAS if versao == "c" else None
    chamadas, etapas = [], []
    rodadas = int(llm.config()["max_rodadas_ferramentas"]) if esquemas else 0
    for rodada in range(rodadas + 1):
        ultima = rodada == rodadas
        t = time.perf_counter()
        msg = None
        if esquemas and rodada == 0:
            # a primeira chamada quase sempre só pede a ferramenta: sem streaming ela leva 0,8 s, com streaming 3,4 s
            # (medianas da reserva em 2026-10-28; D-069). Se ela já trouxer o texto, ele sai de uma vez
            msg = llm.conversar(conteudos, sistema, esquemas)
            if not llm.chamadas(msg) and llm.texto(msg):
                yield "texto", llm.texto(msg)
        else:   # a resposta escrita depois das ferramentas sai em streaming (primeiro texto em ≈ 1 s)
            for tipo, valor in llm.conversar_em_partes(conteudos, sistema, esquemas,
                                                       sem_ferramenta_agora=bool(esquemas) and ultima):
                if tipo == "texto":
                    yield "texto", valor
                else:
                    msg = valor
        etapas.append({"etapa": "modelo", "s": time.perf_counter() - t})
        pedidos = llm.chamadas(msg)
        if not pedidos or ultima:
            yield "fim", Resposta(llm.texto(msg), chamadas, etapas=etapas)
            return
        yield "consultando", None
        conteudos.append(msg)   # como veio: as assinaturas de raciocínio do Gemini precisam voltar
        t = time.perf_counter()
        resultados = _executar_pedidos(con, pedidos, banco)
        etapas.append({"etapa": f"ferramentas ({len(pedidos)})", "s": time.perf_counter() - t})
        partes = []
        for p, resultado in zip(pedidos, resultados):
            chamadas.append({"ferramenta": p["name"], "argumentos": p.get("args") or {}, "resultado": resultado})
            resposta = {"name": p["name"], "response": ferramentas.para_o_modelo(resultado)}
            if p.get("id"):
                resposta["id"] = p["id"]
            partes.append({"functionResponse": resposta})
        conteudos.append({"role": "user", "parts": partes})


def responder(pergunta: str, con: duckdb.DuckDBPyConnection | None, historico: list[dict] | None = None,
              versao: str = "c", banco: str = "") -> Resposta:
    """A resposta inteira de uma vez (avaliação e testes). Levanta llm.LLMIndisponivel se o Gemini não responder."""
    for tipo, valor in responder_em_partes(pergunta, con, historico, versao, banco):
        if tipo == "fim":
            return valor
    raise llm.LLMIndisponivel("erro", llm.MENSAGENS["erro"])


def apoio(resposta: Resposta) -> str:
    """Tudo o que as ferramentas devolveram nesta resposta, cru e como o modelo viu (para conferir se um número da
    resposta tem apoio)."""
    return " ".join(json.dumps([c["resultado"], ferramentas.para_o_modelo(c["resultado"])], ensure_ascii=False)
                    for c in resposta.chamadas)


def separar_fonte(texto: str) -> tuple[str, str]:
    """(corpo, linha de fonte): a página mostra a fonte numa linha pequena abaixo da resposta, não no meio do texto."""
    linhas = texto.rstrip().splitlines()
    for i in range(len(linhas) - 1, -1, -1):
        if re.match(r"^\W*fonte\b", linhas[i].strip(), re.I):
            fonte = " ".join(x.strip() for x in linhas[i:] if x.strip())
            return "\n".join(linhas[:i]).rstrip(), re.sub(r"^\W*", "", fonte).replace("**", "")
    return texto.strip(), ""


ROTULOS_SELO = {"projeção": "projecao", "faixa provável (P5–P95)": "faixa", "sensibilidade": "sensibilidade"}


def selos(chamadas: list[dict]) -> list[str]:
    """Selos do painel (src/painel/ui.SELOS) dos resultados usados: "projeção", "faixa provável", "sensibilidade"."""
    vistos = []
    for c in chamadas:
        s = ROTULOS_SELO.get(str((c.get("resultado") or {}).get("rotulo", "")))
        if s and s not in vistos:
            vistos.append(s)
    return vistos


# ------------------------------------------------------------------ perguntas prontas (D-063)
PULAR = {"uf", "valores", "tabela", "curva", "fonte", "data_referencia", "carga", "versao_premissas", "citar", "conta",
         "rotulo", "trechos"}


def _rotulo(chave: str) -> str:
    return chave.replace("_", " ").capitalize()


def _linhas_md(dados: dict, nivel: int = 0) -> list[str]:
    linhas = []
    for k, v in dados.items():
        if k in PULAR or v in (None, "", [], {}):
            continue
        recuo = "  " * nivel
        if isinstance(v, (str, int, float)):
            linhas.append(f"{recuo}- **{_rotulo(k)}:** {v}")
        elif isinstance(v, dict):
            linhas += [f"{recuo}- **{_rotulo(k)}:**", *_linhas_md(v, nivel + 1)]
        elif isinstance(v, list) and all(isinstance(x, str) for x in v):
            linhas += [f"{recuo}- **{_rotulo(k)}:**", *(f"{recuo}  - {x}" for x in v)]
    return linhas


def _tabela_md(tabela: list[dict]) -> list[str]:
    """As colunas de texto da tabela (os valores já formatados), se alguma delas trouxer valor (R$ ou %); uma tabela só
    com rótulos não ajuda sem o gráfico."""
    if not tabela or not isinstance(tabela[0], dict):
        return []
    colunas = [c for c in tabela[0] if all(isinstance(r.get(c), str) for r in tabela)]
    if len(colunas) < 2 or not any("R$" in r[c] or "%" in r[c] for c in colunas for r in tabela):
        return []
    linhas = ["| " + " | ".join(_rotulo(c) for c in colunas) + " |", "|" + "---|" * len(colunas)]
    for r in tabela[:ferramentas.LINHAS_TABELA]:
        linhas.append("| " + " | ".join(str(r[c]).replace("|", "/").replace("\n", " ") for c in colunas) + " |")
    return ["", *linhas]


def _trechos_md(trechos: list[dict]) -> list[str]:
    """Trechos de norma: norma e artigo em negrito e o texto do artigo (cortado), como na fonte oficial."""
    out = []
    for t in trechos:
        texto = re.sub(r"\s+", " ", t.get("texto", "")).strip()
        out.append(f"- **{t.get('norma', '')}, {str(t.get('artigo', '')).replace('Art.', 'art. ')}:** "
                   f"{texto[:500]}{'…' if len(texto) > 500 else ''}")
    return out


def formatar(resultado: dict, com_rotulo: bool = True) -> str:
    """O resultado de uma ferramenta em markdown: valores formatados, conta e a linha de fonte. `com_rotulo=False`:
    sem o rótulo em itálico (a página mostra o selo no lugar)."""
    if "erro" in resultado:
        return SEM_DADO
    linhas = []
    if com_rotulo and resultado.get("rotulo"):
        linhas.append(f"*{resultado['rotulo'].capitalize()}.*")
    linhas += _linhas_md(resultado)
    if isinstance(resultado.get("trechos"), list):
        linhas += _trechos_md(resultado["trechos"])
    if "numeros" not in resultado:
        linhas += _tabela_md(resultado.get("tabela") or [])
    elif isinstance(resultado["numeros"], list):
        linhas = [ln for ln in linhas if not ln.startswith("- **Numeros")]
        linhas += [f"{n['numero']}. **{n['rotulo']}:** {n['valor']} (mínimo {n['minimo']}, máximo {n['maximo']}; "
                   f"{n['natureza']})" for n in resultado["numeros"]]
    if resultado.get("conta"):
        linhas.append(f"\nConta: {resultado['conta']}.")
    if resultado.get("data_referencia"):   # a linha final do prompt do agente
        linhas.append(f"\nFonte: {resultado.get('fonte', '')} · referência: {resultado['data_referencia']} · "
                      f"premissas: v{resultado.get('versao_premissas', '?')}")
    elif resultado.get("citar"):
        linhas.append(f"\n{resultado['citar']}")
    return "\n".join(linhas)


def responder_sem_modelo(con: duckdb.DuckDBPyConnection | None, pronta: dict, banco: str = "",
                         com_rotulo: bool = True) -> Resposta:
    """Uma pergunta pronta de config/llm.yaml (`perguntas_prontas`), respondida direto pela ferramenta."""
    resultado = executar_com_cache(con, pronta["ferramenta"], pronta["argumentos"], banco)
    return Resposta(formatar(resultado, com_rotulo), [{"ferramenta": pronta["ferramenta"],
                                                       "argumentos": pronta["argumentos"], "resultado": resultado}],
                    com_modelo=False)
