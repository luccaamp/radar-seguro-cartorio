# Viabilidade (Fase 0)

> **Histórico.** Resultado da Fase 0. O que mudou depois: D-032 (bronze enxuto), D-003 a D-008 (decisões pendentes da seção 5), D-015 (887 vínculos sem salário de dezembro). Continua como fonte para a E2, a E5, a E6 e a E7.

> Resultado da Fase 0 do `docs/SPEC.md` (§8). Testes feitos em 2026-10-17 e 2026-10-18 no computador do autor.
> Nenhuma fonte usada exige pagamento, cartão, conta em nuvem ou cadastro.
> Brutos em `data/bronze/<fonte>/` (fora do git, 13,8 GB), com URL, data e SHA-256 em `_metadados.json` ou `*.meta.json`. Amostras pequenas, sem dados pessoais, em `data/samples/`.

## 1. Fontes de dados

| Fonte | Status | Formato / acesso | Campos úteis | Data de referência | Cobertura | Download em massa | Plano B |
|---|---|---|---|---|---|---|---|
| **CNJ / Justiça Aberta**, API pública do novo sistema (`justicaabertaapi.cnj.jus.br/v1/api/serventias`) | **ok** ⚠️ API sem documentação oficial | JSON. `POST` na listagem por UF (página única); `GET /{cns}`, `/{cns}/arrecadacoes`, `/{cns}/dados-complementares` | CNS, denominação, atribuições (`natureza`), cidade, UF, `tipo_cartorio`, `status` (Ativo/Inativo/Extinto), **`situacao_juridica_cartorio`** (PROVIDO / VAGO / SOB INTERVENÇÃO / CONVERSÃO EM DILIGÊNCIA + data), data de instalação; **arrecadação semestral** ("receita bruta") e atos praticados, com histórico de até 41 semestres; **colaboradores** CLT, estatutários, estagiários e terceirizados | Arrecadação até o **1º sem/2026**; cadastro e colaboradores na data da coleta (17/10/2026, declarados pelo cartório) | Brasil: 16.269 registros, **12.121 ativos**. MG: 3.213 registros, **2.525 ativos** (1.654 providos, 830 vagos, 28 em diligência, 13 sob intervenção) em 851 municípios. Colaboradores informados em 99,8% das ativas de MG. Arrecadação "NÃO INFORMADO" em 3 de 30 da amostra (~10%) | Listagem: 1 requisição por UF. Detalhe: 1 requisição por serventia por rota (MG ≈ 2.525 × 1,2 s ≈ 50 min por rota) | Painel Qlik do CNJ com exportação manual pelo autor; listas dos TJs; CNPJ como conferência |
| **Painel de Dados Estatísticos das Serventias** (Qlik, `paineisanalytics.cnj.jus.br`, appid `6ae52b4b…`) | parcial | Painel interativo; abre sem login | Os mesmos do Justiça Aberta | Atualização diária (segundo o CNJ) | Brasil | **Não automatizável** (dados carregados dentro do navegador); exportação CSV/XLSX manual | Conferência manual da API |
| **Dados abertos do CNPJ** (Receita, agora no **SERPRO+**, compartilhamento público WebDAV) | **ok** | ZIP com CSV `;` latin-1, sem cabeçalho. 10 × Estabelecimentos (5,4 GB) + 10 × Empresas (1,4 GB) + tabelas | CNPJ básico, matriz/filial, situação cadastral, data de início, CNAE principal e secundário, UF, município (código da Receita), natureza jurídica (via Empresas) | Pacote **2026-10** (publicado em 13/10/2026) | MG: **2.923 ativos** com CNAE principal 6912-5/00, 100% com natureza 3034 "Serviço Notarial e Registral (Cartório)", em 793 municípios. Brasil: 16.562 ativos (sem exterior) | Sim, cerca de 6,8 GB por mês (~35 min). O endereço mudou em 2026 | Pacote do mês anterior (há histórico desde 2023-05) |
| **RAIS** (PDET, FTP público) | **ok** | `.7z` com CSV `,` latin-1. MG vem junto com ES e RJ (767 MB → 5,0 GB). Estabelecimentos do Brasil (144 MB → 1,5 GB) | Vínculo ativo em 31/12, **remuneração de dezembro** e **média anual** (nominal e em salários mínimos), **tempo de emprego** (meses), faixas, tipo de vínculo, município, natureza jurídica, **tipo de estabelecimento (CNPJ / CAEPF)** | **Ano-base 2025** (publicada em 13/05/2026) | MG, CNAE 6912-5/00: **12.347 vínculos ativos**, dos quais **98% (12.087) em CAEPF**, o CPF do titular. Brasil: 106.735 vínculos (106.524 CLT) em 17.083 estabelecimentos. Filtro pelo CNAE funciona (MG filtrado = 4,2 MB) | Sim. Por região. O layout oficial mais recente no FTP é de 2018/19 (estabelecimentos) e 2020 (vínculos) | RAIS 2024; Novo CAGED para tendência |
| **ANOREG "Cartório em Números"** (7ª ed., 2025) | **ok** (só controle) | PDF, 212 páginas | **12.210 serventias** (p. 48), **96.740 empregados**, sendo 95.099 CLT e 1.641 estatutários (p. 49), atribuições (8.228 notas, 7.201 RCPN, 3.846 protesto…) | 2025 (dez/2025). Fonte declarada: **painel do CNJ** | Só Brasil, **sem divisão por UF** | Sim (1 PDF) | Edição anterior |
| **Painel de vacâncias** (Corregedoria Nacional, Prov. 219/2026) | parcial | Power BI público | Relações gerais de vacância (provisórias e definitivas) por TJ | Desde jul/2026 | Brasil | Não (só visualização) | Desnecessário para o universo: a API do CNJ já traz VAGO |
| **Listas dos TJs** (vacâncias, editais) | parcial | PDF / Diário de Justiça | Serventias vagas, às vezes com a classe | Semestral (Prov. 219) | Exemplos: TJBA (jul/2026) e TJMA (mar/2026). **TJMG não localizado** | Não | Download manual pelo autor, se necessário |
| **IBGE** | **ok** | API JSON (localidades) e SIDRA | Código de município com 7 dígitos (853 em MG), população estimada, PIB municipal | População **2026** (tab. 6579); PIB **2023** (tab. 5938) | Brasil | Sim | — |
| **SUSEP SES** (`BaseCompleta.zip`) | **ok** | ZIP com CSV `;` (577 MB) | Prêmio emitido, prêmio ganho, sinistro ocorrido, comissão, resseguro por ramo × seguradora × mês. Ramos em vigor de garantia: **0775 Setor Público** e **0776 Setor Privado** (os de 0739 a 0750 estão em run-off) | Até **ago/2026** (atualização semanal) | Mercado inteiro | Sim | Painel de Inteligência da SUSEP |
| **Normas** (atos.cnj.jus.br) e **STF** (portal) | **ok** | HTML + PDF; portal do STF sem bloqueio | Prov. 227, 213 (original e compilado) e 243; abas e decisão da ADI 8015 | Coletado em 17/10/2026 | — | Sim | Sites das associações |

Referência pública de garantia (SES, set/2025 a ago/2026, todas as seguradoras; **unidade a confirmar no layout**, tratada como R$):

| Ramo | Prêmio emitido | Prêmio ganho | Sinistro ocorrido | Sinistro ÷ prêmio ganho | Comissão ÷ prêmio emitido |
|---|---|---|---|---|---|
| 0775 Setor Público | 6,13 bi | 3,94 bi | 0,56 bi | ~14% | ~16% |
| 0776 Setor Privado | 0,86 bi | 0,76 bi | 0,45 bi | ~59% | ~22% |

Como o segurado da garantia do Prov. 227 não está definido (art. 13), não se sabe em qual dos dois ramos o produto cairia. As premissas `sinistralidade` e `comissao` precisam mostrar os dois como faixa.

## 2. Conferência entre fontes (Etapa 5)

### Serventias
| | MG | Brasil |
|---|---|---|
| CNJ (ativas, out/2026) | **2.525** | **12.121** |
| ANOREG (fonte CNJ, 2025) | — | 12.210 (+0,7%) |
| CNPJ (ativos, CNAE principal, out/2026) | 2.923 (+15,8%) | 16.562 (+36,6%) |
| RAIS 2025 (estabelecimentos do CNAE com vínculo) | 2.132 | 12.393 |

- **CNJ × ANOREG:** bate (0,7%), mas não é uma conferência independente, porque a ANOREG usa o painel do CNJ. Confirma que a extração da API está correta.
- **CNJ × CNPJ (MG):**
  - 446 dos 853 municípios são idênticos;
  - em 62 municípios há serventia no CNJ e nenhum CNPJ ativo; em 2, o contrário;
  - **339 dos 552 CNPJs "a mais" (61%) coincidem com serventias inativas no CNJ** do mesmo município, ou seja, CNPJs não baixados depois de extinção ou anexação;
  - os picos de abertura de CNPJ em 2018 (109) e 2024 (104) sugerem um CNPJ novo a cada novo titular, com o antigo continuando ativo. Isso é hipótese, não verificada;
  - conclusão: **o CNPJ superestima o universo.**
- **RAIS:** conta só as serventias com empregado. **316** serventias ativas de MG têm 0 CLT no CNJ (57 providas, 258 vagas, 1 sob intervenção).

### Empregados
| | MG | Brasil |
|---|---|---|
| RAIS 2025 (vínculos ativos em 31/12/2025) | **12.347** | 106.524 CLT |
| CNJ, colaboradores CLT declarados (out/2026) | **12.134** | não coletado |
| ANOREG (fonte CNJ, 2025) | — | 95.099 CLT |
| Razão | **RAIS/CNJ = 1,018** | RAIS/ANOREG = 1,120 |

- **Em MG, RAIS e CNJ concordam:** 1,8% de diferença no total e **correlação de 0,996 por município** (821 municípios com dado; 646 com diferença de até 2 vínculos). As fontes são independentes (eSocial × Justiça Aberta).
- **Vínculos no CPF do titular:** a RAIS **capta** esses vínculos (CAEPF, 98% em MG). O risco do §10 do SPEC não se confirmou para MG. Proposta: `fator_cobertura_rais` base **1,0**, com esta conferência como fonte (decisão na Fase 1).
- **Brasil, +12% na RAIS contra a ANOREG:** a causa é desconhecida. Hipóteses: datas diferentes, cadastro do Justiça Aberta desatualizado, ou empresas que não são cartório usando o CNAE em outras UFs. Investigar na Fase 2 coletando os colaboradores do CNJ de todas as UFs.
- **Ruído por município:** em 64 municípios o CNJ tem CLT e a RAIS tem 0. Também há casos como Uberaba (RAIS 169 × CNJ 244) e Contagem (267 × 211). Causa provável: a RAIS registra o vínculo no endereço do CAEPF do titular.

### Proposta de rateio
A RAIS não identifica a serventia, e o município dela tem ruído. Por isso proponho um novo método em `ratear_passivo`: **`por_empregados_cnj`**.
- Peso de cada serventia = colaboradores CLT declarados no Justiça Aberta.
- Distribuição de salário e tempo de emprego = RAIS (ver a decisão pendente 4).
- Os métodos `arrecadacao`, `uniforme` e `peso_por_atribuicao` ficam como sensibilidade.
- **Isso muda o §3.3 do SPEC e precisa da aprovação do autor.**

## 3. Escolhas da Fase 0

- **Lista principal de cartórios (universo): CNJ / Justiça Aberta (API pública).**
  - É a única fonte que tem CNS, situação jurídica (interino), arrecadação semestral e empregados por serventia.
  - Coleta em página única por UF, com checagem de integridade (`meta.total` = registros = CNS distintos).
  - O CNPJ serve de conferência por município; o painel Qlik, de conferência manual.
- **Modelo do Ollama: `qwen3:8b`** (Q4_K_M, 5,6 GB carregado, **100% na GPU** RX 580 de 8 GB via Vulkan).
  - Acertou 4 de 4 casos no teste de tool calling, contra 3 de 4 do `llama3.1:8b`. O llama chamou a ferramenta numa pergunta conceitual e não citou a fonte.
  - Tempo de 2 a 5 s por pergunta.
  - Reserva: `llama3.1:8b`.
  - Pendências para a Fase 3: aumentar o contexto (`num_ctx`, padrão de 4.096) e decidir o `think`; os dois vão para `config/llm.yaml`.
- **Normas:** os critérios da Classe 1 foram **verificados no texto do próprio Prov. 243**:
  - art. 1º, que altera o art. 2º, XXIV, e o art. 16, I a III e §§ 1º a 3º, do 213;
  - Classe 1 até R$ 300.000,00 de receita bruta semestral; Classe 2 até R$ 1.500.000,00;
  - o texto é idêntico ao compilado do 213;
  - vigência em 22/08/2026 (art. 2º do 243).

## 4. Riscos e limitações encontrados

1. **API do CNJ sem documentação oficial:** pode mudar sem aviso. Mitigação: bronze imutável, checagem de integridade e plano B pelo painel Qlik (manual).
2. **Paginação instável da API:** coletar em página única por UF. A consulta do Brasil inteiro numa requisição dá timeout (504).
3. **Colaboradores e cadastro do CNJ são autodeclarados** e sem data de atualização por serventia.
4. **Arrecadação "NÃO INFORMADO"** em cerca de 10% da amostra. Saltos suspeitos na série; exemplo: CNS 152322 passou de R$ 27 mil para R$ 951 mil entre semestres.
5. **Arrecadação ≠ receita bruta do art. 2º, XXIV do 213:** classificação aproximada (D-002).
6. **Peso da regra de classe:** na amostra de 27 serventias com valor, 13 ficam até R$ 300 mil e 8 até R$ 100 mil no 1º sem/2026. A troca `v1` × `v2` muda muito o universo.
7. **RAIS:** defasagem até dez/2025; layout oficial desatualizado; 910 vínculos ativos de MG sem remuneração de dezembro.
8. **Municípios com grafia diferente** entre fontes (ex.: "BRASOPOLIS" no CNPJ): tabela de apelidos na Fase 1.
9. **SUSEP:** unidade dos valores a confirmar; ramo do produto indefinido (0775 × 0776).

## 5. Decisões pendentes para a Fase 1

1. **Usar só os colaboradores CLT no passivo?** O Prov. 227 fala em verbas rescisórias da CLT. Estatutários (178 em MG), estagiários (86) e terceirizados (135) ficariam de fora.
2. **Situações "SOB INTERVENÇÃO" (13 em MG) e "CONVERSÃO EM DILIGÊNCIA" (28 em MG):** tratar como interinidade (fora da norma, art. 19), como provida (dentro) ou como categoria à parte com sensibilidade?
3. **Arrecadação "NÃO INFORMADO"** tratada como **classe indeterminada** (§3.4 do SPEC: fora no `min`, dentro no `max`, com peso no `base`).
4. **Distribuição de salário e tempo de emprego:** usar a do **município** só quando houver vínculos suficientes na RAIS, e a do **estado** nos demais. O limiar mínimo de vínculos vira premissa em `config/`.
5. **Novo método de rateio `por_empregados_cnj`** como padrão (§2 acima). Exige mudar o §3.3 do SPEC.
6. **`fator_cobertura_rais` = 1,0** como base para MG, com fonte nesta conferência.

## 6. Critério de aceite da Fase 0 (SPEC §8)

| Item | Situação |
|---|---|
| `uv` + Python 3.12, sem alterar o Python do sistema | ✅ uv 0.13.1, Python 3.12.15; sistema continua em 3.13.3 |
| RAM e GPU verificadas; modelo proposto e testado em tool calling | ✅ 32 GB RAM, RX 580 8 GB (Vulkan); `qwen3:8b` 4/4 |
| Provimentos 227, 213 e 243 baixados e conferidos (arts. 8º a 17, passivo, prazo do 1º ano, Classe 1, segurado) | ✅ (o segurado **não é definido** na norma) |
| Andamento da ADI 8015 | ✅ rito do art. 12, sem liminar, com vista à PGR (17/10/2026) |
| Cada fonte do §1.1 testada (formato, campos, cobertura, referência, download em massa) | ✅ tabela da seção 1 |
| Totais comparados entre fontes e com o "Cartório em Números" | ✅ seção 2 |
| `viabilidade.md` com status e plano B por fonte, universo e modelo escolhidos | ✅ este documento |
| Nenhuma fonte usada exige pagamento ou cadastro | ✅ |
