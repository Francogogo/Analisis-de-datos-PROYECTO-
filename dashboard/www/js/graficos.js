/* Salida Shiny de los gráficos (ver render_plotly en graficos.py): recibe la figura en JSON y la
   dibuja con plotly.js. plotly.js no está en el camino crítico: se carga la primera vez que llega
   un gráfico o cuando el navegador queda libre tras el arranque, y el navegador lo guarda en caché. */
(function () {
  'use strict';
  const SRC = document.currentScript.dataset.plotly;
  const CONFIG = { responsive: true, displaylogo: false };
  let carga = null;

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
      plotly().then(function (P) {
        if (el._valor !== valor) return;
        const f = JSON.parse(valor);
        return P.react(el, f.data, f.layout || {}, CONFIG);
      }).catch(function (e) { el.textContent = e.message; });
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
