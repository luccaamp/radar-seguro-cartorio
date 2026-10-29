# Recados para a Letícia (do painel, terceira rodada da Etapa 3, D-051)

29/10/2026. O painel foi enxugado para responder a uma pergunta só ("quanto dinheiro o seguro pode movimentar em MG, e
quão certo é esse número?"). O que saiu do painel vai para o chat: **o painel é a história; o chat é o detalhe.** Tabela
completa em `docs/painel/corte.md`. Nenhum arquivo do chat foi mudado, salvo o item 3.

## 1. Pergunta preenchida pelo link (pede mudança na página do chat)

Cada página do painel termina com 2 ou 3 perguntas sugeridas. Elas são links para `Chat?pergunta=<texto>` (HTML
relativo, `src/painel/ui.py`, `link_chat`). **A página do chat ainda não lê o parâmetro.** Sugestão, no topo da
`aba_chat()`:

```python
pedida = st.query_params.get("pergunta")
if pedida and not st.session_state.get("chat_pergunta_do_link_usada"):
    st.session_state["chat_pergunta_do_link_usada"] = True
    pergunta = pedida          # e seguir como uma sugestão clicada
```

O link recarrega a página (o `st.page_link` não funciona quando a página roda sozinha nos testes), então o histórico da
conversa começa vazio. As 15 perguntas sugeridas estão nas páginas (`ui.sugestoes([...])`); vale conferir se o modelo
responde todas (algumas estão no gabarito, como a do lucro da seguradora).

## 2. O que foi para o chat e as ferramentas ainda não respondem

Conferi cada item que saiu do painel contra `CONSULTAS` (`src/agent/ferramentas.py`). Estes não têm ferramenta (as
funções do painel continuam onde estavam; nenhuma foi apagada):

| O que saiu do painel | Onde estava | Dado (tabela) | Sugestão |
|---|---|---|---|
| Recorte regional por atribuição, situação ou classe (mapa e totais do filtro) | Mercado | `gold.mercado_filtro_area`, `mercado_filtro_uf`, `mercado_filtro_regiao` | ferramenta nova em `consultar_mercado`; o `contar_serventias` só conta em MG |
| Tabela por área e ranking das 15 maiores (déficit, passivo, serventias, CLT) e a parte de cada área no total | Mercado | `gold.mercado_area_publico`, `ranking_municipio_publico` | idem; o `consultar_serventia` lista os cartórios de um município, mas não a área agregada nem a posição |
| Regra da Classe 1 em R$ 100 mil (v1) × R$ 300 mil (v2) | Mercado e Qualidade | `gold.diferenca_regra_classe`, `fato_mercado_uf` (regra v1) | parâmetro `regra` no `deficit_e_mercado` (o `_uf_linhas` já aceita) |
| Conferência entre fontes, checagem por checagem, e o gráfico CNJ × RAIS com as maiores diferenças | Qualidade | `qualidade.reconciliacoes`, `qualidade.rec_municipio` | o `qualidade_fontes` dá só o placar (ok × aviso) |
| Sensibilidades antigas: método de rateio, premissas do passivo (INPC, reserva), distribuição salário × tempo | Qualidade | `gold.sensibilidade_rateio`, `sensibilidade_premissas`, `qualidade.resumo_publico` | ferramenta em `consultar_qualidade` |
| As 13 limitações declaradas (o painel agora mostra 5) | Qualidade | texto no código antigo (`git show HEAD:app/pages/3_Qualidade_dos_dados.py`) | levar para o prompt ou para uma consulta de texto, como as normas |
| Simulador completo (premissas do déficit, passivo e STF; seguradora hipotética) | Simulador | `app/simulador.py` (fora da navegação) | o `simular` cobre taxa e market share |

## 3. Mudei um teste seu: `tests/test_chat_cobertura.py`

Em `test_toda_analise_das_paginas_chega_ao_chat`, o piso de "pelo menos 15 análises usadas pelas páginas" virou 5: o
painel enxuto usa 7 de propósito (`faixa_d042`, `numeros_oficiais`, `tornado`, `concentracao`, `grupos`,
`previsao_mercado`, `qualidade_fontes`). Só o número mudou; o resto do teste é o mesmo. Se preferir outro piso, ajuste.

## 4. Coisas do painel que tocam o chat

- **STF fora do painel:** a ADI 8015 e os cenários do STF saíram de todas as páginas; o chat passa a ser o único
  lugar (`situacao_adi`, `premio_por_cenario_stf`). Na véspera da demo, a data da conferência em `config/painel.yaml`
  continua valendo para o chat.
- **Tema novo** (`.streamlit/config.toml`): `primaryColor` mudou de `#1f4e86` para `#3366e6`; o `chat.css` lê a cor do
  tema, então o campo de digitação e as abas do chat mudam junto. Contraste do `#3366e6` sobre o branco: 5,0:1.
- **`ui.contexto` continua** (só o chat usa), com o mesmo HTML; o estilo ficou mais claro. `ui.cabecalho` mudou de
  assinatura (`titulo, subtitulo, sobre`): se for usar no chat, é o cabeçalho compacto que você sugeria (recado 3 do
  `recados_lucca.md`), sem etiquetas.
- **Legendas:** a regra `opacity: 1` das legendas (seu recado 2) foi para o `estilo.css` do painel inteiro.
- **`comum.rodape` não mudou** (o chat e o Simulador usam). As páginas da história usam o novo `comum.fonte_linha`
  (só a fonte e a data).
- **`tests/apoio_painel.py`:** `PAGINAS` agora tem as 5 páginas novas, o chat e `app/simulador.py`; constantes novas
  `HISTORIA`, `SOBRE`, `MERCADO` e `SIMULADOR`.
