* =============================================================================
* 05_data_structures.do
* Chapter 3: Methodology — C2 Data structures and how the model is written
* One example per structure, with the subscripts that go with it:
*   cross-section  y_i      time series  y_t      pooled  y_it (new i each t)     panel  y_it
* Runs on Stata 16 or later with built-in commands only.
* =============================================================================
version 16
clear all
set more off
capture log close
global data "../data"

* --- 1. Cross-section: many students, one point in time --------------------------
* Final_Score_i = b0 + b1 Study_Hours_i + b2 Attendance_i + b3 Sleep_Hours_i
*                 + b4 PT_Job_i + b5 HH_Income_i + b6 Female_i + u_i
use "$data/ds_crosssection_students.dta", clear
generate byte female = Gender == "Female"
regress Final_Score Study_Hours Attendance Sleep_Hours PT_Job HH_Income_k female, vce(robust)

* --- 2. Time series: one country, many years ----------------------------------------
* Inflation_t = b0 + b1 Unemployment_t + b2 Inflation_(t-1) + u_t
use "$data/ds_timeseries_macro.dta", clear
tsset Year
regress Inflation Unemployment L.Inflation
* serial correlation and heteroskedasticity robust (Newey–West) standard errors
newey Inflation Unemployment L.Inflation, lag(2)
generate gdp_growth = 100 * (ln(GDP_USDb) - ln(L.GDP_USDb))
summarize gdp_growth

* --- 3. Pooled cross-sections: different houses sold in 1978 and 1981 ------------------
* price_i = b0 + d0 y81_i + b1 nearinc_i + d1 (y81_i x nearinc_i) + controls + u_i
* d1 is the difference-in-differences estimate (simulated data, Kiel & McClain design)
use "$data/pooled_incinerator_sim.dta", clear
tabulate year nearinc
regress price i.y81##i.nearinc, vce(robust)
regress price i.y81##i.nearinc age rooms area, vce(robust)
* the same estimate from four group means
tabulate nearinc y81, summarize(price) means

* --- 4. Panel: the same 13 states observed every year, 2012-2022 --------------------------
* saving_it = b1 finlit_it + b2 income_it + a_i + l_t + u_it
use "$data/panel_states_sim.dta", clear
encode state, generate(state_id)
xtset state_id year
xtdescribe
regress saving_rate finlit_index income_k i.year, vce(cluster state_id)     // pooled OLS: ignores a_i
* the model you would report: state and year fixed effects, state-clustered SEs
xtreg saving_rate finlit_index income_k i.year, fe vce(cluster state_id)

* Fixed or random effects? The Hausman test compares the two. With only 13 states,
* use a linear trend and a 2020 dummy instead of 10 year dummies so that RE is identified.
generate byte covid = year == 2020
xtreg saving_rate finlit_index income_k year covid, fe
estimates store FE
xtreg saving_rate finlit_index income_k year covid, re
estimates store RE
hausman FE RE, sigmamore

* --- 5. The two small tables from the lecture notes -------------------------------------
use "$data/ds_pooled_crosssection.dta", clear
tabulate Year
use "$data/ds_panel_countries.dta", clear
encode Country, generate(cid)
xtset cid Year
xtdescribe
