"""F2 (arrecadação 2025 de MG: silver × BI), F3 (conflitos), F4 (semestre faltando) e F5 (leituras da regra). Só agregados."""
from comum import conectar, mostrar

con = conectar()
con.execute("""
CREATE TABLE mg AS SELECT cns, situacao_juridica FROM silver.serventia WHERE status = 'Ativo';
-- BI: soma de todas as linhas do CNS no semestre (o 2º sem/2025 vem dividido por atribuição)
CREATE TABLE bi25 AS SELECT b.cns, sem, count(*) linhas, sum(arrec) arrec, sum(repasse) repasse,
    CASE WHEN sem = 2 THEN max(custeio) ELSE sum(custeio) END custeio
    FROM bi_p b JOIN mg USING (cns) WHERE ano = 2025 AND sem IS NOT NULL GROUP BY b.cns, sem;
-- silver: uma linha por CNS × período × versão da fonte
CREATE TABLE sv25 AS SELECT cns, semestre::INT sem, count(*) versoes, bool_or(conflito_fonte) conflito,
    max(arrecadacao) FILTER (WHERE versao = 1) v1, sum(arrecadacao) soma_versoes, bool_and(informado) informado
    FROM silver.serventia_arrecadacao WHERE ano = 2025 AND semestre IS NOT NULL AND cns IN (SELECT cns FROM mg)
    GROUP BY cns, semestre;
""")
mostrar(con, "F2: total de MG por semestre, 2.525 ativas (R$ mi)", """
    SELECT sem, (SELECT count(*) FROM bi25 b WHERE b.sem = s.sem) cns_bi, round((SELECT sum(arrec) FROM bi25 b WHERE b.sem = s.sem) / 1e6, 1) bi,
           count(*) cns_silver, round(sum(v1) / 1e6, 1) silver_versao1, round(sum(soma_versoes) / 1e6, 1) silver_soma_versoes,
           max(versoes) max_versoes
    FROM sv25 s GROUP BY sem ORDER BY sem""")
mostrar(con, "F2: CNS a CNS (silver versão 1 × BI), divergência > 1%", """
    SELECT sem, count(*) FILTER (WHERE b.cns IS NULL) sem_linha_no_bi,
           count(*) FILTER (WHERE b.cns IS NOT NULL AND abs(coalesce(s.v1, 0) - b.arrec) > 0.01 * greatest(abs(b.arrec), 1)) divergem,
           count(*) FILTER (WHERE b.cns IS NOT NULL AND abs(coalesce(s.v1, 0) - b.arrec) > 0.01 * greatest(abs(b.arrec), 1) AND s.v1 = 0) silver_zero_bi_positivo,
           round(sum(coalesce(s.v1, 0) - coalesce(b.arrec, 0)) FILTER (WHERE abs(coalesce(s.v1, 0) - coalesce(b.arrec, 0)) > 0.01 * greatest(abs(coalesce(b.arrec, 0)), 1)) / 1e6, 1) dif_mi
    FROM sv25 s LEFT JOIN bi25 b USING (cns, sem) GROUP BY sem ORDER BY sem""")
mostrar(con, "F2: 2º sem/2025, CNS em que silver e BI divergem, por tipo", """
    SELECT CASE WHEN b.cns IS NULL THEN 'sem linha no BI' WHEN s.v1 = 0 AND b.arrec > 0 THEN 'silver 0, BI > 0'
                WHEN s.v1 > 0 AND coalesce(b.arrec, 0) = 0 THEN 'silver > 0, BI 0' ELSE 'os dois > 0, valores diferentes' END tipo,
           count(*) n, round(sum(coalesce(s.v1, 0)) / 1e6, 1) silver_mi, round(sum(coalesce(b.arrec, 0)) / 1e6, 1) bi_mi
    FROM sv25 s LEFT JOIN bi25 b USING (cns, sem)
    WHERE s.sem = 2 AND (b.cns IS NULL OR abs(coalesce(s.v1, 0) - b.arrec) > 0.01 * greatest(abs(b.arrec), 1)) GROUP BY 1""")

mostrar(con, "F3: pares CNS-período de MG com mais de 1 linha total (BI, atribuição '-') e no silver, por ano", """
    WITH bi AS (SELECT ano, count(*) n FROM (SELECT b.cns, ini, fim, any_value(year(ini)) ano FROM bi_p b JOIN mg USING (cns)
                WHERE atrib IS NULL AND ini IS NOT NULL GROUP BY b.cns, ini, fim HAVING count(*) > 1) GROUP BY ano),
         sv AS (SELECT ano, count(*) pares, count(*) FILTER (WHERE c) pares_conflito, sum(n) FILTER (WHERE c) linhas_conflito
                FROM (SELECT cns, ano, periodo_inicio, count(*) n, bool_or(conflito_fonte) c FROM silver.serventia_arrecadacao
                      WHERE cns IN (SELECT cns FROM mg) GROUP BY ALL HAVING count(*) > 1) GROUP BY ano)
    SELECT coalesce(bi.ano, sv.ano) ano, coalesce(bi.n, 0) pares_bi, coalesce(sv.pares, 0) pares_silver,
           coalesce(sv.pares_conflito, 0) pares_conflito_silver, coalesce(sv.linhas_conflito, 0) linhas_conflito_silver
    FROM bi FULL JOIN sv ON bi.ano = sv.ano ORDER BY 1""", 40)
mostrar(con, "F3: totais do silver (todas as serventias do silver, inclusive inativas)", """
    SELECT count(*) FILTER (WHERE conflito_fonte) linhas_conflito_todas,
           count(*) FILTER (WHERE conflito_fonte AND cns IN (SELECT cns FROM mg)) linhas_conflito_ativas,
           (SELECT count(*) FROM (SELECT cns, periodo_inicio FROM silver.serventia_arrecadacao WHERE conflito_fonte GROUP BY ALL)) pares_conflito_todas
    FROM silver.serventia_arrecadacao""")

mostrar(con, "F4: situação dos semestres de 2025 (2.525 ativas)", """
    WITH x AS (SELECT m.cns,
          (SELECT arrec FROM bi25 b WHERE b.cns = m.cns AND sem = 1) b1, (SELECT arrec FROM bi25 b WHERE b.cns = m.cns AND sem = 2) b2,
          (SELECT v1 FROM sv25 s WHERE s.cns = m.cns AND sem = 1) s1, (SELECT v1 FROM sv25 s WHERE s.cns = m.cns AND sem = 2) s2
        FROM mg m)
    SELECT 'BI' fonte, count(*) FILTER (WHERE b1 IS NULL) sem_linha_1s, count(*) FILTER (WHERE b2 IS NULL) sem_linha_2s,
           count(*) FILTER (WHERE b1 = 0) zero_1s, count(*) FILTER (WHERE b2 = 0) zero_2s,
           count(*) FILTER (WHERE coalesce(b1, 0) = 0 AND coalesce(b2, 0) = 0) zero_ou_ausente_nos_dois,
           count(*) FILTER (WHERE (coalesce(b1, 0) > 0) <> (coalesce(b2, 0) > 0)) positivo_em_um_so FROM x
    UNION ALL
    SELECT 'silver', count(*) FILTER (WHERE s1 IS NULL), count(*) FILTER (WHERE s2 IS NULL), count(*) FILTER (WHERE s1 = 0),
           count(*) FILTER (WHERE s2 = 0), count(*) FILTER (WHERE coalesce(s1, 0) = 0 AND coalesce(s2, 0) = 0),
           count(*) FILTER (WHERE (coalesce(s1, 0) > 0) <> (coalesce(s2, 0) > 0)) FROM x""")
mostrar(con, "F4: 1º sem/2025 > R$ 300 mil e 2º sem ausente ou zero (situação)", """
    SELECT m.situacao_juridica, count(*) FILTER (WHERE b2.cns IS NULL OR b2.arrec = 0) bi,
           count(*) FILTER (WHERE coalesce(s2.v1, 0) = 0) silver
    FROM mg m JOIN bi25 b1 ON b1.cns = m.cns AND b1.sem = 1 AND b1.arrec > 300000
    LEFT JOIN bi25 b2 ON b2.cns = m.cns AND b2.sem = 2 LEFT JOIN sv25 s2 ON s2.cns = m.cns AND s2.sem = 2
    GROUP BY ALL ORDER BY 1""")

mostrar(con, "F5: leituras da regra dos R$ 300 mil, providos de MG, 2025 (BI; ausente = não passa)", """
    WITH p AS (SELECT m.cns, coalesce(max(arrec) FILTER (WHERE sem = 1), 0) a1, coalesce(max(arrec) FILTER (WHERE sem = 2), 0) a2
               FROM mg m LEFT JOIN bi25 b USING (cns) WHERE m.situacao_juridica = 'PROVIDO' GROUP BY m.cns)
    SELECT 'dois semestres > 300 mil' leitura, count(*) FILTER (WHERE a1 > 3e5 AND a2 > 3e5) n,
           round(sum(a1 + a2) FILTER (WHERE a1 > 3e5 AND a2 > 3e5) / 1e9, 2) arrec_bi FROM p
    UNION ALL SELECT 'média anual > 600 mil', count(*) FILTER (WHERE a1 + a2 > 6e5), round(sum(a1 + a2) FILTER (WHERE a1 + a2 > 6e5) / 1e9, 2) FROM p
    UNION ALL SELECT '2º semestre > 300 mil', count(*) FILTER (WHERE a2 > 3e5), round(sum(a1 + a2) FILTER (WHERE a2 > 3e5) / 1e9, 2) FROM p
    UNION ALL SELECT 'algum semestre > 300 mil', count(*) FILTER (WHERE a1 > 3e5 OR a2 > 3e5), round(sum(a1 + a2) FILTER (WHERE a1 > 3e5 OR a2 > 3e5) / 1e9, 2) FROM p
    UNION ALL SELECT 'código atual: média dos semestres > 0 (silver)', count(*) FILTER (WHERE r > 3e5), round(sum(t) FILTER (WHERE r > 3e5) / 1e9, 2)
        FROM (SELECT s.cns, avg(v1) FILTER (WHERE v1 > 0) r, sum(v1) t, bool_or(conflito) c FROM sv25 s JOIN mg m USING (cns)
              WHERE m.situacao_juridica = 'PROVIDO' GROUP BY s.cns) WHERE NOT c
    UNION ALL SELECT 'idem, com a regra do código aplicada ao BI', count(*) FILTER (WHERE r > 3e5), round(sum(t) FILTER (WHERE r > 3e5) / 1e9, 2)
        FROM (SELECT b.cns, avg(arrec) FILTER (WHERE arrec > 0) r, sum(arrec) t FROM bi25 b JOIN mg m USING (cns)
              WHERE m.situacao_juridica = 'PROVIDO' GROUP BY b.cns)""")
