---
name: Chapter 3 Methodology dashboard
description: A PhD research-methods guide set as a bound, examined thesis
colors:
  ivory-page: "#FBF8F1"
  sunk-page: "#F2EDE1"
  raised-sheet: "#FFFDF8"
  ink-navy: "#1C2541"
  ink-secondary: "#3D4560"
  hairline: "#D8D0BF"
  examiner-red: "#8A1E2C"
  red-wash: "#F5E3E1"
  highlighter: "#F3DE9A"
  correct-green: "#285A40"
  buckram-navy: "#1B2340"
  buckram-active: "#2A3560"
  gold-foil: "#D9B76C"
  gold-foil-dim: "#B7A57E"
  cover-ivory: "#EFE8D8"
  night-page: "#141A2E"
  night-ink: "#EFE8D8"
  night-red: "#F0968A"
typography:
  display:
    fontFamily: "KaTeX_Main, Latin Modern Roman, CMU Serif, Source Serif 4, Georgia, serif"
    fontSize: "clamp(2.1rem, 1.4rem + 2.2vw, 2.6rem)"
    fontWeight: 700
    lineHeight: 1.18
  headline:
    fontFamily: "KaTeX_Main, Latin Modern Roman, Georgia, serif"
    fontSize: "1.8rem"
    fontWeight: 700
    lineHeight: 1.18
  title:
    fontFamily: "KaTeX_Main, Latin Modern Roman, Georgia, serif"
    fontSize: "1.35rem"
    fontWeight: 700
    lineHeight: 1.18
  body:
    fontFamily: "Source Sans 3, Segoe UI, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "Source Sans 3, Segoe UI, system-ui, sans-serif"
    fontSize: "max(17px, 0.875rem)"
    fontWeight: 600
    lineHeight: 1.35
  page-specimen:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "1.04rem"
    fontWeight: 400
    lineHeight: 1.78
  code:
    fontFamily: "JetBrains Mono, Consolas, monospace"
    fontSize: "max(17px, 0.9rem)"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  sheet: "3px"
  control: "6px"
  button: "8px"
  card: "10px"
  calc: "12px"
spacing:
  s1: "0.25rem"
  s2: "0.5rem"
  s3: "0.75rem"
  s4: "1rem"
  s5: "1.5rem"
  s6: "2rem"
  s7: "3rem"
  s8: "4.5rem"
components:
  button-primary:
    backgroundColor: "{colors.examiner-red}"
    textColor: "{colors.ivory-page}"
    rounded: "{rounded.button}"
    padding: "0.45em 1.15em"
  button-secondary:
    backgroundColor: "{colors.ivory-page}"
    textColor: "{colors.examiner-red}"
    rounded: "{rounded.button}"
    padding: "0.45em 1.15em"
  nav-link-active:
    backgroundColor: "{colors.buckram-active}"
    textColor: "{colors.raised-sheet}"
    rounded: "{rounded.control}"
    padding: "0.42em 0.75rem"
  subtab-active:
    textColor: "{colors.examiner-red}"
    typography: "{typography.label}"
  thesis-sheet:
    backgroundColor: "{colors.raised-sheet}"
    textColor: "{colors.ink-navy}"
    typography: "{typography.page-specimen}"
    rounded: "{rounded.sheet}"
    padding: "2rem 3rem"
  calculator:
    backgroundColor: "{colors.raised-sheet}"
    rounded: "{rounded.calc}"
    padding: "1.5rem"
---

# Design System: Chapter 3 Methodology dashboard

## Overview

**Creative North Star: "The Bound Thesis, Under Examination"**

The dashboard is a hardbound PhD thesis on the examiner's desk. The frame belongs to the thesis: a navy buckram cover with gold-foil lettering carries the navigation, section heads are set in Computer Modern as LaTeX would set them, and every table follows the booktabs convention of economics papers. The reading column inside that frame stays calm: large, high-contrast sans-serif text at a real measure. The one expressive device is the examiner's red pen, which circles section numbers, writes notes in the margin and marks answers.

The world was chosen by the instructor ("Editorial journal": ivory paper, ink navy, oxblood, serif heads, legible sans body). Its rendition was grounded in what economists read daily: LaTeX-typeset working papers and bound theses.

**Key Characteristics:**
- Navy buckram rail with flat gold foil; ivory page; one red-pen accent.
- Computer Modern section heads with inline LaTeX-style numbers (A1, 3.2), never eyebrow labels.
- Booktabs tables: three horizontal rules, no verticals, tabular numerals.
- Legibility is a hard floor: body 20px desktop / 18px phone, nothing below 17px, body contrast ≥ 7:1.
- Works offline from a ZIP: self-hosted fonts, maths and code highlighting.

## Colors

A restrained palette: tinted paper neutrals, one red-pen accent, gold reserved for the cover.

### Primary
- **Examiner's Red Pen** (#8A1E2C): links, the active sub-tab, primary buttons, margin notes, pen circles, wrong-answer marks. 8.6:1 on the page.

### Secondary
- **Gold Foil** (#D9B76C): only on the buckram, for the cover title, module letters, active-section codes and the ribbon bookmark. Never on the page.

### Neutral
- **Ivory Page** (#FBF8F1): the page ground.
- **Ink Navy** (#1C2541): body text and booktabs rules (14.2:1).
- **Secondary Ink** (#3D4560): ledes, captions, notes (8.9:1). No grey body text.
- **Sunk Page** (#F2EDE1): code listings, form wells, hover.
- **Raised Sheet** (#FFFDF8): thesis-page specimens, calculators, model answers.
- **Hairline** (#D8D0BF): light rules and borders.
- **Buckram Navy** (#1B2340), **Buckram Active** (#2A3560), **Cover Ivory** (#EFE8D8), **Gold Foil Dim** (#B7A57E): the navigation rail.
- **Highlighter** (#F3DE9A): behind key terms and text selection.
- **Correct Green** (#285A40): correct quiz answers and completed checklist counts only.
- **Night reading** (#141A2E page, #EFE8D8 ink, #F0968A pen): the dark theme, set on the buckram itself.

### Named Rules
**The One Pen Rule.** Red appears only where the examiner would write: links, the active state, annotations and marks. Never as decoration.
**The Foil Stays on the Cover Rule.** Gold belongs to the rail and the download banner (the cover). The page never uses it.

## Typography

**Display Font:** Computer Modern (KaTeX_Main, bold), the face of LaTeX theses
**Body Font:** Source Sans 3 (variable)
**Specimen Font:** Source Serif 4, for model write-ups set as thesis pages
**Code Font:** JetBrains Mono, for Stata and Python only

**Character:** Computer Modern makes every heading read like a section of a real thesis; Source Sans 3 keeps long reading easy on screens and projectors.

### Hierarchy
- **Display** (700, clamp(2.1rem, 1.4rem + 2.2vw, 2.6rem), 1.18): section titles with inline codes (“D4 How many respondents…”).
- **Headline** (700, 1.8rem, 1.18): h2 within a section.
- **Title** (700, 1.35rem, 1.18): h3.
- **Body** (400, 1rem = 20px desktop / 19px tablet / 18px phone, 1.7, max 68ch).
- **Label** (600, max(17px, 0.875rem)): navigation, sub-tabs, buttons, captions.
- **Page specimen** (400, 1.04rem, 1.78): model write-ups on thesis sheets.

### Named Rules
**The Seventeen-Pixel Floor Rule.** No visible text renders below 17px. Subscripts use max(17px, 0.72em). Charts are drawn at their real pixel width so their labels never scale down. `tools/qa_playwright.py` enforces this.
**The Number Is the Kicker Rule.** Section heads carry their number inline (A1, 3.2), LaTeX style. Never a tracked-caps label above a heading.

## Layout

A two-column shell: an 18rem buckram rail (sticky; it becomes a drawer below 1024px and in Projector mode) and the page. A sticky running head carries the section's short title and the tools. Sections use a reading grid: a 68ch column, plus a 13–17rem margin column for the examiner's notes when the page container reaches 50rem (a container query). Tables, listings, calculators and figures span both columns. The rhythm is one spacing scale (0.25–4.5rem), with more space above headings than below. The base size is user-adjustable from 18 to 28px, and Projector mode sets 26px.

## Elevation & Depth

Mostly flat, with tonal layering (page, sunk, raised). One soft shadow lifts the thesis sheets, the only objects meant to read as paper on the desk (`0 1px 2px rgb(28 37 65 / .08), 0 6px 18px -8px rgb(28 37 65 / .22)`). Calculators, answers and cards use a hairline border instead, never border and shadow together.

## Shapes

Gentle radii scaled by role: sheets 3px (paper), controls 6px, buttons 8px, answer boxes 10px, calculators 12px. Rules, not boxes, organise reading content: booktabs tables, worksheet rows and checklists use 2px ink rules top and bottom with hairlines between.

## Components

### Buttons
- **Primary:** red-pen fill, ivory text, 8px radius, min-height 2.75rem; hover darkens; 1px press.
- **Secondary:** ivory with red-pen outline and text.

### Navigation (the cover)
- Contents list with code + title. Hover lifts to buckram-hover. The active item gets buckram-active, ivory text, a gold code and a gold ribbon bookmark hanging off the cover's edge. Visited items show a dim tick.

### Sub-tabs
- Notes / Worked example / Write-up / Worksheet / Quiz. Label type, sticky under the running head; the active tab has red-pen text with a square 3px underline.

### Examiner's margin note (signature)
- Source Serif 4 italic in red pen with a hand-drawn tick or query mark. Sits in the margin column on wide pages and inline with a red wash on narrow ones. Can be toggled off.

### Thesis sheet (signature)
- A model write-up set as a thesis page on the raised sheet, with wavy red underlines and numbered red annotations explained beneath.

### Calculators and simulators
- Raised sheet, hairline border, 12px radius; results in Computer Modern red numerals; charts drawn as inline SVG at pixel width.

## Do's and Don'ts

### Do:
- **Do** set every table as booktabs (2px rules top and bottom, 1px under the header, no vertical rules).
- **Do** keep body text at 20/19/18px and every label at 17px or more; check with `tools/qa_playwright.py`.
- **Do** put numbers inline in headings (A1, 3.2) and use the red pen only for annotation, links and state.
- **Do** label hypothetical data as hypothetical.

### Don't:
- **Don't** add eyebrow or kicker labels above headings.
- **Don't** use grey for body text or contrast below 7:1 for running text.
- **Don't** use gold on the page, or red as decoration.
- **Don't** pair a border with a wide shadow on the same card.
- **Don't** embed text in SVG diagrams that scale; build text-bearing diagrams in HTML.
