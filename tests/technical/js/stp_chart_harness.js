// Behaviour harness for the STP tab's chart (owner, 25 November 2026): runs the real dashboard/static/stp/stp.js
// against a minimal DOM, a stand-in chart library that records what the page draws, and a scripted STP API, then
// prints one snapshot per step. Read only; nothing is fetched from the network.
//   node stp_chart_harness.js <stp.js> <scenario.json>
// scenario: {steps: [{serve: {overview?, history?, recommendation?: {id: detail}, now?}}, {mount: true}, {tick: true},
//            {click: "<button text>"}, {click_row: "<recommendation id>"}, ...]}
"use strict";
const fs = require("fs"), vm = require("vm");
const [stpPath, scenarioPath] = process.argv.slice(2);
const scenario = JSON.parse(fs.readFileSync(scenarioPath, "utf8"));

class T { constructor(t) { this._t = String(t); this.parentNode = null; } get textContent() { return this._t; } set textContent(v) { this._t = String(v); }
  remove() { if (this.parentNode) { const a = this.parentNode.children; a.splice(a.indexOf(this), 1); this.parentNode = null; } } }
class E {
  constructor(tag) { this.tagName = String(tag).toUpperCase(); this.children = []; this.parentNode = null; this._text = "";
    this.className = ""; this.style = {}; this.attrs = {}; this.dataset = {}; this.listeners = {}; this.disabled = false;
    const self = this;
    this.classList = { _s() { return new Set(self.className.split(/\s+/).filter(Boolean)); },
      add(...c) { const z = this._s(); c.forEach(x => z.add(x)); self.className = [...z].join(" "); },
      remove(...c) { const z = this._s(); c.forEach(x => z.delete(x)); self.className = [...z].join(" "); },
      toggle(c, on) { (on === undefined ? !this._s().has(c) : on) ? this.add(c) : this.remove(c); },
      contains(c) { return this._s().has(c); } }; }
  appendChild(c) { if (typeof c === "string") c = new T(c); if (c.parentNode) c.remove(); c.parentNode = this; this.children.push(c); return c; }
  append(...cs) { cs.forEach(c => this.appendChild(c)); }
  insertBefore(c, ref) { if (c.parentNode) c.remove(); c.parentNode = this; const i = ref ? this.children.indexOf(ref) : -1;
    if (i < 0) this.children.push(c); else this.children.splice(i, 0, c); return c; }
  get nextSibling() { if (!this.parentNode) return null; const a = this.parentNode.children; return a[a.indexOf(this) + 1] || null; }
  get firstChild() { return this.children[0] || null; }
  remove() { if (this.parentNode) { const a = this.parentNode.children; a.splice(a.indexOf(this), 1); this.parentNode = null; } }
  set textContent(v) { this.children.forEach(c => { c.parentNode = null; }); this.children = []; this._text = String(v); }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(""); }
  setAttribute(k, v) { this.attrs[k] = String(v); } getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }
  addEventListener(ev, f) { (this.listeners[ev] = this.listeners[ev] || []).push(f); } removeEventListener() {}
  click() { (this.listeners.click || []).forEach(f => f({target: this})); }
  scrollIntoView() {} focus() {}
  getBoundingClientRect() { return {left: 0, top: 0, width: 800, height: 400}; }
  get clientWidth() { return 800; } get clientHeight() { return 400; }
  matches(sel) { if (sel.startsWith(".")) return sel.slice(1).split(".").every(c => this.classList.contains(c)); return this.tagName === sel.toUpperCase(); }
  querySelectorAll(sel) { const out = []; const walk = n => n.children.forEach(c => { if (c instanceof E) { if (c.matches(sel)) out.push(c); walk(c); } }); walk(this); return out; }
  querySelector(sel) { const parts = sel.trim().split(/\s+/); let set = [this];
    for (const p of parts) set = set.flatMap(n => n.querySelectorAll(p)); return set[0] || null; }
}
const document = { createElement: t => new E(t), createElementNS: (ns, t) => new E(t), createTextNode: t => new T(t),
  body: new E("body"), hidden: false, addEventListener() {} };

// the stand-in chart library: records the candles, price lines, markers and visible range the page sets
const chart = { data: [], lines: [], markers: [], range: null, setDataCalls: 0, fitCalls: 0 };
const LightweightCharts = { createChart() {
  const ts = { getVisibleLogicalRange: () => chart.range, setVisibleLogicalRange: r => { chart.range = r; chart.fitCalls++; },
               subscribeVisibleLogicalRangeChange() {}, height: () => 26, logicalToCoordinate: l => 10 + l * 4, timeToCoordinate: () => 100 };
  const series = { setData: d => { chart.data = d; chart.setDataCalls++; }, setMarkers: m => { chart.markers = m; },
    createPriceLine: o => { chart.lines.push(o); return o; }, removePriceLine: o => { chart.lines = chart.lines.filter(x => x !== o); },
    priceToCoordinate: p => (1.3150 - p) / 0.0200 * 374 };
  return { timeScale: () => ts, priceScale: () => ({ applyOptions() {}, width: () => 60 }), addCandlestickSeries: () => series };
} };

// the scripted API
const server = { overview: null, history: {ok: true, rows: [], total: 0, pages: 1}, recommendation: {}, now: null, calls: [] };
function candles(tf, endIso) {
  const step = {"5m": 300, "1h": 3600, "4h": 14400}[tf];
  const last = Math.floor(Math.min(endIso ? Date.parse(endIso) : Infinity, Date.parse(server.now)) / 1000 / step) * step - step;
  const out = []; for (let i = 199; i >= 0; i--) { const t = last - i * step; out.push({t, o: 1.306, h: 1.307, l: 1.305, c: 1.3065}); }
  return {ok: true, candles: out, count: out.length, last_end_utc: new Date((last + step) * 1000).toISOString().replace(".000", "")};
}
async function fetch(url) {
  server.calls.push(url);
  const [p, q] = url.replace(/^\/api\/stp\//, "").split("?");
  const qs = new URLSearchParams(q || "");
  let body = null;
  if (p === "overview") body = server.overview;
  else if (p === "history") body = server.history;
  else if (p === "evaluation") body = null;              // not part of these tests: the page shows "could not be loaded"
  else if (p === "recommendation") body = server.recommendation[qs.get("id")] || null;
  else if (p === "candles") body = candles(qs.get("tf"), qs.get("end"));
  return { status: body ? 200 : 404, ok: !!body, json: async () => body || {ok: false, error: "not found"} };
}

const errors = []; let intervalFn = null; let rafs = [];
const win = { document, fetch, LightweightCharts, localStorage: { getItem() { return null; }, setItem() {}, removeItem() {} },
  location: { hash: "#stp", reload() { errors.push("page reload requested"); } },
  setInterval: (f) => { intervalFn = f; return 1; }, clearInterval() {}, setTimeout: () => 0, clearTimeout() {},
  addEventListener() {}, requestAnimationFrame: (f) => { rafs.push(f); return rafs.length; },
  Intl, Date, console: { log() {}, warn() {}, error: (...a) => errors.push(a.join(" ")) }, URLSearchParams, Promise, Math, JSON,
  Object, Array, String, Number, Set, Map, encodeURIComponent, isFinite, parseFloat };
win.window = win;
vm.createContext(win);
process.on("unhandledRejection", e => errors.push("unhandled: " + (e && e.stack || e)));
vm.runInContext(fs.readFileSync(stpPath, "utf8"), win, {filename: "stp.js"});
const root = new E("div"); document.body.appendChild(root);

async function settle() {
  for (let i = 0; i < 60; i++) await new Promise(r => setImmediate(r));
  while (rafs.length) { const f = rafs; rafs = []; f.forEach(x => { try { x(); } catch (e) { errors.push("draw: " + e.stack); } }); }
  for (let i = 0; i < 10; i++) await new Promise(r => setImmediate(r));
}
function snapshot(step) {
  const S = win.STP._state, q = s => S.root && S.root.querySelector(s);
  const banner = q(".stp-histbanner");
  const lastCandles = server.calls.filter(u => u.includes("candles?")).slice(-1)[0] || null;
  return { step, errors: errors.splice(0),
    selected: S.selected, review: S.review, auto_id: S.autoId,
    banner: banner ? banner.textContent : null,
    plan_labels: (S.placed || []).filter(p => p.prio === 1).map(p => p.text),
    layer_text: (q(".stp-layer") || {textContent: ""}).textContent,
    legend: (q(".stp-legend") || {textContent: ""}).textContent,
    price_lines: chart.lines.map(l => l.price),
    markers: chart.markers.map(m => m.text || m.shape),
    last_candle_t: chart.data.length ? chart.data[chart.data.length - 1].time : null,
    candle_fetches: server.calls.filter(u => u.includes("candles?")).length, last_candles_url: lastCandles,
    set_data_calls: chart.setDataCalls, fit_calls: chart.fitCalls,
    lifecycle_head: ((q(".stp-lifebox") || {textContent: ""}).textContent || "").slice(0, 160),
    selected_rows: S.root ? S.root.querySelectorAll(".sel").map(r => r.textContent.slice(0, 80)) : [],
    opportunity_rows: S.root && q(".stp-oppbox") ? q(".stp-oppbox").querySelectorAll("tr").slice(1).map(r => r.children.map(c => c.textContent)) : [] };
}
function button(text) {
  const all = root.querySelectorAll("button"); const b = all.find(x => x.textContent === text);
  if (!b) throw new Error("no button " + JSON.stringify(text) + " among " + JSON.stringify(all.map(x => x.textContent)));
  return b;
}
(async () => {
  const out = [];
  for (const [i, st] of scenario.steps.entries()) {
    try {
      if (st.serve) Object.assign(server, st.serve);
      if (st.mount) win.STP.mount(root);
      if (st.tick) intervalFn();
      if (st.click) button(st.click).click();
      if (st.click_row) { const r = root.querySelectorAll("tr").find(x => x.textContent.includes(st.click_row)); if (!r) throw new Error("no row " + st.click_row); r.click(); }
    } catch (e) { errors.push("step " + i + ": " + e.stack); }
    await settle();
    out.push(snapshot(st.name || i));
  }
  console.log(JSON.stringify(out));
})();
