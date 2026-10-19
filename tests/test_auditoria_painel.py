"""Auditoria do painel (revisao_painel_filtros.md, seção 5): percorre os estados do Mercado (métricas, cada valor de
cada filtro, municípios de exemplo, as duas regras) e do Simulador (3 cenários) com o AppTest e checa mapa, ranking,
tabelas, LGPD, consistência numérica e formato. Roda na cópia temporária do banco (fixture banco_temporario).
"""
import json
import re
import time

import duckdb
import pytest

from apoio_painel import RAIZ

# dados_reais: lê silver.serventia e interno_celulas_publicadas (banco completo); fora da suíte padrão
pytestmark = [pytest.mark.dados_reais, pytest.mark.usefixtures("banco_temporario")]
MERCADO = str(RAIZ / "app/pages/1_Mercado.py")
FILTROS = {"atribuicao": ["notas", "rcpn", "ri", "rtd_rcpj", "protesto"],
           "situacao": ["PROVIDO", "VAGO", "SOB INTERVENÇÃO", "CONVERSÃO EM DILIGÊNCIA"],
           "classe": ["1", "2", "3", "indeterminada"]}
METRICAS = ["valor_descoberto", "passivo", "n_serventias", "clt"]
CINZA, SEM_SERV, CONTORNO = "#c9c8c4", "#f3f2ee", "#55534e"
COL_UF = {"valor_descoberto": "valor_descoberto", "passivo": "passivo_todas", "n_serventias": "n_serventias_ativas",
          "clt": "clt"}


# ------------------------------------------------------------------ apoio
@pytest.fixture(scope="module")
def db(banco_temporario):
    # mesma configuração da conexão do painel (o DuckDB não abre o mesmo arquivo com configurações diferentes no
    # mesmo processo); é a CÓPIA temporária, não o banco real
    con = duckdb.connect(str(banco_temporario["copia"]))
    yield con
    con.close()


@pytest.fixture(scope="module")
def pequenos(db):
    """Nomes e códigos dos municípios com menos de 3 serventias (inclusive sem serventia)."""
    linhas = db.execute("""SELECT m.nome, m.cod_ibge FROM silver.municipio_ibge m LEFT JOIN
        (SELECT cod_ibge, count(*) n FROM silver.serventia WHERE status = 'Ativo' GROUP BY 1) s USING (cod_ibge)
        WHERE coalesce(s.n, 0) < 3""").fetchall()
    return {n for n, _ in linhas} | {str(c) for _, c in linhas}


def mercado(tipo=None, valor=None, metrica=None, municipio=None, regra=None):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(MERCADO, default_timeout=120).run()
    if regra:
        at.radio(key="f_regra").set_value(regra).run()
    if municipio:
        at.selectbox(key="f_mun").set_value(municipio).run()
    if tipo:
        at.selectbox(key="f_tipo").set_value(tipo).run()
        at.selectbox(key="f_valor").set_value(valor).run()
    if metrica:
        [r for r in at.radio if r.label.startswith("Métrica")][0].set_value(metrica).run()
    assert not at.exception, at.exception
    return at


def figuras(at):
    specs = [json.loads(g.proto.spec) for g in at.get("plotly_chart")]
    mapa = next((s for s in specs if any(t.get("type") == "choroplethmap" for t in s["data"])), None)
    ranking = next((s for s in specs if any(t.get("type") == "bar" for t in s["data"])), None)
    return mapa, ranking


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


ESTADOS = ([("geral", None, None, m) for m in METRICAS]
           + [(f"{t}={v}", t, v, m) for t, vs in FILTROS.items() for v in vs for m in ("valor_descoberto", "n_serventias")])


# ------------------------------------------------------------------ mapa, ranking e tabelas em cada estado
@pytest.mark.parametrize("nome, tipo, valor, metrica", ESTADOS, ids=[f"{e[0]}-{e[3]}" for e in ESTADOS])
def test_estado_do_mercado(nome, tipo, valor, metrica, db, pequenos):
    at = mercado(tipo, valor, metrica)
    mapa, ranking = figuras(at)
    if tipo:
        areas = db.execute("SELECT * FROM gold.mercado_filtro_area WHERE visao = ?", [nome]).df()
        uf = db.execute("SELECT * FROM gold.mercado_filtro_uf WHERE visao = ? AND regra_classe = 'v2' AND nivel = 'base'",
                        [nome]).df().iloc[0]
        total = float(uf[COL_UF[metrica]])
    else:
        areas = db.execute("SELECT *, tipo AS nivel_area FROM gold.mercado_area_publico").df()
        total = float(areas[metrica].sum())
    if not (areas[metrica].abs() > 0).any():   # E6: métrica zero em todas as áreas -> mensagem, sem gráfico
        assert mapa is None and ranking is None
        assert any("zero em todas as áreas" in i.value for i in at.info)
        return
    assert mapa is not None
    dados = traco_dados(mapa)
    # E3: escala de cores com rótulos formatados (R$ para valores)
    cb = dados["colorbar"]
    assert cb.get("tickvals") and cb.get("ticktext")
    if metrica in ("valor_descoberto", "passivo"):
        assert all(t.lstrip("≥ ").startswith("R$") for t in cb["ticktext"])
    # E5: três estados distintos (valor, cinza, sem serventia com contorno) e nenhum branco puro
    fixas = [cor_fixa(t) for t in mapa["data"] if cor_fixa(t)]
    assert CINZA in fixas and SEM_SERV in fixas
    assert not any(c and c.lower() in ("#ffffff", "white") for c in fixas)
    sem = next(t for t in mapa["data"] if cor_fixa(t) == SEM_SERV)
    assert sem["marker"]["line"]["color"] == CONTORNO
    # LGPD no texto do mouse e nos identificadores
    valores = {str(x) for t in mapa["data"] for campo in ("locations", "hovertext") for x in (t.get(campo) or [])}
    valores |= {str(x) for t in mapa["data"] for linha in (t.get("customdata") or []) for x in linha}
    assert not (valores & pequenos)
    # as áreas do mapa (+ "outras regiões", que não tem mapa) somam o total da visão
    soma = sum(dados["z"]) + float(areas.loc[areas["nivel_area"] == "outras", metrica].sum())
    assert soma == pytest.approx(total, rel=0.005)
    # área agregada nunca leva o nome de um município sozinho
    for linha in dados["customdata"]:
        nome_area, tipo_area = linha[0], linha[1]
        if tipo_area != "município":
            assert nome_area.startswith(("Região", "Município ")) and ("—" in nome_area or "+" in nome_area or
                                                                         nome_area.startswith("Região imediata de"))
    # E2: ranking com rótulo em todas as barras, eixo com folga e as mesmas áreas do mapa
    if ranking is not None:
        bar = next(t for t in ranking["data"] if t.get("type") == "bar")
        xs = vetor(bar["x"])
        assert all(bar["text"]) and len(bar["text"]) == len(xs)
        assert ranking["layout"]["xaxis"]["range"][1] >= max(xs) * 1.1
        assert {c[0] for c in bar["customdata"]} <= {c[0] for c in dados["customdata"]}
    # E4, E7, E8: tabelas cabem (até 7 colunas), "≈ " com espaço, 1 casa abaixo de 10, zero como "R$ 0"
    for d in at.dataframe:
        assert len(d.value.columns) <= 7, list(d.value.columns)
    for txt in textos_tabelas(at):
        assert "R$ 0,00" not in txt
        if txt.startswith("≈"):
            assert re.fullmatch(r"≈ [\d.]+(,\d)?", txt), txt
            num = float(txt[2:].replace(".", "").replace(",", "."))
            assert ("," in txt) == (num < 10), txt
        assert not txt.endswith("…")


@pytest.mark.parametrize("municipio_sql, rotulo", [
    ("SELECT municipio FROM gold.dim_municipio ORDER BY n_serventias DESC LIMIT 1", "grande"),
    ("SELECT municipio FROM gold.dim_municipio WHERE n_serventias BETWEEN 3 AND 5 ORDER BY municipio LIMIT 1", "medio"),
    ("SELECT municipio FROM gold.dim_municipio WHERE n_serventias BETWEEN 1 AND 2 ORDER BY municipio LIMIT 1", "pequeno")])
def test_filtro_de_municipio_destaque_com_contexto(municipio_sql, rotulo, db, pequenos):
    """U1: MG inteiro em cinza, destaque com contorno forte, zoom na intermediária; pequeno -> área agregada."""
    nome = db.execute(municipio_sql).fetchone()[0]
    at = mercado(municipio=nome)
    mapa, ranking = figuras(at)
    assert ranking is None                                   # ranking com 1 item vira tabela de posições
    dados = traco_dados(mapa)
    assert len(dados["locations"]) == 1 and dados["marker"]["line"]["width"] >= 2
    assert any(cor_fixa(t) == CINZA for t in mapa["data"])   # contexto
    assert mapa["layout"]["map"]["zoom"] > 5.1               # enquadra a região intermediária
    valores = {str(x) for t in mapa["data"] for x in (t.get("locations") or [])}
    valores |= {str(x) for t in mapa["data"] for linha in (t.get("customdata") or []) for x in linha}
    assert not (valores & pequenos)
    if rotulo == "pequeno":
        assert any("agregado" in i.value for i in at.info)
    else:
        posicoes = [d.value for d in at.dataframe if "Posição" in d.value.columns]
        assert posicoes and len(posicoes[0]) == 4


def test_municipio_mais_filtro_mostra_so_o_nivel_regional(db, pequenos):
    nome = db.execute("SELECT municipio FROM gold.dim_municipio ORDER BY n_serventias DESC LIMIT 1").fetchone()[0]
    at = mercado("classe", "3", municipio=nome)
    assert any("nível regional" in i.value for i in at.info) or any("publicável" in w.value for w in at.warning)
    assert not [m for m in at.metric if m.label == "Serventias ativas" and m.value == "34"]


def test_regra_v1_so_nos_totais(db):
    at = mercado(regra="v1")
    assert not at.exception
    at = mercado("classe", "indeterminada", regra="v1")   # v1 suprimida neste filtro pelo auditor
    assert any("regra v1 não é exibida" in w.value for w in at.warning)


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


def test_kpis_iguais_entre_inicio_mercado_e_simulador():
    from streamlit.testing.v1 import AppTest
    ini = AppTest.from_file(str(RAIZ / "app/Inicio.py"), default_timeout=120).run()
    mer = mercado()
    sim = AppTest.from_file(str(RAIZ / "app/pages/2_Simulador.py"), default_timeout=120).run()
    v = lambda at, rot: [m.value for m in at.metric if m.label == rot]  # noqa: E731
    assert v(ini, "Passivo dos obrigados") == v(mer, "Passivo (obrigados)") == v(sim, "Passivo dos obrigados")
    assert v(ini, "Passivo de todas as ativas") == v(mer, "Passivo (todas)")
    assert v(mer, "Com déficit (esperado)") == v(sim, "Com déficit (esperado)")


@pytest.mark.parametrize("cenario", ["mantem", "suspende_8_17", "parcial"])
def test_simulador_nos_tres_cenarios(cenario):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / "app/pages/2_Simulador.py"), default_timeout=120).run()
    at.radio[0].set_value(cenario).run()
    assert not at.exception
    premio = [m.value for m in at.metric if m.label == "Prêmio emitido"][0]
    assert (premio == "R$ 0") == (cenario == "suspende_8_17")
    assert "R$ 0,00" not in " ".join(m.value for m in at.metric)


def test_desempenho_da_troca_de_filtro():
    """Troca de filtro: medida no AppTest (inclui renderizar); alvo de ~2 s."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(MERCADO, default_timeout=120).run()
    tempos = []
    for tipo, valor in (("classe", "3"), ("situacao", "VAGO"), ("atribuicao", "notas")):
        t0 = time.perf_counter()
        at.selectbox(key="f_tipo").set_value(tipo).run()
        at.selectbox(key="f_valor").set_value(valor).run()
        tempos.append(time.perf_counter() - t0)
    print("tempos de troca de filtro (s):", [round(t, 2) for t in tempos])
    assert max(tempos) < 4.0
