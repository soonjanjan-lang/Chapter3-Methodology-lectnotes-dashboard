* =============================================================================
* 02_sample_size.do
* Chapter 3: Methodology — D4 How many respondents do we need?
* Reproduces the Krejcie & Morgan (1970) table, shows how the margin of error
* changes the answer, and runs a priori power analyses with Stata's power command.
* Runs on Stata 16 or later with built-in commands only.
* =============================================================================
version 16
clear all
set more off
capture log close

* --- A. Krejcie & Morgan (1970): s = X2 N P(1-P) / [d2 (N-1) + X2 P(1-P)] ------
capture program drop kmsize
program define kmsize, rclass
    syntax , N(real) [d(real 0.05) P(real 0.5) Level(real 95)]
    local chi2 = invchi2(1, `level'/100)                  // 3.841 at 95%
    return scalar s = (`chi2' * `n' * `p' * (1 - `p')) / (`d'^2 * (`n' - 1) + `chi2' * `p' * (1 - `p'))
end

display as text _n "Population N   exact s   table value"
foreach N in 100 1000 9000 10000 50000 1000000 {
    kmsize, n(`N')
    display as result %12.0fc `N' %10.2f r(s) %12.0f round(r(s))
}

* --- B. The margin of error changes the answer more than the population does -----
display as text _n "N = 10,000: margin of error and required n (rounded up)"
foreach d in 0.03 0.05 0.10 {
    kmsize, n(10000) d(`d')
    display as result "d = " %4.2f `d' "   n = " %5.0f ceil(r(s))
}

* --- C. Infinite population: n = z2 P(1-P) / d2 -----------------------------------
display as result "n0 = " %6.2f invnormal(0.975)^2 * 0.25 / 0.05^2

* --- D. Inflate for non-response and for a cluster design ---------------------------
display as result "Invite " ceil(370 / 0.60) " people to obtain 370 responses at a 60% response rate"
local deff = 1 + (20 - 1) * 0.025                   // 20 students per class, ICC = 0.025
display as result "Design effect = " %4.2f `deff' "; effective n of 384 = " %5.1f 384 / `deff'

* --- E. Power: two groups of 185 (n = 370 split equally), alpha = 0.05 ------------
power twomeans 0 0.2, sd(1) n1(185) n2(185)
power twomeans 0 0.3, sd(1) n1(185) n2(185)
power twomeans 0 0.5, sd(1) n1(185) n2(185)
* sample size per group for 80% power to detect d = 0.2
power twomeans 0 0.2, sd(1) power(0.8)

* --- F. Power for multiple regression: f2 = 0.15 (medium), 5 predictors --------------
* f2 = R2 / (1 - R2), so R2 = 0.15 / 1.15
power rsquared `=0.15/1.15', ntested(5) power(0.8)
* Testing ONE coefficient (e.g. financial literacy) with 7 controls, partial f2 = 0.02 (small)
power rsquared `=0.10' `=0.10 + 0.02*(1 - 0.10)/(1 + 0.02)', ncontrol(7) ntested(1) power(0.8)

* --- G. Worked example in D4: the e-wallet survey ----------------------------------
* Krejcie & Morgan for N = 10,000 (program defined in the do-file)
kmsize, n(10000)
display round(r(s))                                   // 370

* power for one tested coefficient with 7 controls, small partial f2 = 0.02
power rsquared `=0.10' `=0.10 + 0.02*(1 - 0.10)/(1 + 0.02)', ncontrol(7) ntested(1) power(0.8)   // N = 395

display ceil(395 / 0.60)                              // invitations: 659
