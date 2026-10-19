# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static HTML + CSS + vanilla JS (user: "Use CSS for visual presentation, layout, and styling"). Deployed on GitHub Pages from `main` / root of `soonjanjan-lang/Chapter3-Methodology-lectnotes-dashboard`. Must also run offline from a ZIP via `file://` (no fetch, no ES modules, self-hosted vendor files). A stdlib Python `build.py` assembles `src/` into `index.html`.

## Users

- **Primary: PhD students in economics** taking a research-methods course, planning and writing Chapter 3 (Methodology) of their thesis. Many work with primary questionnaire data in Malaysia; others use secondary datasets (DOSM, World Bank, IMF, FRED, WVS, PISA). They study at their own pace and return to the material while drafting.
- **Secondary: the course instructor** (economics professor), who teaches live from the dashboard in lectures and tutorials, often projected on a screen.

## Product Purpose

One structured, interactive place that teaches how to approach and write up the Methodology chapter: the four write-up subsections (data description, RQ–method table, variable operationalisation/codebook, model specification) and the underpinning knowledge (methodology vs research design vs methods, measurement levels, data structures, sampling designs, sample size, questionnaire design, adopt/adapt, Likert vs rating scales, validity and reliability, primary/secondary data collection, data cleaning). Success = students can produce a defensible Chapter 3 and justify every methodological choice; the instructor can teach the whole topic from it.

## Positioning

Built from the instructor's own lecture notes and examples (e.g. Soon 2018 flood-evacuation operationalisation table, the instructor's RQ–method tables and handwritten model-notation notes), in an economics register: econometric model write-ups, Stata and Python code that actually runs, and Malaysian applied examples — rather than a generic social-science methods primer.

## Operating Context

- Live lectures (projector, large room) and self-study on laptops and phones.
- Students download and keep everything (one offline ZIP).
- Instructor writes in Stata; students also receive Jupyter notebooks.
- Material is updated each semester via Claude Code; prompts are logged in `PROMPT_LOG.md`.

## Capabilities and Constraints

- Clickable tabs; worked examples; worksheets with model answers revealed on click (public site — answers are not secret); quizzes; templates; calculators (sample size, power, stratified allocation, Cronbach's alpha, CVI).
- Every `.do` and `.ipynb` must execute without errors (StataNow 19 MP available locally for testing).
- Reading list: peer-reviewed journals only, every entry verified; full-text links only to legal open-access copies.
- Copyright: third-party textbook figures and published PDFs are recreated as original HTML/SVG with citations, not re-hosted.
- Header/footer credit: generic title only — "PhD Research Methods · Chapter 3: Methodology". No personal name or institution on the site.

## Brand Commitments

- Visual direction chosen by the user: **Editorial journal** — warm ivory paper, ink-navy text, oxblood accent, serif display headings with a highly legible sans body.
- British spelling.

## Evidence on Hand

- `downloads/originals/`: `SJJ_Chpt3_lectnotes.docx`, `RQ_method_table_eg.docx`, `soon2018_VarOp_table.png`, `questionnaire_adopt_adapt.png`, `datastructure_emtmodel.png` (handwritten notation; panel block blank).
- `source-materials/` (local only): `materials_KM_VR_likert.docx` (instructor-supplied notes on Krejcie & Morgan, Likert vs rating scales, validity & reliability), Sekaran Table 13.1 and Fig 12.1, Krejcie & Morgan (1970) PDF, target-diagram image.
- No testimonials, student data, or institutional branding exist; none may be invented. Example datasets are hypothetical and must be labelled so.

## Product Principles

1. Justify, don't just describe — every method choice is tied to the research question and defended with a citation.
2. Show the write-up — each concept ends in how it appears in the chapter (template + model paragraph).
3. Practise with feedback — worksheets and quizzes with model answers on every major topic.
4. Nothing unverified — references, URLs, numbers and code are checked, not assumed.
5. Teachable live — works projected in a lecture hall as well as on a phone.

## Accessibility & Inclusion

User requirement: text must be comfortably legible, never small — body 20px desktop / 19px tablet / 18px phone; no text below 17px; body contrast ≥7:1 (WCAG AAA); A−/A+ control and a Projector mode. Keyboard navigable; reduced motion respected.
