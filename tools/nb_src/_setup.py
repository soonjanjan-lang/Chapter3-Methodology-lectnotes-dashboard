# Setup: install anything missing (needed on Google Colab), then load the libraries.
import importlib.util, subprocess, sys
for pkg in ["pandas", "numpy", "scipy", "statsmodels", "linearmodels", "matplotlib", "openpyxl"]:
    if importlib.util.find_spec(pkg) is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True)

from pathlib import Path
import numpy as np
import pandas as pd

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 30)

# Data live in ../data next to this notebook; online (e.g. Colab) they are read from GitHub.
DATA = Path("../data")
RAW_URL = "https://raw.githubusercontent.com/soonjanjan-lang/Chapter3-Methodology-lectnotes-dashboard/main/downloads/data/"

def load(name):
    p = DATA / name
    return pd.read_csv(p) if p.exists() else pd.read_csv(RAW_URL + name)
