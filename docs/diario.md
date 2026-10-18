# Diário do projeto

Registro cronológico de decisões, suposições, limitações e descobertas. Entrada mais recente no topo.

Formato de cada entrada:

```
## AAAA-MM-DD — título curto
- **O que foi feito:**
- **Decisões:** (o que foi escolhido e por quê)
- **Suposições:** (o que foi assumido sem fonte)
- **Limitações encontradas:**
- **Próximo passo:**
```

---

## Linha de base

Medida do "antes", usada na comparação final dos slides. O autor já fez a medição e vai preencher aqui.

- **Tarefa medida:**
- **Data:**
- **Tempo gasto:**
- **Fontes consultadas:**
- **O que foi difícil:**

---

## 2026-10-17 a 2026-10-18 — Fase 0 (viabilidade) concluída
- **O que foi feito:**
  - **Ambiente:** uv 0.13.1 e Python 3.12.15 instalados pelo uv, com o sistema mantido em 3.13.3. `pyproject.toml` mínimo (httpx; pytest como dev), `.python-version` e `uv.lock`.
  - **Computador:** i5-11400, 32 GB de RAM, Radeon RX 580 com 8 GB (o Windows mostra 4 GB; o valor real veio do registro). O Ollama 0.32.6 já estava instalado e usa a GPU via Vulkan.
  - **LLM:** teste de tool calling com uma ferramenta de exemplo (resultado sintético). `qwen3:8b` acertou 4/4 e `llama3.1:8b` 3/4. Os dois rodam 100% na GPU, com 2 a 5 s por pergunta.
  - **Normas:**
    - Prov. 227, 213 (original e compilado) e 243 baixados de atos.cnj.jus.br para `data/bronze/normas/`;
    - ADI 8015 consultada no portal do STF (`data/bronze/stf/`);
    - SPEC atualizado com as diferenças encontradas (decisões D-001 e D-002 em `docs/decisoes.md`; `config/regras_classificacao.yaml` com `v1` e `v2`).
  - **Fontes:** todas as do §1.1 testadas (ver `docs/viabilidade.md`); 13,8 GB de brutos no bronze, com hash; amostras em `data/samples/`.
  - **Conferência entre fontes:** em MG e no Brasil, em total e por município.
- **Descobertas:**
  - **Prov. 227:**
    - os arts. 8º a 17 incluem a declaração de solvência, a garantia (art. 13) e as penalidades;
    - o passivo inclui a projeção do aviso prévio sobre férias e 13º, e os encargos INSS, RAT × FAP e FGTS;
    - a base é a maior remuneração fixa (art. 6º);
    - fiança só de bancos S1/S2;
    - **o segurado não é definido**.
  - **Classe 1 (Prov. 243, texto do próprio ato):**
    - receita bruta semestral de até R$ 300 mil (antes, R$ 100 mil); em vigor desde 22/08/2026;
    - limites atualizados todo ano pela Corregedoria Nacional;
    - o art. 19 do 227 escreve "Classe I" e o 213 usa "Classe 1" (D-001).
  - **ADI 8015:** rito do art. 12 da Lei 9.868/1999 (sem liminar separada); informações do CNJ e da AGU já prestadas; vista à PGR; amicus da Ad Notare indeferido em 13/10/2026. **Não há liminar.**
  - **CNJ / Justiça Aberta:**
    - a API pública do novo sistema traz cadastro, situação jurídica, arrecadação semestral (até o 1º sem/2026) e **colaboradores por serventia**, sem cadastro;
    - MG tem 2.525 ativas (1.654 providas, 830 vagas, 28 em diligência, 13 sob intervenção); o Brasil tem 12.121;
    - **a paginação é instável:** a coleta paginada perdeu 374 CNS de MG; a coleta em página única por UF tem checagem de integridade (SP: 1.680 informados, 1.679 entregues).
  - **CNPJ:** mudou de endereço para o SERPRO+ (WebDAV público). Pacote 2026-10: MG tem 2.923 ativos com CNAE 6912-5/00, todos com natureza 3034.
  - **RAIS 2025** (publicada em 13/05/2026):
    - MG tem 12.347 vínculos ativos no CNAE; **98% em CAEPF** (CPF do titular), que a RAIS **capta**;
    - remuneração de dezembro com mediana de R$ 2.600 e média de R$ 3.640;
    - tempo de emprego com mediana de 32 meses e média de 61; 2.002 vínculos com 10 anos ou mais.
  - **ANOREG (7ª ed., 2025):** 12.210 serventias e 96.740 empregados (95.099 CLT). Só Brasil; a fonte é o próprio CNJ.
  - **SUSEP SES** (até ago/2026): ramos de garantia em vigor 0775 (setor público) e 0776 (setor privado). Sinistro ÷ prêmio ganho em 12 meses: ~14% e ~59%; comissão: ~16% e ~22% (unidade a confirmar).
  - **Conferência:**
    - serventias: CNJ 2.525 × CNPJ 2.923 (+15,8%) em MG; 61% do excesso do CNPJ coincide com serventias inativas no CNJ (CNPJ não baixado);
    - Brasil: CNJ 12.121 × ANOREG 12.210 (+0,7%; mesma origem);
    - empregados em MG: RAIS 12.347 × CNJ 12.134 CLT (razão 1,018; **correlação de 0,996 por município**); no Brasil, RAIS/ANOREG = 1,12 (causa desconhecida).
- **Decisões:**
  - **Universo:** CNJ / Justiça Aberta (API pública), com o CNPJ como conferência.
  - **LLM:** `qwen3:8b`, com `llama3.1:8b` de reserva.
  - **Classe 1:** `v2` = R$ 300 mil como base e `v1` = R$ 100 mil como sensibilidade; classificação sempre aproximada (D-002).
  - **Passivo:** base do art. 6º aproximada pela remuneração de dezembro da RAIS (média anual como alternativa); saldo de salário desligado; `acrescimo_cct_pct` = 0.
  - **Radar:** prioridade para normas estaduais e para a atualização anual dos limites de classe.
- **Propostas que dependem do autor:**
  - **rateio `por_empregados_cnj`** como padrão, pesando cada serventia pelos CLT declarados no Justiça Aberta (muda o §3.3 do SPEC);
  - `fator_cobertura_rais` = 1,0 como base em MG.
- **Pendentes para a Fase 1:**
  1. usar só colaboradores CLT no passivo;
  2. tratamento das situações "sob intervenção" e "conversão em diligência";
  3. arrecadação "NÃO INFORMADO" como classe indeterminada;
  4. distribuição de salário e tempo do município só com vínculos suficientes, e a do estado nos demais (limiar como premissa).
- **Suposições:**
  - vigência do 213 original em 09/04/2026 pela LINDB (o ato não tem cláusula de vigência);
  - CNPJ novo a cada titular (hipótese para o excesso do CNPJ);
  - valores do SES em reais.
- **Limitações encontradas:**
  - API do CNJ sem documentação oficial;
  - colaboradores autodeclarados e sem data;
  - ~10% de arrecadação "NÃO INFORMADO";
  - layout da RAIS no FTP desatualizado (2018/2020);
  - ANOREG sem UF;
  - painéis do CNJ (Qlik) e de vacâncias (Power BI) sem download automático;
  - lista do TJMG não localizada;
  - RAIS +12% no Brasil sem explicação.
- **Erros da IA:** 11 nesta sessão e 3 da Sessão 0, registrados em `docs/erros_ia.md`. Os principais: paginação instável que esconderia 12% de MG, RAIS filtrando 0 vínculos e endereços do CNPJ desatualizados.
- **Próximo passo:** Fase 1 (painel de MG), começando pelo plano curto e pelas decisões pendentes acima.

## 2026-10-17 — Projeto passa a ser 100% gratuito e muda de prioridade
- **O que foi feito:** o SPEC, o CLAUDE.md e o `prompts.md` foram reescritos.
- **Decisões:**
  - **Custo zero.** Nada pago, nenhum cadastro em nuvem, nenhuma chave de API com créditos. Tudo roda no computador do autor.
  - **Nova prioridade:** (1) painel de cartórios com dados reais e (2) chat são o centro do projeto. O radar virou opcional, primeiro numa versão simples sem IA.
  - **Mínimo da demo:** painel (Mercado e Simulador) de MG e o chat respondendo com fonte.
  - **Fontes:** universo pelo Painel de Dados Estatísticos das Serventias Extrajudiciais do CNJ, conferido com os dados abertos de CNPJ da Receita, as listagens dos TJs e o painel de vacâncias. RAIS pelo download direto no PDET. "Cartório em Números" (ANOREG) como total de controle.
  - **LLM:** Ollama local, com modelo escolhido na Fase 0 conforme a RAM e a GPU. Acesso por uma interface única (`src/llm.py`).
  - **Banco:** DuckDB em arquivo local para os dados e para o estado do app.
  - **Nova página "Qualidade dos dados"** no painel, porque a confiabilidade dos dados é o ponto principal.
  - **Ordem das fases:** 0 viabilidade, 1 painel de MG, 2 Brasil e qualidade, 3 chat, 4 radar (opcional), 5 entrega.
- **Decisões que deixaram de valer:** Claude API, BigQuery/Base dos Dados, MotherDuck, GitHub Actions, deploy obrigatório no Streamlit Cloud e envio de resumo por e-mail ou Slack. As pendências sobre conta GCP, orçamento e canal do resumo foram encerradas.
- **Pendências do autor:** data da entrevista; preencher a linha de base acima.
- **Próximo passo:** Fase 0.

## 2026-10-17 — Decisões da Sessão 0 que continuam valendo
- **Fatos verificados pelo autor** (a IA vai confirmá-los no texto oficial na Fase 0): Prov. 227/2026 publicado em 11/06/2026 e em vigor desde 10/08/2026; Prov. 243/2026 alterou as classes do 213; ADI 8015 ajuizada pela ANOREG em set/2026 contra os arts. 8º a 17, relator Min. Flávio Dino; primeira declaração 30 dias após a vigência, depois ciclo anual; passivo = demissão de todos sem justa causa.
- **Modelo:** `prob_deficit` e `pct_descoberto` separados; `escolha_garantia` com três parcelas que somam 100%; receita = IS × taxa × market share, anual e recorrente; market share de seguradora hipotética; resultado técnico com comissão e despesa administrativa; rateio sobre todas as serventias e exclusões depois; classe indeterminada fora no min, dentro no max e com peso no base.
- **Dados:** dado mais recente de cada fonte, com data de referência visível; correção salarial da RAIS como premissa.
- **Premissas:** YAML como semente no git; versões salvas no banco (`premissas_versoes`); `cenarios_stf.yaml` com as definições fixas e `cenarios_salvos` com as combinações do usuário.
- **Orquestração:** `uv run pipeline.py` no lugar do `make`; "do zero" = a partir dos snapshots do bronze.
- **LGPD:** nome e CPF descartados na passagem bronze → silver; limiar de agregação de 3 serventias.
- **Radar (se for feito):** taxonomia de `tipo_evento` aprovada; dedup pela data do ato original; citação normalizada; texto coletado isolado no prompt.
- **Ambiente:** o projeto fica no OneDrive (decisão do autor). Python 3.12 instalado pelo `uv`, sem mexer no 3.13.3 do sistema. `docs/plano_radar_seguro_cartorio.html` foi removido de propósito (era duplicata do SPEC).

## 2026-10-17 — Início do projeto
- **O que foi feito:** SPEC, CLAUDE.md e estrutura de documentação criados; repositório publicado em `luccaamp/radar-seguro-cartorio`.
- **Próximo passo:** Sessão 0 (revisão do SPEC pela IA).
