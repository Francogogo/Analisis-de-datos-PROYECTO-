"""Dashboard Shiny del informe: siete pestañas en el orden del paper."""
import hashlib
import json
import re
from pathlib import Path

from shiny import App, ui
from starlette.middleware.gzip import GZipMiddleware

import cache
import componente
import glosario
import graficos
import datos
import etiquetas
import modelo
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


CSS = graficos.css_tokens()
CREDITOS = json.loads((WWW / "assets/fotos/creditos.json").read_text(encoding="utf-8"))


def _credito(c: dict) -> ui.Tag:
    """Título de la foto (sin extensión), autor y licencia, en una línea con enlace a Commons."""
    titulo = c["titulo"].rsplit(".", 1)[0].lstrip("- ")
    autor = c["autor"].split(" (")[0]
    licencia = c["licencia"].replace("-", "\u2011")  # guion que no corta la línea: "CC BY‑SA" va entero
    return ui.tags.a(f"{titulo}, {autor}, {licencia}", href=c["url"], target="_blank", rel="noopener")


def cifras_cabecera(d) -> dict[str, tuple[str, str]]:
    """Cifra destacada de cada pestaña, calculada de los mismos datos que muestran los gráficos 3D."""
    c, num = d.cifras, graficos.num
    reg = c["pct_prolongadas_por_grupo"]["region"]
    sd = list(c["sd_residuos_cuartil"].values())
    cap = {k.split(": ", 1)[1]: v["%Δ"] for k, v in c["coef"].items() if k.startswith("capitulo: ")}
    top = max(cap, key=cap.get)
    m3 = d.m3
    ref = p_whatif.perfil_ref(m3) if callable(p_whatif.perfil_ref) else p_whatif.perfil_ref
    return {
        "exploracion": (f"{num(float(d.base['dias_estada'].median()), 0)} días",
                        f"es la mediana de estada; la media sube a {num(float(d.base['dias_estada'].mean()), 1)} por la cola larga"),
        "relaciones": (f"{num(min(reg.values()), 1)}–{num(max(reg.values()), 1)} %",
                       "de estadías prolongadas según la región, ordenadas de norte a sur en la figura"),
        "diagnosticos": (f"+{num((sd[-1] / sd[0] - 1) * 100, 0)} %",
                         "sube la desviación estándar del residuo entre el primer y el último cuartil"),
        "modelos": (num(c["eta2_parciales"]["capítulo"]["η² parcial"], 3),
                    "es el $\\eta^2$ parcial del capítulo CIE-10, el factor que más pesa en $M3$"),
        "whatif": (f"{num(modelo.dias_estimados({**ref, 'edad': 45}, m3)[0], 2)} días",
                   "estima M3 para el perfil de referencia a los 45 años"),
        "conclusiones": (f"+{num(cap[top], 0)} %",
                         f"más días en {etiquetas.NOMBRES[top].lower()} ({top}) que en el capítulo digestivo de referencia"),
    }


def medidas_webp(ruta: Path) -> tuple[int, int]:
    """Ancho y alto de un WebP extendido (VP8X, el formato con transparencia), sin depender de Pillow."""
    b = ruta.read_bytes()[:30]
    assert b[:4] == b"RIFF" and b[12:16] == b"VP8X", f"{ruta.name}: se esperaba WebP VP8X"
    return 1 + int.from_bytes(b[24:27], "little"), 1 + int.from_bytes(b[27:30], "little")


def cabecera(id_: str, cifras: dict) -> ui.Tag:
    """Foto real en duotono (assets/fotos) con la figura 3D de la pestaña (assets/3d) y su cifra."""
    cr = CREDITOS[id_]
    cifra = cifras.get(id_)
    figura = WWW / f"assets/3d/{id_}.webp"
    ancho, alto = medidas_webp(figura) if figura.exists() else (0, 0)
    return ui.div(
        # width/height dan caja desde el inicio: sin ellos la imagen diferida mide 0 y nunca se carga.
        ui.tags.img(src=estatico(f"assets/3d/{id_}.webp"), class_="cabecera-figura", alt="", loading="lazy",
                    decoding="async", width=str(ancho), height=str(alto)) if figura.exists() else None,
        ui.p(ui.tags.strong(cifra[0]), ui.span(cifra[1]), class_="cabecera-cifra") if cifra else None,
        ui.p("Foto: ", ui.tags.a(cr["autor"], href=cr["url"], target="_blank", rel="noopener"), f" · {cr['licencia']}",
             class_="cabecera-credito"),
        class_="cabecera-pestana", # La URL se resuelve contra clinica.css (www/css/), por eso sube un nivel.
        style=f"--foto: url('../{estatico(f'assets/fotos/{id_}.webp')}')",
    )


_CIFRAS = cifras_cabecera(_DATOS_INICIALES)

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
    *[ui.nav_panel(titulo, ui.h2(titulo, class_="visually-hidden"),
                   ui.div(cabecera(id_, _CIFRAS), mod.pestana_ui(id_), class_=f"pestana pestana--{id_}"))
      for titulo, id_, mod in PESTANAS],
    title="Estadías hospitalarias FONASA 2020",
    id="pestana",
    header=ui.TagList(
        ui.head_content(
            ui.tags.link(rel="icon", href="assets/favicon.svg", type="image/svg+xml"),
        ),
        ui.tags.link(rel="preload", href="assets/hero-3d-poster.webp", as_="image", type="image/webp", fetchpriority="high"),
        ui.tags.style(CSS),
        ui.tags.link(rel="stylesheet", href=estatico("css/clinica.css")),
        ui.h1("Estadías hospitalarias FONASA 2020", class_="visually-hidden"),
        ui.div(class_="progreso-lectura", aria_hidden="true"),
        ui.tags.script(MATHJAX),
        ui.tags.script(MENU_MOVIL),
        ui.tags.script(src=estatico("js/atlas-engine.js"), defer=True),
        ui.tags.script(src=estatico("js/componentes.js"), defer=True),
        ui.tags.script(src=estatico("js/movimiento.js"), defer=True),
        ui.tags.script(src=estatico("js/graficos.js"), defer=True,
                       data_plotly=estatico("plotly/plotly-cartesian.min.js")),
        componente.MODAL,
        glosario.MODAL,
        glosario.datos(),
        ui.tags.script(src=estatico("js/glosario.js"), defer=True),
        ui.tags.script(src=estatico("mathjax/tex-svg.js"), id="MathJax-script", async_=True, fetchpriority="low"),
    ),
    footer=ui.tags.footer(
        ui.div(
            ui.p(ui.tags.strong("Diego Muñoz y Franco Pastorini"),
                 " · Análisis de Datos e Inferencia Estadística, UDD 2026", class_="pie-autores"),
            ui.p("Datos: DEIS–MINSAL 2020 (FONASA) · ",
                 ui.tags.a("Repositorio", href="https://github.com/Francogogo/Analisis-de-datos-PROYECTO-",
                           target="_blank", rel="noopener"), class_="pie-fuente"),
            class_="pie-fila",
        ),
        ui.tags.details(
            ui.tags.summary("Créditos de las imágenes"),
            ui.p("Fotos de Wikimedia Commons, tratadas en duotono. Las figuras 3D las hicimos en Blender "
                 "con los datos del estudio."),
            ui.tags.ul(*[ui.tags.li(ui.tags.span(titulo, class_="pie-pestana"), _credito(CREDITOS[id_]))
                         for titulo, id_, _ in PESTANAS if id_ != "contexto"]),
            class_="pie-creditos",
        ),
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
