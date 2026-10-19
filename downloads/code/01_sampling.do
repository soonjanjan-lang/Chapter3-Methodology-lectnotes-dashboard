* =============================================================================
* 01_sampling.do
* Chapter 3: Methodology — D2 Probability sampling, worked examples
* Frame : ../data/sme_sampling_frame.dta  (hypothetical list of 2,400 SMEs)
* Draws a simple random, a systematic and two stratified random samples of n = 331
* (the Krejcie–Morgan size for N = 2,400), and reproduces Sekaran & Bougie's Table 13.1.
* Runs on Stata 16 or later with built-in commands only.
* Before running: cd to the folder holding this file.
* =============================================================================
version 16
clear all
set more off
capture log close
global data "../data"
set seed 20261019                         // makes every draw reproducible: report it

use "$data/sme_sampling_frame.dta", clear
count                                     // N = 2,400
tabulate sector

* --- A. Simple random sampling (without replacement) ------------------------
* Method 1: Stata's sample command
preserve
sample 331, count
count
tabulate sector
restore

* Method 2: give every unit a random number, sort, take the first n
* (easy to document in Chapter 3 and to audit)
generate double u = runiform()
sort u
generate byte in_srs = _n <= 331
tabulate sector in_srs, column nofreq
drop u

* --- B. Systematic random sampling ------------------------------------------
sort sme_id
local N = _N
local n = 331
local k = floor(`N' / `n')                // sampling interval
local start = runiformint(1, `k')         // random start between 1 and k
display as text "Interval k = `k'; random start = `start'"
generate byte in_sys = (_n >= `start') & mod(_n - `start', `k') == 0
count if in_sys
* k = 7 gives 342 units; take the first 331 so n matches the other designs
generate long cum_sys = sum(in_sys)
replace in_sys = 0 if cum_sys > `n'
count if in_sys
tabulate sector if in_sys
drop cum_sys

* --- C. Stratified random sampling: proportionate allocation -----------------
bysort sector: generate N_h = _N
generate n_prop = round(`n' * N_h / `N')
tabstat N_h n_prop, by(sector) statistics(mean) nototal format(%9.0f)
generate double u = runiform()
bysort sector (u): generate byte in_prop = _n <= n_prop
tabulate sector in_prop

* --- D. Stratified random sampling: disproportionate allocation --------------
* At least 60 firms in every sector so each can be analysed on its own
generate n_dis = 141 if sector == "Services"
replace  n_dis =  70 if sector == "Manufacturing"
replace  n_dis =  60 if inlist(sector, "Agriculture", "Construction")
drop u
generate double u = runiform()
bysort sector (u): generate byte in_dis = _n <= n_dis
tabulate sector in_dis

* Design weights undo the over-sampling when estimating for all SMEs
generate double w_dis = N_h / n_dis
summarize uses_ewallet_payments                                        // population value
mean uses_ewallet_payments if in_dis                                  // unweighted: biased
mean uses_ewallet_payments [pweight = w_dis] if in_dis                // weighted: unbiased

* --- E. Sekaran & Bougie (2016, Table 13.1): job levels in one organisation ---
clear
input str24 job_level N_h n_disproportionate
"Top management"          10   7
"Middle-level management" 30  15
"Lower-level management"  50  20
"Supervisors"            100  30
"Clerks"                 500  60
"Secretaries"             20  10
end
generate n_proportionate = 0.20 * N_h                // 20% of every stratum
list, noobs abbreviate(20)
tabstat N_h n_proportionate n_disproportionate, statistics(sum) format(%9.0f)
