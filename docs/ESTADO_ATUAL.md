# Estado atual do projeto

> Leia primeiro. Atualizado ao fim de cada sessão (regra do `CLAUDE.md`). Última atualização: **2026-10-19**.

## O que é
Radar Seguro-Garantia Cartórios: projeto de portfólio, 100% gratuito e local.
- **Painel:** cartórios de Minas Gerais, com dados públicos reais.
- **Simulador:** mercado de seguro-garantia criado pelo Provimento CNJ 227/2026.
- **Chat com fontes:** ainda por fazer.

## Onde estamos
- **Fase 1 (painel de MG): concluída**, com o repositório reproduzível publicado na `main` (`be27786`).
- **Agora:** limpeza do projeto (`docs/historico/limpeza_projeto.md`), branch **`limpeza-fase1`**.
  - Feitos: a Etapa 2 inteira (docs, scripts, código, dependências, notebooks, dados locais e o bronze enxuto da D-032).
  - Aguarda a revisão do autor na **Parada 2** e o commit.
- **Depois:** Bloco 2 do `docs/plano_qualidade_e_correcoes.md` e, em seguida, a Fase 2 do SPEC (Brasil inteiro).

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
- **D-032:** bronze enxuto (extrato + `original.json`). Os originais ficam fora do OneDrive, em `C:\radar_arquivo\bronze_originais`. O coletor da RAIS foi corrigido.

## Em andamento e próximos 5 passos
1. Autor revisa a Parada 2 da limpeza e faz o commit na `limpeza-fase1` (e o merge na `main`).
2. Autor publica os Releases a partir de `C:\radar_pacotes\`: o público (2,7 MB) e o da equipe com originais (≈ 9,8 GB) ou enxuto (≈ 85 MB). Ver `docs/publicacao.md`.
3. Autor protege a `main` e convida a equipe (`CONTRIBUTING.md`).
4. Backup externo de `C:\radar_arquivo\`, que é a única cópia local dos originais.
5. Bloco 2 do plano de qualidade (`docs/plano_qualidade_e_correcoes.md`).

## Pendências que dependem do autor
- **Commit da limpeza** e conversão desta sessão (`784e4eca`) para `conversas/`, ao fim dela.
- **Releases** público e privado, proteção da `main` e convites (`docs/publicacao.md`).
- **Backup externo** de `C:\radar_arquivo\` (originais do bronze e linha de base da limpeza).
- **`nbstripout --install`** no seu clone (uma vez), antes do primeiro notebook com saída.
- **Configurar o e-mail "noreply"** do GitHub nos próximos commits.
- **Revisar as regras de estilo do ruff em outra rodada:** hoje o lint usa só as regras `F` (`pyproject.toml`); as regras padrão do ruff acusam cerca de 100 avisos de estilo.
- **Pastas vazias** que o OneDrive não deixou apagar (ignoradas pelo git): `pacotes/`, `docs/qa/antes/`, `data/publico.antigo/`, `data/publico.novo/`.

## Onde está cada coisa
- [`docs/SPEC.md`](SPEC.md): especificação (escopo, arquitetura, fases).
- [`docs/decisoes.md`](decisoes.md): decisões D-001 a D-032.
- [`docs/historico/INDICE.md`](historico/INDICE.md): documentos de rodada da Fase 1.
- [`notebooks/README.md`](../notebooks/README.md): regras dos notebooks.
- [`docs/diario.md`](diario.md): o que foi feito e descoberto, com data.
- [`docs/erros_ia.md`](erros_ia.md): erros da IA e do revisor, e as correções.
- [`docs/publicacao.md`](publicacao.md): passo a passo de Releases, `main` protegida e equipe.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md): como a equipe trabalha e baixa os dados.
- [`README.md`](../README.md): como rodar (demonstração, dados públicos, do zero).
- [`docs/prompts.md`](prompts.md): pedidos usados em cada fase.
- [`docs/plano_qualidade_e_correcoes.md`](plano_qualidade_e_correcoes.md): plano do Bloco 2.
