"""O chat vê o que o painel vê (D-062): toda análise que uma página usa (`analise("nome")` em app/) e toda função
oferecida ao chat por src/painel/analises.py (PARA_O_CHAT e SEM_CONEXAO) é alcançada por uma das 5 ferramentas do chat
(src/agent/ferramentas.py, CONSULTAS), ou está em EXCECOES com o motivo.

Quando o painel ganhar uma análise nova, este teste falha e diz qual: acrescente-a em CONSULTAS (na ferramenta do
tema, com uma descrição curta) ou, se o chat não deve vê-la, em EXCECOES com a justificativa."""
import re

import duckdb
import pytest

from apoio_painel import RAIZ
from src.agent import ferramentas
from src.painel import analises

EXCECOES: dict[str, str] = {
    # "nome_da_funcao": "por que o chat não precisa dela",
}


def _usadas_pelas_paginas() -> dict[str, set[str]]:
    usadas: dict[str, set[str]] = {}
    # varre a pasta direto: o `git ls-files` põe entre aspas os nomes com acento (2_Análises.py) e eles se perderiam
    for arquivo in sorted((RAIZ / "app").rglob("*.py")):
        for nome in re.findall(r"""\banalise\(\s*["'](\w+)["']""", arquivo.read_text(encoding="utf-8")):
            usadas.setdefault(nome, set()).add(arquivo.relative_to(RAIZ).as_posix())
    return usadas


def test_toda_analise_das_paginas_chega_ao_chat():
    usadas = _usadas_pelas_paginas()
    # piso de 5 desde a D-051 (o painel enxuto usa 7 análises; antes eram 21)
    assert len(usadas) >= 5, "não achei as chamadas comum.analise(...) nas páginas: o padrão mudou?"
    faltam = {n: sorted(p) for n, p in usadas.items() if n not in ferramentas.alcancaveis() and n not in EXCECOES}
    assert not faltam, (f"análises que o painel mostra e o chat não alcança: {faltam}. Acrescente em "
                        "src/agent/ferramentas.py (CONSULTAS) ou em EXCECOES deste teste, com o motivo.")


def test_toda_funcao_oferecida_ao_chat_esta_numa_ferramenta():
    oferecidas = set(analises.PARA_O_CHAT) | set(analises.SEM_CONEXAO)
    faltam = sorted(oferecidas - ferramentas.alcancaveis() - set(EXCECOES))
    assert not faltam, f"funções de analises.py (PARA_O_CHAT/SEM_CONEXAO) fora do chat: {faltam}"


def test_excecoes_sao_justificadas_e_atuais():
    for nome, motivo in EXCECOES.items():
        assert len(motivo) > 20, f"exceção sem justificativa: {nome}"
        assert nome not in ferramentas.alcancaveis(), f"{nome} já está no chat: tire de EXCECOES"


def test_cada_consulta_aponta_para_uma_funcao_e_esta_no_esquema():
    for nome, opcoes in ferramentas.CONSULTAS.items():
        esquema = next(e for e in ferramentas.ESQUEMAS if e["name"] == nome)
        assert esquema["parameters"]["properties"]["analise"]["enum"] == list(opcoes)
        for analise in opcoes:
            assert callable(ferramentas._funcao(analise)[0]), analise


def _todas_funcionam(con):
    for nome, opcoes in ferramentas.CONSULTAS.items():
        for analise in opcoes:
            args = {"analise": analise, "pergunta": "quem fica fora do provimento 227", "municipio": "Uberaba"}
            r = ferramentas.executar(con, nome, args)
            assert "erro" not in r, (nome, analise, r.get("erro"))
            assert r.get("citar") or r.get("fonte"), (nome, analise)


def test_todas_as_consultas_funcionam_no_modo_demonstracao(painel_demo):
    """No Streamlit Community Cloud não há banco: o chat lê o conjunto público (D-029)."""
    with duckdb.connect(str(painel_demo["banco"]), read_only=True) as con:
        _todas_funcionam(con)


@pytest.mark.dados_reais
def test_todas_as_consultas_funcionam_no_modo_completo(banco_temporario):
    """Na cópia do banco real (nunca o banco real)."""
    with duckdb.connect(str(banco_temporario["copia"]), read_only=True) as con:
        _todas_funcionam(con)
