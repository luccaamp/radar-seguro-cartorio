"""Chat: perguntas sobre o mercado de MG e as normas, respondidas por um modelo local (Ollama) que só usa as
ferramentas sobre as tabelas públicas do painel (E5; SPEC §5.2). Sem Ollama, a página explica e o resto do painel segue."""
import streamlit as st

from comum import aviso_estimativa, conexao, md_seguro, rodape
from src import llm
from src.agent import chat

st.set_page_config(page_title="Chat", page_icon="💬", layout="wide")
st.title("Chat — perguntas sobre o mercado e as normas (MG)")
aviso_estimativa()

ok, explicacao = llm.situacao()
if not ok:
    st.info(md_seguro(f"**Chat desativado.** {explicacao} O resto do painel funciona normalmente."), icon="💤")
else:
    st.caption(md_seguro(f"Modelo local: {explicacao}. Cada número vem de uma ferramenta sobre as tabelas públicas do "
                         "painel e a resposta cita a fonte; sobre normas, não é parecer jurídico. Dados por cartório não "
                         "são mostrados (LGPD). Uma resposta leva de 10 a 60 segundos."))
    historico = st.session_state.setdefault("chat_historico", [])
    for m in historico:
        with st.chat_message(m["role"]):
            st.markdown(md_seguro(m["content"]))
            for c in m.get("chamadas", []):
                st.caption(f"Ferramenta: {c['ferramenta']} {c['argumentos']}")
    pergunta = st.chat_input("Pergunte sobre serventias, passivo, déficit, prêmio, simulação ou as normas")
    if pergunta:
        with st.chat_message("user"):
            st.markdown(md_seguro(pergunta))
        with st.chat_message("assistant"), st.spinner("Consultando as ferramentas…"):
            try:
                r = chat.responder(pergunta, conexao(), [{"role": m["role"], "content": m["content"]} for m in historico])
                texto, chamadas = r.texto, [{"ferramenta": c["ferramenta"], "argumentos": c["argumentos"]}
                                            for c in r.chamadas]
            except llm.LLMIndisponivel as e:
                texto, chamadas = f"O modelo não respondeu ({e}).", []
            st.markdown(md_seguro(texto))
            for c in chamadas:
                st.caption(f"Ferramenta: {c['ferramenta']} {c['argumentos']}")
        historico += [{"role": "user", "content": pergunta},
                      {"role": "assistant", "content": texto, "chamadas": chamadas}]
    if historico and st.button("Limpar conversa"):
        st.session_state["chat_historico"] = []
        st.rerun()

rodape(["cnj_serventias", "cnj_colaboradores", "cnj_arrecadacao", "rais_vinculos", "susep_ses_garantia"],
       "Normas: texto oficial dos Provimentos CNJ 227, 213 e 243 (atos.cnj.jus.br).", taxa=True)
