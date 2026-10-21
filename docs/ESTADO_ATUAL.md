# Estado atual do projeto

> Leia primeiro. Atualizado ao fim de cada sessão (regra do `CLAUDE.md`). Última atualização: **2026-10-20**.

## O que é
Radar Seguro-Garantia Cartórios: projeto de portfólio, 100% gratuito e local.
- **Painel:** cartórios de Minas Gerais, com dados públicos reais.
- **Simulador:** mercado de seguro-garantia criado pelo Provimento CNJ 227/2026.
- **Chat com fontes:** ainda por fazer.

## Onde estamos
- **Fase 1 (painel de MG): concluída e fechada em 2026-10-20.**
  - Limpeza do projeto (`docs/historico/limpeza_projeto.md`) commitada na `main` (`dc0496b`, `be8ad32`).
  - Releases publicados: `dados-2026-10-19` (público), `carga-2026-10-19` e `originais-2026` (privados). O download de verdade dos privados foi testado em 2026-10-20: 25/25 tabelas, os 10 números e os 25 originais por SHA-256.
  - `main` do repositório público protegida (ruleset `main protegida`; o dono está na Bypass list; `docs/publicacao.md`, seção 4).
  - Fechamento commitado na `main` (`21303e2`).
- **Pasta do projeto:** **`C:\projetos\radar-seguro-cartorio`** (D-033), clonada do GitHub em 2026-10-20, com os dados copiados da pasta antiga. A pasta antiga do OneDrive ficou só como cópia de segurança e não é mais usada.
  - Verificação completa da pasta nova em 2026-10-20 (`docs/diario.md`): suítes 137 / 73 / 2, pipeline a partir do silver com 25/25 + 25/25 e os 10 números, galeria com 0 falhas, modo demonstração ok.
  - Linha de base do "antes" do Bloco 2: `C:\radar_arquivo\baseline_2026-10-20\linha_de_base.json` (igual à de 19/10 e ao `manifesto.json`).
- **Painel só leitura (D-034, 2026-10-20):** o painel abre `data/radar.duckdb` só para leitura e pode ser aberto direto, sem cópia (roteiro no `README.md`, seção 5). Os cenários salvos vão para `data/painel_estado.json`, e o Simulador não cria mais versão de premissas. Com o painel aberto, o pipeline para no início.
- **Próximo:** Bloco 2, começando pelo **Q4** (receita bruta), que depende do **Q8** (repasse por serventia no silver).

## Ordem das etapas (decisão do autor, 2026-10-20; `docs/SPEC.md`, §8)
1. **Bloco 2:** qualidade dos dados (`docs/plano_qualidade_e_correcoes.md`), começando pelo **Q4** (receita bruta do Prov. 213 × arrecadação × arrecadação menos repasse).
2. **Bloco 3:** premissas do seguro (S1 a S6 do mesmo plano).
3. **Mineração dos dados de MG** em notebooks.
4. **Redesenho do painel de MG** com os achados.
5. **Chat de IA:** as ferramentas recebem a UF como parâmetro e respondem só com visões públicas auditadas.
6. **Estudo da ordem dos estados** em notebook: nota que combina tamanho, mercado, viabilidade dos dados e adoção, com teste de sensibilidade e validação com MG; registrado como decisão.
7. **Expansão estado por estado.**

## Números de referência
Carga **2026-10-19**, premissas **v2**, regra base (Classe 1 até R$ 300 mil, Prov. 243), nível base, regra do STF mantida:

| Serventias ativas | Empregados CLT | Obrigadas (Prov. 227) | Passivo (todas) | Passivo (obrigadas) |
|---|---|---|---|---|
| 2.525 | 12.134 | ≈ 1.121 | R$ 311,9 mi | R$ 238,1 mi |

| Com déficit (esperado) | Déficit | IS do mercado | Prêmio anual | Teto teórico |
|---|---|---|---|---|
| ≈ 486 | R$ 36,9 mi | R$ 18,4 mi | R$ 368,7 mil | R$ 4,76 mi |

O conjunto público (`data/publico/manifesto.json`) traz o hash de cada tabela. "Recalcular dá o mesmo" foi provado em 2026-10-19: 25 de 25 tabelas idênticas, a partir do silver e do bronze.

## Últimas decisões
- **D-026:** filtros do Mercado por região, com supressão e auditor de ataque por diferença.
- **D-027:** regra v1 e mínimo/máximo só nos totais de MG.
- **D-028:** partições internas de uma mesma visão não são suprimidas.
- **D-029:** conjunto público versionado (`data/publico/`), modo demonstração e Simulador por totais.
- **D-030:** dados em Releases (público com silver; privado com tudo); no público, nenhuma *estimativa* do modelo por serventia; licença MIT.
- **D-031:** vínculos da RAIS no silver público, só com as colunas que o pipeline usa.
- **D-032:** bronze enxuto (extrato + `original.json`). Os originais ficam fora do projeto, em `C:\radar_arquivo\bronze_originais`. O coletor da RAIS foi corrigido.
- **D-033:** projeto sai do OneDrive para `C:\projetos\radar-seguro-cartorio`; pacotes e originais continuam fora do projeto.
- **D-034:** o painel só lê o banco do pipeline; cenários salvos em `data/painel_estado.json`; o pipeline para se o banco estiver aberto.

## Em andamento e próximos 5 passos
1. Autor aprova o plano do Q4 (e do Q8, do qual ele depende).
2. **Bloco 2, Q8 + Q4:** diagnóstico (só medir), parada, e implementação do que o autor aprovar.
3. Autor faz a conferência de LGPD do zip do silver público e convida os colegas (depois de quarta, 21/10).
4. Restante do diagnóstico do Bloco 2 (Q1 a Q11) e Parada 2.
5. Bloco 3 (premissas do seguro).

## Pendências que dependem do autor
- **Pasta de sessões do Claude Code:** conferir o nome novo (`docs/prompts.md`).
- **Conferência de LGPD do zip do silver público** (`dados-2026-10-19`, já publicado): abrir o zip baixado do Release e conferir que não há nome, CPF, e-mail nem telefone de pessoa física, nem estimativa do modelo por serventia (D-030, D-031).
- **Convite aos colegas, depois de quarta (21/10/2026)** (`docs/publicacao.md`, seção 5; `CONTRIBUTING.md`).
- **Configurar o e-mail "noreply"** do GitHub nos próximos commits.
- **Revisar as regras de estilo do ruff em outra rodada:** hoje o lint usa só as regras `F` (`pyproject.toml`); as regras padrão do ruff acusam cerca de 100 avisos de estilo.
- **`docs/qa/depois/`** (18 MB, fora do git): galeria de QA de uma rodada anterior, com os mesmos 54 nomes de `docs/qa/atual/`, mas imagens diferentes. Foi copiada para a pasta nova; decidir se ainda serve ou se vai para `C:\radar_arquivo`.

## Pendências registradas para etapas futuras (decisões do autor, 2026-10-20)
- **Bloco 2:** avaliar se o pipeline deve gravar também os Parquet de `data/silver` e `data/gold` numa pasta temporária e só trocar no fim, como já faz com o banco. Hoje, se o painel for aberto no meio da carga, o banco fica o anterior, mas os Parquet já são da carga nova (D-034, limitações).
- **Redesenho do painel:** ativar "Salvar cenário" no modo demonstração, agora que os cenários ficam num arquivo separado do banco (D-034).
- **Próxima carga:** a tabela antiga `estado.cenarios_salvos` some do banco real (o pipeline não a cria nem a copia mais; D-034). Não foi apagada à mão.

## Feito pelo autor fora das sessões
- Backup externo de `C:\radar_arquivo\` em `E:\radar_arquivo` (203 arquivos, 0 falhas), com as conversas (2026-10-20).
- `nbstripout --install` neste clone (filtro conferido em 2026-10-20 no `.git/config` e no `.git/info/attributes`).
- VS Code reaberto: o `UV_LINK_MODE=copy` passou a valer nos terminais (conferido em 2026-10-20).

## Onde está cada coisa
- [`docs/SPEC.md`](SPEC.md): especificação (escopo, arquitetura, fases).
- [`docs/decisoes.md`](decisoes.md): decisões D-001 a D-034.
- [`docs/historico/INDICE.md`](historico/INDICE.md): documentos de rodada da Fase 1.
- [`notebooks/README.md`](../notebooks/README.md): regras dos notebooks.
- [`docs/diario.md`](diario.md): o que foi feito e descoberto, com data.
- [`docs/erros_ia.md`](erros_ia.md): erros da IA e do revisor, e as correções.
- [`docs/publicacao.md`](publicacao.md): passo a passo de Releases, `main` protegida e equipe.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md): como a equipe trabalha e baixa os dados.
- [`README.md`](../README.md): como rodar (demonstração, dados públicos, do zero).
- [`docs/prompts.md`](prompts.md): pedidos usados em cada fase.
- [`docs/plano_qualidade_e_correcoes.md`](plano_qualidade_e_correcoes.md): plano do Bloco 2.
