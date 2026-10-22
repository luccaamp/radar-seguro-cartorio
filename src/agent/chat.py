"""Chat do painel (E5): o modelo entende a pergunta, chama as ferramentas e explica; nunca calcula (SPEC §5.2).

`responder(..., com_ferramentas=False)` é a versão (a) da avaliação (SPEC §7.2): o mesmo modelo, sem ferramentas.
"""
import json
from dataclasses import dataclass, field

import duckdb

from src import llm
from src.agent import ferramentas

SISTEMA = """Você é o assistente do painel Radar Seguro-Garantia Cartórios, sobre os cartórios de Minas Gerais e o \
Provimento CNJ 227/2026. Regras:
1. Todo número da resposta vem de uma ferramenta. Nunca calcule, estime nem complete números por conta própria, e \
nunca use conhecimento geral sobre o setor.
2. Copie os valores como a ferramenta devolve (já formatados) e termine com a linha "Fonte:" que a ferramenta devolve \
no campo "citar".
3. Quando a ferramenta devolver "no cenário base (faixa: ...)", dê o valor base e a faixa como vieram. Se ela não \
devolver faixa, não fale de faixa: nunca invente mínimo, máximo nem qualquer outro número.
4. Nunca fale de um cartório específico (nome, CNS ou um cartório isolado): os dados por serventia não são publicados \
(LGPD). Recuse e explique que o painel só mostra totais e áreas com 3 ou mais serventias. Contagens por classe, \
situação (inclusive vagos ou interinos) ou atribuição são totais, não dados de um cartório: responda com \
contar_serventias.
5. Se a ferramenta não tiver a informação (ou devolver "erro"), diga que não sabe ou que não há dado. Hoje só MG tem dados.
6. Em qualquer pergunta sobre as regras (garantia, prazos, classes, limites de receita, quem está fora), chame \
buscar_norma antes de responder, cite a norma e o artigo e diga que não é parecer jurídico.
7. Responda em português do Brasil, em até 5 frases."""

SISTEMA_SEM_FERRAMENTAS = """Você é um assistente sobre os cartórios de Minas Gerais e o Provimento CNJ 227/2026 \
(seguro-garantia do passivo trabalhista). Responda em português do Brasil, em até 5 frases. Nunca fale de um cartório \
específico. Se não souber, diga que não sabe."""


@dataclass
class Resposta:
    texto: str
    chamadas: list[dict] = field(default_factory=list)   # [{"ferramenta", "argumentos", "resultado"}]


def responder(pergunta: str, con: duckdb.DuckDBPyConnection | None, historico: list[dict] | None = None,
              com_ferramentas: bool = True) -> Resposta:
    """Responde uma pergunta. `historico`: mensagens anteriores ({"role", "content"}), as últimas entram no contexto.
    Levanta llm.LLMIndisponivel se o Ollama não responder."""
    sistema = SISTEMA if com_ferramentas else SISTEMA_SEM_FERRAMENTAS
    mensagens = [{"role": "system", "content": sistema}, *(historico or [])[-6:], {"role": "user", "content": pergunta}]
    if not com_ferramentas:
        return Resposta(llm.conversar(mensagens).get("content", "").strip())
    chamadas = []
    for _ in range(int(llm.config()["max_rodadas_ferramentas"])):
        msg = llm.conversar(mensagens, ferramentas.ESQUEMAS)
        pedidos = msg.get("tool_calls") or []
        if not pedidos and not msg.get("content", "").strip() and not chamadas:
            # resposta vazia na primeira rodada (acontece com o qwen3): pede de novo, uma vez, lembrando as ferramentas
            mensagens.append({"role": "user", "content": "Use as ferramentas para responder à pergunta acima."})
            msg = llm.conversar(mensagens, ferramentas.ESQUEMAS)
            pedidos = msg.get("tool_calls") or []
        if not pedidos:
            return Resposta(msg.get("content", "").strip(), chamadas)
        mensagens.append({"role": "assistant", "content": msg.get("content", ""), "tool_calls": pedidos})
        for p in pedidos:
            nome, args = p["function"]["name"], p["function"].get("arguments")
            resultado = ferramentas.executar(con, nome, args)
            chamadas.append({"ferramenta": nome, "argumentos": args, "resultado": resultado})
            mensagens.append({"role": "tool", "tool_name": nome, "content": json.dumps(resultado, ensure_ascii=False)})
    # limite de rodadas: pede a resposta final sem novas ferramentas
    mensagens.append({"role": "user", "content": "Responda agora com o que as ferramentas já devolveram."})
    return Resposta(llm.conversar(mensagens).get("content", "").strip(), chamadas)
