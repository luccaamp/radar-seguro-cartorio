"""Auditoria do painel (docs/historico/revisao_painel_filtros.md, seção 5): percorre os estados do Mercado e do Simulador
(3 cenários) com o AppTest e checa mapa, LGPD, consistência numérica e formato. Roda na cópia temporária do banco
(fixture banco_temporario).

Desde a D-051 (terceira rodada do painel), a página "Onde está o mercado" tem um filtro só (município) e o mapa do
déficit: os estados por métrica, por atribuição/situação/classe e pela regra v1 saíram da tela (o chat responde). As
conferências das tabelas públicas filtradas e do auditor continuam, porque as tabelas seguem no conjunto público.
"""
import json
import re
import time

import duckdb
import pytest

from apoio_painel import RAIZ

# dados_reais: lê silver.serventia e interno_celulas_publicadas (banco completo); fora da suíte padrão
pytestmark = [pytest.mark.dados_reais, pytest.mark.usefixtures("banco_temporario")]
MERCADO = str(RAIZ / "app/pages/2_Onde_está_o_mercado.py")
SIMULADOR = str(RAIZ / "app/simulador.py")
SEM_SERV, CONTORNO = "#f5f7fa", "#45506a"   # cores do mapa no visual da D-052 (app/pages/2_Onde_está_o_mercado.py)


# ------------------------------------------------------------------ apoio
@pytest.fixture(scope="module")
def db(banco_temporario):
    # mesma configuração da conexão do painel (o DuckDB não abre o mesmo arquivo com configurações diferentes no
    # mesmo processo); é a CÓPIA temporária, não o banco real
    con = duckdb.connect(str(banco_temporario["copia"]), read_only=True)
    yield con
    con.close()


@pytest.fixture(scope="module")
def pequenos(db):
    """Nomes e códigos dos municípios com menos de 3 serventias (inclusive sem serventia)."""
    linhas = db.execute("""SELECT m.nome, m.cod_ibge FROM silver.municipio_ibge m LEFT JOIN
        (SELECT cod_ibge, count(*) n FROM silver.serventia WHERE status = 'Ativo' GROUP BY 1) s USING (cod_ibge)
        WHERE coalesce(s.n, 0) < 3""").fetchall()
    return {n for n, _ in linhas} | {str(c) for _, c in linhas}


def mercado(municipio=None):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(MERCADO, default_timeout=120).run()
    if municipio:
        at.selectbox(key="f_mun").set_value(municipio).run()
    assert not at.exception, at.exception
    return at


def html(at) -> str:
    return "\n".join(m.value for m in at.markdown).replace("&#36;", "$")


def figuras(at):
    specs = [json.loads(g.proto.spec) for g in at.get("plotly_chart")]
    return next((s for s in specs if any(t.get("type") == "choroplethmap" for t in s["data"])), None)


def vetor(v) -> list:
    """O Plotly 6 grava vetores numéricos no JSON como {'dtype', 'bdata' (base64)}; devolve uma lista comum."""
    if isinstance(v, dict) and "bdata" in v:
        import base64
        import numpy as np
        return np.frombuffer(base64.b64decode(v["bdata"]), dtype=np.dtype(v["dtype"])).tolist()
    return list(v or [])


def traco_dados(mapa):
    t = next(t for t in mapa["data"] if "colorbar" in t)
    return {**t, "z": vetor(t.get("z"))}


def cor_fixa(t):
    cs = t.get("colorscale") or []
    return cs[0][1] if cs and cs[0][1] == cs[-1][1] else None


def textos_tabelas(at) -> list[str]:
    out = []
    for d in at.dataframe:
        df = d.value
        out += [str(v) for c in df.columns for v in df[c].dropna()]
    return out


# ------------------------------------------------------------------ mapa na visão geral
def test_estado_do_mercado(db, pequenos):
    at = mercado()
    mapa = figuras(at)
    areas = db.execute("SELECT * FROM gold.mercado_area_publico").df()
    assert mapa is not None
    dados = traco_dados(mapa)
    # E3: escala de cores com rótulos em R$
    cb = dados["colorbar"]
    assert cb.get("tickvals") and cb.get("ticktext")
    assert all(t.lstrip("≥ ").startswith("R$") for t in cb["ticktext"])
    # E5: sem serventia com contorno; nenhum branco puro como cor fixa
    fixas = [cor_fixa(t) for t in mapa["data"] if cor_fixa(t)]
    assert SEM_SERV in fixas and not any(c and c.lower() in ("#ffffff", "white") for c in fixas)
    sem = next(t for t in mapa["data"] if cor_fixa(t) == SEM_SERV)
    assert sem["marker"]["line"]["color"] == CONTORNO
    # LGPD no texto do mouse e nos identificadores
    valores = {str(x) for t in mapa["data"] for campo in ("locations", "hovertext") for x in (t.get(campo) or [])}
    valores |= {str(x) for t in mapa["data"] for linha in (t.get("customdata") or []) for x in linha}
    assert not (valores & pequenos)
    # as áreas do mapa somam o déficit de MG; área agregada nunca leva o nome de um município sozinho
    assert sum(dados["z"]) == pytest.approx(float(areas["valor_descoberto"].sum()), rel=0.005)
    tipo = dict(zip(areas["area_nome"], areas["tipo"]))
    for linha in dados["customdata"]:
        if tipo[linha[0]] != "municipio":
            assert linha[0].startswith(("Região", "Município ")) and ("—" in linha[0] or "+" in linha[0] or
                                                                      linha[0].startswith("Região imediata de"))
    # E7, E8: números dos cartões no formato do painel
    for v in re.findall(r'<div class="rd-num">([^<]+)<', html(at)):
        assert "R$ 0,00" not in v and not v.endswith("…")


@pytest.mark.parametrize("municipio_sql, rotulo", [
    ("SELECT municipio FROM gold.dim_municipio ORDER BY n_serventias DESC LIMIT 1", "grande"),
    ("SELECT municipio FROM gold.dim_municipio WHERE n_serventias BETWEEN 3 AND 5 ORDER BY municipio LIMIT 1", "medio"),
    ("SELECT municipio FROM gold.dim_municipio WHERE n_serventias BETWEEN 1 AND 2 ORDER BY municipio LIMIT 1", "pequeno")])
def test_filtro_de_municipio_destaque_com_contexto(municipio_sql, rotulo, db, pequenos):
    """U1: MG inteiro como contexto, destaque com contorno forte, zoom na intermediária; pequeno -> área agregada."""
    nome = db.execute(municipio_sql).fetchone()[0]
    at = mercado(municipio=nome)
    mapa = figuras(at)
    destaque = [t for t in mapa["data"] if t.get("type") == "choroplethmap" and
                (t.get("marker", {}).get("line", {}).get("width") or 0) >= 2]
    assert len(destaque) == 1 and len(destaque[0]["locations"]) == 1
    assert len(traco_dados(mapa)["locations"]) > 300          # contexto: MG inteiro
    assert mapa["layout"]["map"]["zoom"] > 5.4                # enquadra a região intermediária
    valores = {str(x) for t in mapa["data"] for x in (t.get("locations") or [])}
    valores |= {str(x) for t in mapa["data"] for linha in (t.get("customdata") or []) for x in linha}
    assert not (valores & pequenos)
    tela = html(at)
    if rotulo == "pequeno":
        assert any("agregado" in i.value for i in at.info)
        assert f"Déficit em {nome}" not in tela               # o município pequeno nunca aparece sozinho
    else:
        assert f"Déficit em {nome}" in tela and "Parte do déficit de MG" in tela


# ------------------------------------------------------------------ LGPD: ataque por diferença
def test_ataque_por_diferenca(db):
    """Para todas as visões públicas (geral, cada valor de cada filtro, totais de MG por regra e nível): nenhum par de
    células cujo conjunto de serventias difira em 1 ou 2, nenhum complemento ou resto de partição de 1 ou 2."""
    from src.model.supressao import Celula, vazamentos
    from src.transform.visoes import PARTICOES
    cel = db.execute("SELECT visao, area_id, conjunto, list(cns) FROM gold.interno_celulas_publicadas GROUP BY ALL").fetchall()
    por = {}
    for visao, area, conj, cns in cel:
        por.setdefault((visao, area), {})[conj] = frozenset(cns)
    celulas = [Celula(v, a, s.get("todos", frozenset()), s.get("universo", frozenset())) for (v, a), s in por.items()]
    base = db.execute("""SELECT i.cns, m.regiao_imediata FROM gold.interno_serventia i JOIN silver.municipio_ibge m
                         USING (cod_ibge) WHERE nivel = 'base' AND regra_classe = 'v2'""").df()
    totais = {f"RI:{ri}": frozenset(g["cns"]) for ri, g in base.groupby("regiao_imediata")} | {"MG": frozenset(base["cns"])}
    assert len(celulas) > 800
    assert vazamentos(celulas, 3, totais, PARTICOES) == []
    # caso fixo do E1: BH (visão geral) contra qualquer célula publicada contida nele
    bh = db.execute("""SELECT list(i.cns) FROM gold.interno_serventia i JOIN gold.dim_municipio d USING (cod_ibge)
                       WHERE d.municipio = 'Belo Horizonte' AND nivel = 'base' AND regra_classe = 'v2'""").fetchone()[0]
    bh = frozenset(bh)
    assert not [c for c in celulas if c.todos < bh and 0 < len(bh - c.todos) < 3]


def test_tabelas_publicas_batem_com_as_celulas_auditadas(db):
    """O que está nas tabelas públicas filtradas é exatamente o que o auditor aprovou."""
    pub = db.execute("SELECT visao, area_id, n_serventias FROM gold.mercado_filtro_area").fetchall()
    cel = dict(((v, a.split("@")[0]), n) for v, a, n in db.execute(
        "SELECT visao, area_id, count(*) FROM gold.interno_celulas_publicadas WHERE conjunto = 'todos' "
        "AND visao NOT LIKE 'uf:%' AND visao NOT LIKE 'sim:%' AND visao <> 'geral' GROUP BY ALL").fetchall())
    assert {(v, a): n for v, a, n in pub} == cel   # as células 'sim:' são do Simulador (test_simulador_totais.py)


def test_celulas_do_simulador_batem_com_as_tabelas_publicas(db):
    """Cada célula 'sim:' auditada corresponde a uma faixa de uma variante de gold.simulador_*: só totais de MG."""
    sim = db.execute("""SELECT visao, count(*) FROM gold.interno_celulas_publicadas WHERE visao LIKE 'sim:%'
                        AND conjunto = 'universo' GROUP BY ALL""").fetchall()
    assert sim and all(v.split(":")[1] in ("v1", "v2") and v.split(":")[3] in ("classe_2", "classe_3") for v, _ in sim)
    vids = {int(v.split(":")[4]) for v, _ in sim}
    assert vids <= {r[0] for r in db.execute("SELECT variante_id FROM gold.simulador_variantes").fetchall()}
    assert all(n >= 3 for _, n in sim)


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
    df = db.execute("SELECT * FROM gold.mercado_filtro_uf WHERE publicado").df()
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
    at.radio[0].set_value(cenario).run()
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
