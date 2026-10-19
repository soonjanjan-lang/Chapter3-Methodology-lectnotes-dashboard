/* ==========================================================================
   App shell: router, theme, text size, projector, notes, search, progress.
   Classic script (works from file://). Storage is a per-browser convenience
   only; everything works without it.
   ========================================================================== */
(function () {
  'use strict';

  var html = document.documentElement;

  var store = {
    get: function (k, d) {
      try { var v = localStorage.getItem('ch3:' + k); return v === null ? d : JSON.parse(v); }
      catch (e) { return d; }
    },
    set: function (k, v) {
      try { localStorage.setItem('ch3:' + k, JSON.stringify(v)); } catch (e) { /* storage unavailable */ }
    }
  };
  window.Ch3 = window.Ch3 || {};
  window.Ch3.store = store;

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- theme ------------------------------------------------------------ */
  var darkQuery = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  function effectiveTheme() {
    var t = html.getAttribute('data-theme');
    if (t) return t;
    return darkQuery && darkQuery.matches ? 'dark' : 'light';
  }
  function syncThemeButton() {
    var btn = $('#btn-theme');
    if (!btn) return;
    var dark = effectiveTheme() === 'dark';
    btn.setAttribute('aria-label', dark ? 'Switch to light pages' : 'Switch to dark pages');
    var lab = $('.tool-label', btn);
    if (lab) lab.textContent = dark ? 'Light' : 'Dark';
  }
  function setTheme(t) {
    if (t) html.setAttribute('data-theme', t); else html.removeAttribute('data-theme');
    store.set('theme', t || null);
    syncThemeButton();
  }

  /* ---- text size & projector --------------------------------------------- */
  var SIZES = [18, 19, 20, 22, 24, 26, 28];
  function defaultBase() {
    var w = window.innerWidth;
    return w >= 1100 ? 20 : (w >= 700 ? 19 : 18);
  }
  function currentBase() { return parseFloat(getComputedStyle(html).fontSize) || defaultBase(); }
  function applySize() {
    var user = store.get('size', null);
    var projector = html.classList.contains('projector');
    var size = user;
    if (projector) size = Math.max(user || 0, 26);
    if (size) html.style.setProperty('--user-base', size + 'px');
    else html.style.removeProperty('--user-base');
    var out = $('#size-readout');
    if (out) out.textContent = Math.round(currentBase()) + 'px';
  }
  function stepSize(dir) {
    var cur = Math.round(currentBase());
    var next = cur;
    if (dir > 0) { for (var i = 0; i < SIZES.length; i++) if (SIZES[i] > cur) { next = SIZES[i]; break; } }
    else { for (var j = SIZES.length - 1; j >= 0; j--) if (SIZES[j] < cur) { next = SIZES[j]; break; } }
    if (html.classList.contains('projector') && next < 26) { setProjector(false); }
    store.set('size', next === defaultBase() ? null : next);
    applySize();
  }
  function setProjector(on) {
    html.classList.toggle('projector', on);
    store.set('projector', on);
    var b = $('#btn-projector');
    if (b) b.setAttribute('aria-pressed', on ? 'true' : 'false');
    applySize();
  }

  /* ---- examiner's notes ------------------------------------------------- */
  function setNotes(show) {
    html.classList.toggle('hide-notes', !show);
    store.set('notes', show);
    var b = $('#btn-notes');
    if (b) b.setAttribute('aria-pressed', show ? 'true' : 'false');
  }

  /* ---- drawer (narrow screens & projector) -------------------------------- */
  function setDrawer(open) {
    var rail = $('#rail'), scrim = $('#scrim'), btn = $('#btn-menu');
    if (!rail) return;
    rail.classList.toggle('is-open', open);
    if (scrim) scrim.classList.toggle('is-open', open);
    if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) { var cur = $('.toc-link[aria-current="page"]', rail) || $('.toc-link', rail); if (cur) cur.focus(); }
  }

  /* ---- router -------------------------------------------------------------- */
  var tabs = [];
  var visited = {};
  function parseHash() {
    var h = decodeURIComponent((location.hash || '').replace(/^#/, ''));
    var parts = h.split('/');
    return { tab: parts[0] || 'home', sub: parts[1] || null, anchor: parts[2] || null };
  }
  function tabTitle(sec) { return sec.getAttribute('data-title') || ''; }
  function tabCode(sec) { return sec.getAttribute('data-code') || ''; }

  function show(route, opts) {
    opts = opts || {};
    var target = document.getElementById('tab-' + route.tab);
    if (!target) { target = document.getElementById('tab-home'); route = { tab: 'home' }; }
    var changed = target.hidden;
    tabs.forEach(function (s) { s.hidden = s !== target; });

    $all('.toc-link').forEach(function (a) {
      if (a.getAttribute('data-tab') === route.tab) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });

    var rhs = $('#rh-section');
    if (rhs) rhs.textContent = route.tab === 'home' ? '' : (tabCode(target) + '  ' + (target.getAttribute('data-short') || tabTitle(target)));
    document.title = (route.tab === 'home' ? '' : tabCode(target) + ' ' + tabTitle(target) + ' · ') + 'Chapter 3: Methodology';

    // pager
    var i = tabs.indexOf(target);
    var prev = tabs[i - 1], next = tabs[i + 1];
    var pp = $('#pager-prev'), pn = $('#pager-next');
    if (pp) {
      pp.hidden = !prev;
      if (prev) { pp.href = '#' + prev.getAttribute('data-tab'); $('.pager-title', pp).textContent = (tabCode(prev) ? tabCode(prev) + ' ' : '') + tabTitle(prev); }
    }
    if (pn) {
      pn.hidden = !next;
      if (next) { pn.href = '#' + next.getAttribute('data-tab'); $('.pager-title', pn).textContent = (tabCode(next) ? tabCode(next) + ' ' : '') + tabTitle(next); }
    }

    // progress
    visited[route.tab] = true;
    store.set('visited', visited);
    markVisited();

    if (window.Ch3.selectSubtab) window.Ch3.selectSubtab(target, route.sub, false);

    document.dispatchEvent(new CustomEvent('ch3:tab', { detail: { id: route.tab, el: target } }));

    if (route.anchor) {
      var a = document.getElementById(route.anchor);
      if (a) { a.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' }); return; }
    }
    if (changed || opts.top) {
      window.scrollTo(0, 0);
      var h1 = $('h1', target);
      if (h1 && !opts.initial) { h1.setAttribute('tabindex', '-1'); h1.focus({ preventScroll: true }); }
    }
    setDrawer(false);
  }

  function markVisited() {
    $all('.toc-link').forEach(function (a) {
      a.classList.toggle('is-visited', !!visited[a.getAttribute('data-tab')]);
    });
    var n = Object.keys(visited).filter(function (k) { return document.getElementById('tab-' + k); }).length;
    var out = $('#progress-readout');
    if (out) out.textContent = n + ' of ' + tabs.length + ' sections opened';
  }

  /* ---- search ---------------------------------------------------------------- */
  var index = null;
  function buildIndex() {
    index = [];
    tabs.forEach(function (sec) {
      var tab = sec.getAttribute('data-tab');
      var where = (tabCode(sec) ? tabCode(sec) + ' ' : '') + tabTitle(sec);
      index.push({ tab: tab, sub: null, anchor: null, title: where, where: 'Section', text: (($('.lede', sec) || {}).textContent || '').trim() });
      var heading = null;
      $all('h2, h3, h4, p, li, td, dt, dd, summary', sec).forEach(function (el, n) {
        if (el.closest('.search-skip')) return;
        var panel = el.closest('[data-panel]');
        var sub = panel ? panel.getAttribute('data-panel') : null;
        var txt = (el.textContent || '').replace(/\s+/g, ' ').trim();
        if (!txt) return;
        if (/^H[234]$/.test(el.tagName)) {
          if (!el.id) el.id = tab + '-h' + n;
          heading = { id: el.id, text: txt, sub: sub };
          index.push({ tab: tab, sub: sub, anchor: el.id, title: txt, where: where, text: '' });
        } else if (txt.length > 25) {
          index.push({ tab: tab, sub: sub, anchor: heading && heading.sub === sub ? heading.id : null,
            title: heading && heading.sub === sub ? heading.text : where, where: where, text: txt });
        }
      });
    });
  }
  function runSearch(q) {
    var list = $('#search-results');
    if (!list) return;
    list.innerHTML = '';
    q = q.trim().toLowerCase();
    if (q.length < 2) { list.innerHTML = '<li><p class="search-empty">Type at least two letters, e.g. “stratified”, “Cronbach”, “panel”.</p></li>'; return; }
    var terms = q.split(/\s+/);
    var hits = [];
    index.forEach(function (e) {
      var hay = (e.title + ' ' + e.text).toLowerCase();
      for (var i = 0; i < terms.length; i++) if (hay.indexOf(terms[i]) < 0) return;
      var score = (e.title.toLowerCase().indexOf(q) >= 0 ? 10 : 0) + (e.text ? 0 : 3) + (e.where === 'Section' ? 4 : 0);
      hits.push({ e: e, score: score });
    });
    hits.sort(function (a, b) { return b.score - a.score; });
    var seen = {};
    hits = hits.filter(function (h) { var k = h.e.tab + '|' + h.e.anchor + '|' + h.e.text.slice(0, 40); if (seen[k]) return false; seen[k] = 1; return true; }).slice(0, 30);
    if (!hits.length) { list.innerHTML = '<li><p class="search-empty">No matches. Try a shorter or different word.</p></li>'; return; }
    hits.forEach(function (h, i) {
      var e = h.e;
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = '#' + [e.tab, e.sub || (e.anchor ? 'notes' : ''), e.anchor || ''].join('/').replace(/\/+$/, '');
      if (i === 0) a.className = 'is-active';
      var t = document.createElement('span'); t.className = 'sr-title'; t.textContent = e.title;
      var w = document.createElement('span'); w.className = 'sr-where'; w.textContent = e.where === 'Section' ? 'Section' : e.where;
      a.appendChild(t); a.appendChild(w);
      if (e.text) {
        var x = document.createElement('span'); x.className = 'sr-text';
        var pos = e.text.toLowerCase().indexOf(terms[0]);
        x.textContent = (pos > 40 ? '…' + e.text.slice(pos - 30) : e.text);
        a.appendChild(x);
      }
      a.addEventListener('click', function () { closeSearch(); });
      li.appendChild(a);
      list.appendChild(li);
    });
  }
  function openSearch() {
    var d = $('#search-dialog');
    if (!d) return;
    if (!index) buildIndex();
    if (typeof d.showModal === 'function') d.showModal(); else d.setAttribute('open', '');
    var inp = $('#search-input');
    inp.value = '';
    runSearch('');
    inp.focus();
  }
  function closeSearch() {
    var d = $('#search-dialog');
    if (d && d.open) { if (typeof d.close === 'function') d.close(); else d.removeAttribute('open'); }
  }
  function moveActive(dir) {
    var links = $all('#search-results a');
    if (!links.length) return;
    var i = links.findIndex(function (a) { return a.classList.contains('is-active'); });
    links.forEach(function (a) { a.classList.remove('is-active'); });
    i = (i + dir + links.length) % links.length;
    links[i].classList.add('is-active');
    links[i].scrollIntoView({ block: 'nearest' });
  }

  /* ---- printing & PDF: show everything ------------------------------------ */
  var printState = null;
  function expandForPrint() {
    printState = { hidden: [] };
    $all('[hidden]').forEach(function (el) {
      if (el.closest('.tab, main')) { printState.hidden.push(el); el.hidden = false; }
    });
    printState.closed = $all('details:not([open])');
    printState.closed.forEach(function (d) { d.open = true; });
    html.classList.add('print-all');
  }
  function restoreAfterPrint() {
    if (!printState) return;
    printState.hidden.forEach(function (el) { el.hidden = true; });
    printState.closed.forEach(function (d) { d.open = false; });
    html.classList.remove('print-all');
    printState = null;
  }
  window.Ch3.expandForPrint = expandForPrint;

  /* ---- boot -------------------------------------------------------------------- */
  function boot() {
    tabs = $all('section.tab');
    visited = store.get('visited', {}) || {};

    var t = store.get('theme', null);
    if (t) html.setAttribute('data-theme', t);
    syncThemeButton();
    if (darkQuery && darkQuery.addEventListener) darkQuery.addEventListener('change', syncThemeButton);

    if (store.get('projector', false)) html.classList.add('projector');
    var bp = $('#btn-projector'); if (bp) bp.setAttribute('aria-pressed', html.classList.contains('projector') ? 'true' : 'false');
    applySize();
    window.addEventListener('resize', function () { var o = $('#size-readout'); if (o) o.textContent = Math.round(currentBase()) + 'px'; });
    setNotes(store.get('notes', true));

    document.addEventListener('click', function (e) {
      var b = e.target.closest('button');
      if (!b) return;
      switch (b.id) {
        case 'btn-theme': setTheme(effectiveTheme() === 'dark' ? 'light' : 'dark'); break;
        case 'btn-smaller': stepSize(-1); break;
        case 'btn-larger': stepSize(1); break;
        case 'btn-projector': setProjector(!html.classList.contains('projector')); break;
        case 'btn-notes': setNotes(html.classList.contains('hide-notes')); break;
        case 'btn-menu': setDrawer(!$('#rail').classList.contains('is-open')); break;
        case 'btn-search': openSearch(); break;
        case 'btn-print': window.print(); break;
      }
    });
    var scrim = $('#scrim'); if (scrim) scrim.addEventListener('click', function () { setDrawer(false); });

    document.addEventListener('keydown', function (e) {
      var tag = (e.target.tagName || '').toLowerCase();
      var typing = tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable;
      if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) { e.preventDefault(); openSearch(); return; }
      if (e.key === '/' && !typing) { e.preventDefault(); openSearch(); return; }
      if (e.key === 'Escape') { setDrawer(false); }
    });
    var si = $('#search-input');
    if (si) {
      si.addEventListener('input', function () { runSearch(si.value); });
      si.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown') { e.preventDefault(); moveActive(1); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); moveActive(-1); }
        else if (e.key === 'Enter') { var a = $('#search-results a.is-active'); if (a) { e.preventDefault(); location.hash = a.getAttribute('href'); closeSearch(); } }
      });
    }
    var sd = $('#search-dialog');
    if (sd) sd.addEventListener('click', function (e) { if (e.target === sd) closeSearch(); });

    window.addEventListener('hashchange', function () { show(parseHash()); });
    window.addEventListener('beforeprint', expandForPrint);
    window.addEventListener('afterprint', restoreAfterPrint);

    // maths and code
    if (window.renderMathInElement) {
      try {
        window.renderMathInElement(document.body, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '\\[', right: '\\]', display: true },
            { left: '\\(', right: '\\)', display: false }
          ],
          ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'option'],
          throwOnError: false
        });
      } catch (err) { /* maths stays as source text */ }
    }
    if (window.hljs) {
      $all('pre code[class*="language-"]').forEach(function (c) { try { window.hljs.highlightElement(c); } catch (err) {} });
    }

    if (/[?&]print=all\b/.test(location.search)) { expandForPrint(); }
    show(parseHash(), { initial: true, top: true });
    html.classList.add('is-ready');
  }

  // DOMContentLoaded fires after every deferred script, so widgets.js is ready by then.
  if (document.readyState === 'complete') boot();
  else document.addEventListener('DOMContentLoaded', boot);
})();
