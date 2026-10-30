"""Coleta /dados-complementares (contagem de colaboradores) de cada serventia ATIVA de uma UF. Retomável.

Guarda só as contagens e os indicadores de informatização: a rota não é usada para dados pessoais.
Saída: data/bronze/cnj_justica_aberta/<data>/dados_complementares_<UF>.jsonl

Uso: uv run python -m src.ingest.cnj_complementares MG
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
    destino = BRONZE / "cnj_justica_aberta" / hoje() / f"dados_complementares_{uf}.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)
    feitos = set()
    if destino.exists():
        feitos = {json.loads(l)["cns"] for l in destino.read_text(encoding="utf-8").splitlines()
                  if json.loads(l).get("status_http") == 200}
    faltam = [c for c in ativos if c not in feitos]
    print(f"{uf}: {len(ativos)} ativas, {len(faltam)} a coletar", flush=True)
    with cliente(timeout=60, **HEADERS) as c, open(destino, "a", encoding="utf-8") as f:
        for cns in faltam:
            reg = {"cns": cns, "coletado_em": hoje()}
            try:
                r = c.get(f"{URL}/{cns}/dados-complementares")
                reg["status_http"] = r.status_code
                dados = r.json() if r.status_code == 200 and r.content else None
                if isinstance(dados, dict):
                    reg.update({k: v for k, v in dados.items()
                                if k.startswith("quantidade") or k in ("informatizada", "acesso_internet")})
            except Exception as e:
                reg.update(status_http=None, erro=type(e).__name__)
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
            f.flush()
            time.sleep(INTERVALO_S)
    gravar_meta(destino, url=f"{URL}/{{cns}}/dados-complementares", metodo="GET",
                origem_lista=str(lista.relative_to(BRONZE)), serventias_ativas=len(ativos))


if __name__ == "__main__":
    coletar(sys.argv[1] if len(sys.argv) > 1 else "MG")
