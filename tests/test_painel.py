"""Painel da Etapa 3 (docs/painel/) no MODO DEMONSTRAÇÃO, que roda em qualquer clone (suíte padrão):
- as funções de src/painel/analises.py devolvem o formato das ferramentas do chat (valor formatado, conta, fonte, carga,
  premissas, `citar`) e são serializáveis;
- os 10 números do Início batem com a tabela do docs/ESTADO_ATUAL.md;
- os valores da D-042 batem com gold.analise_monte_carlo e gold.fato_mercado_uf, na ordem base > faixa > extremos;
- o 05b vem da saída do notebook (nada digitado no código) e a projeção é sempre rotulada;
- nenhum dado pessoal nos dados de demonstração nem nos downloads.
As mesmas conferências rodam no banco completo em tests/test_app.py (dados_reais).
"""
import json
import re

import duckdb
import pandas as pd
import pytest

from apoio_painel import RAIZ

pytestmark = pytest.mark.usefixtures("painel_demo")
# terceira rodada (D-051): os 10 números foram para "Sobre os dados"; a projeção, para "Para onde vai"
INICIO, SOBRE, PROJECAO = "app/Inicio.py", "app/pages/4_Sobre_os_dados.py", "app/pages/3_Para_onde_vai.py"
CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")


def rodar(pagina: str):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(RAIZ / pagina), default_timeout=120).run()
    assert not at.exception, at.exception
    return at


def html(at) -> str:
    return "\n".join(m.value for m in at.markdown).replace("&#36;", "$")


def con_demo(painel_demo):
    return duckdb.connect(str(painel_demo["banco"]), read_only=True)


def numeros_do_estado_atual() -> list[str]:
    """Os 10 números da tabela "Números de referência" do docs/ESTADO_ATUAL.md, na ordem 1 a 10."""
    texto = (RAIZ / "docs" / "ESTADO_ATUAL.md").read_text(encoding="utf-8").split("## Números de referência")[1]
    linhas = [ln.strip() for ln in texto.splitlines() if ln.strip().startswith("|")]
    valores = [ln for ln in linhas if not ln.startswith("|---") and not re.match(r"\|\s*\d+\.\s+\D", ln)]   # fora o cabeçalho "| 1. Serventias ativas |"
    out = [c.strip() for ln in valores[:2] for c in ln.strip("|").split("|")]
    assert len(out) == 10, out
    return out


def valor(texto: str) -> float:
    """'R$ 311,9 mi' → 311,9e6; '≈ 1.121' → 1121; '2.525' → 2525."""
    from src.painel.artefatos import numero_br
    return numero_br(texto.replace("≈", "").strip())


# ------------------------------------------------------------------ funções (formato das ferramentas do chat)
def test_funcoes_no_formato_das_ferramentas_do_chat(painel_demo):
    from src.painel import analises
    with con_demo(painel_demo) as con:
        for nome, f in analises.PARA_O_CHAT.items():
            r = f(con, "MG")
            assert "erro" not in r, (nome, r)
            json.dumps(r)   # serializável (o chat manda para o modelo)
            assert r["citar"].startswith("Fonte:") and "premissas v" in r["citar"], nome
            assert {"fonte", "carga", "versao_premissas", "data_referencia"} <= set(r), nome
            assert f(con, "SP").get("erro"), nome   # outra UF: erro, como nas ferramentas atuais
    for nome, f in analises.SEM_CONEXAO.items():
        r = f()
        json.dumps(r)
        assert r["citar"].startswith("Fonte:"), nome


def test_ferramentas_do_chat_nao_mudaram():
    """As 6 consultas antigas do chat continuam as mesmas (desde a D-062 elas ficam em `PROPRIAS`, dentro das 5
    ferramentas da Etapa 5; as análises do painel ficam em src/painel/analises.py)."""
    from src.agent import ferramentas
    assert set(ferramentas.PROPRIAS) == {"contar_serventias", "passivo_e_obrigadas", "deficit_e_mercado", "simular",
                                         "buscar_norma", "consultar_serventia"}
    assert set(ferramentas.PROPRIAS) <= ferramentas.alcancaveis()


# ------------------------------------------------------------------ Início: 10 números e D-042
def test_inicio_mostra_os_10_numeros_do_estado_atual(painel_demo):
    """Desde a D-051, os 10 números ficam na tabela de "Sobre os dados" (o nome do teste ficou o mesmo)."""
    from src.painel import analises
    esperado = numeros_do_estado_atual()
    at = rodar(SOBRE)
    tela = html(at)
    with con_demo(painel_demo) as con:
        oficiais = analises.numeros_oficiais(con)["numeros"]
    for n, ref in zip(oficiais, esperado):
        assert f'<td class="rd-num">{n["valor"]}</td>' in tela, n   # o valor está na tela, na tabela
        # e bate com o ESTADO_ATUAL na precisão em que ele está escrito (ex.: "R$ 4,76 mi" = ± R$ 5 mil)
        miolo = ref.replace("R$", "").replace("≈", "").split()[0]
        casas = len(miolo.split(",")[1]) if "," in miolo else 0
        escala = {"mil": 1e3, "mi": 1e6, "bi": 1e9}.get(ref.split()[-1], 1)
        assert abs(n["base_cru"] - valor(ref)) <= 0.5 * escala / 10 ** casas + 1e-6, (n["rotulo"], ref, n["base_cru"])


@pytest.mark.parametrize("medida", ["deficit", "importancia_segurada", "premio"])
def test_d042_bate_com_as_tabelas_e_segue_a_ordem(painel_demo, medida):
    from comum import brl
    from src.painel import analises
    with con_demo(painel_demo) as con:
        mc = con.execute("SELECT * FROM gold.analise_monte_carlo WHERE variante = 'independentes' AND medida = ?",
                         [medida]).df().iloc[0]
        col = analises.MEDIDAS_D042[medida][0]
        f = con.execute(f"SELECT nivel, {col} FROM gold.fato_mercado_uf WHERE regra_classe = 'v2' "
                        "AND cenario_stf = 'mantem'").df().set_index("nivel")[col]
        r = analises.faixa_d042(con, "MG", medida)
    v = r["valores"]
    assert (v["p05"], v["p95"], v["p50"]) == (mc["p05"], mc["p95"], mc["p50"])
    assert (v["base"], v["extremo_min"], v["extremo_max"]) == (f["base"], f["min"], f["max"])
    assert v["base_mc"] == pytest.approx(v["base"])   # o Monte Carlo parte da mesma base
    assert r["valor_base"] == brl(f["base"]) and r["extremos"] == f"{brl(f['min'])} a {brl(f['max'])}"
    assert r["rotulo_faixa"] == "faixa provável (P5–P95)" and r["subrotulo_faixa"] == "faixa dentro das suposições"
    # D-042 na tela (D-051): na tabela de "Sobre os dados", o valor base vem antes dos extremos; no Início, o prêmio
    # base vem antes da faixa provável, e os extremos não aparecem
    tela = html(rodar(SOBRE))
    linha = tela[tela.index(f'<td class="rd-num">{r["valor_base"]}</td>'):]
    assert linha.index(r["valor_base"]) < linha.index(r["extremos"])
    if medida == "premio":
        inicio = html(rodar(INICIO))
        valor, unidade = r["valor_base"].rsplit(" ", 1)
        i_base = inicio.index(f'<div class="rd-num">{valor} <small>{unidade}')
        assert i_base < inicio.index(r["faixa_provavel"]) and r["extremos"] not in inicio


def test_sensibilidades_da_d042_batem_com_a_tabela(painel_demo):
    from src.painel import analises
    with con_demo(painel_demo) as con:
        s = con.execute("SELECT * FROM gold.analise_sensibilidade_metodo").df().set_index("chave")
        met = analises.escolhas_metodo_passivo(con, "MG")
        lit = analises.leitura_literal_receita(con, "MG")
    assert {r["chave"]: r["efeito_passivo"] for r in met["tabela"]} == \
        s.loc[s["bloco"] == "passivo: escolhas de método", "var_passivo_todas"].to_dict()
    assert lit["valores"]["var_universo"] == s.at["receita_liquida", "var_n_universo"]
    # desde a D-051 as sensibilidades de método saíram do painel: ficam no chat
    from src.agent import ferramentas
    assert {"escolhas_metodo_passivo", "leitura_literal_receita"} <= ferramentas.alcancaveis()


# ------------------------------------------------------------------ projeção, 05b e limite
def test_05b_vem_do_notebook_e_aparece_como_faixa_de_comparacao(painel_demo):
    from src.painel import analises, artefatos
    cfg = analises.config()["artefatos"]["subidas_05b"]
    t = artefatos.tabela_do_notebook(cfg["notebook"], cfg["marcador"])
    t = t[(t["ano"] == "2026") & (t["recorte"] == "todas")]
    esperados = sorted(artefatos.numero_br(x) for x in t["esperado"])
    with con_demo(painel_demo) as con:
        r = analises.subidas_comparacao(con, "MG")
    assert r["valores"]["05b_faixa"] == esperados and r["rotulo"] == "projeção"
    # nenhum dos dois valores digitado no código do painel
    for arq in [*(RAIZ / "app").rglob("*.py"), *(RAIZ / "src" / "painel").glob("*.py")]:
        for x in esperados:
            assert not re.search(rf"(?<![\d.,]){round(x)}(?![\d.,])", arq.read_text(encoding="utf-8")), (arq, x)


def test_analises_rotula_projecao_e_a_leitura_do_limite(painel_demo):
    """D-051: a projeção fica em "Para onde vai", com o selo nos cartões, "PROJEÇÃO" no título do gráfico e
    "projeção, não número oficial" na fonte; a leitura do limite é a principal do config (a outra fica no chat)."""
    from src.painel import analises
    at = rodar(PROJECAO)
    tela = html(at)
    assert tela.count('class="rd-selo projecao"') >= 2
    figs = [json.loads(g.proto.spec) for g in at.get("plotly_chart")]
    # o título vem sem <b>: o peso 600 da Newsreader está no template (D-052)
    assert len(figs) == 1 and figs[0]["layout"]["title"]["text"].startswith("PROJEÇÃO")
    assert any("projeção, não número oficial" in a["text"] for a in figs[0]["layout"]["annotations"])
    with con_demo(painel_demo) as con:
        pm = analises.previsao_mercado(con, "MG", ano=2027)
    assert pm["leitura_do_limite"] == analises.config()["projecao"]["leitura_limite_principal"]
    assert pm["principal"]["Obrigadas"].split(" (")[0] in tela


def test_adi_8015_com_data_da_conferencia():
    """A situação da ADI 8015 continua no chat, com a data; o STF saiu do painel inteiro (D-051)."""
    from src.agent import ferramentas
    from src.painel import analises
    adi = analises.situacao_adi()
    assert adi["conferido_em"] and {"situacao_adi", "premio_por_cenario_stf"} <= ferramentas.alcancaveis()
    from apoio_painel import HISTORIA
    for pagina in HISTORIA:
        at = rodar(pagina)
        textos = html(at) + "\n".join(c.value for c in at.caption) + "".join(g.proto.spec for g in at.get("plotly_chart"))
        assert not re.search(r"\bSTF\b|ADI 8015", textos), pagina


# ------------------------------------------------------------------ dados pessoais
def test_sem_dado_pessoal_nos_dados_de_demonstracao_e_nos_downloads(painel_demo):
    """Nenhuma coluna de pessoa e nenhum padrão de CPF no conjunto público nem nas tabelas que o painel baixa."""
    from src import publico
    from src.painel import analises
    proibidas = re.compile(r"nome|cpf|responsavel|titular|substitut|email", re.I)
    # nomes que não são de pessoa: tipo de cartório (k-means), área do mapa e município do IBGE
    permitidas = {"nome_grupo", "area_nome", "silver.municipio_ibge:nome", "silver.municipio_ibge:nome_norm",
                  "silver.municipio_ibge:nome_regiao_corrigido_por"}
    for arq in sorted(publico.PASTA.glob("*.parquet")):
        df = pd.read_parquet(arq)
        ruins = [c for c in df.columns if proibidas.search(c) and c not in permitidas
                 and f"{arq.stem}:{c}" not in permitidas]
        assert not ruins, (arq.name, ruins)
        for c in df.select_dtypes(include=["object", "str"]):
            assert not df[c].astype(str).str.contains(CPF).any(), (arq.name, c)
    def textos(x):   # só os textos (os números crus do JSON não são CPF)
        if isinstance(x, dict):
            return [t for v in x.values() for t in textos(v)]
        if isinstance(x, list):
            return [t for v in x for t in textos(v)]
        return [x] if isinstance(x, str) else []
    with con_demo(painel_demo) as con:
        for nome, f in analises.PARA_O_CHAT.items():
            assert not [t for t in textos(f(con, "MG")) if CPF.search(t)], nome
