/* Movimiento del atlas: la portada se construye (video Blender + barras + cifras en sincronía) y las
   cifras ruedan de su valor anterior al nuevo cuando un filtro o el what if las cambia.
   Con prefers-reduced-motion todo queda en su estado final, sin animación. */
(function () {
  'use strict';

  const QUIETO = window.matchMedia('(prefers-reduced-motion: reduce)');
  const CIFRAS = '.metricas .fs-3 .shiny-text-output, .whatif-cifra strong, .concentracion-cabecera strong';
  const PATRON = /^(\D*?)(-?\d{1,3}(?:\.\d{3})+(?:,\d+)?|-?\d+(?:,\d+)?)(.*)$/s;
  const previo = new Map(); // id de la cifra -> último valor mostrado

  /* "968.098" -> {n: 968098, dec: 0, miles: true}; "9,4 %" -> {n: 9.4, dec: 1, ...} */
  function leer(texto) {
    const m = PATRON.exec(texto.trim());
    if (!m) return null;
    const [, antes, num, despues] = m;
    const dec = num.includes(',') ? num.split(',')[1].length : 0;
    return { antes, despues, dec, miles: num.includes('.'), n: parseFloat(num.replace(/\./g, '').replace(',', '.')) };
  }

  /* Mismo formato que graficos.num(): punto de miles y coma decimal. */
  function escribir(c, n) {
    let [ent, fr] = Math.abs(n).toFixed(c.dec).split('.');
    if (c.miles) ent = ent.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return c.antes + (n < 0 ? '-' : '') + ent + (fr ? ',' + fr : '') + c.despues;
  }

  function clave(el) {
    const salida = el.closest('.shiny-bound-output');
    return salida ? salida.id + ':' + Math.max(0, cifrasDe(salida).indexOf(el)) : '';
  }

  function rodar(el, desde) {
    const c = leer(el.textContent);
    if (!c) return;
    const id = clave(el);
    const inicio = desde !== undefined ? desde : previo.get(id);
    previo.set(id, c.n);
    if (QUIETO.matches || inicio === undefined || inicio === c.n || !Number.isFinite(inicio)) return;
    const final = el.textContent;
    const dur = Math.min(1100, 520 + Math.abs(c.n - inicio) / Math.max(Math.abs(c.n), 1e-9) * 500);
    const t0 = performance.now();
    el.classList.add('cifra-rodando');
    el.setAttribute('aria-busy', 'true');
    el._rueda = t0;
    (function paso(t) {
      if (el._rueda !== t0) return; // llegó otro valor: manda la animación nueva
      const u = Math.min(1, (t - t0) / dur);
      const k = 1 - Math.pow(1 - u, 4);
      el.textContent = u < 1 ? escribir(c, inicio + (c.n - inicio) * k) : final;
      if (u < 1) requestAnimationFrame(paso);
      else { el.classList.remove('cifra-rodando'); el.removeAttribute('aria-busy'); }
    })(t0);
  }

  function visible(el) {
    const pane = el.closest('.tab-pane');
    return !pane || (pane.classList.contains('active') && !pane.hasAttribute('data-preloading'));
  }

  function cifrasDe(raiz) {
    return raiz.matches && raiz.matches(CIFRAS) ? [raiz] : Array.from(raiz.querySelectorAll(CIFRAS));
  }

  /* Cifras nuevas: si están a la vista ruedan desde el valor anterior (o desde 0 la primera vez);
     si llegan a una pestaña oculta esperan a que se abra. */
  $(document).on('shiny:value', function (ev) {
    const salida = ev.target;
    requestAnimationFrame(function () {
      cifrasDe(salida).forEach(function (el) {
        if (visible(el)) rodar(el, previo.has(clave(el)) ? undefined : 0);
        else el.dataset.cifraPendiente = '1';
      });
    });
  });

  document.addEventListener('shown.bs.tab', function (ev) {
    const sel = ev.target.getAttribute('data-bs-target') || ev.target.getAttribute('href');
    const pane = sel && sel.startsWith('#') ? document.querySelector(sel) : null;
    if (!pane) return;
    pane.querySelectorAll('[data-cifra-pendiente]').forEach(function (el) {
      delete el.dataset.cifraPendiente;
      rodar(el, previo.has(clave(el)) ? undefined : 0);
    });
    pane.querySelectorAll('.plotly-salida[data-entrada-pendiente]').forEach(entrar);
  });

  /* Primera aparición de un gráfico: barrido de izquierda a derecha (clip-path en CSS). */
  function entrar(el) {
    delete el.dataset.entradaPendiente;
    if (QUIETO.matches) return;
    el.classList.remove('grafico-entra');
    void el.offsetWidth;
    el.classList.add('grafico-entra');
  }
  document.addEventListener('grafico:primero', function (ev) {
    if (visible(ev.target)) entrar(ev.target);
    else ev.target.dataset.entradaPendiente = '1';
  });

  /* Portada: el video de Blender levanta las 100 columnas; al terminar queda en su último cuadro,
     que es el mismo póster estático. */
  function portada() {
    const video = document.getElementById('hero-3d-img');
    if (!video || QUIETO.matches || !video.play) return;
    const iniciar = function () {
      video.currentTime = 0;
      const p = video.play();
      if (p && p.catch) p.catch(function () {});
    };
    if (video.readyState >= 2) iniciar();
    else video.addEventListener('loadeddata', iniciar, { once: true });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', portada);
  else portada();
})();
