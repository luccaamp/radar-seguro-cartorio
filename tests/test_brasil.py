"""Visão do Brasil, camada 1 (D-087): montagem, contrato, pipeline, leitor do painel e a pasta publicada.

Os dados dos testes de unidade são SINTÉTICOS (inventados, só para os testes). O teste da pasta publicada lê
data/brasil/ (a cópia versionada) ou, com RADAR_BRASIL_TESTE, a pasta que o workflow acabou de gerar: o mesmo teste
que bloqueia a publicação no pipeline agendado.
"""
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
import yaml

from src.ingest.cnj_serventias import integridade
from src.painel import brasil as painel_brasil
from src.transform import brasil

RAIZ = Path(__file__).resolve().parents[1]
PUBLICADA = Path(os.environ.get("RADAR_BRASIL_TESTE") or RAIZ / "data" / "brasil")


# ------------------------------------------------------------------ dados SINTÉTICOS
def _serv(cns, uf, cidade, status="Ativo", sit="PROVIDO", tipo="PRIVATIZADO", nat="Notas | Registro de Imóveis"):
    return {"cns": cns, "uf": uf, "cidade": cidade, "status": status, "tipo_cartorio": tipo,
            "situacao_juridica_cartorio": {"descricao": sit, "data_decisao": "2020-01-01"}, "natureza": nat,
            "responsavel": {"nome": "Pessoa Sintética"}, "telefone": "0000"}


ESTADOS = [{"id": 98, "sigla": "XA", "nome": "Estado A (sintético)", "regiao": {"nome": "Teste"}},
           {"id": 99, "sigla": "XB", "nome": "Estado B (sintético)", "regiao": {"nome": "Teste"}}]
MUNICIPIOS = [{"id": 9800001, "nome": "Vila Um", "microrregiao": {"mesorregiao": {"UF": {"sigla": "XA"}}}},
              {"id": 9800002, "nome": "Pingo-d'Água", "microrregiao": {"mesorregiao": {"UF": {"sigla": "XA"}}}},
              {"id": 9800003, "nome": "Sem Cartório", "microrregiao": None,
               "regiao-imediata": {"regiao-intermediaria": {"UF": {"sigla": "XA"}}}},
              {"id": 9900001, "nome": "Capital B", "microrregiao": {"mesorregiao": {"UF": {"sigla": "XB"}}}}]
POPULACAO = [{"D1C": "Unidade da Federação (Código)", "V": "Valor"},
             {"D1C": "98", "V": "200000", "D3N": "2026"}, {"D1C": "99", "V": "50000", "D3N": "2026"}]
CADASTRO = {
    "XA": [_serv("1", "XA", "Vila Um"), _serv("2", "XA", "Pingo d Agua", sit="VAGO"),
           _serv("3", "XA", "Vila Um", tipo="OFICIALIZADO", nat="Protesto de Títulos"),
           _serv("4", "XA", "Vila Um", status="Inativo"), _serv("5", "XA", "Vila Velha Errada")],
    "XB": [_serv("6", "XB", "Região Administrativa Qualquer", sit="VAGO - SUB JUDICE")],   # UF de um município só
}


def _linhas(apelidos=None):
    return {x["uf"]: x for x in brasil.montar(CADASTRO, ESTADOS, MUNICIPIOS, POPULACAO, apelidos)}


def test_montar_conta_por_uf_sem_campo_pessoal():
    a, b = _linhas().values()
    assert (a["serventias_ativas"], a["serventias_inativas"], a["vagas"], a["oficializadas"]) == (4, 1, 1, 1)
    assert a["pct_vagas"] == 0.25 and a["municipios"] == 3 and a["municipios_com_cartorio"] == 2
    assert a["cidades_sem_codigo"] == 1 and a["por_100mil_hab"] == 2.0 and a["notas"] == 3 and a["protesto"] == 1
    # UF com um município só: a "cidade" do cadastro (região administrativa) é esse município; VAGO - SUB JUDICE é vaga
    assert (b["municipios_com_cartorio"], b["cidades_sem_codigo"], b["vagas"]) == (1, 0, 1)
    assert set(a) == set(brasil.COLUNAS)
    assert "Pessoa Sintética" not in json.dumps(list(_linhas().values()), ensure_ascii=False)


def test_apelidos_e_atribuicao_nova():
    a = _linhas({"XA": {"VILA VELHA ERRADA": 9800003}})["XA"]
    assert (a["municipios_com_cartorio"], a["cidades_sem_codigo"]) == (3, 0)
    estranho = {"XA": [_serv("9", "XA", "Vila Um", nat="Registro de Coisas Novas")]}
    with pytest.raises(ValueError, match="atribuição nova"):
        brasil.montar(estranho, ESTADOS[:1], MUNICIPIOS, POPULACAO)


def test_contrato_pega_uf_faltando_cidades_sem_codigo_e_coluna_a_mais():
    linhas = list(_linhas().values())
    erros = brasil.conferir(linhas, CADASTRO, limite_sem_codigo=0.05)
    assert any("27 UFs" in e for e in erros) and any("XA" in e and "sem código" in e for e in erros)
    linhas[0]["responsavel"] = "x"
    assert any("colunas fora do contrato" in e for e in brasil.conferir(linhas, CADASTRO, 1.0))


def test_integridade_da_coleta_com_tolerancia():
    assert integridade(3, ["1", "2", "3"]) == 0
    assert integridade(1680, [str(i) for i in range(1679)], tolerancia=2) == 1   # o caso de SP
    assert integridade(1680, [str(i) for i in range(1679)]) is None              # sem tolerância, falha
    assert integridade(3, ["1", "1", "2"], tolerancia=5) is None                 # CNS repetido nunca passa
    assert integridade(2, ["1", "2", "3"], tolerancia=5) is None                 # a mais também não


def _script():
    spec = importlib.util.spec_from_file_location("pipeline_brasil", RAIZ / "scripts" / "pipeline_brasil.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _bronze_sintetico(tmp_path: Path, cadastro=CADASTRO) -> tuple[Path, Path]:
    cnj, ibge = tmp_path / "cnj", tmp_path / "ibge"
    cnj.mkdir(parents=True)
    ibge.mkdir(parents=True)
    for uf, itens in cadastro.items():
        (cnj / f"serventias_{uf}.json").write_text(json.dumps({"meta": {"total": len(itens)}, "data": itens}),
                                                   encoding="utf-8")
    quadrado = lambda x: {"type": "Polygon", "coordinates": [[[x, 0], [x + 1, 0], [x + 1, 1], [x, 1], [x, 0]]]}  # noqa
    geo = {"features": [{"properties": {"codarea": str(e["id"])}, "geometry": quadrado(i)}
                        for i, e in enumerate(ESTADOS)]}
    for nome, d in (("brasil_estados.json", ESTADOS), ("brasil_municipios.json", MUNICIPIOS),
                    ("brasil_populacao.json", POPULACAO), ("brasil_malha_uf.geojson", geo)):
        (ibge / nome).write_text(json.dumps(d), encoding="utf-8")
    return cnj, ibge


def test_pipeline_bloqueia_com_problema_e_compara_com_a_anterior(tmp_path, monkeypatch):
    """Com o contrato quebrado (só 2 UFs), nada é gravado. Com o contrato de 27 UFs trocado por 2 (sintético), grava os
    arquivos, o manifesto confere e o "o que mudou" compara com a publicação anterior; um salto maior que o limite
    bloqueia."""
    p = _script()
    cnj, ibge = _bronze_sintetico(tmp_path)
    c = {**p.config(), "limite_cidades_sem_codigo": 1.0}
    saida = tmp_path / "saida"
    assert any("27 UFs" in e for e in p.main(cnj, ibge, saida, None, c)) and not saida.exists()

    monkeypatch.setattr(p.brasil, "conferir", lambda linhas, cad, lim: [])
    assert p.main(cnj, ibge, saida, None, c) == []
    manifesto = json.loads((saida / "manifesto.json").read_text(encoding="utf-8"))
    for a in manifesto["arquivos"]:
        assert hashlib.sha256((saida / a["arquivo"]).read_bytes()).hexdigest() == a["sha256"]
    assert manifesto["totais"]["serventias_ativas"] == 5
    assert "Primeira publicação" in (saida / "o_que_mudou.md").read_text(encoding="utf-8")

    mais = {**CADASTRO, "XB": CADASTRO["XB"] + [_serv("7", "XB", "Capital B")]}
    cnj2, _ = _bronze_sintetico(tmp_path / "2", mais)
    saida2 = tmp_path / "saida2"
    assert any("variaram" in e for e in p.main(cnj2, ibge, saida2, saida, c))   # 5 → 6: +20%, limite 5%
    assert p.main(cnj2, ibge, saida2, saida, {**c, "variacao_maxima_ativas": 0.5}) == []
    texto = (saida2 / "o_que_mudou.md").read_text(encoding="utf-8")
    assert "diferença: +1" in texto and "| XB | serventias_ativas | 1 | 2 |" in texto
    assert "CNJ, Justiça Aberta" in texto   # a vírgula do texto fica (só o número ganha ponto de milhar)


def test_simular_falha_sai_com_codigo_1_e_nao_grava(tmp_path):
    r = subprocess.run([sys.executable, str(RAIZ / "scripts" / "pipeline_brasil.py"), "--cnj", str(tmp_path),
                        "--ibge", str(tmp_path), "--saida", str(tmp_path / "saida"), "--simular-falha"],
                       capture_output=True, text=True, encoding="utf-8", cwd=RAIZ)
    assert r.returncode == 1 and "NÃO publicar" in r.stdout and not (tmp_path / "saida").exists()


def test_ibge_fora_do_ar_usa_a_referencia_versionada(tmp_path, monkeypatch):
    """2026-11-11: o IBGE não aceitou conexão do GitHub Actions e a primeira execução caiu. Agora a coleta segue com a
    referência versionada (data/brasil/ibge), e o manifesto diz isso; o CNJ continua obrigatório."""
    p = _script()
    uf_coletadas = []
    monkeypatch.setattr("src.ingest.cnj_serventias.coletar", lambda uf, pasta, tolerancia: uf_coletadas.append(uf))

    def ibge_fora(pasta):
        raise httpx.ConnectTimeout("[Errno 110] Connection timed out")
    cnj, pasta_ibge = p.coletar(tmp_path, p.config(), coletar_ibge=ibge_fora)
    assert pasta_ibge == p.REFERENCIA_IBGE and len(uf_coletadas) == 27
    referencia = p._ler_ibge(p.REFERENCIA_IBGE)
    assert len(referencia["brasil_estados.json"]) == 27 and len(referencia["brasil_malha_uf.geojson"]["features"]) == 27
    assert len(referencia["brasil_municipios.json"]) > 5500 and set(referencia["brasil_municipios.json"][0]) == {
        "id", "nome", "uf"}
    # a referência dá a mesma tabela que a coleta completa do IBGE (a cópia publicada foi montada com ela)
    manifesto = json.loads((PUBLICADA / "manifesto.json").read_text(encoding="utf-8"))
    assert "origem" in manifesto["fontes"]["ibge"]


def test_pedido_tenta_de_novo_em_erro_de_rede():
    from src.ingest.comum import pedir
    respostas = [httpx.ConnectTimeout("timeout"), httpx.Response(503), httpx.Response(200, text="ok")]

    def transporte(req):
        r = respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r
    esperas = []
    with httpx.Client(transport=httpx.MockTransport(transporte)) as c:
        assert pedir(c, "GET", "https://exemplo.test/", dormir=esperas.append).text == "ok"
    assert esperas == [10, 20]
    respostas[:] = [httpx.ConnectTimeout("x")] * 3
    with httpx.Client(transport=httpx.MockTransport(transporte)) as c, pytest.raises(httpx.ConnectTimeout):
        pedir(c, "GET", "https://exemplo.test/", dormir=esperas.append)


# ------------------------------------------------------------------ a pasta publicada (data/brasil ou a do workflow)
def test_pasta_publicada_confere():
    p = painel_brasil.local(PUBLICADA)   # confere os SHA-256 do manifesto e as colunas
    assert len(p.linhas) == 27 and len({x["uf"] for x in p.linhas}) == 27
    assert sum(x["serventias_ativas"] for x in p.linhas) == p.manifesto["totais"]["serventias_ativas"]
    assert set(painel_brasil.geometrias(p)) == {x["uf"] for x in p.linhas}
    for x in p.linhas:
        assert 0 <= x["pct_vagas"] <= 1 and 0 < x["pct_municipios_com_cartorio"] <= 1 and x["populacao"] > 0
        assert x["municipios_com_cartorio"] <= x["municipios"]
    mg = next(x for x in p.linhas if x["uf"] == "MG")
    assert mg["serventias_ativas"] > 0 and mg["municipios"] == 853
    texto = "".join((PUBLICADA / a).read_text(encoding="utf-8") for a in painel_brasil.ARQUIVOS)
    assert not re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", texto)   # nenhum CPF


# ------------------------------------------------------------------ leitor do painel
def _transporte(release_ok=True, corromper=False):
    pasta = PUBLICADA
    arquivos = {a: (pasta / a).read_bytes() for a in painel_brasil.ARQUIVOS}
    if corromper:
        arquivos["brasil_uf.csv"] = arquivos["brasil_uf.csv"].replace(b"MG", b"XX", 1)

    def responder(req: httpx.Request) -> httpx.Response:
        if req.url.path.endswith("/releases"):
            if not release_ok:
                return httpx.Response(403, json={"message": "API rate limit exceeded"})
            assets = [{"name": a, "browser_download_url": f"https://exemplo.test/{a}"} for a in arquivos]
            return httpx.Response(200, json=[{"tag_name": "outra-coisa", "assets": []},
                                             {"tag_name": "brasil-2099-01-01", "assets": assets}])
        return httpx.Response(200, content=arquivos[req.url.path.strip("/")])
    return httpx.Client(transport=httpx.MockTransport(responder))


def test_painel_le_a_release_e_volta_para_a_copia_local():
    p = painel_brasil.publicacao(_transporte())
    assert p.origem == "Release brasil-2099-01-01" and not p.avisos
    sem = painel_brasil.publicacao(_transporte(release_ok=False))
    assert sem.origem.startswith("cópia do repositório") and "HTTPStatusError" in sem.avisos[0]
    ruim = painel_brasil.publicacao(_transporte(corromper=True))   # hash não confere: nunca mostra
    assert ruim.origem.startswith("cópia do repositório") and "ValueError" in ruim.avisos[0]


def test_preposicao_de_cada_estado():
    p = painel_brasil.local(PUBLICADA)
    assert set(painel_brasil.PREPOSICAO) == {x["uf"] for x in p.linhas}
    assert painel_brasil.do_estado("BA", "Bahia") == "da Bahia"
    assert painel_brasil.do_estado("RJ", "Rio de Janeiro") == "do Rio de Janeiro"
    assert painel_brasil.do_estado("MG", "Minas Gerais") == "de Minas Gerais"


def test_totais_do_brasil_sao_razoes_das_somas():
    t = painel_brasil.totais(painel_brasil.local(PUBLICADA))
    assert t["pct_vagas"] == pytest.approx(t["vagas"] / t["serventias_ativas"])
    assert 0 < t["pct_municipios_com_cartorio"] <= 1 and t["por_100mil_hab"] > 0


# ------------------------------------------------------------------ a página do painel
def test_pagina_brasil_roda_sem_internet(monkeypatch):
    """A página com a cópia local (RADAR_BRASIL_RELEASE=0: a suíte não usa a internet): 4 indicadores, o mapa com as
    27 UFs, a origem no selo e o quadro do estado escolhido, com a preposição certa."""
    from streamlit.testing.v1 import AppTest
    sys.path.insert(0, str(RAIZ / "app"))
    from apoio_painel import mapa_componente
    monkeypatch.setenv("RADAR_BRASIL_RELEASE", "0")
    at = AppTest.from_file(str(RAIZ / "app" / "paginas" / "7_Brasil.py"), default_timeout=60).run()
    assert not at.exception
    html = " ".join(m.value for m in at.markdown)
    assert html.count('class="rd-card"') == 4 and "cópia do repositório" in html and "Atualizado em" in html
    assert len(mapa_componente(at)["areas"]) == 27
    at.session_state["f_uf"] = "BA"
    at.run()
    assert not at.exception and any(h.value == "Os cartórios da Bahia" for h in at.header)


# ------------------------------------------------------------------ workflow
def test_workflow_so_publica_depois_do_contrato_e_dos_testes():
    fluxo = yaml.safe_load((RAIZ / ".github" / "workflows" / "pipeline-brasil.yml").read_text(encoding="utf-8"))
    gatilhos = fluxo.get("on") or fluxo.get(True)   # o YAML 1.1 lê "on" como True
    assert "schedule" in gatilhos and "simular_falha" in gatilhos["workflow_dispatch"]["inputs"]
    assert fluxo["permissions"] == {"contents": "write", "issues": "write"}
    nomes = [p.get("name", "") for p in fluxo["jobs"]["brasil"]["steps"]]
    i_pipe, i_test, i_pub = (next(i for i, n in enumerate(nomes) if n.startswith(t))
                             for t in ("Coleta e montagem", "Testes da pasta", "Publicar"))
    assert i_pipe < i_test < i_pub   # publicar é o último passo normal: qualquer falha antes impede
    passos = fluxo["jobs"]["brasil"]["steps"]
    assert passos[i_pub]["if"] == "github.ref == 'refs/heads/main'"   # numa branch, ensaio sem Release
    assert "--latest=false" in passos[i_pub]["run"]   # a publicação mensal não vira a Release principal
    falha = passos[-1]
    assert falha["if"] == "failure()" and "gh issue create" in falha["run"]
    assert "--simular-falha" in fluxo["jobs"]["brasil"]["steps"][i_pipe]["run"]
