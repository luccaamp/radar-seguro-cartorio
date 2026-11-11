"""Agente "o que mudou" (src/agent/o_que_mudou.py): a comparação determinística entre dois conjuntos públicos e a trava
que descarta o resumo da IA com número sem apoio. Usa o conjunto público versionado e uma cópia ALTERADA dele
(dado SINTÉTICO: o prêmio multiplicado por 1,1, só para o teste). O modelo é um dublê: nenhuma chamada à API."""
import json
import shutil

import duckdb
import pytest

from src import publico
from src.agent import o_que_mudou as om


@pytest.fixture(scope="module")
def alterado(tmp_path_factory):
    """Cópia do data/publico com o prêmio do gold.fato_mercado_uf × 1,1 e outra data de carga (SINTÉTICO)."""
    pasta = tmp_path_factory.mktemp("publico_sintetico") / "publico"
    shutil.copytree(publico.PASTA, pasta)
    arq = pasta / "gold.fato_mercado_uf.parquet"
    with duckdb.connect() as con:
        con.execute(f"COPY (SELECT * REPLACE (mercado_premio_emitido * 1.1 AS mercado_premio_emitido) "
                    f"FROM read_parquet('{arq.as_posix()}')) TO '{(pasta / 'novo.parquet').as_posix()}' (FORMAT parquet)")
    (pasta / "novo.parquet").replace(arq)
    man = json.loads((pasta / publico.MANIFESTO).read_text(encoding="utf-8"))
    man["carga"] = "2099-01-01"   # sintético
    for a in man["arquivos"]:
        if a["tabela"] == "gold.fato_mercado_uf":
            a["sha256_arquivo"] = publico.sha256_arquivo(arq)
            a["sha256_conteudo"] = "sintetico"
    (pasta / publico.MANIFESTO).write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")
    return pasta


def test_mesmo_conjunto_nada_mudou():
    d = om.comparar(publico.PASTA, publico.PASTA)
    assert not any(n["mudou"] for n in d["numeros"]) and len(d["numeros"]) == 10
    assert d["tabelas_mudaram"] == [] and d["fontes"] == []
    assert "nenhum mudou" in om.relatorio(d)


def test_premio_alterado_aparece_no_relatorio(alterado):
    d = om.comparar(publico.PASTA, alterado)
    mudaram = [n for n in d["numeros"] if n["mudou"]]
    assert [n["rotulo"] for n in mudaram] == ["Prêmio anual do mercado"]
    assert mudaram[0]["antes"] == "R$ 341,1 mil" and mudaram[0]["variacao"] == pytest.approx(0.1)
    assert [t["tabela"] for t in d["tabelas_mudaram"]] == ["gold.fato_mercado_uf"]
    texto = om.relatorio(d)
    assert "**2099-01-01**" in texto and "+10,0%" in texto and "R$ 375,2 mil" in texto


def test_resumo_da_ia_com_numero_inventado_e_descartado(alterado):
    d = om.comparar(publico.PASTA, alterado)
    bom = "O prêmio anual do mercado passou de R$ 341,1 mil para R$ 375,2 mil (+10,0%); os outros números não mudaram."
    base, resumo = om.resumir(d, gerar=lambda s, t: bom)
    assert resumo == bom and "R$ 375,2 mil" in base
    _, inventado = om.resumir(d, gerar=lambda s, t: "O prêmio subiu para R$ 400 mil.")
    assert inventado is None                                   # "400" não está no relatório
    assert om.numeros_sem_apoio("subiu 3 pontos", "R$ 341,1 mil") == ["3"]   # pedaço de outro número não vale
    _, falhou = om.resumir(d, gerar=lambda s, t: (_ for _ in ()).throw(RuntimeError("API fora")))
    assert falhou is None                                      # IA indisponível: fica só o relatório
    md = om.markdown(d, resumo, base)
    assert md.startswith("# O que mudou na carga de 2099-01-01") and "conferido no relatório" in md


def test_colunas_novas_aparecem(tmp_path):
    a = tmp_path / "a.parquet"
    b = tmp_path / "b.parquet"
    with duckdb.connect() as con:
        con.execute(f"COPY (SELECT 1 AS x) TO '{a.as_posix()}' (FORMAT parquet)")
        con.execute(f"COPY (SELECT 'MG' AS uf, 1 AS x) TO '{b.as_posix()}' (FORMAT parquet)")
    assert om._colunas(a) == ["x"] and om._colunas(b) == ["uf", "x"]
    d = {"carga": ("a", "b"), "premissas": (4, 4), "numeros": [], "fontes": [], "tabelas_novas": [],
         "tabelas_retiradas": [], "tabelas_mudaram": [{"tabela": "gold.t", "linhas_antes": 1, "linhas_depois": 1,
                                                       "colunas_novas": ["uf"], "colunas_retiradas": []}]}
    assert "coluna nova: `uf`" in om.relatorio(d)
