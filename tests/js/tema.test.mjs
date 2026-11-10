// Testes do componente de tema (src/painel/componentes/tema.js), com o `node --test` (sem dependências). Rodados pela
// suíte padrão em tests/test_mapa.py (test_javascript_do_mapa roda todos os tests/js/*.test.mjs).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const fonte = readFileSync(new URL("../../src/painel/componentes/tema.js", import.meta.url), "utf8");
const mod = await import("data:text/javascript;base64," + Buffer.from(fonte).toString("base64"));

// localStorage falso: getItem, setItem, length e key (o que o tema.js usa)
const guarda = (itens) => ({
  getItem: (k) => (k in itens ? itens[k] : null),
  setItem: (k, v) => { itens[k] = String(v); },
  get length() { return Object.keys(itens).length; },
  key: (i) => Object.keys(itens)[i] ?? null,
  itens,
});

test("ao carregar vale a chave da página; depois, a última escolha, copiada para as outras páginas", () => {
  const p = "stActiveTheme-/-v2", m = "stActiveTheme-/Mercado-v2";
  let e = mod.proximaEscolha(null, { [p]: '"System"', [m]: '"Dark"' }, "/");
  assert.equal(e.escolha, "System");            // recarregou o Início: o Streamlit leu "System"
  assert.equal(e.gravar, null);
  e = mod.proximaEscolha(e, { [p]: '"System"', [m]: '"Dark"' }, "/Mercado");
  assert.equal(e.escolha, "System");            // navegou sem recarregar: o Streamlit mantém o tema
  e = mod.proximaEscolha(e, { [p]: '"System"', [m]: '"Light"' }, "/Mercado");
  assert.equal(e.escolha, "Light");             // escolheu no menu: vale e vai para as outras chaves
  assert.equal(e.gravar, '"Light"');
  e.chaves = { [p]: '"Light"', [m]: '"Light"' };   // o componente grava e relê as chaves
  e = mod.proximaEscolha(e, { [p]: '"Light"', [m]: '"Light"' }, "/");
  assert.equal(e.gravar, null);                 // tudo igual: nada a gravar
  e = mod.proximaEscolha(e, { [p]: '"Light"', [m]: '"Light"' }, "/Nova");
  assert.equal(e.escolha, "Light");
  assert.equal(e.gravar, '"Light"');            // página nova visitada: grava a escolha em vigor na chave dela
});

test("o componente copia a escolha nova para todas as páginas", () => {
  const ls = guarda({ "stActiveTheme-/-v2": '"System"', "stActiveTheme-/Mercado-v2": '"System"' });
  const attrs = {};
  const win = {
    localStorage: ls, location: { pathname: "/Mercado" }, __rdTema: null,
    matchMedia: () => ({ matches: false, addEventListener() {}, removeEventListener() {} }),
    setInterval: () => 1, clearInterval() {},
  };
  const html = { getAttribute: (k) => attrs[k] ?? null, setAttribute: (k, v) => { attrs[k] = v; } };
  const comp = { data: { atual: "claro" }, setStateValue() {},
                 parentElement: { ownerDocument: { defaultView: win, documentElement: html } } };
  mod.default(comp);
  assert.equal(attrs["data-rd-tema"], "claro");
  ls.itens["stActiveTheme-/Mercado-v2"] = '"Dark"';   // o visitante escolhe "Dark" no menu
  mod.default(comp);
  assert.equal(attrs["data-rd-tema"], "escuro");
  assert.equal(ls.itens["stActiveTheme-/-v2"], '"Dark"');
});

test("lê a escolha do menu do Streamlit pela página", () => {
  const ls = guarda({ "stActiveTheme-/Onde-v2": '"Light"', "stActiveTheme-/-v2": '"Dark"' });
  assert.equal(mod.escolhaDoStreamlit(ls, "/Onde"), "Light");
  assert.equal(mod.escolhaDoStreamlit(ls, "/"), "Dark");
  assert.equal(mod.escolhaDoStreamlit(ls, "/outra"), "System");
});

test("aceita objeto com nome, texto puro e armazenamento bloqueado", () => {
  assert.equal(mod.escolhaDoStreamlit(guarda({ "stActiveTheme-/-v2": '{"name":"Dark"}' }), "/"), "Dark");
  assert.equal(mod.escolhaDoStreamlit(guarda({ "stActiveTheme-/-v2": "Light" }), "/"), "Light");
  const bloqueado = { getItem: () => { throw new Error("bloqueado"); } };
  assert.equal(mod.escolhaDoStreamlit(bloqueado, "/"), "System");
});

test("System segue o sistema; Light e Dark mandam", () => {
  assert.equal(mod.temaAtivo("Light", true), "claro");
  assert.equal(mod.temaAtivo("Dark", false), "escuro");
  assert.equal(mod.temaAtivo("System", true), "escuro");
  assert.equal(mod.temaAtivo("System", false), "claro");
  assert.equal(mod.temaAtivo("qualquer", false), "claro");
});

test("marca o <html> e avisa o Python só quando o tema muda", () => {
  const attrs = {};
  const html = { getAttribute: (k) => attrs[k] ?? null, setAttribute: (k, v) => { attrs[k] = v; } };
  const win = {
    localStorage: guarda({ "stActiveTheme-/-v2": '"Light"' }), location: { pathname: "/" },
    matchMedia: () => ({ matches: true, addEventListener() {}, removeEventListener() {} }),
    setInterval: () => 1, clearInterval() {},
  };
  const enviados = [];
  const parar = mod.default({ data: { atual: "escuro" }, setStateValue: (k, v) => enviados.push([k, v]),
                              parentElement: { ownerDocument: { defaultView: win, documentElement: html } } });
  assert.equal(attrs["data-rd-tema"], "claro");
  assert.deepEqual(enviados, [["tema", "claro"]]);
  assert.equal(typeof parar, "function");
  const outros = [];
  mod.default({ data: { atual: "claro" }, setStateValue: (k, v) => outros.push([k, v]),
                parentElement: { ownerDocument: { defaultView: win, documentElement: html } } });
  assert.deepEqual(outros, []);   // já está certo: nada de rodar a página de novo
});
