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

    @property
    def ok(self) -> bool:
        return self.violacoes == 0


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
        if textos:
            cond = " OR ".join(f"regexp_matches(\"{c}\", '{REGEX_CPF}')" for c in textos)
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
        condicao(con, f"{s}.serventia_colaboradores", "colaboradores informados", "NOT informado", "aviso"),
        condicao(con, f"{s}.serventia_colaboradores", "CNS existe no cadastro",
                 f"cns NOT IN (SELECT cns FROM {s}.serventia)"),
        chave_unica(con, f"{s}.serventia_arrecadacao", "cns, periodo_inicio, periodo_fim, versao"),
        condicao(con, f"{s}.serventia_arrecadacao", "período com valores conflitantes na fonte",
                 "conflito_fonte", "aviso"),
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
    return c + sem_dados_pessoais(con, s)


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
