"""Converte o .jsonl de uma sessão do Claude Code em Markdown legível.

Uso: python jsonl_para_md.py <sessao.jsonl> <saida.md> "<título>"
- Mensagens do autor: completas (sem <system-reminder>; conteúdo colado preservado).
- Respostas da IA: texto completo; ferramentas em uma linha (ação, sem resultado).
- Notificações automáticas: uma linha.
- Horário convertido para Brasília (UTC-3).
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

BRT = dt.timezone(dt.timedelta(hours=-3))


def hora(ts):
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(BRT)


def limpar_usuario(t):
    t = re.sub(r"(?s)<system-reminder>.*?</system-reminder>", "", t)
    t = re.sub(r'<pasted_content id="[^"]*">', "<!-- conteúdo colado -->\n", t)
    t = re.sub(r'</pasted_content id="[^"]*">|</pasted_content>', "\n<!-- fim do conteúdo colado -->", t)
    return t.strip()


def uma_linha(s, n=220):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def acao(nome, inp):
    if not isinstance(inp, dict):
        return f"`{nome}`"
    if nome in ("PowerShell", "Bash"):
        d = inp.get("description")
        bg = " (em segundo plano)" if inp.get("run_in_background") else ""
        return f"`{nome}`{bg}: {d + ' — ' if d else ''}`{uma_linha(inp.get('command', ''), 160)}`"
    if nome in ("Read", "Write", "Edit"):
        return f"`{nome}`: `{inp.get('file_path', '')}`"
    if nome == "Grep":
        return f"`Grep`: `{uma_linha(inp.get('pattern', ''), 100)}` em `{inp.get('path', '.')}`"
    if nome == "Glob":
        return f"`Glob`: `{inp.get('pattern', '')}`"
    if nome == "WebSearch":
        return f"`WebSearch`: {uma_linha(inp.get('query', ''))}"
    if nome == "WebFetch":
        return f"`WebFetch`: {inp.get('url', '')}"
    if nome == "ToolSearch":
        return f"`ToolSearch`: {inp.get('query', '')}"
    if nome == "Monitor":
        return f"`Monitor`: {inp.get('description', '')}"
    if nome == "AskUserQuestion":
        qs = [q.get("question", "") for q in inp.get("questions", [])]
        return f"`AskUserQuestion`: {uma_linha(' | '.join(qs))}"
    chave = next((k for k in ("description", "query", "url", "path", "prompt") if k in inp), None)
    return f"`{nome}`" + (f": {uma_linha(inp[chave])}" if chave else "")


def notificacao(t):
    s = re.search(r"<summary>(.*?)</summary>", t, re.S)
    e = re.search(r"<event>(.*?)</event>", t, re.S)
    txt = (s.group(1) if s else "") + (f" — {e.group(1)}" if e else "")
    return uma_linha(txt or t, 240)


arq, saida, titulo = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
regs = []
with open(arq, encoding="utf-8") as f:
    for l in f:
        o = json.loads(l)
        if o.get("type") in ("user", "assistant") and not o.get("isSidechain") and o.get("timestamp"):
            regs.append(o)

linhas, atual, n_aut, n_ia, n_ferr, n_not = [], None, 0, 0, 0, 0
for o in regs:
    t = hora(o["timestamp"])
    c = o["message"].get("content")
    blocos = c if isinstance(c, list) else [{"type": "text", "text": c or ""}]
    if o["type"] == "user":
        for b in blocos:
            if b.get("type") == "tool_result":
                continue
            txt = b.get("text", "") if b.get("type") == "text" else ""
            if not txt.strip():
                continue
            if "<task-notification>" in txt or txt.lstrip().startswith("[SYSTEM NOTIFICATION"):
                linhas.append(f"\n> 🔔 *{t:%d/%m %H:%M} — notificação automática (não é mensagem do autor):* {notificacao(txt)}\n")
                n_not += 1
                atual = None
                continue
            if re.match(r"\s*<ide_(opened_file|selection)>", txt):
                linhas.append(f"\n> 📎 *{t:%d/%m %H:%M} — contexto automático do editor:* {uma_linha(re.sub(r'<[^>]+>', '', txt), 200)}\n")
                continue
            limpo = limpar_usuario(txt)
            if not limpo:
                continue
            linhas.append(f"\n---\n\n## 👤 Autor — {t:%d/%m/%Y %H:%M}\n\n{limpo}\n")
            n_aut += 1
            atual = None
    else:
        for b in blocos:
            tipo = b.get("type")
            if tipo == "thinking":
                continue
            if atual != "ia":
                linhas.append(f"\n## 🤖 Claude — {t:%d/%m/%Y %H:%M}\n")
                atual = "ia"
                n_ia += 1
            if tipo == "text" and b.get("text", "").strip():
                linhas.append("\n" + b["text"].strip() + "\n")
            elif tipo == "tool_use":
                linhas.append(f"- 🔧 {t:%H:%M} {acao(b.get('name'), b.get('input'))}")
                n_ferr += 1

ini, fim = hora(regs[0]["timestamp"]), hora(regs[-1]["timestamp"])
cab = (f"# {titulo}\n\n"
       f"- **Sessão:** `{arq.stem}`\n- **Início:** {ini:%d/%m/%Y %H:%M} · **Fim:** {fim:%d/%m/%Y %H:%M} (horário de Brasília, UTC−3)\n"
       f"- **Conteúdo:** {n_aut} mensagens do autor, {n_ia} blocos de resposta da IA, {n_ferr} chamadas de ferramenta (só a ação, sem resultado), {n_not} notificações automáticas.\n"
       f"- Gerado a partir de `{arq.name}` em {dt.datetime.now(BRT):%d/%m/%Y %H:%M}. O raciocínio interno da IA não é gravado no arquivo e não aparece aqui.\n")
saida.parent.mkdir(parents=True, exist_ok=True)
saida.write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")
print(f"{saida}: {n_aut} msgs autor | {n_ia} blocos IA | {n_ferr} ferramentas | {n_not} notificações | {saida.stat().st_size/1024:,.0f} KB")
