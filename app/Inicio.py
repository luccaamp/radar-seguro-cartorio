"""Página inicial do painel. Rodar com: uv run streamlit run app/Inicio.py

Responde "quanto é esse mercado?": o prêmio base com a faixa provável (D-042), os 10 números, a escada do passivo ao
prêmio e a situação da ADI 8015. Tudo vem de src/painel/analises.py (via comum.analise), o mesmo que o chat usará.
"""
import streamlit as st

from comum import EXPLICA_NIVEIS, analise, data_base_passivo, execucao, md_seguro, num, pagina, rodape
from src.painel import graficos, ui

premio = analise("faixa_d042", medida="premio")
oficiais = analise("numeros_oficiais")
num_ = {n["chave"]: n for n in oficiais["numeros"]}
pagina("Radar Seguro-Garantia Cartórios", "📊", "Radar Seguro-Garantia · Cartórios de Minas Gerais",
       "Quanto o seguro obrigatório dos cartórios movimenta em MG",
       f"Na regra atual, as seguradoras receberiam **{premio['valor_base']} por ano** em prêmios; o valor provável fica "
       f"entre **{premio['faixa_provavel']}**. É um mercado pequeno diante da dívida trabalhista de "
       f"{num_['passivo_obrigadas']['valor']} das obrigadas, e o STF pode zerá-lo.")

st.markdown("O **Provimento CNJ 227/2026** obriga o titular do cartório a declarar o passivo trabalhista dos "
            "empregados CLT e, se os bens livres não o cobrirem, a apresentar fiança bancária ou **seguro-garantia** "
            "do déficit (art. 13). Ficam fora a Classe 1 do Prov. 213 e os cartórios sob interinidade (art. 19).")
with st.expander("Termos em uma linha"):
    st.markdown(md_seguro(
        "- **CLT:** empregado com carteira assinada (estatutários, estagiários e terceirizados ficam fora).\n"
        "- **Passivo trabalhista:** quanto o cartório pagaria se demitisse todos os empregados CLT hoje.\n"
        "- **Classe 1:** cartório com receita de até R$ 300 mil por semestre (Prov. 243); não é obrigado.\n"
        "- **Déficit:** a parte do passivo que os bens do titular não cobrem; precisa de garantia.\n"
        "- **IS (importância segurada):** a parte do déficit coberta por seguro (o resto vai para fiança ou bens).\n"
        "- **Prêmio:** o que as seguradoras recebem por ano (IS × taxa).\n"
        "- **Dado × suposição:** dado vem de fonte pública; suposição é uma premissa do modelo, com faixa.\n"
        "- **Faixa provável (P5–P95):** onde caem 90% dos resultados quando as suposições variam juntas.\n"
        "- **Projeção:** estimativa para 2026–27; nunca é número oficial.\n"
        "- **Sensibilidade:** quanto o resultado muda se uma escolha de método ou de leitura da norma mudar."))

# ---- D-042: déficit, IS e prêmio (base > faixa provável > extremos)
st.header("Déficit, garantia e prêmio")
d042 = [analise("faixa_d042", medida=m) for m in ("deficit", "importancia_segurada", "premio")]
ui.grade([ui.kpi_d042(r) for r in d042], 3)
with st.expander("Como ler a faixa provável e os extremos"):
    st.markdown(md_seguro(
        f"- **Valor base** é o número oficial do painel. **Faixa provável (P5–P95)**: a {premio['subrotulo_faixa']}; "
        f"90% dos {premio['sorteios']} sorteios das suposições caem nela. Mede a "
        "incerteza dentro das faixas de cada suposição, não o risco de elas estarem erradas; não é um intervalo de "
        "confiança.\n"
        f"- **Extremos teóricos:** todas as suposições no limite ao mesmo tempo, o que quase nunca acontece "
        f"(prêmio {premio['extremos']}). {premio['nota_cantos_mc']}\n"
        f"- {premio['nota_mediana']}\n"
        f"- Se as quatro suposições de patrimônio andarem juntas (sensibilidade), a faixa do prêmio vai a "
        f"{premio['sensibilidade_patrimonio_junto']}."))
    ui.fonte(premio)
with st.expander("Sensibilidades: o que mais mexe no prêmio"):
    tor = analise("tornado")
    st.markdown(md_seguro(f"Uma suposição por vez, do mínimo ao máximo: **{tor['mais_pesam'][0]}**; "
                          f"{tor['mais_pesam'][1]}. As duas primeiras somam {tor['parte_das_duas_primeiras']} da "
                          f"soma das amplitudes. Detalhe na página **Análises**."))
    ui.fonte(tor)

# ---- os 10 números
st.header("Os 10 números oficiais")
ajuda = {"obrigadas": "valor esperado: inclui o peso das serventias de classe indeterminada",
         "com_deficit": "valor esperado: soma das chances de déficit das obrigadas",
         "passivo_todas": f"custo de demitir todos os empregados CLT; data-base {data_base_passivo()}",
         "teto": "passivo das obrigadas × taxa base, como se ninguém tivesse bens"}
cartoes = [ui.kpi(f"{n['numero']}. {n['rotulo']}", n["valor"], "dado" if n["natureza"] == "dado" else "suposicao",
                  ajuda.get(n["chave"], "")) for n in oficiais["numeros"]]
ui.grade(cartoes, 5)
ui.fonte(oficiais, oficiais["observacao"] + ".")

# ---- escada
r_escada = analise("escada")
ui.grafico(graficos.escada(r_escada))
with st.expander("Dados do gráfico e método"):
    st.markdown(md_seguro(f"{r_escada['conta']}. Os degraus em azul vêm de dados públicos; os em violeta dependem de "
                          "suposições (D-016, D-046). " + EXPLICA_NIVEIS))
    ui.baixar(r_escada, "escada_do_mercado")

# ---- situação regulatória
st.header("Situação regulatória: ADI 8015")
adi = analise("situacao_adi")
stf = analise("premio_por_cenario_stf")
c1, c2 = st.columns([3, 2])
with c1:
    ui.achado(f"Sem liminar · conferido em {adi['conferido_em']}",
              f"A ANOREG/BR questiona os arts. 8º a 17 do Prov. 227 no STF. {adi['situacao']}", "alerta")
    st.caption(md_seguro(adi["citar"]))
with c2:
    ui.grade([ui.kpi(c["nome"], c["premio_txt"], "suposicao" if c["cenario"] == "parcial" else None,
                     f"faixa provável {c['faixa_txt']}" if c["p95"] > 0 else "a demanda de garantia vai a zero")
              for c in stf["tabela"]], 1)
    ui.fonte(stf, stf["observacao"] + ".")

e = execucao()
st.caption(f"Peso da classe indeterminada no cenário base: {num(100 * e.peso_classe_indeterminada_base, 1)}% "
           f"(calculado na carga). Salário da RAIS sem correção (data-base {data_base_passivo()}, D-020).")
rodape(["cnj_serventias", "cnj_colaboradores", "cnj_arrecadacao", "rais_vinculos"], taxa=True)
