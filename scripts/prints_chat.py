"""Capturas da página do chat (QA visual), em 1366 px e em largura de celular, nos dois modos do painel.

Sobe o Streamlit sozinho: modo completo sobre uma CÓPIA do banco (nunca o real) ou modo demonstração (sem banco, lendo
data/publico). Estados: conversa vazia, perguntas prontas, conversa com 3 perguntas (API REAL do Gemini, com a chave
do .env: ≈ 6 a 9 chamadas por modo) e chat indisponível (sem chave). A chave nunca é impressa.

Uso:
  uv run python scripts/prints_chat.py --saida docs/qa/chat/interface_depois
  uv run python scripts/prints_chat.py --saida docs/qa/chat/interface_antes --sem-abas    # página antiga
"""
import argparse
import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright  # noqa: E402

from qa_painel import BANCO_REAL, RAIZ, _porta_livre, altura_conteudo, esperar  # noqa: E402

LARGURAS = {"1366": (1366, 768), "celular": (390, 844)}
PERGUNTAS = ["quantos cartórios tem em MG?", "e qual o prêmio anual do mercado?",
             "quantas serventias serão obrigadas em 2027?"]


@contextlib.contextmanager
def servidor(modo: str, com_chave: bool):
    pasta = Path(tempfile.mkdtemp(prefix="qa_chat_"))
    env = os.environ | {"RADAR_ESTADO": str(pasta / "painel_estado.json"), "PYTHONIOENCODING": "utf-8"}
    if modo == "completo":
        shutil.copy2(BANCO_REAL, pasta / "radar.duckdb")   # o banco real só é lido (copiado)
        env["RADAR_BANCO"] = str(pasta / "radar.duckdb")
    else:
        env["RADAR_BANCO"] = str(pasta / "nao_existe.duckdb")   # sem banco: modo demonstração (data/publico)
    if not com_chave:
        env["GEMINI_API_KEY"] = ""   # vazia vale como "sem chave" (src/llm.py)
    porta = _porta_livre()
    proc = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app/Inicio.py", "--server.headless", "true",
                             "--server.port", str(porta), "--browser.gatherUsageStats", "false",
                             "--server.fileWatcherType", "none"], cwd=RAIZ, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{porta}"
    try:
        for _ in range(120):
            with contextlib.suppress(httpx.HTTPError):
                if httpx.get(f"{url}/_stcore/health", timeout=2).status_code == 200:
                    break
            time.sleep(0.5)
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(pasta, ignore_errors=True)


CONTRASTE: list[str] = []


def contraste(page, estado: str) -> None:
    """Contraste de texto (axe-core, regra color-contrast, WCAG AA 4,5:1) no conteúdo da página (fora o menu lateral,
    que é do painel). Anota cada texto abaixo do mínimo em CONTRASTE."""
    from axe_playwright_python.sync_playwright import Axe
    r = Axe().run(page, context={"include": [['[data-testid="stMain"]']]},
                  options={"runOnly": {"type": "rule", "values": ["color-contrast"]}})
    nos = [n for v in r.response["violations"] for n in v["nodes"]]
    CONTRASTE.append(f"{estado}: {len(nos)} texto(s) abaixo de 4,5:1")
    for n in nos:
        CONTRASTE.append(f"  - {n['any'][0]['message'][:160]} | {n['target'][0]}")


def foto(page, arquivo: Path, largura: str) -> None:
    w, h = LARGURAS[largura]
    page.set_viewport_size({"width": w, "height": h})
    page.wait_for_timeout(800)
    page.set_viewport_size({"width": w, "height": max(h, altura_conteudo(page))})
    page.wait_for_timeout(1000)
    page.screenshot(path=str(arquivo), full_page=True)
    page.set_viewport_size({"width": w, "height": h})
    print(arquivo.relative_to(RAIZ), flush=True)


def abrir_chat(page, url: str) -> float:
    t = time.perf_counter()
    page.goto(f"{url}/Chat")
    esperar(page, 300)
    return time.perf_counter() - t


def perguntar(page, texto: str) -> float:
    """Envia a pergunta e espera a resposta terminar: duas mensagens a mais, nenhum indicador de espera e o texto da
    última mensagem parado por 3 s (mandar outra pergunta antes interromperia esta resposta). Devolve o tempo até o
    texto parar de mudar."""
    mensagens = page.locator('[data-testid="stChatMessage"]')
    antes = mensagens.count()
    campo = page.get_by_test_id("stChatInputTextArea")
    campo.fill(texto)
    t = time.perf_counter()
    campo.press("Enter")
    ultimo, desde = None, time.perf_counter()
    while time.perf_counter() - t < 120:
        page.wait_for_timeout(250)
        if mensagens.count() < antes + 2 or page.locator(".chat-espera").count():
            ultimo, desde = None, time.perf_counter()
            continue
        agora = mensagens.last.inner_text()
        if agora != ultimo:
            ultimo, desde = agora, time.perf_counter()
        elif time.perf_counter() - desde >= 3:
            return desde - t
    page.screenshot(path=str(RAIZ / "docs/qa/chat/erro_espera.png"), full_page=True)
    raise TimeoutError(f"a resposta não terminou em 120 s ({mensagens.count()} mensagens, esperadas {antes + 2})")


def aba(page, nome: str, sem_abas: bool) -> None:
    if sem_abas:   # página antiga: as perguntas prontas ficavam num expansor
        page.get_by_text("Perguntas prontas", exact=False).first.click()
        page.wait_for_timeout(800)
        return
    page.get_by_role("tab", name=nome, exact=True).first.click()
    page.wait_for_timeout(800)


def main(saida: Path, sem_abas: bool, modos: list[str]) -> None:
    saida.mkdir(parents=True, exist_ok=True)
    tempos = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        for modo in modos:
            with servidor(modo, com_chave=True) as url:
                page = nav.new_page(viewport={"width": 1366, "height": 768}, locale="pt-BR")
                tempos.append(f"{modo}: página do chat aberta em {abrir_chat(page, url):.1f} s (primeira vez)")
                tempos.append(f"{modo}: página do chat aberta em {abrir_chat(page, url):.1f} s (de novo, com cache)")
                for larg in LARGURAS:
                    foto(page, saida / f"{modo}_{larg}_1_conversa_vazia.png", larg)
                contraste(page, f"{modo}, conversa vazia")
                aba(page, "Perguntas prontas", sem_abas)
                if not sem_abas:   # abre a primeira pergunta pronta, para a resposta entrar na captura
                    page.locator('[data-testid="stExpander"] summary').first.click()
                    page.wait_for_timeout(1000)
                for larg in LARGURAS:
                    foto(page, saida / f"{modo}_{larg}_2_perguntas_prontas.png", larg)
                contraste(page, f"{modo}, perguntas prontas")
                if not sem_abas:
                    aba(page, "Chat", sem_abas)
                for p in PERGUNTAS:
                    tempos.append(f"{modo}: '{p}' respondida na tela em {perguntar(page, p):.1f} s")
                for larg in LARGURAS:
                    foto(page, saida / f"{modo}_{larg}_3_conversa_3_perguntas.png", larg)
                contraste(page, f"{modo}, conversa com 3 perguntas")
                page.close()
            with servidor(modo, com_chave=False) as url:
                page = nav.new_page(viewport={"width": 1366, "height": 768}, locale="pt-BR")
                abrir_chat(page, url)
                for larg in LARGURAS:
                    foto(page, saida / f"{modo}_{larg}_4_chat_indisponivel.png", larg)
                contraste(page, f"{modo}, chat indisponível")
                page.close()
        nav.close()
    (saida / "tempos.txt").write_text("\n".join(tempos) + "\n", encoding="utf-8")
    (saida / "contraste.txt").write_text("\n".join(CONTRASTE) + "\n", encoding="utf-8")
    print("\n".join(tempos + CONTRASTE))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # também redirecionada (docs/erros_ia.md, 2026-10-20)
    a = argparse.ArgumentParser()
    a.add_argument("--saida", required=True)
    a.add_argument("--sem-abas", action="store_true", help="página antiga (perguntas prontas num expansor)")
    a.add_argument("--modos", default="demonstracao,completo")
    x = a.parse_args()
    main(RAIZ / x.saida, x.sem_abas, x.modos.split(","))
