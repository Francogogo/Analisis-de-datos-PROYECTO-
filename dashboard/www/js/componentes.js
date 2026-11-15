/* Abre un .componente en el <dialog> #modal-componente moviendo el mismo nodo, así los
   outputs de Shiny siguen enlazados; al cerrar lo devuelve a su lugar. */
(function () {
  'use strict';
  let actual = null, marca = null, boton = null;

  function redimensionar(nodo) {
    requestAnimationFrame(function () {
      if (window.Plotly) nodo.querySelectorAll('.js-plotly-plot').forEach(function (p) { window.Plotly.Plots.resize(p); });
      window.dispatchEvent(new Event('resize'));
    });
  }

  function abrir(btn) {
    const dlg = document.getElementById('modal-componente');
    const comp = btn.closest('.componente');
    if (!dlg || !comp || dlg.open) return;
    boton = btn;
    actual = comp;
    marca = document.createComment('componente');
    comp.before(marca);
    dlg.querySelector('#modal-componente-titulo').textContent = comp.dataset.titulo || '';
    dlg.querySelector('.modal-cuerpo').append(comp);
    comp.classList.add('en-modal');
    dlg.showModal();
    dlg.querySelector('.modal-cuerpo').scrollTop = 0;
    redimensionar(comp);
    // El detalle estaba oculto: las fórmulas que llegaron mientras tanto pueden no estar renderizadas.
    if (window.MathJax && window.MathJax.typesetPromise) window.MathJax.typesetPromise([comp]).catch(() => {});
  }

  function devolver() {
    if (!actual || !marca) return;
    actual.classList.remove('en-modal');
    marca.replaceWith(actual);
    redimensionar(actual);
    if (boton) boton.focus();
    actual = marca = boton = null;
  }

  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.componente-abrir');
    if (btn) { abrir(btn); return; }
    const dlg = document.getElementById('modal-componente');
    if (!dlg || !dlg.open) return;
    if (e.target.closest('.modal-cerrar') || e.target === dlg) dlg.close();
  });

  document.addEventListener('close', function (e) {
    if (e.target.id === 'modal-componente') devolver();
  }, true);
})();
