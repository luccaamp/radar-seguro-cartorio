"""Cascata da Etapa 1: números principais de MG com o código ATUAL, em memória sobre o silver em Parquet (nada é gravado).

Uso: uv run python scripts/verificacao_fase1/cascata.py "<rótulo do passo>"
Imprime uma linha por nível (base v2, mantém) e a sensibilidade v1, e acrescenta o resultado em cascata.csv (pasta deste script).
"""
import csv
import sys
from pathlib import Path

import yaml

from comum import RAIZ, conectar

sys.path.insert(0, str(RAIZ))
from src import estado  # noqa: E402
from src.motor import calcular_serventias, peso_indeterminada, premissas_nivel, resumo_mercado  # noqa: E402
from src.transform.gold import carregar_insumos  # noqa: E402

rotulo = sys.argv[1] if len(sys.argv) > 1 else "atual"
con = conectar()
semente = estado.ler_semente()
regras = yaml.safe_load((RAIZ / "config/regras_classificacao.yaml").read_text(encoding="utf-8"))
cen = yaml.safe_load((RAIZ / "config/cenarios_stf.yaml").read_text(encoding="utf-8"))
ins = carregar_insumos(con)
lim_base = regras["versoes"][regras["versao_base"]]["limites"]
saida = Path(__file__).with_name("cascata.csv")
linhas = []
print(f"premissas versão {semente['versao']} | passo: {rotulo}")
print("regra nivel | ativas | universo | passivo_todas | passivo_univ | com_deficit | deficit | IS | premio | teto")
for regra in ("v2", "v1"):
    lim = regras["versoes"][regra]["limites"]
    peso = peso_indeterminada(ins.serventias, lim)
    for nivel in ("min", "base", "max"):
        p = premissas_nivel(semente, nivel, peso)
        try:
            s, _ = calcular_serventias(ins, p, lim, limites_faixa=lim_base)
        except TypeError:  # código anterior ao passo 3 (A1), sem limites_faixa
            s, _ = calcular_serventias(ins, p, lim)
        r = resumo_mercado(s, p, cen, "mantem")
        teto = r["passivo_universo"] * p["taxa_seguro_anual"]
        linhas.append({"passo": rotulo, "regra": regra, "nivel": nivel, "ativas": r["n_serventias_ativas"],
                       "universo": round(r["n_universo"], 2), "passivo_todas": round(r["passivo_todas"]),
                       "passivo_universo": round(r["passivo_universo"]), "com_deficit": round(r["n_deficit"], 2),
                       "deficit": round(r["valor_descoberto"]), "is": round(r["mercado_importancia_segurada"]),
                       "premio": round(r["mercado_premio_emitido"]), "teto": round(teto)})
        print(f"{regra} {nivel:4s} | {r['n_serventias_ativas']} | {r['n_universo']:7.1f} | {r['passivo_todas']/1e6:6.1f} mi | "
              f"{r['passivo_universo']/1e6:6.1f} mi | {r['n_deficit']:6.1f} | {r['valor_descoberto']/1e6:6.2f} mi | "
              f"{r['mercado_importancia_segurada']/1e6:6.2f} mi | {r['mercado_premio_emitido']/1e3:7.1f} mil | {teto/1e6:5.2f} mi")
novo = not saida.exists()
with open(saida, "a", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(linhas[0]))
    if novo:
        w.writeheader()
    w.writerows(linhas)
