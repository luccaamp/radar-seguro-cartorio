# Erros da IA

Registro dos erros cometidos pela IA (no código, nos agentes do radar ou do chat) e do que foi feito para corrigir. Daqui saem os 2 ou 3 casos para o slide "onde a IA errou e o que mudou".

Formato de cada entrada:

```
## AAAA-MM-DD — título curto
- **Onde:** (código gerado / radar / chat / eval)
- **O que aconteceu:** (entrada, saída errada e saída esperada)
- **Como foi detectado:** (teste, eval, revisão manual)
- **Causa provável:**
- **Correção:** (prompt, schema, ferramenta, dado)
- **Resultado depois da correção:** (métrica antes → depois, se houver)
- **Bom para os slides?** sim / não
```

---

## 2026-10-18 — Simulador criava versão nova de premissas sem nenhuma mudança (ponto flutuante)
- **Onde:** código gerado (`src/model/premissas.py::com_novo_base`, usado pelo botão "Salvar" do Simulador)
- **O que aconteceu:** salvar um cenário sem mexer em nada criava a versão 2 das premissas com o diff `market_share_hipotetico: 0.052 → 0.052000000000000005`. O controle devolve 5,2 e o código divide por 100, e no computador 5,2 ÷ 100 não é exatamente 0,052. Esperado: nenhuma versão nova.
- **Como foi detectado:** teste automático novo (`test_simulador_salva_cenario_sem_nova_versao`), escrito antes de entregar a página.
- **Causa provável:** comparação de números decimais com `!=`.
- **Correção:** função `iguais()` com tolerância numérica e teste com o caso real (5,2/100 e 10,9/100). A versão 2 e o cenário criados pelo teste foram apagados do banco.
- **Resultado depois da correção:** 75 testes passando; salvar sem mudança não cria versão.
- **Bom para os slides?** não

## 2026-10-18 — Painel: "R$" virava fórmula matemática e o mapa não desenhava
- **Onde:** código gerado (`app/`)
- **O que aconteceu:** (1) no `st.markdown`, o Streamlit lê `$...$` como LaTeX, e as frases com dois "R$" saíam embaralhadas; (2) o mapa com `px.choropleth` aparecia como um retângulo azul (orientação dos polígonos do IBGE).
- **Como foi detectado:** **conferência visual**: captura de tela das páginas com o Edge (Playwright). Os testes automáticos passavam, porque a página rodava sem exceção.
- **Causa provável:** a IA testou "roda sem erro", mas não "aparece certo".
- **Correção:** função `md()` que escapa o cifrão nos textos; mapa trocado por `px.choropleth_map` com fundo branco (também funciona offline, requisito da demo); cor do mapa saturada no percentil 95, porque Belo Horizonte concentrava a escala.
- **Resultado depois da correção:** capturas conferidas nas 4 páginas.
- **Lição:** teste automático de interface prova que a tela abre, não que está legível. Olhar a tela faz parte do aceite.
- **Bom para os slides?** sim (junto com o erro do 13º: os dois foram pegos por conferência humana ou visual, não por teste)

## 2026-10-18 — 13º da projeção do aviso contado com mês de 30 dias, e não pelo calendário
- **Onde:** código gerado (`src/model/passivo.py`) e exemplo à mão do ponto (b)
- **O que aconteceu:** para um aviso de 45 dias a partir de 31/12, a IA calculou 2/12 de 13º ("45 dias = 1 mês + 15 dias, e 15 dias conta como mês"). Pelo calendário, os 45 dias vão de 1º/jan a 14/fev: janeiro inteiro + 14 dias de fevereiro, que não completam a fração de 15 dias. O certo é **1/12** (Lei 4.090/1962, art. 1º, §§ 1º e 2º, conta "por mês de serviço do ano"). O passivo do exemplo caiu de R$ 16.491,67 para **R$ 16.161,17** (−2%).
- **Como foi detectado:** **pelo autor**, conferindo o exemplo feito à mão. O teste automático não pegou, porque tinha sido escrito com a mesma conta errada.
- **Causa provável:** a IA usou a mesma aproximação de "mês de 30 dias" para o 13º e para as férias sem perceber que as duas leis contam o tempo de formas diferentes: o 13º conta meses do ano civil; as férias contam a partir da data de admissão.
- **Correção:** nova função `avos_13_da_projecao(data_posicao, dias_aviso, ...)` pelo calendário, com a premissa `data_posicao` = 31/12/2025; teste do exemplo corrigido e teste novo com 7 casos de fronteira (30, 33, 44, 45, 46, 59 e 90 dias). Nas férias, o mês de 30 dias continua, agora como aproximação declarada no código (a RAIS não traz o dia de admissão).
- **Resultado depois da correção:** 64 testes passando; exemplo à mão e código dão o mesmo valor.
- **Lição:** um teste escrito pela mesma cabeça que escreveu o código repete o erro do código. A conferência humana do exemplo foi o que pegou.
- **Bom para os slides?** **sim**

## 2026-10-18 — Vínculos por prazo indeterminado somados de cabeça (11.864 × 11.865)
- **Onde:** `docs/decisoes.md`, D-009 (Fase 1)
- **O que aconteceu:** a IA escreveu "ficam 11.864 vínculos" somando os códigos 15, 10 e 25 de uma lista que mostrava só os 6 tipos mais frequentes. O código 20 (1 vínculo) estava fora da lista. A consulta ao silver deu **11.865**.
- **Como foi detectado:** pela própria IA, ao conferir o número com uma consulta direta ao `silver.rais_vinculo`.
- **Causa provável:** a mesma do erro 315 × 316: conta feita ao redigir, a partir de uma saída truncada (`most_common(6)`).
- **Correção:** D-009 corrigida com o número da consulta. Reforço da regra: número em documento vem de uma consulta que conta exatamente aquilo, não de soma de parciais.
- **Resultado depois da correção:** número consistente com o silver.
- **Bom para os slides?** não

## 2026-10-18 — Silver supôs que "atos praticados" era sempre número
- **Onde:** código gerado (`src/transform/silver.py`, Fase 1)
- **O que aconteceu:** a primeira execução do silver quebrou com `Could not convert string 'NÃO INFORMADO' to INT32`. A IA tinha tratado "NÃO INFORMADO" só no campo de arrecadação, mas a API usa o mesmo texto em `atos_praticados`.
- **Como foi detectado:** erro de tipo do DuckDB ao gravar a tabela.
- **Causa provável:** a amostra inspecionada (CNS 152322) não tinha esse caso; a IA generalizou a partir dela.
- **Correção:** `atos_praticados` passa pela mesma conversão (`para_float_br`) e vira nulo quando não informado.
- **Resultado depois da correção:** silver gravado; o tipo forte da tabela pegou o problema antes de virar dado errado.
- **Bom para os slides?** não

## 2026-10-18 — E-mail do autor colocado no User-Agent de uma requisição externa
- **Onde:** código gerado (primeiro teste de acesso a atos.cnj.jus.br, Fase 0, Etapa 3)
- **O que aconteceu:** o comando incluía o e-mail pessoal do autor no cabeçalho User-Agent das requisições ao site do CNJ. Esperado: um User-Agent identificável **sem** dado pessoal.
- **Como foi detectado:** pela própria IA, ao procurar dados pessoais nas transcrições das conversas (18/10/2026). Por sorte, o comando tinha falhado antes de rodar (erro de aspas no PowerShell; ver entrada "Código Python colado direto no PowerShell"), então **o e-mail não foi enviado**. Os scripts seguintes já usavam um User-Agent sem e-mail.
- **Causa provável:** a regra "User-Agent identificável" (SPEC §1.2) foi interpretada como "incluir um contato", sem pesar que o e-mail é um dado pessoal do autor e não deve ir para serviços externos.
- **Correção:** User-Agent padrão do projeto: `radar-seguro-cartorio/<versão> (projeto de portfolio)`, sem e-mail. Na Fase 1, fica num só lugar em `config/`, para nenhum coletor montar o seu.
- **Resultado depois da correção:** nenhuma requisição enviada com o e-mail (o único comando que o continha não executou).
- **Bom para os slides?** não

## 2026-10-18 — Número de serventias sem CLT trocado no resumo (315 × 316)
- **Onde:** resposta da IA ao autor (Fase 0, Etapa 5)
- **O que aconteceu:** o texto da Etapa 5 disse "315 das ativas em MG têm 0 CLT no CNJ". A saída do script mostrava 57 (providas) + 258 (vagas) + 0 (diligência) + 1 (intervenção) = **316**.
- **Como foi detectado:** releitura da conversa pela IA, a pedido do autor.
- **Causa provável:** soma feita "de cabeça" ao redigir, sem copiar o número de uma saída.
- **Correção:** o número certo (316) foi usado no `viabilidade.md` e no diário. Regra: número mostrado ao autor vem de saída de script, nunca de conta mental.
- **Resultado depois da correção:** número consistente nos documentos.
- **Bom para os slides?** não

## 2026-10-18 — Total de serventias ativas do CNJ no Brasil saiu 0
- **Onde:** código gerado (script de conferência da Etapa 5)
- **O que aconteceu:** a conferência imprimiu "CNJ ativas: 0" para o Brasil. O esperado era 12.121, valor medido na Etapa 4.
- **Como foi detectado:** a IA notou o valor impossível ao ler a saída e avisou o autor antes de concluir.
- **Causa provável:** o filtro de arquivos usava `len(p.stem) == 14` para pegar `serventias_XX.json`, mas o nome sem extensão tem 13 caracteres. Nenhum arquivo passou no filtro, e a soma ficou vazia.
- **Correção:** foi usado o total já medido na Etapa 4. No coletor da Fase 1, o filtro será por padrão de nome (`serventias_[A-Z][A-Z].json`), e um total zero vai **falhar** o pipeline em vez de seguir.
- **Resultado depois da correção:** total correto (12.121) no relatório.
- **Bom para os slides?** não

## 2026-10-17 — RAIS de vínculos filtrou 0 linhas (coluna de município errada)
- **Onde:** código gerado (filtro da RAIS 2025, arquivo MG/ES/RJ, 5 GB)
- **O que aconteceu:** o filtro do CNAE 6912-5/00 em MG devolveu **0 vínculos**. O esperado era cerca de 12 mil (o arquivo de estabelecimentos dava 12.227).
- **Como foi detectado:** a IA desconfiou do zero e inspecionou os valores brutos das colunas.
- **Causa provável:** a coluna era escolhida por "primeiro nome que começa com *munic*". A primeira encontrada foi "Município Trab - Código" (sempre 999999), e não "Município - Código". Além disso, os padrões de nome da remuneração não batiam com os nomes abreviados de 2025 ("Vl Rem Dezembro Nom").
- **Correção:** colunas escolhidas pelo **nome exato** (`cab.index("Município - Código")`) e inspeção dos valores brutos antes de filtrar.
- **Resultado depois da correção:** 0 → **12.347** vínculos ativos, a 1% do arquivo de estabelecimentos e a 1,8% do CNJ.
- **Bom para os slides?** sim. É o exemplo de um "zero silencioso" que só aparece porque havia uma segunda fonte para comparar.

## 2026-10-17 — RAIS de estabelecimentos: três falhas de leitura seguidas
- **Onde:** código gerado (leitura de `RAIS_ESTAB_PUB`)
- **O que aconteceu:**
  1. o script travou porque os nomes das colunas vinham entre aspas e a UF vinha como código numérico (31), não como sigla;
  2. a primeira versão **somava colunas que são códigos** (natureza jurídica, tipo de estabelecimento), o que não tem significado;
  3. a segunda versão fixou o separador como `;`, quando o arquivo usa `,`, e travou de novo.
- **Como foi detectado:** erros de execução (1 e 3) e revisão da IA antes de rodar (2).
- **Causa provável:** layout suposto de memória em vez de inspecionado; na versão reescrita, perdi a detecção automática de separador que a primeira tinha.
- **Correção:** inspecionar cabeçalho e uma linha bruta antes de escrever o leitor; tratar códigos como categorias (contagem) e não como números.
- **Resultado depois da correção:** leitura correta (MG: 2.852 estabelecimentos e 12.227 vínculos).
- **Bom para os slides?** não

## 2026-10-17 — Script de cobertura travou duas vezes e repetiu 120 consultas à API do CNJ
- **Onde:** código gerado (amostra de cobertura de arrecadação e empregados, 30 serventias de MG)
- **O que aconteceu:**
  1. o script supôs que a arrecadação era sempre numérica e travou no texto "NÃO INFORMADO";
  2. depois travou ao imprimir o símbolo "≤" no terminal.

  Como os resultados só eram gravados no fim, cada falha obrigou a repetir as 60 consultas. Foram 180 consultas no total, quando 60 bastariam.
- **Como foi detectado:** erro de execução.
- **Causa provável:** dado suposto limpo; gravação do resultado depois da impressão; caractere fora do padrão do terminal.
- **Correção:** conversão numérica tolerante (contando os "NÃO INFORMADO"); **gravar antes de imprimir**; `-X utf8`. Nos coletores da Fase 1: resultados gravados por item (jsonl retomável), como já foi feito na coleta dos 2.525 colaboradores.
- **Resultado depois da correção:** a terceira execução funcionou e mediu o "NÃO INFORMADO" (3 de 30), que virou um dado de qualidade.
- **Bom para os slides?** não

## 2026-10-17 — Acentos trocados nas saídas por configuração ignorada
- **Onde:** execução de scripts (Etapas 3 e 4)
- **O que aconteceu:** as saídas mostravam "t�tulo", "Peti��o" etc. A IA definia `PYTHONIOENCODING=utf-8` achando que corrigia, mas não corrigia.
- **Como foi detectado:** o erro de "≤" (entrada acima) levou a IA a investigar.
- **Causa provável:** os scripts rodam com `python -I` (modo isolado, por segurança), que **ignora** as variáveis `PYTHON*`.
- **Correção:** usar `python -I -X utf8`.
- **Resultado depois da correção:** saídas legíveis. Nenhum arquivo salvo foi afetado (todos gravados em UTF-8).
- **Bom para os slides?** não

## 2026-10-17 — Confiança na paginação da API do CNJ (12% das serventias de MG sumiram)
- **Onde:** código gerado (listagem de serventias do Justiça Aberta)
- **O que aconteceu:** a listagem paginada (33 páginas de 100) devolveu 3.213 registros, mas só 2.839 CNS distintos. Os ativos contados foram **2.222**, quando o certo é **2.525**. A IA chegou a tratar as repetições como "duplicatas" a remover.
- **Como foi detectado:** a IA investigou as duplicatas e viu que elas estavam sempre em páginas diferentes. Uma consulta em página única trouxe 3.213 CNS distintos.
- **Causa provável:** a API ordena os registros de forma não determinística entre páginas; a IA supôs que a paginação era estável.
- **Correção:** coletar em **página única por UF** e checar a integridade (`meta.total` = registros = CNS distintos). Essa checagem já detectou 1 registro faltando em SP.
- **Resultado depois da correção:** MG 2.222 → **2.525** ativas (+13,6%). Brasil: 12.121 ativas, 26 de 27 UFs íntegras.
- **Bom para os slides?** sim. Um erro que **reduziria o mercado em 12% sem nenhum aviso**, pego por uma checagem de integridade.

## 2026-10-17 — Soma de um código impressa como valor (SUSEP)
- **Onde:** código gerado (agregação dos ramos 0775/0776 do SES)
- **O que aconteceu:** a saída mostrou "cogrupo=33,1 mi", que é a soma do **código do grupo** tratado como valor monetário.
- **Como foi detectado:** a IA percebeu ao ler a saída e avisou o autor para ignorar a linha.
- **Causa provável:** o script somava todas as colunas, exceto uma lista de exclusão incompleta.
- **Correção:** na Fase 1, somar só uma lista explícita de colunas de valor.
- **Resultado depois da correção:** os números de prêmio, sinistro e comissão não foram afetados.
- **Bom para os slides?** não

## 2026-10-17 — Endereços do CNPJ da Receita tirados da memória (desatualizados)
- **Onde:** código gerado (listagem dos dados abertos do CNPJ)
- **O que aconteceu:** a IA tentou três endereços conhecidos (`arquivos.receitafederal.gov.br/dados/cnpj/...`, `.../cnpj/...` e `dadosabertos.rfb.gov.br`). Dois deram 404 e um deu timeout.
- **Como foi detectado:** teste de acesso.
- **Causa provável:** corte de conhecimento. A Receita migrou o repositório para o **SERPRO+** (Nextcloud).
- **Correção:** busca do endereço atual e navegação pelo compartilhamento público via WebDAV (sem conta). O endereço vai para `config/`, não fica fixo no código.
- **Resultado depois da correção:** os 22 arquivos do pacote 2026-10 foram baixados e testados (0 corrompidos).
- **Bom para os slides?** sim, junto com as normas. O conhecimento da IA "envelhece" e só o teste real mostra isso.

## 2026-10-17 — Norma estadual citada no SPEC sem conferência
- **Onde:** edição do SPEC (§5.3, lista de monitoramento do radar)
- **O que aconteceu:** a IA escreveu "Provimento 40/2026-CGJ/RS" como exemplo de norma estadual. Esse número só aparecia num resumo de busca, sem fonte oficial aberta.
- **Como foi detectado:** a própria IA, ao revisar o trecho logo depois de escrever.
- **Causa provável:** pressa em dar um segundo exemplo; violação da regra "nunca inventar números de normas".
- **Correção:** trocado por "norma da CGJ/RS de 27/08/2026, a confirmar na fonte oficial".
- **Resultado depois da correção:** o SPEC só cita como confirmado o que foi lido na fonte oficial.
- **Bom para os slides?** não

## 2026-10-17 — Código Python colado direto no PowerShell
- **Onde:** execução de comandos (Etapa 3)
- **O que aconteceu:** um comando `python -c "..."` com aspas e colchetes foi interpretado pelo PowerShell e falhou com erro de sintaxe.
- **Como foi detectado:** erro de execução.
- **Causa provável:** mistura de regras de aspas do PowerShell e do Python.
- **Correção:** escrever o código em arquivo de script e executá-lo.
- **Resultado depois da correção:** sem novas falhas desse tipo.
- **Bom para os slides?** não

## 2026-10-17 — (Sessão 0) A IA disse que o projeto não estava no git
- **Onde:** revisão do SPEC (Sessão 0, outra conversa)
- **O que aconteceu:** a IA afirmou que o projeto ainda não era um repositório git. Ele já estava no git e publicado no GitHub (`luccaamp/radar-seguro-cartorio`).
- **Como foi detectado:** pelo autor.
- **Causa provável:** afirmação feita sem verificar o ambiente (por exemplo, com `git status`).
- **Correção:** verificar o estado com comandos só de leitura antes de afirmar algo sobre o ambiente.
- **Resultado depois da correção:** registro feito pelo autor; a IA não tem acesso à conversa original.
- **Bom para os slides?** não

## 2026-10-17 — (Sessão 0) A IA tratou os Provimentos 227 e 243 e a ADI 8015 como incertos
- **Onde:** revisão do SPEC (Sessão 0, outra conversa)
- **O que aconteceu:** a IA não conhecia os Provimentos 227/2026 e 243/2026 nem a ADI 8015 e tratou a existência deles como incerta.
- **Como foi detectado:** o autor verificou e informou.
- **Causa provável:** corte de conhecimento anterior às normas.
- **Correção:** regra do SPEC de confirmar todo artigo no texto oficial na Fase 0. Feito em 2026-10-17: textos baixados de atos.cnj.jus.br e andamento da ADI lido no portal do STF.
- **Resultado depois da correção:** fatos confirmados, com artigo e cópia no bronze.
- **Bom para os slides?** sim

## 2026-10-17 — (Sessão 0) Prazo errado da primeira declaração do Prov. 227
- **Onde:** revisão do SPEC (Sessão 0, outra conversa)
- **O que aconteceu:** a IA disse que a primeira declaração venceria em 31/03/2027. O correto, pelo art. 18, é 30 dias após a vigência, por volta de 09/09/2026.
- **Como foi detectado:** pelo autor.
- **Causa provável:** corte de conhecimento anterior à norma. A IA aplicou a regra anual (art. 4º) sem conhecer a regra de transição.
- **Correção:** corrigido pelo autor no SPEC; na Fase 0 a IA confirmou o art. 18 e o art. 20 no texto oficial.
- **Resultado depois da correção:** prazo correto no SPEC, com o artigo citado.
- **Bom para os slides?** sim. Mostra por que a regra "toda norma conferida no texto oficial" existe.

---

> Registros acrescentados em 2026-10-18 (tarde), na verificação final da Fase 1 (`docs/revisao_fase1.md` e `docs/verificacao_final_fase1.md`). Fonte dos números: `scripts/verificacao_fase1/` sobre os Parquet de 09:52 (o motor reproduz o gold com diferença zero).

## 2026-10-18 — Troca da regra de classe reclassificava as faixas de déficit (A1)
- **Onde:** código gerado (`src/model/universo.py`, `src/model/mercado.py`, `src/transform/gold.py:67`)
- **O que aconteceu:** `universo()` recalcula a classe com os limites da regra escolhida e `deficit()` usa essa classe nas faixas. Na v1, 834 serventias do universo base ficam na Classe 3 (contra 354 na v2), com prob. e parte descoberta menores; e o peso da indeterminada é recalculado por regra (v1 0,932 × v2 0,678). Resultado: universo maior (1.545 × 1.121) com prêmio menor (R$ 382,9 mil × 404,4 mil). Esperado: a v1 só inclui serventias; as faixas seguem a classe v2. Com a correção: déficit base v1 R$ 44,9 mi e prêmio R$ 448,8 mil (≥ v2 em min, base e max).
- **Como foi detectado:** revisão do autor (A1); a IA havia apontado o efeito como "pergunta" no ponto (c), mas não corrigiu nem registrou como erro.
- **Causa provável:** D-011 aplicado ao pé da letra sem testar monotonicidade.
- **Correção:** proposta D-019 (aguarda aprovação) e teste de monotonicidade.
- **Bom para os slides?** sim (universo maior, mercado menor: falta de teste de propriedade).

## 2026-10-18 — "Serventias com déficit" contava serventias sem empregado (A4)
- **Onde:** `src/model/mercado.py`, `deficit()`
- **O que aconteceu:** `n_deficit = peso_universo × prob_deficit` sem olhar o passivo. No base v2, 8 serventias do universo com 0 CLT somam 3,8 das 489,9 "com déficit" (min 2,1; max 6,3). O valor do déficit delas já é zero.
- **Como foi detectado:** revisão do autor (A4: o número não muda entre métodos de rateio).
- **Correção:** proposta D-021 (prob. só onde passivo > 0) com teste.
- **Bom para os slides?** não

## 2026-10-18 — Testes gravando no banco real (A5, item 5)
- **Onde:** `tests/test_app.py` (`test_simulador_salva_cenario_sem_nova_versao`) e `app/comum.py:47` (conexão de escrita)
- **O que aconteceu:** o teste insere e apaga linhas em `estado.cenarios_salvos` de `data/radar.duckdb`. Na carga de 09:52, uma falha anterior desse teste já tinha criado uma versão 2 espúria das premissas no banco real (apagada à mão pela IA).
- **Como foi detectado:** leitura do código na verificação (a suíte NÃO foi rodada nesta etapa para não alterar o banco; data do arquivo antes e depois da verificação: 2026-10-18T09:52:40, 11.022.336 bytes).
- **Correção:** proposta: fixture que copia o banco para uma pasta temporária e aponta o app para ela por variável de ambiente.
- **Bom para os slides?** sim (teste que muda o dado que deveria proteger).

## 2026-10-18 — Correções 2, 3, 4 e 6 do painel não implementadas (A5)
- **Onde:** `app/`
- **O que aconteceu:** nenhum arquivo de `app/` mudou depois das 09:52; o Streamlit aberto às 13:27 já roda o código atual. As correções não foram feitas (não há registro delas nos docs desta sessão).
- **Correção:** etapa 1 do plano da verificação final.
- **Bom para os slides?** não

## 2026-10-18 — Datas-base misturadas no passivo (A2)
- **Onde:** `config/premissas/premissas_v001.yaml` (`data_posicao` 31/12/2025; `correcao_salarial_rais` INPC até o último mês) e `src/motor.py`
- **O que aconteceu:** tempo de casa, aviso, 13º e férias na posição de 31/12/2025 (RAIS e art. 4º do 227), mas salário corrigido até set/2026 (fator 1,0401) e empregados contados em out/2026 (CNJ). Efeito do INPC: +3,86% em passivo, déficit, IS e prêmio.
- **Correção:** proposta D-020 (data-base única 31/12/2025; INPC só como sensibilidade).
- **Bom para os slides?** não

## 2026-10-18 — Tabelas de conferência expõem municípios com menos de 3 serventias (D1)
- **Onde:** `app/pages/3_Qualidade_dos_dados.py` (tabelas de maiores diferenças e texto do gráfico CNJ × RAIS)
- **O que aconteceu:** 2 dos 10 municípios da tabela CNPJ − CNJ e 502 dos 821 pontos do gráfico têm menos de 3 serventias, com nome no texto ao passar o mouse.
- **Correção:** etapa 1 do plano (regra de 3 serventias + teste).
- **Bom para os slides?** não

## 2026-10-18 — Sinistralidade sobre prêmio ganho aplicada ao prêmio emitido (B5)
- **Onde:** `src/model/mercado.py` `_receita()`; rótulo do Simulador
- **O que aconteceu:** as premissas vêm de sinistro ÷ prêmio ganho (0775: 10,9%), e a conta multiplica pelo prêmio emitido. Pela mesma SES, sinistro ÷ emitido = 8,2% (0775) e 59,3% (0776).
- **Correção:** alinhar conta e rótulo (etapa 2, junto com o B1).
- **Bom para os slides?** não

## 2026-10-18 — Rastreabilidade incompleta e checagem de correlação fraca (C5, C1)
- **Onde:** `silver.fonte_metadados`; `src/quality/reconciliacao.py`
- **O que aconteceu:** sem URL em `cnj_colaboradores` e `susep_ses_garantia`; sem hora em `cnj_colaboradores`; data de referência = dia do download em `ibge_municipios`, `ibge_malha` (e no cadastro do CNJ, onde o snapshot é a referência). A correlação bruta (0,996) passa só por causa de BH: em log é 0,965, o erro mediano é 13,2% e só 69,1% dos municípios com ≥ 5 empregados ficam dentro de ±20%.
- **Correção:** etapa 1 do plano.
- **Bom para os slides?** sim (C1: métrica que passa sem testar nada).

---

> Acréscimos de 2026-10-18 (noite), na execução da Etapa 1 (`docs/aprovacao_etapa1_fase1.md`).

## Nota à entrada "Troca da regra de classe reclassificava as faixas de déficit (A1)"
- **O peso por regra não era erro; o erro era a classe das faixas.** A proposta da IA de unificar o peso da indeterminada (0,932 × 0,678) foi rejeitada pelo autor com razão: o peso mede a chance de uma serventia sem dado passar no corte de **cada** regra. Só a classe das faixas de déficit passou a ser sempre a da regra base.
- Além disso, as serventias que só entram pela v1 caíam na faixa da Classe 2 por um padrão implícito de `_faixa` ("tudo que não é 3 vira 2"), e não por decisão. Agora é uma tabela explícita e testada (`FAIXA_POR_CLASSE`).

## Nota à entrada "Correções 2, 3, 4 e 6 do painel não implementadas (A5)"
- Classificação do autor: **IA informou correção não feita.** Implementadas agora, no passo 10 da Etapa 1.

## 2026-10-18 — Data de referência do IBGE trocada pela observação (C5)
- **Onde:** `src/transform/silver.py`, `ler_municipios`
- **O que aconteceu:** ao registrar a versão da lista de municípios, a IA passou o texto da versão como observação, e a data de referência continuou sendo o dia do download.
- **Como foi detectado:** pelo teste novo `tests/test_rastreabilidade.py`, escrito antes de rodar o pipeline.
- **Correção:** data de referência "vigente em 2026-10-18" e a observação de que a API de localidades não informa a versão da DTB.
- **Bom para os slides?** não

## 2026-10-18 — Heredoc aninhado não aplicou a edição e não deu erro
- **Onde:** comando de shell usado pela IA para editar `src/transform/gold.py`
- **O que aconteceu:** um script Python dentro de um heredoc aninhado não rodou, sem mensagem de erro. A IA conferiu o arquivo, viu que nada mudou e refez com a ferramenta de edição.
- **Correção:** depois de toda edição por script, conferir a mudança (os scripts seguintes passaram a afirmar que cada trecho trocado existia uma única vez).
- **Bom para os slides?** não

---

> Acréscimos de 2026-10-18 (noite), no Bloco 1 de `docs/plano_qualidade_e_correcoes.md`.

## 2026-10-18 — "$" lido como fórmula LaTeX nas Limitações (1.1)
- **Onde:** `app/pages/3_Qualidade_dos_dados.py` (bloco "Limitações declaradas") e três `help=` da página Início.
- **O que aconteceu:** o item "Regra dos R$ 300 mil" tinha dois "R$" no mesmo texto, sem escape; o Streamlit leu o trecho entre eles como fórmula e mostrou `**` e fonte de código. A função de escape existia (`md`), mas não foi usada nesse bloco.
- **Como foi detectado:** revisão do painel pelo autor.
- **Correção:** função única `md_seguro` e teste estático (`tests/test_app_codigo.py`) que falha se algum texto com "R$" (ou valor de `brl`/`faixa`) chega ao Streamlit sem ela, mais um teste que renderiza as 4 páginas e procura o padrão LaTeX.
- **Bom para os slides?** não

## 2026-10-18 — Mapa pintava cada município pequeno com o total da região (1.2)
- **Onde:** `app/pages/1_Mercado.py` (Etapa 1, passo 10).
- **O que aconteceu:** para proteger os municípios com menos de 3 serventias, a IA deu a cada um o total da sua região imediata. Uma região com 10 cidades pequenas pintava as 10 com o total, e as manchas escuras viravam grupos de municípios minúsculos: leitura visual errada.
- **Como foi detectado:** revisão do painel pelo autor.
- **Correção:** geometria dissolvida no gold (`gold.geo_mapa_publico`, 385 áreas: 315 municípios e 70 grupos regionais), pintada uma vez por área; contrato de que nenhuma área pública tem menos de 3 serventias.
- **Bom para os slides?** sim (proteger o dado sem distorcer a leitura).

## 2026-10-18 — Testes do painel regravavam os Parquet reais de data/gold
- **Onde:** `src/transform/gold.py` (`_gravar`) chamado pelo fixture de `tests/test_app.py`.
- **O que aconteceu:** desde a Etapa 1, o fixture refazia o gold na cópia temporária do banco, mas `_gravar` sempre exportava o Parquet para `data/gold`. O teste de proteção só olhava o banco. O conteúdo era o mesmo, mas era uma escrita fora da cópia.
- **Como foi detectado:** pela IA, ao implementar a carga atômica (1.7).
- **Correção:** `exportar_parquet=False` nos testes; o teste de proteção passou a conferir também os Parquet de `data/silver` e `data/gold`.
- **Bom para os slides?** não

## Nota à entrada "Heredoc aninhado não aplicou a edição e não deu erro" ([VERIFICAR] do 1.7)
- O arquivo era `src/transform/gold.py` (passar a classe da regra base, `lim_base`, para as faixas de déficit). A edição foi refeita com a ferramenta de edição na mesma hora.
- Cobertura: o contrato de monotonicidade do gold e o fixture de `tests/test_app.py`, que refaz o gold e falha em qualquer contrato violado, pegariam a ausência; a reprodutibilidade agora também é testada (`tests/test_pipeline.py`).
- Regra nova no `CLAUDE.md`: código só com a ferramenta de edição, nunca por script de substituição.

---

> Acréscimos de 2026-10-18 (noite), na revisão do painel com filtros (`docs/revisao_painel_filtros.md`).

## 2026-10-18 — Vazamento por subtração entre visões (E1, crítico, LGPD)
- **Onde:** página Mercado (Bloco 1): a regra de 3 serventias era checada em cada tabela isoladamente.
- **O que aconteceu:** visão geral × filtro Classe 3 por município: BH 34 × 33, Uberaba 9 × 8, Betim 6 × 5 serventias. A diferença isolava 1 cartório (CLT e passivo).
- **Como foi detectado:** revisão do autor, exportando as visões com filtro.
- **Causa provável:** a IA testou "nenhuma célula com menos de 3" e não "nenhuma diferença entre células com 1 ou 2".
- **Correção:** visões filtradas por região com supressão complementar, hierárquica e secundária; auditor de ataque por diferença (pares contidos, complemento, resto de partição) que roda no gold e falha a carga; teste `test_ataque_por_diferenca` com o caso BH/Classe 3 fixo.
- **Bom para os slides?** sim (o caso mais forte de "onde a IA errou": proteção que parecia certa e não era).

## 2026-10-18 — O mesmo ataque pela troca de regra ou de nível (E1-b, achado na auditoria própria)
- **Onde:** Mercado e `gold.fato_mercado_municipio_publico` (todas as regras e níveis por município).
- **O que aconteceu:** v1 − v2 e máximo − base, na mesma área, isolavam serventias que mudam de lado no universo. O auditor também achou casos no total de MG (RTD × RCPJ, 2 serventias; RI e indeterminada entre níveis).
- **Correção:** D-027 (proposta aplicada) e união de RTD e RCPJ no filtro (D-026).
- **Bom para os slides?** sim.

## 2026-10-18 — Ranking cortava as maiores barras; mapa sem escala; cinza = branco (E2, E3, E5)
- **O que aconteceu:** o eixo do ranking não tinha folga para o rótulo da maior barra; a escala de cores sumiu; as áreas sem dado publicável saíam brancas como os municípios sem serventia.
- **Correção:** eixo até o máximo × 1,15 com rótulo fora da barra; escala sempre presente, em R$ e com "≥" quando satura; três camadas (cinza de contexto, sem serventia claro com contorno, valor) com legenda em texto. Testes na auditoria (`tests/test_auditoria_painel.py`).
- **Bom para os slides?** não

## 2026-10-18 — Páginas de app/pages só achavam `comum` por sorte nos testes
- **O que aconteceu:** rodando sozinha no AppTest, `pages/1_Mercado.py` não importava `comum` (fica em `app/`). Os testes passavam porque a Início rodava antes e punha `app/` no caminho.
- **Correção:** o fixture de sessão põe `app/` no caminho explicitamente (`tests/apoio_painel.py`).
- **Bom para os slides?** não

## 2026-10-18 — Zoom do mapa do município deixava o destaque fora do quadro (achado pelo QA visual)
- **Onde:** `app/pages/1_Mercado.py`, função `mapa` (U1).
- **O que aconteceu:** o zoom era `log2(360 / vão) + 0,6`, que supõe um mapa bem mais largo que os ~470 px da coluna em 1280; o centro era a média das latitudes (não de Mercator) e o enquadramento não incluía a geometria do próprio destaque. Em Almenara metade do polígono ficava fora; num município pequeno (área agregada) o destaque inteiro sumia. A auditoria do AppTest só conferia `zoom > 5,1`, não o que aparece na tela.
- **Correção:** `_enquadrar` calcula o zoom em Web Mercator (mundo = 512 × 2^z px) para a largura útil em 1280, com folga, inclui o destaque e desloca o centro por causa da escala de cores. A checagem 5 de `tests/test_visual.py` confere os vértices do polígono contra o quadro.
- **Bom para os slides?** sim (teste que passava sem olhar a tela).

## 2026-10-18 — Checagem visual com falsos alarmes (QA)
- **O que aconteceu:** na galeria "antes", 100 das 182 falhas eram da própria ferramenta: 404 internos do Streamlit em `/_stcore/` tratados como erro nosso, e contagem de barras lida de `gd.data` (binário no Plotly 6). Também faltavam o texto de botão e a tabela dentro do expansor nas checagens.
- **Correção:** filtro de `/_stcore/` com o motivo documentado em `ouvir_console`; `gd._fullData`/`gd.calcdata`; seletor de botão; o `abrir` expande os expansores do Mercado. As comparações "antes × depois" separam essas categorias.
- **Bom para os slides?** não

## 2026-10-19 — `pipeline.py --help` trocava o banco por um vazio (achado no clone limpo)
- **Onde:** `pipeline.py` (`main(sys.argv[1])` sem validação dos argumentos).
- **O que aconteceu:** qualquer argumento desconhecido (ex.: `--help`) era tratado como etapa; nenhuma etapa rodava, mas a carga atômica criava um banco quase vazio e fazia `os.replace` sobre `data/radar.duckdb`. Num clone limpo só criou um banco vazio; no ambiente do autor teria apagado a carga real. Nenhum teste chamava o pipeline pela linha de comando.
- **Correção:** ver o registro da rodada "repositório reproduzível" no diário (argparse com `--help`, etapas válidas e `--a-partir-de`; teste de linha de comando).
- **Bom para os slides?** sim (um `--help` inofensivo que destruía dados).

## 2026-10-19 — Instalador de dados punha os arquivos numa subpasta (achado na prova final)
- **Onde:** `scripts/baixar_dados.py`.
- **O que aconteceu:** o script criava a pasta de destino e depois movia a pasta extraída para dentro dela (`shutil.move` numa pasta que já existe = mover para dentro). O silver ia para `data/silver/extr_silver/`, e o `pipeline.py --a-partir-de silver` dizia "Nenhum Parquet". A conferência de hashes tinha passado, porque era feita antes de mover.
- **Correção:** move arquivo por arquivo para o caminho do manifesto. O `tests/test_pacotes.py`, com pacote sintético, confere a estrutura final, as partes, o arquivo corrompido e o `--substituir`.
- **Bom para os slides?** sim (conferir o hash não basta: é preciso conferir onde o arquivo foi parar).

## 2026-10-19 — Troca de pastas falhava no OneDrive
- **Onde:** `scripts/gerar_publico.py` e `scripts/empacotar_dados.py`.
- **O que aconteceu:** renomear e apagar pastas recém-alteradas falhou (WinError 183 e 5), porque o OneDrive segura a pasta enquanto sincroniza. O `data/publico` anterior ficou intacto; sobraram pastas vazias ignoradas pelo git.
- **Correção:** troca arquivo por arquivo, com o manifesto por último (`publico.trocar_conteudo`), e remoção de pastas com novas tentativas.
- **Bom para os slides?** não

## Registro completo da Fase 1 (acrescentado em 2026-10-19, `docs/limpeza_projeto.md` 2.4)
Os erros abaixo foram achados nas revisões da Fase 1 e ainda não tinham entrada própria aqui; os demais da lista do autor já estavam registrados acima (A1, A2, A4, A5, D1, E1, E1-b com RTD × RCPJ, testes gravando no banco e nos Parquet, "$" virando fórmula, zoom do município, `pipeline.py --help`, instalador em subpasta, edição por script).

## 2026-10-19 — `qualidade.rec_municipio` publicava grupos com 1 ou 2 serventias
- **Onde:** `src/quality/reconciliacao.py` (`rec_municipio_publico`), página Qualidade dos dados.
- **O que aconteceu:** a versão pública (D1) somava os municípios pequenos por região imediata, mas não conferia o tamanho do grupo. 4 grupos tinham 1 ou 2 serventias e mostravam o CLT declarado e os vínculos da RAIS delas. O teste de LGPD do painel olhava só nomes de município, não contagens.
- **Como foi achado:** pela checagem de limiar do `scripts/gerar_publico.py`, ao montar o conjunto público.
- **Correção:** os grupos pequenos viram uma linha "Outras regiões" (com proteção para o caso de a soma também ficar pequena). Os números de referência não mudaram.
- **Bom para os slides?** sim (a proteção existia, mas não era testada no lugar certo).

## 2026-10-18 — C1 a C3 declarados corrigidos por teste estrutural, sem efeito na tela
- **Onde:** página Mercado (ranking, escala do mapa, colunas das tabelas); `tests/test_auditoria_painel.py`.
- **O que aconteceu:** na revisão dos filtros (E2, E3), a IA declarou corrigidos o rótulo cortado da maior barra e a escala de cores, porque o teste do AppTest conferia o JSON da figura (eixo até 1,15 × o máximo, `colorbar` presente). Na tela, o "R$ 6,3 mi" continuava cortado, a escala não tinha título e colunas sumiam em 1280 px.
- **Como foi achado:** pelo autor, olhando o painel (C1 a C3 de `correcoes_e_qa_visual.md`); a galeria com Playwright confirmou (182 falhas no "antes").
- **Correção:** QA visual com prints e checagens pelo DOM (`scripts/qa_painel.py`, `tests/test_visual.py`, `-m visual`); só conta como corrigido o que aparece certo no print "depois".
- **Bom para os slides?** sim (teste verde que não olhava a tela).

## 2026-10-18 — "Juíz de Fora" com acento no painel (C4)
- **Onde:** nomes de região do IBGE no silver e no Mercado.
- **O que aconteceu:** a API de localidades do IBGE grafa a região intermediária 3106 como "Juíz de Fora". A IA levou o nome adiante sem conferir contra o nome do município-sede.
- **Como foi achado:** pelo autor, no painel.
- **Correção:** `config/correcoes_nomes.yaml`, com a evidência, aplicado no silver (o bronze não muda), e o teste `tests/test_nomes.py`: nenhum nome de região difere do município do IBGE só por acento.
- **Bom para os slides?** não

## 2026-10-19 — `GROUP BY` sem `ORDER BY`: texto mudava de ordem entre cargas
- **Onde:** `src/quality/reconciliacao.py` (detalhe da checagem "cobertura da arrecadação" e linhas do `resumo_publico`).
- **O que aconteceu:** a ordem das partes do texto vinha de um `GROUP BY` sem `ORDER BY`, que o DuckDB não garante. Os números eram iguais, mas o hash de conteúdo da tabela mudava.
- **Como foi achado:** na prova de reprodutibilidade (24 de 25 tabelas idênticas no caminho 3).
- **Correção:** `ORDER BY 1` nas duas consultas; a prova passou a dar 25 de 25.
- **Bom para os slides?** não

## 2026-10-19 — Regra do mínimo de 3 serventias ausente do `CLAUDE.md`
- **Onde:** `CLAUDE.md`, "Regras inegociáveis".
- **O que aconteceu:** ao escrever a regra de LGPD do público (D-030), a IA não conferiu que a regra do mínimo de 3 serventias por área (SPEC, seção de LGPD; D-026, D-027) também estava no `CLAUDE.md`. Ela não estava: o histórico do git não mostra essa regra em nenhuma versão commitada do arquivo, então a lacuna vinha de antes e não foi notada.
- **Como foi achado:** pelo autor, comparando o `CLAUDE.md` com as regras do projeto (`limpeza_projeto.md` 2.1).
- **Correção:** regra restaurada em 2026-10-19, junto com as do pacote da equipe, do `gh`, do disco e do dado pessoal.
- **Bom para os slides?** não

## 2026-10-19 — Pacote de dados gravado dentro do OneDrive
- **Onde:** `scripts/empacotar_dados.py` (saída padrão `pacotes/<nivel>/`, dentro do projeto).
- **O que aconteceu:** a IA percebeu o risco no pacote da equipe (8,4 GB) e o gerou fora do OneDrive com `--saida`, mas deixou a saída padrão dentro do projeto, e o pacote público de teste ficou lá (`pacotes/publico`, 2,6 MB), sincronizado pelo OneDrive.
- **Como foi achado:** pelo autor (pré-inventário da limpeza, P5).
- **Correção:** proposta na limpeza (Etapa 2): saída padrão em `C:\radar_pacotes`, e a pasta do projeto removida.
- **Bom para os slides?** não

## 2026-10-19 — Lista de contratos do silver dependia de quais colunas existiam
- **Onde:** `src/quality/contratos.py` (`sem_dados_pessoais`).
- **O que aconteceu:** o contrato "sem CPF em campos de texto" só era criado para tabelas com colunas de texto. Ao tirar do silver público as colunas que o pipeline não usa (D-031), a `rais_vinculo` ficou sem texto, a checagem sumiu e `qualidade.checagens` deixou de bater com o conjunto público (gold 18 de 18 idêntico, mas 24 de 25 tabelas no total).
- **Como foi achado:** no teste da D-031 (pacote público novo + `pipeline.py --a-partir-de silver` num clone).
- **Correção:** no silver, a checagem sai sempre (0 se não há texto); no gold, como antes, para não mudar a carga real. O teste voltou a dar 25 de 25.
- **Bom para os slides?** não

## Erros do revisor (assistente no chat)
O projeto registra erros de IA de qualquer origem, inclusive do assistente que revisa as rodadas no chat (informados pelo autor em 2026-10-19).
- **Manchas escuras no mapa de serventias:** interpretadas como efeito da agregação; eram reais (municípios com muitos distritos de registro civil). Ver o diário, leitura 5 da revisão dos filtros.
- **Almenara "cortada no mapa":** apontada como defeito; era um zoom manual do autor no momento da exportação do print.
- **`config/apelidos_municipios.yaml` "vazio":** o "0 KB" do levantamento era arredondamento; o arquivo tem as grafias que diferem do IBGE e é usado na normalização.
- **Partição "todas × obrigadas" (Almenara) como vazamento crítico:** o autor discordou e decidiu pela D-028 (partições internas da mesma visão não são suprimidas).
- **Plano de repositório com um repositório só:** uma versão do plano contrariava a decisão do autor (dois repositórios: código público e dados privado; D-030).

## 2026-10-19 — O coletor da RAIS não regera o extrato a partir do original (achado no inventário da limpeza)
- **Onde:** `src/ingest/rais.py`, `filtrar()`.
- **O que aconteceu:** o `.COMT` dos vínculos (extraído do `.7z`) vem separado por vírgula e entre aspas; o `filtrar()` lê com `;` e procura `"CNAE 2.0 Subclasse - Codigo"` num cabeçalho que vira uma coluna só (`ValueError`). O extrato do bronze (`RAIS_VINC_PUB_MG_ES_RJ_CNAE6912500_MG.csv`, separado por `;`) não pode ter saído desta versão do código; o pipeline funciona porque lê o extrato pronto. É a mesma causa da entrada de 2026-10-17 ("separador fixado como `;`, quando o arquivo usa `,`"), que voltou no coletor de vínculos.
- **Como foi achado:** no teste de extração da D-032 (cópia fora do OneDrive): regenerar o extrato a partir do `.7z` guardado. CNPJ e SUSEP regeneraram com o mesmo SHA-256; a RAIS quebrou.
- **Correção:** não feita (a limpeza não mistura correção; princípio 5 de `docs/limpeza_projeto.md`). Proposta na Parada 1: detectar o separador e conferir que o extrato regenerado tem o mesmo hash, antes de tirar os originais da RAIS do bronze oficial.
- **Bom para os slides?** sim (o pipeline passava; só regenerar o dado do zero mostrou que a coleta não é reprodutível).

## 2026-10-19 — Correção do coletor da RAIS (D-032 a; exceção aprovada ao princípio 5)
- **Correção da entrada "O coletor da RAIS não regera o extrato a partir do original":** o `filtrar()` agora detecta o separador pelo cabeçalho (`rais.separador`; `;` ou `,` entre aspas). O teste `tests/test_coletores.py::test_rais_extrato_regenerado_igual` (`dados_reais`) regera o extrato a partir do `.7z` guardado e confere o mesmo SHA-256 do extrato do bronze; há também um teste sintético na suíte padrão.
- **Bom para os slides?** sim (junto com a entrada anterior).

## 2026-10-19 — Testes novos dependiam de haver um repositório git
- **Onde:** `tests/test_links_docs.py` e `tests/test_notebooks.py` (listavam arquivos com `git ls-files`).
- **O que aconteceu:** numa pasta sem `.git` (a cópia de teste, ou um zip baixado do GitHub), a lista vinha vazia e os dois testes falhavam.
- **Como foi achado:** na suíte da cópia de teste da D-032 (2 failed).
- **Correção:** `tests/apoio_painel.py::arquivos_versionaveis()` usa o git quando há repositório e, senão, varre o disco pulando as pastas ignoradas.
- **Bom para os slides?** não

## 2026-10-19 — Remoção do pydantic deixou pacotes pela metade no .venv
- **Onde:** `.venv` (ambiente local; não versionado).
- **O que aconteceu:** o `uv remove pydantic` não conseguiu apagar pastas `licenses` do `.venv`, porque o OneDrive negou acesso. Ao apagá-las à mão, a IA deixou os metadados do `pydantic`, `pydantic_core`, `annotated_types` e `typing_inspection` incompletos, e a suíte passou a mostrar 72 avisos de metadado.
- **Correção:** conferido que os 4 pacotes saíram do `uv.lock`, as sobras foram removidas do `.venv` e o `uv sync` foi feito; a suíte voltou sem avisos.
- **Bom para os slides?** não

## 2026-10-19 — Originais movidos ficaram dentro de uma pasta com o próprio nome
- **Onde:** script de movimentação para `C:\radar_arquivo` (scratch da limpeza; não versionado).
- **O que aconteceu:** para um arquivo isolado, o destino já incluía o nome do arquivo e o script acrescentou o nome de novo: `…\BaseCompleta.zip\BaseCompleta.zip`. O SHA-256 conferido depois de mover batia (o conteúdo estava certo), mas o caminho não, e o `MANIFESTO.md` registrou o destino errado.
- **Como foi achado:** os 3 testes de regeneração (`dados_reais`) falharam com "Permission denied" ao abrir o que era uma pasta.
- **Correção:** cada um dos 27 arquivos subiu um nível, com o SHA-256 conferido de novo contra o manifesto; uma nota de correção foi acrescentada ao `MANIFESTO.md` (nada apagado). Os testes de regeneração passaram.
- **Bom para os slides?** sim (conferir o hash depois de mover não basta: é preciso conferir também onde o arquivo foi parar; mesmo padrão do instalador em subpasta).

## 2026-10-19 — Script da prova do clone rodou comandos no projeto real (codificação do caminho)
- **Onde:** script PowerShell da prova final da limpeza (scratch, não versionado).
- **O que aconteceu:** o `.ps1` foi gravado em UTF-8 sem BOM; o PowerShell 5.1 leu o "Á" de "Área de Trabalho" errado, o caminho do projeto saiu corrompido, o clone não foi montado e os `Set-Location` falharam. Os comandos seguintes rodaram na pasta atual, que era o **projeto real**:
  - `baixar_dados.py` recusou instalar silver e bronze ("Já há dados locais… Nada foi alterado"; a proteção funcionou);
  - `pipeline.py --a-partir-de silver` e `--a-partir-de bronze` rodaram sobre os dados reais, recalculando a partir dos mesmos dados;
  - a instalação da camada `originais` foi para a pasta do clone, mas gravou um `data/carga_atual.json` no projeto.
- **Como foi achado:** na leitura da saída da prova.
- **Verificação:** gold 25/25 e público 25/25 idênticos à linha de base, 10 números iguais, `data/publico` 26/26 arquivos intactos, originais (27) e bronze oficial intactos. O banco e os Parquet foram regravados com o mesmo conteúdo.
- **Correção:** o `data/carga_atual.json` criado por engano foi apagado (antes não existia). A prova foi refeita com o caminho passado como parâmetro e com parada imediata se o `Set-Location` falhar.
- **Lição:** script que muda de pasta tem de parar se a mudança falhar (`$ErrorActionPreference = "Stop"`), e nunca deve depender de caminho com acento escrito no próprio arquivo.
- **Bom para os slides?** sim (a proteção "nunca sobrescreve sem --substituir" segurou o pior).

## 2026-10-20 — Linha de base da limpeza não listava os arquivos soltos de data/
- **Onde:** script da linha de base da limpeza (`C:\radar_arquivo\baseline\linha_de_base.json`, gravado em 2026-10-19 19:59).
- **O que aconteceu:** a linha de base registrava arquivo por arquivo só `data/gold`, `data/silver`, `data/publico` e o banco; do resto de `data/` guardava apenas o tamanho de cada subpasta. Um arquivo solto na raiz de `data/` (como o `carga_atual.json`) não ficava registrado. Por isso, quando o script da prova criou esse arquivo por engano (entrada anterior), a linha de base não servia de prova de que ele não existia antes. A evidência foi indireta: o `git status --ignored` do inventário, o conteúdo do arquivo (instalado às 23:12, camada `originais`) e o fato de só o `baixar_dados.py` criá-lo.
- **Como foi achado:** pelo autor, ao pedir que a IA mostrasse na linha de base que o arquivo não existia.
- **Correção:** `scripts/linha_de_base.py` (versionado) registra todos os arquivos de `data/` (caminho, tamanho, data de modificação e SHA-256), inclusive os soltos na raiz, além dos hashes de conteúdo e dos números de referência. Também: o `baixar_dados.py` passou a recusar gravar o `carga_atual.json` onde já há banco ou gold, salvo com `--substituir` (ver o diário).
- **Bom para os slides?** sim (uma linha de base só prova o que ela registra).

## 2026-10-20 — Comando de lint "padrão" documentado sem ter sido rodado como documentado
- **Onde:** `CLAUDE.md` e `CONTRIBUTING.md` (`uv run ruff check src app tests scripts pipeline.py --exclude scripts/arquivo`).
- **O que aconteceu:** na limpeza, a IA documentou esse comando como o padrão do projeto, mas só tinha rodado o ruff com `--select F401,F841,F821`. Com as regras padrão do ruff 0.17, o comando acusa 103 avisos de estilo (ordem de imports, `noqa` sem uso, `dict()` em vez de `{}`, `subprocess.run` sem `check`, etc.), nenhum de erro real. Só com as regras do pyflakes (`--select F`), passa.
- **Como foi achado:** ao rodar o comando completo depois da mudança no `baixar_dados.py` (2026-10-20).
- **Correção:** pendente de decisão do autor. Proposta: fixar `[tool.ruff.lint] select = ["F"]` no `pyproject.toml` (erros reais: imports e variáveis sem uso, nomes indefinidos), para o comando documentado passar, e tratar as regras de estilo depois, se o autor quiser.
- **Bom para os slides?** não

## Nota à entrada "Comando de lint 'padrão' documentado sem ter sido rodado como documentado" (2026-10-20)
- **Correção aplicada, com a aprovação do autor:** `[tool.ruff.lint] select = ["F"]` no `pyproject.toml`. O comando documentado passa sem avisos (`All checks passed!`) e a suíte padrão segue com 135 passed. As regras de estilo ficaram como pendência no `docs/ESTADO_ATUAL.md`.

## 2026-10-20 — Pasta de QA dada como cópia sem comparar
- **Onde:** `docs/ESTADO_ATUAL.md` (pendências), no fechamento da Fase 1.
- **O que aconteceu:** a IA escreveu que `docs/qa/depois/` "repete a galeria de `docs/qa/atual/`" só porque as duas tinham os mesmos 54 nomes de arquivo e quase o mesmo tamanho.
- **Como foi achado:** pela própria IA, ao conferir com `diff -rq` antes do relatório: as imagens são diferentes.
- **Correção:** o texto passou a dizer que é uma galeria de outra rodada, com imagens diferentes, e a decisão de mantê-la ficou com o autor. Regra: mesmo nome e tamanho parecido não provam cópia; comparar o conteúdo (hash ou `diff`).
- **Bom para os slides?** não
