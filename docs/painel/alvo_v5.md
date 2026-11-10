# Alvo do painel: protótipo V5 (D-082)

O [`prototipo_v5.html`](prototipo_v5.html) é a **referência de estrutura** do painel com vários estados. É uma referência, não um contrato: os detalhes visuais serão revistos na Fase 6, com os dados reais na mão. Abra o arquivo no navegador; ele funciona sozinho, sem servidor.

**Dados do protótipo:** Minas Gerais usa os números reais da carga de 07/11/2026 (premissas v4), tirados das funções de `src/painel/analises.py`. Os outros 26 estados e a série de 2016 a 2026 são **simulados** a partir do perfil de MG, só para ver o desenho funcionando. Cartório só por CNS e município (D-038).

## O que vale desde já

Cada bloco do painel (correções de MG, Fase 3, Fase 4) segue esta estrutura:

- **Abas:** Panorama · Mercado do seguro · Quão certo é · Para onde vai · Os cartórios (sub-abas Classes e migração, Arrecadação, Dívida trabalhista) · Simule · Sobre os dados.
- **Barra de recorte** (Estado, Ano, Regra de classe), fixa no topo e válida para todas as abas, com o selo do tipo de dado do recorte.
- **Panorama:** a pergunta central respondida no topo (valor e faixa provável), 6 KPIs com uma linha de contexto e o explorador (mapa, hexágonos, tabela e ranking).
- **Mapa:** bordas dos estados nítidas; escala de cor calculada no recorte, com o zero neutro; rótulos dos 3 maiores; resumo em uma frase. Clicar num estado abre o quadro do estado. Clicar num município abre o quadro dele e a lista de cartórios. Todo mapa que entra num estado tem o botão "Voltar ao Brasil".
- **Ficha do cartório** (por CNS): classe nas duas regras, receita, empregados, passivo, déficit e prêmio esperados.
- **Chat com contexto:** um painel lateral aberto pelo menu ("Pergunte à IA") ou pelo ícone, com tela cheia. Ele sabe a aba, o estado, o município e o cartório abertos, e tem botões "Perguntar sobre este…". As perguntas sugeridas ficam no fim de cada página. O detalhe técnico (Gini, métodos de comparação etc.) vai para o chat.
- **Sobre os dados:** estados no painel, os 10 números oficiais, saúde dos dados, fontes com a data de referência e a de coleta, como foi calculado, classes e limitações.

## O que está em aberto

- Os gráficos de cada aba, as cores e o número de abas: revistos na Fase 6.
- Os textos, que seguem o `padrao_visual.md` e a revisão do autor.

## Ressalvas

1. **Tecnologia.** O protótipo é D3/HTML; o painel é Streamlit. O mapa ligado ao quadro lateral, a barra fixa, os hexágonos e o chat lateral não existem prontos no Streamlit. **A decidir no primeiro bloco de painel**:
   - (a) mapa e explorador como componente HTML dentro do Streamlit, alimentado pelo conjunto público, com o resto (inclusive o chat com o Gemini) em Streamlit nativo; recomendação da IA;
   - (b) Streamlit puro, com o visual aproximado.

   Um site estático fica fora porque pediria hospedagem fora das exceções gratuitas aprovadas.

   **Decidido em 2026-11-10 (D-083): opção (a).** O mapa de "Onde está o mercado" já é o componente (`src/painel/mapa.py`), com a lógica em Python e o JavaScript só desenhando e avisando o clique.
2. **Camada 1 × camada 2.** A Fase 4 publica os 27 estados só na camada 1: cartórios, classe, obrigados, arrecadação. O prêmio e o déficit chegam estado por estado na Fase 6. O painel precisa de um terceiro tipo de estado, "só camada 1", além de real e simulado. A visão do Brasil abre num indicador de camada 1 (por exemplo, % de obrigados), e o mapa de prêmio mostra só os estados com camada 2.
3. **Séries no tempo.** Só a arrecadação e o cadastro do CNJ têm série, e só no período coletado. O passivo, o déficit e o prêmio existem para o ano da RAIS (hoje, 2025).

## Como mudar

Uma mudança no alvo é uma linha nova na D-082 (data, o que mudou e por quê) e, se for grande, um novo protótipo ao lado deste.
