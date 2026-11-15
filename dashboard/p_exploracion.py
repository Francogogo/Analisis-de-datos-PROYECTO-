"""Pestaña Exploración: descripción y depuración de los días de estada, con filtros."""
from __future__ import annotations

import numpy as np
import pandas as pd
from shiny import module, reactive, render, ui

import graficos
import componente
import resumen
import etiquetas

FILTROS = {
    "region": "Región",
    "capitulo": "Capítulo CIE-10",
    "tramo_edad": "Tramo de edad",
    "sexo": "Sexo",
    "establecimiento": "Establecimiento",
    "cirugia": "Cirugía",
    "fallecido": "Fallecido",
}

TEXTOS = {
    "titulo": "Exploración de los días de estada",
    "intro": (
        "Revisamos los 968.098 egresos de la base depurada. Cada fila es un alta hospitalaria, no un paciente: "
        "una misma persona pudo internarse más de una vez en 2020. Los siete filtros recalculan tarjetas, tabla "
        "y gráficos al instante. Un selector vacío no restringe nada, y la columna de referencia siempre muestra "
        "la base completa."
    ),
    "filtros_titulo": "Filtros",
    "filtros_placeholder": "Todos (sin filtro)",
    "sin_resultados": "No hay egresos con esta combinación de filtros. Quita alguno para volver a ver datos.",
    "caja_n": "Egresos",
    "caja_mediana": "Mediana de días",
    "caja_prol": "% de egresos prolongados",
    "caja_cama": "% de días-cama de prolongados",
    "base_completa": "Base completa",
    "kpi_titulo": "Resumen del filtro",
    "kpi_resumen": (
        "Las cuatro tarjetas responden al filtro activo. Las dos últimas describen las estadías largas, "
        "las que pasan de 15 días, y cuánto ocupan de las camas."
    ),
    "prol_titulo": "Qué miden las cuatro tarjetas",
    "prol_1_t": "Ventana prolongada",
    "prol_1": (
        r"La primera tarjeta cuenta los egresos que pasan el filtro. La mediana $M_e$ es el día que deja la mitad "
        r"de las estadías por debajo y la otra mitad por encima. Consideramos prolongada una estadía de más de 15 "
        r"días, que es el percentil 90 de la base. La última tarjeta suma los días-cama de esas estadías y los "
        r"compara con el total; un día-cama es una cama ocupada durante un día."
    ),
    "prol_2_t": "Brecha entre SNSS y No SNSS",
    "prol_2": (
        r"En recintos del SNSS (792.345 egresos), $M_e = 3{,}0$ días, el 10,6 % son prolongados y ocupan el 48,1 % "
        r"de los días-cama. En los No SNSS (175.753), $M_e = 2{,}0$ días, el 4,2 % supera 15 días y ocupa el 38,3 %. "
        r"Es una diferencia descriptiva: la base no registra gravedad, así que no sabemos si refleja casos más "
        r"complejos o la forma de gestionar."
    ),
    "tabla_titulo": "Estadísticos descriptivos",
    "tabla_resumen": (
        r"En la base completa, la mediana es de 3 días y el promedio sube a 6,70 días por la cola de estadías largas. "
        r"Con filtros cambia la columna de la izquierda; la de la derecha queda fija."
    ),
    "tabla_formula": (
        r"$$\begin{aligned}" "\n"
        r"\bar{x} &= \frac{1}{n}\sum_{i=1}^{n} x_i, \qquad M_e = Q_2, \qquad \text{RIC} = Q_3 - Q_1 \\" "\n"
        r"s &= \sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(x_i - \bar{x})^2}, \qquad g_1 = \frac{n}{(n-1)(n-2)}\sum_{i=1}^{n}\left(\frac{x_i - \bar{x}}{s}\right)^3" "\n"
        r"\end{aligned}$$"
    ),
    "tabla_guia_titulo": "Cómo leer la tabla descriptiva",
    "tabla_1_t": "Mediana de 3 días",
    "tabla_1": (
        r"Si ordenamos los 968.098 egresos de más corto a más largo, el del medio dura $M_e = 3{,}00$ días. "
        r"La mitad vuelve a casa en 3 días o menos, y la otra mitad se queda 3 días o más."
    ),
    "tabla_2_t": "Por qué el promedio engaña",
    "tabla_2": (
        r"El promedio $\bar{x} = 6{,}70$ días más que duplica la mediana, porque unas pocas estadías de meses empujan "
        r"la suma hacia arriba. Si usáramos $\bar{x}$ para describir una estadía típica, creeríamos que dura casi "
        r"una semana, y no es así."
    ),
    "tabla_3_t": "RIC frente a desviación típica",
    "tabla_3": (
        r"El RIC es la distancia entre $Q_1 = 2$ y $Q_3 = 7$ días, y deja fuera los extremos: vale 5. La desviación "
        r"típica $s = 12{,}79$, en cambio, sí se infla con la cola, cuya asimetría $g_1 = 9{,}04$ indica que los "
        r"valores altos pesan mucho. En $\ln(\text{días})$, el promedio y la mediana se acercan ($\bar{x} = 1{,}25$, "
        r"$M_e = 1{,}10$) y $g_1$ baja a $0{,}68$. La edad, en cambio, es casi simétrica ($g_1 = 0{,}01$)."
    ),
    "dist_titulo": "Distribución de los días",
    "h_dias": "Días de estada (hasta 60)",
    "h_dias_resumen": (
        "La asimetría $g_1$ mide qué tan cargada está la cola: aquí vale 9,04, así que unos pocos egresos muy largos "
        "tiran el promedio hacia arriba."
    ),
    "h_dias_guia_titulo": "Cómo leer días de estada (hasta 60)",
    "h_dias_1_t": "Asimetría extrema",
    "h_dias_1": (
        r"Con $g_1 = 9{,}04$, la mitad de las altas dura 3 días o menos, pero la cola llega a cientos de días. "
        r"Por eso el eje se corta en 60: si no, las barras iniciales quedarían aplastadas contra el eje."
    ),
    "h_dias_2_t": "Cómo se lee el recorte a 60 días",
    "h_dias_2": (
        "Las 40 barras cubren de 0 a 60 días. Los egresos más largos no se quitan del cálculo, solo quedan fuera "
        "de la vista. Si el eje llegara a 365 días, las barras iniciales serían casi invisibles."
    ),
    "h_ln": "ln(días)",
    "h_ln_resumen": (
        "El logaritmo comprime la cola: la asimetría baja de 9,04 a 0,68. Los saltos de la escala aparecen porque "
        "los días se registran como números enteros."
    ),
    "h_ln_guia_titulo": "Cómo leer ln(días)",
    "h_ln_1_t": "Compresión y saltos",
    "h_ln_1": (
        r"La asimetría pasa de $g_1 = 9{,}04$ a $0{,}68$. Las barras no son continuas porque los días son enteros: "
        r"$\ln(1) = 0$, $\ln(2) \approx 0{,}69$ y $\ln(3) \approx 1{,}10$ marcan los primeros saltos."
    ),
    "h_ln_2_t": "Cómo se lee la escala",
    "h_ln_2": (
        r"La escala llega hasta $\ln(365) \approx 5{,}90$ y reparte en 40 barras toda la base depurada. Sobre ella, "
        r"el promedio $\bar{x} = 1{,}25$ queda junto a la mediana $M_e = 1{,}10$."
    ),
    "dist_decision_titulo": r"¿Hay normalidad tras aplicar $\ln(\text{días})$?",
    "dist_dec_1_t": "No hay normalidad estricta",
    "dist_dec_1": (
        r"Aun con $\ln(\text{días})$, las barras iniciales siguen siendo discretas por medir días enteros. Con "
        r"968.098 egresos, las pruebas de normalidad rechazan una campana perfecta."
    ),
    "dist_dec_3_t": "Por qué la inferencia sigue siendo válida",
    "dist_dec_3": (
        r"Las pruebas bivariadas usan rangos no paramétricos y no exigen normalidad. En el modelo M3, el Teorema del "
        r"Límite Central con $n = 968.098$ respalda los $\hat{\beta}_j$ bajo errores $\text{HC3}$, que son robustos "
        r"a varianza no constante."
    ),
    "def_q": r"¿Qué logra transformar a $\ln(\text{días})$?",
    "def_a": (
        r"No vuelve normal la variable. Lo que logra es comprimir la cola extrema: baja la asimetría $g_1$ de 9,04 a "
        r"0,68. Además, un cambio proporcional pasa a ser una suma, porque duplicar el valor suma siempre "
        r"$\ln(2) \approx 0{,}69$, y el efecto se puede leer como razón multiplicativa con $\%\Delta = 100(e^{\beta} - 1)$."
    ),
    "h_conc": "Concentración de los días-cama",
    "h_conc_resumen": (
        "Ordenamos los egresos del más largo al más corto y acumulamos sus días-cama. La curva sube rápido: una "
        "fracción pequeña de los egresos concentra casi la mitad de las camas."
    ),
    "ayuda_conc": "% de egresos, de los más largos a los más cortos",
    "h_conc_guia_titulo": "Cómo leer la concentración",
    "h_conc_1_t": "Concentración de camas",
    "h_conc_1": (
        "El 9,4 % más largo de los egresos consume el 47,1 % de los días-cama. Si todas las estadías duraran igual, "
        "la curva sería una diagonal, y aquí queda muy por encima de ella."
    ),
    "h_conc_2_t": "Cómo leer la curva",
    "h_conc_2": (
        "En X van los egresos del más largo al más corto, y en Y el porcentaje acumulado de días-cama. Un tramo "
        "empinado al inicio significa que pocos egresos concentran muchas camas."
    ),
    "dep_titulo": "Valores atípicos y depuración",
    "dep_formula": r"$$L_s = Q_3 + 1{,}5\,\text{RIC}$$",
    "dep_resumen": (
        "La regla de Tukey marca como atípicas las estadías sobre [[ls]] días. Las retenemos, y solo sacamos las de más "
        "de 365 días ([[n_exc]] casos)."
    ),
    "dep_guia_titulo": "Criterio de Tukey y corte en 365 días",
    "dep_1_t": "Regla de Tukey",
    "dep_tukey": (
        r"Con $Q_3 = [[q3]]$ y $\text{RIC} = [[ric]]$ días, el límite $L_s = [[ls]]$ marca [[n_ls]] egresos, el "
        r"[[pct_ls]] % de la base. Los retenemos: son estadías reales, y justo ahí se concentra el uso de camas."
    ),
    "dep_2_t": "Por qué excluimos más de 365 días",
    "dep_365": (
        r"Excluimos [[n_exc]] egresos de más de 365 días ([[pct_exc]] % de los [[n_con365]] iniciales), y quedan "
        r"$n = [[n_final]]$. Son estadías crónicas o errores administrativos, ajenos al cuidado agudo. Esta depuración "
        r"es fija para toda la base."
    ),
    "dep_3_t": "Qué pasa si los incluimos",
    "dep_nota": (
        r"Con esos [[n_exc]] casos, la mediana sigue en $M_e = [[mediana]]$ días, pero el promedio sube de [[media]] a "
        r"[[media365]] días y la desviación típica pasa de [[s]] a [[s365]] días, casi cinco veces su valor. Por eso conviene "
        r"leer la mediana, que casi no se mueve."
    ),
}


def num_ref(x, dec=1):
    return graficos.num(x, dec)


def llenar(texto: str, valores: dict) -> str:
    for k, v in valores.items():
        texto = texto.replace(f"[[{k}]]", str(v))
    return texto


def asimetria(s: pd.Series) -> float:
    """Coeficiente de asimetría como en el informe (pandas, corregido por sesgo)."""
    return float(s.astype(float).skew())


def tabla_desc(df: pd.DataFrame, cifras: dict) -> pd.DataFrame:
    """Tabla del informe: valor con el filtro y valor de la base completa, ya formateados."""
    filas = []
    for etiqueta, col in [("Días de estada", "dias_estada"), ("ln(días)", "log_dias"), ("Edad (años)", "edad")]:
        s = df[col].astype(float)
        q1, q3 = (s.quantile(0.25), s.quantile(0.75)) if len(s) else (np.nan, np.nan)
        filtrado = {"Media": s.mean(), "Mediana": s.median(), "Desv. est.": s.std(),
                    "Asimetría": asimetria(s), "RIC": q3 - q1}
        paper = cifras["descriptivos"][col]
        claves = {"Media": "mean", "Mediana": "median", "Desv. est.": "s", "Asimetría": "asimetría", "RIC": "RIC"}
        for nombre, v in filtrado.items():
            filas.append([etiqueta, nombre, graficos.num(v, 2), graficos.num(paper[claves[nombre]], 2)])
    return pd.DataFrame(filas, columns=["Variable", "Estadístico", "Con el filtro", "base completa (paper)"])


def tabla_desc_html(t: pd.DataFrame) -> ui.Tag:
    """La tabla larga de `tabla_desc` en formato ancho: una fila por estadístico y, por variable,
    el valor con el filtro junto al de la base completa."""
    variables = list(dict.fromkeys(t["Variable"]))
    estadisticos = list(dict.fromkeys(t["Estadístico"]))
    celda = t.set_index(["Variable", "Estadístico"])
    cab1 = [ui.tags.th("Estadístico", rowspan="2", scope="col")] + [
        ui.tags.th(v, colspan="2", scope="colgroup", class_="desc-grupo") for v in variables]
    cab2 = [ui.tags.th(x, scope="col", class_=c) for _ in variables
            for x, c in (("Con el filtro", "desc-filtro"), ("Base completa", "desc-base"))]
    filas = [ui.tags.tr(ui.tags.th(e, scope="row"), *[
        ui.tags.td(celda.loc[(v, e), col], class_=c) for v in variables
        for col, c in (("Con el filtro", "desc-filtro"), ("base completa (paper)", "desc-base"))])
        for e in estadisticos]
    return ui.tags.table(ui.tags.thead(ui.tags.tr(*cab1), ui.tags.tr(*cab2)), ui.tags.tbody(*filas),
                         class_="table table-sm tabla-desc")


def cajas_valores(df: pd.DataFrame, cifras: dict) -> list[tuple[str, str, str]]:
    """(título, valor filtrado, valor de la base completa) de las cuatro cajas."""
    d = resumen.descriptivos(df)
    return [
        (TEXTOS["caja_n"], graficos.num(d["n"], 0), graficos.num(cifras["n"], 0)),
        (TEXTOS["caja_mediana"], graficos.num(d["mediana"], 1),
         graficos.num(cifras["descriptivos"]["dias_estada"]["median"], 1)),
        (TEXTOS["caja_prol"], graficos.num(d["pct_prolongadas"], 1) + (" %" if d["n"] else ""),
         graficos.num(cifras["pct_prolongadas"], 1) + " %"),
        (TEXTOS["caja_cama"], graficos.num(d["pct_dias_cama_prolongadas"], 1) + (" %" if d["n"] else ""),
         graficos.num(cifras["pct_dias_cama"], 1) + " %"),
    ]


def valores_depuracion(cifras: dict) -> dict:
    at, cr = cifras["atipicos"]["días"], cifras["comparacion_robustez"]
    con, fin = cr["días con > 365 incluidos"], cr["días (base final)"]
    desc_dias = cifras["descriptivos"]["dias_estada"]
    return {
        "n_ls": graficos.num(at["n > Ls"], 0), "pct_ls": graficos.num(at["% > Ls"], 1),
        "ls": graficos.num(at["Ls"], 1),
        "q3": graficos.num(desc_dias["Q3"], 0), "ric": graficos.num(desc_dias["RIC"], 0),
        "n_exc": graficos.num(cifras["excluidos_mas_365"], 0),
        "pct_exc": graficos.num(cifras["pct_excluidos"], 2),
        "n_con365": graficos.num(con["n"], 0), "n_final": graficos.num(fin["n"], 0),
        "media": graficos.num(fin["media"], 2), "media365": graficos.num(con["media"], 2),
        "s": graficos.num(fin["s"], 2), "s365": graficos.num(con["s"], 2),
        "mediana": graficos.num(fin["mediana"], 0),
    }


def notas_depuracion(cifras: dict) -> list[str]:
    v = valores_depuracion(cifras)
    return [llenar(TEXTOS[k], v) for k in ("dep_tukey", "dep_365", "dep_nota")]


def _guia(titulo: str, *subcards: tuple[str, str] | str, pila: bool = False):
    if len(subcards) == 1 and isinstance(subcards[0], str):
        return ui.div(
            ui.p(titulo, class_="guia-lectura-titulo"),
            ui.p(subcards[0]),
            class_="guia-lectura guia-lectura--simple",
        )
    rejilla_cls = "guia-rejilla guia-rejilla--pila" if pila else "guia-rejilla"
    tarjetas = [
        ui.div(
            ui.p(subtitulo, class_="guia-subcard-titulo"),
            ui.p(cuerpo),
            class_="guia-subcard",
        )
        for subtitulo, cuerpo in subcards
    ]
    return ui.div(
        ui.p(titulo, class_="guia-lectura-titulo"),
        ui.div(*tarjetas, class_=rejilla_cls),
        class_="guia-lectura",
    )


def _formula(latex: str):
    return ui.div(latex, class_="formula-latex")


def _caja(i):
    return ui.card(
        ui.card_header(ui.output_text(f"caja{i}_t")),
        ui.tags.div(ui.output_text(f"caja{i}_v"), class_="fs-3 fw-bold", style="color:var(--acento)"),
        ui.tags.small(ui.output_text(f"caja{i}_r"), style="color:#6b7c82"),
    )


@module.ui
def pestana_ui():
    return ui.div(
        ui.h3(TEXTOS["titulo"]),
        ui.p(TEXTOS["intro"]),
        ui.div(
            ui.h5(TEXTOS["filtros_titulo"]),
            ui.layout_columns(
                *[ui.input_selectize(k, e, choices=[], multiple=True,
                                     options={"placeholder": TEXTOS["filtros_placeholder"]})
                  for k, e in FILTROS.items()], col_widths=3),
            class_="panel-filtros",
        ),
        ui.div(ui.output_ui("estado_filtros"), role="status", aria_live="polite"),
        componente.componente(
            TEXTOS["kpi_titulo"],
            ui.div(ui.layout_columns(*[_caja(i) for i in range(4)], col_widths=3), class_="metricas"),
            abierto=True,
            resumen=ui.p(TEXTOS["kpi_resumen"]),
            detalle=_guia(
                TEXTOS["prol_titulo"],
                (TEXTOS["prol_1_t"], TEXTOS["prol_1"]),
                (TEXTOS["prol_2_t"], TEXTOS["prol_2"]),
            ),
        ),
        ui.h5(TEXTOS["tabla_titulo"]),
        componente.componente(
            TEXTOS["tabla_titulo"],
            ui.div(ui.output_ui("tabla"), class_="table-responsive", role="region", tabindex="0",
                   aria_label=TEXTOS["tabla_titulo"]),
            abierto=True,
            resumen=ui.p(TEXTOS["tabla_resumen"]),
            detalle=ui.div(
                _formula(TEXTOS["tabla_formula"]),
                _guia(
                    TEXTOS["tabla_guia_titulo"],
                    (TEXTOS["tabla_1_t"], TEXTOS["tabla_1"]),
                    (TEXTOS["tabla_2_t"], TEXTOS["tabla_2"]),
                    (TEXTOS["tabla_3_t"], TEXTOS["tabla_3"]),
                ),
            ),
        ),
        ui.h5(TEXTOS["dist_titulo"]),
        ui.layout_columns(
            componente.componente(
                TEXTOS["h_dias"],
                graficos.salida("h_dias"),
                resumen=ui.p(TEXTOS["h_dias_resumen"]),
                detalle=_guia(
                    TEXTOS["h_dias_guia_titulo"],
                    (TEXTOS["h_dias_1_t"], TEXTOS["h_dias_1"]),
                    (TEXTOS["h_dias_2_t"], TEXTOS["h_dias_2"]),
                    pila=True,
                ),
            ),
            componente.componente(
                TEXTOS["h_ln"],
                graficos.salida("h_ln"),
                resumen=ui.p(TEXTOS["h_ln_resumen"]),
                detalle=ui.div(
                    _guia(
                        TEXTOS["h_ln_guia_titulo"],
                        (TEXTOS["h_ln_1_t"], TEXTOS["h_ln_1"]),
                        (TEXTOS["h_ln_2_t"], TEXTOS["h_ln_2"]),
                        pila=True,
                    ),
                    _guia(
                        TEXTOS["dist_decision_titulo"],
                        (TEXTOS["dist_dec_1_t"], TEXTOS["dist_dec_1"]),
                        (TEXTOS["dist_dec_3_t"], TEXTOS["dist_dec_3"]),
                        (TEXTOS["def_q"], TEXTOS["def_a"]),
                        pila=True,
                    ),
                ),
            ),
            componente.componente(
                TEXTOS["h_conc"],
                graficos.salida("h_conc"),
                resumen=ui.p(TEXTOS["h_conc_resumen"]),
                detalle=_guia(
                    TEXTOS["h_conc_guia_titulo"],
                    (TEXTOS["h_conc_1_t"], TEXTOS["h_conc_1"]),
                    (TEXTOS["h_conc_2_t"], TEXTOS["h_conc_2"]),
                    pila=True,
                ),
            ),
            col_widths=4,
        ),
        ui.h5(TEXTOS["dep_titulo"]),
        componente.componente(
            TEXTOS["dep_titulo"],
            abierto=True,
            resumen=ui.output_ui("depuracion_resumen"),
            detalle=ui.div(
                _formula(TEXTOS["dep_formula"]),
                ui.output_ui("depuracion"),
            ),
        ),
    )


@module.server
def pestana_server(input, output, session, d):
    for k in FILTROS:
        niveles = [str(c) for c in d.base[k].cat.categories]
        ui.update_selectize(k, choices=etiquetas.opciones(k, niveles), session=session)

    @reactive.calc
    def filtrado():
        return resumen.filtrar(d.base, {k: list(input[k]() or []) for k in FILTROS})

    @reactive.calc
    def base_cache():
        import cache
        df = filtrado()
        return cache.exploracion_base(d) if df is d.base else None

    @render.ui
    def estado_filtros():
        if base_cache() is not None:
            return None
        return ui.p(TEXTOS["sin_resultados"], class_="sin-resultados") if filtrado().empty else None

    @reactive.calc
    def cajas():
        c_pre = base_cache()
        return c_pre["cajas"] if c_pre is not None else cajas_valores(filtrado(), d.cifras)

    def registrar(i):
        # Shiny exige funciones con nombre válido; el id del output se fija con output(id=...).
        def textos():
            return cajas()[i]

        for k, f in [("t", lambda: textos()[0]), ("v", lambda: textos()[1]),
                     ("r", lambda: f"{TEXTOS['base_completa']}: {textos()[2]}")]:
            f.__name__ = f"caja{i}_{k}"
            output(id=f"caja{i}_{k}")(render.text(f))

    for i in range(4):
        registrar(i)

    @render.ui
    def tabla():
        c_pre = base_cache()
        return tabla_desc_html(c_pre["tabla"] if c_pre is not None else tabla_desc(filtrado(), d.cifras))

    def hist_df(df_h, titulo):
        f = graficos.barras(df_h, "x", "n") if len(df_h) else graficos.barras(pd.DataFrame({"x": [], "n": []}), "x", "n")
        return graficos.tema(f, titulo)

    @graficos.render_plotly
    def h_dias():
        c_pre = base_cache()
        h = c_pre["h_dias"] if c_pre is not None else resumen.histograma(filtrado(), "dias_estada", 60).rename(columns={"inicio": "x"})
        return hist_df(h, TEXTOS["h_dias"])

    @graficos.render_plotly
    def h_ln():
        c_pre = base_cache()
        h = c_pre["h_ln"] if c_pre is not None else resumen.histograma(filtrado(), "log_dias", None).rename(columns={"inicio": "x"})
        return hist_df(h, TEXTOS["h_ln"])

    @graficos.render_plotly
    def h_conc():
        c_pre = base_cache()
        conc = c_pre["conc"] if c_pre is not None else resumen.concentracion(filtrado())
        f = graficos.lineas(conc, "pct_egresos", ["pct_dias"])
        f.update_layout(showlegend=False, xaxis_title=TEXTOS["ayuda_conc"], yaxis_title="% de días-cama")
        return graficos.tema(f, TEXTOS["h_conc"])

    @render.ui
    def depuracion_resumen():
        return ui.p(llenar(TEXTOS["dep_resumen"], valores_depuracion(d.cifras)))

    @render.ui
    def depuracion():
        notas = notas_depuracion(d.cifras)
        return _guia(
            TEXTOS["dep_guia_titulo"],
            (TEXTOS["dep_1_t"], notas[0]),
            (TEXTOS["dep_2_t"], notas[1]),
            (TEXTOS["dep_3_t"], notas[2]),
        )
