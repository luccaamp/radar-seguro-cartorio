// Testes do botão de tema (src/painel/componentes/tema.js), com o `node --test` (sem dependências). Rodados pela
// suíte padrão em tests/test_mapa.py (test_javascript_do_mapa roda todos os tests/js/*.test.mjs).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const fonte = readFileSync(new URL("../../src/painel/componentes/tema.js", import.meta.url), "utf8");
const mod = await import("data:text/javascript;base64," + Buffer.from(fonte).toString("base64"));

// localStorage falso: getItem e setItem (o que o tema.js usa)
const guarda = (itens) => ({
  getItem: (k) => (k in itens ? itens[k] : null),
  setItem: (k, v) => { itens[k] = String(v); },
  itens,
});

// Botões falsos, como o HTML do componente (src/painel/ui.py): um por opção, com data-t.
function botoes() {
  const lista = mod.OPCOES.map(([t]) => {
    const attrs = {};
    return { dataset: { t }, attrs, setAttribute: (k, v) => { attrs[k] = v; },
             closest: function () { return this; } };
  });
  return { lista, raiz: { querySelectorAll: () => lista, onclick: null } };
}

function montar({ itens = {}, sistemaEscuro = false, atual = "", caminho = "/" } = {}) {
  const attrs = {};
  const html = { getAttribute: (k) => attrs[k] ?? null, setAttribute: (k, v) => { attrs[k] = v; } };
  const ls = guarda(itens);
  const recargas = [];
  const win = {
    localStorage: ls, location: { pathname: caminho, reload: () => recargas.push(1) },
    matchMedia: () => ({ matches: sistemaEscuro, addEventListener() {}, removeEventListener() {} }),
  };
  const { lista, raiz } = botoes();
  const enviados = [];
  const parentElement = { ownerDocument: { defaultView: win, documentElement: html }, querySelector: () => raiz };
  mod.default({ data: { atual }, setStateValue: (k, v) => enviados.push([k, v]), parentElement });
  return { attrs, ls, recargas, lista, raiz, enviados };
}

test("sem escolha guardada, o padrão é o claro, mesmo com o sistema no escuro", () => {
  assert.equal(mod.escolhaGuardada(guarda({})), "claro");
  assert.equal(mod.escolhaGuardada(guarda({ "radar-tema": "qualquer" })), "claro");
  assert.equal(mod.escolhaGuardada({ getItem: () => { throw new Error("bloqueado"); } }), "claro");
  assert.equal(mod.temaAtivo("claro", true), "claro");
  assert.equal(mod.temaAtivo("escuro", false), "escuro");
  assert.equal(mod.temaAtivo("sistema", true), "escuro");
  assert.equal(mod.temaAtivo("sistema", false), "claro");
});

test("a escolha vai para a chave do Streamlit da página; só recarrega quando ela muda", () => {
  const ls = guarda({});
  assert.equal(mod.sincronizarStreamlit(ls, "/Mercado", "escuro"), true);
  assert.equal(ls.itens["stActiveTheme-/Mercado-v2"], '"Dark"');
  assert.equal(mod.sincronizarStreamlit(ls, "/Mercado", "escuro"), false);   // já está: nada a fazer
  const naoGrava = { getItem: () => null, setItem() {} };
  assert.equal(mod.sincronizarStreamlit(naoGrava, "/", "claro"), false);     // não grava: não entra em laço
});

test("primeira visita com o Streamlit sem a chave: grava 'Light' e recarrega uma vez", () => {
  const m = montar({ sistemaEscuro: true });
  assert.equal(m.ls.itens["stActiveTheme-/-v2"], '"Light"');
  assert.equal(m.recargas.length, 1);
  assert.equal(m.attrs["data-rd-tema"], "claro");
});

test("com a chave em dia: marca o <html>, o botão ativo e avisa o Python só quando o tema muda", () => {
  const m = montar({ itens: { "radar-tema": "escuro", "stActiveTheme-/-v2": '"Dark"' }, atual: "claro" });
  assert.equal(m.recargas.length, 0);
  assert.equal(m.attrs["data-rd-tema"], "escuro");
  assert.deepEqual(m.enviados, [["tema", "escuro"]]);
  assert.deepEqual(m.lista.map((b) => b.attrs["aria-pressed"]), ["false", "true", "false"]);
  const igual = montar({ itens: { "radar-tema": "escuro", "stActiveTheme-/-v2": '"Dark"' }, atual: "escuro" });
  assert.deepEqual(igual.enviados, []);   // já está certo: nada de rodar a página de novo
});

test("clicar em Claro guarda a escolha, troca as cores e recarrega para o Streamlit seguir", () => {
  const m = montar({ itens: { "radar-tema": "escuro", "stActiveTheme-/-v2": '"Dark"' }, atual: "escuro" });
  m.raiz.onclick({ target: m.lista[0] });
  assert.equal(m.ls.itens["radar-tema"], "claro");
  assert.equal(m.ls.itens["stActiveTheme-/-v2"], '"Light"');
  assert.equal(m.attrs["data-rd-tema"], "claro");
  assert.equal(m.recargas.length, 1);
  m.raiz.onclick({ target: m.lista[0] });   // o mesmo botão de novo: nada
  assert.equal(m.recargas.length, 1);
});
