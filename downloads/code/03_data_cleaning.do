* =============================================================================
* 03_data_cleaning.do
* Chapter 3: Methodology — C5 Data cleaning, worked example
* Raw file : ../data/ewallet_survey_raw.csv  (hypothetical survey of 414 records)
* Output   : ../data/ewallet_survey_clean.dta
* Runs on Stata 16 or later with built-in commands only.
* Before running: set Stata's working directory to the folder holding this file,
*   e.g.  cd "C:/Users/you/Downloads/Chapter3-Methodology/downloads/code"
* =============================================================================
version 16
clear all
set more off
capture log close
global data "../data"

import delimited using "$data/ewallet_survey_raw.csv", clear varnames(1) case(preserve)
display as text "Raw records: " _N

* --- 1. Inspect structure ----------------------------------------------------
describe, short
codebook gender state, compact
summarize age allowance_rm ewallet_days PU1-EOU3 intention

* --- 2. Duplicates ------------------------------------------------------------
duplicates report resp_id
duplicates report                         // identical on every variable?
duplicates drop
display as text "After dropping exact duplicates: " _N

* --- 3. Incomplete questionnaires (break-offs) ---------------------------------
egen n_missing = rowmiss(PU1-PU4 PS1-PS4 EOU1-EOU3 intention finlit1-finlit3)
tabulate n_missing if n_missing > 0
drop if n_missing >= 8                    // fewer than half of the 15 scale items answered
drop n_missing
display as text "After dropping break-offs: " _N

* --- 4. Missing-value codes → Stata missing ------------------------------------
mvdecode age, mv(999)
mvdecode allowance_rm PU1-PU4 PS1-PS4 EOU1-EOU3 intention, mv(-9)

* --- 5. Out-of-range and implausible values ------------------------------------
foreach v of varlist PU1-PU4 PS1-PS4 EOU1-EOU3 intention {
    quietly count if !inrange(`v', 1, 5) & !missing(`v')
    if r(N) > 0 display as text "`v': " r(N) " out-of-range value(s) set to missing"
    quietly replace `v' = . if !inrange(`v', 1, 5)
}
list resp_id age if !inrange(age, 17, 40) & !missing(age), noobs
replace age = . if !inrange(age, 17, 40)
list resp_id allowance_rm if allowance_rm > 10000 & !missing(allowance_rm), noobs
replace allowance_rm = . if allowance_rm > 10000

* --- 6. Inconsistent text coding -----------------------------------------------
tabulate gender, missing
generate byte female = .
replace female = 1 if inlist(lower(strtrim(gender)), "f", "female")
replace female = 0 if inlist(lower(strtrim(gender)), "m", "male")
tabulate gender female, missing
replace state = proper(strtrim(state))
tabulate state, missing

* --- 7. Logical consistency (skip pattern) -------------------------------------
count if ewallet_days > 7 & !missing(ewallet_days)
replace ewallet_days = . if ewallet_days > 7
count if ewallet_user == 0 & ewallet_days > 0 & !missing(ewallet_days)
replace ewallet_days = . if ewallet_user == 0 & ewallet_days > 0

* --- 8. Generate analysis variables ---------------------------------------------
egen PU  = rowmean(PU1-PU4)
egen PS  = rowmean(PS1-PS4)
egen EOU = rowmean(EOU1-EOU3)
egen finlit = rowtotal(finlit1-finlit3), missing
generate ln_allow = ln(allowance_rm)
encode faculty, generate(fac)
generate byte urban = hometown_urban

label variable female   "Female (1 = yes)"
label variable PU       "Perceived usefulness, mean of PU1-PU4 (1-5)"
label variable PS       "Perceived security, mean of PS1-PS4 (1-5)"
label variable EOU      "Ease of use, mean of EOU1-EOU3 (1-5)"
label variable finlit   "Financial literacy score, correct answers (0-3)"
label variable ln_allow "Log monthly allowance (RM)"
label variable urban    "Urban hometown (1 = yes)"
label define yesno 0 "No" 1 "Yes"
label values female urban ewallet_user yesno

* the codebook as Stata sees it
describe ewallet_user ewallet_days intention PU PS EOU finlit female ln_allow urban
codebook female ewallet_user, compact

* --- 9. Save raw and clean separately (never overwrite the raw file) -------------
drop gender hometown_urban
order resp_id faculty fac year_study female age state urban allowance_rm ln_allow ///
      ewallet_user ewallet_days ewallet_spend_rm PU PS EOU finlit intention satisfaction
compress
display as text "Clean records: " _N
summarize female age allowance_rm ewallet_user PU PS EOU finlit
save "$data/ewallet_survey_clean.dta", replace
