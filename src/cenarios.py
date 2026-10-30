"""Cenários salvos pelo painel, num arquivo próprio (D-034): o banco do pipeline é só leitura para o painel.

Arquivo: data/painel_estado.json (ou a variável RADAR_ESTADO), fora do git, dos pacotes e do conjunto público.
Formato:
  {"formato": 1, "cenarios": [{"id", "nome", "criado_em", "versao_premissas", "cenario_stf", "regra_classe",
                               "metodo_rateio", "nivel", "ajustes", "premissas_alteradas", "resultado"}]}
- `versao_premissas` é a versão vigente no banco (a da carga) e `premissas_alteradas` é o diff
  {premissa: {"de", "para"}} sobre ela. O painel não cria versão de premissas: só o pipeline, a partir da semente.
- Arquivo ausente: começa vazio e é criado no primeiro "Salvar".
- Arquivo corrompido: o painel abre com um aviso e a lista vazia; no próximo "Salvar" o arquivo ruim é movido
  (nunca apagado) para `painel_estado.json.corrompido-AAAAMMDD-HHMMSS` e um novo é gravado.
- Gravação atômica (arquivo temporário + troca) e uma trava por processo para dois "Salvar" ao mesmo tempo.
"""
import datetime as dt
import json
import os
import threading
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
FORMATO = 1
_TRAVA = threading.Lock()


def caminho() -> Path:
    """RADAR_ESTADO aponta para outro arquivo (testes e galeria usam um temporário). Lido a cada chamada."""
    return Path(os.environ.get("RADAR_ESTADO") or RAIZ / "data" / "painel_estado.json")


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1,
                      default=lambda o: o.isoformat() if hasattr(o, "isoformat") else str(o))


def ler(arquivo: Path | None = None) -> tuple[list[dict], str | None]:
    """(cenários, aviso). O aviso é None, ou o texto a mostrar quando o arquivo não pôde ser lido."""
    arquivo = arquivo or caminho()
    if not arquivo.exists():
        return [], None
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        if not isinstance(dados, dict) or not isinstance(dados.get("cenarios"), list):
            raise ValueError("estrutura inesperada")
        return dados["cenarios"], None
    except (OSError, ValueError) as e:
        return [], (f"Não foi possível ler os cenários salvos ({arquivo.name}: {e}). O painel segue sem eles; "
                    "ao salvar um cenário, o arquivo atual é guardado ao lado com o sufixo '.corrompido-…'.")


def salvar(cenario: dict, arquivo: Path | None = None) -> int:
    """Acrescenta o cenário (sem 'id' e 'criado_em', que são preenchidos aqui) e devolve o id novo."""
    arquivo = arquivo or caminho()
    with _TRAVA:
        cenarios, aviso = ler(arquivo)
        if aviso:   # guarda o arquivo ruim para análise, em vez de sobrescrever
            arquivo.replace(arquivo.with_name(f"{arquivo.name}.corrompido-{dt.datetime.now():%Y%m%d-%H%M%S}"))
        novo = max((int(c["id"]) for c in cenarios), default=0) + 1
        cenarios.append({"id": novo, "criado_em": dt.datetime.now().replace(microsecond=0), **cenario})
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        temp = arquivo.with_name(arquivo.name + ".novo")
        temp.write_text(_json({"formato": FORMATO, "cenarios": cenarios}), encoding="utf-8")
        temp.replace(arquivo)
    return novo
