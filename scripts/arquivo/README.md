# Scripts arquivados

Scripts de uso único, guardados para rastreabilidade. Não fazem parte do pipeline nem da suíte de testes.

| Pasta | Data | O que é |
|---|---|---|
| `verificacao_fase1/` | 2026-10-18 | Conferências da verificação final da Fase 1 (`docs/historico/verificacao_final_fase1.md`): silver × CSV do BI do CNJ (F1 a F7), modelo (M1, M2) e a cascata dos números (`cascata.py`, resultado em `cascata.csv`). Os resultados estão em `docs/historico/resposta_verificacao_final_fase1.md` e no `docs/diario.md`. |

Ainda rodam, só leitura, a partir da raiz do projeto (ex.: `uv run python scripts/arquivo/verificacao_fase1/f2_arrecadacao.py`). Sem o CSV do BI (exportado manualmente; só no pacote de dados da equipe), avisam "arquivo ausente" e encerram sem erro.
