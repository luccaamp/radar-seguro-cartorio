"""Coletores e bronze enxuto (D-032).

- Suíte padrão (dados SINTÉTICOS): separador da RAIS detectado pelo cabeçalho; filtro da RAIS sobre um .7z sintético
  separado por vírgula; silver lendo URL e hora de coleta do original.json quando o original não está no bronze.
- dados_reais: regerar cada extrato (RAIS, SUSEP, CNPJ) a partir do original guardado dá o MESMO SHA-256 do extrato
  do bronze oficial (os originais ficam na pasta de originais, fora do OneDrive; config/pacotes.yaml).
"""
import json
from pathlib import Path

import py7zr
import pytest

from src.ingest import cnpj, comum, rais, susep
from src.transform import silver


def test_separador_da_rais():
    assert rais.separador('"Bairros SP - Código","CNAE 2.0 Subclasse - Codigo","Município - Código"\n') == ","
    assert rais.separador("Bairros SP - Código;CNAE 2.0 Subclasse - Codigo;Município - Código\n") == ";"


def test_filtro_da_rais_com_virgula_e_aspas(tmp_path):
    """SINTÉTICO: arquivo da RAIS separado por vírgula e entre aspas (como o de 2025) vira extrato com ';'."""
    bruto = tmp_path / "RAIS_TESTE.COMT"
    linhas = ['"Tipo Vínculo - Código","CNAE 2.0 Subclasse - Codigo","Município - Código","Vl Rem Dezembro Nom"',
              '"10","6912500","310620","3000,50"', '"10","6912500","330455","2000,00"',
              '"10","1234567","310620","1000,00"', '"15"," 6912500 ","311000"," 2500,00 "']
    bruto.write_text("\n".join(linhas) + "\n", encoding="latin-1")
    pacote = tmp_path / "RAIS_TESTE.7z"
    with py7zr.SevenZipFile(pacote, "w") as z:
        z.write(bruto, "RAIS_TESTE.COMT")
    bruto.unlink()
    saida = rais.filtrar(pacote, "MG", saida_extrato=tmp_path / "saida", pasta_extracao=tmp_path / "extr")
    assert saida.read_text(encoding="utf-8").splitlines() == [
        "Tipo Vínculo - Código;CNAE 2.0 Subclasse - Codigo;Município - Código;Vl Rem Dezembro Nom",
        "10;6912500;310620;3000,50", "15;6912500;311000;2500,00"]


def test_silver_le_o_original_json_quando_o_original_saiu(tmp_path, monkeypatch):
    """SINTÉTICO: extrato cuja origem não está mais no bronze pega URL e hora de coleta do original.json."""
    bronze = tmp_path / "bronze"
    pasta = bronze / "susep_ses" / "2026-01-01"
    pasta.mkdir(parents=True)
    extrato = pasta / "ses_seguros_garantia.csv"
    extrato.write_text("x\n", encoding="utf-8")
    (pasta / "ses_seguros_garantia.csv.meta.json").write_text(json.dumps(
        {"coletado_em": "2026-01-02T00:00:00-03:00", "origem": "susep_ses\\2026-01-01\\BaseCompleta.zip"}),
        encoding="utf-8")
    (pasta / "original.json").write_text(json.dumps({"arquivos": {"BaseCompleta.zip": {
        "url": "https://exemplo.invalido/BaseCompleta.zip", "coletado_em": "2026-01-01T10:00:00-03:00"}}}),
        encoding="utf-8")
    monkeypatch.setattr(silver, "BRONZE", bronze)
    meta = silver._meta(extrato)
    assert meta["url"] == "https://exemplo.invalido/BaseCompleta.zip"
    assert meta["coletado_em"] == "2026-01-01T10:00:00-03:00"


# ------------------------------------------------------------------ dados reais: reprodutibilidade dos extratos
def _original(rel: str) -> Path:
    for base in (comum.originais(), comum.BRONZE):   # depois da D-032, fora do bronze; antes, no bronze
        if (base / rel).exists():
            return base / rel
    pytest.skip(f"original ausente: {rel} (ver config/pacotes.yaml, pastas.originais)")


@pytest.mark.dados_reais
def test_rais_extrato_regenerado_igual(tmp_path):
    pacote = _original("rais/2025/RAIS_VINC_PUB_MG_ES_RJ.7z")
    novo = rais.filtrar(pacote, "MG", saida_extrato=tmp_path / "saida", pasta_extracao=tmp_path / "extr")
    oficial = comum.BRONZE / "rais" / "2025" / "extraido" / novo.name
    assert comum.sha256_arquivo(novo) == comum.sha256_arquivo(oficial)


@pytest.mark.dados_reais
def test_susep_extrato_regenerado_igual(tmp_path):
    zpath = _original("susep_ses/2026-10-17/BaseCompleta.zip")
    novo = susep.filtrar(zpath, saida=tmp_path)
    oficial = comum.BRONZE / "susep_ses" / "2026-10-17"
    for nome in ("ses_seguros_garantia.csv", "ses_cias.csv"):
        assert comum.sha256_arquivo(tmp_path / nome) == comum.sha256_arquivo(oficial / nome), nome
    assert novo.name == "ses_seguros_garantia.csv"


@pytest.mark.dados_reais
def test_cnpj_extrato_regenerado_igual(tmp_path):
    """Lê os 6,8 GB do CNPJ: leva alguns minutos."""
    pasta = _original("cnpj/2026-10/Estabelecimentos0.zip").parent
    novo = cnpj.filtrar(pasta, saida=tmp_path)
    oficial = comum.BRONZE / "cnpj" / "2026-10" / novo.name
    assert comum.sha256_arquivo(novo) == comum.sha256_arquivo(oficial)
