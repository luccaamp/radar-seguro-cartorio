"""Testes das funções de normalização (dados de entrada fictícios)."""
import pytest

from src.transform.normalizar import normalizar_nome, para_float_br


@pytest.mark.parametrize("entrada, esperado", [
    ("Pingo-d'Água", "PINGO D AGUA"),
    ("  São   João del-Rei ", "SAO JOAO DEL REI"),
    ("BRASÓPOLIS", "BRASOPOLIS"),
    (None, ""),
    ("", ""),
])
def test_normalizar_nome(entrada, esperado):
    assert normalizar_nome(entrada) == esperado


@pytest.mark.parametrize("entrada, esperado", [
    ("1021527.54", 1021527.54),
    ("350407,58", 350407.58),
    ("1.234,56", 1234.56),
    ("0", 0.0),
    ("NÃO INFORMADO", None),
    ("", None),
    (None, None),
])
def test_para_float_br(entrada, esperado):
    assert para_float_br(entrada) == esperado
