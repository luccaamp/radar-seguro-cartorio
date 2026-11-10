// Testes do JavaScript do mapa clicável (D-083, src/painel/componentes/mapa.js), com o executor que já vem com o Node
// (`node --test tests/js`), sem dependências. Rodados pela suíte padrão em tests/test_mapa.py.
// O DOM é um falso mínimo (só o que o mapa.js usa). Dados SINTÉTICOS.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

// importa pelo texto (data: URL), para não depender de o Node tratar o .js como módulo ES
const fonte = readFileSync(new URL("../../src/painel/componentes/mapa.js", import.meta.url), "utf8");
const mod = await import("data:text/javascript;base64," + Buffer.from(fonte).toString("base64"));

class No {
  constructor(tag, ns = null) {
    this.tagName = tag; this.namespaceURI = ns; this.attrs = {}; this.children = []; this.listeners = {};
    this.textContent = ""; this.parentNode = null;
  }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k] ?? null; }
  appendChild(c) {
    if (c.parentNode) c.parentNode.removeChild(c);
    c.parentNode = this; this.children.push(c); return c;
  }
  removeChild(c) { this.children = this.children.filter((x) => x !== c); c.parentNode = null; return c; }
  get firstChild() { return this.children[0] ?? null; }
  addEventListener(tipo, fn) { (this.listeners[tipo] ??= []).push(fn); }
  dispatch(tipo) { for (const fn of this.listeners[tipo] ?? []) fn({ type: tipo, target: this }); }
  querySelector(sel) { return this.todos().find((n) => combina(n, sel)) ?? null; }
  querySelectorAll(sel) { return this.todos().filter((n) => combina(n, sel)); }
  todos() { return this.children.flatMap((c) => [c, ...c.todos()]); }
}

function combina(n, sel) {
  if (sel.startsWith(".")) return (n.attrs.class ?? "").split(" ").includes(sel.slice(1));
  return n.tagName === sel;
}

const doc = {
  createElement: (tag) => new No(tag),
  createElementNS: (ns, tag) => new No(tag, ns),
  createTextNode: (t) => Object.assign(new No("#text"), { textContent: t }),
};

const dados = () => ({
  viewBox: "0 0 1000 800",
  areas: [
    { id: "3100104", d: "M0 0L10 0L10 10Z", faixa: "zero", valor: 0, nome: "Município A", texto: "Déficit: R$ 0" },
    { id: "3100203", d: "M10 0L20 0L20 10Z", faixa: "3", valor: 10, nome: "Município B", texto: "Déficit: R$ 10" },
    { id: "3100302", d: "M20 0L30 0L30 10Z", faixa: "6", valor: 99, nome: "<b>C</b>", texto: "" },
  ],
  fundo: [{ d: "M0 0L5 0L5 5Z" }],
  selecionado: "3100203",
  legenda: [{ faixa: "zero", texto: "Zero" }, { faixa: "1", texto: "até R$ 1,0 mil" }],
  tituloLegenda: "Déficit de cobertura do município",
  legendaFundo: "Sem cartório no cadastro do CNJ",
  resumo: "",
  rotulos: [{ id: "3100302", texto: "<b>C</b>", x: 25, y: 5 }, { id: "3100203", texto: "Município B", x: 400, y: 400 }],
  tamanhoRotulo: 20,
});

test("contorno do estado: uma cópia de cada área e do fundo, por baixo das áreas", () => {
  const svg = mod.desenhar(new No("div"), dados(), () => {}, doc);
  const grupos = svg.children.map((g) => g.getAttribute("class"));
  assert.deepEqual(grupos, ["rd-contorno", "rd-areas", "rd-fundo", "rd-rotulos"]);   // ordem de desenho
  const contorno = svg.querySelector(".rd-contorno");
  assert.equal(contorno.children.length, 3 + 1);
  assert.equal(contorno.getAttribute("aria-hidden"), "true");
  assert.equal(contorno.children[0].listeners.click, undefined);                     // não pega o clique
});

test("tamanhoLetra: px fixos na tela viram unidades do viewBox, pela menor escala; sem medida, null", () => {
  const T = (l, a) => ({ largura: l, altura: a });
  assert.equal(mod.tamanhoLetra(T(500, 400), T(1000, 800), 13), 26);   // 500 px mostrando 1000 unidades
  assert.equal(mod.tamanhoLetra(T(1000, 1000), T(250, 250), 13), 3.25); // com zoom, a letra encolhe em unidades
  // a altura limita: 980 × 560 px mostrando 1000 × 818 → escala 560 / 818 (não 980 / 1000)
  assert.equal(mod.tamanhoLetra(T(980, 560), T(1000, 818), 14), 14 / (560 / 818));
  assert.equal(mod.tamanhoLetra(T(0, 0), T(1000, 800), 13), null);       // fora da página: usa a reserva
});

test("escolherRotulos: pula o que se sobrepõe e para no máximo, na ordem recebida", () => {
  const c = [
    { id: "a", texto: "Belo Horizonte", x: 100, y: 100 },
    { id: "b", texto: "Contagem", x: 104, y: 102 },      // em cima de "a": pula
    { id: "c", texto: "Betim", x: 300, y: 100 },
    { id: "d", texto: "Uberaba", x: 100, y: 300 },
    { id: "e", texto: "Uberlândia", x: 500, y: 500 },     // já tem 3: para
  ];
  assert.deepEqual(mod.escolherRotulos(c, 3, 10).map((r) => r.id), ["a", "c", "d"]);
  assert.deepEqual(mod.escolherRotulos(c, 0, 10), []);
  assert.deepEqual(mod.escolherRotulos(undefined, 3, 10), []);
  // letra grande: "c" passa a encostar em "a" ("a" vai até 100 + 14 × 0,6 × 40 / 2 = 268; "c" começa em 300 − 60 = 240)
  assert.deepEqual(mod.escolherRotulos(c, 3, 40).map((r) => r.id), ["a", "d", "e"]);
});

test("com a tela medida, a letra sai do tamanho na tela (13 px no computador, 11 px no celular)", () => {
  for (const [larg, px] of [[1000, 13], [400, 11]]) {
    // o <svg> "medido": getBoundingClientRect só nele
    const svg = mod.desenhar(new No("div"), dados(), () => {}, {
      ...doc,
      createElementNS: (ns, tag) => {
        const n = new No(tag, ns);
        if (tag === "svg") n.getBoundingClientRect = () => ({ width: larg, height: larg * 0.8 });   // viewBox 1000 × 800
        return n;
      },
    });
    const t = svg.querySelector(".rd-rotulos").children[0];
    assert.equal(Number(t.getAttribute("font-size")), (px * 1000) / larg);
  }
});

test("rótulos: texto puro, na posição e no tamanho que vieram do Python, com halo proporcional", () => {
  const svg = mod.desenhar(new No("div"), dados(), () => {}, doc);
  const ts = svg.querySelector(".rd-rotulos").children;
  assert.equal(ts.length, 2);
  assert.equal(ts[0].tagName, "text");
  assert.equal(ts[0].textContent, "<b>C</b>");                 // literal, nunca HTML
  assert.equal(ts[0].children.length, 0);
  assert.deepEqual([ts[0].getAttribute("x"), ts[0].getAttribute("y")], ["25", "5"]);
  assert.equal(ts[0].getAttribute("font-size"), "20");
  assert.equal(ts[0].getAttribute("stroke-width"), "5");
  const sem = mod.desenhar(new No("div"), { ...dados(), rotulos: undefined }, () => {}, doc);
  assert.equal(sem.querySelector(".rd-rotulos").children.length, 0);
});

const caminhos = (svg) => svg.querySelector(".rd-areas").children;

test("desenha um <path> SVG por área, com código, faixa e caminho", () => {
  const raiz = new No("div");
  const svg = mod.desenhar(raiz, dados(), () => {}, doc);
  assert.equal(svg.namespaceURI, "http://www.w3.org/2000/svg");
  assert.equal(svg.getAttribute("viewBox"), "0 0 1000 800");
  const ps = caminhos(svg);
  assert.equal(ps.length, 3);
  assert.deepEqual(ps.map((p) => p.getAttribute("data-id")).sort(), ["3100104", "3100203", "3100302"]);
  const a = ps.find((p) => p.getAttribute("data-id") === "3100104");
  assert.equal(a.getAttribute("d"), "M0 0L10 0L10 10Z");
  assert.equal(a.getAttribute("class"), "rd-f-zero");
  assert.equal(svg.querySelector(".rd-fundo").children.length, 1);
});

test("o selecionado ganha a classe rd-sel e é desenhado por último (contorno por cima)", () => {
  const ps = caminhos(mod.desenhar(new No("div"), dados(), () => {}, doc));
  const ultimo = ps[ps.length - 1];
  assert.equal(ultimo.getAttribute("data-id"), "3100203");
  assert.equal(ultimo.getAttribute("class"), "rd-f-3 rd-sel");
  assert.equal(ps.filter((p) => p.getAttribute("class").includes("rd-sel")).length, 1);
});

test("o clique devolve o código da área clicada, uma vez", () => {
  const escolhidos = [];
  const ps = caminhos(mod.desenhar(new No("div"), dados(), (id) => escolhidos.push(id), doc));
  ps.find((p) => p.getAttribute("data-id") === "3100302").dispatch("click");
  assert.deepEqual(escolhidos, ["3100302"]);
});

test("nome e texto vão como texto puro no balão (<title>), nunca como HTML", () => {
  const ps = caminhos(mod.desenhar(new No("div"), dados(), () => {}, doc));
  const c = ps.find((p) => p.getAttribute("data-id") === "3100302");
  const titulo = c.children.find((n) => n.tagName === "title");
  assert.equal(titulo.textContent, "<b>C</b>");             // texto literal, sem virar elemento
  assert.equal(c.children.length, 1);
  const b = ps.find((p) => p.getAttribute("data-id") === "3100203").children[0];
  assert.equal(b.textContent, "Município B\nDéficit: R$ 10");
});

test("faixa fora do esperado vira 'sem' (a classe não aceita texto arbitrário)", () => {
  const d = dados();
  d.areas[0].faixa = "1 rd-sel\" onclick=\"x";
  const ps = caminhos(mod.desenhar(new No("div"), d, () => {}, doc));
  assert.equal(ps.find((p) => p.getAttribute("data-id") === "3100104").getAttribute("class"), "rd-f-sem");
});

test("legenda com título, as faixas e o fundo", () => {
  const raiz = new No("div");
  mod.desenhar(raiz, dados(), () => {}, doc);
  const leg = raiz.querySelector(".rd-mapa-legenda");
  assert.equal(leg.querySelector(".rd-mapa-legenda-titulo").textContent, "Déficit de cobertura do município");
  const itens = leg.querySelectorAll(".rd-mapa-item");
  assert.deepEqual(itens.map((i) => i.children[1].textContent), ["Zero", "até R$ 1,0 mil", "Sem cartório no cadastro do CNJ"]);
  assert.deepEqual(itens.map((i) => i.children[0].getAttribute("class")), ["rd-f-zero", "rd-f-1", "rd-f-fundo"]);
});

test("resumo aparece só quando vem, e vira o nome acessível do mapa", () => {
  const sem = new No("div");
  mod.desenhar(sem, dados(), () => {}, doc);
  assert.equal(sem.querySelector(".rd-mapa-resumo"), null);
  assert.equal(sem.querySelector("svg").getAttribute("aria-label"), "Déficit de cobertura do município");
  const com = new No("div");
  mod.desenhar(com, { ...dados(), resumo: "Belo Horizonte concentra 30%." }, () => {}, doc);
  assert.equal(com.querySelector(".rd-mapa-resumo").textContent, "Belo Horizonte concentra 30%.");
  assert.equal(com.querySelector("svg").getAttribute("role"), "img");
});

test("desenhar de novo substitui o mapa anterior (não duplica)", () => {
  const raiz = new No("div");
  mod.desenhar(raiz, dados(), () => {}, doc);
  mod.desenhar(raiz, { ...dados(), selecionado: null }, () => {}, doc);
  assert.equal(raiz.querySelectorAll("svg").length, 1);
  assert.equal(raiz.querySelectorAll(".rd-mapa-legenda").length, 1);
});

test("entrada do componente: liga o clique ao gatilho 'municipio' do Streamlit", () => {
  const pai = new No("div");
  const raiz = pai.appendChild(new No("div"));
  raiz.setAttribute("class", "rd-mapa");
  const gatilhos = [];
  globalThis.document = doc;
  try {
    mod.default({ data: dados(), parentElement: pai, setTriggerValue: (k, v) => gatilhos.push([k, v]) });
  } finally {
    delete globalThis.document;
  }
  caminhos(raiz.querySelector("svg"))[0].dispatch("click");
  assert.equal(gatilhos.length, 1);
  assert.equal(gatilhos[0][0], "municipio");
});

test("entrada do componente sem dados ou sem a raiz não quebra", () => {
  assert.doesNotThrow(() => mod.default({ data: null, parentElement: new No("div"), setTriggerValue() {} }));
  assert.doesNotThrow(() => mod.default({ data: dados(), parentElement: new No("div"), setTriggerValue() {} }));
});
