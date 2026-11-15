/* Atlas Engine: preload inteligente, View Transitions y MathJax acotado */
(function () {
  'use strict';

  const REDUCED_MOTION = () =>
    window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const yieldToMain = () => {
    if ('scheduler' in window && typeof window.scheduler.yield === 'function') {
      return window.scheduler.yield();
    }
    return new Promise((resolve) => setTimeout(resolve, 0));
  };

  /* 1. MathJax acotado: controlador unico (startup.typeset=false) sin doble splitText */
  function initScopedMathJax() {
    let pendingNodes = new Set();
    let timer = null;
    let chain = Promise.resolve();
    const hasMath = (txt) => txt.includes('$') || txt.includes('\\(') || txt.includes('\\[');

    function topHost(pe) {
      const candidate = pe.closest('.formula-latex, p, li, dd, dt, td, th, span');
      if (candidate && !candidate.querySelector('mjx-container')) return candidate;
      return pe;
    }

    function dedupeTargets(list) {
      const unique = [];
      for (const el of list) {
        if (!el || !el.isConnected || !hasMath(el.textContent || '')) continue;
        if (el.closest('mjx-container, svg, .js-plotly-plot, .plotly')) continue;
        if (list.some((other) => other !== el && other && other.contains(el))) continue;
        unique.push(el);
      }
      return unique;
    }

    async function typesetSafe(batch) {
      for (const el of batch) {
        if (!el || !el.isConnected || !hasMath(el.textContent || '')) continue;
        try {
          if (window.MathJax.typesetClear) window.MathJax.typesetClear([el]);
          await window.MathJax.typesetPromise([el]);
        } catch (_) {}
      }
    }

    function flush() {
      timer = null;
      if (pendingNodes.size === 0) return;
      if (!window.MathJax || !window.MathJax.typesetPromise) {
        timer = setTimeout(flush, 100);
        return;
      }
      const targets = dedupeTargets(Array.from(pendingNodes));
      pendingNodes.clear();
      if (targets.length === 0) return;
      const startupReady = (window.MathJax.startup && window.MathJax.startup.promise) || Promise.resolve();
      chain = chain
        .then(() => startupReady)
        .then(() => window.MathJax.typesetPromise(targets).catch(() => typesetSafe(targets)));
    }

    function queueNode(rawNode) {
      const node = rawNode && rawNode.nodeType === 3 ? rawNode.parentElement : rawNode;
      if (!node || node.nodeType !== 1) return;
      if (node.closest && node.closest('mjx-container, svg, .js-plotly-plot, .plotly')) return;
      if (!hasMath(node.textContent || '')) return;
      rescanUnrendered(node);
    }

    function rescanUnrendered(scope) {
      const base = scope || document.querySelector('.tab-pane.active') || document.querySelector('.tab-content') || document.body;
      if (!base) return;
      const walker = document.createTreeWalker(base, NodeFilter.SHOW_TEXT);
      let n;
      while ((n = walker.nextNode())) {
        const pe = n.parentElement;
        if (!pe || pe.closest('script, style, textarea, pre, mjx-container, svg, .js-plotly-plot, .plotly')) continue;
        if (!hasMath(n.nodeValue || '')) continue;
        pendingNodes.add(topHost(pe));
      }
      if (pendingNodes.size > 0 && !timer) {
        timer = setTimeout(flush, 30);
      }
    }

    document.addEventListener('DOMContentLoaded', () => {
      const root = document.querySelector('.tab-content') || document.body;
      rescanUnrendered(root);
      const mo = new MutationObserver((mutations) => {
        for (const m of mutations) {
          for (const n of m.addedNodes) queueNode(n);
        }
      });
      mo.observe(root, { childList: true, subtree: true });
      document.addEventListener('shown.bs.tab', (ev) => {
        const sel = ev.target && (ev.target.getAttribute('data-bs-target') || ev.target.getAttribute('href'));
        const pane = sel && sel.startsWith('#') ? document.querySelector(sel) : null;
        if (pane) rescanUnrendered(pane);
      });
    });

    if (window.jQuery) {
      window.jQuery(document).on('shiny:value', (ev) => {
        if (ev && ev.target) setTimeout(() => rescanUnrendered(ev.target), 30);
      });
      window.jQuery(document).on('shiny:idle', () => {
        rescanUnrendered(document.querySelector('.tab-content') || document.body);
      });
    }
  }

  /* 2. Preload inteligente de pestanas Shiny (por intencion hover/focus + siguiente paso en idle) */
  function initSmartTabPreloader() {
    const preloaded = new Set();
    let userActive = false;

    function getTabPane(tabLink) {
      const sel = tabLink.getAttribute('data-bs-target') || tabLink.getAttribute('href');
      if (!sel || !sel.startsWith('#')) return null;
      return document.querySelector(sel);
    }

    async function prewarmPane(tabLink) {
      const pane = getTabPane(tabLink);
      if (!pane || pane.classList.contains('active') || pane.classList.contains('show') || preloaded.has(pane.id)) return;
      preloaded.add(pane.id);

      pane.setAttribute('data-preloading', 'true');
      pane.setAttribute('aria-hidden', 'true');

      if (window.jQuery) {
        window.jQuery(pane).find('.shiny-bound-output').trigger('shown');
        window.jQuery(window).trigger('resize');
      } else {
        window.dispatchEvent(new Event('resize'));
      }

      await new Promise((resolve) => {
        let done = false;
        const finish = () => {
          if (done) return;
          done = true;
          resolve();
        };
        const t = setTimeout(finish, 1800);
        if (window.jQuery) {
          window.jQuery(document).one('shiny:idle', () => {
            clearTimeout(t);
            setTimeout(finish, 60);
          });
        }
      });

      pane.removeAttribute('data-preloading');
      pane.removeAttribute('aria-hidden');
    }

    function scheduleNextTabWarmup() {
      const conn = navigator.connection;
      if (conn && (conn.saveData || conn.effectiveType === '2g')) return;
      const run = () => {
        if (userActive || document.hidden) return;
        const nextLink = document.querySelector('.navbar-nav .nav-link[data-bs-toggle="tab"]:not(.active)');
        if (nextLink) prewarmPane(nextLink);
      };
      if ('requestIdleCallback' in window) {
        requestIdleCallback(run, { timeout: 2200 });
      } else {
        setTimeout(run, 1200);
      }
    }

    document.addEventListener('DOMContentLoaded', () => {
      const navLinks = document.querySelectorAll('.navbar-nav .nav-link[data-bs-toggle="tab"]');
      navLinks.forEach((link) => {
        const triggerIntent = () => prewarmPane(link);
        link.addEventListener('pointerenter', triggerIntent, { passive: true });
        link.addEventListener('focus', triggerIntent, { passive: true });
      });

      document.addEventListener('show.bs.tab', (ev) => {
        userActive = true;
        const pane = getTabPane(ev.target);
        if (!pane) return;
        pane.removeAttribute('data-preloading');
        pane.removeAttribute('aria-hidden');
      });

      // Al activarse una pestana, recalcula tamano Plotly si fue prehidratada fuera de pantalla
      document.addEventListener('shown.bs.tab', (ev) => {
        const pane = getTabPane(ev.target);
        if (!pane) return;
        pane.removeAttribute('data-preloading');
        pane.removeAttribute('aria-hidden');
        requestAnimationFrame(() => {
          window.dispatchEvent(new Event('resize'));
          if (window.Plotly) {
            pane.querySelectorAll('.js-plotly-plot').forEach((plot) => {
              try {
                window.Plotly.Plots.resize(plot);
              } catch (_) {}
            });
          }
        });
      });

      if (window.jQuery) {
        window.jQuery(document).on('shiny:inputchanged', () => {
          userActive = true;
        });
        window.jQuery(document).one('shiny:idle', scheduleNextTabWarmup);
      } else {
        setTimeout(scheduleNextTabWarmup, 1500);
      }
    });
  }

  /* 3. View Transitions API entre pestanas en escritorio (respeta prefers-reduced-motion y menu movil) */
  function initViewTransitions() {
    if (!('startViewTransition' in document)) return;
    document.addEventListener('click', (ev) => {
      if (REDUCED_MOTION()) return;
      const link = ev.target.closest('.navbar-nav .nav-link[data-bs-toggle="tab"]');
      if (!link || link.classList.contains('active')) return;
      const toggler = document.querySelector('.navbar-toggler');
      // En menu movil conserva flujo exacto de foco y colapso Bootstrap
      if (toggler && toggler.getClientRects().length > 0) return;

      const bsTab = window.bootstrap && window.bootstrap.Tab ? window.bootstrap.Tab.getOrCreateInstance(link) : null;
      if (!bsTab) return;
      ev.preventDefault();
      ev.stopImmediatePropagation();
      document.startViewTransition(() => {
        bsTab.show();
      });
    }, true);
  }

  initScopedMathJax();
  initSmartTabPreloader();
  initViewTransitions();
})();
