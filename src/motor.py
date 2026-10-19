"""Motor de cálculo: encadeia as funções puras de src/model na ordem do SPEC §3. Sem I/O.

Usado pelo pipeline (gold) e pelo Simulador, para que os dois deem sempre o mesmo número.
Ordem: passivo por município -> rateio sobre todas as serventias -> universo -> déficit -> demanda -> receita.
"""
from dataclasses import dataclass

import pandas as pd

from src.model.cenario import aplicar_cenario_stf
from src.model.distribuicao import passivo_medio_por_municipio, preparar_vinculos
from src.model.mercado import deficit, demanda_seguro, receita
from src.model.premissas import resolver
from src.model.rateio import ratear_passivo
from src.model.universo import classificar, fracao_fora_classe_1, universo


@dataclass
class Insumos:
    rais: pd.DataFrame        # silver.rais_vinculo
    serventias: pd.DataFrame  # ativas: cns, cod_ibge, situacao_juridica, atribuicoes, clt, receita_ref, origem_receita
    fator_inpc: float
    mes_inpc: int
    regioes: dict[int, str] | None = None  # cod_ibge -> região imediata do IBGE (reserva da distribuição, D-022)


def pesos_por_atribuicao(serventias: pd.DataFrame) -> dict[str, float]:
    """Peso do método `peso_por_atribuicao`: média de CLT declarados no CNJ por combinação de atribuições."""
    return serventias.groupby("atribuicoes")["clt"].mean().fillna(0).to_dict()


def peso_indeterminada(serventias: pd.DataFrame, limites: dict) -> float:
    s = serventias.assign(classe=[classificar(r, limites) for r in serventias["receita_ref"]])
    return fracao_fora_classe_1(s)


def premissas_nivel(semente: dict, nivel: str, peso_indet_base: float, ajustes: dict | None = None) -> dict:
    """Premissas resolvidas num nível, com o peso da classe indeterminada (0 no min, calculado no base, 1 no max)."""
    peso = {"min": 0.0, "base": peso_indet_base, "max": 1.0}[nivel]
    return resolver(semente, nivel, {"peso_classe_indeterminada_base": peso, **(ajustes or {})})


def calcular_serventias(ins: Insumos, p: dict, limites: dict, metodo: str | None = None,
                        limites_faixa: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Passivo, universo e déficit por serventia (uso interno; nunca exibido por serventia) e passivo médio por município.

    `limites`: regra que decide o universo. `limites_faixa`: regra base, cuja classe define as faixas de déficit (D-019).
    """
    fator = 1.0 if p["correcao_salarial_rais"] == "sem_correcao" else ins.fator_inpc
    # a contagem de pessoas vem do CNJ (D-005), por isso o fator_cobertura_rais (D-006) não entra aqui
    vinc = preparar_vinculos(ins.rais, p["base_remuneracao_rais"], fator)
    municipios = ins.serventias["cod_ibge"].dropna().astype(int).unique().tolist()
    medio = passivo_medio_por_municipio(vinc, municipios, p, int(p["limiar_vinculos_distribuicao_municipal"]),
                                        ins.regioes)
    metodo = metodo or p["metodo_rateio_padrao"]
    pesos = pesos_por_atribuicao(ins.serventias) if metodo == "peso_por_atribuicao" else None
    rat = ratear_passivo(ins.serventias, medio, metodo, pesos)
    return deficit(universo(rat, limites, p, limites_faixa), p), medio


def resumo_mercado(serv: pd.DataFrame, p: dict, cenarios: dict, cenario: str, ajustes_cenario: dict | None = None
                   ) -> dict:
    """Totais de um recorte de serventias: universo, passivo, déficit, demanda e receita (mercado e seguradora)."""
    pc = aplicar_cenario_stf(p, cenarios, cenario, ajustes_cenario)
    dem = demanda_seguro(float(serv["valor_descoberto"].sum()), pc)
    rec = receita(dem, pc)
    return {
        "n_serventias_ativas": int(len(serv)),
        "clt": float(serv["clt"].fillna(0).sum()),
        "passivo_todas": float(serv["passivo"].sum()),
        "n_universo": float(serv["peso_universo"].sum()),
        "n_indeterminadas_universo": int(((serv["classe"] == "indeterminada") & (serv["peso_universo"] > 0)).sum()),
        "passivo_universo": float((serv["passivo"] * serv["peso_universo"]).sum()),
        "n_deficit": float(serv["n_deficit"].sum()),
        "valor_descoberto": float(serv["valor_descoberto"].sum()),
        "bens_proprios": dem.bens_proprios, "fianca": dem.fianca,
        **{f"mercado_{k}": v for k, v in rec["mercado"].como_dict().items()},
        **{f"seguradora_{k}": v for k, v in rec["seguradora"].como_dict().items()},
    }
