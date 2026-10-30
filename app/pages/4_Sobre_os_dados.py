"""Sobre os dados: a única página com detalhes técnicos (D-051). Os 10 números oficiais numa tabela compacta, as fontes
e as datas, como o número foi calculado (carga, versão das premissas, regra de classe, nível) e as principais
limitações. O detalhe de qualidade (conferências, contratos, sensibilidades de método, lacunas) fica no chat."""
import pandas as pd
import streamlit as st

from comum import (FONTES_NAO_USADAS, NOMES_FONTE, _data_ref, analise, aviso_modo, carga_em_uso, data_base_passivo,
                   execucao, md_seguro, num, pagina, rodape)
from src.painel import ui

oficiais = analise("numeros_oficiais")
fontes = analise("qualidade_fontes")
premio = analise("faixa_d042", medida="premio")
pagina("Sobre os dados", "ℹ️", "Sobre os dados",
       "De onde vêm os números, como foram calculados e o que eles ainda não respondem.", sobre="Sobre os dados")
aviso_modo()

st.header("Os 10 números oficiais")
ui.tabela(["#", "Número", "Valor base", "Extremos teóricos", "Origem"],
          [[str(n["numero"]), n["rotulo"], n["valor"], f"{n['minimo']} a {n['maximo']}" if n["minimo"] != n["maximo"]
            else "—", "dado público" if n["natureza"] == "dado" else "suposição do modelo"]
           for n in oficiais["numeros"]], numericas={2}, mudas={3, 4})
st.caption("Extremos teóricos: todas as suposições no limite ao mesmo tempo, o que quase nunca acontece. O teto teórico "
           "é a dívida das obrigadas × a taxa base, como se nenhum titular tivesse bens.")

st.header("Fontes e datas")


def _data(v) -> str:
    t = str(v)
    return pd.Timestamp(t[:10]).strftime("%d/%m/%Y") if t[:4].isdigit() and t[4:5] == "-" else t


ui.tabela(["Fonte", "Data de referência", "Coletado em"],
          [[NOMES_FONTE.get(f["fonte"], f["fonte"]) + (" (coletado, não usado)" if f["fonte"] in FONTES_NAO_USADAS
                                                      else ""), _data_ref(f["data_referencia"]), _data(f["coletado_em"])]
           for f in fontes["tabela"]], mudas={2})

st.header("Como foi calculado")
e = execucao()
ui.tabela(["Item", "Valor"], [
    ["Carga dos dados", carga_em_uso()],
    ["Versão das premissas", f"v{int(e.versao_premissas)} (suposições aprovadas pelo autor, em config/premissas/)"],
    ["Regra da Classe 1 (fora da obrigação)", "receita de até R$ 300 mil por semestre (Prov. CNJ 243)"],
    ["Nível das suposições", "base (o mínimo e o máximo dão os extremos teóricos)"],
    ["Estado", "Minas Gerais"],
    ["Data-base da dívida trabalhista", f"{data_base_passivo()} (art. 4º do Prov. CNJ 227), salário da RAIS sem correção"],
    ["Peso dos cartórios de classe indeterminada", f"{num(100 * e.peso_classe_indeterminada_base, 1)}%"],
    ["Faixa provável", f"P5 a P95 de {premio['sorteios']} simulações das suposições"],
], mudas={1})

st.header("Principais limitações")
st.markdown(md_seguro(
    "- **Estimativa de mercado, não avaliação de cartório:** usa só dados públicos e suposições declaradas, e supõe a "
    "regra do Provimento como foi publicada.\n"
    "- **Classe aproximada:** a arrecadação publicada pelo CNJ não é exatamente a receita bruta da norma.\n"
    "- **Dívida trabalhista:** a RAIS não traz a maior remuneração fixa nem as verbas de convenção coletiva; usa-se a "
    "remuneração de dezembro de 2025.\n"
    "- **Quem não tem bens:** sai da renda do titular (saldo declarado ao CNJ), que não é patrimônio.\n"
    "- **Taxa e adesão ao seguro:** nenhuma fonte pública as traz; por isso a faixa provável é larga."))
rodape(["cnj_serventias", "cnj_colaboradores", "cnj_arrecadacao", "rais_vinculos", "ibge_malha"])
ui.sugestoes(["Quais dados não têm fonte pública?", "As fontes de dados batem entre si?",
              "Quais decisões de método mudam o resultado?"])
