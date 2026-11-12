"""Componentes de interface do painel (docs/painel/padrao_visual.md, seção 6), usados por todas as páginas.

Recebem os resultados de src/painel/analises.py e só os exibem. O HTML vai por st.markdown(unsafe_allow_html=True), com
o texto escapado e o "$" trocado por entidade (senão o Streamlit lê "R$ ... R$" como fórmula LaTeX).
"""
import html
from pathlib import Path
from urllib.parse import quote

import streamlit as st

ESTILO = Path(__file__).with_name("estilo.css")
SELOS = {"dado": "dado", "suposicao": "suposição", "projecao": "projeção", "faixa": "faixa provável",
         "sensibilidade": "sensibilidade", "comparacao": "comparação", "alerta": "alerta",
         "preliminar": "estimativa preliminar", "calibrado": "calibrado"}


def aviso_preliminar(nome: str) -> None:
    """Faixa de aviso dos estados que herdam as premissas de MG (D-081, D-088): todo número do modelo é estimativa
    preliminar até a calibração do estado."""
    _html(f'<div class="rd-frase-bloco">{selo("preliminar")} Os números do modelo para {_t(nome)} usam as premissas '
          "de Minas Gerais, ainda não calibradas para este estado. O cadastro, os empregados e a arrecadação são dados "
          "do próprio estado.</div>")
CHAT = "Chat"   # endereço da página do chat (app/paginas/5_Chat.py)


def _t(texto) -> str:
    """Texto seguro para o HTML: escapado e sem "$" (vira &#36;)."""
    return html.escape(str(texto)).replace("$", "&#36;")


def _negrito(texto: str) -> str:
    """Texto seguro em que **trecho** vira negrito."""
    return "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(_t(texto).split("**")))


def _html(conteudo: str) -> None:
    st.markdown(conteudo, unsafe_allow_html=True)


CHAVE_TEMA = "rd_tema"
_componente_tema = None


def tema() -> str:
    """'escuro' ou 'claro', o tema que o visitante está vendo. Primeiro o que o navegador informou pelo botão de tema
    do painel (componentes/tema.js); antes disso, o st.context.theme (o botão grava a escolha também para o Streamlit).
    '' quando nenhum dos dois informou: o CSS fica no claro, o padrão."""
    try:
        do_navegador = (st.session_state.get(CHAVE_TEMA) or {}).get("tema")
        if do_navegador in ("claro", "escuro"):
            return do_navegador
        t = st.context.theme.type
    except Exception:   # fora do Streamlit (testes do módulo)
        return ""
    return {"dark": "escuro", "light": "claro"}.get(t or "", "")


def _registrar_tema():
    global _componente_tema
    if _componente_tema is None:
        botoes = "".join(f'<button type="button" data-t="{t}" aria-pressed="false">{rot}</button>'
                         for t, rot in (("claro", "Claro"), ("escuro", "Escuro"), ("sistema", "Sistema")))
        _componente_tema = st.components.v2.component(
            "radar_tema", html=f'<div class="rd-tema" role="group" aria-label="Tema do painel">{botoes}</div>',
            css=ESTILO.with_name("componentes").joinpath("tema.css").read_text(encoding="utf-8"),
            js=ESTILO.with_name("componentes").joinpath("tema.js").read_text(encoding="utf-8"))
    return _componente_tema


def estilo() -> None:
    """Injeta o CSS único do painel, o marcador do tema (.rd-tema-escuro ou .rd-tema-claro), que escolhe os tokens
    claros ou escuros no estilo.css, e o botão de tema (Claro · Escuro · Sistema, no canto do topo; ele marca o <html>
    com data-rd-tema, que vale mais que o marcador). Chamado uma vez no topo de cada página."""
    t = tema()
    marca = f'<div class="rd-tema-{t}" hidden></div>' if t else ""
    _html(f"<style>{ESTILO.read_text(encoding='utf-8')}</style>{marca}")
    try:
        _registrar_tema()(data={"atual": t}, key=CHAVE_TEMA, on_tema_change=lambda: None)
    except Exception:   # fora de uma execução do Streamlit (testes do módulo)
        pass


def selo(tipo: str, texto: str | None = None) -> str:
    return f'<span class="rd-selo {tipo}">{_t(texto or SELOS[tipo])}</span>'


def _chips(chips: list[tuple[str, str]]) -> str:
    return '<div class="rd-contexto">' + "".join(f'<span class="rd-chip">{_t(r)}: <b>{_t(v)}</b></span>'
                                                 for r, v in chips) + "</div>"


def contexto(chips: list[tuple[str, str]]) -> None:
    """Etiquetas de estado [(rótulo, valor), ...]. Fora do painel da história; só a página do chat usa."""
    _html(_chips(chips))


def termo(texto: str, explicacao: str) -> str:
    """Termo com a explicação curta ao passar o mouse (o glossário "Termos em uma linha" virou isto)."""
    return f'<span class="rd-termo" title="{_t(explicacao)}">{_t(texto)}</span>'


def cabecalho(titulo: str, subtitulo: str, sobre: str = "") -> None:
    """Título da página (V5 .lede): rótulo pequeno acima (`sobre`), título em negrito e uma linha de subtítulo."""
    _html(f'<div class="rd-cab">{f"<div class=rd-sobre>{_t(sobre)}</div>" if sobre else ""}<h1>{_t(titulo)}</h1>'
          f'<div class="rd-sub">{_negrito(subtitulo)}</div><div class="rd-ouro"></div></div>')


def resposta(rotulo: str, valor: str, unidade: str, faixa: str, frase: str) -> None:
    """A resposta principal do Início: número grande, a faixa provável logo abaixo e a frase de quão certo é."""
    _html(f'<div class="rd-resposta"><div class="rd-rot">{_t(rotulo)}</div>'
          f'<div class="rd-num">{_t(valor)} <small>{_t(unidade)}</small></div>'
          f'<div class="rd-faixa">{_negrito(faixa)}</div><div class="rd-frase">{_negrito(frase)}</div></div>')


def kpi(rotulo: str, valor: str, nota: str = "", projecao: bool = False, dica: str = "") -> str:
    """Cartão de número (HTML, para `grade`): rótulo pequeno em cima, número grande e uma linha de contexto. O selo
    "projeção" só onde houver projeção. `dica`: explicação ao passar o mouse no rótulo."""
    rot = termo(rotulo, dica) if dica else _t(rotulo)
    return (f'<div class="rd-card"><div class="rd-rot">{rot}{selo("projecao") if projecao else ""}</div>'
            f'<div class="rd-num">{_t(valor)}</div>' + (f'<div class="rd-nota">{_negrito(nota)}</div>' if nota else "")
            + "</div>")


def grade(cartoes: list[str], colunas: int) -> None:
    """Cartões numa linha da grade, com a mesma altura (no celular, um por linha)."""
    _html(f'<div class="rd-grade c{colunas}">' + "".join(cartoes) + "</div>")


def frase(texto: str) -> None:
    """Frase de conclusão de um bloco (no máximo duas frases). **trecho** vira negrito."""
    _html(f'<div class="rd-frase-bloco">{_negrito(texto)}</div>')   # div: o <p> do Markdown impõe o tamanho


def grafico(fig) -> None:
    """Exibe um gráfico com o template do painel (theme=None: sem o tema do Streamlit por cima) e sem a barra."""
    from src.painel.graficos import finalizar
    st.plotly_chart(finalizar(fig), width="stretch", theme=None, config={"displayModeBar": False})


def tabela(colunas: list[str], linhas: list[list[str]], numericas: set[int] = frozenset(),
           mudas: set[int] = frozenset(), so_no_computador: set[int] = frozenset(), html: set[int] = frozenset()) -> None:
    """Tabela compacta em HTML. `numericas`: índices das colunas de número (alinhadas à direita, classe rd-num);
    `mudas`: colunas de texto secundário; `so_no_computador`: colunas escondidas em tela estreita (≤ 640 px), para a
    tabela caber no celular sem rolagem lateral; `html`: colunas que já vêm em HTML seguro (um `selo`), sem escapar."""
    def classes(i):
        return " ".join(c for c, sim in (("rd-num", i in numericas), ("rd-mudo", i in mudas and i not in numericas),
                                         ("rd-so-pc", i in so_no_computador)) if sim)

    def cel(i, v):
        classe = classes(i)
        conteudo = v if i in html else _t(v)
        return f'<td class="{classe}">{conteudo}</td>' if classe else f"<td>{conteudo}</td>"
    cab = "".join(f'<th class="rd-so-pc">{_t(c)}</th>' if i in so_no_computador else f"<th>{_t(c)}</th>"
                  for i, c in enumerate(colunas))
    corpo = "".join("<tr>" + "".join(cel(i, v) for i, v in enumerate(ln)) + "</tr>" for ln in linhas)
    _html(f'<table class="rd-tabela"><thead><tr>{cab}</tr></thead><tbody>{corpo}</tbody></table>')


def quadro_calor(titulo_linhas: str, titulo_colunas: str, colunas: list[str],
                 linhas: list[tuple[str, list[dict]]]) -> None:
    """Quadro de calor em HTML (a grade Taxa × adesão do V5): uma linha por valor de `titulo_linhas`, uma coluna por
    valor de `titulo_colunas`. Cada célula é {"texto", "faixa" (zero, 1 … 6: a cor dos tokens --mapa-*), "base"}; a
    célula base ganha o contorno grosso e a palavra "base" para leitor de tela."""
    cab = (f'<tr><th scope="col">{_t(titulo_linhas)} ↓ · {_t(titulo_colunas)} →</th>'
           + "".join(f'<th scope="col">{_t(c)}</th>' for c in colunas) + "</tr>")
    corpo = "".join(
        f'<tr><th scope="row">{_t(rot)}</th>' + "".join(
            f'<td class="rd-calor-{_t(c["faixa"])}{" rd-calor-base" if c.get("base") else ""}">{_t(c["texto"])}'
            + ('<span class="rd-calor-marca"> base</span>' if c.get("base") else "") + "</td>" for c in cels) + "</tr>"
        for rot, cels in linhas)
    _html(f'<table class="rd-tabela rd-calor"><thead>{cab}</thead><tbody>{corpo}</tbody></table>')


def fonte(texto: str) -> None:
    """Fonte de um bloco numa linha pequena: só a fonte e a data."""
    _html(f'<div class="rd-fonte">{_t(texto)}</div>')


def link_chat(pergunta: str, pagina: str = "", municipio: str = "", uf: str = "") -> str:
    """Endereço relativo da página do chat com a pergunta no parâmetro ?pergunta= (a página do chat precisa
    lê-lo). Link HTML, e não st.page_link: este só acha a página quando o painel roda pela
    Início, e cada página também roda sozinha (testes). `pagina`, `municipio` e `uf` levam o contexto (V5, D-082;
    D-088): a página do chat confere os três antes de usar (src/agent/chat.texto_contexto)."""
    extra = "".join(f"&{k}={quote(v)}" for k, v in (("pagina", pagina), ("municipio", municipio), ("uf", uf)) if v)
    return f"{CHAT}?pergunta={quote(pergunta)}{extra}"


def sugestoes(perguntas: list[str], pagina: str = "", municipio: str = "", uf: str = "") -> None:
    """De 2 a 3 perguntas para o chat, ligadas ao que a página mostra; cada uma abre o chat com a pergunta e, com
    `pagina`, `municipio` e `uf`, com o contexto de onde a pessoa estava (V5, D-082)."""
    links = "".join(f'<a class="rd-sugestao" href="{_t(link_chat(p, pagina, municipio, uf))}" target="_self">{_t(p)}</a>'
                    for p in perguntas)
    _html(f'<div class="rd-sugestoes"><div class="rd-sugestoes-tit">Pergunte ao chat</div>'
          f'<div class="rd-sugestoes-links">{links}</div></div>')
