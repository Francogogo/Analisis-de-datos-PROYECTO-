"""Pestaña Diagnósticos: supuestos del modelo lineal M3 (residuos, ajuste, varianza, colinealidad)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.special import ndtri
from shiny import module, render, ui

import componente
import datos
import graficos
import resumen

TEXTOS = {
    "titulo": "Diagnósticos del modelo lineal",
    "intro": (
        "Ajustamos $M3$, $y_i = \\ln(\\text{días}_i)$, sobre [[n]] egresos. Las métricas numéricas usan toda la base; "
        "los gráficos de puntos y el Q-Q usan una muestra de [[muestra]] egresos para que no se saturen."
    ),
    "intro_formula": r"$$e_i = \ln(\text{días}_i) - \widehat{\ln(\text{días}_i)} = y_i - \hat{y}_i$$",
    "intro_nota": (
        r"El residuo $e_i$ es lo observado menos lo estimado. Si $e_i > 0$, la estadía real superó lo que estima "
        r"$M3$; si $e_i < 0$, fue más corta."
    ),
    "intro_supuestos": (
        "Revisamos cinco supuestos de MCO sobre $M3$, cada uno con su gráfico o tabla: linealidad y varianza constante "
        "con los residuos frente a valores ajustados y la varianza por cuartil; normalidad con el histograma y el Q-Q; "
        "ajuste por grupos con las curvas por edad y por decil; y multicolinealidad con el VIF. La independencia no "
        "tiene gráfico, porque la base no identifica pacientes ni hospitales. Los reingresos del mismo paciente y los "
        "egresos de un mismo hospital la cuestionan, y en ese caso los valores-$p$ quedan optimistas."
    ),
    "supuestos_titulo": "Estado de los supuestos de M3",
    "supuestos": [
        ("cumple", "Linealidad", "La media de los residuos queda cerca de 0 en todo el rango de valores ajustados."),
        ("no", "Varianza constante", "La dispersión sube de $Q_1$ a $Q_4$. Los errores HC3 corrigen la inferencia."),
        ("no", "Normalidad de los residuos", "El Q-Q se aparta en las colas. Con [[n]] egresos, el TLC sostiene las pruebas."),
        ("alerta", "Ajuste por edad", "Sigue la subida desde los 20 años, pero se aparta en los extremos."),
        ("cumple", "Ajuste por decil", "Las curvas avanzan juntas, sin un sesgo en un solo sentido."),
        ("cumple", "Multicolinealidad", "VIF máximo de [[vif]], bajo 5."),
        ("alerta", "Independencia", "No se puede revisar: la base no identifica pacientes ni hospitales."),
    ],
    "resid_titulo": "Residuos frente a valores ajustados",
    "resid_texto": (
        "Revisa dos supuestos a la vez: que el modelo no se desvíe de forma sistemática en ningún tramo de valores "
        "ajustados y que la dispersión sea parecida en todo el rango. La media queda cerca de 0, pero la nube se abre "
        "hacia la derecha: a valores ajustados altos, los residuos varían más."
    ),
    "resid_guia": (
        "Qué muestra la nube de residuos",
        [
            (
                "Qué muestra",
                "Eje horizontal: el $\\ln(\\text{días})$ ajustado por $M3$. Eje vertical: el residuo $e_i$. Cada punto es "
                "un egreso; se dibujan [[muestra]] de los [[n]] para que no se sature. La línea marca la media de cada "
                "ventil: 20 grupos del 5 % de los [[n]] egresos, ordenados por valor ajustado y calculados con toda la base.",
            ),
            (
                "Qué supuesto revisa",
                "Linealidad en promedio y varianza constante. Si se cumpliera perfecto, la nube sería una franja horizontal "
                "alrededor de 0, con la misma altura de izquierda a derecha, y la media de cada ventil quedaría sobre 0. "
                "La media por ventil mira lo primero, pero $\\bar{e} = 0$ es automático en MCO, así que no permite afirmar "
                "exogeneidad.",
            ),
            (
                "Qué vemos aquí",
                "Las medias por ventil se mantienen cerca de 0 en todo el rango. La dispersión crece con el valor ajustado: "
                "el abanico se abre a la derecha, y la desviación de los residuos pasa de [[sd1]] en el primer cuartil a "
                "[[sd4]] en el cuarto.",
            ),
            (
                "Qué implica para M3",
                "Las estimaciones de los coeficientes siguen siendo válidas, pero con varianza desigual el error estándar "
                "clásico queda mal calculado. Por eso reportamos los errores HC3: corrigen la inferencia sin cambiar los "
                "coeficientes.",
            ),
            (
                "Pregunta probable",
                "¿Por qué no usar otra transformación para que el abanico desaparezca? Podría ayudar, pero el $\\ln$ ya "
                "reduce la cola y los errores HC3 resuelven la inferencia sin cambiar la lectura en porcentajes.",
            ),
        ],
    ),
    "hist_titulo": "Histograma de los residuos",
    "hist_texto": (
        "Revisa si la distribución de los residuos se parece a una normal. La asimetría $g_1$ de [[asim]] carga la cola "
        "hacia la derecha y la curtosis en exceso de [[curt]] indica colas algo más pesadas: no es normal en sentido "
        "estricto, aunque el centro sí se parece."
    ),
    "hist_guia": (
        "Normalidad de los residuos y papel del ln",
        [
            (
                "Qué muestra",
                "Eje horizontal: rangos de residuo $e_i$ de igual ancho. Eje vertical: cantidad de egresos en cada rango, "
                "sobre los [[n]] de la base. Cada barra es un rango; una campana simétrica indica residuos equilibrados.",
            ),
            (
                "Qué supuesto revisa",
                "Normalidad de los residuos. Si se cumpliera perfecto, las barras formarían una campana simétrica centrada "
                "en 0, con asimetría $g_1 = 0$ y curtosis en exceso $= 0$.",
            ),
            (
                "Qué vemos aquí",
                "La asimetría es de [[asim]]: la cola derecha es más larga, por las estadías extremas. La curtosis en "
                "exceso de [[curt]] indica colas algo más pesadas que una normal. El centro queda cerca de $\\bar{e} = 0$.",
            ),
            (
                "Qué implica para M3",
                "Los residuos no son normales en sentido estricto, pero para los coeficientes importa la distribución de "
                "$\\hat{\\beta}_j$, no la de $e_i$. Con [[n]] egresos, el Teorema del Límite Central (TLC) hace que esa "
                "distribución sea aproximadamente normal, así que las pruebas $t$ y los intervalos son razonables. Lo que "
                "no queda bien estimado es cada egreso con estadía muy larga.",
            ),
            (
                "Pregunta probable",
                "¿Por qué no quitar las estadías extremas? Son parte de la duración real, y la base no trae gravedad para "
                "separarlas. Quitarlas cambiaría la población que se estudia, no solo la forma de los residuos.",
            ),
        ],
    ),
    "qq_titulo": "Gráfico Q-Q de los residuos",
    "qq_texto": (
        "Revisa la normalidad con otra escala: compara cada residuo ordenado con el cuantil que le correspondería en una "
        "normal. El centro sigue la recta, pero en la cola derecha los puntos se separan, así que la forma de los "
        "residuos no es normal en sentido estricto."
    ),
    "qq_guia": (
        "Qué muestra el Q-Q con el ln",
        [
            (
                "Qué muestra",
                "Eje horizontal: cuantiles teóricos de una normal estándar. Eje vertical: cuantiles observados de los "
                "residuos. Cada punto es un residuo de la muestra de [[muestra]] egresos, ordenados. La recta punteada une "
                "los cuartiles de los residuos con los de la normal.",
            ),
            (
                "Qué supuesto revisa",
                "Normalidad de los residuos, leída en cuantiles. Si se cumpliera perfecto, todos los puntos quedarían sobre "
                "la recta; los desvíos en las colas indican colas más pesadas o más livianas que la normal.",
            ),
            (
                "Qué vemos aquí",
                r"Entre $Q_1$ y $Q_3$ los puntos siguen la recta, y el tramo central es casi simétrico: "
                r"$z_{0{,}25} \approx -0{,}674$ y $z_{0{,}75} \approx 0{,}674$. Arriba, a la derecha, los puntos se separan "
                "de la recta por las estadías más largas.",
            ),
            (
                "Qué implica para M3",
                "El tramo central es el que más pesa para los coeficientes, y ahí la aproximación es buena. Las colas "
                "separadas confirman lo que dice el histograma: la inferencia es razonable por el TLC con [[n]] egresos, pero "
                "$M3$ no describe bien la distribución completa de las estadías.",
            ),
            (
                "Pregunta probable",
                "¿Si los puntos no siguen la recta, el modelo está mal? No necesariamente: $M3$ describe la media de "
                "$\\ln(\\text{días})$, y el Q-Q mira la forma de los residuos. Con muchos egresos, el desvío en las colas no "
                "cambia las estimaciones por sí solo.",
            ),
        ],
    ),
    "edad_titulo": "Observado y ajustado por tramo de edad",
    "edad_texto": (
        "Revisa si la curva de la edad está bien capturada: compara la media de $\\ln(\\text{días})$ observada en 11 "
        "tramos de edad con la que estima $M3$, que usa la edad centrada y su cuadrado. El modelo sigue la subida desde "
        "los 20 años, pero se aparta en los extremos."
    ),
    "edad_formula": r"$$\text{Media geométrica} = \exp\!\left(\overline{\ln(\text{días})}\right)$$",
    "edad_cols": [
        "Tramo de edad",
        "Edad (punto medio)",
        "$\\ln(\\text{días})$ observado",
        "$\\ln(\\text{días})$ ajustado",
        "Media geométrica observada (días)",
        "Media geométrica ajustada (días)",
    ],
    "edad_tabla_titulo": "Tabla por tramo de edad",
    "edad_tabla_resumen": (
        "Cada fila es un tramo de edad. Las columnas en días son medias geométricas: el exponencial de la media de "
        "$\\ln(\\text{días})$."
    ),
    "edad_guia": (
        "Qué muestra la curva por edad",
        [
            (
                "Qué muestra",
                "Eje horizontal: punto medio de cada uno de los 11 tramos de edad. Línea sólida: media observada de "
                "$\\ln(\\text{días})$ en el tramo. Línea punteada: media ajustada por $M3$. Cada valor promedia todos los "
                "egresos del tramo, sin importar su tamaño; la tabla de abajo los pasa a días.",
            ),
            (
                "Qué supuesto revisa",
                "Forma de la relación con la edad, o sea, si una curva con $\\text{edad}_c$ y $\\text{edad}_c^2$ basta. "
                "También es un chequeo de ajuste por grupos: si el modelo acierta en promedio dentro de cada tramo. Si se "
                "cumpliera perfecto, las dos líneas se superpondrían en los 11 tramos.",
            ),
            (
                "Qué vemos aquí",
                "En menores de un año, la media geométrica observada es [[ed_inf_obs]] días y la ajustada, [[ed_inf_aj]]. En "
                "90 y más, es [[ed_sup_obs]] frente a [[ed_sup_aj]]. En el tramo medio, las dos curvas van casi juntas.",
            ),
            (
                "Qué implica para M3",
                "La parábola recoge la curva general, pero en los extremos el error es sistemático. Eso no invalida el efecto "
                "de la edad como resumen, aunque para un lactante o un adulto de 90 años la estimación se aleja más de lo "
                "observado.",
            ),
            (
                "Pregunta probable",
                "¿Por qué no usar los 11 tramos en el modelo? Lo hace $M4$, que reemplaza la edad por los tramos y sube el "
                "$R^2_{\\text{aj.}}$ de [[m3_r2]] a [[m4_r2]]. La mejora es pequeña ($\\eta^2_{\\text{parcial}}$ de "
                "[[m4_eta]]), y $M3$ se mantiene por ser más simple de leer.",
            ),
        ],
    ),
    "decil_titulo": "Ajustado y observado por decil de valor ajustado",
    "decil_texto": (
        "Revisa si el modelo acierta en promedio dentro de cada decil de valor ajustado: ordena los [[n]] egresos en 10 "
        "grupos y compara medias geométricas. Las curvas avanzan juntas, y el modelo queda por debajo en el decil 7 "
        "([[aj7]] frente a [[ob7]] días) y por encima en el 10 ([[aj10]] frente a [[ob10]]), sin un sesgo en un solo sentido."
    ),
    "decil_cols": [
        "Decil",
        "Egresos",
        "Ajustada, $e^{\\overline{\\hat{y}}}$ (días)",
        "Observada, $e^{\\overline{y}}$ (días)",
        "Mediana obs. (días)",
    ],
    "decil_tabla_titulo": "Tabla por decil",
    "decil_tabla_resumen": (
        "Cada fila es un decil de valor ajustado, con su número de egresos. La mediana observada se incluye como "
        "referencia que no depende de los extremos."
    ),
    "decil_guia": (
        "Qué muestra la calibración por deciles",
        [
            (
                "Qué muestra",
                "Eje horizontal: decil de valor ajustado, del 1 (menor) al 10 (mayor), con los [[n]] egresos repartidos en "
                "10 grupos. Eje vertical: media geométrica en días. Línea sólida: observada. Línea punteada: ajustada. La "
                "tabla agrega la mediana observada, que no depende de los extremos.",
            ),
            (
                "Qué supuesto revisa",
                "Calibración por grupos: que, para egresos con el mismo valor ajustado, la estadía promedio observada coincida "
                "con la estimada. Si se cumpliera perfecto, las dos líneas se superpondrían en los 10 deciles.",
            ),
            (
                "Qué vemos aquí",
                "Las curvas avanzan juntas. La mediana observada da [[med7]] días en el decil 7 y [[med10]] en el 10. El "
                "$R^2_{\\text{aj.}}$ de $M3$ es [[m3_r2]]: el modelo sigue la tendencia, pero explica solo una parte de la "
                "variación de $\\ln(\\text{días})$.",
            ),
            (
                "Qué implica para M3",
                "$M3$ describe bien la tendencia promedio por grupo, pero no cada egreso. Que el modelo quede por debajo en "
                "un decil y por encima en otro no señala un sesgo sistemático, y no obliga a cambiar $M3$. Sí limita lo que "
                "se puede decir de un egreso aislado.",
            ),
            (
                "Pregunta probable",
                "¿Si el modelo explica solo [[m3_r2]] de la variación, sirve? Sirve para comparar promedios entre grupos, como "
                "el SNSS frente a los demás establecimientos, que es lo que se pregunta. No sirve para asegurar la duración "
                "de un egreso concreto.",
            ),
        ],
    ),
    "sd_titulo": "Varianza de los residuos por cuartil",
    "sd_texto": (
        "Revisa si la dispersión de los residuos es igual en todo el rango de valores ajustados: divide los egresos en "
        "cuartiles y calcula la desviación estándar de los residuos en cada uno. Sube de [[sd1]] en $Q_1$ a [[sd4]] en "
        "$Q_4$, un aumento de [[sd_ratio]] %, así que la varianza no es constante."
    ),
    "sd_guia": (
        "Qué muestra el salto entre cuartiles",
        [
            (
                "Qué muestra",
                "Eje horizontal: cuartiles de valor ajustado, de $Q_1$ (el 25 % más bajo) a $Q_4$ (el 25 % más alto). Eje "
                "vertical: desviación estándar de los residuos dentro de cada cuartil. Cada barra resume un cuarto de los "
                "[[n]] egresos.",
            ),
            (
                "Qué supuesto revisa",
                r"Varianza constante, o homocedasticidad: $\text{Var}(\varepsilon_i \mid X_i) = \sigma^2$. Si se cumpliera "
                "perfecto, las cuatro barras tendrían la misma altura, con diferencias solo por azar.",
            ),
            (
                "Qué vemos aquí",
                "Las barras suben de [[sd1]] en $Q_1$ a [[sd2]], [[sd3]] y [[sd4]]. El salto mayor está entre $Q_1$ y $Q_3$. "
                "La media de los residuos no cambia, pero su dispersión sí: los egresos con valor ajustado alto tienen "
                "errores más variables.",
            ),
            (
                "Qué implica para M3",
                "La heterocedasticidad no sesga los coeficientes de MCO, pero sí su error estándar clásico, así que las "
                "pruebas $t$ y los intervalos del clásico no son fiables. Los errores HC3 recalculan ese error sin suponer "
                "varianza constante: corrigen la inferencia, no la dispersión.",
            ),
            (
                "Pregunta probable",
                "¿Vale $M3$ sin normalidad ni varianza constante? Sí para inferir sobre los coeficientes: el TLC aproxima "
                "cada $\\hat{\\beta}_j$ a una normal con [[n]] egresos, y HC3 corrige el error estándar. No garantiza que cada "
                "egreso quede bien estimado, porque $M3$ modela la tendencia media.",
            ),
        ],
    ),
    "vif_titulo": "Colinealidad y errores robustos",
    "vif_formula": r"$$\text{VIF}_j = \frac{1}{1 - R_j^2}$$",
    "vif": (
        "Revisa la multicolinealidad: cuánto se infla la varianza de cada coeficiente porque su variable se correlaciona "
        "con las demás explicativas (VIF). El máximo es [[vif]], menos de 5, así que no hay colinealidad problemática."
    ),
    "hc3": (
        "Comparamos el error estándar HC3 con el clásico mediante la razón $\\text{EE}_{\\text{HC3}} / "
        "\\text{EE}_{\\text{clásico}}$. Va de [[rmin]] en [[cmin]] a [[rmax]] en [[cmax]]."
    ),
    "vif_guia": (
        "Qué muestran VIF y HC3 juntos",
        [
            (
                "Qué muestra",
                r"Para cada coeficiente, $\text{VIF}_j$ sale de regresar la variable $j$ contra las demás y usar su $R_j^2$. "
                r"La razón $\text{EE}_{\text{HC3}} / \text{EE}_{\text{clásico}}$ se calcula para todos los coeficientes de $M3$.",
            ),
            (
                "Qué supuesto revisa",
                "Multicolinealidad, o sea, que ninguna explicativa sea casi combinación exacta de las demás; y, con HC3, que "
                "el error estándar no dependa de varianza constante. Si se cumpliera perfecto, todos los VIF valdrían 1 y "
                "todas las razones HC3 serían 1.",
            ),
            (
                "Qué vemos aquí",
                "El VIF máximo es [[vif]]: ninguna explicativa queda explicada casi por completo por las demás. La razón HC3 "
                "va de [[rmin]] a [[rmax]] veces el clásico, y el número de coeficientes que cambian de significancia al 5 % "
                "es [[cambios]].",
            ),
            (
                "Qué implica para M3",
                "La colinealidad no impide leer los coeficientes. El VIF mide la relación con el conjunto de variables, no entre "
                "dos, así que asociaciones parecidas, como las de capítulo y cirugía, pueden convivir con VIF bajo. Con HC3, las "
                "pruebas $t$ de $M3$ se mantienen.",
            ),
            (
                "Pregunta probable",
                "¿Por qué no quitar variables con VIF alto? No hay ninguno que lo justifique: el máximo es [[vif]]. Quitar "
                "variables además cambiaría la pregunta sobre cada factor.",
            ),
        ],
    ),
    "ejes": {
        "ajuste": "ln(días) ajustado",
        "residuo": "Residuo",
        "teorico": "Cuantiles teóricos",
        "obs": "Cuantiles observados",
        "edad": "Edad (punto medio del tramo)",
        "decil": "Decil de valor ajustado",
    },
}


MAX_PUNTOS = graficos.MAX_PUNTOS


def llenar(texto: str, valores: dict) -> str:
    for k, v in valores.items():
        texto = texto.replace(f"[[{k}]]", v)
    return texto


def muestra(base: pd.DataFrame) -> pd.DataFrame:
    """Hasta MAX_PUNTOS egresos (random_state=1) para los gráficos de puntos."""
    return base.sample(min(len(base), MAX_PUNTOS), random_state=1)


def valores(d) -> dict:
    c, n = d.cifras, graficos.num
    dc, sd, hc = c["deciles"], c["sd_residuos_cuartil"], c["hc3_resumen"]
    ed, esp = c["edad_observada_ajustada"], c["especificaciones"]
    g = lambda k, col: n(dc[k][col], 2)  # noqa: E731
    return {
        "n": n(len(d.base), 0),
        "muestra": n(min(len(d.base), MAX_PUNTOS), 0),
        "sd1": n(sd["Q1"], 3),
        "sd2": n(sd["Q2"], 3),
        "sd3": n(sd["Q3"], 3),
        "sd4": n(sd["Q4"], 3),
        "sd_ratio": n((sd["Q4"] / sd["Q1"] - 1) * 100, 1),
        "asim": n(c["asimetria_residuos"], 3),
        "curt": n(c["curtosis_residuos"], 3),
        "aj10": g("10", "ajustada (media geométrica)"),
        "ob10": g("10", "observada (media geométrica)"),
        "med10": g("10", "observada (mediana)"),
        "aj7": g("7", "ajustada (media geométrica)"),
        "ob7": g("7", "observada (media geométrica)"),
        "med7": g("7", "observada (mediana)"),
        "ed_inf_obs": n(float(np.exp(ed["0.5"]["log_dias"])), 2),
        "ed_inf_aj": n(float(np.exp(ed["0.5"]["ajuste_ln"])), 2),
        "ed_sup_obs": n(float(np.exp(ed["92.5"]["log_dias"])), 2),
        "ed_sup_aj": n(float(np.exp(ed["92.5"]["ajuste_ln"])), 2),
        "m3_r2": n(esp["M3"]["R² aj."], 3),
        "m4_r2": n(esp["M4"]["R² aj."], 3),
        "m4_dbic": n(esp["M4"]["Δ BIC"], 0),
        "m4_eta": n(esp["M4"]["η² parcial"], 4),
        "vif": n(c["vif_max"], 2),
        "rmin": n(hc["razon_min"], 2),
        "rmax": n(hc["razon_max"], 2),
        "cmin": hc["coef_razon_min"],
        "cmax": hc["coef_razon_max"],
        "cambios": n(hc["cambios_significancia"], 0),
    }


# ---------- figuras
def ventiles(base: pd.DataFrame) -> pd.DataFrame:
    """Media del valor ajustado y del residuo en cada 5 % (20 grupos) de la base completa."""
    g = pd.qcut(base["ajuste_ln"].rank(method="first"), 20, labels=False)
    return base.groupby(g, observed=True)[["ajuste_ln", "residuo"]].mean().reset_index(drop=True)


def fig_residuos(base: pd.DataFrame, m_pre: pd.DataFrame | None = None, v_pre: pd.DataFrame | None = None) -> go.Figure:
    e = TEXTOS["ejes"]
    fig = graficos.dispersion(m_pre if m_pre is not None else muestra(base), "ajuste_ln", "residuo")
    v = v_pre if v_pre is not None else ventiles(base)
    fig.add_trace(go.Scatter(x=v["ajuste_ln"], y=v["residuo"], mode="lines+markers", name="media por ventil", showlegend=True,
                             line=dict(color=graficos.REFERENCIA), hovertemplate="media %{y:.3f}<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=graficos.GRIS, dash="dash"))
    fig.update_xaxes(title_text=e["ajuste"])
    fig.update_yaxes(title_text=e["residuo"])
    return fig


def fig_histograma(base: pd.DataFrame, h_pre: pd.DataFrame | None = None) -> go.Figure:
    h = h_pre.copy() if h_pre is not None else resumen.histograma(base, "residuo", None)
    h["centro"] = (h["inicio"] + h["fin"]) / 2
    fig = graficos.barras(h, "centro", "n")
    fig.update_xaxes(title_text=TEXTOS["ejes"]["residuo"])
    fig.update_yaxes(title_text="Egresos")
    return fig


def fig_qq(base: pd.DataFrame, m_pre: pd.DataFrame | None = None) -> go.Figure:
    r = np.sort((m_pre if m_pre is not None else muestra(base))["residuo"].to_numpy(dtype=float))
    teo = datos.cuantiles_normales(len(r))
    fig = graficos.dispersion(pd.DataFrame({"teo": teo, "obs": r}), "teo", "obs", ancho=1000, alto=480)
    q1, q3 = np.quantile(r, [0.25, 0.75])
    z25, z75 = float(ndtri(0.25)), float(ndtri(0.75))
    b = (q3 - q1) / (z75 - z25)
    a = q1 - b * z25
    fig.add_trace(go.Scatter(x=[teo[0], teo[-1]], y=[a + b * teo[0], a + b * teo[-1]], mode="lines",
                             line=dict(color=graficos.REFERENCIA, dash="dash"), hoverinfo="skip"))
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title_text=TEXTOS["ejes"]["teorico"])
    fig.update_yaxes(title_text=TEXTOS["ejes"]["obs"])
    return fig


def tabla_edad(cifras: dict) -> pd.DataFrame:
    t = pd.DataFrame(cifras["edad_observada_ajustada"]).T
    t.index = t.index.astype(float)
    t = t.sort_index().rename(columns={"log_dias": "Observada", "ajuste_ln": "Ajustada"})
    t.index.name = "edad"
    return t.reset_index()


def html_edad(cifras: dict, base: pd.DataFrame):
    """Tabla por tramo de edad: ln(días) observado y ajustado y su media geométrica (exp de la media de ln)."""
    nombre = {round(float(e), 1): t for t, e in base.groupby("tramo_edad", observed=True)["edad"].mean().items()}
    num = graficos.num
    filas = [[nombre.get(round(r["edad"], 1), "—"), num(r["edad"], 1), num(r["Observada"], 2), num(r["Ajustada"], 2),
              num(float(np.exp(r["Observada"])), 2), num(float(np.exp(r["Ajustada"])), 2)]
             for _, r in tabla_edad(cifras).iterrows()]
    return ui.tags.table(ui.tags.thead(ui.tags.tr(*[ui.tags.th(c) for c in TEXTOS["edad_cols"]])),
                         ui.tags.tbody(*[ui.tags.tr(*[ui.tags.td(x) for x in f]) for f in filas]), class_="table table-sm")


def fig_edad(cifras: dict) -> go.Figure:
    fig = graficos.lineas(tabla_edad(cifras), "edad", ["Observada", "Ajustada"])
    fig.update_traces(mode="lines+markers", hovertemplate="%{y:.3f}<extra>%{fullData.name}</extra>")
    fig.update_traces(line_dash="dash", selector=dict(name="Ajustada"))
    fig.update_xaxes(title_text=TEXTOS["ejes"]["edad"])
    fig.update_yaxes(title_text="Media de ln(días)")
    return fig


def tabla_deciles(cifras: dict) -> pd.DataFrame:
    t = pd.DataFrame(cifras["deciles"]).T
    t.index = t.index.astype(int)
    t = t.sort_index()
    t.index.name = "decil"
    return t.reset_index()


def fig_deciles(cifras: dict) -> go.Figure:
    t = tabla_deciles(cifras).rename(columns={"ajustada (media geométrica)": "Ajustada",
                                              "observada (media geométrica)": "Observada"})
    fig = graficos.lineas(t, "decil", ["Observada", "Ajustada"])
    fig.update_traces(mode="lines+markers", hovertemplate="%{y:.2f} días<extra>%{fullData.name}</extra>")
    fig.update_traces(line_dash="dash", selector=dict(name="Ajustada"))
    fig.update_xaxes(title_text=TEXTOS["ejes"]["decil"], dtick=1)
    fig.update_yaxes(title_text="Media geométrica (días)")
    return fig


def fig_sd(cifras: dict) -> go.Figure:
    s = cifras["sd_residuos_cuartil"]
    fig = graficos.barras(pd.DataFrame({"cuartil": list(s), "sd": list(s.values())}), "cuartil", "sd")
    fig.update_yaxes(title_text="Desviación estándar del residuo")
    return fig


def html_deciles(cifras: dict):
    cols = ["egresos", "ajustada (media geométrica)", "observada (media geométrica)", "observada (mediana)"]
    filas = [[str(int(r["decil"])), graficos.num(r["egresos"], 0)] + [graficos.num(r[c], 2) for c in cols[1:]]
             for _, r in tabla_deciles(cifras).iterrows()]
    return ui.tags.table(ui.tags.thead(ui.tags.tr(*[ui.tags.th(c) for c in TEXTOS["decil_cols"]])),
                         ui.tags.tbody(*[ui.tags.tr(*[ui.tags.td(x) for x in f]) for f in filas]), class_="table table-sm")


def _formula(clave: str, v: dict):
    return ui.div(llenar(TEXTOS[clave], v), class_="formula-latex")


def _guia(clave: str, v: dict, pila: bool = True):
    titulo, subcards = TEXTOS[clave]
    rejilla = "guia-rejilla guia-rejilla--pila" if pila else "guia-rejilla"
    tarjetas = [
        ui.div(
            ui.p(llenar(subtitulo, v), class_="guia-subcard-titulo"),
            ui.p(llenar(cuerpo, v)),
            class_="guia-subcard",
        )
        for subtitulo, cuerpo in subcards
    ]
    return ui.div(
        ui.p(titulo, class_="guia-lectura-titulo"),
        ui.div(*tarjetas, class_=rejilla),
        class_="guia-lectura",
    )


def _bloque(titulo, clave, *cuerpo, junto=None):
    """Sección con el componente: `cuerpo` visible, `t_<clave>` como lectura breve, `d_<clave>` en el modal.
    `junto` (la tabla del mismo gráfico) queda al lado en pantallas anchas."""
    comp = componente.componente(
        titulo, *cuerpo,
        resumen=ui.output_ui(f"t_{clave}"),
        detalle=ui.output_ui(f"d_{clave}"),
    )
    return ui.tags.section(
        ui.h4(titulo),
        ui.div(comp, junto, class_="par-lado") if junto is not None else comp,
        class_="seccion-editorial",
    )


def _tabla(titulo, clave_resumen, salida, aria):
    return componente.componente(
        titulo,
        ui.div(ui.output_ui(salida), class_="table-responsive", role="region", tabindex="0", aria_label=aria),
        resumen=ui.p(TEXTOS[clave_resumen]),
    )


# ---------- módulo
@module.ui
def pestana_ui():
    T = TEXTOS
    return ui.div(
        ui.tags.section(ui.h3(T["titulo"]), ui.output_ui("intro"), class_="seccion-editorial"),
        _bloque(T["resid_titulo"], "resid", graficos.salida("g_resid")),
        ui.div(
            _bloque(T["hist_titulo"], "hist", graficos.salida("g_hist")),
            _bloque(T["qq_titulo"], "qq", graficos.salida("g_qq")),
            class_="par-lado",
        ),
        _bloque(T["edad_titulo"], "edad", graficos.salida("g_edad"),
                junto=_tabla(T["edad_tabla_titulo"], "edad_tabla_resumen", "tabla_edad", T["edad_tabla_titulo"])),
        _bloque(T["decil_titulo"], "decil", graficos.salida("g_decil"),
                junto=_tabla(T["decil_tabla_titulo"], "decil_tabla_resumen", "tabla_decil", T["decil_tabla_titulo"])),
        _bloque(T["sd_titulo"], "sd", graficos.salida("g_sd")),
        ui.tags.section(
            ui.h4(T["vif_titulo"]),
            componente.componente(T["vif_titulo"], ui.output_ui("t_vif"), detalle=ui.output_ui("d_vif"), abierto=True),
            class_="seccion-editorial",
        ),
    )


@module.server
def pestana_server(input, output, session, d):
    @render.ui
    def intro():
        v = valores(d)
        return ui.div(
            ui.p(llenar(TEXTOS["intro"], v)),
            ui.p(llenar(TEXTOS["intro_supuestos"], v)),
            _formula("intro_formula", v),
            ui.p(llenar(TEXTOS["intro_nota"], v)),
            ui.tags.figure(
                ui.tags.figcaption(TEXTOS["supuestos_titulo"], class_="guia-lectura-titulo"),
                ui.div(*[graficos.semaforo(e, t, llenar(n, v)) for e, t, n in TEXTOS["supuestos"]],
                       class_="semaforo-rejilla"),
                class_="guia-lectura guia-lectura--simple",
            ),
        )

    def registrar(id_, fn):
        fn.__name__ = id_  # Shiny registra el output con el nombre de la función
        output(id=id_)(render.ui(fn))

    for clave, clave_txt, clave_guia, clave_fx in [
        ("resid", "resid_texto", "resid_guia", None),
        ("hist", "hist_texto", "hist_guia", None),
        ("qq", "qq_texto", "qq_guia", None),
        ("edad", "edad_texto", "edad_guia", "edad_formula"),
        ("decil", "decil_texto", "decil_guia", None),
        ("sd", "sd_texto", "sd_guia", None),
    ]:
        def hacer_resumen(ct):
            def texto():
                return ui.p(llenar(TEXTOS[ct], valores(d)))

            return texto

        def hacer_detalle(cg, cfx):
            def detalle():
                v = valores(d)
                partes = [_formula(cfx, v)] if cfx else []
                partes.append(_guia(cg, v))
                return ui.div(*partes)

            return detalle

        registrar(f"t_{clave}", hacer_resumen(clave_txt))
        registrar(f"d_{clave}", hacer_detalle(clave_guia, clave_fx))

    @render.ui
    def tabla_edad():
        return html_edad(d.cifras, d.base)

    @render.ui
    def tabla_decil():
        return html_deciles(d.cifras)

    @render.ui
    def t_vif():
        v = valores(d)
        return ui.p(llenar(TEXTOS["vif"], v))

    @render.ui
    def d_vif():
        v = valores(d)
        return ui.div(
            _formula("vif_formula", v),
            ui.p(llenar(TEXTOS["hc3"], v)),
            _guia("vif_guia", v, pila=False),
        )

    @graficos.render_plotly
    def g_resid():
        import cache
        pre = cache.diagnosticos_base(d)
        return fig_residuos(d.base, m_pre=pre["muestra"], v_pre=pre["ventiles"])

    @graficos.render_plotly
    def g_hist():
        import cache
        pre = cache.diagnosticos_base(d)
        return fig_histograma(d.base, h_pre=pre["hist"])

    @graficos.render_plotly
    def g_qq():
        import cache
        pre = cache.diagnosticos_base(d)
        return fig_qq(d.base, m_pre=pre["muestra"])

    @graficos.render_plotly
    def g_edad():
        return fig_edad(d.cifras)

    @graficos.render_plotly
    def g_decil():
        return fig_deciles(d.cifras)

    @graficos.render_plotly
    def g_sd():
        return fig_sd(d.cifras)
