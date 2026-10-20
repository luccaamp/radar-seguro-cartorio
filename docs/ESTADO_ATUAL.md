# Estado atual do projeto

> Leia primeiro. Atualizado ao fim de cada sessão (regra do `CLAUDE.md`). Última atualização: **2026-10-19**.

## O que é
Radar Seguro-Garantia Cartórios: projeto de portfólio, 100% gratuito e local.
- **Painel:** cartórios de Minas Gerais, com dados públicos reais.
- **Simulador:** mercado de seguro-garantia criado pelo Provimento CNJ 227/2026.
- **Chat com fontes:** ainda por fazer.

## Onde estamos
- **Fase 1 (painel de MG): concluída**, com o repositório reproduzível publicado na `main` (`be27786`).
- **Agora:** limpeza do projeto (`docs/limpeza_projeto.md`), branch **`limpeza-fase1`**.
  - Feitos: os ajustes rápidos (seção 2) e o inventário (Etapa 1).
  - Aguarda a aprovação do autor na **Parada 1**.
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
- **D-032 (proposta, aguarda o autor):** bronze enxuto, com extrato e registro do original.

## Em andamento e próximos 5 passos
1. Autor revisa o inventário da limpeza (Parada 1) e aprova item a item. Também decide a conversão das conversas da Fase 1 e a D-032.
2. Etapa 2 da limpeza: mover docs de rodada para `docs/historico/`, arquivar scripts de uso único, criar `notebooks/` e mover dados não usados para `C:\radar_arquivo\`. Provas ao final: 25/25 tabelas, números iguais e as três suítes.
3. Autor faz o commit da limpeza, regera os pacotes em `C:\radar_pacotes\` e publica os Releases (`docs/publicacao.md`).
4. Autor protege a `main` e convida a equipe (`CONTRIBUTING.md`).
5. Bloco 2 do plano de qualidade.

## Pendências que dependem do autor
- **Parada 1 da limpeza:** aprovar os itens, a D-032 e a pasta `notebooks/`.
- **Conversas:** aprovar a conversão das sessões da Fase 1 para `conversas/`.
- **Releases** público e privado, proteção da `main` e convites (`docs/publicacao.md`).
- **Backup externo** de `C:\radar_arquivo\` depois que os originais do bronze forem movidos (se a D-032 for aprovada).
- **Configurar o e-mail "noreply"** do GitHub nos próximos commits.

## Onde está cada coisa
- [`docs/SPEC.md`](SPEC.md): especificação (escopo, arquitetura, fases).
- [`docs/decisoes.md`](decisoes.md): decisões D-001 a D-031.
- [`docs/diario.md`](diario.md): o que foi feito e descoberto, com data.
- [`docs/erros_ia.md`](erros_ia.md): erros da IA e do revisor, e as correções.
- [`docs/publicacao.md`](publicacao.md): passo a passo de Releases, `main` protegida e equipe.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md): como a equipe trabalha e baixa os dados.
- [`README.md`](../README.md): como rodar (demonstração, dados públicos, do zero).
- [`docs/prompts.md`](prompts.md): pedidos usados em cada fase.
- [`docs/plano_qualidade_e_correcoes.md`](plano_qualidade_e_correcoes.md): plano do Bloco 2.
