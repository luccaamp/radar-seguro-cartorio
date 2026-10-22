"""Ferramentas do chat (E5): o LLM não calcula números; ele chama estas funções e explica o resultado (SPEC §5.2).

Regras (CLAUDE.md, D-026 a D-030):
- só leem tabelas do conjunto público já auditado (`config/publico.yaml`), por uma conexão só de leitura recebida de
  fora (a do painel); nenhuma tabela interna, nada de SQL livre (testado em tests/test_chat.py);
- sempre com a UF como parâmetro; hoje só MG tem dados (expansão na E7);
- regra v1 e mínimo/máximo só nos totais da UF (D-027): nenhuma ferramenta desce abaixo da UF, exceto as contagens por
  filtro que o auditor publicou (`publicado`);
- cada resultado traz os valores já formatados e a linha `citar` (fonte, carga e versão das premissas).
"""
import json
import re
import unicodedata
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[2]
NORMAS_DIR = RAIZ / "data" / "bronze" / "normas" / "2026-10-17"
UFS_COM_DADOS = ("MG",)
CENARIOS = {"mantem": "regra mantida", "suspende_8_17": "STF suspende os arts. 8º a 17",
            "parcial": "decisão parcial (fração do déficit exigida = suposição)"}
NORMAS = {"227": ("prov_227_2026_pagina.txt", "Prov. CNJ 227/2026"),
          "213": ("prov_213_2026_pagina.txt", "Prov. CNJ 213/2026 (texto compilado)"),
          "243": ("prov_243_2026_pagina.txt", "Prov. CNJ 243/2026")}
# valores aceitos nos filtros de contagem (as visões publicadas em gold.mercado_filtro_uf)
SINONIMOS = {
    "classe": {"1": "1", "2": "2", "3": "3", "indeterminada": "indeterminada"},
    "situacao": {"provido": "PROVIDO", "provida": "PROVIDO", "titular": "PROVIDO", "vago": "VAGO", "vaga": "VAGO",
                 "interino": "VAGO", "interina": "VAGO", "interinidade": "VAGO", "sob intervencao": "SOB INTERVENÇÃO",
                 "intervencao": "SOB INTERVENÇÃO", "conversao em diligencia": "CONVERSÃO EM DILIGÊNCIA",
                 "diligencia": "CONVERSÃO EM DILIGÊNCIA"},
    "atribuicao": {"notas": "notas", "tabelionato de notas": "notas", "registro civil": "rcpn", "rcpn": "rcpn",
                   "registro de imoveis": "ri", "imoveis": "ri", "ri": "ri", "protesto": "protesto",
                   "titulos e documentos": "rtd_rcpj", "pessoa juridica": "rtd_rcpj", "rtd": "rtd_rcpj",
                   "rcpj": "rtd_rcpj", "rtd_rcpj": "rtd_rcpj"},
}


# ------------------------------------------------------------------ formatação pt-BR (mesma do painel)
def _br(v: float, casas: int) -> str:
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def brl(v: float) -> str:
    a = abs(v)
    if a < 0.005:
        return "R$ 0"
    if a >= 1e9:
        return f"R$ {_br(v / 1e9, 2)} bi"
    if a >= 1e6:
        return f"R$ {_br(v / 1e6, 1)} mi"
    if a >= 1e3:
        return f"R$ {_br(v / 1e3, 1)} mil"
    return f"R$ {_br(v, 2)}"


def aprox(v: float) -> str:
    return f"≈ {_br(v, 1 if abs(v) < 10 else 0)}"


def pct(v: float) -> str:
    return f"{_br(100 * v, 1)}%"


def _sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower()) if unicodedata.category(c) != "Mn").strip()


# ------------------------------------------------------------------ apoio
def _uf(uf: str) -> str | None:
    u = str(uf or "").strip().upper()
    return u if u in UFS_COM_DADOS else None


def _sem_uf(uf: str) -> dict:
    return {"erro": f"Sem dados para a UF {uf!r}: o projeto cobre só MG por enquanto (expansão estado por estado na "
                    "E7 do roteiro). Diga que não há dado para essa UF."}


def _citar(con, tabela: str) -> str:
    versao, executado = con.execute("SELECT versao_premissas, executado_em FROM gold.execucao "
                                    "WHERE regra_classe = 'v2'").fetchone()
    return (f"Fonte: {tabela} (CNJ/Justiça Aberta, RAIS/PDET e SUSEP SES; estimativa de mercado com premissas "
            f"públicas); carga {executado:%Y-%m-%d}; premissas v{versao}.")


def _uf_linhas(con, cenario: str, regra: str = "v2") -> dict:
    df = con.execute("SELECT * FROM gold.fato_mercado_uf WHERE regra_classe = ? AND cenario_stf = ?",
                     [regra, cenario]).df()
    return {r["nivel"]: r for _, r in df.iterrows()}


def _com_faixa(niveis: dict, coluna: str, fmt) -> str:
    """Valor base primeiro e a faixa depois, num texto só (o modelo copia os dois juntos)."""
    base, minimo, maximo = (fmt(niveis[n][coluna]) for n in ("base", "min", "max"))
    return f"{base} no cenário base (faixa: {minimo} a {maximo})"


def _premissas(con) -> dict:
    (conteudo,) = con.execute("SELECT conteudo_json FROM estado.premissas_versoes ORDER BY versao DESC LIMIT 1").fetchone()
    return json.loads(conteudo)["premissas"]


# ------------------------------------------------------------------ as 5 ferramentas
def _recorte(texto: str) -> tuple[str, str] | None:
    """'vago', 'Classe 3', 'interino', 'registro de imóveis'... -> (filtro, valor) da visão publicada; None se não achar."""
    for parte in re.split(r"[/,(]| ou ", _sem_acento(texto)):
        parte = parte.strip(" )")
        for f, valores in SINONIMOS.items():
            chave = re.sub(r"^classe\s*", "", parte) if f == "classe" else parte
            if chave in valores and (f != "classe" or parte.startswith("classe")):
                return f, valores[chave]
    return None


def contar_serventias(con: duckdb.DuckDBPyConnection, uf: str, recorte: str = "total") -> dict:
    """Serventias ativas e empregados CLT da UF (recorte "total") ou de um recorte publicado (classe, situação ou
    atribuição)."""
    if not _uf(uf):
        return _sem_uf(uf)
    if _sem_acento(recorte or "total") in ("total", "todas", "todos", ""):
        base = _uf_linhas(con, "mantem")["base"]
        return {"uf": "MG", "recorte": "total da UF", "serventias_ativas": _br(base["n_serventias_ativas"], 0),
                "empregados_clt": _br(base["clt"], 0), "citar": _citar(con, "gold.fato_mercado_uf")}
    achado = _recorte(recorte)
    if achado is None:
        return {"erro": f"recorte {recorte!r} não existe; use um destes: {RECORTES}"}
    f, v = achado
    linha = con.execute("SELECT publicado, n_serventias_ativas, clt FROM gold.mercado_filtro_uf WHERE visao = ? "
                        "AND regra_classe = 'v2' AND nivel = 'base'", [f"{f}={v}"]).fetchone()
    if linha is None or not linha[0]:
        return {"erro": "contagem não publicada (suprimida pelo auditor de LGPD)"}
    r = {"uf": "MG", "recorte": f"{f} = {v}", "serventias_ativas_no_recorte": _br(linha[1], 0),
         "empregados_clt_no_recorte": _br(linha[2], 0)}
    if f == "classe":
        r["observacao"] = "classe pela regra v2 (Prov. 243, Classe 1 até R$ 300 mil por semestre), aproximada"
    return {**r, "citar": _citar(con, "gold.mercado_filtro_uf")}


def passivo_e_obrigadas(con: duckdb.DuckDBPyConnection, uf: str) -> dict:
    """Passivo trabalhista estimado (todas as ativas e só as obrigadas) e o número de obrigadas pelo Prov. 227."""
    if not _uf(uf):
        return _sem_uf(uf)
    n = _uf_linhas(con, "mantem")
    faixa = lambda col, fmt: _com_faixa(n, col, fmt)  # noqa: E731
    return {"uf": "MG", "obrigadas_prov_227": faixa("n_universo", aprox),
            "passivo_todas_as_ativas": faixa("passivo_todas", brl),
            "passivo_das_obrigadas": faixa("passivo_universo", brl),
            "observacao": "obrigadas = sem interinos e sem Classe 1 (art. 19 do 227); classe aproximada",
            "citar": _citar(con, "gold.fato_mercado_uf")}


def deficit_e_mercado(con: duckdb.DuckDBPyConnection, uf: str, cenario_stf: str = "mantem") -> dict:
    """Serventias com déficit, déficit, importância segurada e prêmio anual, num cenário do STF."""
    if not _uf(uf):
        return _sem_uf(uf)
    c = _sem_acento(cenario_stf or "mantem").replace(" ", "_")
    c = {"mantida": "mantem", "regra_mantida": "mantem", "suspende": "suspende_8_17", "suspensao": "suspende_8_17",
         "decisao_parcial": "parcial"}.get(c, c)
    if c not in CENARIOS:
        return {"erro": f"cenário {cenario_stf!r} não existe; use {list(CENARIOS)}"}
    n = _uf_linhas(con, c)
    faixa = lambda col, fmt: _com_faixa(n, col, fmt)  # noqa: E731
    return {"uf": "MG", "cenario_stf": CENARIOS[c], "serventias_com_deficit": faixa("n_deficit", aprox),
            "deficit": faixa("valor_descoberto", brl),
            "importancia_segurada_mercado": faixa("mercado_importancia_segurada", brl),
            "premio_anual_mercado": faixa("mercado_premio_emitido", brl),
            "premio_anual_seguradora_hipotetica": faixa("seguradora_premio_emitido", brl),
            "citar": _citar(con, "gold.fato_mercado_uf")}


def simular(con: duckdb.DuckDBPyConnection, uf: str, taxa: float | None = None, market_share: float | None = None,
            cenario_stf: str = "mantem") -> dict:
    """Prêmio do mercado e da seguradora hipotética com outra taxa e outro market share (nível base, regra v2)."""
    if not _uf(uf):
        return _sem_uf(uf)
    c = _sem_acento(cenario_stf or "mantem").replace(" ", "_")
    c = {"mantida": "mantem", "suspende": "suspende_8_17", "decisao_parcial": "parcial"}.get(c, c)
    if c not in CENARIOS:
        return {"erro": f"cenário {cenario_stf!r} não existe; use {list(CENARIOS)}"}
    p = _premissas(con)
    fracao = lambda x, padrao: padrao if x is None else (float(x) / 100 if float(x) > 1 else float(x))  # noqa: E731
    t = fracao(taxa, p["taxa_seguro_anual"]["valores"]["base"])
    s = fracao(market_share, p["market_share_hipotetico"]["valores"]["base"])
    if not (0 < t <= 0.2 and 0 < s <= 1):
        return {"erro": "taxa entre 0% e 20% e market share entre 0% e 100%"}
    is_ = float(_uf_linhas(con, c)["base"]["mercado_importancia_segurada"])
    premio = is_ * t
    custos = sum(float(p[k]["valores"]["base"]) for k in ("sinistralidade", "comissao", "despesa_administrativa"))
    return {"uf": "MG", "cenario_stf": CENARIOS[c], "taxa": pct(t), "market_share": pct(s),
            "importancia_segurada_mercado": brl(is_), "premio_anual_mercado": brl(premio),
            "premio_anual_seguradora_hipotetica": brl(premio * s),
            "resultado_tecnico_mercado": brl(premio * (1 - custos)),
            "conta": f"prêmio = IS {brl(is_)} × taxa {pct(t)}; seguradora = prêmio × {pct(s)}",
            "observacao": "resultado técnico antes de impostos, resseguro e capital; nível base, regra v2",
            "citar": _citar(con, "gold.fato_mercado_uf e premissas vigentes")}


# palavras da pergunta que o texto da norma diz de outro jeito (busca simples, sem embeddings; SPEC §5.2)
SINONIMOS_NORMA = {"fora": ["nao se aplicam"], "excluidas": ["nao se aplicam"], "isentas": ["nao se aplicam"],
                   "limite": ["nao superior"], "teto": ["nao superior"], "valor": ["corresponder"],
                   "prazo": ["validade", "prazo"], "fianca": ["fianca bancaria"], "seguro": ["seguro-garantia"]}


def _artigos(arquivo: Path) -> tuple[str, list[tuple[str, str]]]:
    texto = arquivo.read_text(encoding="utf-8")
    fonte = re.search(r"\nFonte\n(.+)", texto)
    partes = re.split(r"(?m)^(Art\.\s*\d+[ºo°]?)", texto)
    artigos = [(partes[i].replace(" ", ""), (partes[i] + partes[i + 1]).strip()) for i in range(1, len(partes), 2)]
    return (fonte.group(1).strip() if fonte else ""), artigos


def buscar_norma(pergunta: str, provimento: str | None = None) -> dict:
    """Até 3 trechos (artigos) dos Provimentos 227, 213 e 243 mais ligados à pergunta, com norma, artigo e publicação.
    Texto oficial coletado em atos.cnj.jus.br (bronze, 2026-10-17)."""
    citados = [n for n in NORMAS if n in str(provimento or "") + " " + str(pergunta)]
    escolhidos = citados or list(NORMAS)
    if not all((NORMAS_DIR / NORMAS[n][0]).exists() for n in escolhidos):
        return {"erro": "o texto das normas não está nesta instalação (bronze ausente); diga que não sabe"}
    termos = [t for t in re.findall(r"\w{4,}", _sem_acento(pergunta)) if t not in
              {"qual", "quais", "como", "para", "pelo", "pela", "sobre", "provimento", "cartorio", "cartorios",
               "serventia", "serventias", "artigo", "norma", "isso", "esse", "essa", "pode", "quem", "deve"}]
    termos += [s for t in list(termos) for s in SINONIMOS_NORMA.get(t, [])]
    art_pedido = re.search(r"art(?:igo|\.)?\s*(\d+)", _sem_acento(pergunta))
    achados = []
    for n in escolhidos:
        fonte, artigos = _artigos(NORMAS_DIR / NORMAS[n][0])
        for rotulo, corpo in artigos:
            alvo = _sem_acento(corpo)
            # termos diferentes presentes pesam mais que repetições; a densidade desempata (artigos longos não ganham)
            presentes = sum(1 for t in set(termos) if t in alvo)
            nota = presentes + min(sum(alvo.count(t) for t in termos) / max(len(alvo), 1) * 200, 0.99) if presentes else 0
            if art_pedido and re.fullmatch(rf"Art\.{art_pedido.group(1)}[ºo°]?", rotulo):
                nota += 50
            if nota:
                achados.append((nota, NORMAS[n][1], rotulo, corpo, fonte))
    achados.sort(key=lambda a: -a[0])
    if not achados:
        return {"erro": "nenhum artigo encontrado para a pergunta; diga que não sabe"}
    return {"trechos": [{"norma": norma, "artigo": rot, "publicacao": fonte, "texto": corpo[:1200]}
                        for _, norma, rot, corpo, fonte in achados[:3]],
            "citar": (f"Fonte: {achados[0][1]}, {achados[0][2].replace('.', '. ')} (texto oficial em atos.cnj.jus.br, "
                      "coletado em 2026-10-17). Não é parecer jurídico.")}


RECORTES = ["total", "classe 1", "classe 2", "classe 3", "classe indeterminada", "provido", "vago",
            "sob intervencao", "conversao em diligencia", "notas", "registro civil", "registro de imoveis", "protesto",
            "titulos e documentos"]
FERRAMENTAS = {"contar_serventias": contar_serventias, "passivo_e_obrigadas": passivo_e_obrigadas,
               "deficit_e_mercado": deficit_e_mercado, "simular": simular, "buscar_norma": buscar_norma}
SEM_CONEXAO = {"buscar_norma"}

_UF = {"type": "string", "description": "sigla da UF; hoje só MG tem dados"}
_CENARIO = {"type": "string", "enum": list(CENARIOS),
            "description": "cenário do STF: mantem (regra mantida), suspende_8_17 (arts. 8º a 17 suspensos), parcial"}
ESQUEMAS = [
    {"type": "function", "function": {
        "name": "contar_serventias",
        "description": "Conta as serventias (cartórios) ativas e os empregados CLT de uma UF, no total ou num recorte "
                       "(classe, situação jurídica ou atribuição). Contagens são totais, não dados de um cartório. "
                       "Use recorte 'total' quando a pergunta não pedir recorte; 'vago' = interino.",
        "parameters": {"type": "object", "properties": {
            "uf": _UF, "recorte": {"type": "string", "enum": RECORTES, "description": "total ou um recorte da lista"}},
            "required": ["uf", "recorte"]}}},
    {"type": "function", "function": {
        "name": "passivo_e_obrigadas",
        "description": "Passivo trabalhista estimado (de todas as serventias ativas e só das obrigadas) e quantas "
                       "serventias são obrigadas pelo Provimento 227, com a faixa mínimo a máximo.",
        "parameters": {"type": "object", "properties": {"uf": _UF}, "required": ["uf"]}}},
    {"type": "function", "function": {
        "name": "deficit_e_mercado",
        "description": "Serventias com déficit, valor do déficit, importância segurada (IS) e prêmio anual do "
                       "mercado e da seguradora hipotética, num cenário do STF, com a faixa mínimo a máximo.",
        "parameters": {"type": "object", "properties": {"uf": _UF, "cenario_stf": _CENARIO}, "required": ["uf"]}}},
    {"type": "function", "function": {
        "name": "simular",
        "description": "Simula o prêmio anual do mercado e da seguradora hipotética com outra taxa (% da importância "
                       "segurada) e outro market share (%). Sem um deles, usa o valor das premissas.",
        "parameters": {"type": "object", "properties": {
            "uf": _UF, "taxa": {"type": "number", "description": "taxa anual em %, ex.: 3 para 3%"},
            "market_share": {"type": "number", "description": "market share da seguradora hipotética em %, ex.: 10"},
            "cenario_stf": _CENARIO}, "required": ["uf"]}}},
    {"type": "function", "function": {
        "name": "buscar_norma",
        "description": "Busca trechos (artigos) dos Provimentos CNJ 227/2026, 213/2026 e 243/2026 que respondem a "
                       "uma pergunta sobre as regras: garantia e seguro, fiança, solvência, prazos, classes e limites de "
                       "receita das classes, quem está fora do 227.",
        "parameters": {"type": "object", "properties": {
            "pergunta": {"type": "string"}, "provimento": {"type": "string", "enum": list(NORMAS)}},
            "required": ["pergunta"]}}},
]


def executar(con: duckdb.DuckDBPyConnection, nome: str, argumentos: dict | str | None) -> dict:
    """Executa uma chamada de ferramenta do modelo; erro vira resposta, nunca exceção."""
    if nome not in FERRAMENTAS:
        return {"erro": f"ferramenta {nome!r} não existe"}
    if isinstance(argumentos, str):
        try:
            argumentos = json.loads(argumentos or "{}")
        except ValueError:
            argumentos = {}
    funcao = FERRAMENTAS[nome]
    aceitos = funcao.__code__.co_varnames[:funcao.__code__.co_argcount]
    args = {k: v for k, v in (argumentos or {}).items() if k in aceitos and k != "con"}
    try:
        return funcao(**args) if nome in SEM_CONEXAO else funcao(con, **args)
    except (TypeError, ValueError, KeyError, duckdb.Error) as e:
        return {"erro": f"falha na ferramenta {nome}: {e}"}
