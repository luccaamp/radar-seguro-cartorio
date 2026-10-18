"""Qualidade dos dados: data de referência de cada fonte, cobertura, divergências entre fontes e contratos (SPEC §4)."""
import plotly.express as px
import streamlit as st

from comum import AZUL_SERIE, NOMES_FONTE, brl, consulta, execucao, md, num, pct, rodape

st.set_page_config(page_title="Qualidade dos dados", page_icon="✅", layout="wide")
st.title("Qualidade dos dados")
st.markdown("O quanto os números deste painel são confiáveis: de onde vem cada dado, quando foi coletado, "
            "o que bate e o que não bate entre fontes independentes.")

# ---- fontes
st.subheader("Fontes e datas de referência")
f = consulta("SELECT * FROM silver.fonte_metadados ORDER BY fonte")
f["Fonte"] = f["fonte"].map(lambda x: NOMES_FONTE.get(x, x))
f["SHA-256"] = f["sha256"].str[:12] + "…"
f["coletado_em"] = f["coletado_em"].fillna("—")
st.dataframe(f[["Fonte", "data_referencia", "coletado_em", "arquivo", "SHA-256", "url", "observacao"]].rename(columns={
    "data_referencia": "Data de referência", "coletado_em": "Coletado em", "arquivo": "Arquivo no bronze",
    "url": "URL de origem", "observacao": "Observação"}), hide_index=True, width="stretch")

# ---- reconciliações
st.subheader("Conferência entre fontes")
ICONE = {"ok": "✅ ok", "aviso": "⚠️ aviso"}
r = consulta("SELECT * FROM qualidade.reconciliacoes")
r["Situação"] = r["status"].map(ICONE)
r["fonte_b"] = r["fonte_b"].fillna("—")
r["Valor"] = [num(a, 3) if b != b or b is None else num(a) for a, b in zip(r["valor_a"], r["valor_b"])]
r["Comparado com"] = [num(b) if b == b and b is not None else "—" for b in r["valor_b"]]
r["Indicador"] = [pct(i) if b == b and b is not None else num(i, 3) for i, b in zip(r["indicador"], r["valor_b"])]
st.dataframe(r[["Situação", "checagem", "fonte_a", "Valor", "fonte_b", "Comparado com", "Indicador", "tolerancia",
                "detalhe"]].rename(columns={"checagem": "Checagem", "fonte_a": "Fonte A", "fonte_b": "Fonte B",
                                            "tolerancia": "Tolerância", "detalhe": "Detalhe"}),
             hide_index=True, width="stretch")
st.caption("Tolerâncias em `config/qualidade.yaml`. Aviso não interrompe o pipeline: a divergência é mostrada e explicada. "
           "O CNPJ tem mais estabelecimentos que o CNJ porque CNPJs de serventias extintas ou anexadas continuam ativos "
           "(61% do excesso coincide com serventias inativas no CNJ; docs/viabilidade.md).")

m = consulta("SELECT * FROM qualidade.rec_municipio WHERE clt_cnj > 0 OR vinc_rais > 0")
a, b = st.columns([3, 2])
with a:
    fig = px.scatter(m, x="clt_cnj", y="vinc_rais", hover_name="municipio", log_x=True, log_y=True,
                     labels={"clt_cnj": "Empregados CLT declarados ao CNJ (out/2026)",
                             "vinc_rais": "Vínculos ativos na RAIS (31/12/2025)"},
                     title="Empregados por município: CNJ × RAIS (escala log)")
    lim = max(m.clt_cnj.max(), m.vinc_rais.max())
    fig.add_shape(type="line", x0=1, y0=1, x1=lim, y1=lim, line=dict(color="#a3a29d", width=1, dash="dot"))
    fig.update_traces(marker=dict(color=AZUL_SERIE, size=8, opacity=0.6, line=dict(width=1, color="#fcfcfb")))
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, width="stretch")
    st.caption("A linha pontilhada é a igualdade. Municípios com 0 em uma das fontes não aparecem na escala log "
               "(a RAIS registra o vínculo no endereço do CAEPF do titular).")
with b:
    st.markdown("**Maiores diferenças de empregados (RAIS − CNJ)**")
    d = m.reindex(m["dif_empregados"].abs().sort_values(ascending=False).index).head(10)
    st.dataframe(d[["municipio", "clt_cnj", "vinc_rais", "dif_empregados"]].rename(columns={
        "municipio": "Município", "clt_cnj": "CNJ", "vinc_rais": "RAIS", "dif_empregados": "Diferença"}),
        hide_index=True, width="stretch")
    st.markdown("**Maiores diferenças de serventias (CNPJ − CNJ)**")
    s = consulta("SELECT municipio, n_cnj, n_cnpj, dif_serventias FROM qualidade.rec_municipio "
                 "ORDER BY abs(dif_serventias) DESC LIMIT 10")
    st.dataframe(s.rename(columns={"municipio": "Município", "n_cnj": "CNJ", "n_cnpj": "CNPJ",
                                   "dif_serventias": "Diferença"}), hide_index=True, width="stretch")

# ---- regra de classe e rateio
st.subheader("Sensibilidade das escolhas de modelagem")
a, b = st.columns(2)
with a:
    st.markdown(md("**Regra da Classe 1: R$ 300 mil (v2, base) × R$ 100 mil (v1)** — cenário regra mantida"))
    dif = consulta("SELECT * FROM gold.diferenca_regra_classe ORDER BY array_position(['min','base','max'], nivel)")
    st.dataframe(dif.assign(
        **{"Universo v2": dif.n_universo_v2.map(num), "Universo v1": dif.n_universo_v1.map(num),
           "Passivo v2": dif.passivo_universo_v2.map(brl), "Passivo v1": dif.passivo_universo_v1.map(brl),
           "Prêmio v2": dif.mercado_premio_emitido_v2.map(brl), "Prêmio v1": dif.mercado_premio_emitido_v1.map(brl)})
        [["nivel", "Universo v2", "Universo v1", "Passivo v2", "Passivo v1", "Prêmio v2", "Prêmio v1"]]
        .rename(columns={"nivel": "Nível"}), hide_index=True, width="stretch")
with b:
    st.markdown("**Método de rateio do passivo** — base, v2, regra mantida")
    sr = consulta("SELECT * FROM gold.sensibilidade_rateio")
    st.dataframe(sr.assign(**{"Déficit": sr.valor_descoberto.map(brl), "Com déficit": sr.n_deficit.map(num),
                              "Prêmio do mercado": sr.mercado_premio_emitido.map(brl)})
                 [["metodo_rateio", "Com déficit", "Déficit", "Prêmio do mercado"]].rename(
                     columns={"metodo_rateio": "Método"}), hide_index=True, width="stretch")
    st.caption("Todos os métodos distribuem o mesmo passivo municipal; muda só quem recebe cada parte.")
o = consulta("SELECT origem_distribuicao, count(*) n, sum(n_vinculos_rais) v FROM gold.fato_passivo_municipio "
             "WHERE nivel = 'base' GROUP BY 1")
txt = "; ".join(f"{'próprio município' if x.origem_distribuicao == 'municipio' else 'estado (MG)'}: "
                f"{num(x.n)} municípios ({num(x.v)} vínculos)" for x in o.itertuples())
st.markdown(f"**Distribuição de salário × tempo de emprego** (limiar de 20 vínculos, D-008): {txt}.")

# ---- contratos
st.subheader("Contratos das tabelas")
c = consulta("SELECT * FROM qualidade.checagens ORDER BY camada DESC, violacoes DESC")
ok = int((c.violacoes == 0).sum())
st.markdown(f"**{ok} de {len(c)}** checagens sem violação. Erro interrompe o pipeline; aviso fica registrado aqui.")
c["Situação"] = [("✅ ok" if v == 0 else "⚠️ aviso" if s == "aviso" else "⛔ erro") for v, s in zip(c.violacoes, c.severidade)]
st.dataframe(c[["Situação", "camada", "tabela", "checagem", "severidade", "violacoes", "detalhe"]].rename(columns={
    "camada": "Camada", "tabela": "Tabela", "checagem": "Checagem", "severidade": "Severidade",
    "violacoes": "Violações", "detalhe": "Detalhe"}), hide_index=True, width="stretch")

# ---- limitações
st.subheader("Limitações declaradas")
st.markdown("""
- **Classe aproximada:** a arrecadação do Justiça Aberta não é igual à receita bruta do art. 2º, XXIV, do Prov. 213 (D-002).
- **Arrecadação:** 76 serventias com R$ 0 nos dois semestres de 2025 e 2 com valores conflitantes na fonte ficam com classe indeterminada (D-013, D-014).
- **Passivo:** a RAIS não traz a maior remuneração fixa (art. 6º): usa-se a remuneração de dezembro corrigida pelo INPC. Verbas de convenção coletiva não estimadas (art. 5º, V). Estatutários, estagiários e terceirizados fora (D-003).
- **Distribuição:** só vínculos por prazo indeterminado e com remuneração de dezembro (D-009, D-015); 887 afastados ficam fora da distribuição, mas não da contagem.
- **Déficit:** patrimônio dos titulares não é público; probabilidade e parte descoberta são suposições (D-016).
- **Seguro:** segurado da garantia não definido no art. 13; taxa e despesa administrativa são suposições; `desp_com` do SES é a despesa de comercialização inteira.
- **Colaboradores** autodeclarados ao CNJ, sem data por serventia. API do Justiça Aberta sem documentação oficial.
- **Contribuições de terceiros** fora do passivo (art. 5º, parágrafo único; STJ Tema 1228); Sistema S do titular pessoa física sem fonte oficial (D-018).
""")
e = execucao()
rodape(list(NOMES_FONTE), f"Execução do pipeline com premissas versão {int(e.versao_premissas)}.")
