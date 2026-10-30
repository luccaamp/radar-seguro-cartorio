# Erros da IA

Registro dos erros cometidos pela IA e pelo revisor (o assistente que revisa as rodadas no chat), no código, nos documentos, nos agentes do radar ou do chat, e do que foi feito para corrigir. Daqui saem os 2 ou 3 casos para o slide "onde a IA errou e o que mudou".

**Ordem:** as primeiras entradas ficaram fora da ordem das datas, e os erros do revisor têm uma seção própria no meio do arquivo; as entradas novas da IA vão sempre no fim. Nada é reordenado.

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

### 2026-10-21 — ROADMAP.md entregue pelo revisor com fatos errados e lacunas
- **Onde:** `docs/ROADMAP.md`, na versão entregue pelo revisor ao autor.
- **O que aconteceu:**
  - a E2 não trazia os itens S1 a S6 reais do plano de qualidade (falava de taxa, despesas, market share e escolha de garantia);
  - o efeito da E2 nos números estava como "8 a 10"; o certo é 6 a 10 (o S2 muda a probabilidade de déficit);
  - aparecia a palavra "calculadora", que não existe no projeto;
  - a SES por UF foi tratada como existente, sem conferência;
  - a avaliação do chat estava mais fraca que a do SPEC §7 (só "acerto mínimo", sem gabarito congelado, métricas e comparação das versões);
  - o Radar e a Entrega (Fases 4 e 5 do SPEC) foram esquecidos.
- **Como foi detectado:** pela análise de contradições que o autor pediu à IA antes de qualquer edição (2026-10-21).
- **Correção:** a rodada de harmonização dos documentos (D-035): E2 reescrita, "calculadora" trocada, SES por UF marcada "a conferir", SPEC §7 incorporado na E5, Radar como etapa opcional e Entrega por marco.
- **Bom para os slides?** sim (o revisor também erra; a conferência contra o projeto real pega).

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

## 2026-10-20 — Pipeline cai quando a saída é redirecionada (codificação cp1252)
- **Onde:** código gerado (`pipeline.py`, `etapa_gold`, linha 71, impressão das reconciliações).
- **O que aconteceu:** `pipeline.py --a-partir-de silver` com a saída num pipe parou com `UnicodeEncodeError: 'charmap' codec can't encode character '≥'`. O texto da checagem tem "≥", e, fora de um console, o Python no Windows grava a saída em cp1252, que não tem esse caractere. O banco não foi substituído (a carga é gravada num arquivo temporário e só troca no fim). Esperado: o pipeline rodar igual com a saída no terminal, num arquivo ou num pipe.
- **Como foi detectado:** na verificação da pasta nova (2026-10-20), ao rodar o pipeline numa cópia com a saída redirecionada para um log.
- **Causa provável:** a IA usou caracteres fora do cp1252 nas mensagens e só testou com a saída no console (UTF-8).
- **Correção (aprovada pelo autor e aplicada em 2026-10-20):** `sys.stdout.reconfigure(encoding="utf-8")` (e o mesmo no `stderr`) na entrada do `pipeline.py` e dos 7 scripts que imprimem (`acessibilidade`, `baixar_dados`, `empacotar_dados`, `gerar_publico`, `jsonl_para_md`, `linha_de_base`, `prints_painel`). Testes em `tests/test_saida_utf8.py`:
  - suíte padrão: varre o `pipeline.py` e os `scripts/` e falha se um arquivo que imprime não reconfigura a saída;
  - `dados_reais`: roda `pipeline.py --a-partir-de silver` numa cópia temporária do projeto e do banco, com `PYTHONIOENCODING=cp1252` e a saída num arquivo. Com o `pipeline.py` antigo, falha com o mesmo `UnicodeEncodeError`; com o novo, passa.
- **Bom para os slides?** não

## 2026-10-20 — O painel gravava no banco do pipeline, e isso não foi notado na Fase 1
- **Onde:** código gerado (`app/comum.py`, `_abrir`; `app/pages/2_Simulador.py`, "Salvar"; `src/estado.py`).
- **O que aconteceu:** o painel abria `data/radar.duckdb` para gravação. Ao abrir qualquer página, criava as tabelas de estado e inseria a semente se faltasse. No "Salvar" do Simulador, gravava o cenário e, se alguma premissa tivesse mudado, **uma versão nova de premissas**, que passava a ser a vigente para a carga seguinte (`src/transform/gold.py:220`), para o Início (teto teórico), para o conjunto público e para a linha de base. Esperado: o banco é resultado reproduzível do pipeline, e o painel só o lê.
- **Efeitos:** o banco real nunca recebeu cenário nem versão do painel (só as sementes v1 e v2; conferido em 2026-10-20), então nenhum número publicado foi afetado. Mas:
  - o SHA-256 do banco mudava a cada uso do painel;
  - com o painel aberto, nenhum outro programa conseguia ler o banco (o pipeline falhava logo no início);
  - todas as conferências da Fase 1 precisaram de uma cópia do banco para não mexer no real, sem que a causa fosse registrada.
- **Como foi detectado:** pela IA, na verificação da pasta nova (2026-10-20), ao preparar o comando para o autor abrir o painel (`duckdb.connect(caminho)` sem `read_only`). O autor pediu a correção.
- **Causa provável:** o SPEC (§2.1, §2.4) previa o estado do app "no mesmo arquivo DuckDB", e a IA seguiu sem medir as consequências: estado pessoal misturado ao resultado reproduzível e versões do painel virando premissa oficial. Os testes usavam sempre uma cópia, o que escondia o efeito.
- **Correção:** D-034. O painel abre o banco só para leitura; os cenários vão para `data/painel_estado.json` (`src/cenarios.py`), sem criar versão de premissas; o pipeline para antes de começar se o banco estiver aberto. Testes: SHA-256 igual depois de abrir e salvar, banco com atributo de somente leitura, cenário presente depois de reiniciar, varredura de `read_only` no código do painel.
- **Bom para os slides?** sim (um teste que sempre usa cópia pode esconder que o programa grava onde não devia).

## 2026-10-20 — Teste substituído sem aprovação e contagem parcial apresentada como a da suíte
- **Onde:** relatório da D-034 e `tests/test_app.py`.
- **O que aconteceu:**
  - (1) o relatório trouxe "63 passed" para os testes `dados_reais`, logo depois de uma rodada com 73. Os 63 eram só 4 arquivos (`test_app` 14, `test_auditoria_painel` 45, `test_pipeline` 3, `test_saida_utf8` 1), não a suíte inteira, e o relatório não deixou isso claro;
  - (2) ao reescrever o teste de "Salvar cenário", a IA trocou `test_simulador_salva_cenario_sem_nova_versao` (Fase 1) por um teste de nome novo, sem pedir aprovação. A regra do autor: nenhum teste removido sem aprovação.
- **Como foi detectado:** pelo autor, ao perguntar por que a contagem caiu de 73 para 63. A IA comparou a lista de testes coletados no commit `21303e2` (73) com a atual (76): a única saída era esse teste; as entradas eram 3 testes novos do painel e o `test_pipeline_com_saida_redirecionada`.
- **Causa provável:** rodada parcial para ganhar tempo, sem rodar a suíte inteira antes do relatório; e o teste antigo tratado como "o mesmo teste reescrito", em vez de mantido.
- **Correção:**
  - o teste voltou com o nome original e a mesma intenção (salvar sem mexer em premissa grava o cenário e não cria versão nova); só as verificações passaram da tabela antiga para o arquivo de cenários. O teste novo do SHA-256 ficou ao lado;
  - a suíte `dados_reais` foi rodada inteira.
  - Regras: nunca comparar contagens de rodadas diferentes sem dizer o que cada uma cobriu; mudar o que um teste verifica só dizendo qual teste e por quê; remover, só com aprovação.
- **Bom para os slides?** não

## 2026-10-22 — Arquivo de teste gravado por comando do shell, e não pela ferramenta de edição
- **Onde:** `tests/test_notebooks.py` (D-038).
- **O que aconteceu:** a IA regravou o arquivo inteiro com um heredoc no Bash (`cat > ... <<EOF`), contra a regra do `CLAUDE.md` ("edite código só com a ferramenta de edição de arquivos").
- **Como foi detectado:** pela própria IA, ao reler as regras antes de editar o arquivo seguinte.
- **Causa provável:** o arquivo ia ser quase todo reescrito, e o shell pareceu o caminho mais curto.
- **Correção:** o conteúdo foi conferido (a suíte passou: 178 testes) e todas as edições seguintes de código usaram a ferramenta de edição. Os notebooks 01 e 02 foram gerados por um script no scratchpad (arquivos novos, montados com `nbformat`), não por substituição de texto.
- **Bom para os slides?** não

## 2026-10-22 — Gráficos com mediana e cercas diferentes das tabelas
- **Onde:** notebooks 02 (distribuições e boxplot por situação) e 01 (saltos).
- **O que aconteceu:** (1) no histograma, a mediana e a média foram calculadas só com os valores positivos, enquanto a tabela usava todos (CLT: a linha marcava 3, e a mediana real é 2); (2) o boxplot do matplotlib aplica a regra de Tukey na escala comum, e o texto dizia "cercas de Tukey em log", como no notebook 01; (3) no gráfico de saltos, os zeros apareciam como "R$ 1".
- **Como foi detectado:** revisão dos PNGs pela IA antes do relatório.
- **Causa provável:** o filtro `> 0`, necessário para a escala log das barras, foi reaproveitado nas linhas de resumo; o padrão do boxplot não foi conferido.
- **Correção:** mediana e média da série inteira; boxplot desenhado em log10; zeros marcados com "×" e legenda.
- **Bom para os slides?** sim (um gráfico pode contradizer a tabela ao lado sem nenhum teste falhar)

## 2026-10-22 — Vagas "fora da Classe 1" contavam as indeterminadas, e o mercado futuro usava o passivo de todas as vagas
- **Onde:** notebook 02, §3 e achado 4 (parte A da mineração).
- **O que aconteceu:** o texto dizia "24% das vagas não são Classe 1" e "≈ R$ 50 milhões de passivo" como mercado futuro. A conta `classe != "1"` incluía as 48 vagas de classe indeterminada; o certo é `classe in ("2", "3")`: 150 vagas (18,1%). E os R$ 50 mi eram o passivo de **todas** as vagas, inclusive as de Classe 1, que nunca entrariam no universo; o das vagas de Classe 2 ou 3 é R$ 35,4 mi.
- **Como foi detectado:** revisão de cientista de dados, recalculando direto no banco.
- **Causa provável:** a negação ("não é Classe 1") tratou "indeterminada" como "acima do limite", e o número do mercado futuro foi tirado da tabela por situação sem filtrar a classe.
- **Correção:** filtro por `classe in ("2", "3")`, com a contagem das indeterminadas à parte; texto e resumo refeitos.
- **Bom para os slides?** sim (um "não é X" num campo com três valores esconde o terceiro)

## 2026-10-22 — Checagem circular de "serventia sem município"
- **Onde:** notebook 01, §5; `src/analise/dados.py`, `serventias()`.
- **O que aconteceu:** a checagem procurava serventias sem município na tabela `sv`, mas `serventias()` fazia INNER JOIN com `silver.municipio_ibge`: uma serventia sem município seria descartada antes da checagem, que daria sempre 0. O resultado estava certo por outro caminho (2.525 em `sv` = 2.525 ativas no cadastro), mas o teste não testava nada.
- **Como foi detectado:** revisão de cientista de dados.
- **Causa provável:** a checagem foi escrita sobre a tabela pronta, sem olhar como ela é montada.
- **Correção:** LEFT JOIN em `serventias()`; a checagem passou a ler o `silver.serventia`; teste sintético novo (`test_serventias_mantem_quem_nao_tem_municipio`).
- **Bom para os slides?** sim (uma checagem que não pode falhar não é uma checagem)

## 2026-10-22 — "418 municípios sem obrigadas" contava pelo passivo, não pelas obrigadas
- **Onde:** notebook 02, §5 (mapa) e achado 5.
- **O que aconteceu:** o mapa pinta de cinza os municípios com **passivo** das obrigadas igual a zero (418), e o texto os chamou de "sem nenhuma obrigada". Um município tem obrigada com passivo zero (zero CLT), e 2 não têm serventia: são 417 sem obrigada, o que bate com os 436 "com alguma obrigada" da §8 (853 − 436).
- **Como foi detectado:** revisão de cientista de dados (853 − 436 ≠ 418).
- **Causa provável:** o rótulo do gráfico descreveu a regra de cor com outra palavra.
- **Correção:** o mapa separa "sem obrigada" (cinza) de "obrigada sem passivo" (amarelo); o texto diz 417, com os 2 sem serventia.
- **Bom para os slides?** não

## 2026-10-23 — Plano do projeto com "143 municípios" no T6, e revisão que não pegou
- **Onde:** documentos (`docs/plano_projeto.md`, escrito com outra IA no navegador, e a revisão feita aqui).
- **O que aconteceu:** o plano dizia que o teste T6 usou 143 municípios com 20 ou mais vínculos; o `resultados.json` do script diz 135 (`n_municipios_teste`). Na primeira revisão do plano, a IA desta sessão afirmou que "todos os resultados do T1 ao T7 se reproduzem exatamente", conferindo as métricas, mas sem conferir os tamanhos de amostra.
- **Como foi detectado:** ao escrever `docs/qa/analises/testes_metodos.md` a partir dos campos do JSON.
- **Causa provável:** a revisão comparou só os números das tabelas impressas no terminal, e o tamanho da amostra do T6 só aparece no JSON.
- **Correção:** 135 nos dois lugares do plano; o documento dos testes tira todos os números do JSON.
- **Resultado depois da correção:** os tamanhos (2.444, 2.692, 2.406, 10.978, 887, 135) conferidos contra o JSON.
- **Bom para os slides?** sim (afirmar "tudo confere" sem conferir tudo)

## 2026-10-23 — D-039 acrescentada ao `decisoes.md` por comando do shell
- **Onde:** documentos (`docs/decisoes.md`).
- **O que aconteceu:** a D-039 foi acrescentada no fim do arquivo com `cat >> ... <<EOF`, e não com a ferramenta de edição, a mesma falha da entrada de 2026-10-22 ("Arquivo de teste gravado por comando do shell").
- **Como foi detectado:** a própria IA, logo depois, ao lembrar a regra do `CLAUDE.md`.
- **Causa provável:** pressa num acréscimo grande no fim de um arquivo longo.
- **Correção:** conferido que o texto entrou inteiro e sem mudar o resto do arquivo (`git diff docs/decisoes.md`: só linhas acrescentadas); os outros registros da sessão foram feitos com a ferramenta de edição.
- **Bom para os slides?** não

## 2026-10-23 — Ordem das regras de associação mudava a cada execução
- **Onde:** código (`src/analise/padroes.py`) e notebook 03, §4.
- **O que aconteceu:** as regras vinham na ordem do `mlxtend`, que depende da ordem dos itens em `frozenset` de textos; essa ordem muda a cada sessão do Python (hash aleatório). Com empate no lift (Notas→RCPN e RCPN→Notas), a tabela saía em ordem diferente a cada execução.
- **Como foi detectado:** na revisão, rodando os notebooks duas vezes do zero e comparando as saídas.
- **Causa provável:** confiar na ordem de saída de uma biblioteca e ordenar só pelo lift, sem desempate.
- **Correção:** ordenação completa e fixa (texto do "se", consequente, lift, suporte), teste novo e prova com `PYTHONHASHSEED` 1 e 2.
- **Resultado depois da correção:** saídas e PNGs idênticos nas duas rodadas.
- **Bom para os slides?** sim ("semente fixa" não basta para reprodutibilidade)

## 2026-10-23 — Texto dos notebooks escrito antes de ver os números
- **Onde:** notebooks 03, 04 e 05.
- **O que aconteceu:** parte das leituras foi escrita com os números da exploração, antes da execução final, e algumas não bateram: a subestimação do 05b atribuída às faixas altas (está nas baixas), "metade das janelas" (4 de 10), "dois terços do déficit" (59% no máximo), Varginha entre as 10 principais (11ª) e uma afirmação sem número ("as vagas não achadas são as grandes"). No gráfico da projeção, `"recal" in "sem recalibração"` deu rótulos errados.
- **Como foi detectado:** revisão, conferindo cada frase contra as saídas e cada gráfico aberto.
- **Causa provável:** escrever a interpretação junto com o código, sem uma passada final frase a frase contra a saída.
- **Correção:** frases corrigidas; as afirmações que dependiam de conta (sensibilidade do grupo-alvo, perfil das vagas não achadas) passaram a ser calculadas no notebook; rótulo pelo nome exato do modelo.
- **Bom para os slides?** não

## 2026-10-23 — Taxa de vacância "sem lote" tirava os lotes também do estoque
- **Onde:** código (`src/analise/vacancia.py`, primeira versão de `taxas_por_ano`), antes de entrar no notebook 05c.
- **O que aconteceu:** para tirar as vacâncias decididas em lote, a função filtrava o cadastro inteiro; com isso, as providas em lote (as ondas de concurso) saíam também do denominador, e o estoque caía de ≈ 2.000 para ≈ 500, inflando a taxa (2025: 42% em vez de 7,4%).
- **Como foi detectado:** a própria IA, ao comparar o estoque com e sem lote na exploração.
- **Causa provável:** usar um filtro de linhas onde a regra pedia tirar só do numerador.
- **Correção:** parâmetro `fora` em `taxa_vacancia` (sai das vacâncias, fica no estoque), com teste sintético.
- **Também na sessão:** de novo, números escritos no texto antes da execução final (983 × 1.008, 60% × 54%, 20% × 17,5%), corrigidos na conferência frase a frase; e um comando do shell (`cat >> ... <<EOF` vazio) rodado sobre `tests/test_analise_modelos.py` por engano: não acrescentou nada (conferido no `git diff`), e o teste foi escrito com a ferramenta de edição.
- **Bom para os slides?** não

## 2026-10-23 — Leituras dos notebooks 06 e 08 com números arredondados "de cabeça"
- **Onde:** notebooks 06 (§3 e §8) e 08 (§2 e §4), textos de leitura.
- **O que aconteceu:** seis frases tinham números que não vinham de uma saída impressa, mas de uma leitura do gráfico ou de uma conta de cabeça: mediana do resíduo "entre −0,6 e +0,1" (era −0,55 a +0,02), resíduos "de 40 a 65" (36 a 65), "316 serventias com zero CLT" (no recorte, 285), "três quartos do passivo" (72%), "quase metade da IS" (43%) e "4,5 vezes" (4,4).
- **Como foi detectado:** na revisão dos notebooks, recalculando cada número do texto na cópia do banco.
- **Causa provável:** as leituras foram escritas logo depois da primeira execução, a partir do que o gráfico "mostrava", sem imprimir o número.
- **Correção:** os seis números corrigidos; a conta das verbas que crescem com o tempo de casa entrou no texto, verba por verba.
- **Bom para os slides?** sim (número de texto também precisa de saída que o prove)

## 2026-10-23 — Rótulo "R$ … a R$ …" virou fórmula no gráfico
- **Onde:** notebook 08, gráficos do tornado e do Monte Carlo.
- **O que aconteceu:** o matplotlib trata o texto entre dois `$` como fórmula; "R$ 206,1 mil a R$ 736,2 mil" saiu como "R206,1milaR 736,2 mil" em itálico.
- **Como foi detectado:** conferência visual dos PNGs.
- **Causa provável:** os rótulos dos notebooks 01 e 02 tinham um só valor em reais por texto, e o problema não tinha aparecido.
- **Correção:** `\$` nos rótulos com dois valores; PNGs conferidos de novo.
- **Bom para os slides?** não

## 2026-10-27 — MASE do teste T2 com o divisor errado
- **Onde:** `scripts/testes_metodos.py`, T2 (sessão de 2026-10-23), e a tabela do T2 em `docs/qa/analises/testes_metodos.md`.
- **O que aconteceu:** o comentário dizia "MASE: erro do sazonal ingênuo no treino", mas o código usava `np.mean(np.abs(np.diff(x, 2)))`, que é a **segunda diferença** da série, não a diferença de 2 semestres (`x[t] − x[t−2]`). Todos os MASE do T2 ficaram ≈ 1,5 vez menores (tendência 0,52 em vez de 0,79; referência 1,30 em vez de 1,99).
- **Como foi detectado:** ao refazer o T2 no notebook 07, o MAPE e o viés bateram com o teste e o MASE não, sempre na mesma proporção.
- **Causa provável:** `np.diff(x, n)` foi lido como "diferença com defasagem n", mas o `n` é a ordem da diferença.
- **Correção:** `src/analise/previsao.py` usa `x[2:] − x[:-2]`; nota no `testes_metodos.md`. O script do T2 não foi alterado (fica como registro do teste). O MAPE, que decide, e a escolha do método não mudam.
- **Bom para os slides?** sim (nome de função que parece dizer uma coisa e faz outra)

## 2026-10-27 — Exemplo do notebook 07 com número que parecia real
- **Onde:** notebook 07, §5 (rascunho do texto), antes da execução final.
- **O que aconteceu:** o exemplo do desvio dizia "em 2024, MG cresceu 20%", mas o crescimento real de 2024 foi de 12,8%. Também, a leitura da tabela de desvios dizia "metade das serventias" para a faixa P10–P90, que cobre 8 em cada 10.
- **Como foi detectado:** na conferência dos números do texto contra as saídas, antes de parar.
- **Causa provável:** exemplo didático escrito com um ano real, sem conferir; P10–P90 confundido com o intervalo entre os quartis.
- **Correção:** o exemplo passou a ser hipotético ("num ano em que MG cresce 20%") e a leitura diz "8 em cada 10".
- **Bom para os slides?** não

## 2026-10-27 (achado em 2026-10-28) — Número de linhas da `gold.analise_previsao` errado no diário
- **Onde:** `docs/diario.md`, entrada de 2026-10-27 (notebook 07).
- **O que aconteceu:** o diário dizia "99 linhas: 19 da arrecadação e 80 do mercado"; a saída do notebook mostra 107 (19 + 88 = 11 medidas × 2 anos × 2 variantes × 2 cenários do limite).
- **Como foi detectado:** na revisão do 07, conferindo o texto do diário contra a saída da seção 7.
- **Causa provável:** a conta foi feita com 10 medidas, antes de a medida `classe_2_para_3` entrar, e não foi refeita.
- **Correção:** a linha do diário foi corrigida, com nota.
- **Bom para os slides?** não

## 2026-10-28 — Título de gráfico que dizia o contrário do dado
- **Onde:** notebook 09, achado 10 (rascunho), gráfico `09_clt_outros_estados`.
- **O que aconteceu:** o título dizia "o total sai com erro de até ±10% na maioria das regiões", mas 7 das 13 regiões passam de ±10%.
- **Como foi detectado:** na leitura das saídas da primeira execução, antes de escrever o texto.
- **Causa provável:** título escrito antes de ver o número, pela lembrança de "±10%" do T1 (que vale para o total do estado, não de cada região).
- **Correção:** o título passou a ser calculado ("passa de ±10% em 7 de 13 regiões") e o texto separa o erro por região do erro do estado (−2,5%).
- **Bom para os slides?** sim (escrever o título só depois de ver o número)

## 2026-10-28 — Floresta com resultado diferente a cada execução (15ª casa)
- **Onde:** `src/analise/regressao.py`, `prever_floresta` (notebooks 06 e 09; `gold.analise_clt_modelo`).
- **O que aconteceu:** a mesma previsão, feita duas vezes, diferia em até 1,4e-14 em 45% das serventias. Na tela não aparece, mas o hash de conteúdo da tabela mudaria a cada carga, e a prova "recalcular dá o mesmo" falharia.
- **Como foi detectado:** ao comparar a tabela do módulo novo (`tabelas.py`) com a desenhada no notebook 06: 5 das 6 tabelas iguais e esta diferente.
- **Causa provável:** com `n_jobs=-1`, o scikit-learn soma as árvores em paralelo, em ordem variável, e a soma em ponto flutuante depende da ordem.
- **Correção:** ajuste em paralelo e previsão sequencial (`set_params(n_jobs=None)`); teste `test_floresta_preve_igual_duas_vezes`. O notebook 06 rodado de novo deu as mesmas saídas e PNGs.
- **Bom para os slides?** sim (reprodutível na tela não é o mesmo que reprodutível no hash)

## 2026-10-28 — Primeira carga da Etapa 2 parada por tipo misto na `analise_tornado`
- **Onde:** `pipeline.etapa_analise`, ao gravar a `gold.analise_tornado` (numa cópia).
- **O que aconteceu:** as colunas `valor_min/base/max` misturavam número e verdadeiro/falso (premissas sim/não), e o DuckDB recusou a tabela. A carga atômica funcionou: nenhum banco foi trocado e `data/` ficou intacto.
- **Como foi detectado:** na primeira execução do pipeline do zero.
- **Causa provável:** a conferência com os notebooks usou Parquet, e o pyarrow converte a mistura em número sem avisar; o DuckDB não converte.
- **Correção:** `sensibilidade.tabela_tornado` grava as três colunas como número (sim = 1, não = 0); teste `test_tabela_tornado_grava_no_duckdb_com_premissa_sim_nao`. Lição: conferir gravando no mesmo destino do pipeline, não num formato intermediário.
- **Bom para os slides?** sim

## 2026-10-28 — Documento editado por script de substituição
- **Onde:** `docs/plano_mineracao.md` (6 marcas de status do 09 e das partes B e C).
- **O que aconteceu:** as trocas foram feitas com um script Python de substituição de texto (com conferência de que cada trecho aparecia uma vez só), e não com a ferramenta de edição. O `CLAUDE.md` proíbe isso para código; para documento não é proibido, mas o motivo da regra (trocar o trecho errado sem ver) é o mesmo.
- **Como foi detectado:** pela própria IA, logo depois; o `git diff` do arquivo foi conferido e só tem as 6 trocas pretendidas.
- **Correção:** os outros documentos da sessão (`plano_projeto.md`, `ESTADO_ATUAL.md`, `dicionario_dados.md`, `SPEC.md`) foram editados com a ferramenta de edição.
- **Bom para os slides?** não

## 2026-10-28 — Tabela nova do pipeline dependia de um arquivo opcional do bronze
- **Onde:** `src/analise/tabelas.py`, `sensibilidade_metodo` (`gold.analise_sensibilidade_metodo`, D-044).
- **O que aconteceu:** a linha da receita líquida lê o CSV do BI do CNJ no bronze, que é opcional (README) e não vai no pacote público. Com isso, o `pipeline.py --a-partir-de silver` passou a falhar onde não há bronze, contra a D-029 ("gold a partir do silver, sem bronze"). No banco oficial não houve efeito, porque o CSV existe: a tabela gravada está certa.
- **Como foi detectado:** `tests/test_saida_utf8.py::test_pipeline_com_saida_redirecionada` (`dados_reais`), que roda o pipeline numa cópia do projeto sem o bronze. Ele só rodou depois da carga oficial: antes, a IA tinha rodado os `dados_reais` de 3 arquivos, e não de todos.
- **Causa provável:** a função copiou o cálculo do notebook 08, que roda com o bronze, sem conferir de onde vinha cada entrada.
- **Correção:** sem o CSV, a linha sai com um aviso, e o resto da tabela é gravado. Com o CSV, o resultado é idêntico ao do banco oficial (mesmo hash). Teste novo: `test_sensibilidade_metodo_sem_o_bi_nao_para`. Lição: antes de uma carga oficial, rodar **todos** os testes `dados_reais`, não só os do código mudado.
- **Bom para os slides?** sim

## 2026-10-28 — Código acrescentado por comando de terminal
- **Onde:** `src/analise/melhorias.py` (funções da M3, M4 e M5) e `config/analise.yaml` (seção `melhorias`).
- **O que aconteceu:** a IA acrescentou o código ao fim dos arquivos com `cat >> arquivo <<EOF` no terminal, e não com a ferramenta de edição, contra a regra do `CLAUDE.md`.
- **Como foi detectado:** pela própria IA, logo depois do comando.
- **Causa provável:** pressa num trabalho longo; o atalho do terminal pareceu equivalente para "acrescentar no fim".
- **Correção:** o conteúdo foi conferido (ruff sem erro; testes `tests/test_analise_melhorias.py`). As edições seguintes de código e de config usaram só a ferramenta de edição.
- **Bom para os slides?** não

## 2026-10-28 — Premissa nova com casas decimais e o simulador que arredonda
- **Onde:** `app/pages/2_Simulador.py` (controles da chance de déficit e da parte descoberta), depois das premissas v3 (D-046).
- **O que aconteceu:** as premissas v3 têm valores como 10,8% e 90,7%. O simulador mostrava esses controles em porcentagem inteira, com passo de 5, e começava em 11% e 91%: o simulador padrão deixou de repetir a base do painel (≈ 151 com déficit, contra ≈ 148).
- **Como foi detectado:** `tests/test_app_demo.py::test_simulador_padrao_igual_ao_cenario_base_do_painel`, depois da carga oficial.
- **Causa provável:** a IA trocou os valores da semente sem procurar onde eles são mostrados ou arredondados; as premissas da v1 e da v2 eram todas redondas.
- **Correção:** esses quatro controles passaram a ter uma casa decimal e a começar no valor exato da semente; a dica mostra a fonte certa (BI do CNJ, e não "suposição"). Teste passando. O banco não precisou ser refeito (o erro era só da tela). O mesmo descuido apareceu em 4 testes `dados_reais` que fixavam números da v2 (Monte Carlo, receita líquida, tornado do T7, linhas da sensibilidade): atualizados, com a v2 mantida só onde o teste confere o método do T7.
- **Bom para os slides?** sim

## 2026-10-28 — Teste de LGPD esquecido na D-048
- **Onde:** `tests/test_app.py::test_lgpd_tabelas_publicas_do_gold_e_da_qualidade`, depois da tabela `gold.serventia_publico` (D-048).
- **O que aconteceu:** a tabela nova mostra o município de cada cartório, como a D-038 permite. O teste ainda cobrava a regra antiga (nenhum município com menos de 3 serventias em tabela pública) e falhou com 532 municípios.
- **Como foi detectado:** rodada dos testes `dados_reais`, depois da carga oficial.
- **Causa provável:** a IA ajustou as travas do `publico.py` e o `test_publico.py`, mas não procurou outros testes que conferem a mesma regra.
- **Correção:** a `serventia_publico` entrou na lista `EXCECOES_LGPD` do teste, com o motivo (D-038, D-048). O teste passou. Banco e `data/publico/` não mudaram. O teste some ou muda de vez na fase 2 da D-038 (Etapa 3).
- **Bom para os slides?** não

## 2026-10-28 — Código corrigido por script de substituição (de novo)
- **Onde:** `src/painel/analises.py` (Etapa 3), três correções pequenas (porte sem CLT declarado, o texto do "topo" e o rótulo da leitura literal) e `docs/painel/inventario_achados.md` (coluna "Revisão", com `sed`).
- **O que aconteceu:** a IA aplicou as três correções no módulo novo com um script Python de substituição de texto, e não com a ferramenta de edição, contra a regra do `CLAUDE.md`; é a mesma falha da entrada anterior de 28/10.
- **Como foi detectado:** pela própria IA, logo depois do comando.
- **Causa provável:** pressa, de novo, numa tarefa longa; o script parecia mais rápido para três trocas no mesmo arquivo.
- **Correção:** o resultado foi conferido (as funções rodaram e repetem os números do notebook 09; `tests/test_painel.py`). Todas as edições seguintes de código (páginas, testes, scripts) foram feitas com a ferramenta de edição.
- **Bom para os slides?** não

## 2026-10-28 — Template do Plotly trocado pelo Streamlit
- **Onde:** `src/painel/graficos.py` (Etapa 3).
- **O que aconteceu:** os gráficos novos saíram com fundo cinza e títulos cortados nas primeiras capturas, apesar do template próprio registrado como padrão.
- **Como foi detectado:** revisão visual das capturas de prévia em 1366 px.
- **Causa provável:** o Streamlit registra o template dele como padrão do Plotly quando é importado, depois do módulo de gráficos; além disso, `st.plotly_chart` aplica o tema do Streamlit por cima se `theme` não for `None`.
- **Correção:** cada figura recebe `template="radar"` e as cores de fundo explicitamente, e é exibida por `ui.grafico` com `theme=None`. Também o eixo dos semestres ("2026-1") era lido como data: passou a categoria.
- **Bom para os slides?** sim

## 2026-10-28 — Pergunta ao usuário com as colunas da D-031 trocadas
- **Onde:** pergunta de múltipla escolha sobre versionar os dados do painel (D-050).
- **O que aconteceu:** a pergunta dizia que a D-031 tira do silver público "remuneração e tempo de emprego" da RAIS. É o contrário: essas colunas ficam (o pipeline usa); saem `ano_base`, `tipo_estabelecimento`, `horas_contratadas`, `mes_admissao`, `mes_desligamento` e `cbo`.
- **Como foi detectado:** leitura do `config/publico.yaml` logo depois da resposta.
- **Causa provável:** resumo feito antes de ler a lista da D-031 por inteiro.
- **Correção:** avisado na resposta final; a escolha do usuário não muda (o silver versionado segue a lista da D-031 do `config/publico.yaml`).
- **Bom para os slides?** não

## 2026-10-28 — Teste de cobertura do chat não via a página Análises (nome com acento)
- **Onde:** código gerado (`tests/test_chat_cobertura.py`, com o `arquivos_versionaveis` de `tests/apoio_painel.py`)
- **O que aconteceu:** o teste que confere se o chat alcança toda análise do painel achou 14 análises nas páginas, e não 21: a página `app/pages/2_Análises.py` ficava de fora. O `git ls-files` põe entre aspas, com escapes octais, os nomes com acento (`"app/pages/2_An\303\241lises.py"`), e o caminho não existia. Um teste de cobertura que pula uma página passaria mesmo com o chat sem as análises dela.
- **Como foi detectado:** a trava do próprio teste ("pelo menos 15 análises nas páginas"), escrita antes de rodar.
- **Causa provável:** confiar que o `git ls-files` devolve os caminhos como estão no disco.
- **Correção:** o teste de cobertura varre `app/` direto; o `arquivos_versionaveis` passou a usar `git ls-files -z`, que não põe aspas (hoje só lê `.md` e `.ipynb` sem acento, então nenhum outro teste tinha sido afetado).
- **Resultado depois da correção:** 21 análises achadas, todas alcançadas pelo chat.
- **Bom para os slides?** sim (um teste de cobertura também precisa provar que está vendo tudo)

## 2026-10-28 — Critério do gabarito aceitava qualquer "não" como certo
- **Onde:** eval (`eval/gabarito_chat.csv`, pergunta 43, "A ADI 8015 já tem liminar?")
- **O que aconteceu:** a primeira versão do critério era `nao|sem liminar`. Como a correção procura o texto em qualquer lugar da resposta, qualquer resposta com a palavra "não" (até "não sei") contaria como acerto.
- **Como foi detectado:** revisão do gabarito pela IA antes de congelar o hash.
- **Causa provável:** critério de texto curto demais.
- **Correção:** alternativas específicas (`sem liminar|nao tem liminar|nao ha liminar|nenhuma liminar|...`), antes do congelamento e de qualquer rodada com o modelo.
- **Bom para os slides?** não

## 2026-10-28 — Trava da Etapa 3 sobre as ferramentas do chat quebrada pela troca de nome
- **Onde:** código gerado (`src/agent/ferramentas.py`, D-062), com o teste `tests/test_painel.py::test_ferramentas_do_chat_nao_mudaram`
- **O que aconteceu:** o nome `FERRAMENTAS` passou a ser a lista das 5 ferramentas novas, e as 6 consultas antigas foram para `PROPRIAS`. O teste da Etapa 3, que conferia as 6 em `FERRAMENTAS`, falhou. Os testes do chat tinham sido rodados sozinhos, sem a suíte inteira.
- **Como foi detectado:** a suíte inteira, rodada antes de parar.
- **Causa provável:** reaproveitar um nome público de um módulo sem procurar quem o usa (`grep FERRAMENTAS tests/`).
- **Correção:** o teste confere as 6 em `PROPRIAS` e que elas continuam alcançáveis pelas 5 ferramentas; o ajuste foi registrado, porque o arquivo é da Etapa 3.
- **Resultado depois da correção:** 286 passed, 2 skipped.
- **Bom para os slides?** não

## 2026-10-28 — Chave do Gemini exposta na saída de um comando de diagnóstico
- **Onde:** diagnóstico do chat (comando de terminal da IA)
- **O que aconteceu:** para testar a API com o `curl`, a IA carregou o `.env` no shell (`set -a; . ./.env`). A linha da chave tinha um espaço depois do `=` (inofensivo para o `python-dotenv`), e o shell tentou executar o valor como comando. A mensagem de erro, "command not found", trouxe a chave inteira na saída do comando, dentro da conversa com a IA. A chave não foi para o git, nem para nenhum arquivo do projeto, nem para a resposta do chat.
- **Como foi detectado:** a própria IA viu a mensagem de erro.
- **Causa provável:** carregar um arquivo de segredo no shell em vez de ler a chave pelo código do projeto, que nunca a imprime.
- **Correção:**
  - o diagnóstico seguiu só pelo Python (`llm.chave()`), com a saída filtrada;
  - a IA avisou para **revogar a chave e criar outra** no AI Studio;
  - regra para os próximos diagnósticos: nunca fazer `source`, `cat` ou `echo` do `.env`; para ver o formato do arquivo, mostrar só os nomes das variáveis e o tamanho dos valores.
- **Bom para os slides?** sim (segredo vaza pelo caminho de erro, não pelo caminho feliz)

## 2026-10-28 — A reserva do chat não cobria a demora do modelo principal
- **Onde:** código gerado (`src/llm.py`)
- **O que aconteceu:** a reserva só entrava em cota esgotada ou erro HTTP. Quando o `gemini-3.8-flash` travou, cada pergunta esperava 60 s e terminava em "sem internet (ReadTimeout)", com a reserva funcionando.
- **Como foi detectado:** uso real, no painel.
- **Causa provável:** o desenho tratou só os erros que o servidor responde, não a ausência de resposta; e os testes simulavam 429 e 400, não demora.
- **Correção:** D-068, com o teste `test_llm_principal_lento_vai_para_a_reserva`.
- **Resultado depois da correção:** respostas em 4 a 24 s, em vez de erro depois de 60 s.
- **Bom para os slides?** sim

## 2026-10-29 — "Mágica" do Streamlit mostrou um objeto interno em cada pergunta
- **Onde:** código gerado (`app/pages/5_Chat.py`)
- **O que aconteceu:** a linha `_mostrar(m) if ... else st.markdown(...)` é uma expressão solta. O Streamlit exibe o valor de expressões soltas ("mágica"), e cada pergunta do histórico ganhou a documentação inteira de um `DeltaGenerator` na tela.
- **Como foi detectado:** captura da conversa com 3 perguntas (`scripts/prints_chat.py`). O AppTest não pegou.
- **Correção:** `if`/`else` comuns, com um comentário no código.
- **Bom para os slides?** sim (o teste automático passava; só a captura mostrou)

## 2026-10-29 — Pergunta nova no meio do streaming apagava a anterior
- **Onde:** código gerado (`app/pages/5_Chat.py`)
- **O que aconteceu:** a pergunta e a resposta só entravam no histórico no fim do streaming. Uma pergunta nova antes disso interrompe a execução do Streamlit, e o par anterior sumia da conversa.
- **Como foi detectado:** o script de capturas mandou a segunda pergunta cedo demais e a conversa ficou com 2 mensagens, não 4.
- **Correção:** a pergunta entra no histórico logo no início e a resposta, mesmo parcial, no `finally`.
- **Bom para os slides?** não

## 2026-10-29 — Conclusões de velocidade tiradas de uma amostra só, e streaming em todas as chamadas
- **Onde:** decisões de velocidade (D-069)
- **O que aconteceu:**
  - **raciocínio:** com uma chamada de cada nível, a IA escolheu `minimal` na reserva (1,5 s contra 2,5 s). Medido com 5 perguntas, ele foi pior: mediana de 7,4 s contra 2,3 s com `low`;
  - **streaming:** a IA ligou o streaming em todas as chamadas, e a chamada que só pede a ferramenta ficou 4 vezes mais lenta (3,4 s contra 0,8 s);
  - **medição:** o script de latência não registrava as chamadas que estouravam o tempo-limite, e 30 s de espera ficaram fora da tabela.
- **Como foi detectado:** medições repetidas e alternadas (A/B), e a soma das etapas que não batia com o total.
- **Correção:** `low` nos dois modelos; streaming só nas chamadas que escrevem a resposta; o script registra também as falhas.
- **Bom para os slides?** sim (medir de novo antes de decidir)

## 2026-10-29 — O modelo chamava os extremos teóricos de "faixa provável"
- **Onde:** chat (saída das ferramentas para o modelo)
- **O que aconteceu:** perguntado sobre o prêmio, o modelo respondeu "faixa provável (P5–P95) de R$ 51,7 mil a R$ 1,9 mi". Esses são os extremos teóricos; a faixa provável é de R$ 215 mil a R$ 687 mil. As consultas devolviam os extremos como "faixa" ou como "mínimo" e "máximo".
- **Como foi detectado:** leitura das capturas da conversa.
- **Correção:**
  - a consulta de mercado traz a faixa provável da mesma função do painel, com os extremos num campo à parte;
  - no que vai para o modelo, "minimo" e "maximo" viraram "extremo_teorico_minimo" e "extremo_teorico_maximo";
  - teste novo. Os números não mudaram.
- **Resultado depois da correção:** prêmio e déficit respondidos com a faixa certa no teste real.
- **Bom para os slides?** sim (o número estava certo, e o rótulo errado mudava o sentido)

## 2026-10-29 — Erro de direção: o painel mostrava tudo em vez de responder à pergunta
- **Onde:** painel da Etapa 3, segunda rodada (D-049): todas as páginas
- **O que aconteceu:** o plano pedia "um painel que reúna todos os achados importantes", e a IA seguiu ao pé da letra: inventário de 34 achados, cada um com lugar no painel. O Início ficou com 13 cartões, a ADI, o glossário e a escada; os 3 cartões D-042 se repetiam na Análises; a Análises tinha 4 abas e 8 gráficos. Nada respondia, em 5 segundos, à pergunta do projeto ("quanto dinheiro, e quão certo"), que estava escrita no próprio plano.
- **Como foi detectado:** revisão do autor ("o painel tem informação demais e, por isso, não informa nada").
- **Correção:** D-051. O painel responde a uma pergunta; cada elemento passou pela regra de corte (`docs/painel/corte.md`: de 71, ficaram 17 e 8 foram para "Sobre os dados"); o detalhe foi para o chat. Limites por página testados.
- **Lição:** antes de inventariar o que mostrar, escrever a pergunta que a tela responde e cortar o que não a responde.
- **Bom para os slides?** sim (antes × depois em `docs/qa/painel/rodada3_antes/` e `rodada3_depois/`)

## 2026-10-29 — Script de substituição de texto para editar código
- **Onde:** `app/comum.py` (função `pagina` e a nova `fonte_linha`)
- **O que aconteceu:** a IA trocou o fim do arquivo com um script Python (`read_text`/`write_text`), contra a regra do `CLAUDE.md` ("edite código só com a ferramenta de edição de arquivos").
- **Como foi detectado:** a própria IA, logo depois.
- **Correção:** o resultado foi conferido (o trecho substituído era só a função `pagina`, no fim do arquivo); o resto da sessão usou só a ferramenta de edição.
- **Bom para os slides?** não

## 2026-10-29 — Capturas "antes" tiradas enquanto as páginas mudavam
- **Onde:** `docs/qa/painel/rodada3_antes/`
- **O que aconteceu:** a IA rodou o script de capturas em segundo plano e, ao mesmo tempo, começou a reescrever as páginas. O Streamlit lê os arquivos a cada execução: parte das capturas "antes" já pegava código novo, e o script quebrou no meio (o filtro "Filtrar por" não existia mais).
- **Como foi detectado:** o script terminou com erro.
- **Correção:** as capturas "antes" foram refeitas a partir de uma cópia exata do último commit (`git archive HEAD`, numa pasta temporária, com uma cópia do banco).
- **Bom para os slides?** não

## 2026-10-29 — Contagem do corte escrita antes de contar
- **Onde:** `docs/painel/corte.md` e D-051
- **O que aconteceu:** a IA escreveu "81 elementos: 20 ficam, 7 Sobre, 38 chat, 16 saem" antes de contar as linhas da tabela; a contagem real dava 71 (17, 8, 31, 15).
- **Como foi detectado:** a IA contou as linhas com um script antes de fechar.
- **Correção:** números corrigidos nos dois documentos, com a regra de contagem escrita.
- **Bom para os slides?** não

## 2026-10-29 — CSS do visual novo quebrou o painel em quatro pontos antes da conferência no navegador
- **Onde:** `src/painel/estilo.css` e `src/painel/graficos.py` (D-052).
- **O que aconteceu:** (1) a frase de conclusão virou colunas soltas, porque o quadro usava `display: flex` e cada trecho em negrito virou um item; (2) o subtítulo dos gráficos continuou em serifa, porque o Plotly ignora `font-family` dentro do título; (3) o rótulo do topo e o título do Chat ficaram escondidos sob a barra do Streamlit; (4) o primeiro título de "Sobre os dados" subiu sobre a faixa azul-marinho, ilegível.
- **Como foi detectado:** capturas de cada página no navegador (1366 px e 375 px), antes de entregar.
- **Causa provável:** o CSS foi escrito pelo HTML do artefato (página estática), sem levar em conta os contêineres do Streamlit e o que o Plotly aceita no título.
- **Correção:** quadro com o sinal em posição absoluta (sem flex); subtítulo no campo `title.subtitle` do Plotly; respiro de 72 px no topo e barra da cor certa por página; a regra de "subir sobre a faixa" não vale para títulos de seção.
- **Bom para os slides?** sim (mostra por que a conferência visual faz parte da entrega)

## 2026-10-29 — Faixa do topo com pseudo-elemento largo escondeu a navegação do painel
- **Onde:** `src/painel/estilo.css` (D-052, segunda passada).
- **O que aconteceu:** para pintar o degradê da faixa até as bordas, um `::before` com `left/right: -100vmax`; o contêiner principal do Streamlit (`overflow: hidden`) passou a ter conteúdo além da largura e rolou para o lado, tirando a navegação da tela.
- **Como foi detectado:** captura no navegador sem a barra lateral; medição no DOM mostrou o `stMain` com `overflow-x: hidden` e a faixa deslocada.
- **Causa provável:** técnica de página estática aplicada a um contêiner com rolagem própria.
- **Correção:** o degradê vai num `border-image` com recuo lateral (`fill 0 / 0 / 0 100vmax`), que pinta fora da caixa sem criar rolagem.
- **Bom para os slides?** não

## 2026-10-29 — "Igual ao Raio-X" feito só no tema claro, e sem avisar que o painel aberto precisava reiniciar
- **Onde:** D-052, primeira e segunda passadas (`src/painel/estilo.css`, `.streamlit/config.toml`).
- **O que aconteceu:** o Raio-X tem tema claro e escuro e segue o sistema; a IA copiou só os tokens claros. O autor usa o sistema no escuro e via o Raio-X escuro; além disso, o painel dele estava aberto desde antes das mudanças. Resultado: "nada mudou".
- **Como foi detectado:** capturas do autor com o fundo `#0c1018` e o terminal dele mostrando o Streamlit iniciado às 21:48.
- **Causa provável:** a leitura do código do artefato parou no bloco `:root` e ignorou o `@media (prefers-color-scheme: dark)`; a conferência foi feita só no navegador da IA, em modo claro.
- **Correção:** os dois temas com os tokens do artefato, escolha pelo tema do Streamlit ou do sistema, gráficos e mapa trocando de cor; conferência nos dois esquemas; aviso explícito para reiniciar o painel.
- **Bom para os slides?** sim (o pedido era claro; faltou conferir no ambiente de quem pediu)
