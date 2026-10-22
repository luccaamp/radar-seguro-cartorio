"""Chat do painel (E5): ferramentas só sobre tabelas públicas, painel funcionando sem Ollama, laço de ferramentas e
correção do gabarito. Sem o modelo de verdade: o LLM é trocado por um falso; os dados são o conjunto público."""
import re

import duckdb
import pytest
import yaml

from apoio_painel import OLLAMA_AUSENTE, RAIZ
from src.agent import avaliacao, chat, ferramentas

CODIGO_DO_CHAT = [RAIZ / "src" / "llm.py", *sorted((RAIZ / "src" / "agent").glob("*.py")), RAIZ / "app/pages/4_Chat.py"]


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
    r = ferramentas.executar(con, "contar_serventias", {"uf": "mg"})
    assert r["serventias_ativas"] == ferramentas._br(ref["n_serventias_ativas"], 0) and "premissas v" in r["citar"]
    r = ferramentas.executar(con, "passivo_e_obrigadas", {"uf": "MG"})
    assert r["passivo_das_obrigadas"].startswith(ferramentas.brl(ref["passivo_universo"]) + " no cenário base")
    r = ferramentas.executar(con, "simular", {"uf": "MG", "taxa": 3, "market_share": 10})
    assert r["premio_anual_mercado"] == ferramentas.brl(ref["mercado_importancia_segurada"] * 0.03)
    assert r["premio_anual_seguradora_hipotetica"] == ferramentas.brl(ref["mercado_importancia_segurada"] * 0.003)
    r = ferramentas.executar(con, "deficit_e_mercado", {"uf": "MG", "cenario_stf": "suspende_8_17"})
    assert r["premio_anual_mercado"].startswith("R$ 0 no cenário base")


def test_filtros_uf_sem_dados_e_erros_viram_resposta(con):
    for recorte in ("vago", "interino", "Vago (interino)"):
        assert ferramentas.executar(con, "contar_serventias", {"uf": "MG", "recorte": recorte})[
            "recorte"] == "situacao = VAGO"
    assert ferramentas.executar(con, "contar_serventias", {"uf": "MG", "recorte": "Classe 3"})["recorte"] == "classe = 3"
    assert "erro" in ferramentas.executar(con, "contar_serventias", {"uf": "SP", "recorte": "total"})
    assert "erro" in ferramentas.executar(con, "contar_serventias", {"uf": "MG", "recorte": "CNS 012345"})
    assert "erro" in ferramentas.executar(con, "nao_existe", {})
    assert "erro" in ferramentas.executar(con, "simular", {"uf": "MG", "taxa": 90})


@pytest.mark.skipif(not (ferramentas.NORMAS_DIR / "prov_227_2026_pagina.txt").exists(),
                    reason="texto das normas (bronze) ausente")
def test_buscar_norma_acha_o_artigo():
    r = ferramentas.buscar_norma("quais serventias ficam fora do provimento 227?")
    assert r["trechos"][0]["artigo"] == "Art.19" and "Classe I" in r["trechos"][0]["texto"]
    assert any(t["artigo"] == "Art.13" for t in ferramentas.buscar_norma("a garantia pode ser fiança bancária?")["trechos"])


# ------------------------------------------------------------------ laço do chat, com um LLM falso
def test_chat_chama_a_ferramenta_e_devolve_o_texto(con, monkeypatch):
    roteiro = [{"content": "", "tool_calls": [{"function": {"name": "contar_serventias", "arguments": {"uf": "MG"}}}]},
               {"content": "São 2.525 serventias. Fonte: ..."}]
    enviados = []

    def falso(mensagens, ferramentas_=None):
        enviados.append(list(mensagens))
        return roteiro.pop(0)
    monkeypatch.setattr(chat.llm, "conversar", falso)
    r = chat.responder("Quantas serventias há em MG?", con)
    assert r.texto.startswith("São 2.525") and [c["ferramenta"] for c in r.chamadas] == ["contar_serventias"]
    assert enviados[1][-1]["role"] == "tool" and "2.525" in enviados[1][-1]["content"]


# ------------------------------------------------------------------ painel sem Ollama
def test_painel_abre_sem_ollama(painel_demo, monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("RADAR_OLLAMA_URL", OLLAMA_AUSENTE)
    at = AppTest.from_file(str(RAIZ / "app/pages/4_Chat.py"), default_timeout=120).run()
    assert not at.exception
    assert any("Chat desativado" in i.value for i in at.info)
    assert not at.chat_input


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
