# Chapter 3 Methodology dashboard

Interactive teaching dashboard for a PhD research-methods course (economics): everything needed to plan and write the Methodology chapter of a thesis. Static site deployed on GitHub Pages from `main` / root:
https://github.com/soonjanjan-lang/Chapter3-Methodology-lectnotes-dashboard → https://soonjanjan-lang.github.io/Chapter3-Methodology-lectnotes-dashboard/

## Prompt log — every turn

Append each new instructor prompt **verbatim** to `PROMPT_LOG.md` as a new numbered section, plus their answers to any clarifying questions (as a table). Do this before starting the work the prompt asks for.

## Build

- `python build.py` stitches `src/shell.html` + `src/sections/*.html` (sorted by filename) into `index.html`, runs the code tests, then builds `downloads/Chapter3-Methodology-offline.zip`. `index.html` is generated: edit `src/`, never `index.html`.
- `python build.py --fast` skips code tests and ZIP (for quick visual iteration).
- Run Python helper scripts **without** `python -I`: the tooling (python-docx, nbformat, nbclient, playwright) lives in user site-packages, which `-I` hides.

## Offline-first constraint

The ZIP must work by double-clicking `index.html` (`file://`). So: no `fetch()`, no ES modules, no CDN at runtime. All content is in-page; vendor libraries (KaTeX, highlight.js) and fonts are self-hosted in `assets/vendor/` and `assets/fonts/`; scripts are classic `<script defer>`.

## Design conventions

- Style is "Editorial journal": ivory paper, ink-navy text, oxblood accent; Fraunces (display), Source Sans 3 (body), JetBrains Mono (code). Colours and sizes come only from tokens in `assets/css/tokens.css`, which also define the dark theme.
- **Legibility floor (instructor requirement):** body text 20px desktop / 19px tablet / 18px phone; no text anywhere below 17px; body contrast ≥7:1. Wide tables and equations scroll inside their own box rather than shrinking. `tools/qa_playwright.py` enforces this — keep it passing.
- British spelling. Economics examples, Malaysian context where natural; label hypothetical data as hypothetical.
- Each content tab follows the frame in existing sections (kicker, title, outcomes, sub-tabs Notes / Worked example / Write-up template / Worksheet / Quiz, key takeaways, references). Copy an existing section's markup when adding one.

## Copyright rule

Third-party figures (textbook tables/diagrams, published PDFs) are recreated as original HTML/SVG with a citation, never published as the original image. Originals live in git-ignored `source-materials/`. The instructor's own files go in `downloads/originals/`.

## Reading list rule

Peer-reviewed journal articles only, each verified against Crossref by `tools/verify_refs.py`; "Free full text" links only when OpenAlex reports a legal OA copy that returns HTTP 200. Never add an entry by hand without running the verifier.

## Code downloads must run clean

Every `downloads/code/*.do` and `*.ipynb` must execute with zero errors — `tools/run_code_tests.py` runs them (Stata: `"C:\Program Files\StataNow19\StataMP-64.exe" /e do`, scanning logs for `r(###);`; notebooks: nbclient). Stata files use built-in commands only (no `ssc`), start with `version 16`, and set a seed. Notebooks use only pandas/numpy/scipy/statsmodels/linearmodels/matplotlib and are saved with outputs.
