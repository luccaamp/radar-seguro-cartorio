"""Teste da agregação LGPD (municípios SINTÉTICOS)."""
import pandas as pd
import pytest

from src.model.lgpd import agregar_lgpd


def test_municipios_pequenos_agregados():
    df = pd.DataFrame({"cod_ibge": [1, 2, 3, 4], "municipio": ["A", "B", "C", "D"],
                       "n_serventias": [5, 2, 1, 3], "valor_descoberto": [100.0, 20.0, 10.0, 30.0]})
    out = agregar_lgpd(df, 3)
    assert set(out.loc[~out["agregado_lgpd"], "municipio"]) == {"A", "D"}
    agregado = out[out["agregado_lgpd"]].iloc[0]
    assert agregado["n_serventias"] == 3 and agregado["valor_descoberto"] == pytest.approx(30.0)
    assert agregado["n_municipios_agregados"] == 2
    assert out["valor_descoberto"].sum() == pytest.approx(df["valor_descoberto"].sum())


def test_sem_municipio_pequeno():
    df = pd.DataFrame({"cod_ibge": [1], "municipio": ["A"], "n_serventias": [4], "x": [1.0]})
    assert not agregar_lgpd(df, 3)["agregado_lgpd"].any()
