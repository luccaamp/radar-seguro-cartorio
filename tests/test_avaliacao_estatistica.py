"""Margem de erro da avaliação do chat (src/agent/avaliacao.py; Miller, 2024, arXiv:2411.00640). Funções puras, sem
API. Os valores de referência são os de livro (Wilson para 0/10 e 10/10; 385 perguntas para ±5 pontos a 50%) e o
resultado da rodada de 2026-11-07 (50 de 52). Dados SINTÉTICOS, menos esse último."""
import math

import pytest

from src.agent import avaliacao as a

C95 = 0.95


def test_wilson_valores_de_referencia():
    lo, hi = a.intervalo_wilson(0, 10, C95)
    assert lo == pytest.approx(0.0, abs=1e-12) and hi == pytest.approx(0.2775, abs=1e-4)
    lo, hi = a.intervalo_wilson(10, 10, C95)
    assert lo == pytest.approx(0.7225, abs=1e-4) and hi == pytest.approx(1.0, abs=1e-12)
    lo, hi = a.intervalo_wilson(50, 52, C95)          # a rodada (c) de 2026-11-07
    assert (round(lo, 3), round(hi, 3)) == (0.870, 0.989)


def test_wilson_fica_dentro_de_0_1_e_estreita_com_mais_perguntas():
    for k, n in [(0, 1), (1, 1), (3, 7), (99, 100)]:
        lo, hi = a.intervalo_wilson(k, n, C95)
        assert 0 <= lo <= k / n <= hi <= 1
    assert (lambda x: x[1] - x[0])(a.intervalo_wilson(96, 100, C95)) < \
        (lambda x: x[1] - x[0])(a.intervalo_wilson(48, 50, C95))
    assert a.intervalo_wilson(5, 10, 0.99)[0] < a.intervalo_wilson(5, 10, C95)[0]   # mais confiança, mais largo
    with pytest.raises(ValueError):
        a.intervalo_wilson(0, 0, C95)


def test_erro_agrupado_com_grupos_de_um_e_o_erro_comum():
    x = [True, False, True, True, False, True]
    m = sum(x) / len(x)
    comum = math.sqrt(sum((v - m) ** 2 for v in x)) / len(x)
    assert a.erro_padrao_agrupado({str(i): [v] for i, v in enumerate(x)}) == pytest.approx(comum)


def test_erro_agrupado_cresce_quando_o_grupo_erra_junto():
    """O mesmo acerto (50%), mas com os erros todos num tipo: o erro agrupado é maior que o de perguntas soltas."""
    junto = {"a": [True] * 4, "b": [False] * 4}
    solto = {"a": [True, False] * 2, "b": [True, False] * 2}
    assert a.erro_padrao_agrupado(junto) > a.erro_padrao_agrupado(solto)
    with pytest.raises(ValueError):
        a.erro_padrao_agrupado({})


def test_diferenca_pareada():
    d, lo, hi = a.diferenca_pareada([True, False] * 5, [True, False] * 5, C95)
    assert (d, lo, hi) == (0.0, 0.0, 0.0)                      # mesmas respostas: diferença zero, sem incerteza
    d, lo, hi = a.diferenca_pareada([False] * 8 + [True] * 2, [True] * 10, C95)
    assert d == pytest.approx(0.8) and lo < 0.8 < hi == 1.0      # não passa de +1 (aproximação normal cortada)
    assert a.diferenca_pareada([True] * 10, [False] * 8 + [True] * 2, C95)[1] == -1.0
    with pytest.raises(ValueError):
        a.diferenca_pareada([True], [True, False], C95)


def test_perguntas_para_margem():
    assert a.perguntas_para_margem(0.5, 0.05, C95) == 385   # o número clássico de pesquisa de opinião
    assert a.perguntas_para_margem(50 / 52, 0.03, C95) == 158
    assert a.perguntas_para_margem(1.0, 0.03, C95) > 0       # 100% não zera a conta
    with pytest.raises(ValueError):
        a.perguntas_para_margem(0.5, 0, C95)
