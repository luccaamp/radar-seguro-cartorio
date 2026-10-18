"""Armadilhas do CSV do BI (seção 2), F1 (universo de MG) e F7 (totais Brasil). Só agregados."""
from comum import conectar, mostrar

con = conectar()
mostrar(con, "Formato: linhas por período (2025 e 2026)", """
    SELECT ano, sem, count(*) linhas, count(DISTINCT cns) cns, count(*) FILTER (WHERE atrib IS NULL) linhas_sem_atrib,
           count(*) FILTER (WHERE atrib IS NOT NULL) linhas_com_atrib, count(*) FILTER (WHERE custeio IS NULL) custeio_nulo
    FROM bi_p WHERE ano >= 2025 GROUP BY ALL ORDER BY ALL""")
mostrar(con, "Formato: armadilhas", """
    SELECT (SELECT count(*) FROM bi WHERE ini IS NULL) linhas_sem_data,
           (SELECT count(DISTINCT cns) FROM bi WHERE ini IS NULL) cns_sem_data,
           (SELECT coalesce(sum(arrec), 0) FROM bi WHERE ini IS NULL) arrec_sem_data,
           (SELECT count(*) FROM bi WHERE custeio < 0) custeio_negativo,
           (SELECT count(*) FROM (SELECT cns FROM bi_p WHERE ano = 2025 AND sem = 1 GROUP BY cns HAVING count(*) > 1)) cns_2_linhas_1s25""")
mostrar(con, "Formato: custeio repetido no 2º sem/2025 (CNS com mais de 1 linha)", """
    WITH g AS (SELECT cns, count(*) n, count(DISTINCT custeio) d FROM bi_p WHERE ano = 2025 AND sem = 2 GROUP BY cns HAVING n > 1)
    SELECT count(*) cns_multilinha, count(*) FILTER (WHERE d = 1) custeio_identico,
           (SELECT round(sum(custeio) / 1e9, 2) FROM bi_p WHERE ano = 2025 AND sem = 2) soma_ingenua_bi,
           (SELECT round(sum(c) / 1e9, 2) FROM (SELECT max(custeio) c FROM bi_p WHERE ano = 2025 AND sem = 2 GROUP BY cns)) um_por_cns_bi
    FROM g""")
mostrar(con, "Formato: idem só MG (cadastro Justiça Aberta)", """
    WITH g AS (SELECT b.cns, count(*) n, count(DISTINCT custeio) d FROM bi_p b JOIN cad_br c USING (cns)
               WHERE c.uf = 'MG' AND ano = 2025 AND sem = 2 GROUP BY b.cns HAVING n > 1)
    SELECT count(*) cns_multilinha_mg, count(*) FILTER (WHERE d = 1) custeio_identico_mg FROM g""")

mostrar(con, "F1: situação das ativas de MG no cadastro Justiça Aberta (silver)", """
    SELECT coalesce(situacao_juridica, '(vazia)') situacao, count(*) n FROM silver.serventia WHERE status = 'Ativo'
    GROUP BY ALL ORDER BY n DESC""")
mostrar(con, "F1: cruzamento cadastro × CSV", """
    WITH mg AS (SELECT cns FROM silver.serventia WHERE status = 'Ativo'),
         csv AS (SELECT DISTINCT cns FROM bi)
    SELECT (SELECT count(*) FROM mg) ativas_mg,
           (SELECT count(*) FROM mg WHERE cns NOT IN (SELECT cns FROM csv)) ativas_mg_fora_do_csv,
           (SELECT count(*) FROM csv) cns_no_csv,
           (SELECT count(*) FROM csv WHERE cns NOT IN (SELECT cns FROM cad_br)) csv_fora_de_todo_cadastro,
           (SELECT count(*) FROM csv WHERE cns IN (SELECT cns FROM cad_br WHERE uf = 'MG')) csv_com_uf_mg,
           (SELECT count(*) FROM csv WHERE cns IN (SELECT cns FROM cad_br WHERE uf = 'MG' AND status <> 'Ativo')) csv_mg_nao_ativo""")

mostrar(con, "F7: Brasil, cadastro Justiça Aberta (17/10/2026)", """
    SELECT count(DISTINCT cns) cns_distintos, count(*) FILTER (WHERE status = 'Ativo') ativos,
           count(*) FILTER (WHERE status = 'Ativo' AND situacao = 'PROVIDO') providos_ativos,
           count(*) FILTER (WHERE status = 'Ativo' AND cns NOT IN (SELECT cns FROM bi)) ativos_fora_do_csv
    FROM cad_br""")
mostrar(con, "F7: Brasil 2025 pelo CSV (ativas no cadastro Justiça Aberta)", """
    WITH a AS (SELECT cns, sum(arrec) arrec, sum(repasse) rep FROM bi_p WHERE ano = 2025 AND sem IS NOT NULL
               AND cns IN (SELECT cns FROM cad_br WHERE status = 'Ativo') GROUP BY cns),
         c AS (SELECT cns, sem, CASE WHEN sem = 2 THEN max(custeio) ELSE sum(custeio) END cus FROM bi_p
               WHERE ano = 2025 AND sem IS NOT NULL AND cns IN (SELECT cns FROM cad_br WHERE status = 'Ativo') GROUP BY cns, sem)
    SELECT count(*) cns, round(sum(arrec) / 1e9, 2) arrec_bi, round(sum(rep) / 1e9, 2) repasse_bi,
           (SELECT round(sum(cus) / 1e9, 2) FROM c) custeio_bi FROM a""")
mostrar(con, "F7: Brasil 2025 pelo CSV (todos os CNS com dado, sem filtro de cadastro)", """
    SELECT count(DISTINCT cns) cns, round(sum(arrec) / 1e9, 2) arrec_bi, round(sum(repasse) / 1e9, 2) repasse_bi
    FROM bi_p WHERE ano = 2025 AND sem IS NOT NULL""")
