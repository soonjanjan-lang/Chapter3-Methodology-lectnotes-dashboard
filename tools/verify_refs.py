"""Verify reading-list candidates against Crossref, and find legal open-access full text via OpenAlex.

Every citation shown on the dashboard is rendered from the Crossref record this script saves,
never from hand-typed metadata. A "Free full text" link is kept only when OpenAlex reports an
open-access location AND the URL answers HTTP 200 right now.

Usage:  python tools/verify_refs.py            (writes tools/reading_list_verified.json)
"""
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATES = HERE / "reading_list_candidates.json"
OUT = HERE / "reading_list_verified.json"
UA = "Chapter3-Methodology-dashboard reference checker/1.0 (teaching resource; https://github.com/soonjanjan-lang/Chapter3-Methodology-lectnotes-dashboard)"
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

# Publisher pages known to host the article free of charge but not flagged OA in OpenAlex
# (the Journal of Economic Perspectives is free to read). They are still checked live.
EXTRA_OA = {
    "angrist2010": ["https://www.aeaweb.org/articles?id=10.1257/jep.24.2.3"],
    "meyer2015": ["https://www.aeaweb.org/articles?id=10.1257/jep.29.4.199"],
}


def url_ok_page(url):
    """Third opinion: a full page load in headless Chromium (passes publishers' JavaScript checks)."""
    try:
        if "page" not in _browser:
            url_ok_browser("about:blank")
            _browser["page"] = _browser["ctx"].new_page()
        r = _browser["page"].goto(url, wait_until="domcontentloaded", timeout=60000)
        title = _browser["page"].title().lower()
        if r and r.status == 200 and "just a moment" not in title and "denied" not in title:
            return True, "html"
        return False, str(r.status if r else "no response")
    except Exception as e:
        return False, type(e).__name__


def clean(s):
    """Crossref strings can carry HTML entities, footnote markers and inline tags (<i>, <sup>)."""
    s = re.sub(r"<sup>.*?</sup>", "", s or "", flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", html.unescape(s)).strip()
    if s.isupper():                      # e.g. "SURVEY RESEARCH" → "Survey research"
        s = s.capitalize()
    return s


_browser = {}


def url_ok_browser(url):
    """Second opinion through a real Chromium request context, for publishers that refuse urllib."""
    try:
        if "ctx" not in _browser:
            from playwright.sync_api import sync_playwright
            _browser["pw"] = sync_playwright().start()
            _browser["b"] = _browser["pw"].chromium.launch()
            _browser["ctx"] = _browser["b"].new_context(user_agent=BROWSER_UA)
        r = _browser["ctx"].request.get(url, timeout=45000, max_redirects=10)
        ctype = r.headers.get("content-type", "")
        if r.status != 200:
            return False, str(r.status)
        body = r.body()[:4096]
        if "pdf" in ctype or body.startswith(b"%PDF"):
            return True, "pdf"
        if "html" in ctype:
            low = body.lower()
            if b"just a moment" in low or b"captcha" in low or b"access denied" in low:
                return False, "bot-wall"
            return True, "html"
        return False, ctype
    except Exception as e:
        return False, type(e).__name__


def get_json(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def words(s):
    return [w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if len(w) > 2]


def year_of(item):
    for k in ("published-print", "issued", "published-online", "published"):
        dp = (item.get(k) or {}).get("date-parts")
        if dp and dp[0] and dp[0][0]:
            return int(dp[0][0])
    return None


def title_overlap(title, query):
    tw = words(title)
    qw = set(words(query))
    if not tw:
        return 0.0
    return sum(1 for w in tw if w in qw) / len(tw)


def crossref_by_doi(doi):
    d = get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))
    return d["message"] if d else None


def crossref_search(q):
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(
        {"query.bibliographic": q, "rows": 8, "filter": "type:journal-article"})
    d = get_json(url)
    return d["message"]["items"] if d else []


def url_ok(url):
    """True if the URL answers 200 with a document (PDF or HTML)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA, "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8"})
        with urllib.request.urlopen(req, timeout=40) as r:
            ctype = r.headers.get("Content-Type", "")
            head = r.read(2048)
            if r.status != 200:
                return False, ctype
            if "pdf" in ctype or head.startswith(b"%PDF"):
                return True, "pdf"
            if "html" in ctype:
                return True, "html"
            return False, ctype
    except Exception as e:
        return False, type(e).__name__


def openalex_fulltext(doi, key=None):
    d = get_json("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi))
    if not d:
        return None
    oa = d.get("open_access") or {}
    cands = [(u, "pdf_url", "publisher (free to read)") for u in EXTRA_OA.get(key, [])]
    best = d.get("best_oa_location") or {}
    for loc in [best] + (d.get("locations") or []):
        if not loc or not loc.get("is_oa"):
            continue
        src = (loc.get("source") or {}).get("display_name") or ""
        for key in ("pdf_url", "landing_page_url"):
            u = loc.get(key)
            if u and not u.startswith("https://doi.org/") and u not in [c[0] for c in cands]:
                cands.append((u, key, src))
    # doi.org landing is only useful when the publisher itself is OA (gold/hybrid/bronze)
    if oa.get("is_oa") and oa.get("oa_status") in ("gold", "hybrid", "bronze", "diamond"):
        cands.append(("https://doi.org/" + doi, "landing_page_url", "publisher"))
    for u, kind_key, src in cands:
        ok, kind = url_ok(u)
        if not ok:
            ok, kind = url_ok_browser(u)
        if not ok and src.startswith("publisher (free"):
            ok, kind = url_ok_page(u)
        if ok:
            return {"url": u, "kind": "PDF" if kind == "pdf" else "Free full text",
                    "oa_status": oa.get("oa_status") or "free-to-read", "host": src or urllib.parse.urlparse(u).netloc}
    return {"url": None, "oa_status": oa.get("oa_status"), "tried": [c[0] for c in cands]}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cands = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    out = []
    for c in cands:
        rec = {"key": c["key"], "topic": c["topic"], "why": c["why"]}
        item = None
        if c.get("doi"):
            item = crossref_by_doi(c["doi"])
            if item and abs((year_of(item) or 0) - c["year"]) > 1:
                rec["warning"] = f"year mismatch: crossref {year_of(item)} vs expected {c['year']}"
        else:
            best, best_score = None, 0.0
            for it in crossref_search(c["q"]):
                t = (it.get("title") or [""])[0]
                y = year_of(it)
                score = title_overlap(t, c["q"])
                fam = ((it.get("author") or [{}])[0].get("family") or "").lower()
                if fam and fam.split()[-1] not in c["q"].lower():
                    score -= 0.5
                if y is None or abs(y - c["year"]) > 1:
                    score -= 0.5
                if score > best_score:
                    best, best_score = it, score
            if best is not None and best_score >= 0.8:
                item = best
            rec["match_score"] = round(best_score, 2)
        if not item:
            rec["status"] = "not_verified"
            out.append(rec)
            print(f"[FAIL] {c['key']}", flush=True)
            continue
        doi = item["DOI"].lower()
        rec.update({
            "status": "verified",
            "doi": doi,
            "type": item.get("type"),
            "title": clean((item.get("title") or [""])[0]),
            "journal": clean((item.get("container-title") or [""])[0]),
            "year": year_of(item),
            "volume": item.get("volume"),
            "issue": item.get("issue"),
            "pages": item.get("page") or item.get("article-number"),
            "authors": [{"family": a.get("family") or a.get("name", ""), "given": a.get("given", "")}
                        for a in (item.get("author") or [])],
        })
        rec["fulltext"] = openalex_fulltext(doi, c["key"])
        ft = rec["fulltext"] or {}
        print(f"[OK]   {c['key']:<18} {rec['year']} {rec['journal'][:45]:<45} | {rec['title'][:60]} | OA: {ft.get('kind') or '-'}", flush=True)
        out.append(rec)
        time.sleep(0.3)
    OUT.write_text(json.dumps({"checked": time.strftime("%Y-%m-%d"), "entries": out}, indent=2, ensure_ascii=False), encoding="utf-8")
    bad = [r["key"] for r in out if r["status"] != "verified"]
    print(f"\n{len(out) - len(bad)} verified, {len(bad)} not verified: {bad}")


if __name__ == "__main__":
    sys.exit(main())
