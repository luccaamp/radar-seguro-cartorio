# Fase 1, item 2: D-038, fase 2 (sem o limiar de 3 serventias)

> Plano proposto pela IA em 2026-11-06, para a aprovação do autor. Item 2 da Fase 1 do [`plano_projeto.md`](plano_projeto.md).
> Origem: D-038 (estudo público, só nome e CPF proibidos) e D-048, item 2 (a fase 2 tira o limiar, as áreas agregadas e o auditor obrigatório).

## Por que agora
Desde a D-048 a `gold.serventia_publico` publica o resultado de **cada uma das 2.525 serventias**, com CNS e município. Mesmo assim, o painel e as tabelas por área ainda escondem os municípios com menos de 3 serventias, o que já não protege nada e só tira informação.

Medido numa cópia do banco (carga 2026-11-06):

| O que | Hoje | Depois |
|---|---|---|
| Municípios com cartório | 851 (2 sem nenhum) | 851 |
| Municípios com 1 ou 2 serventias, escondidos | **532** (649 serventias; 415 com 1, 117 com 2) | 0 |
| Linhas da `fato_mercado_municipio_publico` | 320 (319 municípios + 1 linha "Outros municípios") | 851 |
| Municípios no ranking (`ranking_municipio_publico`) | 319 | 851 |
| Áreas do mapa (`geo_mapa_publico`) | 385 (319 municípios + 66 regiões dissolvidas) | 851 municípios |
| Municípios na `fato_passivo_municipio` | 319 | 851 |
| Combinações filtro × regra × nível sem publicação (`mercado_filtro_uf`) | 7 de 78 | 0 |
| Tamanho da geometria do mapa | 358 kB (+ 525 kB das visões filtradas) | ≈ 498 kB (malha municipal de MG) |

**Efeito esperado nos 10 números: nenhum.** O limiar só agrupa na exibição; os totais de MG não passam por ele. A conferência na cópia vai comparar os 10 números e as tabelas que não deveriam mudar.

## O que muda

### 1. Premissas v4
`config/premissas/premissas_v004.yaml` = v3 sem a premissa `limiar_agregacao_lgpd` (e com a data e a fonte da mudança: D-078). Todas as outras iguais. A coluna `gold.execucao.limiar_lgpd` sai.

### 2. Pipeline (gold)
- `fato_mercado_municipio_publico`: todos os municípios, sem a linha agregada (sai `src/model/lgpd.py` e a coluna `agregado_lgpd`).
- `fato_passivo_municipio`: todos os municípios (hoje igual à `interno_passivo_municipio` filtrada).
- `ranking_municipio_publico`: as 4 métricas para os 851 municípios.
- Mapa: uma área por município (`geo_mapa_publico` = malha municipal; `geo_area_municipio` com `area_id` = código IBGE); sai a dissolução por região (`areas_do_mapa` em `src/transform/geo.py`). `mercado_area_publico` com `tipo = municipio` em todas as linhas.
- `qualidade.rec_municipio` (pública) passa a ter todos os municípios, como a `interno_rec_municipio`.
- `mercado_filtro_uf`: todas as combinações publicadas (a coluna `publicado` fica sempre verdadeira; ver a questão 1).
- Contratos do gold sobre o limiar (`reconciliacao.py`: "exibição sem município com menos serventias que o limiar" e "mapa: nenhuma área pública com menos serventias") saem; entra "uma linha por município com cartório" no mapa, no ranking e no mercado por município.

### 3. Conjunto público e auditor
- `scripts/gerar_publico.py` deixa de rodar o auditor de ataque por diferença (`src/model/supressao.py`, `visoes.auditar`).
- `src/publico.py` (`checar`): sai o contrato do limiar e as `excecoes_limiar`; **continuam** as travas de nome de pessoa, CPF, e-mail e colunas de dado pessoal, em todas as tabelas.
- `manifesto.json` sem `limiar_lgpd` nem `excecoes_limiar`.

### 4. Painel e chat
- **Onde está o mercado:** mapa por município (inclusive os pequenos); sai o aviso "tem menos de 3 cartórios: aparece agregado em…"; o município escolhido mostra a posição dele no ranking de MG ("12º de 851 no déficit"). Entra um ranking curto (os 10 primeiros na métrica do mapa, mais o município escolhido), como pede o plano.
- **Chat:** sai a resposta "contagem não publicada (suprimida pelo auditor de LGPD)" (`src/agent/ferramentas.py`); o prompt passa a dizer que todo município tem dado. Nome de pessoa continua proibido.

### 5. Testes e documentos
- Saem ou mudam: `tests/test_lgpd.py`, `tests/test_auditoria_painel.py`, os testes de limiar de `tests/test_publico.py`, `test_app.py` e `test_app_demo.py`. Entra um teste de que os 851 municípios aparecem no mapa, no ranking e na tabela por município, e de que nenhuma tabela pública tem nome de pessoa (o que já existe continua).
- Banco de demonstração (`tests/` e modo demo): regerado com as tabelas novas, marcado como sintético.
- Documentos: SPEC §6 reescrita (só nome e CPF), `dicionario_dados.md`, `decisoes.md` (D-078), `entenda_o_projeto.md` e README onde falam do limiar, `ESTADO_ATUAL.md`, `diario.md`.

## Ordem de execução
1. Branch `fase-1-d038-fase2`, a partir da `main` atualizada.
2. Premissas v4 e código (itens 1 a 4), com os testes da suíte padrão verdes.
3. Pipeline `--a-partir-de silver` **numa cópia**: os 10 números iguais; tabelas que não deveriam mudar com o mesmo conteúdo; as que mudam conferidas uma a uma; `gerar_publico.py --banco <cópia>` sem nome nem CPF.
4. Painel na cópia, no navegador: mapa com os 851 municípios, um município pequeno escolhido, capturas em 390 e 1366 px.
5. `pytest -m dados_reais` na cópia (≈ 25 min).
6. **Parar e mostrar o resultado.** A carga oficial no `data/radar.duckdb` real, a regeração de `data/publico` e `data/completo` e o PR só com o pedido do autor na mensagem (regra do `CLAUDE.md`).

**Pronto quando:** mapa e ranking por município com os pequenos; nenhuma área agregada no gold, no público, no painel nem no chat; os 10 números iguais; suíte e `dados_reais` verdes; CI verde no PR.

## Questões para o autor
1. **Visões filtradas por região** (`mercado_filtro_area`, `mercado_filtro_regiao`, `geo_mapa_filtro`, `geo_regiao_imediata`, `interno_celulas_publicadas`, `interno_auditoria`): existiam para a supressão; o painel não as lê desde a Etapa 3 e o chat só usa a `mercado_filtro_uf`. **Recomendação:** tirá-las do pipeline e do público (as da carga atual ficam no backup em `C:\radar_arquivo`), e manter a `mercado_filtro_uf` com tudo publicado. Alternativa: mantê-las, sem supressão.
2. **Premissa do limiar:** **recomendação:** tirar da v4 (o conceito deixa de existir). Alternativa: deixar `valor: 1` e o código como está, o que muda menos código mas mantém o auditor e a dissolução do mapa sem uso.
3. **Ranking no painel:** **recomendação:** os 10 primeiros mais o município escolhido, na página "Onde está o mercado". Alternativa: só a posição do município escolhido, sem lista.
4. **Mesma carga oficial:** o item 2 pede uma carga oficial; a renomeação da `fato_mercado_municipio_publico` (item 5 da Fase 1) também mudaria o gold. **Recomendação:** não juntar; o item 5 vai depois, numa carga própria, para este PR ficar só com a D-038.
