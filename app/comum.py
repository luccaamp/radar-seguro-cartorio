"""Peças comuns do painel: conexão, formatação pt-BR, rodapé de fonte e paleta. Todo número exibido leva rodapé."""
import json
import os
import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src import estado, publico  # noqa: E402

CARGA_ATUAL = RAIZ / "data" / "carga_atual.json"   # gravado por scripts/baixar_dados.py (2.5.3)


def caminho_banco() -> Path:
    """RADAR_BANCO aponta o painel para outro arquivo (os testes usam uma cópia temporária; nunca o banco real).
    Lido a cada chamada: os testes trocam de modo no mesmo processo."""
    return Path(os.environ.get("RADAR_BANCO") or RAIZ / "data" / "radar.duckdb")


def pasta_publico() -> Path:
    """RADAR_PUBLICO aponta para outro conjunto público (testes); padrão: data/publico, versionado no repositório."""
    return Path(os.environ.get("RADAR_PUBLICO") or publico.PASTA)


BANCO = caminho_banco()   # caminho no momento da importação (compatibilidade)


def modo() -> str:
    """'completo' com o banco do pipeline; 'demonstracao' só com o conjunto público (D-029); 'sem_dados' sem nenhum."""
    if caminho_banco().exists():
        return "completo"
    return "demonstracao" if (pasta_publico() / publico.MANIFESTO).exists() else "sem_dados"


def demonstracao() -> bool:
    return modo() == "demonstracao"

# paleta (skill de visualização, instância de referência): sequencial azul, série única azul, superfícies
AZUL_SEQUENCIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
AZUL_SERIE = "#2a78d6"

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
FONTES_NAO_USADAS = {"ibge_ipca"}   # coletadas, mas fora de qualquer conta: só na tabela de fontes, não nos rodapés
SITUACOES = {"PROVIDO": "Provida (titular)", "VAGO": "Vaga (interino)", "SOB INTERVENÇÃO": "Sob intervenção",
             "CONVERSÃO EM DILIGÊNCIA": "Conversão em diligência"}
ATRIBUICOES = {"notas": "Notas", "rcpn": "Registro Civil (PN)", "ri": "Registro de Imóveis",
               "rtd": "Títulos e Documentos", "rcpj": "Registro Civil (PJ)", "protesto": "Protesto"}
NIVEIS = {"min": "mínimo", "base": "base", "max": "máximo"}


@st.cache_resource
def _abrir(caminho: str) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(caminho)
    estado.garantir_tabelas(con)
    return con


def conexao() -> duckdb.DuckDBPyConnection:
    m = modo()
    if m == "sem_dados":
        st.error("Sem dados: nem o banco (data/radar.duckdb) nem o conjunto público (data/publico/). "
                 "Veja 'Como rodar' no README.")
        st.stop()
    # modo demonstração: banco temporário montado a partir do conjunto público (fora do repositório)
    return _abrir(str(caminho_banco() if m == "completo" else publico.banco_demonstracao(pasta_publico())))


def carga_em_uso() -> str:
    """Rodapé (2.5.3): 'Carga 2026-10-18 · dados completos' ou '· demonstração'."""
    if demonstracao():
        return f"Carga {publico.ler_manifesto(pasta_publico())['carga']} · demonstração"
    nivel = {"equipe": "dados completos", "publico": "recalculada com os dados públicos"}
    try:
        info = json.loads(CARGA_ATUAL.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        info = {}
    carga = info.get("carga") or f"{execucao().executado_em:%Y-%m-%d}"
    return f"Carga {carga} · {nivel.get(info.get('nivel'), 'dados completos')}"


def aviso_modo() -> None:
    """Faixa discreta do modo demonstração (2.2), no topo de cada página."""
    if demonstracao():
        data = pd.Timestamp(publico.ler_manifesto(pasta_publico())["carga"]).strftime("%d/%m/%Y")
        st.caption(f":material/info: **Modo demonstração:** dados da carga de {data}. Para recalcular, veja "
                   "'Como rodar' no README.")


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
    if abs(v) < 0.005:
        return "R$ 0"   # zero sem centavos (E8)
    a = abs(v)
    if a >= 1e9:
        return f"R$ {_br(v / 1e9, 2)} bi"
    if a >= 1e6:
        return f"R$ {_br(v / 1e6, 1)} mi"
    if a >= 1e3:
        return f"R$ {_br(v / 1e3, 1)} mil"
    return f"R$ {_br(v, 2)}"


def aprox(v: float) -> str:
    """Contagem esperada (valor esperado, fracionário): '≈ 0,4' abaixo de 10 e '≈ 486' a partir de 10 (E7, E8)."""
    if v is None or pd.isna(v):
        return "—"
    return f"≈ {_br(v, 1 if abs(v) < 10 else 0)}"


def pct(v: float, casas: int = 1) -> str:
    return "—" if v is None or pd.isna(v) else f"{_br(100 * v, casas)}%"


def md_seguro(texto: str) -> str:
    """Escapa o cifrão para st.markdown/st.caption/help, que leem $...$ como fórmula (LaTeX). Todo texto com "R$"
    exibido pelo Streamlit passa por aqui (testado em tests/test_app_codigo.py)."""
    return texto.replace("$", r"\$")


def faixa(vmin: float, vbase: float, vmax: float, fmt=brl) -> str:
    return f"{fmt(vbase)}  (faixa {fmt(vmin)} a {fmt(vmax)})"


def execucao() -> pd.Series:
    return consulta("SELECT * FROM gold.execucao WHERE regra_classe = 'v2'").iloc[0]


EXPLICA_NIVEIS = ("**Mínimo, base e máximo:** cada cenário põe todas as suposições no extremo ao mesmo tempo; "
                  "é um limite, não uma previsão.")


def data_base_passivo() -> str:
    """Data-base do passivo nas premissas vigentes (D-020), no formato dd/mm/aaaa."""
    p = estado.premissas_vigentes(conexao())[0]["premissas"]["data_posicao"]["valor"]
    return pd.Timestamp(p).strftime("%d/%m/%Y")


def rodape(fontes: list[str], extra: str = "", passivo: bool = True, taxa: bool = False) -> None:
    """Fonte, data de referência e versão das premissas de tudo que está acima (SPEC §0, restrição 6).

    `passivo`: acrescenta a data-base do passivo (D-020). `taxa`: diz que a taxa do seguro é suposição (E2)."""
    f = consulta("SELECT fonte, data_referencia FROM silver.fonte_metadados WHERE fonte IN (SELECT unnest(?))", [fontes])
    partes = [f"{NOMES_FONTE.get(r.fonte, r.fonte)} (ref. {r.data_referencia})" for r in f.itertuples()]
    e = execucao()
    v = int(e.versao_premissas)
    texto = (f"**Fontes:** {'; '.join(partes)}. **Premissas:** versão {v} · carga de {e.executado_em:%d/%m/%Y %H:%M}"
             f" ({carga_em_uso()}).")
    if passivo:
        texto += f" **Data-base do passivo:** {data_base_passivo()} (art. 4º do Prov. CNJ 227/2026)."
    if taxa:
        texto += f" **Taxa do seguro:** suposição (premissas v{v})."
    st.caption(md_seguro(texto + (f" {extra}" if extra else "")))


def universo_txt(valor: float, n_indeterminadas: int) -> str:
    """Universo do Prov. 227 como valor esperado (C6): '≈ 1.121 (valor esperado; inclui peso das 27 indeterminadas)'."""
    return f"{aprox(valor)} (valor esperado; inclui peso das {num(n_indeterminadas)} indeterminadas)"


def n_indeterminadas_no_universo(regra: str = "v2", nivel: str = "base") -> int:
    return int(consulta("SELECT n_indeterminadas_universo FROM gold.fato_mercado_uf WHERE regra_classe = ? "
                        "AND nivel = ? AND cenario_stf = 'mantem'", [regra, nivel]).iloc[0, 0])


def ticks_brl(vmax: float, n: int = 5) -> tuple[list[float], list[str]]:
    """Marcas de legenda de mapa em R$ com notação brasileira ('R$ 350 mil'), de 0 a `vmax`."""
    vals = [vmax * i / (n - 1) for i in range(n)]
    return vals, ["R$ 0" if v == 0 else brl(v) for v in vals]


def slider_br(col, rotulo: str, vmin: float, vmax: float, passo: float, valor: float, casas: int = 1,
              sufixo: str = "%", **kw) -> float:
    """Controle deslizante com vírgula decimal ('2,0%', '1,00'). O st.slider só formata com ponto, então usa
    select_slider com as opções já formatadas. Devolve o número escolhido (na mesma escala dos limites)."""
    n = int(round((vmax - vmin) / passo))
    opcoes = [round(vmin + i * passo, 10) for i in range(n + 1)]
    inicial = min(opcoes, key=lambda o: abs(o - valor))
    return col.select_slider(rotulo, options=opcoes, value=inicial, format_func=lambda o: f"{_br(o, casas)}{sufixo}", **kw)


def aviso_estimativa() -> None:
    aviso_modo()
    st.info("Estimativas de mercado com premissas públicas, **não** avaliação de nenhum cartório. "
            "O market share é de uma **seguradora hipotética**. Classificação de classe sempre aproximada (D-002).",
            icon="ℹ️")
