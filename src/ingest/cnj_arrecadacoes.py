"""Coleta a série de arrecadação semestral de cada serventia ATIVA de uma UF (Justiça Aberta, GET /{cns}/arrecadacoes).

Retomável: se o arquivo do dia já existe, só busca os CNS que faltam (ou que falharam).
Saída: data/bronze/cnj_justica_aberta/<data>/arrecadacoes_<UF>.jsonl, uma linha por serventia, com a resposta bruta.
A rota não traz dados pessoais (só período, atos praticados e arrecadação).

Uso: uv run python -m src.ingest.cnj_arrecadacoes MG
"""
import json
import sys
import time

from src.ingest.comum import BRONZE, cliente, gravar_meta, hoje, snapshot_mais_recente

URL = "https://justicaabertaapi.cnj.jus.br/v1/api/serventias"
HEADERS = {"Origin": "https://justicaaberta.cnj.jus.br", "Referer": "https://justicaaberta.cnj.jus.br/"}
INTERVALO_S = 1.2


def coletar(uf: str) -> None:
    lista = snapshot_mais_recente("cnj_justica_aberta", f"serventias_{uf}.json")
    ativos = [s["cns"] for s in json.loads(lista.read_text(encoding="utf-8"))["data"] if s["status"] == "Ativo"]
    destino = BRONZE / "cnj_justica_aberta" / hoje() / f"arrecadacoes_{uf}.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)

    feitos = set()
    if destino.exists():
        for linha in destino.read_text(encoding="utf-8").splitlines():
            reg = json.loads(linha)
            if reg.get("integridade_ok"):
                feitos.add(reg["cns"])
    faltam = [c for c in ativos if c not in feitos]
    print(f"{uf}: {len(ativos)} ativas, {len(feitos)} já coletadas, {len(faltam)} a coletar", flush=True)

    erros = 0
    with cliente(timeout=60, **HEADERS) as c, open(destino, "a", encoding="utf-8") as f:
        for n, cns in enumerate(faltam, 1):
            reg = {"cns": cns, "coletado_em": hoje()}
            try:
                r = c.get(f"{URL}/{cns}/arrecadacoes", params={"page": 1, "perPage": 200})
                reg["status_http"] = r.status_code
                if r.status_code == 200 and r.content:
                    corpo = r.json()
                    dados = corpo.get("data") or []
                    total = (corpo.get("meta") or {}).get("total")
                    reg.update(meta_total=total, registros=len(dados), integridade_ok=(total == len(dados)), dados=dados)
            except Exception as e:  # rede instável: registra e segue; a próxima execução tenta de novo
                reg.update(status_http=None, erro=type(e).__name__)
                erros += 1
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
            f.flush()
            if n % 200 == 0:
                print(f"  {n}/{len(faltam)}", flush=True)
            time.sleep(INTERVALO_S)

    gravar_meta(destino, url=f"{URL}/{{cns}}/arrecadacoes", metodo="GET", params={"page": 1, "perPage": 200},
                origem_lista=str(lista.relative_to(BRONZE)), serventias_ativas=len(ativos))
    print(f"FIM {uf} | erros de rede: {erros}", flush=True)


if __name__ == "__main__":
    coletar(sys.argv[1] if len(sys.argv) > 1 else "MG")
