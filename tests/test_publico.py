"""Conjunto público versionado (data/publico, D-029): integridade, LGPD e coerência com o gold local.

Os testes de integridade e LGPD rodam em qualquer clone. O de coerência só roda se o banco local existir: o
conjunto público tem de ter o mesmo conteúdo (hash) que o gold atual.
"""
import json

import duckdb
import pytest

from apoio_painel import BANCO_REAL
from src import publico

MAN = publico.ler_manifesto()


def test_manifesto_e_arquivos_batem():
    assert MAN, "data/publico/manifesto.json ausente: rode uv run python scripts/gerar_publico.py"
    for chave in ("carga", "executado_em", "versao_premissas", "commit", "fontes", "arquivos"):
        assert chave in MAN
    for a in MAN["arquivos"]:
        p = publico.PASTA / a["arquivo"]
        assert p.stat().st_size == a["bytes"] and publico.sha256_arquivo(p) == a["sha256_arquivo"], a["arquivo"]
    assert {a["tabela"] for a in MAN["arquivos"]} == set(publico.tabelas())
    total = sum(a["bytes"] for a in MAN["arquivos"])
    assert total < publico.CONFIG["limite_mb"] * 1e6, f"{total / 1e6:.1f} MB"


def test_sem_dado_pessoal_nem_area_abaixo_do_limiar(tmp_path):
    banco = publico.montar_banco(publico.PASTA, tmp_path / "publico.duckdb")
    with duckdb.connect(str(banco), read_only=True) as con:
        problemas, excecoes = publico.checar(con, MAN["limiar_lgpd"])
    assert not problemas, problemas
    assert all(e.split(":")[0] in publico.CONFIG["excecoes_limiar"] for e in excecoes)


def test_checagem_pega_os_casos_errados(tmp_path):
    """Dados SINTÉTICOS: cada problema plantado precisa ser pego."""
    with duckdb.connect(str(tmp_path / "ruim.duckdb")) as con:
        con.execute("CREATE SCHEMA gold")
        con.execute("CREATE TABLE gold.interno_x AS SELECT 1 AS a")
        con.execute("CREATE TABLE gold.t AS SELECT '000.111.222-33' AS obs, 'x@y.com' AS contato, 'FULANO DE TAL' AS b, "
                    "'999999' AS cod, 2 AS n_serventias, 'z' AS responsavel")
        problemas, _ = publico.checar(con, 3, cns={"999999"}, nomes={"FULANO DE TAL"})
    texto = " | ".join(problemas)
    for esperado in ("tabela interna", "CPF", "e-mail", "nome de pessoa", "CNS", "abaixo do limiar", "proibido"):
        assert esperado in texto, (esperado, problemas)


def test_cns_so_nas_tabelas_por_serventia(tmp_path):
    """Dados SINTÉTICOS (D-048): o CNS é esperado nas tabelas por serventia e continua erro numa tabela agregada; nome
    de pessoa é erro nas duas."""
    assert "gold.serventia_publico" in publico.CONFIG["por_serventia"]
    with duckdb.connect(str(tmp_path / "x.duckdb")) as con:
        con.execute("CREATE SCHEMA gold")
        con.execute("CREATE TABLE gold.serventia_publico AS SELECT '999999' AS cns, 'BELO HORIZONTE' AS municipio")
        con.execute("CREATE TABLE gold.agregada AS SELECT '999999' AS area")
        problemas, _ = publico.checar(con, 3, cns={"999999"})
        assert problemas == ["gold.agregada.area: código CNS de serventia"], problemas
        con.execute("CREATE OR REPLACE TABLE gold.serventia_publico AS SELECT '999999' AS cns, 'FULANO DE TAL' AS obs")
        con.execute("DROP TABLE gold.agregada")
        problemas, _ = publico.checar(con, 3, cns={"999999"}, nomes={"FULANO DE TAL"})
    assert len(problemas) == 1 and "nome de pessoa" in problemas[0]


def test_mesmo_conteudo_tolera_so_ruido_de_ponto_flutuante():
    """Dados SINTÉTICOS: ruído abaixo da tolerância passa; diferença acima dela, em texto ou em inteiro, não."""
    tol = publico.CONFIG["tolerancia_coerencia"]
    with duckdb.connect() as con:
        con.execute("CREATE TABLE a AS SELECT 'x' AS t, 1 AS n, 1000.0::DOUBLE AS v, 'h1' AS carimbo")
        casos = {f"'x', 1, {1000 * (1 + tol / 10)}, 'h2'": True,    # ruído entre máquinas; carimbo fora do hash
                 f"'x', 1, {1000 * (1 + tol * 10)}, 'h1'": False,   # diferença real no valor
                 "'y', 1, 1000.0, 'h1'": False, "'x', 2, 1000.0, 'h1'": False}
        for valores, esperado in casos.items():
            con.execute(f"CREATE OR REPLACE TABLE b AS SELECT t, n, v::DOUBLE AS v, carimbo "
                        f"FROM (VALUES ({valores})) x(t, n, v, carimbo)")
            assert publico.mesmo_conteudo(con, "a", "b", ["carimbo"]) is esperado, valores


@pytest.mark.skipif(not BANCO_REAL.exists(), reason="sem banco local: nada a comparar")
def test_publico_coerente_com_o_gold_local():
    """Se o gold local existir, o conjunto público tem de bater com ele (hash de conteúdo ou, entre máquinas, os
    mesmos valores dentro da tolerância de ponto flutuante)."""
    with duckdb.connect(str(BANCO_REAL), read_only=True) as con:
        diferentes = [a["tabela"] for a in MAN["arquivos"] if not publico.tabela_coerente(con, a)]
    assert not diferentes, (f"dados públicos desatualizados: rode `uv run python scripts/gerar_publico.py` "
                            f"({len(diferentes)} tabelas diferentes: {diferentes[:5]})")


def test_manifesto_sem_dado_pessoal():
    texto = json.dumps(MAN, ensure_ascii=False)
    assert not publico.CPF.search(texto) and not publico.EMAIL.search(texto)
