# Aprovação da Etapa 1 — ajustes finais da Fase 1

> **Para o Claude Code.** Este documento responde à sua "Resposta à verificação final da Fase 1" (18/10/2026, tarde). Ele diz, item por item, **o que aprovo, o que aprovo com ajuste e onde discordo**, sempre com o motivo, e define a **ordem de execução**, os **critérios de aceite** e o **relatório final** esperado.
>
> Continue atuando como **engenheiro de dados e cientista de dados sênior, especialista em seguros**. Se em algum ponto você discordar da minha decisão com base em dado ou em texto legal, **não siga em silêncio nem ignore**: pare naquele item, explique e espere.

---

## 0. Contexto e regras

**Situação atual**
- Antes desta mensagem, fiz um **commit de ponto de controle** com os docs e os scripts de `scripts/verificacao_fase1/`. Esse é o ponto seguro de volta.
- O Streamlit **está fechado**. Não abra o painel durante a implementação. Só no fim, para a conferência (seção 6).

**Regras (todas continuam valendo)**
- `CLAUDE.md` acima de tudo.
- **Nunca** faça commit nem push. No fim, só liste os arquivos e sugira a mensagem.
- **Não apague nada.** Nesta etapa você **pode alterar** os arquivos listados no seu plano (os itens "M") **somente na forma aprovada abaixo**.
  - Nada fora do plano é alterado sem me perguntar.
  - Código substituído não deixa "versão antiga comentada". O histórico está no git.
  - Premissas que mudam de valor viram **nova versão** do YAML (ex.: `premissas_v002.yaml`). A v001 continua no lugar, para dar para comparar.
- Docs: `diario.md` e `erros_ia.md` só recebem **acréscimos no fim**. Em `decisoes.md`, as decisões D-019 a D-025 mudam de "PROPOSTA" para "APROVADA" ou "APROVADA COM AJUSTE", **sem apagar o texto da proposta**: acrescente abaixo dele a decisão final, com a data. **Nenhuma decisão antiga (D-001 a D-018) é editada.**
- Todo número novo na tela tem **fonte e data de referência**.
- **LGPD:** nada no nível de cartório identificável. Municípios com menos de 3 serventias são agregados.
- O CSV do BI continua **só no bronze**. Não crie coletor nem tabela silver para ele nesta etapa (isso é da Etapa 2).
- Arquivos grandes **nunca** são lidos inteiros pela ferramenta de leitura. Saída de script com no máximo 50 linhas.

---

## 1. O que aprovo sem ressalvas

| Item | O que você propôs | Por que aprovo |
|---|---|---|
| **Método de medição** | Recalcular em memória a partir dos Parquet das 09:52, com diferença zero contra o gold, sem abrir o banco travado | Correto e seguro. O banco ficou intocado. |
| **F1, F7** | Universo e totais Brasil conferem com o BI | Confere com o que calculei por fora: 2.525 / 1.654 / 830 / 28 / 13; R$ 36,23 / 12,34 / 13,26 bi. |
| **F2** | O silver tem **mais** que o BI no 2º sem/2025 (168 CNS, R$ 62,7 mi), porque a API está mais completa | Confere: no BI faltam exatamente 168 CNS de MG nesse semestre. Sem eles a diferença cai para +0,11%. **Não era erro.** |
| **F3 / C4** | 154 = linhas (77 pares × 2); só 2 conflitos em 2025, os mesmos CNS nas duas fontes | Explicação coerente. Conflitos antigos não entram no modelo. |
| **A3** | O 13º do ano já vem quitado em 31/12; só entra a projeção do aviso (64 meses → aviso de 45 dias → 1/12) | Correto pela CLT e pela Lei 12.506/2011 (30 dias + 3 por ano completo: 5 anos → 45 dias). O aviso indenizado projeta o contrato e gera 1/12 de 13º e de férias. **Não era erro.** |
| **A4** | 8 serventias com zero CLT somam 3,8 das 489,9 "com déficit" | Erro pequeno, mas real. Passivo zero → déficit zero e probabilidade zero. |
| **A5** | As correções 2, 3, 4 e 6 nunca foram implementadas | Bom diagnóstico. Fica registrado em `erros_ia.md` como "IA informou correção não feita", se ainda não estiver assim. |
| **Item 5** | Os testes gravam em `estado.cenarios_salvos` do banco real | Erro confirmado e **o mais urgente**. Ver a ordem na seção 4. |
| **A2** | Data-base única **31/12/2025** (art. 4º do Prov. 227); o art. 18 muda só o prazo da 1ª declaração; o INPC sai da base e vira sensibilidade; −3,86% em todos os valores | Concordo. Os salários da RAIS são de dezembro/2025, então corrigir até setembro/2026 misturava datas. −3,86% = 1/1,0401 − 1. Ajustes na seção 2.3. |
| **B5, trava dos controles** | A fiança já é limitada a 1 − seguro | **Não era erro.** |
| **B5, férias 0,5** | Aprovada na D-017; falta nas Limitações e o YAML diz "aguarda aprovação" | Corrigir o texto e acrescentar às Limitações. |
| **C2** | A distribuição "estado" inclui BH (R$ 24.951 contra R$ 13.842 por vínculo nos municípios pequenos); reserva pela região imediata → passivo −5,5% | **Aprovado.** É uma melhora metodológica clara e usa a mesma região imediata do mapa. |
| **C3** | Peso 0 no mínimo e 1 no máximo já existem; o perfil é menor (3,5 CLT contra 5,9) | Confirma o viés. Documentar o perfil nas Limitações. |
| **C6, 887 vínculos** | 714 têm remuneração média zero e 12+ meses: afastados de fato | Aceito. Registrar em Limitações. |
| **E2** | O prêmio do Mercado não usa a SES | O rodapé deve dizer "taxa: suposição (premissas vN)". |
| **E4** | Teto R$ 5,13 mi e R$ 10,56 mi | Confere. Recalcular depois do A2: vai cair junto com o passivo. |
| **IS** | IS = déficit × fatia que escolhe seguro × fração do cenário; prêmio = IS × taxa | Correto. A "fração do cenário" precisa ter definição visível na tela (seção 2.6). |
| **F8, ponte** | 461,7 → 281,2 (método −180,5) → 234,5 (premissas −46,7) → 256,5 (universo +22,0) | Excelente: a conta fecha. Fica no `diario.md` e vira material do slide. **Não entra no painel nesta etapa.** |

---

## 2. Onde aprovo com ajuste ou discordo (leia com atenção)

### 2.1 A1, peso da indeterminada: **discordo** de unificar o peso

**O que você disse:** o peso é recalculado por regra (v1 0,932 × v2 0,678) e "deveria ser o mesmo nas duas regras".

**Por que discordo.** O peso da indeterminada responde a uma pergunta: *"qual a probabilidade de uma serventia sem dado de arrecadação estar no universo?"*. A resposta **depende da regra**:
- pela v1 (Classe 1 até R$ 100 mil), 93,2% das serventias conhecidas ficam acima do corte;
- pela v2 (até R$ 300 mil), 67,8%.

Usar 0,678 na regra v1 diria que uma serventia sem dado tem a mesma chance de passar num corte de R$ 100 mil e num de R$ 300 mil, o que é falso. Recalcular o peso por regra está **certo**.

O que a minha revisão pediu foi outra coisa: que a **classe usada nas faixas de déficit** (probabilidade e parte descoberta) seja **sempre a v2**. Essa parte você corrigiu.

**Decisão:**
- **O peso da indeterminada continua recalculado por regra.** Não unifique.
- A classe das faixas de déficit fica sempre pela v2 (como você propôs).
- **O teste de monotonicidade precisa continuar passando** com o peso por regra. Se não passar, pare e me mostre por quê.
- Corrija a entrada do A1 em `erros_ia.md` acrescentando uma nota: "peso por regra não era erro; o erro era a classe das faixas".

### 2.2 A1, faixa das serventias que só entram pela v1: **falta definir**

**O problema.** As ~424 serventias que entram no universo só pela regra v1 têm receita entre R$ 100 mil e R$ 300 mil, ou seja, são **Classe 1 pela v2**. A Classe 1 **não tem faixa de déficit** no modelo, porque está fora da obrigação. Mesmo assim, o prêmio v1 corrigido subiu para R$ 448,8 mil, então você deu alguma faixa a elas.

**[VERIFICAR antes de implementar]** Qual faixa elas recebem hoje na sua correção? Responda antes de mexer.

**Decisão, se ainda não for assim:** elas recebem a **faixa da Classe 2**. Motivo: no cenário v1, elas seriam as **menores obrigadas**, e a Classe 2 é a faixa das menores obrigadas na v2. Usar a Classe 3 (cartórios maiores, menor probabilidade de déficit) subestimaria o risco delas. Registre isso como parte da D-019, com a frase: "suposição: na sensibilidade v1, serventias Classe 1 pela v2 recebem a faixa da Classe 2".

### 2.3 A2, data-base: aprovado, com três complementos

1. **Rodapé de todas as páginas com valores:** "Data-base do passivo: 31/12/2025 (art. 4º do Prov. CNJ 227/2026)".
2. **Limitação nova:** os empregados por serventia são a declaração ao CNJ de out/2026, e não de 31/12/2025. Eles só servem como **peso do rateio** (proporção entre serventias), então a diferença de data afeta pouco. Diga isso nas Limitações.
3. **Sensibilidade nova "salário corrigido pelo INPC até set/2026"** (+4,01%), na tabela de sensibilidade, com o nome claro: "se a data-base fosse a da 1ª declaração".
4. Em `decisoes.md` (D-020), **cite o texto literal** do art. 4º e do art. 18 do Prov. 227, a partir da cópia oficial do bronze.

### 2.4 F5, regra dos R$ 300 mil: **discordo** de trocar a leitura principal

**O que você propôs:** passar a leitura principal para "média com o semestre zerado contando como zero" (ao pé da letra do §1º), o que daria **1.087** providos em vez de 1.103.

**Por que discordo.** O texto fala da **receita bruta real** do exercício anterior. O nosso dado não é a receita real: é a **declaração ao CNJ**, e o seu próprio F4 mostrou que **zero, na fonte, muitas vezes significa "não declarou"**:
- no BI faltam 168 CNS de MG no 2º sem/2025;
- o prazo desse semestre foi prorrogado até 15/04/2026 por troca de sistema, e no fim de março só ~50% tinham enviado (IRIB, 01/04/2026);
- uma serventia que arrecadou R$ 400 mil num semestre não arrecadou R$ 0 no outro; ela deixou de declarar.

Contar esse zero como receita zero **erra para baixo de propósito** e tira do universo serventias que provavelmente são obrigadas. Ignorar o semestre zerado e fazer a média dos semestres com valor é a **melhor estimativa da receita real**, e é isso que a regra mede.

**Decisão:**
- **Leitura principal: a atual** (média dos semestres com valor > 0, `universo.py:24-30`): **1.103 providos**. Não altere o código do universo.
- D-023 fica "APROVADA COM AJUSTE": acrescente a justificativa acima e a citação literal do §1º do art. 16 do Prov. 213 (alterado pelo 243).
- **Acrescente à tabela de sensibilidade** as leituras alternativas, cada uma com o número de providos e o efeito no passivo e no prêmio:
  - "zero conta como zero (literal)" → 1.087;
  - "nos dois semestres > R$ 300 mil" → 928 (referência BI);
  - "em algum semestre > R$ 300 mil" → 1.161 (referência BI).
- **Limitações:** "14 providos com 1º semestre > R$ 300 mil e 2º semestre zerado entram no universo pelo 1º semestre".

### 2.5 B1, vacância: **não trazer o cadastro do BI**

Você deixou para eu decidir se vale trazer o cadastro do BI para ter as datas de vacância. **Decisão: não.** Conferi o arquivo antes:
- a "data de ingresso do responsável" tem **1.066 dos 1.654 providos de MG em 2024**, o que é claramente a data de recadastramento no sistema novo, não a posse real;
- a "data de decisão" tem o mesmo defeito (250 vagas "decididas" em 2024, contra 36 em 2023 e 133 em 2025);
- o arquivo traz nome, substituto e e-mail dos titulares (risco de LGPD sem ganho).

**O que fazer agora:**
- Registrar no `diario.md`: "cadastro do BI não mede vacância; datas são de recadastramento".
- D-025 continua **PROPOSTA** (é da Etapa 2). Acrescente a nota: "a frequência de término da delegação será suposição com faixa. Os 133 serventias de MG com decisão de vacância em 2025 (≈ 7% dos providos) entram só como **indicador fraco de teto**, não como estimativa".

### 2.6 B5, "decisão parcial" e rótulo da sinistralidade

- **Decisão parcial (ADI 8015):** escreva na tela, ao lado do seletor e não só no "?", uma linha objetiva:
  > "Cenário hipotético: o STF suspende parte da obrigação, e só [X]% do valor hoje exigido continua exigido. [X] = 50%, suposição sem base em decisão real; até 17/10/2026 não havia liminar."

  Confira a frase com o que o código faz. Se o código fizer outra coisa, me diga.
- **Rótulo da sinistralidade:** a SES dá sinistro ÷ prêmio **ganho**, e a conta aplica sobre o prêmio **emitido**. Numa carteira anual estável, ganho ≈ emitido. **Mantenha a conta** e troque o rótulo para:
  > "Sinistralidade da SES (sinistro ÷ prêmio ganho), aplicada ao prêmio emitido do ano — aproximação"

  O modelo de frequência × severidade (B1) substituirá isso na Etapa 2.

### 2.7 F2, contrato novo: aprovado, com a referência certa

O total de controle **principal** é o do **próprio silver** (o pipeline não pode perder linhas entre uma carga e outra). O BI é **conferência cruzada**:
- **Contrato 1 (erro):** a arrecadação de MG por semestre no silver não pode cair mais de 0,5% em relação ao total registrado em `config/qualidade.yaml` (1º sem/2025 R$ 2.379,6 mi; 2º sem/2025 R$ 3.133,9 mi).
- **Contrato 2 (aviso):** silver × BI. Tolerância de 1% no 1º sem/2025 e de 3% no 2º sem/2025, com o motivo no YAML: "BI incompleto no 2º sem/2025 (168 CNS de MG ausentes em 18/10/2026)".
- O valor do BI fica no YAML com a fonte, o arquivo do bronze e a data da exportação.

---

## 3. Itens sem divergência, com detalhe de execução

**D1, LGPD**
- Tabelas "Maiores diferenças" (CNPJ − CNJ e RAIS − CNJ): só municípios com **≥ 3 serventias**. Abaixo disso, mostrar a **região imediata** ou omitir a linha.
- **Gráfico CNJ × RAIS:** 502 dos 821 pontos têm menos de 3 serventias. Plote **por região imediata**, com o nome da região no texto ao passar o mouse. Se preferir manter por município, os pontos abaixo de 3 ficam sem nome e sem valores no texto do mouse.
- Teste: falha se qualquer saída do gold ou do app com nome de município tiver menos de 3 serventias. A exceção é explícita e listada para contagens do cadastro público do CNJ.

**D2:** acrescentar a limitação de que o rateio por empregados declarados é recalculável por terceiros, e que a defesa é tratar-se de **estimativa de mercado com premissas públicas**.

**C1:** acrescentar as três checagens (correlação em log, erro percentual mediano por município, % dentro de ±20% com ≥ 5 empregados) e a contagem de municípios com zero numa das fontes na legenda. **Defina a tolerância de cada checagem com base no resultado e me mostre os valores** antes de fixar. Não escolha uma tolerância só para passar.

**C5:** URL e hora de coleta para colaboradores e SUSEP; um `.meta.json` no bronze dos colaboradores, sem tocar no dado; IBGE com a **versão do dado** (ano da malha, data da lista de municípios), não a data do download.

**C6:**
- **Campo Azul e Senador José Bento** viram limitação documentada: "sem serventia no cadastro do CNJ em out/2026; 1 CNPJ ativo do CNAE em cada; motivo não identificado".
- Universo exibido como "≈ 1.121 (valor esperado; inclui peso das 27 indeterminadas)" em todas as telas.

**A5 + E1 a E4 (painel)**
- **Mapas** de passivo e déficit agregados pela **região imediata** quando o município tem menos de 3 serventias. Nada de "municípios em branco".
- **Página Mercado:** dois valores com nomes claros, "Passivo de todas as ativas" e "Passivo dos obrigados — universo".
- **Bloco Faixas** como tabela pequena: mínimo / base / máximo × passivo / universo / déficit / IS / prêmio.
- **Formatação brasileira em todo lugar:**
  - R$, "mil", "mi", vírgula decimal e ponto de milhar;
  - legendas de mapa ("R$ 350 mil", não "350k");
  - sliders ("2,0%");
  - Tabela por UF e tabela por município.
- **Uma linha na tela explicando min, base e max:** "cada cenário põe todas as suposições no extremo ao mesmo tempo; é um limite, não uma previsão".
- **Início:** "passivo trabalhista dos empregados CLT".
- **Teto teórico** (Simulador ou Início), com a fórmula visível: "passivo dos obrigados × taxa; supõe que todos têm déficit igual ao passivo e todos escolhem seguro".

---

## 4. Ordem de execução (obrigatória)

Rode a suíte de testes **ao fim de cada passo**. Se algum teste quebrar, corrija antes de seguir.

1. **Item 5, isolar os testes do banco real.** O caminho do banco vem por variável de ambiente, com um fixture que copia o banco para uma pasta temporária.
   - Critério: anote a data de modificação e o tamanho do DuckDB real, rode a suíte, e os dois **não mudam**. Mostre isso.
   - Remova a "versão 2 espúria das premissas" que um teste criou no banco real **só se** ela não for usada por nada. Antes, me diga o que é e onde está. **Isto precisa da minha aprovação explícita** (é uma remoção).
2. **A4**, passivo zero → déficit zero. Teste.
3. **A1** com os ajustes 2.1 e 2.2. Teste de monotonicidade em min, base e max.
4. **A2** com os complementos 2.3: `premissas_v002.yaml` sem o INPC na base; o INPC vira sensibilidade. Teste com o vínculo calculado à mão (R$ 3.000, 64 meses, data-base 31/12/2025), mostrando cada verba.
5. **C2**, reserva pela região imediata. Teste: um município pequeno usa a distribuição da sua região, não a do estado.
6. **F5 com o ajuste 2.4** (sem mudar a leitura principal; só a sensibilidade nova) e **F2 com o 2.7** (contratos).
7. **D1 e D2**.
8. **C1, C5 e C6**.
9. **B5 com o 2.6.**
10. **Painel: A5 + E1 a E4.**
11. **Pipeline do zero** (`uv run pipeline.py`) e suíte completa. Confira o banco antes e depois: agora ele **deve** mudar, porque o pipeline grava.

**Pontos de parada obrigatórios**
- Depois do **passo 1**, se for preciso remover a versão espúria das premissas.
- Em qualquer passo, se um número principal se mover **mais do que o esperado** na seção 5 sem explicação.
- Se um item exigir mudar algo **fora do plano aprovado**.

---

## 5. Números esperados (para você se conferir)

Ponto de partida (base v2): 2.525 ativas; ≈ 1.121,3 obrigadas; passivo de R$ 343,4 mi (todas) e R$ 256,5 mi (obrigadas); déficit R$ 40,4 mi; IS R$ 20,2 mi; prêmio R$ 404,4 mil.

| Correção | Efeito esperado, isolado |
|---|---|
| A1 | Base v2 **não muda**. Sensibilidade v1: prêmio ≥ R$ 404,4 mil. |
| A2 | −3,86% em tudo: R$ 330,1 mi / R$ 246,6 mi / R$ 38,9 mi / R$ 19,4 mi / R$ 389 mil. |
| A4 | "Com déficit" 489,9 → 486,1. Valores em R$ não mudam. |
| C2 | Passivo de todas as ativas −5,5%. Efeito no universo: **medir e mostrar**. |
| F5 | Base **não muda** (leitura atual mantida). |

**No relatório final, mostre uma "cascata"** do ponto de partida até o número final, correção por correção, para passivo (todas e obrigadas), déficit, IS, prêmio e teto teórico. **O efeito combinado não precisa bater com a soma dos isolados**, mas a diferença precisa ser explicada.

---

## 6. Relatório final esperado

1. **Checklist** de cada item (D1, D2, A1 a A5, item 5, B5, C1 a C6, E1 a E4, F2, F5): feito / não feito, com arquivo e teste correspondente.
2. **Prova do item 5:** data e tamanho do banco real antes e depois da suíte.
3. **Cascata** dos números (seção 5).
4. **Resultado das novas checagens** do C1, com as tolerâncias propostas.
5. **O que eu devo conferir no painel**, página por página: lista curta do que mudou na tela.
6. **Registros** acrescentados em `erros_ia.md`, `diario.md` e `decisoes.md` (D-019 a D-024 com a decisão final; D-025 continua PROPOSTA).
7. **Arquivos alterados e criados**, marcando o que é **A** (acréscimo) e o que é **M** (alteração), e a **sugestão de mensagem de commit**. Não faça o commit.
8. **Pare.** Eu abro o painel e confiro antes de qualquer outra coisa.

---

## 7. Etapa 2 (registro de prioridade; não implementar agora)

Para você registrar no `diario.md` como próximos passos aprovados em princípio, por ordem:

1. **B6 + F6:** probabilidade de déficit por faixa de **passivo ÷ saldo anual**, lado a lado com a versão por classe. Os dados do F6 mostram que o modelo atual (~490 com déficit) provavelmente superestima: só 41 serventias precisam de mais de 12 meses de saldo e 47 têm saldo ≤ 0. Deixar claro que o Prov. 227 mede **bens livres de ônus** e que o saldo é só um indicador. Exige o coletor do CSV e a tabela silver de custeio e repasse, com contratos para o custeio repetido por atribuição no 2º sem/2025.
2. **B3:** número de apólices, prêmio médio, prêmio mínimo e custo fixo por apólice (suposições com faixa).
3. **B2:** índice combinado, "resultado técnico antes de impostos e capital" e PIS/COFINS com a alíquota conferida no texto legal.
4. **B4:** gráfico tornado e cenários coerentes "otimista" e "pessimista para a seguradora".
5. **Opcional, só se sobrar tempo:** B1 completo (frequência × severidade) e Monte Carlo.
