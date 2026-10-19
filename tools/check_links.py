"""Check every external link in index.html (HTTP 200 or a redirect to one; headless browser as a fallback).

    python tools/check_links.py
"""
import html as htmlmod
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def fetch(u):
    if u.startswith("https://doi.org/"):
        # a registered DOI answers with a redirect to the publisher; publishers often block robots
        try:
            urllib.request.build_opener(NoRedirect).open(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=40)
            return u, 200
        except urllib.error.HTTPError as e:
            return u, 200 if e.code in (301, 302, 303, 307, 308) else e.code
        except Exception as e:
            return u, type(e).__name__
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=40)
        return u, r.status
    except urllib.error.HTTPError as e:
        return u, e.code
    except Exception as e:
        return u, type(e).__name__


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    urls = sorted(set(htmlmod.unescape(u) for u in re.findall(r'href="(https?://[^"#]+)"', html)))
    with ThreadPoolExecutor(8) as ex:
        res = dict(ex.map(fetch, urls))
    retry = [u for u, s in res.items() if s != 200]
    if retry:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            for u in retry:
                pg = b.new_page(user_agent=UA)
                try:
                    r = pg.goto(u, wait_until="domcontentloaded", timeout=45000)
                    pg.wait_for_timeout(1200)
                    title = pg.title().lower()
                    ok = r is not None and r.status == 200 and "just a moment" not in title
                    res[u] = 200 if ok else (f"{r.status if r else '?'} {pg.title()[:40]}")
                except Exception as e:
                    msg = str(e)
                    res[u] = 200 if "Download is starting" in msg else type(e).__name__
                pg.close()
            b.close()
    bad = {u: s for u, s in res.items() if s != 200}
    print(f"{len(urls)} external links; {len(urls) - len(bad)} OK; {len(bad)} not confirmed")
    for u, s in bad.items():
        print(f"  {s}  {u}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
