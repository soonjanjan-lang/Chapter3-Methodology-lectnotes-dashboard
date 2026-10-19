"""Build the Word worksheets and the templates for the downloads, from the dashboard's own sources.

    python tools/make_worksheets.py

Outputs
  downloads/worksheets/Chapter3_Worksheets.docx                       questions with answer space
  downloads/worksheets/Chapter3_Worksheets_with_model_answers.docx    questions and model answers
  downloads/templates/RQ_method_table_template.docx
  downloads/templates/Codebook_template.xlsx
  downloads/templates/Chapter3_outline_template.docx
  downloads/templates/Adaptation_log_template.docx
"""
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Cm
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = ROOT / "src" / "sections"
WS_DIR = ROOT / "downloads" / "worksheets"
TPL_DIR = ROOT / "downloads" / "templates"
PEN = RGBColor(0x8A, 0x1E, 0x2C)
INK = RGBColor(0x1C, 0x25, 0x41)

GREEK = {r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ", r"\lambda": "λ", r"\varepsilon": "ε", r"\rho": "ρ",
         r"\sigma": "σ", r"\mu": "μ", r"\pi": "π", r"\kappa": "κ", r"\tau": "τ", r"\chi": "χ", r"\times": "×", r"\cdot": "·",
         r"\ge": "≥", r"\le": "≤", r"\in": "∈", r"\neq": "≠", r"\approx": "≈", r"\infty": "∞", r"\sum": "Σ", r"\mid": "|",
         r"\Lambda": "Λ", r"\ldots": "…", r"\dots": "…"}


def plain_math(s):
    """Turn the inline LaTeX used in worksheets into readable plain text."""
    def conv(m):
        t = m.group(1)
        t = re.sub(r"\\(?:mathbf|boldsymbol|mathrm|operatorname|text)\{([^}]*)\}", r"\1", t)
        t = re.sub(r"\\(?:mathbf|boldsymbol)\\?(\w)", r"\1", t)
        t = re.sub(r"\\d?frac\{([^}]*)\}\{([^}]*)\}", r"(\1)/(\2)", t)
        t = re.sub(r"\\sqrt\{([^}]*)\}", r"√(\1)", t)
        for k in sorted(GREEK, key=len, reverse=True):
            t = t.replace(k, GREEK[k])
        t = t.replace(r"\{", "{").replace(r"\}", "}").replace("\\,", " ").replace("\\;", " ").replace("\\!", "")
        t = re.sub(r"_\{([^}]*)\}", r"_\1", t)
        t = re.sub(r"\^\{([^}]*)\}", r"^\1", t)
        t = t.replace("\\", "")
        return t
    s = re.sub(r"\\\((.*?)\\\)", conv, s, flags=re.S)
    s = re.sub(r"\$\$(.*?)\$\$", conv, s, flags=re.S)
    return re.sub(r"\s+", " ", s).strip()


def text_of(el):
    return plain_math(el.get_text(" ", strip=True)).replace(" ,", ",").replace(" .", ".").replace("( ", "(").replace(" )", ")").replace(" ;", ";").replace(" :", ":")


def set_cell_shading(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def new_doc(title, subtitle):
    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    for side in ("left_margin", "right_margin"):
        setattr(sec, side, Cm(2.2))
    sec.top_margin = sec.bottom_margin = Cm(2.0)
    st = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(12)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.line_spacing = 1.2
    for lvl, size in ((1, 18), (2, 14), (3, 12)):
        h = doc.styles[f"Heading {lvl}"]
        h.font.name = "Cambria"
        h.font.size = Pt(size)
        h.font.color.rgb = INK
    doc.add_heading(title, 0).runs[0].font.color.rgb = INK
    p = doc.add_paragraph(subtitle)
    p.runs[0].italic = True
    return doc


def add_table(doc, rows, header=True, widths=None):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            c = t.cell(i, j)
            c.text = v
            for par in c.paragraphs:
                for run in par.runs:
                    run.font.size = Pt(11)
                    run.bold = header and i == 0
            if header and i == 0:
                set_cell_shading(c, "E9E4D8")
            if widths:
                c.width = Cm(widths[j])
    doc.add_paragraph()
    return t


def add_answer(doc, body):
    """Model answer: paragraphs, lists and tables inside an <x-answer>."""
    lab = doc.add_paragraph()
    r = lab.add_run("Model answer")
    r.bold = True
    r.font.color.rgb = PEN
    for child in body.children:
        if isinstance(child, NavigableString):
            if child.strip():
                doc.add_paragraph(plain_math(str(child)))
            continue
        if child.name == "table":
            rows = [[text_of(td) for td in tr.find_all(["th", "td"])] for tr in child.find_all("tr")]
            if rows:
                add_table(doc, rows)
        elif child.name in ("ul", "ol"):
            for li in child.find_all("li", recursive=False):
                doc.add_paragraph(text_of(li), style="List Bullet")
        else:
            p = doc.add_paragraph(text_of(child))
            for run in p.runs:
                run.font.color.rgb = RGBColor(0x28, 0x34, 0x4F)


def collect():
    """Return [(code, title, [(question_text, answer_tag)])] in section order."""
    out = []
    for f in sorted(SECTIONS.glob("*.html")):
        raw = f.read_text(encoding="utf-8")
        meta = dict(re.findall(r"^(\w+):\s*(.*)$", re.search(r"<!--meta(.*?)-->", raw, re.S).group(1), re.M))
        soup = BeautifulSoup(raw, "html.parser")
        for panel in soup.select('div.panel[data-panel="worksheet"], div.panel[data-panel="fix"], div.panel[data-panel="tutorial"]'):
            qs = []
            intro = None
            box = panel.select_one(".box")
            if box is not None and panel.get("data-panel") == "tutorial":
                intro = text_of(box)
            for li in panel.select("li.ws-q"):
                q = li.find("p")
                qs.append((text_of(q), li.find("x-answer")))
            if qs:
                kind = {"worksheet": "Worksheet", "fix": "Fix the items", "tutorial": "Integrated tutorial"}[panel["data-panel"]]
                out.append((meta.get("code", ""), meta["title"], kind, intro, qs))
    return out


def build_worksheets(with_answers):
    doc = new_doc("Chapter 3: Methodology — Worksheets" + (" with model answers" if with_answers else ""),
                  "PhD Research Methods. Worksheets from the Chapter 3 dashboard. "
                  + ("Model answers follow each question; try each question first." if with_answers
                     else "Write your answers in the space provided; model answers are in the companion file."))
    first = True
    for code, title, kind, intro, qs in collect():
        if not first:
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        first = False
        doc.add_heading(f"{code} {title}".strip(), 1)
        doc.add_paragraph(kind).runs[0].italic = True
        if intro:
            doc.add_paragraph(intro)
        for i, (q, ans) in enumerate(qs, 1):
            p = doc.add_paragraph()
            r = p.add_run(f"Q{i}. ")
            r.bold = True
            r.font.color.rgb = PEN
            p.add_run(q)
            if with_answers and ans is not None:
                add_answer(doc, ans)
            elif not with_answers:
                for _ in range(5):
                    line = doc.add_paragraph()
                    pPr = line._p.get_or_add_pPr()
                    bdr = OxmlElement("w:pBdr")
                    bottom = OxmlElement("w:bottom")
                    for k, v in (("w:val", "single"), ("w:sz", "4"), ("w:space", "1"), ("w:color", "BFB8A8")):
                        bottom.set(qn(k), v)
                    bdr.append(bottom)
                    pPr.append(bdr)
    name = "Chapter3_Worksheets_with_model_answers.docx" if with_answers else "Chapter3_Worksheets.docx"
    WS_DIR.mkdir(parents=True, exist_ok=True)
    doc.save(WS_DIR / name)
    print(name)


def build_templates():
    TPL_DIR.mkdir(parents=True, exist_ok=True)
    # RQ–method table
    doc = new_doc("Template: RQ–method table", "Section 3.2. One row per research question or sub-question; wording identical to Chapter 1.")
    add_table(doc, [["Research question", "Outcome variable (measurement level)", "Main explanatory variable(s)", "Data source and unit", "Method or model"],
                    ["RQ1:", "", "", "", ""], ["RQ2:", "", "", "", ""], ["RQ3:", "", "", "", ""], ["RQ4:", "", "", "", ""]],
              widths=[4.5, 3.2, 3.2, 2.8, 2.8])
    doc.add_paragraph("Optional columns: hypothesis; data collection method; theory; section of Chapter 4 where the question is answered.")
    doc.save(TPL_DIR / "RQ_method_table_template.docx")
    # Adaptation log
    doc = new_doc("Template: adaptation log", "Appendix. One row per item adopted, adapted, dropped or added.")
    add_table(doc, [["Construct", "Original item and source", "Adapted item", "Type of change", "Reason and evidence"],
                    ["", "", "", "", ""], ["", "", "", "", ""], ["", "", "", "", ""], ["", "", "", "", ""]],
              widths=[2.6, 4.2, 4.2, 2.6, 3.0])
    doc.add_paragraph("Types of change: context words; tense; translation (with back-translation); response format; item dropped; item added. "
                      "Record expert-review and pilot evidence for every changed item.")
    doc.save(TPL_DIR / "Adaptation_log_template.docx")
    # Chapter 3 outline
    doc = new_doc("Template: Chapter 3 outline", "Headings and prompts for an economics Methodology chapter. Delete the prompts as you write.")
    outline = [
        ("3.0 Introduction", ["State the paradigm in one or two sentences and what it implies for this study.",
                              "Name the research design (quantitative, qualitative or mixed; cross-sectional, panel, experimental).",
                              "Give a one-sentence map of the sections that follow."]),
        ("3.1 Data", ["Target population (who, where, when) and sampling frame, with its gaps.",
                      "Sampling design and why it suits the research questions.",
                      "Sample size: precision or power calculation; inflation for non-response and design effect.",
                      "Instrument: sections, items, response formats, sources of adopted and adapted scales; translation.",
                      "Table: questionnaire items mapped to variables.",
                      "Pretest and pilot; administration (mode, dates); response (invited, returned, usable, rate).",
                      "Or, for secondary data: dataset, provider, version, access date, coverage, unit, series codes, limitations.",
                      "Data preparation: cleaning rules and the path from raw records to the analysis sample."]),
        ("3.2 Research questions and methods", ["Introduce the RQ–method table; explain why each method suits its question."]),
        ("3.3 Variables and measurement", ["Operationalisation table (name, definition, item, level, coding, expected sign).",
                                           "Composite scores: how built; reliability and validity evidence from this sample.",
                                           "Transformations (logs, dummies) and why."]),
        ("3.4 Model specification", ["Numbered estimating equations with subscripts matching the data structure; every symbol defined.",
                                     "Estimator and justification (outcome level; identification problem).",
                                     "Key assumptions and diagnostic tests; standard errors; what will be reported; robustness checks.",
                                     "Methodological review for any less familiar estimator."]),
        ("3.5 Ethics and limitations", ["Approval reference, consent, anonymity, data protection.",
                                        "Each limitation with its likely consequence and your response."]),
        ("3.6 Summary", ["One paragraph: what was done; bridge to Chapter 4."]),
    ]
    for head, prompts in outline:
        doc.add_heading(head, 1)
        for pr in prompts:
            doc.add_paragraph(pr, style="List Bullet")
    doc.save(TPL_DIR / "Chapter3_outline_template.docx")
    # Codebook (Excel)
    wb = Workbook()
    ws = wb.active
    ws.title = "Codebook"
    head = ["Variable name", "Label / operational definition", "Questionnaire item or data source", "Level of measurement",
            "Coding / values / unit", "Role and expected sign", "Missing-value codes", "Notes"]
    ws.append(head)
    for _ in range(25):
        ws.append([""] * len(head))
    ex = wb.create_sheet("Example (e-wallet survey)")
    ex.append(head)
    for row in [
        ["ewallet_user", "Used an e-wallet in the past 30 days", "B1", "Nominal (binary)", "1 = yes, 0 = no", "Outcome (RQ2)", "", ""],
        ["ewallet_days", "Days an e-wallet was used in the past 7 days", "B2", "Ratio (count)", "0–7", "Outcome (RQ3)", ">7 set to missing", "Missing if non-user reports use"],
        ["intention", "I intend to keep using e-wallets", "E1", "Ordinal", "1 = strongly disagree … 5 = strongly agree", "Outcome (RQ4)", "-9", ""],
        ["PU", "Perceived usefulness", "C1–C4", "Interval-like composite", "Mean of four 1–5 items", "Explanatory (+)", "", "α = 0.86"],
        ["PS", "Perceived security", "C5–C8", "Interval-like composite", "Mean of four 1–5 items", "Explanatory (+)", "", "α = 0.86"],
        ["EOU", "Ease of use", "C9–C11", "Interval-like composite", "Mean of three 1–5 items", "Explanatory (+)", "", "α = 0.77"],
        ["finlit", "Correct answers to three financial-literacy questions", "D1–D3", "Interval-like index", "0–3", "Explanatory (+)", "", ""],
        ["female", "Respondent is female", "A1", "Nominal (binary)", "1 = female, 0 = male", "Control", "", "Raw text standardised"],
        ["ln_allow", "Natural log of monthly allowance (RM)", "A7", "Ratio (log)", "ln(RM)", "Control (+)", "-9; > RM 10,000 set to missing", ""],
        ["urban", "Hometown is urban", "A6", "Nominal (binary)", "1 = urban, 0 = rural", "Control (+)", "", ""],
    ]:
        ex.append(row)
    for sheet in (ws, ex):
        for c in sheet[1]:
            c.font = Font(bold=True, color="1C2541")
            c.fill = PatternFill("solid", fgColor="E9E4D8")
        for col, w in zip("ABCDEFGH", (16, 40, 22, 22, 30, 20, 24, 28)):
            sheet.column_dimensions[col].width = w
        for row in sheet.iter_rows():
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical="top")
        sheet.freeze_panes = "A2"
    wb.save(TPL_DIR / "Codebook_template.xlsx")
    print("templates written")


if __name__ == "__main__":
    build_worksheets(False)
    build_worksheets(True)
    build_templates()
