# Chapter 3: Methodology — an interactive teaching dashboard

**Live site:** https://soonjanjan-lang.github.io/Chapter3-Methodology-lectnotes-dashboard/

Teaching notes, economics worked examples, worksheets with model answers, calculators and runnable code for a PhD research-methods course: everything needed to plan and write the Methodology chapter (Chapter 3) of an economics thesis.

## What is inside

| Part | Sections |
|---|---|
| Start | How to write the Methodology chapter; the chapter's structure |
| A Foundations | Methodology vs research design vs methods; correlation, causation and identification |
| B Writing Chapter 3 | 3.1 Data · 3.2 RQ–method table · 3.3 Variables and codebook · 3.4 Model specification · 3.5 Ethics, limitations and the submission checklist |
| C Data | Levels of measurement · Data structures and model notation · Primary data · Secondary data sources · Data cleaning |
| D Sampling | Concepts · Probability sampling (with simulator and allocation calculator) · Non-probability sampling · How many respondents? (Krejcie–Morgan, precision and power calculators) |
| E The instrument | Questionnaire design · Adopting and adapting instruments · Likert and rating scales · Validity and reliability (interactive tree, CVI and alpha calculators) |
| F Practice and resources | All worksheets and an integrated tutorial · Glossary · Verified reading list · Downloads |

## Use offline

Download `downloads/Chapter3-Methodology-offline.zip` from the site's Downloads tab, unzip it, and double-click `index.html`. Everything — fonts, maths rendering, code highlighting, calculators — works without an internet connection.

## Code and data

`downloads/code/` holds six Stata do-files and six Jupyter notebooks (sampling, sample size, data cleaning, validity and reliability, data structures, model specification). `downloads/data/` holds the practice datasets, all hypothetical except the four small data-structure tables reproduced from the lecture notes. Every do-file (StataNow 19, built-in commands only, Stata 16+) and every notebook is executed on each build and must finish without errors; see `tools/code_test_report.md`.

## Building

```
python build.py          # index.html + code tests + PDF notes + offline ZIP
python build.py --fast   # index.html only
python tools/qa_playwright.py   # legibility, contrast, overflow, calculator checks
python tools/verify_refs.py     # re-verify the reading list against Crossref and OpenAlex
```

Sections are edited in `src/sections/`; `index.html` is generated. See `CLAUDE.md` for conventions.

## Sources and licences

- Teaching content © the course instructor. Reproduced material is cited in place; textbook figures are redrawn, not copied.
- Reading-list citations are generated from Crossref records; free full-text links point only to legal open-access copies.
- Fonts: Source Sans 3, Source Serif 4 and JetBrains Mono (SIL Open Font License). Maths: KaTeX (MIT). Code highlighting: highlight.js (BSD-3-Clause).
