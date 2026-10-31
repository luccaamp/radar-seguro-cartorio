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
# dados_reais: recarrega o banco completo numa cópia; fora da suíte padrão
pytestmark = [pytest.mark.dados_reais, pytest.mark.skipif(not BANCO_REAL.exists(), reason="rode uv run pipeline.py antes")]
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
    # D-034: o estado preservado entre cargas são as versões de premissas; os cenários do painel saíram do banco, e
    # a tabela antiga estado.cenarios_salvos (ainda no banco real até a próxima carga) não é mais criada nem copiada
    tabela_antiga = "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'estado' " \
                    "AND table_name = 'cenarios_salvos'"
    with duckdb.connect(str(copia)) as con:
        if not con.execute(tabela_antiga).fetchone()[0]:   # banco já recarregado: recria a tabela antiga para o teste
            con.execute("CREATE TABLE estado.cenarios_salvos (id INTEGER PRIMARY KEY, nome VARCHAR)")
        versoes = con.execute("SELECT count(*) FROM estado.premissas_versoes").fetchone()[0]
    pipeline.main("gold", banco=copia, exportar_parquet=False)
    tamanho_1, hash_1 = copia.stat().st_size, _hash_publico(copia)
    pipeline.main("gold", banco=copia, exportar_parquet=False)
    tamanho_2, hash_2 = copia.stat().st_size, _hash_publico(copia)
    with duckdb.connect(str(copia), read_only=True) as con:
        assert con.execute(tabela_antiga).fetchone()[0] == 0
        assert con.execute("SELECT count(*) FROM estado.premissas_versoes").fetchone()[0] == versoes
        assert con.execute("SELECT count(*) FROM silver.serventia").fetchone()[0] > 0   # silver trazido do banco anterior
    assert abs(tamanho_2 - tamanho_1) <= 0.05 * tamanho_1     # o arquivo não cresce de uma carga para outra
    assert hash_1 == hash_2 and len(hash_1) >= 10              # mesmo silver -> mesmo gold público
    assert not copia.with_name(copia.name + ".novo").exists()


def test_a_partir_do_silver_parquet_reproduz_o_conjunto_publico(tmp_path):
    """D-029/2.4: gold recalculado só com data/silver/*.parquet (sem banco antigo, sem bronze) tem o mesmo conteúdo do
    conjunto público versionado (hash de conteúdo do manifesto)."""
    from src import publico
    banco = tmp_path / "radar.duckdb"
    pipeline.main("gold_de_parquet", banco=banco, exportar_parquet=False)
    man = publico.ler_manifesto()
    with duckdb.connect(str(banco), read_only=True) as con:
        diferentes = [a["tabela"] for a in man["arquivos"] if a["comparar"] and not publico.tabela_coerente(con, a)]
    assert not diferentes, diferentes


def test_carga_que_falha_nao_altera_o_banco(copia, monkeypatch):
    antes = hashlib.sha256(copia.read_bytes()).hexdigest()

    def quebra(con, exportar_parquet=True):
        raise RuntimeError("falha simulada no meio da carga")
    monkeypatch.setattr(pipeline, "etapa_gold", quebra)
    with pytest.raises(RuntimeError):
        pipeline.main("gold", banco=copia, exportar_parquet=False)
    assert hashlib.sha256(copia.read_bytes()).hexdigest() == antes
    assert not copia.with_name(copia.name + ".novo").exists()
