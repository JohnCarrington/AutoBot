/* The Structural Trade Planner tab (owner's brief of 17 November 2026). OBSERVE ONLY: it shows what the planner
   recorded and never controls trading. Read only: it only GETs /api/stp/*. Every level, zone, destination and
   decision drawn is the planner's own; nothing is forecast or recommended here. Built with DOM calls, never HTML
   strings, so nothing from the records is run as HTML. Loaded by index.html when the tab is first opened. */
(function () {
  "use strict";
  const API = "/api/stp/";
  const TF_KEY = "stp.tf";
  const S = {
    tf: "1h", mode: "plan", ov: null, candles: [], chart: null, series: null, lines: [], selected: null, detail: null,
    show: {past: true}, placed: [], hoverItems: [],
    hist: {page: 1, size: 15, q: "", sort: "created", order: "desc", rows: [], total: 0, pages: 1},
    timer: null, loadingMore: false, root: null,
  };
  // The chart always opens on H1 in the TRADE PLAN view (owner's brief, 18 November 2026); a timeframe chosen is kept
  // for the rest of the visit only.
  try { localStorage.removeItem(TF_KEY); } catch (e) { /* none */ }
  const MODES = [["plan", "Trade plan", "The recommendation only: entry zone, destinations, invalidation and the forecast direction"],
                 ["structure", "Market structure", "Significant 4-hour swings, daily and weekly levels, major support and resistance, confluence zones, and the trade plan"],
                 ["full", "Full analysis", "Every level the planner recorded; hover a line for its details, or open the level list"]];
  const SHOW_BARS = {"4h": 60, "1h": 60, "5m": 72};

  // ---- helpers -------------------------------------------------------------------------------------------------
  function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined && text !== null) e.textContent = text; return e; }
  function add(parent, ...kids) { kids.forEach(k => k && parent.appendChild(k)); return parent; }
  const ukFmt = new Intl.DateTimeFormat("en-GB", {timeZone: "Europe/London", weekday: "short", day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit"});
  const ukTime = new Intl.DateTimeFormat("en-GB", {timeZone: "Europe/London", hour: "2-digit", minute: "2-digit"});
  const ukDay = new Intl.DateTimeFormat("en-GB", {timeZone: "Europe/London", day: "2-digit", month: "short"});
  const when = (iso) => iso ? ukFmt.format(new Date(iso)) + " UK" : "not recorded";
  const dirClass = (d) => d === "BEARISH" || d === "SELL" ? "bear" : d === "BULLISH" || d === "BUY" ? "bull" : "neutral";
  const arrow = (d) => d === "BEARISH" || d === "SELL" ? "▼ " : d === "BULLISH" || d === "BUY" ? "▲ " : "◆ ";
  const nice = (x) => x ? String(x).replace(/_/g, " ") : "–";
  async function get(path) {
    const r = await fetch(API + path, {credentials: "same-origin", cache: "no-store"});
    if (r.status === 401) { location.hash = ""; location.reload(); throw new Error("logged out"); }
    const data = await r.json().catch(() => ({ok: false, error: "bad answer"}));
    if (!r.ok) throw new Error(data.error || ("error " + r.status));
    return data;
  }
  function rows(box, pairs) {
    const g = el("div", "stp-rows");
    pairs.forEach(([k, v, cls, tip]) => {
      if (v === undefined) return;
      const kk = el("div", "k", k); if (tip) { kk.classList.add("stp-tip"); kk.title = tip; }
      add(g, kk, el("div", "v" + (cls ? " " + cls : ""), (v === null || v === "") ? "–" : String(v)));
    });
    box.appendChild(g); return g;
  }
  function list(box, items, empty) {
    if (!items || !items.length) { if (empty) box.appendChild(el("div", "stp-empty", empty)); return; }
    const u = el("ul", "stp-list"); items.forEach(x => u.appendChild(el("li", "", x))); box.appendChild(u);
  }

  // ---- the page skeleton -----------------------------------------------------------------------------------------
  function build(root) {
    root.textContent = "";
    const w = el("div", "stp-wrap");
    const fb = el("div", "stp-flagbar");
    const title = el("div", "stp-title"); title.append("GBP/USD — STRUCTURAL TRADE PLAN ");
    add(fb, title, el("div", "stp-observe", "OBSERVE ONLY — DOES NOT CONTROL TRADING"));
    add(w, fb, el("div", "stp-meta"), el("div", "stp-tiles"), el("div", "stp-explainbox"));
    const main = el("div", "stp-main");
    const cc = el("div", "stp-card stp-chartcard");
    const h = el("h3"); add(h, el("span", "", "Interactive chart"), el("span", "stp-chartsub stp-note", ""));
    cc.appendChild(h);
    cc.appendChild(el("div", "stp-histslot"));
    const tb = el("div", "stp-toolbar");
    const seg = el("div", "stp-seg");
    [["4h", "H4"], ["1h", "H1"], ["5m", "M5"]].forEach(([tf, label]) => {
      const b = el("button", tf === S.tf ? "on" : "", label); b.type = "button"; b.dataset.tf = tf;
      b.addEventListener("click", () => setTf(tf)); seg.appendChild(b);
    });
    const modes = el("div", "stp-seg stp-modes");
    MODES.forEach(([m, label, tip]) => {
      const b = el("button", m === S.mode ? "on" : "", label); b.type = "button"; b.dataset.mode = m; b.title = tip;
      b.addEventListener("click", () => setMode(m)); modes.appendChild(b);
    });
    add(tb, modes, seg);
    const past = el("button", "stp-tog" + (S.show.past ? " on" : ""), "Past recs"); past.type = "button"; past.title = "Markers for past recommendations";
    past.addEventListener("click", () => { S.show.past = !S.show.past; past.classList.toggle("on", S.show.past); drawOverlays(); });
    const reset = el("button", "stp-tog", "Reset view"); reset.type = "button";
    reset.addEventListener("click", () => { if (S.chart) { S.chart.priceScale("right").applyOptions({autoScale: true}); if (isHist()) showHistoricalOnChart(); else fitRecent(); } });
    add(tb, past, reset);
    cc.appendChild(tb);
    const box = el("div", "stp-chartbox"); add(box, el("div", "stp-chart"), el("div", "stp-layer"), el("div", "stp-hover"));
    cc.appendChild(box);
    cc.appendChild(el("div", "stp-legend"));
    const lv = el("details", "stp-levels"); lv.appendChild(el("summary", "", "Level list")); lv.appendChild(el("div", "stp-levelbody")); cc.appendChild(lv);
    cc.appendChild(el("div", "stp-note", "Finished candles only, chart (sell) price, UK time; the live candle is not drawn. Right of the dotted NOW line is the planner's FORECAST, drawn schematically: a direction sequence, no timing or price path implied. Every level is the planner's own recorded value; nearby levels share one label (hover for all of them)."));
    const pc = el("div", "stp-card stp-planbox");
    add(main, cc, pc);
    w.appendChild(main);
    add(w, el("div", "stp-sec", "Recommendation lifecycle"), el("div", "stp-card stp-lifebox"));
    add(w, el("div", "stp-sec", "Recommendation history"), el("div", "stp-card stp-histbox"));
    add(w, el("div", "stp-sec", "Forecast evaluation"), el("div", "stp-evalbox"));
    const det = el("details", "stp-tech"); det.appendChild(el("summary", "", "Technical Evidence & Market Structure"));
    det.appendChild(el("div", "stp-techgrid")); w.appendChild(det);
    root.appendChild(w);
    S.root = w;
  }
  const $q = (sel) => S.root.querySelector(sel);

  // ---- overview -------------------------------------------------------------------------------------------------
  function renderOverview() {
    const o = S.ov, f = o.freshness || {}, fc = o.forecast || {};
    const flag = $q(".stp-observe");                    // Stage A observes; Stage B authorises entries (owner, 25 Nov)
    if (flag && o.label) { flag.textContent = o.label; flag.classList.toggle("stp-authorising", !!(o.stp_mode && o.stp_mode.authorises_entries)); }
    const meta = $q(".stp-meta"); meta.textContent = "";
    const badge = el("span", "stp-badge " + (f.state || "UNAVAILABLE"), f.label || "UNAVAILABLE"); badge.title = f.detail || "";
    add(meta, badge);
    if (o.price && o.price.text) { const s = el("span"); s.append("Price "); s.appendChild(el("b", "", o.price.text)); s.append(" (bid · " + (o.price.time_utc ? ukTime.format(new Date(o.price.time_utc)) : "–") + ")"); meta.appendChild(s); }
    const la = el("span"); la.append("Last analysis "); la.appendChild(el("b", "", f.last_analysis_utc ? when(f.last_analysis_utc) : "–")); meta.appendChild(la);
    if (f.next_analysis_due_utc) meta.appendChild(el("span", "", "next due " + ukTime.format(new Date(f.next_analysis_due_utc)) + " UK"));
    if (f.last_run_utc) meta.appendChild(el("span", "", "planner checked " + ukTime.format(new Date(f.last_run_utc)) + " UK"));
    meta.appendChild(el("span", "", f.detail || ""));

    const tiles = $q(".stp-tiles"); tiles.textContent = "";
    const tile = (k, v, cls, sub, tag, wide) => { const t = el("div", "stp-tile" + (wide ? " wide" : "")); t.appendChild(el("div", "k", k));
      if (tag) t.appendChild(el("div", "tag", tag)); t.appendChild(el("div", "v " + (cls || "") + (String(v).length > 16 ? " long" : ""), v)); if (sub) t.appendChild(el("div", "s", sub)); tiles.appendChild(t); };
    if (!o.available) {
      tile("Planner", "UNAVAILABLE", "neutral", (o.explanation || {}).text, null, true);
    } else {
      tile("Dominant direction", arrow(fc.dominant_direction) + (fc.dominant_direction || "–"), dirClass(fc.dominant_direction), fc.direction_text);
      tile("Market condition", nice(fc.condition), "", fc.condition_text);
      tile("Expected movement", fc.movement_text || "No movement forecast", "", fc.expected_movement ? "Planner: " + fc.expected_movement : "The planner forecasts a movement only when it finds an opportunity.", "FORECAST", true);
      const opp = o.recommendation ? o.recommendation.trade : "NO CURRENT OPPORTUNITY";
      tile("Preferred opportunity", (o.recommendation ? arrow(opp) : "") + opp, o.recommendation ? dirClass(opp) : "neutral",
           o.recommendation ? (o.recommendation.opportunity || "") : (fc.forecast_trade ? "Forecast direction " + fc.forecast_trade + " (" + (fc.opportunity || "") + "), but no live recommendation" : "No forecast direction to trade"));
      tile("Recommendation status", (o.status || {}).label || "–", "st-" + ((o.status || {}).code || "NONE"),
           o.recommendation ? o.recommendation.id : "");
    }
    const ex = $q(".stp-explainbox"); ex.textContent = "";
    if (o.explanation) {
      const b = el("div", "stp-explain"); b.appendChild(el("div", "", o.explanation.text));
      if (o.explanation.planner_reason) b.appendChild(el("div", "why", "Planner's recorded reason: " + o.explanation.planner_reason));
      ex.appendChild(b);
    }
    renderOpportunities();
    renderPlan();
    renderTech();
  }

  // STP_OPPORTUNITIES (owner, 24 November 2026): every opportunity STP is tracking, read only
  function renderOpportunities() {
    let box = $q(".stp-oppbox");
    const list = S.ov.opportunities;
    if (!list) { if (box) box.remove(); return; }
    if (!box) { box = el("div", "stp-oppbox"); const ex = $q(".stp-explainbox"); ex.parentNode.insertBefore(box, ex.nextSibling); }
    box.textContent = "";
    box.appendChild(el("h3", "", "STP opportunities (" + list.length + ")"));
    const auth = !!(S.ov.stp_mode && S.ov.stp_mode.authorises_entries);
    box.appendChild(el("div", "stp-note", auth ? "Stage B: Waiting and Watch & Wait opportunities authorise entries of the gated strategies in their direction."
                                               : "Stage A: observation only. No opportunity authorises a trade."));
    if (!list.length) { box.appendChild(el("div", "stp-note", "STP is tracking no opportunity.")); return; }
    const t = el("table", "stp-table"), hr = el("tr");
    ["Id", "Trade", "Status", "Zone", "Class", "Primary", "Zone break", "4-hour", "Created"].forEach((x) => hr.appendChild(el("th", "", x)));
    t.appendChild(hr);
    list.forEach((o) => {
      const r = el("tr");
      [o.id, o.trade, o.label + (o.authorises ? "" : " (does not authorise)"), o.zone || "", o.zone_class || "",
       o.primary || "–", o.zone_break || "–", o.relation_to_h4 || "–", o.created_utc ? when(o.created_utc) : "–"]
        .forEach((x, i) => r.appendChild(el("td", i === 2 ? "st-" + o.status : "", String(x))));
      t.appendChild(r);
    });
    box.appendChild(t);
  }

  function renderPlan() {
    const box = $q(".stp-planbox"); box.textContent = "";
    const o = S.ov, r = o.recommendation, fc = o.forecast || {};
    const h = el("h3"); add(h, el("span", "", "Current structural trade plan"));
    if (r) h.appendChild(el("span", "stp-pill st-" + r.status, r.status_label));
    box.appendChild(h);
    if (!o.available) { box.appendChild(el("div", "stp-empty", (o.explanation || {}).text || "Planner unavailable.")); return; }
    if (!r) {
      rows(box, [["Instrument", o.pair_text], ["Dominant direction", fc.dominant_direction, dirClass(fc.dominant_direction)],
                 ["Market condition", nice(fc.condition)], ["Forecast opportunity", fc.opportunity || "none"],
                 ["Status", "NO RECOMMENDATION", "dirv"], ["Last updated", when((o.freshness || {}).last_analysis_utc)]]);
      box.appendChild(el("div", "stp-h", "Why there is no recommendation"));
      list(box, [o.explanation && o.explanation.text, o.explanation && o.explanation.planner_reason && ("Planner: " + o.explanation.planner_reason)].filter(Boolean));
      box.appendChild(el("div", "stp-note", "No entry zone, destination or invalidation is drawn: the planner has no live recommendation."));
      return;
    }
    const p = r.plan || {}, d = p.destinations || {};
    rows(box, [["Instrument", o.pair_text], ["Dominant direction", r.dominant_direction, dirClass(r.dominant_direction), "The 4-hour structural direction"],
               ["Market condition", nice(r.condition)], ["Opportunity", r.opportunity],
               ["Preferred direction", arrow(r.trade) + r.trade, "dirv " + dirClass(r.trade)],
               ["Entry zone", r.entry_zone, "price key " + dirClass(r.trade)], ["Zone class", r.zone_class],
               ["Reference level", r.reference, null, "The zone's primary structural reference level"],
               ["Reachability", r.reachability],
               ["Intermediate destination", d.intermediate ? d.intermediate.text : "none recorded", "price", "The first relevant obstacle"],
               ["Primary destination", d.primary ? d.primary.text : "none recorded", "price key dest"],
               ["Extended destination", d.extended ? d.extended.text : "none recorded", "price"],
               ["Invalidation (hourly close)", (p.invalidation || [])[0] ? p.invalidation[0].text : "none recorded", "price key inval"],
               ["Status", r.status_label], ["Created", when(r.created_utc)], ["Last updated", when(r.last_updated_utc)],
               ["Id", r.id]]);
    box.appendChild(el("div", "stp-h", "Invalidation"));
    list(box, p.invalidation_conditions, "None recorded");
    box.appendChild(el("div", "stp-h", "Why this zone"));
    list(box, [r.selection_reason, (r.families && r.families.length) ? "Families: " + r.families.join(", ") : null].filter(Boolean));
    box.appendChild(el("div", "stp-h", "Structural evidence"));
    list(box, r.evidence, "None recorded");
    if (r.status_reason) { box.appendChild(el("div", "stp-h", "Latest status reason")); list(box, [r.status_reason]); }
  }

  // ---- the chart ----------------------------------------------------------------------------------------------------
  function ensureChart() {
    if (S.chart || !window.LightweightCharts) return;
    const LC = window.LightweightCharts;
    const holder = $q(".stp-chart");
    S.chart = LC.createChart(holder, {
      autoSize: true,
      layout: {background: {type: "solid", color: "#111118"}, textColor: "#9a9ab0", fontFamily: "JetBrains Mono, monospace", fontSize: 11},
      grid: {vertLines: {color: "#ffffff08"}, horzLines: {color: "#ffffff08"}},
      rightPriceScale: {borderColor: "#ffffff18", scaleMargins: {top: 0.08, bottom: 0.08}},
      timeScale: {borderColor: "#ffffff18", timeVisible: true, secondsVisible: false, rightOffset: 14,
                  tickMarkFormatter: (t, type) => { const d = new Date(t * 1000); return type <= 2 ? ukDay.format(d) : ukTime.format(d); }},
      crosshair: {mode: 0},
      localization: {priceFormatter: (p) => p.toFixed(5), timeFormatter: (t) => ukFmt.format(new Date(t * 1000))},
      handleScroll: {mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false},
      handleScale: {axisPressedMouseMove: true, mouseWheel: true, pinch: true},
    });
    S.series = S.chart.addCandlestickSeries({upColor: "#00ff88", downColor: "#ff4466", borderVisible: false,
      wickUpColor: "#00ff88aa", wickDownColor: "#ff4466aa", priceFormat: {type: "price", precision: 5, minMove: 0.00001},
      priceLineVisible: false, lastValueVisible: false});
    S.chart.timeScale().subscribeVisibleLogicalRangeChange((rng) => { schedule(); if (rng && rng.from < 5) loadMore(); });
    const box = $q(".stp-chartbox");
    ["pointermove", "wheel", "pointerup", "touchmove"].forEach(ev => box.addEventListener(ev, schedule, {passive: true}));
    box.addEventListener("pointermove", hover, {passive: true});
    box.addEventListener("pointerleave", () => { $q(".stp-hover").style.display = "none"; });
    window.addEventListener("resize", schedule);
  }
  let raf = 0;
  function schedule() { if (!raf) raf = requestAnimationFrame(() => { raf = 0; drawLayer(); }); }

  async function loadCandles(endIso) {
    const sub = $q(".stp-chartsub");
    try {
      const d = await get("candles?tf=" + S.tf + (endIso ? "&end=" + encodeURIComponent(endIso) : ""));
      S.candles = d.candles.map(c => ({time: c.t, open: c.o, high: c.h, low: c.l, close: c.c}));
      S.series.setData(S.candles);
      sub.textContent = d.count + " " + S.tf.toUpperCase() + " candles" + (d.last_end_utc ? " · to " + when(d.last_end_utc) : "");
      drawOverlays();
      return true;
    } catch (e) { sub.textContent = "Candles could not be loaded: " + e.message; return false; }
  }
  async function loadMore() {
    if (S.loadingMore || !S.candles.length) return;
    S.loadingMore = true;
    try {
      const first = S.candles[0].time;
      const d = await get("candles?tf=" + S.tf + "&end=" + encodeURIComponent(new Date(first * 1000).toISOString().replace(".000", "")));
      const older = d.candles.map(c => ({time: c.t, open: c.o, high: c.h, low: c.l, close: c.c})).filter(c => c.time < first);
      if (older.length) {
        const rng = S.chart.timeScale().getVisibleLogicalRange();
        S.candles = older.concat(S.candles);
        S.series.setData(S.candles);
        if (rng) S.chart.timeScale().setVisibleLogicalRange({from: rng.from + older.length, to: rng.to + older.length});
        drawOverlays();
      }
    } catch (e) { /* the chart keeps what it has */ }
    setTimeout(() => { S.loadingMore = false; }, 800);
  }
  function fitRecent() {
    if (!S.candles.length) return;
    const n = S.candles.length, show = SHOW_BARS[S.tf] || 60;
    S.chart.timeScale().setVisibleLogicalRange({from: Math.max(0, n - show), to: n + 14});
  }
  function setTf(tf) {
    if (tf === S.tf) return;
    S.tf = tf;
    $q(".stp-seg").querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.tf === tf));
    if (isHist()) showHistoricalOnChart(); else loadCandles().then(fitRecent);
  }
  function barAt(ts) {   // the start time of the candle containing ts (a marker needs a real candle)
    let lo = 0, hi = S.candles.length - 1, best = null;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (S.candles[m].time <= ts) { best = S.candles[m].time; lo = m + 1; } else hi = m - 1; }
    return best;
  }

  // historical review: a selected recommendation that is not the live one (the live one is drawn as current)
  function isHist() { return !!(S.selected && S.detail && !(S.ov && S.ov.recommendation && S.ov.recommendation.id === S.selected)); }
  // what to draw: the live recommendation (or the selected historical one) and the latest analysis's levels
  function activePlan() {
    if (isHist()) { const c = S.detail.at_creation.card; return c && c.plan ? c.plan : null; }
    return S.ov && S.ov.recommendation ? S.ov.recommendation.plan : null;
  }
  // ---- the three chart views (owner's brief, 18 November 2026) ----------------------------------------------------
  // TRADE PLAN (default): candles, current price, entry zone, destinations, invalidation and the forecast direction.
  // MARKET STRUCTURE: plus significant 4-hour swings, daily and weekly levels, major/moderate confluence zones.
  // FULL ANALYSIS: every recorded level, quiet; hover a line or open the level list for details.
  // Everything is drawn in one SVG layer with one label column, so labels never overlap; only the current price has a
  // price-axis label. Nearby levels share one label; their values are never moved or rounded.
  function setMode(m) {
    if (m === S.mode) return;
    S.mode = m;
    $q(".stp-modes").querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.mode === m));
    drawOverlays();
  }
  const GROUP = {h4_swing: ["#c58cff", "4-hour swing"], daily_sr: ["#ffaa00", "daily swing / previous day"],
                 weekly_sr: ["#ff7a3d", "previous week"], daily_pivot: ["#4fc3f7", "daily pivot, R, S"],
                 weekly_pivot: ["#2f8ff0", "weekly pivot, R, S"], h1: ["#8a8aa0", "hourly swing"],
                 session: ["#a8977a", "session high/low"], round: ["#7aa6a6", "round number"], ma: ["#a87aa0", "moving average"],
                 other: ["#8a8aa0", "other"]};
  const RANK = ["weekly_pivot", "weekly_sr", "daily_pivot", "daily_sr", "h4_swing", "round", "session", "h1", "ma", "other"];
  const PLAN = {primary: ["#5b8cff", "", 2, 1], inter: ["#8fa8e8", "2 3", 1, 0.9], ext: ["#5b8cff", "7 4", 1, 0.65],
                inval: ["#ff3b3b", "", 1.5, 0.95], inval2: ["#ff3b3b", "7 4", 1, 0.6]};
  const LABEL_H = 15;
  const grp = (g) => GROUP[g] || GROUP.other;
  const shortName = (n) => String(n || "").replace("4-hour swing ", "H4 swing ").replace("hourly swing ", "H1 swing ").replace("previous ", "prev ");

  // the recorded structure for the view: the latest analysis's, or the selected recommendation's snapshot at creation
  function structureSet() {
    if (isHist()) return S.detail.overlays_at_creation || null;
    return (S.ov && S.ov.overlays) || null;
  }
  function viewLevels() {
    if (S.mode === "plan") return [];
    const set = structureSet(); if (!set) return [];
    return (set.levels || []).filter(l => l.price !== null && l.price !== undefined && (S.mode === "full" || l.tier === "structure"));
  }
  function viewZones() {
    if (S.mode === "plan") return [];
    const set = structureSet(); if (!set) return [];
    return (set.zones || []).filter(z => z.low !== null && z.high !== null && (S.mode === "full" || z.tier === "structure"));
  }
  function planItems(p) {   // the trade plan's lines, most important first (they always get a label)
    if (!p) return [];
    const d = p.destinations || {}, out = [];
    if (d.primary) out.push({price: d.primary.price, text: d.primary.text, label: "PRIMARY " + d.primary.text, cls: "primary", why: "Primary destination"});
    (p.invalidation || []).forEach((x, i) => out.push({price: x.price, text: x.text, label: (i === 0 ? "INVALIDATION " : "STRUCTURE BREAK ") + x.text,
                                                       cls: i === 0 ? "inval" : "inval2", why: x.label}));
    if (d.intermediate) out.push({price: d.intermediate.price, text: d.intermediate.text, label: "INTERMEDIATE " + d.intermediate.text, cls: "inter", why: "Intermediate destination (the first obstacle)"});
    if (d.extended) out.push({price: d.extended.price, text: d.extended.text, label: "EXTENDED " + d.extended.text, cls: "ext", why: "Extended destination"});
    return out.filter(x => x.price !== null && x.price !== undefined);
  }
  // one label column: the plan's labels first (moved to the nearest free place if needed), then structure labels only
  // where there is room. Returns each label with its drawn position (ly).
  function placeLabels(items, top, bottom) {
    const placed = [], h = LABEL_H;
    const ok = (yy) => yy >= top + h / 2 && yy <= bottom - h / 2 && placed.every(q => Math.abs(q.ly - yy) >= h);
    items.slice().sort((a, b) => a.prio - b.prio || a.y - b.y).forEach(it => {
      if (it.prio === 1) {
        for (let d = 0; d <= 90; d += 1) { const yy = [it.y + d, it.y - d].find(ok); if (yy !== undefined) { placed.push(Object.assign({}, it, {ly: yy})); break; } }
      } else if (ok(it.y)) placed.push(Object.assign({}, it, {ly: it.y}));
    });
    return placed;
  }

  function drawOverlays() {
    if (!S.series) return;
    S.lines.forEach(l => { try { S.series.removePriceLine(l); } catch (e) { /* gone */ } }); S.lines = [];
    const hist = isHist();
    const px = S.ov && S.ov.price;
    if (!hist && px && px.price) S.lines.push(S.series.createPriceLine({price: px.price, color: "#e8e8f0aa", lineWidth: 1, lineStyle: 1, axisLabelVisible: true, title: ""}));
    const p = activePlan();
    // legend: only what this view draws
    const legend = $q(".stp-legend"); legend.textContent = "";
    const leg = (color, text, dash, band) => { const s = el("span"); const i = el("i", (dash ? "dash" : "") + (band ? " band" : "")); i.style.borderTopColor = color; if (band) i.style.background = color + "33"; s.appendChild(i); s.append(text); legend.appendChild(s); };
    if (p) {
      leg(p.trade === "SELL" ? "#ff4466" : "#00ff88", "entry zone", false, true); leg(PLAN.primary[0], "primary destination");
      leg(PLAN.inter[0], "intermediate / extended", true); leg(PLAN.inval[0], "invalidation"); leg("#e8e8f0", "forecast (schematic)", true);
    } else legend.appendChild(el("span", "", hist ? "" : "No live recommendation: no trade plan to draw."));
    if (S.mode !== "plan") {
      const groups = new Set(viewLevels().map(l => l.group));
      RANK.filter(g => groups.has(g)).forEach(g => leg(grp(g)[0], grp(g)[1], true));
      if (viewZones().length) leg("#9a9ab0", S.mode === "full" ? "confluence zones" : "major / moderate zones", true, true);
      if (!structureSet()) legend.appendChild(el("span", "stp-warnnote", hist ? "The full level map was not recorded for this recommendation (issued before 18 November 2026): only its trade plan can be replayed."
                                                                                : "No structural snapshot in the latest analysis."));
    }
    renderLevelList(p);
    // markers: past recommendations, or the selected one's lifecycle
    const markers = [];
    if (hist) {
      const st = S.detail.stages || {};
      const mk = (iso, text, color, pos, shape) => { if (!iso) return; const t = barAt(Math.floor(new Date(iso).getTime() / 1000)); if (t) markers.push({time: t, position: pos, color, shape, text}); };
      mk(st.created, "created", "#e8e8f0", "aboveBar", "arrowDown");
      const act = (S.detail.observed_after || {}).activation || {};
      mk(st.active, act.correction ? "active (recorded)" : "active", "#5b8cff", "aboveBar", "circle");
      if (act.correction && act.confirmed_utc) mk(act.confirmed_candle_start_utc, "zone reached after creation", "#ffaa00", "aboveBar", "circle");
      mk(st.completed, "completed", "#00ff88", "belowBar", "circle");
      mk(st.invalidated, "invalidated", "#ff4466", "belowBar", "square");
      mk(st.superseded, "superseded", "#6b6b80", "belowBar", "square");
    } else if (S.show.past) {
      (S.hist.rows || []).forEach(r => { const t = barAt(Math.floor(new Date(r.created_utc).getTime() / 1000));
        if (t) markers.push({time: t, position: r.trade === "SELL" ? "aboveBar" : "belowBar", color: r.trade === "SELL" ? "#ff446699" : "#00ff8899",
                             shape: r.trade === "SELL" ? "arrowDown" : "arrowUp", text: ""}); });
    }
    markers.sort((a, b) => a.time - b.time);
    S.series.setMarkers(markers);
    schedule();
  }

  function renderLevelList(p) {
    const det = $q(".stp-levels"); if (!det) return;
    const body = det.querySelector(".stp-levelbody"); body.textContent = "";
    const set = structureSet();
    const lv = S.mode === "plan" ? [] : viewLevels().slice().sort((a, b) => b.price - a.price);
    det.querySelector("summary").textContent = S.mode === "plan" ? "Level list — trade plan" : "Level list — " + lv.length + " recorded level" + (lv.length === 1 ? "" : "s") + (S.mode === "full" ? " (all)" : " (market structure)");
    const t = el("table", "stp-table stp-leveltable"); const tb = el("tbody");
    const row = (price, name, what, color) => { const tr = el("tr"); const a = el("td", "num", price); const b = el("td", "", name); const c = el("td", "hide-sm", what); if (color) a.style.borderLeft = "3px solid " + color; add(tr, a, b, c); tb.appendChild(tr); };
    if (p) {
      if (p.entry_zone) row(p.entry_zone.text, "Entry zone (" + (p.entry_zone.class || "") + ")", "trade plan", p.trade === "SELL" ? "#ff4466" : "#00ff88");
      planItems(p).forEach(it => row(it.text, it.why, "trade plan", PLAN[it.cls][0]));
    }
    lv.forEach(l => row(l.price_text, l.name + (l.role ? " (" + l.role + ")" : ""), grp(l.group)[1] + (l.timeframe ? " · " + l.timeframe : ""), grp(l.group)[0]));
    if (!tb.children.length) { body.appendChild(el("div", "stp-empty", set || S.mode === "plan" ? "Nothing to list." : "No full level map recorded.")); return; }
    t.appendChild(tb); const w = el("div", "stp-tablewrap"); w.appendChild(t); body.appendChild(w);
  }

  // the layer: zones, levels, the plan, labels and the forecast
  function drawLayer() {
    const layer = $q(".stp-layer"); if (!layer || !S.series) return;
    layer.textContent = ""; S.hoverItems = []; S.placed = [];
    const ts = S.chart.timeScale();
    const W = layer.clientWidth, H = layer.clientHeight;
    const plotW = Math.max(0, W - (S.chart.priceScale("right").width() || 60));
    const plotH = Math.max(0, H - (ts.height() || 26));
    const yOf = (price) => { const v = S.series.priceToCoordinate(price); return v === null || v === undefined ? null : v; };
    const inView = (v) => v !== null && v >= 0 && v <= plotH;
    const NS = "http://www.w3.org/2000/svg";
    const mk = (tag, attrs) => { const e = document.createElementNS(NS, tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v)); return e; };
    const svg = mk("svg", {width: W, height: H}); svg.style.position = "absolute"; svg.style.left = "0"; svg.style.top = "0";
    const hline = (price, color, width, dash, opacity) => { const y = yOf(price); if (!inView(y)) return null;
      svg.appendChild(mk("line", {x1: 0, x2: plotW, y1: y, y2: y, stroke: color, "stroke-width": width, "stroke-dasharray": dash || "", opacity: opacity})); return y; };
    const band = (low, high, fill, stroke, dash) => { let y1 = yOf(high), y2 = yOf(low); if (y1 === null || y2 === null) return null;
      const a = Math.max(0, Math.min(y1, y2)), b = Math.min(plotH, Math.max(y1, y2)); if (b <= a && !(b === a && inView(a))) return null;
      svg.appendChild(mk("rect", {x: 0, y: a, width: plotW, height: Math.max(2, b - a), fill, stroke, "stroke-width": 1, "stroke-dasharray": dash || ""})); return (a + b) / 2; };
    const labels = [];
    const hist = isHist(), p = activePlan();
    // structure (MARKET STRUCTURE / FULL ANALYSIS)
    viewZones().forEach(z => { const m = band(z.low, z.high, "#ffffff07", "#ffffff22", "3 3");
      if (m !== null) S.hoverItems.push({y: m, text: z.text + "  " + (z.class || "") + " confluence zone"}); });
    const lv = viewLevels().map(l => Object.assign({}, l, {y: yOf(l.price)})).filter(l => inView(l.y)).sort((a, b) => a.y - b.y);
    const groups = [];
    lv.forEach(l => { const g = groups[groups.length - 1]; if (g && l.y - g.y0 <= 9) g.items.push(l); else groups.push({y0: l.y, items: [l]}); });
    groups.forEach(g => {
      g.items.forEach(l => hline(l.price, grp(l.group)[0], 1, l.tier === "structure" ? "5 3" : "2 4", l.tier === "structure" ? 0.7 : 0.35));
      g.items.sort((a, b) => RANK.indexOf(a.group) - RANK.indexOf(b.group));
      const top = g.items[0], structural = g.items.filter(i => i.tier === "structure");
      if (S.mode === "structure" || structural.length) {
        const lead = structural[0] || top;
        labels.push({y: lead.y, prio: 2, color: grp(lead.group)[0], text: shortName(lead.name) + " " + lead.price_text + (g.items.length > 1 ? "  +" + (g.items.length - 1) : "")});
      }
      g.items.forEach(l => S.hoverItems.push({y: l.y, color: grp(l.group)[0], text: l.price_text + "  " + l.name + (l.role ? " (" + l.role + ")" : "") + " · " + grp(l.group)[1]}));
    });
    // the trade plan (every view)
    if (p) {
      const d = p.destinations || {};
      if (d.primary && d.primary.zone) band(d.primary.zone.low, d.primary.zone.high, "#5b8cff12", "#5b8cff44", "3 3");
      if (p.entry_zone) {
        const col = p.trade === "SELL" ? "#ff4466" : "#00ff88";
        const m = band(p.entry_zone.low, p.entry_zone.high, col + "2e", col + "bb", "");
        if (m !== null) { labels.push({y: m, prio: 1, color: col, solid: true, text: (hist ? "ORIGINAL " : "") + "ENTRY ZONE " + p.entry_zone.text + " · " + p.trade});
                          S.hoverItems.push({y: m, color: col, text: p.entry_zone.text + "  entry zone (" + (p.entry_zone.class || "") + ")"}); }
      }
      planItems(p).forEach(it => { const [col, dash, w, op] = PLAN[it.cls]; const y = hline(it.price, col, w, dash, op);
        if (y !== null) { labels.push({y, prio: 1, color: col, solid: true, text: it.label}); S.hoverItems.push({y, color: col, text: it.text + "  " + it.why}); } });
    }
    // the forecast: right of NOW (live), or from the creation candle (historical, the original forecast)
    let anchorIdx = S.candles.length - 1;
    if (hist && S.detail.stages.created) { const t = barAt(Math.floor(new Date(S.detail.stages.created).getTime() / 1000)); const i = S.candles.findIndex(c => c.time === t); if (i >= 0) anchorIdx = i; }
    const xa = S.candles.length ? ts.logicalToCoordinate(anchorIdx) : null;
    if (xa !== null && xa !== undefined && xa > 0 && xa < plotW) {
      const xs = xa + 4;
      if (!hist) svg.appendChild(mk("rect", {x: xs, y: 0, width: Math.max(0, plotW - xs), height: plotH, fill: "#ffffff05"}));
      svg.appendChild(mk("line", {x1: xs, x2: xs, y1: 0, y2: plotH, stroke: "#e8e8f0", "stroke-width": 1, "stroke-dasharray": "2 3", opacity: 0.45}));
      const cap = mk("text", {x: xs + 4, y: plotH - 6, fill: "#9a9ab0", "font-size": 9, "font-family": "JetBrains Mono, monospace"});
      cap.textContent = hist ? "CREATED" : "NOW"; svg.appendChild(cap);
      if (p && p.entry_zone && p.destinations && p.destinations.primary) {
        const a = S.candles[anchorIdx];
        const start = hist ? a.close : ((S.ov.price && S.ov.price.price) || a.close);
        const room = hist ? Math.min(90, plotW - xs - 8) : plotW - xs - 8;
        const x1 = xs + room * 0.4, x2 = xs + room * 0.92;
        const y0 = yOf(start), y1 = yOf((p.entry_zone.low + p.entry_zone.high) / 2), y2 = yOf(p.destinations.primary.price);
        if (room > 36 && [y0, y1, y2].every(v => v !== null)) {
          const defs = mk("defs", {}); const m = mk("marker", {id: "stpArrow", viewBox: "0 0 10 10", refX: 8, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse"});
          m.appendChild(mk("path", {d: "M0,0 L10,5 L0,10 z", fill: "#e8e8f0"})); defs.appendChild(m); svg.appendChild(defs);
          const seg = (xp, yp, xq, yq) => svg.appendChild(mk("line", {x1: xp, y1: yp, x2: xq, y2: yq, stroke: "#e8e8f0", "stroke-width": 1.6, "stroke-dasharray": "6 5", "marker-end": "url(#stpArrow)", opacity: hist ? 0.6 : 0.85}));
          seg(xs, y0, x1, y1); seg(x1, y1, x2, y2);
          const t = mk("text", {x: xs + 4, y: 12, fill: "#e8e8f0", "font-size": 9, "font-family": "JetBrains Mono, monospace", opacity: 0.8});
          t.textContent = hist ? "ORIGINAL FORECAST" : "FORECAST (schematic)"; svg.appendChild(t);
        }
      }
    }
    layer.appendChild(svg);
    // the label column (left edge of the chart, clear of the forecast on the right)
    const placed = placeLabels(labels, 0, plotH);
    placed.forEach(q => {
      if (Math.abs(q.ly - q.y) > 1) svg.appendChild(mk("line", {x1: 2, x2: 2, y1: q.y, y2: q.ly, stroke: q.color, "stroke-width": 1, opacity: 0.8}));
      const lab = el("div", "stp-lab" + (q.solid ? " plan" : ""), q.text);
      lab.style.top = (q.ly - LABEL_H / 2) + "px"; lab.style.borderLeftColor = q.color; if (q.solid) lab.style.color = q.color;
      layer.appendChild(lab);
    });
    S.placed = placed;
  }

  // hover details: every line within a few pixels of the pointer
  function hover(ev) {
    const tip = $q(".stp-hover"); if (!tip) return;
    const r = $q(".stp-chartbox").getBoundingClientRect();
    const y = ev.clientY - r.top, x = ev.clientX - r.left;
    const near = S.hoverItems.filter(h => Math.abs(h.y - y) <= 5).slice(0, 12);
    if (!near.length) { tip.style.display = "none"; return; }
    tip.textContent = "";
    near.sort((a, b) => a.y - b.y).forEach(h => { const d = el("div", "", h.text); if (h.color) d.style.borderLeftColor = h.color; tip.appendChild(d); });
    tip.style.display = "block";
    const w = tip.offsetWidth, hh = tip.offsetHeight;
    tip.style.left = Math.max(4, Math.min(x + 14, r.width - w - 4)) + "px";
    tip.style.top = Math.max(4, Math.min(y + 14, r.height - hh - 4)) + "px";
  }

  // ---- lifecycle ------------------------------------------------------------------------------------------------
  function renderLifecycle() {
    const box = $q(".stp-lifebox"); box.textContent = "";
    const d = S.detail;
    if (!d) { box.appendChild(el("div", "stp-empty", S.hist.total ? "Select a recommendation in the history below to see its lifecycle." : "No recommendation has been recorded yet.")); return; }
    const h = el("h3"); add(h, el("span", "", d.id + (d.live ? " · live" : "")), el("span", "stp-pill st-" + d.status, d.status_label)); box.appendChild(h);
    box.appendChild(el("div", "stp-note", "A recommendation is a recorded forecast, not a trade: nothing was opened or executed."));
    const life = el("div", "stp-life"); const st = d.stages || {};
    const endKind = st.completed ? "COMPLETED" : st.invalidated ? "INVALIDATED" : st.superseded ? "SUPERSEDED" : null;
    const stages = [["CREATED", st.created], ["WAITING FOR ZONE", st.waiting], ["ACTIVE (ZONE REACHED)", st.active]];
    stages.push([endKind || "ENDED", endKind ? (st.completed || st.invalidated || st.superseded) : null]);
    stages.forEach(([name, t], i) => {
      if (i) life.appendChild(el("div", "stp-arrow", "→"));
      const s = el("div", "stp-stage " + (t ? "done" : "none") + (i === 3 && endKind ? " end-" + endKind : ""));
      add(s, el("div", "n", name), el("div", "t", t ? when(t) : (i === 2 && endKind ? "never reached" : i === 3 ? (d.live ? "still live" : "not recorded") : "not recorded")));
      life.appendChild(s);
    });
    box.appendChild(life);
    if (d.outcome) box.appendChild(el("div", "stp-explain", "Outcome: " + d.outcome + " — " + (d.outcome_reason || "")));
    box.appendChild(el("div", "stp-h", "Every recorded event (in order)"));
    const ev = el("div", "stp-events");
    d.timeline.forEach(e => { const r = el("div"); add(r, el("span", "", when(e.time_utc)), el("span", "", e.label), el("span", "w", e.why || "")); ev.appendChild(r); });
    box.appendChild(ev);
    const two = el("div", "stp-two"); two.style.marginTop = "12px";
    const a = el("div", "stp-card"); a.appendChild(el("h3", "", "Forecast information available at creation"));
    const c = d.at_creation.card || {};
    a.appendChild(el("div", "stp-note", "Source: " + d.at_creation.note));
    const cp = c.plan || {}, cd = cp.destinations || {};
    rows(a, [["Created", when(c.created_utc)], ["Direction", c.dominant_direction, dirClass(c.dominant_direction)], ["Condition", nice(c.condition)],
             ["Opportunity", c.opportunity], ["Preferred", c.trade, dirClass(c.trade)], ["Entry zone", c.entry_zone], ["Reference", c.reference],
             ["Reachability", c.reachability], ["Intermediate", cd.intermediate ? cd.intermediate.text : "not recorded"],
             ["Primary destination", cd.primary ? cd.primary.text : "not recorded"], ["Extended", cd.extended ? cd.extended.text : "not recorded"]]);
    a.appendChild(el("div", "stp-h", "Original invalidation")); list(a, cp.invalidation_conditions, "not recorded in the planner's history for this recommendation");
    a.appendChild(el("div", "stp-h", "Original evidence")); list(a, c.evidence, "not recorded");
    const b = el("div", "stp-card"); const oa = d.observed_after || {};
    b.appendChild(el("h3", "", "Market movement observed afterwards"));
    b.appendChild(el("div", "stp-note", oa.label || ""));
    rows(b, [["Final status", d.status_label], ["Ended", d.ended_utc ? when(d.ended_utc) : (d.live ? "still live" : "–")],
             ["Activation candle (recorded)", oa.activation && oa.activation.recorded_candle_start_utc ? when(oa.activation.recorded_candle_start_utc) + " · " + oa.activation.recorded_timing : "–", null, "Where the candle that the planner recorded as reaching the zone lies against the recommendation's creation"],
             ["Zone reached after creation", oa.activation && oa.activation.confirmed_utc ? "candle " + when(oa.activation.confirmed_candle_start_utc) : "not confirmed", null, "Only market evidence after creation counts (correction of 18 November 2026)"],
             ["Creation → zone", oa.minutes_to_zone === null || oa.minutes_to_zone === undefined ? "zone not reached after creation" : oa.minutes_to_zone + " min"],
             ["Active → primary", oa.minutes_active_to_end === null || oa.minutes_active_to_end === undefined ? "–" : oa.minutes_active_to_end + " min"],
             ["Max favourable excursion", oa.mfe_pips === null || oa.mfe_pips === undefined ? "– (not activated)" : oa.mfe_pips + " pips", null, "Furthest price moved in the forecast direction after the zone was reached, from the reference level. A distance, not a profit."],
             ["Max adverse excursion", oa.mae_pips === null || oa.mae_pips === undefined ? "– (not activated)" : oa.mae_pips + " pips", null, "Furthest price moved against the forecast after the zone was reached, from the reference level."]]);
    if (oa.measured_from) b.appendChild(el("div", "stp-note", "Measured from " + oa.measured_from));
    if (oa.ambiguities && oa.ambiguities.length) { b.appendChild(el("div", "stp-h", "Notes and ambiguities")); list(b, oa.ambiguities); }
    if (d.latest) { b.appendChild(el("div", "stp-h", "Latest version (updated by hourly re-checks)")); list(b, ["Entry zone " + d.latest.entry_zone, "Status " + d.latest.status_label]); }
    add(two, a, b); box.appendChild(two);
  }

  async function select(id, scroll) {
    S.selected = id;
    try { S.detail = await get("recommendation?id=" + encodeURIComponent(id)); }
    catch (e) { S.detail = null; $q(".stp-lifebox").textContent = ""; $q(".stp-lifebox").appendChild(el("div", "stp-err", "Could not load " + id + ": " + e.message)); return; }
    renderLifecycle(); renderHistoryTable();
    const live = S.ov && S.ov.recommendation && S.ov.recommendation.id === id;
    if (live) { clearHistorical(false); return; }
    showHistoricalOnChart();
    if (scroll) $q(".stp-chartcard").scrollIntoView({behavior: "smooth", block: "start"});
  }
  async function selectQuiet(id) {   // the lifecycle panel shows the newest one; the chart stays on the current view
    S.selected = null;
    try { S.detail = await get("recommendation?id=" + encodeURIComponent(id)); } catch (e) { S.detail = null; }
    renderLifecycle();
  }
  async function showHistoricalOnChart() {
    const st = S.detail.stages || {};
    const end = st.completed || st.invalidated || st.superseded;
    const span = {"4h": 24, "1h": 30, "5m": 40}[S.tf] * {"4h": 4 * 3600, "1h": 3600, "5m": 300}[S.tf] * 1000;
    const endAt = end ? new Date(Math.min(Date.now(), new Date(end).getTime() + span)).toISOString().replace(/\.\d{3}Z$/, "Z") : null;
    const slot = $q(".stp-histslot"); slot.textContent = "";
    const bn = el("div", "stp-histbanner"); bn.appendChild(el("span", "", "Historical review: " + S.detail.id + " — original plan as issued; candles after creation are what happened afterwards."));
    const back = el("button", "stp-tog", "Back to current"); back.type = "button"; back.addEventListener("click", () => clearHistorical(true)); bn.appendChild(back);
    slot.appendChild(bn);
    await loadCandles(endAt);
    const t0 = barAt(Math.floor(new Date(st.created).getTime() / 1000));
    const i0 = S.candles.findIndex(c => c.time === t0);
    if (i0 >= 0) S.chart.timeScale().setVisibleLogicalRange({from: Math.max(0, i0 - 28), to: S.candles.length + 4});
  }
  function clearHistorical(reload) {
    const was = isHist();
    $q(".stp-histslot").textContent = "";
    if (reload) { S.selected = null; S.detail = null; renderLifecycle(); renderHistoryTable(); defaultSelection(); }
    if (was || reload) loadCandles().then(fitRecent); else drawOverlays();
  }

  // ---- history ----------------------------------------------------------------------------------------------------
  function buildHistory() {
    const box = $q(".stp-histbox"); box.textContent = "";
    const bar = el("div", "stp-hbar");
    const q = el("input", "stp-search"); q.type = "search"; q.placeholder = "Search id, direction, zone, status, reason…"; q.value = S.hist.q;
    let tmo = 0; q.addEventListener("input", () => { clearTimeout(tmo); tmo = setTimeout(() => { S.hist.q = q.value; S.hist.page = 1; loadHistory(); }, 300); });
    bar.appendChild(q);
    bar.appendChild(el("span", "stp-note stp-histcount", ""));
    box.appendChild(bar);
    const wrap = el("div", "stp-tablewrap"); const t = el("table", "stp-table"); wrap.appendChild(t); box.appendChild(wrap);
    const pg = el("div", "stp-pager"); box.appendChild(pg);
    box.appendChild(el("div", "stp-note", "One row per recommendation id. Recommendations with identical zones stay separate when their ids or lifecycles differ. Select a row to review it on the chart."));
  }
  function renderHistoryTable() {
    const box = $q(".stp-histbox"); if (!box) return;
    const t = box.querySelector("table"); t.textContent = "";
    const head = el("tr");
    [["Created", "created", ""], ["Id", null, "hide-sm"], ["Direction", "trade", ""], ["Opportunity", null, "hide-sm"], ["Entry zone", null, ""],
     ["Primary", null, "hide-sm"], ["Status", "status", ""], ["Outcome", null, "hide-sm"], ["Reason", null, "hide-sm"]].forEach(([n, key, cls]) => {
      const th = el("th", (key ? "sort " : "") + cls, n + (key && S.hist.sort === key ? (S.hist.order === "desc" ? " ▾" : " ▴") : ""));
      if (key) th.addEventListener("click", () => { if (S.hist.sort === key) S.hist.order = S.hist.order === "desc" ? "asc" : "desc"; else { S.hist.sort = key; S.hist.order = "desc"; } S.hist.page = 1; loadHistory(); });
      head.appendChild(th);
    });
    const th = el("thead"); th.appendChild(head); t.appendChild(th);
    const tb = el("tbody");
    if (!S.hist.rows.length) { const tr = el("tr"); const td = el("td", "", S.hist.q ? "No recommendation matches." : "No recommendation recorded yet."); td.colSpan = 9; tr.appendChild(td); tb.appendChild(tr); }
    S.hist.rows.forEach(r => {
      const tr = el("tr", "row" + (S.selected === r.id ? " sel" : ""));
      add(tr, el("td", "", when(r.created_utc)), el("td", "hide-sm", r.id), el("td", dirClass(r.trade), arrow(r.trade) + (r.trade || "–")),
          el("td", "hide-sm", r.opportunity || "–"), el("td", "", r.zone || "–"), el("td", "hide-sm", r.primary || "–"));
      const s = el("td"); s.appendChild(el("span", "stp-pill st-" + r.status, r.status_label + (r.live ? " · live" : ""))); tr.appendChild(s);
      add(tr, el("td", "hide-sm", r.outcome || "–"), el("td", "reason hide-sm", r.reason || ""));
      tr.addEventListener("click", () => select(r.id, true));
      tb.appendChild(tr);
    });
    t.appendChild(tb);
    box.querySelector(".stp-histcount").textContent = S.hist.total + " recommendation" + (S.hist.total === 1 ? "" : "s");
    const pg = box.querySelector(".stp-pager"); pg.textContent = "";
    const prev = el("button", "stp-tog", "‹ Newer"), next = el("button", "stp-tog", "Older ›"); prev.type = next.type = "button";
    prev.disabled = S.hist.page <= 1; next.disabled = S.hist.page >= S.hist.pages;
    prev.addEventListener("click", () => { S.hist.page--; loadHistory(); }); next.addEventListener("click", () => { S.hist.page++; loadHistory(); });
    add(pg, prev, el("span", "", "page " + S.hist.page + " of " + S.hist.pages), next);
  }
  async function loadHistory() {
    const h = S.hist;
    try {
      const d = await get(`history?page=${h.page}&size=${h.size}&sort=${h.sort}&order=${h.order}&q=${encodeURIComponent(h.q)}`);
      h.rows = d.rows; h.total = d.total; h.pages = d.pages;
    } catch (e) { h.rows = []; const box = $q(".stp-histbox"); box.appendChild(el("div", "stp-err", "History could not be loaded: " + e.message)); }
    renderHistoryTable(); drawOverlays();
  }
  function defaultSelection() {
    const live = S.ov && S.ov.recommendation;
    if (live) select(live.id, false);
    else if (S.hist.rows.length) { const newest = S.hist.rows.slice().sort((a, b) => (b.created_utc || "").localeCompare(a.created_utc || ""))[0]; selectQuiet(newest.id); }
    else renderLifecycle();
  }

  // ---- evaluation ---------------------------------------------------------------------------------------------------
  async function loadEvaluation() {
    const box = $q(".stp-evalbox"); box.textContent = "";
    let e; try { e = await get("evaluation"); } catch (err) { box.appendChild(el("div", "stp-err", "Evaluation could not be loaded: " + err.message)); return; }
    const card = el("div", "stp-card");
    card.appendChild(el("div", "stp-note", e.label + ". Observation period: " + (e.period_start_utc ? when(e.period_start_utc) + " to " + when(e.period_end_utc) : "not started") +
                                            " · " + e.analyses + " hourly analyses recorded (" + e.analyses_recommending + " with a recommendable plan)."));
    const tiles = el("div", "stp-evtiles"); tiles.style.marginTop = "10px";
    const c = e.counts;
    const T = (k, v, s, tip) => { const t = el("div", "stp-ev"); const kk = el("div", "k", k); if (tip) { kk.title = tip; kk.classList.add("stp-tip"); } t.appendChild(kk);
      t.appendChild(el("div", "v" + (v === "INSUFFICIENT DATA" ? " ins" : String(v).length > 10 ? " long" : ""), String(v))); if (s) t.appendChild(el("div", "s", s)); tiles.appendChild(t); };
    T("Total recommendations", c.total); T("Awaiting entry now", c.awaiting_entry);
    T("Activated (zone reached after creation)", c.activated, c.activation_corrected ? (c.activated_as_recorded + " as recorded; " + c.activation_corrected + " corrected") : null, "Only candles that began after the recommendation was created count; see the corrections listed below");
    T("Completed", c.completed); T("Invalidated", c.invalidated); T("Superseded", c.superseded);
    T("Never reached their zone", c.never_reached_zone, "of " + e.ended + " ended");
    T("Reached primary destination", c.reached_primary, c.reached_primary_after_entry + " after a confirmed zone visit, " + c.destination_before_entry + " before the zone" + (c.completed_without_confirmed_activation ? ", " + c.completed_without_confirmed_activation + " completed without one" : ""));
    T("Invalidated before primary", c.invalidated_before_primary);
    T("Issued with price already at the primary destination", c.issued_at_destination, "see the investigation report", "The last finished 5-minute candle before creation was within 3 pips of the primary destination");
    const D = (k, x, tip) => T(k, x.verdict || (x.median + " " + x.unit), x.verdict ? ("n = " + x.n + (x.values.length ? " · values: " + x.values.join(", ") : "")) : ("median · n = " + x.n + " · range " + x.min + "–" + x.max), tip);
    D("Max favourable excursion after activation", e.mfe_pips, "From the reference level, in pips; a distance, not a profit");
    D("Max adverse excursion after activation", e.mae_pips, "From the reference level, in pips");
    D("Creation → entry-zone interaction", e.minutes_to_zone);
    D("Activation → primary destination", e.minutes_active_to_primary);
    T("Stability across hourly re-analysis", e.stability.verdict || (e.stability.supported + " supported / " + e.stability.changed + " changed"),
      e.stability.rechecks + " re-checks · " + e.stability.superseded + " superseded", "Each hourly re-check of a live recommendation: unchanged (supported), changed (same structure), or replaced (superseded)");
    card.appendChild(tiles);
    if (e.ambiguous && e.ambiguous.length) { card.appendChild(el("div", "stp-h", "Corrections, ambiguous or noteworthy event order")); list(card, e.ambiguous.map(a => a.id + ": " + a.notes.join("; "))); }
    card.appendChild(el("div", "stp-h", "Methodology")); list(card, e.methodology);
    box.appendChild(card);
  }

  // ---- technical evidence ------------------------------------------------------------------------------------------
  function renderTech() {
    const g = $q(".stp-techgrid"); g.textContent = "";
    const o = S.ov; if (!o.available || !o.technical) { g.appendChild(el("div", "stp-empty", "No technical evidence: the planner has not written an analysis.")); return; }
    const t = o.technical;
    const C = (title, fill) => { const c = el("div", "stp-card"); c.appendChild(el("h3", "", title)); fill(c); g.appendChild(c); };
    C("4-hour swing structure (direction)", c => list(c, t.direction_evidence));
    C("Condition evidence", c => list(c, t.condition_evidence));
    C("Daily and weekly context", c => rows(c, [["Daily structure", t.daily_structure], ["Daily pivot", t.vs_daily_pivot], ["Weekly pivot", t.vs_weekly_pivot],
                                             ["Last 4-hour opposite swing", o.forecast && o.forecast.h4_last_swing ? o.forecast.h4_last_swing.kind + " " + o.forecast.h4_last_swing.text : null]]));
    C("Indicators (4-hour)", c => rows(c, [
      ["EMA 7/13/21", t.ema.stack, null, "Exponential moving averages: their order shows short-term direction"],
      ["EMA100", t.ema.ema100, null, "Longer-term trend reference"], ["EMA200", t.ema.ema200], ["EMA100 slope", t.ema.ema100_slope_pips === undefined ? null : t.ema.ema100_slope_pips + " pips / 6 candles"],
      ["RSI 3", t.rsi3, null, "Very fast relative strength index (70/30 lines)"],
      ["MACD 35/45/30", t.macd ? ("line " + t.macd.line + " · signal " + t.macd.signal + " · hist " + t.macd.histogram) : null, null, "Momentum: line, signal and histogram"],
      ["Bollinger 20/2", t.bollinger.position, null, "Where the last close sits relative to the bands"],
      ["Bands", t.bollinger.upper ? t.bollinger.lower + " / " + t.bollinger.middle + " / " + t.bollinger.upper : null],
      ["Band width", t.bollinger.width_pips ? t.bollinger.width_pips + " pips" : null]]));
    C("Daily range", c => rows(c, [["ADR (20 weekdays)", t.adr_pips ? t.adr_pips + " pips" : null, null, "Average daily range"], ["Today's range", t.today_range_pips ? t.today_range_pips + " pips" : null],
                                  ["Share of ADR", t.today_range_adr], ["Room left", t.remaining_room_pips ? t.remaining_room_pips + " pips" : null],
                                  ["Impulse", t.impulse.pips ? t.impulse.pips + " pips (" + t.impulse.adr + " ADR)" : null], ["Reward to invalidation", t.reward_to_invalidation]]));
    C("Directional conflicts", c => list(c, t.conflicts, "None recorded"));
    C("Indicator warm-up", c => { list(c, t.warming_up, "All indicators warmed up"); if (t.threshold_misses.length) { c.appendChild(el("div", "stp-h", "Threshold notes")); list(c, t.threshold_misses); } });
    C("Data freshness", c => { rows(c, [["State", o.freshness.label], ["Market data to", when(t.market_data_utc)], ["Planner's freshness rule", t.data_fresh ? "fresh" : "NOT fresh"]]); list(c, t.freshness_reasons); });
    C("Decision reasons", c => { list(c, [t.selection_reason && ("Zone choice: " + t.selection_reason), t.no_recommendation && ("No recommendation: " + t.no_recommendation),
                                         t.direction_rule_5m && t.direction_rule_5m.side && ("5-minute direction rule: " + t.direction_rule_5m.side + (t.direction_rule_5m.reason ? " — " + t.direction_rule_5m.reason : ""))].filter(Boolean), "None recorded"); });
    C("Structural confluence zones considered", c => {
      if (!t.candidates.length) { c.appendChild(el("div", "stp-empty", "None recorded in the latest analysis.")); return; }
      list(c, t.candidates.map(z => z.text + " · " + (z.class || "") + " · " + (z.reachability || "") + (z.chosen ? " · CHOSEN" : z.rejected_because ? " · " + z.rejected_because : "") + " · " + (z.families || []).join(", ")));
    });
  }

  // ---- start / refresh -------------------------------------------------------------------------------------------
  async function refresh(first) {
    try { S.ov = await get("overview"); }
    catch (e) { S.ov = {available: false, freshness: {state: "UNAVAILABLE", label: "PLANNER UNAVAILABLE", detail: e.message}, explanation: {text: "The planner's data could not be loaded (" + e.message + "). The rest of the dashboard is unaffected."}}; }
    renderOverview();
    if (first) {
      await loadHistory();
      defaultSelection();
      loadEvaluation();
      if (S.chart) { await loadCandles(); fitRecent(); }
    } else if (!isHist()) {
      const rng = S.chart && S.chart.timeScale().getVisibleLogicalRange();
      const n = S.candles.length;
      if (S.chart && await loadCandles() && rng) { const dn = S.candles.length - n; S.chart.timeScale().setVisibleLogicalRange({from: rng.from + dn, to: rng.to + dn}); }
      loadHistory();
    }
  }

  window.STP = {
    mount(root) {
      if (S.root && root.contains(S.root)) { this.resume(); return; }
      build(root);
      ensureChart();
      if (!S.chart) $q(".stp-chartsub").textContent = "The chart library did not load.";
      buildHistory();
      refresh(true);
      this.resume();
    },
    resume() { clearInterval(S.timer); S.timer = setInterval(() => { if (!document.hidden) refresh(false); }, 60000); schedule(); },
    pause() { clearInterval(S.timer); S.timer = null; },
    _state: S,
  };
})();
