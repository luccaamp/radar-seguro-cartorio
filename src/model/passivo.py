"""Passivo trabalhista por vínculo e por município (Prov. CNJ 227/2026, arts. 5º e 6º). Funções puras.

Posição de cálculo: 31/12 (art. 4º). Hipótese do art. 5º: despedida de todos os prepostos sem justa causa,
com aviso prévio indenizado. A projeção do aviso integra o tempo de serviço (CLT art. 487, § 1º), por isso
gera 13º e férias proporcionais adicionais.
"""
from dataclasses import asdict, dataclass
from datetime import date, timedelta

import pandas as pd


@dataclass(frozen=True)
class Passivo:
    """Valor de cada verba do passivo de um vínculo, em R$."""
    aviso_previo: float = 0.0
    decimo_terceiro: float = 0.0
    ferias: float = 0.0            # proporcionais + vencidas pendentes, já com o terço
    multa_fgts: float = 0.0
    verbas_cct: float = 0.0
    saldo_salario: float = 0.0
    fgts_rescisorio: float = 0.0   # "FGTS mensal" do parágrafo único do art. 5º, sobre as verbas que têm incidência
    inss_patronal: float = 0.0
    rat_fap: float = 0.0
    # memória de cálculo (para o exemplo à mão e para conferência)
    dias_aviso: int = 0
    avos_13: int = 0
    avos_ferias: int = 0
    periodos_ferias_vencidas: float = 0.0
    saldo_fgts_estimado: float = 0.0

    @property
    def verbas(self) -> float:
        return self.aviso_previo + self.decimo_terceiro + self.ferias + self.multa_fgts + self.verbas_cct + self.saldo_salario

    @property
    def encargos(self) -> float:
        return self.fgts_rescisorio + self.inss_patronal + self.rat_fap

    @property
    def total(self) -> float:
        return self.verbas + self.encargos

    def como_dict(self) -> dict:
        return asdict(self) | {"verbas": self.verbas, "encargos": self.encargos, "total": self.total}


def avos(dias: float, dias_fracao: int) -> int:
    """Meses (1/12 avos) contidos em `dias`: cada 30 dias é um mês, e a sobra de `dias_fracao` dias ou mais conta como mês."""
    dias = int(round(dias))
    return dias // 30 + (1 if dias % 30 >= dias_fracao else 0)


def avos_13_da_projecao(data_posicao: date, dias_aviso: int, dias_fracao: int) -> int:
    """Avos de 13º gerados pela projeção do aviso, contados pelo CALENDÁRIO (Lei 4.090/1962, art. 1º, §§ 1º e 2º).

    O aviso começa no dia seguinte à posição. Ex.: 31/12 + 45 dias = 14/02 -> janeiro inteiro + 14 dias de
    fevereiro (menos de 15) = 1/12.
    """
    fim = data_posicao + timedelta(days=dias_aviso)
    if fim.year == data_posicao.year:
        return 0
    return (fim.month - 1) + (1 if fim.day >= dias_fracao else 0)


def dias_aviso_previo(meses_servico: float, p: dict) -> int:
    """30 dias + 3 por ano completo de serviço, com teto de 90 (Lei 12.506/2011)."""
    anos_completos = int(meses_servico // 12)
    return min(p["aviso_previo_dias_base"] + p["aviso_previo_dias_por_ano"] * anos_completos,
               p["aviso_previo_dias_max"])


def passivo_por_vinculo(salario: float, meses_servico: float, p: dict) -> Passivo:
    """Custo de despedir o empregado sem justa causa na posição de 31/12, conforme o art. 5º do Prov. 227.

    `salario` já é a base do art. 6º aproximada (remuneração da RAIS corrigida); `p` são as premissas resolvidas.
    """
    if salario <= 0 or meses_servico < 0:
        return Passivo()
    fr = p["dias_fracao_mes_integral"]
    anos_completos = int(meses_servico // 12)

    # I - aviso prévio indenizado proporcional
    dias_av = dias_aviso_previo(meses_servico, p)
    aviso = salario * dias_av / 30

    # III - 13º proporcional: na posição de 31/12 o do ano já foi pago; resta a projeção do aviso, pelo calendário
    if not p["decimo_terceiro_quitado_na_data_base"]:
        raise ValueError("o modelo só calcula na posição de 31/12 com o 13º do ano quitado (art. 4º do Prov. 227)")
    avos_13 = avos_13_da_projecao(p["data_posicao"], dias_av, fr)
    decimo = salario * avos_13 / 12

    # II - férias proporcionais (período aquisitivo em curso + projeção do aviso) e vencidas pendentes, + 1/3.
    # Aqui o mês é de 30 dias de propósito: o período aquisitivo conta da data de admissão, que a RAIS não traz.
    dias_periodo_em_curso = (meses_servico - 12 * anos_completos) * 30 + dias_av
    avos_fer = avos(dias_periodo_em_curso, fr)
    vencidas = 0.0
    if avos_fer >= 12:  # a projeção do aviso completa um período aquisitivo inteiro
        vencidas += 1
        avos_fer = avos(dias_periodo_em_curso - 360, fr)
    if anos_completos >= 1:
        vencidas += p["fracao_ferias_vencidas_pendentes"]
    ferias = salario * (avos_fer / 12 + vencidas) * (1 + p["terco_ferias"])

    saldo_sal = salario if p["incluir_saldo_salario"] else 0.0

    # encargos sobre as verbas em que a lei faz incidir (parágrafo único do art. 5º)
    inc = p["incidencias"]
    base_fgts = (aviso * inc["aviso_previo_indenizado"]["fgts"] + decimo * inc["decimo_terceiro"]["fgts"]
                 + ferias * inc["ferias_indenizadas"]["fgts"] + saldo_sal)
    base_inss = (aviso * inc["aviso_previo_indenizado"]["inss"] + decimo * inc["decimo_terceiro"]["inss"]
                 + ferias * inc["ferias_indenizadas"]["inss"] + saldo_sal)
    fgts_resc = p["aliquota_fgts"] * base_fgts

    # IV - multa de 40% sobre todos os depósitos do contrato (saldo estimado + depósitos da rescisão)
    saldo_fgts = (p["aliquota_fgts"] * salario * meses_servico * p["meses_remuneracao_fgts_por_ano"] / 12
                  * p["fator_correcao_saldo_fgts"])
    multa = p["multa_fgts"] * (saldo_fgts + fgts_resc)

    # V - verbas de acordo ou convenção coletiva
    cct = p["acrescimo_cct_pct"] * (aviso + decimo + ferias + multa)

    return Passivo(
        aviso_previo=aviso, decimo_terceiro=decimo, ferias=ferias, multa_fgts=multa, verbas_cct=cct,
        saldo_salario=saldo_sal, fgts_rescisorio=fgts_resc, inss_patronal=p["inss_patronal"] * base_inss,
        rat_fap=p["rat"] * p["fap"] * base_inss, dias_aviso=dias_av, avos_13=avos_13, avos_ferias=avos_fer,
        periodos_ferias_vencidas=vencidas, saldo_fgts_estimado=saldo_fgts)


def passivo_vinculos(vinculos: pd.DataFrame, p: dict) -> pd.Series:
    """Passivo total de cada vínculo (colunas `salario` e `meses_servico`). Nunca usa médias como entrada (SPEC §3.2)."""
    return pd.Series([passivo_por_vinculo(s, m, p).total for s, m in zip(vinculos["salario"], vinculos["meses_servico"])],
                     index=vinculos.index, dtype=float)


def passivo_municipio(vinculos: pd.DataFrame, p: dict, chave: str = "cod_ibge") -> pd.DataFrame:
    """Aplica `passivo_por_vinculo` a cada vínculo e agrega por `chave`: nº de vínculos, passivo total e médio por vínculo."""
    if vinculos.empty:
        return pd.DataFrame(columns=[chave, "n_vinculos", "passivo_total", "passivo_medio_vinculo"])
    v = vinculos.assign(_passivo=passivo_vinculos(vinculos, p))
    g = v.groupby(chave).agg(n_vinculos=("_passivo", "size"), passivo_total=("_passivo", "sum")).reset_index()
    g["passivo_medio_vinculo"] = g["passivo_total"] / g["n_vinculos"]
    return g
