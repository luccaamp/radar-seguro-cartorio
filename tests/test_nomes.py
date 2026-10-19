"""C4: nenhum nome público de região difere do nome de um município do IBGE só por acento.

Lê o bronze pelo leitor do silver (sem gravar nada); pulado se o bronze não estiver na máquina.
"""
import unicodedata

import pytest
import yaml

from src.transform import silver

ESC = yaml.safe_load((silver.CONFIG / "escopo.yaml").read_text(encoding="utf-8"))
# dados_reais: lê o bronze do IBGE; fora da suíte padrão
pytestmark = [pytest.mark.dados_reais,
              pytest.mark.skipif(not (silver.BRONZE / "ibge" / ESC["snapshots"]["ibge"]).exists(), reason="bronze ausente")]


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def test_regioes_sem_diferenca_so_de_acento():
    mun = silver.ler_municipios(ESC["snapshots"]["ibge"], "MG", [])
    por_chave = {_sem_acento(n): n for n in mun["nome"]}
    ruins = []
    for coluna in ("regiao_imediata", "regiao_intermediaria"):
        for regiao in mun[coluna].unique():
            for parte in regiao.split(" - "):   # nomes compostos, ex.: "Santa Bárbara - Ouro Preto"
                certo = por_chave.get(_sem_acento(parte))
                if certo and certo != parte:
                    ruins.append((coluna, parte, certo))
    assert not ruins, ruins


def test_correcao_de_juiz_de_fora_marcada():
    mun = silver.ler_municipios(ESC["snapshots"]["ibge"], "MG", [])
    jf = mun[mun["nome"] == "Juiz de Fora"].iloc[0]
    assert jf["regiao_intermediaria"] == "Juiz de Fora"
    assert "correcoes_nomes.yaml" in jf["nome_regiao_corrigido_por"]
    assert mun["nome_regiao_corrigido_por"].notna().sum() == (mun["regiao_intermediaria"] == "Juiz de Fora").sum()
