"""F5 (leitura literal do art. 16, § 1º, no silver) e F7 (ativas do Justiça Aberta ausentes do BI). Só agregados."""
from comum import conectar, mostrar

con = conectar()
mostrar(con, "F5: providos de MG, 2025, silver (versão 1), leituras", """
    WITH s AS (SELECT a.cns, max(arrecadacao) FILTER (WHERE semestre = 1 AND versao = 1) s1,
                      max(arrecadacao) FILTER (WHERE semestre = 2 AND versao = 1) s2, bool_or(conflito_fonte) c
               FROM silver.serventia_arrecadacao a JOIN silver.serventia v USING (cns)
               WHERE v.status = 'Ativo' AND v.situacao_juridica = 'PROVIDO' AND a.ano = 2025 AND a.semestre IS NOT NULL GROUP BY a.cns)
    SELECT count(*) providos, count(*) FILTER (WHERE c) conflito,
           count(*) FILTER (WHERE NOT c AND (coalesce(s1, 0) + coalesce(s2, 0)) / 2 > 3e5) literal_media_com_zero,
           count(*) FILTER (WHERE NOT c AND (s1 > 0) <> (s2 > 0) AND greatest(s1, s2) > 3e5 AND (coalesce(s1, 0) + coalesce(s2, 0)) / 2 <= 3e5) mudam_de_classe
    FROM s""")
mostrar(con, "F7: ativas no Justiça Aberta sem nenhuma linha no CSV do BI, por UF (top 10) e situação", """
    SELECT uf, count(*) n, count(*) FILTER (WHERE situacao = 'VAGO') vagas, count(*) FILTER (WHERE situacao IS NULL) sem_situacao
    FROM cad_br WHERE status = 'Ativo' AND cns NOT IN (SELECT cns FROM bi) GROUP BY uf ORDER BY n DESC""", 10)
