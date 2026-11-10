// Tema do painel (2026-11-10). O visitante escolhe o tema no menu do Streamlit (⋮ → System, Light ou Dark); o
// Streamlit guarda a escolha no navegador e troca os próprios botões, mas não avisa o servidor. Este componente,
// invisível, lê o tema ativo, marca o <html> com data-rd-tema="claro" ou "escuro" (o estilo.css troca as cores na
// hora) e manda o tema ao Python, que redesenha os gráficos (src/painel/ui.tema). Nenhum dado aqui.
// Testes: tests/js/tema.test.mjs (node --test), rodados pelo tests/test_tema.py.

// Escolha guardada pelo Streamlit para a página: "Light", "Dark", "System" (texto JSON) ou um objeto com `name`.
export function escolhaDoStreamlit(armazenamento, caminho) {
  let bruto = null;
  try {
    bruto = armazenamento.getItem(`stActiveTheme-${caminho}-v2`);
  } catch {
    return "System";
  }
  if (bruto === null || bruto === undefined) return "System";
  let v;
  try {
    v = JSON.parse(bruto);
  } catch {
    v = bruto;
  }
  const nome = typeof v === "string" ? v : (v && (v.name || v.base)) || "System";
  return String(nome);
}

const PREFIXO = "stActiveTheme-";

// Todas as escolhas guardadas pelo Streamlit, {chave: texto bruto}.
export function lerChaves(armazenamento) {
  const out = {};
  try {
    for (let i = 0; i < armazenamento.length; i++) {
      const k = armazenamento.key(i);
      if (k && k.startsWith(PREFIXO)) out[k] = armazenamento.getItem(k);
    }
  } catch {
    // armazenamento bloqueado: fica vazio (vale o sistema)
  }
  return out;
}

// O Streamlit guarda a escolha só na chave da página em que o menu foi usado, mas a aplica ao app inteiro até a
// página ser recarregada. Por isso: ao carregar, vale a chave da página (o que o Streamlit leu); depois, qualquer
// chave que mude é uma escolha nova, que passa a valer e deve ser copiada para as outras chaves (`gravar`).
// `antes`: {escolha, chaves} da checagem anterior neste documento, ou null.
// `bruto`: o texto guardado da escolha em vigor (para gravar na chave de cada página visitada; null = nenhuma escolha).
export function proximaEscolha(antes, chaves, caminho) {
  const chave = `${PREFIXO}${caminho}-v2`;
  const daPagina = escolhaDoStreamlit({ getItem: (k) => (k in chaves ? chaves[k] : null) }, caminho);
  if (!antes) return { escolha: daPagina, bruto: chave in chaves ? chaves[chave] : null, chaves: { ...chaves }, gravar: null };
  for (const [k, v] of Object.entries(chaves)) {
    if (antes.chaves[k] !== v) {
      const nova = escolhaDoStreamlit({ getItem: () => v }, "");
      return { escolha: nova, bruto: v, chaves: { ...chaves }, gravar: v };
    }
  }
  const gravar = antes.bruto !== null && chaves[chave] !== antes.bruto ? antes.bruto : null;   // página nova visitada
  return { escolha: antes.escolha, bruto: antes.bruto, chaves: { ...chaves }, gravar };
}

// "claro" ou "escuro": a escolha do menu; "System" (ou desconhecida) segue o sistema.
export function temaAtivo(escolha, sistemaEscuro) {
  if (/light|claro/i.test(escolha)) return "claro";
  if (/dark|escuro/i.test(escolha)) return "escuro";
  return sistemaEscuro ? "escuro" : "claro";
}

export default function (component) {
  const { data, setStateValue, parentElement } = component;
  const doc = parentElement.ownerDocument;
  const win = doc.defaultView;
  const html = doc.documentElement;
  const consulta = win.matchMedia ? win.matchMedia("(prefers-color-scheme: dark)") : null;
  let enviado = (data && data.atual) || "";

  const aplicar = () => {
    let ls = null;
    try {
      ls = win.localStorage;
    } catch {
      ls = null;
    }
    const chaves = ls ? lerChaves(ls) : {};
    const estado = proximaEscolha(win.__rdTema || null, chaves, win.location.pathname);
    if (estado.gravar !== null && ls) {
      try {
        for (const k of Object.keys(chaves)) if (chaves[k] !== estado.gravar) ls.setItem(k, estado.gravar);
        ls.setItem(`${PREFIXO}${win.location.pathname}-v2`, estado.gravar);
        estado.chaves = lerChaves(ls);
      } catch {
        // sem gravar: a escolha vale até recarregar
      }
    }
    win.__rdTema = { escolha: estado.escolha, bruto: estado.bruto, chaves: estado.chaves };
    const t = temaAtivo(estado.escolha, consulta && consulta.matches);
    if (html.getAttribute("data-rd-tema") !== t) html.setAttribute("data-rd-tema", t);
    if (t !== enviado) {
      enviado = t;
      setStateValue("tema", t);   // o Python roda a página de novo com o tema certo (gráficos)
    }
  };
  aplicar();
  const relogio = win.setInterval(aplicar, 400);   // a troca no menu não dispara evento; uma checagem leve basta
  if (consulta && consulta.addEventListener) consulta.addEventListener("change", aplicar);
  return () => {
    win.clearInterval(relogio);
    if (consulta && consulta.removeEventListener) consulta.removeEventListener("change", aplicar);
  };
}
