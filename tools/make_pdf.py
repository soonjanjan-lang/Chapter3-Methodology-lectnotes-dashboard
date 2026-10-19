"""Print the whole dashboard (every section, panel and model answer) to one PDF.

    python tools/make_pdf.py      → downloads/Chapter3-Methodology-Notes.pdf
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "downloads" / "Chapter3-Methodology-Notes.pdf"

FOOTER = ('<div style="width:100%;font-family:Calibri,Arial,sans-serif;font-size:9pt;color:#555;'
          'padding:0 17mm;display:flex;justify-content:space-between;">'
          '<span>PhD Research Methods · Chapter 3: Methodology</span>'
          '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 900})
        pg.emulate_media(media="print", color_scheme="light")
        pg.goto((ROOT / "index.html").as_uri() + "?print=all#home")
        pg.wait_for_timeout(1500)
        pg.pdf(path=str(OUT), format="A4", print_background=True, prefer_css_page_size=True,
               display_header_footer=True, header_template="<div></div>", footer_template=FOOTER)
        b.close()
    print(f"{OUT.name}: {OUT.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
