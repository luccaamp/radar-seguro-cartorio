"""Chat do painel (E5; D-060 a D-066): ferramentas só sobre tabelas públicas, laço de ferramentas com um modelo FALSO,
chamada ao Gemini contra um servidor SIMULADO (httpx.MockTransport), página sem chave e com o limite da sessão,
resposta sem modelo e correção do gabarito. Nenhum teste usa a API real nem a internet (tests/conftest.py,
_sem_gemini); os dados são o conjunto público."""
import json
import re

import duckdb
import httpx
import pytest
import yaml

from apoio_painel import RAIZ
from src import llm
from src.agent import avaliacao, chat, ferramentas


# ------------------------------------------------------------------ tabelas que existem no modo demonstração
def test_ferramentas_so_leem_tabelas_do_conjunto_publico():
    """Toda tabela citada no SQL das ferramentas está em config/publico.yaml, para o chat funcionar também no banco
    de demonstração (D-029); nenhum SQL grava (D-034). A D-038 retirou a proibição de interno_* por LGPD."""
    publicas = set(yaml.safe_load((RAIZ / "config" / "publico.yaml").read_text(encoding="utf-8"))["tabelas"])
    publicas.add("estado.premissas_versoes")   # publicada como estado.premissas_vigente (só a versão vigente)
    texto = (RAIZ / "src" / "agent" / "ferramentas.py").read_text(encoding="utf-8")
    citadas = set(re.findall(r"\b(?:gold|silver|qualidade|estado)\.\w+", texto))
    assert citadas and citadas <= publicas, citadas - publicas
    assert not re.search(r"\b(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|COPY|ATTACH)\b", texto)


# ------------------------------------------------------------------ ferramentas no conjunto público
@pytest.fixture(scope="module")
def con(painel_demo):
    c = duckdb.connect(str(painel_demo["banco"]), read_only=True)
    yield c
    c.close()


def test_ferramentas_devolvem_os_numeros_do_gold(con):
    ref = con.execute("SELECT * FROM gold.fato_mercado_uf WHERE nivel = 'base' AND regra_classe = 'v2' "
                      "AND cenario_stf = 'mantem'").df().iloc[0]
    r = ferramentas.executar(con, "consultar_numeros", {"analise": "contar_serventias", "uf": "mg"})
    assert r["serventias_ativas"] == ferramentas._br(ref["n_serventias_ativas"], 0) and "premissas v" in r["citar"]
    r = ferramentas.executar(con, "consultar_numeros", {"analise": "passivo_e_obrigadas"})   # UF padrão: MG
    assert r["passivo_das_obrigadas"].startswith(ferramentas.brl(ref["passivo_universo"]) + " no cenário base")
    r = ferramentas.executar(con, "consultar_numeros", {"analise": "simular", "taxa": 3, "market_share": 10})
    assert r["premio_anual_mercado"] == ferramentas.brl(ref["mercado_importancia_segurada"] * 0.03)
    assert r["premio_anual_seguradora_hipotetica"] == ferramentas.brl(ref["mercado_importancia_segurada"] * 0.003)
    r = ferramentas.executar(con, "consultar_numeros", {"analise": "deficit_e_mercado", "cenario_stf": "suspende_8_17"})
    assert r["premio_anual_mercado"].startswith("R$ 0 no cenário base")
    # os nomes antigos (D-036) continuam aceitos
    assert ferramentas.executar(con, "contar_serventias", {"uf": "MG"}) == \
        ferramentas.executar(con, "consultar_numeros", {"analise": "contar_serventias", "uf": "MG"})


def test_consultas_do_painel_devolvem_o_mesmo_que_as_paginas(con):
    """O chat chama as mesmas funções de src/painel/analises.py que as páginas (comum.analise), com a mesma UF."""
    from src.painel import analises
    assert ferramentas.executar(con, "consultar_numeros", {"analise": "numeros_oficiais"}) == \
        analises.numeros_oficiais(con, "MG")
    r = ferramentas.executar(con, "consultar_analises", {"analise": "previsao_mercado", "ano": "2026"})
    assert r == analises.previsao_mercado(con, "MG", ano=2026)
    assert ferramentas.executar(con, "consultar_decisoes", {"analise": "situacao_adi"}) == analises.situacao_adi()
    assert "erro" in ferramentas.executar(con, "consultar_analises", {"analise": "previsao_mercado", "ano": 2040})
    assert "erro" in ferramentas.executar(con, "consultar_numeros", {"analise": "tornado"})   # é de outra ferramenta
    assert "erro" in ferramentas.executar(con, "consultar_mercado", {"analise": "grupos", "uf": "SP"})


def test_consultar_serventia_por_cns_e_por_municipio(con):
    """D-048 (D-038): o resultado por serventia sai de gold.serventia_publico, pelo CNS ou pelo município, e a soma
    dos prêmios bate com o total da UF."""
    s = con.execute("SELECT * FROM gold.serventia_publico WHERE premio_emitido > 0 ORDER BY premio_emitido DESC "
                    "LIMIT 1").df().iloc[0]
    pedir = lambda **kw: ferramentas.executar(con, "consultar_mercado", {"analise": "consultar_serventia", **kw})  # noqa: E731
    r = pedir(cns=s["cns"])
    assert r["premio_anual"] == ferramentas.brl(s["premio_emitido"]) and r["municipio"] == s["municipio"]
    assert r["obrigada_prov_227"] == "sim" and "nome" not in " ".join(r)
    r = pedir(municipio=s["municipio"].lower())
    assert any(x["cns"] == s["cns"] for x in r["serventias"])
    assert "erro" in pedir(cns="000000")
    assert "erro" in pedir()
    total, uf = con.execute("SELECT (SELECT sum(premio_emitido) FROM gold.serventia_publico), mercado_premio_emitido "
                            "FROM gold.fato_mercado_uf WHERE nivel = 'base' AND regra_classe = 'v2' "
                            "AND cenario_stf = 'mantem'").fetchone()
    assert total == pytest.approx(uf)


def test_filtros_uf_sem_dados_e_erros_viram_resposta(con):
    contar = lambda recorte, uf="MG": ferramentas.executar(  # noqa: E731
        con, "consultar_numeros", {"analise": "contar_serventias", "uf": uf, "recorte": recorte})
    for recorte in ("vago", "interino", "Vago (interino)"):
        assert contar(recorte)["recorte"] == "situacao = VAGO"
    assert contar("Classe 3")["recorte"] == "classe = 3"
    assert "erro" in contar("total", uf="SP")
    assert "erro" in contar("CNS 012345")
    assert "erro" in ferramentas.executar(con, "nao_existe", {})
    assert "erro" in ferramentas.executar(con, "consultar_numeros", "{json quebrado")
    assert "erro" in ferramentas.executar(con, "consultar_numeros", {"analise": "simular", "taxa": 90})


def test_o_modelo_recebe_so_valores_formatados_e_listas_curtas(con):
    for nome, opcoes in ferramentas.CONSULTAS.items():
        for analise in opcoes:
            args = {"analise": analise, "pergunta": "quem fica fora do 227", "municipio": "Uberaba"}
            r = ferramentas.para_o_modelo(ferramentas.executar(con, nome, args))
            assert "valores" not in r and len(json.dumps(r, ensure_ascii=False)) < 8000, (analise, len(str(r)))
            assert all(len(v) <= ferramentas.LINHAS_TABELA + 1 for v in r.values() if isinstance(v, list))


# ------------------------------------------------------------------ normas versionadas (D-064)
def test_buscar_norma_acha_o_artigo():
    r = ferramentas.buscar_norma("quais serventias ficam fora do provimento 227?")
    assert r["trechos"][0]["artigo"] == "Art.19" and "Classe I" in r["trechos"][0]["texto"]
    assert any(t["artigo"] == "Art.13" for t in ferramentas.buscar_norma("a garantia pode ser fiança bancária?")["trechos"])


def test_normas_versionadas_sem_assinatura_e_iguais_ao_texto_oficial():
    """data/normas/ é o texto oficial menos a linha de assinatura, que traz nome de pessoa física (D-038)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("exportar_normas", RAIZ / "scripts" / "exportar_normas.py")
    exportar = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exportar)
    for arquivo, _ in ferramentas.NORMAS.values():
        texto = (ferramentas.NORMAS_DIR / arquivo).read_text(encoding="utf-8")
        assert "Art. 1" in texto and not re.search(r"(?m)^Minist(ro|ra) ", texto)
        bronze = ferramentas.NORMAS_BRONZE / arquivo
        if bronze.exists():   # só nas máquinas com o bronze
            assert texto == exportar.sem_assinatura(bronze.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ laço do chat, com um modelo falso
def _modelo_falso(monkeypatch, roteiro: list[dict]) -> list[dict]:
    """Troca o Gemini (em streaming) por um roteiro de respostas: cada texto sai em dois pedaços, como no streaming."""
    enviados = []

    def registrar(conteudos, sistema, ferramentas_, sem_ferramenta_agora, streaming):
        enviados.append({"conteudos": json.loads(json.dumps(conteudos)), "sistema": sistema, "streaming": streaming,
                         "ferramentas": ferramentas_, "sem_ferramenta_agora": sem_ferramenta_agora})
        return roteiro.pop(0)

    def falso_em_partes(conteudos, sistema, ferramentas_=None, sem_ferramenta_agora=False):
        msg = registrar(conteudos, sistema, ferramentas_, sem_ferramenta_agora, True)
        texto = llm.texto(msg)
        if texto:
            yield "texto", texto[:5]
            yield "texto", texto[5:]
        yield "fim", msg
    monkeypatch.setattr(chat.llm, "conversar_em_partes", falso_em_partes)
    monkeypatch.setattr(chat.llm, "conversar", lambda c, s, f=None, sem_ferramenta_agora=False:
                        registrar(c, s, f, sem_ferramenta_agora, False))
    return enviados


def _texto(t: str) -> dict:
    return {"role": "model", "parts": [{"text": t}]}


def _pede(nome, args, id_="c1"):
    return {"role": "model", "parts": [{"functionCall": {"id": id_, "name": nome, "args": args},
                                        "thoughtSignature": "assinatura"}]}


def test_chat_chama_a_ferramenta_e_devolve_o_texto(con, monkeypatch):
    enviados = _modelo_falso(monkeypatch, [
        _pede("consultar_numeros", {"analise": "contar_serventias", "uf": "MG"}),
        {"role": "model", "parts": [{"text": "pensando", "thought": True}, {"text": "São 2.525 serventias. Fonte: ..."}]}])
    r = chat.responder("qts cartorios tem em mg?", con)
    assert r.texto.startswith("São 2.525") and [c["ferramenta"] for c in r.chamadas] == ["consultar_numeros"]
    segunda = enviados[1]["conteudos"]
    assert segunda[1]["parts"][0]["thoughtSignature"] == "assinatura"   # a resposta do modelo volta como veio
    resposta = segunda[2]["parts"][0]["functionResponse"]
    assert resposta["id"] == "c1" and resposta["response"]["serventias_ativas"] == "2.525"
    assert enviados[0]["sistema"] == chat.prompt_sistema("c") and "consultar_numeros" in enviados[0]["sistema"]
    assert "2.525" in chat.apoio(r)


def test_streaming_entrega_o_texto_aos_pedacos_e_avisa_a_consulta(con, monkeypatch):
    enviados = _modelo_falso(monkeypatch, [_pede("consultar_numeros", {"analise": "escada"}),
                                           _texto("O prêmio é R$ 341,1 mil.\n\nFonte: gold.fato_mercado_uf · ref.: x")])
    eventos = list(chat.responder_em_partes("e o premio?", con))
    tipos = [t for t, _ in eventos]
    assert tipos == ["consultando", "texto", "texto", "fim"]
    # D-069: a 1ª chamada (que pede a ferramenta) sem streaming; a resposta escrita depois, em streaming
    assert [e["streaming"] for e in enviados] == [False, True]
    assert "".join(v for t, v in eventos if t == "texto") == eventos[-1][1].texto
    assert [e["etapa"] for e in eventos[-1][1].etapas] == ["modelo", "ferramentas (1)", "modelo"]


def test_varias_ferramentas_rodam_em_paralelo_e_com_cache(con, monkeypatch):
    """D-069: dois pedidos na mesma rodada rodam em threads, cada um num cursor; a mesma consulta não roda de novo."""
    import threading
    chat._cache.clear()
    threads, executar = set(), ferramentas.executar

    def contado(c, nome, args):
        threads.add(threading.get_ident())
        return executar(c, nome, args)
    monkeypatch.setattr(chat.ferramentas, "executar", contado)
    duplo = {"role": "model", "parts": [
        {"functionCall": {"id": "a", "name": "consultar_numeros", "args": {"analise": "escada"}}},
        {"functionCall": {"id": "b", "name": "consultar_decisoes", "args": {"analise": "situacao_adi"}}}]}
    _modelo_falso(monkeypatch, [duplo, _texto("ok"), duplo, _texto("ok")])
    r = chat.responder("x", con, banco="teste")
    assert [c["ferramenta"] for c in r.chamadas] == ["consultar_numeros", "consultar_decisoes"] and len(threads) == 2
    threads.clear()
    chat.responder("x", con, banco="teste")
    assert not threads   # tudo veio do cache


def test_chat_para_no_limite_de_rodadas(con, monkeypatch):
    n = int(llm.config()["max_rodadas_ferramentas"])
    pedidos = [_pede("consultar_decisoes", {"analise": "situacao_adi"}, f"c{i}") for i in range(n)]
    enviados = _modelo_falso(monkeypatch, [*pedidos, {"role": "model", "parts": [{"text": "Sem liminar."}]}])
    r = chat.responder("e a adi?", con, historico=[{"role": "user", "content": "oi"},
                                                    {"role": "assistant", "content": "Olá!"}])
    assert r.texto == "Sem liminar." and len(r.chamadas) == n
    assert enviados[-1]["sem_ferramenta_agora"] and enviados[0]["conteudos"][1]["role"] == "model"


def test_versoes_a_e_b_sem_ferramentas(con, monkeypatch):
    enviados = _modelo_falso(monkeypatch, [_texto("Não sei."), _texto("Não sei.")])
    assert chat.responder("x", con, versao="a").chamadas == []
    chat.responder("x", con, versao="b")
    assert enviados[0]["ferramentas"] is None and "Art. 19" in enviados[1]["sistema"]
    assert "Art. 19" not in enviados[0]["sistema"]


# ------------------------------------------------------------------ src/llm.py contra um servidor simulado
@pytest.fixture
def servidor(monkeypatch):
    """Servidor simulado do Gemini; `respostas` é a fila de (status, json) por modelo."""
    estado = {"pedidos": [], "respostas": {}}

    def tratar(request: httpx.Request) -> httpx.Response:
        modelo = request.url.path.rsplit("/", 1)[-1].split(":")[0]
        estado["pedidos"].append({"modelo": modelo, "url": str(request.url), "cabecalho": dict(request.headers),
                                  "corpo": json.loads(request.content)})
        status, corpo = estado["respostas"][modelo].pop(0)
        return httpx.Response(status, json=corpo)
    monkeypatch.setattr(llm, "_transporte", httpx.MockTransport(tratar))
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste-123")
    monkeypatch.setattr(llm, "_principal_fora_ate", 0.0)
    return estado


def test_llm_monta_o_pedido_e_le_a_resposta(servidor):
    c = llm.config()
    servidor["respostas"][c["modelo"]] = [(200, {"candidates": [{"content": _pede("consultar_numeros", {"analise": "escada"})}]})]
    msg = llm.conversar([{"role": "user", "parts": [{"text": "oi"}]}], "sistema", ferramentas.ESQUEMAS)
    assert llm.chamadas(msg) == [{"id": "c1", "name": "consultar_numeros", "args": {"analise": "escada"}}]
    p = servidor["pedidos"][0]
    assert p["cabecalho"]["x-goog-api-key"] == "chave-de-teste-123" and "chave-de-teste" not in p["url"]
    assert p["corpo"]["tools"][0]["functionDeclarations"] == ferramentas.ESQUEMAS
    assert p["corpo"]["systemInstruction"]["parts"][0]["text"] == "sistema"
    assert p["corpo"]["generationConfig"]["thinkingConfig"]["thinkingLevel"] == c["nivel_raciocinio"]


def test_llm_usa_a_reserva_e_avisa_cota_sem_mostrar_a_chave(servidor):
    c = llm.config()
    ok = {"candidates": [{"content": {"role": "model", "parts": [{"text": "ok"}]}}]}
    servidor["respostas"] = {c["modelo"]: [(429, {"error": {"message": "quota"}})], c["reserva"]: [(200, ok)]}
    assert llm.texto(llm.conversar([], "s")) == "ok"
    llm._principal_fora_ate = 0.0
    servidor["respostas"] = {c["modelo"]: [(429, {})], c["reserva"]: [(429, {})]}
    with pytest.raises(llm.LLMIndisponivel) as e:
        llm.conversar([], "s")
    assert e.value.motivo == "cota"
    llm._principal_fora_ate = 0.0
    servidor["respostas"] = {c["modelo"]: [(400, {"error": {"message": "API key chave-de-teste-123 inválida"}})],
                             c["reserva"]: [(400, {"error": {"message": "chave-de-teste-123"}})]}
    with pytest.raises(llm.LLMIndisponivel) as e:
        llm.conversar([], "s")
    assert e.value.motivo == "erro" and "chave-de-teste-123" not in str(e.value)


def test_llm_principal_lento_vai_para_a_reserva(monkeypatch):
    """D-068: o principal pode travar no nível gratuito (visto em 2026-10-28); passou de timeout_s, usa a reserva."""
    c = llm.config()

    def tratar(request):
        if c["modelo"] in request.url.path:
            raise httpx.ReadTimeout("demorou", request=request)
        return httpx.Response(200, json={"candidates": [{"content": {"role": "model", "parts": [{"text": "ok"}]}}]})
    pedidos = []
    monkeypatch.setattr(llm, "_transporte", httpx.MockTransport(lambda r: pedidos.append(r.url.path) or tratar(r)))
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste-123")
    monkeypatch.setattr(llm, "_principal_fora_ate", 0.0)
    assert llm.texto(llm.conversar([], "s")) == "ok"
    assert llm.texto(llm.conversar([], "s")) == "ok"   # a segunda vai direto para a reserva
    assert [c["modelo"] in p for p in pedidos] == [True, False, False]

    monkeypatch.setattr(llm, "_principal_fora_ate", 0.0)

    def sempre_lento(request):
        raise httpx.ReadTimeout("demorou", request=request)
    monkeypatch.setattr(llm, "_transporte", httpx.MockTransport(sempre_lento))
    with pytest.raises(llm.LLMIndisponivel) as e:
        llm.conversar([], "s")
    assert e.value.motivo == "lento" and "sobrecarregado" in str(e.value)


def test_llm_em_streaming_le_o_sse_e_usa_a_reserva(monkeypatch):
    """`conversar_em_partes` lê o streaming (SSE) do Gemini, guarda todas as partes e, se o principal falhar antes do
    primeiro texto, usa a reserva."""
    c = llm.config()
    pedacos = [{"candidates": [{"content": {"role": "model", "parts": [{"text": "Olá, ", "thoughtSignature": "s"}]}}]},
               {"candidates": [{"content": {"role": "model", "parts": [{"text": "tudo bem."}]}}]}]
    sse = "".join(f"data: {json.dumps(p)}\r\n\r\n" for p in pedacos)
    pedidos = []

    def tratar(request):
        pedidos.append(str(request.url))
        if c["modelo"] in request.url.path:
            return httpx.Response(429, json={"error": {"message": "quota"}})
        corpo = json.loads(request.content)
        assert corpo["generationConfig"]["thinkingConfig"]["thinkingLevel"] == c["nivel_raciocinio_reserva"]
        return httpx.Response(200, text=sse, headers={"content-type": "text/event-stream"})
    monkeypatch.setattr(llm, "_transporte", httpx.MockTransport(tratar))
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste-123")
    monkeypatch.setattr(llm, "_principal_fora_ate", 0.0)
    eventos = list(llm.conversar_em_partes([{"role": "user", "parts": [{"text": "oi"}]}], "s"))
    assert eventos[:2] == [("texto", "Olá, "), ("texto", "tudo bem.")]
    assert eventos[-1][1]["parts"][0]["thoughtSignature"] == "s" and llm.texto(eventos[-1][1]) == "Olá, tudo bem."
    assert all("alt=sse" in p for p in pedidos) and "chave-de-teste" not in " ".join(pedidos)


def test_sem_dado_a_frase_e_a_da_d069(con, monkeypatch):
    """D-069: sem dado ou fora do escopo, "Não foi possível encontrar essa resposta nos dados do painel." (prompt v3,
    perguntas prontas e o detector de "não sei" da avaliação)."""
    prompt = chat.prompt_sistema("c")
    assert prompt.count(chat.SEM_DADO) == 3 and "Não possuo" not in prompt and llm.config()["versao_prompt"] == 3
    pronta = {"ferramenta": "consultar_numeros", "argumentos": {"analise": "contar_serventias", "uf": "SP"}}
    assert chat.responder_sem_modelo(con, pronta).texto == chat.SEM_DADO
    for frase in (chat.SEM_DADO, "Não consegui encontrar isso nos dados.", "Essa informação não está nos dados do "
                  "painel.", "nao foi possivel localizar essa resposta"):
        assert avaliacao.corrigir(frase, "recusa", ""), frase
    # com o modelo falso: fora do escopo (sem ferramenta) e sem dado (a ferramenta devolve erro)
    _modelo_falso(monkeypatch, [_texto(chat.SEM_DADO + " O painel cobre a projeção de 2026 e 2027."),
                                _pede("consultar_analises", {"analise": "previsao_mercado", "ano": 2030}),
                                _texto(chat.SEM_DADO)])
    fora = chat.responder("qual a inflação de 2027?", con)
    sem_dado = chat.responder("e o prêmio em 2030?", con)
    assert fora.texto.startswith(chat.SEM_DADO) and fora.chamadas == []
    assert "erro" in sem_dado.chamadas[0]["resultado"] and sem_dado.texto == chat.SEM_DADO
    assert avaliacao.corrigir(fora.texto, "recusa", "") and avaliacao.corrigir(sem_dado.texto, "recusa", "")


def test_consulta_de_mercado_traz_a_faixa_provavel_do_painel(con):
    """D-069 (D-042): no cenário "mantém", déficit, IS e prêmio vêm com a faixa provável P5–P95 da mesma função do
    painel; os extremos ficam num campo à parte (o modelo chamava os extremos de "faixa provável")."""
    from src.painel import analises
    r = ferramentas.executar(con, "consultar_numeros", {"analise": "deficit_e_mercado"})
    f = analises.faixa_d042(con, "MG", "premio")
    assert r["premio_anual_mercado"] == f"{f['valor_base']} no cenário base; faixa provável (P5–P95): {f['faixa_provavel']}"
    assert r["premio_anual_mercado_extremos_teoricos_so_se_pedirem"] == f["extremos"]
    assert "faixa provável" not in ferramentas.executar(con, "consultar_numeros", {
        "analise": "deficit_e_mercado", "cenario_stf": "parcial"})["premio_anual_mercado"].replace("não é a faixa", "")


def test_separar_fonte_e_selos():
    corpo, fonte = chat.separar_fonte("São 2.525.\n\n**Fonte:** gold.x · referência: 2026-10-17 · premissas: v3")
    assert corpo == "São 2.525." and fonte == "Fonte: gold.x · referência: 2026-10-17 · premissas: v3"
    assert chat.separar_fonte("Sem fonte aqui.") == ("Sem fonte aqui.", "")
    assert chat.selos([{"resultado": {"rotulo": "projeção"}}, {"resultado": {"rotulo": "projeção"}},
                       {"resultado": {}}]) == ["projecao"]


def test_o_modelo_nao_converte_numeros_crus(con):
    """D-069: as tabelas vão ao modelo já formatadas (no teste real, ele converteu 0,2815 em "28,15%" sozinho)."""
    r = ferramentas.para_o_modelo(ferramentas.executar(con, "consultar_mercado", {"analise": "grupos"}))
    linha = r["tabela"][0]
    assert linha["pct_serventias"].endswith("%") and linha["passivo"].startswith("R$")
    assert not any(isinstance(v, float) for ln in r["tabela"] for v in ln.values())
    r = ferramentas.para_o_modelo(ferramentas.executar(con, "consultar_mercado", {"analise": "capacidade_pagar"}))
    assert r["calibracao"][0]["prob_deficit_m1"].endswith("%")   # fração, não R$


def test_llm_sem_chave_e_sem_internet(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    assert llm.situacao()[0] is False and llm.chave() is None
    with pytest.raises(llm.LLMIndisponivel) as e:
        llm.conversar([], "s")
    assert e.value.motivo == "sem_chave"
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste-123")   # a rede da suíte falha sempre (conftest)
    with pytest.raises(llm.LLMIndisponivel) as e:
        llm.conversar([], "s")
    assert e.value.motivo == "sem_internet" and "chave-de-teste-123" not in str(e.value)


def test_a_chave_nao_esta_no_repositorio():
    """Nenhum arquivo versionável tem cara de chave do Google (AIza...) e o .env fica fora do git."""
    from apoio_painel import arquivos_versionaveis
    for a in [*arquivos_versionaveis("*.py"), *arquivos_versionaveis("*.yaml"), *arquivos_versionaveis("*.md"),
              *arquivos_versionaveis("*.toml"), *arquivos_versionaveis(".env*")]:
        assert not re.search(r"AIza[0-9A-Za-z_\-]{30,}", a.read_text(encoding="utf-8", errors="ignore")), a
    ignorados = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in ignorados and ".streamlit/secrets.toml" in ignorados


# ------------------------------------------------------------------ resposta sem modelo (D-063)
def test_perguntas_prontas_respondem_sem_modelo_com_os_numeros_do_painel(con):
    from src.painel import analises
    prontas = llm.config()["perguntas_prontas"]
    for p in prontas:
        r = chat.responder_sem_modelo(con, p)
        assert not r.com_modelo and r.texto != chat.SEM_DADO, p
        assert {"tema", "pergunta", "ferramenta", "argumentos"} <= set(p), p
        assert "Fonte:" in r.texto, p
    texto = chat.responder_sem_modelo(con, prontas[0]).texto
    assert all(n["valor"] in texto for n in analises.numeros_oficiais(con, "MG")["numeros"])
    assert "2.525" in texto and "R$ 341,1 mil" in texto


# ------------------------------------------------------------------ página do chat
def _pagina():
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(RAIZ / "app/pages/5_Chat.py"), default_timeout=120)


PROIBIDOS_NA_TELA = ("sem o modelo", "sem chat", "respondidas direto pelo painel", "modo reserva", "fallback",
                     "consultar_", "gemini-", "LLMIndisponivel", "HTTP ", "{\"", "chave-de-teste", "nível gratuito")


def _textos_visiveis(at, sem_expansor_de_fontes: bool = True) -> str:
    """Tudo o que a página mostra fora do expansor "Fontes e datas" (onde o modelo e o nível gratuito podem aparecer)."""
    elementos = [*at.markdown, *at.caption, *at.info, *at.warning, *at.button, *at.tabs]
    textos = []
    for e in elementos:
        valor = str(getattr(e, "value", "") or getattr(e, "label", ""))
        if sem_expansor_de_fontes and any(x in valor for x in ("Como o chat responde", "Dados pessoais:**", "Fontes:")):
            continue
        textos.append(valor)
    return " ".join(textos)


def test_pagina_sem_chave_mostra_so_a_frase_e_as_perguntas_prontas(painel_demo):
    at = _pagina().run()
    assert not at.exception
    assert [t.label for t in at.tabs] == ["Chat", "Perguntas prontas"]
    assert [i.value for i in at.tabs[0].info] == [chat.INDISPONIVEL] and not at.chat_input
    prontas = llm.config()["perguntas_prontas"]
    rotulos = [e.label for e in at.tabs[1].expander]
    assert rotulos == [p["pergunta"] for p in prontas]
    temas = [m.value for m in at.tabs[1].markdown if m.value.startswith("#### ")]
    assert temas == [f"#### {t}" for t in dict.fromkeys(p["tema"] for p in prontas)]
    primeira = at.tabs[1].expander[0]
    assert "2.525" in " ".join(m.value for m in primeira.markdown)
    assert any(c.value.startswith("Fonte:") for c in primeira.caption)   # fonte numa linha pequena abaixo
    visivel = _textos_visiveis(at)
    assert not [p for p in PROIBIDOS_NA_TELA if p in visivel], [p for p in PROIBIDOS_NA_TELA if p in visivel]


def _falso_em_partes(texto: str, rotulo: str | None = None):
    def falso(pergunta, con, historico=None, versao="c", banco=""):
        yield "consultando", None
        yield "texto", texto[:4]
        yield "texto", texto[4:]
        yield "fim", chat.Resposta(texto, [{"ferramenta": "consultar_numeros", "argumentos": {"analise": "x"},
                                            "resultado": {"rotulo": rotulo} if rotulo else {}}])
    return falso


def test_pagina_com_modelo_falso_sugestoes_selo_e_limite(painel_demo, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste-123")
    monkeypatch.setattr(chat, "responder_em_partes", _falso_em_partes(
        "São ≈ 1.204 serventias em 2027.\n\nFonte: gold.analise_previsao · referência: x · premissas: v3", "projeção"))
    at = _pagina().run()
    assert not at.exception and not at.tabs[0].info and not at.chat_input[0].proto.disabled
    sugestoes = [b for b in at.button if b.key and b.key.startswith("sugestao_")]
    assert sorted(b.label for b in sugestoes) == sorted(llm.config()["sugestoes"])   # o AppTest lê coluna a coluna
    sugestoes = sorted(sugestoes, key=lambda b: llm.config()["sugestoes"].index(b.label))
    rodape = " ".join(m.value for m in at.markdown)
    assert "Não digite dados pessoais. As perguntas são enviadas ao Google Gemini." in rodape
    assert "0 de 20 perguntas nesta sessão" in rodape   # modo demonstração = link público
    sugestoes[2].click().run()   # a sugestão envia a pergunta
    assert not at.exception and at.session_state["chat_perguntas_usadas"] == 1
    assert not [b for b in at.button if b.key and b.key.startswith("sugestao_")]
    mensagens = at.tabs[0].chat_message
    assert [m.name for m in mensagens] == ["user", "assistant"]
    resposta = mensagens[1]
    assert "rd-selo projecao" in " ".join(m.value for m in resposta.markdown)
    assert any("São ≈ 1.204" in m.value for m in resposta.markdown)
    assert [c.value for c in resposta.caption] == ["Fonte: gold.analise_previsao · referência: x · premissas: v3"]
    at.chat_input[0].set_value("e em 2026?").run()
    assert at.session_state["chat_perguntas_usadas"] == 2 and len(at.tabs[0].chat_message) == 4
    assert not [p for p in PROIBIDOS_NA_TELA if p in _textos_visiveis(at)]
    at.session_state["chat_perguntas_usadas"] = int(llm.config()["limite_perguntas_sessao"])
    at.run()
    assert at.chat_input[0].proto.disabled and any("limite de 20 perguntas" in i.value for i in at.info)


def test_pagina_com_cota_esgotada_mostra_so_a_frase(painel_demo, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste-123")

    def sem_cota(*a, **kw):
        raise llm.LLMIndisponivel("cota", llm.MENSAGENS["cota"] + " (HTTP 429 chave-de-teste-123)")
        yield   # noqa: unreachable (gerador)
    monkeypatch.setattr(chat, "responder_em_partes", sem_cota)
    at = _pagina().run()
    at.chat_input[0].set_value("oi").run()
    assert not at.exception and at.session_state["chat_cota_esgotada"]
    assert chat.INDISPONIVEL in " ".join(m.value for m in at.tabs[0].chat_message[1].markdown)
    at.run()
    assert [i.value for i in at.tabs[0].info] == [chat.INDISPONIVEL] and not at.chat_input
    assert not [p for p in PROIBIDOS_NA_TELA if p in _textos_visiveis(at)]


# ------------------------------------------------------------------ gabarito congelado (D-065)
def _gabarito() -> list[dict]:
    import csv
    with (RAIZ / "eval" / "gabarito_chat.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def test_gabarito_congelado_com_hash_e_meta():
    """O gabarito só muda com um hash novo em config/llm.yaml (e uma decisão registrada); a meta é fixa (D-065)."""
    import hashlib
    av = llm.config()["avaliacao"]
    assert hashlib.sha256((RAIZ / "eval" / "gabarito_chat.csv").read_bytes()).hexdigest() == av["gabarito_sha256"]
    assert av["meta_acerto"] == 0.85
    linhas = _gabarito()
    assert 40 <= len(linhas) <= 60 and len({r["id"] for r in linhas}) == len(linhas)
    assert {r["criterio"] for r in linhas} <= {"numero", "texto", "recusa", "recusa_com_dados"}
    assert {"informal", "fora_escopo", "armadilha", "normas", "grafico", "dado_pessoal"} <= {r["tipo"] for r in linhas}
    assert not re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", (RAIZ / "eval" / "gabarito_chat.csv").read_text(encoding="utf-8"))


def test_gabarito_bate_com_as_ferramentas(con):
    """Todo número esperado aparece (a até 1%) na saída de alguma ferramenta, e todo texto esperado com número também:
    se uma carga nova mudar os números, este teste avisa que o gabarito precisa ser refeito."""
    saidas = []
    for nome, opcoes in ferramentas.CONSULTAS.items():
        for analise in opcoes:
            saidas.append(ferramentas.executar(con, nome, {"analise": analise}))
    extras = [("consultar_numeros", {"analise": "contar_serventias", "recorte": r}) for r in ("classe 3", "vago",
                                                                                              "registro de imoveis")]
    extras += [("consultar_numeros", {"analise": "simular", "taxa": 3}),
               ("consultar_numeros", {"analise": "simular", "taxa": 2, "market_share": 10}),
               ("consultar_numeros", {"analise": "faixa_d042", "medida": "deficit"}),
               ("consultar_mercado", {"analise": "consultar_serventia", "cns": "035741"}),
               ("consultar_decisoes", {"analise": "buscar_norma", "pergunta": "fiança bancária"}),
               ("consultar_decisoes", {"analise": "buscar_norma", "pergunta": "quem fica fora do provimento 227"}),
               ("consultar_decisoes", {"analise": "buscar_norma", "pergunta": "valor da garantia", "provimento": "227"}),
               ("consultar_decisoes", {"analise": "buscar_norma", "pergunta": "limite da classe 1",
                                       "provimento": "243"}),
               ("consultar_decisoes", {"analise": "buscar_norma", "pergunta": "prazo no primeiro ano"})]
    saidas += [ferramentas.executar(con, n, a) for n, a in extras]
    apoio = json.dumps(saidas, ensure_ascii=False)
    for r in _gabarito():
        if r["criterio"] == "numero":
            assert avaliacao.corrigir(apoio, "numero", r["esperado"]), (r["id"], r["esperado"])
        elif r["criterio"] == "texto":   # só os grupos com número (os outros são palavras da resposta)
            for grupo in (g for g in r["esperado"].split("&") if re.search(r"\d", g)):
                assert avaliacao.corrigir(apoio, "texto", grupo), (r["id"], grupo)


def test_avaliacao_guarda_as_respostas_e_nao_repete_chamadas(painel_demo, monkeypatch, tmp_path):
    """scripts/avaliar_chat.py com um modelo falso: grava eval/respostas/ (aqui, numa pasta temporária), a segunda
    rodada não chama o modelo de novo e o relatório traz a meta."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("avaliar_chat", RAIZ / "scripts" / "avaliar_chat.py")
    av = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(av)
    monkeypatch.setattr(av, "RESPOSTAS", tmp_path / "respostas")
    monkeypatch.setattr(av, "SAIDA", tmp_path / "resultado.md")
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste-123")
    monkeypatch.setattr(av.time, "sleep", lambda s: None)
    chamadas = []

    def falso(pergunta, con, historico=None, versao="c"):
        chamadas.append(versao)
        return chat.Resposta("São 2.525 serventias. Fonte: x")
    monkeypatch.setattr(av.chat, "responder", falso)
    av.main(["a", "c"], 3, refazer=False, so_relatorio=False)
    assert len(chamadas) == 6 and len((tmp_path / "respostas" / "c.jsonl").read_text(encoding="utf-8").splitlines()) == 3
    av.main(["a", "c"], 3, refazer=False, so_relatorio=False)
    assert len(chamadas) == 6   # tudo veio do que foi guardado
    texto = (tmp_path / "resultado.md").read_text(encoding="utf-8")
    assert "Meta (fixada antes" in texto and "chave-de-teste" not in texto
    assert "chave-de-teste" not in (tmp_path / "respostas" / "c.jsonl").read_text(encoding="utf-8")


# ------------------------------------------------------------------ correção do gabarito
def test_correcao_do_gabarito():
    assert avaliacao.numeros("R$ 238,1 mi; ≈ 1.121; 2.525; R$ 368,7 mil") == [238.1e6, 1121, 2525, 368700]
    assert avaliacao.corrigir("São 2.525 serventias", "numero", "2525")
    assert avaliacao.corrigir("o prêmio cai a R$ 0", "numero", "0")
    assert not avaliacao.corrigir("São 2.600 serventias", "numero", "2525")
    assert avaliacao.corrigir("Ficam fora a Classe 1 e as sob interinidade", "texto", "classe 1|classe i&interin")
    assert avaliacao.corrigir("Não posso informar dados de um cartório (LGPD).", "recusa", "")
    assert not avaliacao.corrigir("Não sei, mas o passivo é R$ 1,2 mi", "recusa", "")
    apoio = '{"serventias_ativas": "2.525", "citar": "carga 2026-10-19; premissas v2"}'
    assert avaliacao.numeros_sem_apoio("São 2.525 serventias (art. 19).", apoio) == []
    assert avaliacao.numeros_sem_apoio("São 2.525, entre 2.480 e 2.570.", apoio) == [2480, 2570]
