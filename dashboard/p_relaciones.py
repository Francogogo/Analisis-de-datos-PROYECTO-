"""Pestaña Relaciones: normalidad y pruebas de a pares entre cada factor y la estadía."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shiny import module, reactive, render, ui

import componente
import datos
import graficos
import resumen

ETIQ = {
    "dias_estada": "Días de estada", "edad": "Edad", "sexo": "Sexo", "nacionalidad": "Nacionalidad",
    "etnia": "Etnia", "cirugia": "Cirugía", "fallecido": "Condición de egreso",
    "establecimiento": "Establecimiento", "capitulo": "Capítulo CIE-10", "region": "Región",
    "tramo_edad": "Tramo de edad",
}
MUESTRA_NORMALIDAD = 5000
UMBRALES = {"ε²": (0.01, 0.06, 0.14)}   # el resto usa 0,10 / 0,30 / 0,50 (Cohen)

TEXTOS = {
    "titulo": "Relaciones entre pares de variables",
    "intro": (
        "Antes del modelo multivariable revisamos cómo se relaciona cada variable con la estadía, por separado, en los "
        "968.098 egresos. Primero comprobamos si las variables numéricas siguen una distribución normal. No la siguen, "
        "así que usamos pruebas basadas en rangos en lugar de comparar promedios con $t$ o ANOVA. En cada contraste, "
        "$H_0$ dice que no hay asociación o diferencia y $H_1$ que sí la hay. Rechazamos $H_0$ cuando el valor-$p$ "
        "es menor que 0,05, es decir, cuando una diferencia así sería poco probable si $H_0$ fuera cierta."
    ),
    "normalidad_titulo": "Pruebas de normalidad",
    "normalidad_nota": (
        "Probamos si los días de estada y la edad siguen una distribución normal, porque $t$ y ANOVA lo suponen. "
        "Las tres pruebas y sus resultados están en la ampliación de la tabla de pruebas."
    ),
    "efecto_titulo": "Por qué no basta con mirar el valor-$p$: tamaño del efecto",
    "efecto_nota": (
        "Con casi un millón de egresos, casi cualquier diferencia da $p < 0{,}001$. Por eso medimos también el tamaño "
        "del efecto y lo comparamos con los criterios de Cohen."
    ),
    "pruebas_titulo": "Las 20 pruebas de a pares",
    "pruebas_cols": ["Variable", "Respuesta", "Prueba", "Estadístico", "$\\text{gl}$", "Valor-$p$", "Tamaño del efecto", "Decisión"],
    "explorador_titulo": "Explorar cada prueba en detalle",
    "explorador_nota": (
        "Selecciona un par para ver su gráfico, su ficha de hipótesis y, en las pruebas de estadía prolongada, "
        "la tabla de contingencia."
    ),
    "explorador_resumen": "El valor-$p$ dice si hay diferencia; el tamaño del efecto dice cuánto pesa.",
    "pruebas_resumen": (
        "En las 18 pruebas de asociación el valor-$p$ queda bajo 0,001, así que para ordenar los factores sirve más "
        "el tamaño del efecto."
    ),
    "selector": "Prueba",
    "cramer_titulo": "Asociación entre factores: $V$ de Cramér",
    "cramer_componente": "Mapa de asociación entre factores (V de Cramér)",
    "cramer_nota": (
        "Los factores clínicos y sociodemográficos no actúan aislados, así que medimos cuánto se solapan entre sí. "
        "El capítulo CIE-10 y la cirugía tienen $V \\approx [[v]]$; el capítulo y el sexo, $V \\approx [[vs]]$. "
        "Lo tendremos en cuenta al pasar al modelo multivariable."
    ),
    "cramer_resumen": (
        "La $V$ de Cramér va de 0 (sin asociación) a 1 (asociación total). Cuando es alta, los dos factores aportan "
        "en buena parte la misma información."
    ),
    "hip": {
        "Shapiro-Wilk, Lilliefors, Anderson-Darling": (
            "La variable sigue una distribución normal.", "La variable no sigue una distribución normal."),
        "Spearman": ("$\\rho_s = 0$: la edad y los días de estada no tienen asociación monótona.",
                     "$\\rho_s \\neq 0$: hay asociación monótona entre ambas."),
        "Mann-Whitney U": (
            "Ambos grupos tienen la misma distribución de días de estada.", "Un grupo tiende a tener estadías más largas."),
        "Kruskal-Wallis": (
            "Todos los grupos tienen la misma distribución de días de estada.", "Al menos un grupo difiere del resto."),
        "Chi-cuadrado": (
            "El factor y la estadía prolongada (más de 15 días, el decil superior de la base) son independientes.",
            "No son independientes."),
    },
    "ef": {"ρ": "$\\rho_s$", "r": "$r$", "ε²": "$\\varepsilon^2$", "V": "$V$", "W": "$W$"},
    "lectura_sin_efecto": (
        "Rechazamos normalidad en ambas variables con $p < 0{,}001$, así que el análisis bivariado usa pruebas no "
        "paramétricas, que trabajan con rangos en vez de valores originales."
    ),
    "lectura": "El efecto es [[magnitud]]: $[[medida]] = [[efecto]]$. [[detalle]]",
    "holm": (
        "Como hacemos muchas comparaciones de a pares, ajustamos los valores-$p$ con Holm para no inflar los falsos "
        "hallazgos. Con ese ajuste, [[distintos]] de los [[pares]] pares de grupos difieren."
    ),
    "contingencia": "Conteo de egresos según el factor y la estadía prolongada",
    "prolongadas": "% de egresos con estadía prolongada (> 15 días)",
    "campos": ["$H_0$", "$H_1$", "Estadístico", "Valor-$p$", "Tamaño del efecto", "Decisión", "Lectura"],
    "rechaza": "Se rechaza $H_0$",
    "no_rechaza": "No se rechaza $H_0$",
}


# ---------- ayudas puras
def _num_tex(x: float, dec: int = 1) -> str:
    return graficos.num(x, dec).replace(",", "{,}")


def _guia(titulo: str, *subcards: tuple[str, str]) -> ui.Tag:
    if len(subcards) == 1:
        sub_tit, texto = subcards[0]
        return ui.div(
            ui.p(titulo, class_="guia-lectura-titulo"),
            ui.p(sub_tit, class_="guia-subcard-titulo") if sub_tit else None,
            ui.p(texto),
            class_="guia-lectura guia-lectura--simple",
        )
    cards = [
        ui.div(
            ui.p(sub_tit, class_="guia-subcard-titulo"),
            ui.p(texto),
            class_="guia-subcard",
        )
        for sub_tit, texto in subcards
    ]
    return ui.div(
        ui.p(titulo, class_="guia-lectura-titulo"),
        ui.div(*cards, class_="guia-rejilla"),
        class_="guia-lectura",
    )


def _formula(tex: str) -> ui.Tag:
    return ui.div(tex, class_="formula-latex")


def fmt_p(p) -> str:
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "—"
    return "< 0,001" if p < 0.001 else graficos.num(p, 4)


def magnitud(medida: str, efecto) -> str:
    if efecto is None or (isinstance(efecto, float) and math.isnan(efecto)):
        return "—"
    a = abs(efecto)
    ch, me, gr = UMBRALES.get(medida, (0.1, 0.3, 0.5))
    return "despreciable" if a < ch else "pequeño" if a < me else "mediano" if a < gr else "grande"


def claves(cifras: dict) -> list[tuple[str, str]]:
    """Los 20 pares: 2 filas de normalidad y 18 de asociación, en el orden del informe."""
    norm = [(v, "normalidad") for v in cifras["normalidad"]]
    return norm + [(p["variable"], p["respuesta"]) for p in cifras["pares"]]


def prueba(cifras: dict, variable: str, respuesta: str) -> dict:
    if respuesta == "normalidad":
        n = cifras["normalidad"][variable]
        return {"variable": variable, "respuesta": respuesta,
                "prueba": "Shapiro-Wilk, Lilliefors, Anderson-Darling", "estadístico": n["Shapiro-Wilk W"],
                "valor-p": n["p SW"], "medida": "W", "efecto": n["Shapiro-Wilk W"], "detalle": "",
                "gl": float("nan"), "esperada mínima": float("nan"),
                "lilliefors": n["Lilliefors D"], "p KS": n["p KS"], "A2": n["Anderson-Darling A²"], "p AD": n["p AD"]}
    for p in cifras["pares"]:
        if p["variable"] == variable and p["respuesta"] == respuesta:
            return dict(p)
    raise KeyError((variable, respuesta))


def _estadistico(p: dict) -> str:
    if p["respuesta"] == "normalidad":
        return (f"$W = {_num_tex(p['estadístico'], 3)}$; $D = {_num_tex(p['lilliefors'], 3)}$; "
                f"$A^2 = {_num_tex(p['A2'], 0)}$")
    sim = {"Spearman": r"\rho_s", "Mann-Whitney U": "U", "Kruskal-Wallis": "H", "Chi-cuadrado": r"\chi^2"}[p["prueba"]]
    s = f"${sim} = {_num_tex(p['estadístico'], 3 if p['prueba'] == 'Spearman' else 1)}$"
    return s + ("" if math.isnan(p["gl"]) else rf", $\text{{gl}} = {_num_tex(p['gl'], 0)}$")


def ficha(cifras: dict, variable: str, respuesta: str) -> list[tuple[str, str]]:
    """Filas (campo, texto) de la tarjeta de una prueba."""
    p = prueba(cifras, variable, respuesta)
    h0, h1 = TEXTOS["hip"][p["prueba"]]
    if p["respuesta"] == "normalidad":
        pv = rf"SW y Lilliefors: {fmt_p(p['valor-p'])}; Anderson–Darling: $p \le {_num_tex(p['p AD'], 2)}$"
        efecto, lectura = "—", TEXTOS["lectura_sin_efecto"]
        rechaza = p["valor-p"] < 0.05
    else:
        pv, rechaza = fmt_p(p["valor-p"]), p["valor-p"] < 0.05
        mag = magnitud(p["medida"], p["efecto"])
        sim_ef = {"ρ": r"\rho_s", "r": "r", "ε²": r"\varepsilon^2", "V": "V", "W": "W"}[p["medida"]]
        efecto = f"${sim_ef} = {_num_tex(p['efecto'], 3)}$, {mag}"
        det = p["detalle"].strip()
        lectura = (TEXTOS["lectura"].replace("[[magnitud]]", mag).replace("[[medida]]", sim_ef)
                   .replace("[[efecto]]", _num_tex(p["efecto"], 3)).replace("[[detalle]]", det + ("." if det else "")))
        if variable in cifras["posthoc_holm"] and respuesta == "días":
            lectura += " " + (TEXTOS["holm"].replace("[[distintos]]", str(cifras["posthoc_holm"][variable]["distintos"]))
                              .replace("[[pares]]", str(cifras["posthoc_holm"][variable]["pares"])))
    return list(zip(TEXTOS["campos"], [h0, h1, _estadistico(p), pv, efecto,
                                       TEXTOS["rechaza"] if rechaza else TEXTOS["no_rechaza"], lectura]))


def opciones(cifras: dict) -> dict:
    respuestas = {"días": "días de estada", "prolongada": f"estadía prolongada (más de {resumen.UMBRAL_PROLONGADA} días)"}
    return {f"{v}|{r}": (f"Normalidad de {ETIQ.get(v, v).lower()}" if r == "normalidad"
                           else f"{ETIQ.get(v, v)} y {respuestas.get(r, r)}")
            for v, r in claves(cifras)}


def matriz_cramer(cifras: dict) -> pd.DataFrame:
    pares = {tuple(k.split(" | ")): v for k, v in cifras["cramer_variables"].items()}
    nombres = sorted({n for k in pares for n in k})
    m = pd.DataFrame(1.0, index=nombres, columns=nombres)
    for (a, b), v in pares.items():
        m.loc[a, b] = m.loc[b, a] = v
    return m.rename(index=ETIQ, columns=ETIQ)


def muestra_normalidad(base: pd.DataFrame, col: str) -> pd.Series:
    return base.sample(MUESTRA_NORMALIDAD, random_state=1)[col].astype(float)


def fig_normalidad(base: pd.DataFrame, col: str) -> go.Figure:
    """Histograma de la variable y Q-Q de días, ln(días) y edad (muestra de 5.000, la de Shapiro-Wilk)."""
    qq = [("dias_estada", "Q-Q días"), ("log_dias", "Q-Q ln(días)"), ("edad", "Q-Q edad")]
    fig = make_subplots(rows=2, cols=2, vertical_spacing=0.16, horizontal_spacing=0.12,
                        subplot_titles=("Histograma de " + ETIQ[col].lower(),) + tuple(t for _, t in qq))
    n, bordes = np.histogram(base[col].astype(float), bins=40)
    fig.add_trace(go.Bar(x=(bordes[:-1] + bordes[1:]) / 2, y=n, marker_color=graficos.ACENTO,
                         hovertemplate="%{x:.1f}: %{y} egresos<extra></extra>", showlegend=False), 1, 1)
    celda = {2: (1, 2), 3: (2, 1), 4: (2, 2)}
    for j, (c, _) in enumerate(qq, start=2):
        x = muestra_normalidad(base, c).sort_values().to_numpy()
        teo = datos.cuantiles_normales(len(x))
        f, k = celda[j]
        graficos.puntos(fig, teo, x, row=f, col=k, ancho=480, alto=400, radio=3)
        a, b = np.polyfit(teo, x, 1)
        fig.add_trace(go.Scatter(x=[teo[0], teo[-1]], y=[a * teo[0] + b, a * teo[-1] + b], mode="lines",
                                 line=dict(color=graficos.REFERENCIA, dash="dash"), hoverinfo="skip", showlegend=False), f, k)
        fig.update_xaxes(title_text="Cuantiles teóricos", row=f, col=k)
    fig.update_xaxes(title_text=ETIQ[col], row=1, col=1)
    fig.update_yaxes(title_text="Cuantiles observados", row=1, col=2)
    fig.update_yaxes(title_text="Cuantiles observados", row=2, col=1)
    return graficos.tema(fig).update_layout(height=860)


def _orden_regiones(grupos) -> list:
    """Regiones de norte a sur; las que no estén en el listado quedan al final."""
    orden = [r for r, _ in graficos.REGIONES]
    return sorted(grupos, key=lambda g: orden.index(g) if g in orden else len(orden))


def colores_grupos(d, variable: str, grupos) -> tuple[list, dict, str]:
    """Clase de color de cada grupo según el código clínico, sus colores y el título de la leyenda."""
    if variable == "capitulo":
        pct = d.cifras["pct_prolongadas_por_grupo"]["capitulo"]
        nombres = graficos.TRAMOS_CARGA
        clases = [nombres[graficos.tramo_carga(pct[g])] if g in pct else nombres[0] for g in grupos]
        return clases, dict(zip(nombres, graficos.CARGA)), f"% > {resumen.UMBRAL_PROLONGADA} días"
    if variable == "region":
        return [graficos.MACROZONA.get(g, "Centro") for g in grupos], graficos.ZONAS, "Macrozona"
    if variable == "fallecido":
        return list(grupos), {"No": graficos.NEUTRO, "Sí": graficos.FALLECIDO}, "Fallecido"
    return None, None, ""


def fig_prueba(d, variable: str, respuesta: str) -> go.Figure:
    if respuesta == "normalidad":
        return fig_normalidad(d.base, variable)
    if respuesta == "prolongada":
        pct = d.cifras["pct_prolongadas_por_grupo"][variable]
        grupos = _orden_regiones(pct) if variable == "region" else list(pct)
        df = pd.DataFrame({"grupo": grupos, "pct": [pct[g] for g in grupos]})
        # El largo de la barra da el %, y el color repite el tramo de carga para leerlo igual en todas las pestañas.
        fig = graficos.barras(df, "grupo", "pct", colores=[graficos.CARGA[graficos.tramo_carga(v)] for v in df["pct"]])
        total = d.cifras["pct_prolongadas"]
        fig.add_hline(y=total, line=dict(color=graficos.REFERENCIA, dash="dash"),
                      annotation_text=f"Total: {graficos.num(total, 1)} %", annotation_position="top left")
        fig.update_xaxes(categoryorder="array", categoryarray=grupos)
        fig.update_yaxes(title_text=TEXTOS["prolongadas"])
        return fig
    por = "tramo_edad" if variable == "edad" else variable
    try:
        import cache
        cj = cache.cajas_relaciones(d, por)
    except Exception:
        cj = resumen.cajas(d.base, por, "log_dias")
        if por == "tramo_edad":
            orden = d.base.groupby("tramo_edad", observed=True)["edad"].mean().sort_values().index.tolist()
            cj = cj.set_index("grupo").loc[orden].reset_index()
    if por == "region":
        cj = cj.set_index("grupo").loc[_orden_regiones(cj["grupo"])].reset_index()
    clases, colores, leyenda = colores_grupos(d, por, cj["grupo"])
    fig = graficos.cajas(cj, clases, colores, leyenda)
    fig.update_yaxes(title_text="ln(días)")
    return fig


def _tabla(cols, filas, clase="table table-sm"):
    return ui.tags.table(ui.tags.thead(ui.tags.tr(*[ui.tags.th(c) for c in cols])),
                         ui.tags.tbody(*[ui.tags.tr(*[ui.tags.td(c) for c in f]) for f in filas]), class_=clase)


def filas_pruebas(cifras: dict) -> list[list[str]]:
    """Una fila por cada una de las 20 pruebas: variable, respuesta, prueba, estadístico, gl, valor-p, efecto, decisión."""
    out = []
    for v, r in claves(cifras):
        p = prueba(cifras, v, r)
        f = dict(ficha(cifras, v, r))
        gl = "—" if math.isnan(p["gl"]) else graficos.num(p["gl"], 0)
        ef = f["Tamaño del efecto"]
        out.append([ETIQ.get(v, v), "normalidad" if r == "normalidad" else r, p["prueba"], _estadistico(p), gl,
                    f["Valor-$p$"], ef, f["Decisión"]])
    return out


def tabla_pruebas(cifras: dict):
    return _tabla(TEXTOS["pruebas_cols"], filas_pruebas(cifras), "table table-sm")


def tabla_contingencia(cifras: dict, variable: str):
    pct = cifras["pct_prolongadas_por_grupo"][variable]
    filas = [(g, graficos.num(c["No"], 0), graficos.num(c["Sí"], 0), graficos.num(c["No"] + c["Sí"], 0),
              graficos.num(pct[g], 1) + " %") for g, c in cifras["contingencia"][variable].items()]
    return ui.div(ui.h6(TEXTOS["contingencia"]),
                  ui.div(_tabla([ETIQ.get(variable, variable), "No prolongada", "Prolongada", "Total", "% prolongadas"], filas),
                         class_="table-responsive", role="region", tabindex="0", aria_label=TEXTOS["contingencia"]))


def ficha_html(cifras: dict, variable: str, respuesta: str):
    p = prueba(cifras, variable, respuesta)
    return ui.div(ui.h5(p["prueba"]),
                  ui.tags.dl(*[x for c, t in ficha(cifras, variable, respuesta)
                               for x in (ui.tags.dt(c), ui.tags.dd(t))]), class_="ficha-prueba")


# ---------- bloques explicativos (.guia-lectura y .formula-latex)
def guia_normalidad_html() -> ui.Tag:
    return _guia(
        "Normalidad de días y de edad: qué mide cada prueba",
        (
            "Los días no son normales",
            "$W = 0{,}442$ es el estadístico de Shapiro–Wilk: cuanto más cerca de 1, más parecida a una normal es la "
            "forma. $D = 0{,}328$ (Lilliefors) es la mayor brecha entre la distribución observada y la normal, y "
            "$A^2 = 150.921$ (Anderson–Darling) pesa sobre todo la cola larga de estadías. Todo con $p < 0{,}001$, y "
            "Anderson–Darling con $p \\le 0{,}01$.",
        ),
        (
            "Por qué la edad tampoco es normal",
            "Con $W = 0{,}957$ parece cercana a 1, pero $D = 0{,}129$ y $A^2 = 13.546$ rechazan normalidad con "
            "$p < 0{,}001$. El gráfico sugiere una mezcla de grupos (recién nacidos, edad fértil y adultos mayores), "
            "no una sola campana.",
        ),
        (
            "Por qué descartamos $t$ y ANOVA clásico",
            "Esa asimetría rompe el supuesto normal de $t$ y ANOVA, que comparan medias crudas.",
        ),
        (
            "¿Hay normalidad en los datos?",
            "No. Ni días ni edad son normales: $W = 0{,}442$ y $W = 0{,}957$, ambos con $p < 0{,}001$. Por eso los cruces "
            "bivariados usan pruebas no paramétricas ($U$, $H$ y $\\rho_s$) y el modelo de regresión trabaja con "
            "$\\ln(\\text{días})$.",
        ),
    )


def guia_efecto_html() -> ui.Tag:
    return ui.TagList(
        _formula(
            "$$|\\rho_s|,\\; |r|,\\; V: \\quad 0{,}10\\;\\text{(pequeño)} \\;\\;\\big|\\;\\; "
            "0{,}30\\;\\text{(mediano)} \\;\\;\\big|\\;\\; 0{,}50\\;\\text{(grande)}$$"
            "$$\\varepsilon^2: \\quad 0{,}01\\;\\text{(pequeño)} \\;\\;\\big|\\;\\; "
            "0{,}06\\;\\text{(mediano)} \\;\\;\\big|\\;\\; 0{,}14\\;\\text{(grande)}$$"
        ),
        _guia(
            "Lo que sacamos en limpio de las 20 pruebas",
            (
                "¿Por qué casi todo da $p < 0{,}001$?",
                "Las 18 pruebas de asociación dan $p < 0{,}001$; la más alta es etnia en estadía prolongada, con "
                "$p = 0{,}0002$. El error estándar cae como $1/\\sqrt{n}$, así que con casi un millón de egresos incluso "
                "diferencias mínimas salen significativas. Por eso exigimos un tamaño mínimo: en los modelos, "
                "$\\eta^2_{\\text{parcial}} \\ge 0{,}01$ y un $\\Delta\\text{BIC}$ favorable. El primer corte de $\\varepsilon^2$ "
                "también es 0,01.",
            ),
            (
                "Las asociaciones más marcadas con la estadía",
                "Establecimiento con $r = -0{,}374$, capítulo CIE-10 con $\\varepsilon^2 = 0{,}120$, condición de egreso "
                "con $r = -0{,}292$, edad con $\\rho_s = 0{,}250$ y cirugía con $r = 0{,}224$.",
            ),
            (
                "Qué pesa en la estadía prolongada",
                "Capítulo con $V = 0{,}251$, tramo de edad con $V = 0{,}165$, condición de egreso con $V = 0{,}109$ y sexo "
                "con $V = 0{,}103$. Región, nacionalidad y etnia salen significativas, pero su efecto es despreciable en las "
                "dos respuestas ($V \\le 0{,}049$ en prolongada).",
            ),
        ),
    )


def guia_prueba_html(cifras: dict, variable: str, respuesta: str) -> ui.Tag:
    p = prueba(cifras, variable, respuesta)
    nombre_var = ETIQ.get(variable, variable)

    if respuesta == "normalidad":
        if variable == "dias_estada":
            g1_dias = _num_tex(cifras["descriptivos"]["dias_estada"]["asimetría"], 2)
            g1_log = _num_tex(cifras["descriptivos"]["log_dias"]["asimetría"], 2)
            sub_mid = (
                "Qué logra $\\ln(\\text{días})$ en el Q–Q",
                f"Con $\\ln(\\text{{días}})$ el centro se acerca a la recta y la asimetría ($g_1$) baja de ${g1_dias}$ "
                f"a ${g1_log}$. Aun así quedan escalones por días enteros y colas separadas de la recta.",
            )
            sub_res = (
                "Conclusión para pruebas y modelo",
                "El logaritmo mejora el centro, pero no da normalidad perfecta. Por eso las pruebas van por rangos y M3 "
                "ajusta $\\ln(\\text{días})$.",
            )
        else:
            sub_mid = (
                "La forma en S del Q–Q de edad",
                "La curva en S indica una mezcla de grupos (lactantes, edad fértil y adultos mayores) que se separa de la "
                "recta en ambos extremos.",
            )
            sub_res = (
                "Conclusión frente a normalidad",
                "Edad tampoco cumple los supuestos de $t$ o ANOVA, así que la evaluamos con Spearman.",
            )
        return _guia(
            f"Lectura del gráfico de normalidad: {nombre_var.lower()}",
            (
                "Qué muestra este gráfico",
                f"El histograma de 40 intervalos usa los 968.098 egresos de {nombre_var.lower()}. Los tres Q–Q usan una "
                "muestra de 5.000 egresos y comparan cuantiles observados con la recta normal punteada: si hubiera "
                "normalidad, los puntos seguirían esa recta.",
            ),
            sub_mid,
            sub_res,
        )

    if respuesta == "prolongada":
        mag = magnitud("V", p["efecto"])
        v_txt = _num_tex(p["efecto"], 3)
        chi_txt = _num_tex(p["estadístico"], 1)
        gl_txt = _num_tex(p["gl"], 0)
        p_txt = "$p < 0{,}001$" if p["valor-p"] < 0.001 else f"$p = {_num_tex(p['valor-p'], 4)}$"
        pct_dict = cifras["pct_prolongadas_por_grupo"][variable]
        g_min = min(pct_dict, key=pct_dict.get)
        g_max = max(pct_dict, key=pct_dict.get)
        min_txt = graficos.num(pct_dict[g_min], 1)
        max_txt = graficos.num(pct_dict[g_max], 1)
        if abs(p["efecto"]) >= 0.10:
            remate = (
                f"Con $\\chi^2 = {chi_txt}$, $\\text{{gl}} = {gl_txt}$ y {p_txt} rechazamos independencia. Como "
                f"$V = {v_txt}$ supera el corte de 0,10 de Cohen ({mag}), la diferencia en la tasa es relevante."
            )
        else:
            remate = (
                f"Aunque $\\chi^2 = {chi_txt}$ con $\\text{{gl}} = {gl_txt}$ da {p_txt} por el tamaño de la muestra, "
                f"$V = {v_txt}$ queda bajo 0,10 ({mag}): este factor cambia poco la tasa."
            )
        return _guia(
            f"Lectura de {nombre_var.lower()} frente a estadía prolongada",
            (
                "Qué muestra el gráfico de tasas",
                f"Las barras muestran el porcentaje de egresos con más de 15 días en cada grupo de {nombre_var.lower()}. "
                "La tabla de contingencia tiene los conteos exactos.",
            ),
            (
                "Rango frente al 9,4 % global",
                f"En el total de egresos, un 9,4 % supera los 15 días. Aquí la proporción va de {min_txt} % en {g_min} "
                f"a {max_txt} % en {g_max}.",
            ),
            (
                "Lectura de $\\chi^2$ y la $V$ de Cramér",
                remate,
            ),
        )

    if p["prueba"] == "Spearman":
        return _guia(
            "Lectura de edad frente a días de estada",
            (
                "Qué muestra la tendencia por edad",
                "Las cajas en $\\ln(\\text{días})$ suben desde los 20–29 años hasta mayores de 80. Los menores de 1 año "
                "son la excepción neonatal. $\\rho_s = 0{,}250$ se calculó con los 968.098 egresos.",
            ),
            (
                "Cómo pasar de $\\ln(\\text{días})$ a días",
                "Cada caja va de $Q_1$ a $Q_3$ (el rango intercuartílico es $\\text{RIC} = Q_3 - Q_1$), con la mediana al "
                "centro. Con $e^y$, 0,69 equivale a 2 días, 1,10 a 3 días y 1,61 a 5 días.",
            ),
            (
                "Conclusión y por qué",
                "$\\rho_s$ (Spearman) mide qué tan monótona es la relación, entre -1 y 1. Con $\\rho_s = 0{,}250$ y "
                "$p < 0{,}001$, la asociación es real pero pequeña según Cohen. La edad se asocia con estadías más largas, "
                "aunque conviene controlar el diagnóstico en M3.",
            ),
        )

    mag = magnitud(p["medida"], p["efecto"])
    sim = r"r" if p["medida"] == "r" else r"\varepsilon^2"
    est_tex = _estadistico(p)
    umbral_txt = "0,10 / 0,30 / 0,50" if p["medida"] == "r" else "0,01 / 0,06 / 0,14"
    if mag != "despreciable":
        lectura_ef = (
            f"Con {est_tex} y $p < 0{{,}}001$ rechazamos igualdad entre grupos ({p['detalle']}). El efecto "
            f"${sim} = {_num_tex(p['efecto'], 3)}$ es {mag}. Los cortes de Cohen son {umbral_txt}."
        )
    else:
        lectura_ef = (
            f"Con {est_tex} y $p < 0{{,}}001$ hay diferencia estadística ({p['detalle']}), pero el efecto "
            f"${sim} = {_num_tex(p['efecto'], 3)}$ queda bajo {umbral_txt} ({mag}): las cajas quedan casi al mismo nivel."
        )
    if variable in cifras["posthoc_holm"]:
        ph = cifras["posthoc_holm"][variable]
        tercera = (
            "Pares distintos tras ajuste de Holm",
            f"Kruskal–Wallis solo indica que al menos un grupo difiere. Con el ajuste de Holm sobre todos los pares, "
            f"{ph['distintos']} de los {ph['pares']} muestran diferencias con $p < 0{{,}}05$.",
        )
    else:
        tercera = (
            "Por qué este cruce no basta solo",
            "En un cruce de a pares no fijamos los demás factores. Una diferencia bivariada puede mezclarse con el "
            "diagnóstico o la edad, y eso lo resolvemos en M3.",
        )
    return _guia(
        f"Lectura de {nombre_var.lower()} frente a días de estada",
        (
            "Qué muestra el desplazamiento de cajas",
            f"Las cajas ordenan las categorías de {nombre_var.lower()} por la mediana de $\\ln(\\text{{días}})$. El "
            "rango intercuartílico ($\\text{RIC} = Q_3 - Q_1$) muestra la dispersión, y $e^{\\text{mediana}}$ devuelve la "
            "mediana a días: 0,69 son 2 y 1,10 son 3.",
        ),
        (
            "Resultado y tamaño del efecto",
            lectura_ef,
        ),
        tercera,
    )


def guia_cramer_html(cifras: dict) -> ui.Tag:
    v_cap_cir = _num_tex(cifras["cramer_variables"]["capitulo | cirugia"], 4)
    v_cap_sex = _num_tex(cifras["cramer_variables"]["capitulo | sexo"], 4)
    v_cap_fal = _num_tex(cifras["cramer_variables"]["capitulo | fallecido"], 4)
    v_cir_est = _num_tex(cifras["cramer_variables"]["cirugia | establecimiento"], 4)
    v_reg_sex = _num_tex(cifras["cramer_variables"]["region | sexo"], 4)
    return ui.TagList(
        _formula(r"$$V = \sqrt{\frac{\chi^2}{n\,\min(f - 1,\, c - 1)}}$$"),
        _guia(
            "Asociación entre factores y por qué obliga a usar M3",
            (
                "Qué muestra el mapa",
                "Los factores se solapan entre sí en los 968.098 egresos. La $V$ de Cramér escala $\\chi^2$ entre 0 y 1, "
                "así que los bloques oscuros muestran qué variables comparten información antes de modelar.",
            ),
            (
                "Dónde se cruzan los factores clínicos",
                f"El capítulo CIE-10 se asocia fuerte con cirugía, $V = {v_cap_cir}$, y con sexo, $V = {v_cap_sex}$, por los "
                f"partos. Con fallecimiento la asociación es moderada, $V = {v_cap_fal}$; cirugía con establecimiento da "
                f"$V = {v_cir_est}$ y región con sexo, $V = {v_reg_sex}$.",
            ),
            (
                "Por qué la cirugía parece acortar la estadía",
                "Sola, la cirugía parece acortar la estadía (mediana de 2 frente a 4 días), porque mezcla operar con "
                "diagnósticos cortos como los partos o la oftalmología. Solo el modelo multivariable M3 separa ambos efectos.",
            ),
        ),
    )


# ---------- módulo
@module.ui
def pestana_ui():
    return ui.div(
        ui.h3(TEXTOS["titulo"]), ui.p(TEXTOS["intro"]),
        ui.h4(TEXTOS["normalidad_titulo"]), ui.p(TEXTOS["normalidad_nota"]),
        ui.h4(TEXTOS["efecto_titulo"]), ui.p(TEXTOS["efecto_nota"]),
        ui.h4(TEXTOS["pruebas_titulo"]),
        componente.componente(
            TEXTOS["pruebas_titulo"],
            ui.div(ui.output_ui("pruebas"), class_="table-responsive", role="region", tabindex="0",
                   aria_label=TEXTOS["pruebas_titulo"]),
            abierto=True,
            resumen=TEXTOS["pruebas_resumen"],
            detalle=ui.TagList(guia_normalidad_html(), guia_efecto_html()),
        ),
        ui.h4(TEXTOS["explorador_titulo"]), ui.p(TEXTOS["explorador_nota"]),
        componente.componente(
            "Explorador de pruebas",
            ui.input_select("par", TEXTOS["selector"], choices={}, width="100%"),
            ui.layout_columns(graficos.salida("grafico"), ui.div(ui.output_ui("ficha"), ui.output_ui("extra")),
                              col_widths=(7, 5)),
            resumen=TEXTOS["explorador_resumen"],
            detalle=ui.output_ui("guia_prueba"),
        ),
        ui.h4(TEXTOS["cramer_titulo"]),
        componente.componente(
            TEXTOS["cramer_componente"],
            ui.output_ui("cramer_nota"), graficos.salida("cramer"),
            resumen=TEXTOS["cramer_resumen"],
            detalle=ui.output_ui("guia_cramer"),
        ),
    )


@module.server
def pestana_server(input, output, session, d):
    @reactive.effect
    def _():
        ui.update_select("par", choices=opciones(d.cifras), selected="edad|días")

    def sel():
        v, r = (input.par() or "edad|días").split("|")
        return v, r

    @render.ui
    def pruebas():
        return tabla_pruebas(d.cifras)

    @graficos.render_plotly
    def grafico():
        return fig_prueba(d, *sel())

    # Shiny deja marcada como oculta la ficha tras recorrer las pestañas y no la actualiza
    @output(suspend_when_hidden=False)
    @render.ui
    def ficha():
        return ficha_html(d.cifras, *sel())

    @output(suspend_when_hidden=False)
    @render.ui
    def extra():
        v, r = sel()
        return tabla_contingencia(d.cifras, v) if r == "prolongada" else None

    @output(suspend_when_hidden=False)
    @render.ui
    def guia_prueba():
        return guia_prueba_html(d.cifras, *sel())

    @render.ui
    def cramer_nota():
        v = d.cifras["cramer_variables"]["capitulo | cirugia"]
        vs = d.cifras["cramer_variables"]["capitulo | sexo"]
        txt = (TEXTOS["cramer_nota"].replace("[[v]]", _num_tex(v, 2)).replace("[[vs]]", _num_tex(vs, 2)))
        return ui.p(txt)

    @graficos.render_plotly
    def cramer():
        return graficos.calor(matriz_cramer(d.cifras).round(2))

    @render.ui
    def guia_cramer():
        return guia_cramer_html(d.cifras)
