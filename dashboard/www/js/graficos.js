/* Salida Shiny de los gráficos (ver render_plotly en graficos.py): recibe la figura en JSON y la
   dibuja con plotly.js. plotly.js no está en el camino crítico: se carga la primera vez que llega
   un gráfico o cuando el navegador queda libre tras el arranque, y el navegador lo guarda en caché. */
(function () {
  'use strict';
  const SRC = document.currentScript.dataset.plotly;
  const CONFIG = { responsive: true, displaylogo: false };
  let carga = null;
  // Un gráfico por tarea: al abrir una pestaña con varios, cada uno se dibuja en su propio cuadro en vez
  // de sumar todos en un solo cuadro largo que congela el scroll y la transición.
  let turno = Promise.resolve();
  function enSuTurno(dibujar) {
    const t = turno.then(function () { return new Promise(function (ok) { requestAnimationFrame(function () { setTimeout(ok, 0); }); }); })
      .then(dibujar);
    turno = t.catch(function () {});
    return t;
  }

  function plotly() {
    if (window.Plotly) return Promise.resolve(window.Plotly);
    if (!carga) {
      carga = new Promise(function (ok, mal) {
        const s = document.createElement('script');
        s.src = SRC;
        s.onload = function () { ok(window.Plotly); };
        s.onerror = function () { carga = null; mal(new Error('No se pudo cargar plotly.js')); };
        document.head.append(s);
      });
    }
    return carga;
  }

  function limpiar(el) { if (window.Plotly && el._fullLayout) window.Plotly.purge(el); }

  class SalidaPlotly extends Shiny.OutputBinding {
    find(scope) { return $(scope).find('.plotly-salida'); }
    renderValue(el, valor) {
      el._valor = valor; // si llega otro valor mientras carga plotly.js, gana el último
      if (valor == null) { limpiar(el); return; }
      plotly().then(function (P) { return enSuTurno(function () {
        if (el._valor !== valor) return;
        const f = JSON.parse(valor);
        const primero = !el._fullLayout;
        const layout = f.layout || {};
        // Plotly solo sabe animar si las trazas y los ejes siguen siendo los mismos; si cambian
        // (otra variable, subgráficos nuevos) la transición falla con "a[c._name] is undefined".
        const firma = JSON.stringify([
          (f.data || []).map(function (t) { return [t.type, t.xaxis, t.yaxis]; }),
          Object.keys(layout).filter(function (k) { return /^[xy]axis/.test(k); }).sort()
        ]);
        const anima = !primero && el._firma === firma &&
          !matchMedia('(prefers-reduced-motion: reduce)').matches;
        el._firma = firma;
        // Cambios de filtro: las barras y puntos se desplazan a su nuevo valor en vez de saltar.
        if (anima) layout.transition = { duration: 480, easing: 'cubic-in-out' };
        const fin = function () {
          // Plotly guarda transition en el layout: sin esto cada resize también se animaría.
          if (el.layout) delete el.layout.transition;
          if (primero) el.dispatchEvent(new CustomEvent('grafico:primero', { bubbles: true }));
        };
        return Promise.resolve().then(function () { return P.react(el, f.data, layout, CONFIG); }).then(fin, function (e) {
          if (!anima) throw e;
          // Respaldo: si la animación igual falla, dibuja de cero sin transición.
          delete layout.transition;
          P.purge(el);
          return P.newPlot(el, f.data, layout, CONFIG).then(fin);
        });
      }); }).catch(function (e) { el.textContent = e.message; });
    }
    renderError(el, err) {
      el._valor = null;
      limpiar(el);
      super.renderError(el, err);
    }
  }
  Shiny.outputBindings.register(new SalidaPlotly(), 'dashboard.plotly');

  $(document).one('shiny:idle', function () {
    (window.requestIdleCallback || setTimeout)(function () { plotly().catch(function () {}); });
  });
})();
