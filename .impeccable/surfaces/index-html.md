---
version: 1
slug: "index-html"
primary_target: "index.html"
related_targets: ["src/shell.html"]
---

# Surface: Chapter 3 Methodology dashboard (index.html)

Scope: whole single-page teaching dashboard, 25 tabs. Visitor mode: **Read** (guide/notes), with Operate islands (calculators, quizzes).
Audience/job: PhD economics students learning to plan and write Chapter 3; instructor teaching live on a projector.
Constraints: user-pinned "Editorial journal" (ivory paper, ink-navy, oxblood, serif display + legible sans body); legibility floor body 20px/18px phone, min 17px, AAA body contrast; offline file://; no kickers/eyebrows.

## Direction contract

THESIS: The dashboard is a bound PhD thesis being examined. The frame is the hardbound thesis and its LaTeX typesetting; the reading column is a calm, large-type page. It refuses the SaaS docs template (grey sidebar, card grids, coloured callout bars, progress rings).

OWN-WORLD: Navy buckram cover cloth (#1B2340) as the navigation rail with gold-foil lettering (#D9B76C); ivory page (#FBF8F1) carrying ink-navy text (#1C2541); oxblood examiner's red pen (#8A1E2C) for annotations, links and active states; highlighter gold behind key terms. Headings in Computer Modern bold (KaTeX_Main) with LaTeX-style section numbers inline; body Source Sans 3; model write-ups as thesis-page specimens in Source Serif 4; Stata/Python in listing boxes (JetBrains Mono). Every table is booktabs: three horizontal rules, no verticals, tabular numerals.

STORY: Reader sees Chapter 3 as a structure (3.1–3.4), understands each subsection's job, learns the underlying concepts, practises with worksheets, and leaves with templates and runnable code.

FIRST VIEWPORT: Left: buckram rail with gold "Chapter 3 · Methodology" title block and the module contents (A–F) like a thesis contents page. Right: the Home page shows a large typeset "Contents of Chapter 3" — 3.1 Data, 3.2 RQ–Method table, 3.3 Variables, 3.4 Model specification — with dotted leaders, each line a link; examiner's red-pen marginal notes draw in once beside two lines. Top running head (italic) with search, text size, projector and theme controls.

FORM: Pinned by user brief ("Editorial journal"); no concept-seed roll — Read-mode rules applied directly. Rendition: bound thesis + LaTeX + examiner's report. Signature interaction: examiner's margin notes (toggle) and the annotated contents page. Seed key: none (brief-pinned).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
