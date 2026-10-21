"""Testes estáticos do código do painel (não abrem o banco).

1.1: texto com "R$" exibido pelo Streamlit precisa passar por md_seguro (o "$" vira fórmula LaTeX).
1.7: o painel só lê tabelas públicas; gold.interno_* é proibido fora do pipeline.
D-034: o painel abre o banco só para leitura.
"""
import ast
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVOS_APP = sorted((RAIZ / "app").rglob("*.py"))
FUNCOES_MARKDOWN = {"markdown", "caption", "write", "info", "warning", "error", "success", "subheader", "title"}
FORMATADORES_RS = {"brl", "faixa"}   # devolvem texto com "R$"


def _tem_rs(no: ast.AST) -> bool:
    """O texto (constante, f-string ou concatenação) contém 'R$' ou valor formatado por brl/faixa?"""
    if isinstance(no, ast.Constant) and isinstance(no.value, str):
        return "R$" in no.value
    if isinstance(no, ast.JoinedStr):
        return any(_tem_rs(v) for v in no.values)
    if isinstance(no, ast.FormattedValue):
        return _tem_rs(no.value)
    if isinstance(no, ast.BinOp):
        return _tem_rs(no.left) or _tem_rs(no.right)
    if isinstance(no, ast.Call) and isinstance(no.func, ast.Name) and no.func.id in FORMATADORES_RS:
        return True
    return False


def _protegido(no: ast.AST) -> bool:
    return isinstance(no, ast.Call) and isinstance(no.func, ast.Name) and no.func.id == "md_seguro"


def _violacoes(arquivo: Path) -> list[str]:
    out = []
    for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
        if not (isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)):
            continue
        textos = []
        if no.func.attr in FUNCOES_MARKDOWN and no.args:
            textos.append(no.args[0])
        textos += [k.value for k in no.keywords if k.arg == "help"]
        for t in textos:
            if not _protegido(t) and _tem_rs(t):
                out.append(f"{arquivo.relative_to(RAIZ)}:{no.lineno} ({no.func.attr})")
    return out


def test_textos_com_rs_passam_por_md_seguro():
    violacoes = [v for a in ARQUIVOS_APP for v in _violacoes(a)]
    assert not violacoes, violacoes


def test_painel_nao_le_tabelas_internas():
    """1.7 e D-026: o painel (e, na Fase 3, o chat) só lê tabelas públicas; 'interno_' não pode aparecer no código.
    Sem exceções (a do Mercado foi removida com a opção B)."""
    achados = [str(a.relative_to(RAIZ)).replace("\\", "/") for a in ARQUIVOS_APP
               if "interno_" in a.read_text(encoding="utf-8")]
    assert not achados, achados


def test_painel_abre_o_banco_so_para_leitura():
    """D-034: toda conexão DuckDB do painel tem read_only=True, e o código do painel não tem SQL que grava."""
    sem_read_only, grava = [], []
    for a in ARQUIVOS_APP:
        texto = a.read_text(encoding="utf-8")
        for no in ast.walk(ast.parse(texto)):
            if isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute) and no.func.attr == "connect":
                if not any(k.arg == "read_only" and getattr(k.value, "value", None) is True for k in no.keywords):
                    sem_read_only.append(f"{a.relative_to(RAIZ)}:{no.lineno}")
            if isinstance(no, ast.Constant) and isinstance(no.value, str) and re.search(
                    r"\b(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|COPY|ATTACH)\b", no.value):
                grava.append(f"{a.relative_to(RAIZ)}:{no.lineno}")
    assert not sem_read_only and not grava, (sem_read_only, grava)


def test_detector_pega_o_caso_errado():
    """O próprio detector: texto com R$ sem md_seguro é violação; com md_seguro, não."""
    errado = ast.parse('st.markdown("Regra dos R$ 300 mil e R$ 100 mil")').body[0].value
    certo = ast.parse('st.markdown(md_seguro("Regra dos R$ 300 mil e R$ 100 mil"))').body[0].value
    assert _tem_rs(errado.args[0]) and not _protegido(errado.args[0]) and _protegido(certo.args[0])
