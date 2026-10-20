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
