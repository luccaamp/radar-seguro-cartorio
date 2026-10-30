"""Apoio aos testes do painel: caminhos, assinatura do banco real e preparo da cópia temporária.

Os testes do painel rodam sobre uma CÓPIA do banco gerado pelo pipeline (variável RADAR_BANCO, lida por app/comum.py),
com o gold refeito nela pelo código atual. O banco real e os Parquet de data/ nunca são escritos.
"""
import os
import shutil
import sys
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
BANCO_REAL = RAIZ / "data" / "radar.duckdb"
# painel da terceira rodada (D-051): as cinco páginas da história e o chat. O Simulador saiu da navegação e roda à
# parte (app/simulador.py), mas continua testado.
HISTORIA = ["app/Inicio.py", "app/pages/1_Quão_certo_é.py", "app/pages/2_Onde_está_o_mercado.py",
            "app/pages/3_Para_onde_vai.py", "app/pages/4_Sobre_os_dados.py"]
SOBRE, MERCADO, SIMULADOR = HISTORIA[4], HISTORIA[2], "app/simulador.py"
PAGINAS = HISTORIA + ["app/pages/5_Chat.py", SIMULADOR]


def assinatura_real(p: Path = BANCO_REAL) -> tuple:
    """Data e tamanho do banco real e dos Parquet de data/silver e data/gold (nada disso pode mudar nos testes)."""
    arquivos = [p] + sorted((RAIZ / "data" / "gold").glob("*.parquet")) + sorted((RAIZ / "data" / "silver").glob("*.parquet"))
    return tuple((a.name, a.stat().st_mtime_ns, a.stat().st_size) for a in arquivos)


def preparar_copia(destino_dir: Path) -> Path:
    copia = destino_dir / "radar.duckdb"
    shutil.copy2(BANCO_REAL, copia)
    wal = BANCO_REAL.with_name(BANCO_REAL.name + ".wal")
    if wal.exists():
        shutil.copy2(wal, copia.with_name(copia.name + ".wal"))
    import pipeline
    with duckdb.connect(str(copia)) as con:
        pipeline.etapa_gold(con, exportar_parquet=False)   # não toca em data/gold
    return copia


VARIAVEIS = ("RADAR_BANCO", "RADAR_PUBLICO", "RADAR_ESTADO", "GEMINI_API_KEY")
PASTAS_FORA_DO_GIT = {".git", ".venv", "data", "conversas", "qa", "saidas", "modelos", "__pycache__",
                      ".pytest_cache", ".ruff_cache", ".agents", ".claude", ".ipynb_checkpoints"}


def arquivos_versionaveis(padrao: str) -> list[Path]:
    """Arquivos que o git versionaria (`git ls-files`); sem repositório git (cópia ou zip do GitHub), varre o disco
    pulando as pastas ignoradas pelo .gitignore."""
    import subprocess
    # -z: sem ele, o git põe entre aspas os nomes com acento ("app/pages/2_An\303\241lises.py") e eles se perdem
    r = subprocess.run(["git", "-C", str(RAIZ), "ls-files", "-z", "-co", "--exclude-standard", padrao],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 0 and r.stdout.strip("\0"):
        return [RAIZ / a for a in r.stdout.split("\0") if a and (RAIZ / a).is_file()]
    return sorted(p for p in RAIZ.rglob(padrao) if p.is_file()
                  and not PASTAS_FORA_DO_GIT & set(p.relative_to(RAIZ).parts[:-1]))


def _limpar_caches() -> None:
    """Os caches do Streamlit vivem no processo: ao trocar de banco entre módulos de teste, começam vazios."""
    import streamlit as st
    st.cache_data.clear()
    st.cache_resource.clear()


def apontar_painel(copia: Path, publico: Path | None = None) -> dict:
    """Aponta o painel para `copia` (modo completo) ou, se `copia` não existir e `publico` for dado, para o conjunto
    público (modo demonstração). Devolve as variáveis anteriores para restaurar()."""
    # as páginas importam `comum`, que fica em app/: no `streamlit run` app/ entra no caminho pela página inicial;
    # nos testes, uma página de app/pages/ pode rodar primeiro
    if str(RAIZ / "app") not in sys.path:
        sys.path.insert(0, str(RAIZ / "app"))
    anterior = {v: os.environ.get(v) for v in VARIAVEIS}
    os.environ["RADAR_BANCO"] = str(copia)
    os.environ["RADAR_ESTADO"] = str(copia.with_name("painel_estado.json"))   # cenários salvos ao lado da cópia (D-034)
    os.environ["GEMINI_API_KEY"] = ""   # sem chave: nos testes do painel, o chat fica sempre sem o modelo (D-063)
    if publico is not None:
        os.environ["RADAR_PUBLICO"] = str(publico)
    _limpar_caches()
    return anterior


def restaurar(anterior: dict) -> None:
    for v, valor in anterior.items():
        if valor is None:
            os.environ.pop(v, None)
        else:
            os.environ[v] = valor
    _limpar_caches()
