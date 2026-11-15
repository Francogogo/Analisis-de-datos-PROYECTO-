"""Pestana Modelos: modelos anidados, ANOVA, ranking de factores, coeficientes, especificaciones y forward."""
from __future__ import annotations

import math

import pandas as pd
from shiny import module, render, ui

import componente
import graficos

TEXTOS = {
    "titulo": "Modelos de regresión lineal",
    "intro": (
        "Ajustamos regresiones lineales por mínimos cuadrados ordinarios (MCO) sobre $\\ln(\\text{días})$, el "
        "logaritmo natural de la duración de la estadía, con los 968.098 egresos de la base completa. Usamos el "
        "logaritmo porque los días tienen una cola derecha muy larga y así la escala se vuelve manejable. Cada "
        "coeficiente $\\beta$ se lee entonces como un cambio porcentual sobre la media geométrica de los días, "
        "$\\%\\Delta = 100\\,(e^{\\beta} - 1)$, manteniendo fijas las demás variables."
    ),
    "formula_m3": (
        "$$\\begin{aligned}\n"
        "\\widehat{\\ln(\\text{días})}_i &= \\beta_0 + \\sum \\beta_c\\,\\text{cap}_{ic} "
        "+ \\beta_{\\text{cir}}\\,\\text{cir}_i + \\beta_{\\text{fall}}\\,\\text{fall}_i \\\\\n"
        "&\\quad + \\beta_1\\,\\text{edad}_{c,i} + \\beta_2\\,\\text{edad}_{c,i}^2 "
        "+ \\beta_{\\text{hom}}\\,\\text{hom}_i + \\beta_{\\text{snss}}\\,\\text{snss}_i "
        "+ \\sum \\beta_r\\,\\text{reg}_{ir}\n"
        "\\end{aligned}$$\n"
        "$$\\%\\Delta = 100\\,(e^{\\beta} - 1), \\qquad \\text{edad}_c = \\text{edad} - 45{,}01$$"
    ),
    "anidados_titulo": "Modelos anidados M0 a M3",
    "anidados_resumen": (
        "Cada modelo suma un bloque de variables al anterior. El $R^2$ ajustado, que descuenta los parámetros "
        "que se agregan, llega a 0,1980 en M3, y el BIC, que también penaliza parámetros, es el más bajo de la serie."
    ),
    "anidados": (
        "M0 solo tiene el intercepto ($k = 1$). M1 suma los factores clínicos: capítulo CIE-10, cirugía y condición "
        "de egreso. M2 agrega la edad, con $\\text{edad}_c$ y $\\text{edad}_c^2$ para permitir una curva, y el sexo. "
        "M3 completa el cuadro con establecimiento y región. Comparamos los modelos con el $R^2_{\\text{aj.}}$, que "
        "descuenta la cantidad de parámetros $k$, y con el criterio de información bayesiano ($\\text{BIC}$), que "
        "castiga cada parámetro con $\\ln(n)$ y por eso favorece los modelos más simples."
    ),
    "formula_bic": "$$\\text{BIC} = n\\ln\\!\\left(\\frac{\\text{SCR}}{n}\\right) + k\\ln(n), \\qquad \\Delta\\text{BIC} = \\text{BIC}_{m} - \\text{BIC}_{m-1}$$",
    "metrica_etiqueta": "Métrica para comparar los modelos",
    "metricas": {"R² aj.": "R² ajustado", "BIC": "BIC"},
    "modelos_cols": ["Modelo", "$k$", "$R^2$", "$R^2_{\\text{aj.}}$", "$\\text{BIC}$", "$\\Delta\\text{BIC}$", "$F$ parcial", "$\\text{gl}$", "Valor-$p$"],
    "anova_titulo": "Tabla ANOVA de M3",
    "anova_resumen": (
        "La prueba $F$ global compara lo que explica M3 con lo que queda como residuo. Con $F = 5.830$ se rechaza "
        "que todas las pendientes sean cero."
    ),
    "anova": (
        "Descompusimos la variación total de $\\ln(\\text{días})$ en la parte que explica M3 y la residual. El "
        "valor-$p$ es la probabilidad de obtener un $F$ igual o mayor si $H_0$ fuera verdadera, es decir, si todas "
        "las pendientes fueran cero. Aquí queda por debajo de 0,001."
    ),
    "anova_cols": ["Fuente", "Suma de cuadrados $\\text{SC}$", "$\\text{gl}$", "Cuadrado medio $\\text{CM}$", "$F$", "Valor-$p$"],
    "bloques_titulo": "Tamaño de efecto por bloque",
    "bloques_resumen": (
        "El $\\eta^2$ secuencial es la proporción de variación que agrega cada bloque al anterior. El bloque clínico, "
        "que entra primero, concentra la mayor parte."
    ),
    "bloques": (
        "El $\\eta^2$ es la proporción de la variación de $\\ln(\\text{días})$ que explica cada bloque. Como depende "
        "del orden de entrada, comparamos cada bloque con el anterior y el total de M3 frente a M0. Según los cortes "
        "de Cohen para varianza explicada, un efecto es pequeño desde 0,01, mediano desde 0,06 y grande desde 0,14."
    ),
    "bloques_cols": ["Comparación", "$\\eta^2$", "Efecto (Cohen)"],
    "ranking_titulo": "Ranking de factores",
    "ranking_resumen": (
        "Capítulo CIE-10, establecimiento y edad superan el corte de efecto pequeño de 0,01. Cirugía queda al final, "
        "con un aporte propio casi nulo."
    ),
    "ranking": (
        "Como los factores están correlacionados entre sí, el $\\eta^2$ por bloques cambia según el orden en que "
        "entran. Para aislar el aporte único de cada uno en M3 usamos el $\\eta^2_{\\text{parcial}}$: cuánto cae el "
        "$R^2$ al retirar ese factor, en proporción a la varianza que quedaba sin explicar."
    ),
    "formula_eta2": "$$\\eta^2_{\\text{parcial}} = \\frac{R^2_{\\text{con}} - R^2_{\\text{sin}}}{1 - R^2_{\\text{sin}}}$$",
    "ranking_cols": ["Pos.", "Factor", "$\\eta^2_{\\text{parcial}}$", "Efecto (Cohen)", "$F$", "Valor-$p$"],
    "coef_titulo": "Coeficientes de M3",
    "coef_resumen": (
        "Cada punto es el cambio porcentual de los días frente al perfil base, con su intervalo de confianza al 95 %. "
        "Si el intervalo cruza el 0 %, el efecto no se distingue de cero con un 5 % de error."
    ),
    "coef": (
        "Cada fila compara una categoría contra el perfil base: capítulo K00-K93, Región Metropolitana de Santiago, "
        "mujer, establecimiento no SNSS, sin cirugía y egreso no fallecido. Dejamos fuera del gráfico la constante "
        "$\\beta_0 = 0{,}6001$, cuyo exponencial $e^{\\beta_0} \\approx 1{,}82$ días corresponde a ese perfil base a "
        "los 45,01 años. Mantenemos juntos $\\text{edad}_c$ y $\\text{edad}_c^2$ en la tabla porque forman una sola curva."
    ),
    "coef_se": "Error estándar del intervalo",
    "coef_se_op": {"clasico": "Clásico", "hc3": "Robusto (HC3)"},
    "coef_factor": "Factor",
    "coef_todos": "Todos",
    "coef_cols": ["Variable", "$\\beta$", "$\\text{EE}$", "$\\%\\Delta$", "$\\text{IC}_{95\\%}$ inf. $\\%\\Delta$", "$\\text{IC}_{95\\%}$ sup. $\\%\\Delta$", "Valor-$p$"],
    "espec_titulo": "Especificaciones alternativas M3 a M6",
    "espec": "El menor $\\text{BIC}$ corresponde a [[menor_bic]]. Evaluamos si esa mejora compensa la mayor complejidad.",
    "espec_metodo": (
        "Probamos tres modelos más complejos sobre M3 para ver si la especificación cambiaba las conclusiones. M4 "
        "suma edad por sexo y edad por fallecimiento, M5 agrega establecimiento por capítulo y M6 añade "
        "establecimiento por región."
    ),
    "espec_cols": ["Modelo", "$k$", "$R^2_{\\text{aj.}}$", "$\\text{AIC}$", "$\\text{BIC}$", "$\\Delta\\text{BIC}$", "$F$ parcial", "$\\text{gl}$", "Valor-$p$", "$\\eta^2_{\\text{parcial}}$"],
    "sens_titulo": "Sensibilidad: nacionalidad y etnia",
    "sens_resumen": (
        "Sumar nacionalidad y pertenencia a pueblo originario a M3 da un efecto estadísticamente significativo, pero "
        "casi nulo en la práctica."
    ),
    "sens": (
        "Contrastamos $H_0$: ambos coeficientes son cero. El valor-$p$ indica si el efecto es estadísticamente "
        "distinguible de cero; el $\\eta^2_{\\text{parcial}}$ indica cuánto importa en la práctica. Una cosa no "
        "garantiza la otra."
    ),
    "sens_cols": ["Modelo", "$k$", "$R^2_{\\text{aj.}}$", "$\\text{BIC}$", "$F$ parcial", "Valor-$p$", "$\\eta^2_{\\text{parcial}}$"],
    "fwd_titulo": "Selección forward por BIC",
    "fwd_resumen": (
        "Partiendo de M0, en cada paso entra el factor que más reduce el $\\text{BIC}$. El orden de entrada confirma "
        "el podio del ranking por $\\eta^2_{\\text{parcial}}$."
    ),
    "fwd": (
        "Para verificar la jerarquía de factores con un criterio que penaliza los parámetros, hicimos una selección "
        "forward desde M0: en cada paso entra el factor que más reduce el $\\text{BIC}$."
    ),
    "fwd_cols": ["Paso", "Entra", "$k$", "$\\text{BIC}$", "$R^2_{\\text{aj.}}$", "$\\Delta\\text{BIC}$", "$F$ parcial", "Valor-$p$"],
    "guias": {
        "anidados": {
            "titulo": "Por qué gana M3 y qué queda sin explicar",
            "subcards": [
                {
                    "titulo": "Cómo sube el ajuste hasta M3",
                    "texto": (
                        "De M0 a M3, el $R^2_{\\text{aj.}}$ sube de 0 a 0,1980 y el BIC baja de 2.814.166 a 2.601.099, "
                        "con $\\Delta\\text{BIC} = -42.565$. Al sumar establecimiento y región el cambio es significativo, "
                        "con $p < 0{,}001$."
                    ),
                },
                {
                    "titulo": "¿Sirve un R² ajustado de 0,198?",
                    "texto": (
                        "Sí, para aislar asociaciones poblacionales entre los 968.098 egresos cuando faltan el peso GRD "
                        "y la gravedad clínica. No sirve para proyectar cuántos días exactos va a estar internado un "
                        "paciente puntual, porque el 80 % de la variación queda fuera del modelo."
                    ),
                },
                {
                    "titulo": "Criterio para elegir parsimonia",
                    "texto": (
                        "Un $R^2_{\\text{aj.}}$ más alto indica más varianza explicada. Un BIC más bajo premia la "
                        "parsimonia, es decir, el modelo más simple que explica lo esencial, porque cada parámetro "
                        "descuenta $\\ln(n) \\approx 13{,}78$. Con ambos criterios gana M3."
                    ),
                },
            ],
        },
        "anova": {
            "titulo": "Prueba global y efecto del orden de entrada",
            "subcards": [
                {
                    "titulo": "Qué muestra la prueba F = 5.830",
                    "texto": (
                        "La suma de cuadrados total, $\\text{SCT} = 1.037.265{,}8$, se reparte en $\\text{SC}_{\\text{reg}} "
                        "= 205.399{,}1$ explicada por M3 y un residuo $\\text{SCR} = 831.866{,}7$. Así obtenemos "
                        "$F = 5.830$ y $p < 0{,}001$: la señal que capta M3 supera con holgura al ruido."
                    ),
                },
                {
                    "titulo": "Por qué el orden altera η² secuencial",
                    "texto": (
                        "El bloque clínico entra primero con $\\eta^2 = 0{,}1324$; después, demografía agrega 0,0338 y "
                        "red con región, 0,0432. Capítulo y cirugía están asociados, con $V = 0{,}4287$ (la V de Cramér "
                        "va de 0 a 1 y mide la asociación entre variables categóricas). Por eso el orden cambia el "
                        "$\\eta^2$ de cada bloque, y miramos el $\\eta^2_{\\text{parcial}}$."
                    ),
                },
            ],
        },
        "ranking": {
            "titulo": "Por qué solo tres factores superan el corte de Cohen",
            "subcards": [
                {
                    "titulo": "Qué muestra el corte en 0,01",
                    "texto": (
                        "Solo capítulo CIE-10 ($\\eta^2_{\\text{parcial}} = 0{,}0740$), establecimiento (0,0409) y edad "
                        "(0,0347) superan la línea de efecto pequeño. Los otros cuatro factores tienen $p < 0{,}001$ "
                        "sobre todo porque hay 968.098 egresos."
                    ),
                },
                {
                    "titulo": "¿Por qué cirugía cae al final en M3?",
                    "texto": (
                        "En cruces simples sí pesa: la correlación es $r = 0{,}22$ y la mediana baja de 4 días sin "
                        "cirugía a 2 días con cirugía. Pero las cirugías se concentran en capítulos específicos "
                        "($V = 0{,}4287$), así que buena parte de esa diferencia viene del diagnóstico. Al fijar el "
                        "capítulo CIE-10, operar o no operar cae a $\\eta^2_{\\text{parcial}} = 0{,}0002$, y su "
                        "coeficiente queda en −2,8 %."
                    ),
                },
                {
                    "titulo": "Grados de libertad y chequeo BIC",
                    "texto": (
                        "$\\eta^2_{\\text{parcial}}$ no castiga los grados de libertad, así que favorece al capítulo, "
                        "que tiene 20 parámetros frente a uno solo de establecimiento. Aun así, el forward por BIC, que "
                        "sí los castiga, llega al mismo podio."
                    ),
                },
            ],
        },
        "coef": {
            "titulo": "Lectura de efectos ajustados y robustez HC3",
            "subcards": [
                {
                    "titulo": "Cómo leer el gráfico forest",
                    "texto": (
                        "Cada punto es el cambio porcentual $\\%\\Delta = 100\\,(e^{\\hat{\\beta}} - 1)$ frente al perfil "
                        "base (K00-K93, RM, mujer, no SNSS, sin cirugía, vivo), con su $\\text{IC}_{95\\%}$. Si el "
                        "intervalo no cruza el 0 %, el efecto difiere de cero al 5 %."
                    ),
                },
                {
                    "titulo": "Efectos aislados en SNSS, F00-F99 y cirugía",
                    "texto": (
                        "Controlando el resto, SNSS se asocia con una estadía geométrica 70,0 % más larga "
                        "($\\beta = 0{,}5304$). Los trastornos mentales F00-F99 se asocian con +214,8 % frente a K00-K93 "
                        "($\\beta = 1{,}1469$). Cirugía, en cambio, queda en −2,8 % ($\\beta = -0{,}0282$)."
                    ),
                },
                {
                    "titulo": "Intervalos robustos HC3 frente al abanico",
                    "texto": (
                        "Cuando la varianza crece con el valor ajustado (heterocedasticidad), los errores estándar "
                        "clásicos quedan mal calibrados. El selector HC3 los corrige: ensancha F00-F99 (razón 1,36) y "
                        "fallecido (1,34), pero ningún efecto deja de ser significativo ni cambia de signo."
                    ),
                },
            ],
        },
        "sens": {
            "titulo": "Nacionalidad y etnia fuera de M3",
            "subcards": [
                {
                    "titulo": "Por qué quedan fuera",
                    "texto": (
                        "Agregarlas a M3 da $p < 0{,}001$ y $F = 7{,}49$, pero $\\eta^2_{\\text{parcial}} = 0{,}00002$ y "
                        "$\\Delta\\text{BIC} = +12{,}6$ (de 2.601.099 a 2.601.112). Son estadísticamente significativas, "
                        "pero su aporte práctico es nulo, así que no entran al modelo."
                    ),
                },
            ],
        },
        "extensiones": {
            "titulo": "Por qué mantenemos M3 frente a especificaciones más complejas",
            "subcards": [
                {
                    "titulo": "Qué cambia en M4 a M6",
                    "texto": (
                        "M5 sube ligeramente a $R^2_{\\text{aj.}} = 0{,}2140$ con $\\eta^2_{\\text{parcial}} = 0{,}0152$, "
                        "porque la brecha SNSS cambia según el capítulo. M6 logra el menor BIC, 2.581.310, al cruzar red "
                        "y región con 80 parámetros."
                    ),
                },
                {
                    "titulo": "Por qué nos quedamos con M3",
                    "texto": (
                        "Preferimos M3 por parsimonia y claridad clínica. Resume el efecto promedio del SNSS (+70,0 %) "
                        "sin repartirlo entre 70 u 80 parámetros, y el ranking principal no cambia. El forward por BIC "
                        "llega al mismo orden."
                    ),
                },
            ],
        },
    },
}

FACTORES = {"capitulo": "Capítulo", "cirugia": "Cirugía", "fallecido": "Condición de egreso", "sexo": "Sexo",
            "establecimiento": "Establecimiento", "region": "Región", "edad": "Edad"}


def _p(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return "<0,001" if x < 0.001 else graficos.num(x, 3)


def _n(x, dec):
    return graficos.num(x, dec)


def _entero(x):
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else graficos.num(x, 0)


def metrica_modelos(c: dict, metrica: str) -> pd.DataFrame:
    """Modelos M0..M3 con la métrica elegida ('R² aj.' o 'BIC')."""
    return pd.DataFrame({"modelo": list(c["modelos"]), "valor": [m[metrica] for m in c["modelos"].values()]})


def filas_modelos(c: dict) -> list[list[str]]:
    return [[k, _entero(m["k"]), _n(m["R²"], 4), _n(m["R² aj."], 4), _entero(m["BIC"]), _entero(m["Δ BIC"]),
             _n(m["F parcial"], 1), _entero(m["gl"]), _p(m["valor-p"])] for k, m in c["modelos"].items()]


def filas_anova(c: dict) -> list[list[str]]:
    return [[k, _n(a["Suma de cuadrados (SS)"], 1), _entero(a["Grados de libertad (gl)"]),
             _n(a["Cuadrado medio (MS)"], 3), _n(a["F"], 1), _p(a["valor-p"])] for k, a in c["anova"].items()]


def filas_bloques(c: dict) -> list[list[str]]:
    return [[k, _n(b["η²"], 4), b["efecto (Cohen)"]] for k, b in c["eta2_bloques"].items()]


def ranking(c: dict) -> pd.DataFrame:
    """Factores ordenados de mayor a menor η² parcial, con su prueba F del informe."""
    df = pd.DataFrame([{"factor": k, "eta2": v["η² parcial"], "efecto": v["efecto (Cohen)"]}
                       for k, v in c["eta2_parciales"].items()])
    claves = {"capítulo": "capitulo", "cirugía": "cirugia", "fallecido": "fallecido", "sexo": "sexo",
              "establecimiento": "establecimiento", "región": "region"}
    df["F"] = [c["ftest"].get(claves.get(f), {}).get("F", float("nan")) for f in df["factor"]]
    df["p"] = [c["ftest"].get(claves.get(f), {}).get("valor-p", float("nan")) for f in df["factor"]]
    return df.sort_values("eta2", ascending=False, ignore_index=True)


def filas_ranking(c: dict) -> list[list[str]]:
    r = ranking(c)
    return [[str(i + 1), x.factor.capitalize(), _n(x.eta2, 4), x.efecto, _n(x.F, 1), _p(x.p)]
            for i, x in enumerate(r.itertuples())]


def factor_de(nombre: str) -> str:
    """Factor al que pertenece un coeficiente de M3."""
    if nombre == "Intercept":
        return "Intercept"
    return nombre.split(": ", 1)[0] if ": " in nombre else "edad"


def coeficientes(c: dict, hc3: bool = False, factor: str | None = None) -> pd.DataFrame:
    """Coeficientes de M3 (sin la constante) con %Δ y su IC clásico o HC3; filtro opcional por factor."""
    suf = " HC3" if hc3 else ""
    filas = []
    for nombre, v in c["coef"].items():
        if nombre == "Intercept" or (factor and factor_de(nombre) != factor):
            continue
        filas.append({"variable": nombre, "beta": v["β"], "ee": v["EE HC3" if hc3 else "EE"], "pct": v["%Δ"],
                      "inf": v[f"%Δ{suf} inf"], "sup": v[f"%Δ{suf} sup"],
                      "p": v["valor-p HC3" if hc3 else "valor-p"]})
    return pd.DataFrame(filas, columns=["variable", "beta", "ee", "pct", "inf", "sup", "p"])


def filas_coef(df: pd.DataFrame) -> list[list[str]]:
    return [[x.variable, _n(x.beta, 4), _n(x.ee, 4), _n(x.pct, 1), _n(x.inf, 1), _n(x.sup, 1), _p(x.p)]
            for x in df.itertuples()]


def filas_espec(c: dict) -> list[list[str]]:
    return [[k, _entero(m["k"]), _n(m["R² aj."], 4), _entero(m["AIC"]), _entero(m["BIC"]), _entero(m["Δ BIC"]),
             _n(m["F parcial"], 1), _entero(m["gl"]), _p(m["valor-p"]), _n(m["η² parcial"], 4)]
            for k, m in c["especificaciones"].items()]


def filas_sens(c: dict) -> list[list[str]]:
    return [[k, _entero(m["k"]), _n(m["R² aj."], 4), _entero(m["BIC"]), _n(m["F parcial"], 2), _p(m["valor-p"]),
             _n(m["η² parcial"], 5)] for k, m in c["sensibilidad_variables"].items()]


def filas_forward(c: dict) -> list[list[str]]:
    return [[k, p["entra"], _entero(p["k"]), _entero(p["BIC"]), _n(p["R² ajustado"], 4), _entero(p["ΔBIC"]),
             _n(p["F parcial"], 1), _p(p["valor-p"])] for k, p in c["forward_pasos"].items()]


def _tabla(cols, filas):
    cab = ui.tags.tr(*[ui.tags.th(x) for x in cols])
    cuerpo = [ui.tags.tr(*[ui.tags.td(x) for x in f]) for f in filas]
    return ui.tags.table(ui.tags.thead(cab), ui.tags.tbody(*cuerpo), class_="table table-sm tabla-texto")


def _tabla_salida(id_, titulo):
    return ui.div(ui.output_ui(id_), class_="table-responsive", role="region", tabindex="0", aria_label=titulo)


def _formula(tex: str):
    return ui.div(tex, class_="formula-latex")


def _guia(clave: str):
    g = TEXTOS["guias"][clave]
    subcards = [
        ui.div(
            ui.p(sub["titulo"], class_="guia-subcard-titulo"),
            ui.p(sub["texto"]),
            class_="guia-subcard",
        )
        for sub in g["subcards"]
    ]
    return ui.div(
        ui.p(g["titulo"], class_="guia-lectura-titulo"),
        ui.div(*subcards, class_="guia-rejilla"),
        class_="guia-lectura",
    )


def fig_metrica(c: dict, metrica: str):
    return graficos.tema(graficos.barras(metrica_modelos(c, metrica), "modelo", "valor"), TEXTOS["metricas"][metrica])


def fig_ranking(c: dict):
    r = ranking(c)
    fig = graficos.barras(r, "factor", "eta2", horizontal=True, linea=0.01)
    fig.update_yaxes(autorange="reversed")
    return graficos.tema(fig, "η² parcial por factor")


def fig_forest(df: pd.DataFrame):
    fig = graficos.intervalos(df, "variable", "pct", "inf", "sup")
    fig.add_vline(x=0, line=dict(color=graficos.REFERENCIA, dash="dash"))
    fig.update_xaxes(title="%Δ en la media geométrica de días")
    fig.update_yaxes(autorange="reversed")
    fig.update_traces(hovertemplate="%{y}: %{x:.1f} %<extra></extra>")
    return graficos.tema(fig, "Cambio porcentual frente a la referencia, IC 95 %")


@module.ui
def pestana_ui():
    return ui.div(
        ui.h3(TEXTOS["titulo"]),
        ui.p(TEXTOS["intro"]),
        _formula(TEXTOS["formula_m3"]),
        ui.h4(TEXTOS["anidados_titulo"]),
        componente.componente(
            TEXTOS["anidados_titulo"],
            ui.input_radio_buttons("metrica", TEXTOS["metrica_etiqueta"], TEXTOS["metricas"], inline=True),
            graficos.salida("graf_metrica"),
            _tabla_salida("tabla_modelos", TEXTOS["anidados_titulo"]),
            resumen=TEXTOS["anidados_resumen"],
            detalle=ui.div(ui.p(TEXTOS["anidados"]), _formula(TEXTOS["formula_bic"]), _guia("anidados")),
        ),
        ui.h4(TEXTOS["anova_titulo"]),
        componente.componente(
            TEXTOS["anova_titulo"],
            _tabla_salida("tabla_anova", TEXTOS["anova_titulo"]),
            abierto=True,
            resumen=TEXTOS["anova_resumen"],
            detalle=ui.div(ui.p(TEXTOS["anova"]), _guia("anova")),
        ),
        ui.h5(TEXTOS["bloques_titulo"]),
        componente.componente(
            TEXTOS["bloques_titulo"],
            _tabla_salida("tabla_bloques", TEXTOS["bloques_titulo"]),
            abierto=True,
            resumen=TEXTOS["bloques_resumen"],
            detalle=ui.p(TEXTOS["bloques"]),
        ),
        ui.h4(TEXTOS["ranking_titulo"]),
        componente.componente(
            TEXTOS["ranking_titulo"],
            graficos.salida("graf_ranking"),
            _tabla_salida("tabla_ranking", TEXTOS["ranking_titulo"]),
            resumen=TEXTOS["ranking_resumen"],
            detalle=ui.div(ui.p(TEXTOS["ranking"]), _formula(TEXTOS["formula_eta2"]), _guia("ranking")),
        ),
        ui.h4(TEXTOS["coef_titulo"]),
        componente.componente(
            TEXTOS["coef_titulo"],
            ui.layout_columns(
                ui.input_radio_buttons("se", TEXTOS["coef_se"], TEXTOS["coef_se_op"], inline=True),
                ui.input_select("factor", TEXTOS["coef_factor"], {"": TEXTOS["coef_todos"], **FACTORES}),
            ),
            graficos.salida("graf_forest"),
            _tabla_salida("tabla_coef", TEXTOS["coef_titulo"]),
            resumen=TEXTOS["coef_resumen"],
            detalle=ui.div(ui.p(TEXTOS["coef"]), _guia("coef")),
        ),
        ui.h4(TEXTOS["espec_titulo"]),
        componente.componente(
            TEXTOS["espec_titulo"],
            _tabla_salida("tabla_espec", TEXTOS["espec_titulo"]),
            abierto=True,
            resumen=ui.output_ui("espec_texto"),
            detalle=ui.div(ui.p(TEXTOS["espec_metodo"]), _guia("extensiones")),
        ),
        ui.h4(TEXTOS["sens_titulo"]),
        componente.componente(
            TEXTOS["sens_titulo"],
            _tabla_salida("tabla_sens", TEXTOS["sens_titulo"]),
            abierto=True,
            resumen=TEXTOS["sens_resumen"],
            detalle=ui.div(ui.p(TEXTOS["sens"]), _guia("sens")),
        ),
        ui.h4(TEXTOS["fwd_titulo"]),
        componente.componente(
            TEXTOS["fwd_titulo"],
            _tabla_salida("tabla_forward", TEXTOS["fwd_titulo"]),
            abierto=True,
            resumen=TEXTOS["fwd_resumen"],
            detalle=ui.p(TEXTOS["fwd"]),
        ),
        class_="pestana-texto",
    )


@module.server
def pestana_server(input, output, session, d):
    c = d.cifras

    @graficos.render_plotly
    def graf_metrica():
        return fig_metrica(c, input.metrica())

    @graficos.render_plotly
    def graf_ranking():
        return fig_ranking(c)

    def _coef():
        return coeficientes(c, input.se() == "hc3", input.factor() or None)

    @graficos.render_plotly
    def graf_forest():
        return fig_forest(_coef())

    @render.ui
    def tabla_modelos():
        return _tabla(TEXTOS["modelos_cols"], filas_modelos(c))

    @render.ui
    def tabla_anova():
        return _tabla(TEXTOS["anova_cols"], filas_anova(c))

    @render.ui
    def tabla_bloques():
        return _tabla(TEXTOS["bloques_cols"], filas_bloques(c))

    @render.ui
    def tabla_ranking():
        return _tabla(TEXTOS["ranking_cols"], filas_ranking(c))

    @render.ui
    def tabla_coef():
        return _tabla(TEXTOS["coef_cols"], filas_coef(_coef()))

    @render.ui
    def espec_texto():
        return ui.p(TEXTOS["espec"].replace("[[menor_bic]]", c["especificacion_menor_bic"]))

    @render.ui
    def tabla_espec():
        return _tabla(TEXTOS["espec_cols"], filas_espec(c))

    @render.ui
    def tabla_sens():
        return _tabla(TEXTOS["sens_cols"], filas_sens(c))

    @render.ui
    def tabla_forward():
        return _tabla(TEXTOS["fwd_cols"], filas_forward(c))
