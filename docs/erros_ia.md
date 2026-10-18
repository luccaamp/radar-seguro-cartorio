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
