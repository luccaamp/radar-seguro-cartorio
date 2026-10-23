# Entenda o projeto (comece por aqui)

> Para quem nunca ouviu falar de seguro-garantia nem do Provimento CNJ 227 e quer entender o projeto em 10 minutos. Linguagem simples; os termos difíceis estão no **glossário** no fim. A versão técnica completa está no [`SPEC.md`](SPEC.md).
> Números da carga 2026-10-19 (a tabela oficial fica no [`ESTADO_ATUAL.md`](ESTADO_ATUAL.md)); situação do STF conferida em 17/10/2026.

## Em uma frase

O projeto responde: **"Quanto dinheiro o novo seguro obrigatório dos cartórios pode movimentar em Minas Gerais, e quão certo é esse número?"**

---

## 1. O problema: o que a regra do CNJ manda e por quê

### Quem é quem no cartório
- O cartório é tocado por **uma pessoa**, o **titular** (no texto da lei: *delegatário*). Ele passou num concurso público e recebeu do Estado o direito de prestar o serviço.
- Os funcionários (*prepostos*) são **contratados pelo titular, como pessoa física**, pela CLT (carteira assinada).

### O risco
Se o titular sai, morre ou não tem dinheiro, quem paga os direitos dos funcionários na demissão (aviso prévio, férias, multa do FGTS...)? Se ninguém pagar, os funcionários ficam sem receber e o serviço do cartório pode parar. A norma fala em "risco à continuidade do serviço público" (art. 13, § 1º).

### A regra (Provimento CNJ 227/2026, em vigor desde 10/08/2026)
Todo ano, o titular faz quatro coisas:

1. **Calcula a "dívida trabalhista"** (*passivo*): quanto custaria **demitir hoje todos os funcionários sem justa causa**. A data de referência é 31 de dezembro, e a entrega vai até 31 de março.
2. **Mostra que tem bens** suficientes para pagar essa dívida. Só contam bens que poderiam ser tomados pela Justiça: a casa onde a família mora não conta.
3. **Se os bens não bastam**, a diferença é o **déficit**. O titular tem 60 dias para resolver de um destes jeitos:
   - conseguir mais bens;
   - apresentar uma **fiança bancária** de um banco grande;
   - contratar um **seguro-garantia**. **É esse o mercado que o projeto estima.**
4. **A garantia** (fiança ou seguro):
   - cobre **100% do déficit**;
   - dura **pelo menos 1 ano** e precisa ser **renovada** (com prova 30 dias antes de vencer);
   - tem o valor atualizado todo ano.

Por isso o seguro é uma **receita que se repete todo ano**, não uma venda única.

### Quem não precisa cumprir (art. 19)
- **Cartórios pequenos (Classe 1):** receita de até **R$ 300 mil por semestre** (antes de 22/08/2026, o limite era R$ 100 mil). As classes vêm de outra norma do CNJ, o Provimento 213, alterado pelo 243:

  | Classe | Receita por semestre | Precisa cumprir? |
  |---|---|---|
  | 1 | até R$ 300 mil | **Não** |
  | 2 | até R$ 1,5 milhão | Sim |
  | 3 | acima de R$ 1,5 milhão | Sim |

- **Cartórios sem titular** (com um **interino** cuidando temporariamente).

### O risco jurídico
A associação dos cartórios (ANOREG) entrou no STF (**ADI 8015**) pedindo para derrubar justamente a parte dos bens e da garantia (arts. 8º a 17). Em 17/10/2026 **não havia liminar**: a regra está valendo. O projeto tem um cenário para o caso de o STF derrubar: nele, o mercado de seguro vai a zero.

---

## 2. O básico de seguro-garantia

### Não é como o seguro do carro
No seguro do carro, você paga e você é protegido. No **seguro-garantia** são **três partes**, e quem paga **não** é quem fica protegido:

| Papel | O que faz | No caso do cartório |
|---|---|---|
| **Tomador** | tem a obrigação e **paga** o seguro | o titular do cartório |
| **Segurado** | **recebe** se a obrigação não for cumprida | **a norma não diz quem é** (ver abaixo) |
| **Seguradora** | **garante**: paga o segurado se der problema | uma seguradora autorizada pela SUSEP |

### O ponto que mais confunde
Se a seguradora precisar pagar, ela **cobra de volta do tomador**. O seguro-garantia funciona como um "fiador profissional": protege quem está do outro lado, não quem contratou. Por isso é barato: no projeto, o preço vai de **1% a 3,5% do valor garantido por ano** (2% no cenário base).

### Exemplo (ilustrativo, não é um cartório real)

| | Valor |
|---|---|
| Dívida trabalhista do cartório | R$ 500 mil |
| Bens que contam | R$ 300 mil |
| **Déficit = valor do seguro** | **R$ 200 mil** |
| Preço anual do seguro (2%) | **R$ 4 mil por ano** |

### O que a SUSEP tem a ver
A **SUSEP** é o órgão do governo que fiscaliza as seguradoras. Elas informam à SUSEP quanto venderam e quanto pagaram de prejuízo, e a SUSEP publica esses números (base **SES**) separados por **ramo** (tipo de seguro). O seguro-garantia tem dois ramos ativos:

| Ramo | Quem é protegido | De cada R$ 100 recebidos, quanto vira prejuízo (set/2025–ago/2026) |
|---|---|---|
| **0775 Setor Público** | um órgão público | ~R$ 14 |
| **0776 Setor Privado** | uma empresa ou pessoa | ~R$ 59 |

Como a norma **não diz quem é o segurado**, não se sabe em qual ramo o seguro dos cartórios cairia. O projeto usa o 0775 como base, porque a regra fala em proteger o serviço público, e o 0776 como cenário pessimista.

**As classes (1, 2, 3) não são da SUSEP.** Elas são do CNJ. A SUSEP só entra nos números do mercado de seguro.

---

## 3. As perguntas que o projeto responde

As perguntas formam uma escada: cada resposta alimenta a próxima.

| # | Pergunta | Como responde | Dado real ou suposição? | Resposta em MG (base) |
|---|---|---|---|---|
| 1 | Quantos cartórios existem? | Conta os ativos | **Real** (CNJ) | 2.525 |
| 2 | Quantos funcionários CLT eles têm? | Soma o que cada cartório declara | **Real** (CNJ) | 12.134 |
| 3 | Quantos precisam cumprir a regra? | Tira a Classe 1 (pela receita de 2025) e os sem titular | **Real**, mas a classe é **aproximada**: a receita publicada não é exatamente a que a norma usa | ≈ 1.121 |
| 4 | Qual é a dívida trabalhista? | Para cada funcionário: aviso prévio, férias, 13º, multa do FGTS e impostos, como manda a norma | **Real** (salários e tempo de casa da RAIS 2025) + **regras de lei**; o salário vem da média do município, não do cartório | R$ 311,9 mi (todos); R$ 238,1 mi (só os que precisam cumprir) |
| 5 | Quantos não têm bens suficientes? | Chance de ter déficit, por classe | **Suposição**: o patrimônio do titular não é público | ≈ 486 |
| 6 | Quanto falta, somando todos? | Parte da dívida sem bens, por classe | **Suposição** | R$ 36,9 mi |
| 7 | Quanto disso vira seguro? | Divide o déficit entre bens, fiança e seguro | **Suposição** | R$ 18,4 mi garantidos |
| 8 | Quanto as seguradoras receberiam por ano? | Valor garantido × preço (2%) | **Suposição** (a SUSEP não publica o preço) | R$ 368,7 mil |
| 9 | Isso dá lucro? | Receita − prejuízos − comissão − custos | **Real** (SUSEP, 2020–2026) para prejuízo e comissão; **suposição** para os custos | no Simulador |
| 10 | E se o STF derrubar a regra? | Três cenários: mantém, derruba, meio-termo | Cenários; o meio-termo é **suposição** | se derrubar, o mercado vai a zero |
| — | Qual o máximo possível? (**teto teórico**) | Toda a dívida × 2%, como se ninguém tivesse bens | Não depende das suposições 5 a 7 | R$ 4,76 mi por ano |

**Como ler:** as perguntas 1 a 4 se apoiam em **dados públicos reais**. Da 5 em diante entram **suposições**, porque ninguém publica o patrimônio do titular nem o preço que as seguradoras cobram. Por isso esses números vêm sempre com **mínimo, base e máximo**, e o **Simulador** deixa você mudar cada suposição e ver o efeito. Toda suposição fica escrita em [`config/premissas/`](../config/premissas/), com a marca `fonte: suposição`.

### Que anos de dados são usados
- **A conta principal usa 2025** (receita, salários, data da dívida em 31/12/2025), porque é o que a norma manda olhar. Misturar anos aqui deixaria a conta errada.
- **O risco do seguro usa vários anos** da SUSEP (2020 a 2026), porque o prejuízo das seguradoras muda muito de um ano para outro.
- **Os anos antigos dos cartórios** (desde 2007) servem para conferir se 2025 parece normal, completar buracos e prever o futuro.

### As peças do projeto
| Peça | O que é |
|---|---|
| **Pipeline** | a "fábrica": baixa os dados oficiais, limpa e faz as contas |
| **Painel** | site local que mostra os números, com mapa, filtros e a fonte de cada número |
| **Simulador** | página do painel onde você muda as suposições e vê o mercado mudar |
| **Chat** | responde perguntas sobre os números, com a conta e a fonte (roda no computador, de graça) |
| **Notebooks** | estudos dos dados: qualidade, padrões, grupos, previsões ([`plano_mineracao.md`](plano_mineracao.md)) |

---

## 4. Glossário

### Cartórios e a regra do CNJ
| Termo | O que quer dizer |
|---|---|
| **CNJ** | Conselho Nacional de Justiça. Fiscaliza os cartórios e escreve as regras para eles. |
| **Provimento** | Norma do CNJ. As três do projeto: **227** (a obrigação de garantia), **213** (as classes) e **243** (mudou os limites das classes). |
| **Corregedoria** | Parte do CNJ (nacional) ou do tribunal (estadual) que fiscaliza os cartórios. |
| **Serventia** | O nome oficial de um cartório. |
| **CNS** | Código Nacional de Serventia: o "CPF" do cartório. É como o projeto identifica cada um. |
| **Delegatário / titular** | A pessoa que passou no concurso e responde pelo cartório. |
| **Delegação** | O direito, dado pelo Estado, de prestar o serviço do cartório. |
| **Preposto** | Funcionário do cartório. |
| **Interino / interinidade** | Responsável temporário por um cartório sem titular (**vago**). Cartórios com interino ficam fora da regra. |
| **Provida / vaga** | Situação do cartório: com titular (provida) ou sem (vaga). |
| **Atribuição** | Tipo de serviço do cartório: notas, registro de imóveis, registro civil, protesto, títulos e documentos etc. Um cartório pode ter várias. |
| **Emolumentos** | O que o cartório cobra pelos serviços. |
| **Receita bruta / arrecadação** | Quanto o cartório recebeu no semestre. A norma usa a "receita bruta"; o dado público é a "arrecadação", que é parecida, mas não igual. |
| **Classe 1, 2, 3** | Faixas de tamanho do cartório pela receita do semestre (ver §1). Só as Classes 2 e 3 precisam cumprir a regra. |
| **Subclasse** | Faixas dentro da Classe 3 (A a J). A "Subclasse I" **não** é a Classe 1. |
| **Classe indeterminada** | Cartório sem receita válida em 2025: não dá para saber a classe. Entra no cálculo com um peso. |
| **Enquadramento** | Em que classe o cartório fica. É revisto todo ano. |
| **Passivo (trabalhista)** | A "dívida" com os funcionários: quanto custaria demitir todos hoje. |
| **Solvência** | Ter bens suficientes para pagar o passivo. |
| **Bens livres e penhoráveis** | Bens sem dívida em cima e que a Justiça pode tomar. A casa da família (**bem de família**) não entra. |
| **Déficit (de cobertura)** | Passivo − bens que contam. É o valor que a garantia precisa cobrir. |
| **Fiança bancária** | Um banco promete pagar se o titular não pagar. Pelo 227, só vale de banco **S1 ou S2**. |
| **S1 / S2** | Os maiores bancos do país, pela classificação do Banco Central. |
| **STF** | Supremo Tribunal Federal. |
| **ADI 8015** | A ação no STF que pede para derrubar parte do Provimento 227. |
| **Liminar** | Decisão provisória do juiz antes do julgamento final. No caso, não houve. |

### Direitos trabalhistas (o que entra no passivo)
| Termo | O que quer dizer |
|---|---|
| **CLT** | A lei dos empregados com carteira assinada. Só eles entram no passivo. |
| **Demissão sem justa causa** | Demissão em que o empregado não cometeu falta grave; é a que gera mais direitos. |
| **Aviso prévio indenizado** | Salário pago no lugar de avisar com antecedência: 30 dias + 3 por ano trabalhado, até 90 dias. |
| **Férias vencidas e proporcionais** | Férias já ganhas e não tiradas, mais a parte do ano em curso. |
| **Terço de férias** | Adicional de 1/3 sobre as férias. |
| **13º proporcional** | A parte do 13º salário dos meses trabalhados no ano. |
| **FGTS** | Depósito mensal de 8% do salário numa conta do empregado. |
| **Multa de 40% do FGTS** | Na demissão sem justa causa, o patrão paga 40% de tudo o que depositou no FGTS. |
| **INSS patronal** | Contribuição de 20% que o patrão paga ao INSS sobre os salários. |
| **RAT e FAP** | Contribuição para acidentes de trabalho (RAT, 1% para cartórios), ajustada por um multiplicador de cada empresa (FAP, de 0,5 a 2). |
| **Encargos** | Os valores que o patrão paga além do salário (INSS, RAT, FGTS). |

### Seguro
| Termo | O que quer dizer |
|---|---|
| **SUSEP** | Superintendência de Seguros Privados: o órgão do governo que fiscaliza as seguradoras. |
| **SES** | Base pública da SUSEP com os números de cada seguradora, por ramo e por mês. |
| **Seguro-garantia** | Seguro em que a seguradora garante que alguém vai cumprir uma obrigação (ver §2). |
| **Tomador** | Quem tem a obrigação e paga o seguro (o titular). |
| **Segurado** | Quem é protegido e recebe se a obrigação não for cumprida. |
| **Seguradora** | A empresa que garante. |
| **Apólice** | O contrato do seguro. |
| **Importância segurada (IS)** | O valor máximo que o seguro garante. Aqui, igual ao déficit. |
| **Prêmio** | O preço do seguro, pago pelo tomador. "Prêmio" não é prêmio de sorteio. |
| **Prêmio emitido / ganho** | Emitido: o valor vendido. Ganho: a parte que corresponde ao tempo já passado da apólice. |
| **Taxa** | O prêmio como % da IS, por ano. Prêmio = IS × taxa. |
| **Sinistro** | Quando acontece o problema e a seguradora precisa pagar. |
| **Sinistralidade** | Sinistros ÷ prêmio: de cada R$ 100 recebidos, quanto vira prejuízo. |
| **Ressarcimento / contragarantia** | Quando a seguradora paga, ela cobra de volta do tomador; a contragarantia é o contrato que garante isso. |
| **Comissão** | O que vai para o corretor que vendeu o seguro. |
| **Despesa administrativa** | O custo da seguradora para funcionar. |
| **Resultado técnico** | Prêmio − sinistros − comissão − despesas: o "lucro" da operação. |
| **Ramo** | Tipo de seguro na classificação da SUSEP (ex.: 0775 garantia setor público). |
| **Run-off** | Ramo que não vende mais apólices novas, só administra as antigas. |
| **Market share** | A fatia do mercado de uma seguradora. |
| **Seguradora hipotética** | Uma seguradora imaginária usada no Simulador para ver quanto **uma** empresa ganharia com uma certa fatia do mercado. |
| **Mercado total** | Tudo o que todas as seguradoras juntas receberiam. |
| **Teto teórico** | O máximo possível: toda a dívida dos obrigados × taxa, como se nenhum tivesse bens. |

### Dados e fontes
| Termo | O que quer dizer |
|---|---|
| **Justiça Aberta** | Sistema público do CNJ com o cadastro, a receita e os funcionários de cada cartório. |
| **BI do CNJ** | Painel do CNJ com dados parecidos, usado para conferência. |
| **RAIS** | Relatório anual que os empregadores entregam ao governo, com salário e tempo de casa de cada empregado. É pública sem identificar o empregador, por isso o projeto usa a média do município. |
| **CNPJ / CNAE** | Cadastro de empresas da Receita Federal; o CNAE é o código da atividade (cartório = 6912-5/00). Usado só para conferir. |
| **IBGE** | Fonte dos municípios, das regiões, da população e da inflação (INPC, IPCA). |
| **Região imediata** | Agrupamento de municípios vizinhos do IBGE. É usado quando o município tem poucos dados na RAIS. |
| **Rateio** | Divisão da dívida do município entre os cartórios, pelo número de funcionários de cada um. |
| **Data de referência / data-base** | A data a que o dado se refere (aqui, 31/12/2025). |
| **Premissa** | Um valor que o cálculo precisa e que foi definido (por lei ou por suposição). Fica em `config/`. |
| **Suposição** | Premissa sem fonte oficial. Sempre marcada como tal. |
| **Mínimo, base, máximo (nível)** | Três versões de cada conta: otimista, mais provável e pessimista. |
| **Cenário (do STF)** | O que acontece se o STF mantiver, derrubar ou derrubar em parte a regra. |
| **Regra v1 / v2** | Os limites de classe antes (v1, R$ 100 mil) e depois (v2, R$ 300 mil) do Provimento 243. |
| **Sensibilidade** | Refazer a conta mudando uma coisa, para ver quanto o resultado muda. |
| **Aproximado** | Resultado que usa um dado parecido com o que a norma pede, mas não igual. |
| **Decisão D-0xx** | Uma escolha do projeto, registrada com o motivo em [`decisoes.md`](decisoes.md). |

### Parte técnica (código e dados)
| Termo | O que quer dizer |
|---|---|
| **Pipeline** | O programa que baixa, limpa e calcula tudo, em sequência. |
| **Bronze / silver / gold** | As três etapas dos dados: bronze = como veio da fonte; silver = limpo; gold = calculado, pronto para o painel. |
| **Carga** | Uma rodada completa do pipeline, identificada pela data (ex.: carga 2026-10-19). |
| **Conjunto público** | As tabelas que podem ser publicadas, em `data/publico/`. |
| **DuckDB / Parquet** | O banco de dados local (um arquivo só) e o formato dos arquivos de tabela. |
| **Hash / SHA-256** | "Impressão digital" de um arquivo: prova que ele não mudou. |
| **Release** | Pacote de arquivos publicado no GitHub (aqui, os dados de cada carga). |
| **Streamlit** | A ferramenta que faz o painel. |
| **Ollama** | Programa que roda a IA do chat no próprio computador, sem pagar nada. |
| **Notebook** | Documento que mistura texto, código e gráficos (Jupyter). |
| **LGPD** | Lei de proteção de dados pessoais. No projeto: nenhum nome nem CPF de pessoa. |

### Estatística (aparece nos notebooks)
| Termo | O que quer dizer |
|---|---|
| **Média / mediana** | Média: soma ÷ quantidade. Mediana: o valor do meio. Com poucos cartórios muito grandes, a mediana representa melhor o "típico". |
| **Quartil** | Divide os dados em 4 partes iguais. |
| **Outlier** | Valor muito fora do padrão (pode ser erro ou caso real raro). |
| **Escala log** | Gráfico em que cada passo multiplica (1, 10, 100...), útil quando há valores muito pequenos e muito grandes juntos. |
| **Correlação** | Quanto duas coisas sobem e descem juntas (de −1 a 1). |
| **Regressão** | Modelo que estima um número (ex.: funcionários pela receita). |
| **R²** | Quanto da variação o modelo de regressão explica (de 0 a 1). |
| **Classificação** | Modelo que prevê uma categoria (ex.: vai ou não subir de classe). |
| **Precisão / recall / AUC** | Medidas de acerto de um classificador: dos que ele apontou, quantos acertou; dos que existiam, quantos achou; e uma nota geral de 0,5 (chute) a 1 (perfeito). |
| **Validação cruzada** | Testar o modelo em partes dos dados que ele não viu no treino. |
| **MAPE** | Erro médio da previsão, em %. |
| **Referência simples ("chute")** | O modelo mais bobo possível (a média, o valor anterior). Um modelo só vale se for melhor que ele. |
| **Agrupamento (cluster, k-means)** | Separar os cartórios em grupos parecidos, sem dizer antes quais são os grupos. |
| **Silhueta** | Nota de quão bem separados estão os grupos. |
| **Regras de associação (suporte, confiança, lift)** | Achar combinações que aparecem juntas com frequência (no formato "quem tem a atribuição X costuma ser da classe Y"); o lift diz quanto isso é mais comum do que o acaso. |
| **Gini / concentração** | Quanto o total está concentrado em poucos (0 = igual para todos; 1 = tudo num só). |
| **Tornado** | Gráfico que mostra qual suposição mais mexe no resultado. |
