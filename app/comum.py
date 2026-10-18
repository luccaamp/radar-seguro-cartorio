"""Peças comuns do painel: conexão, formatação pt-BR, rodapé de fonte e paleta. Todo número exibido leva rodapé."""
import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src import estado  # noqa: E402

BANCO = RAIZ / "data" / "radar.duckdb"

# paleta (skill de visualização, instância de referência): sequencial azul, série única azul, superfícies
AZUL_SEQUENCIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
AZUL_SERIE = "#2a78d6"
CINZA_AGREGADO = "#d9d8d4"

NOMES_FONTE = {
    "cnj_serventias": "CNJ / Justiça Aberta (cadastro)",
    "cnj_colaboradores": "CNJ / Justiça Aberta (colaboradores)",
    "cnj_arrecadacao": "CNJ / Justiça Aberta (arrecadação)",
    "rais_vinculos": "RAIS / PDET",
    "cnpj_estabelecimentos": "CNPJ / Receita Federal",
    "susep_ses_garantia": "SUSEP SES",
    "ibge_municipios": "IBGE (municípios)",
    "ibge_populacao": "IBGE (população)",
    "ibge_malha": "IBGE (malha)",
    "ibge_inpc": "IBGE (INPC)",
    "ibge_ipca": "IBGE (IPCA)",
}
SITUACOES = {"PROVIDO": "Provida (titular)", "VAGO": "Vaga (interino)", "SOB INTERVENÇÃO": "Sob intervenção",
             "CONVERSÃO EM DILIGÊNCIA": "Conversão em diligência"}
ATRIBUICOES = {"notas": "Notas", "rcpn": "Registro Civil (PN)", "ri": "Registro de Imóveis",
               "rtd": "Títulos e Documentos", "rcpj": "Registro Civil (PJ)", "protesto": "Protesto"}
NIVEIS = {"min": "mínimo", "base": "base", "max": "máximo"}


@st.cache_resource
def conexao() -> duckdb.DuckDBPyConnection:
    if not BANCO.exists():
        st.error("Banco não encontrado. Rode `uv run pipeline.py` antes de abrir o painel.")
        st.stop()
    con = duckdb.connect(str(BANCO))
    estado.garantir_tabelas(con)
    return con


def consulta(sql: str, params: list | None = None) -> pd.DataFrame:
    return conexao().execute(sql, params or []).df()


def _br(v: float, casas: int) -> str:
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def num(v: float, casas: int = 0) -> str:
    return "—" if v is None or pd.isna(v) else _br(v, casas)


def brl(v: float) -> str:
    """R$ em escala legível: mil, mi, bi."""
    if v is None or pd.isna(v):
        return "—"
    a = abs(v)
    if a >= 1e9:
        return f"R$ {_br(v / 1e9, 2)} bi"
    if a >= 1e6:
        return f"R$ {_br(v / 1e6, 1)} mi"
    if a >= 1e3:
        return f"R$ {_br(v / 1e3, 1)} mil"
    return f"R$ {_br(v, 2)}"


def pct(v: float, casas: int = 1) -> str:
    return "—" if v is None or pd.isna(v) else f"{_br(100 * v, casas)}%"


def md(texto: str) -> str:
    """Escapa o cifrão para st.markdown/st.caption, que leem $...$ como fórmula (LaTeX)."""
    return texto.replace("$", r"\$")


def faixa(vmin: float, vbase: float, vmax: float, fmt=brl) -> str:
    return f"{fmt(vbase)}  (faixa {fmt(vmin)} a {fmt(vmax)})"


def execucao() -> pd.Series:
    return consulta("SELECT * FROM gold.execucao WHERE regra_classe = 'v2'").iloc[0]


def rodape(fontes: list[str], extra: str = "") -> None:
    """Fonte, data de referência e versão das premissas de tudo que está acima (SPEC §0, restrição 6)."""
    f = consulta("SELECT fonte, data_referencia FROM silver.fonte_metadados WHERE fonte IN (SELECT unnest(?))", [fontes])
    partes = [f"{NOMES_FONTE.get(r.fonte, r.fonte)} (ref. {r.data_referencia})" for r in f.itertuples()]
    e = execucao()
    st.caption(f"**Fontes:** {'; '.join(partes)}. **Premissas:** versão {int(e.versao_premissas)} · "
               f"carga de {e.executado_em:%d/%m/%Y %H:%M}." + (f" {extra}" if extra else ""))


def aviso_estimativa() -> None:
    st.info("Estimativas de mercado com premissas públicas, **não** avaliação de nenhum cartório. "
            "O market share é de uma **seguradora hipotética**. Classificação de classe sempre aproximada (D-002).",
            icon="ℹ️")
