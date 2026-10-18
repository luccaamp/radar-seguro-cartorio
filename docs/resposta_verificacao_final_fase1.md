# Resposta à verificação final da Fase 1

> Resposta da IA a `docs/revisao_fase1.md` e `docs/verificacao_final_fase1.md`, em 18/10/2026 (tarde).
> **Nada foi implementado.** A IA aguarda a aprovação do autor, item a item.

**Como medi:** o Streamlit aberto às 13:27 trava o arquivo do banco, então não abri o banco nem encerrei o processo. Recalculei em memória, com o mesmo motor do pipeline, a partir das cópias em Parquet das 09:52; esse recálculo reproduz o gold com **diferença zero**. O banco continua com a data de 09:52:40 e o mesmo tamanho, antes e depois. Os scripts estão em `scripts/verificacao_fase1/` e só leem dados. O CSV do BI foi para `data/bronze/cnj_bi_painel/2026-10-18/`, sem alteração e com o arquivo de linhagem.

## 1. Respostas aos [VERIFICAR]

Números do cenário base, regra v2 (Classe 1 até R$ 300 mil) e regra mantida, salvo indicação.

| Item | Número do banco | Referência | Bate? | Explicação |
|---|---|---|---|---|
| **A1** classes no universo | v2: Classe 2 = 749, Classe 3 = 354, indeterminada = 27. v1: Classe 2 = 686, **Classe 3 = 834**, indeterminada = 27 | — | — | A v1 empurra serventias para a Classe 3, que tem probabilidade de déficit menor. |
| **A1** peso da indeterminada | **recalculado por regra**: v1 0,932 × v2 0,678 (`gold.py:67`) | 67,8% | não | Deveria ser o mesmo nas duas regras. |
| **A1** com a correção | prêmio v1 base R$ 382,9 mil → **R$ 448,8 mil** (≥ v2 em min, base e max) | monotonicidade | sim | Com a correção, o teste de monotonicidade passa. |
| **A2** data-base | tempo de casa, aviso, 13º e férias em **31/12/2025**; salário corrigido até **set/2026** (fator 1,0401); empregados de **out/2026** | — | não | O art. 18 do 227 muda só o *prazo* do 1º ano; a posição continua a do art. 4º, 31/12 do ano anterior. |
| **A3** 13º | já vem quitado na data-base. Exemplo (R$ 3.000, 64 meses): aviso de 45 dias → **1/12 = R$ 250** (nunca 12/12) | ~0 | sim | Só entra o 13º gerado pela projeção do aviso. |
| **A4** zero CLT | **8** das serventias do universo; somam **3,8** das 489,9 "com déficit"; déficit em R$ delas = 0 | — | — | O efeito é pequeno, mas o erro é real. |
| **A5** 2, 3, 4, 6 | nenhum arquivo de `app/` mudou depois das 09:52 | — | — | **Não foram implementadas.** Não é questão de reiniciar o Streamlit. |
| **A5** item 5 | o teste grava em `estado.cenarios_salvos` do banco real | data não pode mudar | não | Não rodei a suíte, para não alterar o banco. Confirmado pelo código e por um caso anterior: um teste já criou uma versão 2 espúria das premissas. |
| **B1** SES | min 1,7% = 0775, set/2021–ago/2022; base 10,9% = 0775, set/2020–ago/2026; max 73,9% = 0776, mesmo período. São sinistro ÷ prêmio **ganho**; sobre o prêmio emitido seriam 8,2% e 59,3% | — | — | Sobre a vacância: o cadastro só tem a data da **situação atual** (vagas por ano da decisão: 2023 = 36, 2024 = 250, 2025 = 133). Não dá para tirar uma taxa disso. |
| **B5** férias 0,5 | aprovada pelo autor na D-017 (fonte: suposição). Falta nas Limitações, e o YAML ainda diz "aguarda aprovação" | — | — | Corrigir o texto. |
| **B5** decisão parcial | definida só no "?" do seletor, de forma vaga, com fração de 50% (suposição) | — | — | Definição fraca. |
| **B5** trava dos controles | já existe: o máximo da fiança é 1 − seguro | — | sim | Não era erro. |
| **B5** rótulo | o rótulo diz "ganho", a conta usa o emitido | — | não | Rótulo e conta desalinhados. |
| **C2** distribuição "estado" | usa **todos** os 10.978 vínculos, com BH: R$ 24.951 por vínculo, contra R$ 13.842 nos municípios abaixo do limiar | — | — | Com reserva pela região imediata, o passivo de todas as ativas fica **−5,5%**. |
| **C3** indeterminadas | 78 = 76 com zero + 2 em conflito. 48 vagas, 27 providas, 3 especiais. CLT médio 3,5 contra 5,9 nas conhecidas | peso 0 no min | sim | O peso já é 0 no mínimo e 1 no máximo. O perfil menor confirma o viés apontado pelo autor. |
| **C4 / F3** | 154 = **linhas**, ou seja, 77 pares em conflito × 2 versões | 151 pares (BI) | — | São duplicações diferentes em fontes diferentes; a diferença de 3 é coincidência. Em 2025 são 2 conflitos nas duas fontes, os mesmos CNS. O modelo só usa 2025. |
| **C6** municípios | **Campo Azul** e **Senador José Bento**: 0 registros no CNJ e 1 CNPJ ativo do CNAE em cada | — | — | Inconclusivo. |
| **C6** 887 vínculos | 714 têm também remuneração média zero e 12+ meses de casa; só 4 foram admitidos em dezembro | — | — | Provavelmente afastados de fato, não um defeito do campo. |
| **C6** universo | 1.121,31 é valor esperado (peso × indeterminadas) | — | — | Padronizar a exibição. |
| **E2** | o prêmio do Mercado usa a taxa e a escolha de garantia, **não a SES** | — | — | Não precisa da SES no rodapé, mas o rodapé deve dizer "taxa: suposição". |
| **E4** teto | R$ 256,5 mi × 2% = **R$ 5,13 mi**; R$ 301,8 mi × 3,5% = **R$ 10,56 mi** | 5,1 e 10,6 | sim | — |
| **F1** universo | 2.525 / 1.654 / 830 / 28 / 13. Todas as 2.525 estão no CSV; 1 CNS do CSV não existe em nenhum cadastro | 2.525 / 1.654 / 830 / 28 / 13 | sim | — |
| **F2** 1º sem/2025 | R$ 2.379,6 mi (+0,24%); 16 CNS divergem > 1% | R$ 2.373,9 mi | sim | — |
| **F2** 2º sem/2025 | R$ 3.133,9 mi (+2,16%) | R$ 3.067,7 mi | não, mas explicado | **O silver tem mais, não menos.** A API traz 168 CNS (R$ 62,7 mi) que o BI ainda não tem. Sem eles, +0,11%. |
| **F2** coletor | a API devolve 1 linha por CNS e semestre. O silver guarda cada versão (`silver.py:203-208`), e versões diferentes viram conflito → classe indeterminada (`universo.py:21-22`) | — | — | Quem divide por atribuição é o BI, não a API. |
| **F4** | silver: 0 semestres ausentes; zero em 135/143 (1º/2º sem); zero nos dois = 77; positivo em só um = 124 | BI: 168 ausentes no 2º sem; zero nos dois = 81; positivo em só um = 222 | não, mas explicado | Diferença de extração. Com o 1º sem > R$ 300 mil e o 2º ausente/zero: 14 providos no silver, 45 no BI. **Hoje entram no universo**, classificados pelo 1º semestre. |
| **F5** leitura do código | média só dos semestres com valor > 0 (`universo.py:24-30`): **1.103** providos | 928 / 1.065 / 1.106 / 1.161 (conferem no BI) | — | O texto do §1º diz "média das receitas brutas semestrais do exercício imediatamente anterior". Lendo ao pé da letra, com o zero contando como zero, seriam **1.087** providos. |
| **F6** repasse/custeio | a API não traz repasse nem custeio, então a fonte é o CSV. Custeio 2025 MG R$ 1.406 mi contra folha RAIS com encargos R$ 713 mi; 29 de 389 áreas com custeio menor que a folha | — | — | — |
| **F6** passivo ÷ saldo anual | < 3 meses: 708; 3 a 12: 260; > 12: 41; saldo ≤ 0: 47; sem dado: 74. No agregado, 1,94 mês de saldo | — | — | — |
| **F7** Brasil | arrecadação R$ 36,23 bi, repasse R$ 12,34 bi, custeio R$ 13,26 bi | iguais | sim | — |
| **F7** contagem de serventias | o Justiça Aberta tem 12.121 ativas e o BI 11.866: 256 ativas sem nenhuma linha no BI, quase todas sem situação jurídica (RJ 80, SE 35, ES 25) | ANOREG 12.210 | — | A diferença para a ANOREG continua **inconclusiva**: ela é de dez/2025 e usa a mesma base do CNJ. |
| **F8** ponte do passivo | estudo R$ 461,5 mi ≈ 11,5% de R$ 4.015 mi, no universo "dois semestres > R$ 300 mil" (928 serventias) | — | — | Etapas: o método do estudo vale R$ 461,7 mi. Com o nosso método por vínculo e as premissas dele: **R$ 281,2 mi** (método: −180,5). Com as nossas premissas: **R$ 234,5 mi** (premissas: −46,7). No nosso universo: **R$ 256,5 mi** (universo: +22,0). |
| **F8** ponte do prêmio | o nosso vai de R$ 256,5 mi de passivo → R$ 40,4 mi de déficit → R$ 20,2 mi de IS → **R$ 0,40 mi** de prêmio | estudo: R$ 3,23 mi | — | — |

**Conceito de IS:** o código segue a definição. IS = déficit × fatia que escolhe seguro × fração exigida pelo cenário, e o prêmio é IS × taxa anual.

## 2. Classificação

- **ERRO CONFIRMADO**
  - A1, A2, A4, A5 (as correções 2, 3, 4 e 6 não foram feitas; os testes gravam no banco real);
  - D1: 2 dos 10 municípios da tabela CNPJ − CNJ e 502 dos 821 pontos do gráfico têm menos de 3 serventias;
  - B5: rótulo × conta, e a definição fraca da "decisão parcial";
  - C1: a checagem é fraca e passa só por causa de BH;
  - C2: o BH entra na distribuição "estado";
  - C5: sem URL em colaboradores e SUSEP, sem hora em colaboradores, e datas de referência do IBGE iguais ao dia do download;
  - E1 e E3.
- **NÃO ERA ERRO**
  - A3: o 13º já vem quitado e só entra a projeção do aviso;
  - F2: o coletor não perde linhas; a API está mais completa que o BI;
  - F3: os conflitos antigos não afetam o modelo;
  - a trava dos controles de garantia já existe;
  - E2: o prêmio não usa a SES;
  - o conceito de IS;
  - F1 e F7, que batem com a referência.
- **INCONCLUSIVO**
  - C6: os 2 municípios sem serventia;
  - F7: a diferença para os 12.210 da ANOREG;
  - B1: falta histórico de vacância. O cadastro do BI teria as datas, e trazê-lo é decisão do autor.

## 3. Impacto nos números principais (base v2)

Ponto de partida: 2.525 ativas; 1.121,3 obrigadas; passivo de R$ 343,4 mi (todas) e R$ 256,5 mi (obrigadas); déficit R$ 40,4 mi; IS R$ 20,2 mi; prêmio R$ 404,4 mil.

| Correção | Efeito |
|---|---|
| A1 (D-019) | Base v2 não muda. Só a sensibilidade v1 muda: prêmio R$ 382,9 mil → R$ 448,8 mil. |
| A2 (D-020) | **−3,86%** em todos os valores: R$ 330,1 mi / R$ 246,6 mi / déficit R$ 38,9 mi / IS R$ 19,4 mi / prêmio R$ 389 mil. |
| A4 (D-021) | "Com déficit" 489,9 → **486,1**. Os valores em R$ não mudam. |
| C2 (D-022) | Passivo de todas as ativas **−5,5%** (R$ 324,4 mi). O efeito no universo será medido na implementação. |
| F5 (D-023) | **−16** providos no universo (1.103 → 1.087). O efeito em R$ será medido na implementação. |

Cada efeito foi medido sozinho. O efeito combinado só sai depois de implementar.

## 4. Plano

Na lista, **A** significa que a mudança só acrescenta algo novo; **M** significa que ela altera algo que já existe e precisa da aprovação do autor item a item.

**Etapa 1 (antes do commit)**

1. **A1** — **M** em `src/model/mercado.py` e `src/transform/gold.py` (classe v2 nas faixas, peso único da indeterminada); **A** um teste de monotonicidade.
2. **A2** — **M** em `premissas_v001.yaml` (INPC sai da base e vira sensibilidade) e nos rodapés ("data-base 31/12/2025"); **A** um teste com o vínculo calculado à mão.
3. **A4** — **M** em `deficit()`; **A** um teste com passivo zero.
4. **Item 5 (testes gravando no banco)** — **M** em `app/comum.py` (caminho do banco por variável de ambiente) e `tests/test_app.py`; **A** um fixture que copia o banco para uma pasta temporária.
5. **A5 e E1–E4** — **M** nas 4 páginas:
   - mapa agregado por região imediata;
   - passivo em dois valores ("todas as ativas" × "obrigados");
   - bloco Faixas como tabela, e R$ e vírgula decimal em mapas, controles e tabelas;
   - explicação de min, base e max;
   - "empregados CLT" no Início;
   - **A** o teto teórico.
6. **D1 e D2** — **M** na página Qualidade (regra de 3 serventias nas tabelas e no texto ao passar o mouse); **A** um teste sobre as saídas com nome de município e a limitação D2.
7. **F2 (D-024)** — **A** o total de controle em `config/qualidade.yaml` e um contrato novo.
8. **F4 e F5 (D-023)** — **M** em `receita_referencia` (leitura principal); **A** as leituras alternativas na tabela de sensibilidade.
9. **C1, C5 e C6**
   - **A** três checagens novas (log, erro mediano, % dentro de ±20%) e a contagem de municípios com zero na legenda;
   - **M** nos metadados (URL e hora dos colaboradores, versão da malha e da lista de municípios do IBGE);
   - **A** um `.meta.json` no bronze para os colaboradores, sem mexer no dado;
   - **M** na exibição do universo como valor esperado.
10. **C2 (D-022)** — **M** em `distribuicao.py` (reserva pela região imediata), se aprovado.

Depois disso: rodar o pipeline do zero e a suíte de testes (já isolada do banco real), e conferir o banco antes e depois.

**Etapa 2 (ajuste de modelagem, depende da decisão do autor)**

- **B1 (D-025)** — sinistro por frequência × severidade, com a SES só como comparação. O autor decide se vale trazer o cadastro do BI para ter as datas de vacância.
- **B2** — índice combinado e "resultado técnico antes de impostos e capital". PIS/COFINS entra como premissa nova, com a alíquota **conferida no texto legal antes de usar**; nada é fixado de memória.
- **B3** — número de apólices, prêmio médio, e suposições com faixa de prêmio mínimo e custo fixo por apólice.
- **B4** — gráfico tornado e cenários coerentes "otimista" e "pessimista para a seguradora". Monte Carlo opcional, com semente fixa.
- **B6 e F6** — probabilidade de déficit por faixa de passivo ÷ saldo, deixando claro que o Prov. 227 mede bens livres e o saldo é só um indicador. Fica lado a lado com a versão por classe.
- **Uso do CSV como fonte** — **A** um coletor e uma tabela silver nova para custeio e repasse.

## 5. Registros feitos (todos acrescentados no fim dos arquivos)

- `docs/erros_ia.md`: 8 entradas (A1, A4, item 5, A5, A2, D1, B5, C5/C1).
- `docs/decisoes.md`: D-019 a D-025, todas marcadas **PROPOSTA**.
- `docs/diario.md`: uma entrada da verificação, com F1–F8 e os totais de controle Brasil para a Fase 2.

## Alterações prontas para commit

Não foi feito commit.

- **Docs alterados (só acréscimos):** `docs/diario.md`, `docs/erros_ia.md`, `docs/decisoes.md`
- **Scripts novos:** `scripts/verificacao_fase1/` (`comum.py`, `f1_formato_universo.py`, `f2_arrecadacao.py`, `f5_f7_complemento.py`, `m1_modelo.py`, `m2_qualidade_seguro.py`)
- **CSV:** saiu da raiz e foi para o bronze, que fica fora do git.

Sugestão de mensagem: `Fase 1: verificação final contra o BI do CNJ (só leitura) e propostas D-019 a D-025`

Fontes: o texto do art. 16 do Prov. 213/243 e do art. 18 do 227 foi lido nas cópias oficiais do bronze. Nenhum número acima vem da internet.
