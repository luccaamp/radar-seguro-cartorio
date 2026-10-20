"""Bronze → silver: dados limpos e tipados, com chaves normalizadas (CNS, código IBGE de 7 dígitos).

LGPD (SPEC §6): nome do responsável, substitutos, telefone, e-mail, endereço e denominação fantasia da serventia
são descartados aqui e não chegam ao silver. Da RAIS, só campos agregáveis (microdados já desidentificados).

Cada tabela vai para o schema `silver` do DuckDB e é exportada em Parquet para data/silver/.
"""
import csv
import json
import re
from pathlib import Path

import duckdb
import pandas as pd
import yaml

from src.ingest.comum import BRONZE, RAIZ, sha256_arquivo
from src.transform.normalizar import normalizar_nome, para_float_br

CONFIG = RAIZ / "config"
SILVER = RAIZ / "data" / "silver"
BANCO = RAIZ / "data" / "radar.duckdb"

ATRIBUICOES = {  # natureza no Justiça Aberta -> coluna booleana
    "Notas": "notas",
    "Registro Civil das Pessoas Naturais": "rcpn",
    "Registro de Imóveis": "ri",
    "Registro de Títulos e Documentos": "rtd",
    "Registro Civil das Pessoas Jurídicas": "rcpj",
    "Protesto de Títulos": "protesto",
    "Registro de Contratos Marítimos": "maritimo",
    "Registro de Distribuição": "distribuicao",
    "Registro de Interdições e Tutelas": "interdicoes_tutelas",
}
RAIS_COLUNAS = {
    "Município - Código": "cod_ibge6",
    "Ind Vínculo Ativo 31/12 - Código": "ativo_31_12",
    "Tipo Vínculo - Código": "tipo_vinculo",
    "Tipo Estabelecimento - Nome": "tipo_estabelecimento",
    "Vl Rem Dezembro Nom": "rem_dezembro",
    "Vl Rem Média Nom": "rem_media",
    "Tempo Emprego": "tempo_emprego_meses",
    "Qtd Hora Contr": "horas_contratadas",
    "Mês Admissão - Código": "mes_admissao",
    "Mês Desligamento - Código": "mes_desligamento",
    "CBO 2002 Ocupação - Código": "cbo",
}
TIPOS_VINCULO_INDETERMINADO = {10, 15, 20, 25}  # layout RAIS 2020; D-009
SITUACOES_CNPJ = {"01": "nula", "02": "ativa", "03": "suspensa", "04": "inapta", "08": "baixada"}


def _yaml(nome: str) -> dict:
    return yaml.safe_load((CONFIG / nome).read_text(encoding="utf-8"))


def _do_original(origem_rel: str) -> dict | None:
    """Registro do arquivo original em <bronze>/<fonte>/<snapshot>/original.json (D-032: o original fica fora do
    bronze oficial). `origem_rel` é um arquivo (ex.: susep_ses/2026-10-17/BaseCompleta.zip) ou a pasta (cnpj/2026-10,
    caso em que vale o primeiro original registrado, como no _metadados.json)."""
    p = BRONZE / origem_rel
    pasta, nome = (p.parent, p.name) if p.suffix else (p, None)
    reg = pasta / "original.json"
    if not reg.exists():
        return None
    arqs = json.loads(reg.read_text(encoding="utf-8"))["arquivos"]
    return arqs.get(nome) if nome else next(iter(arqs.values()), None)


def _meta(arquivo: Path) -> dict:
    """Metadados de coleta do arquivo. Padrões: <arq>.meta.json (Fase 1), <stem>.meta.json, original.json (D-032) e
    _metadados.json (Fase 0). Para arquivos filtrados (RAIS, CNPJ, SUSEP), URL e hora de coleta vêm do original:
    do próprio arquivo, se ainda estiver no bronze; senão, do original.json."""
    for cand in (arquivo.with_name(arquivo.name + ".meta.json"), arquivo.with_name(arquivo.stem + ".meta.json")):
        if cand.exists():
            meta = json.loads(cand.read_text(encoding="utf-8"))
            origem_rel = str(meta.get("origem", "")).replace("\\", "/")
            origem = BRONZE / origem_rel
            if not meta.get("url") and meta.get("origem"):
                # arquivo filtrado: URL e hora de COLETA vêm do pacote baixado (C5); o resto fica do filtrado
                if origem.is_file():
                    meta = {**meta, **{k: v for k, v in _meta(origem).items() if k in ("url", "coletado_em")}}
                elif (o := _do_original(origem_rel)) is not None:
                    meta = {**meta, **{k: o[k] for k in ("url", "coletado_em") if k in o}}
            return meta
    for pasta in (arquivo.parent, arquivo.parent.parent):
        reg = pasta / "original.json"
        if reg.exists():
            d = json.loads(reg.read_text(encoding="utf-8"))["arquivos"]
            origem = [k for k in d if arquivo.stem.startswith(Path(k).stem)]  # filtrado -> pacote de origem
            return d.get(arquivo.name) or (d[origem[0]] if origem else next(iter(d.values())))
        m = pasta / "_metadados.json"
        if m.exists():
            d = json.loads(m.read_text(encoding="utf-8"))
            origem = [k for k in d if arquivo.stem.startswith(Path(k).stem)]  # filtrado -> pacote de origem
            return d.get(arquivo.name) or (d[origem[0]] if origem else next(iter(d.values())))
    return {}


def _registrar(fontes: list, fonte: str, arquivo: Path, data_referencia: str, obs: str = "",
               coletado_em: str | None = None) -> None:
    meta = _meta(arquivo)
    if coletado_em and not meta.get("coletado_em"):
        meta["coletado_em"] = coletado_em
    fontes.append({"fonte": fonte, "arquivo": str(arquivo.relative_to(BRONZE)).replace("\\", "/"),
                   "sha256": sha256_arquivo(arquivo), "bytes": arquivo.stat().st_size,
                   "url": meta.get("url"), "coletado_em": meta.get("coletado_em"),
                   "data_referencia": data_referencia, "observacao": obs})


# ---------- leitores (bronze -> DataFrame) ----------

def ler_municipios(snap: str, uf: str, fontes: list) -> pd.DataFrame:
    d = BRONZE / "ibge" / snap
    mun = json.loads((d / f"municipios_{uf}.json").read_text(encoding="utf-8"))
    pop = json.loads((d / f"populacao_{uf}.json").read_text(encoding="utf-8"))[1:]
    pop_por_cod = {int(p["D1C"]): int(p["V"]) for p in pop if p["V"].isdigit()}
    ano_pop = pop[0]["D3N"]
    df = pd.DataFrame([{
        "cod_ibge": m["id"], "cod_ibge6": m["id"] // 10, "uf": uf, "nome": m["nome"],
        "nome_norm": normalizar_nome(m["nome"]),
        "microrregiao": m["microrregiao"]["nome"], "mesorregiao": m["microrregiao"]["mesorregiao"]["nome"],
        "regiao_imediata": m["regiao-imediata"]["nome"],
        "regiao_intermediaria": m["regiao-imediata"]["regiao-intermediaria"]["nome"],
        "populacao": pop_por_cod.get(m["id"]),
        "ano_populacao": int(ano_pop)} for m in mun])
    # nomes de região com erro de grafia na fonte (C4): corrigidos pela tabela versionada, com marcação
    correcoes = _yaml("correcoes_nomes.yaml")
    df["nome_regiao_corrigido_por"] = None
    for coluna in ("regiao_imediata", "regiao_intermediaria"):
        for errado, c in (correcoes.get(coluna) or {}).items():
            alvo = df[coluna] == errado
            df.loc[alvo, coluna] = c["corrigido"]
            df.loc[alvo, "nome_regiao_corrigido_por"] = f"config/correcoes_nomes.yaml ({coluna}: {errado!r})"
    versoes = _yaml("escopo.yaml").get("versoes_dado", {})
    _registrar(fontes, "ibge_municipios", d / f"municipios_{uf}.json", f"vigente em {snap}",
               versoes.get("ibge_municipios", ""))
    _registrar(fontes, "ibge_populacao", d / f"populacao_{uf}.json", ano_pop, "SIDRA tabela 6579, variável 9324")
    _registrar(fontes, "ibge_malha", d / f"malha_{uf}.geojson", versoes.get("ibge_malha", snap),
               "malha municipal do IBGE (API v3); versão conferida por hash (config/escopo.yaml)")
    return df


def ler_malha(snap: str, uf: str) -> pd.DataFrame:
    """Malha municipal do IBGE, um polígono por linha (GeoJSON do feature, na ordem do arquivo). Fica no silver para o
    gold poder ser recalculado só a partir do silver, sem o bronze (D-029). A fonte já é registrada em ler_municipios."""
    malha = json.loads((BRONZE / "ibge" / snap / f"malha_{uf}.geojson").read_text(encoding="utf-8"))
    return pd.DataFrame([{"uf": uf, "ordem": i, "cod_ibge": int(f["properties"]["codarea"]),
                          "feature_json": json.dumps(f, ensure_ascii=False)} for i, f in enumerate(malha["features"])])


def malha_do_silver(con, uf: str | None = None) -> dict:
    """Remonta o GeoJSON da malha a partir de silver.malha_municipio (mesma ordem e mesmos números do arquivo)."""
    filtro, params = ("WHERE uf = ?", [uf]) if uf else ("", [])
    linhas = con.execute(f"SELECT feature_json FROM silver.malha_municipio {filtro} ORDER BY uf, ordem", params).fetchall()
    return {"type": "FeatureCollection", "features": [json.loads(x) for (x,) in linhas]}


def ler_indices(snap: str, fontes: list) -> pd.DataFrame:
    linhas = []
    for indice in ("ipca", "inpc"):
        arq = BRONZE / "ibge" / snap / f"{indice}.json"
        dados = json.loads(arq.read_text(encoding="utf-8"))[1:]
        for d in dados:
            v = para_float_br(d["V"])
            if v is not None:
                linhas.append({"indice": indice.upper(), "ano_mes": int(d["D3C"]), "numero_indice": v})
        ult = max(int(d["D3C"]) for d in dados if para_float_br(d["V"]) is not None)
        _registrar(fontes, f"ibge_{indice}", arq, str(ult), "número-índice, base dez/1993 = 100")
    return pd.DataFrame(linhas)


def _indice_municipio(municipios: pd.DataFrame, uf: str) -> dict[str, int]:
    idx = dict(zip(municipios["nome_norm"], municipios["cod_ibge"]))
    idx.update({k: v for k, v in (_yaml("apelidos_municipios.yaml").get(uf) or {}).items()})
    return idx


def _situacao(s) -> tuple[str | None, str | None]:
    if isinstance(s, dict):
        return s.get("descricao"), s.get("data_decisao")
    return None, None


def ler_serventias(snap: str, uf: str, municipios: pd.DataFrame, fontes: list) -> pd.DataFrame:
    arq = BRONZE / "cnj_justica_aberta" / snap / f"serventias_{uf}.json"
    itens = json.loads(arq.read_text(encoding="utf-8"))["data"]
    idx = _indice_municipio(municipios, uf)
    linhas = []
    for s in itens:  # campos pessoais (responsavel, substitutos, telefone, email, endereco...) não são lidos
        nat = [x.strip() for x in (s.get("natureza") or "").split("|") if x.strip()]
        desc, data = _situacao(s.get("situacao_juridica_cartorio"))
        linha = {"cns": s["cns"], "uf": s["uf"], "cidade_fonte": s["cidade"],
                 "cod_ibge": idx.get(normalizar_nome(s["cidade"])), "status": s["status"],
                 "tipo_cartorio": s["tipo_cartorio"], "situacao_juridica": desc, "data_situacao": data,
                 "atribuicoes": " | ".join(nat), "n_atribuicoes": len(nat)}
        linha.update({col: (rot in nat) for rot, col in ATRIBUICOES.items()})
        desconhecidas = set(nat) - set(ATRIBUICOES)
        if desconhecidas:
            raise ValueError(f"atribuição nova no Justiça Aberta: {desconhecidas}")
        linhas.append(linha)
    _registrar(fontes, "cnj_serventias", arq, snap, "cadastro na data da coleta (autodeclarado)")
    df = pd.DataFrame(linhas)
    df["data_situacao"] = pd.to_datetime(df["data_situacao"], errors="coerce").dt.date
    return df


def ler_colaboradores(snap: str, uf: str, fontes: list) -> pd.DataFrame:
    arq = BRONZE / "cnj_justica_aberta" / snap / f"dados_complementares_{uf}.jsonl"
    regs = {}
    for linha in arq.read_text(encoding="utf-8").splitlines():
        r = json.loads(linha)
        if r.get("status_http") == 200 or r["cns"] not in regs:
            regs[r["cns"]] = r  # a última resposta válida vence
    df = pd.DataFrame([{
        "cns": r["cns"], "informado": r.get("status_http") == 200 and "quantidade_colaboradores_clt" in r,
        "clt": r.get("quantidade_colaboradores_clt"), "estatutarios": r.get("quantidade_colaboradores_estatutarios"),
        "estagiarios": r.get("quantidade_colaboradores_estagiarios"),
        "terceirizados": r.get("quantidade_colaboradores_terceirizados"),
        "total_declarado": r.get("quantidade_total_colaboradores"),
        "informatizada": r.get("informatizada"), "data_coleta": r.get("coletado_em")} for r in regs.values()])
    for c in ("clt", "estatutarios", "estagiarios", "terceirizados", "total_declarado"):
        df[c] = df[c].astype("Int64")
    _registrar(fontes, "cnj_colaboradores", arq, snap, "contagem declarada pela serventia, sem data por serventia",
               coletado_em=str(df["data_coleta"].max()))
    return df


_PERIODO = re.compile(r"De (\d{2})/(\d{2})/(\d{4}) até (\d{2})/(\d{2})/(\d{4})")


def ler_arrecadacoes(snap: str, uf: str, fontes: list) -> pd.DataFrame:
    arq = BRONZE / "cnj_justica_aberta" / snap / f"arrecadacoes_{uf}.jsonl"
    regs = {}
    for linha in arq.read_text(encoding="utf-8").splitlines():
        r = json.loads(linha)
        if r.get("integridade_ok"):
            regs[r["cns"]] = r
    linhas = []
    for r in regs.values():
        for p in r["dados"]:
            m = _PERIODO.fullmatch(p["periodo"].strip())
            if not m:
                raise ValueError(f"período fora do padrão: {p['periodo']!r} (CNS {r['cns']})")
            d1, m1, a1, d2, m2, a2 = map(int, m.groups())
            semestre = 1 if (m1, m2) == (1, 6) else 2 if (m1, m2) == (7, 12) else None
            valor = para_float_br(p["arrecadacao"])
            atos = para_float_br(p.get("atos_praticados"))  # também pode vir "NÃO INFORMADO"
            linhas.append({"cns": r["cns"], "ano": a1, "semestre": semestre,
                           "periodo_inicio": f"{a1}-{m1:02d}-{d1:02d}", "periodo_fim": f"{a2}-{m2:02d}-{d2:02d}",
                           "informado": valor is not None, "arrecadacao": valor,
                           "valor_fonte": None if valor is not None else p["arrecadacao"],
                           "atos_praticados": None if atos is None else int(atos)})
    df = pd.DataFrame(linhas)
    df["atos_praticados"] = df["atos_praticados"].astype("Int64")
    df["semestre"] = df["semestre"].astype("Int64")
    for c in ("periodo_inicio", "periodo_fim"):
        df[c] = pd.to_datetime(df[c]).dt.date
    # A API repete períodos de algumas serventias. Cópias idênticas viram uma linha; valores diferentes
    # para o mesmo período ficam todos, marcados com conflito_fonte (tratamento decidido no gold).
    chave = ["cns", "periodo_inicio", "periodo_fim"]
    df = df.drop_duplicates(subset=chave + ["arrecadacao", "valor_fonte", "atos_praticados"]).reset_index(drop=True)
    df["versoes_fonte"] = df.groupby(chave)["cns"].transform("size")
    df["conflito_fonte"] = df["versoes_fonte"] > 1
    df["versao"] = df.groupby(chave).cumcount() + 1
    ult = df.loc[df["informado"], "periodo_fim"].max()
    ano_classe = _yaml("escopo.yaml")["ano_enquadramento"]
    _registrar(fontes, "cnj_arrecadacao", arq, f"classe: exercício {ano_classe}; série coletada até {ult}",
               f"{len(regs)} serventias com série íntegra")
    return df


def ler_rais(ano: str, uf: str, municipios: pd.DataFrame, fontes: list) -> pd.DataFrame:
    arq = next((BRONZE / "rais" / ano / "extraido").glob(f"*_CNAE6912500_{uf}.csv"))
    with open(arq, encoding="utf-8", newline="") as f:
        rd = csv.reader(f, delimiter=";")
        cab = next(rd)
        idx = {novo: cab.index(orig) for orig, novo in RAIS_COLUNAS.items()}
        linhas = [{novo: row[i] for novo, i in idx.items()} for row in rd]
    df = pd.DataFrame(linhas)
    for c in ("rem_dezembro", "rem_media", "tempo_emprego_meses", "horas_contratadas"):
        df[c] = df[c].map(para_float_br)
    for c in ("cod_ibge6", "ativo_31_12", "tipo_vinculo", "mes_admissao", "mes_desligamento"):
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    df["ativo_31_12"] = df["ativo_31_12"] == 1
    df["prazo_indeterminado"] = df["tipo_vinculo"].isin(TIPOS_VINCULO_INDETERMINADO)
    df = df.merge(municipios[["cod_ibge6", "cod_ibge"]], on="cod_ibge6", how="left").drop(columns="cod_ibge6")
    df.insert(0, "id_vinculo", range(1, len(df) + 1))
    df.insert(1, "ano_base", int(ano))
    _registrar(fontes, "rais_vinculos", arq, f"{ano}-12-31", "vínculos do CNAE 6912-5/00; filtrado do pacote do PDET")
    return df


def ler_cnpj(mes: str, uf: str, municipios: pd.DataFrame, fontes: list) -> pd.DataFrame:
    arq = BRONZE / "cnpj" / mes / "estabelecimentos_cnae6912500.json"
    itens = [s for s in json.loads(arq.read_text(encoding="utf-8")) if s["uf"] == uf]
    idx = _indice_municipio(municipios, uf)
    df = pd.DataFrame([{
        "cnpj_basico": s["cnpj_basico"], "matriz_filial": s["matriz_filial"], "uf": s["uf"],
        "mun_rfb": s["mun_rfb"], "municipio_fonte": s["municipio"],
        "cod_ibge": idx.get(normalizar_nome(s["municipio"])),
        "situacao": SITUACOES_CNPJ.get(s["situacao"], s["situacao"]),
        "cnae_principal": s["cnae_principal"] == "6912500", "natureza_juridica": s["natureza_juridica"],
        "data_inicio": pd.to_datetime(s["data_inicio"], format="%Y%m%d", errors="coerce")} for s in itens])
    df["data_inicio"] = df["data_inicio"].dt.date
    _registrar(fontes, "cnpj_estabelecimentos", arq, mes, "pacote mensal da Receita (SERPRO+)")
    return df


def ler_susep(snap: str, fontes: list) -> pd.DataFrame:
    arq = BRONZE / "susep_ses" / snap / "ses_seguros_garantia.csv"
    df = pd.read_csv(arq, sep=";", dtype=str)
    num = [c for c in df.columns if c not in ("damesano", "coenti", "cogrupo", "coramo")]
    for c in num:
        df[c] = df[c].map(para_float_br)
    df = df.rename(columns={"damesano": "ano_mes", "coenti": "cod_entidade", "cogrupo": "cod_grupo", "coramo": "ramo"})
    df["ano_mes"] = df["ano_mes"].astype(int)
    _registrar(fontes, "susep_ses_garantia", arq, str(df["ano_mes"].max()),
               "ramos 0775 e 0776; valores em R$ (inferido)")
    return df


# ---------- orquestração ----------

def construir(con: duckdb.DuckDBPyConnection | None = None) -> dict[str, int]:
    esc = _yaml("escopo.yaml")
    snaps = esc["snapshots"]
    SILVER.mkdir(parents=True, exist_ok=True)
    fecha = con is None
    con = con or duckdb.connect(str(BANCO))
    con.execute("CREATE SCHEMA IF NOT EXISTS silver")
    fontes: list[dict] = []
    tabelas: dict[str, pd.DataFrame] = {"indice_preco": ler_indices(snaps["ibge"], fontes),
                                        "susep_garantia": ler_susep(snaps["susep_ses"], fontes)}
    partes: dict[str, list] = {k: [] for k in ("municipio_ibge", "serventia", "serventia_colaboradores",
                                               "serventia_arrecadacao", "rais_vinculo", "cnpj_estabelecimento",
                                               "malha_municipio")}
    for uf in esc["ufs"]:
        mun = ler_municipios(snaps["ibge"], uf, fontes)
        partes["municipio_ibge"].append(mun)
        partes["malha_municipio"].append(ler_malha(snaps["ibge"], uf))
        partes["serventia"].append(ler_serventias(snaps["cnj_justica_aberta"], uf, mun, fontes))
        partes["serventia_colaboradores"].append(ler_colaboradores(snaps["cnj_justica_aberta"], uf, fontes))
        partes["serventia_arrecadacao"].append(ler_arrecadacoes(snaps["cnj_arrecadacoes"], uf, fontes))
        partes["rais_vinculo"].append(ler_rais(snaps["rais"], uf, mun, fontes))
        partes["cnpj_estabelecimento"].append(ler_cnpj(snaps["cnpj"], uf, mun, fontes))
    tabelas.update({k: pd.concat(v, ignore_index=True) for k, v in partes.items()})
    tabelas["fonte_metadados"] = pd.DataFrame(fontes)

    contagens = {}
    for nome, df in tabelas.items():
        con.register("_df", df)
        con.execute(f"CREATE OR REPLACE TABLE silver.{nome} AS SELECT * FROM _df")
        con.unregister("_df")
        con.execute(f"COPY silver.{nome} TO '{(SILVER / f'{nome}.parquet').as_posix()}' (FORMAT parquet)")
        contagens[nome] = len(df)
    if fecha:
        con.close()
    return contagens
