"""Receita de referência, classe (Prov. 213, art. 16) e universo do Prov. 227 (art. 19). Funções puras.

O universo é aplicado DEPOIS do rateio (SPEC §3.4). A classificação é sempre aproximada: a arrecadação pública
não é igual à receita bruta do art. 2º, XXIV, do 213 (D-002).
"""
import pandas as pd

SITUACOES_ESPECIAIS = ("SOB INTERVENÇÃO", "CONVERSÃO EM DILIGÊNCIA")


def receita_referencia(semestres: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Média dos semestres do `ano` (art. 16, § 1º, do 213; D-010, D-013, D-014).

    `semestres`: cns, ano, semestre, arrecadacao, informado, conflito_fonte (uma linha por versão da fonte).
    Regras: semestre com conflito na fonte -> indeterminada; semestres sem valor ou com valor zero são ignorados;
    se nenhum semestre válido sobrar -> indeterminada.
    """
    s = semestres[(semestres["ano"] == ano) & semestres["semestre"].notna()]
    linhas = []
    for cns, g in s.groupby("cns"):
        if g["conflito_fonte"].any():
            linhas.append((cns, None, "conflito_fonte", 0))
            continue
        validos = g[g["informado"] & (g["arrecadacao"] > 0)]
        if validos.empty:
            motivo = "zero_nos_dois_semestres" if g["informado"].all() else "nao_informado"
            linhas.append((cns, None, motivo, 0))
        else:
            n = validos["semestre"].nunique()
            linhas.append((cns, float(validos["arrecadacao"].mean()), "media_2_semestres" if n == 2 else "um_semestre", n))
    return pd.DataFrame(linhas, columns=["cns", "receita_ref", "origem_receita", "semestres_validos"])


def classificar(receita: float | None, limites: dict) -> str:
    """'1', '2', '3' ou 'indeterminada', pelos limites semestrais de uma versão da regra (regras_classificacao.yaml)."""
    if receita is None or pd.isna(receita):
        return "indeterminada"
    if receita <= limites["classe_1_max"]:
        return "1"
    if receita <= limites["classe_2_max"]:
        return "2"
    return "3"


def fracao_fora_classe_1(serventias: pd.DataFrame) -> float:
    """Base de `peso_classe_indeterminada_base`: fração de Classe 2 ou 3 entre as não vagas com classe conhecida (D-016)."""
    conhecidas = serventias[(serventias["situacao_juridica"] != "VAGO") & (serventias["classe"] != "indeterminada")]
    return float((conhecidas["classe"] != "1").mean()) if len(conhecidas) else 0.0


def universo(serventias: pd.DataFrame, limites: dict, p: dict, limites_faixa: dict | None = None) -> pd.DataFrame:
    """Marca cada serventia com `peso_universo` (0 a 1), `motivo` e `classe_faixa`.

    `limites` (regra escolhida) decide quem entra. `limites_faixa` (regra base) dá a classe usada nas faixas de
    déficit (`classe_faixa`, D-019); se omitido, é a própria regra escolhida.

    `serventias`: cns, situacao_juridica, receita_ref (+ demais colunas, mantidas). `p`: premissas resolvidas num nível,
    com `situacoes_especiais_dentro` (bool) e `peso_classe_indeterminada_base` (número).
    - VAGO (interinidade, art. 19 do 227): fora, sempre.
    - Classe 1 (art. 19 do 227; D-001): fora.
    - SOB INTERVENÇÃO e CONVERSÃO EM DILIGÊNCIA: dentro só se `situacoes_especiais_dentro` (D-007).
    - Classe indeterminada: entra com o peso `peso_classe_indeterminada_base` (0 no min, 1 no max).
    """
    s = serventias.copy()
    s["classe"] = [classificar(r, limites) for r in s["receita_ref"]]
    s["classe_faixa"] = s["classe"] if limites_faixa is None else [classificar(r, limites_faixa) for r in s["receita_ref"]]
    s["classificacao_aproximada"] = True
    peso, motivo = [], []
    for sit, classe in zip(s["situacao_juridica"], s["classe"]):
        if sit == "VAGO":
            peso.append(0.0); motivo.append("interinidade")
        elif sit in SITUACOES_ESPECIAIS and not p["situacoes_especiais_dentro"]:
            peso.append(0.0); motivo.append("situacao_especial_fora")
        elif classe == "1":
            peso.append(0.0); motivo.append("classe_1")
        elif classe == "indeterminada":
            peso.append(float(p["peso_classe_indeterminada_base"])); motivo.append("classe_indeterminada")
        elif sit == "PROVIDO" or sit in SITUACOES_ESPECIAIS:
            peso.append(1.0); motivo.append("dentro")
        else:
            peso.append(0.0); motivo.append("situacao_desconhecida")
    s["peso_universo"] = peso
    s["motivo"] = motivo
    return s
