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
