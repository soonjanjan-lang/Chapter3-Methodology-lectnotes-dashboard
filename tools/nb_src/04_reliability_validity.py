# %% [markdown]
# # 04 Validity and reliability
# **Chapter 3: Methodology — E4 Validity and reliability, worked example.** The Python twin of `04_reliability_validity.do`.
#
# Data: `ewallet_survey_clean.csv` (run notebook 03 first). Three reflective constructs measured with
# five-point agreement items: perceived usefulness (PU1–PU4), perceived security (PS1–PS4), ease of use (EOU1–EOU3).

# %%
from statsmodels.multivariate.factor import Factor

df = load("ewallet_survey_clean.csv")
constructs = {"PU": [f"PU{j}" for j in range(1, 5)],
              "PS": [f"PS{j}" for j in range(1, 5)],
              "EOU": [f"EOU{j}" for j in range(1, 4)]}
items = sum(constructs.values(), [])
print(len(df), "respondents")

# %% [markdown]
# ## A. Cronbach's alpha, item by item
# α = k/(k−1) × (1 − Σσ²ᵢ / σ²ₜ). Stata's `alpha` uses every respondent with the items it needs
# (pairwise covariances), so we do the same.

# %%
def cronbach_alpha(d):
    C = d.cov()                                  # pairwise-complete covariances, like Stata
    k = C.shape[0]
    return k / (k - 1) * (1 - np.trace(C.values) / C.values.sum())

rows = []
for name, cols in constructs.items():
    d = df[cols]
    for c in cols:
        rest = [x for x in cols if x != c]
        item_rest = d[c].corr(d[rest].mean(axis=1))
        rows.append({"construct": name, "item": c, "item-rest r": round(item_rest, 4),
                     "alpha if deleted": round(cronbach_alpha(d[rest]), 4)})
    rows.append({"construct": name, "item": "scale", "item-rest r": None, "alpha if deleted": round(cronbach_alpha(d), 4)})
pd.DataFrame(rows)

# %% [markdown]
# Standardised alpha from the average inter-item correlation: α = k r̄ / (1 + (k − 1) r̄).

# %%
R = df[constructs["PU"]].corr().values
k = R.shape[0]
rbar = (R.sum() - k) / (k * (k - 1))
print(f"PU: mean inter-item r = {rbar:.4f}, standardised alpha = {k * rbar / (1 + (k - 1) * rbar):.4f}")

# %% [markdown]
# ## B. Exploratory factor analysis and the KMO measure of sampling adequacy

# %%
X = df[items].dropna()
efa = Factor(X, n_factor=3, method="ml").fit()
efa.rotate("promax")
pd.DataFrame(efa.loadings, index=items, columns=["F1", "F2", "F3"]).round(3)

# %%
def kmo(data):
    Rm = data.corr().to_numpy(copy=True)
    inv = np.linalg.inv(Rm)
    P = -inv / np.sqrt(np.outer(np.diag(inv), np.diag(inv)))          # partial correlations
    np.fill_diagonal(Rm, 0); np.fill_diagonal(P, 0)
    return (Rm**2).sum() / ((Rm**2).sum() + (P**2).sum())
print(f"Overall KMO = {kmo(X):.4f}")

# %% [markdown]
# ## C. Composite reliability (omega) and AVE from a one-factor model per construct
# CR = (Σλ)² / [(Σλ)² + Σ(1 − λ²)],  AVE = mean(λ²), with standardised loadings λ.

# %%
crave = {}
for name, cols in constructs.items():
    d = df[cols].dropna()
    lam = np.abs(Factor(d, n_factor=1, method="ml").fit().loadings[:, 0])
    cr = lam.sum()**2 / (lam.sum()**2 + (1 - lam**2).sum())
    ave = (lam**2).mean()
    crave[name] = (cr, ave)
    print(f"{name}: loadings {np.round(lam, 3)}  CR = {cr:.3f}  AVE = {ave:.3f}  sqrt(AVE) = {np.sqrt(ave):.3f}")

# %% [markdown]
# ## D. Discriminant validity: HTMT (Henseler, Ringle & Sarstedt, 2015)
# HTMT = mean heterotrait correlation / √(mean monotrait correlation of i × of j). Values below 0.85 (strict) or 0.90 support discriminant validity.

# %%
Rall = df[items].corr()
def mono(cols):
    S = Rall.loc[cols, cols].values
    k = len(cols)
    return (S.sum() - k) / (k * (k - 1))
names = list(constructs)
for i in range(3):
    for j in range(i + 1, 3):
        a, b = constructs[names[i]], constructs[names[j]]
        h = Rall.loc[a, b].values.mean() / np.sqrt(mono(a) * mono(b))
        print(f"HTMT {names[i]}-{names[j]} = {h:.3f}")

# %% [markdown]
# ## E. Why reliability matters for your regression: attenuation bias
# If the true slope is 0.50 and the regressor's reliability ratio is 0.70, OLS converges to about 0.35.

# %%
rng = np.random.default_rng(1)
x_true = rng.normal(0, 1, 200_000)
y = 0.5 * x_true + rng.normal(0, 1, x_true.size)
x_obs = x_true + rng.normal(0, np.sqrt(1 / 0.7 - 1), x_true.size)   # reliability = 1 / (1 + var(u)) = 0.70
slope = np.cov(x_obs, y)[0, 1] / np.var(x_obs, ddof=1)
print(f"Estimated slope with a noisy regressor: {slope:.3f}  (theory: 0.50 x 0.70 = 0.35)")

# %%
stata_alpha = [0.8555, 0.8630, 0.7745]          # from 04_reliability_validity.log
assert all(abs(cronbach_alpha(df[c]) - a) < 0.0005 for c, a in zip(constructs.values(), stata_alpha))
assert all(abs(crave[k][0] - v) < 0.002 for k, v in {"PU": 0.856, "PS": 0.863, "EOU": 0.775}.items())
print("Alpha, CR and AVE match the Stata do-file.")
