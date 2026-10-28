"""Componentes de interface do painel (docs/painel/padrao_visual.md, seção 6), usados por todas as páginas.

Recebem os resultados de src/painel/analises.py e só os exibem. O HTML vai por st.markdown(unsafe_allow_html=True), com
o texto escapado e o "$" trocado por entidade (senão o Streamlit lê "R$ ... R$" como fórmula LaTeX).
"""
import html
from pathlib import Path

import pandas as pd
import streamlit as st

ESTILO = Path(__file__).with_name("estilo.css")
SELOS = {"dado": "dado", "suposicao": "suposição", "projecao": "projeção", "faixa": "faixa provável",
         "sensibilidade": "sensibilidade", "comparacao": "comparação", "alerta": "alerta"}


def _t(texto) -> str:
    """Texto seguro para o HTML: escapado e sem "$" (vira &#36;)."""
    return html.escape(str(texto)).replace("$", "&#36;")


def _html(conteudo: str) -> None:
    st.markdown(conteudo, unsafe_allow_html=True)


def estilo() -> None:
    """Injeta o CSS único do painel. Chamado uma vez no topo de cada página."""
    _html(f"<style>{ESTILO.read_text(encoding='utf-8')}</style>")


def selo(tipo: str, texto: str | None = None) -> str:
    return f'<span class="rd-selo {tipo}">{_t(texto or SELOS[tipo])}</span>'


def _chips(chips: list[tuple[str, str]]) -> str:
    return '<div class="rd-contexto">' + "".join(f'<span class="rd-chip">{_t(r)}: <b>{_t(v)}</b></span>'
                                                 for r, v in chips) + "</div>"


def cabecalho(sobre: str, titulo: str, manchete: str, numero: tuple[str, str] | None = None,
              chips: list[tuple[str, str]] | None = None) -> None:
    """Faixa colorida do topo: sobretítulo, título, a manchete de 10 segundos e, à direita, o número principal da página
    (`numero` = (valor, o que ele é)); embaixo, os selos de contexto. Na manchete, **trecho** vira negrito."""
    partes = _t(manchete).split("**")
    m = "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(partes))
    hero = (f'<div class="rd-hero"><div class="rd-hero-num">{_t(numero[0])}</div>'
            f'<div class="rd-hero-rot">{_t(numero[1])}</div></div>') if numero else ""
    _html(f'<div class="rd-topo"><div class="rd-topo-linha"><div class="rd-cab"><div class="rd-sobre">{_t(sobre)}</div>'
          f'<h1>{_t(titulo)}</h1><div class="rd-manchete">{m}</div></div>{hero}</div>'
          f'{_chips(chips) if chips else ""}</div>')


def contexto(chips: list[tuple[str, str]]) -> None:
    """Faixa com o estado de uma página (filtros ativos etc.): [(rótulo, valor), ...]."""
    _html(_chips(chips))


def secao(nome: str, tom: str = "clara"):
    """Bloco da página com fundo próprio (tom "clara" ou "tinta"), para separar as seções por cor e não só por espaço.
    Uso: `with ui.secao("numeros"): ...`. O CSS pega a classe que o Streamlit gera pela chave (st-key-rd-<tom>-<nome>)."""
    return st.container(key=f"rd-{tom}-{nome}")


def _card(classe: str, rotulo: str, valor: str, selo_html: str = "", miolo: str = "", nota: str = "",
          titulo: str = "") -> str:
    dica = f' title="{_t(titulo)}"' if titulo else ""
    return (f'<div class="rd-card {classe}"{dica}><div class="rd-rot">{_t(rotulo)}{selo_html}</div>'
            f'<div class="rd-num">{_t(valor)}</div>{miolo}'
            + (f'<div class="rd-nota">{_t(nota)}</div>' if nota else "") + "</div>")


def grade(cartoes: list[str], colunas: int) -> None:
    _html(f'<div class="rd-grade c{colunas}">' + "".join(cartoes) + "</div>")


def kpi(rotulo: str, valor: str, natureza: str | None = None, nota: str = "", titulo: str = "") -> str:
    """Cartão simples (HTML, para `grade`). `natureza`: 'dado' ou 'suposicao' (dá o selo e a cor da borda). `titulo`
    vira a dica do mouse."""
    return _card(natureza or "", rotulo, valor, selo(natureza) if natureza else "", nota=nota, titulo=titulo)


def _barrinha(v: dict) -> str:
    """Barra da D-042 em escala linear, dos extremos teóricos (trilho) à faixa provável (banda) e ao valor base (ponto)."""
    lo, hi = v["extremo_min"], v["extremo_max"]
    pos = lambda x: 100 * (x - lo) / (hi - lo) if hi > lo else 50  # noqa: E731
    return (f'<div class="rd-barra"><span class="trilho"></span>'
            f'<span class="banda" style="left:{pos(v["p05"]):.1f}%;width:{pos(v["p95"]) - pos(v["p05"]):.1f}%"></span>'
            f'<span class="ponto" style="left:{pos(v["base"]):.1f}%"></span></div>')


def kpi_d042(r: dict, rotulo: str | None = None) -> str:
    """D-042: valor base em destaque > faixa provável P5–P95 logo abaixo (texto e barrinha) > extremos teóricos em nota
    secundária."""
    faixa = (f'<div class="rd-faixa"><small>{_t(r["rotulo_faixa"])} · {_t(r["subrotulo_faixa"])}</small>'
             f'{_t(r["faixa_provavel"])}{_barrinha(r["valores"])}</div>')
    ext = f'<div class="rd-ext">{_t(r["rotulo_extremos"])}: {_t(r["extremos"])}</div>'
    return _card("d042", rotulo or r["medida"], r["valor_base"], selo("suposicao", "valor base"), faixa + ext,
                 titulo=r["nota_mediana"])


def kpi_projecao(rotulo: str, valor: str, faixa: str, nota: str = "") -> str:
    return _card("proj", rotulo, valor, selo("projecao"), f'<div class="rd-faixa">{_t(faixa)}</div>', nota)


def kpi_comparacao(rotulo: str, valor: str, nota: str = "") -> str:
    return _card("comp", rotulo, valor, selo("comparacao"), nota=nota)


def grafico(fig) -> None:
    """Exibe um gráfico com o template do painel (theme=None: sem o tema do Streamlit por cima) e sem a barra."""
    from src.painel.graficos import finalizar
    st.plotly_chart(finalizar(fig), width="stretch", theme=None, config={"displayModeBar": False})


def achado(titulo: str, texto: str, tipo: str = "") -> None:
    _html(f'<div class="rd-achado {tipo}"><div class="rd-tit">{_t(titulo)}</div>'
          f'<div class="rd-txt">{_t(texto)}</div></div>')


def fonte(r: dict, extra: str = "") -> None:
    """Rodapé curto de um bloco: fonte, data de referência, carga e versão das premissas."""
    partes = [f"Fonte: {r['fonte']}"]
    if r.get("carga"):
        partes.append(f"carga {r['carga']}")
    if r.get("versao_premissas"):
        partes.append(f"premissas v{r['versao_premissas']}")
    if r.get("data_referencia"):   # a data de referência de cada fonte vai na dica do mouse (e no rodapé da página)
        partes.append("data de referência dos dados: passe o mouse")
    dica = f' title="Data de referência: {_t(r["data_referencia"])}"' if r.get("data_referencia") else ""
    _html(f'<div class="rd-fonte"{dica}>{_t(" · ".join(partes) + (". " + extra if extra else ""))}</div>')


def baixar(r: dict, nome: str, chave: str = "tabela") -> None:
    """Botão "Baixar dados (CSV)" com a tabela agregada do resultado, mais fonte, carga e premissas em colunas."""
    df = pd.DataFrame(r.get(chave) or [])
    if df.empty:
        return
    for k in ("fonte", "carga", "versao_premissas", "rotulo"):
        if r.get(k) is not None:
            df[k] = r[k]
    st.download_button("Baixar dados (CSV)", df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name=f"{nome}.csv", mime="text/csv", key=f"baixar_{nome}_{chave}")
