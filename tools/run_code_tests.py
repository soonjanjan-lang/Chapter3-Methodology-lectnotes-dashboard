"""Run every Stata do-file and Jupyter notebook in downloads/code and fail on any error.

    python tools/run_code_tests.py            run all (Stata files in order, then notebooks)
    python tools/run_code_tests.py --dir X    run the copies in another folder (e.g. an unzipped release)

Stata: batch mode (/e). A do-file fails if Stata exits non-zero, writes no log, or the log contains
an error return code line such as "r(198);".
Notebooks: executed top to bottom in a fresh kernel with nbclient; any cell error fails. Executed
notebooks are saved back with their outputs so students see results before running anything.
Writes tools/code_test_report.md.
"""
import argparse
import datetime as dt
import re
import subprocess
import sys
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent.parent
STATA = Path(r"C:\Program Files\StataNow19\StataMP-64.exe")


def run_stata(do):
    log = do.with_suffix(".log")
    if log.exists():
        log.unlink()
    t0 = time.time()
    try:
        r = subprocess.run([str(STATA), "/e", "do", do.name], cwd=do.parent, timeout=900)
        code = r.returncode
    except subprocess.TimeoutExpired:
        return False, "timed out after 900 s", time.time() - t0
    if not log.exists():
        return False, f"no log written (exit {code})", time.time() - t0
    text = log.read_text(encoding="utf-8", errors="replace")
    errs = re.findall(r"^r\((\d+)\);", text, re.M)
    if code != 0 or errs:
        tail = "\n".join(text.splitlines()[-25:])
        return False, f"exit {code}, error codes {errs}\n{tail}", time.time() - t0
    return True, "ok", time.time() - t0


def run_notebook(nb_path, save=True):
    nb = nbformat.read(nb_path, as_version=4)
    t0 = time.time()
    client = NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(nb_path.parent)}})
    try:
        client.execute()
    except Exception as e:  # CellExecutionError and kernel failures
        return False, str(e)[-2500:], time.time() - t0
    if save:
        nbformat.write(nb, nb_path)
    return True, "ok", time.time() - t0


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "downloads" / "code"))
    ap.add_argument("--only", default=None, help="substring filter on file names")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    code_dir = Path(a.dir)
    dos = sorted(code_dir.glob("*.do"))
    nbs = sorted(code_dir.glob("*.ipynb"))
    if a.only:
        dos = [d for d in dos if a.only in d.name]
        nbs = [n for n in nbs if a.only in n.name]
    results = []
    if dos and not STATA.exists():
        print(f"Stata not found at {STATA}")
        return 2
    for d in dos:
        ok, msg, secs = run_stata(d)
        results.append((d.name, ok, msg, secs))
        print(f"[{'PASS' if ok else 'FAIL'}] {d.name} ({secs:.0f}s)" + ("" if ok else "\n" + msg), flush=True)
    for n in nbs:
        ok, msg, secs = run_notebook(n, save=not a.no_save)
        results.append((n.name, ok, msg, secs))
        print(f"[{'PASS' if ok else 'FAIL'}] {n.name} ({secs:.0f}s)" + ("" if ok else "\n" + msg), flush=True)
    n_fail = sum(1 for r in results if not r[1])
    if code_dir == ROOT / "downloads" / "code" and not a.only:
        lines = [f"# Code test report", "",
                 f"Run {dt.datetime.now():%Y-%m-%d %H:%M} — StataNow 19 MP (batch mode) and Python {sys.version.split()[0]} (nbclient).", "",
                 "| File | Result | Time |", "|---|---|---|"]
        lines += [f"| `{name}` | {'PASS' if ok else 'FAIL'} | {secs:.0f} s |" for name, ok, _, secs in results]
        lines += ["", f"**{len(results) - n_fail} of {len(results)} files ran without errors.**"]
        (ROOT / "tools" / "code_test_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{len(results) - n_fail}/{len(results)} passed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
