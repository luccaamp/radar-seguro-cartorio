"""Supressão estatística das visões filtradas do Mercado (D-026, E1). Funções puras.

Cada número publicado é uma soma sobre um CONJUNTO de serventias. Duas regras:
1. primária (por célula): o recorte tem >= `limiar` serventias e o complemento (total da área − recorte) é 0 ou >= `limiar`;
2. diferença (entre células): se o conjunto de uma célula publicada está contido no de outra e a diferença tem 1 ou 2
   serventias, a subtração isola um cartório. O mesmo vale para o resto de um filtro que particiona (classe, situação):
   total da área − categorias publicadas.
A célula que falha sobe: região imediata -> grupo da região intermediária -> "outras regiões" (soma fecha o total).
"""
from dataclasses import dataclass, field

import pandas as pd

OUTRAS = "OUTRAS"


@dataclass(frozen=True)
class Celula:
    visao: str                 # ex.: "geral", "classe=3", "situacao=VAGO", "uf:classe=3:v2:base"
    area_id: str
    todos: frozenset           # serventias somadas em contagem, CLT e passivo de todas as ativas
    universo: frozenset = field(default=frozenset())   # serventias com peso no universo e passivo > 0 (obrigados, déficit)


def passa(n_recorte: int, n_total: int, limiar: int) -> bool:
    """Regra primária: recorte >= limiar e complemento 0 ou >= limiar."""
    comp = n_total - n_recorte
    return n_recorte >= limiar and (comp == 0 or comp >= limiar)


def _pequena(d: int, limiar: int) -> bool:
    return 0 < d < limiar


def vazamentos(celulas: list[Celula], limiar: int, totais_por_area: dict[str, frozenset] | None = None,
               particoes: dict[str, list[str]] | None = None) -> list[tuple[str, str, str]]:
    """Ataques por diferença possíveis entre as células publicadas. Devolve (motivo, celula_a, celula_b).

    - contido: conjunto de A dentro do de B com diferença de 1 ou 2 (em `todos` ou em `universo`);
    - complemento: total da área − célula com 1 ou 2 (`totais_por_area`, área -> todas as serventias);
    - resto: para filtros que particionam (`particoes`: filtro -> visões), total da área − categorias publicadas.
    """
    achados = []
    for nome_conj in ("todos", "universo"):
        por_tamanho: dict[int, list[Celula]] = {}
        for c in celulas:
            s = getattr(c, nome_conj)
            if s:
                por_tamanho.setdefault(len(s), []).append(c)
        for n, menores in por_tamanho.items():
            for d in range(1, limiar):
                for a in menores:
                    sa = getattr(a, nome_conj)
                    for b in por_tamanho.get(n + d, []):
                        if sa < getattr(b, nome_conj):
                            achados.append((f"contido em {nome_conj} (diferença {d})", f"{a.visao}|{a.area_id}",
                                            f"{b.visao}|{b.area_id}"))
    for c in celulas:
        if len(c.todos) < limiar:
            achados.append(("célula abaixo do limiar", f"{c.visao}|{c.area_id}", ""))
        if totais_por_area and c.area_id in totais_por_area and _pequena(len(totais_por_area[c.area_id] - c.todos), limiar):
            achados.append(("complemento de 1 ou 2", f"{c.visao}|{c.area_id}", ""))
    if particoes and totais_por_area:
        for filtro, visoes in particoes.items():
            por_area: dict[str, set] = {}
            for c in celulas:
                if c.visao in visoes:
                    por_area.setdefault(c.area_id, set()).update(c.todos)
            for area, publicados in por_area.items():
                if area in totais_por_area and _pequena(len(totais_por_area[area] - publicados), limiar):
                    achados.append((f"resto da partição {filtro}", area, ""))
    return achados


def montar_visao(recorte: pd.DataFrame, total: pd.DataFrame, limiar: int, nao_publicar: set[str] = frozenset()
                 ) -> dict[str, str]:
    """Decide a área publicada de cada região imediata numa visão filtrada.

    `recorte` e `total`: uma linha por serventia, colunas cns, regiao_imediata, regiao_intermediaria.
    `nao_publicar`: áreas ("RI:<nome>" ou "RG:<intermediária>") forçadas a subir (supressão secundária).
    Devolve regiao_imediata -> area_id
    ("RI:<nome>", "RG:<intermediária>" ou OUTRAS) para as regiões com recorte > 0.
    """
    n_rec = recorte.groupby("regiao_imediata").size()
    n_tot = total.groupby("regiao_imediata").size()
    rint = total.drop_duplicates("regiao_imediata").set_index("regiao_imediata")["regiao_intermediaria"]
    destino = {}
    sobem = []
    for ri, n in n_rec.items():
        if f"RI:{ri}" not in nao_publicar and passa(int(n), int(n_tot.get(ri, 0)), limiar):
            destino[ri] = f"RI:{ri}"
        else:
            sobem.append(ri)
    for grupo, ris in pd.Series(sobem, dtype=object).groupby(rint.reindex(sobem).to_numpy()):
        ris = list(ris)
        if passa(int(n_rec[ris].sum()), int(n_tot[ris].sum()), limiar) and f"RG:{grupo}" not in nao_publicar:
            destino.update({ri: f"RG:{grupo}" for ri in ris})
        else:
            destino.update({ri: OUTRAS for ri in ris})
    # "outras regiões" também precisa passar; senão absorve a menor área publicada até passar
    while True:
        outras = [ri for ri, a in destino.items() if a == OUTRAS]
        if not outras or passa(int(n_rec[outras].sum()), int(n_tot[outras].sum()), limiar):
            break
        publicadas = {a for a in destino.values() if a != OUTRAS}
        if not publicadas:   # nada passa: quem chama não publica "outras" (a visão fica sem área publicada)
            break
        menor = min(publicadas, key=lambda a: int(n_rec[[r for r, x in destino.items() if x == a]].sum()))
        destino.update({ri: OUTRAS for ri, a in destino.items() if a == menor})
    return destino
