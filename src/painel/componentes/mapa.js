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
export const ROTULOS_MAX = 60;
// Com mais de um estado na tela (o Sudeste) e pouco zoom, só os nomes dos estados (V3, D-089); os municípios
// aparecem a partir deste zoom. Os nomes dos estados somem a partir de ZOOM_SEM_ESTADOS (no estado em foco, atrapalham).
export const ZOOM_MUNICIPIOS = 1.4;
export const ZOOM_SEM_ESTADOS = 1.6;

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

// Quantos nomes mostrar: o número de base, crescendo com o QUADRADO do zoom em relação à vista inicial (a área na tela
// encolhe com o quadrado), até ROTULOS_MAX; 0 fica 0.
export function maxRotulosNaVista(base, inicial, vista) {
  if (!base) return 0;
  // o teto vale para o crescimento com o zoom; uma base maior fica como veio
  const z = inicial.w / vista.w;
  return Math.min(Math.max(ROTULOS_MAX, base), Math.max(base, Math.round(base * z * z)));
}

// O que nomear com este zoom (z = largura do estado inteiro ÷ largura da vista), com `varios` estados no mapa:
// municípios e etiquetas só a partir de ZOOM_MUNICIPIOS no Sudeste; nomes dos estados até ZOOM_SEM_ESTADOS.
export function camadasDeNomes(z, varios) {
  const municipios = !varios || z >= ZOOM_MUNICIPIOS;
  return { municipios, destaques: municipios, estados: z < ZOOM_SEM_ESTADOS };
}

export function rotulosNaVista(candidatos, v) {
  return (candidatos || []).filter((r) => r.x >= v.x && r.x <= v.x + v.w && r.y >= v.y && r.y <= v.y + v.h);
}

// Desenha o mapa dentro de `raiz` e chama `aoEscolher(id)` no clique. O teclado escolhe o município pelo seletor da
// página (851 paradas de Tab no mapa atrapalhariam mais do que ajudariam). Devolve o <svg>. Pode ser chamada de novo com dados novos: limpa o que desenhou antes.
export function desenhar(raiz, dados, aoEscolher, doc = globalThis.document) {
  limpar(raiz);
  const svg = el(doc, "svg", {
    viewBox: dados.viewBox, role: "img", preserveAspectRatio: "xMidYMid meet",
    "aria-label": dados.resumo || dados.tituloLegenda || "Mapa",
  }, true);
  // camadas (V3, D-089): os estados vizinhos em cinza, por baixo; os municípios; os sem cartório; as divisas finas dos
  // estados, por cima (não pegam o clique); os nomes
  const estados = dados.estados || [];
  const varios = estados.filter((e) => e.ativo).length > 1;
  const gVizinhos = el(doc, "g", { class: "rd-vizinhos", "aria-hidden": "true" }, true);
  const gAreas = el(doc, "g", { class: "rd-areas" }, true);
  const gFundo = el(doc, "g", { class: "rd-fundo" }, true);
  const gDivisas = el(doc, "g", { class: "rd-divisas", "aria-hidden": "true" }, true);
  const gRotulos = el(doc, "g", { class: "rd-rotulos", "aria-hidden": "true" }, true);
  for (const e of estados) (e.ativo ? gDivisas : gVizinhos).appendChild(el(doc, "path", { d: e.d }, true));
  let selecionado = null;
  const caminhos = [];   // [path, faixa, classe] para destacar uma faixa pela legenda
  for (const a of dados.areas || []) {
    const sel = a.id === dados.selecionado;
    const classe = classeFaixa(a.faixa) + (sel ? " rd-sel" : "");
    const path = el(doc, "path", { d: a.d, "data-id": a.id, class: classe }, true);
    const titulo = el(doc, "title", {}, true);
    titulo.textContent = a.texto ? `${a.nome}\n${a.texto}` : a.nome;
    path.appendChild(titulo);
    path.addEventListener("click", () => aoEscolher(a.id));
    caminhos.push([path, String(a.faixa), classe]);
    if (sel) selecionado = path; else gAreas.appendChild(path);
  }
  if (selecionado) gAreas.appendChild(selecionado);   // por último: o contorno do selecionado fica por cima
  for (const f of dados.fundo || []) gFundo.appendChild(el(doc, "path", { d: f.d }, true));
  for (const g of [gVizinhos, gAreas, gFundo, gDivisas, gRotulos]) svg.appendChild(g);
  const inicial = lerVista(dados.viewBox);
  const inteiro = lerVista(dados.viewBoxInteiro) || inicial;
  if (inicial) raiz.appendChild(barra(doc, dados, () => mostrar(inteiro)));
  // a vista: o mapa e os cartões por cima dele (no celular, o total e o resumo vão para baixo do mapa, pelo CSS)
  const caixaVista = el(doc, "div", { class: "rd-mapa-vista" });
  caixaVista.appendChild(svg);
  if (inicial) caixaVista.appendChild(botoesZoom(doc, inicial, inteiro, () => vista, (v) => mostrar(v)));
  if (dados.info) caixaVista.appendChild(cartaoInfo(doc, dados.info));
  if (dados.resumo) caixaVista.appendChild(cartaoResumo(doc, dados.resumo, () => rotular()));
  raiz.appendChild(caixaVista);
  const medir = () => (typeof svg.getBoundingClientRect === "function" ? svg.getBoundingClientRect() : { width: 0, height: 0 });
  let vista = inicial;

  // rótulos depois de o mapa estar na página: a largura real dá o tamanho da letra (13 px; 11 px no celular); refeitos
  // a cada zoom ou arrastar, só com os candidatos que estão na tela. Ordem de prioridade: as etiquetas dos maiores,
  // os nomes dos estados e os nomes dos municípios; nenhum encosta noutro nem fica atrás de um cartão.
  const rotular = () => {
    limpar(gRotulos);
    const r = medir();
    const vb = vista || { x: 0, y: 0, w: 0, h: 0 };
    const tam = tamanhoLetra({ largura: r.width, altura: r.height }, { largura: vb.w, altura: vb.h },
                             r.width < 500 ? 11 : 13) ?? (dados.tamanhoRotulo || 16);
    const z = inicial && inteiro ? inteiro.w / vb.w : 1;
    const camadas = camadasDeNomes(z, varios);
    // estado inteiro na tela vindo de uma região: os maiores do estado (rotulosInteiro); senão, os do recorte
    const noInteiro = inicial && (dados.rotulosInteiro || []).length && vb.w >= inteiro.w * 0.999;
    const base = noInteiro ? (dados.maxRotulosInteiro ?? 3) : (dados.maxRotulos ?? 3);
    const lista = noInteiro ? dados.rotulosInteiro : dados.rotulos;
    const max = !camadas.municipios ? 0 : inicial ? maxRotulosNaVista(base, noInteiro ? inteiro : inicial, vb) : base;
    const cand = inicial ? rotulosNaVista(lista, vb) : (lista || []);
    const postas = ocupadosPelosCartoes(caixaVista, r, vb);
    const medida = (t, folga) => {   // a caixa medida de verdade (getBBox); sem medida (testes), null
      try {
        const b = typeof t.getBBox === "function" ? t.getBBox() : null;
        return b && b.width > 0 ? { x0: b.x - folga, x1: b.x + b.width + folga, y0: b.y - folga, y1: b.y + b.height + folga } : null;
      } catch {
        return null;
      }
    };
    const livre = (c) => !postas.some((o) => sobrepoe(c, o));
    // quanto deslocar na horizontal para a caixa não sair pela borda da vista (no celular, "Espírito Santo" cortava)
    const paraDentro = (c) => (!inicial ? 0 : c.x0 < vb.x ? Math.min(vb.x - c.x0, vb.x + vb.w - c.x1)
                                         : c.x1 > vb.x + vb.w ? Math.max(vb.x + vb.w - c.x1, vb.x - c.x0) : 0);
    const mover = (c, dx) => ({ ...c, x0: c.x0 + dx, x1: c.x1 + dx });
    // 1) etiquetas "▲ nome · R$" nos de maior valor; se o lugar estiver ocupado, tentam logo acima e abaixo
    if (camadas.destaques) {
      for (const c of cand.filter((x) => x.valor)) {
        const g = el(doc, "g", { class: "rd-destaque", "data-id": c.id }, true);
        const fundo = el(doc, "rect", {}, true);
        const t = el(doc, "text", { x: c.x, y: c.y, "font-size": tam }, true);
        const nome = el(doc, "tspan", {}, true);
        nome.textContent = `▲ ${c.texto} `;
        const valor = el(doc, "tspan", { class: "rd-destaque-valor" }, true);
        valor.textContent = `· ${c.valor}`;
        t.appendChild(nome); t.appendChild(valor); g.appendChild(fundo); g.appendChild(t); gRotulos.appendChild(g);
        const folga = tam * 0.45;
        const posta = [0, -1.9, 1.9].some((dy) => {
          t.setAttribute("x", c.x);
          t.setAttribute("y", c.y + dy * tam);
          let caixa = medida(t, folga) || caixaEstimada({ x: c.x, y: c.y + dy * tam, texto: `▲ ${c.texto} · ${c.valor}` }, tam);
          const dx = paraDentro(caixa);
          if (dx) { t.setAttribute("x", c.x + dx); caixa = mover(caixa, dx); }
          if (!livre(caixa)) return false;
          postas.push(caixa);
          for (const [k, v] of Object.entries({ x: caixa.x0, y: caixa.y0, width: caixa.x1 - caixa.x0,
                                                 height: caixa.y1 - caixa.y0, rx: (caixa.y1 - caixa.y0) / 2 })) fundo.setAttribute(k, v);
          return true;
        });
        if (!posta) gRotulos.removeChild(g);
      }
    }
    const nomear = (x, y, texto, classe, px, id) => {
      const t = el(doc, "text", { x, y, class: classe, "font-size": px, "stroke-width": px * 0.25, ...(id ? { "data-id": id } : {}) }, true);
      t.textContent = texto;
      gRotulos.appendChild(t);
      let caixa = medida(t, px * 0.3) || caixaEstimada({ x, y, texto }, px);
      const dx = paraDentro(caixa);
      if (dx) { t.setAttribute("x", x + dx); caixa = mover(caixa, dx); }
      if (livre(caixa)) { postas.push(caixa); return true; }
      gRotulos.removeChild(t);
      return false;
    };
    // 2) os nomes dos estados (com pouco zoom); os vizinhos, em cinza e só a sigla
    if (camadas.estados && inicial) {
      for (const e of rotulosNaVista(estados, vb)) nomear(e.x, e.y, e.nome, e.ativo ? "rd-uf" : "rd-uf-vizinho", tam, null);
    }
    // 3) os municípios: mais nomes quanto maior o zoom
    let n = 0;
    for (const c of cand) {
      if (n >= max) break;
      if (c.valor && camadas.destaques) continue;   // já tem a etiqueta (ou não coube nem com ela)
      if (nomear(c.x, c.y, c.texto, "", tam, c.id)) n++;
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
  // clicar numa faixa da legenda destaca só os municípios dela; clicar de novo volta ao normal
  raiz.appendChild(legenda(doc, dados, (faixa) => {
    for (const [path, f, classe] of caminhos) path.setAttribute("class", faixa === null || f === faixa ? classe : classe + " rd-apagado");
  }));
  return svg;
}

function botao(doc, texto, rotulo, acao) {
  const b = el(doc, "button", { type: "button", class: "rd-mapa-botao", "aria-label": rotulo, title: rotulo });
  b.textContent = texto;
  b.addEventListener("click", acao);
  return b;
}

// Acima do mapa: "Ver o estado inteiro" (ou "Ver o mapa inteiro").
function barra(doc, dados, verInteiro) {
  const div = el(doc, "div", { class: "rd-mapa-controles" });
  const texto = dados.rotuloInteiro || "Ver o estado inteiro";
  div.appendChild(botao(doc, texto, texto, verInteiro));
  return div;
}

// No canto do mapa (V3): + e − (zoom no centro da vista).
function botoesZoom(doc, inicial, inteiro, vistaAtual, mostrar) {
  const div = el(doc, "div", { class: "rd-mapa-cartao rd-mapa-zoom" });
  const zoom = (f) => {
    const v = vistaAtual() || inicial;
    mostrar(zoomVista(v, f, v.x + v.w / 2, v.y + v.h / 2, inteiro));
  };
  div.appendChild(botao(doc, "+", "Aproximar o mapa", () => zoom(1.6)));
  div.appendChild(botao(doc, "−", "Afastar o mapa", () => zoom(1 / 1.6)));
  return div;
}

// No alto do mapa (V3): o total do que está na tela ({titulo, valor, nota}, já escritos pelo Python).
function cartaoInfo(doc, info) {
  const div = el(doc, "div", { class: "rd-mapa-cartao rd-mapa-info" });
  for (const [chave, classe] of [["titulo", "rd-mapa-info-k"], ["valor", "rd-mapa-info-v"], ["nota", "rd-mapa-info-s"]]) {
    if (!info[chave]) continue;
    const d = el(doc, "div", { class: classe });
    d.textContent = info[chave];
    div.appendChild(d);
  }
  return div;
}

// Embaixo, à esquerda (V3): o resumo em uma frase, num cartão que se pode fechar (libera espaço para os nomes).
function cartaoResumo(doc, resumo, depoisDeFechar) {
  const div = el(doc, "div", { class: "rd-mapa-cartao rd-mapa-resumo-c" });
  const tag = el(doc, "span", { class: "rd-mapa-tag" });
  tag.textContent = "Resumo";
  const p = el(doc, "p", { class: "rd-mapa-resumo" });
  p.textContent = resumo;
  const fechar = el(doc, "button", { type: "button", class: "rd-mapa-fechar", "aria-label": "Fechar o resumo",
                                      title: "Fechar o resumo" });
  fechar.textContent = "×";
  fechar.addEventListener("click", () => {
    div.setAttribute("hidden", "");
    div.hidden = true;
    depoisDeFechar();
  });
  div.appendChild(tag); div.appendChild(p); div.appendChild(fechar);
  return div;
}

// As caixas dos cartões que estão POR CIMA do mapa, em unidades do viewBox, para nenhum nome ficar atrás deles (no
// celular os cartões ficam embaixo do mapa e não cruzam a caixa dele). Sem medida (testes), nenhuma.
function ocupadosPelosCartoes(caixaVista, r, vb) {
  if (!r.width || !r.height || typeof caixaVista.querySelectorAll !== "function") return [];
  const k = Math.min(r.width / vb.w, r.height / vb.h);
  if (!Number.isFinite(k) || k <= 0) return [];
  const ox = (r.width - vb.w * k) / 2, oy = (r.height - vb.h * k) / 2, m = 4;
  const caixas = [];
  for (const c of caixaVista.querySelectorAll(".rd-mapa-cartao")) {
    if (c.hidden || typeof c.getBoundingClientRect !== "function") continue;
    const b = c.getBoundingClientRect();
    if (!b.width || b.bottom <= r.top || b.top >= r.bottom) continue;
    caixas.push({ x0: vb.x + (b.left - m - r.left - ox) / k, x1: vb.x + (b.right + m - r.left - ox) / k,
                  y0: vb.y + (b.top - m - r.top - oy) / k, y1: vb.y + (b.bottom + m - r.top - oy) / k });
  }
  return caixas;
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

// Legenda (V1/V3): as faixas lado a lado, cada uma com o texto e, se veio, quantas áreas tem. Cada faixa é um botão que
// destaca só as áreas dela (`aoFiltrar(faixa)`; null volta ao normal). O fundo (sem cartório) não é botão.
function legenda(doc, dados, aoFiltrar = () => {}) {
  const div = el(doc, "div", { class: "rd-mapa-legenda" });
  if (dados.tituloLegenda) {
    const t = el(doc, "span", { class: "rd-mapa-legenda-titulo" });
    t.textContent = dados.tituloLegenda;
    div.appendChild(t);
  }
  const itens = [...(dados.legenda || [])];
  if (dados.legendaFundo) itens.push({ faixa: "fundo", texto: dados.legendaFundo, n: dados.nFundo });
  const botoes = [];
  let ativa = null;
  for (const item of itens) {
    const fundo = item.faixa === "fundo";
    const span = el(doc, fundo ? "span" : "button", fundo ? { class: "rd-mapa-item" }
      : { type: "button", class: "rd-mapa-item", "aria-pressed": "false", title: "Destacar só esta faixa" });
    const cor = el(doc, "i", { class: fundo ? "rd-f-fundo" : classeFaixa(item.faixa), "aria-hidden": "true" });
    span.appendChild(cor);
    span.appendChild(doc.createTextNode(item.texto));
    if (dados.unidadeLegenda && Number.isFinite(item.n)) {
      const n = el(doc, "span", { class: "rd-mapa-n" });
      n.textContent = `${Number(item.n).toLocaleString("pt-BR")} ${dados.unidadeLegenda}`;
      span.appendChild(n);
    }
    if (!fundo) {
      const faixa = String(item.faixa);
      botoes.push([span, faixa]);
      span.addEventListener("click", () => {
        ativa = ativa === faixa ? null : faixa;
        for (const [b, f] of botoes) b.setAttribute("aria-pressed", String(f === ativa));
        aoFiltrar(ativa);
      });
    }
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
