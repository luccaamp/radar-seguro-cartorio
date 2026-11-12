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
// Uma medida menor que MEDIDA_MINIMA px é o mapa ainda se ajeitando na página (durante o carregamento ele chega a ter
// poucos px de altura): conta como "sem medida", senão 13 px na tela viram uma letra do tamanho do mapa (2026-11-11).
export const MEDIDA_MINIMA = 120;
export function tamanhoLetra(tela, viewBox, px) {
  if (!(tela.largura >= MEDIDA_MINIMA && tela.altura >= MEDIDA_MINIMA)) return null;
  const escalas = [tela.largura / viewBox.largura, tela.altura / viewBox.altura].filter((e) => Number.isFinite(e) && e > 0);
  return escalas.length ? px / Math.min(...escalas) : null;
}

// Rótulos que cabem sem se sobrepor: percorre os candidatos na ordem que vieram (maior valor primeiro) e fica com os
// `max` primeiros cuja caixa estimada (largura ≈ 0,6 × letra por caractere, altura ≈ 1,2 × letra) não encosta numa já
// escolhida. É só apresentação: quem são os candidatos e onde fica cada ponto vem do Python.
export function caixaEstimada(r, tam) {
  const w = 0.6 * tam * String(r.texto).length, h = 1.2 * tam;
  return { x0: r.x - w / 2, x1: r.x + w / 2, y0: r.y - h / 2, y1: r.y + h / 2 };
}

export function sobrepoe(a, b) {
  return !(a.x1 < b.x0 || a.x0 > b.x1 || a.y1 < b.y0 || a.y0 > b.y1);
}

export function escolherRotulos(candidatos, max, tam) {
  const escolhidos = [];
  for (const r of candidatos || []) {
    if (escolhidos.length >= max) break;
    const c = caixaEstimada(r, tam);
    if (escolhidos.every(({ c: o }) => !sobrepoe(c, o))) escolhidos.push({ r, c });
  }
  return escolhidos.map((e) => e.r);
}

// ------------------------------------------------------------------ vista: zoom e arrastar (autor, 2026-11-10)
// Uma vista é {x, y, w, h} em unidades do viewBox. ZOOM_MAX: até 12× o estado inteiro.
export const ZOOM_MAX = 12;
export const ROTULOS_MAX = 12;

export function lerVista(texto) {
  const [x, y, w, h] = String(texto || "").split(" ").map(Number);
  return [x, y, w, h].every(Number.isFinite) && w > 0 && h > 0 ? { x, y, w, h } : null;
}

export function textoVista(v) {
  return [v.x, v.y, v.w, v.h].map((n) => Math.round(n * 10) / 10).join(" ");
}

// Mantém a vista dentro do estado inteiro (com folga de meia tela para o arrastar não "bater na parede") e entre
// 1/ZOOM_MAX e 1× o tamanho do estado.
export function limitarVista(v, inteiro) {
  const w = Math.min(inteiro.w, Math.max(inteiro.w / ZOOM_MAX, v.w));
  const h = w * (v.h / v.w);
  const cx = Math.min(inteiro.x + inteiro.w, Math.max(inteiro.x, v.x + v.w / 2));
  const cy = Math.min(inteiro.y + inteiro.h, Math.max(inteiro.y, v.y + v.h / 2));
  return { x: cx - w / 2, y: cy - h / 2, w, h };
}

// Aproxima (fator > 1) ou afasta (< 1) mantendo o ponto (px, py) do viewBox no mesmo lugar da tela.
export function zoomVista(v, fator, px, py, inteiro) {
  const w = v.w / fator, h = v.h / fator;
  return limitarVista({ x: px - (px - v.x) / fator, y: py - (py - v.y) / fator, w, h }, inteiro);
}

export function moverVista(v, dx, dy, inteiro) {
  return limitarVista({ ...v, x: v.x - dx, y: v.y - dy }, inteiro);
}

// Quantos nomes mostrar: o número de base, crescendo com o zoom em relação à vista inicial (até ROTULOS_MAX); 0 fica 0.
export function maxRotulosNaVista(base, inicial, vista) {
  if (!base) return 0;
  // o teto vale para o crescimento com o zoom; uma base maior (os 27 estados no mapa do Brasil, D-088) fica como veio
  return Math.min(Math.max(ROTULOS_MAX, base), Math.max(base, Math.round(base * (inicial.w / vista.w))));
}

export function rotulosNaVista(candidatos, v) {
  return (candidatos || []).filter((r) => r.x >= v.x && r.x <= v.x + v.w && r.y >= v.y && r.y <= v.y + v.h);
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
  const inicial = lerVista(dados.viewBox);
  const inteiro = lerVista(dados.viewBoxInteiro) || inicial;
  if (inicial) raiz.appendChild(controles(doc, dados, svg, inicial, inteiro, () => vista, (v) => mostrar(v)));
  raiz.appendChild(svg);
  const medir = () => (typeof svg.getBoundingClientRect === "function" ? svg.getBoundingClientRect() : { width: 0, height: 0 });
  let vista = inicial;

  // rótulos depois de o mapa estar na página: a largura real dá o tamanho da letra (13 px; 11 px no celular); refeitos
  // a cada zoom ou arrastar, só com os candidatos que estão na tela
  const rotular = () => {
    limpar(gRotulos);
    const r = medir();
    const vb = vista || { w: 0, h: 0 };
    const tam = tamanhoLetra({ largura: r.width, altura: r.height }, { largura: vb.w, altura: vb.h },
                             r.width < 500 ? 11 : 13) ?? (dados.tamanhoRotulo || 16);
    // estado inteiro na tela vindo de uma região: os maiores do estado (rotulosInteiro); senão, os do recorte
    const noInteiro = inicial && (dados.rotulosInteiro || []).length && vb.w >= inteiro.w * 0.999;
    const base = noInteiro ? (dados.maxRotulosInteiro ?? 3) : (dados.maxRotulos ?? 3);
    const lista = noInteiro ? dados.rotulosInteiro : dados.rotulos;
    const max = inicial ? maxRotulosNaVista(base, noInteiro ? inteiro : inicial, vb) : base;
    const cand = inicial ? rotulosNaVista(lista, vb) : lista;
    // a caixa de cada nome é medida de verdade (getBBox, com folga para o halo); sem medida (testes), a estimativa
    const postas = [];
    for (const c of cand || []) {
      if (postas.length >= max) break;
      const t = el(doc, "text", { x: c.x, y: c.y, "data-id": c.id, "font-size": tam, "stroke-width": tam * 0.25 }, true);
      t.textContent = c.texto;
      gRotulos.appendChild(t);
      let caixa = null;
      try {
        const b = typeof t.getBBox === "function" ? t.getBBox() : null;
        const folga = tam * 0.3;
        if (b && b.width > 0) caixa = { x0: b.x - folga, x1: b.x + b.width + folga, y0: b.y - folga, y1: b.y + b.height + folga };
      } catch {
        caixa = null;
      }
      caixa = caixa || caixaEstimada(c, tam);
      if (postas.some((o) => sobrepoe(caixa, o))) gRotulos.removeChild(t);
      else postas.push(caixa);
    }
  };
  const mostrar = (v) => {
    vista = v;
    svg.setAttribute("viewBox", textoVista(v));
    const aproximado = v.w < inteiro.w * 0.999;
    svg.setAttribute("class", aproximado ? "rd-mapa-svg rd-aproximado" : "rd-mapa-svg");
    rotular();
  };
  if (inicial) mostrar(inicial); else rotular();
  if (inicial) arrastar(svg, inteiro, () => vista, mostrar, medir);
  // o tamanho final do mapa só existe depois que a página se ajeita: refaz os rótulos quando ele muda
  const Observador = doc.defaultView && doc.defaultView.ResizeObserver;
  if (Observador) {
    let ultima = "";
    new Observador(() => {
      const r = medir();
      const chave = `${Math.round(r.width)}x${Math.round(r.height)}`;
      if (chave !== ultima) { ultima = chave; rotular(); }
    }).observe(svg);
  }
  raiz.appendChild(legenda(doc, dados));
  return svg;
}

// Botões + e − (zoom no centro da vista) e "Ver o estado inteiro".
function controles(doc, dados, svg, inicial, inteiro, vistaAtual, mostrar) {
  const div = el(doc, "div", { class: "rd-mapa-controles" });
  const botao = (texto, rotulo, acao) => {
    const b = el(doc, "button", { type: "button", class: "rd-mapa-botao", "aria-label": rotulo, title: rotulo });
    b.textContent = texto;
    b.addEventListener("click", acao);
    div.appendChild(b);
  };
  const zoom = (f) => {
    const v = vistaAtual() || inicial;
    mostrar(zoomVista(v, f, v.x + v.w / 2, v.y + v.h / 2, inteiro));
  };
  botao("+", "Aproximar o mapa", () => zoom(1.6));
  botao("−", "Afastar o mapa", () => zoom(1 / 1.6));
  botao(dados.rotuloInteiro || "Ver o estado inteiro", dados.rotuloInteiro || "Ver o estado inteiro",
        () => mostrar(inteiro));
  return div;
}

// Arrastar para mover (mouse, caneta ou dedo). Um arrastar não vira clique no município. Sem duplo clique para
// aproximar: os dois cliques escolheriam o município.
function arrastar(svg, inteiro, vistaAtual, mostrar, medir) {
  if (typeof svg.addEventListener !== "function") return;
  let inicio = null, moveu = false;
  const escala = () => {
    const r = medir(), v = vistaAtual();
    return Math.min(r.width / v.w, r.height / v.h) || 1;
  };
  svg.addEventListener("pointerdown", (e) => {
    if (e.button !== undefined && e.button !== 0) return;
    inicio = { x: e.clientX, y: e.clientY, v: vistaAtual() };
    moveu = false;
  });
  svg.addEventListener("pointermove", (e) => {
    if (!inicio) return;
    const dx = e.clientX - inicio.x, dy = e.clientY - inicio.y;
    if (!moveu && Math.hypot(dx, dy) < 4) return;
    if (!moveu && typeof svg.setPointerCapture === "function" && e.pointerId !== undefined) svg.setPointerCapture(e.pointerId);
    moveu = true;
    const k = escala();
    mostrar(moverVista(inicio.v, dx / k, dy / k, inteiro));
  });
  const fim = () => { inicio = null; };
  svg.addEventListener("pointerup", fim);
  svg.addEventListener("pointercancel", fim);
  svg.addEventListener("click", (e) => {   // fase de captura: o clique que fecha um arrastar não escolhe município
    if (moveu) { e.stopPropagation(); e.preventDefault(); moveu = false; }
  }, true);
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
