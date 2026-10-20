"""Contratos das tabelas silver: chave única, não nulos, domínios, faixas plausíveis e ausência de dados pessoais.

Severidade `erro` faz o pipeline falhar; `aviso` só registra (SPEC §4). Resultados em `qualidade.checagens`.
"""
from dataclasses import asdict, dataclass

import duckdb
import pandas as pd

UFS_VALIDAS = ("AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO").split()
COLUNAS_PROIBIDAS = ("responsavel", "substituto", "cpf", "titular", "delegatario", "telefone", "email", "endereco",
                     "denominacao_fantasia")
REGEX_CPF = r"\d{3}\.\d{3}\.\d{3}-\d{2}"


@dataclass
class Checagem:
    tabela: str
    checagem: str
    severidade: str  # erro | aviso
    violacoes: int
    detalhe: str = ""


def _conta(con, sql: str) -> int:
    return con.execute(sql).fetchone()[0]


def chave_unica(con, tabela: str, colunas: str) -> Checagem:
    n = _conta(con, f"SELECT count(*) FROM (SELECT {colunas} FROM {tabela} GROUP BY {colunas} HAVING count(*) > 1)")
    return Checagem(tabela, f"chave única ({colunas})", "erro", n)


def nao_nulo(con, tabela: str, coluna: str, filtro: str = "TRUE", severidade: str = "erro") -> Checagem:
    n = _conta(con, f"SELECT count(*) FROM {tabela} WHERE {coluna} IS NULL AND ({filtro})")
    return Checagem(tabela, f"não nulo: {coluna}" + ("" if filtro == "TRUE" else f" onde {filtro}"), severidade, n)


def condicao(con, tabela: str, nome: str, violacao_sql: str, severidade: str = "erro") -> Checagem:
    n = _conta(con, f"SELECT count(*) FROM {tabela} WHERE {violacao_sql}")
    return Checagem(tabela, nome, severidade, n)


def sem_dados_pessoais(con, schema: str) -> list[Checagem]:
    out = []
    cols = con.execute("SELECT table_name, column_name, data_type FROM information_schema.columns "
                       f"WHERE table_schema = '{schema}'").fetchall()
    for tab in sorted({t for t, _, _ in cols}):
        proibidas = [c for t, c, _ in cols if t == tab and any(p in c.lower() for p in COLUNAS_PROIBIDAS)]
        out.append(Checagem(f"{schema}.{tab}", "sem colunas de dados pessoais", "erro", len(proibidas),
                            ", ".join(proibidas)))
        textos = [c for t, c, tipo in cols if t == tab and tipo == "VARCHAR"]
        # no silver, sempre presente (0 se a tabela não tem texto): a lista de checagens não pode depender de quais
        # colunas o silver traz (o silver público da D-031 tem menos colunas que o interno). No gold, como antes.
        if textos or schema == "silver":
            cond = " OR ".join(f"regexp_matches(\"{c}\", '{REGEX_CPF}')" for c in textos) or "false"
            out.append(condicao(con, f"{schema}.{tab}", "sem CPF em campos de texto", cond))
    return out


def contratos_silver(con: duckdb.DuckDBPyConnection) -> list[Checagem]:
    s = "silver"
    cod_ok = "cod_ibge NOT BETWEEN 1100000 AND 5399999"
    c = [
        chave_unica(con, f"{s}.municipio_ibge", "cod_ibge"),
        nao_nulo(con, f"{s}.municipio_ibge", "populacao", severidade="aviso"),
        chave_unica(con, f"{s}.serventia", "cns"),
        nao_nulo(con, f"{s}.serventia", "cod_ibge"),
        condicao(con, f"{s}.serventia", "código IBGE com 7 dígitos válido", cod_ok),
        condicao(con, f"{s}.serventia", "UF válida", f"uf NOT IN {tuple(UFS_VALIDAS)}"),
        condicao(con, f"{s}.serventia", "status no domínio", "status NOT IN ('Ativo', 'Inativo', 'Extinto')"),
        condicao(con, f"{s}.serventia", "situação jurídica no domínio (ativas)",
                 "status = 'Ativo' AND coalesce(situacao_juridica, '') NOT IN "
                 "('PROVIDO', 'VAGO', 'SOB INTERVENÇÃO', 'CONVERSÃO EM DILIGÊNCIA')"),
        chave_unica(con, f"{s}.serventia_colaboradores", "cns"),
        condicao(con, f"{s}.serventia_colaboradores", "colaboradores CLT entre 0 e 1000",
                 "informado AND (clt < 0 OR clt > 1000)"),
        _com_detalhe(condicao(con, f"{s}.serventia_colaboradores", "serventias com colaboradores declarados",
                              "NOT informado", "aviso"), "{n} serventias sem colaboradores declarados"),
        condicao(con, f"{s}.serventia_colaboradores", "CNS existe no cadastro",
                 f"cns NOT IN (SELECT cns FROM {s}.serventia)"),
        chave_unica(con, f"{s}.serventia_arrecadacao", "cns, periodo_inicio, periodo_fim, versao"),
        conflitos_arrecadacao(con),
        condicao(con, f"{s}.serventia_arrecadacao", "arrecadação não negativa", "arrecadacao < 0"),
        condicao(con, f"{s}.serventia_arrecadacao", "arrecadação semestral abaixo de R$ 1 bilhão",
                 "arrecadacao > 1e9", "aviso"),
        condicao(con, f"{s}.serventia_arrecadacao", "CNS existe no cadastro",
                 f"cns NOT IN (SELECT cns FROM {s}.serventia)"),
        chave_unica(con, f"{s}.rais_vinculo", "id_vinculo"),
        nao_nulo(con, f"{s}.rais_vinculo", "cod_ibge"),
        condicao(con, f"{s}.rais_vinculo", "remuneração de dezembro não negativa", "rem_dezembro < 0"),
        condicao(con, f"{s}.rais_vinculo", "tempo de emprego entre 0 e 720 meses",
                 "tempo_emprego_meses < 0 OR tempo_emprego_meses > 720"),
        condicao(con, f"{s}.rais_vinculo", "ativo e indeterminado sem remuneração de dezembro",
                 "ativo_31_12 AND prazo_indeterminado AND coalesce(rem_dezembro, 0) = 0", "aviso"),
        nao_nulo(con, f"{s}.cnpj_estabelecimento", "cod_ibge"),
        chave_unica(con, f"{s}.susep_garantia", "ano_mes, cod_entidade, cod_grupo, ramo"),
        condicao(con, f"{s}.susep_garantia", "ramo no domínio", "ramo NOT IN ('0775', '0776')"),
        chave_unica(con, f"{s}.indice_preco", "indice, ano_mes"),
        chave_unica(con, f"{s}.fonte_metadados", "arquivo"),
        nao_nulo(con, f"{s}.fonte_metadados", "data_referencia"),
    ]
    return c + controle_arrecadacao_mg(con) + sem_dados_pessoais(con, s)


def _com_detalhe(c: Checagem, modelo: str) -> Checagem:
    """Texto legível no painel quando há violação (E8): ex. '4 serventias sem colaboradores declarados'."""
    if c.violacoes:
        c.detalhe = modelo.format(n=c.violacoes)
    return c


def conflitos_arrecadacao(con: duckdb.DuckDBPyConnection) -> Checagem:
    """Períodos com versões de valor diferente na fonte (aviso). O detalhe separa linhas, pares CNS-período e os do
    ano de enquadramento, que são os únicos que afetam o modelo (1.5)."""
    import yaml
    from pathlib import Path
    ano = yaml.safe_load((Path(__file__).resolve().parents[2] / "config" / "escopo.yaml").read_text(encoding="utf-8")
                         )["ano_enquadramento"]
    linhas, pares, pares_ano = con.execute(f"""
        SELECT count(*), count(DISTINCT (cns, periodo_inicio)), count(DISTINCT (cns, periodo_inicio)) FILTER (WHERE ano = {ano})
        FROM silver.serventia_arrecadacao WHERE conflito_fonte""").fetchone()
    return Checagem("silver.serventia_arrecadacao", "período com valores conflitantes na fonte", "aviso", linhas,
                    f"{linhas} linhas ({pares} pares CNS-período; {pares_ano} em {ano}, os únicos que afetam a classe)")


def _mi(v: float) -> str:
    """R$ em milhões no formato brasileiro (texto exibido no painel)."""
    return "R$ " + f"{v / 1e6:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + " mi"


def _pct(v: float, sinal: bool = False) -> str:
    return (f"{100 * v:+.2f}" if sinal else f"{100 * v:.1f}").replace(".", ",") + "%"


def controle_arrecadacao_mg(con: duckdb.DuckDBPyConnection) -> list[Checagem]:
    """F2 (D-024): total de MG por semestre contra os totais de controle de config/qualidade.yaml.
    Contrato 1 (erro): queda maior que a tolerância em relação ao silver registrado. Contrato 2 (aviso): × BI do CNJ."""
    import yaml
    from pathlib import Path
    cfg = yaml.safe_load((Path(__file__).resolve().parents[2] / "config" / "qualidade.yaml").read_text(encoding="utf-8"))
    ctl = cfg.get("controle_arrecadacao_mg")
    if not ctl or not _conta(con, "SELECT count(*) FROM silver.serventia WHERE uf = 'MG'"):
        return []
    atual = dict(con.execute("""
        SELECT ano || '-' || semestre::INT, sum(arrecadacao) FROM silver.serventia_arrecadacao
        WHERE versao = 1 AND semestre IS NOT NULL
          AND cns IN (SELECT cns FROM silver.serventia WHERE status = 'Ativo' AND uf = 'MG')
        GROUP BY 1""").fetchall())
    out = []
    for periodo, ref in ctl["silver"]["totais"].items():
        v = float(atual.get(periodo) or 0.0)
        queda = (ref - v) / ref
        out.append(Checagem("silver.serventia_arrecadacao", f"total MG {periodo} × controle do silver (queda ≤ "
                            f"{_pct(ctl['silver']['tolerancia_queda'])})", "erro",
                            int(queda > ctl["silver"]["tolerancia_queda"]),
                            f"atual {_mi(v)}; controle {_mi(ref)} ({_pct(-queda, True)})"))
    for periodo, ref in ctl["bi"]["totais"].items():
        v = float(atual.get(periodo) or 0.0)
        dif, tol = v / ref - 1, ctl["bi"]["tolerancias"][periodo]
        out.append(Checagem("silver.serventia_arrecadacao", f"total MG {periodo} × BI do CNJ (±{_pct(tol)})", "aviso",
                            int(abs(dif) > tol), f"silver {_mi(v)}; BI {_mi(ref)} ({_pct(dif, True)})"))
    return out


def gravar(con: duckdb.DuckDBPyConnection, checagens: list[Checagem], camada: str) -> pd.DataFrame:
    df = pd.DataFrame([asdict(x) | {"camada": camada} for x in checagens])
    con.execute("CREATE SCHEMA IF NOT EXISTS qualidade")
    con.execute("CREATE TABLE IF NOT EXISTS qualidade.checagens (tabela VARCHAR, checagem VARCHAR, "
                "severidade VARCHAR, violacoes BIGINT, detalhe VARCHAR, camada VARCHAR)")
    con.execute("DELETE FROM qualidade.checagens WHERE camada = ?", [camada])
    con.register("_df", df)
    con.execute("INSERT INTO qualidade.checagens SELECT tabela, checagem, severidade, violacoes, detalhe, camada FROM _df")
    con.unregister("_df")
    return df
