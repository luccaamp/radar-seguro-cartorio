"""Funções puras de normalização de texto usadas nas junções entre fontes."""
import re
import unicodedata


def normalizar_nome(texto: str | None) -> str:
    """Maiúsculas, sem acento, sem pontuação e com espaços simples. Ex.: "Pingo-d'Água" -> "PINGO D AGUA"."""
    if not texto:
        return ""
    s = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").upper()
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def para_float_br(valor: str | None) -> float | None:
    """Converte '1.234,56', '1234.56' ou '1234,56' em float; vazio ou não numérico vira None."""
    if valor is None:
        return None
    s = str(valor).strip()
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None
