"""Quadro do município (V5, D-082; bloco "painel de MG rumo ao V5", item 2): os cartórios de um município, pelo CNS,
na página "Onde está o mercado" e no chat (src/painel/analises.cartorios_do_municipio). Roda no modo demonstração
(conjunto público versionado), em qualquer clone."""
import re

import duckdb
import pytest

from apoio_painel import MERCADO, RAIZ

pytestmark = pytest.mark.usefixtures("painel_demo")
CPF = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")


@pytest.fixture
def con(painel_demo):
    with duckdb.connect(str(painel_demo["banco"]), read_only=True) as c:
        yield c


def test_todos_os_cartorios_do_municipio_do_maior_para_o_menor_deficit(con):
    from src.painel import analises
    r = analises.cartorios_do_municipio(con, "MG", municipio="Belo Horizonte")
    n = con.execute("SELECT count(*) FROM gold.serventia_publico WHERE municipio = 'Belo Horizonte' AND uf = 'MG'"
                    ).fetchone()[0]
    assert len(r["cartorios"]) == n > 30                    # todos (a consulta antiga do chat parava em 30)
    deficits = [c["deficit_cru"] for c in r["cartorios"]]
    assert deficits == sorted(deficits, reverse=True)
    assert all(re.fullmatch(r"\d{6}", c["cns"]) for c in r["cartorios"])
    assert {c["situacao"] for c in r["cartorios"]} <= set(analises.SITUACAO.values())
    todas = {s for (s,) in con.execute("SELECT DISTINCT situacao_juridica FROM gold.serventia_publico").fetchall()}
    # toda situação da carga tem tradução; a vazia (a fonte não informou, D-088) vira "não informada"
    assert todas - {None, ""} <= set(analises.SITUACAO), todas - set(analises.SITUACAO)
    assert r["citar"].startswith("Fonte:") and r["fonte"] == "gold.serventia_publico"
    soma = con.execute("SELECT sum(valor_descoberto) FROM gold.serventia_publico WHERE municipio = 'Belo Horizonte'"
                       ).fetchone()[0]
    assert sum(deficits) == pytest.approx(soma)


def test_nome_sem_acento_municipio_inexistente_e_sem_municipio(con):
    from src.painel import analises
    assert analises.cartorios_do_municipio(con, "MG", municipio="uberlandia")["municipio"] == "Uberlândia"
    assert "erro" in analises.cartorios_do_municipio(con, "MG", municipio="Cidade Que Não Existe")
    vazio = analises.cartorios_do_municipio(con, "MG")
    assert vazio["cartorios"] == [] and "erro" not in vazio
    assert analises.cartorios_do_municipio(con, "BA", municipio="Uberaba").get("erro")   # fora do estudo (D-088)


def test_quadro_sem_nome_de_pessoa(con):
    """D-038: só CNS e município; os textos do quadro não trazem CPF nem os campos de nome do cadastro."""
    from src.painel import analises
    r = analises.cartorios_do_municipio(con, "MG", municipio="Uberaba")
    textos = [v for c in r["cartorios"] for v in c.values() if isinstance(v, str)]   # os números crus não são CPF
    assert not [t for t in textos if CPF.search(t)]
    assert not {"responsavel", "titular_nome", "nome"} & {k for c in r["cartorios"] for k in c}


def test_chat_alcanca_o_quadro():
    from src.agent import ferramentas
    assert "cartorios_do_municipio" in ferramentas.CONSULTAS["consultar_mercado"]


def test_pagina_mostra_o_quadro_quando_ha_municipio(con):
    from apoio_painel import escolher_municipio, pagina_em_mg
    at = pagina_em_mg(MERCADO)
    assert not at.exception
    assert not [h for h in at.header if h.value.startswith("Os cartórios de")]   # MG inteira: sem quadro
    escolher_municipio(at, "Uberaba")
    assert not at.exception
    assert [h.value for h in at.header] == ["Os cartórios de Uberaba"]
    tela = "\n".join(m.value for m in at.markdown)
    cnss = [c for (c,) in con.execute("SELECT cns FROM gold.serventia_publico WHERE municipio = 'Uberaba'").fetchall()]
    assert all(f"<td>{c}</td>" in tela for c in cnss)
    assert 'class="rd-so-pc"' in tela                   # colunas secundárias escondidas no celular


def test_tabela_esconde_colunas_no_celular(monkeypatch):
    from src.painel import ui
    saida = []
    monkeypatch.setattr(ui, "_html", saida.append)
    ui.tabela(["A", "B", "C"], [["1", "2", "3"]], numericas={2}, mudas={1}, so_no_computador={1, 2})
    html = saida[0]
    assert '<th>A</th><th class="rd-so-pc">B</th><th class="rd-so-pc">C</th>' in html
    assert '<td>1</td><td class="rd-mudo rd-so-pc">2</td><td class="rd-num rd-so-pc">3</td>' in html
    css = (RAIZ / "src" / "painel" / "estilo.css").read_text(encoding="utf-8")
    assert re.search(r"@media \(max-width: 640px\) \{ \.rd-tabela \.rd-so-pc \{ display: none; \} \}", css)
