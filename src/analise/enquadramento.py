"""Sensibilidade do enquadramento da classe (Prov. 213, art. 16) a semestres suspeitos. Só análise: o pipeline continua
com a regra da D-010 (média dos semestres de 2025)."""
import pandas as pd
import yaml

from src.analise import RAIZ


def limites_classe(regra: str = "v2") -> tuple[float, float]:
    """Limites semestrais das Classes 1 e 2 em config/regras_classificacao.yaml."""
    cfg = yaml.safe_load((RAIZ / "config" / "regras_classificacao.yaml").read_text(encoding="utf-8"))
    lim = cfg["versoes"][regra]["limites"]
    return lim["classe_1_max"], lim["classe_2_max"]


def classe_pela_receita(receita: pd.Series, regra: str = "v2") -> pd.Series:
    """Classe "1", "2" ou "3" pela receita semestral (até o limite, inclusive, fica na classe de baixo); vazio = vazio."""
    c1, c2 = limites_classe(regra)
    r = pd.Series(receita, dtype="float64")
    out = pd.Series(pd.NA, index=r.index, dtype="object")
    out[r.notna()] = "3"
    out[r <= c2] = "2"
    out[r <= c1] = "1"
    return out


def receita_sem_saltos(serie: pd.DataFrame, saltos: pd.DataFrame, ano: int) -> pd.Series:
    """Receita de referência alternativa, por CNS, para as serventias com salto no `ano`: a média dos semestres do ano
    sem salto e com valor > 0; se não sobrar nenhum, a média dos semestres > 0 do ano anterior."""
    marcados = set(map(tuple, saltos.loc[saltos["ano"] == ano, ["cns", "ano", "semestre"]].values.tolist()))
    s = serie[serie["cns"].isin({c for c, _, _ in marcados}) & serie["ano"].isin([ano - 1, ano])].copy()
    s["salto"] = [(c, a, m) in marcados for c, a, m in zip(s["cns"], s["ano"], s["semestre"])]
    validos = s[(s["arrecadacao"] > 0) & ~s["salto"]]
    no_ano = validos[validos["ano"] == ano].groupby("cns")["arrecadacao"].mean()
    anterior = validos[validos["ano"] == ano - 1].groupby("cns")["arrecadacao"].mean()
    return no_ano.combine_first(anterior).rename("receita_sem_saltos")
