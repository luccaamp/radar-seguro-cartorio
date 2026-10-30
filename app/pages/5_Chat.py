"""Chat: perguntas sobre o que o painel mostra, respondidas pelo Gemini (nível gratuito; D-060, D-061), que só usa as
ferramentas sobre as mesmas funções das páginas (src/painel/analises.py). Duas abas (D-069): Chat e Perguntas prontas
(respondidas direto pelas ferramentas, com os mesmos números, contas e fontes; D-063). Sem o Gemini (sem chave, sem
internet, cota esgotada ou erro), a aba Chat mostra uma frase só; o motivo técnico vai para o log."""
import logging
import tomllib

import streamlit as st

from comum import aviso_modo, caminho_banco, carga_em_uso, conexao, demonstracao, execucao, md_seguro, modo, rodape
from src import llm
from src.agent import chat
from src.painel import ui

log = logging.getLogger("radar.chat")
cfg = llm.config()
LIMITE = int(cfg["limite_perguntas_sessao"])
BANCO = f"{modo()}:{caminho_banco()}"   # chave do cache das ferramentas: não mistura bancos
ESPERA = '<div class="chat-espera">Consultando os dados…</div>'


def _css() -> None:
    """CSS só desta página (src/agent/chat.css), com a cor de marca do tema do painel (.streamlit/config.toml). Desde a
    D-052 o tema tem as seções [theme.light] e [theme.dark]; o chat.css usa as variáveis de tema do estilo.css."""
    tema = tomllib.loads((llm.RAIZ / ".streamlit" / "config.toml").read_text(encoding="utf-8"))["theme"]
    primaria = tema.get("primaryColor") or tema.get("light", {}).get("primaryColor", "")
    css = (llm.RAIZ / "src" / "agent" / "chat.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css.replace('__PRIMARIA__', primaria)}</style>", unsafe_allow_html=True)


def _cabecalho() -> None:
    """Versão compacta da faixa do topo (o ui.cabecalho não tem uma): título e as etiquetas de dados e premissas."""
    st.markdown('<div class="chat-titulo">Pergunte ao painel</div><div class="chat-sub">Pergunte sobre os dados do '
                'painel: serventias, passivo, déficit, prêmio, projeções, qualidade dos dados e normas.</div>',
                unsafe_allow_html=True)
    ui.contexto([("Dados", carga_em_uso()), ("Premissas", f"v{int(execucao().versao_premissas)}")])
    aviso_modo()   # a linha do modo demonstração, como em todas as páginas do painel


def _selos_html(nomes: list[str]) -> str:
    return f'<div class="chat-selos">{"".join(ui.selo(s) for s in nomes)}</div>' if nomes else ""


def _mostrar(m: dict) -> None:
    """Uma resposta: selos (projeção, faixa provável…), a resposta e, numa linha pequena abaixo, a fonte."""
    corpo, fonte = chat.separar_fonte(m["content"])
    if m.get("selos"):
        st.markdown(_selos_html(m["selos"]), unsafe_allow_html=True)
    st.markdown(md_seguro(corpo))
    if fonte:
        st.caption(md_seguro(fonte))


def _guardar_resposta(r: chat.Resposta | None, parcial: str = "") -> dict:
    """Guarda a resposta no histórico. Sem resposta completa: o texto que já tinha chegado (a pessoa mandou outra
    pergunta no meio e o Streamlit interrompeu esta execução) ou, sem nada, a frase de indisponível."""
    if r is not None:
        m = {"role": "assistant", "content": r.texto, "selos": chat.selos(r.chamadas)}
    elif parcial:
        m = {"role": "assistant", "content": parcial + " …", "selos": []}
    else:
        m = {"role": "assistant", "content": chat.INDISPONIVEL, "selos": [], "indisponivel": True}
    st.session_state["chat_historico"].append(m)
    return m


def _responder(pergunta: str, conversa) -> None:
    """Mostra a pergunta e a resposta enquanto ela chega (streaming). A pergunta entra no histórico logo no início e a
    resposta no `finally`: uma pergunta nova no meio do streaming interrompe esta execução, e nada se perde."""
    anteriores = [{"role": m["role"], "content": m["content"]} for m in st.session_state["chat_historico"]
                  if not m.get("indisponivel")]
    st.session_state["chat_perguntas_usadas"] += 1
    st.session_state["chat_historico"].append({"role": "user", "content": pergunta})
    with conversa:
        with st.chat_message("user"):
            st.markdown(md_seguro(pergunta))
        with st.chat_message("assistant"):
            area = st.empty()
            area.markdown(ESPERA, unsafe_allow_html=True)
            texto, resposta = "", None
            try:
                for tipo, valor in chat.responder_em_partes(pergunta, conexao(), anteriores, banco=BANCO):
                    if tipo == "texto":
                        texto += valor
                        area.markdown(md_seguro(texto))
                    elif tipo == "consultando":   # o texto até aqui era preâmbulo: volta o indicador
                        texto = ""
                        area.markdown(ESPERA, unsafe_allow_html=True)
                    else:
                        resposta = valor
                log.info("chat: %s; %s", llm.situacao()[1],
                         ", ".join(f"{e['etapa']} {e['s']:.1f}s" for e in resposta.etapas))
                if not resposta.texto:
                    resposta.texto = chat.SEM_DADO
            except llm.LLMIndisponivel as e:
                log.warning("chat indisponível: %s (%s)", e.motivo, e)
                if e.motivo == "cota":
                    st.session_state["chat_cota_esgotada"] = True
            finally:
                m = _guardar_resposta(resposta, texto.strip())
            area.empty()
            _mostrar(m)


def aba_chat() -> None:
    historico = st.session_state.setdefault("chat_historico", [])
    st.session_state.setdefault("chat_perguntas_usadas", 0)
    ok, motivo = llm.situacao()
    if ok and st.session_state.get("chat_cota_esgotada"):
        ok, motivo = False, "cota esgotada nesta sessão"
    if not ok:
        log.warning("chat indisponível: %s", motivo)
        st.info(chat.INDISPONIVEL)
        return
    conversa = st.container()
    with conversa:
        for m in historico:
            with st.chat_message(m["role"]):
                # if comum, não expressão: uma expressão solta é exibida pela "mágica" do Streamlit (D-069, erro da IA)
                if m["role"] == "assistant":
                    _mostrar(m)
                else:
                    st.markdown(md_seguro(m["content"]))
    pergunta = None
    sugestoes = st.empty()
    if not historico:
        with sugestoes.container(key="sugestoes"):
            st.caption("Sugestões para começar:")
            colunas = st.columns(2)
            for i, s in enumerate(cfg["sugestoes"]):
                if colunas[i % 2].button(s, key=f"sugestao_{i}", width="stretch"):
                    pergunta = s
    no_limite = st.session_state["chat_perguntas_usadas"] >= LIMITE
    rodape_campo = st.empty()
    digitada = st.chat_input("Escreva sua pergunta sobre os dados do painel", disabled=no_limite)
    pergunta = pergunta or digitada
    if pergunta and not no_limite:
        sugestoes.empty()
        _responder(pergunta, conversa)
    usadas = st.session_state["chat_perguntas_usadas"]
    contador = f"<span>{usadas} de {LIMITE} perguntas nesta sessão</span>" if demonstracao() else ""
    rodape_campo.markdown('<div class="chat-rodape-campo"><span>🔒 Não digite dados pessoais. As perguntas são enviadas '
                          f'ao Google Gemini.</span>{contador}</div>', unsafe_allow_html=True)
    if usadas >= LIMITE:
        st.info(f"Você chegou ao limite de {LIMITE} perguntas nesta sessão. Veja as respostas na aba Perguntas prontas.")
    if historico and st.button("Limpar conversa", type="tertiary"):
        st.session_state["chat_historico"] = []
        st.rerun()   # necessário: a conversa já foi desenhada acima nesta execução


def aba_prontas() -> None:
    st.caption("Respostas com os mesmos números, contas e fontes das outras páginas. Clique numa pergunta para ver a "
               "resposta.")
    temas: dict[str, list[dict]] = {}
    for p in cfg["perguntas_prontas"]:
        temas.setdefault(p["tema"], []).append(p)
    for tema, perguntas in temas.items():
        st.markdown(f"#### {tema}")
        for p in perguntas:
            with st.expander(p["pergunta"]):
                r = chat.responder_sem_modelo(conexao(), p, BANCO, com_rotulo=False)
                _mostrar({"content": r.texto, "selos": chat.selos(r.chamadas)})


st.set_page_config(page_title="Chat", page_icon="💬", layout="wide")
ui.estilo()
_css()
_cabecalho()
tab_chat, tab_prontas = st.tabs(["Chat", "Perguntas prontas"])
with tab_chat, st.container(key="chat"):
    aba_chat()
with tab_prontas, st.container(key="prontas"):
    aba_prontas()

with st.expander("Fontes e datas"):
    rodape(["cnj_serventias", "cnj_colaboradores", "cnj_arrecadacao", "rais_vinculos", "susep_ses_garantia"],
           "Normas: texto oficial dos Provimentos CNJ 227, 213 e 243 (atos.cnj.jus.br, coletado em 2026-10-17).", taxa=True)
    st.caption(md_seguro(
        f"**Como o chat responde:** o modelo Gemini ({cfg['modelo']}; reserva {cfg['reserva']}), do Google, no nível "
        f"gratuito, com as instruções da versão {cfg['versao_prompt']}. Ele não faz contas: cada número vem das mesmas "
        "consultas das outras páginas, com a fonte, a data de referência e a versão das premissas. Sobre normas, não é "
        "parecer jurídico."))
    st.caption("**Dados pessoais:** no nível gratuito do Gemini, o Google pode usar as conversas para melhorar os "
               "produtos dele. Por isso, não digite nome, CPF, telefone nem outro dado pessoal. O painel identifica "
               f"cartórios só pelo CNS e pelo município. Cada sessão faz até {LIMITE} perguntas ao modelo, porque a "
               "cota gratuita é dividida por todos os visitantes do link público.")
