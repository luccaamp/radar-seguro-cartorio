"""Visão do Brasil, camada 1 (D-087): o que o cadastro nacional do CNJ e o IBGE dão por UF, sem o modelo de passivo.

Entrada: o cadastro do Justiça Aberta das 27 UFs (`serventias_<UF>.json`, o mesmo coletor de MG) e quatro arquivos do
IBGE (`src.ingest.ibge.urls_brasil`). Saída (`montar`): uma linha por UF, só com contagens. Os campos pessoais do
cadastro (responsável, substitutos, telefone, e-mail, endereço) nunca são lidos, como no silver de MG (D-030, D-038).

Por que só camada 1: arrecadação e classe por UF exigem uma coleta por UF e semestre na API do CNJ (lenta, com
timeout no Brasil inteiro); o prêmio e o déficit exigem a RAIS e o modelo calibrado de cada estado (Fase 6). O painel
mostra o Brasil com estes números e MG com o estudo completo.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from src.ingest.cnj_serventias import integridade
from src.transform.normalizar import normalizar_nome
from src.transform.silver import ATRIBUICOES

# situação jurídica da serventia no cadastro: "VAGO" e "VAGO - SUB JUDICE" = sem titular concursado (respondida por
# interino); as outras (PROVIDO, CONVERSÃO EM DILIGÊNCIA, SOB INTERVENÇÃO, vazio) não contam como vagas
VAGAS = ("VAGO", "VAGO - SUB JUDICE")
OFICIALIZADAS = ("OFICIALIZADO", "PUBLICO")   # tipo_cartorio; o resto é PRIVATIZADO
CAMPOS_LIDOS = ("cns", "uf", "cidade", "status", "tipo_cartorio", "situacao_juridica_cartorio", "natureza")
COLUNAS = ["uf", "cod_ibge", "nome", "regiao", "serventias_ativas", "serventias_inativas", "serventias_extintas",
           "vagas", "pct_vagas", "oficializadas", "municipios", "municipios_com_cartorio", "pct_municipios_com_cartorio",
           "populacao", "por_100mil_hab", *ATRIBUICOES.values(), "cidades_sem_codigo"]


def ler_cadastro(pasta: Path, tolerancia: int = 0) -> dict[str, list[dict]]:
    """Os registros de cada UF, só com os CAMPOS_LIDOS (nada pessoal sai daqui). Confere a integridade de cada arquivo
    como o coletor (`cnj_serventias.integridade`, com a mesma `tolerancia`)."""
    por_uf: dict[str, list[dict]] = {}
    for arq in sorted(pasta.glob("serventias_*.json")):
        if arq.name.endswith(".meta.json"):
            continue
        d = json.loads(arq.read_text(encoding="utf-8"))
        itens = d["data"]
        if integridade(d["meta"]["total"], [i["cns"] for i in itens], tolerancia) is None:
            raise ValueError(f"{arq.name}: integridade falhou (meta.total={d['meta']['total']}, {len(itens)} registros)")
        uf = arq.stem.removeprefix("serventias_")
        por_uf[uf] = [{k: i.get(k) for k in CAMPOS_LIDOS} for i in itens]
    return por_uf


def _situacao(s) -> str:
    return (s.get("descricao") or "") if isinstance(s, dict) else (s or "")


def _uf_do_municipio(m: dict) -> str:
    """Sigla da UF de um município da API de localidades (a microrregião vem nula em municípios novos)."""
    micro = m.get("microrregiao")
    if micro:
        return micro["mesorregiao"]["UF"]["sigla"]
    return m["regiao-imediata"]["regiao-intermediaria"]["UF"]["sigla"]


def montar(cadastro: dict[str, list[dict]], estados: list[dict], municipios: list[dict], populacao: list[dict],
           apelidos: dict[str, dict[str, int]] | None = None) -> list[dict]:
    """Uma linha por UF de `estados` (as 27), em ordem de sigla. `apelidos`: {UF: {nome normalizado: cod_ibge}} para
    as cidades do cadastro escritas diferente do IBGE (config/estados.yaml; hoje só MG tem)."""
    apelidos = apelidos or {}
    mun_por_uf: dict[str, dict[str, int]] = defaultdict(dict)
    for m in municipios:
        mun_por_uf[_uf_do_municipio(m)][normalizar_nome(m["nome"])] = int(m["id"])
    pop = {int(p["D1C"]): int(p["V"]) for p in populacao if str(p.get("D1C", "")).isdigit() and str(p["V"]).isdigit()}
    linhas = []
    for e in sorted(estados, key=lambda e: e["sigla"]):
        uf = e["sigla"]
        regs = cadastro.get(uf, [])
        ativas = [r for r in regs if r.get("status") == "Ativo"]
        status = Counter(r.get("status") for r in regs)
        indice = {**mun_por_uf.get(uf, {}), **apelidos.get(uf, {})}
        unico = next(iter(mun_por_uf[uf].values())) if len(mun_por_uf.get(uf, {})) == 1 else None
        codigos, sem_codigo = set(), set()
        for r in ativas:
            # UF com um município só (DF): as "cidades" do cadastro são regiões administrativas de Brasília
            cod = unico or indice.get(normalizar_nome(r.get("cidade")))
            (codigos.add(cod) if cod else sem_codigo.add(r.get("cidade") or ""))
        nats = Counter(n.strip() for r in ativas for n in (r.get("natureza") or "").split("|") if n.strip())
        desconhecidas = set(nats) - set(ATRIBUICOES)
        if desconhecidas:
            raise ValueError(f"{uf}: atribuição nova no Justiça Aberta: {desconhecidas}")
        n_mun = len(mun_por_uf.get(uf, {}))
        habitantes = pop.get(int(e["id"]))
        vagas = sum(_situacao(r.get("situacao_juridica_cartorio")) in VAGAS for r in ativas)
        linhas.append({
            "uf": uf, "cod_ibge": int(e["id"]), "nome": e["nome"], "regiao": e["regiao"]["nome"],
            "serventias_ativas": len(ativas), "serventias_inativas": status.get("Inativo", 0),
            "serventias_extintas": status.get("Extinto", 0),
            "vagas": vagas, "pct_vagas": round(vagas / len(ativas), 4) if ativas else None,
            "oficializadas": sum(r.get("tipo_cartorio") in OFICIALIZADAS for r in ativas),
            "municipios": n_mun, "municipios_com_cartorio": len(codigos),
            "pct_municipios_com_cartorio": round(len(codigos) / n_mun, 4) if n_mun else None,
            "populacao": habitantes,
            "por_100mil_hab": round(len(ativas) / habitantes * 1e5, 2) if habitantes else None,
            **{col: nats.get(rot, 0) for rot, col in ATRIBUICOES.items()},
            "cidades_sem_codigo": len(sem_codigo),
        })
    return linhas


def conferir(linhas: list[dict], cadastro: dict[str, list[dict]], limite_sem_codigo: float) -> list[str]:
    """Contrato da camada 1: devolve os problemas (vazio = pode publicar). As 27 UFs, todas com cadastro e população;
    a soma das ativas por UF bate com o cadastro; nenhuma coluna fora de COLUNAS (nada pessoal); poucas cidades sem
    código do IBGE (`limite_sem_codigo`, fração das cidades com cartório da UF)."""
    erros = []
    ufs = [x["uf"] for x in linhas]
    if len(ufs) != 27 or len(set(ufs)) != 27:
        erros.append(f"esperadas 27 UFs, vieram {len(set(ufs))}")
    for x in linhas:
        if set(x) != set(COLUNAS):
            erros.append(f"{x['uf']}: colunas fora do contrato: {sorted(set(x) ^ set(COLUNAS))}")
        if x["uf"] not in cadastro or not x["serventias_ativas"]:
            erros.append(f"{x['uf']}: sem serventia ativa no cadastro")
        if not x["populacao"]:
            erros.append(f"{x['uf']}: sem população do IBGE")
        com_cartorio = x["municipios_com_cartorio"] + x["cidades_sem_codigo"]
        if com_cartorio and x["cidades_sem_codigo"] / com_cartorio > limite_sem_codigo:
            erros.append(f"{x['uf']}: {x['cidades_sem_codigo']} cidades do cadastro sem código do IBGE")
    total = sum(sum(r.get("status") == "Ativo" for r in regs) for regs in cadastro.values())
    if sum(x["serventias_ativas"] for x in linhas) != total:
        erros.append("a soma das serventias ativas por UF não bate com o cadastro")
    return erros


def mudancas(antes: list[dict], depois: list[dict], colunas=("serventias_ativas", "vagas", "municipios_com_cartorio",
                                                             "populacao")) -> list[dict]:
    """O que mudou entre duas publicações, por UF e coluna (só o que mudou). Base do "o que mudou" da Release."""
    a = {x["uf"]: x for x in antes}
    out = []
    for x in depois:
        for c in colunas:
            v0 = (a.get(x["uf"]) or {}).get(c)
            if v0 != x.get(c):
                out.append({"uf": x["uf"], "coluna": c, "antes": v0, "depois": x.get(c)})
    return out
