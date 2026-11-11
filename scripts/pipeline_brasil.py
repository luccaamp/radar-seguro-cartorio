"""Pipeline do Brasil, camada 1 (D-087): coleta → tabela por UF → contrato → comparação com a publicação anterior →
pasta pública com manifesto e "o que mudou". Roda no GitHub Actions todo mês (.github/workflows/pipeline-brasil.yml),
que publica a pasta como Release datada; qualquer problema = código 1, nada é publicado e o workflow abre uma issue.

Só fontes públicas e sem chave: cadastro do Justiça Aberta (CNJ) das 27 UFs e IBGE. Nada pessoal: o cadastro é lido
só nos campos de `src.transform.brasil.CAMPOS_LIDOS`, e a saída tem só contagens por UF.

Uso:
  uv run python scripts/pipeline_brasil.py --coletar                   # coleta hoje e grava em data/brasil/
  uv run python scripts/pipeline_brasil.py --cnj PASTA --ibge PASTA    # usa o que já foi coletado
  ... --anterior PASTA   # publicação anterior (brasil_uf.csv): limite de variação e "o que mudou"
  ... --saida PASTA      # padrão data/brasil (a cópia versionada que o painel usa sem internet)
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import estados_config  # noqa: E402
from src.transform import brasil  # noqa: E402

CONFIG = RAIZ / "config" / "brasil.yaml"
SAIDA = RAIZ / "data" / "brasil"
REFERENCIA_IBGE = SAIDA / "ibge"   # a última coleta do IBGE que deu certo, no git (≈ 350 KB)
CASAS_MALHA = 3   # casas decimais das coordenadas da malha publicada (≈ 100 m; o mapa tem 1000 px de largura)
ARQUIVOS_IBGE = ("brasil_estados.json", "brasil_municipios.json", "brasil_populacao.json", "brasil_malha_uf.geojson")


def config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def apelidos(c: dict) -> dict[str, dict[str, int]]:
    """Os de MG (config/estados.yaml) mais os do Brasil (config/brasil.yaml)."""
    out = {uf: {str(k): int(v) for k, v in m.items()} for uf, m in (c.get("apelidos_municipios") or {}).items()}
    for uf in estados_config.ufs():
        out.setdefault(uf, {}).update(estados_config.apelidos_municipios(uf))
    return out


def coletar(base: Path, c: dict, coletar_ibge=None) -> tuple[Path, Path]:
    """Coleta o IBGE e o cadastro do CNJ das 27 UFs. O IBGE muda no máximo uma vez por ano (estados, municípios,
    população estimada, malha) e não aceita conexão do GitHub Actions (2026-11-11): sem resposta, usa a referência
    versionada (REFERENCIA_IBGE) e o manifesto diz isso. O CNJ, que muda todo mês, é obrigatório."""
    from src.ingest import cnj_serventias, ibge
    hoje = f"{dt.date.today():%Y-%m-%d}"
    cnj, pasta_ibge = base / "cnj_justica_aberta" / hoje, base / "ibge" / hoje
    try:
        (coletar_ibge or ibge.coletar_brasil)(pasta_ibge)
    except Exception as e:   # noqa: BLE001 (qualquer falha do IBGE: a referência versionada serve)
        print(f"IBGE sem resposta ({type(e).__name__}): usando a referência versionada em {REFERENCIA_IBGE}")
        pasta_ibge = REFERENCIA_IBGE
    ufs = [e["sigla"] for e in _ler_ibge(pasta_ibge)["brasil_estados.json"]]
    for uf in sorted(ufs):
        cnj_serventias.coletar(uf, cnj, tolerancia=int(c["tolerancia_meta_total"]))
    return cnj, pasta_ibge


def _ler_ibge(pasta: Path) -> dict:
    return {n: json.loads((pasta / n).read_text(encoding="utf-8")) for n in ARQUIVOS_IBGE}


def atualizar_referencia_ibge(origem: Path, destino: Path = None) -> None:
    """Grava a referência versionada a partir de uma coleta do IBGE que deu certo (rodar quando o IBGE publicar uma
    estimativa de população ou uma malha nova): municípios na forma compacta e os .meta.json da coleta."""
    destino = destino or REFERENCIA_IBGE
    destino.mkdir(parents=True, exist_ok=True)
    d = _ler_ibge(origem)
    from src.transform.brasil import _uf_do_municipio
    d["brasil_municipios.json"] = [{"id": m["id"], "nome": m["nome"], "uf": _uf_do_municipio(m)}
                                   for m in d["brasil_municipios.json"]]
    for n, v in d.items():
        (destino / n).write_text(json.dumps(v, ensure_ascii=False, separators=(",", ":")), encoding="utf-8",
                                 newline="\n")
        meta = origem / f"{n}.meta.json"
        if meta.exists():
            (destino / meta.name).write_bytes(meta.read_bytes())


def ler_csv(arq: Path) -> list[dict]:
    """brasil_uf.csv de volta em dicionários com os tipos (int, float ou None)."""
    def tipo(v: str):
        if v == "":
            return None
        try:
            return int(v)
        except ValueError:
            try:
                return float(v)
            except ValueError:
                return v
    with arq.open(encoding="utf-8", newline="") as f:
        return [{k: tipo(v) for k, v in linha.items()} for linha in csv.DictReader(f)]


def _csv(linhas: list[dict]) -> bytes:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=brasil.COLUNAS, lineterminator="\n")
    w.writeheader()
    w.writerows({k: ("" if v is None else v) for k, v in x.items()} for x in linhas)
    return buf.getvalue().encode("utf-8")


def malha(geo: dict, estados: list[dict]) -> bytes:
    """A malha dos estados com a sigla em `uf` e as coordenadas com CASAS_MALHA casas."""
    sigla = {str(e["id"]): e["sigla"] for e in estados}

    def arred(c):
        return [arred(x) for x in c] if isinstance(c[0], list) else [round(c[0], CASAS_MALHA), round(c[1], CASAS_MALHA)]
    feats = [{"type": "Feature", "properties": {"uf": sigla[str(f["properties"]["codarea"])]},
              "geometry": {"type": f["geometry"]["type"], "coordinates": arred(f["geometry"]["coordinates"])}}
             for f in geo["features"]]
    return json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")).encode("utf-8")


def _datas_meta(pasta: Path, padrao: str) -> list[str]:
    datas = set()
    for m in pasta.glob(padrao):
        d = json.loads(m.read_text(encoding="utf-8"))
        if d.get("coletado_em"):
            datas.add(d["coletado_em"][:10])
    return sorted(datas)


def _milhar(n: int) -> str:
    """12121 → "12.121" (separador de milhar do português)."""
    return f"{n:,}".replace(",", ".")


def o_que_mudou(antes: list[dict] | None, depois: list[dict], data: str) -> str:
    """Texto determinístico (Markdown) para as notas da Release: totais e o que mudou por UF."""
    total = sum(x["serventias_ativas"] for x in depois)
    linhas = [f"# Brasil, camada 1 — publicação de {data}", "",
              f"**{_milhar(total)} serventias ativas** nas 27 UFs (cadastro do CNJ, Justiça Aberta), com população e "
              "municípios do IBGE.", ""]
    if antes is None:
        return "\n".join(linhas + ["Primeira publicação: nada a comparar.", ""])
    total0 = sum(x["serventias_ativas"] for x in antes)
    dif = total - total0
    linhas += [f"Antes: {_milhar(total0)} serventias ativas; diferença: {'+' if dif >= 0 else '−'}{_milhar(abs(dif))}.",
               ""]
    mud = brasil.mudancas(antes, depois)
    if not mud:
        return "\n".join(linhas + ["Nenhuma mudança por UF nas serventias ativas, vagas, municípios com cartório e "
                                   "população.", ""])
    linhas += ["| UF | O quê | Antes | Depois |", "|---|---|---|---|"]
    linhas += [f"| {m['uf']} | {m['coluna']} | {m['antes']} | {m['depois']} |" for m in mud]
    return "\n".join(linhas + [""])


def main(cnj: Path, pasta_ibge: Path, saida: Path, anterior: Path | None, c: dict) -> list[str]:
    """Monta e grava em `saida`. Devolve os problemas: com algum, nada é gravado."""
    ibge = _ler_ibge(pasta_ibge)
    cad = brasil.ler_cadastro(cnj, int(c["tolerancia_meta_total"]))
    linhas = brasil.montar(cad, ibge["brasil_estados.json"], ibge["brasil_municipios.json"],
                           ibge["brasil_populacao.json"], apelidos(c))
    erros = brasil.conferir(linhas, cad, float(c["limite_cidades_sem_codigo"]))
    antes = ler_csv(anterior / "brasil_uf.csv") if anterior and (anterior / "brasil_uf.csv").exists() else None
    if antes:
        t0, t1 = (sum(x["serventias_ativas"] for x in v) for v in (antes, linhas))
        if t0 and abs(t1 - t0) / t0 > float(c["variacao_maxima_ativas"]):
            erros.append(f"serventias ativas do Brasil variaram de {t0} para {t1} (limite "
                         f"{float(c['variacao_maxima_ativas']):.0%}): conferir a coleta antes de publicar")
    if erros:
        return erros
    hoje = f"{dt.date.today():%Y-%m-%d}"
    arquivos = {"brasil_uf.csv": _csv(linhas), "malha_uf.geojson": malha(ibge["brasil_malha_uf.geojson"],
                                                                         ibge["brasil_estados.json"])}
    datas_cnj, datas_ibge = _datas_meta(cnj, "serventias_*.meta.json"), _datas_meta(pasta_ibge, "brasil_*.meta.json")
    pop_ano = next((p["D3N"] for p in ibge["brasil_populacao.json"][1:]), None)
    manifesto = {
        "publicacao": hoje,
        "camada": 1,
        "decisao": "D-087",
        "fontes": {
            "cnj_cadastro": {"orgao": "CNJ, Justiça Aberta (cadastro de serventias)", "coletado_em": datas_cnj,
                             "url": "https://justicaaberta.cnj.jus.br/"},
            "ibge": {"orgao": "IBGE (localidades, SIDRA tabela 6579 e malhas v3)", "coletado_em": datas_ibge,
                     "origem": ("referência versionada (data/brasil/ibge): o IBGE não respondeu nesta execução"
                                if pasta_ibge.resolve() == REFERENCIA_IBGE.resolve() else "coleta desta execução"),
                     "populacao_estimada": pop_ano, "url": "https://servicodados.ibge.gov.br/"},
        },
        "totais": {"ufs": len(linhas), "serventias_ativas": sum(x["serventias_ativas"] for x in linhas),
                   "municipios_com_cartorio": sum(x["municipios_com_cartorio"] for x in linhas)},
        "arquivos": [{"arquivo": n, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(),
                      **({"linhas": len(linhas)} if n.endswith(".csv") else {})} for n, b in arquivos.items()],
    }
    saida.mkdir(parents=True, exist_ok=True)
    for n, b in arquivos.items():
        (saida / n).write_bytes(b)
    (saida / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (saida / "o_que_mudou.md").write_text(o_que_mudou(antes, linhas, hoje), encoding="utf-8")
    return []


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = argparse.ArgumentParser()
    a.add_argument("--coletar", action="store_true", help="coleta hoje (CNJ das 27 UFs e IBGE)")
    a.add_argument("--bronze", type=Path, default=RAIZ / "data" / "bronze", help="onde a coleta grava")
    a.add_argument("--cnj", type=Path, help="pasta com serventias_<UF>.json (sem --coletar)")
    a.add_argument("--ibge", type=Path, help="pasta com os brasil_*.json do IBGE (sem --coletar)")
    a.add_argument("--anterior", type=Path, help="pasta da publicação anterior")
    a.add_argument("--saida", type=Path, default=SAIDA)
    a.add_argument("--simular-falha", action="store_true",
                   help="acrescenta um problema de propósito: prova que a falha bloqueia a publicação e abre a issue")
    a.add_argument("--atualizar-referencia-ibge", type=Path, metavar="PASTA",
                   help="grava data/brasil/ibge a partir de uma coleta do IBGE que deu certo, e sai")
    x = a.parse_args()
    c = config()
    if x.atualizar_referencia_ibge:
        atualizar_referencia_ibge(x.atualizar_referencia_ibge)
        raise SystemExit(0)
    if x.coletar:
        x.cnj, x.ibge = coletar(x.bronze, c)
    if not (x.cnj and x.ibge):
        raise SystemExit("passe --coletar ou --cnj e --ibge")
    problemas = (["falha simulada (--simular-falha): teste do bloqueio da publicação"] if x.simular_falha
                 else main(x.cnj, x.ibge, x.saida, x.anterior, c))
    if problemas:
        print("NÃO publicar:\n- " + "\n- ".join(problemas))
        raise SystemExit(1)
    print((x.saida / "o_que_mudou.md").read_text(encoding="utf-8"))
