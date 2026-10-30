"""C1, C2, C5, C6, D1, B1, F3 (mesmos CNS), F6 e F8: recálculo em memória (nada é gravado). Só agregados, sem nomes de cartório."""
import sys

import numpy as np
import pandas as pd
import yaml

from comum import RAIZ, conectar

sys.path.insert(0, str(RAIZ))
from src import estado  # noqa: E402
from src.model.distribuicao import preparar_vinculos  # noqa: E402
from src.model.passivo import passivo_municipio  # noqa: E402
from src.motor import calcular_serventias, peso_indeterminada, premissas_nivel, resumo_mercado  # noqa: E402
from src.transform.gold import carregar_insumos  # noqa: E402

con = conectar()
sem_ = estado.ler_semente()
L2 = yaml.safe_load((RAIZ / "config/regras_classificacao.yaml").read_text(encoding="utf-8"))["versoes"]["v2"]["limites"]
cen = yaml.safe_load((RAIZ / "config/cenarios_stf.yaml").read_text(encoding="utf-8"))
ins = carregar_insumos(con)
pb = premissas_nivel(sem_, "base", peso_indeterminada(ins.serventias, L2))
serv, med = calcular_serventias(ins, pb, L2)

# ---------- C1 (mesma tabela que reconciliacao.rec_municipio, recalculada)
rec = con.sql("""
    WITH cnj AS (SELECT s.cod_ibge, count(*) n_cnj, sum(k.clt) clt FROM silver.serventia s
                 LEFT JOIN silver.serventia_colaboradores k USING (cns) WHERE s.status = 'Ativo' GROUP BY 1),
         rais AS (SELECT cod_ibge, count(*) rais FROM silver.rais_vinculo WHERE ativo_31_12 GROUP BY 1),
         cnpj AS (SELECT cod_ibge, count(*) n_cnpj FROM silver.cnpj_estabelecimento WHERE situacao = 'ativa' AND cnae_principal GROUP BY 1)
    SELECT m.cod_ibge, m.regiao_imediata, coalesce(n_cnj, 0) n_cnj, coalesce(clt, 0) clt, coalesce(rais, 0) rais, coalesce(n_cnpj, 0) n_cnpj
    FROM silver.municipio_ibge m LEFT JOIN cnj USING (cod_ibge) LEFT JOIN rais USING (cod_ibge) LEFT JOIN cnpj USING (cod_ibge)""").df()
x = rec[(rec.clt > 0) | (rec.rais > 0)]
pos = x[(x.clt > 0) & (x.rais > 0)]
f5 = x[(x.clt >= 5) | (x.rais >= 5)]
erro = (f5.rais - f5.clt).abs() / f5.clt.where(f5.clt > 0)
print("## C1: CNJ (CLT) × RAIS por município")
print(f"  municípios com dado {len(x)} | correlação bruta {x.clt.corr(x.rais):.3f} | sem BH {x[x.clt < 1000].clt.corr(x[x.clt < 1000].rais):.3f}"
      f" | correlação em log (ambos > 0) {np.log(pos.clt).corr(np.log(pos.rais)):.3f}")
print(f"  com >= 5 em uma das fontes: {len(f5)} | erro % mediano {erro.median():.1%} | dentro de ±20%: {(erro <= 0.20).mean():.1%}"
      f" | CNJ = 0 nesses: {int((f5.clt == 0).sum())}")
print(f"  zero em uma das fontes (escondidos no gráfico log): CNJ 0 e RAIS > 0: {int(((x.clt == 0) & (x.rais > 0)).sum())};"
      f" RAIS 0 e CNJ > 0: {int(((x.rais == 0) & (x.clt > 0)).sum())}")

# ---------- D1
x = x.assign(dif_e=(x.rais - x.clt).abs())
top_e = x.nlargest(10, "dif_e")
r2 = rec.assign(dif_s=(rec.n_cnpj - rec.n_cnj).abs()).nlargest(10, "dif_s")
print("\n## D1: exposição de municípios com menos de 3 serventias (contagens, sem nomes)")
print(f"  top 10 RAIS − CNJ: {int((top_e.n_cnj < 3).sum())} com < 3 serventias | top 10 CNPJ − CNJ: {int((r2.n_cnj < 3).sum())}"
      f" | pontos do gráfico com < 3 serventias: {int((x.n_cnj < 3).sum())} de {len(x)}")

# ---------- C2
p_ = pb
v = preparar_vinculos(ins.rais, p_["base_remuneracao_rais"], ins.fator_inpc)
pm = passivo_municipio(v, p_)
lim = int(p_["limiar_vinculos_distribuicao_municipal"])
abaixo = set(pm[pm.n_vinculos < lim].cod_ibge)
est_todos = passivo_municipio(v.assign(_u=0), p_, "_u").passivo_medio_vinculo.iloc[0]
est_abaixo = passivo_municipio(v[v.cod_ibge.isin(abaixo)].assign(_u=0), p_, "_u").passivo_medio_vinculo.iloc[0]
bh = 3106200
est_sem_bh = passivo_municipio(v[v.cod_ibge != bh].assign(_u=0), p_, "_u").passivo_medio_vinculo.iloc[0]
print("\n## C2: distribuição 'estado'")
print(f"  usa TODOS os vínculos de MG ({len(v)}, inclusive BH): passivo médio por vínculo R$ {est_todos:,.0f}"
      f" | só municípios abaixo do limiar ({int(v.cod_ibge.isin(abaixo).sum())} vínculos): R$ {est_abaixo:,.0f} | MG sem BH: R$ {est_sem_bh:,.0f}")
reg = con.sql("SELECT cod_ibge, regiao_imediata FROM silver.municipio_ibge").df()
vr = v.merge(reg, on="cod_ibge", how="left")
pr = passivo_municipio(vr, p_, "regiao_imediata").set_index("regiao_imediata")
mm = med.merge(reg, on="cod_ibge", how="left")
alt = []
for r in mm.itertuples():
    if r.origem_distribuicao == "municipio":
        alt.append((r.passivo_medio_vinculo, "municipio"))
    elif r.regiao_imediata in pr.index and pr.at[r.regiao_imediata, "n_vinculos"] >= lim:
        alt.append((pr.at[r.regiao_imediata, "passivo_medio_vinculo"], "regiao"))
    else:
        alt.append((est_todos, "estado"))
mm["alt"], mm["origem_alt"] = [a for a, _ in alt], [o for _, o in alt]
clt_mun = ins.serventias.groupby("cod_ibge").clt.sum()
mm["clt"] = mm.cod_ibge.map(clt_mun).fillna(0)
atual, novo = (mm.clt * mm.passivo_medio_vinculo).sum(), (mm.clt * mm.alt).sum()
print(f"  reserva pela região imediata (limiar {lim}): origens {mm.origem_alt.value_counts().to_dict()}"
      f" | passivo de todas as ativas R$ {atual/1e6:.1f} mi -> R$ {novo/1e6:.1f} mi ({novo/atual-1:+.1%})")
peq = mm[mm.origem_distribuicao == "estado"]
print(f"  só municípios que hoje usam 'estado': R$ {(peq.clt*peq.passivo_medio_vinculo).sum()/1e6:.1f} mi -> "
      f"R$ {(peq.clt*peq.alt).sum()/1e6:.1f} mi")

# ---------- C5
print("\n## C5: rastreabilidade das fontes (silver.fonte_metadados)")
fm = con.sql("SELECT fonte, url IS NULL sem_url, length(coletado_em) < 11 sem_hora, data_referencia FROM silver.fonte_metadados").df()
print("  sem URL:", fm[fm.sem_url].fonte.tolist(), "| sem hora de coleta:", fm[fm.sem_hora].fonte.tolist())
print("  data de referência = dia do download:", fm[fm.data_referencia.isin(["2026-10-17", "2026-10-18"])].fonte.tolist())

# ---------- C6
print("\n## C6: os 887 vínculos ativos, indeterminados e sem remuneração de dezembro")
r = ins.rais
z = r[r.ativo_31_12 & r.prazo_indeterminado & (r.rem_dezembro.fillna(0) == 0)]
print(f"  n {len(z)} | admitidos em dezembro {int((z.mes_admissao == 12).sum())} | com rem. média > 0 {int((z.rem_media.fillna(0) > 0).sum())}"
      f" | tempo de emprego mediano {z.tempo_emprego_meses.median():.0f} meses | com 12+ meses {int((z.tempo_emprego_meses >= 12).sum())}")
print(f"  com remuneração média zero e 12+ meses de casa (afastados o ano inteiro?): {int(((z.rem_media.fillna(0) == 0) & (z.tempo_emprego_meses >= 12)).sum())}")
cnpj2 = con.sql("SELECT cod_ibge, count(*) FROM silver.cnpj_estabelecimento WHERE cod_ibge IN (3111150, 3165800) AND situacao = 'ativa' GROUP BY 1").fetchall()
print("  CNPJ ativos nos 2 municípios sem serventia no CNJ:", cnpj2)

# ---------- B1
print("\n## B1: dados de vacância no cadastro (data da decisão da situação jurídica, MG, ativas)")
vac = con.sql("""SELECT year(data_situacao) ano, count(*) FILTER (WHERE situacao_juridica = 'VAGO') vago,
                        count(*) FILTER (WHERE situacao_juridica = 'PROVIDO') provido
                 FROM silver.serventia WHERE status = 'Ativo' AND data_situacao IS NOT NULL GROUP BY 1 ORDER BY 1""").df()
print("  " + " | ".join(f"{int(a)}: V{int(b)} P{int(c)}" for a, b, c in vac[vac.ano >= 2015].itertuples(index=False)))
sem_data = con.sql("SELECT count(*) FROM silver.serventia WHERE status='Ativo' AND data_situacao IS NULL").fetchone()[0]
print(f"  sem data: {sem_data}")
ses = con.sql("""SELECT ramo, sum(sinistro_ocorrido)/sum(premio_ganho) sin_ganho, sum(sinistro_ocorrido)/sum(premio_emitido2) sin_emit,
                 sum(premio_ganho)/sum(premio_emitido2) ganho_emit FROM silver.susep_garantia
                 WHERE ano_mes BETWEEN 202009 AND 202608 GROUP BY 1 ORDER BY 1""").df()
print("  SES set/2020–ago/2026:", ses.round(3).to_dict("records"))

# ---------- F3: os 2 conflitos de 2025 são os mesmos?
b = set(con.sql("""SELECT b.cns FROM bi_p b WHERE ano = 2025 AND sem = 1 AND atrib IS NULL AND b.cns IN
                   (SELECT cns FROM silver.serventia) GROUP BY b.cns HAVING count(*) > 1""").df().cns)
s = set(con.sql("SELECT DISTINCT cns FROM silver.serventia_arrecadacao WHERE ano = 2025 AND conflito_fonte").df().cns)
print(f"\n## F3: conflitos de 2025 em MG: BI {len(b)}, silver {len(s)}, em comum {len(b & s)}")

# ---------- F6
bi = con.sql("""SELECT cns, sum(arrec) arrec, sum(repasse) repasse, sum(custeio) custeio,
                bool_and(custeio IS NOT NULL) custeio_ok FROM (
                  SELECT cns, sem, sum(arrec) arrec, sum(repasse) repasse,
                         CASE WHEN sem = 2 THEN max(custeio) ELSE sum(custeio) END custeio
                  FROM bi_p WHERE ano = 2025 AND sem IS NOT NULL GROUP BY cns, sem) GROUP BY cns""").df()
sv = serv.merge(bi, on="cns", how="left")
sv["saldo"] = sv.arrec - sv.repasse - sv.custeio
print("\n## F6: custeio × folha RAIS com encargos, por área (municípios com >= 3 serventias; demais pela região imediata)")
enc = pb["inss_patronal"] + pb["rat"] * pb["fap"] + pb["aliquota_fgts"]
folha = ins.rais[ins.rais.ativo_31_12].assign(f=lambda d: d.rem_media.fillna(0) * 13.333 * (1 + enc))
folha = folha.merge(reg, on="cod_ibge", how="left")
sv = sv.merge(reg, on="cod_ibge", how="left")
nmun = sv.groupby("cod_ibge").cns.transform("size")
sv["area"] = np.where(nmun >= 3, sv.cod_ibge.astype(str), "R:" + sv.regiao_imediata.astype(str))
nmun_f = folha.cod_ibge.map(sv.groupby("cod_ibge").size()).fillna(0)
folha["area"] = np.where(nmun_f >= 3, folha.cod_ibge.astype("Int64").astype(str), "R:" + folha.regiao_imediata.astype(str))
a = sv.groupby("area").agg(custeio=("custeio", "sum"), n=("cns", "size")).join(folha.groupby("area").f.sum().rename("folha"), how="left").fillna(0)
print(f"  áreas {len(a)} | custeio < folha: {int((a.custeio < a.folha).sum())} | custeio MG R$ {a.custeio.sum()/1e6:.0f} mi; folha RAIS c/ encargos R$ {a.folha.sum()/1e6:.0f} mi")
print("\n## F6: passivo dos obrigados ÷ saldo anual 2025 (base v2; serventias com peso > 0; contagens e somas)")
u = sv[sv.peso_universo > 0].copy()
u["meses"] = np.where(u.saldo > 0, 12 * u.passivo / u.saldo, np.nan)
u["faixa"] = np.select([u.saldo.isna() | ~u.custeio_ok.fillna(False).astype(bool), u.saldo <= 0, u.meses < 3, u.meses <= 12],
                       ["sem custeio/dado", "saldo <= 0", "< 3 meses", "3 a 12 meses"], "> 12 meses")
t = u.groupby("faixa").agg(serventias=("cns", "size"), peso=("peso_universo", "sum"), passivo_mi=("passivo", lambda q: q.sum() / 1e6),
                           saldo_mi=("saldo", lambda q: q.sum() / 1e6))
print(t.round(1).to_string())
ok = u[u.saldo > 0]
print(f"  agregado (saldo > 0): passivo R$ {ok.passivo.sum()/1e6:.1f} mi ÷ saldo R$ {ok.saldo.sum()/1e6:.1f} mi = {12*ok.passivo.sum()/ok.saldo.sum():.2f} meses de saldo")

# ---------- F8: ponte com o estudo externo (passivo de MG R$ 461,5 mi; 11,5% da arrecadação)
print("\n## F8: ponte do passivo de MG (estudo externo × modelo)")
prov = sv[sv.situacao_juridica == "PROVIDO"]
seu_univ = prov[(prov.arrec.notna())]
# universo do estudo: providos com os dois semestres > 300 mil no BI (R$ 4,02 bi; 461,5 ÷ 4.018 = 11,5%)
s12 = con.sql("""SELECT cns FROM (SELECT cns, sem, sum(arrec) a FROM bi_p WHERE ano = 2025 AND sem IS NOT NULL GROUP BY cns, sem)
                 GROUP BY cns HAVING count(*) FILTER (WHERE a > 300000) = 2""").df().cns
e = sv[sv.cns.isin(set(s12)) & (sv.situacao_juridica == "PROVIDO")]
print(f"  universo 'dois semestres > 300 mil' (providos): {len(e)} serventias, arrecadação R$ {e.arrec.sum()/1e6:.0f} mi;"
      f" 11,5% disso = R$ {0.115*e.arrec.sum()/1e6:.1f} mi")
# premissas do estudo aplicadas ao nosso método: 10 anos fixos, INSS em aviso e férias, RAT 2%
alt = {"rat": 0.02, "incidencias": {"aviso_previo_indenizado": {"fgts": True, "inss": True},
                                    "decimo_terceiro": {"fgts": True, "inss": True},
                                    "ferias_indenizadas": {"fgts": False, "inss": True}}}
pe = premissas_nivel(sem_, "base", peso_indeterminada(ins.serventias, L2), alt)
ins10 = type(ins)(rais=ins.rais.assign(tempo_emprego_meses=120.0), serventias=ins.serventias, fator_inpc=ins.fator_inpc, mes_inpc=ins.mes_inpc)
se, _ = calcular_serventias(ins10, pe, L2)
p_est_premissas = se[se.cns.isin(e.cns)].passivo.sum()
p_nos_premissas = sv[sv.cns.isin(e.cns)].passivo.sum()
p_univ = (serv.passivo * serv.peso_universo).sum()
print(f"  nosso método + premissas do estudo, universo do estudo: R$ {p_est_premissas/1e6:.1f} mi")
print(f"  nosso método + nossas premissas, universo do estudo: R$ {p_nos_premissas/1e6:.1f} mi")
print(f"  nosso método + nossas premissas, nosso universo (esperado): R$ {p_univ/1e6:.1f} mi")
rb = resumo_mercado(serv, pb, cen, "mantem")
print(f"  ponte do prêmio (nosso): passivo do universo {p_univ/1e6:.1f} -> déficit {rb['valor_descoberto']/1e6:.1f} -> IS {rb['mercado_importancia_segurada']/1e6:.1f}"
      f" -> prêmio {rb['mercado_premio_emitido']/1e6:.3f} mi | estudo (MG): 461,5 × 100% × 70% × 1% = R$ {461.5*0.7*0.01:.2f} mi")
