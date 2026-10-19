"""Visões públicas do Mercado com filtro (D-026, E1): um filtro por vez, no nível da região imediata, com supressão
primária, hierárquica (região intermediária -> outras regiões) e secundária (auditor de ataque por diferença).

Também decide quais totais ESTADUAIS de cada filtro podem sair em regra v1 e em mínimo/máximo: trocar a regra ou o
nível muda QUEM entra no universo, e a diferença entre duas visões não pode isolar 1 ou 2 serventias.
"""
from dataclasses import dataclass

import pandas as pd

from src.model.supressao import OUTRAS, Celula, montar_visao, passa, vazamentos

# RTD e RCPJ vêm juntos em quase todo cartório: filtrados em separado, a diferença entre os totais de MG isolava
# 2 serventias (achado do auditor). Viram um valor só do filtro (D-026).
ATRIBUICOES = {"notas": "Notas", "rcpn": "Registro Civil (PN)", "ri": "Registro de Imóveis",
               "rtd_rcpj": "Títulos e Documentos / Pessoa Jurídica", "protesto": "Protesto"}
COLUNAS_ATRIBUICAO = {"rtd_rcpj": ("rtd", "rcpj")}
SITUACOES = ["PROVIDO", "VAGO", "SOB INTERVENÇÃO", "CONVERSÃO EM DILIGÊNCIA"]
CLASSES = ["1", "2", "3", "indeterminada"]
PARTICOES = {"situacao": [f"situacao={v}" for v in SITUACOES], "classe": [f"classe={v}" for v in CLASSES]}


def filtros() -> list[tuple[str, str, str]]:
    """(filtro, valor, id da visão). Atribuição não particiona (uma serventia tem várias)."""
    out = [("atribuicao", a, f"atribuicao={a}") for a in ATRIBUICOES]
    out += [("situacao", s, f"situacao={s}") for s in SITUACOES]
    out += [("classe", c, f"classe={c}") for c in CLASSES]
    return out


def mascara(df: pd.DataFrame, filtro: str, valor: str) -> pd.Series:
    if filtro == "atribuicao":
        cols = list(COLUNAS_ATRIBUICAO.get(valor, (valor,)))
        return df[cols].fillna(False).astype(bool).any(axis=1)
    if filtro == "situacao":
        return df["situacao_juridica"] == valor
    return df["classe_faixa"] == valor   # classe pela regra base (D-019)


def _universo(df: pd.DataFrame) -> frozenset:
    return frozenset(df.loc[(df["peso_universo"] > 0) & (df["passivo"] > 0), "cns"])


@dataclass
class Resultado:
    destinos: dict[str, dict[str, str]]          # visão -> regiao_imediata -> area_id
    estaduais: dict[tuple[str, str, str], bool]  # (visão, regra, nível) -> publicado?
    celulas: list[Celula]
    iteracoes: int


def construir(base: pd.DataFrame, por_regra_nivel: dict[tuple[str, str], pd.DataFrame], areas_gerais: pd.DataFrame,
              limiar: int, regra_base: str, max_iter: int = 50) -> Resultado:
    """`base`: serventias na regra base e nível base (cns, regiao_imediata, regiao_intermediaria, filtros, passivo,
    peso_universo). `por_regra_nivel`: as mesmas serventias em cada (regra, nível), para os totais estaduais.
    `areas_gerais`: cns -> area_id da visão geral (mapa sem filtro)."""
    totais = {f"RI:{ri}": frozenset(g["cns"]) for ri, g in base.groupby("regiao_imediata")}
    totais["MG"] = frozenset(base["cns"])
    nao_publicar: dict[str, set[str]] = {v: set() for _, _, v in filtros()}
    estaduais = {(v, r, n): True for _, _, v in filtros() for (r, n) in por_regra_nivel}
    for it in range(1, max_iter + 1):
        celulas, destinos = [], {}
        # visão geral (mapa sem filtro): só base, regra base
        for area, g in base.merge(areas_gerais, on="cns").groupby("area_id"):
            celulas.append(Celula("geral", area, frozenset(g["cns"]), _universo(g)))
        for (r, n), df in por_regra_nivel.items():      # totais estaduais sem filtro
            celulas.append(Celula(f"uf:geral:{r}:{n}", "MG", frozenset(df["cns"]), _universo(df)))
        for filtro, valor, visao in filtros():
            rec = base[mascara(base, filtro, valor)]
            destino = montar_visao(rec, base, limiar, nao_publicar[visao])
            destinos[visao] = destino
            for area in set(destino.values()):
                ris = [ri for ri, a in destino.items() if a == area]
                g = rec[rec["regiao_imediata"].isin(ris)]
                n_tot = int(base["regiao_imediata"].isin(ris).sum())
                if area == OUTRAS and not passa(len(g), n_tot, limiar):
                    continue   # "outras regiões" sem dado publicável
                celulas.append(Celula(visao, area if area.startswith("RI:") else f"{area}@{visao}",
                                      frozenset(g["cns"]), _universo(g)))
            for (r, n), df in por_regra_nivel.items():   # totais estaduais do filtro
                if estaduais[(visao, r, n)]:
                    sub = df[mascara(df, filtro, valor)]
                    celulas.append(Celula(f"uf:{visao}:{r}:{n}", "MG", frozenset(sub["cns"]), _universo(sub)))
        achados = vazamentos(celulas, limiar, totais, PARTICOES)
        if not achados:
            return Resultado(destinos, estaduais, celulas, it)
        mudou = _suprimir(achados, celulas, nao_publicar, estaduais, regra_base)
        if not mudou:
            raise RuntimeError(f"vazamento sem supressão possível: {achados[:5]}")
    raise RuntimeError(f"supressão não convergiu em {max_iter} iterações: {achados[:5]}")


def _suprimir(achados, celulas, nao_publicar, estaduais, regra_base: str) -> bool:
    """Supressão secundária: tira a célula filtrada envolvida no vazamento (a menor), ou o total estadual em regra v1 /
    mínimo / máximo. Nunca mexe na visão geral nem no total estadual base da regra base."""
    tamanho = {f"{c.visao}|{c.area_id}": len(c.todos) for c in celulas}
    mudou = False
    for motivo, a, b in achados:
        candidatos = [x for x in (a, b) if x and not x.startswith("geral|") and not x.startswith("uf:geral")]
        if motivo.startswith("resto da partição"):   # a = área RI: sobe a menor categoria publicada nela
            filtro = motivo.split()[-1]
            pub = [k for k in tamanho if k.endswith(f"|{a}") and k.split("|")[0].split("=")[0] == filtro]
            candidatos = sorted(pub, key=tamanho.get)[:1]
        for alvo in candidatos:   # a primeira candidata que pode sair (a menor vem primeiro)
            visao, area = alvo.split("|")
            if visao.startswith("uf:"):
                _, v, r, n = visao.split(":", 3)
                if (r, n) != (regra_base, "base") and estaduais.get((v, r, n)):
                    estaduais[(v, r, n)] = False
                    mudou = True
                    break
            elif area != "MG":
                area_base = area.split("@")[0]
                if area_base != OUTRAS and area_base not in nao_publicar[visao]:
                    nao_publicar[visao].add(area_base)
                    mudou = True
                    break
    return mudou
