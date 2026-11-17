/* The Structural Trade Planner tab (owner's brief of 17 November 2026). OBSERVE ONLY: it shows what the planner
   recorded and never controls trading. Read only: it only GETs /api/stp/*. Every level, zone, destination and
   decision drawn is the planner's own; nothing is forecast or recommended here. Built with DOM calls, never HTML
   strings, so nothing from the records is run as HTML. Loaded by index.html when the tab is first opened. */
(function () {
  "use strict";
  const API = "/api/stp/";
  const TF_KEY = "stp.tf";
  const S = {
    tf: "1h", ov: null, candles: [], chart: null, series: null, lines: [], selected: null, detail: null,
    show: {structure: true, pivots: true, plan: true, zones: false, past: true},
    hist: {page: 1, size: 15, q: "", sort: "created", order: "desc", rows: [], total: 0, pages: 1},
    timer: null, loadingMore: false, root: null,
  };
  try { const t = localStorage.getItem(TF_KEY); if (["4h", "1h", "5m"].includes(t)) S.tf = t; } catch (e) { /* none */ }

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
    tb.appendChild(seg);
    [["structure", "Structure"], ["pivots", "Pivots"], ["zones", "Zones"], ["plan", "Trade plan"], ["past", "Past recs"]].forEach(([k, label]) => {
      const b = el("button", "stp-tog" + (S.show[k] ? " on" : ""), label); b.type = "button"; b.dataset.show = k;
      b.title = {structure: "Confirmed 4-hour swings, hourly levels, daily and weekly support/resistance recorded by the planner",
                 pivots: "Daily and weekly pivots recorded by the planner", zones: "The confluence zones the planner considered",
                 plan: "The recommendation's entry zone, destinations and invalidation", past: "Markers for past recommendations"}[k];
      b.addEventListener("click", () => { S.show[k] = !S.show[k]; b.classList.toggle("on", S.show[k]); drawOverlays(); });
      tb.appendChild(b);
    });
    const reset = el("button", "stp-tog", "Reset view"); reset.type = "button";
    reset.addEventListener("click", () => { if (S.chart) { S.chart.timeScale().resetTimeScale(); S.chart.priceScale("right").applyOptions({autoScale: true}); fitRecent(); } });
    tb.appendChild(reset);
    cc.appendChild(tb);
    const box = el("div", "stp-chartbox"); add(box, el("div", "stp-chart"), el("div", "stp-layer"));
    cc.appendChild(box);
    cc.appendChild(el("div", "stp-legend"));
    cc.appendChild(el("div", "stp-note", "Candles: finished candles only, chart (sell) price, UK time. The live, unfinished candle is not drawn; the dotted line is the current price. Dashed arrows are the planner's FORECAST direction sequence, drawn schematically: no timing or price path is implied."));
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
    renderPlan();
    renderTech();
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
                 ["Status", "NO RECOMMENDATION", "big"], ["Last updated", when((o.freshness || {}).last_analysis_utc)]]);
      box.appendChild(el("div", "stp-h", "Why there is no recommendation"));
      list(box, [o.explanation && o.explanation.text, o.explanation && o.explanation.planner_reason && ("Planner: " + o.explanation.planner_reason)].filter(Boolean));
      box.appendChild(el("div", "stp-note", "No entry zone, destination or invalidation is drawn: the planner has no live recommendation."));
      return;
    }
    const p = r.plan || {}, d = p.destinations || {};
    rows(box, [["Instrument", o.pair_text], ["Dominant direction", r.dominant_direction, dirClass(r.dominant_direction), "The 4-hour structural direction"],
               ["Market condition", nice(r.condition)], ["Opportunity", r.opportunity],
               ["Preferred direction", arrow(r.trade) + r.trade, "big " + dirClass(r.trade)],
               ["Entry zone", r.entry_zone + " (" + (r.zone_class || "") + ")", "big"],
               ["Reference level", r.reference, null, "The zone's primary structural reference level"],
               ["Reachability", r.reachability],
               ["Intermediate destination", d.intermediate ? d.intermediate.text : "none recorded", null, "The first relevant obstacle"],
               ["Primary destination", d.primary ? d.primary.text : "none recorded", "big"],
               ["Extended destination", d.extended ? d.extended.text : "none recorded"],
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
      timeScale: {borderColor: "#ffffff18", timeVisible: true, secondsVisible: false, rightOffset: 24,
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
    const n = S.candles.length, show = {"4h": 90, "1h": 120, "5m": 144}[S.tf] || 120;
    S.chart.timeScale().setVisibleLogicalRange({from: Math.max(0, n - show), to: n + 20});
  }
  function setTf(tf) {
    if (tf === S.tf) return;
    S.tf = tf; try { localStorage.setItem(TF_KEY, tf); } catch (e) { /* none */ }
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
  function drawOverlays() {
    if (!S.series) return;
    S.lines.forEach(l => { try { S.series.removePriceLine(l); } catch (e) { /* gone */ } }); S.lines = [];
    const L = (price, color, title, style, width, axis) => { if (price === null || price === undefined) return;
      S.lines.push(S.series.createPriceLine({price, color, lineWidth: width || 1, lineStyle: style === undefined ? 2 : style, axisLabelVisible: axis !== false, title: title || ""})); };
    const legend = $q(".stp-legend"); legend.textContent = "";
    const leg = (color, text, dash) => { const s = el("span"); const i = el("i", dash ? "dash" : ""); i.style.borderTopColor = color; s.appendChild(i); s.append(text); legend.appendChild(s); };
    const hist = isHist();
    const ov = (S.ov && S.ov.overlays) || {levels: [], zones: []};
    if (!hist) {
      // merge levels at the same price into one line with their names (one label per price)
      const by = new Map();
      (ov.levels || []).forEach(lv => {
        const isPivot = lv.group === "daily_pivot" || lv.group === "weekly_pivot";
        const isStruct = ["h4_swing", "h1", "daily_sr", "weekly_sr"].includes(lv.group);
        if ((isPivot && !S.show.pivots) || (isStruct && !S.show.structure) || (!isPivot && !isStruct)) return;
        const k = lv.price_text; if (!by.has(k)) by.set(k, []); by.get(k).push(lv);
      });
      const colour = {h4_swing: "#c58cff", h1: "#6b6b80", daily_sr: "#ffaa00", weekly_sr: "#ff7a3d", daily_pivot: "#4fc3f7", weekly_pivot: "#2196f3"};
      const rank = ["weekly_pivot", "weekly_sr", "daily_pivot", "daily_sr", "h4_swing", "h1"];
      by.forEach((lvs) => {
        lvs.sort((a, b) => rank.indexOf(a.group) - rank.indexOf(b.group));
        const top = lvs[0];
        const short = (n) => n.replace("4-hour swing ", "H4 swing ").replace("hourly swing ", "H1 swing ").replace("previous ", "prev ");
        const title = lvs.map(x => short(x.name)).filter((v, i, a) => a.indexOf(v) === i).slice(0, 2).join(" + ");
        // hourly levels, and any level more than one ADR from price: quiet lines without a label (they are many)
        const px0 = S.ov && S.ov.price && S.ov.price.price, adr = Number((S.ov.technical || {}).adr_pips || 0) * 0.0001;
        const strong = top.group !== "h1" && !(px0 && adr && Math.abs(top.price - px0) > adr);
        L(top.price, colour[top.group] + (strong ? "bb" : "55"), strong ? title : "", strong ? 2 : 1, 1, strong);
      });
      if (S.show.structure) { leg("#c58cff", "H4 swing"); leg("#6b6b80", "H1 level"); leg("#ffaa00", "daily S/R"); leg("#ff7a3d", "weekly S/R"); }
      if (S.show.pivots) { leg("#4fc3f7", "daily pivot"); leg("#2196f3", "weekly pivot"); }
      const px = S.ov && S.ov.price;
      if (px && px.price) L(px.price, "#e8e8f0", "price " + px.text, 1, 1, true);
    }
    const p = activePlan();
    if (p && S.show.plan) {
      const d = p.destinations || {};
      if (p.entry_zone) { L(p.entry_zone.low, p.trade === "SELL" ? "#ff4466" : "#00ff88", "", 0, 1, true); L(p.entry_zone.high, p.trade === "SELL" ? "#ff4466" : "#00ff88", "", 0, 1, true); }
      if (d.intermediate) L(d.intermediate.price, "#88aaff", "Intermediate", 2, 1, true);
      if (d.primary) L(d.primary.price, "#4488ff", "PRIMARY DESTINATION", 0, 2, true);
      if (d.extended) L(d.extended.price, "#4488ff99", "Extended", 2, 1, true);
      (p.invalidation || []).forEach(x => L(x.price, "#ff2222", x.label, 0, 2, true));
      leg(p.trade === "SELL" ? "#ff4466" : "#00ff88", "entry zone"); leg("#4488ff", "destinations"); leg("#ff2222", "invalidation");
      leg("#e8e8f0", "forecast path (schematic)", true);
    }
    // markers: past recommendations, or the selected one's lifecycle
    const markers = [];
    if (hist) {
      const st = S.detail.stages || {};
      const mk = (iso, text, color, pos, shape) => { if (!iso) return; const t = barAt(Math.floor(new Date(iso).getTime() / 1000)); if (t) markers.push({time: t, position: pos, color, shape, text}); };
      mk(st.created, "created", "#e8e8f0", "aboveBar", "arrowDown");
      mk(st.active, "active", "#4488ff", "aboveBar", "circle");
      mk(st.completed, "completed", "#00ff88", "belowBar", "circle");
      mk(st.invalidated, "invalidated", "#ff4466", "belowBar", "square");
      mk(st.superseded, "superseded", "#6b6b80", "belowBar", "square");
    } else if (S.show.past) {
      (S.hist.rows || []).forEach(r => { const t = barAt(Math.floor(new Date(r.created_utc).getTime() / 1000));
        if (t) markers.push({time: t, position: r.trade === "SELL" ? "aboveBar" : "belowBar", color: r.trade === "SELL" ? "#ff4466" : "#00ff88",
                             shape: r.trade === "SELL" ? "arrowDown" : "arrowUp", text: r.trade + " · " + (r.outcome || r.status)}); });
    }
    markers.sort((a, b) => a.time - b.time);
    S.series.setMarkers(markers);
    schedule();
  }

  // the HTML/SVG layer: shaded zones and the schematic forecast path
  function drawLayer() {
    const layer = $q(".stp-layer"); if (!layer || !S.series) return;
    layer.textContent = "";
    const ts = S.chart.timeScale();
    const width = layer.clientWidth - (S.chart.priceScale("right").width() || 60);
    const band = (low, high, cls, label) => {
      if (low === null || high === null || low === undefined || high === undefined) return;
      const y1 = S.series.priceToCoordinate(high), y2 = S.series.priceToCoordinate(low);
      if (y1 === null || y2 === null) return;
      const b = el("div", "stp-band " + cls); b.style.top = Math.min(y1, y2) + "px"; b.style.height = Math.max(2, Math.abs(y2 - y1)) + "px";
      b.style.width = Math.max(0, width) + "px"; if (label) b.appendChild(el("span", "", label)); layer.appendChild(b);
    };
    const hist = isHist();
    if (!hist && S.show.zones && S.ov && S.ov.overlays) (S.ov.overlays.zones || []).forEach(z => band(z.low, z.high, "cand", ""));
    const p = activePlan();
    if (!p || !S.show.plan) return;
    const d = p.destinations || {};
    ["intermediate", "primary", "extended"].forEach(k => { if (d[k] && d[k].zone) band(d[k].zone.low, d[k].zone.high, "dest", ""); });
    if (p.entry_zone) band(p.entry_zone.low, p.entry_zone.high, "entry " + p.trade, (hist ? "ORIGINAL " : "") + "ENTRY ZONE " + p.entry_zone.text + " · " + p.trade);
    // forecast path: from the anchor (latest candle, or the creation candle for a historical one), into the zone,
    // then towards the primary destination. A direction sequence only, drawn schematically to the right.
    if (!S.candles.length || !p.entry_zone || !d.primary) return;
    let anchorIdx = S.candles.length - 1;
    if (hist && S.detail.stages.created) { const t = barAt(Math.floor(new Date(S.detail.stages.created).getTime() / 1000)); const i = S.candles.findIndex(c => c.time === t); if (i >= 0) anchorIdx = i; }
    const a = S.candles[anchorIdx];
    const k1 = hist ? 3 : 8, k2 = hist ? 7 : 18;          // historical: short, beside the creation candle
    const x0 = ts.logicalToCoordinate(anchorIdx), x1 = ts.logicalToCoordinate(anchorIdx + k1), x2 = ts.logicalToCoordinate(anchorIdx + k2);
    const startPrice = hist ? a.close : ((S.ov.price && S.ov.price.price) || a.close);
    const y0 = S.series.priceToCoordinate(startPrice), y1 = S.series.priceToCoordinate((p.entry_zone.low + p.entry_zone.high) / 2), y2 = S.series.priceToCoordinate(d.primary.price);
    if ([x0, x1, x2, y0, y1, y2].some(v => v === null || v === undefined)) return;
    const NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg"); svg.setAttribute("width", layer.clientWidth); svg.setAttribute("height", layer.clientHeight);
    svg.style.position = "absolute"; svg.style.left = "0"; svg.style.top = "0";
    const defs = document.createElementNS(NS, "defs"); const m = document.createElementNS(NS, "marker");
    m.setAttribute("id", "stpArrow"); m.setAttribute("viewBox", "0 0 10 10"); m.setAttribute("refX", "8"); m.setAttribute("refY", "5");
    m.setAttribute("markerWidth", "7"); m.setAttribute("markerHeight", "7"); m.setAttribute("orient", "auto-start-reverse");
    const mp = document.createElementNS(NS, "path"); mp.setAttribute("d", "M0,0 L10,5 L0,10 z"); mp.setAttribute("fill", "#e8e8f0"); m.appendChild(mp); defs.appendChild(m); svg.appendChild(defs);
    const seg = (xa, ya, xb, yb) => { const l = document.createElementNS(NS, "line"); l.setAttribute("x1", xa); l.setAttribute("y1", ya); l.setAttribute("x2", xb); l.setAttribute("y2", yb);
      l.setAttribute("stroke", "#e8e8f0"); l.setAttribute("stroke-width", "1.6"); l.setAttribute("stroke-dasharray", "6 5"); l.setAttribute("marker-end", "url(#stpArrow)"); l.setAttribute("opacity", "0.85"); svg.appendChild(l); };
    seg(x0, y0, x1, y1); seg(x1, y1, x2, y2);
    const t = document.createElementNS(NS, "text"); t.setAttribute("x", Math.max(4, Math.min(x1 + 6, width - 300))); t.setAttribute("y", Math.max(12, Math.min(y1, y2) - 8));
    t.setAttribute("fill", "#e8e8f0"); t.setAttribute("font-size", "10"); t.setAttribute("font-family", "JetBrains Mono, monospace");
    t.textContent = (hist ? "ORIGINAL FORECAST" : "FORECAST") + " (schematic, no timing implied)"; svg.appendChild(t);
    layer.appendChild(svg);
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
             ["Creation → zone", oa.minutes_to_zone === null || oa.minutes_to_zone === undefined ? "zone not reached" : oa.minutes_to_zone + " min"],
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
    const span = {"4h": 40, "1h": 36, "5m": 72}[S.tf] * {"4h": 4 * 3600, "1h": 3600, "5m": 300}[S.tf] * 1000;
    const endAt = end ? new Date(Math.min(Date.now(), new Date(end).getTime() + span)).toISOString().replace(/\.\d{3}Z$/, "Z") : null;
    const slot = $q(".stp-histslot"); slot.textContent = "";
    const bn = el("div", "stp-histbanner"); bn.appendChild(el("span", "", "Historical review: " + S.detail.id + " — original plan as issued; candles after creation are what happened afterwards."));
    const back = el("button", "stp-tog", "Back to current"); back.type = "button"; back.addEventListener("click", () => clearHistorical(true)); bn.appendChild(back);
    slot.appendChild(bn);
    await loadCandles(endAt);
    const t0 = barAt(Math.floor(new Date(st.created).getTime() / 1000));
    const i0 = S.candles.findIndex(c => c.time === t0);
    if (i0 >= 0) S.chart.timeScale().setVisibleLogicalRange({from: Math.max(0, i0 - 30), to: S.candles.length + 6});
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
      t.appendChild(el("div", "v" + (v === "INSUFFICIENT DATA" ? " ins" : ""), String(v))); if (s) t.appendChild(el("div", "s", s)); tiles.appendChild(t); };
    T("Total recommendations", c.total); T("Awaiting entry now", c.awaiting_entry); T("Activated (zone reached)", c.activated);
    T("Completed", c.completed); T("Invalidated", c.invalidated); T("Superseded", c.superseded);
    T("Never reached their zone", c.never_reached_zone, "of " + e.ended + " ended");
    T("Reached primary destination", c.reached_primary, c.reached_primary_after_entry + " after the zone, " + c.destination_before_entry + " before it");
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
    if (e.ambiguous && e.ambiguous.length) { card.appendChild(el("div", "stp-h", "Ambiguous or noteworthy event order")); list(card, e.ambiguous.map(a => a.id + ": " + a.notes.join("; "))); }
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
