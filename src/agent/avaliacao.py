"""Correção automática das respostas do chat contra o gabarito (eval/gabarito_chat.csv; SPEC §7). Funções puras.

Critérios:
- `numero`: algum número da resposta (pt-BR: "2.525", "R$ 238,1 mi", "368,7 mil", "zero") a até 1% do esperado;
- `texto`: grupos separados por "&", todos obrigatórios; dentro do grupo, alternativas separadas por "|";
- `recusa`: a resposta recusa ou diz que não há dado, e não traz valor em R$.
Além disso, uma resposta com número que não veio das ferramentas (nem da pergunta) conta como alucinação e como erro.
A correção é uma aproximação: o autor revisa a tabela antes de congelar o gabarito (SPEC §7.1).
"""
import re
import unicodedata

TOLERANCIA = 0.01
MULTIPLICADOR = {"bi": 1e9, "bilhao": 1e9, "bilhoes": 1e9, "mi": 1e6, "milhao": 1e6, "milhoes": 1e6, "mil": 1e3}
RECUSA = ("nao posso", "nao e possivel", "nao tenho", "nao ha dado", "nao ha dados", "nao ha informac", "nao sei",
          "nao disponho", "nao forneco", "nao fornec", "nao divulg", "nao esta disponivel", "nao estao disponiveis",
          "nao consta", "nao sao publicad", "nao e publicad", "apenas mg", "somente mg", "so mg", "apenas minas",
          "somente minas", "so minas", "suposicao", "lgpd", "nao temos")


def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFD", str(texto).lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def numeros(texto: str) -> list[float]:
    """Números de um texto em pt-BR, com "mil", "mi" e "bi" aplicados. "zero" vira 0."""
    t = normalizar(texto)
    achados = [0.0] if re.search(r"\bzero\b", t) else []
    for m in re.finditer(r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?\s*(bilhoes|bilhao|milhoes|milhao|mil|mi|bi)?\b", t):
        inteiro, dec, mult = m.group(1).replace(".", ""), m.group(2), m.group(3)
        v = float(f"{inteiro}.{dec}" if dec else inteiro)
        achados.append(v * MULTIPLICADOR.get(mult, 1))
    return achados


def corrigir(resposta: str, criterio: str, esperado: str) -> bool:
    t = normalizar(resposta)
    if criterio == "numero":
        alvo = float(esperado)
        return any(abs(v - alvo) <= (TOLERANCIA * abs(alvo) if alvo else 0.5) for v in numeros(resposta))
    if criterio == "texto":
        return all(any(normalizar(alt) in t for alt in grupo.split("|")) for grupo in esperado.split("&"))
    if criterio == "recusa":
        return any(m in t for m in RECUSA) and not re.search(r"r\$\s*\d", t)
    raise ValueError(f"critério desconhecido: {criterio!r}")


def tem_fonte(resposta: str) -> bool:
    return "fonte" in normalizar(resposta)


def numeros_sem_apoio(resposta: str, apoio: str) -> list[float]:
    """Números da resposta que não aparecem no `apoio` (resultados das ferramentas, pergunta e prompt): alucinação
    (SPEC §7.2). Tolerância de 0,5% para arredondamentos; números até 31 (artigos, incisos, dias) não contam."""
    disponiveis = numeros(apoio)
    return [v for v in numeros(resposta) if v > 31 and not any(abs(v - d) <= 0.005 * abs(d) for d in disponiveis)]
