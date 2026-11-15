/* Glosario: marca términos (texto y fórmulas MathJax) de la página con un tooltip corto al pasar
   el mouse o enfocar, y abre #modal-glosario con la explicación larga al hacer click o Enter.
   Marca todas las apariciones; solo la primera de cada término por sección (ver SECCION) entra al orden
   del tabulador, para no llenar de paradas el recorrido con teclado. Datos: #glosario-datos. */
(function () {
  'use strict';
  const SECCION = '.guia-subcard, .componente-resumen, .seccion-editorial, section, .modal-cuerpo, .tab-pane';
  const SALTAR = 'script, style, button, select, option, input, textarea, a, nav, h1, h2, ' +
    '.navbar, .js-plotly-plot, .plotly-salida, .selectize-control, .modal-cabecera, .glos, #glos-tip, [data-noglos]';
  let terminos = [], porId = {}, regex = null, tip = null, timer = null;

  function escHtml(s) { return s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }

  function cargar() {
    const el = document.getElementById('glosario-datos');
    if (!el) return false;
    terminos = JSON.parse(el.textContent);
    const alts = [];
    terminos.forEach(t => {
      porId[t.id] = t;
      t.texRe = (t.tex || []).map(r => new RegExp(r));
      (t.patrones || []).forEach(p => alts.push({ p, id: t.id }));
    });
    alts.sort((a, b) => b.p.length - a.p.length);
    terminos.forEach(t => { t.re = new RegExp('^(?:' + (t.patrones || []).join('|') + ')$', 'iu'); });
    if (alts.length) regex = new RegExp('(?<![\\p{L}\\p{N}])(' + alts.map(a => a.p).join('|') + ')(?![\\p{L}\\p{N}])', 'giu');
    return true;
  }

  function idDe(texto) { return (terminos.find(t => t.re.test(texto)) || {}).id; }

  function yaMarcado(nodo, id) {
    const sec = nodo.parentElement && nodo.parentElement.closest(SECCION);
    return !sec || !!sec.querySelector('.glos[tabindex="0"][data-glos="' + id + '"]');
  }

  function preparar(el, id, enfocable) {
    el.classList.add('glos');
    el.dataset.glos = id;
    el.tabIndex = enfocable ? 0 : -1;
    el.setAttribute('role', 'button');
    el.setAttribute('aria-describedby', 'glos-tip');
    el.setAttribute('aria-haspopup', 'dialog');
  }

  function marcarTexto(raiz) {
    if (!regex) return;
    const w = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT, {
      // LaTeX sin procesar ($, \) no se marca: el span partiría la fórmula antes de que MathJax la renderice.
      acceptNode: n => (!n.nodeValue.trim() || /[$\\]/.test(n.nodeValue) || (n.parentElement && n.parentElement.closest(SALTAR + ', mjx-container')))
        ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
    });
    const nodos = [];
    while (w.nextNode()) nodos.push(w.currentNode);
    const enPasada = new Map(); // sección -> ids marcados en esta pasada (aún no están en el DOM)
    nodos.forEach(n => {
      const sec = n.parentElement.closest(SECCION);
      if (!sec) return;
      if (!enPasada.has(sec)) enPasada.set(sec, new Set());
      const usados = enPasada.get(sec);
      const s = n.nodeValue; regex.lastIndex = 0;
      let m, ult = 0, frag = null;
      while ((m = regex.exec(s))) {
        const id = idDe(m[1]);
        if (!id) continue;
        const enfocable = !usados.has(id) && !yaMarcado(n, id);
        usados.add(id);
        frag = frag || document.createDocumentFragment();
        frag.append(s.slice(ult, m.index));
        const span = document.createElement('span');
        span.textContent = m[1];
        preparar(span, id, enfocable);
        frag.append(span);
        ult = m.index + m[1].length;
      }
      if (frag) { frag.append(s.slice(ult)); n.replaceWith(frag); }
    });
  }

  function marcarFormulas(raiz) {
    const doc = window.MathJax && window.MathJax.startup && window.MathJax.startup.document;
    if (!doc || !doc.math) return;
    for (const item of doc.math) {
      const c = item.typesetRoot;
      if (!c || !c.isConnected || c.classList.contains('glos') || !raiz.contains(c) || c.closest(SALTAR)) continue;
      const t = terminos.find(t => t.texRe.some(r => r.test(item.math)));
      if (t) preparar(c, t.id, !yaMarcado(c, t.id));
    }
  }

  function escanear() {
    document.querySelectorAll('.tab-pane, .modal-cuerpo').forEach(r => { marcarTexto(r); marcarFormulas(r); });
  }

  /* ---------- tooltip */
  let actualTip = null;
  function ubicar(el) {
    const r = el.getBoundingClientRect(), tw = tip.offsetWidth, th = tip.offsetHeight, m = 8;
    const x = Math.min(Math.max(m, r.left + r.width / 2 - tw / 2), innerWidth - tw - m);
    let y = r.bottom + m;
    if (y + th > innerHeight - m) y = Math.max(m, r.top - th - m);
    tip.style.left = x + 'px';
    tip.style.top = y + 'px';
  }
  function mostrar(el) {
    const t = porId[el.dataset.glos];
    if (!t) return;
    actualTip = el;
    // El HTML con las fórmulas ya renderizadas se guarda por término: MathJax corre una sola vez.
    tip.innerHTML = t._tip || ('<strong>' + escHtml(t.nombre) + '</strong><span>' + escHtml(t.corto) +
      '</span><em>Detalles</em>');
    tip.hidden = false;
    ubicar(el);
    if (!t._tip && window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise([tip]).then(() => {
        t._tip = tip.innerHTML;
        if (actualTip === el && !tip.hidden) ubicar(el);
      }).catch(() => {});
    }
  }
  function ocultar() { if (tip) tip.hidden = true; actualTip = null; }

  /* ---------- modal */
  function abrir(el) {
    const t = porId[el.dataset.glos], dlg = document.getElementById('modal-glosario');
    if (!t || !dlg) return;
    ocultar();
    dlg.querySelector('#modal-glosario-titulo').textContent = t.nombre;
    const cuerpo = dlg.querySelector('.modal-cuerpo');
    cuerpo.innerHTML = '<p class="glosario-corto">' + escHtml(t.corto) + '</p>' +
      (t.largo || []).map(([st, tx]) => '<section class="guia-subcard"><p class="guia-subcard-titulo">' +
        escHtml(st) + '</p><p>' + escHtml(tx) + '</p></section>').join('');
    cuerpo.setAttribute('data-noglos', '');
    dlg._origen = el;
    dlg.showModal();
    if (window.MathJax && window.MathJax.typesetPromise) window.MathJax.typesetPromise([cuerpo]).catch(() => {});
  }

  function iniciar() {
    if (!cargar()) return;
    tip = document.createElement('div');
    tip.id = 'glos-tip';
    tip.setAttribute('role', 'tooltip');
    tip.hidden = true;
    document.body.append(tip);

    document.addEventListener('mouseover', e => { const g = e.target.closest('.glos'); if (g) mostrar(g); });
    document.addEventListener('mouseout', e => { const g = e.target.closest('.glos'); if (g && !g.contains(e.relatedTarget)) ocultar(); });
    document.addEventListener('focusin', e => { const g = e.target.closest('.glos'); if (g) mostrar(g); });
    document.addEventListener('focusout', e => { if (e.target.closest('.glos')) ocultar(); });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') ocultar();
      const g = e.target.closest && e.target.closest('.glos');
      if (g && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); abrir(g); }
    });
    document.addEventListener('click', e => {
      const dlg = document.getElementById('modal-glosario');
      if (dlg && dlg.open && (e.target.closest('#modal-glosario .modal-cerrar') || e.target === dlg)) { dlg.close(); return; }
      const g = e.target.closest('.glos');
      if (g) { e.preventDefault(); e.stopPropagation(); abrir(g); }
    }, true);
    document.addEventListener('close', e => {
      if (e.target.id === 'modal-glosario' && e.target._origen && e.target._origen.isConnected) e.target._origen.focus();
    }, true);
    window.addEventListener('scroll', ocultar, true);

    new MutationObserver(muts => {
      if (muts.every(m => [...m.addedNodes].every(n => n.nodeType === 1 && n.classList.contains('glos')))) return;
      clearTimeout(timer);
      timer = setTimeout(escanear, 250);
    }).observe(document.body, { childList: true, subtree: true });
    escanear();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
