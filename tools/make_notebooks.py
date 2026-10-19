"""Turn the cell-marked Python sources in tools/nb_src/ into Jupyter notebooks in downloads/code/.

A line '# %%' starts a code cell; '# %% [markdown]' starts a markdown cell whose lines drop
their leading '# '. The shared setup cell (tools/nb_src/_setup.py) is inserted after the
title cell of every notebook.

    python tools/make_notebooks.py
"""
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

HERE = Path(__file__).resolve().parent
SRC = HERE / "nb_src"
OUT = HERE.parent / "downloads" / "code"


def cells_from(text):
    cells, kind, buf = [], None, []

    def flush():
        if kind is None:
            return
        body = "\n".join(buf).strip("\n")
        if not body:
            return
        if kind == "md":
            lines = [l[2:] if l.startswith("# ") else l.lstrip("#") for l in body.splitlines()]
            cells.append(new_markdown_cell("\n".join(lines)))
        else:
            cells.append(new_code_cell(body))

    for line in text.splitlines():
        if line.startswith("# %% [markdown]"):
            flush(); kind, buf = "md", []
        elif line.startswith("# %%"):
            flush(); kind, buf = "code", []
        else:
            buf.append(line)
    flush()
    return cells


def main():
    setup = (SRC / "_setup.py").read_text(encoding="utf-8").strip()
    for src in sorted(SRC.glob("[0-9]*.py")):
        cells = cells_from(src.read_text(encoding="utf-8"))
        cells.insert(1, new_code_cell(setup))
        nb = new_notebook(cells=cells, metadata={
            "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
            "language_info": {"name": "python"}})
        out = OUT / (src.stem + ".ipynb")
        nbformat.write(nb, out)
        print(out.name, len(cells), "cells")


if __name__ == "__main__":
    main()
