// Botão de tema do painel (V5 .seg: Claro · Escuro · Sistema), no canto do topo de todas as páginas (2026-11-11).
// Substitui o menu ⋮ do Streamlit, que no link público (moldura do Streamlit Cloud) não oferece a troca (erros_ia.md,
// D-084). O tema padrão é o claro. A escolha fica no navegador ("radar-tema") e vale para o painel inteiro:
// - marca o <html> com data-rd-tema="claro" ou "escuro" (o estilo.css troca as cores na hora);
// - grava a mesma escolha na chave do Streamlit da página (stActiveTheme-<caminho>-v2: "Light", "Dark" ou "System"),
//   para os componentes nativos (seletores, controles, chat) seguirem; o Streamlit só lê essa chave ao carregar, então,
//   quando ela muda, a página recarrega uma vez;
// - manda o tema ao Python, que redesenha os gráficos (src/painel/ui.tema).
// Nenhum dado aqui. Testes: tests/js/tema.test.mjs (node --test).

export const CHAVE = "radar-tema";
export const OPCOES = [["claro", "Claro"], ["escuro", "Escuro"], ["sistema", "Sistema"]];
const NOME_STREAMLIT = { claro: "Light", escuro: "Dark", sistema: "System" };

// A escolha guardada ("claro", "escuro" ou "sistema"); sem escolha ou armazenamento bloqueado: "claro".
export function escolhaGuardada(armazenamento) {
  let v = null;
  try {
    v = armazenamento.getItem(CHAVE);
  } catch {
    v = null;
  }
  return v in NOME_STREAMLIT ? v : "claro";
}

// "claro" ou "escuro": "sistema" segue a preferência do aparelho.
export function temaAtivo(escolha, sistemaEscuro) {
  if (escolha === "escuro") return "escuro";
  if (escolha === "sistema") return sistemaEscuro ? "escuro" : "claro";
  return "claro";
}

// O texto que o Streamlit guarda para a escolha (JSON de "Light", "Dark" ou "System").
export function valorStreamlit(escolha) {
  return JSON.stringify(NOME_STREAMLIT[escolha] || "Light");
}

// Grava a escolha na chave do Streamlit desta página. true quando a chave mudou (o Streamlit carregou com outro tema e
// a página precisa recarregar).
export function sincronizarStreamlit(armazenamento, caminho, escolha) {
  const chave = `stActiveTheme-${caminho}-v2`;
  const valor = valorStreamlit(escolha);
  try {
    if (armazenamento.getItem(chave) === valor) return false;
    armazenamento.setItem(chave, valor);
    return armazenamento.getItem(chave) === valor;   // armazenamento que não grava: não recarrega (evita laço)
  } catch {
    return false;
  }
}

export default function (component) {
  const { data, setStateValue, parentElement } = component;
  const doc = parentElement.ownerDocument;
  const win = doc.defaultView;
  const html = doc.documentElement;
  const consulta = win.matchMedia ? win.matchMedia("(prefers-color-scheme: dark)") : null;
  let ls = null;
  try {
    ls = win.localStorage;
  } catch {
    ls = null;
  }
  const guarda = ls || { getItem: () => null, setItem() {} };
  let enviado = (data && data.atual) || "";
  let escolha = escolhaGuardada(guarda);

  const raiz = parentElement.querySelector ? parentElement.querySelector(".rd-tema") : null;
  const marcarBotoes = () => {
    if (!raiz) return;
    for (const b of raiz.querySelectorAll("button")) b.setAttribute("aria-pressed", String(b.dataset.t === escolha));
  };

  const aplicar = () => {
    const t = temaAtivo(escolha, consulta && consulta.matches);
    if (html.getAttribute("data-rd-tema") !== t) html.setAttribute("data-rd-tema", t);
    marcarBotoes();
    if (t !== enviado) {
      enviado = t;
      setStateValue("tema", t);   // o Python roda a página de novo com o tema certo (gráficos)
    }
  };

  // O Streamlit já carregou com o tema da chave desta página: se ela não bate com a escolha, recarrega uma vez.
  if (ls && sincronizarStreamlit(ls, win.location.pathname, escolha)) {
    aplicar();
    win.location.reload();
    return () => {};
  }

  if (raiz) {
    raiz.onclick = (ev) => {
      const b = ev.target && ev.target.closest ? ev.target.closest("button[data-t]") : null;
      if (!b || b.dataset.t === escolha) return;
      escolha = b.dataset.t;
      try {
        guarda.setItem(CHAVE, escolha);
      } catch {
        // sem gravar: vale até sair da página
      }
      aplicar();
      if (ls && sincronizarStreamlit(ls, win.location.pathname, escolha)) win.location.reload();
    };
  }
  aplicar();
  if (consulta && consulta.addEventListener) consulta.addEventListener("change", aplicar);
  return () => {
    if (consulta && consulta.removeEventListener) consulta.removeEventListener("change", aplicar);
  };
}
