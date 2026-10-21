"""Nenhum link relativo dos .md do projeto aponta para arquivo inexistente (limpeza da Fase 1, 2c).

Confere links Markdown `[texto](caminho)` relativos (não http, não âncora). Os registros históricos citam arquivos
pelo nome em texto corrido, sem link; isso não é conferido aqui.
"""
import re

from apoio_painel import RAIZ, arquivos_versionaveis

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def arquivos_md():
    return arquivos_versionaveis("*.md")


def test_links_relativos_existem():
    quebrados = []
    for md in arquivos_md():
        texto = md.read_text(encoding="utf-8")
        for alvo in LINK.findall(texto):
            if alvo.startswith(("http://", "https://", "ftp://", "mailto:", "#")):
                continue
            caminho = (md.parent / alvo.split("#")[0]).resolve()
            if not caminho.exists():
                quebrados.append(f"{md.relative_to(RAIZ).as_posix()} -> {alvo}")
    assert len(arquivos_md()) > 10
    assert not quebrados, quebrados


def _alvos(md):
    return {(md.parent / a.split("#")[0]).resolve() for a in LINK.findall(md.read_text(encoding="utf-8"))}


def test_indice_de_docs_cita_todos_os_documentos():
    """docs/README.md (índice) tem um link para cada .md de docs/, para o docs/historico/INDICE.md e para os
    documentos fora de docs/ que fazem parte do sistema; o INDICE.md do histórico tem um link para cada .md de
    docs/historico/ (D-035); o CLAUDE.md aponta para o índice."""
    indice, historico = RAIZ / "docs" / "README.md", RAIZ / "docs" / "historico" / "INDICE.md"
    esperados = [p for p in arquivos_md() if p.parent == RAIZ / "docs" and p != indice] + [historico]
    esperados += [RAIZ / "CLAUDE.md", RAIZ / "README.md", RAIZ / "CONTRIBUTING.md", RAIZ / "notebooks" / "README.md"]
    faltando = [p.relative_to(RAIZ).as_posix() for p in esperados if p.resolve() not in _alvos(indice)]
    assert not faltando, f"documentos sem entrada no docs/README.md: {faltando}"
    no_historico = [p for p in arquivos_md() if p.parent == historico.parent and p != historico]
    faltando = [p.relative_to(RAIZ).as_posix() for p in no_historico if p.resolve() not in _alvos(historico)]
    assert no_historico and not faltando, f"documentos sem entrada no docs/historico/INDICE.md: {faltando}"
    assert "docs/README.md" in (RAIZ / "CLAUDE.md").read_text(encoding="utf-8")
