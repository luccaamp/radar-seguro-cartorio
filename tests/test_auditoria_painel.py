"""Auditoria do painel (docs/historico/revisao_painel_filtros.md, seção 5): percorre os estados do Mercado e do Simulador
(3 cenários) com o AppTest e checa mapa, consistência numérica e formato. Roda na cópia temporária do banco
(fixture banco_temporario).

Desde a D-051 (terceira rodada do painel), a página "Onde está o mercado" tem um filtro só (município) e o mapa do
déficit: os estados por métrica, por atribuição/situação/classe e pela regra v1 saíram da tela (o chat responde).
Desde a D-078 (D-038, fase 2), o mapa tem uma área por município e não há auditor de ataque por diferença.
Desde a D-083, o mapa é o componente clicável de src/painel/mapa.py; os testes leem os dados que ele recebe.
"""
import re
import time

import duckdb
import pytest

from apoio_painel import RAIZ, mapa_componente

# dados_reais: lê o banco completo; fora da suíte padrão
pytestmark = [pytest.mark.dados_reais, pytest.mark.usefixtures("banco_temporario")]
MERCADO = str(RAIZ / "app/pages/2_Onde_está_o_mercado.py")
SIMULADOR = str(RAIZ / "app/pages/6_Explorar.py")


# ------------------------------------------------------------------ apoio
@pytest.fixture(scope="module")
def db(banco_temporario):
    # mesma configuração da conexão do painel (o DuckDB não abre o mesmo arquivo com configurações diferentes no
    # mesmo processo); é a CÓPIA temporária, não o banco real
    con = duckdb.connect(str(banco_temporario["copia"]), read_only=True)
    yield con
    con.close()


def mercado(municipio=None):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(MERCADO, default_timeout=120).run()
    if municipio:
        at.selectbox(key="f_mun").set_value(municipio).run()
    assert not at.exception, at.exception
    return at


def html(at) -> str:
    return "\n".join(m.value for m in at.markdown).replace("&#36;", "$")


def textos_tabelas(at) -> list[str]:
    out = []
    for d in at.dataframe:
        df = d.value
        out += [str(v) for c in df.columns for v in df[c].dropna()]
    return out


# ------------------------------------------------------------------ mapa na visão geral
def test_estado_do_mercado(db):
    at = mercado()
    mapa = mapa_componente(at)
    areas = db.execute("SELECT * FROM gold.mercado_area_publico").df()
    assert mapa is not None
    # E3: legenda com título, o zero à parte e as faixas em R$
    assert mapa["tituloLegenda"] and mapa["legenda"][0]["faixa"] == "zero"
    assert all("R$" in item["texto"] for item in mapa["legenda"][1:])
    # E5: sem serventia como fundo (não clicável), com legenda própria
    assert mapa["fundo"] and mapa["legendaFundo"]
    # D-078: uma área por município com serventia, todas com o nome do município; somam o déficit de MG
    com_serv = db.execute("SELECT count(*) FROM gold.dim_municipio WHERE n_serventias > 0").fetchone()[0]
    assert len(mapa["areas"]) == com_serv and (areas["tipo"] == "municipio").all()
    assert sum(a["valor"] for a in mapa["areas"]) == pytest.approx(float(areas["valor_descoberto"].sum()), rel=0.005)
    # D-083: o zero tem cor neutra, fora da escala
    assert all((a["faixa"] == "zero") == (a["valor"] == 0) for a in mapa["areas"])
    # ranking: os 10 municípios com mais déficit, numa tabela abaixo do mapa
    assert html(at).count("º</td>") == 10
    # E7, E8: números dos cartões no formato do painel
    for v in re.findall(r'<div class="rd-num">([^<]+)<', html(at)):
        assert "R$ 0,00" not in v and not v.endswith("…")


@pytest.mark.parametrize("municipio_sql, rotulo", [
    ("SELECT municipio FROM gold.dim_municipio ORDER BY n_serventias DESC LIMIT 1", "grande"),
    ("SELECT municipio FROM gold.dim_municipio WHERE n_serventias BETWEEN 3 AND 5 ORDER BY municipio LIMIT 1", "medio"),
    ("SELECT municipio FROM gold.dim_municipio WHERE n_serventias BETWEEN 1 AND 2 ORDER BY municipio LIMIT 1", "pequeno")])
def test_filtro_de_municipio_destaque_com_contexto(municipio_sql, rotulo, db):
    """U1: MG inteiro como contexto, destaque com contorno forte, zoom na intermediária; o pequeno também com os números
    dele (D-078)."""
    nome = db.execute(municipio_sql).fetchone()[0]
    at = mercado(municipio=nome)
    mapa, geral = mapa_componente(at), mapa_componente(mercado())
    cod = db.execute("SELECT cod_ibge FROM gold.dim_municipio WHERE municipio = ?", [nome]).fetchone()[0]
    assert mapa["selecionado"] == str(cod)                    # destaque com contorno forte (classe rd-sel no JS)
    assert len(mapa["areas"]) > 300                           # contexto: MG inteiro
    largura = lambda m: float(m["viewBox"].split()[2])        # noqa: E731
    assert largura(mapa) < largura(geral)                     # enquadra a região intermediária
    tela = html(at)
    assert f"Déficit em {nome}" in tela and "Parte do déficit de MG" in tela
    assert "municípios no déficit" in tela                    # a posição dele no ranking de MG
    assert not any("agregad" in i.value for i in at.info)


# ------------------------------------------------------------------ consistência numérica
def test_somas_por_classe_e_situacao_fecham_o_total(db):
    geral = db.execute("SELECT * FROM gold.fato_mercado_uf WHERE regra_classe = 'v2' AND nivel = 'base' "
                       "AND cenario_stf = 'mantem'").df().iloc[0]
    for filtro in ("classe", "situacao"):
        s = db.execute("SELECT * FROM gold.mercado_filtro_uf WHERE filtro = ? AND regra_classe = 'v2' "
                       "AND nivel = 'base'", [filtro]).df()
        for col in ("n_serventias_ativas", "clt", "passivo_todas", "passivo_universo", "valor_descoberto", "n_deficit"):
            assert s[col].sum() == pytest.approx(geral[col], rel=1e-6), (filtro, col)
    a = db.execute("SELECT sum(n_serventias_ativas) FROM gold.mercado_filtro_uf WHERE filtro = 'atribuicao' "
                   "AND regra_classe = 'v2' AND nivel = 'base'").fetchone()[0]
    assert a >= geral["n_serventias_ativas"]   # uma serventia tem várias atribuições (explicado na tela)


def test_faixas_ordenadas_em_cada_filtro(db):
    df = db.execute("SELECT * FROM gold.mercado_filtro_uf").df()
    assert len(df) == 13 * 6   # todos os recortes em toda regra e nível (D-078)
    for (visao, regra), g in df.groupby(["visao", "regra_classe"]):
        g = g.set_index("nivel")
        for col in ("passivo_todas", "passivo_universo", "valor_descoberto", "mercado_importancia_segurada",
                    "mercado_premio_emitido"):
            niveis = [n for n in ("min", "base", "max") if n in g.index]
            vals = [g.at[n, col] for n in niveis]
            assert vals == sorted(vals), (visao, regra, col)


def test_kpis_iguais_entre_sobre_os_dados_e_simulador():
    """D-051: os 10 números ficam na tabela de "Sobre os dados"; o Simulador (fora da navegação) bate com ela."""
    from streamlit.testing.v1 import AppTest
    sob = AppTest.from_file(str(RAIZ / "app/pages/4_Sobre_os_dados.py"), default_timeout=120).run()
    sim = AppTest.from_file(SIMULADOR, default_timeout=120).run()
    v = lambda at, rot: [m.value for m in at.metric if m.label == rot]  # noqa: E731
    tela = html(sob)
    linha = lambda rot: re.search(rf'<td>{re.escape(rot)}</td><td class="rd-num">([^<]+)<', tela).group(1)  # noqa: E731
    assert [linha("Passivo trabalhista (obrigadas)")] == v(sim, "Passivo dos obrigados")
    assert [linha("Com déficit (esperado)")] == v(sim, "Com déficit (esperado)")
    assert [linha("Déficit de cobertura")] == v(sim, "Déficit de cobertura")


@pytest.mark.parametrize("cenario", ["mantem", "suspende_8_17", "parcial"])
def test_simulador_nos_tres_cenarios(cenario):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(SIMULADOR, default_timeout=120).run()
    at.radio(key="x_cenario").set_value(cenario).run()
    assert not at.exception
    premio = [m.value for m in at.metric if m.label == "Prêmio emitido"][0]
    assert (premio == "R$ 0") == (cenario == "suspende_8_17")
    assert "R$ 0,00" not in " ".join(m.value for m in at.metric)


def test_desempenho_da_troca_de_filtro():
    """Troca de município: medida no AppTest (inclui renderizar); alvo de ~2 s."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(MERCADO, default_timeout=120).run()
    tempos = []
    for nome in ("Belo Horizonte", "Uberaba", "Todos"):
        t0 = time.perf_counter()
        at.selectbox(key="f_mun").set_value(nome).run()
        tempos.append(time.perf_counter() - t0)
    print("tempos de troca de município (s):", [round(t, 2) for t in tempos])
    assert max(tempos) < 4.0
