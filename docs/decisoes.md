# Registro de decisões

Cada decisão de interpretação ou de modelagem que afeta números do painel ou do chat. Mais recente no topo.
O `docs/diario.md` conta o que aconteceu; este arquivo explica **por que** cada escolha foi feita.

Formato:

```
## D-NNN — título
- **Data:**
- **Contexto:**
- **Opções:**
- **Decisão:**
- **Justificativa:**
- **Consequências / onde aparece:**
- **Fonte:**
```

---

## D-002 — Limite da Classe 1: R$ 300 mil (Prov. 243) × R$ 100 mil (Prov. 213 original)
- **Data:** 2026-10-17
- **Contexto:** o Prov. 227 entrou em vigor em 10/08/2026. Nessa data, o limite da Classe 1 era a receita semestral de até R$ 100.000,00 (art. 16, I, do 213 original). O Prov. 243 elevou o limite para R$ 300.000,00 de receita bruta semestral e entrou em vigor em 22/08/2026 (art. 2º do 243: 30 dias após a publicação no DJe de 23/07/2026). A entrega do 1º ciclo venceu por volta de 09/09/2026, já sob o 243. O texto não diz qual versão vale para o 1º ciclo.
- **Opções:**
  1. R$ 100 mil, a regra vigente na entrada em vigor do 227;
  2. R$ 300 mil, a regra vigente no prazo de entrega do 1º ciclo e hoje;
  3. as duas, uma como base e a outra como sensibilidade.
- **Decisão:** opção 3. **Base `v2` = R$ 300 mil** (Prov. 243) e **sensibilidade `v1` = R$ 100 mil**. As duas versões ficam em `config/regras_classificacao.yaml`, com as datas de vigência.
- **Justificativa:** a regra vigente no prazo de entrega e nos ciclos anuais seguintes é a do 243. Mostrar a versão anterior deixa visível o tamanho do efeito da mudança.
- **Consequências / onde aparece:**
  - o pipeline calcula as duas versões e registra a **diferença de universo** (nº de serventias, passivo) e de **mercado** (IS, prêmio) no diário e na página Qualidade dos dados;
  - a classificação é marcada como **aproximada**, porque a receita bruta do art. 2º, XXIV do 213 (inclui o ressarcimento de atos gratuitos e a complementação de renda mínima; deduz os valores de terceiros e os repasses legais) pode não coincidir com a arrecadação publicada nas fontes públicas;
  - os limites são atualizados todo ano (art. 16, §2º, do 213). Cada atualização vira uma nova versão, e a divulgação entra na lista de monitoramento do radar.
- **Fonte:** Prov. 213/2026, art. 2º, XXIV, e art. 16 (texto compilado); Prov. 243/2026, art. 2º; Prov. 227/2026, arts. 18 a 20. Cópias em `data/bronze/normas/2026-10-17/`.

## D-001 — "Classe I" (art. 19 do 227) = Classe 1 do Prov. 213
- **Data:** 2026-10-17
- **Contexto:** o art. 19 do Prov. 227 exclui "as serventias extrajudiciais enquadrada[s] na Classe I do Provimento nº 213/2026". O 213 numera as classes em algarismos arábicos (Classe 1, 2 e 3) e usa letras para as subclasses (A a J). Uma dessas subclasses é a **Subclasse I**, dentro da Classe 3: receita acima de 6 e até 12 vezes o teto da Classe 2.
- **Opções:**
  1. "Classe I" = Classe 1, as menores serventias;
  2. "Classe I" = Subclasse I da Classe 3, serventias grandes.
- **Decisão:** opção 1.
- **Justificativa:**
  - o art. 19 diz "Classe", e não "Subclasse";
  - o algarismo romano I equivale ao arábico 1;
  - excluir as menores serventias está de acordo com a lógica de proporcionalidade do 213 (art. 2º, III; art. 16, §4º);
  - a opção 2 isentaria uma faixa intermediária de serventias grandes, o que não tem lógica regulatória aparente.
- **Consequências / onde aparece:** `universo()` exclui a Classe 1. A interpretação é citada no chat quando a pergunta envolver as exclusões. Se uma norma ou decisão posterior esclarecer o ponto, esta decisão é revista (monitorado pelo radar).
- **Fonte:** Prov. 227/2026, art. 19; Prov. 213/2026, art. 16 (texto compilado).
