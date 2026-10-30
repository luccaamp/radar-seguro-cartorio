"""Análises do painel (Etapa 3), no formato das ferramentas do chat (src/agent/ferramentas.py), para a Etapa 5.

Cada função recebe a conexão só de leitura do painel (banco do pipeline ou banco de demonstração) e a UF, lê as
tabelas públicas (`config/publico.yaml`) ou a saída gravada de um notebook (src/painel/artefatos.py) e devolve um
dicionário com:
- os valores já formatados em pt-BR (o que o chat copia e o painel mostra);
- `conta`: como o número sai das tabelas; `rotulo`: o rótulo da D-042 ("faixa provável", "projeção",
  "sensibilidade", "extremos teóricos" ...) quando houver;
- `fonte`, `data_referencia`, `versao_premissas` e `citar` (a mesma linha "Fonte: ..." das ferramentas do chat);
- `valores` (números crus, para gráficos e testes) e, quando houver, `tabela` (lista de linhas, para gráfico e
  download). Tudo serializável em JSON (tipos do Python).
As páginas só exibem o que estas funções devolvem; nada é recalculado nem digitado nas páginas.
"""
import math
import re
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import yaml

from src import estado
from src.agent.ferramentas import _br, _citar, _sem_uf, _uf, aprox, brl, pct
from src.painel import artefatos

RAIZ = Path(__file__).resolve().parents[2]

# rótulos da D-042 (docs/decisoes.md), escritos uma vez só
FAIXA = "faixa provável (P5–P95)"
FAIXA_SUB = "faixa dentro das suposições"
EXTREMOS = "extremos teóricos (todas as suposições no limite ao mesmo tempo)"
PROJECAO = "projeção"
SENSIBILIDADE = "sensibilidade"
LEITURA_LITERAL = ("leitura literal do art. 2º, XXIV (aproximada: o repasse do BI cobre só o inciso XXVI; o inciso XXV "
                   "não tem fonte, então mais serventias sairiam)")
BLOCO_PASSIVO = "Passivo: escolhas de método"
NOTA_CANTOS_MC = ("O Monte Carlo segura o passivo no nível base, por isso os cantos dele ({mc}) são outros que os "
                  "extremos teóricos oficiais.")
MEDIDAS_D042 = {"deficit": ("valor_descoberto", "Déficit de cobertura"),
                "importancia_segurada": ("mercado_importancia_segurada", "Importância segurada (IS) do mercado"),
                "premio": ("mercado_premio_emitido", "Prêmio anual do mercado")}
FONTES_MODELO = ("cnj_serventias", "cnj_colaboradores", "cnj_arrecadacao", "rais_vinculos")


def config() -> dict:
    return yaml.safe_load((RAIZ / "config" / "painel.yaml").read_text(encoding="utf-8"))


def _py(v):
    """Número do numpy/pandas → tipo do Python (JSON); vazio → None."""
    if v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NA:
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return None if np.isnan(v) else float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def _linhas(df: pd.DataFrame) -> list[dict]:
    return [{k: _py(v) for k, v in r.items()} for r in df.to_dict("records")]


def _meta(con, tabela: str, fontes=FONTES_MODELO, rotulo: str | None = None) -> dict:
    """Fonte, data de referência, carga e versão das premissas de um resultado."""
    versao, executado = con.execute("SELECT versao_premissas, executado_em FROM gold.execucao "
                                    "WHERE regra_classe = 'v2'").fetchone()
    refs = con.execute("SELECT fonte, data_referencia FROM silver.fonte_metadados WHERE fonte IN (SELECT unnest(?)) "
                       "ORDER BY fonte", [list(fontes)]).fetchall()
    out = {"fonte": tabela, "data_referencia": "; ".join(f"{f}: {d}" for f, d in refs),
           "carga": f"{executado:%Y-%m-%d}", "versao_premissas": int(versao), "citar": _citar(con, tabela)}
    if rotulo:
        out["rotulo"] = rotulo
    return out


def _uf_mercado(con, cenario: str = "mantem") -> pd.DataFrame:
    return con.execute("SELECT * FROM gold.fato_mercado_uf WHERE regra_classe = 'v2' AND cenario_stf = ?",
                       [cenario]).df().set_index("nivel")


def _faixa_txt(lo: float, hi: float) -> str:
    """'R$ 215 mil a R$ 687 mil': a faixa arredondada da D-042 (sem casas em mil; uma casa em mi)."""
    def curto(v):
        a = abs(v)
        if 1e3 <= a < 1e6:
            return f"R$ {_br(v / 1e3, 0)} mil"
        return brl(v)
    return f"{curto(lo)} a {curto(hi)}"


# ------------------------------------------------------------------ Início
OFICIAIS = [  # (chave, coluna do gold, rótulo, formato, natureza)
    ("serventias", "n_serventias_ativas", "Serventias ativas", "num", "dado"),
    ("clt", "clt", "Empregados CLT", "num", "dado"),
    ("obrigadas", "n_universo", "Obrigadas pelo Prov. 227", "aprox", "dado"),
    ("passivo_todas", "passivo_todas", "Passivo trabalhista (todas)", "brl", "dado"),
    ("passivo_obrigadas", "passivo_universo", "Passivo trabalhista (obrigadas)", "brl", "dado"),
    ("com_deficit", "n_deficit", "Com déficit (esperado)", "aprox", "suposição"),
    ("deficit", "valor_descoberto", "Déficit de cobertura", "brl", "suposição"),
    ("importancia_segurada", "mercado_importancia_segurada", "IS do mercado", "brl", "suposição"),
    ("premio", "mercado_premio_emitido", "Prêmio anual do mercado", "brl", "suposição"),
    ("teto", None, "Teto teórico do prêmio", "brl", "suposição"),
]
_FMT = {"num": lambda v: _br(v, 0), "aprox": aprox, "brl": brl}


def numeros_oficiais(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Os 10 números oficiais de MG (regra v2, nível base, STF "mantém"), com o mínimo e o máximo dos cantos das
    premissas. O teto teórico é o passivo das obrigadas × a taxa do nível (como se ninguém tivesse bens)."""
    if not _uf(uf):
        return _sem_uf(uf)
    f = _uf_mercado(con)
    taxa = estado.premissas_vigentes(con)[0]["premissas"]["taxa_seguro_anual"]["valores"]
    linhas = []
    for i, (chave, col, rotulo, fmt, natureza) in enumerate(OFICIAIS, start=1):
        v = {n: (float(f.at[n, "passivo_universo"]) * float(taxa[n]) if col is None else float(f.at[n, col]))
             for n in ("min", "base", "max")}
        linhas.append({"numero": i, "chave": chave, "rotulo": rotulo, "natureza": natureza,
                       "valor": _FMT[fmt](v["base"]), "minimo": _FMT[fmt](v["min"]), "maximo": _FMT[fmt](v["max"]),
                       "base_cru": v["base"], "min_cru": v["min"], "max_cru": v["max"]})
    return {"uf": "MG", "numeros": linhas,
            "conta": "gold.fato_mercado_uf (regra v2, cenário 'mantém'); teto = passivo das obrigadas × taxa do nível",
            "observacao": "1 a 5 vêm de dados públicos; 6 a 10 dependem de suposições (D-016, D-046)",
            "valores": {r["chave"]: r["base_cru"] for r in linhas}, "tabela": linhas,
            **_meta(con, "gold.fato_mercado_uf")}


def faixa_d042(con: duckdb.DuckDBPyConnection, uf: str = "MG", medida: str = "premio") -> dict:
    """D-042 para o déficit, a IS ou o prêmio: valor base > faixa provável P5–P95 (Monte Carlo, suposições
    independentes) > extremos teóricos oficiais (todas as premissas no mínimo ou no máximo) > sensibilidade "patrimônio
    junto". Faixa e sorteios de gold.analise_monte_carlo; base e extremos de gold.fato_mercado_uf."""
    if not _uf(uf):
        return _sem_uf(uf)
    if medida not in MEDIDAS_D042:
        return {"erro": f"medida {medida!r} não existe; use {list(MEDIDAS_D042)}"}
    col, titulo = MEDIDAS_D042[medida]
    mc = con.execute("SELECT * FROM gold.analise_monte_carlo WHERE medida = ?", [medida]).df().set_index("variante")
    ind, junto = mc.loc["independentes"], mc.loc["patrimônio junto"]
    f = _uf_mercado(con)
    base, lo, hi = float(f.at["base", col]), float(f.at["min", col]), float(f.at["max", col])
    p05, p50, p95 = float(ind["p05"]), float(ind["p50"]), float(ind["p95"])
    return {"uf": "MG", "medida": titulo, "valor_base": brl(base), "faixa_provavel": _faixa_txt(p05, p95),
            "faixa_provavel_exata": f"{brl(p05)} a {brl(p95)}", "rotulo_faixa": FAIXA, "subrotulo_faixa": FAIXA_SUB,
            "extremos": f"{brl(lo)} a {brl(hi)}", "rotulo_extremos": EXTREMOS,
            "mediana_sorteios": brl(p50), "sorteios": _br(int(ind["n_sorteios"]), 0),
            "nota_mediana": (f"O valor base ({brl(base)}) fica abaixo da mediana dos sorteios ({brl(p50)}): as faixas das "
                             "suposições são mais longas para cima." if base < p50 else
                             f"Mediana dos sorteios: {brl(p50)}."),
            "nota_cantos_mc": NOTA_CANTOS_MC.format(mc=f"{brl(float(ind['canto_min']))} a {brl(float(ind['canto_max']))}"),
            "sensibilidade_patrimonio_junto": f"{brl(float(junto['p05']))} a {brl(float(junto['p95']))}",
            "conta": (f"P5 e P95 de {int(ind['n_sorteios']):,} sorteios triangulares (mín., base, máx.) das suposições "
                      f"dos passos 5 a 8, semente {int(ind['semente'])}; extremos = nível mínimo e máximo do "
                      "gold.fato_mercado_uf").replace(",", "."),
            "valores": {"base": base, "p05": p05, "p25": float(ind["p25"]), "p50": p50, "p75": float(ind["p75"]),
                        "p95": p95, "media": float(ind["media"]), "extremo_min": lo, "extremo_max": hi,
                        "canto_mc_min": float(ind["canto_min"]), "canto_mc_max": float(ind["canto_max"]),
                        "base_mc": float(ind["valor_base"]), "junto_p05": float(junto["p05"]),
                        "junto_p95": float(junto["p95"]), "largura_vezes": (hi - lo) / (p95 - p05)},
            **_meta(con, "gold.analise_monte_carlo e gold.fato_mercado_uf", rotulo=FAIXA)}


def escada(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Do passivo ao prêmio (achado 1 do 09): cada degrau é uma parte do anterior, em % do passivo das obrigadas."""
    if not _uf(uf):
        return _sem_uf(uf)
    n = numeros_oficiais(con, uf)["valores"]
    ref = n["passivo_obrigadas"]
    degraus = [("Passivo de todas as serventias", "passivo_todas", "dado"),
               ("Passivo das obrigadas", "passivo_obrigadas", "dado"),
               ("Déficit (sem bens que cubram)", "deficit", "suposição"),
               ("IS do mercado (vira seguro)", "importancia_segurada", "suposição"),
               ("Prêmio anual do mercado", "premio", "suposição")]
    linhas = [{"degrau": d, "valor": n[k], "valor_txt": brl(n[k]), "pct_passivo_obrigadas": n[k] / ref,
               "pct_txt": pct(n[k] / ref), "natureza": nat} for d, k, nat in degraus]
    return {"uf": "MG", "premio_sobre_teto": pct(n["premio"] / n["teto"]),
            "is_sobre_passivo": pct(n["importancia_segurada"] / ref), "deficit_sobre_passivo": pct(n["deficit"] / ref),
            "conta": "degraus 4 a 8 da escada no nível base; % do passivo das obrigadas",
            "valores": {"premio_sobre_teto": n["premio"] / n["teto"], "teto": n["teto"]}, "tabela": linhas,
            **_meta(con, "gold.fato_mercado_uf")}


def situacao_adi() -> dict:
    """Situação da ADI 8015 (STF) e a data da conferência, de config/painel.yaml."""
    a = config()["adi_8015"]
    return {"situacao": " ".join(a["situacao"].split()), "liminar": "não" if not a["liminar"] else "sim",
            "conferido_em": pd.Timestamp(a["conferido_em"]).strftime("%d/%m/%Y"),
            "citar": f"Fonte: {' '.join(a['fonte'].split())}. Não é parecer jurídico.",
            "fonte": "config/painel.yaml (adi_8015)"}


def premio_por_cenario_stf(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Prêmio base e faixa provável em cada cenário do STF (M7): mantém, decisão parcial (hipotética) e suspende."""
    if not _uf(uf):
        return _sem_uf(uf)
    c = con.execute("SELECT * FROM gold.analise_premio_cenarios").df()
    nomes = {"mantem": "Regra mantida", "parcial": "Decisão parcial (hipotética)", "suspende_8_17": "STF suspende os arts. 8º a 17"}
    linhas = [{"cenario": r.cenario, "nome": nomes.get(r.cenario, r.cenario), "fracao_exigida": float(r.fracao_exigida),
               "premio_base": float(r.premio_base), "p05": float(r.premio_p05), "p95": float(r.premio_p95),
               "premio_txt": brl(r.premio_base), "faixa_txt": _faixa_txt(r.premio_p05, r.premio_p95)
               if r.premio_p95 > 0 else "—", "descricao": " ".join(str(r.descricao).split())}
              for r in c.itertuples()]
    return {"uf": "MG", "cenarios": {r["cenario"]: f"{r['premio_txt']} (faixa provável {r['faixa_txt']})"
                                     for r in linhas},
            "conta": "prêmio do cenário = prêmio da regra mantida × fração exigida (config/cenarios_stf.yaml)",
            "observacao": "o efeito do STF é binário e fica fora da faixa provável; 'parcial' é hipotético",
            "tabela": linhas, **_meta(con, "gold.analise_premio_cenarios", rotulo=FAIXA)}


# ------------------------------------------------------------------ Mercado
def grupos(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Os seis tipos de cartório do k-means (notebook 04) e o grupo-alvo do seguro, com a parte de MG de cada um."""
    if not _uf(uf):
        return _sem_uf(uf)
    g = con.execute("SELECT * FROM gold.analise_grupos_perfil ORDER BY grupo").df()
    linhas = _linhas(g)
    alvo = g[g["grupo_alvo"]].iloc[0]
    return {"uf": "MG", "grupo_alvo": f"grupo {int(alvo.grupo)}: {alvo.nome_grupo}",
            "serventias_do_alvo": _br(alvo.n_serventias, 0), "parte_das_serventias": pct(alvo.pct_serventias),
            "parte_das_obrigadas": pct(alvo.pct_obrigadas_mg),
            "parte_do_passivo_das_obrigadas": pct(alvo.pct_passivo_obrigadas_mg),
            "parte_do_deficit": pct(alvo.pct_deficit_mg), "deficit_por_obrigada": brl(alvo.deficit_por_obrigada),
            "conta": "k-means em escala log (receita, CLT, nº de atribuições, situação; notebook 04); partes de MG "
                     "somadas por grupo",
            "observacao": "passivo = dado; déficit = pela capacidade de pagar (premissas v3, D-046)",
            "valores": {"alvo": int(alvo.grupo)}, "tabela": linhas, **_meta(con, "gold.analise_grupos_perfil")}


ATRIBUICOES_09 = {"Notas": "Notas", "Registro Civil das Pessoas Naturais": "RCPN", "Registro de Imóveis": "RI",
                  "Registro de Títulos e Documentos": "RTD", "Registro Civil das Pessoas Jurídicas": "RCPJ",
                  "Protesto de Títulos": "Protesto"}
PORTES = [(0, 0, "0 CLT"), (1, 2, "1 a 2 CLT"), (3, 9, "3 a 9 CLT"), (10, math.inf, "10+ CLT")]


def quem_e_obrigado(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Que parte das serventias de classe conhecida é obrigada, por atribuição e por porte (notebook 03), e as três
    regras de associação mais fortes (gold.analise_regras)."""
    if not _uf(uf):
        return _sem_uf(uf)
    s = con.execute("SELECT atribuicoes, clt, peso_universo FROM gold.serventia_publico "
                    "WHERE classe IN ('1', '2', '3')").df()
    s["obrigada"] = s["peso_universo"] > 0
    linhas = []
    for nome, curto in ATRIBUICOES_09.items():
        m = s["atribuicoes"].fillna("").str.split(" | ", regex=False).map(lambda a, n=nome: n in a)
        linhas.append({"tipo": "atribuição", "item": curto, "serventias": int(m.sum()),
                       "obrigadas": int(s.loc[m, "obrigada"].sum()), "pct": float(s.loc[m, "obrigada"].mean())})
    for lo, hi, rot in PORTES:
        m = s["clt"].between(lo, hi)   # sem CLT declarado fica fora do porte, como no notebook 09
        linhas.append({"tipo": "porte", "item": rot, "serventias": int(m.sum()),
                       "obrigadas": int(s.loc[m, "obrigada"].sum()), "pct": float(s.loc[m, "obrigada"].mean())})
    regras = con.execute("SELECT se, entao, serventias_com_se, confianca, lift FROM gold.analise_regras "
                         "ORDER BY posicao LIMIT 3").df()
    media = float(s["obrigada"].mean())
    return {"uf": "MG", "media_obrigadas": pct(media), "serventias_classe_conhecida": _br(len(s), 0),
            "por_item": {r["item"]: pct(r["pct"]) for r in linhas},
            "regras": [f"{r.se} → {r.entao}: acerta {pct(r.confianca)} de {_br(r.serventias_com_se, 0)} (lift "
                       f"{_br(r.lift, 2)})" for r in regras.itertuples()],
            "conta": "obrigada = peso no universo > 0 (provida e Classe 2 ou 3), entre as serventias de classe conhecida",
            "observacao": "descrição de 2025, não previsão; as 78 de classe indeterminada ficam fora",
            "valores": {"media": media}, "tabela": linhas,
            **_meta(con, "gold.serventia_publico e gold.analise_regras")}


# ------------------------------------------------------------------ Análises
def concentracao(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Gini e a parte dos 10% maiores no passivo das obrigadas (dado) e no déficit esperado (suposição), com a curva
    de Lorenz (a mesma conta de src/analise/conclusoes.concentracao, sobre gold.serventia_publico)."""
    if not _uf(uf):
        return _sem_uf(uf)
    from src.analise import estatistica as est
    topo = float(yaml.safe_load((RAIZ / "config" / "analise.yaml").read_text(encoding="utf-8"))
                 ["sensibilidade"]["topo_concentracao"])
    s = con.execute("SELECT passivo, peso_universo, valor_descoberto FROM gold.serventia_publico "
                    "WHERE peso_universo > 0").df()
    series = {"passivo das obrigadas": s["passivo"] * s["peso_universo"], "déficit esperado": s["valor_descoberto"]}
    medidas, curvas = [], []
    for nome, serie in series.items():
        g, parte = est.gini(serie), est.participacao_topo(serie, topo)
        medidas.append({"medida": nome, "gini": g, "parte_do_topo": parte})
        lz = est.curva_lorenz(serie)
        idx = np.unique(np.linspace(0, len(lz) - 1, 201).round().astype(int))
        curvas += [{"medida": nome, "fracao_unidades": float(a), "fracao_valor": float(b)}
                   for a, b in lz.iloc[idx][["fracao_unidades", "fracao_valor"]].to_numpy()]
    m = {r["medida"]: r for r in medidas}
    return {"uf": "MG", "gini_passivo": _br(m["passivo das obrigadas"]["gini"], 2),
            "parte_dos_maiores_no_passivo": pct(m["passivo das obrigadas"]["parte_do_topo"]),
            "gini_deficit": _br(m["déficit esperado"]["gini"], 2),
            "parte_dos_maiores_no_deficit": pct(m["déficit esperado"]["parte_do_topo"]),
            "topo": f"{_br(100 * topo, 0)}%", "serventias": _br(len(s), 0),
            "explicacao": "O índice de Gini vai de 0 (todos os cartórios com o mesmo valor) a 1 (tudo num cartório só).",
            "conta": "Gini = dobro da área entre a igualdade e a curva de Lorenz; serventias com peso no universo",
            "valores": {"gini_passivo": m["passivo das obrigadas"]["gini"],
                        "topo_passivo": m["passivo das obrigadas"]["parte_do_topo"],
                        "gini_deficit": m["déficit esperado"]["gini"],
                        "topo_deficit": m["déficit esperado"]["parte_do_topo"], "topo": topo, "n": len(s)},
            "tabela": medidas, "curva": curvas, **_meta(con, "gold.serventia_publico")}


def tornado(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Sensibilidade do prêmio a cada suposição, uma por vez do mínimo ao máximo (D-042, notebook 08)."""
    if not _uf(uf):
        return _sem_uf(uf)
    t = con.execute("SELECT * FROM gold.analise_tornado ORDER BY ordem").df()
    soma = float(t["amplitude"].sum())
    duas = float(t["amplitude"].iloc[:2].sum()) / soma
    passivo_max = float((t.loc[t["grupo"] == "passivo e universo", "amplitude"].max()) / t["premio_base"].iloc[0])
    linhas = _linhas(t)
    return {"uf": "MG", "premio_base": brl(float(t["premio_base"].iloc[0])),
            "mais_pesam": [f"{r.rotulo}: {brl(min(r.premio_no_min, r.premio_no_max))} a "
                           f"{brl(max(r.premio_no_min, r.premio_no_max))}" for r in t.head(3).itertuples()],
            "parte_das_duas_primeiras": pct(duas), "passivo_e_universo_no_maximo": pct(passivo_max),
            "conta": "cada suposição sozinha no mínimo e no máximo, as outras no base; amplitude = prêmio no máx. − no mín.",
            "valores": {"duas_primeiras": duas, "passivo_max": passivo_max}, "tabela": linhas,
            **_meta(con, "gold.analise_tornado", rotulo=SENSIBILIDADE)}


def grade_taxa_adesao(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Prêmio numa grade de taxa × parte do déficit que escolhe seguro (M8): a taxa não tem fonte pública."""
    if not _uf(uf):
        return _sem_uf(uf)
    g = con.execute("SELECT * FROM gold.analise_premio_grade ORDER BY adesao, taxa").df()
    return {"uf": "MG", "de": brl(g["premio"].min()), "ate": brl(g["premio"].max()),
            "observacao": "a SES da SUSEP não publica a importância segurada; a taxa média não sai dela (M8)",
            "conta": "prêmio = IS da base × (adesão ÷ adesão base) × taxa", "tabela": _linhas(g),
            **_meta(con, "gold.analise_premio_grade", rotulo=SENSIBILIDADE)}


def previsao_arrecadacao(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Arrecadação semestral de MG prevista para 2026–27 (tendência do T2, notebook 07), com P10–P90, e o 2026-1
    realizado (parcial). Sempre projeção."""
    if not _uf(uf):
        return _sem_uf(uf)
    var = config()["projecao"]["variante_principal"].replace(" (principal)", "")
    p = con.execute("SELECT * FROM gold.analise_previsao WHERE bloco = 'arrecadacao_mg' ORDER BY variante, periodo").df()
    principal = p[p["variante"].str.startswith(var) & p["variante"].str.contains("principal")]
    anual = principal.assign(ano=principal["periodo"].str[:4]).groupby("ano")[["p10", "central", "p90"]].sum()
    real = principal.dropna(subset=["realizado"])
    acima = [f"{r.periodo}: realizado {brl(r.realizado)} contra P90 de {brl(r.p90)}" for r in real.itertuples()
             if r.realizado > r.p90]
    return {"uf": "MG", "rotulo": PROJECAO,
            "por_ano": {a: f"{brl(r.central)} (soma dos P10 e P90 dos semestres: {brl(r.p10)} a {brl(r.p90)})"
                        for a, r in anual.iterrows()},
            "realizado_acima_do_p90": acima,
            "observacao": ("o 2026-1 realizado é parcial (serventias ainda sem informar na coleta de 18/10) e já passou "
                           "do P90: a projeção principal tende a ser conservadora") if acima else "",
            "conta": "tendência log-linear com efeito de semestre, treinada até 2025-2 (teste T2, MAPE 7,4%); faixa "
                     "P10–P90 dos erros do teste no passado",
            "valores": {a: float(r.central) for a, r in anual.iterrows()},
            "tabela": _linhas(p[["variante", "periodo", "p10", "central", "p90", "realizado"]]),
            **_meta(con, "gold.analise_previsao", fontes=("cnj_arrecadacao",), rotulo=PROJECAO)}


MEDIDAS_PROJ = {"n_universo": ("Obrigadas", aprox), "subidas": ("Subidas da Classe 1 para a 2", aprox),
                "mercado_premio_emitido": ("Prêmio anual", brl), "passivo_universo": ("Passivo das obrigadas", brl),
                "valor_descoberto": ("Déficit", brl), "mercado_importancia_segurada": ("IS do mercado", brl)}


def previsao_mercado(con: duckdb.DuckDBPyConnection, uf: str = "MG", ano: int = 2027,
                     leitura_limite: str | None = None) -> dict:
    """Universo, subidas, passivo, déficit, IS e prêmio projetados para `ano` (notebook 07), na leitura do limite
    escolhida (principal: config/painel.yaml) e na outra, como comparação. Passivo de cada serventia fixo no de 2025."""
    if not _uf(uf):
        return _sem_uf(uf)
    cfg = config()["projecao"]
    principal = leitura_limite or cfg["leitura_limite_principal"]
    leituras = [cfg["leitura_limite_principal"], cfg["leitura_limite_comparacao"]]
    if principal not in leituras:
        return {"erro": f"leitura do limite {leitura_limite!r} não existe; use {leituras}"}
    outra = leituras[1 - leituras.index(principal)]
    p = con.execute("SELECT * FROM gold.analise_previsao WHERE bloco = 'mercado' AND variante = ?",
                    [cfg["variante_principal"]]).df()
    if str(ano) not in set(p["periodo"]):
        return {"erro": f"ano {ano} fora da projeção; use {sorted(set(p['periodo']))}"}
    base = _uf_mercado(con).loc["base"]

    def leitura(c):
        d = p[(p["periodo"] == str(ano)) & (p["cenario_limite"] == c)].set_index("medida")
        return {m: {"central": float(d.at[m, "central"]), "p10": float(d.at[m, "p10"]), "p90": float(d.at[m, "p90"]),
                    "txt": f"{fmt(d.at[m, 'central'])} (P10–P90 {fmt(d.at[m, 'p10'])} a {fmt(d.at[m, 'p90'])})"}
                for m, (_, fmt) in MEDIDAS_PROJ.items()}
    a, b = leitura(principal), leitura(outra)
    serie = p[p["medida"].isin(["n_universo", "mercado_premio_emitido"])]
    m5 = passivo_m5()
    return {"uf": "MG", "ano": ano, "rotulo": PROJECAO, "leitura_do_limite": principal, "comparacao": outra,
            "principal": {MEDIDAS_PROJ[m][0]: v["txt"] for m, v in a.items()},
            "na_comparacao": {MEDIDAS_PROJ[m][0]: v["txt"] for m, v in b.items()},
            "diferenca_obrigadas": _br(a["n_universo"]["central"] - b["n_universo"]["central"], 0),
            "base_2025": {"Obrigadas": aprox(base["n_universo"]), "Prêmio anual": brl(base["mercado_premio_emitido"])},
            "nota_passivo": ("O passivo de cada serventia fica o de 2025; com o passivo de cada ano (M5, notebook 10), "
                             f"o passivo das obrigadas seria {m5['texto']}, e o prêmio subiria na mesma proporção."
                             if "texto" in m5 else ""),
            "conta": "receita de 2025 × crescimento projetado de MG × desvio sorteado da serventia (500 sorteios); "
                     "modelo refeito com a receita de cada ano",
            "valores": {"principal": a, "comparacao": b, "base_2025": {"n_universo": float(base["n_universo"]),
                                                                       "premio": float(base["mercado_premio_emitido"])}},
            "tabela": _linhas(serie[["periodo", "cenario_limite", "medida", "p10", "central", "p90"]]),
            **_meta(con, "gold.analise_previsao", rotulo=PROJECAO)}


def passivo_m5() -> dict:
    """Fator do passivo das obrigadas em 2026 e 2027 sobre 2025 (M5, notebook 10): mesmos vínculos, tempo de casa
    + 12 meses por ano e salário corrigido pelo INPC. Lido da saída gravada do notebook."""
    a = config()["artefatos"]["passivo_m5"]
    try:
        t = artefatos.tabela_do_notebook(a["notebook"], a["marcador"])
    except (LookupError, OSError):
        return {"erro": "saída da M5 não encontrada no notebook 10"}
    t["ano"] = t["ano"].map(artefatos.numero_br).astype(int)
    fator = dict(zip(t["ano"], t["fator sobre 2025"].map(artefatos.numero_br)))
    anos = [x for x in sorted(fator) if fator[x] != 1]
    return {"fator": {int(x): float(fator[x]) for x in anos},
            "texto": " e ".join(f"{pct(fator[x] - 1)} maior em {x}" for x in anos),
            "fonte": f"{a['notebook']} (M5)"}


def subidas_comparacao(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Subidas da Classe 1 para a 2 em 2026: a projeção principal do 07 (com P10–P90) e, como comparação, a faixa do
    05b com as duas leituras (sem e com a recalibração de Platt; D-047), lidas da saída gravada do notebook 05."""
    if not _uf(uf):
        return _sem_uf(uf)
    cfg = config()
    a = cfg["artefatos"]["subidas_05b"]
    p = con.execute("SELECT * FROM gold.analise_previsao WHERE bloco = 'mercado' AND variante = ? AND medida = 'subidas' "
                    "AND periodo = ?", [cfg["projecao"]["variante_principal"], str(a["ano"])]).df()
    p = p.set_index("cenario_limite")
    pr, co = cfg["projecao"]["leitura_limite_principal"], cfg["projecao"]["leitura_limite_comparacao"]
    t = artefatos.tabela_do_notebook(a["notebook"], a["marcador"])
    t = t[(t["ano"].map(artefatos.numero_br) == a["ano"]) & (t["recorte"] == a["recorte"])]
    b5 = {r.modelo: {"esperado": artefatos.numero_br(r.esperado), "p10": artefatos.numero_br(r.p10),
                     "p90": artefatos.numero_br(r.p90)} for r in t.itertuples()}
    lo, hi = min(v["esperado"] for v in b5.values()), max(v["esperado"] for v in b5.values())
    return {"uf": "MG", "ano": a["ano"], "rotulo": PROJECAO,
            "notebook_07": f"{aprox(p.at[pr, 'central'])} ({pr}; P10–P90 {aprox(p.at[pr, 'p10'])} a {aprox(p.at[pr, 'p90'])})",
            "notebook_07_comparacao": f"{aprox(p.at[co, 'central'])} ({co})",
            "notebook_05b": f"{_br(lo, 0)} a {_br(hi, 0)} subidas (sem e com a recalibração; comparação)",
            "observacao": "a evidência é dividida: a recalibração acerta mais em 2024–25 e erra mais na média da origem "
                          "móvel; por isso o 05b aparece como faixa, nunca só uma das leituras (D-047)",
            "conta": "07: contagem acima do limite na projeção por serventia; 05b: soma das probabilidades da floresta",
            "valores": {"07": {c: {k: float(p.at[c, k]) for k in ("p10", "central", "p90")} for c in (pr, co)},
                        "05b": b5, "05b_faixa": [lo, hi]},
            **_meta(con, f"gold.analise_previsao e {a['notebook']} (tabela 'entrega')", fontes=("cnj_arrecadacao",),
                    rotulo=PROJECAO)}


def pergunta_9(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """A seguradora tem lucro? Sinistro por frequência × severidade (M2): P(fim da delegação no ano) de 2%, 4% e 7,5%
    (notebook 05c) e a parte da IS que o titular não paga, com e sem a capacidade de pagar (M1)."""
    if not _uf(uf):
        return _sem_uf(uf)
    s = con.execute("SELECT * FROM gold.analise_sinistro").df()
    com, sem = s[s["leitura"].str.startswith("com")], s[s["leitura"].str.startswith("sem")]
    return {"uf": "MG",
            "com_a_capacidade_de_pagar": (f"sinistralidade de {pct(com['sinistralidade'].min())} a "
                                          f"{pct(com['sinistralidade'].max())}; resultado técnico de "
                                          f"{brl(com['resultado_tecnico'].min())} a {brl(com['resultado_tecnico'].max())} por ano"),
            "sem_a_capacidade_de_pagar": (f"índice combinado de {pct(sem['indice_combinado'].min())} a "
                                          f"{pct(sem['indice_combinado'].max())}: prejuízo em qualquer P(fim)"),
            "p_fim": " / ".join(pct(v) for v in sorted(s["p_fim"].unique())),
            "conta": "sinistralidade = P(fim) × parte da IS que vira sinistro ÷ taxa; índice combinado = sinistralidade "
                     "+ comissão + despesa",
            "observacao": "renda não é patrimônio; a P(fim) tem viés de sobrevivência (05c); sem impostos, resseguro "
                          "e capital",
            "tabela": _linhas(s), **_meta(con, "gold.analise_sinistro", rotulo=SENSIBILIDADE)}


def capacidade_pagar(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Capacidade de pagar (M1): obrigadas por meses de saldo para cobrir o passivo e a calibração por classe."""
    if not _uf(uf):
        return _sem_uf(uf)
    fx = con.execute("SELECT * FROM gold.analise_capacidade_faixas").df()
    cal = con.execute("SELECT * FROM gold.analise_capacidade_calibracao ORDER BY horizonte_meses, faixa_deficit").df()
    return {"uf": "MG", "conta": "meses de saldo (arrecadação − repasse − custeio, BI do CNJ, 2025) para pagar o passivo",
            "observacao": "o horizonte de 12 meses de saldo é suposição (6 e 24 como sensibilidade)",
            "tabela": _linhas(fx), "calibracao": _linhas(cal),
            **_meta(con, "gold.analise_capacidade_faixas e gold.analise_capacidade_calibracao")}


# ------------------------------------------------------------------ Qualidade dos dados
def _sens_metodo(con) -> pd.DataFrame:
    return con.execute("SELECT * FROM gold.analise_sensibilidade_metodo").df().set_index("chave")


def escolhas_metodo_passivo(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Bloco "Passivo: escolhas de método" da D-042: T5, T6 e a reserva no estado inteiro, no passivo de todas."""
    if not _uf(uf):
        return _sem_uf(uf)
    s = _sens_metodo(con)
    b = s[s["bloco"] == "passivo: escolhas de método"]
    lo, hi = float(b["var_passivo_todas"].min()), float(b["var_passivo_todas"].max())
    reserva = b["var_passivo_todas"].abs().idxmax()
    linhas = [{"chave": k, "rotulo": r.rotulo, "efeito_passivo": float(r.var_passivo_todas),
               "efeito_txt": f"{'+' if r.var_passivo_todas > 0 else ''}{pct(r.var_passivo_todas)}",
               "passivo_todas": float(r.passivo_todas), "efeito_premio": float(r.var_mercado_premio_emitido)}
              for k, r in b.iterrows()]
    sinal = lambda v: f"{'+' if v > 0 else ''}{pct(v)}"  # noqa: E731
    return {"uf": "MG", "bloco": BLOCO_PASSIVO,
            "frase": (f"o passivo varia de {sinal(lo)} a {sinal(hi)} conforme o método; "
                      + ("a escolha da reserva pesa mais que os detalhes" if reserva == "sem_regiao" else
                         "nenhuma escolha domina")),
            "efeitos": {r["chave"]: r["efeito_txt"] for r in linhas},
            "nota_t5": "dos vínculos sem remuneração de dezembro, a maioria não tem remuneração no ano e pode ser de "
                       "afastados, que nem deveriam entrar no passivo",
            "conta": "passivo de todas as ativas com cada método ÷ passivo da base − 1 (D-015 e D-022 continuam na base)",
            "valores": {"min": lo, "max": hi}, "tabela": linhas,
            **_meta(con, "gold.analise_sensibilidade_metodo", rotulo=SENSIBILIDADE)}


def leitura_literal_receita(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Leitura literal do art. 2º, XXIV, do Prov. 213 (receita líquida do repasse), com a faixa de déficit da base."""
    if not _uf(uf):
        return _sem_uf(uf)
    s = _sens_metodo(con)
    b, r = s.loc["base"], s.loc["receita_liquida"]
    cols = {"n_universo": ("Obrigadas", aprox), "passivo_universo": ("Passivo das obrigadas", brl),
            "valor_descoberto": ("Déficit", brl), "mercado_premio_emitido": ("Prêmio anual", brl)}
    linhas = [{"medida": nome, "base": float(b[c]), "leitura_literal": float(r[c]), "variacao": float(r[f"var_{c}"]),
               "base_txt": fmt(b[c]), "literal_txt": fmt(r[c]), "variacao_txt": pct(r[f"var_{c}"])}
              for c, (nome, fmt) in cols.items()]
    return {"uf": "MG", "rotulo": LEITURA_LITERAL,
            "obrigadas": f"{aprox(b['n_universo'])} → {aprox(r['n_universo'])} ({pct(r['var_n_universo'])})",
            "premio": f"{brl(b['mercado_premio_emitido'])} → {brl(r['mercado_premio_emitido'])} "
                      f"({pct(r['var_mercado_premio_emitido'])})",
            "conta": "receita de referência − fração de repasse declarada no BI do CNJ (2025); faixa de déficit da base",
            "observacao": "sensibilidade: a base do painel continua com a arrecadação (D-002, D-042)",
            "valores": {"var_universo": float(r["var_n_universo"]), "var_premio": float(r["var_mercado_premio_emitido"])},
            "tipo": SENSIBILIDADE, "tabela": linhas, **_meta(con, "gold.analise_sensibilidade_metodo")}


def saltos_declaracao(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Semestres com salto grosseiro (aviso do pipeline, D-046) e a sensibilidade "sem os saltos"."""
    if not _uf(uf):
        return _sem_uf(uf)
    c = con.execute("SELECT violacoes, detalhe FROM qualidade.checagens WHERE checagem LIKE '%salto grosseiro%'").fetchone()
    s = _sens_metodo(con)
    r, b = s.loc["sem_saltos"], s.loc["base"]
    return {"uf": "MG", "aviso_do_pipeline": c[1] if c else "checagem não encontrada",
            "sem_os_saltos": (f"{_br(r['n_universo'] - b['n_universo'], 1)} obrigadas ({pct(r['var_n_universo'])}); "
                              f"prêmio {pct(r['var_mercado_premio_emitido'])}"),
            "conta": "semestre 10 vezes acima ou abaixo da mediana dos 4 anteriores; sem eles, a receita vira a média "
                     "dos semestres sem salto",
            "observacao": "a classe usa o valor declarado (D-046)",
            "valores": {"violacoes": int(c[0]) if c else None, "var_universo": float(r["var_n_universo"])},
            **_meta(con, "qualidade.checagens e gold.analise_sensibilidade_metodo", rotulo=SENSIBILIDADE)}


def lacunas() -> dict:
    """As lacunas do notebook 09 (o que os dados não respondem e a fonte que resolveria), da saída gravada."""
    a = config()["artefatos"]["lacunas_09"]
    t = artefatos.tabela_do_notebook(a["notebook"], a["marcador"])
    return {"n_lacunas": len(t), "lacunas": t["lacuna"].tolist(), "tabela": _linhas(t),
            "fonte": f"{a['notebook']} (seção 3)",
            "citar": f"Fonte: {a['notebook']}, seção 3 (tabela de lacunas, gravada na saída do notebook)."}


def qualidade_fontes(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Data de referência de cada fonte, conferências entre fontes e contratos das tabelas (ok × aviso)."""
    if not _uf(uf):
        return _sem_uf(uf)
    f = con.execute("SELECT fonte, data_referencia, coletado_em FROM silver.fonte_metadados ORDER BY fonte").df()
    r = con.execute("SELECT checagem, status FROM qualidade.reconciliacoes").df()
    c = con.execute("SELECT checagem, tabela, severidade, violacoes FROM qualidade.checagens").df()
    return {"uf": "MG", "fontes": {x.fonte: str(x.data_referencia) for x in f.itertuples()},
            "conferencias": f"{int((r['status'] == 'ok').sum())} ok e {int((r['status'] != 'ok').sum())} com aviso, "
                            f"de {len(r)}",
            "contratos": f"{int((c['violacoes'] == 0).sum())} de {len(c)} sem violação; avisos: "
                         + "; ".join(f"{x.checagem} ({_br(x.violacoes, 0)})" for x in c[c["violacoes"] > 0].itertuples()),
            "tabela": _linhas(f.astype(str)),
            **_meta(con, "silver.fonte_metadados, qualidade.reconciliacoes e qualidade.checagens")}


def clt_outros_estados(con: duckdb.DuckDBPyConnection, uf: str = "MG") -> dict:
    """Empregados CLT pela receita (floresta do T1, notebook 06a): erro por serventia e do total de cada região
    deixada de fora. Para outros estados, só o total estadual com ±10% como piso (D-042, item 4)."""
    if not _uf(uf):
        return _sem_uf(uf)
    t = con.execute("SELECT * FROM gold.analise_clt_modelo").df()
    mae = {m: float((t[c] - t["clt_declarado"]).abs().mean()) for m, c in
           (("floresta", "clt_previsto_floresta"), ("referencia", "clt_previsto_referencia"))}
    reg = t.groupby("regiao_intermediaria")[["clt_declarado", "clt_previsto_floresta"]].sum()
    reg["erro"] = reg["clt_previsto_floresta"] / reg["clt_declarado"] - 1
    margem = float(yaml.safe_load((RAIZ / "config" / "analise.yaml").read_text(encoding="utf-8"))
                   ["regressao"]["margem_total"])
    tot = float(t["clt_previsto_floresta"].sum() / t["clt_declarado"].sum() - 1)
    return {"uf": "MG", "erro_medio_por_serventia": f"{_br(mae['floresta'], 2)} empregado (referência {_br(mae['referencia'], 2)})",
            "regioes_fora_da_margem": f"{int((reg['erro'].abs() > margem).sum())} de {len(reg)}",
            "maior_erro_regional": pct(float(reg["erro"].abs().max())), "erro_total_mg": pct(tot),
            "observacao": f"fora de MG, só o total estadual, com ±{_br(100 * margem, 0)}% como piso; nenhum mapa nem "
                          "ranking estimado",
            "conta": "cada uma das 13 regiões intermediárias prevista com o modelo treinado nas outras 12",
            "valores": {"mae_floresta": mae["floresta"], "mae_referencia": mae["referencia"], "erro_total": tot},
            "tabela": _linhas(reg.reset_index()), **_meta(con, "gold.analise_clt_modelo")}


def decisoes(numeros: tuple[str, ...] = ("D-042", "D-046", "D-047", "D-048", "D-049")) -> dict:
    """Título e situação das decisões que mudam a leitura do painel, de docs/decisoes.md."""
    texto = (RAIZ / "docs" / "decisoes.md").read_text(encoding="utf-8")
    achadas = {m.group(1): m.group(2).strip() for m in re.finditer(r"^## (D-\d{3}) — (.+)$", texto, re.M)}
    linhas = [{"decisao": n, "titulo": achadas[n]} for n in numeros if n in achadas]
    return {"decisoes": {r["decisao"]: r["titulo"] for r in linhas}, "tabela": linhas, "fonte": "docs/decisoes.md",
            "citar": "Fonte: docs/decisoes.md (registro de decisões do projeto)."}


# ferramentas novas que a Etapa 5 pode expor ao chat (mesma assinatura: con, uf)
PARA_O_CHAT = {f.__name__: f for f in (numeros_oficiais, faixa_d042, escada, premio_por_cenario_stf, grupos,
                                       quem_e_obrigado, concentracao, tornado, grade_taxa_adesao, previsao_arrecadacao,
                                       previsao_mercado, subidas_comparacao, pergunta_9, capacidade_pagar,
                                       escolhas_metodo_passivo, leitura_literal_receita, saltos_declaracao,
                                       qualidade_fontes, clt_outros_estados)}
SEM_CONEXAO = {"situacao_adi": situacao_adi, "lacunas": lacunas, "decisoes": decisoes}
