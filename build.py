"""Build the Chapter 3 dashboard.

    python build.py          full build: index.html, code tests, PDF notes, offline ZIP
    python build.py --fast   index.html only (for quick visual iteration)

Sections live in src/sections/*.html (sorted by filename) and start with a meta block:

    <!--meta
    id: d4
    group: D
    code: D4
    title: How many respondents?
    -->

Authoring shortcuts expanded here (so section files stay readable):
    <div class="panel" data-panel="notes" data-label="Notes">  → sub-tab bar + ARIA wiring
    <x-listing> <x-stata file="a.do">…</x-stata> <x-python file="a.ipynb">…</x-python> </x-listing>
    <x-answer>…</x-answer>              → "Show model answer" disclosure
    <x-draft key="d4-q1"></x-draft>     → answer box saved in the reader's browser
    <table class="bt">                  → wrapped in a scrollable region
    <!--@READING_LIST--> <!--@DOWNLOADS--> <!--@GLOSSARY_INDEX-->
"""
import datetime as dt
import html
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
SECTIONS = SRC / "sections"
OUT = ROOT / "index.html"
DL = ROOT / "downloads"
ZIP_NAME = "Chapter3-Methodology-offline.zip"

GROUPS = {
    "S": "Start",
    "A": "Foundations",
    "B": "Writing Chapter 3",
    "C": "Data",
    "D": "Sampling",
    "E": "The instrument",
    "F": "Practice and resources",
}

TICK = '<svg class="toc-tick" aria-hidden="true"><use href="#i-check"/></svg>'


def parse_meta(text, name):
    m = re.match(r"\s*<!--meta\s*(.*?)-->", text, re.S)
    if not m:
        sys.exit(f"{name}: missing <!--meta ... --> block")
    meta = {}
    for line in m.group(1).strip().splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    for k in ("id", "group", "title"):
        if k not in meta:
            sys.exit(f"{name}: meta needs '{k}'")
    meta.setdefault("code", "")
    meta.setdefault("short", meta["title"])
    return meta, text[m.end():]


# ---------------------------------------------------------------------------
# macros
# ---------------------------------------------------------------------------
def dedent_code(code):
    lines = code.strip("\n").splitlines()
    pad = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    return "\n".join(l[pad:] for l in lines)


def expand_listing(m):
    body = m.group(1)
    title = re.search(r'title="([^"]*)"', m.group(0)[:200])
    pres = []
    langs = []
    for lang, attrs, code in re.findall(r"<x-(stata|python|text)([^>]*)>(.*?)</x-\1>", body, re.S):
        f = re.search(r'file="([^"]*)"', attrs)
        fattr = f' data-file="{html.escape(f.group(1))}"' if f else ""
        cls = "language-stata" if lang == "stata" else ("language-python" if lang == "python" else "language-plaintext")
        pres.append(f'<pre data-lang="{lang}"{fattr}><code class="{cls}">{html.escape(dedent_code(code))}</code></pre>')
        langs.append(lang)
    switch = ""
    if len(langs) > 1:
        names = {"stata": "Stata", "python": "Python", "text": "Output"}
        switch = '<span class="lang-switch" role="group" aria-label="Language">' + "".join(
            f'<button type="button" data-lang="{l}" aria-pressed="{"true" if i == 0 else "false"}">{names[l]}</button>'
            for i, l in enumerate(langs)) + "</span>"
    t = html.escape(title.group(1)) if title else ""
    bar = (f'<div class="listing-bar"><span class="listing-title">{t}</span>{switch}'
           '<button type="button" class="copy-btn"><svg aria-hidden="true"><use href="#i-copy"/></svg><span class="copy-label">Copy</span></button></div>')
    return f'<div class="listing" data-langs>{bar}{"".join(pres)}</div>'


def expand_answer(m):
    label = m.group(1) or "model answer"
    return ('<details class="answer"><summary><span class="when-closed">Show ' + label + '</span>'
            '<span class="when-open">Hide ' + label + '</span></summary><div class="answer-body">'
            + m.group(2) + "</div></details>")


def expand_draft(m):
    key = m.group(1)
    return (f'<label class="draft-label" for="draft-{key}">Your answer (saved in this browser only)</label>'
            f'<textarea class="draft" id="draft-{key}" data-key="{key}" rows="4"></textarea>')


def wire_panels(tab_id, body):
    panels = list(re.finditer(r'<div class="panel" data-panel="([^"]+)" data-label="([^"]+)">', body))
    if not panels:
        return body
    buttons = []
    for i, p in enumerate(panels):
        name, label = p.group(1), p.group(2)
        buttons.append(
            f'<button type="button" role="tab" id="t-{tab_id}-{name}" data-sub="{name}" '
            f'aria-controls="p-{tab_id}-{name}" aria-selected="{"true" if i == 0 else "false"}" '
            f'tabindex="{0 if i == 0 else -1}">{label}</button>')
    bar = f'<div class="subtabs" role="tablist" aria-label="Parts of this section">{"".join(buttons).replace("<button", "<button class=\"subtab\"")}</div>\n'
    out, last = [], 0
    for i, p in enumerate(panels):
        name = p.group(1)
        out.append(body[last:p.start()])
        if i == 0:
            out.append(bar)
        hidden = "" if i == 0 else " hidden"
        out.append(f'<div class="panel" data-panel="{name}" id="p-{tab_id}-{name}" role="tabpanel" '
                   f'aria-labelledby="t-{tab_id}-{name}" tabindex="0"{hidden}>')
        last = p.end()
    out.append(body[last:])
    return "".join(out)


def wrap_tables(body):
    def w(m):
        cap = re.search(r"<caption>(.*?)</caption>", m.group(0), re.S)
        label = html.escape(re.sub(r"<[^>]+>", "", cap.group(1)).strip()) if cap else "Table"
        return f'<div class="table-wrap" role="region" aria-label="{label}" tabindex="0">{m.group(0)}</div>'
    return re.sub(r'(?<!tabindex="0">)<table class="bt[^"]*".*?</table>', w, body, flags=re.S)


def expand(tab_id, body):
    body = re.sub(r"<x-listing[^>]*>(.*?)</x-listing>", expand_listing, body, flags=re.S)
    body = re.sub(r'<x-answer(?: label="([^"]*)")?>(.*?)</x-answer>', expand_answer, body, flags=re.S)
    body = re.sub(r'<x-draft key="([^"]+)"></x-draft>', expand_draft, body)
    body = wire_panels(tab_id, body)
    body = wrap_tables(body)
    return body


# ---------------------------------------------------------------------------
# generated content
# ---------------------------------------------------------------------------
TOPICS = [
    ("methodology", "Methodology, paradigms and research design"),
    ("design", "Identification and model specification in economics"),
    ("measurement", "Levels of measurement"),
    ("scales", "Likert and rating scales"),
    ("sampling", "Sampling and sample size"),
    ("questionnaire", "Questionnaire design and surveys"),
    ("validity", "Validity and reliability"),
    ("qualitative", "Interviews and focus groups"),
    ("secondary", "Secondary data and data quality"),
    ("cleaning", "Data cleaning, reproducibility and reporting"),
]
TITLE_FIX = {"SURVEY RESEARCH": "Survey research"}


def apa_authors(authors):
    def one(a):
        given = a.get("given") or ""
        initials = " ".join(p[0] + "." for p in re.split(r"[\s]+", given.replace(".", " ").replace("-", " -")) if p and p[0].isalpha())
        initials = initials.replace(" -", "-")
        return f"{a['family']}, {initials}".strip().rstrip(",")
    names = [one(a) for a in authors]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) <= 20:
        return ", ".join(names[:-1]) + ", &amp; " + names[-1]
    return ", ".join(names[:19]) + ", … " + names[-1]


def render_reading_list():
    p = ROOT / "tools" / "reading_list_verified.json"
    if not p.exists():
        return "<p>Reading list not yet verified. Run <code>python tools/verify_refs.py</code>.</p>"
    data = json.loads(p.read_text(encoding="utf-8"))
    entries = [e for e in data["entries"] if e.get("status") == "verified" and e.get("type") == "journal-article"]
    n_oa = sum(1 for e in entries if (e.get("fulltext") or {}).get("url"))
    out = [f'<p class="small">{len(entries)} articles, each checked against the Crossref record on {data["checked"]}. '
           f'{n_oa} have a free full-text copy that loaded when checked; the rest are reachable through your library via the DOI.</p>']
    out.append('<div class="rl-filter" role="group" aria-label="Filter by topic"><button type="button" data-topic="all" aria-pressed="true">All topics</button>'
               + "".join(f'<button type="button" data-topic="{k}" aria-pressed="false">{html.escape(v)}</button>' for k, v in TOPICS)
               + '<button type="button" data-topic="oa" aria-pressed="false">Free full text only</button></div>')
    for key, label in TOPICS:
        items = sorted([e for e in entries if e["topic"] == key], key=lambda e: (e["authors"][0]["family"] if e["authors"] else "", e["year"] or 0))
        if not items:
            continue
        out.append(f'<section class="rl-topic" data-topic="{key}"><h2 class="rl-h">{html.escape(label)}</h2><ul class="rl-list">')
        for e in items:
            title = TITLE_FIX.get(e["title"], e["title"])
            vol = f", <i>{html.escape(e['volume'])}</i>" if e.get("volume") else ""
            iss = f"({html.escape(e['issue'])})" if e.get("issue") else ""
            pages = f", {html.escape(str(e['pages']))}" if e.get("pages") else ""
            cite = (f"{apa_authors(e['authors'])} ({e['year']}). {html.escape(title)}. "
                    f"<i>{html.escape(e['journal'])}</i>{vol}{iss}{pages}.")
            ft = e.get("fulltext") or {}
            links = [f'<li><a href="https://doi.org/{html.escape(e["doi"])}" rel="noopener" target="_blank">doi:{html.escape(e["doi"])}</a></li>']
            if ft.get("url"):
                links.append(f'<li><a class="badge-oa" href="{html.escape(ft["url"])}" rel="noopener" target="_blank">'
                             f'<svg aria-hidden="true"><use href="#i-open"/></svg>Free full text ({"PDF" if ft.get("kind") == "PDF" else "web"})</a></li>')
            oa = ' data-oa="1"' if ft.get("url") else ""
            out.append(f'<li class="rl-item"{oa}><p class="rl-cite">{cite}</p><p class="rl-why">{html.escape(e["why"])}</p>'
                       f'<ul class="rl-links">{"".join(links)}</ul></li>')
        out.append("</ul></section>")
    return "\n".join(out)


def human_size(n):
    for unit in ("bytes", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.0f} {unit}" if unit == "bytes" else f"{n:.1f} {unit}"
        n /= 1024


DOWNLOAD_GROUPS = [
    ("code", "Stata do-files and Jupyter notebooks", "Run as they are: every file is tested on each build."),
    ("data", "Practice datasets", "Hypothetical data used in the worked examples (CSV and Stata .dta)."),
    ("worksheets", "Worksheets", "Word versions of every worksheet, with and without model answers."),
    ("templates", "Templates", "Starting points for your own Chapter 3 tables."),
    ("originals", "Original lecture materials", "The instructor's own notes and examples."),
]


def render_downloads():
    zp = DL / ZIP_NAME
    zsize = human_size(zp.stat().st_size) if zp.exists() else "built on release"
    out = [f'''<div class="dl-hero">
<svg class="dl-icon" aria-hidden="true"><use href="#i-archive"/></svg>
<div><h2>Everything in one file</h2>
<p>The whole dashboard plus every file below, for offline use. Unzip it and double-click <code>index.html</code>; no internet connection needed.</p>
<a class="btn" href="downloads/{ZIP_NAME}" download><svg aria-hidden="true"><use href="#i-download"/></svg>Download the offline ZIP ({zsize})</a></div>
</div>''']
    for folder, label, note in DOWNLOAD_GROUPS:
        files = sorted(p for p in (DL / folder).glob("*") if p.is_file() and not p.name.startswith(("~", ".")) and p.suffix != ".log")
        if not files:
            continue
        rows = "".join(
            f'<tr><td><a href="downloads/{folder}/{html.escape(f.name)}" download>{html.escape(f.name)}</a></td>'
            f'<td class="num">{human_size(f.stat().st_size)}</td></tr>' for f in files)
        out.append(f'<h3>{html.escape(label)}</h3><p>{html.escape(note)}</p>'
                   f'<table class="bt narrow"><caption><b>{html.escape(label)}</b></caption><thead><tr><th>File</th><th class="num">Size</th></tr></thead><tbody>{rows}</tbody></table>')
    pdf = DL / "Chapter3-Methodology-Notes.pdf"
    if pdf.exists():
        out.insert(1, f'<p><a class="btn secondary" href="downloads/{pdf.name}" download><svg aria-hidden="true"><use href="#i-download"/></svg>Lecture notes as one PDF ({human_size(pdf.stat().st_size)})</a></p>')
    return "\n".join(out)


# ---------------------------------------------------------------------------
def build_html():
    shell = (SRC / "shell.html").read_text(encoding="utf-8")
    files = sorted(SECTIONS.glob("*.html"))
    metas, bodies = [], []
    for f in files:
        meta, body = parse_meta(f.read_text(encoding="utf-8"), f.name)
        body = body.replace("<!--@READING_LIST-->", render_reading_list()) if "<!--@READING_LIST-->" in body else body
        body = body.replace("<!--@DOWNLOADS-->", render_downloads()) if "<!--@DOWNLOADS-->" in body else body
        metas.append(meta)
        bodies.append(expand(meta["id"], body))

    nav, current = [], None
    for m in metas:
        if m["group"] != current:
            if current is not None:
                nav.append("</ol>")
            current = m["group"]
            letter = "" if current == "S" else f'<span class="grp-letter">{current}</span>'
            nav.append(f'<h2 class="rail-group">{letter}{html.escape(GROUPS[current])}</h2><ol>')
        code = m["code"] or "§"
        nav.append(f'<li><a class="toc-link" href="#{m["id"]}" data-tab="{m["id"]}"><span class="toc-code">{html.escape(code)}</span>'
                   f'<span class="toc-text">{html.escape(m["short"])}</span>{TICK}</a></li>')
    nav.append("</ol>")

    sections = []
    for m, b in zip(metas, bodies):
        sections.append(f'<section class="tab" id="tab-{m["id"]}" data-tab="{m["id"]}" data-code="{html.escape(m["code"])}" '
                        f'data-title="{html.escape(m["title"])}" data-short="{html.escape(m["short"])}" '
                        f'aria-labelledby="h-{m["id"]}">\n{b.strip()}\n</section>')
    page = (shell.replace("<!--@NAV-->", "\n".join(nav))
                 .replace("<!--@SECTIONS-->", "\n".join(sections))
                 .replace("<!--@BUILD_DATE-->", dt.date.today().strftime("%d %B %Y").lstrip("0")))
    # every section after the first starts hidden; the router reveals the requested one
    first = True
    def hide(m):
        nonlocal first
        if first:
            first = False
            return m.group(0)
        return m.group(0).replace(">", " hidden>", 1)
    page = re.sub(r'<section class="tab"[^>]*>', hide, page)
    OUT.write_text(page, encoding="utf-8")
    print(f"index.html: {len(metas)} sections, {OUT.stat().st_size/1024:.0f} KB")
    return metas


def build_zip():
    zp = DL / ZIP_NAME
    if zp.exists():
        zp.unlink()
    include = [OUT, ROOT / "README.md"] + [p for p in (ROOT / "assets").rglob("*") if p.is_file()]
    include += [p for p in DL.rglob("*") if p.is_file() and p.name != ZIP_NAME and p.suffix != ".log"
                and ".ipynb_checkpoints" not in p.parts]
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in include:
            if p.exists():
                z.write(p, Path("Chapter3-Methodology") / p.relative_to(ROOT))
        report = ROOT / "tools" / "code_test_report.md"
        if report.exists():
            z.write(report, Path("Chapter3-Methodology") / "code_test_report.md")
    print(f"{ZIP_NAME}: {zp.stat().st_size/1024/1024:.1f} MB")


def run(cmd):
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"FAILED: {' '.join(cmd)}")


def main():
    fast = "--fast" in sys.argv
    build_html()
    if fast:
        return
    run([sys.executable, "tools/make_datasets.py"])      # deterministic: fixed seeds
    run([sys.executable, "tools/make_notebooks.py"])
    run([sys.executable, "tools/run_code_tests.py"])     # every .do and .ipynb must pass
    run([sys.executable, "tools/make_worksheets.py"])
    build_html()
    run([sys.executable, "tools/make_pdf.py"])
    build_html()          # downloads list now knows the PDF size
    build_zip()
    build_html()          # downloads list now knows the ZIP size
    build_zip()           # ZIP carries the final index.html


if __name__ == "__main__":
    main()
