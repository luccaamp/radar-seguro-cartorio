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
    this.textContent = ""; this.parentNode = null; this.style = {};
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

const ESTADOS = [
  { uf: "MG", nome: "Minas Gerais", d: "M0 0L500 0L500 800Z", x: 250, y: 400, ativo: true },
  { uf: "SP", nome: "São Paulo", d: "M500 0L1000 0L1000 800Z", x: 750, y: 400, ativo: true },
  { uf: "GO", nome: "GO", d: "M0 0L-100 0L-100 100Z", x: 50, y: 50, ativo: false },
];

test("camadas (V3): vizinhos por baixo, municípios, sem cartório, divisas por cima, nomes", () => {
  const svg = mod.desenhar(new No("div"), { ...dados(), estados: ESTADOS }, () => {}, doc);
  const grupos = svg.children.map((g) => g.getAttribute("class"));
  // ordem de desenho; rd-fora: os municípios dos outros estados da região (vazio aqui)
  assert.deepEqual(grupos, ["rd-vizinhos", "rd-fora", "rd-areas", "rd-fundo", "rd-divisas", "rd-rotulos"]);
  assert.equal(svg.querySelector(".rd-divisas").children.length, 2);                 // um contorno por estado do recorte
  assert.equal(svg.querySelector(".rd-vizinhos").children.length, 1);
  for (const c of [".rd-divisas", ".rd-vizinhos"]) {
    assert.equal(svg.querySelector(c).getAttribute("aria-hidden"), "true");
    assert.equal(svg.querySelector(c).children[0].listeners.click, undefined);       // não pegam o clique
  }
});

test("camadasDeNomes: no Sudeste sem zoom, só os estados; com zoom, os municípios; num estado, sempre", () => {
  assert.deepEqual(mod.camadasDeNomes(1, true), { municipios: false, destaques: false, estados: true });
  assert.deepEqual(mod.camadasDeNomes(mod.ZOOM_MUNICIPIOS, true), { municipios: true, destaques: true, estados: true });
  assert.deepEqual(mod.camadasDeNomes(1, false), { municipios: true, destaques: true, estados: true });
  assert.equal(mod.camadasDeNomes(mod.ZOOM_SEM_ESTADOS, false).estados, false);
});

test("Sudeste inteiro: só os nomes dos estados (os vizinhos com a sigla); aproximando, os municípios", () => {
  const raiz = new No("div");
  const rotulos = [{ id: "3100302", texto: "Cidade C", x: 260, y: 300, valor: "R$ 60,8 mi" },
                   { id: "3100203", texto: "Cidade B", x: 600, y: 300 }];
  const svg = mod.desenhar(raiz, { ...dados(), estados: ESTADOS, rotulos, maxRotulos: 5, viewBoxInteiro: "0 0 1000 800" },
                           () => {}, doc);
  const textos = () => svg.querySelector(".rd-rotulos").todos().filter((n) => n.tagName === "text")
    .map((t) => t.textContent || t.children.map((s) => s.textContent).join(""));
  assert.deepEqual(textos(), ["Minas Gerais", "São Paulo", "GO"]);
  const mais = raiz.querySelectorAll(".rd-mapa-botao").find((b) => b.textContent === "+");
  mais.dispatch("click");                                                             // zoom 1,6: municípios, sem estados
  assert.deepEqual(textos(), ["▲ Cidade C · R$ 60,8 mi", "Cidade B"]);
  const etiqueta = svg.querySelector(".rd-destaque");
  assert.equal(etiqueta.children[0].tagName, "rect");                                 // a pílula atrás do texto
  assert.ok(Number(etiqueta.children[0].getAttribute("width")) > 0);
});

test("cartões sobre o mapa: total, zoom e resumo que se fecha", () => {
  const raiz = new No("div");
  mod.desenhar(raiz, { ...dados(), resumo: "Frase.", info: { titulo: "Déficit · Sudeste", valor: "R$ 243,3 mi",
                                                             nota: "1.666 municípios com cartório" } }, () => {}, doc);
  const vista = raiz.querySelector(".rd-mapa-vista");
  assert.equal(vista.children[0].tagName, "svg");
  const info = vista.querySelector(".rd-mapa-info");
  assert.deepEqual(info.children.map((c) => c.textContent), ["Déficit · Sudeste", "R$ 243,3 mi", "1.666 municípios com cartório"]);
  assert.ok(vista.querySelector(".rd-mapa-zoom"));
  const resumo = vista.querySelector(".rd-mapa-resumo-c");
  assert.equal(resumo.querySelector(".rd-mapa-tag").textContent, "Resumo");
  resumo.querySelector(".rd-mapa-fechar").dispatch("click");
  assert.equal(resumo.hidden, true);
  const sem = new No("div");
  mod.desenhar(sem, dados(), () => {}, doc);
  assert.equal(sem.querySelector(".rd-mapa-info"), null);                             // sem info, sem cartão
});

test("legenda: quantas áreas por faixa e, ao clicar, só aquela faixa em destaque", () => {
  const raiz = new No("div");
  const svg = mod.desenhar(raiz, { ...dados(), unidadeLegenda: "mun.",
                                   legenda: [{ faixa: "zero", texto: "Zero", n: 1 }, { faixa: "3", texto: "até 10", n: 1234 }] },
                           () => {}, doc);
  const itens = raiz.querySelector(".rd-mapa-legenda").querySelectorAll(".rd-mapa-item");
  assert.deepEqual(itens.map((i) => i.tagName), ["button", "button", "span"]);       // o fundo não é botão
  assert.equal(itens[1].querySelector(".rd-mapa-n").textContent, `${(1234).toLocaleString("pt-BR")} mun.`);
  const classe = (id) => svg.querySelectorAll("path").find((p) => p.getAttribute("data-id") === id).getAttribute("class");
  itens[1].dispatch("click");
  assert.equal(itens[1].getAttribute("aria-pressed"), "true");
  assert.ok(classe("3100104").includes("rd-apagado") && !classe("3100203").includes("rd-apagado"));
  itens[1].dispatch("click");                                                         // de novo: volta ao normal
  assert.ok(!classe("3100104").includes("rd-apagado"));
  assert.equal(itens[1].getAttribute("aria-pressed"), "false");
});

test("tamanhoLetra: px fixos na tela viram unidades do viewBox, pela menor escala; sem medida, null", () => {
  const T = (l, a) => ({ largura: l, altura: a });
  assert.equal(mod.tamanhoLetra(T(500, 400), T(1000, 800), 13), 26);   // 500 px mostrando 1000 unidades
  assert.equal(mod.tamanhoLetra(T(1000, 1000), T(250, 250), 13), 3.25); // com zoom, a letra encolhe em unidades
  // a altura limita: 980 × 560 px mostrando 1000 × 818 → escala 560 / 818 (não 980 / 1000)
  assert.equal(mod.tamanhoLetra(T(980, 560), T(1000, 818), 14), 14 / (560 / 818));
  assert.equal(mod.tamanhoLetra(T(0, 0), T(1000, 800), 13), null);       // fora da página: usa a reserva
  // durante o carregamento (2026-11-11): 982 × 20 px dariam uma letra de 13 / (20 / 1027) ≈ 668 unidades, o mapa todo
  assert.equal(mod.tamanhoLetra(T(982, 20), T(1000, 1027), 13), null);
  assert.equal(mod.tamanhoLetra(T(982, mod.MEDIDA_MINIMA), T(1000, 1027), 13), 13 / (mod.MEDIDA_MINIMA / 1027));
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
  assert.equal(ts[0].getAttribute("y"), "5");
  // x = 25 colado na borda esquerda: o nome (≈ 0,6 × 20 × 8 = 96 de largura) vai para dentro, até começar no 0
  assert.equal(ts[0].getAttribute("x"), "48");
  assert.equal(ts[1].getAttribute("x"), "400");                 // longe da borda: fica onde veio
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

// ------------------------------------------------------------------ vista: zoom, arrastar e "estado inteiro" (2026-11-10)
const INTEIRO = { x: 0, y: 0, w: 1000, h: 800 };

test("lê e escreve a vista do viewBox", () => {
  assert.deepEqual(mod.lerVista("10 20 300 240"), { x: 10, y: 20, w: 300, h: 240 });
  assert.equal(mod.lerVista("x"), null);
  assert.equal(mod.lerVista("0 0 0 10"), null);
  assert.equal(mod.textoVista({ x: 1.234, y: 2, w: 3, h: 4 }), "1.2 2 3 4");
});

test("zoom no centro mantém o centro; limites de 1× a 12× o estado", () => {
  const v = mod.zoomVista(INTEIRO, 2, 500, 400, INTEIRO);
  assert.deepEqual(v, { x: 250, y: 200, w: 500, h: 400 });
  assert.equal(mod.zoomVista(INTEIRO, 1 / 2, 500, 400, INTEIRO).w, 1000);        // não afasta além do estado
  assert.equal(mod.zoomVista(INTEIRO, 100, 500, 400, INTEIRO).w, 1000 / mod.ZOOM_MAX);
});

test("arrastar move a vista, sem o centro sair do estado", () => {
  const v = { x: 250, y: 200, w: 500, h: 400 };
  assert.deepEqual(mod.moverVista(v, 100, 50, INTEIRO), { x: 150, y: 150, w: 500, h: 400 });
  const longe = mod.moverVista(v, 5000, 5000, INTEIRO);
  assert.equal(longe.x + longe.w / 2, 0);   // o centro para na borda do estado
  assert.equal(longe.y + longe.h / 2, 0);
});

test("mais nomes com mais zoom, até ROTULOS_MAX; zero continua zero; só os que estão na tela", () => {
  assert.equal(mod.maxRotulosNaVista(3, INTEIRO, INTEIRO), 3);
  assert.equal(mod.maxRotulosNaVista(3, INTEIRO, { w: 500 }), 12);                     // cresce com o quadrado do zoom
  assert.equal(mod.maxRotulosNaVista(3, INTEIRO, { w: 50 }), mod.ROTULOS_MAX);
  assert.equal(mod.maxRotulosNaVista(0, INTEIRO, { w: 50 }), 0);
  const c = [{ x: 10, y: 10 }, { x: 900, y: 700 }];
  assert.deepEqual(mod.rotulosNaVista(c, { x: 0, y: 0, w: 100, h: 100 }), [{ x: 10, y: 10 }]);
});

test("botões +, − e estado inteiro mudam o viewBox", () => {
  const raiz = new No("div");
  const svg = mod.desenhar(raiz, { ...dados(), viewBoxInteiro: "0 0 1000 800", rotuloInteiro: "Ver o estado" },
                           () => {}, doc);
  const botoes = raiz.querySelectorAll(".rd-mapa-botao");
  assert.deepEqual(botoes.map((b) => b.textContent), ["Ver o estado", "+", "−"]);   // o zoom fica no canto do mapa
  botoes[1].dispatch("click");
  assert.equal(svg.getAttribute("viewBox"), "187.5 150 625 500");
  assert.ok(svg.getAttribute("class").includes("rd-aproximado"));
  botoes[0].dispatch("click");
  assert.equal(svg.getAttribute("viewBox"), "0 0 1000 800");
  assert.ok(!svg.getAttribute("class").includes("rd-aproximado"));
});

// ------------------------------------------------------------------ V3 completo (D-089): barra, painel ao lado, foco
const LADO_LISTA = { titulo: "Onde mais falta cobrir no Sudeste", contexto: "Os 10 municípios somam 50,4%",
                     lista: [{ id: "3100302", pos: "1º", nome: "Município C (MG)", valor: "R$ 60,8 mi", frac: 1 },
                             { id: "3100203", pos: "2º", nome: "Município B (MG)", valor: "R$ 26,2 mi", frac: 0.43 }] };

test("V3: mapa num cartão e a lista ao lado; clicar na lista escolhe o município", () => {
  const raiz = new No("div"), escolhidos = [];
  mod.desenhar(raiz, { ...dados(), lado: LADO_LISTA, fonte: "Fonte: X." }, (id) => escolhidos.push(id), doc);
  const grade = raiz.children[0];
  assert.equal(grade.getAttribute("class"), "rd-mapa-grade");
  assert.deepEqual(grade.children.map((c) => c.getAttribute("class")), ["rd-mapa-c", "rd-mapa-lado"]);
  const cartao = grade.children[0];
  assert.ok(cartao.querySelector(".rd-mapa-vista") && cartao.querySelector(".rd-mapa-legenda"));
  assert.equal(cartao.querySelector(".rd-mapa-fonte").textContent, "Fonte: X.");   // a fonte dentro do cartão
  const itens = grade.children[1].querySelectorAll("button");
  assert.equal(itens.length, 2);
  assert.equal(itens[1].querySelector(".rd-vl").textContent, "R$ 26,2 mi");
  assert.equal(itens[1].querySelector(".rd-bar").children[0].style.width, "43%");
  itens[0].dispatch("click");
  assert.deepEqual(escolhidos, ["3100302"]);
});

test("V3: município escolhido ao lado, com o botão que volta à lista", () => {
  const raiz = new No("div"), limpos = [];
  const lado = { titulo: "Município B", contexto: "Minas Gerais", valor: "R$ 8,9 mi", sub: "falta cobrir · 3º",
                 linhas: [["Cartórios", "45"]], voltar: "Ver os 10 que mais faltam cobrir" };
  mod.desenhar(raiz, { ...dados(), lado }, () => {}, doc, { limpar: () => limpos.push(1) });
  const aside = raiz.querySelector(".rd-mapa-lado");
  assert.equal(aside.querySelector(".rd-mapa-det-v").textContent, "R$ 8,9 mi");
  assert.equal(aside.querySelector("dd").textContent, "45");
  const voltar = aside.querySelector(".rd-mapa-botao");
  assert.equal(voltar.textContent, "Ver os 10 que mais faltam cobrir");
  voltar.dispatch("click");
  assert.equal(limpos.length, 1);
});

test("V3: barra com a busca, os estados e o Sudeste inteiro; os botões pedem o recorte", () => {
  const raiz = new No("div"), pedidos = [];
  const ufs = [{ uf: "MG", nome: "Minas Gerais", ativo: true }, { uf: "SP", nome: "São Paulo", ativo: false }];
  mod.desenhar(raiz, { ...dados(), viewBoxInteiro: "0 0 1000 800", rotuloInteiro: "Ver o Sudeste inteiro",
                       busca: [{ id: "1", nome: "Abaeté", uf: "MG" }], ufs, escopoRegiao: "SUDESTE",
                       regiaoAtiva: false }, () => {}, doc, { estado: (u) => pedidos.push(u) });
  const barra = raiz.querySelector(".rd-mapa-controles");
  assert.ok(barra.querySelector(".rd-mapa-busca").querySelector("input"));
  const botoes = barra.querySelectorAll(".rd-mapa-botao");
  assert.deepEqual(botoes.map((b) => b.textContent), ["MG", "SP", "Ver o Sudeste inteiro"]);
  assert.equal(botoes[0].getAttribute("aria-pressed"), "true");
  botoes[1].dispatch("click");   // outro estado
  botoes[0].dispatch("click");   // o estado em foco de novo: volta à região
  botoes[2].dispatch("click");   // "Ver o Sudeste inteiro" com o foco num estado: volta à região
  assert.deepEqual(pedidos, ["SP", "SUDESTE", "SUDESTE"]);
});

test("V3: busca sem acento e sem maiúsculas, os que começam com o texto primeiro", () => {
  const lista = [{ id: "1", nome: "Abaeté", uf: "MG" }, { id: "2", nome: "Ribeirão Preto", uf: "SP" },
                 { id: "3", nome: "Preto Velho", uf: "MG" }];
  assert.deepEqual(mod.buscar(lista, "ABAETE").map((x) => x.id), ["1"]);
  assert.deepEqual(mod.buscar(lista, "preto").map((x) => x.id), ["3", "2"]);
  assert.deepEqual(mod.buscar(lista, "p"), []);   // menos de 2 letras
});

test("V3: foco num estado: os municípios dos outros em cinza (o clique troca o foco), a divisa do foco mais forte", () => {
  const raiz = new No("div"), pedidos = [];
  const estados = [{ ...ESTADOS[0], regiao: true }, { ...ESTADOS[1], ativo: false, regiao: true }, ESTADOS[2]];
  const svg = mod.desenhar(raiz, { ...dados(), estados, fora: [{ id: "3500105", uf: "SP", d: "M600 0L700 0L700 10Z" }] },
                           () => {}, doc, { estado: (u) => pedidos.push(u) });
  const fora = svg.querySelector(".rd-fora").children;
  assert.equal(fora.length, 1);
  fora[0].dispatch("click");
  assert.deepEqual(pedidos, ["SP"]);
  const divisas = svg.querySelector(".rd-divisas").children;
  assert.equal(divisas.length, 2);                                    // MG e SP (a região); GO fica nos vizinhos
  assert.equal(divisas[0].getAttribute("class"), "rd-foco");
  assert.equal(divisas[1].getAttribute("class"), null);
});

test("V3: nomes dos estados: os da região sempre; o do foco some com zoom; os vizinhos só com pouco zoom", () => {
  const foco = { ativo: true, regiao: true }, outro = { ativo: false, regiao: true }, viz = { ativo: false, regiao: false };
  assert.equal(mod.mostraNomeDoEstado(foco, 1, false), true);
  assert.equal(mod.mostraNomeDoEstado(foco, 3, false), false);
  assert.equal(mod.mostraNomeDoEstado(outro, 3, false), true);
  assert.equal(mod.mostraNomeDoEstado(foco, 3, true), true);          // no Sudeste inteiro, os 4 sempre
  assert.equal(mod.mostraNomeDoEstado(viz, 3, true), false);
});
