* =============================================================================
* 04_reliability_validity.do
* Chapter 3: Methodology — E4 Validity and reliability, worked example
* Data : ../data/ewallet_survey_clean.dta  (run 03_data_cleaning.do first)
* Three reflective constructs: perceived usefulness (PU1-PU4), perceived
* security (PS1-PS4) and ease of use (EOU1-EOU3), five-point agreement items.
* Runs on Stata 16 or later with built-in commands only (alpha, factor, sem, Mata).
* =============================================================================
version 16
clear all
set more off
capture log close
global data "../data"

use "$data/ewallet_survey_clean.dta", clear

* --- A. Internal consistency: Cronbach's alpha, item by item ------------------
alpha PU1-PU4, item
alpha PS1-PS4, item
alpha EOU1-EOU3, item
* standardised alpha = k r / (1 + (k-1) r), r = average inter-item correlation
alpha PU1-PU4, std

* --- B. Exploratory factor analysis: do the 11 items form three factors? -------
factor PU1-PU4 PS1-PS4 EOU1-EOU3, ml factors(3)
rotate, promax
estat kmo

* --- C. Composite reliability (omega) and AVE, one construct at a time -----------
* Standardised loadings from a one-factor CFA per construct:
*   CR (= omega) = (sum L)^2 / [(sum L)^2 + sum(1 - L^2)],   AVE = mean(L^2)
capture program drop crave
program define crave, rclass
    syntax varlist
    quietly sem (F -> `varlist'), latent(F) nocapslatent standardized
    matrix T = r(table)
    local sumL = 0
    local sumL2 = 0
    local k : word count `varlist'
    foreach v of local varlist {
        local L = T[1, colnumb(T, "`v':F")]
        local sumL  = `sumL' + `L'
        local sumL2 = `sumL2' + `L'^2
        display as text "  loading `v' = " as result %5.3f `L'
    }
    return scalar cr  = `sumL'^2 / (`sumL'^2 + (`k' - `sumL2'))
    return scalar ave = `sumL2' / `k'
end
foreach c in PU PS EOU {
    display as text _n "`c'"
    if "`c'" == "EOU" crave EOU1-EOU3
    else crave `c'1-`c'4
    display as text "  CR (omega) = " as result %5.3f r(cr) as text "   AVE = " as result %5.3f r(ave) ///
            as text "   sqrt(AVE) = " as result %5.3f sqrt(r(ave))
    scalar ave_`c' = r(ave)
}

* the same for one construct, as shown in E4 on the dashboard
crave PU1-PU4
display "CR = " r(cr) "   AVE = " r(ave)

* --- D. Discriminant validity 1: Fornell–Larcker (joint three-factor CFA) ----------
* item names start with capitals, so declare the latent variables and switch off
* Stata's "capitalised = latent" convention
sem (Usefulness -> PU1-PU4) (Security -> PS1-PS4) (EaseOfUse -> EOU1-EOU3), ///
    latent(Usefulness Security EaseOfUse) nocapslatent standardized nolog
estat framework, standardized
* Compare each sqrt(AVE) above with the factor correlations shown in the
* "Covariance of exogenous variables" block: sqrt(AVE) should be larger.

* --- E. Discriminant validity 2: HTMT (Henseler, Ringle & Sarstedt, 2015) ----------
* HTMT(i,j) = mean heterotrait correlation / sqrt(mean monotrait_i x mean monotrait_j)
quietly correlate PU1-PU4 PS1-PS4 EOU1-EOU3
matrix R = r(C)
mata:
    R = st_matrix("R")
    blocks = (1, 4 \ 5, 8 \ 9, 11)
    names = ("PU", "PS", "EOU")
    function mono(R, a, b) {
        S = R[|a, a \ b, b|]
        k = b - a + 1
        return((sum(S) - k) / (k * (k - 1)))
    }
    for (i = 1; i <= 3; i++) {
        for (j = i + 1; j <= 3; j++) {
            H = R[|blocks[i,1], blocks[j,1] \ blocks[i,2], blocks[j,2]|]
            htmt = mean(vec(H)) / sqrt(mono(R, blocks[i,1], blocks[i,2]) * mono(R, blocks[j,1], blocks[j,2]))
            printf("HTMT %s-%s = %5.3f\n", names[i], names[j], htmt)
        }
    }
end

* --- F. Attenuation: why reliability matters for your regression ---------------------
* With reliability ratio 0.70, a true slope of 0.50 is estimated near 0.35.
display as result "plim b = 0.50 x 0.70 = " 0.50 * 0.70
