"""Pestana Conclusiones: contraste de hipotesis, ranking, limitaciones e implicancias."""
from __future__ import annotations

from htmltools import Tag
from shiny import module, render, ui

import componente
import graficos
from p_contexto import formula_latex, guia_lectura, llenar, rejilla_subcards

UMBRAL = 0.01  # criterio de relevancia del informe: eta2 parcial >= 0,01

TEXTOS = {
    "titulo": "Conclusiones",
    "resp_titulo": "Respuesta a la pregunta y contraste de hipótesis",
    "resp": (
        "La pregunta es qué factores clínicos, demográficos y del sistema de salud se asocian con la duración. "
        "La prueba $F$ global de M3 ($F=[[F_global]]$, $p<0{,}001$ frente al modelo nulo M0) rechaza la $H_0$ general, "
        "así que sí hay asociación. La tabla revisa bloque por bloque sobre los 968.098 egresos, con pruebas $F$ parciales "
        "de tipo II y la $t$ de la edad, a nivel $\\alpha=0{,}05$ y con $p<0{,}001$ salvo donde se indica."
    ),
    "hip_comp": "Contraste de hipótesis por bloque",
    "hip_cols": ["Hipótesis", "Prueba en M3", "Decisión", "Relevancia: $\\eta^2_{\\text{parcial}}\\ge 0{,}01$"],
    "hip_resumen": (
        "La última columna pide $\\eta^2_{\\text{parcial}} \\ge 0{,}01$: la parte de la variación de $\\ln(\\text{días})$ "
        "que aporta cada bloque, descontados los demás."
    ),
    "hip_cierre": (
        "Rechazamos las cuatro nulas, pero solo el capítulo CIE-10, la edad y el establecimiento tienen un peso que importe "
        "en la práctica. Cirugía, fallecido, sexo y región dan un $F$ significativo, pero su $\\eta^2_{\\text{parcial}}$ "
        "queda bajo ese piso. Con casi un millón de egresos, casi cualquier diferencia sale significativa, por eso miramos la magnitud."
    ),
    "guia_hip_titulo": "Lectura del contraste de hipótesis",
    "guia_hip": [
        ("Significancia frente a magnitud",
         "El $F$ (o la $t$) dice si el bloque aporta más de lo que daría una relación nula. El $\\%\\Delta$ dice cuánto cambia "
         "la duración. Y la $\\eta^2_{\\text{parcial}}$ dice qué parte de la variación de $\\ln(\\text{días})$ se pierde al retirar "
         "ese bloque. Con tantos casos el valor-$p$ casi siempre sale bajo, así que la magnitud es lo que decide."),
        ("Dónde está la señal en H₀a, H₀b y H₀c",
         "En $H_{0a}$ el capítulo CIE-10 llega a 0,074, mientras cirugía y fallecimiento quedan bajo 0,01. En $H_{0b}$ la edad "
         "pesa 0,035 y en $H_{0c}$ el establecimiento SNSS llega a 0,041."),
        ("Por qué H₀d rechaza pero no sirve",
         "Nacionalidad y etnia dan $F = 7{,}49$ con $p = 0{,}0006$, así que rechazan $H_{0d}$. Pero su "
         "$\\eta^2_{\\text{parcial}} = 0{,}000015$ es casi nulo y el BIC sube $+12{,}6$ al agregarlas, o sea, el modelo empeora. "
         "Por eso quedan fuera."),
    ],
    "rank_titulo": "Ranking de los factores",
    "rank_intro": (
        "Todos los factores de M3 dan $p<0{,}001$, así que el valor-$p$ no sirve para ordenarlos. Usamos el "
        "$\\eta^2_{\\text{parcial}}$ de cada uno. Ojo con un sesgo: no penaliza grados de libertad, así que un factor de 21 "
        "niveles como el capítulo suma más que uno binario. Solo tres superan 0,01, el umbral de efecto pequeño de Cohen."
    ),
    "rank_comp": "Ranking de factores por η² parcial",
    "rank_resumen": (
        "Cada barra es la parte de la variación de $\\ln(\\text{días})$ que aporta un factor, descontados los demás. "
        "La línea marca 0,01."
    ),
    "rank_cierre": (
        "Solo con capítulo, establecimiento y edad, el $R^2_{\\text{aj.}}$ es [[r2_tres]], y el de M3 completo es [[r2_m3]]: "
        "la diferencia es menor a un punto. Cirugía y condición al alta quedan al final porque, una vez dentro el capítulo CIE-10, "
        "su aporte propio casi desaparece. Nacionalidad y etnia quedan fuera del modelo: su $\\eta^2_{\\text{parcial}}$ es "
        "[[eta_nac]]. La tabla completa con $F$ y valor-$p$ está en Modelos."
    ),
    "guia_rank_titulo": "Lectura del ranking y caída de cirugía",
    "guia_rank": [
        ("Barras frente a la línea punteada",
         "Cada barra es el $\\eta^2_{\\text{parcial}}$ de un factor: cuánto cae la explicación de $\\ln(\\text{días})$ al retirarlo "
         "de M3. Solo tres barras en color cruzan la línea de 0,01."),
        ("Tres factores sostienen el modelo",
         "Capítulo CIE-10 con 0,0740, establecimiento con 0,0409 y edad con 0,0347. Cada uno recoge una dimensión distinta: la "
         "mezcla clínica, la diferencia entre la red SNSS y otros prestadores, y el perfil etario. Los cuatro grises quedan bajo 0,01."),
        ("Por qué cirugía y fallecido caen al fondo",
         "Ambos se concentran en diagnósticos precisos, con una $V$ de Cramér de 0,4287 para cirugía y 0,2611 para fallecido. "
         "Esa $V$ va de 0 a 1 y mide la asociación entre variables categóricas. Al entrar el capítulo en M3, absorbe esa señal "
         "y deja a ambos con 0,0002 y 0,0001."),
    ],
    "concl_titulo": "Conclusiones",
    "concl": [
        ("Tres factores explican lo esencial",
         "El capítulo CIE-10, el establecimiento y la edad son los factores que más se asocian con la duración. Sexo, cirugía, "
         "condición al alta y región quedan bajo 0,01 al controlar por los demás."),
        ("Brecha entre la red SNSS y otros centros",
         "A igual diagnóstico, edad y región, los egresos de la red SNSS tienen una media geométrica de días [[snss]] mayor que "
         "los de establecimientos fuera del SNSS. Es una asociación ajustada; el registro no dice por qué."),
        ("Cuánto explica M3 y qué falta",
         "M3 explica el [[r2_m3_pct]] % de la variación de $\\ln(\\text{días})$, y las especificaciones más complejas llegan a "
         "[[r2_max_pct]] %. El resto probablemente responde a gravedad y comorbilidades, que el registro no trae."),
    ],
    "formula_geom": (
        "$$\\widehat{\\text{Media geométrica}} = \\exp\\!\\left(\\overline{\\ln(\\text{días})}\\right), \\qquad "
        "\\%\\Delta = 100\\,\\left(e^{\\hat\\beta_j} - 1\\right)$$"
    ),
    "impl_titulo": "Implicancias",
    "impl": [
        ("Grupos a revisar primero en gestión de camas",
         "Los trastornos mentales (capítulo F00-F99) muestran estadías ajustadas más largas: [[mental]] frente al capítulo "
         "digestivo de referencia. Junto con la red SNSS, son los grupos que más conviene mirar. Es una asociación: no dice que "
         "el diagnóstico o el establecimiento causen la estadía."),
        ("Lactantes con piso alto en la duración",
         "La mediana sube a partir de los 40 años, pero los menores de un año ya parten con [[med_lact]] días, frente a "
         "[[med_joven]] días en el tramo de 20 a 29 años. Ese piso inicial merece una mirada propia en la planificación."),
        ("Uso analítico, no decisión clínica",
         "Sin peso GRD ni puntaje de gravedad no se puede atribuir causalidad ni decidir sobre un paciente. Con esos datos sí "
         "podríamos separar complejidad clínica de gestión hospitalaria, que hoy van juntas en la misma asociación."),
    ],
    "lim_titulo": "Limitaciones",
    "lim": [
        ("Sin GRD ni independencia plena",
         "Faltan gravedad, comorbilidades e identificadores de paciente y de hospital. Los reingresos y la agrupación por centro "
         "hacen que los errores estándar salgan más estrechos de lo real, y con ellos los valores-$p$."),
        ("Corte en 365 días y edad en tramos",
         "Excluir estadías de más de 365 días deja fuera casos largos legítimos, y el modelo no se reestimó con ellos. La edad "
         "viene en 11 tramos decenales, así que la curva de edad tiene poco detalle."),
        ("Solo FONASA en año de pandemia",
         "La base no cubre afiliados a ISAPRE. Además, 2020 tuvo menos cirugías electivas que 2019 por COVID-19, así que estas "
         "asociaciones no se trasladan sin ajuste a otros años o seguros."),
        ("Parte exploratoria en el modelamiento",
         "Comparar especificaciones alternativas (M4 a M6) y filtrar variables antes del modelo hace que parte de la etapa final "
         "sea exploratoria. Sus valores-$p$ se leen con esa cautela."),
    ],
}


def _num(x, dec=1):
    return graficos.num(x, dec)


def _pct(x, dec=1):
    return f"{'+' if x >= 0 else '−'}{_num(abs(x), dec)} %"


def _p(x):
    return "p<0,001" if x < 0.001 else f"p={_num(x, 4)}"


def _eta(c, clave, dec=4):
    return _num(c["eta2_parciales"][clave]["η² parcial"], dec)


def valores(c: dict) -> dict:
    ep, co = c["eta2_parciales"], c["coef"]
    tres = c["forward_pasos"]["3"]["R² ajustado"]
    tr = c["mediana_dias_por_tramo"]
    return {
        "F_global": _num(c["anova"]["Regresión"]["F"], 0),
        "r2_tres": _num(tres, 3),
        "r2_m3": _num(c["modelos"]["M3"]["R² aj."], 3),
        "r2_m3_pct": _num(c["modelos"]["M3"]["R²"] * 100, 1),
        "r2_max_pct": _num(max(e["R² aj."] for e in c["especificaciones"].values()) * 100, 1),
        "snss": _pct(co["establecimiento: SNSS"]["%Δ"]),
        "mental": _pct(co["capitulo: F00-F99"]["%Δ"]),
        "med_lact": _num(tr["menor de un año"], 0),
        "med_joven": _num(tr["20 a 29"], 0),
        "eta_nac": _num(c["sensibilidad_variables"]["M3 + nacionalidad + etnia"]["η² parcial"], 5),
    }


def filas_hipotesis(c: dict) -> list[tuple[str, str, str, str]]:
    """Tabla de contraste: nulas del informe con los numeros de cifras."""
    f, co = c["ftest"], c["coef"]
    sv = c["sensibilidad_variables"]
    nac = sv["M3 + nacionalidad + etnia"]
    dbic = nac["BIC"] - sv["M3"]["BIC"]
    F = lambda k: _num(f[k]["F"], 0)  # noqa: E731
    return [
        ("$H_{0a}$ clínicos",
         f"Capítulo $F={F('capitulo')}$; cirugía $F={F('cirugia')}$; fallecido $F={F('fallecido')}$",
         "Rechaza $H_{0a}$",
         f"Capítulo sí ({_eta(c, 'capítulo', 3)}). Cirugía y fallecido no ({_eta(c, 'cirugía')} y {_eta(c, 'fallecido')})"),
        ("$H_{0b}$ demográficos",
         f"Edad {_pct(co['edad_c']['%Δ'], 2)} por año, $t={_num(co['edad_c']['t'], 1)}$; sexo $F={F('sexo')}$",
         "Rechaza $H_{0b}$",
         f"Edad sí ({_eta(c, 'edad (edad y edad²)', 3)}). Sexo no ({_eta(c, 'sexo')})"),
        ("$H_{0c}$ sistema de salud",
         f"SNSS {_pct(co['establecimiento: SNSS']['%Δ'])}, $F={F('establecimiento')}$; región $F={F('region')}$",
         "Rechaza $H_{0c}$",
         f"Establecimiento sí ({_eta(c, 'establecimiento', 3)}). Región no ({_eta(c, 'región')})"),
        ("$H_{0d}$ sensibilidad",
         f"Nacionalidad y etnia, $F={_num(nac['F parcial'], 2)}$, ${_p(nac['valor-p'])}$",
         "Rechaza $H_{0d}$" if nac["valor-p"] < 0.05 else "No rechaza $H_{0d}$",
         f"No ({_num(nac['η² parcial'], 5)}); el BIC sube {_num(dbic, 1)}"),
    ]


def _tabla(cols, filas, nombre):
    return ui.div(
        ui.tags.table(
            ui.tags.thead(ui.tags.tr(*[ui.tags.th(x) for x in cols])),
            ui.tags.tbody(*[ui.tags.tr(*[ui.tags.td(x) for x in f]) for f in filas]),
            class_="table table-sm tabla-texto",
        ),
        class_="tabla-responsive", tabindex="0", role="region", **{"aria-label": nombre},
    )


def _svg_ranking(c: dict):
    """Grafico vectorial geometrico del eta2 parcial frente al umbral 0,01."""
    orden = sorted(c["eta2_parciales"].items(), key=lambda kv: -kv[1]["η² parcial"])
    max_v = max(v["η² parcial"] for _, v in orden)
    escala = max(max_v, 0.08)
    alto_fila = 28
    y0 = 20
    alto_total = y0 + len(orden) * alto_fila + 26
    x_ini, x_fin = 185, 560
    ancho = x_fin - x_ini
    x_umbral = x_ini + (UMBRAL / escala) * ancho

    elems = [
        Tag("line", x1=f"{x_umbral:.1f}", y1="12", x2=f"{x_umbral:.1f}", y2=str(alto_total - 20),
            stroke="#a94530", **{"stroke-width": "1.5", "stroke-dasharray": "4 3"}),
        Tag("text", "Umbral 0,01", x=f"{x_umbral + 5:.1f}", y="16", fill="#a94530",
            **{"font-size": "11", "font-weight": "700", "font-family": "Figtree, sans-serif"}),
    ]
    for i, (nombre, datos_f) in enumerate(orden):
        val = datos_f["η² parcial"]
        y = y0 + i * alto_fila
        w = max(2.0, (val / escala) * ancho)
        relevante = val >= UMBRAL
        fill = "#086c70" if relevante else "#6b7c82"
        etiqueta = nombre[0].upper() + nombre[1:]
        elems.extend([
            Tag("text", etiqueta, x="0", y=str(y + 15), fill="#132f38",
                **{"font-size": "12", "font-weight": "650" if relevante else "400", "font-family": "Figtree, sans-serif"}),
            Tag("rect", x=str(x_ini), y=str(y + 4), width=str(ancho), height="14", rx="2", fill="#e6efe9"),
            Tag("rect", x=str(x_ini), y=str(y + 4), width=f"{w:.1f}", height="14", rx="2", fill=fill, class_="svg-barra-eta"),
            Tag("text", _num(val, 4), x=f"{x_ini + w + 8:.1f}", y=str(y + 15), fill="#132f38",
                **{"font-size": "12", "font-weight": "700" if relevante else "500",
                   "font-family": "Figtree, sans-serif", "font-variant-numeric": "tabular-nums"}),
        ])

    return ui.tags.figure(
        ui.tags.svg(
            *elems,
            viewBox=f"0 0 640 {alto_total}",
            class_="svg-ranking-eta",
            role="img",
            **{"aria-label": "Gráfico vectorial del tamaño de efecto η² parcial por factor frente al umbral 0,01"},
        ),
        ui.tags.figcaption("Contribución única (η² parcial) respecto del criterio práctico 0,01", class_="svg-pie"),
        class_="figura-vectorial",
    )


def _cuerpo(c: dict):
    v = valores(c)
    return ui.div(
        ui.tags.section(
            ui.h4(TEXTOS["concl_titulo"]),
            rejilla_subcards(TEXTOS["concl"], v),
            formula_latex(TEXTOS["formula_geom"], v),
            class_="panel-destacado",
        ),
        ui.tags.section(
            ui.h4(TEXTOS["resp_titulo"]), ui.p(llenar(TEXTOS["resp"], v)),
            componente.componente(
                TEXTOS["hip_comp"],
                _tabla(TEXTOS["hip_cols"], filas_hipotesis(c), TEXTOS["resp_titulo"]),
                abierto=True,
                resumen=llenar(TEXTOS["hip_resumen"], v),
                detalle=guia_lectura(TEXTOS["guia_hip_titulo"], TEXTOS["guia_hip"], v),
            ),
            ui.p(TEXTOS["hip_cierre"]),
            class_="seccion-editorial",
        ),
        ui.tags.section(
            ui.h4(TEXTOS["rank_titulo"]), ui.p(TEXTOS["rank_intro"]),
            componente.componente(
                TEXTOS["rank_comp"],
                _svg_ranking(c),
                resumen=TEXTOS["rank_resumen"],
                detalle=guia_lectura(TEXTOS["guia_rank_titulo"], TEXTOS["guia_rank"], v),
            ),
            ui.p(llenar(TEXTOS["rank_cierre"], v)),
            class_="seccion-editorial",
        ),
        ui.tags.section(
            ui.h4(TEXTOS["impl_titulo"]),
            rejilla_subcards(TEXTOS["impl"], v),
            class_="seccion-editorial",
        ),
        ui.tags.section(
            ui.h4(TEXTOS["lim_titulo"]),
            rejilla_subcards(TEXTOS["lim"]),
            class_="seccion-editorial",
        ),
    )


@module.ui
def pestana_ui():
    return ui.div(ui.h3(TEXTOS["titulo"]), ui.output_ui("cuerpo"), class_="pestana-texto")


@module.server
def pestana_server(input, output, session, d):
    @output(suspend_when_hidden=False)
    @render.ui
    def cuerpo():
        return _cuerpo(d.cifras)
