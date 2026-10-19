"""Quick screenshots for visual review.

    python tools/shot.py home a1/worksheet --w 1440 --h 900 --theme dark --full
Writes tools/_qa/<route>-<w>-<theme>.png and prints console errors.
"""
import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "_qa"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("routes", nargs="+")
    ap.add_argument("--w", type=int, default=1440)
    ap.add_argument("--h", type=int, default=900)
    ap.add_argument("--theme", default="light")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--projector", action="store_true")
    ap.add_argument("--click", default=None, help="CSS selector to click before capture")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    url = (ROOT / "index.html").as_uri()
    errors = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": a.w, "height": a.h}, color_scheme=a.theme, reduced_motion="reduce")
        init = "localStorage.setItem('ch3:penDrawn','true');"
        if a.projector:
            init += "localStorage.setItem('ch3:projector','true');"
        ctx.add_init_script(init)
        pg = ctx.new_page()
        pg.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        for r in a.routes:
            pg.goto(url + "#" + r)
            pg.wait_for_timeout(500)
            if a.click:
                pg.click(a.click)
                pg.wait_for_timeout(300)
            name = r.replace("/", "_") + f"-{a.w}-{a.theme}{'-proj' if a.projector else ''}.png"
            pg.screenshot(path=str(OUT / name), full_page=a.full)
            print(OUT / name)
        b.close()
    for e in errors:
        print(e)
    return 1 if any(e.startswith("pageerror") for e in errors) else 0


if __name__ == "__main__":
    sys.exit(main())
