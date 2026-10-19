* =============================================================================
* 06_model_specification.do
* Chapter 3: Methodology — B4 Model specification, worked example
* Data : ../data/ewallet_survey_clean.dta  (run 03_data_cleaning.do first)
* One research question per model, matching the RQ–method table in B2:
*   RQ1  Who uses e-wallets?              binary   → logit (and LPM for comparison)
*   RQ2  How often do users use them?     0-7 days → OLS among users
*   RQ3  Who intends to keep using them?  1-5      → ordered logit
* Runs on Stata 16 or later with built-in commands only.
* =============================================================================
version 16
clear all
set more off
capture log close
global data "../data"

use "$data/ewallet_survey_clean.dta", clear
global X "PU PS EOU finlit female ln_allow urban"
summarize ewallet_user ewallet_days intention $X

* --- RQ1: binary outcome --------------------------------------------------------
* Pr(user_i = 1 | x_i) = Lambda(b0 + b1 PU_i + ... + b7 urban_i)
regress ewallet_user $X, vce(robust)                 // linear probability model
estimates store LPM
logit ewallet_user $X, vce(robust) nolog
estimates store LOGIT
margins, dydx(*)                                      // average marginal effects

* --- RQ2: days of use in the past week, users only -----------------------------------
* days_i = b0 + b1 PU_i + ... + b7 urban_i + year-of-study dummies + u_i
regress ewallet_days $X i.year_study if ewallet_user == 1, vce(robust)
estimates store OLS_DAYS

* --- RQ3: ordinal outcome ---------------------------------------------------------
* intention*_i = x_i'b + e_i ;  intention_i = j if cut_(j-1) < intention*_i <= cut_j
ologit intention $X, vce(robust) nolog
estimates store OLOGIT
margins, dydx(PU) predict(outcome(5))                 // effect on Pr(strongly agree)

* --- side by side ---------------------------------------------------------------
estimates table LPM LOGIT OLS_DAYS OLOGIT, b(%7.3f) se(%7.3f) stats(N) varwidth(12)
