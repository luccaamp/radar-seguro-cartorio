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

## Linha de base (preencher ANTES de começar o projeto)

Medida do "antes", usada na comparação final dos slides. Faça a tarefa manualmente e cronometre.

- **Tarefa medida:** (ex.: descobrir o que mudou na regulação de cartórios esta semana e estimar quantos cartórios de MG seriam afetados)
- **Data:**
- **Tempo gasto:**
- **Fontes consultadas:**
- **O que foi difícil:**

---

## 2026-10-17 — Decisões finais da Sessão 0
- **O que foi feito:** o SPEC foi atualizado com as respostas do autor e houve commit local (sem push).
- **Decisões:**
  - A taxonomia de `tipo_evento` foi aprovada como proposta (SPEC §5.1).
  - O MotherDuck foi escolhido para o estado operacional e para o gold no deploy. A Fase 0 só valida a conexão (local, GitHub Actions e Streamlit Cloud) e os limites do plano free.
  - BigQuery: só a cota gratuita, sempre com `maximum_bytes_billed`.
  - Python: instalar o `uv` e o Python 3.12 pelo `uv`, sem mexer no Python 3.13.3 do sistema.
  - Linha de base: o autor já mediu e vai preencher a seção ele mesmo. Isso não bloqueia a Fase 0.
  - `docs/plano_radar_seguro_cartorio.html` foi removido de propósito, porque era uma duplicata do SPEC.
- **Pendências do autor** (vieram como campos sem resposta):
  - se o projeto GCP já existe ou ainda vai ser criado;
  - canal do resumo diário: e-mail ou Slack;
  - data da entrevista;
  - orçamento máximo de LLM e BigQuery somados.
- **Próximo passo:** Fase 0, quando o autor liberar.

## 2026-10-17 — Revisão do SPEC antes da Fase 0
- **O que foi feito:** a IA leu o SPEC e apontou ambiguidades, decisões pendentes e riscos. O autor respondeu e o SPEC foi reescrito com as decisões. Também foi conferido o ambiente: repositório git com remote `luccaamp/radar-seguro-cartorio`, Python 3.13.3 no sistema e `uv` ainda não instalado.
- **Fatos verificados pelo autor (a IA não tinha esses fatos e vai confirmá-los na Fase 0 em atos.cnj.jus.br):**
  - o Prov. 227/2026 foi publicado em 11/06/2026 e está em vigor desde 10/08/2026;
  - o Prov. 243/2026 (jul/2026) alterou as classes do 213;
  - a ADI 8015 foi ajuizada pela ANOREG em set/2026 contra os arts. 8º a 17, relator Min. Flávio Dino;
  - no primeiro ano, a declaração venceu 30 dias após a vigência. Depois, o ciclo é anual (base 31/12, entrega até 31/03);
  - o passivo é o cenário de demissão de todos os empregados sem justa causa.
- **Decisões:**
  - Déficit: duas premissas separadas, `prob_deficit` e `pct_descoberto`.
  - Demanda: uma premissa única `escolha_garantia` com três parcelas que somam 100% (bens próprios / fiança / seguro). O fator "adesão" saiu da receita.
  - Receita = IS × taxa × market share, anual e recorrente. O market share é de uma seguradora hipotética (`fonte: suposição`), e o mercado total aparece sempre ao lado.
  - Resultado técnico = prêmio − sinistro − comissão − despesa administrativa. O teste de monotonicidade vale para o prêmio emitido.
  - O passivo é rateado sobre todas as serventias do município. Os interinos e a Classe I são excluídos depois.
  - A classe indeterminada fica fora no `min`, dentro no `max`, e o `base` usa a premissa `peso_classe_indeterminada_base`.
  - Períodos: usar o dado mais recente de cada fonte, com a `data_referencia` exibida no dashboard. A correção salarial da RAIS é premissa.
  - Premissas: o YAML é a semente no git, e as versões aprovadas ficam no banco (`premissas_versoes`).
  - `cenarios_stf.yaml` guarda as definições fixas. `cenarios_salvos` guarda as combinações do usuário.
  - O local do gold no deploy é decidido na Fase 0, junto com o armazenamento.
  - O `make` foi trocado por `uv run pipeline.py`. "Do zero" significa a partir dos snapshots do bronze.
  - A data da chave de dedup é a publicação do ato original. A citação é normalizada antes da comparação. O gabarito do chat fixa a versão das premissas.
  - O gabarito do radar precisa de pelo menos 10 documentos relevantes, completando com normas anteriores do setor se faltar.
  - LGPD: nome e CPF são descartados na passagem bronze → silver, e o limiar de agregação é de 3 serventias.
  - O projeto continua no OneDrive (decisão do autor). O risco foi registrado no SPEC §10.
  - BigQuery: sempre filtrar por CNAE e ano, com `maximum_bytes_billed`.
  - Radar: o texto coletado fica isolado no prompt e a saída é validada (prompt injection).
  - Mínimo da demo: Mercado e Simulador de MG, o radar detectando um evento real e a aprovação mudando o simulador. O chat é bônus e virou o primeiro item da ordem de corte.
- **Suposições:** o desenho do produto (tomador pessoa física, segurado indefinido) é tratado como premissa e como limitação no README.
- **Limitações encontradas:** o corte de conhecimento da IA é anterior às normas, então todo artigo precisa ser confirmado no texto oficial.
- **Pendências do autor:**
  - contas disponíveis: GCP e MotherDuck ou Supabase. A Claude API ainda não está disponível;
  - canal do resumo diário: Slack ou e-mail;
  - data da entrevista e orçamento de LLM e BigQuery;
  - aprovar a taxonomia de `tipo_evento` (SPEC §5.1);
  - preencher a seção "Linha de base" acima, que ainda está vazia.
- **Observação:** `docs/plano_radar_seguro_cartorio.html` aparece como apagado no git, e não foi a IA que apagou. É preciso confirmar se a remoção foi intencional.
- **Próximo passo:** Fase 0, depois de aprovada esta revisão.

## AAAA-MM-DD — Início do projeto
- **O que foi feito:** SPEC, CLAUDE.md e estrutura de documentação criados.
- **Decisões:** desenvolvimento por fases, começando pela Fase 0 (viabilidade das fontes).
- **Suposições:** nenhuma ainda.
- **Limitações encontradas:** nenhuma ainda.
- **Próximo passo:** Fase 0.
