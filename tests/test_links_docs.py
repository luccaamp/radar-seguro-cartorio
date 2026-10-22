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


def test_indice_do_historico_cita_todos_os_documentos():
    """O docs/historico/INDICE.md tem um link para cada .md de docs/historico/ (D-035). O índice de docs/ (README.md)
    saiu na simplificação dos documentos (D-037): cada sessão lê o CLAUDE.md, o ESTADO_ATUAL.md e o documento da
    etapa, que o ESTADO_ATUAL.md indica."""
    historico = RAIZ / "docs" / "historico" / "INDICE.md"
    no_historico = [p for p in arquivos_md() if p.parent == historico.parent and p != historico]
    faltando = [p.relative_to(RAIZ).as_posix() for p in no_historico if p.resolve() not in _alvos(historico)]
    assert no_historico and not faltando, f"documentos sem entrada no docs/historico/INDICE.md: {faltando}"


def test_estado_atual_indica_o_documento_da_etapa():
    """O ESTADO_ATUAL.md aponta, com link, para um documento da etapa que existe em docs/ (D-037)."""
    estado = RAIZ / "docs" / "ESTADO_ATUAL.md"
    alvos = [a for a in _alvos(estado) if a.parent == estado.parent.resolve() and a.name.startswith("plano_")]
    assert alvos and all(a.exists() for a in alvos), "o ESTADO_ATUAL.md precisa apontar para docs/plano_<etapa>.md"
