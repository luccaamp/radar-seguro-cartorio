"""Fixtures dos testes. As premissas vêm da semente versionada; os dados de serventias e vínculos são SINTÉTICOS."""
from pathlib import Path

import pytest
import yaml

from src.model.premissas import resolver

CONFIG = Path(__file__).resolve().parents[1] / "config"
PESO_INDETERMINADA_TESTE = 0.656  # valor fixo para teste (no pipeline é calculado a cada carga)


def pytest_collection_modifyitems(config, items):
    """Testes `dados_reais` (precisam do banco completo, do silver ou do bronze) ficam fora da suíte padrão (addopts
    em pyproject.toml); se forem pedidos (-m dados_reais) numa máquina sem os dados, são pulados com o motivo."""
    from apoio_painel import BANCO_REAL
    if BANCO_REAL.exists():
        return
    pular = pytest.mark.skip(reason="dados reais ausentes (data/radar.duckdb); ver CONTRIBUTING.md, 'Dados da equipe'")
    for item in items:
        if "dados_reais" in item.keywords:
            item.add_marker(pular)


@pytest.fixture(scope="session", autouse=True)
def _sem_gemini():
    """A suíte padrão nunca chama a API do Gemini (D-060): a chave fica vazia (vale mais que o .env e o st.secrets) e
    a rede do src/llm.py é trocada por um transporte que falha. Os testes do chat usam um modelo falso ou um
    servidor simulado (tests/test_chat.py)."""
    import os

    import httpx

    from src import llm

    def sem_rede(request):
        raise httpx.ConnectError("a suíte de testes não usa a rede", request=request)
    nome = llm.config()["variavel_chave"]
    anterior, transporte = os.environ.get(nome), llm._transporte
    os.environ[nome] = ""
    llm._transporte = httpx.MockTransport(sem_rede)
    yield
    llm._transporte = transporte
    llm._principal_fora_ate = 0.0
    if anterior is None:
        os.environ.pop(nome, None)
    else:
        os.environ[nome] = anterior


@pytest.fixture(scope="session")
def _copia_real(tmp_path_factory):
    """Cópia do banco real com o gold refeito pelo código atual (uma vez por sessão). Confere no fim que o banco real
    e os Parquet de data/ não mudaram."""
    from apoio_painel import BANCO_REAL, assinatura_real, preparar_copia
    if not BANCO_REAL.exists():
        pytest.skip("rode uv run pipeline.py antes")
    antes = assinatura_real()
    copia = preparar_copia(tmp_path_factory.mktemp("banco"))
    yield {"copia": copia, "real_antes": antes}
    assert assinatura_real() == antes, "o banco real ou os Parquet de data/ mudaram durante os testes"


@pytest.fixture(scope="module")
def banco_temporario(_copia_real):
    """Modo completo: o painel aponta para a cópia do banco real durante o módulo de teste (testes dados_reais)."""
    from apoio_painel import apontar_painel, restaurar
    anterior = apontar_painel(_copia_real["copia"])
    yield _copia_real
    restaurar(anterior)


@pytest.fixture(scope="module")
def painel_demo(tmp_path_factory):
    """Modo demonstração: sem banco, o painel monta o seu a partir do conjunto público versionado (data/publico).
    Roda em qualquer clone, sem dados reais. Devolve o caminho do banco de demonstração (só leitura nos testes)."""
    from apoio_painel import apontar_painel, restaurar
    from src import publico
    if not (publico.PASTA / publico.MANIFESTO).exists():
        pytest.fail("data/publico/manifesto.json ausente: rode uv run python scripts/gerar_publico.py")
    inexistente = tmp_path_factory.mktemp("sem_banco") / "nao_existe.duckdb"
    anterior = apontar_painel(inexistente, publico.PASTA)
    yield {"banco": publico.banco_demonstracao(publico.PASTA)}
    restaurar(anterior)


@pytest.fixture(scope="session")
def semente() -> dict:
    from src.estado import ler_semente   # a mesma semente que o pipeline usa (hoje premissas_v003.yaml)
    return ler_semente()


@pytest.fixture(scope="session")
def regras() -> dict:
    return yaml.safe_load((CONFIG / "regras_classificacao.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def cenarios() -> dict:
    return yaml.safe_load((CONFIG / "cenarios_stf.yaml").read_text(encoding="utf-8"))


def _nivel(semente, nivel):
    return resolver(semente, nivel, {"peso_classe_indeterminada_base": {"min": 0.0, "base": PESO_INDETERMINADA_TESTE,
                                                                        "max": 1.0}[nivel]})


@pytest.fixture(scope="session")
def p_base(semente):
    return _nivel(semente, "base")


@pytest.fixture(scope="session")
def p_min(semente):
    return _nivel(semente, "min")


@pytest.fixture(scope="session")
def p_max(semente):
    return _nivel(semente, "max")
