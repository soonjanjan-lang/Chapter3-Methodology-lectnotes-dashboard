"""Generate the practice datasets used in the worked examples, do-files and notebooks.

All data are HYPOTHETICAL (simulated with fixed seeds), except the four small data-structure
tables, which reproduce the illustrative values in the instructor's lecture notes.

    python tools/make_datasets.py      → downloads/data/*.csv and *.dta
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "downloads" / "data"
OUT.mkdir(parents=True, exist_ok=True)


def save(df, name, labels=None, dta=True):
    df.to_csv(OUT / f"{name}.csv", index=False)
    if dta:
        d = df.copy()
        for c in d.columns:
            if d[c].dtype == object:
                d[c] = d[c].fillna("").astype(str)
        d.to_stata(OUT / f"{name}.dta", write_index=False, version=118,
                   variable_labels={k: v[:80] for k, v in (labels or {}).items() if k in d.columns},
                   data_label=f"{name} (hypothetical teaching data)"[:80])
    print(f"{name}: {len(df)} rows x {df.shape[1]} cols")


# ---------------------------------------------------------------------------
# 1. E-wallet survey of university students (raw, messy) — for cleaning, reliability, models
# ---------------------------------------------------------------------------
def likert(latent, loading, rng, noise=0.62):
    z = loading * latent + rng.normal(0, noise, len(latent))
    cuts = np.array([-1.35, -0.55, 0.25, 1.05])
    return 1 + np.searchsorted(cuts, z)


def ewallet():
    rng = np.random.default_rng(20261019)
    n = 408                                   # 400 complete + 8 incomplete
    faculty = rng.choice(["Economics", "Business", "Engineering", "Science", "Arts"], n, p=[.24, .26, .2, .16, .14])
    year = rng.choice([1, 2, 3, 4], n, p=[.28, .27, .25, .2])
    female = rng.binomial(1, 0.58, n)
    age = np.clip(np.round(18.3 + year + rng.normal(0, 1.1, n)), 18, 30).astype(int)
    states = ["Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan", "Pahang", "Perak", "Perlis",
              "Pulau Pinang", "Sabah", "Sarawak", "Selangor", "Terengganu", "Kuala Lumpur"]
    state = rng.choice(states, n, p=[.09, .12, .07, .04, .04, .05, .09, .05, .08, .07, .07, .16, .05, .02])
    urban = rng.binomial(1, np.where(np.isin(state, ["Selangor", "Kuala Lumpur", "Pulau Pinang", "Johor"]), .82, .55))
    allowance = np.round(np.exp(rng.normal(np.log(820), 0.45, n)) / 10) * 10

    # latent constructs: perceived usefulness, perceived security, ease of use
    cov = np.array([[1, .35, .5], [.35, 1, .3], [.5, .3, 1]])
    L = rng.multivariate_normal([0, 0, 0], cov, n)
    pu, ps, eou = L[:, 0], L[:, 1], L[:, 2]
    know = 0.45 * (faculty == "Economics") + 0.25 * (faculty == "Business") + 0.15 * year / 4 + rng.normal(0, 1, n)
    fl = [(know + rng.normal(0, 0.9, n) > t).astype(int) for t in (-0.9, -0.2, 0.5)]   # interest, inflation, diversification

    ln_allow = (np.log(allowance) - np.log(820)) / 0.45
    xb = 1.15 + 0.95 * pu + 0.45 * ps + 0.35 * eou + 0.25 * sum(fl) + 0.35 * ln_allow + 0.4 * urban - 0.15 * female
    user = rng.binomial(1, 1 / (1 + np.exp(-xb)))
    freq = np.where(user == 1, np.clip(np.round(2.6 + 1.1 * pu + 0.5 * eou + 0.4 * ln_allow + rng.normal(0, 1.4, n)), 0, 7), 0).astype(int)
    spend = np.where(user == 1, np.round(np.exp(4.6 + 0.35 * ln_allow + 0.15 * freq + rng.normal(0, 0.5, n))), 0)
    intention = likert(0.8 * pu + 0.35 * ps + 0.25 * eou, 1.0, rng, noise=0.7)
    satisf = np.where(user == 1, likert(0.6 * pu + 0.5 * eou, 1.0, rng, noise=0.75), np.nan)

    df = pd.DataFrame({
        "resp_id": np.arange(1001, 1001 + n),
        "faculty": faculty, "year_study": year,
        "gender": np.where(female == 1, "Female", "Male"),
        "age": age, "state": state, "hometown_urban": urban,
        "allowance_rm": allowance,
        "ewallet_user": user, "ewallet_days": freq, "ewallet_spend_rm": spend,
    })
    for j, lam in enumerate([.82, .78, .85, .74], 1):
        df[f"PU{j}"] = likert(pu, lam, rng)
    for j, lam in enumerate([.80, .84, .76, .79], 1):
        df[f"PS{j}"] = likert(ps, lam, rng)
    for j, lam in enumerate([.81, .77, .73], 1):
        df[f"EOU{j}"] = likert(eou, lam, rng)
    for j in range(3):
        df[f"finlit{j+1}"] = fl[j]
    df["intention"] = intention
    df["satisfaction"] = satisf

    # ---- inject the problems students meet in real raw files --------------------
    items = [c for c in df.columns if c[:2] in ("PU", "PS") or c.startswith("EOU")]
    raw = df.astype(object).copy()
    g = rng.choice(n, 140, replace=False)
    variants = {"Female": ["F", "female", "FEMALE", "f", "Female "], "Male": ["M", "male", "MALE", "m", "Male "]}
    for i in g:
        raw.at[i, "gender"] = rng.choice(variants[df.at[i, "gender"]])
    s = rng.choice(n, 90, replace=False)
    for i in s:
        v = df.at[i, "state"]
        raw.at[i, "state"] = rng.choice([v.upper(), v.lower(), v + " ", " " + v])
    raw.loc[[17, 133, 288], "age"] = 999                        # missing-value code
    raw.loc[[61], "age"] = 150                                  # keying error
    raw.loc[[44, 97, 203, 351], "allowance_rm"] = -9            # missing-value code
    raw.loc[[120, 309], "allowance_rm"] = df.loc[[120, 309], "allowance_rm"] * 100   # extra zeros
    for (i, c, v) in [(12, "PU2", 6), (80, "PS3", 0), (150, "EOU1", 6), (222, "PU4", 9), (390, "PS1", 6)]:
        raw.at[i, c] = v                                        # out-of-range codes
    for k in range(10):
        raw.at[int(rng.integers(0, 400)), str(rng.choice(items))] = -9   # item non-response code
    raw.loc[[30, 260, 377], "ewallet_days"] = [8, 10, 9]        # impossible: > 7 days in a week
    nonusers = df.index[(df.ewallet_user == 0) & (df.index < 400)][:4]
    raw.loc[nonusers, "ewallet_days"] = [2, 1, 3, 1]            # skip-pattern contradiction
    raw.loc[400:, items + ["intention", "finlit1", "finlit2", "finlit3"]] = np.nan   # 8 break-offs (rows 400-407)
    dups = raw.iloc[rng.choice(400, 6, replace=False)].copy()
    raw = pd.concat([raw, dups]).sample(frac=1, random_state=7).reset_index(drop=True)
    labels = {"resp_id": "Respondent ID", "faculty": "Faculty", "year_study": "Year of study", "gender": "Gender (raw text)",
              "age": "Age in years (999 = missing)", "state": "Home state (raw text)", "hometown_urban": "Hometown is urban (1 = yes)",
              "allowance_rm": "Monthly allowance, RM (-9 = missing)", "ewallet_user": "Used an e-wallet in past 30 days (1 = yes)",
              "ewallet_days": "Days used e-wallet in past 7 days", "ewallet_spend_rm": "E-wallet spending past 30 days, RM",
              "intention": "Intention to keep using e-wallets (1-5)", "satisfaction": "Satisfaction with e-wallets (1-5)"}
    save(raw, "ewallet_survey_raw", labels)


# ---------------------------------------------------------------------------
# 2. Sampling frame: SMEs (for SRS, systematic and stratified sampling)
# ---------------------------------------------------------------------------
def sme_frame():
    rng = np.random.default_rng(31)
    sectors = (["Services"] * 1560 + ["Manufacturing"] * 480 + ["Agriculture"] * 240 + ["Construction"] * 120)
    n = len(sectors)
    emp = np.round(np.exp(rng.normal(2.3, 0.9, n))).astype(int) + 1
    size = np.select([emp < 5, emp < 30], ["Micro", "Small"], "Medium")
    sector = rng.permutation(sectors)
    p_accept = pd.Series(sector).map({"Services": .55, "Manufacturing": .35, "Agriculture": .15, "Construction": .25}).values
    df = pd.DataFrame({"sme_id": np.arange(1, n + 1),
                       "sector": sector,
                       "state": rng.choice(["Kedah", "Perlis", "Pulau Pinang", "Perak"], n, p=[.42, .1, .3, .18]),
                       "employees": emp, "size_class": size,
                       "uses_ewallet_payments": rng.binomial(1, p_accept)})
    save(df, "sme_sampling_frame", {"sme_id": "Frame ID", "sector": "Sector", "state": "State", "employees": "Number of employees",
                                    "size_class": "SME size class", "uses_ewallet_payments": "Accepts e-wallet payments (1 = yes)"})


# ---------------------------------------------------------------------------
# 3. The four data-structure tables from the lecture notes (values as shown there)
# ---------------------------------------------------------------------------
def structures():
    cs = pd.DataFrame({
        "Student_ID": [f"STU{i:03d}" for i in range(1, 23)],
        "Study_Hours": [18, 16, 16, 20, 7, 29, 25, 7, 25, 20, 30, 13, 8, 15, 10, 18, 27, 23, 15, 14, 19, 28],
        "Attendance": [100, 78, 88, 91, 64, 61, 63, 90, 79, 72, 81, 100, 73, 97, 65, 65, 84, 70, 83, 90, 67, 88],
        "Sleep_Hours": [8, 5, 9, 9, 7, 7, 5, 8, 9, 7, 7, 9, 8, 9, 5, 8, 6, 5, 7, 5, 7, 7],
        "PT_Job": [1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 1],
        "HH_Income_k": [75, 34, 102, 128, 33, 43, 139, 129, 93, 67, 34, 144, 35, 118, 88, 56, 143, 53, 76, 67, 49, 59],
        "Final_Score": [96.7, 77, 95, 98, 62.6, 100, 100, 84.6, 100, 85.7, 98.7, 99.5, 65.3, 96.4, 76.5, 91.2, 100, 90.2, 87.1, 87.1, 98.6, 93],
        "Gender": ["Female", "Female", "Female", "Male", "Female", "Male", "Male", "Male", "Male", "Female", "Female", "Female",
                   "Female", "Female", "Male", "Female", "Female", "Male", "Female", "Male", "Female", "Male"],
        "Form": [5, 5, 3, 2, 5, 1, 5, 3, 3, 5, 4, 3, 2, 4, 2, 4, 3, 3, 2, 4, 1, 5]})
    save(cs, "ds_crosssection_students")
    ts = pd.DataFrame({
        "Year": list(range(2000, 2024)),
        "GDP_USDb": [102.15, 101.05, 109.83, 120.03, 135.87, 150.35, 170.41, 202.73, 241.95, 211.85, 258.64, 302.18,
                     318.91, 327.87, 342.87, 301.36, 301.26, 319.11, 358.78, 365.18, 337.46, 373.78, 407.61, 399.71],
        "Unemployment": [3, 3.53, 3.48, 3.61, 3.54, 3.53, 3.32, 3.23, 3.32, 3.66, 3.39, 3.05, 3.1, 3.16, 2.88, 3.1, 3.44,
                         3.41, 3.3, 3.26, 4.54, 4.64, 3.93, 3.87],
        "Inflation": [1.53, 1.42, 1.81, 1.09, 1.42, 2.98, 3.61, 2.03, 5.44, 0.58, 1.62, 3.17, 1.66, 2.11, 3.14, 2.1, 2.09,
                      3.87, 0.88, 0.66, -1.14, 2.48, 3.38, 2.49],
        "Export_USDb": [112.37, 102.44, 109.22, 117.85, 143.93, 162.05, 182.52, 205.49, 229.66, 184.9, 221.69, 254.02,
                        249.35, 244.49, 249.47, 209.29, 201.17, 223.41, 245.97, 238.38, 207.8, 264.02, 313.25, 274.13],
        "Import_USDb": [94.35, 86.25, 91.82, 96.15, 118.51, 130.55, 147.06, 167.03, 178.11, 143.89, 181.1, 207.62, 215.53,
                        216.89, 218.12, 186.6, 181.13, 201.5, 221.9, 210.89, 186.31, 236.99, 283.92, 253.74]})
    save(ts, "ds_timeseries_macro")
    pooled = pd.DataFrame({
        "Year": [2022] * 10 + [2023] * 10,
        "ID": list(range(101, 111)) + list(range(201, 211)),
        "Age": [25, 34, 22, 45, 50, 29, 42, 23, 36, 52, 28, 31, 40, 21, 55, 30, 43, 24, 37, 53],
        "Income": [45000, 60000, 15000, 80000, 90000, 48000, 65000, 20000, 72000, 85000,
                   52000, 58000, 75000, 12000, 95000, 50000, 68000, 22000, 75000, 88000],
        "Educ_yrs": [14, 16, 12, 16, 18, 14, 16, 12, 18, 16, 14, 16, 16, 12, 18, 14, 16, 12, 18, 16],
        "Employed": ["Yes", "Yes", "No", "Yes", "Yes", "Yes", "Yes", "No", "Yes", "Yes",
                     "Yes", "Yes", "Yes", "No", "Yes", "Yes", "Yes", "No", "Yes", "Yes"]})
    save(pooled, "ds_pooled_crosssection")
    panel = pd.DataFrame({
        "Country": [c for c in ["USA", "China", "Japan", "Germany", "India"] for _ in range(3)],
        "Year": [2021, 2022, 2023] * 5,
        "GDP_USDb": [23315, 25462, 27360, 17734, 17963, 17700, 5005, 4231, 4212, 4259, 4072, 4456, 3150, 3385, 3732],
        "Inflation": [4.7, 8, 4.1, 0.9, 2, 0.2, -0.2, 2.5, 3.2, 3.1, 6.9, 5.9, 5.1, 6.7, 5.5],
        "Unemp": [5.3, 3.6, 3.6, 3.9, 4.2, 5.2, 2.8, 2.6, 2.6, 3.6, 3.1, 3, 5.9, 7.3, 8],
        "Pop_m": [332, 333, 334, 1412, 1412, 1410, 125, 124, 124, 83, 83, 84, 1407, 1417, 1428],
        "TradeBal_USDb": [-845, -948, -773, 676, 877, 823, 15, -155, -66, 226, 85, 225, -177, -283, -238]})
    save(panel, "ds_panel_countries")


# ---------------------------------------------------------------------------
# 4. Pooled cross-section around an incinerator (simulated, Kiel & McClain 1995 design)
# ---------------------------------------------------------------------------
def incinerator():
    rng = np.random.default_rng(2001)
    rows = []
    for year, n in ((1978, 179), (1981, 142)):
        near = rng.binomial(1, 0.33, n)
        age = np.clip(rng.gamma(2.0, 9.0, n), 0, 120).round()
        rooms = np.clip(np.round(rng.normal(6.6, 0.9, n)), 4, 10)
        area = np.round(rng.normal(2100, 600, n)).clip(700, 4500)
        y81 = int(year == 1981)
        price = (21000 + 9000 * rooms + 9.5 * area - 180 * age + 18000 * y81 - 15000 * near
                 - 11500 * y81 * near + rng.normal(0, 14000, n))
        rows.append(pd.DataFrame({"year": year, "y81": y81, "nearinc": near, "price": price.round(-2),
                                  "age": age, "rooms": rooms, "area": area}))
    df = pd.concat(rows, ignore_index=True)
    df.insert(0, "house_id", np.arange(1, len(df) + 1))
    save(df, "pooled_incinerator_sim", {"y81": "Sold in 1981 (1 = yes)", "nearinc": "Near the incinerator site, within 3 km (1 = yes)",
                                        "price": "Sale price, USD (simulated)", "age": "House age, years", "rooms": "Number of rooms",
                                        "area": "Floor area, sq ft"})


# ---------------------------------------------------------------------------
# 5. Panel of Malaysian states (simulated) — fixed and random effects
# ---------------------------------------------------------------------------
def state_panel():
    rng = np.random.default_rng(50)
    states = ["Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan", "Pahang", "Perak", "Perlis",
              "Pulau Pinang", "Sabah", "Sarawak", "Selangor", "Terengganu"]
    years = list(range(2012, 2023))
    a = rng.normal(0, 3.0, len(states))                       # unobserved state effects
    rows = []
    for i, s in enumerate(states):
        base_inc = 4.2 + 0.6 * a[i] / 3 + rng.normal(0, 0.3)
        for t, y in enumerate(years):
            finlit = 48 + 1.2 * t + 4 * a[i] / 3 + rng.normal(0, 5.0)        # correlated with a_i → FE ≠ RE
            income = base_inc + 0.12 * t + rng.normal(0, 0.45)               # RM thousand per month
            shock = -2.5 if y == 2020 else 0
            save_rate = 6 + a[i] + 0.15 * finlit + 1.1 * income + shock + rng.normal(0, 1.2)
            rows.append((s, y, round(save_rate, 2), round(finlit, 1), round(income, 2)))
    df = pd.DataFrame(rows, columns=["state", "year", "saving_rate", "finlit_index", "income_k"])
    save(df, "panel_states_sim", {"saving_rate": "Household saving rate, % (simulated)",
                                  "finlit_index": "Financial literacy index, 0-100 (simulated)",
                                  "income_k": "Mean household income, RM thousand/month (simulated)"})


if __name__ == "__main__":
    ewallet()
    sme_frame()
    structures()
    incinerator()
    state_panel()
