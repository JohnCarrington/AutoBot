"""Browser checks of the STP chart (dev harness). Prints one JSON result per check; exit 1 if any fails."""
import json, sys
from playwright.sync_api import sync_playwright
BASE = sys.argv[1]
res = []
def check(name, ok, detail=""):
    res.append({"check": name, "ok": bool(ok), "detail": detail})
OVERLAP = """() => { const b = [...document.querySelectorAll('.stp-lab')].map(e => e.getBoundingClientRect());
  let n = 0; for (let i = 0; i < b.length; i++) for (let j = i + 1; j < b.length; j++) { const a = b[i], c = b[j];
  if (a.top < c.bottom - 0.5 && c.top < a.bottom - 0.5 && a.left < c.right && c.left < a.right) n++; } return {labels: b.length, overlaps: n}; }"""
ALIGN = """() => { const S = window.STP._state; const p = S.ov && S.ov.recommendation && S.ov.recommendation.plan; if (!p) return null;
  const rect = [...document.querySelectorAll('.stp-layer svg rect')].find(r => r.getAttribute('fill').length === 9 && r.getAttribute('stroke') && r.getAttribute('stroke-dasharray') === '');
  const y1 = S.series.priceToCoordinate(p.entry_zone.high), y2 = S.series.priceToCoordinate(p.entry_zone.low);
  const lines = [...document.querySelectorAll('.stp-layer svg line')].map(l => +l.getAttribute('y1'));
  const want = [p.destinations.primary.price].concat(p.invalidation.map(x => x.price)).map(v => S.series.priceToCoordinate(v));
  return {band: rect ? [+rect.getAttribute('y'), +rect.getAttribute('y') + +rect.getAttribute('height')] : null, zone: [Math.min(y1, y2), Math.max(y1, y2)],
          lines_ok: want.every(w => w === null || lines.some(y => Math.abs(y - w) < 0.6)), fill: rect && rect.getAttribute('fill')}; }"""
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--no-sandbox"])
    for mobile in (False, True):
        tag = "mobile" if mobile else "desktop"
        ctx = b.new_context(viewport={"width": 390, "height": 844} if mobile else {"width": 1440, "height": 900}, is_mobile=mobile, has_touch=mobile)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" and "401" not in m.text else None)
        pg.goto(BASE + "/"); pg.fill("#pw", "dev-password-123"); pg.press("#pw", "Enter"); pg.wait_for_selector("#app", state="visible")
        pg.evaluate("localStorage.setItem('stp.tf', '5m')")            # an old remembered timeframe must not change the default
        pg.evaluate("location.hash='#stp'"); pg.wait_for_selector(".stp-wrap"); pg.wait_for_timeout(3000)
        st = pg.evaluate("() => ({mode: window.STP._state.mode, tf: window.STP._state.tf, n: window.STP._state.candles.length, r: window.STP._state.chart.timeScale().getVisibleLogicalRange()})")
        bars = st["r"]["to"] - 14 - st["r"]["from"]
        check(f"{tag}: default view is TRADE PLAN on H1 with 48-72 candles", st["mode"] == "plan" and st["tf"] == "1h" and 48 <= bars <= 72, st)
        modes = pg.evaluate("[...document.querySelectorAll('.stp-modes button')].map(b => b.dataset.mode + (b.classList.contains('on') ? '*' : ''))")
        check(f"{tag}: three viewing modes", modes == ["plan*", "structure", "full"], modes)
        a = pg.evaluate(ALIGN)
        if a:
            check(f"{tag}: entry zone shaded exactly between its recorded edges", a["band"] and abs(a["band"][0] - max(0, a["zone"][0])) < 0.6 and abs(a["band"][1] - a["zone"][1]) < 0.6 and a["fill"].endswith("2e"), a)
            check(f"{tag}: destination and invalidation lines at their recorded prices", a["lines_ok"], a)
        axis = pg.evaluate("window.STP._state.lines.length")
        check(f"{tag}: one price-axis label only (current price)", axis == 1, axis)
        for m in ("plan", "structure", "full"):
            pg.evaluate("document.querySelector('.stp-chartcard').scrollIntoView()")
            pg.click(f".stp-modes button[data-mode='{m}']"); pg.wait_for_timeout(500)
            o = pg.evaluate(OVERLAP)
            check(f"{tag}: no overlapping labels in {m}", o["overlaps"] == 0 and o["labels"] > 0, o)
        n_full = pg.evaluate("document.querySelectorAll('.stp-layer svg line').length")
        pg.click(".stp-modes button[data-mode='plan']"); pg.wait_for_timeout(400)
        n_plan = pg.evaluate("document.querySelectorAll('.stp-layer svg line').length")
        check(f"{tag}: trade plan draws far fewer lines than full analysis", n_plan < n_full, {"plan": n_plan, "full": n_full})
        if not mobile:
            pg.click(".stp-modes button[data-mode='full']"); pg.wait_for_timeout(400)
            y = pg.evaluate("() => { const l = window.STP._state.hoverItems[0]; const r = document.querySelector('.stp-chartbox').getBoundingClientRect(); return [r.left + 200, r.top + l.y]; }")
            pg.mouse.move(*y); pg.wait_for_timeout(300)
            check("desktop: hover shows level details in full analysis", pg.evaluate("getComputedStyle(document.querySelector('.stp-hover')).display") == "block", pg.evaluate("document.querySelector('.stp-hover').textContent.slice(0,80)"))
            pg.click(".stp-levels summary"); pg.wait_for_timeout(200)
            check("desktop: expandable level list lists every recorded level", pg.evaluate("document.querySelectorAll('.stp-leveltable tr').length") > 50)
            pg.click(".stp-modes button[data-mode='plan']")
        for tf, want in (("4h", 14400), ("5m", 300), ("1h", 3600)):
            pg.click(f".stp-seg button[data-tf='{tf}']"); pg.wait_for_timeout(1500)
            gap = pg.evaluate("() => { const c = window.STP._state.candles; return c[c.length-1].time - c[c.length-2].time; }")
            check(f"{tag}: {tf} switch loads {tf} candles", gap >= want, gap)
        pg.evaluate("document.querySelectorAll('.stp-table tr.row')[3].click()"); pg.wait_for_timeout(2500)
        h = pg.evaluate("() => ({hist: !!document.querySelector('.stp-histbanner'), lab: [...document.querySelectorAll('.stp-lab')].map(e => e.textContent)})")
        check(f"{tag}: historical replay draws the original plan", h["hist"] and any(t.startswith("ORIGINAL ENTRY ZONE") for t in h["lab"]), h)
        check(f"{tag}: no horizontal overflow", pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth") <= 0)
        pg.click("#tab-ops"); pg.wait_for_timeout(800)
        check(f"{tag}: operations tab still renders with the compact card", pg.evaluate("!document.getElementById('view-ops').hidden && !!document.querySelector('.stpc')"))
        check(f"{tag}: no script errors", not errs, errs)
        ctx.close()
    b.close()
for r in res: print(json.dumps(r))
print("CHART CHECKS:", sum(r["ok"] for r in res), "passed,", sum(not r["ok"] for r in res), "failed")
sys.exit(0 if all(r["ok"] for r in res) else 1)
