"""Configuração por estado (Fase 3, bloco 1, D-081): config/estados.yaml e o leitor src/estados_config.py."""
import re
from pathlib import Path

import pytest

from src import estados_config
from src.ingest import ibge

RAIZ = Path(__file__).resolve().parents[1]
CAMPOS = {"nome", "cod_ibge", "fonte_cod_ibge", "pacote_rais", "fonte_pacote_rais", "apelidos_municipios",
          "normas_locais", "controle_arrecadacao", "premissas"}


def test_toda_uf_do_escopo_tem_entrada_completa():
    for uf in estados_config.ufs():
        e = estados_config.estado(uf)
        assert CAMPOS <= set(e), f"{uf}: faltam {CAMPOS - set(e)}"
        assert 11 <= int(e["cod_ibge"]) <= 53   # códigos de UF do IBGE
        assert e["fonte_cod_ibge"] and e["fonte_pacote_rais"]


def test_valores_de_mg_iguais_aos_de_antes():
    """Os valores que estavam no código e em outros YAMLs (Fase 2) chegam iguais pelo estados.yaml."""
    assert estados_config.uf_padrao() == "MG"
    assert estados_config.cod_ibge("MG") == 31
    assert estados_config.pacote_rais("MG") == "RAIS_VINC_PUB_MG_ES_RJ.7z"
    assert estados_config.apelidos_municipios("MG") == {"BRASOPOLIS": 3108909, "AMPARO DA SERRA": 3102506}
    ctl = estados_config.controle_arrecadacao("MG")
    assert ctl["silver"]["totais"] == {"2025-1": 2379639987.32, "2025-2": 3133904766.00}
    assert ctl["bi"]["totais"] == {"2025-1": 2373919679.17, "2025-2": 3067663494.52}


def test_apelidos_apontam_para_municipios_da_propria_uf():
    for uf in estados_config.ufs():
        for nome, cod in estados_config.apelidos_municipios(uf).items():
            assert str(cod).startswith(str(estados_config.cod_ibge(uf))) and len(str(cod)) == 7, (uf, nome)


def test_uf_sem_entrada_da_erro_claro():
    with pytest.raises(KeyError, match="config/estados.yaml"):
        estados_config.estado("ZZ")


def test_coletor_do_ibge_usa_o_codigo_da_configuracao():
    u = ibge.urls("MG")
    assert u["municipios_MG.json"].endswith("/localidades/estados/31/municipios")
    assert "in%20n3%2031/" in u["populacao_MG.json"]


def test_nenhum_codigo_de_uf_fixo_nos_coletores():
    """Nada de dicionário {"MG": ...} nem padrão "MG" literal nos coletores: tudo vem de estados.yaml."""
    for arq in (RAIZ / "src" / "ingest").glob("*.py"):
        texto = arq.read_text(encoding="utf-8")
        assert not re.search(r"""["']MG["']""", texto), arq.name


def test_snapshots_por_uf_sobrepoem_so_a_uf_e_mg_continua_igual():
    """Um estado que entra depois tem as coletas dele em outra data (D-088): `snapshots_por_uf` muda só aquela UF; MG
    (sem entrada própria) lê as mesmas pastas de antes, e os colaboradores vêm da pasta do cadastro."""
    from src.transform.silver import snapshots_da_uf
    esc = {"snapshots": {"ibge": "2026-10-18", "cnj_justica_aberta": "2026-10-17", "cnj_arrecadacoes": "2026-10-18"},
           "snapshots_por_uf": {"SP": {"ibge": "2026-11-11", "cnj_arrecadacoes": "2026-11-11",
                                       "cnj_colaboradores": "2026-11-11"}}}
    mg, sp = snapshots_da_uf(esc, "MG"), snapshots_da_uf(esc, "SP")
    assert mg == {**esc["snapshots"], "cnj_colaboradores": "2026-10-17"}
    assert sp["ibge"] == sp["cnj_arrecadacoes"] == sp["cnj_colaboradores"] == "2026-11-11"
    assert sp["cnj_justica_aberta"] == "2026-10-17"   # o cadastro continua o mesmo de MG


def test_totais_do_bi_dos_estados_novos_tem_fonte():
    for uf in ("SP", "RJ", "ES"):
        e = estados_config.estado(uf)
        bi = e["controle_arrecadacao"]["bi"]
        assert bi["fonte"] and set(bi["totais"]) == {"2025-1", "2025-2"} and e["premissas"] == "herdada"
