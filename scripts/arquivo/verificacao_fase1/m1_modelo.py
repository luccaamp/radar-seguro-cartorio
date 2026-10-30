"""A1, A2, A3, A4, C3, C6, B3, E4: recálculo EM MEMÓRIA com o mesmo motor do pipeline (nada é gravado). Só agregados."""
import sys

import pandas as pd
import yaml

from comum import RAIZ, conectar

sys.path.insert(0, str(RAIZ))
from src import estado  # noqa: E402
from src.model.passivo import passivo_por_vinculo  # noqa: E402
from src.model.universo import classificar  # noqa: E402
from src.motor import calcular_serventias, peso_indeterminada, premissas_nivel, resumo_mercado  # noqa: E402
from src.transform.gold import carregar_insumos  # noqa: E402

pd.set_option("display.width", 200)
con = conectar()
semente = estado.ler_semente()
regras = yaml.safe_load((RAIZ / "config/regras_classificacao.yaml").read_text(encoding="utf-8"))
cen = yaml.safe_load((RAIZ / "config/cenarios_stf.yaml").read_text(encoding="utf-8"))
ins = carregar_insumos(con)
L = {r: regras["versoes"][r]["limites"] for r in ("v1", "v2")}
peso = {r: peso_indeterminada(ins.serventias, L[r]) for r in L}
print("versão das premissas no gold (parquet):", con.sql("SELECT DISTINCT versao_premissas FROM gold.execucao").fetchall(),
      "| semente:", semente["versao"])
print("A1: peso da classe indeterminada por regra:", {r: round(v, 4) for r, v in peso.items()})


def rodar(regra, nivel, ajustes=None, limites_faixa=None, metodo=None, insumos=None):
    p = premissas_nivel(semente, nivel, peso[regra], ajustes)
    s, med = calcular_serventias(insumos or ins, p, L[regra], metodo)
    if limites_faixa is not None:  # faixas de déficit pela classe de outra regra (A1)
        from src.model.mercado import deficit
        s = deficit(s.assign(classe=[classificar(r, limites_faixa) for r in s["receita_ref"]]), p)
    return s, p, med


# reprodução do gold
g = con.sql("SELECT * FROM gold.fato_mercado_uf WHERE cenario_stf = 'mantem'").df().set_index(["nivel", "regra_classe"])
R = {}
for regra in ("v2", "v1"):
    for nivel in ("min", "base", "max"):
        s, p, _ = rodar(regra, nivel)
        R[(nivel, regra)] = (s, p, resumo_mercado(s, p, cen, "mantem"))
dif = max(abs(R[k][2]["mercado_premio_emitido"] - g.at[k, "mercado_premio_emitido"]) for k in R)
print(f"reprodução do gold (prêmio, 6 combinações): maior diferença R$ {dif:.6f}")

print("\n## A1: classe usada nas faixas de déficit, serventias com peso > 0 no universo (base)")
for regra in ("v2", "v1"):
    s = R[("base", regra)][0]
    u = s[s.peso_universo > 0]
    print(f"  {regra}: " + ", ".join(f"classe {c}: {n}" for c, n in u["classe"].value_counts().sort_index().items())
          + f" | universo esperado {u.peso_universo.sum():.1f}")
print("  regra v1 com faixas pela classe v2 (correção pedida), cenário mantém:")
print("  nivel | univ v2 | univ v1 | déficit v2 | déficit v1 atual | déficit v1 corrigido | prêmio v2 | prêmio v1 atual | prêmio v1 corrigido")
for nivel in ("min", "base", "max"):
    s2, p2, r2 = R[(nivel, "v2")]
    s1, p1, r1 = R[(nivel, "v1")]
    # correção: classe v2 nas faixas E peso da indeterminada da v2 (o mesmo conjunto de indeterminadas)
    pc = premissas_nivel(semente, nivel, peso["v2"])
    sc, _ = calcular_serventias(ins, pc, L["v1"])
    from src.model.mercado import deficit
    sc = deficit(sc.assign(classe=[classificar(r, L["v2"]) for r in sc["receita_ref"]]), pc)
    rc = resumo_mercado(sc, pc, cen, "mantem")
    print(f"  {nivel:5s} | {r2['n_universo']:7.1f} | {rc['n_universo']:7.1f} | {r2['valor_descoberto']/1e6:10.2f} | "
          f"{r1['valor_descoberto']/1e6:16.2f} | {rc['valor_descoberto']/1e6:20.2f} | {r2['mercado_premio_emitido']/1e3:9.1f} | "
          f"{r1['mercado_premio_emitido']/1e3:15.1f} | {rc['mercado_premio_emitido']/1e3:19.1f}")

print("\n## A4: zero CLT no universo (v2, cenário mantém)")
for nivel in ("min", "base", "max"):
    s, p, r = R[(nivel, "v2")]
    u = s[s.peso_universo > 0]
    z = u[u["clt"].fillna(0) == 0]
    print(f"  {nivel}: universo {u.peso_universo.sum():.1f} | com 0 CLT: {len(z)} serventias (peso {z.peso_universo.sum():.1f}) "
          f"| 'com déficit' {s.n_deficit.sum():.1f}, dos quais 0 CLT {z.n_deficit.sum():.1f} | déficit dessas R$ {z.valor_descoberto.sum():.0f}")

print("\n## A3: vínculo de exemplo (R$ 3.000, 64 meses), premissas base")
pb = R[("base", "v2")][1]
v = passivo_por_vinculo(3000.0, 64, pb)
print("  " + ", ".join(f"{k} {getattr(v, k):,.2f}" for k in ("aviso_previo", "decimo_terceiro", "ferias", "multa_fgts",
                                                              "fgts_rescisorio", "inss_patronal", "rat_fap"))
      + f" | total {v.total:,.2f} | dias aviso {v.dias_aviso}, avos 13º {v.avos_13}, avos férias {v.avos_ferias}")
vs = passivo_por_vinculo(3000.0, 6, pb)
print(f"  com 6 meses de casa: dias aviso {vs.dias_aviso}, avos 13º {vs.avos_13} (13º R$ {vs.decimo_terceiro:,.2f})")
print(f"  data_posicao = {pb['data_posicao']} | 13º quitado na data-base = {pb['decimo_terceiro_quitado_na_data_base']}")

print("\n## A2: efeito de tirar a correção INPC (data-base única 31/12/2025), base v2")
s0, p0, r0 = rodar("v2", "base", {"correcao_salarial_rais": "sem_correcao"})
r0 = resumo_mercado(s0, p0, cen, "mantem")
rb = R[("base", "v2")][2]
for k in ("passivo_todas", "passivo_universo", "valor_descoberto", "mercado_importancia_segurada", "mercado_premio_emitido"):
    print(f"  {k}: {rb[k]/1e6:.2f} -> {r0[k]/1e6:.2f} mi ({r0[k]/rb[k]-1:+.2%})")
print(f"  fator INPC no gold: {ins.fator_inpc:.4f} ({ins.mes_inpc})")

print("\n## C3: perfil das indeterminadas (todas as ativas)")
sv = R[("base", "v2")][0]
ind = sv[sv.classe == "indeterminada"]
print("  por origem:", ind.origem_receita.value_counts().to_dict(), "| por situação:", ind.situacao_juridica.value_counts().to_dict())
print(f"  CLT: total {ind.clt.sum():.0f}, média {ind.clt.mean():.2f}, zero CLT {int((ind.clt.fillna(0) == 0).sum())} "
      f"| média de CLT das conhecidas não vagas: {sv[(sv.classe != 'indeterminada') & (sv.situacao_juridica != 'VAGO')].clt.mean():.2f}")
print("  atribuição (top 4):", ind.atribuicoes.value_counts().head(4).to_dict())
print(f"  peso no min: {R[('min', 'v2')][1]['peso_classe_indeterminada_base']} | base {pb['peso_classe_indeterminada_base']:.4f} | max {R[('max', 'v2')][1]['peso_classe_indeterminada_base']}")
ip = ind[ind.situacao_juridica == "PROVIDO"]
print(f"  providos indeterminados {len(ip)} -> peso no universo base {ip.peso_universo.sum():.1f}; "
      f"providos com classe 2/3 {int(((sv.situacao_juridica == 'PROVIDO') & sv.classe.isin(['2', '3'])).sum())}")

print("\n## C6: universo fracionário e municípios")
print(f"  universo base v2 = {rb['n_universo']:.2f} (esperado; peso {pb['peso_classe_indeterminada_base']:.3f} × indeterminadas)")
mun = con.sql("""SELECT nome, cod_ibge FROM silver.municipio_ibge WHERE cod_ibge NOT IN
                 (SELECT cod_ibge FROM silver.serventia WHERE status = 'Ativo' AND cod_ibge IS NOT NULL)""").df()
print("  municípios IBGE sem serventia ativa no CNJ:", mun.to_dict("records"))
for _, m in mun.iterrows():
    n = con.sql(f"SELECT count(*), count(*) FILTER (WHERE status='Ativo') FROM silver.serventia WHERE cod_ibge = {m.cod_ibge}").fetchone()
    print(f"    {m.nome}: registros no CNJ {n[0]} (ativos {n[1]})")
print("  serventias ativas sem cod_ibge:", con.sql("SELECT count(*) FROM silver.serventia WHERE status='Ativo' AND cod_ibge IS NULL").fetchone()[0])

print("\n## B3 / E4: apólices, médias e teto (v2, mantém)")
for nivel in ("min", "base", "max"):
    s, p, r = R[(nivel, "v2")]
    apol = r["n_deficit"] * p["escolha_garantia"]["seguro"] * p["fracao_exigencia_garantia"]
    teto = r["passivo_universo"] * p["taxa_seguro_anual"]
    print(f"  {nivel}: apólices {apol:.0f} (seguradora {apol*p['market_share_hipotetico']:.1f}) | IS média R$ "
          f"{r['mercado_importancia_segurada']/apol if apol else 0:,.0f} | prêmio médio R$ {r['mercado_premio_emitido']/apol if apol else 0:,.0f}"
          f" | teto (passivo do universo × taxa {p['taxa_seguro_anual']:.3f}) R$ {teto/1e6:.2f} mi | combinado "
          f"{p['sinistralidade']+p['comissao']+p['despesa_administrativa']:.1%}")
