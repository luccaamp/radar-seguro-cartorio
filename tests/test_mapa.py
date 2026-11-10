"""Mapa clicável (D-083, src/painel/mapa.py): projeção, cores, enquadramento, conferência do clique e os testes do
JavaScript (tests/js/mapa.test.mjs, com o `node --test` que já vem com o Node; pulados se o Node não estiver instalado).

Geometrias SINTÉTICAS (quadrados em graus), exceto o último teste, que usa o conjunto público versionado.
"""
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from src.painel import mapa as m

RAIZ = Path(__file__).resolve().parents[1]


def quadrado(lon: float, lat: float, lado: float = 1.0) -> dict:
    """Polygon sintético: quadrado com o canto sudoeste em (lon, lat)."""
    return {"type": "Polygon", "coordinates": [[[lon, lat], [lon + lado, lat], [lon + lado, lat + lado],
                                                [lon, lat + lado], [lon, lat]]]}


GEO = {"1": quadrado(-45, -20), "2": quadrado(-44, -20), "3": quadrado(-45, -19), "4": quadrado(-44, -19)}


# ------------------------------------------------------------------ projeção
def test_projecao_ocupa_a_largura_e_o_norte_fica_em_cima():
    p = m.Projecao(GEO.values())
    assert p.largura == m.LARGURA
    assert p.xy(-45, -18) == (0.0, 0.0)                       # canto noroeste na origem
    x, y = p.xy(-43, -20)
    assert x == pytest.approx(m.LARGURA) and y == pytest.approx(p.altura)
    assert p.xy(-44, -18.5)[1] < p.xy(-44, -19.5)[1]          # mais ao norte, menor y


def test_projecao_encolhe_a_longitude_pelo_cosseno():
    """2° × 2° perto de 19° S: a largura em graus vale cos(19°) da altura, então a altura passa da largura."""
    p = m.Projecao(GEO.values())
    assert p.altura / p.largura == pytest.approx(1 / math.cos(math.radians(19)), rel=0.01)


def test_caminho_fecha_cada_anel_e_inclui_os_furos():
    p = m.Projecao(GEO.values())
    d = p.caminho(GEO["1"])
    assert d.startswith("M") and d.endswith("Z") and d.count("M") == 1
    com_furo = {"type": "Polygon", "coordinates": GEO["1"]["coordinates"] + [
        [[-44.8, -19.8], [-44.2, -19.8], [-44.2, -19.2], [-44.8, -19.2], [-44.8, -19.8]]]}
    assert p.caminho(com_furo).count("M") == 2
    multi = {"type": "MultiPolygon", "coordinates": [GEO["1"]["coordinates"], GEO["4"]["coordinates"]]}
    assert p.caminho(multi).count("M") == 2


def test_caminho_sem_pontos_repetidos_e_sem_anel_degenerado():
    p = m.Projecao(GEO.values())
    # um anel minúsculo vira um ponto depois do arredondamento: some
    minusculo = {"type": "Polygon", "coordinates": [[[-44.5, -19.5], [-44.50001, -19.5], [-44.5, -19.50001],
                                                     [-44.5, -19.5]]]}
    assert p.caminho(minusculo) == ""
    pares = re.findall(r"[ML]([\d.]+) ([\d.]+)", p.caminho(GEO["2"]))
    assert len(pares) == len(set(pares)) == 4                 # 4 cantos, o fechamento é o "Z"


def test_geometria_sem_suporte_avisa():
    with pytest.raises(ValueError, match="sem suporte"):
        m.Projecao([{"type": "Point", "coordinates": [-44, -19]}])
    with pytest.raises(ValueError, match="sem geometrias"):
        m.Projecao([])


def test_caixa_enquadra_com_folga_sem_sair_do_estado():
    p = m.Projecao(GEO.values())
    x, y, w, h = p.caixa([GEO["4"]])                          # o quadrado do sudeste
    assert 0 <= x and 0 <= y and x + w <= p.largura + 0.1 and y + h <= p.altura + 0.1
    assert w < p.largura and h < p.altura
    assert x < p.largura / 2 + 0.1 and x > p.largura / 2 - m.FOLGA * p.altura - 0.1   # folga só para fora
    assert p.caixa([]) == (0.0, 0.0, p.largura, p.altura)


# ------------------------------------------------------------------ cores
def test_faixas_zero_neutro_sem_valor_e_teto_no_quantil():
    valores = {"z": 0.0, "n": None, "nan": float("nan"), **{str(i): float(i) for i in range(1, 101)}}
    cor, legenda = m.faixas(valores)
    assert cor["z"] == "zero" and cor["n"] == "sem" and cor["nan"] == "sem"
    teto = m._quantil(sorted(float(i) for i in range(1, 101)), m.QUANTIL_TETO)
    assert teto == pytest.approx(95.05)                       # o mesmo quantil do pandas
    # passo redondo que cobre o teto em n − 1 faixas: 95,05 / 5 = 19,01 → 20
    assert cor["1"] == "1" and cor["20"] == "1" and cor["21"] == "2" and cor["100"] == "5"
    # faixas crescem com o valor (monótono) e só a última fica para o que passa de (n − 1) passos
    seq = [int(cor[str(i)]) for i in range(1, 101)]
    assert seq == sorted(seq) and set(seq) == set(range(1, m.N_FAIXAS))
    assert m.faixas({"a": 10.0, "b": 1000.0, **{str(i): 50.0 for i in range(40)}})[0]["b"] == str(m.N_FAIXAS)
    assert legenda[0] == {"faixa": "zero", "texto": "Zero"} and len(legenda) == m.N_FAIXAS + 1
    assert [x["texto"] for x in legenda[1:3]] == ["até R$ 20,00", "até R$ 40,00"]
    assert legenda[-1]["texto"] == "mais de R$ 100,00"


@pytest.mark.parametrize("x, esperado", [(0.7, 0.8), (1, 1), (1.2, 1.5), (19.01, 20), (21, 25), (27, 30), (33, 40),
                                         (57_600, 60_000), (79_000, 80_000), (81_000, 100_000)])
def test_passo_redondo(x, esperado):
    assert m.passo_redondo(x) == pytest.approx(esperado)


def test_formatos_curtos_da_legenda():
    assert m.brl_curto(60_000) == "R$ 60 mil" and m.brl_curto(62_500) == "R$ 62,5 mil"
    assert m.brl_curto(1_000_000) == "R$ 1 mi"
    assert m.pct_curto(0.25) == "25%" and m.pct_curto(0.125) == "12,5%" and m.pct_curto(0) == "0%"
    cor, leg = m.faixas({"a": 0.1, "b": 0.5}, fmt=m.pct_curto)
    assert leg[1]["texto"].startswith("até ") and leg[1]["texto"].endswith("%")


def test_faixas_calculadas_no_recorte():
    """A escala sai só dos valores recebidos: o mesmo valor muda de cor conforme o recorte."""
    todos, _ = m.faixas({"a": 10.0, "b": 1000.0})
    recorte, _ = m.faixas({"a": 10.0, "c": 12.0})
    assert int(todos["a"]) < int(recorte["a"])


def test_faixas_sem_positivos_nao_quebra():
    cor, legenda = m.faixas({"a": 0.0, "b": None})
    assert cor == {"a": "zero", "b": "sem"} and legenda == [{"faixa": "zero", "texto": "Zero"}]
    cor, _ = m.faixas({"a": 5.0})                             # um só valor: cabe nas faixas de baixo, sem quebrar
    assert 1 <= int(cor["a"]) < m.N_FAIXAS


# ------------------------------------------------------------------ rótulos
def test_ponto_interno_fica_dentro_mesmo_em_forma_de_u():
    assert m.ponto_interno(GEO["1"]) == pytest.approx((-44.5, -19.5))   # quadrado: o centro
    # "U": o centroide cai no vão, fora do polígono; o ponto do rótulo tem de cair dentro
    u = {"type": "Polygon", "coordinates": [[[0, 0], [3, 0], [3, 3], [2, 3], [2, 1], [1, 1], [1, 3], [0, 3], [0, 0]]]}
    _, cx, cy = m._area_e_centro(u["coordinates"][0])
    assert not m._dentro(cx, cy, u["coordinates"])
    x, y = m.ponto_interno(u)
    assert m._dentro(x, y, u["coordinates"])
    # MultiPolygon: o rótulo vai no pedaço maior
    multi = {"type": "MultiPolygon", "coordinates": [quadrado(0, 0, 0.1)["coordinates"], quadrado(5, 5, 2)["coordinates"]]}
    assert m.ponto_interno(multi) == pytest.approx((6, 6))


def test_rotulos_nos_maiores_do_recorte():
    vals = {"1": 10.0, "2": 40.0, "3": 30.0, "4": 0.0}
    d = m.dados_mapa(GEO, vals, {"1": "Um", "2": "Dois", "3": "Três", "4": "Quatro"}, {})
    assert [r["texto"] for r in d["rotulos"]] == ["Dois", "Três", "Um"]     # candidatos em ordem; o zero fica fora
    assert all(set(r) == {"id", "texto", "x", "y"} for r in d["rotulos"]) and d["tamanhoRotulo"] > 0
    assert d["maxRotulos"] == m.N_ROTULOS
    n = m.N_CANDIDATOS + 5
    muitos = {str(i): quadrado(-50 + i * 0.5, -20) for i in range(n)}
    cand = m.dados_mapa(muitos, {str(i): float(i + 1) for i in range(n)}, {}, {})["rotulos"]
    assert [r["id"] for r in cand] == [str(i) for i in range(n - 1, n - 1 - m.N_CANDIDATOS, -1)]   # até N_CANDIDATOS
    recorte = m.dados_mapa(GEO, vals, {}, {}, enquadrar=["1", "4"])
    assert [r["id"] for r in recorte["rotulos"]] == ["1"]                    # só os do recorte, e só com valor
    assert recorte["maxRotulos"] == m.N_ROTULOS_RECORTE                      # numa região, mais nomes
    um = m.dados_mapa(GEO, vals, {}, {}, enquadrar=["1"])
    assert um["viewBoxInteiro"] == d["viewBox"] != um["viewBox"]             # o botão volta ao estado inteiro
    assert [r["texto"] for r in um["rotulosInteiro"]] == ["2", "3", "1"]     # e mostra os maiores do estado
    assert um["maxRotulosInteiro"] == m.N_ROTULOS and d["rotulosInteiro"] == []
    zoom = m.dados_mapa(GEO, vals, {}, {}, enquadrar=["1"])                  # ("1" e "4" em diagonal cobrem tudo)
    assert zoom["tamanhoRotulo"] < d["tamanhoRotulo"]                        # com zoom, a letra encolhe no viewBox
    assert m.dados_mapa(GEO, vals, {}, {}, rotulos=0)["rotulos"] == []


# ------------------------------------------------------------------ dados do componente e clique
def test_dados_mapa_e_json_e_tem_o_que_o_js_le():
    d = m.dados_mapa(GEO, {"1": 0.0, "2": 10.0, "3": 20.0, "4": None}, {"1": "Um"}, {"2": "texto"},
                     fundo=[quadrado(-45, -20, 0.2)], selecionado="2", titulo_legenda="Déficit", legenda_fundo="Sem")
    json.dumps(d, allow_nan=False)                            # JSON válido, sem NaN
    assert set(d) == {"viewBox", "viewBoxInteiro", "rotuloInteiro", "areas", "fundo", "selecionado", "legenda",
                      "tituloLegenda", "legendaFundo", "resumo", "rotulos", "maxRotulos", "rotulosInteiro",
                      "maxRotulosInteiro", "tamanhoRotulo"}
    areas = {a["id"]: a for a in d["areas"]}
    assert areas["1"]["nome"] == "Um" and areas["2"]["nome"] == "2"          # sem nome: o código
    assert areas["1"]["faixa"] == "zero" and areas["4"]["faixa"] == "sem" and areas["4"]["valor"] is None
    assert d["selecionado"] == "2" and len(d["fundo"]) == 1
    assert d["viewBox"].split()[:2] == ["0", "0"]


def test_dados_mapa_ignora_selecionado_e_enquadramento_fora_do_mapa():
    d = m.dados_mapa(GEO, {}, {}, {}, selecionado="999", enquadrar=["999"])
    assert d["selecionado"] is None and d["viewBox"].split()[:2] == ["0", "0"]
    zoom = m.dados_mapa(GEO, {}, {}, {}, enquadrar=["4"])
    assert float(zoom["viewBox"].split()[2]) < float(d["viewBox"].split()[2])


@pytest.mark.parametrize("valor, esperado", [
    ("1", "1"), (1, "1"), (1.0, "1"), ("999", None), (None, None), ("", None), (True, None), (["1"], None),
    ({"id": "1"}, None), ("1<script>", None)])
def test_clique_so_aceita_area_do_mapa(valor, esperado):
    assert m.clique_valido(valor, GEO) == esperado


# ------------------------------------------------------------------ arquivos do componente
def test_js_nao_monta_html_com_texto_dos_dados():
    js = re.sub(r"//[^\n]*", "", (m.PASTA / "mapa.js").read_text(encoding="utf-8"))   # sem os comentários
    assert "innerHTML" not in js and "outerHTML" not in js and "insertAdjacentHTML" not in js
    assert "eval(" not in js and "new Function" not in js
    assert "export default function" in js and 'setTriggerValue("municipio"' in js


def test_css_tem_uma_classe_por_faixa_e_tokens_nos_dois_temas():
    css = (m.PASTA / "mapa.css").read_text(encoding="utf-8")
    estilo = (RAIZ / "src" / "painel" / "estilo.css").read_text(encoding="utf-8")
    for f in ["zero", *map(str, range(1, m.N_FAIXAS + 1))]:
        assert f".rd-f-{f} " in css, f
        assert estilo.count(f"--mapa-{f}:") == 2, f           # claro e escuro (o botão de tema do painel decide)
    assert f".rd-f-{m.N_FAIXAS + 1} " not in css


# ------------------------------------------------------------------ JavaScript (node --test)
def test_javascript_do_mapa():
    if shutil.which("node") is None:
        if os.environ.get("CI"):   # no CI (GitHub Actions define CI=true) o Node é obrigatório: nada de pular calado
            pytest.fail("Node ausente no CI: os testes do JavaScript do mapa não rodaram")
        pytest.skip("Node ausente: os testes do JavaScript do mapa não rodam")
    arquivos = sorted(str(p) for p in (RAIZ / "tests" / "js").glob("*.test.mjs"))   # lista explícita (Node 20 e 22)
    assert arquivos
    # formato TAP sempre: sem a opção, o Node escolhe o formato pelo ambiente (no CI do GitHub sai o "spec", sem o
    # "# fail 0" que a linha de baixo procura; 2026-11-10, PR #12)
    r = subprocess.run(["node", "--test", "--test-reporter=tap", *arquivos], capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    assert re.search(r"# fail 0", r.stdout) and not re.search(r"# pass 0\b", r.stdout), r.stdout


# ------------------------------------------------------------------ com o conjunto público versionado
def test_mapa_de_mg_com_o_conjunto_publico():
    """As 851 áreas de MG viram caminhos válidos, o estado cabe no viewBox e os dados ficam leves para a página."""
    pd = pytest.importorskip("pandas")
    pub = RAIZ / "data" / "publico"
    geo = pd.read_parquet(pub / "gold.geo_mapa_publico.parquet")
    sem = pd.read_parquet(pub / "gold.geo_sem_serventia.parquet")
    areas = pd.read_parquet(pub / "gold.mercado_area_publico.parquet")
    d = m.dados_mapa({a: json.loads(g) for a, g in zip(geo["area_id"], geo["geometria"])},
                     dict(zip(areas["area_id"], areas["valor_descoberto"])), dict(zip(areas["area_id"], areas["area_nome"])),
                     {}, fundo=[json.loads(g) for g in sem["geometria"]])
    assert len(d["areas"]) == len(areas) and all(a["d"].startswith("M") for a in d["areas"])
    _, _, w, h = map(float, d["viewBox"].split())
    assert w == m.LARGURA and 0.5 < h / w < 1.5
    assert sum(a["faixa"] == "zero" for a in d["areas"]) == int((areas["valor_descoberto"] == 0).sum())
    assert len(json.dumps(d)) < 600_000                       # ≈ 0,3 MB hoje
