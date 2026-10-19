"""E1 e D-026: supressão complementar e auditor de ataque por diferença. Serventias SINTÉTICAS."""
import pandas as pd

from src.model.supressao import OUTRAS, Celula, montar_visao, passa, vazamentos


def test_regra_primaria_exige_recorte_e_complemento():
    assert passa(5, 5, 3)            # complemento 0
    assert passa(3, 6, 3)            # complemento 3
    assert not passa(2, 9, 3)        # recorte pequeno
    assert not passa(33, 34, 3)      # complemento 1: o caso BH / Classe 3
    assert not passa(8, 9, 3)        # Uberaba / Classe 3


def test_caso_fixo_bh_classe_3_e_pego_pelo_auditor():
    """A tabela geral mostrava BH com 34 serventias e o filtro Classe 3 com 33: a diferença isola 1 cartório."""
    bh = frozenset(f"bh{i}" for i in range(34))
    classe3 = frozenset(list(bh)[:33])
    achados = vazamentos([Celula("geral", "BH", bh, bh), Celula("classe=3", "BH", classe3, classe3)], 3)
    assert any(m.startswith("contido") for m, _, _ in achados)


def _serventias():
    linhas = []
    for ri, rint, n_rec, n_out in [("A", "X", 5, 5), ("B", "X", 2, 4), ("C", "X", 2, 0), ("D", "Y", 4, 1), ("E", "Y", 1, 3)]:
        linhas += [{"cns": f"{ri}r{i}", "regiao_imediata": ri, "regiao_intermediaria": rint, "rec": True} for i in range(n_rec)]
        linhas += [{"cns": f"{ri}o{i}", "regiao_imediata": ri, "regiao_intermediaria": rint, "rec": False} for i in range(n_out)]
    return pd.DataFrame(linhas)


def test_montar_visao_sobe_para_intermediaria_e_outras():
    tot = _serventias()
    rec = tot[tot["rec"]]
    d = montar_visao(rec, tot, 3)
    assert d["A"] == "RI:A"                       # 5 de 10: passa
    assert d["B"] == d["C"] == "RG:X"             # B (2 de 6) e C (2 de 2) somados: 4 de 8, passa
    # D (4 de 5: complemento 1) e E (1 de 4) falham; juntos em Y: 5 de 9, passa
    assert d["D"] == d["E"] == "RG:Y"
    assert OUTRAS not in d.values()


def test_supressao_secundaria_forcada():
    tot = _serventias()
    rec = tot[tot["rec"]]
    d = montar_visao(rec, tot, 3, nao_publicar={"RI:A"})
    assert d["A"] != "RI:A"


def test_resto_da_particao_e_vazamento():
    """Filtro que particiona: se 3 de 4 categorias são publicadas na área, o total − publicadas isola a 4ª."""
    area = frozenset(f"s{i}" for i in range(11))   # 5 + 4 publicadas; o resto (2 da classe 3) fica isolado
    cats = {"classe=1": list(area)[:5], "classe=2": list(area)[5:9], "classe=3": list(area)[9:11]}
    cel = [Celula(v, "RI:A", frozenset(s)) for v, s in cats.items() if len(s) >= 3]
    achados = vazamentos(cel, 3, {"RI:A": area}, {"classe": list(cats)})
    assert any(m.startswith("resto da partição") for m, _, _ in achados)
