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
         "sensibilidade": "sensibilidade", "comparacao": "comparação", "alerta": "alerta"}
CHAT = "Chat"   # endereço da página do chat (app/pages/5_Chat.py)


def _t(texto) -> str:
    """Texto seguro para o HTML: escapado e sem "$" (vira &#36;)."""
    return html.escape(str(texto)).replace("$", "&#36;")


def _negrito(texto: str) -> str:
    """Texto seguro em que **trecho** vira negrito."""
    return "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(_t(texto).split("**")))


def _html(conteudo: str) -> None:
    st.markdown(conteudo, unsafe_allow_html=True)


def tema() -> str:
    """'escuro' ou 'claro', o tema que o Streamlit está mostrando (segue o sistema, como o Raio-X; o menu troca). ''
    quando o navegador ainda não informou: o CSS cai na preferência do sistema."""
    try:
        t = st.context.theme.type
    except Exception:   # fora do Streamlit (testes do módulo)
        return ""
    return {"dark": "escuro", "light": "claro"}.get(t or "", "")


def estilo() -> None:
    """Injeta o CSS único do painel e o marcador do tema (.rd-tema-escuro ou .rd-tema-claro), que escolhe os tokens
    claros ou escuros do Raio-X no estilo.css. Chamado uma vez no topo de cada página."""
    marca = f'<div class="rd-tema-{tema()}" hidden></div>' if tema() else ""
    _html(f"<style>{ESTILO.read_text(encoding='utf-8')}</style>{marca}")


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
    """Faixa azul-marinho do topo (D-052): rótulo pequeno acima (`sobre`), título em serifa, uma linha de subtítulo e
    o traço dourado; sem etiquetas. O primeiro bloco da página sobe sobre a faixa (estilo.css)."""
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
           mudas: set[int] = frozenset()) -> None:
    """Tabela compacta em HTML. `numericas`: índices das colunas de número (alinhadas à direita, classe rd-num);
    `mudas`: colunas de texto secundário."""
    def cel(i, v):
        classe = "rd-num" if i in numericas else "rd-mudo" if i in mudas else ""
        return f'<td class="{classe}">{_t(v)}</td>' if classe else f"<td>{_t(v)}</td>"
    cab = "".join(f"<th>{_t(c)}</th>" for c in colunas)
    corpo = "".join("<tr>" + "".join(cel(i, v) for i, v in enumerate(ln)) + "</tr>" for ln in linhas)
    _html(f'<table class="rd-tabela"><thead><tr>{cab}</tr></thead><tbody>{corpo}</tbody></table>')


def fonte(texto: str) -> None:
    """Fonte de um bloco numa linha pequena: só a fonte e a data."""
    _html(f'<div class="rd-fonte">{_t(texto)}</div>')


def link_chat(pergunta: str) -> str:
    """Endereço relativo da página do chat com a pergunta no parâmetro ?pergunta= (a página do chat precisa
    lê-lo). Link HTML, e não st.page_link: este só acha a página quando o painel roda pela
    Início, e cada página também roda sozinha (testes)."""
    return f"{CHAT}?pergunta={quote(pergunta)}"


def sugestoes(perguntas: list[str]) -> None:
    """De 2 a 3 perguntas para o chat, ligadas ao que a página mostra; cada uma abre o chat com a pergunta."""
    links = "".join(f'<a class="rd-sugestao" href="{link_chat(p)}" target="_self">{_t(p)}</a>' for p in perguntas)
    _html(f'<div class="rd-sugestoes"><div class="rd-sugestoes-tit">Pergunte ao chat</div>'
          f'<div class="rd-sugestoes-links">{links}</div></div>')
