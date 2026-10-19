# %% [markdown]
# # 05 Data structures and how the model is written
# **Chapter 3: Methodology — C2 Data structures.** The Python twin of `05_data_structures.do`.
#
# | Structure | Subscript | Example here |
# |---|---|---|
# | Cross-section | $y_i$ | 22 students, one semester |
# | Time series | $y_t$ | one economy, 2000–2023 |
# | Pooled cross-sections | $y_{it}$, new $i$ each $t$ | houses sold in 1978 and 1981 (simulated) |
# | Panel | $y_{it}$, same $i$ every $t$ | 13 states, 2012–2022 (simulated) |

# %%
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS, RandomEffects
from scipy import stats

# %% [markdown]
# ## 1. Cross-section: $Score_i = \beta_0 + \beta_1 StudyHours_i + \dots + u_i$

# %%
cs = load("ds_crosssection_students.csv")
cs["female"] = (cs["Gender"] == "Female").astype(int)
m1 = smf.ols("Final_Score ~ Study_Hours + Attendance + Sleep_Hours + PT_Job + HH_Income_k + female", cs).fit(cov_type="HC1")
print(m1.summary().tables[1])

# %% [markdown]
# ## 2. Time series: $Inflation_t = \beta_0 + \beta_1 Unemployment_t + \beta_2 Inflation_{t-1} + u_t$

# %%
ts = load("ds_timeseries_macro.csv").set_index("Year")
ts["Inflation_lag1"] = ts["Inflation"].shift(1)
m2 = smf.ols("Inflation ~ Unemployment + Inflation_lag1", ts.dropna()).fit()
m2_nw = smf.ols("Inflation ~ Unemployment + Inflation_lag1", ts.dropna()).fit(cov_type="HAC", cov_kwds={"maxlags": 2})
print(pd.DataFrame({"b": m2.params, "OLS se": m2.bse, "Newey-West se": m2_nw.bse}).round(4))
ts["gdp_growth"] = 100 * np.log(ts["GDP_USDb"]).diff()
print(ts["gdp_growth"].describe().round(2))

# %% [markdown]
# ## 3. Pooled cross-sections: difference-in-differences
# $price_i = \beta_0 + \delta_0\, y81_i + \beta_1\, nearinc_i + \delta_1 (y81_i \times nearinc_i) + \text{controls} + u_i$ — the simulated true $\delta_1$ is −11,500.

# %%
pool = load("pooled_incinerator_sim.csv")
m3 = smf.ols("price ~ y81 * nearinc", pool).fit(cov_type="HC1")
m3c = smf.ols("price ~ y81 * nearinc + age + rooms + area", pool).fit(cov_type="HC1")
print(pd.DataFrame({"no controls": m3.params, "with controls": m3c.params}).round(1))
means = pool.pivot_table(index="nearinc", columns="y81", values="price", aggfunc="mean")
print(means.round(0))
print("DiD from the four means:", round((means.loc[1, 1] - means.loc[1, 0]) - (means.loc[0, 1] - means.loc[0, 0]), 2))

# %% [markdown]
# ## 4. Panel: $saving_{it} = \beta_1 finlit_{it} + \beta_2 income_{it} + a_i + \lambda_t + u_{it}$ (true $\beta_1 = 0.15$)

# %%
pan = load("panel_states_sim.csv")
pan["covid"] = (pan["year"] == 2020).astype(int)
pan["trend"] = pan["year"]
panel = pan.set_index(["state", "year"])
pooled = smf.ols("saving_rate ~ finlit_index + income_k + C(year)", pan).fit(
    cov_type="cluster", cov_kwds={"groups": pd.factorize(pan["state"])[0]})
# the model you would report: state and year fixed effects, state-clustered standard errors
fe = PanelOLS.from_formula("saving_rate ~ finlit_index + income_k + EntityEffects + TimeEffects", panel).fit(
    cov_type="clustered", cluster_entity=True)
print(pd.DataFrame({"pooled OLS": pooled.params[["finlit_index", "income_k"]], "fixed effects": fe.params,
                    "FE clustered se": fe.std_errors}).round(4))

# %% [markdown]
# ### Fixed or random effects? The Hausman test
# With only 13 states, the comparison uses a linear trend and a 2020 dummy instead of 10 year dummies so that
# random effects is identified (the do-file does the same). H = (b_FE − b_RE)' [V_FE − V_RE]⁻¹ (b_FE − b_RE).

# %%
f = "saving_rate ~ finlit_index + income_k + trend + covid"
fe_h = PanelOLS.from_formula(f + " + EntityEffects", panel).fit()
re_h = RandomEffects.from_formula(f.replace("~", "~ 1 +"), panel).fit()
cols = ["finlit_index", "income_k", "trend", "covid"]
print(pd.DataFrame({"FE": fe_h.params[cols], "RE": re_h.params[cols]}).round(4))
b = (fe_h.params[cols] - re_h.params[cols]).values
V = (fe_h.cov.loc[cols, cols] - re_h.cov.loc[cols, cols]).values
H = float(b @ np.linalg.pinv(V) @ b)
print(f"Hausman chi2({len(cols)}) = {H:.2f}, p = {1 - stats.chi2.cdf(H, len(cols)):.4f}  → reject RE: use fixed effects")
print("(Stata's 'sigmamore' option scales the variances slightly differently; the conclusion is the same.)")

# %%
assert abs(m3c.params["y81:nearinc"] - (-11729.18)) < 1
assert abs(fe.params["finlit_index"] - 0.1494) < 0.0005
print("DiD and fixed-effects estimates match the Stata do-file.")
