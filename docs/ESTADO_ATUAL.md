# Estado atual do projeto

> Leia primeiro. Atualizado ao fim de cada sessão (regra do `CLAUDE.md`). Última atualização: **2026-10-21**.

## O que é
Radar Seguro-Garantia Cartórios: projeto de portfólio, 100% gratuito e local.
- **Painel:** cartórios de Minas Gerais, com dados públicos reais.
- **Simulador:** mercado de seguro-garantia criado pelo Provimento CNJ 227/2026.
- **Chat com fontes:** ainda por fazer (E5).

## Etapa atual
- **E1 — Qualidade dos dados (plano ainda não aprovado).** O que a etapa pede está no [`ROADMAP.md`](ROADMAP.md), E1.
- **Ramo atual:** `main` (último commit `a5064f4`). O ramo da E1 (ex.: `e1-qualidade`) é criado pelo autor.
- **Próximo passo:** o diagnóstico de Q1 a Q11 da E1 (só leitura), depois do plano aprovado.

## Onde estamos
- **Fase 1 (MG) concluída em 2026-10-20** (`21303e2`), na pasta `C:\projetos\radar-seguro-cartorio` (D-033); `main` protegida (`docs/publicacao.md`, seção 4).
- **Releases:** `dados-2026-10-19` (público), `carga-2026-10-19` e `originais-2026` (privados); o download dos privados foi testado em 2026-10-20 (25/25 tabelas, os 10 números e os 25 originais por SHA-256).
- **Linha de base do "antes" da E1:** `C:\radar_arquivo\baseline_2026-10-20\linha_de_base.json`.
- **Painel só leitura (D-034)** e documentos harmonizados (D-035): o mapa dos documentos está no [`README.md`](README.md) desta pasta.

## Números de referência
Carga **2026-10-19**, premissas **v2**, regra base (Classe 1 até R$ 300 mil, Prov. 243), nível base, regra do STF mantida. Esta tabela é a fonte dos valores; o ROADMAP usa a mesma numeração (1 a 10).

| 1. Serventias ativas | 2. Empregados CLT | 3. Obrigadas (Prov. 227) | 4. Passivo (todas) | 5. Passivo (obrigadas) |
|---|---|---|---|---|
| 2.525 | 12.134 | ≈ 1.121 | R$ 311,9 mi | R$ 238,1 mi |

| 6. Com déficit (esperado) | 7. Déficit | 8. IS do mercado | 9. Prêmio anual | 10. Teto teórico |
|---|---|---|---|---|
| ≈ 486 | R$ 36,9 mi | R$ 18,4 mi | R$ 368,7 mil | R$ 4,76 mi |

Valores exatos na linha de base (`linha_de_base.json`). O conjunto público (`data/publico/manifesto.json`) traz o hash de cada tabela. "Recalcular dá o mesmo" foi provado em 2026-10-19 e de novo em 2026-10-20: 25 de 25 tabelas idênticas.

**Última decisão:** D-035. **Próxima:** D-036 (ver [`decisoes.md`](decisoes.md)).

## O que depende do autor agora
- Revisar a harmonização dos documentos (2026-10-21) e fazer o commit.
- Criar o ramo da E1 e aprovar o plano da E1, quando a IA apresentar.
- As pendências marcadas **[autor]** no [`ROADMAP.md`](ROADMAP.md), §7 (as demais pendências também vivem lá).
