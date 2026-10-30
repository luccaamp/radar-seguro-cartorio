# Correções objetivas + QA visual automático — fechamento da Fase 1

> **Para o Claude Code.** Este documento **substitui** o `auditoria_painel_v3.md` (não execute aquele). O escopo é curto:
> 1. aprovações e decisões;
> 2. quatro correções objetivas;
> 3. montar ferramentas de **QA visual automático** para eu revisar o painel por prints gerados sempre no mesmo estado, em vez de PDFs exportados à mão.
>
> **Fora do escopo agora:** redesenho do layout (será feito depois, a partir de um modelo que eu vou escolher), Bloco 2 e qualquer mudança de número.
>
> Nada de commit ou push. Modo de trabalho: diga o que vai fazer, faça, pare no fim com o relatório da seção 6.

---

## 1. Aprovações e decisões

1. **D-027 aprovada** como está: por área, só base e v2; v1, mínimo e máximo só nos totais de MG. Marque APROVADA em `docs/decisoes.md`.
2. **D-028 (nova): partições internas de uma mesma visão não serão suprimidas.**
   - Exemplo: numa área, "passivo (todas)" − "passivo (obrigados)" dá o passivo das não obrigadas.
   - **Motivo:** os insumos são públicos (contagens, empregados declarados e arrecadação do CNJ), e a limitação D2 já declara que a estimativa de cada cartório é recalculável a partir deles. A defesa do projeto é tratar-se de **estimativa de mercado com premissas públicas**.
   - O auditor de ataque por diferença que já existe **continua como está**, sem ampliar.
   - Registrar a D-028 e acrescentar uma frase à limitação D2 citando-a.
3. **Pacotes aprovados (só de desenvolvimento):** `playwright` (baixar **só o Chromium**) e `axe-playwright-python`. Use `uv add --dev`. Nenhum outro pacote sem me perguntar.
4. **Registros (só acréscimos):**
   - **Limitações:** "Ataques combinando 3 ou mais visões não são auditados; o auditor cobre pares de visões e o resto das partições dos filtros."
   - **SPEC, Fase 3:** "As ferramentas do chat devolvem só as visões públicas já auditadas, nunca SQL livre; v1, mínimo e máximo só nos totais de MG."
   - **SPEC, Fase 2:** "Medir o tempo do auditor com as 27 UFs."

---

## 2. Correções objetivas (só estas)

Nas exportações da carga das 20:31, estes quatro problemas continuam visíveis. Os testes estruturais (`fig.to_dict()`) passaram, mas a tela não mudou. Por isso, **cada correção só conta como feita depois de conferida no print da seção 3.**

| # | Problema | Onde aparece | Correção esperada |
|---|---|---|---|
| C1 | A **maior barra do ranking** fica sem rótulo; na indeterminada, as 3 primeiras ocupam a largura toda e o rótulo sai "R" | Ranking em todas as visões | Eixo de 0 até máx × 1,18, `cliponaxis=False`, rótulo fora da barra e margem direita suficiente |
| C2 | **Mapa sem barra de escala de cores** | Todas as visões de mapa | Escala visível dentro da figura, com título curto e marcas formatadas em R$ ou contagem ("≥" quando satura) |
| C3 | **Colunas fora da área visível:** "Prêmio" (tabela Faixas), "Déficit" (tabela por área/região), "Posição" (tabela de posições do filtro de município) | Mercado | Tudo cabe em 1280 px de largura. Se for preciso, tire a coluna "Tipo" (o nome "RI …" / "Int. …" já diz o tipo) ou leve "Passivo (todas)" para o "?" da Faixas |
| C4 | Nome com acento errado: **"Int. Juíz de Fora"** (o "RI Juiz de Fora" sai certo) | Rankings e tabelas por região | Descobrir a origem (API do IBGE ou código). Se vier do IBGE, corrigir por `config/correcoes_nomes.yaml` (com a evidência), sem tocar no bronze. Teste: nenhum nome público difere do nome do município-sede do IBGE só por acento |

**Os números não podem mudar.** Referência: 2.525 · 12.134 · ≈ 1.121 · R$ 311,9 mi · R$ 238,1 mi · ≈ 486 · R$ 36,9 mi · R$ 18,4 mi · R$ 368,7 mil · teto R$ 4,76 mi.

---

## 3. QA visual automático (camadas 2, 3 e 4)

### 3.1 Galeria de prints — `scripts/prints_painel.py`
- O script **sobe o Streamlit sozinho** numa porta livre, abre o painel com o Playwright (Chromium), percorre os **estados fixos** abaixo, tira um print de página inteira de cada um e **encerra o servidor** no fim.
- Para cada estado, tira o print em **1280 × 800** e **1920 × 1080**.
- Gera `docs/qa/galeria.html`, uma página com todos os prints em grade, cada um com o nome do estado, a largura e a data e hora. Eu abro essa página no navegador para revisar.
- `docs/qa/` fica no `.gitignore`.
- O script é **reutilizável**: vou rodar de novo a cada mudança e na Fase 5, para os slides.

**Estados fixos (sem nenhuma interação manual de zoom):**
1. Início
2. Mercado sem filtro × as 4 métricas (Déficit, Passivo, Serventias, Empregados)
3. Mercado com Classe = 1, 2, 3, indeterminada
4. Situação = Provida; Situação = Vaga
5. Atribuição = Notas; Atribuição = Registro de Imóveis
6. Município = Belo Horizonte; Município = Almenara; um município pequeno (agregado); Campo Azul
7. Município = Belo Horizonte + Classe 3
8. Regra "R$ 100 mil" sem filtro
9. Simulador padrão; taxa 3,0%; cenário "STF suspende"; cenário "Decisão parcial"
10. Qualidade: topo, gráfico CNJ × RAIS e Limitações

### 3.2 Checagens automáticas de layout — `tests/test_visual.py`
Marcar com `@pytest.mark.visual`, **fora da suíte padrão** (rodar com `uv run pytest -m visual`). Em cada estado e largura, verificar no navegador, pela página renderizada (DOM), e não pelo `fig.to_dict()`:
- **texto cortado:** nenhum elemento de texto visível com `scrollWidth > clientWidth` (rótulos, cabeçalhos, KPIs);
- **tabelas:** a última coluna de cada tabela está dentro da área visível do contêiner;
- **ranking:** todas as barras têm rótulo, e o rótulo está dentro da área do gráfico;
- **mapa:** a barra de escala de cores existe e está visível;
- **filtro de município:** o polígono do município está inteiro dentro do enquadramento do mapa;
- **erros:** nenhuma caixa de erro do Streamlit na página, e nenhum erro no console do navegador.

Cada falha mostra **estado, largura, elemento e motivo**.

### 3.3 Acessibilidade — `scripts/acessibilidade.py`
- Rodar o **axe** (`axe-playwright-python`) em cada página (Início, Mercado sem filtro, Simulador, Qualidade).
- Gerar `docs/qa/acessibilidade.md` com as violações por gravidade (critical, serious, moderate, minor), cada uma com o elemento afetado.
- **Corrigir só as de contraste de texto e de rótulo ausente** que estejam em código **nosso** (não nas entranhas do Streamlit). Listar o resto como sugestão.

### 3.4 Fluxo desta rodada
1. Instalar os pacotes (seção 1.3).
2. Rodar a galeria e as checagens **antes** de corrigir. Guardar em `docs/qa/antes/`.
3. Corrigir C1 a C4.
4. Rodar de novo. Guardar em `docs/qa/depois/`.
5. A suíte padrão e `-m visual` passando.

---

## 4. Regras de sempre

- `CLAUDE.md` acima de tudo.
- Não apagar nada. Docs só com acréscimos.
- Testes na cópia do banco. Conferir o banco real e os Parquet **antes e depois** da suíte.
- O script de prints lê o banco **só para leitura** e não grava nada em `data/`.
- O Streamlit que eu uso fica fechado durante o trabalho. O script sobe e derruba o próprio.

---

## 5. Fora do escopo (não fazer agora)

- Mudanças de layout ou design além de C1–C4 (o redesenho virá depois, com um modelo de referência).
- Teste de regressão visual por comparação de imagem (fica para depois que eu aprovar a versão final).
- Bloco 2.

---

## 6. Relatório ao fim (e PARE)

1. Aprovações e registros feitos (D-027, D-028, pacotes, Limitações, SPEC).
2. C1–C4: o que mudou, arquivo e teste, e **o nome do print "depois"** que mostra a correção.
3. Resultado das checagens de layout: falhas **antes** × **depois** (tabela curta).
4. Resumo da acessibilidade: quantas violações por gravidade, o que foi corrigido e o que ficou como sugestão.
5. Prova: suíte padrão e `-m visual` passando; banco real e Parquet intactos; números da seção 2 iguais.
6. Como eu rodo sozinho: os comandos exatos para gerar a galeria e as checagens.
7. Arquivos A/M e sugestão de mensagem de commit.

**Pare. Não comece o Bloco 2. Nada de commit ou push.**
