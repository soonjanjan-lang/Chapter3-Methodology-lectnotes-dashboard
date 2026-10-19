/* ==========================================================================
   Widgets: sub-tabs, Stata/Python switch, copy, quizzes, sorters, drafts,
   home-page red-pen annotation.
   ========================================================================== */
(function () {
  'use strict';
  var store = (window.Ch3 && window.Ch3.store) || { get: function (k, d) { return d; }, set: function () {} };
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- sub-tabs ------------------------------------------------------------- */
  function selectSubtab(tabSection, name, updateHash) {
    var list = $('.subtabs', tabSection);
    if (!list) return;
    var tabsEls = $all('[role="tab"]', list);
    var target = null;
    if (name) target = tabsEls.filter(function (t) { return t.getAttribute('data-sub') === name; })[0];
    if (!target) target = tabsEls.filter(function (t) { return t.getAttribute('aria-selected') === 'true'; })[0] || tabsEls[0];
    tabsEls.forEach(function (t) {
      var on = t === target;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.tabIndex = on ? 0 : -1;
      var p = document.getElementById(t.getAttribute('aria-controls'));
      if (p) {
        var wasHidden = p.hidden;
        p.hidden = !on;
        if (on && wasHidden && !reduceMotion) { p.classList.remove('is-entering'); void p.offsetWidth; p.classList.add('is-entering'); }
      }
    });
    if (updateHash && target) {
      var id = tabSection.getAttribute('data-tab');
      var h = '#' + id + '/' + target.getAttribute('data-sub');
      if (history.replaceState) history.replaceState(null, '', h);
      document.dispatchEvent(new CustomEvent('ch3:subtab', { detail: { id: id, sub: target.getAttribute('data-sub') } }));
    }
  }
  window.Ch3 = window.Ch3 || {};
  window.Ch3.selectSubtab = selectSubtab;

  document.addEventListener('click', function (e) {
    var t = e.target.closest('.subtabs [role="tab"]');
    if (!t) return;
    var sec = t.closest('section.tab');
    selectSubtab(sec, t.getAttribute('data-sub'), true);
    var list = t.closest('.subtabs');
    var top = list.getBoundingClientRect().top;
    if (top < 0 || top > window.innerHeight * 0.6) list.scrollIntoView({ block: 'start' });
  });
  document.addEventListener('keydown', function (e) {
    var t = e.target.closest && e.target.closest('.subtabs [role="tab"]');
    if (!t || (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft' && e.key !== 'Home' && e.key !== 'End')) return;
    e.preventDefault();
    var all = $all('[role="tab"]', t.closest('.subtabs'));
    var i = all.indexOf(t);
    if (e.key === 'ArrowRight') i = (i + 1) % all.length;
    if (e.key === 'ArrowLeft') i = (i - 1 + all.length) % all.length;
    if (e.key === 'Home') i = 0;
    if (e.key === 'End') i = all.length - 1;
    all[i].focus();
    selectSubtab(t.closest('section.tab'), all[i].getAttribute('data-sub'), true);
  });

  /* ---- Stata / Python switch (one preference for every listing) -------------- */
  function applyLang(lang) {
    $all('.listing[data-langs]').forEach(function (l) {
      var pres = $all('pre[data-lang]', l);
      var has = pres.some(function (p) { return p.getAttribute('data-lang') === lang; });
      var use = has ? lang : pres[0] && pres[0].getAttribute('data-lang');
      pres.forEach(function (p) { p.hidden = p.getAttribute('data-lang') !== use; });
      $all('.lang-switch button', l).forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-lang') === use ? 'true' : 'false'); });
      var t = $('.listing-title', l);
      var pre = pres.filter(function (p) { return !p.hidden; })[0];
      if (t && pre && pre.getAttribute('data-file')) t.textContent = pre.getAttribute('data-file');
    });
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('.lang-switch button');
    if (!b) return;
    var lang = b.getAttribute('data-lang');
    store.set('lang', lang);
    applyLang(lang);
  });

  /* ---- copy code -------------------------------------------------------------- */
  function copyText(text, done) {
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); done(true); } catch (err) { done(false); }
      document.body.removeChild(ta);
    }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(function () { done(true); }, fallback);
    else fallback();
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('.copy-btn');
    if (!b) return;
    var l = b.closest('.listing');
    var pre = $all('pre', l).filter(function (p) { return !p.hidden; })[0];
    if (!pre) return;
    copyText(pre.innerText.replace(/\n$/, ''), function (ok) {
      var lab = $('.copy-label', b);
      b.classList.toggle('is-done', ok);
      if (lab) lab.textContent = ok ? 'Copied' : 'Select and copy';
      setTimeout(function () { b.classList.remove('is-done'); if (lab) lab.textContent = 'Copy'; }, 1800);
    });
  });

  /* ---- quizzes ------------------------------------------------------------------ */
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-quiz-check], [data-quiz-reset]');
    if (!b) return;
    var quiz = b.closest('.quiz');
    if (b.hasAttribute('data-quiz-reset')) {
      quiz.classList.remove('is-marked');
      $all('.opt', quiz).forEach(function (o) { o.classList.remove('is-correct', 'is-wrong', 'is-chosen'); });
      $all('input', quiz).forEach(function (i) { i.checked = false; });
      $('.quiz-score', quiz).textContent = '';
      return;
    }
    var sets = $all('fieldset', quiz);
    var right = 0, answered = 0;
    sets.forEach(function (fs) {
      var chosen = $('input:checked', fs);
      $all('.opt', fs).forEach(function (o) {
        var inp = $('input', o);
        var correct = inp.hasAttribute('data-correct');
        o.classList.toggle('is-chosen', inp.checked);
        o.classList.toggle('is-correct', correct && !!chosen);
        o.classList.toggle('is-wrong', inp.checked && !correct);
      });
      if (chosen) { answered++; if (chosen.hasAttribute('data-correct')) right++; }
    });
    quiz.classList.add('is-marked');
    var msg = right + ' of ' + sets.length + ' correct';
    if (answered < sets.length) msg += ' (' + (sets.length - answered) + ' not answered)';
    $('.quiz-score', quiz).textContent = msg + '.';
  });

  /* ---- sorting games (e.g. NOIR) ---------------------------------------------------- */
  document.addEventListener('click', function (e) {
    var b = e.target.closest('.sort-choices button');
    if (!b) return;
    var item = b.closest('.sort-item');
    var answer = item.getAttribute('data-answer');
    $all('.sort-choices button', item).forEach(function (x) {
      x.setAttribute('aria-pressed', x === b ? 'true' : 'false');
      x.classList.remove('is-right', 'is-wrong');
    });
    var ok = b.getAttribute('data-choice') === answer;
    b.classList.add(ok ? 'is-right' : 'is-wrong');
    var fb = $('.sort-feedback', item);
    if (fb) {
      fb.textContent = (ok ? 'Correct. ' : 'Not quite — it is ' + item.getAttribute('data-answer-label') + '. ') + (item.getAttribute('data-explain') || '');
      fb.style.color = ok ? 'var(--correct)' : 'var(--pen)';
    }
    var sorter = item.closest('.sorter');
    var done = $all('.sort-item', sorter).filter(function (it) { return $('[aria-pressed="true"]', it); });
    var right = done.filter(function (it) { return $('.is-right', it); }).length;
    var out = $('.sorter-score', sorter);
    if (out) out.textContent = right + ' of ' + $all('.sort-item', sorter).length + ' correct so far.';
  });

  /* ---- drafts: students' own answers, kept in this browser only ---------------------- */
  function initDrafts() {
    $all('textarea.draft[data-key]').forEach(function (ta) {
      var k = 'draft:' + ta.getAttribute('data-key');
      var v = store.get(k, '');
      if (v) ta.value = v;
      var timer;
      ta.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(function () { store.set(k, ta.value); }, 400);
      });
    });
  }

  /* ---- home: the examiner's red pen draws in once ------------------------------------- */
  function initPen() {
    var pen = $('.cp-pen');
    if (!pen) return;
    $all('.draw', pen).forEach(function (p) {
      try { var len = Math.ceil(p.getTotalLength()); p.style.setProperty('--len', len); } catch (err) {}
    });
    if (reduceMotion || store.get('penDrawn', false)) return;
    function go() {
      pen.classList.add('is-drawing');
      store.set('penDrawn', true);
    }
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (ents) {
        if (ents.some(function (en) { return en.isIntersecting; })) { setTimeout(go, 350); io.disconnect(); }
      }, { threshold: 0.4 });
      io.observe(pen);
    } else go();
  }

  /* ---- checklists (ticks kept in this browser) ---------------------------------------- */
  function initChecklists() {
    $all('.checklist[data-checklist]').forEach(function (list) {
      var id = list.getAttribute('data-checklist');
      var saved = store.get('check:' + id, {}) || {};
      var boxes = $all('input[type="checkbox"]', list);
      var out = list.nextElementSibling && list.nextElementSibling.classList.contains('checklist-count') ? list.nextElementSibling : null;
      function count() {
        var n = boxes.filter(function (b) { return b.checked; }).length;
        if (out) out.textContent = n + ' of ' + boxes.length + ' checked' + (n === boxes.length ? '. Chapter 3 is ready for your supervisor.' : '.');
      }
      boxes.forEach(function (b) {
        b.checked = !!saved[b.getAttribute('data-key')];
        b.addEventListener('change', function () {
          saved[b.getAttribute('data-key')] = b.checked;
          store.set('check:' + id, saved);
          count();
        });
      });
      count();
    });
  }

  function boot() {
    applyLang(store.get('lang', 'stata'));
    initDrafts();
    initChecklists();
    initPen();
  }
  if (document.readyState === 'complete') boot();
  else document.addEventListener('DOMContentLoaded', boot);
})();
