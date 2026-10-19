"""1.7: carga atômica, estado do usuário preservado e reprodutibilidade do gold.

Tudo roda numa CÓPIA temporária do banco gerado pelo pipeline (nunca no banco real) e sem exportar Parquet.
Pulado se o pipeline ainda não rodou.
"""
import hashlib
import shutil
from pathlib import Path

import duckdb
import pytest

import pipeline

RAIZ = Path(__file__).resolve().parents[1]
BANCO_REAL = RAIZ / "data" / "radar.duckdb"
pytestmark = pytest.mark.skipif(not BANCO_REAL.exists(), reason="rode uv run pipeline.py antes")
COLUNAS_DE_HORARIO = {"executado_em"}   # mudam a cada carga por definição; fora da comparação


def _hash_publico(banco: Path) -> dict[str, str]:
    """Hash de cada tabela pública do gold (sem as interno_* e sem colunas de horário), com as linhas ordenadas."""
    out = {}
    with duckdb.connect(str(banco), read_only=True) as con:
        tabelas = [t for (t,) in con.execute("SELECT table_name FROM information_schema.tables WHERE "
                                             "table_schema = 'gold' AND table_name NOT LIKE 'interno_%'").fetchall()]
        for t in sorted(tabelas):
            df = con.sql(f"SELECT * FROM gold.{t}").df()
            df = df.drop(columns=[c for c in df.columns if c in COLUNAS_DE_HORARIO])
            df = df.sort_values(list(df.columns)).reset_index(drop=True)
            out[t] = hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()
    return out


@pytest.fixture()
def copia(tmp_path) -> Path:
    destino = tmp_path / "radar.duckdb"
    shutil.copy2(BANCO_REAL, destino)
    return destino


def test_carga_preserva_estado_nao_cresce_e_e_reprodutivel(copia):
    with duckdb.connect(str(copia)) as con:   # um cenário salvo pelo usuário, que a carga não pode perder
        n = con.execute("SELECT coalesce(max(id), 0) + 1 FROM estado.cenarios_salvos").fetchone()[0]
        con.execute("INSERT INTO estado.cenarios_salvos (id, nome) VALUES (?, 'cenário de teste')", [n])
        versoes = con.execute("SELECT count(*) FROM estado.premissas_versoes").fetchone()[0]
    pipeline.main("gold", banco=copia, exportar_parquet=False)
    tamanho_1, hash_1 = copia.stat().st_size, _hash_publico(copia)
    pipeline.main("gold", banco=copia, exportar_parquet=False)
    tamanho_2, hash_2 = copia.stat().st_size, _hash_publico(copia)
    with duckdb.connect(str(copia), read_only=True) as con:
        assert con.execute("SELECT nome FROM estado.cenarios_salvos WHERE id = ?", [n]).fetchone() == ("cenário de teste",)
        assert con.execute("SELECT count(*) FROM estado.premissas_versoes").fetchone()[0] == versoes
        assert con.execute("SELECT count(*) FROM silver.serventia").fetchone()[0] > 0   # silver trazido do banco anterior
    assert abs(tamanho_2 - tamanho_1) <= 0.05 * tamanho_1     # o arquivo não cresce de uma carga para outra
    assert hash_1 == hash_2 and len(hash_1) >= 10              # mesmo silver -> mesmo gold público
    assert not copia.with_name(copia.name + ".novo").exists()


def test_carga_que_falha_nao_altera_o_banco(copia, monkeypatch):
    antes = hashlib.sha256(copia.read_bytes()).hexdigest()

    def quebra(con, exportar_parquet=True):
        raise RuntimeError("falha simulada no meio da carga")
    monkeypatch.setattr(pipeline, "etapa_gold", quebra)
    with pytest.raises(RuntimeError):
        pipeline.main("gold", banco=copia, exportar_parquet=False)
    assert hashlib.sha256(copia.read_bytes()).hexdigest() == antes
    assert not copia.with_name(copia.name + ".novo").exists()
