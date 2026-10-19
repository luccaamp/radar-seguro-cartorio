"""C5: toda fonte do silver tem URL, data e hora de coleta e data de referência do DADO (não do download).

Chama só os leitores do silver (não grava nada). Usa o bronze real; pulado se o bronze não estiver na máquina.
"""
import re

import pytest
import yaml

from src.transform import silver

ESC = yaml.safe_load((silver.CONFIG / "escopo.yaml").read_text(encoding="utf-8"))
SNAP = ESC["snapshots"]
pytestmark = pytest.mark.skipif(not (silver.BRONZE / "cnj_justica_aberta" / SNAP["cnj_justica_aberta"]).exists(),
                                reason="bronze ausente")


@pytest.fixture(scope="module")
def fontes():
    f: list = []
    mun = silver.ler_municipios(SNAP["ibge"], "MG", f)
    silver.ler_indices(SNAP["ibge"], f)
    silver.ler_serventias(SNAP["cnj_justica_aberta"], "MG", mun, f)
    silver.ler_colaboradores(SNAP["cnj_justica_aberta"], "MG", f)
    silver.ler_susep(SNAP["susep_ses"], f)
    return {x["fonte"]: x for x in f}


@pytest.mark.parametrize("fonte", ["cnj_colaboradores", "susep_ses_garantia", "cnj_serventias", "ibge_malha",
                                   "ibge_municipios", "ibge_inpc"])
def test_url_e_hora_de_coleta(fontes, fonte):
    x = fontes[fonte]
    assert x["url"] and x["url"].startswith("http")
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", x["coletado_em"] or ""), x["coletado_em"]


def test_ibge_com_versao_do_dado(fontes):
    assert fontes["ibge_malha"]["data_referencia"] == ESC["versoes_dado"]["ibge_malha"]
    assert fontes["ibge_malha"]["data_referencia"] != SNAP["ibge"]   # não é a data do download
    assert "vigente" in fontes["ibge_municipios"]["data_referencia"]
