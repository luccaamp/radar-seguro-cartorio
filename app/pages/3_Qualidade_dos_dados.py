"""Qualidade dos dados: data de referência de cada fonte, cobertura, divergências entre fontes e contratos (SPEC §4)."""
import pandas as pd
import plotly.express as px
import streamlit as st

from comum import (AZUL_SERIE, FONTES_NAO_USADAS, NOMES_FONTE, aprox, aviso_modo, brl, consulta, execucao, md_seguro,
                   num, pct, rodape)

st.set_page_config(page_title="Qualidade dos dados", page_icon="✅", layout="wide")
st.title("Qualidade dos dados")
aviso_modo()
st.markdown("O quanto os números deste painel são confiáveis: de onde vem cada dado, quando foi coletado, "
            "o que bate e o que não bate entre fontes independentes.")

# ---- fontes
st.header("Fontes e datas de referência")
f = consulta("SELECT * FROM silver.fonte_metadados ORDER BY fonte")
f["Fonte"] = f["fonte"].map(lambda x: NOMES_FONTE.get(x, x))
f["SHA-256"] = f["sha256"].str[:12] + "…"
f["coletado_em"] = f["coletado_em"].fillna("—")
f["observacao"] = [f"coletado, não usado. {o or ''}".strip() if fo in FONTES_NAO_USADAS else o
                   for fo, o in zip(f["fonte"], f["observacao"])]
st.dataframe(f[["Fonte", "data_referencia", "coletado_em", "arquivo", "SHA-256", "url", "observacao"]].rename(columns={
    "data_referencia": "Data de referência", "coletado_em": "Coletado em", "arquivo": "Arquivo no bronze",
    "url": "URL de origem", "observacao": "Observação"}), hide_index=True, width="stretch",
    column_config={"Data de referência": st.column_config.TextColumn(width="large")})

# ---- reconciliações
st.header("Conferência entre fontes")
ICONE = {"ok": "✅ ok", "aviso": "⚠️ aviso"}
r = consulta("SELECT * FROM qualidade.reconciliacoes")
r["Situação"] = r["status"].map(ICONE)
r["fonte_b"] = r["fonte_b"].fillna("—")
r["Valor"] = [num(a, 3) if b != b or b is None else num(a) for a, b in zip(r["valor_a"], r["valor_b"])]
r["Comparado com"] = [num(b) if b == b and b is not None else "—" for b in r["valor_b"]]
r["Indicador"] = [pct(i) if b == b and b is not None else num(i, 3) for i, b in zip(r["indicador"], r["valor_b"])]
r["tolerancia"] = [pct(tl) if (b == b and b is not None) or "fração" in fa or "erro" in fa else num(tl, 2)
                   for tl, b, fa in zip(r["tolerancia"], r["valor_b"], r["fonte_a"])]
st.dataframe(r[["Situação", "checagem", "fonte_a", "Valor", "fonte_b", "Comparado com", "Indicador", "tolerancia",
                "detalhe"]].rename(columns={"checagem": "Checagem", "fonte_a": "Fonte A", "fonte_b": "Fonte B",
                                            "tolerancia": "Tolerância", "detalhe": "Detalhe"}),
             hide_index=True, width="stretch")
st.caption("Tolerâncias em `config/qualidade.yaml`. Aviso não interrompe o pipeline: a divergência é mostrada e explicada. "
           "O CNPJ tem mais estabelecimentos que o CNJ porque CNPJs de serventias extintas ou anexadas continuam ativos "
           "(61% do excesso coincide com serventias inativas no CNJ; docs/viabilidade.md).")

# versão pública (D1): municípios com menos de 3 serventias aparecem somados por região imediata
AJUDA_AREA = st.column_config.TextColumn(
    width="medium", help="RI = região imediata do IBGE: soma dos municípios com menos de 3 serventias (LGPD). "
                         "O nome completo aparece ao passar o mouse no gráfico.")
RESUMO = dict(consulta("SELECT chave, valor FROM qualidade.resumo_publico").itertuples(index=False))
m = consulta("SELECT * FROM qualidade.rec_municipio WHERE clt_cnj > 0 OR vinc_rais > 0")
a, b = st.columns([3, 2])
with a:
    fig = px.scatter(m, x="clt_cnj", y="vinc_rais", hover_name="area_completa", log_x=True, log_y=True,
                     hover_data={"n_municipios": True, "clt_cnj": True, "vinc_rais": True},
                     labels={"clt_cnj": "Empregados CLT declarados ao CNJ (out/2026)",
                             "vinc_rais": "Vínculos ativos na RAIS (31/12/2025)", "n_municipios": "Municípios"},
                     title="Empregados: CNJ × RAIS por município (≥ 3 serventias) ou região imediata (escala log)")
    lim = max(m.clt_cnj.max(), m.vinc_rais.max())
    fig.add_shape(type="line", x0=1, y0=1, x1=lim, y1=lim, line=dict(color="#a3a29d", width=1, dash="dot"))
    fig.update_traces(marker=dict(color=AZUL_SERIE, size=8, opacity=0.6, line=dict(width=1, color="#fcfcfb")))
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, width="stretch")
    st.caption(f"A linha pontilhada é a igualdade. **Fora do gráfico (zero numa das fontes, sem lugar na escala log):** "
               f"{num(RESUMO.get('municipios_rais_zero_cnj_positivo', 0))} municípios com RAIS = 0 e CNJ > 0 e "
               f"{num(RESUMO.get('municipios_cnj_zero_rais_positivo', 0))} com CNJ = 0 e RAIS > 0 "
               "(a RAIS registra o vínculo no endereço do CAEPF do titular).")
with b:
    st.markdown("**Maiores diferenças de empregados (RAIS − CNJ)**")
    d = m.reindex(m["dif_empregados"].abs().sort_values(ascending=False).index).head(10).copy()
    for col in ("clt_cnj", "vinc_rais", "dif_empregados"):
        d[col] = d[col].map(num)
    st.dataframe(d[["area", "clt_cnj", "vinc_rais", "dif_empregados"]].rename(columns={
        "area": "Município ou região", "clt_cnj": "CNJ", "vinc_rais": "RAIS", "dif_empregados": "Diferença"}),
        hide_index=True, width="stretch", column_config={"Município ou região": AJUDA_AREA})
    st.markdown("**Maiores diferenças de serventias (CNPJ − CNJ)**")
    s = consulta("SELECT area, n_cnj, n_cnpj, dif_serventias FROM qualidade.rec_municipio "
                 "ORDER BY abs(dif_serventias) DESC LIMIT 10")
    for col in ("n_cnj", "n_cnpj", "dif_serventias"):
        s[col] = s[col].map(num)
    st.dataframe(s.rename(columns={"area": "Município ou região", "n_cnj": "CNJ", "n_cnpj": "CNPJ",
                                   "dif_serventias": "Diferença"}), hide_index=True, width="stretch",
                 column_config={"Município ou região": AJUDA_AREA})
    st.caption("Municípios com menos de 3 serventias aparecem somados na sua região imediata do IBGE (LGPD).")

# ---- regra de classe e rateio
st.header("Sensibilidade das escolhas de modelagem")
a, b = st.columns(2)
with a:
    st.markdown(md_seguro("**Regra da Classe 1: R$ 300 mil (v2, base) × R$ 100 mil (v1)** — cenário regra mantida"))
    dif = consulta("SELECT * FROM gold.diferenca_regra_classe ORDER BY array_position(['min','base','max'], nivel)")
    st.dataframe(dif.assign(
        **{"Obrigadas v2 (≈)": dif.n_universo_v2.map(num), "Obrigadas v1 (≈)": dif.n_universo_v1.map(num),
           "Passivo v2": dif.passivo_universo_v2.map(brl), "Passivo v1": dif.passivo_universo_v1.map(brl),
           "Prêmio v2": dif.mercado_premio_emitido_v2.map(brl), "Prêmio v1": dif.mercado_premio_emitido_v1.map(brl)})
        [["nivel", "Obrigadas v2 (≈)", "Obrigadas v1 (≈)", "Passivo v2", "Passivo v1", "Prêmio v2", "Prêmio v1"]]
        .rename(columns={"nivel": "Nível"}), hide_index=True, width="stretch")
with b:
    st.markdown("**Método de rateio do passivo** — base, v2, regra mantida")
    sr = consulta("SELECT * FROM gold.sensibilidade_rateio")
    st.dataframe(sr.assign(**{"Déficit": sr.valor_descoberto.map(brl), "Com déficit": sr.n_deficit.map(aprox),
                              "Prêmio do mercado": sr.mercado_premio_emitido.map(brl)})
                 [["metodo_rateio", "Com déficit", "Déficit", "Prêmio do mercado"]].rename(
                     columns={"metodo_rateio": "Método"}), hide_index=True, width="stretch")
    st.caption("Todos os métodos distribuem o mesmo passivo municipal; muda só quem recebe cada parte.")
st.markdown("**Premissas e leituras da regra** — base, v2, regra mantida; uma mudança por linha")
sp = consulta("SELECT * FROM gold.sensibilidade_premissas")
ref_premio = float(sp.loc[sp["chave"] == "base", "mercado_premio_emitido"].iloc[0])
ref_passivo = float(sp.loc[sp["chave"] == "base", "passivo_universo"].iloc[0])
st.dataframe(pd.DataFrame({
    "Variação": sp["variacao"], "Providos acima de R$ 300 mil": sp["providos_acima_limite"].map(num),
    "Obrigadas (≈)": sp["n_universo"].map(num), "Passivo de todas as ativas": sp["passivo_todas"].map(brl),
    "Passivo dos obrigados": sp["passivo_universo"].map(brl),
    "Efeito no passivo dos obrigados": [pct(v / ref_passivo - 1) for v in sp["passivo_universo"]],
    "Prêmio do mercado": sp["mercado_premio_emitido"].map(brl),
    "Efeito no prêmio": [pct(v / ref_premio - 1) for v in sp["mercado_premio_emitido"]]}),
    hide_index=True, width="stretch",
    column_config={"Variação": st.column_config.TextColumn(width="large")})
e_ = execucao()
st.caption(md_seguro(
    f"**INPC:** salário da RAIS corrigido de dez/2025 até {str(int(e_.mes_inpc_final))[4:]}/"
    f"{str(int(e_.mes_inpc_final))[:4]} (fator {num(e_.fator_inpc, 4)}), como seria se a data-base fosse a da "
    "1ª declaração. **Reserva = MG inteiro:** como era antes da D-022. **Regra:** leituras alternativas dos R$ 300 mil "
    "(D-023); referências do BI do CNJ (exportado em 18/10/2026) para os providos: 928 nos dois semestres e 1.161 em "
    "algum semestre acima de R$ 300 mil; o silver tem 168 CNS a mais no 2º sem/2025, por isso os números diferem um "
    "pouco. A leitura principal ignora o semestre zerado."))

ORIGEM = {"municipio": "próprio município", "regiao": "região imediata", "estado": "MG inteiro"}
txt = "; ".join(f"{rotulo}: {num(RESUMO[f'distribuicao_{chave}_municipios'])} municípios "
                f"({num(RESUMO[f'distribuicao_{chave}_vinculos'])} vínculos próprios)"
                for chave, rotulo in ORIGEM.items() if f"distribuicao_{chave}_municipios" in RESUMO)
st.markdown(f"**Distribuição de salário × tempo de emprego** (limiar de 20 vínculos; reserva pela região imediata, "
            f"D-008 e D-022): {txt}.")

# ---- contratos
st.header("Contratos das tabelas")
c = consulta("SELECT * FROM qualidade.checagens ORDER BY camada DESC, violacoes DESC")
ok = int((c.violacoes == 0).sum())
st.markdown(f"**{ok} de {len(c)}** checagens sem violação. Erro interrompe o pipeline; aviso fica registrado aqui.")
c["Situação"] = [("✅ ok" if v == 0 else "⚠️ aviso" if s == "aviso" else "⛔ erro") for v, s in zip(c.violacoes, c.severidade)]
st.dataframe(c[["Situação", "camada", "tabela", "checagem", "severidade", "violacoes", "detalhe"]].rename(columns={
    "camada": "Camada", "tabela": "Tabela", "checagem": "Checagem", "severidade": "Severidade",
    "violacoes": "Violações", "detalhe": "Detalhe"}), hide_index=True, width="stretch")

# ---- limitações
st.header("Limitações declaradas")
st.markdown(md_seguro("""
- **Classe aproximada:** a arrecadação do Justiça Aberta não é igual à receita bruta do art. 2º, XXIV, do Prov. 213 (D-002).
- **Arrecadação:** 76 serventias com R$ 0 nos dois semestres de 2025 e 2 com valores conflitantes na fonte ficam com classe indeterminada (D-013, D-014). Elas são menores que as demais (3,5 empregados CLT em média, contra 5,9 nas não vagas com classe conhecida; 48 das 78 são vagas): dar a elas a proporção média tende a superestimar o universo; por isso o peso é 0 no mínimo.
- **Regra dos R$ 300 mil:** o semestre zerado é ignorado na média (D-023); 14 providos com 1º semestre acima de R$ 300 mil e 2º semestre zerado entram no universo pelo 1º semestre.
- **Passivo:** data-base 31/12/2025 (art. 4º do Prov. 227, D-020). A RAIS não traz a maior remuneração fixa (art. 6º): usa-se a remuneração de dezembro/2025, sem correção (a correção pelo INPC está só na tabela de sensibilidade). Verbas de convenção coletiva não estimadas (art. 5º, V). Estatutários, estagiários e terceirizados fora (D-003).
- **Empregados por serventia:** são a declaração ao CNJ de out/2026, não de 31/12/2025. Servem só como peso do rateio (proporção entre serventias), então a diferença de data afeta pouco.
- **Férias vencidas não gozadas:** a RAIS não informa; suposição de 0,5 período no base (0 no mínimo e 1 no máximo), aprovada na D-017.
- **Distribuição:** só vínculos por prazo indeterminado e com remuneração de dezembro (D-009, D-015). Os 887 sem remuneração de dezembro ficam fora da distribuição, mas não da contagem: 714 deles têm também remuneração média zero e 12 meses ou mais de casa, ou seja, são afastados de fato. Município com menos de 20 vínculos usa a distribuição da sua região imediata do IBGE e, se ela também for pequena, a de MG (D-022).
- **Déficit:** patrimônio dos titulares não é público; probabilidade e parte descoberta são suposições (D-016).
- **Seguro:** segurado da garantia não definido no art. 13; taxa e despesa administrativa são suposições; `desp_com` do SES é a despesa de comercialização inteira.
- **Colaboradores** autodeclarados ao CNJ, sem data por serventia. API do Justiça Aberta sem documentação oficial.
- **Contribuições de terceiros** fora do passivo (art. 5º, parágrafo único; STJ Tema 1228); Sistema S do titular pessoa física sem fonte oficial (D-018).
- **Municípios sem serventia:** Campo Azul: a serventia do município aparece no cadastro do CNJ com o município de Ubaí (correção prevista); Senador José Bento: motivo não identificado. Há 1 CNPJ ativo do CNAE 6912-5/00 em cada.
- **Agregação LGPD protege menos do que parece:** o rateio é proporcional aos empregados declarados ao CNJ, um número público, então qualquer pessoa consegue recalcular a estimativa de cada cartório a partir do total do município. A defesa é que se trata de **estimativa de mercado com premissas públicas**, e não de avaliação de nenhum cartório. Por isso as partições internas de uma mesma visão (por exemplo, passivo de todas as ativas − passivo dos obrigados numa área) não são suprimidas (D-028).
- **Auditoria de diferenças:** ataques combinando 3 ou mais visões não são auditados; o auditor cobre pares de visões e o resto das partições dos filtros.
"""))
e = execucao()
# o IPCA é coletado mas não entra em nenhuma conta: fica só na tabela de fontes (1.6)
rodape([f for f in NOMES_FONTE if f not in FONTES_NAO_USADAS],
       f"Execução do pipeline com premissas versão {int(e.versao_premissas)}.")
