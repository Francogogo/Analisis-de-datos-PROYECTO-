"""Pestana Contexto: problema, pregunta, hipotesis, flujo metodologico y variables."""
from __future__ import annotations

from htmltools import Tag
from shiny import module, render, ui

import componente
import graficos

TEXTOS = {
    "color_titulo": "Cómo leer el color",
    "color_intro": (
        "El color lleva datos en todo el dashboard y cada familia significa una sola cosa. El largo de una barra o la "
        "posición de un punto siguen dando el valor; el color agrega a qué grupo pertenece o cuánto pesa."
    ),
    "titulo": "Contexto del estudio",
    "problema": (
        "En este estudio (UDD, 2026), Diego Muñoz y Franco Pastorini analizamos los egresos FONASA de 2020 para ver "
        "dónde se concentra el uso de camas. La mitad de los egresos dura [[mediana]] días o menos. En cambio, el "
        "[[pct_prol]] % más largo, con estadías sobre [[corte]] días, ocupa el [[pct_cama]] % de los días-cama."
    ),
    "pregunta_titulo": "Pregunta de investigación",
    "pregunta": (
        "¿Qué factores clínicos, demográficos y del sistema de salud se asocian con la duración de la estadía "
        "hospitalaria en los egresos FONASA de Chile en 2020?"
    ),
    "prolongada": (
        "Fijamos el corte en el percentil 90 de la base, $P_{90} = [[corte]]$ días. Así aislamos el 10 % más largo "
        "sin imponer un límite médico arbitrario. Lo usamos para medir la concentración y en los cruces $\\chi^2$; "
        "el modelo principal, en cambio, trabaja con $\\ln(\\text{días})$."
    ),
    "formula_conc": (
        "$$\\begin{aligned}\n"
        "&\\text{Estadía prolongada:} \\\\\n"
        "&\\qquad \\text{días}_i > P_{90} = [[corte]]\\text{ días} \\\\[.6em]\n"
        "&\\text{Proporción de días-cama:} \\\\\n"
        "&\\qquad \\frac{\\sum_{\\text{días}_i > [[corte]]} \\text{días}_i}{\\sum_{i=1}^{n} \\text{días}_i}\n"
        "\\end{aligned}$$"
    ),
    "titulo_conc": "Concentración de días-cama",
    "resumen_conc": (
        "Las estadías de más de [[corte]] días son el [[pct_prol]] % de los egresos, pero suman el [[pct_cama]] % de los "
        "días-cama. Eso sugiere que la presión sobre las camas depende más de esa cola larga que del número total de altas."
    ),
    "guia_conc_titulo": "Cómo leer la concentración",
    "guia_conc": [
        ("Egresos y días-cama no miden lo mismo",
         "Un egreso cuenta igual si la estadía duró 1 día o 30, pero la segunda ocupa 30 veces más cama. Los días-cama "
         "son la suma de los días que cada egreso ocupó una cama, así que pesan más los casos largos."),
        ("Cómo leer las barras",
         "La sala de arriba muestra 100 camas, cada una con el 1 % de los egresos y una ficha por día de estada. Las rojas son "
         "estadías de más de [[corte]] días. "
         "Cada barra suma el 100 % de su propio total: una compara proporciones de egresos y la otra de días-cama."),
        ("Qué sugiere esta concentración",
         "Pocas estadías largas explican casi la mitad del uso de camas. Eso indica dónde está la presión sobre la red, "
         "pero no por qué esos casos se alargan: la base describe, no explica causas."),
    ],
    "hip_titulo": "Hipótesis",
    "hip_intro": (
        "Contrastamos la hipótesis nula $H_0$, que dice que no hay asociación, con la alternativa $H_1$, que dice que sí "
        "la hay. Rechazamos $H_0$ cuando el valor-$p$ queda bajo $\\alpha = 0{,}05$, el nivel de significancia que fijamos. "
        "El valor-$p$ es la probabilidad de obtener un resultado igual o más extremo que el observado si $H_0$ fuera "
        "verdadera. La hipótesis general del estudio es:"
    ),
    "hip_general": [
        ("$H_0$", "la duración de la estadía no se asocia con los factores clínicos, demográficos ni del sistema de salud."),
        ("$H_1$", "al menos uno de esos factores se asocia con la duración de la estadía."),
    ],
    "hip_grupos_intro": (
        "Dividimos esa pregunta en cuatro pares de hipótesis, uno por bloque de factores. En cada par, la nula dice que "
        "ningún factor del bloque se asocia con $\\ln(\\text{días})$ cuando se mantienen constantes los demás:"
    ),
    # (nula, alternativa, grupo, factores)
    "hip_grupos": [
        ("$H_{0a}$", "$H_{1a}$", "clínicos", "capítulo del diagnóstico CIE-10, cirugía y condición de egreso."),
        ("$H_{0b}$", "$H_{1b}$", "demográficos", "edad, con $\\text{edad}$ y $\\text{edad}^2$ para captar una curva, y sexo. Esperamos más días en adultos mayores."),
        ("$H_{0c}$", "$H_{1c}$", "sistema de salud", "tipo de establecimiento SNSS o no SNSS y región."),
        ("$H_{0d}$", "$H_{1d}$", "sensibilidad",
         "nacionalidad y etnia, que quedaron fuera de la selección de variables. La nula dice que no aportan nada a la "
         "duración por sobre los siete factores anteriores."),
    ],
    "pruebas_titulo": "Hipótesis de cada prueba",
    "resumen_pruebas": (
        "Cada fila indica qué se contrasta y con qué estadístico de prueba. Como la base es grande, casi cualquier diferencia sale "
        "significativa, así que el tamaño del efecto pesa tanto como el valor-$p$."
    ),
    "pruebas_nota": (
        "Elegimos cada prueba según la escala de las variables. Con 968.098 egresos, cualquier diferencia mínima da "
        "$p < 0{,}05$, así que cada contraste va acompañado de un tamaño del efecto ($r$, $\\varepsilon^2$, $V$ o "
        "$\\eta^2_{\\text{parcial}}$) que mide cuán grande es la diferencia. Los $\\beta_j$ son los coeficientes del modelo "
        "lineal en $\\ln(\\text{días})$."
    ),
    "pruebas_cols": ["Prueba", "Se aplica a", "$H_0$", "$H_1$", "Estadístico"],
    "pruebas": [
        ("Shapiro–Wilk, Lilliefors, A–D", "Días y edad", "La variable sigue una distribución normal", "No la sigue", "$W$, $D$, $A^2$"),
        ("Spearman", "Edad y días", "$\\rho_s=0$", "$\\rho_s\\neq0$", "$\\rho_s$"),
        ("Mann–Whitney $U$", "Días según un factor de dos grupos", "Ambos grupos tienen la misma distribución de días", "Un grupo tiende a más días", "$U$; $r$"),
        ("Kruskal–Wallis + Holm", "Días según capítulo o región", "Todos los grupos tienen la misma distribución", "Al menos un grupo difiere", "$H$; $\\varepsilon^2$"),
        ("$\\chi^2$ de independencia", "Factor y estadía prolongada (bivariado)", "Son independientes", "No son independientes", "$\\chi^2$; $V$"),
        ("$F$ global (ANOVA)", "Modelo lineal M3 en $\\ln(\\text{días})$", "Todos los $\\beta_j=0$ salvo el intercepto", "Algún $\\beta_j\\neq0$", "$F$"),
        ("$F$ parcial", "Cada bloque M1 a M3 y cada factor retirado de M3", "Los coeficientes del factor valen 0", "Alguno es distinto de 0", "$F$; $\\eta^2_{\\text{parcial}}$"),
        ("$t$ (EE clásico, $\\text{HC3}$)", "Cada coeficiente de M3", "$\\beta_j=0$", "$\\beta_j\\neq0$", "$t$"),
    ],
    "guia_pruebas_titulo": "Cómo leer las pruebas y el criterio de relevancia",
    "guia_pruebas": [
        ("Cómo leer cada fila",
         "Cada fila une una prueba con las variables que evalúa, su hipótesis nula y alternativa, y el par "
         "estadístico–tamaño del efecto que usamos en las pestañas de análisis."),
        ("Por qué no basta el valor-p",
         "Con 968.098 registros, diferencias de décimas de día dan $p < 0{,}001$ y rechazan $H_0$. Por eso exigimos además "
         "$\\eta^2_{\\text{parcial}} \\ge 0{,}01$ en M3, es decir, que el factor explique al menos el 1 % de la variación "
         "que los demás no explican, antes de hablar de relevancia práctica."),
    ],
    "flujo_titulo": "Diagrama metodológico",
    "resumen_flujo": (
        "El punto de quiebre está entre las pruebas de a pares y la regresión: ahí pasamos a $\\ln(\\text{días})$ para "
        "controlar la cola larga y después evaluamos el modelo."
    ),
    "flujo": [
        ("Problema", "duración de la estadía"),
        ("Datos", "DEIS 2020, [[n]] egresos"),
        ("Procesamiento", "filtros, variables y exploración"),
        ("Asociaciones", "pruebas de a pares y tamaño del efecto"),
        ("Modelamiento", "regresión lineal en $\\ln$ y sensibilidad"),
        ("Evaluación", "supuestos, $F$, $\\text{BIC}$, $\\eta^2_{\\text{parcial}}$ y ranking"),
    ],
    "guia_flujo_titulo": "Ruta metodológica paso a paso",
    "guia_flujo": [
        ("De los datos crudos al modelo M3",
         "Leemos de izquierda a derecha: acotamos el problema, filtramos los [[n]] egresos del DEIS 2020, revisamos "
         "asimetrías, medimos cruces bivariados (de a dos variables), ajustamos M0 a M3 y evaluamos los supuestos."),
        ("De pruebas no paramétricas a ln(días)",
         "$W$, $D$ y $A^2$ rechazan la normalidad por la cola extrema, así que en los cruces usamos $U$, $H$ y $\\rho_s$, "
         "que no suponen una distribución normal. En M0 a M3 pasamos a $\\ln(\\text{días})$ para comprimir esa cola, y los "
         "errores $\\text{HC3}$ corrigen el error estándar cuando la varianza no es constante."),
        ("Qué miden los criterios de evaluación",
         "El $\\text{BIC}$ compara modelos y penaliza agregar variables, así que gana el de menor valor. La $F$ global y la "
         "parcial dicen si el conjunto y cada factor aportan. El $\\eta^2_{\\text{parcial}}$ indica cuánto explica cada "
         "factor, y con eso armamos el ranking."),
    ],
    "datos_titulo": "Datos",
    "datos": [
        "Usamos los egresos hospitalarios 2020 del DEIS–MINSAL para beneficiarios FONASA de 1 a 365 días. Excluimos [[excl]] casos ([[pct_excl]] %) de más de un año para evitar distorsiones extremas, quedando [[n]] egresos.",
        "La unidad de análisis es el egreso, no la persona: alguien hospitalizado dos veces aparece dos veces. Además, la condición al alta solo se conoce al cerrar la estadía, así que el modelo describe asociaciones ya ocurridas y no sirve para decidir al momento del ingreso.",
    ],
    "vars_titulo": "Variables del estudio",
    "resumen_vars": (
        "Cada variable aparece con su tipo y la razón de incluirla. La edad entra como $\\text{edad}$ y $\\text{edad}^2$ "
        "porque esperamos una curva, no una recta."
    ),
    "vars_cols": ["Variable", "Tipo", "Justificación"],
    "vars": [
        ("Días de estada", "Numérica", "Respuesta de la regresión, modelada como $\\ln(\\text{días})$"),
        ("Estadía prolongada", "Categórica (Sí/No)", "Corte en $P_{90} = [[corte]]$ días; solo para describir y en cruces $\\chi^2$ de a pares"),
        ("Capítulo CIE-10", "Categórica (21)", "Aproxima el cuadro clínico principal, porque la base no trae peso GRD (medida de complejidad que usa el sistema de pago)"),
        ("Cirugía", "Categórica (Sí/No)", "Separa egresos quirúrgicos de hospitalizaciones médicas"),
        ("Condición de egreso", "Categórica (vivo/fallecido)", "Refleja desenlaces extremos, conocidos al cerrar la estadía"),
        ("Edad", "Numérica (punto medio del tramo)", "Entra como $\\text{edad}$ y $\\text{edad}^2$ para captar su curva"),
        ("Sexo", "Categórica", "Variable demográfica básica de control"),
        ("Nacionalidad", "Categórica (2)", "Se evalúa en sensibilidad frente a M3"),
        ("Etnia", "Categórica (Sí/No)", "Se evalúa en sensibilidad por pertenencia a pueblo originario"),
        ("Establecimiento", "Categórica (SNSS/No SNSS)", "Distingue la red pública asistencial del resto de prestadores"),
        ("Región", "Categórica (16)", "Capta diferencias territoriales de oferta de camas y derivación"),
    ],
    "guia_vars_titulo": "Alcance y límites de las variables",
    "guia_vars": [
        ("Siete variables en M3, dos a prueba",
         "De las 11 variables, siete entran a M3. Nacionalidad y etnia se evalúan aparte como sensibilidad, y la estadía "
         "prolongada sirve solo para describir la concentración y las pruebas $\\chi^2$."),
        ("Vacíos de origen en la base DEIS",
         "Los datos abiertos no traen peso GRD ni gravedad clínica, así que el capítulo CIE-10 y la condición al alta cargan "
         "con esa señal. La edad viene en tramos de diez años y entra con su marca de clase, es decir, el punto medio del tramo."),
    ],
}


def _num(x, dec=1):
    return graficos.num(x, dec)


def llenar(texto: str, valores: dict) -> str:
    """Reemplaza [[clave]] por su valor ya formateado (no usa llaves: el LaTeX las necesita)."""
    for k, v in valores.items():
        texto = texto.replace(f"[[{k}]]", str(v))
    return texto


def valores(c: dict) -> dict:
    return {
        "n": _num(c["n"], 0),
        "pct_prol": _num(c["pct_prolongadas"], 1),
        "pct_cama": _num(c["pct_dias_cama"], 1),
        "corte": _num(c["percentil_90_dias"], 0),
        "mediana": _num(c["descriptivos"]["dias_estada"]["median"], 0),
        "excl": _num(c["excluidos_mas_365"], 0),
        "pct_excl": _num(c["pct_excluidos"], 2),
    }


def _tabla(cols, filas, nombre, v=None):
    v = v or {}
    cab = ui.tags.tr(*[ui.tags.th(c) for c in cols])
    cuerpo = [ui.tags.tr(*[ui.tags.td(llenar(x, v)) for x in f]) for f in filas]
    return ui.div(
        ui.tags.table(ui.tags.thead(cab), ui.tags.tbody(*cuerpo), class_="table table-sm tabla-texto"),
        class_="tabla-responsive", tabindex="0", role="region", **{"aria-label": nombre},
    )


def _svg_conector():
    return ui.tags.div(
        ui.tags.svg(
            Tag("path", d="M2 8h20m-5-5 6 5-6 5", fill="none", stroke="currentColor",
                **{"stroke-width": "1.75", "stroke-linecap": "round", "stroke-linejoin": "round"}),
            viewBox="0 0 28 16", width="28", height="16", class_="flujo-svg", aria_hidden="true",
        ),
        class_="flujo-flecha",
        aria_hidden="true",
    )


def _svg_icono_etapa(idx: int):
    rutas = [
        "M9 3v12M3 9h12M5 5l8 8",                              # Problema (eje / foco)
        "M3 5h12M3 9h12M3 13h8",                               # Datos (registros)
        "M3 4h12l-4.5 5.5v4l-3 1.5v-5.5z",                     # Procesamiento (embudo)
        "M4 13L14 5M5 5.5a1.5 1.5 0 1 0 0 .01M13 12.5a1.5 1.5 0 1 0 0 .01",  # Asociaciones
        "M3 14L7 10l4 2 4-7",                                  # Modelamiento (curva)
        "M3 9l4 4 8-8",                                        # Evaluacion (verificacion)
    ]
    return ui.tags.svg(
        Tag("path", d=rutas[idx % len(rutas)], fill="none", stroke="currentColor",
            **{"stroke-width": "1.75", "stroke-linecap": "round", "stroke-linejoin": "round"}),
        viewBox="0 0 18 18", width="18", height="18", class_="flujo-icono", aria_hidden="true",
    )


def _flujo(v):
    pasos = []
    for i, (t, s) in enumerate(TEXTOS["flujo"]):
        if i:
            pasos.append(_svg_conector())
        pasos.append(
            ui.tags.div(
                ui.div(_svg_icono_etapa(i), ui.tags.strong(t), class_="flujo-cabecera"),
                ui.tags.span(llenar(s, v), class_="flujo-desc"),
                class_="flujo-caja",
                style=f"--orden: {i}",
            )
        )
    return ui.tags.div(*pasos, class_="flujo")


def _par_subcard(item):
    """Normaliza una subcard desde tupla (titulo, texto) o dict {'titulo', 'texto'}."""
    if isinstance(item, dict):
        return item["titulo"], item["texto"]
    return item[0], item[1]


def rejilla_subcards(items, v: dict | None = None, pila: bool = False):
    """Grilla responsiva de subcards visuales (.guia-rejilla / .guia-subcard)."""
    v = v or {}
    cls = "guia-rejilla guia-rejilla--pila" if pila else "guia-rejilla"
    cards = []
    for item in items:
        sub, txt = _par_subcard(item)
        cards.append(
            ui.div(
                ui.p(llenar(sub, v), class_="guia-subcard-titulo"),
                ui.p(llenar(txt, v)),
                class_="guia-subcard",
            )
        )
    return ui.div(*cards, class_=cls)


def guia_lectura(titulo: str, items, v: dict | None = None, pila: bool = False):
    """Bloque editorial de lectura guiada: rejilla de subcards o fallback simple."""
    v = v or {}
    if items and isinstance(items[0], str):
        return ui.div(
            ui.p(titulo, class_="guia-lectura-titulo"),
            *[ui.p(llenar(p, v)) for p in items],
            class_="guia-lectura guia-lectura--simple",
        )
    return ui.div(
        ui.p(titulo, class_="guia-lectura-titulo"),
        rejilla_subcards(items, v, pila=pila),
        class_="guia-lectura",
    )


def formula_latex(expr: str, v: dict | None = None):
    """Caja destacada para ecuaciones LaTeX en bloque."""
    return ui.div(llenar(expr, v or {}), class_="formula-latex")


def _problema_html(c: dict):
    v = valores(c)
    return ui.div(
        ui.p(llenar(TEXTOS["problema"], v)),
        ui.p(llenar(TEXTOS["prolongada"], v)),
        formula_latex(TEXTOS["formula_conc"], v),
    )


def _concentracion_html(c: dict):
    """Compara dos proporciones con denominadores distintos de la base completa."""
    def fila(etiqueta, porcentaje):
        return ui.div(
            ui.div(ui.span(etiqueta), ui.tags.strong(f"{_num(porcentaje, 1)} %"),
                   class_="concentracion-cabecera"),
            ui.tags.svg(
                Tag("rect", x="0", y="0", width="100", height="6", rx="1", fill="#d3dadb"),
                Tag("line", x1="25", y1="0", x2="25", y2="6", stroke="#ffffff", **{"stroke-width": "0.6"}),
                Tag("line", x1="50", y1="0", x2="50", y2="6", stroke="#ffffff", **{"stroke-width": "0.6"}),
                Tag("line", x1="75", y1="0", x2="75", y2="6", stroke="#ffffff", **{"stroke-width": "0.6"}),
                Tag("rect", x="0", y="0", width=str(float(porcentaje)), height="6", rx="1", fill=graficos.CARGA[3], class_="concentracion-fill"),
                viewBox="0 0 100 6", preserveAspectRatio="none", class_="concentracion-barra", aria_hidden="true",
            ),
            class_="concentracion-fila",
        )

    return ui.tags.figure(
        ui.tags.figcaption("La concentración de los días-cama", class_="concentracion-titulo"),
        ui.p(f"Estadías de más de {_num(c['percentil_90_dias'], 0)} días", class_="concentracion-corte"),
        fila("Del total de egresos", c["pct_prolongadas"]),
        fila("Del total de días-cama", c["pct_dias_cama"]),
        ui.p("Cada barra representa el 100 % de su propio total.", class_="concentracion-nota"),
        class_="concentracion",
    )


def _datos_html(c: dict):
    v = valores(c)
    return ui.div(*[ui.p(llenar(p, v)) for p in TEXTOS["datos"]])


def _hipotesis():
    gen = ui.tags.ul(*[ui.tags.li(ui.tags.strong(h), ": ", t) for h, t in TEXTOS["hip_general"]])
    grp = ui.tags.ul(
        *[ui.tags.li(ui.tags.strong(f"{h0} y {h1}"), f" ({g}): {f}") for h0, h1, g, f in TEXTOS["hip_grupos"]]
    )
    return ui.div(
        ui.h4(TEXTOS["hip_titulo"]), ui.p(TEXTOS["hip_intro"]), gen,
        ui.p(TEXTOS["hip_grupos_intro"]), grp,
        componente.componente(
            TEXTOS["pruebas_titulo"],
            ui.h5(TEXTOS["pruebas_titulo"]),
            _tabla(TEXTOS["pruebas_cols"], TEXTOS["pruebas"], TEXTOS["pruebas_titulo"]),
            abierto=True,
            resumen=TEXTOS["resumen_pruebas"],
            detalle=ui.div(ui.p(TEXTOS["pruebas_nota"]), ui.output_ui("guia_pruebas")),
        ),
    )


def _muestras(pares) -> ui.Tag:
    """Fila de muestras de color, cada una con su texto al lado."""
    return ui.tags.ul(*[ui.tags.li(ui.span(class_="muestra", style=f"background:{c}"), t) for c, t in pares],
                      class_="muestras")


def codigo_color() -> ui.Tag:
    """Clave del código de color: qué significa cada familia en todas las pestañas."""
    g = graficos
    tarjetas = [
        ("Carga de días-cama",
         "Más oscuro, más carga: el % de estadías de más de 15 días del grupo. Va de arena a rojo profundo, el mismo "
         "rojo de las torres de estadía prolongada en la sala de la portada.",
         list(zip(g.CARGA, g.TRAMOS_CARGA))),
        ("Semáforo de supuestos",
         "Estado de cada supuesto del modelo. El ícono y la palabra repiten el color, así que se lee también sin él.",
         [(c, f"{i} {p}") for c, i, p in g.ESTADO.values()]),
        ("Más o menos días",
         "Cambio frente a la referencia: rojo alarga la estadía, turquesa la acorta y gris es un intervalo que cruza el 0.",
         [(g.MENOS, "menos días"), (g.NEUTRO, "sin diferencia clara"), (g.MAS, "más días")]),
        ("Macrozonas",
         "Las 16 regiones van de norte a sur en cinco macrozonas, cada una con el color de su paisaje.",
         [(c, z) for z, c in g.ZONAS.items()]),
    ]
    return ui.div(
        ui.div(*[ui.div(ui.p(t, class_="guia-subcard-titulo"), ui.p(x), _muestras(m), class_="guia-subcard")
                 for t, x, m in tarjetas], class_="guia-rejilla"),
        class_="guia-lectura codigo-color",
    )


@module.ui
def pestana_ui():
    return ui.div(
        ui.h3(TEXTOS["titulo"]),
        ui.tags.section(
            ui.div(
                ui.h4(TEXTOS["pregunta_titulo"]),
                ui.tags.blockquote(TEXTOS["pregunta"]),
                ui.output_ui("problema"),
                class_="hero-contenido",
            ),
            ui.div(
                ui.div(
                    # Poster = last frame: without JS or with reduced motion the still is the final state.
                    ui.tags.video(
                        src="assets/hero-sala.webm",
                        poster="assets/hero-3d-poster.webp",
                        id="hero-3d-img",
                        width="560",
                        height="380",
                        muted="",
                        playsinline="",
                        preload="auto",
                        disablepictureinpicture="",
                        role="img",
                        aria_label=("Sala de 100 camas vista desde arriba. Cada cama resume el 1 % de los egresos y apila "
                                    "una ficha por día de estada. Las 9 camas en rojo, de estadía prolongada, suman cerca "
                                    "de la mitad de las fichas."),
                    ),
                    ui.p("100 camas, cada una el 1 % de los egresos. Una ficha por día: las 9 rojas apilan casi la mitad.",
                         class_="hero-3d-meta"),
                    id="hero-3d-stage",
                    class_="hero-3d-stage",
                ),
                componente.componente(
                    TEXTOS["titulo_conc"],
                    ui.output_ui("concentracion"),
                    resumen=ui.output_ui("resumen_conc"),
                    detalle=ui.output_ui("guia_concentracion"),
                ),
                class_="hero-datos",
            ),
            class_="hero-investigacion",
        ),
        ui.tags.section(_hipotesis(), class_="seccion-editorial"),
        ui.tags.section(
            ui.h4(TEXTOS["flujo_titulo"]),
            componente.componente(
                TEXTOS["flujo_titulo"],
                ui.output_ui("flujo"),
                abierto=True,
                resumen=TEXTOS["resumen_flujo"],
                detalle=ui.output_ui("guia_flujo"),
            ),
            class_="seccion-editorial",
        ),
        ui.tags.section(
            ui.h4(TEXTOS["datos_titulo"]), ui.output_ui("datos"),
            componente.componente(
                TEXTOS["vars_titulo"],
                ui.h5(TEXTOS["vars_titulo"]),
                ui.output_ui("variables"),
                abierto=True,
                resumen=TEXTOS["resumen_vars"],
                detalle=ui.output_ui("guia_vars"),
            ),
            class_="seccion-editorial",
        ),
        ui.tags.section(ui.h4(TEXTOS["color_titulo"]), ui.p(TEXTOS["color_intro"]), codigo_color(),
                        class_="seccion-editorial"),
        class_="pestana-texto",
    )


@module.server
def pestana_server(input, output, session, d):
    c = d.cifras

    @output
    @render.ui
    def problema():
        return _problema_html(c)

    @output
    @render.ui
    def concentracion():
        return _concentracion_html(c)

    @output
    @render.ui
    def resumen_conc():
        return ui.p(llenar(TEXTOS["resumen_conc"], valores(c)))

    @output
    @render.ui
    def guia_concentracion():
        return guia_lectura(TEXTOS["guia_conc_titulo"], TEXTOS["guia_conc"], valores(c))

    @output
    @render.ui
    def guia_pruebas():
        return guia_lectura(TEXTOS["guia_pruebas_titulo"], TEXTOS["guia_pruebas"], valores(c))

    @output
    @render.ui
    def flujo():
        return _flujo(valores(c))

    @output
    @render.ui
    def guia_flujo():
        return guia_lectura(TEXTOS["guia_flujo_titulo"], TEXTOS["guia_flujo"], valores(c))

    @output
    @render.ui
    def datos():
        return _datos_html(c)

    @output
    @render.ui
    def variables():
        return _tabla(TEXTOS["vars_cols"], TEXTOS["vars"], TEXTOS["vars_titulo"], valores(c))

    @output
    @render.ui
    def guia_vars():
        return guia_lectura(TEXTOS["guia_vars_titulo"], TEXTOS["guia_vars"], valores(c))
