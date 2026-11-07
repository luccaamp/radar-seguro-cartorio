"""Fase 2 (D-074): o que o Streamlit Community Cloud precisa para abrir o painel a partir do repositório."""
import re
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REQ = RAIZ / "app" / "requirements.txt"
REGERAR = ("uv export --no-dev --no-hashes --no-emit-project --no-header --format requirements-txt "
           "-o app/requirements.txt")


def _nome(n: str) -> str:
    return re.sub(r"[-_.]+", "-", n).lower()


def _requisitos() -> dict[str, str]:
    out = {}
    for linha in REQ.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Za-z0-9_.\-]+)==([^\s;]+)", linha)
        if m:
            out[_nome(m.group(1))] = m.group(2)
    return out


def test_requirements_do_painel_batem_com_o_uv_lock():
    lock = tomllib.loads((RAIZ / "uv.lock").read_text(encoding="utf-8"))
    versoes = {_nome(p["name"]): p["version"] for p in lock["package"] if "version" in p}
    req = _requisitos()
    diferentes = {n: (v, versoes.get(n)) for n, v in req.items() if versoes.get(n) != v}
    assert not diferentes, f"app/requirements.txt desatualizado; regere com: {REGERAR}\n{diferentes}"


def test_requirements_do_painel_tem_as_dependencias_do_projeto_e_nao_as_de_desenvolvimento():
    proj = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    req = _requisitos()
    principais = {_nome(re.split(r"[<>=!~\[ ;]", d)[0]) for d in proj["project"]["dependencies"]}
    dev = {_nome(re.split(r"[<>=!~\[ ;]", d)[0]) for d in proj["dependency-groups"]["dev"]}
    assert principais <= set(req), f"faltam no app/requirements.txt: {principais - set(req)}; regere com: {REGERAR}"
    assert not (dev - principais) & set(req), "dependências de desenvolvimento no app/requirements.txt"


def test_painel_publicado_le_os_dados_do_repositorio():
    """No Cloud não há data/radar.duckdb (fora do git): o painel abre no modo demonstração, com o conjunto público."""
    ignorados = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    assert "*.duckdb" in ignorados
    assert (RAIZ / "data" / "publico" / "manifesto.json").exists()


def test_fontes_embutidas_existem_com_a_licenca():
    """D-080: as fontes declaradas no config.toml estão no repositório, com a licença OFL ao lado."""
    cfg = tomllib.loads((RAIZ / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert cfg["server"]["enableStaticServing"] is True
    for f in cfg["theme"]["fontFaces"]:
        arq = RAIZ / f["url"]
        assert arq.exists(), f["url"]
    assert len(list((RAIZ / "app" / "static" / "fontes").glob("OFL_*.txt"))) == 2
