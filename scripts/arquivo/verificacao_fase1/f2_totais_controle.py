"""F2: totais de controle exatos da arrecadação de MG por semestre de 2025 (silver × BI), para config/qualidade.yaml."""
from comum import conectar

con = conectar()
print(con.sql("""
    WITH mg AS (SELECT cns FROM silver.serventia WHERE status = 'Ativo')
    SELECT semestre::INT sem, count(DISTINCT cns) cns, round(sum(arrecadacao), 2) silver_versao1
    FROM silver.serventia_arrecadacao WHERE ano = 2025 AND semestre IS NOT NULL AND versao = 1 AND cns IN (SELECT cns FROM mg)
    GROUP BY 1 ORDER BY 1""").df().to_string(index=False))
print(con.sql("""
    WITH mg AS (SELECT cns FROM silver.serventia WHERE status = 'Ativo')
    SELECT sem, count(DISTINCT cns) cns, round(sum(arrec), 2) bi
    FROM bi_p WHERE ano = 2025 AND sem IS NOT NULL AND cns IN (SELECT cns FROM mg) GROUP BY 1 ORDER BY 1""").df().to_string(index=False))
