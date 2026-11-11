"""Dados da visão do Brasil, camada 1 (D-087), para o painel.

Lê a publicação mais recente do pipeline agendado (Release `brasil-*` do repositório) e confere cada arquivo pelo
SHA-256 do manifesto. Sem internet, com a API do GitHub no limite (60 pedidos por hora sem token) ou com qualquer
arquivo que não confira, usa a cópia versionada em data/brasil/ (gerada pelo mesmo scripts/pipeline_brasil.py). O
painel diz de onde veio o dado e a data ("atualizado em").
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import yaml

from src.transform.brasil import COLUNAS

RAIZ = Path(__file__).resolve().parents[2]
LOCAL = RAIZ / "data" / "brasil"
CONFIG = RAIZ / "config" / "brasil.yaml"
ARQUIVOS = ("manifesto.json", "brasil_uf.csv", "malha_uf.geojson")
TIMEOUT_S = 8   # o painel não pode travar esperando o GitHub: depois disso, a cópia local
# "os cartórios da Bahia", "do Rio de Janeiro", "de Minas Gerais": a preposição de cada UF (uso corrente)
PREPOSICAO = {"AC": "do", "AL": "de", "AP": "do", "AM": "do", "BA": "da", "CE": "do", "DF": "do", "ES": "do",
              "GO": "de", "MA": "do", "MT": "de", "MS": "de", "MG": "de", "PA": "do", "PB": "da", "PR": "do",
              "PE": "de", "PI": "do", "RJ": "do", "RN": "do", "RS": "do", "RO": "de", "RR": "de", "SC": "de",
              "SP": "de", "SE": "de", "TO": "do"}


def do_estado(uf: str, nome: str) -> str:
    """'BA', 'Bahia' → 'da Bahia'."""
    return f"{PREPOSICAO.get(uf, 'de')} {nome}"


@dataclass
class Publicacao:
    linhas: list[dict]
    manifesto: dict
    malha: dict
    origem: str                     # "Release brasil-AAAA-MM-DD" ou "cópia do repositório (data/brasil)"
    avisos: list[str] = field(default_factory=list)

    @property
    def data(self) -> str:
        return self.manifesto["publicacao"]


def _tipo(v: str):
    if v == "":
        return None
    for f in (int, float):
        try:
            return f(v)
        except ValueError:
            pass
    return v


def _montar(conteudo: dict[str, bytes], origem: str) -> Publicacao:
    """Confere e lê os três arquivos. Erro (ValueError) se algum hash não bate ou o CSV sai do contrato."""
    manifesto = json.loads(conteudo["manifesto.json"])
    for a in manifesto["arquivos"]:
        if hashlib.sha256(conteudo[a["arquivo"]]).hexdigest() != a["sha256"]:
            raise ValueError(f"{a['arquivo']}: SHA-256 não confere com o manifesto")
    leitor = csv.DictReader(io.StringIO(conteudo["brasil_uf.csv"].decode("utf-8")))
    if leitor.fieldnames != COLUNAS:
        raise ValueError("brasil_uf.csv com colunas fora do contrato")
    linhas = [{k: (v if k in ("uf", "nome", "regiao") else _tipo(v)) for k, v in x.items()} for x in leitor]
    return Publicacao(linhas, manifesto, json.loads(conteudo["malha_uf.geojson"]), origem)


def local(pasta: Path = LOCAL) -> Publicacao:
    return _montar({a: (pasta / a).read_bytes() for a in ARQUIVOS}, "cópia do repositório (data/brasil)")


def da_release(cliente: httpx.Client, repositorio: str, prefixo: str) -> Publicacao:
    r = cliente.get(f"https://api.github.com/repos/{repositorio}/releases", params={"per_page": 30})
    r.raise_for_status()
    rel = next((x for x in r.json() if x["tag_name"].startswith(prefixo) and not x.get("draft")), None)
    if rel is None:
        raise LookupError("nenhuma Release do Brasil publicada ainda")
    urls = {a["name"]: a["browser_download_url"] for a in rel["assets"]}
    conteudo = {}
    for a in ARQUIVOS:
        resp = cliente.get(urls[a], follow_redirects=True)
        resp.raise_for_status()
        conteudo[a] = resp.content
    return _montar(conteudo, f"Release {rel['tag_name']}")


def publicacao(cliente: httpx.Client | None = None, pasta: Path = LOCAL) -> Publicacao:
    """A Release mais recente, se der; senão a cópia local, com o motivo em `avisos`."""
    c = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if cliente is None and os.environ.get("RADAR_BRASIL_RELEASE") == "0":   # testes: sem internet
        return local(pasta)
    try:
        if cliente is not None:
            return da_release(cliente, c["repositorio"], c["prefixo_release"])
        with httpx.Client(timeout=TIMEOUT_S, headers={"Accept": "application/vnd.github+json"}) as novo:
            return da_release(novo, c["repositorio"], c["prefixo_release"])
    except (httpx.HTTPError, LookupError, KeyError, ValueError) as e:
        p = local(pasta)
        p.avisos.append(f"Release indisponível ({type(e).__name__}): mostrando a cópia do repositório")
        return p


def geometrias(p: Publicacao) -> dict[str, dict]:
    """{UF: geometria GeoJSON} na ordem do CSV."""
    por_uf = {f["properties"]["uf"]: f["geometry"] for f in p.malha["features"]}
    return {x["uf"]: por_uf[x["uf"]] for x in p.linhas if x["uf"] in por_uf}


def totais(p: Publicacao) -> dict[str, float]:
    """Os indicadores do Brasil inteiro (somas e razões das somas, não médias das UFs)."""
    s = {k: sum(x[k] or 0 for x in p.linhas) for k in ("serventias_ativas", "vagas", "municipios",
                                                         "municipios_com_cartorio", "populacao")}
    return {**s,
            "pct_vagas": s["vagas"] / s["serventias_ativas"] if s["serventias_ativas"] else 0.0,
            "pct_municipios_com_cartorio": s["municipios_com_cartorio"] / s["municipios"] if s["municipios"] else 0.0,
            "por_100mil_hab": s["serventias_ativas"] / s["populacao"] * 1e5 if s["populacao"] else 0.0}
