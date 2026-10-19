# %% [markdown]
# # 06 Model specification
# **Chapter 3: Methodology — B4 Model specification, worked example.** The Python twin of `06_model_specification.do`.
#
# One research question per model, matching the RQ–method table in B2:
#
# | RQ | Outcome | Level | Model |
# |---|---|---|---|
# | RQ1 Who uses e-wallets? | `ewallet_user` | binary | logit (LPM for comparison) |
# | RQ2 How often do users use them? | `ewallet_days` 0–7 | count / ratio | OLS among users |
# | RQ3 Who intends to keep using them? | `intention` 1–5 | ordinal | ordered logit |

# %%
import statsmodels.formula.api as smf
from statsmodels.miscmodels.ordinal_model import OrderedModel

df = load("ewallet_survey_clean.csv")
X = "PU + PS + EOU + finlit + female + ln_allow + urban"
df[["ewallet_user", "ewallet_days", "intention", "PU", "PS", "EOU", "finlit", "female", "ln_allow", "urban"]].describe().T.round(3)

# %% [markdown]
# ## RQ1: binary outcome
# $\Pr(user_i = 1 \mid x_i) = \Lambda(\beta_0 + \beta_1 PU_i + \dots + \beta_7 urban_i)$

# %%
lpm = smf.ols(f"ewallet_user ~ {X}", df).fit(cov_type="HC1")
logit = smf.logit(f"ewallet_user ~ {X}", df).fit(disp=False, cov_type="HC1")
print(pd.DataFrame({"LPM b": lpm.params, "logit b": logit.params, "logit se": logit.bse}).round(3))
print("N =", int(logit.nobs))
print(logit.get_margeff(at="overall").summary_frame().round(4))

# %% [markdown]
# ## RQ2: days of use in the past week, users only

# %%
ols_days = smf.ols(f"ewallet_days ~ {X} + C(year_study)", df[df["ewallet_user"] == 1]).fit(cov_type="HC1")
print(ols_days.summary().tables[1])

# %% [markdown]
# ## RQ3: ordinal outcome — ordered logit
# $intention^*_i = x_i'\beta + \varepsilon_i$, and $intention_i = j$ if $\kappa_{j-1} < intention^*_i \le \kappa_j$

# %%
d3 = df.dropna(subset=["intention", "PU", "PS", "EOU", "finlit", "female", "ln_allow", "urban"])
ologit = OrderedModel(d3["intention"].astype(int), d3[["PU", "PS", "EOU", "finlit", "female", "ln_allow", "urban"]],
                      distr="logit").fit(method="bfgs", disp=False)
print(ologit.params.round(3))

# %%
assert int(logit.nobs) == 394
assert abs(logit.params["PU"] - 0.874) < 0.001 and abs(lpm.params["PU"] - 0.128) < 0.001
print("Logit and LPM coefficients match the Stata do-file.")
