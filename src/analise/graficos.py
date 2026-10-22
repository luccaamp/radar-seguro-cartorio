"""Gráficos dos notebooks (matplotlib): estilo comum, números no formato brasileiro e exportação em PNG.

Cores: a paleta categórica validada para daltonismo (ordem fixa, nunca reciclada), uma rampa azul para magnitude e
cinza para o que é contexto. Os PNGs vão para a pasta de config/analise.yaml (docs/qa/analises/).
"""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from src.analise import RAIZ, config

SUPERFICIE = "#fcfcfb"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
GRADE = "#e4e3df"
CINZA = "#a3a29c"
CORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
AZUL = {"claro": "#86b6ef", "medio": "#2a78d6", "escuro": "#184f95"}


def estilo() -> None:
    """Aplica o estilo comum a todos os gráficos da sessão."""
    mpl.rcParams.update({
        "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE,
        "figure.dpi": 110, "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelcolor": TEXTO_2, "text.color": TEXTO, "xtick.color": TEXTO_2, "ytick.color": TEXTO_2,
        "axes.edgecolor": GRADE, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.6, "axes.axisbelow": True,
        "axes.prop_cycle": mpl.cycler(color=CORES), "lines.linewidth": 2, "legend.frameon": False,
    })


def salvar(fig: plt.Figure, nome: str) -> Path:
    """Grava o PNG em docs/qa/analises/<nome>.png e devolve o caminho."""
    cfg = config()["graficos"]
    pasta = RAIZ / cfg["pasta"]
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{nome}.png"
    fig.savefig(caminho, dpi=cfg["dpi"], bbox_inches="tight")
    return caminho


def num(v: float, casas: int = 0) -> str:
    """2525 → "2.525"; 0,5 com 1 casa → "0,5"."""
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v: float, casas: int = 1) -> str:
    """0,123 → "12,3%"."""
    return num(100 * v, casas) + "%"


def reais(v: float, casas: int = 1) -> str:
    """Valor em R$ abreviado: R$ 311,9 mi, R$ 368,7 mil, R$ 950."""
    for base, sufixo in ((1e9, " bi"), (1e6, " mi"), (1e3, " mil")):
        if abs(v) >= base:
            return f"R$ {num(v / base, casas)}{sufixo}"
    return f"R$ {num(v)}"


FORMATOS = {"int": num, "num1": lambda v: num(v, 1), "num2": lambda v: num(v, 2), "pct": pct, "reais": reais,
             "reais_cheio": lambda v: "R$ " + num(v, 2)}


def tabela(df: pd.DataFrame, formatos: dict[str, str]) -> pd.DataFrame:
    """Cópia da tabela com as colunas indicadas como texto no formato brasileiro (int, num1, num2, pct, reais,
    reais_cheio); vazios viram "—". Só para mostrar: as contas usam a tabela original."""
    out = df.copy()
    for col, f in formatos.items():
        out[col] = [("—" if pd.isna(v) else FORMATOS[f](v)) for v in out[col]]
    return out


def eixo_reais(ax: plt.Axes, eixo: str = "y") -> None:
    """Rótulos do eixo em R$ abreviado, com uma casa só quando ela não é zero (R$ 1,5 bi; R$ 2 bi)."""
    f = FuncFormatter(lambda v, _: reais(v, 1).replace(",0 ", " ") if v else "0")
    (ax.yaxis if eixo == "y" else ax.xaxis).set_major_formatter(f)


def eixo_num(ax: plt.Axes, eixo: str = "y") -> None:
    """Rótulos do eixo com separador de milhar brasileiro."""
    f = FuncFormatter(lambda v, _: num(v))
    (ax.yaxis if eixo == "y" else ax.xaxis).set_major_formatter(f)


def eixo_periodos(ax: plt.Axes, periodos: list[str], passo: int = 2) -> None:
    """Eixo x de semestres ("2025-1"): posições 0..n−1, com o ano escrito no 1º semestre a cada `passo` anos."""
    marcas = [(i, p[:4]) for i, p in enumerate(periodos) if p.endswith("-1") and int(p[:4]) % passo == 0]
    ax.set_xticks([i for i, _ in marcas], [a for _, a in marcas])
    ax.set_xlim(-0.5, len(periodos) - 0.5)


def nota(fig: plt.Figure, texto: str) -> None:
    """Linha de fonte no pé do gráfico."""
    fig.text(0.01, -0.02, texto, ha="left", va="top", fontsize=8, color=TEXTO_2)
