"""Área "Explorar" (D-077): tornado e faixa por sorteio ao redor dos valores escolhidos (src/painel/explorar.py).
Totais SINTÉTICOS; premissas da semente versionada."""
import time

import numpy as np
import pandas as pd
import pytest
import yaml

from src import estado
from src.analise import RAIZ, sensibilidade
from src.model.premissas import resolver
from src.model.simulador import resumo_por_totais
from src.painel import explorar

CENARIOS = yaml.safe_load((RAIZ / "config" / "cenarios_stf.yaml").read_text(encoding="utf-8"))
TOTAIS = {"passivo_ponderado_classe_2": 6.0e7, "passivo_ponderado_classe_3": 1.7e8,   # sintéticos
          "peso_com_passivo_classe_2": 700.0, "peso_com_passivo_classe_3": 350.0, "n_serventias_ativas": 10,
          "clt": 50.0, "passivo_todas": 3e8, "n_universo": 1000.0, "n_indeterminadas_universo": 0,
          "passivo_universo": 2.3e8}


def _premissas(**ajustes):
    return resolver(estado.ler_semente(), "base", {"peso_classe_indeterminada_base": 0.5, **ajustes})


def _faixas():
    return sensibilidade.faixas_suposicoes(estado.ler_semente())


def test_no_valor_base_o_tornado_e_o_do_notebook_08():
    """Com os controles no valor base, o tornado do Explorar repete o da página "Quão certo é" (sensibilidade.tornado)."""
    p = _premissas()
    novo = explorar.tornado(TOTAIS, p, _faixas(), CENARIOS)
    antigo = sensibilidade.tornado(TOTAIS, _faixas(), p, CENARIOS)
    assert [x["suposicao"] for x in novo] == list(antigo["suposicao"])
    for x, (_, y) in zip(novo, antigo.iterrows()):
        assert x["premio_no_min"] == pytest.approx(y["premio_no_min"])
        assert x["premio_no_max"] == pytest.approx(y["premio_no_max"])
        assert x["premio_base"] == pytest.approx(y["premio_base"])


def test_tornado_centrado_no_valor_escolhido():
    p = _premissas(taxa_seguro_anual=0.03)
    t = {x["suposicao"]: x for x in explorar.tornado(TOTAIS, p, _faixas(), CENARIOS)}
    escolhido = resumo_por_totais(TOTAIS, p, CENARIOS, "mantem")["mercado_premio_emitido"]
    assert all(x["premio_base"] == pytest.approx(escolhido) for x in t.values())
    assert t["taxa"]["valor_escolhido"] == 0.03
    assert t["taxa"]["premio_no_min"] <= escolhido <= t["taxa"]["premio_no_max"]


def test_valor_fora_da_faixa_estende_a_faixa():
    f = _faixas()
    acima = float(f.loc["taxa", "max"]) + 0.01
    g = explorar.faixas_ao_redor(f, _premissas(taxa_seguro_anual=acima))
    assert g.loc["taxa", "max"] == acima and g.loc["taxa", "base"] == acima
    assert g.loc["taxa", "min"] == f.loc["taxa", "min"]


def test_faixa_por_sorteio_no_valor_base_e_o_monte_carlo_do_notebook_08():
    """Mesma semente e mesmos sorteios: no valor base, a faixa do Explorar é a da variante principal do notebook 08."""
    p, f = _premissas(), _faixas()
    r = explorar.faixa_por_sorteio(TOTAIS, p, f, CENARIOS, n=20000, semente=5)
    x = sensibilidade.sortear(f, 20000, 5)
    ref = np.quantile(sensibilidade.premio_vetorial(TOTAIS, x)["premio"], [0.05, 0.95])
    assert [r["premio"]["p05"], r["premio"]["p95"]] == pytest.approx(list(ref))
    assert r["premio"]["extremo_min"] <= r["premio"]["p05"] <= r["premio"]["escolhido"] <= r["premio"]["p95"] \
        <= r["premio"]["extremo_max"]


def test_premio_sobe_com_a_taxa_e_suspensao_zera():
    """SPEC §3: prêmio monotônico na taxa; o cenário "suspende" zera a demanda (também nos sorteios)."""
    f = _faixas()
    baixo = explorar.faixa_por_sorteio(TOTAIS, _premissas(taxa_seguro_anual=0.015), f, CENARIOS, n=5000, semente=1)
    alto = explorar.faixa_por_sorteio(TOTAIS, _premissas(taxa_seguro_anual=0.03), f, CENARIOS, n=5000, semente=1)
    assert alto["premio"]["mediana"] > baixo["premio"]["mediana"]
    zero = explorar.faixa_por_sorteio(TOTAIS, _premissas(), f, CENARIOS, "suspende_8_17", n=5000, semente=1)
    assert zero["premio"]["p95"] == 0 and zero["premio"]["escolhido"] == 0
    meio = explorar.faixa_por_sorteio(TOTAIS, _premissas(), f, CENARIOS, "parcial", {"fracao_exigencia_garantia": 0.5},
                                      n=5000, semente=1)
    cheio = explorar.faixa_por_sorteio(TOTAIS, _premissas(), f, CENARIOS, n=5000, semente=1)
    assert meio["premio"]["mediana"] == pytest.approx(cheio["premio"]["mediana"] / 2)


def test_suposicao_sem_faixa_nao_quebra_o_sorteio():
    f = _faixas()
    f.loc["seguro", ["min", "max"]] = 0.5
    r = explorar.faixa_por_sorteio(TOTAIS, _premissas(), f, CENARIOS, n=1000, semente=2)
    assert np.isfinite([r["premio"]["p05"], r["premio"]["p95"]]).all()


def _previsao(medidas=explorar.TOTAIS_PROJETADOS):
    """Bloco `mercado` sintético da gold.analise_previsao: 2 anos × 2 leituras do limite × 2 variantes."""
    linhas = []
    for i, (ano, lim, var) in enumerate((a, c, v) for a in ("2026", "2027") for c in ("fixo", "corrigido")
                                        for v in ("principal", "outra")):
        for m in medidas:
            linhas.append({"bloco": "mercado", "periodo": ano, "cenario_limite": lim, "variante": var, "medida": m,
                           "p10": 0.0, "central": TOTAIS[m] * (1 + i / 10), "p90": 0.0})
    linhas.append({"bloco": "arrecadacao_mg", "periodo": "2027-1", "cenario_limite": "—", "variante": "principal",
                   "medida": "arrecadacao_semestral", "p10": 0.0, "central": 9e9, "p90": 0.0})
    return pd.DataFrame(linhas)


def test_totais_projetados_escolhem_ano_limite_e_variante():
    """2027, limite corrigido, variante principal = a 7ª combinação (i = 6): os totais da projeção × 1,6; o que a
    projeção não muda (ativas, CLT, passivo de todas) vem da base."""
    base = {**TOTAIS, "n_serventias_ativas": 99}
    t = explorar.totais_projetados(_previsao(), base, 2027, "corrigido", "principal")
    for m in explorar.TOTAIS_PROJETADOS:
        assert t[m] == pytest.approx(TOTAIS[m] * 1.6)
    assert (t["n_serventias_ativas"], t["clt"], t["passivo_todas"]) == (99, TOTAIS["clt"], TOTAIS["passivo_todas"])
    r = resumo_por_totais(t, _premissas(), CENARIOS, "mantem")
    assert r["mercado_premio_emitido"] == pytest.approx(
        1.6 * resumo_por_totais(TOTAIS, _premissas(), CENARIOS, "mantem")["mercado_premio_emitido"])


def test_totais_projetados_sem_os_totais_da_carga():
    """Carga anterior (só as 11 medidas antigas): None, e a página não oferece o ano projetado."""
    antigas = _previsao(["n_universo", "passivo_universo"])
    assert explorar.totais_projetados(antigas, TOTAIS, 2027, "fixo", "principal") is None
    assert explorar.totais_projetados(_previsao(), TOTAIS, 2030, "fixo", "principal") is None


def test_tornado_e_sorteio_em_menos_de_um_segundo():
    """Pronto quando da Fase 1, item 1: o recálculo do Explorar leva menos de 1 s (com os sorteios da configuração)."""
    p, f = _premissas(taxa_seguro_anual=0.025), _faixas()
    explorar.faixa_por_sorteio(TOTAIS, p, f, CENARIOS)   # aquece (import do numpy, leitura da configuração)
    inicio = time.perf_counter()
    explorar.tornado(TOTAIS, p, f, CENARIOS)
    explorar.faixa_por_sorteio(TOTAIS, p, f, CENARIOS)
    assert time.perf_counter() - inicio < 1.0
