# %% [markdown]
# # 01 Probability sampling
# **Chapter 3: Methodology — D2 Probability sampling, worked examples.** The Python twin of `01_sampling.do`.
#
# Frame: `sme_sampling_frame.csv`, a hypothetical list of 2,400 SMEs. We draw samples of n = 331,
# the Krejcie–Morgan size for N = 2,400. Random draws differ from Stata's (different generators),
# but every allocation and every design rule is the same.

# %%
frame = load("sme_sampling_frame.csv")
N, n = len(frame), 331
rng = np.random.default_rng(20261019)     # report the seed in your thesis
print("N =", N)
frame["sector"].value_counts()

# %% [markdown]
# ## A. Simple random sampling (without replacement)

# %%
srs = frame.sample(n=n, random_state=20261019)
print(len(srs))
pd.concat([frame["sector"].value_counts(normalize=True).rename("frame"),
           srs["sector"].value_counts(normalize=True).rename("SRS")], axis=1).round(3)

# %% [markdown]
# ## B. Systematic random sampling
# Interval k = floor(N / n); random start between 1 and k; then every k-th unit of the sorted frame.

# %%
k = N // n
start = int(rng.integers(1, k + 1))
ordered = frame.sort_values("sme_id").reset_index(drop=True)
sys_sample = ordered.iloc[start - 1::k].head(n)          # k = 7 gives 342 or 343; keep the first 331
print(f"k = {k}, random start = {start}, n = {len(sys_sample)}")
sys_sample["sector"].value_counts()

# %% [markdown]
# ## C. Stratified random sampling: proportionate allocation, n_h = n × N_h / N

# %%
alloc = frame.groupby("sector").size().rename("N_h").to_frame()
alloc["n_prop"] = (n * alloc["N_h"] / N).round().astype(int)
print(alloc, "\nTotal:", alloc["n_prop"].sum())
prop = pd.concat([g.sample(n=alloc.loc[s, "n_prop"], random_state=1) for s, g in frame.groupby("sector")])
prop["sector"].value_counts()

# %% [markdown]
# ## D. Disproportionate allocation, with design weights w_h = N_h / n_h

# %%
alloc["n_dis"] = pd.Series({"Services": 141, "Manufacturing": 70, "Agriculture": 60, "Construction": 60})
alloc["w"] = alloc["N_h"] / alloc["n_dis"]
print(alloc)
dis = pd.concat([g.sample(n=alloc.loc[s, "n_dis"], random_state=2) for s, g in frame.groupby("sector")])
dis["w"] = dis["sector"].map(alloc["w"])
print("Population share accepting e-wallets:", round(frame["uses_ewallet_payments"].mean(), 4))
print("Unweighted sample estimate:          ", round(dis["uses_ewallet_payments"].mean(), 4))
print("Weighted sample estimate:            ", round(np.average(dis["uses_ewallet_payments"], weights=dis["w"]), 4))

# %% [markdown]
# ## E. Sekaran & Bougie (2016, Table 13.1): proportionate (20%) and disproportionate samples

# %%
sek = pd.DataFrame({
    "job_level": ["Top management", "Middle-level management", "Lower-level management", "Supervisors", "Clerks", "Secretaries"],
    "N_h": [10, 30, 50, 100, 500, 20],
    "n_disproportionate": [7, 15, 20, 30, 60, 10]})
sek["n_proportionate"] = (0.20 * sek["N_h"]).astype(int)
sek.loc["Total"] = ["Total", sek["N_h"].sum(), sek["n_disproportionate"].sum(), sek["n_proportionate"].sum()]
sek

# %%
assert alloc["n_prop"].tolist() == [33, 17, 66, 215] and alloc["n_prop"].sum() == 331
assert sek.loc["Total", "n_proportionate"] == 142 == sek.loc["Total", "n_disproportionate"]
print("Allocations match the Stata do-file and Table 13.1.")
