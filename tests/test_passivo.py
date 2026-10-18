"""Testes do passivo por vínculo e por município. Funcionários e municípios SINTÉTICOS."""
from datetime import date

import pandas as pd
import pytest

from src.model.passivo import avos, avos_13_da_projecao, dias_aviso_previo, passivo_municipio, passivo_por_vinculo


def test_exemplo_feito_a_mao(p_base):
    """Funcionário fictício: R$ 3.000,00, 5 anos e 4 meses de casa (64 meses) em 31/12. Conta à mão em docs/diario.md."""
    r = passivo_por_vinculo(3000.0, 64, p_base)
    assert r.dias_aviso == 45                               # 30 + 3 x 5 anos
    assert r.aviso_previo == pytest.approx(4500.00)         # 3.000 x 45/30
    assert r.avos_13 == 1                                   # 31/12 + 45 dias = 14/02: janeiro inteiro + 14 dias -> 1/12
    assert r.decimo_terceiro == pytest.approx(250.00)
    assert r.avos_ferias == 6                               # 4 meses + 45 dias = 165 dias -> 6/12
    assert r.periodos_ferias_vencidas == pytest.approx(0.5)
    assert r.ferias == pytest.approx(4000.00)               # 3.000 x (6/12 + 0,5) x 4/3
    assert r.saldo_fgts_estimado == pytest.approx(17066.67, abs=0.01)  # 8% x 3.000 x 64 x 13,33/12
    assert r.fgts_rescisorio == pytest.approx(380.00)       # 8% x (aviso 4.500 + 13º 250)
    assert r.multa_fgts == pytest.approx(6978.67, abs=0.01) # 40% x (17.066,67 + 380)
    assert r.inss_patronal == pytest.approx(50.00)          # 20% x 13º
    assert r.rat_fap == pytest.approx(2.50)                 # 1% x FAP 1,0 x 13º
    assert r.total == pytest.approx(16161.17, abs=0.01)


@pytest.mark.parametrize("dias, esperado", [
    (30, 1),   # termina em 30/01: 30 dias de janeiro
    (33, 1),   # 02/02
    (44, 1),   # 13/02
    (45, 1),   # 14/02: 14 dias de fevereiro não completam a fração
    (46, 2),   # 15/02
    (59, 2),   # 28/02 (ano não bissexto)
    (90, 3),   # 31/03
])
def test_avos_13_pelo_calendario(dias, esperado):
    assert avos_13_da_projecao(date(2025, 12, 31), dias, 15) == esperado


def test_inss_sobre_aviso_so_no_max(p_base, p_max):
    base = passivo_por_vinculo(3000.0, 64, p_base)
    mx = passivo_por_vinculo(3000.0, 64, {**p_max, "fap": 1.0, "fracao_ferias_vencidas_pendentes": 0.5})
    assert base.inss_patronal == pytest.approx(0.20 * 250)
    assert mx.inss_patronal == pytest.approx(0.20 * (250 + 4500))


def test_sem_vinculos_passivo_zero(p_base):
    vazio = pd.DataFrame(columns=["cod_ibge", "salario", "meses_servico"])
    assert passivo_municipio(vazio, p_base).empty
    assert passivo_por_vinculo(0.0, 120, p_base).total == 0


def test_aviso_previo_respeita_teto_de_90_dias(p_base):
    assert dias_aviso_previo(11.9, p_base) == 30
    assert dias_aviso_previo(12, p_base) == 33
    assert dias_aviso_previo(20 * 12, p_base) == 90
    assert dias_aviso_previo(35 * 12, p_base) == 90


@pytest.mark.parametrize("dias, esperado", [(14, 0), (15, 1), (30, 1), (44, 1), (45, 2), (90, 3)])
def test_regra_dos_15_dias(dias, esperado):
    assert avos(dias, 15) == esperado


def test_projecao_do_aviso_completa_periodo_de_ferias(p_base):
    # 11,5 meses de casa + 30 dias de aviso passa de 12 meses: um período inteiro + 1/12 (15 dias de sobra)
    r = passivo_por_vinculo(1000.0, 11.5, p_base)
    assert r.periodos_ferias_vencidas == 1
    assert r.avos_ferias == 1


def test_menos_de_um_ano_sem_ferias_vencidas_pendentes(p_max):
    assert passivo_por_vinculo(2000.0, 8, p_max).periodos_ferias_vencidas == 0


def test_passivo_proporcional_ao_salario(p_base):
    assert passivo_por_vinculo(6000.0, 64, p_base).total == pytest.approx(2 * passivo_por_vinculo(3000.0, 64, p_base).total)


def test_passivo_nao_linear_no_tempo(p_base):
    """Por isso o modelo aplica a função a cada vínculo e nunca à média (SPEC §3.2)."""
    def tot(m):
        return passivo_por_vinculo(3000.0, m, p_base).total
    assert tot(6) + tot(234) != pytest.approx(2 * tot(120))


def test_faixa_min_base_max(p_min, p_base, p_max):
    totais = [passivo_por_vinculo(3000.0, 64, p).total for p in (p_min, p_base, p_max)]
    assert totais[0] < totais[1] < totais[2]


def test_passivo_municipio_agrega_por_vinculo(p_base):
    v = pd.DataFrame({"cod_ibge": [1, 1, 2], "salario": [3000.0, 3000.0, 1500.0], "meses_servico": [64, 64, 10]})
    g = passivo_municipio(v, p_base).set_index("cod_ibge")
    assert g.at[1, "n_vinculos"] == 2
    assert g.at[1, "passivo_total"] == pytest.approx(2 * 16161.17, abs=0.02)
    assert g.at[2, "passivo_medio_vinculo"] == pytest.approx(passivo_por_vinculo(1500.0, 10, p_base).total)
