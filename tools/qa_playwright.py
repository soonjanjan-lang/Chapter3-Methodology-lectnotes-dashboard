"""Automated QA for the dashboard (legibility, contrast, overflow, errors, calculators).

    python tools/qa_playwright.py            # full sweep, writes tools/_qa/qa_report.md, exits 1 on failure
    python tools/qa_playwright.py --shots    # also saves first-viewport screenshots of every tab

Legibility rules (instructor requirement):
  * no visible text below 17px anywhere (SVG text measured at its on-screen size);
  * body paragraphs at least 20px on desktop and 18px on phones;
  * body text contrast >= 7:1, all other text >= 4.5:1.
Mathematical sub/superscripts inside KaTeX are typeset by KaTeX and are reported separately.
"""
import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "_qa"

AUDIT_JS = r"""
(opts) => {
  const lum = (c) => { const v = c.map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
                       return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
  const parse = (s) => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null;
                         const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return { rgb: p.slice(0, 3), a: p.length > 3 ? p[3] : 1 }; };
  const bgOf = (el) => { for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c.a > 0.5) return c.rgb; } return parse(getComputedStyle(document.body).backgroundColor).rgb; };
  const ratio = (a, b) => { const la = lum(a), lb = lum(b); return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05); };
  const visible = (el) => { if (!el.getClientRects().length) return false; const cs = getComputedStyle(el);
                            if (cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
                            const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const roots = [document.querySelector('section.tab:not([hidden])'), document.querySelector('.running-head'), document.querySelector('.page-foot')];
  const rail = document.querySelector('#rail'); if (rail && getComputedStyle(rail).visibility !== 'hidden' && rail.getBoundingClientRect().right > 0) roots.push(rail);
  const small = [], lowContrast = [], katexSmall = [], bodySmall = [];
  const seen = new Set();
  for (const root of roots) {
    if (!root) continue;
    for (const el of root.querySelectorAll('*')) {
      if (seen.has(el)) continue; seen.add(el);
      // zero-width spaces (KaTeX layout struts) are not readable text
      const own = Array.from(el.childNodes).some(n => n.nodeType === 3 && /[^\s​]/.test(n.textContent));
      if (!own || !visible(el) || el.closest('.sr-only, [hidden], details:not([open]) > :not(summary)')) continue;
      const cs = getComputedStyle(el);
      let fs = parseFloat(cs.fontSize);
      if (el instanceof SVGElement) { const m = el.getScreenCTM(); if (m) fs = fs * Math.abs(m.a); }
      const label = (el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : '') + ': ' + el.textContent.trim().slice(0, 40));
      if (el.closest('.katex')) { if (fs < 16.5) katexSmall.push(fs.toFixed(1)); continue; }
      if (fs < opts.floor - 0.25) small.push(fs.toFixed(1) + 'px ' + label);
      if (el.tagName === 'P' && el.closest('.panel') && !el.closest('.small, .table-note, .calc-explain, .rl-why, .sim-log, .cp-margin, .ex-note, figcaption, .tab-facts, .box, .result, .quiz, .outcomes, .anno-notes, .checklist-count, .target-cell, .vr-detail, .mm-desc') && !el.classList.contains('small') && fs < opts.body - 0.25)
        bodySmall.push(fs.toFixed(1) + 'px ' + label);
      if (!(el instanceof SVGElement)) {
        const col = parse(cs.color); if (!col) continue;
        const r = ratio(col.rgb, bgOf(el));
        // WCAG large text (>= 24px, or >= 18.66px bold) needs 4.5:1 for AAA; body-sized running text needs 7:1
        const large = fs >= 24 || (fs >= 18.66 && parseInt(cs.fontWeight, 10) >= 700);
        const isBody = /^(P|LI|DD|TD)$/.test(el.tagName) && el.closest('.panel') && !el.closest('.small, .table-note, .rl-why, .calc-explain') && !large;
        const need = isBody ? 7 : 4.5;
        if (r < need - 0.01) lowContrast.push(r.toFixed(2) + ':1 (needs ' + need + ') ' + label);
      }
    }
  }
  const de = document.documentElement;
  return { small, lowContrast, bodySmall, katexMin: katexSmall.length ? Math.min(...katexSmall.map(Number)) : null,
           overflow: de.scrollWidth > window.innerWidth + 1 ? de.scrollWidth - window.innerWidth : 0,
           base: parseFloat(getComputedStyle(de).fontSize) };
}
"""

CALC_JS = r"""
() => {
  const S = window.Ch3.stats;
  const published = {10:10,15:14,20:19,25:24,30:28,35:32,40:36,45:40,50:44,55:48,60:52,65:56,70:59,75:63,80:66,85:70,90:73,95:76,100:80,110:86,120:92,130:97,140:103,150:108,160:113,170:118,180:123,190:127,200:132,210:136,220:140,230:144,240:148,250:152,260:155,270:159,280:162,290:165,300:169,320:175,340:181,360:186,380:191,400:196,420:201,440:205,460:210,480:214,500:217,550:226,600:234,650:242,700:248,750:254,800:260,850:265,900:269,950:274,1000:278,1100:285,1200:291,1300:297,1400:302,1500:306,1600:310,1700:313,1800:317,1900:320,2000:322,2200:327,2400:331,2600:335,2800:338,3000:341,3500:346,4000:351,4500:354,5000:357,6000:361,7000:364,8000:367,9000:368,10000:370,15000:375,20000:377,30000:379,40000:380,50000:381,75000:382,1000000:384};
  const kmMismatch = Object.entries(published).filter(([N, s]) => Math.round(S.km(+N, 0.05, 0.5, 0.95)) !== s).map(([N, s]) => N + ': table ' + s + ', calc ' + Math.round(S.km(+N, 0.05, 0.5, 0.95)));
  return {
    kmMismatch,
    power_d02_n185: +S.powerT(0.2, 185, 0.05).toFixed(4),
    power_d03_n185: +S.powerT(0.3, 185, 0.05).toFixed(4),
    power_d05_n185: +S.powerT(0.5, 185, 0.05).toFixed(4),
    n80_d02: S.searchN(m => S.powerT(0.2, m, 0.05), 0.8, 2, 16),
    regN_f015_u5: S.searchN(m => S.powerReg(0.15, 5, 0, m, 0.05), 0.8, 7, 16),
    regN_f002_u1_c7: S.searchN(m => S.powerReg(0.02, 1, 7, m, 0.05), 0.8, 10, 16),
    moe_N10000: [0.03, 0.05, 0.10].map(d => Math.ceil(S.km(10000, d, 0.5, 0.95)))
  };
}
"""

EXPECT = {"power_d02_n185": 0.4835, "power_d03_n185": 0.8206, "power_d05_n185": 0.9977, "n80_d02": 394,
          "regN_f015_u5": 92, "regN_f002_u1_c7": 395, "moe_N10000": [965, 370, 96]}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", action="store_true")
    ap.add_argument("--url", default=(ROOT / "index.html").as_uri())
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "review").mkdir(exist_ok=True)
    fails, notes = [], []
    katex_min = 99
    with sync_playwright() as p:
        b = p.chromium.launch()
        combos = [("desktop", 1440, 900, "light", 17, 20), ("desktop", 1440, 900, "dark", 17, 20),
                  ("phone", 390, 844, "light", 17, 18), ("phone", 390, 844, "dark", 17, 18)]
        for dev, w, h, theme, floor, body in combos:
            ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme=theme, reduced_motion="reduce")
            ctx.add_init_script("localStorage.setItem('ch3:penDrawn','true');")
            pg = ctx.new_page()
            errs = []
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(a.url)
            pg.wait_for_timeout(600)
            tabs = pg.eval_on_selector_all("section.tab", "els => els.map(e => e.dataset.tab)")
            for t in tabs:
                pg.evaluate(f"location.hash = '#{t}'")
                pg.wait_for_timeout(120)
                subs = pg.eval_on_selector_all(f"#tab-{t} .subtabs [role=tab]", "els => els.map(e => e.dataset.sub)") or [None]
                for s in subs:
                    if s:
                        pg.evaluate(f"location.hash = '#{t}/{s}'")
                        pg.wait_for_timeout(120)
                    r = pg.evaluate(AUDIT_JS, {"floor": floor, "body": body})
                    where = f"{dev}/{theme} #{t}{'/' + s if s else ''}"
                    for x in r["small"][:5]:
                        fails.append(f"[font<17] {where}: {x}")
                    for x in r["bodySmall"][:3]:
                        fails.append(f"[body<{body}] {where}: {x}")
                    for x in r["lowContrast"][:5]:
                        fails.append(f"[contrast] {where}: {x}")
                    if r["overflow"]:
                        fails.append(f"[overflow {r['overflow']}px] {where}")
                    if r["katexMin"] is not None:
                        katex_min = min(katex_min, r["katexMin"])
                    if a.shots and theme == "light" and s in (None, subs[0]):
                        pg.evaluate("window.scrollTo(0,0)")
                        pg.screenshot(path=str(OUT / "review" / f"{t}-{dev}.png"))
            for e in errs:
                fails.append(f"[console] {dev}/{theme}: {e}")
            if dev == "desktop" and theme == "light":
                calc = pg.evaluate(CALC_JS)
                if calc["kmMismatch"]:
                    fails.append(f"[calc] Krejcie–Morgan mismatches: {calc['kmMismatch']}")
                for k, v in EXPECT.items():
                    got = calc[k]
                    ok = (abs(got - v) < 0.0006) if isinstance(v, float) else got == v
                    if not ok:
                        fails.append(f"[calc] {k}: expected {v}, got {got}")
                notes.append("Calculator benchmarks: " + json.dumps({k: calc[k] for k in EXPECT}))
                # UI check: K&M calculator at N = 9000 shows 368; Sekaran allocation shows 2/6/10/20/100/4
                pg.evaluate("location.hash = '#d4/calculators'")
                pg.fill("#km-N", "9000")
                pg.dispatch_event("#km-N", "input")
                if pg.inner_text("#km-out-s").strip() != "368":
                    fails.append("[calc-ui] K&M N=9000 did not show 368")
                pg.evaluate("location.hash = '#d2/simulator'")
                props = pg.eval_on_selector_all(".alloc-table .prop", "els => els.map(e => e.textContent.trim())")
                if props != ["2", "6", "10", "20", "100", "4"]:
                    fails.append(f"[calc-ui] Sekaran allocation shows {props}")
            ctx.close()
        # projector mode: 26px, no overflow
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
        ctx.add_init_script("localStorage.setItem('ch3:projector','true');localStorage.setItem('ch3:penDrawn','true');")
        pg = ctx.new_page()
        pg.goto(a.url)
        for t in ["home", "b4", "c2", "d4/calculators", "e4"]:
            pg.evaluate(f"location.hash = '#{t}'")
            pg.wait_for_timeout(150)
            r = pg.evaluate(AUDIT_JS, {"floor": 17, "body": 26})
            if r["base"] < 26:
                fails.append(f"[projector] #{t}: base font {r['base']}px")
            if r["overflow"]:
                fails.append(f"[projector overflow {r['overflow']}px] #{t}")
            if a.shots:
                pg.screenshot(path=str(OUT / "review" / f"projector-{t.replace('/', '_')}.png"))
        ctx.close()
        b.close()
    notes.append(f"Smallest KaTeX glyph (maths sub/superscripts): {katex_min:.1f}px")
    lines = ["# QA report", "", *notes, "", f"**{len(fails)} problem(s)**", ""] + [f"- {f}" for f in fails[:400]]
    (OUT / "qa_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(notes))
    print(f"{len(fails)} problem(s)")
    for f in fails[:60]:
        print(" ", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
