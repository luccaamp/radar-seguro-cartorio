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

// Letra do rótulo com tamanho fixo NA TELA (px), convertida para unidades do viewBox; null se a tela não foi medida.
// Com preserveAspectRatio "meet", a escala do desenho é a MENOR entre a da largura e a da altura (o mapa tem altura
// máxima de 560 px, então muitas vezes é a altura que limita).
export function tamanhoLetra(tela, viewBox, px) {
  const escalas = [tela.largura / viewBox.largura, tela.altura / viewBox.altura].filter((e) => Number.isFinite(e) && e > 0);
  return escalas.length ? px / Math.min(...escalas) : null;
}

// Rótulos que cabem sem se sobrepor: percorre os candidatos na ordem que vieram (maior valor primeiro) e fica com os
// `max` primeiros cuja caixa estimada (largura ≈ 0,6 × letra por caractere, altura ≈ 1,2 × letra) não encosta numa já
// escolhida. É só apresentação: quem são os candidatos e onde fica cada ponto vem do Python.
export function escolherRotulos(candidatos, max, tam) {
  const caixa = (r) => {
    const w = 0.6 * tam * String(r.texto).length, h = 1.2 * tam;
    return { x0: r.x - w / 2, x1: r.x + w / 2, y0: r.y - h / 2, y1: r.y + h / 2 };
  };
  const escolhidos = [];
  for (const r of candidatos || []) {
    if (escolhidos.length >= max) break;
    const c = caixa(r);
    if (escolhidos.every(({ c: o }) => c.x1 < o.x0 || c.x0 > o.x1 || c.y1 < o.y0 || c.y0 > o.y1)) escolhidos.push({ r, c });
  }
  return escolhidos.map((e) => e.r);
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
  // contorno do estado: as mesmas áreas por baixo, com traço grosso; as de cima cobrem a parte de dentro, e só a
  // borda de fora aparece (sem calcular a união das geometrias)
  const gContorno = el(doc, "g", { class: "rd-contorno", "aria-hidden": "true" }, true);
  const gAreas = el(doc, "g", { class: "rd-areas" }, true);
  const gFundo = el(doc, "g", { class: "rd-fundo" }, true);
  const gRotulos = el(doc, "g", { class: "rd-rotulos", "aria-hidden": "true" }, true);
  let selecionado = null;
  for (const a of dados.areas || []) {
    gContorno.appendChild(el(doc, "path", { d: a.d }, true));
    const sel = a.id === dados.selecionado;
    const path = el(doc, "path", { d: a.d, "data-id": a.id, class: classeFaixa(a.faixa) + (sel ? " rd-sel" : "") }, true);
    const titulo = el(doc, "title", {}, true);
    titulo.textContent = a.texto ? `${a.nome}\n${a.texto}` : a.nome;
    path.appendChild(titulo);
    path.addEventListener("click", () => aoEscolher(a.id));
    if (sel) selecionado = path; else gAreas.appendChild(path);
  }
  if (selecionado) gAreas.appendChild(selecionado);   // por último: o contorno do selecionado fica por cima
  for (const f of dados.fundo || []) {
    gContorno.appendChild(el(doc, "path", { d: f.d }, true));
    gFundo.appendChild(el(doc, "path", { d: f.d }, true));
  }
  svg.appendChild(gContorno);
  svg.appendChild(gAreas);
  svg.appendChild(gFundo);
  svg.appendChild(gRotulos);
  raiz.appendChild(svg);
  // rótulos depois de o mapa estar na página: a largura real dá o tamanho da letra (13 px; 11 px no celular)
  const r = typeof svg.getBoundingClientRect === "function" ? svg.getBoundingClientRect() : { width: 0, height: 0 };
  const [, , vbLarg, vbAlt] = String(dados.viewBox || "").split(" ").map(Number);
  const tam = tamanhoLetra({ largura: r.width, altura: r.height }, { largura: vbLarg, altura: vbAlt },
                           r.width < 500 ? 11 : 13) ?? (dados.tamanhoRotulo || 16);
  const max = dados.maxRotulos ?? 3;
  for (const r of escolherRotulos(dados.rotulos, max, tam)) {
    const t = el(doc, "text", { x: r.x, y: r.y, "data-id": r.id, "font-size": tam, "stroke-width": tam * 0.25 }, true);
    t.textContent = r.texto;
    gRotulos.appendChild(t);
  }
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
