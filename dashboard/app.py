"""Dashboard Shiny del informe: siete pestañas en el orden del paper."""
import hashlib
import re
from pathlib import Path

from shiny import App, ui
from starlette.middleware.gzip import GZipMiddleware

import cache
import componente
import glosario
import datos
import p_conclusiones
import p_contexto
import p_diagnosticos
import p_exploracion
import p_modelos
import p_relaciones
import p_whatif

WWW = Path(__file__).parent / "www"


def estatico(ruta: str) -> str:
    """URL de un archivo de www/ con la huella de su contenido: se puede cachear como inmutable."""
    return f"{ruta}?v={hashlib.sha256((WWW / ruta).read_bytes()).hexdigest()[:10]}"


FIGTREE, BRICOLAGE = estatico("fonts/Figtree-variable.woff2"), estatico("fonts/BricolageGrotesque-variable.woff2")


# Calienta base y agregados una sola vez al iniciar el proceso
_DATOS_INICIALES = cache.calentar(datos.cargar())

PESTANAS = [
    ("Contexto", "contexto", p_contexto),
    ("Exploración", "exploracion", p_exploracion),
    ("Relaciones", "relaciones", p_relaciones),
    ("Diagnósticos", "diagnosticos", p_diagnosticos),
    ("Modelos", "modelos", p_modelos),
    ("What if", "whatif", p_whatif),
    ("Conclusiones", "conclusiones", p_conclusiones),
]

CSS = """
@font-face {
  font-family: Figtree; src: url('[[FIGTREE]]') format('woff2');
  font-style: normal; font-weight: 300 900; font-display: swap;
}
@font-face {
  font-family: Bricolage; src: url('[[BRICOLAGE]]') format('woff2');
  font-style: normal; font-weight: 200 800; font-display: swap;
}
:root {
  --tinta: #132f38; --acento: #086c70; --claro: #dcece8;
  --alerta: #a94530; --gris: #40575d; --papel: #f4f1e8; --linea: #b9c9c5;
  --ease-expo: cubic-bezier(0.16, 1, 0.3, 1);
  scrollbar-width: thin;
  scrollbar-color: var(--acento) var(--papel);
}
@property --barra-escala {
  syntax: '<number>';
  inherits: false;
  initial-value: 1;
}
body { font-family: Figtree, system-ui, sans-serif; color: var(--tinta); background: var(--papel); line-height: 1.65; caret-color: var(--acento); }
::selection { background: #b9ddd4; color: var(--tinta); }
:focus-visible { outline: 3px solid #087d79; outline-offset: 3px; }
a { color: var(--acento); text-underline-offset: .2em; }
.navbar { background: var(--tinta) !important; padding: 1rem clamp(1rem, 3vw, 2.5rem) 0; }
.navbar > .container-fluid { padding: 0; }
.navbar .navbar-brand { color: #fff !important; font-family: Bricolage, system-ui, sans-serif; font-size: 1.12rem; line-height: 1.15; font-weight: 750; letter-spacing: -.025em; white-space: normal; }
.navbar .navbar-collapse { flex-basis: 100%; }
.navbar .navbar-nav { gap: .2rem 1.3rem; }
.navbar .nav-link { color: #d2e6e1 !important; font-size: .95rem; font-weight: 600; padding: .8rem 0; border-bottom: 3px solid transparent; }
.navbar .nav-link:hover, .navbar .nav-link.active { color: #fff !important; }
.navbar .nav-link.active { border-bottom-color: #85dfcf; text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: .3em; }
.navbar-toggler { border-color: #bdd6d1; margin-bottom: .8rem; }
.navbar-toggler-icon { filter: invert(1); }
.bslib-page-navbar > .container-fluid { max-width: 1620px; margin: auto; padding: clamp(1.5rem, 3.5vw, 4rem); }
h1, h2, h3, h4, h5 { font-family: Bricolage, system-ui, sans-serif; color: var(--tinta); font-weight: 700; letter-spacing: -.025em; line-height: 1.12; text-wrap: balance; }
.tab-pane h3 { font-size: clamp(2.2rem, 1.6rem + 2vw, 3.8rem); max-width: 20ch; margin: 0 0 1.5rem; }
.tab-pane h4 { font-size: clamp(1.3rem, 1.15rem + .5vw, 1.75rem); margin: 3rem 0 1rem; }
.tab-pane h5 { font-size: 1.12rem; margin: 2rem 0 .8rem; }
p, li { max-width: 75ch; }
p { margin-bottom: 1rem; text-wrap: pretty; }
li + li { margin-top: .4rem; }
.seccion-editorial { padding: 1.5rem 0 2rem; border-bottom: 1px solid var(--linea); contain: layout style; }
.seccion-editorial:last-child { border-bottom: 0; }
.seccion-cabecera { margin-bottom: 1.5rem; }
.panel-destacado { background: #dcece8; padding: clamp(1.5rem, 3vw, 3rem); margin: 1.5rem 0; }
.panel-destacado h4, .seccion-editorial h4:first-child { margin-top: 0; }
.panel-destacado blockquote { max-width: 45ch; font-size: clamp(1.2rem, 1rem + .6vw, 1.55rem); line-height: 1.4; font-weight: 650; margin: .8rem 0 1.2rem; }
.hero-investigacion { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, .95fr); gap: clamp(2rem, 4vw, 5rem); border-top: 2px solid var(--tinta); border-bottom: 1px solid var(--linea); margin: 1rem 0 2rem; padding: clamp(1.75rem, 3vw, 3rem) 0; }
.hero-contenido { min-width: 0; }
.hero-contenido h4 { color: var(--acento); margin: 0 0 1rem; font-size: 1rem; }
.hero-contenido blockquote { font-family: Bricolage, system-ui, sans-serif; font-size: clamp(1.7rem, 1.2rem + 1.3vw, 2.6rem); font-weight: 650; line-height: 1.14; letter-spacing: -.025em; margin: 0 0 2rem; max-width: 24ch; border-left: 0; padding-left: 0; }
.hero-contenido p { max-width: 65ch; }
.hero-datos { display: flex; flex-direction: column; justify-content: center; gap: .85rem; min-width: 0; align-self: start; padding: clamp(1.1rem, 2vw, 1.85rem); background: var(--tinta); color: #f6f5ed; contain: layout style; }
.hero-3d-stage { border-bottom: 1px solid #2b545f; padding-bottom: .75rem; }
#hero-3d-img { display: block; width: 100%; height: auto; max-height: 290px; object-fit: contain; aspect-ratio: 560 / 380; border-radius: 4px; }
.hero-3d-meta { margin: .45rem 0 0; font-size: .84rem; color: #cbe1db; }
.concentracion { color: #f6f5ed; margin: 0; }
.concentracion-titulo { font-family: Bricolage, system-ui, sans-serif; font-size: 1.4rem; line-height: 1.15; font-weight: 700; margin-bottom: .35rem; }
.concentracion-corte { color: #cbe1db; font-size: .92rem; margin-bottom: .25rem; }
.concentracion-fila { margin-top: 1rem; }
.concentracion-cabecera { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; font-weight: 600; }
.concentracion-cabecera strong { font-family: Bricolage, system-ui, sans-serif; color: #ffbaaa; font-size: clamp(1.7rem, 1.35rem + .9vw, 2.3rem); font-variant-numeric: tabular-nums; white-space: nowrap; }
.concentracion-barra { display: block; width: 100%; height: auto; }
.concentracion-fill { transform-origin: left center; }
.concentracion-nota { margin: .9rem 0 0; color: #cbe1db; font-size: .86rem; }
.tarjetas-hallazgos { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr)); gap: 1rem; }
.panel-filtros { background: #dcece8; padding: clamp(1.25rem, 2vw, 2rem); margin: 1.5rem 0; }
.panel-filtros h5 { margin-top: 0; }
.metricas { margin: 1.5rem 0; }
.metricas small { color: var(--gris) !important; }
.sin-resultados { background: #fff0e7; color: #793a24; padding: .85rem 1rem; }
.card { border: 0; border-top: 2px solid var(--tinta); border-radius: 0; background: #fffdf8; box-shadow: none; }
.card-header { background: transparent; border-bottom: 1px solid var(--linea); color: var(--tinta); font-weight: 650; }
.metricas .card .fs-3 { font-family: Bricolage, system-ui, sans-serif; font-variant-numeric: tabular-nums; font-size: 2rem !important; }
.form-label, .control-label { color: var(--tinta); font-weight: 650; }
.form-control, .form-select, .selectize-input { border-color: #627f7a; border-radius: 4px; }
.form-control:focus, .form-select:focus, .selectize-input.focus { border-color: var(--acento); box-shadow: 0 0 0 .2rem rgba(8, 108, 112, .2); }
.tabla-responsive, .shiny-table-output, .table-responsive { max-width: 100%; overflow-x: auto; }
.table { --bs-table-bg: transparent; --bs-table-color: var(--tinta); --bs-table-border-color: var(--linea); font-size: .93rem; font-variant-numeric: tabular-nums; }
.table th, .table td { padding: .75rem .8rem; vertical-align: top; }
.table thead th { background: var(--tinta); color: #fff; font-weight: 700; }
.table tbody tr:nth-child(even) { background: rgba(220, 236, 232, .55); }
details { margin: 1.2rem 0; padding: 1rem 1.2rem; background: #fffdf8; border: 1px solid var(--linea); }
summary { cursor: pointer; color: var(--acento); font-weight: 700; }
details[open] summary { margin-bottom: 1rem; }
.flujo { display: flex; align-items: stretch; flex-wrap: wrap; gap: .6rem; }
.flujo-caja { flex: 1 1 11rem; padding: 1rem; background: #fffdf8; border-top: 2px solid var(--acento); display: flex; flex-direction: column; gap: .35rem; }
.flujo-cabecera { display: flex; align-items: center; gap: .45rem; color: var(--tinta); }
.flujo-icono { color: var(--acento); flex: none; }
.flujo-desc { font-size: .95rem; color: var(--gris); }
.flujo-flecha { align-self: center; color: var(--acento); display: flex; align-items: center; }
.figura-vectorial { margin: 1.25rem 0 1.5rem; padding: 1.1rem 1.25rem; background: #fffdf8; border-top: 2px solid var(--tinta); max-width: 44rem; }
.svg-ranking-eta { display: block; width: 100%; height: auto; }
.svg-barra-eta { transform-origin: 185px center; }
.svg-pie { margin: .5rem 0 0; font-size: .86rem; color: var(--gris); }
.whatif-cifra strong { color: var(--acento); font-family: Bricolage, system-ui, sans-serif; font-size: 2rem; font-variant-numeric: tabular-nums; }
.plotly-salida { min-height: 400px; contain: layout style; }
.tab-pane[data-preloading="true"] {
  display: block !important; position: fixed; inset: 0 auto auto 0;
  width: 960px; height: 640px; opacity: .001; pointer-events: none; z-index: -10; contain: strict;
}
@media (prefers-reduced-motion: no-preference) {
  .tab-pane.active {
    animation: atlas-entrada .28s var(--ease-expo);
  }
  details[open]::details-content {
    transition: opacity .24s var(--ease-expo), transform .24s var(--ease-expo);
    @starting-style { opacity: 0; transform: translateY(-4px); }
  }
  .concentracion-fill, .svg-barra-eta {
    animation: atlas-barra .65s var(--ease-expo) both;
  }
  .flujo-caja {
    animation: atlas-caja .45s var(--ease-expo) both;
    animation-delay: calc(var(--orden, 0) * 45ms);
  }
}
@keyframes atlas-entrada {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes atlas-barra {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}
@keyframes atlas-caja {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (prefers-reduced-motion: reduce) {
  ::view-transition-group(*), ::view-transition-old(*), ::view-transition-new(*) {
    animation: none !important;
  }
}
.componente { position: relative; margin: 1rem 0 1.5rem; }
.componente-abrir { position: absolute; top: 0; right: 0; z-index: 2; display: inline-flex; align-items: center; gap: .35rem; padding: .35rem .75rem; font-size: .85rem; font-weight: 650; color: var(--acento); background: #fffdf8; border: 1px solid var(--acento); border-radius: 999px; cursor: pointer; }
.componente-abrir::before { content: "+"; font-size: 1.05rem; font-weight: 800; line-height: 1; }
.componente-abrir:hover { background: var(--acento); color: #fff; }
.componente:has(> .componente-abrir) { padding-top: 2.4rem; }
.componente-resumen { margin: .6rem 0 0; color: var(--gris); font-size: .95rem; max-width: 75ch; }
.componente-resumen p { margin: 0 0 .4rem; }
.componente-detalle { display: none; }
.hero-datos .componente-resumen { color: #cbe1db; }
.componente.en-modal .concentracion { background: var(--tinta); color: #f6f5ed; padding: clamp(1rem, 2vw, 1.75rem); }
.glos { text-decoration: underline dotted var(--acento); text-decoration-thickness: 1.5px; text-underline-offset: .22em; cursor: help; border-radius: 2px; }
.glos:hover, .glos:focus-visible { background: rgba(8, 108, 112, .12); }
mjx-container.glos { padding: 0 .1em; border-bottom: 1.5px dotted var(--acento); text-decoration: none; }
.table thead .glos, .navbar .glos { text-decoration-color: currentColor; }
.table tbody .glos { text-decoration-color: rgba(8, 108, 112, .45); }
.table tbody mjx-container.glos { border-bottom-color: rgba(8, 108, 112, .45); }
#glos-tip { position: fixed; z-index: 2000; max-width: min(24rem, calc(100vw - 1rem)); padding: .8rem 1rem; background: var(--tinta); color: #f6f5ed; font-size: .9rem; line-height: 1.5; box-shadow: 0 10px 30px rgba(19, 47, 56, .3); pointer-events: none; display: flex; flex-direction: column; gap: .3rem; }
#glos-tip[hidden] { display: none; }
#glos-tip strong { font-family: Bricolage, system-ui, sans-serif; font-size: 1rem; color: #fff; }
#glos-tip em { font-style: normal; font-size: .8rem; color: #9fd8cc; }
#modal-glosario { width: min(760px, calc(100vw - 2rem)); }
.glosario-corto { font-size: 1.1rem; font-weight: 600; max-width: none; }
.glosario-cuerpo .guia-subcard { margin-top: .8rem; }
.componente--abierto > .componente-detalle { display: block; margin-top: 1rem; }
.tabla-desc thead tr + tr th { background: #24464f; font-size: .82rem; font-weight: 650; }
.tabla-desc th[colspan], .tabla-desc td.desc-filtro, .tabla-desc thead tr + tr th.desc-filtro { border-left: 2px solid var(--linea); }
.tabla-desc td.desc-filtro { font-weight: 650; }
.tabla-desc td.desc-base { color: var(--gris); }
.tabla-desc tbody th { font-weight: 650; background: transparent; color: var(--tinta); }
.componente.en-modal { margin: 0; padding-top: 0; }
.componente.en-modal > .componente-abrir { display: none; }
.componente.en-modal > .componente-detalle { display: block; margin-top: 1.5rem; padding-top: 1.25rem; border-top: 1px solid var(--linea); }
.componente.en-modal .componente-resumen { font-size: 1.02rem; color: var(--tinta); padding: .9rem 1.1rem; background: #fffdf8; border-left: 3px solid var(--acento); }
.componente.en-modal .componente-detalle .guia-rejilla { grid-template-columns: 1fr; }
.componente.en-modal .componente-detalle .guia-lectura { margin-top: 0; }
.componente.en-modal .componente-detalle .guia-subcard { padding: 1rem 1.2rem; }
.componente.en-modal .componente-detalle .guia-lectura p { font-size: .97rem; line-height: 1.6; }
@media (min-width: 1000px) {
  #modal-componente { width: min(1500px, calc(100vw - 2rem)); }
  .componente.en-modal { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(340px, 1fr); column-gap: 2.25rem; align-items: start; }
  .componente.en-modal > :not(.componente-detalle) { grid-column: 1; min-width: 0; }
  .componente.en-modal > .componente-detalle { grid-column: 2; grid-row: 1 / span 30; margin: 0; padding: 0 0 0 2.25rem; border-top: 0; border-left: 1px solid var(--linea); }
}
#modal-componente, #modal-glosario { width: min(1180px, calc(100vw - 2rem)); max-height: calc(100dvh - 2rem); padding: 0; border: 0; border-top: 3px solid var(--tinta); background: var(--papel); color: var(--tinta); box-shadow: 0 24px 64px rgba(19, 47, 56, .35); overflow: hidden; }
#modal-componente[open], #modal-glosario[open] { display: flex; flex-direction: column; }
#modal-componente::backdrop, #modal-glosario::backdrop { background: rgba(19, 47, 56, .55); }
.modal-cabecera { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 1rem clamp(1rem, 3vw, 2rem); border-bottom: 1px solid var(--linea); background: #fffdf8; }
.modal-cabecera h2 { font-size: clamp(1.2rem, 1rem + .8vw, 1.6rem); margin: 0; }
.modal-cerrar { flex: none; width: 2.5rem; height: 2.5rem; font-size: 1.6rem; line-height: 1; color: var(--tinta); background: transparent; border: 1px solid var(--linea); border-radius: 50%; cursor: pointer; }
.modal-cerrar:hover { background: var(--claro); }
.modal-cuerpo { overflow-y: auto; overscroll-behavior: contain; padding: clamp(1rem, 3vw, 2rem); }
@media (prefers-reduced-motion: no-preference) {
  #modal-componente[open], #modal-glosario[open] { animation: atlas-entrada .22s var(--ease-expo); }
}
.vista-niveles .plotly-salida { height: 666px !important; }
@supports selector(:has(*)) {
  .vista-niveles:not(:has(option[value="capitulo"]:checked)) .plotly-salida { height: 400px !important; }
}
.ficha-prueba dt { margin-top: .8rem; }
.ficha-prueba dd { margin-bottom: .5rem; }
.guia-lectura { margin: 1rem 0 1.65rem; }
.guia-lectura--simple { padding: .95rem 1.15rem; background: #fffdf8; border: 1px solid var(--linea); border-left: 3px solid var(--acento); }
.guia-lectura-titulo { font-family: Bricolage, system-ui, sans-serif; font-size: .86rem; font-weight: 700; color: var(--acento); text-transform: uppercase; letter-spacing: .04em; margin: 0 0 .6rem; }
.guia-rejilla { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 16.5rem), 1fr)); gap: .8rem; align-items: stretch; }
.guia-rejilla--pila { grid-template-columns: 1fr; gap: .65rem; }
.guia-subcard { padding: .85rem 1.05rem; background: #fffdf8; border: 1px solid var(--linea); border-top: 2px solid var(--acento); }
.guia-subcard-titulo { font-family: Bricolage, system-ui, sans-serif; font-size: .95rem; font-weight: 700; color: var(--tinta); margin: 0 0 .35rem; line-height: 1.25; }
.guia-lectura p { margin: 0 0 .45rem; font-size: .93rem; line-height: 1.55; max-width: none; }
.guia-lectura p:last-child { margin-bottom: 0; }
.guia-lectura strong { color: var(--tinta); }
.formula-latex { margin: .85rem 0 1.1rem; padding: .85rem 1.15rem; background: #eef5f4; border-left: 3px solid var(--tinta); overflow-x: auto; max-width: 100%; font-size: .95rem; }
.firma-autores { margin: 1rem 0 0; padding: 1rem clamp(1.5rem, 3.5vw, 4rem) 2rem; border-top: 1px solid var(--linea); font-size: .88rem; color: var(--gris); }
mjx-container { overflow-x: auto; overflow-y: hidden; max-width: 100%; }
mjx-container[jax="SVG"][display="true"] { display: block; margin: .25rem 0; }
@media (min-width: 1100px) {
  .navbar { position: fixed; inset: 0 auto 0 0; width: 16.5rem; overflow-y: auto; align-items: flex-start; padding: 2.5rem 1.5rem; z-index: 1030; }
  .navbar > .container-fluid { display: flex; flex-direction: column; align-items: stretch; }
  .navbar .navbar-brand { display: block; margin: 0 0 2rem; padding: 0 0 1.5rem; border-bottom: 1px solid #54746f; font-size: 1.35rem; }
  .navbar .navbar-collapse { display: block !important; flex-basis: auto; }
  .navbar .navbar-nav { display: flex; flex-direction: column; gap: .35rem; width: 100%; }
  .navbar .nav-link { display: block; padding: .75rem .9rem; border: 0; }
  .navbar .nav-link:hover { background: #244b50; }
  .navbar .nav-link.active { background: #dcece8; color: var(--tinta) !important; }
  .bslib-page-navbar > .container-fluid { max-width: none; width: auto; margin-left: 16.5rem; padding: clamp(2rem, 4vw, 4.5rem); }
  .firma-autores { margin-left: 16.5rem; padding: 1rem clamp(2rem, 4vw, 4.5rem) 2rem; }
}
@media (min-width: 768px) and (max-width: 1099px) {
  .navbar .navbar-nav { flex-wrap: wrap; }
}
@media (max-width: 850px) {
  .hero-investigacion { grid-template-columns: minmax(0, 1fr); }
  .hero-datos { align-self: stretch; }
}
@media (max-width: 767px) {
  .navbar { padding-bottom: .2rem; }
  .navbar .navbar-brand { max-width: calc(100% - 4.5rem); font-size: .95rem; }
  .navbar .navbar-nav { padding-bottom: .75rem; gap: 0; }
  .navbar .nav-link { padding: .65rem .35rem; }
  .flujo-flecha { display: none; }
}
"""

CSS = CSS.replace("[[FIGTREE]]", FIGTREE).replace("[[BRICOLAGE]]", BRICOLAGE)

# MathJax local (www/mathjax/tex-svg.js, sin fuentes externas): la app no depende de internet.
MATHJAX = """
window.MathJax = {
  startup: { typeset: false },
  tex: {
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
    processEscapes: true
  },
  options: {skipHtmlTags: ['script', 'style', 'textarea', 'pre']}
};
"""

MENU_MOVIL = """
document.addEventListener('click', function (event) {
  var enlace = event.target.closest('.navbar-collapse .nav-link[data-bs-toggle="tab"]');
  if (!enlace) return;
  var menu = enlace.closest('.navbar-collapse');
  var boton = enlace.closest('.navbar').querySelector('.navbar-toggler');
  if (!boton || !boton.getClientRects().length || boton.getAttribute('aria-expanded') !== 'true') return;
  function cerrar() {
    boton.click();
    boton.focus();
  }
  if (menu.classList.contains('collapsing')) menu.addEventListener('shown.bs.collapse', cerrar, {once: true});
  else cerrar();
});
"""

app_ui = ui.page_navbar(
    *[ui.nav_panel(titulo, ui.h2(titulo, class_="visually-hidden"), mod.pestana_ui(id_))
      for titulo, id_, mod in PESTANAS],
    title="Estadías hospitalarias FONASA 2020",
    id="pestana",
    header=ui.TagList(
        ui.head_content(
            ui.tags.link(rel="icon", href="assets/favicon.svg", type="image/svg+xml"),
        ),
        ui.tags.link(rel="preload", href=BRICOLAGE, as_="font", type="font/woff2", crossorigin="anonymous"),
        ui.tags.link(rel="preload", href=FIGTREE, as_="font", type="font/woff2", crossorigin="anonymous"),
        ui.tags.link(rel="preload", href="assets/hero-3d-poster.webp", as_="image", type="image/webp", fetchpriority="high"),
        ui.tags.style(CSS),
        ui.h1("Estadías hospitalarias FONASA 2020", class_="visually-hidden"),
        ui.tags.script(MATHJAX),
        ui.tags.script(MENU_MOVIL),
        ui.tags.script(src=estatico("js/atlas-engine.js"), defer=True),
        ui.tags.script(src=estatico("js/componentes.js"), defer=True),
        ui.tags.script(src=estatico("js/graficos.js"), defer=True,
                       data_plotly=estatico("plotly/plotly-cartesian.min.js")),
        componente.MODAL,
        glosario.MODAL,
        glosario.datos(),
        ui.tags.script(src=estatico("js/glosario.js"), defer=True),
        ui.tags.script(src=estatico("mathjax/tex-svg.js"), id="MathJax-script", async_=True, fetchpriority="low"),
    ),
    footer=ui.tags.footer(
        "Diego Muñoz y Franco Pastorini · Análisis de Datos e Inferencia Estadística (UDD, 2026) · Datos: DEIS–MINSAL 2020 (FONASA) · ",
        ui.tags.a("Repositorio en GitHub", href="https://github.com/Francogogo/Analisis-de-datos-PROYECTO-", target="_blank", rel="noopener"),
        class_="firma-autores",
    ),
    lang="es",
)


def server(input, output, session):
    d = _DATOS_INICIALES
    for _, id_, mod in PESTANAS:
        mod.pestana_server(id_, d=d)


class CacheInmutable:
    """Cache-Control de un año para lo que no cambia sin cambiar de URL: las librerías de Shiny
    (lib/<nombre>-<versión>/) y los archivos con ?v=<huella>. El resto se revalida con ETag."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not (
            scope["path"].startswith("/lib/") or re.search(rb"(^|&)v=", scope["query_string"])
        ):
            return await self.app(scope, receive, send)

        async def enviar(msg):
            if msg["type"] == "http.response.start" and msg["status"] == 200:
                msg["headers"] = [*msg.get("headers", []), (b"cache-control", b"public, max-age=31536000, immutable")]
            await send(msg)

        await self.app(scope, receive, enviar)


app = App(app_ui, server, static_assets=WWW)
app.starlette_app.add_middleware(CacheInmutable)
app.starlette_app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)
