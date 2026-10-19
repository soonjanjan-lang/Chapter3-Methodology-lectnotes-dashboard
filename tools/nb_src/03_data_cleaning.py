# %% [markdown]
# # 03 Data cleaning
# **Chapter 3: Methodology — C5 Data cleaning, worked example.** The Python twin of `03_data_cleaning.do`.
#
# Raw file: `ewallet_survey_raw.csv` (hypothetical survey, 414 records). Output: `ewallet_survey_clean.csv`.
# Every step mirrors the do-file, so both produce the same 400 clean records.

# %% [markdown]
# ## 1. Inspect structure

# %%
raw = load("ewallet_survey_raw.csv")
print("Raw records:", len(raw))
raw.info()

# %%
print(raw["gender"].value_counts(dropna=False).head(12))
raw[["age", "allowance_rm", "ewallet_days", "PU1", "PS1", "EOU1", "intention"]].describe().round(2)

# %% [markdown]
# ## 2. Duplicates

# %%
print("Repeated IDs:", raw["resp_id"].duplicated().sum())
print("Rows identical on every variable:", raw.duplicated().sum())
df = raw.drop_duplicates().copy()
print("After dropping exact duplicates:", len(df))

# %% [markdown]
# ## 3. Incomplete questionnaires (break-offs)
# Drop anyone who answered fewer than half of the 15 scale items.

# %%
items = [f"PU{j}" for j in range(1, 5)] + [f"PS{j}" for j in range(1, 5)] + [f"EOU{j}" for j in range(1, 4)]
scale = items + ["intention", "finlit1", "finlit2", "finlit3"]
n_missing = df[scale].isna().sum(axis=1)
print(n_missing[n_missing > 0].value_counts())
df = df[n_missing < 8].copy()
print("After dropping break-offs:", len(df))

# %% [markdown]
# ## 4. Missing-value codes and 5. out-of-range or implausible values

# %%
df["age"] = df["age"].replace(999, np.nan)
for v in ["allowance_rm"] + items + ["intention"]:
    df[v] = df[v].replace(-9, np.nan)
for v in items + ["intention"]:
    bad = df[v].notna() & ~df[v].between(1, 5)
    if bad.any():
        print(f"{v}: {bad.sum()} out-of-range value(s) set to missing")
    df.loc[bad, v] = np.nan
print(df.loc[df["age"].notna() & ~df["age"].between(17, 40), ["resp_id", "age"]])
df.loc[~df["age"].between(17, 40), "age"] = np.nan
print(df.loc[df["allowance_rm"] > 10000, ["resp_id", "allowance_rm"]])
df.loc[df["allowance_rm"] > 10000, "allowance_rm"] = np.nan

# %% [markdown]
# ## 6. Inconsistent text coding

# %%
g = df["gender"].str.strip().str.lower()
df["female"] = np.select([g.isin(["f", "female"]), g.isin(["m", "male"])], [1, 0], default=np.nan)
print(pd.crosstab(df["gender"], df["female"]))
df["state"] = df["state"].str.strip().str.title()
print(df["state"].value_counts())

# %% [markdown]
# ## 7. Logical consistency (skip pattern)

# %%
print("Days > 7:", (df["ewallet_days"] > 7).sum())
df.loc[df["ewallet_days"] > 7, "ewallet_days"] = np.nan
contra = (df["ewallet_user"] == 0) & (df["ewallet_days"] > 0)
print("Non-users reporting use:", contra.sum())
df.loc[contra, "ewallet_days"] = np.nan

# %% [markdown]
# ## 8. Generate analysis variables

# %%
df["PU"] = df[[f"PU{j}" for j in range(1, 5)]].mean(axis=1)
df["PS"] = df[[f"PS{j}" for j in range(1, 5)]].mean(axis=1)
df["EOU"] = df[[f"EOU{j}" for j in range(1, 4)]].mean(axis=1)
df["finlit"] = df[["finlit1", "finlit2", "finlit3"]].sum(axis=1, min_count=1)
df["ln_allow"] = np.log(df["allowance_rm"])
df["urban"] = df["hometown_urban"]

# %% [markdown]
# ## 9. Save raw and clean separately (never overwrite the raw file)

# %%
order = ["resp_id", "faculty", "year_study", "female", "age", "state", "urban", "allowance_rm", "ln_allow",
         "ewallet_user", "ewallet_days", "ewallet_spend_rm", "PU", "PS", "EOU", "finlit", "intention", "satisfaction"]
clean = df[order + [c for c in df.columns if c not in order and c not in ("gender", "hometown_urban")]]
print("Clean records:", len(clean))
print(clean[["female", "age", "allowance_rm", "ewallet_user", "PU", "PS", "EOU", "finlit"]].describe().T.round(4))
if DATA.exists():
    clean.to_csv(DATA / "ewallet_survey_clean.csv", index=False)

# %% [markdown]
# ## 10. A data dictionary for the appendix

# %%
# a data dictionary you can export to Word or Excel for the appendix
codebook = pd.DataFrame({
    "variable": ["ewallet_user", "PU", "finlit", "female"],
    "definition": ["Used an e-wallet in past 30 days", "Perceived usefulness, mean of PU1-PU4",
                   "Financial literacy, correct answers", "Respondent is female"],
    "level": ["nominal (binary)", "interval-like", "interval-like", "nominal (binary)"],
    "coding": ["1 = yes, 0 = no", "1-5", "0-3", "1 = female, 0 = male"],
})
codebook.to_excel(DATA / "codebook_ewallet.xlsx" if DATA.exists() else "codebook.xlsx", index=False)
clean[codebook["variable"]].describe().T

# %% [markdown]
# **Check against Stata:** 400 clean records; mean of `female` 0.5825, `ewallet_user` 0.7525, `PU` 3.1433, `finlit` 1.8975 —
# identical to the summary at the end of `03_data_cleaning.log`.

# %%
assert len(clean) == 400
assert round(clean["female"].mean(), 4) == 0.5825 and round(clean["ewallet_user"].mean(), 4) == 0.7525
assert round(clean["PU"].mean(), 4) == 3.1433 and round(clean["finlit"].mean(), 4) == 1.8975
print("Matches the Stata results.")
