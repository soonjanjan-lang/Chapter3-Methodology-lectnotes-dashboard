/* ==========================================================================
   Calculators and simulators.
   A small statistics core (normal quantile, regularized incomplete beta,
   central and noncentral F) reproduces G*Power / Stata `power` results:
   e.g. N = 92 for f2 = 0.15 with 5 predictors; 394 per group for d = 0.2.
   ========================================================================== */
(function () {
  'use strict';
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function fmt(x, d) { return Number(x).toLocaleString('en-GB', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }

  /* ---- statistics core ---------------------------------------------------- */
  var S = {};
  // inverse standard normal CDF (Acklam's rational approximation, |error| < 1.2e-9)
  S.qnorm = function (p) {
    var a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00];
    var b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01];
    var c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00];
    var d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00];
    var pl = 0.02425, q, r;
    if (p < pl) { q = Math.sqrt(-2 * Math.log(p)); return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
    if (p > 1 - pl) { q = Math.sqrt(-2 * Math.log(1 - p)); return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
    q = p - 0.5; r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  };
  // log gamma (Lanczos)
  S.lgamma = function (x) {
    var g = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5];
    var y = x, tmp = x + 5.5, ser = 1.000000000190015;
    tmp -= (x + 0.5) * Math.log(tmp);
    for (var j = 0; j < 6; j++) ser += g[j] / ++y;
    return -tmp + Math.log(2.5066282746310005 * ser / x);
  };
  function betacf(a, b, x) {
    var MAXIT = 400, EPS = 3e-14, FPMIN = 1e-300;
    var qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    d = 1 / d;
    var h = d;
    for (var m = 1; m <= MAXIT; m++) {
      var m2 = 2 * m, aa = m * (b - m) * x / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
      c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1 / d; h *= d * c;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
      c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1 / d;
      var del = d * c; h *= del;
      if (Math.abs(del - 1) < EPS) break;
    }
    return h;
  }
  // regularized incomplete beta I_x(a, b)
  S.ibeta = function (x, a, b) {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    var bt = Math.exp(S.lgamma(a + b) - S.lgamma(a) - S.lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    if (x < (a + 1) / (a + b + 2)) return bt * betacf(a, b, x) / a;
    return 1 - bt * betacf(b, a, 1 - x) / b;
  };
  S.pf = function (f, d1, d2) { return f <= 0 ? 0 : S.ibeta(d1 * f / (d1 * f + d2), d1 / 2, d2 / 2); };
  S.qf = function (p, d1, d2) {
    var lo = 0, hi = 1;
    while (S.pf(hi, d1, d2) < p) hi *= 2;
    for (var i = 0; i < 200; i++) { var mid = (lo + hi) / 2; if (S.pf(mid, d1, d2) < p) lo = mid; else hi = mid; }
    return (lo + hi) / 2;
  };
  // noncentral F CDF as a Poisson mixture of central (beta) terms
  S.pncf = function (f, d1, d2, lambda) {
    if (f <= 0) return 0;
    if (lambda <= 0) return S.pf(f, d1, d2);
    var x = d1 * f / (d1 * f + d2), half = lambda / 2;
    var jmax = Math.ceil(half + 12 * Math.sqrt(half) + 30), sum = 0;
    for (var j = 0; j <= jmax; j++) {
      var w = Math.exp(-half + j * Math.log(half) - S.lgamma(j + 1));
      if (w < 1e-16 && j > half) break;
      sum += w * S.ibeta(x, d1 / 2 + j, d2 / 2);
    }
    return Math.min(1, sum);
  };
  // power of an F test with numerator df u, denominator df v, noncentrality lambda
  S.powerF = function (u, v, lambda, alpha) {
    var crit = S.qf(1 - alpha, u, v);
    return 1 - S.pncf(crit, u, v, lambda);
  };
  // smallest integer n in [lo, hi] with fn(n) >= target (fn increasing)
  S.searchN = function (fn, target, lo, hi) {
    while (fn(hi) < target) { lo = hi; hi *= 2; if (hi > 1e6) return NaN; }
    while (hi - lo > 1) { var mid = Math.floor((lo + hi) / 2); if (fn(mid) >= target) hi = mid; else lo = mid; }
    return hi;
  };
  // two-sample t-test (equal groups of n): power via F(1, 2n-2, d^2 n / 2)
  S.powerT = function (d, n, alpha) { return S.powerF(1, 2 * n - 2, d * d * n / 2, alpha); };
  // multiple regression (G*Power convention): lambda = f2 * N, df = (u, N - u - controls - 1)
  S.powerReg = function (f2, u, controls, N, alpha) {
    var v = N - u - controls - 1;
    return v < 1 ? 0 : S.powerF(u, v, f2 * N, alpha);
  };
  // Krejcie & Morgan / Cochran with finite-population correction
  S.km = function (N, d, P, conf) {
    // Krejcie and Morgan used the tabled value 3.841 at 95%; keep it so their table is reproduced exactly
    var z = S.qnorm((1 + conf) / 2), chi2 = Math.abs(conf - 0.95) < 1e-9 ? 3.841 : z * z;
    if (!N || !isFinite(N)) return chi2 * P * (1 - P) / (d * d);
    return chi2 * N * P * (1 - P) / (d * d * (N - 1) + chi2 * P * (1 - P));
  };
  window.Ch3 = window.Ch3 || {};
  window.Ch3.stats = S;

  /* ---- sampling simulator -------------------------------------------------- */
  function initSim(box) {
    var grid = $('.frame-grid', box);
    if (!grid || grid.childElementCount) return;
    // a fixed, interleaved frame: 130 services (1), 40 manufacturing (2), 30 agriculture (3)
    var strata = [];
    for (var i = 0; i < 200; i++) strata.push(i < 130 ? 1 : (i < 170 ? 2 : 3));
    var seed = 20261019;
    function rnd() { seed |= 0; seed = seed + 0x6D2B79F5 | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }
    for (var j = strata.length - 1; j > 0; j--) { var r = Math.floor(rnd() * (j + 1)); var tmp = strata[j]; strata[j] = strata[r]; strata[r] = tmp; }
    var units = strata.map(function (s, k) {
      var u = document.createElement('span');
      u.className = 'u'; u.setAttribute('data-stratum', s); u.title = 'Unit ' + (k + 1);
      grid.appendChild(u); return u;
    });
    var names = { 1: 'Services', 2: 'Manufacturing', 3: 'Agriculture' };
    var log = $('.sim-log', box), nIn = $('#sim-n', box);

    function pickRandom(arr, m) {
      var a = arr.slice();
      for (var i = a.length - 1; i > 0; i--) { var r = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[r]; a[r] = t; }
      return a.slice(0, m);
    }
    function show(idx, label) {
      units.forEach(function (u) { u.classList.remove('is-picked'); u.style.transitionDelay = ''; });
      idx.sort(function (a, b) { return a - b; }).forEach(function (k, n) {
        if (!reduceMotion) units[k].style.transitionDelay = Math.min(n * 18, 600) + 'ms';
        units[k].classList.add('is-picked');
      });
      var c = { 1: 0, 2: 0, 3: 0 };
      idx.forEach(function (k) { c[strata[k]]++; });
      log.textContent = label + ': ' + idx.length + ' units: ' + names[1] + ' ' + c[1] + ', ' + names[2] + ' ' + c[2] + ', ' + names[3] + ' ' + c[3] + '.';
    }
    box.addEventListener('click', function (e) {
      var b = e.target.closest('[data-draw]');
      if (!b) return;
      var n = Math.max(5, Math.min(100, parseInt(nIn.value, 10) || 20));
      nIn.value = n;
      var all = units.map(function (_, k) { return k; });
      var kind = b.getAttribute('data-draw');
      if (kind === 'clear') { units.forEach(function (u) { u.classList.remove('is-picked'); }); log.textContent = ''; return; }
      if (kind === 'srs') show(pickRandom(all, n), 'Simple random');
      if (kind === 'sys') {
        var k = Math.floor(200 / n), start = 1 + Math.floor(Math.random() * k), idx = [];
        for (var p = start - 1; p < 200 && idx.length < n; p += k) idx.push(p);
        show(idx, 'Systematic (k = ' + k + ', random start = ' + start + ')');
      }
      if (kind === 'strat') {
        var Nh = { 1: 130, 2: 40, 3: 30 }, alloc = largestRemainder([130, 40, 30], n), idx2 = [];
        [1, 2, 3].forEach(function (s, i) {
          idx2 = idx2.concat(pickRandom(all.filter(function (q) { return strata[q] === s; }), alloc[i]));
        });
        show(idx2, 'Stratified, proportionate (' + alloc.join(' / ') + ')');
      }
    });
  }
  function largestRemainder(sizes, n) {
    var N = sizes.reduce(function (a, b) { return a + b; }, 0);
    var raw = sizes.map(function (s) { return N ? n * s / N : 0; });
    var base = raw.map(Math.floor);
    var left = n - base.reduce(function (a, b) { return a + b; }, 0);
    raw.map(function (r, i) { return { i: i, f: r - Math.floor(r) }; })
       .sort(function (a, b) { return b.f - a.f; })
       .slice(0, left).forEach(function (o) { base[o.i]++; });
    return base;
  }

  /* ---- stratified allocation calculator ----------------------------------- */
  function initAlloc(box) {
    function run() {
      var n = parseInt($('#alloc-n', box).value, 10) || 0;
      var rows = $all('tbody tr', box).filter(function (r) { return $('.Nh', r); });
      var Ns = rows.map(function (r) { return Math.max(0, parseFloat($('.Nh', r).value) || 0); });
      var props = largestRemainder(Ns, n);
      var totN = 0, totn = 0;
      rows.forEach(function (r, i) {
        var nh = Math.max(0, parseFloat($('.nh', r).value) || 0);
        $('.prop', r).textContent = fmt(props[i]);
        $('.w', r).textContent = nh > 0 ? fmt(Ns[i] / nh, 2) : '—';
        totN += Ns[i]; totn += nh;
      });
      $('.tot-N', box).textContent = fmt(totN);
      $('.tot-prop', box).textContent = fmt(props.reduce(function (a, b) { return a + b; }, 0));
      $('.tot-n', box).textContent = fmt(totn);
      var note = $('.alloc-note', box);
      var frac = totN ? (100 * n / totN) : 0;
      note.textContent = 'Sampling fraction ' + fmt(frac, 1) + '%. ' +
        (totn !== n ? 'Your allocation sums to ' + fmt(totn) + ', not ' + fmt(n) + '. ' : '') +
        'Proportionate allocation uses n × Nₕ / N, rounded so the total equals n; weights Nₕ/nₕ apply to your own allocation.';
    }
    box.addEventListener('input', run);
    run();
  }

  /* ---- Krejcie–Morgan / Cochran calculator ---------------------------------- */
  var KM_N = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210,
    220, 230, 240, 250, 260, 270, 280, 290, 300, 320, 340, 360, 380, 400, 420, 440, 460, 480, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1100,
    1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2200, 2400, 2600, 2800, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000, 9000, 10000, 15000, 20000, 30000, 40000, 50000, 75000, 1000000];
  window.Ch3.KM_N = KM_N;
  function initKM(box) {
    var tb = $('#km-table tbody', box);
    if (tb && !tb.childElementCount) {
      for (var r = 0; r < 30; r++) {
        var tr = document.createElement('tr');
        [0, 30, 60].forEach(function (off) {
          var N = KM_N[r + off];
          tr.insertAdjacentHTML('beforeend', '<td class="num">' + fmt(N) + '</td><td class="num">' + Math.round(S.km(N, 0.05, 0.5, 0.95)) + '</td>');
        });
        tb.appendChild(tr);
      }
    }
    function run() {
      var Nraw = $('#km-N', box).value.trim(), N = Nraw === '' ? Infinity : Math.max(1, parseFloat(Nraw));
      var conf = parseFloat($('#km-conf', box).value), d = (parseFloat($('#km-d', box).value) || 5) / 100;
      var P = (parseFloat($('#km-P', box).value) || 50) / 100, rr = (parseFloat($('#km-rr', box).value) || 100) / 100;
      var deff = Math.max(1, parseFloat($('#km-deff', box).value) || 1);
      var s = S.km(N, d, P, conf);
      var cons = Math.ceil(s * deff - 1e-9);
      $('#km-out-s', box).textContent = fmt(Math.round(s));
      $('#km-out-ceil', box).textContent = fmt(cons);
      $('#km-out-inv', box).textContent = fmt(Math.ceil(cons / rr - 1e-9));
      $('#km-explain', box).textContent = 'Exact value ' + fmt(s, 2) + ' for ' + (isFinite(N) ? 'N = ' + fmt(N) : 'a very large population') +
        ', ' + Math.round(conf * 100) + '% confidence, ±' + fmt(d * 100, 1) + ' points, P = ' + fmt(P * 100) + '%' +
        (deff > 1 ? '; design effect ' + fmt(deff, 2) : '') + (rr < 1 ? '; ' + fmt(rr * 100) + '% response' : '') +
        '. Valid only for estimating a proportion from a probability sample.';
      drawKM($('#km-chart', box), N, d, P, conf);
    }
    box.addEventListener('input', run);
    box.addEventListener('change', run);
    // redraw when the chart becomes visible or the window changes size
    document.addEventListener('ch3:tab', run);
    document.addEventListener('ch3:subtab', run);
    var t;
    window.addEventListener('resize', function () { clearTimeout(t); t = setTimeout(run, 150); });
    run();
  }
  function drawKM(svg, Ncur, d, P, conf) {
    if (!svg) return;
    // draw at the chart's real pixel width so the 17px labels never scale down
    var W = Math.round(svg.getBoundingClientRect().width) || 640, H = 300, L = 64, R = 18, T = 18, B = 52;
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    var narrow = W < 460;
    var lx = function (N) { return L + (Math.log10(N) - 1) / 5 * (W - L - R); };
    var ymax = Math.max(400, S.km(Infinity, d, P, conf) * 1.12);
    var step = ymax > 2000 ? 1000 : (ymax > 900 ? 200 : 100);
    ymax = Math.ceil(ymax / step) * step;
    var ly = function (v) { return T + (1 - v / ymax) * (H - T - B); };
    var out = ['<g class="grid">'];
    for (var v = 0; v <= ymax; v += step) out.push('<line x1="' + L + '" x2="' + (W - R) + '" y1="' + ly(v) + '" y2="' + ly(v) + '"/>');
    out.push('</g><g class="axis">');
    out.push('<line x1="' + L + '" x2="' + (W - R) + '" y1="' + ly(0) + '" y2="' + ly(0) + '"/>');
    for (var v2 = 0; v2 <= ymax; v2 += step) out.push('<text x="' + (L - 8) + '" y="' + (ly(v2) + 6) + '" text-anchor="end">' + fmt(v2) + '</text>');
    [10, 100, 1000, 10000, 100000, 1000000].forEach(function (N, i) {
      if (narrow && i % 2) return;
      out.push('<text x="' + lx(N) + '" y="' + (H - B + 24) + '" text-anchor="middle">' + ['10', '100', '1k', '10k', '100k', '1m'][i] + '</text>');
    });
    out.push('<text x="' + ((L + W - R) / 2) + '" y="' + (H - 6) + '" text-anchor="middle">Population size N (log scale)</text></g>');
    var pts = [];
    for (var e = 1; e <= 6.0001; e += 0.025) { var N = Math.pow(10, e); pts.push(lx(N).toFixed(1) + ',' + ly(S.km(N, d, P, conf)).toFixed(1)); }
    out.push('<polyline class="series" points="' + pts.join(' ') + '"/>');
    var lim = S.km(Infinity, d, P, conf);
    out.push('<line class="series-2" x1="' + L + '" x2="' + (W - R) + '" y1="' + ly(lim) + '" y2="' + ly(lim) + '"/>');
    out.push('<text x="' + (W - R) + '" y="' + (ly(lim) - 8) + '" text-anchor="end">limit ' + fmt(lim, 1) + '</text>');
    if (isFinite(Ncur) && Ncur >= 10 && Ncur <= 1e6) {
      var sc = S.km(Ncur, d, P, conf);
      out.push('<circle class="marker" cx="' + lx(Ncur) + '" cy="' + ly(sc) + '" r="6"/>');
      var anchor = lx(Ncur) > W - 190 ? 'end' : 'start', dx = anchor === 'end' ? -10 : 10;
      out.push('<text class="marker-label" x="' + (lx(Ncur) + dx) + '" y="' + (ly(sc) + 24) + '" text-anchor="' + anchor + '">N = ' + fmt(Ncur) + ': ' + fmt(Math.round(sc)) + '</text>');
    }
    svg.innerHTML = out.join('');
  }

  /* ---- power: two groups ----------------------------------------------------- */
  function initTT(box) {
    function run() {
      var dEl = $('#tt-d', box), d = parseFloat(dEl.value), n = Math.max(3, parseInt($('#tt-n', box).value, 10) || 3), a = parseFloat($('#tt-a', box).value);
      $('#tt-d-out', box).textContent = d.toFixed(2);
      $('#tt-power', box).textContent = fmt(100 * S.powerT(d, n, a), 1) + '%';
      $('#tt-n80', box).textContent = fmt(S.searchN(function (m) { return S.powerT(d, m, a); }, 0.8, 2, 16));
      $('#tt-n90', box).textContent = fmt(S.searchN(function (m) { return S.powerT(d, m, a); }, 0.9, 2, 16));
    }
    box.addEventListener('input', run);
    box.addEventListener('change', run);
    run();
  }

  /* ---- regression sample size --------------------------------------------- */
  function initReg(box) {
    function run() {
      var f2 = Math.max(0.001, parseFloat($('#rg-f2', box).value) || 0.15);
      var u = Math.max(1, parseInt($('#rg-u', box).value, 10) || 1);
      var c = Math.max(0, parseInt($('#rg-c', box).value, 10) || 0);
      var pw = parseFloat($('#rg-pow', box).value);
      var N = S.searchN(function (m) { return S.powerReg(f2, u, c, m, 0.05); }, pw, u + c + 2, Math.max(16, u + c + 4));
      $('#rg-N', box).textContent = isNaN(N) ? '> 1m' : fmt(N);
      $('#rg-green', box).textContent = fmt(50 + 8 * (u + c));
      $('#rg-explain', box).textContent = 'F test of ' + u + ' tested predictor' + (u > 1 ? 's' : '') + (c ? ' with ' + c + ' control' + (c > 1 ? 's' : '') : '') +
        ', f² = ' + f2 + ', α = 0.05, power ' + pw + '. Green\'s rule ignores effect size, which is why the two can differ widely.';
    }
    box.addEventListener('input', run);
    box.addEventListener('change', run);
    run();
  }

  /* ---- alpha vs number of items ------------------------------------------------ */
  function initAlpha(box) {
    function run() {
      var k = parseInt($('#al-k', box).value, 10), r = parseFloat($('#al-r', box).value);
      var a = k * r / (1 + (k - 1) * r);
      $('#al-k-out', box).textContent = k;
      $('#al-r-out', box).textContent = r.toFixed(2);
      $('#al-out', box).textContent = a.toFixed(3);
      var a4 = 4 * r / (1 + 3 * r), a10 = 10 * r / (1 + 9 * r);
      $('#al-explain', box).textContent = 'With r̄ = ' + r.toFixed(2) + ': 4 items give α = ' + a4.toFixed(3) + ', 10 items give α = ' + a10.toFixed(3) +
        '. The items are no better related to each other, yet alpha rises. A high alpha is not evidence of validity.';
    }
    box.addEventListener('input', run);
    run();
  }

  /* ---- content validity index -------------------------------------------------- */
  function initCVI(box) {
    function run() {
      var n = Math.max(1, parseInt($('#cvi-n', box).value, 10) || 1);
      var counts = $('#cvi-items', box).value.split(/[,\s;]+/).filter(Boolean).map(Number).filter(function (x) { return !isNaN(x); });
      var out = $('#cvi-explain', box);
      if (!counts.length) { $('#cvi-ave', box).textContent = '—'; $('#cvi-ua', box).textContent = '—'; out.textContent = 'Enter one count per item, separated by commas.'; return; }
      if (counts.some(function (c) { return c > n || c < 0; })) { out.textContent = 'A count cannot exceed the number of experts (' + n + ').'; return; }
      var icvi = counts.map(function (c) { return c / n; });
      var ave = icvi.reduce(function (a, b) { return a + b; }, 0) / icvi.length;
      var ua = icvi.filter(function (x) { return x === 1; }).length / icvi.length;
      $('#cvi-ave', box).textContent = ave.toFixed(2);
      $('#cvi-ua', box).textContent = ua.toFixed(2);
      var cut = n <= 5 ? 1 : 0.78;
      var weak = icvi.map(function (x, i) { return x < cut ? 'item ' + (i + 1) + ' (' + x.toFixed(2) + ')' : null; }).filter(Boolean);
      out.textContent = 'Item CVIs: ' + icvi.map(function (x) { return x.toFixed(2); }).join(', ') + '. Guideline (Polit et al., 2007): with ' +
        (n <= 5 ? 'five or fewer experts every item should reach 1.00' : 'six or more experts each item should reach 0.78') +
        ', and S-CVI/Ave should reach 0.90. ' + (weak.length ? 'Revise ' + weak.join(', ') + '.' : 'All items meet the guideline.');
    }
    box.addEventListener('input', run);
    run();
  }

  /* ---- attenuation ----------------------------------------------------------------- */
  function initAtten(box) {
    function run() {
      var b = parseFloat($('#at-b', box).value) || 0, rel = parseFloat($('#at-rel', box).value);
      $('#at-rel-out', box).textContent = rel.toFixed(2);
      $('#at-out', box).textContent = (b * rel).toFixed(3);
    }
    box.addEventListener('input', run);
    run();
  }

  /* ---- validity and reliability tree ------------------------------------------------- */
  function initVR(layout) {
    var detail = $('.vr-detail', layout);
    function select(node) {
      $all('.vr-btn', layout).forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-node') === node ? 'true' : 'false'); });
      $all('.vr-info', detail).forEach(function (d) { d.hidden = d.getAttribute('data-info') !== node; });
      if (window.renderMathInElement) {
        var shown = $('.vr-info:not([hidden])', detail);
        try { window.renderMathInElement(shown, { delimiters: [{ left: '\\(', right: '\\)', display: false }], throwOnError: false }); } catch (e) {}
      }
    }
    layout.addEventListener('click', function (e) {
      var b = e.target.closest('.vr-btn');
      if (!b) return;
      select(b.getAttribute('data-node'));
      if (window.innerWidth < 1100) detail.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'nearest' });
    });
    select('goodness');
  }

  /* ---- reading-list filter ------------------------------------------------------------ */
  function initRL(rl) {
    rl.addEventListener('click', function (e) {
      var b = e.target.closest('.rl-filter button');
      if (!b) return;
      var t = b.getAttribute('data-topic');
      $all('.rl-filter button', rl).forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      $all('.rl-topic', rl).forEach(function (sec) {
        var items = $all('.rl-item', sec);
        if (t === 'oa') {
          var any = false;
          items.forEach(function (it) { var on = it.hasAttribute('data-oa'); it.hidden = !on; any = any || on; });
          sec.hidden = !any;
        } else {
          items.forEach(function (it) { it.hidden = false; });
          sec.hidden = !(t === 'all' || sec.getAttribute('data-topic') === t);
        }
      });
    });
  }

  function boot() {
    $all('[data-sim="sampling"]').forEach(initSim);
    $all('[data-calc="alloc"]').forEach(initAlloc);
    $all('[data-calc="km"]').forEach(initKM);
    $all('[data-calc="ttest"]').forEach(initTT);
    $all('[data-calc="reg"]').forEach(initReg);
    $all('[data-calc="alpha"]').forEach(initAlpha);
    $all('[data-calc="cvi"]').forEach(initCVI);
    $all('[data-calc="atten"]').forEach(initAtten);
    $all('.vr-layout').forEach(initVR);
    $all('.rl').forEach(initRL);
  }
  if (document.readyState === 'complete') boot();
  else document.addEventListener('DOMContentLoaded', boot);
})();
