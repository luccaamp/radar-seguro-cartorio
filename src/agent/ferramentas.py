"""Ferramentas do chat (E5): o LLM não calcula números; ele chama estas funções e explica o resultado (SPEC §5.2).

Regras (CLAUDE.md, D-026 a D-030):
- só leem tabelas do conjunto público já auditado (`config/publico.yaml`), por uma conexão só de leitura recebida de
  fora (a do painel); nenhuma tabela interna, nada de SQL livre (testado em tests/test_chat.py);
- sempre com a UF como parâmetro; hoje só MG tem dados (expansão na E7);
- regra v1 e mínimo/máximo só nos totais da UF (D-027); abaixo da UF, as contagens por filtro que o auditor publicou
  (`publicado`) e, desde a D-048 (D-038), o resultado por serventia (`consultar_serventia`, pelo CNS ou pelo
  município; nunca nome de pessoa);
- cada resultado traz os valores já formatados e a linha `citar` (fonte, carga e versão das premissas).
"""
import inspect
import json
import re
import unicodedata
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[2]
# texto oficial das normas, versionado sem a assinatura (D-064; scripts/exportar_normas.py copia do bronze)
NORMAS_DIR = RAIZ / "data" / "normas" / "2026-10-17"
NORMAS_BRONZE = RAIZ / "data" / "bronze" / "normas" / "2026-10-17"
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
    """Valor base primeiro e os extremos depois, num texto só (o modelo copia os dois juntos). São os extremos teóricos
    da D-042 (todas as premissas no mínimo ou no máximo), não a faixa provável: no teste real de 2026-10-28, o rótulo
    antigo "faixa" levou o modelo a chamá-los de "faixa provável (P5–P95)" (D-069)."""
    base, minimo, maximo = (fmt(niveis[n][coluna]) for n in ("base", "min", "max"))
    return f"{base} no cenário base (extremos teóricos: {minimo} a {maximo}; não é a faixa provável)"


def _premissas(con) -> dict:
    (conteudo,) = con.execute("SELECT conteudo_json FROM estado.premissas_versoes ORDER BY versao DESC LIMIT 1").fetchone()
    return json.loads(conteudo)["premissas"]


# ------------------------------------------------------------------ consultas próprias do chat (D-036, D-048)
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
    r = {"uf": "MG", "cenario_stf": CENARIOS[c], "serventias_com_deficit": faixa("n_deficit", aprox),
         "deficit": faixa("valor_descoberto", brl),
         "importancia_segurada_mercado": faixa("mercado_importancia_segurada", brl),
         "premio_anual_mercado": faixa("mercado_premio_emitido", brl),
         "premio_anual_seguradora_hipotetica": faixa("seguradora_premio_emitido", brl),
         "citar": _citar(con, "gold.fato_mercado_uf")}
    if c == "mantem":
        # D-042 (D-069): base > faixa provável P5–P95 > extremos só se pedirem. A faixa provável é a mesma do painel
        # (analises.faixa_d042); os extremos ficam à parte (no teste real, o modelo os chamou de "faixa provável")
        from src.painel import analises
        for chave, (col, medida) in {"deficit": ("valor_descoberto", "deficit"),
                                     "importancia_segurada_mercado": ("mercado_importancia_segurada",
                                                                      "importancia_segurada"),
                                     "premio_anual_mercado": ("mercado_premio_emitido", "premio")}.items():
            f = analises.faixa_d042(con, "MG", medida)
            r[chave] = f"{brl(n['base'][col])} no cenário base; faixa provável (P5–P95): {f['faixa_provavel']}"
            r[f"{chave}_extremos_teoricos_so_se_pedirem"] = f"{brl(n['min'][col])} a {brl(n['max'][col])}"
    return r


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


def _obrigada(peso: float) -> str:
    if peso >= 1:
        return "sim"
    return "não" if peso <= 0 else f"talvez (classe indeterminada; peso {_br(peso, 2)} no universo)"


def consultar_serventia(con: duckdb.DuckDBPyConnection, uf: str, cns: str | None = None,
                        municipio: str | None = None) -> dict:
    """Resultado do modelo para um cartório (pelo CNS) ou a lista dos cartórios de um município (D-038, D-048):
    situação, classe aproximada, se é obrigado, passivo, déficit esperado, IS e prêmio (nível base, regra v2, STF
    mantém). Identifica o cartório pelo CNS e pelo município; não há nome de pessoa na tabela."""
    if not _uf(uf):
        return _sem_uf(uf)
    citar = _citar(con, "gold.serventia_publico")
    if cns:
        codigo = re.sub(r"\D", "", str(cns)).zfill(6)
        df = con.execute("SELECT * FROM gold.serventia_publico WHERE cns = ?", [codigo]).df()
        if df.empty:
            return {"erro": f"CNS {cns!r} não é de uma serventia ativa de MG nesta carga"}
        s = df.iloc[0]
        return {"uf": "MG", "cns": s["cns"], "municipio": s["municipio"], "regiao_imediata": s["regiao_imediata"],
                "situacao": s["situacao_juridica"], "atribuicoes": s["atribuicoes"],
                "empregados_clt": "não declarado" if s["clt"] != s["clt"] else _br(s["clt"], 0),
                "receita_semestral_2025": "sem receita válida" if s["receita_ref"] != s["receita_ref"]
                else brl(s["receita_ref"]),
                "classe": s["classe"], "obrigada_prov_227": _obrigada(float(s["peso_universo"])),
                "passivo_trabalhista": brl(s["passivo"]), "deficit_esperado": brl(s["valor_descoberto"]),
                "importancia_segurada": brl(s["importancia_segurada"]), "premio_anual": brl(s["premio_emitido"]),
                "observacao": "estimativas do modelo (nível base, regra v2, STF mantém); classe aproximada; o déficit "
                              "é um valor esperado (chance × parte descoberta), não o déficit real do cartório",
                "citar": citar}
    if municipio:
        df = con.execute("SELECT * FROM gold.serventia_publico ORDER BY cns").df()
        df = df[df["municipio"].map(lambda m: _sem_acento(str(m))) == _sem_acento(municipio)]
        if df.empty:
            return {"erro": f"município {municipio!r} sem serventia ativa em MG (confira a grafia)"}
        linhas = [{"cns": r["cns"], "situacao": r["situacao_juridica"], "classe": r["classe"],
                   "obrigada": _obrigada(float(r["peso_universo"])), "premio_anual": brl(r["premio_emitido"])}
                  for _, r in df.head(30).iterrows()]
        return {"uf": "MG", "municipio": df["municipio"].iloc[0], "serventias_ativas": _br(len(df), 0),
                "obrigadas": aprox(df["peso_universo"].sum()), "premio_anual_do_municipio": brl(df["premio_emitido"].sum()),
                "serventias": linhas, **({"observacao": "lista com as 30 primeiras, pela ordem do CNS"}
                                         if len(df) > 30 else {}),
                "citar": citar}
    return {"erro": "informe o CNS ou o município"}


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
        return {"erro": "o texto das normas não está nesta instalação (data/normas ausente); diga que não sabe"}
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
# consultas próprias do chat (anteriores à Etapa 3); as do painel vêm de src/painel/analises.py
PROPRIAS = {"contar_serventias": contar_serventias, "passivo_e_obrigadas": passivo_e_obrigadas,
            "deficit_e_mercado": deficit_e_mercado, "simular": simular, "buscar_norma": buscar_norma,
            "consultar_serventia": consultar_serventia}
PROPRIAS_SEM_CONEXAO = {"buscar_norma"}


# ------------------------------------------------------------------ as 5 ferramentas do chat (Etapa 5; D-062)
# Cada ferramenta agrupa consultas pelo tema do prompt (config/prompts/agente_sistema.md). As do painel chamam as
# mesmas funções que as páginas usam (src/painel/analises.py), para chat e painel mostrarem os mesmos números;
# tests/test_chat_cobertura.py falha se uma análise do painel ficar fora daqui.
CONSULTAS = {
    "consultar_numeros": {
        "numeros_oficiais": "os 10 números principais do painel (Início), com os extremos teóricos (não são a faixa "
                            "provável; para a faixa provável do déficit, da IS ou do prêmio, use faixa_d042)",
        "escada": "do passivo ao prêmio: cada degrau como parte do anterior (Início)",
        "faixa_d042": "déficit, importância segurada ou prêmio: valor base, faixa provável P5–P95, extremos e "
                      "sensibilidade (use `medida`)",
        "contar_serventias": "serventias ativas e empregados CLT, no total ou num recorte (use `recorte`)",
        "passivo_e_obrigadas": "passivo trabalhista (todas e obrigadas) e quantas são obrigadas pelo Prov. 227",
        "deficit_e_mercado": "serventias com déficit, déficit, importância segurada e prêmio num cenário do STF",
        "simular": "prêmio com outra taxa (%) e outro market share (%) (use `taxa` e `market_share`)",
    },
    "consultar_mercado": {
        "grupos": "os seis tipos de cartório (k-means, notebook 04) e o grupo-alvo do seguro (Mercado)",
        "quem_e_obrigado": "que parte é obrigada, por atribuição e por porte (Mercado)",
        "concentracao": "Gini e parte dos 10% maiores no passivo e no déficit (Análises)",
        "capacidade_pagar": "obrigadas por meses de saldo para cobrir o passivo (M1, Análises)",
        "consultar_serventia": "resultado do modelo para um cartório pelo CNS, ou a lista de um município "
                               "(use `cns` ou `municipio`)",
    },
    "consultar_analises": {
        "previsao_mercado": "projeção de 2026 ou 2027: obrigadas, subidas, passivo, déficit, IS e prêmio (use `ano` "
                            "e, se pedirem, `leitura_limite`)",
        "previsao_arrecadacao": "projeção da arrecadação semestral de MG 2026–27 com P10–P90",
        "subidas_comparacao": "subidas da Classe 1 para a 2: projeção principal e a recalibração (105 a 145) como "
                              "comparação",
        "passivo_m5": "quanto o passivo das obrigadas cresce em 2026 e 2027 (M5)",
        "tornado": "sensibilidade do prêmio a cada suposição (gráfico tornado)",
        "grade_taxa_adesao": "prêmio numa grade de taxa × parte do déficit que escolhe seguro",
        "premio_por_cenario_stf": "prêmio base e faixa em cada cenário do STF",
        "pergunta_9": "a seguradora tem lucro? sinistralidade por frequência × severidade",
    },
    "consultar_qualidade": {
        "qualidade_fontes": "data de referência de cada fonte, conferências entre fontes e contratos das tabelas",
        "lacunas": "o que os dados não respondem e a fonte que resolveria (notebook 09)",
        "escolhas_metodo_passivo": "passivo: escolhas de método (T5, T6, reserva no estado inteiro)",
        "leitura_literal_receita": "leitura literal do art. 2º, XXIV, do Prov. 213 (receita líquida)",
        "saltos_declaracao": "semestres com salto grosseiro na declaração e a sensibilidade sem eles",
        "clt_outros_estados": "erro do modelo de empregados CLT pela receita, para outros estados",
    },
    "consultar_decisoes": {
        "decisoes": "título das decisões de método que mudam a leitura do painel",
        "situacao_adi": "situação da ADI 8015 no STF e a data da conferência",
        "buscar_norma": "trechos dos Provimentos CNJ 227, 213 e 243 (use `pergunta` e, se souber, `provimento`)",
    },
}
DESCRICOES = {
    "consultar_numeros": "Números gerais e os 10 indicadores do painel: serventias, CLT, obrigadas, passivo, déficit, "
                         "importância segurada, prêmio, teto, contagens por recorte e simulação de taxa.",
    "consultar_mercado": "Mercado: tipos de cartório (grupos), grupo-alvo, quem é obrigado, concentração, capacidade "
                         "de pagar e o resultado por cartório (pelo CNS ou pelo município).",
    "consultar_analises": "Projeções 2026–27, sensibilidades (tornado), cenários do STF, grade de taxa e o lucro da "
                          "seguradora.",
    "consultar_qualidade": "Qualidade e lacunas dos dados: datas de referência das fontes, conferências, escolhas de "
                           "método, saltos na declaração, o que os dados não respondem.",
    "consultar_decisoes": "Decisões de método do projeto, normas (Provimentos 227, 213 e 243) e situação da ADI 8015.",
}
PARAMETROS = {   # parâmetro → (esquema, ferramentas que o aceitam)
    "uf": ({"type": "string", "description": "sigla da UF; hoje só MG tem dados (padrão MG)"},
           ("consultar_numeros", "consultar_mercado", "consultar_analises", "consultar_qualidade")),
    "medida": ({"type": "string", "enum": ["premio", "deficit", "importancia_segurada"],
                "description": "para faixa_d042"}, ("consultar_numeros",)),
    "recorte": ({"type": "string", "enum": RECORTES, "description": "para contar_serventias; 'vago' = interino"},
                ("consultar_numeros",)),
    "cenario_stf": ({"type": "string", "enum": list(CENARIOS), "description": "mantem, suspende_8_17 ou parcial"},
                    ("consultar_numeros",)),
    "taxa": ({"type": "number", "description": "para simular: taxa anual em %, ex.: 3 para 3%"}, ("consultar_numeros",)),
    "market_share": ({"type": "number", "description": "para simular: market share em %, ex.: 10"},
                     ("consultar_numeros",)),
    "cns": ({"type": "string", "description": "CNS do cartório (6 dígitos)"}, ("consultar_mercado",)),
    "municipio": ({"type": "string", "description": "nome do município de MG"}, ("consultar_mercado",)),
    "ano": ({"type": "integer", "description": "para previsao_mercado: 2026 ou 2027"}, ("consultar_analises",)),
    "leitura_limite": ({"type": "string", "description": "para previsao_mercado: leitura do limite de classe (fixo "
                                                         "ou corrigido); sem ela, usa a principal"},
                       ("consultar_analises",)),
    "pergunta": ({"type": "string", "description": "para buscar_norma: a pergunta sobre a norma"},
                 ("consultar_decisoes",)),
    "provimento": ({"type": "string", "enum": list(NORMAS), "description": "para buscar_norma"},
                   ("consultar_decisoes",)),
}
FERRAMENTAS = list(CONSULTAS)


def _esquema(nome: str) -> dict:
    opcoes = CONSULTAS[nome]
    props = {"analise": {"type": "string", "enum": list(opcoes),
                         "description": "; ".join(f"{k}: {v}" for k, v in opcoes.items())}}
    props |= {p: esquema for p, (esquema, onde) in PARAMETROS.items() if nome in onde}
    return {"name": nome, "description": DESCRICOES[nome],
            "parameters": {"type": "object", "properties": props, "required": ["analise"]}}


ESQUEMAS = [_esquema(n) for n in FERRAMENTAS]   # functionDeclarations do Gemini


def _funcao(analise: str):
    """(função, recebe conexão e UF?) de uma consulta."""
    from src.painel import analises
    if analise in analises.PARA_O_CHAT:
        return analises.PARA_O_CHAT[analise], True
    if analise in analises.SEM_CONEXAO:
        return analises.SEM_CONEXAO[analise], False
    if analise == "passivo_m5":
        return analises.passivo_m5, False
    return PROPRIAS[analise], analise not in PROPRIAS_SEM_CONEXAO


def alcancaveis() -> set[str]:
    """Nomes de todas as funções que o chat alcança pelas 5 ferramentas."""
    return {a for opcoes in CONSULTAS.values() for a in opcoes}


def executar(con: duckdb.DuckDBPyConnection, nome: str, argumentos: dict | str | None) -> dict:
    """Executa uma chamada de ferramenta do modelo; erro vira resposta, nunca exceção."""
    if isinstance(argumentos, str):
        try:
            argumentos = json.loads(argumentos or "{}")
        except ValueError:
            argumentos = {}
    argumentos = dict(argumentos or {})
    if nome in PROPRIAS and "analise" not in argumentos:   # nome antigo (D-036), aceito nos testes e no gabarito
        nome, argumentos["analise"] = next(f for f, o in CONSULTAS.items() if nome in o), nome
    if nome not in CONSULTAS:
        return {"erro": f"ferramenta {nome!r} não existe; use {FERRAMENTAS}"}
    analise = argumentos.pop("analise", None)
    if analise not in CONSULTAS[nome]:
        return {"erro": f"analise {analise!r} não existe em {nome}; use {list(CONSULTAS[nome])}"}
    funcao, com_conexao = _funcao(analise)
    aceitos = set(inspect.signature(funcao).parameters) - {"con"}
    args = {k: v for k, v in argumentos.items() if k in aceitos and v not in (None, "")}
    if com_conexao:
        args.setdefault("uf", "MG")
    if "ano" in args:
        try:
            args["ano"] = int(args["ano"])
        except (TypeError, ValueError):
            return {"erro": f"ano {args['ano']!r} inválido"}
    try:
        return funcao(con, **args) if com_conexao else funcao(**args)
    except (TypeError, ValueError, KeyError, LookupError, OSError, duckdb.Error) as e:
        return {"erro": f"falha na consulta {analise}: {e}"}


LINHAS_TABELA = 25   # linhas de `tabela` que vão para o modelo (o resto fica no painel e no download)


# nome da coluna → formato (a ordem importa: "prob_deficit" é fração, não R$; "com_deficit" é contagem)
FRACOES = ("pct", "prob", "p_fim", "sinistralidade", "indice", "taxa", "adesao", "erro", "parte", "fracao", "efeito")
CONTAGENS = ("n_", "com_", "obrigadas", "serventias")
MONETARIAS = ("passivo", "deficit", "premio", "receita", "valor", "importancia", "p05", "p95", "p10", "p90", "central",
              "realizado", "resultado", "custo", "sinistro", "amplitude")


def _formatar_celula(coluna: str, v, linha: dict):
    """Número cru de uma linha de tabela → texto pt-BR, pelo nome da coluna (ou pela `medida` da linha), com as
    mesmas funções do painel. O modelo copia o texto: não converte fração em % nem arredonda (regra "não calcula")."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return v
    nome = coluna.lower()
    medida = str(linha.get("medida", "")).lower()
    if nome in ("valor_min", "valor_base", "valor_max"):   # valor da suposição no tornado (taxa, chance, fração…)
        return _br(v, 3)
    if nome.startswith(FRACOES) or nome.endswith("_pct") or "fracao" in nome:
        return pct(v)
    if medida and nome in ("p10", "central", "p90", "p05", "p95", "base", "minimo", "maximo"):
        return aprox(v) if medida.startswith("n_") else brl(v)
    if nome.startswith(CONTAGENS):
        return _br(v, 0) if float(v).is_integer() else aprox(v)
    if any(m in nome for m in MONETARIAS):
        return brl(v)
    if isinstance(v, int) or float(v).is_integer():
        return _br(v, 0)
    return _br(v, 2)


# nomes que o modelo confundia com a faixa provável P5–P95 da D-042 (teste real de 2026-10-28; D-069)
NOMES_PARA_O_MODELO = {"minimo": "extremo_teorico_minimo", "maximo": "extremo_teorico_maximo"}


def _linha_para_o_modelo(linha: dict) -> dict:
    """Sem as colunas cruas que já têm a versão formatada (`*_txt`, `*_cru`), com os demais números formatados e com
    "mínimo" e "máximo" chamados pelo que são: extremos teóricos."""
    return {NOMES_PARA_O_MODELO.get(c, c): _formatar_celula(c, x, linha) for c, x in linha.items()
            if not c.endswith("_cru") and f"{c}_txt" not in linha}


def para_o_modelo(resultado: dict) -> dict:
    """O que o modelo recebe: sem os números crus (`valores`, colunas `*_cru` e as que têm `*_txt`; os outros números
    das tabelas vão formatados em pt-BR), sem a `tabela` quando ela repete outro campo e com as listas cortadas em
    LINHAS_TABELA linhas (a curva de um gráfico tem milhares de pontos: fica no painel e no download)."""
    r = {}
    for k, v in resultado.items():
        if k == "valores" or (k == "tabela" and any(v == outro for c, outro in resultado.items() if c != k)):
            continue
        if isinstance(v, list):
            v = [_linha_para_o_modelo(linha) if isinstance(linha, dict) else linha for linha in v[:LINHAS_TABELA]]
            if len(resultado[k]) > LINHAS_TABELA:
                v.append({"observacao": f"mais {len(resultado[k]) - LINHAS_TABELA} linhas no painel"})
        r[k] = v
    return r
