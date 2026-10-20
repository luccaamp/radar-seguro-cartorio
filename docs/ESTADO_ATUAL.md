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
- **Pasta do projeto:** sai do OneDrive para **`C:\projetos\radar-seguro-cartorio`** (D-033). Até a mudança ser feita pelo autor, o projeto ainda está no caminho antigo.
- **Próximo:** Bloco 2, começando pelo **Q4** (receita bruta).

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

## Em andamento e próximos 5 passos
1. Autor faz o commit do fechamento da Fase 1 (esta rodada).
2. Autor muda o projeto para `C:\projetos\radar-seguro-cartorio` (D-033): clone novo, cópia do que não está no git com `robocopy` e `uv sync` (lista no relatório de 2026-10-20, `docs/diario.md`).
3. Autor faz a conferência de LGPD do zip do silver público e convida os colegas (depois de quarta, 21/10).
4. Backup externo de `C:\radar_arquivo\`, que é a única cópia local dos originais.
5. **Bloco 2, item Q4** (receita bruta), na pasta nova.

## Pendências que dependem do autor
- **Commit** desta rodada (fechamento da Fase 1).
- **Mudança de pasta** para `C:\projetos\radar-seguro-cartorio` (D-033). Depois dela, conferir o nome novo da pasta de sessões do Claude Code (`docs/prompts.md`) e tirar de `.claude/settings.local.json` as duas permissões com o caminho antigo.
- **Conferência de LGPD do zip do silver público** (`dados-2026-10-19`, já publicado): abrir o zip baixado do Release e conferir que não há nome, CPF, e-mail nem telefone de pessoa física, nem estimativa do modelo por serventia (D-030, D-031).
- **Convite aos colegas, depois de quarta (21/10/2026)** (`docs/publicacao.md`, seção 5; `CONTRIBUTING.md`).
- **Backup externo** de `C:\radar_arquivo\` (originais do bronze e linha de base da limpeza).
- **`nbstripout --install`** no seu clone (uma vez), antes do primeiro notebook com saída.
- **Configurar o e-mail "noreply"** do GitHub nos próximos commits.
- **Revisar as regras de estilo do ruff em outra rodada:** hoje o lint usa só as regras `F` (`pyproject.toml`); as regras padrão do ruff acusam cerca de 100 avisos de estilo.
- **`docs/qa/depois/`** (18 MB, fora do git): galeria de QA de uma rodada anterior, com os mesmos 54 nomes de `docs/qa/atual/`, mas imagens diferentes. Decidir se ainda serve ou se vai para `C:\radar_arquivo` em vez de ser copiada para a pasta nova.

## Onde está cada coisa
- [`docs/SPEC.md`](SPEC.md): especificação (escopo, arquitetura, fases).
- [`docs/decisoes.md`](decisoes.md): decisões D-001 a D-033.
- [`docs/historico/INDICE.md`](historico/INDICE.md): documentos de rodada da Fase 1.
- [`notebooks/README.md`](../notebooks/README.md): regras dos notebooks.
- [`docs/diario.md`](diario.md): o que foi feito e descoberto, com data.
- [`docs/erros_ia.md`](erros_ia.md): erros da IA e do revisor, e as correções.
- [`docs/publicacao.md`](publicacao.md): passo a passo de Releases, `main` protegida e equipe.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md): como a equipe trabalha e baixa os dados.
- [`README.md`](../README.md): como rodar (demonstração, dados públicos, do zero).
- [`docs/prompts.md`](prompts.md): pedidos usados em cada fase.
- [`docs/plano_qualidade_e_correcoes.md`](plano_qualidade_e_correcoes.md): plano do Bloco 2.
