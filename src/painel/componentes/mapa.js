// Mapa clicável do painel (D-083). Só desenha o que o Python manda (src/painel/mapa.py) e avisa o clique.
// Regras: nenhum cálculo de dado aqui; nenhum innerHTML com texto dos dados (só textContent e atributos).
// Testes: tests/js/mapa.test.mjs (node --test), rodados pelo tests/test_mapa.py.

const NS = "http://www.w3.org/2000/svg";
const FAIXA_OK = /^(zero|sem|[1-9])$/;

function limpar(no) {
  while (no.firstChild) no.removeChild(no.firstChild);
}

function el(doc, tag, attrs = {}, svg = false) {
  const n = svg ? doc.createElementNS(NS, tag) : doc.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, String(v));
  return n;
}

function classeFaixa(faixa) {
  return "rd-f-" + (FAIXA_OK.test(String(faixa)) ? String(faixa) : "sem");
}

// Desenha o mapa dentro de `raiz` e chama `aoEscolher(id)` no clique. O teclado escolhe o município pelo seletor da
// página (851 paradas de Tab no mapa atrapalhariam mais do que ajudariam). Devolve o <svg>. Pode ser chamada de novo com dados novos: limpa o que desenhou antes.
export function desenhar(raiz, dados, aoEscolher, doc = globalThis.document) {
  limpar(raiz);
  if (dados.resumo) {
    const p = el(doc, "p", { class: "rd-mapa-resumo" });
    p.textContent = dados.resumo;
    raiz.appendChild(p);
  }
  const svg = el(doc, "svg", {
    viewBox: dados.viewBox, role: "img", preserveAspectRatio: "xMidYMid meet",
    "aria-label": dados.resumo || dados.tituloLegenda || "Mapa",
  }, true);
  const gAreas = el(doc, "g", { class: "rd-areas" }, true);
  const gFundo = el(doc, "g", { class: "rd-fundo" }, true);
  let selecionado = null;
  for (const a of dados.areas || []) {
    const sel = a.id === dados.selecionado;
    const path = el(doc, "path", { d: a.d, "data-id": a.id, class: classeFaixa(a.faixa) + (sel ? " rd-sel" : "") }, true);
    const titulo = el(doc, "title", {}, true);
    titulo.textContent = a.texto ? `${a.nome}\n${a.texto}` : a.nome;
    path.appendChild(titulo);
    path.addEventListener("click", () => aoEscolher(a.id));
    if (sel) selecionado = path; else gAreas.appendChild(path);
  }
  if (selecionado) gAreas.appendChild(selecionado);   // por último: o contorno do selecionado fica por cima
  for (const f of dados.fundo || []) gFundo.appendChild(el(doc, "path", { d: f.d }, true));
  svg.appendChild(gAreas);
  svg.appendChild(gFundo);
  raiz.appendChild(svg);
  raiz.appendChild(legenda(doc, dados));
  return svg;
}

function legenda(doc, dados) {
  const div = el(doc, "div", { class: "rd-mapa-legenda" });
  if (dados.tituloLegenda) {
    const t = el(doc, "span", { class: "rd-mapa-legenda-titulo" });
    t.textContent = dados.tituloLegenda;
    div.appendChild(t);
  }
  const itens = [...(dados.legenda || [])];
  if (dados.legendaFundo) itens.push({ faixa: "fundo", texto: dados.legendaFundo });
  for (const item of itens) {
    const span = el(doc, "span", { class: "rd-mapa-item" });
    const cor = el(doc, "i", { class: item.faixa === "fundo" ? "rd-f-fundo" : classeFaixa(item.faixa), "aria-hidden": "true" });
    span.appendChild(cor);
    span.appendChild(doc.createTextNode(item.texto));
    div.appendChild(span);
  }
  return div;
}

// Ponto de entrada do st.components.v2: recebe os dados do Python e devolve o clique como gatilho "municipio".
export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  const raiz = parentElement.querySelector(".rd-mapa");
  if (!raiz || !data) return;
  desenhar(raiz, data, (id) => setTriggerValue("municipio", id));
}
