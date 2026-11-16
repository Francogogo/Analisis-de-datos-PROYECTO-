"""Pestana Simulación: dias estimados de M3 para un perfil elegido (asociación ajustada, no un pronóstico)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from shiny import module, reactive, render, ui

import componente
import graficos
import modelo
import etiquetas

TEXTOS = {
    "titulo": "Simulación con el modelo M3",
    "intro": (
        "Elige un perfil de egreso y mira la estadía típica que estima M3 para él. Lo que ves es una asociación "
        "ajustada, no un pronóstico para un paciente individual ni prueba de que cambiar una característica "
        "modifique la duración."
    ),
    "formula_whatif": "$$\\text{media geométrica} = e^{\\hat{\\mu}}, \\qquad \\hat{\\mu} = \\widehat{\\ln(\\text{días})}$$",
    "entradas_titulo": "Perfil",
    "etiquetas": {"capitulo": "Capítulo del diagnóstico (CIE-10)", "region": "Región", "sexo": "Sexo",
                  "establecimiento": "Establecimiento", "cirugia": "Cirugía", "fallecido": "Fallecido"},
    "edad": "Edad (años)",
    "resultado_titulo": "Días estimados",
    "resultado": (
        "La media geométrica ajustada para este perfil es de [[dias]] días, con un $\\text{IC}_{95\\%}$ entre "
        "[[inf]] y [[sup]] días. Ese rango acota el promedio del grupo con estas características, no la estadía "
        "de un egreso concreto."
    ),
    "resumen_resultado": (
        "El $\\text{IC}_{95\\%}$ mide la precisión de la media estimada, no la dispersión de los egresos: "
        "un intervalo estrecho no significa que los pacientes se parezcan entre sí."
    ),
    "cambio": "Frente al perfil de referencia ([[ref_desc]], 45 años: [[ref]] días), el cambio estimado es de [[cambio]] %.",
    "r2": (
        "El $R^2$ ajustado mide qué parte de la variación de $\\ln(\\text{días})$ explican estas variables. "
        "Aquí vale $[[r2]]$, cerca de un quinto; el resto depende de factores que la base no recoge."
    ),
    "edad_titulo": "Días estimados según la edad",
    "edad_nota": (
        "Varía solo la edad, entre 0 y 92 años, y deja fijo el resto del perfil. La banda es el "
        "$\\text{IC}_{95\\%}$ y el punto marca la edad elegida."
    ),
    "resumen_edad": (
        "La estadía crece de forma continua con la edad: en el perfil base pasa de 1,47 días a los 20 años "
        "a 2,52 a los 80 (+71 %)."
    ),
    "niveles_titulo": "Días estimados según una variable",
    "niveles_nota": (
        "Cada fila muestra la media geométrica ajustada $e^{\\hat{\\mu}}$ al cambiar solo la variable elegida y "
        "mantener fijo el resto del perfil."
    ),
    "resumen_niveles": (
        "Si dos intervalos no se traslapan, la diferencia entre esos niveles es significativa al 5 %. "
        "Si se traslapan, no necesariamente no hay diferencia."
    ),
    "niveles_sel": "Variable a comparar",
    "guias": {
        "resultado": {
            "titulo": "Por qué esta cifra no pronostica a un paciente puntual",
            "subcards": [
                {
                    "titulo": "Qué muestra el simulador",
                    "texto": (
                        "M3 modela $\\ln(\\text{días})$, así que $e^{\\hat{\\mu}}$ devuelve la media geométrica a días. "
                        "La cifra es un promedio de egresos con estas siete características, no la estadía esperada "
                        "de una persona. El modelo explica cerca de un quinto de la variación de $\\ln(\\text{días})$: "
                        "casi 80 % de la variación individual queda fuera, sobre todo la gravedad clínica, que DEIS no registra."
                    ),
                },
                {
                    "titulo": "Por qué el intervalo al 95 % es estrecho",
                    "texto": (
                        "El rango $[e^{\\hat{\\mu} - t_{0{,}975}\\text{EE}},\\, e^{\\hat{\\mu} + t_{0{,}975}\\text{EE}}]$ "
                        "acota la media del grupo, no la dispersión de los pacientes. Es estrecho porque el modelo "
                        "se estima con 968.098 egresos: con tantos casos la media queda bien determinada, aunque "
                        "cada egreso varíe mucho alrededor de ella."
                    ),
                },
            ],
        },
        "edad": {
            "titulo": "Por qué la curva de edad sube de forma suave",
            "subcards": [
                {
                    "titulo": "Qué muestra la curva",
                    "texto": (
                        "La línea traza $e^{\\hat{\\mu}}$ para cada edad de 0 a 92 años, con las otras seis variables "
                        "fijas en el perfil elegido. Solo recoge la asociación con la edad; las demás diferencias no "
                        "entran en esta curva."
                    ),
                },
                {
                    "titulo": "Por qué sube de forma suave y continua",
                    "texto": (
                        "La edad entra con dos términos, uno lineal y otro cuadrático, centrados en la edad promedio. "
                        "Sus coeficientes son positivos ($\\beta_1 = 0{,}0089$ y $\\beta_2 = 0{,}000011$), así que la "
                        "curva es suave y convexa: la pendiente aumenta con la edad."
                    ),
                },
            ],
        },
        "niveles": {
            "titulo": "Qué muestran los contrastes entre niveles",
            "subcards": [
                {
                    "titulo": "Cómo leer cada barra",
                    "texto": (
                        "Cada punto es $e^{\\hat{\\mu}}$ al cambiar solo esa variable, y su barra es el "
                        "$\\text{IC}_{95\\%}$. Las otras seis variables quedan iguales, así que la comparación se hace "
                        "dentro del mismo perfil."
                    ),
                },
                {
                    "titulo": "Dos contrastes en el perfil base",
                    "texto": (
                        "En Establecimiento, pasar de no SNSS a SNSS sube la estadía media de 1,82 a 3,10 días "
                        "(+70,0 %). En Capítulo, F00-F99 (trastornos mentales) llega a 5,74 días frente a K00-K93 "
                        "(+214,8 %). Son asociaciones con el resto del perfil fijo, no el efecto de cambiar el "
                        "establecimiento."
                    ),
                },
            ],
        },
    },
}

REFERENCIA = {"capitulo": "K00-K93", "region": "Metropolitana de Santiago", "sexo": "MUJER",
              "establecimiento": "No SNSS", "cirugia": "No", "fallecido": "No"}
EDAD_REF = 45


def perfil_ref(m3: dict) -> dict:
    """Perfil por defecto: nivel de referencia de cada factor (el primero) a los 45 años."""
    return {**{f: n[0] for f, n in m3["niveles"].items()}, "edad": EDAD_REF}


def cambio_pct(dias: float, ref: float) -> float:
    return (dias / ref - 1) * 100


def textos_resultado(perfil: dict, m3: dict) -> dict:
    """Valores de las frases del resultado; la descripción del perfil de referencia sale de sus niveles."""
    dias, inf, sup = modelo.dias_estimados(perfil, m3)
    base = perfil_ref(m3)
    ref = modelo.dias_estimados(base, m3)[0]
    cambio = cambio_pct(dias, ref)
    return {"dias": graficos.num(dias, 2), "inf": graficos.num(inf, 2), "sup": graficos.num(sup, 2),
            "ref": graficos.num(ref, 2), "cambio": ("+" if cambio > 0 else "") + graficos.num(cambio, 1),
            "ref_desc": ", ".join(etiquetas.etiqueta(f, str(base[f]))
                                  for f in m3["niveles"])}


def _llenar(t: str, v: dict) -> str:
    for k, x in v.items():
        t = t.replace(f"[[{k}]]", x)
    return t


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


def resultado_html(perfil: dict, m3: dict, cifras: dict):
    v = textos_resultado(perfil, m3)
    v["r2"] = graficos.num(cifras["modelos"]["M3"]["R² aj."], 3)
    return ui.div(
        ui.h4(TEXTOS["resultado_titulo"]),
        ui.p(ui.tags.strong(f"{v['dias']} días"), f" ($\\text{{IC}}_{{95\\%}}$: {v['inf']} a {v['sup']})", class_="whatif-cifra"),
        ui.p(_llenar(TEXTOS["resultado"], v)), ui.p(_llenar(TEXTOS["cambio"], v)), ui.p(_llenar(TEXTOS["r2"], v)),
    )


def fig_edad(perfil: dict, m3: dict) -> go.Figure:
    df = modelo.curva(perfil, "edad", m3)
    fig = graficos.lineas(df, "valor", ["dias"], banda=("inf", "sup"))
    fig.update_traces(hovertemplate="%{x} años: %{y:.2f} días<extra></extra>", selector=dict(name="dias"))
    dias = modelo.dias_estimados(perfil, m3)[0]
    fig.add_trace(go.Scatter(x=[perfil["edad"]], y=[dias], mode="markers", name="edad elegida",
                             marker=dict(color=graficos.TINTA, size=12, line=dict(color="#ffffff", width=2)),
                             hovertemplate="%{x} años: %{y:.2f} días<extra></extra>"))
    fig.update_xaxes(title="Edad (años)")
    fig.update_yaxes(title="Días estimados")
    fig.update_layout(showlegend=False)
    return fig


def fig_niveles(perfil: dict, variable: str, m3: dict) -> go.Figure:
    df = modelo.curva(perfil, variable, m3)
    df["valor"] = df["valor"].astype(str)
    if variable == "region":  # de norte a sur, como en Relaciones
        orden = [r for r, _ in graficos.REGIONES]
        df = df.sort_values("valor", key=lambda c: c.map(lambda r: orden.index(r) if r in orden else 99))
    if variable == "establecimiento":
        df["valor"] = df["valor"].map(lambda valor: etiquetas.etiqueta(variable, valor))
    # Frente al perfil elegido: rojo = más días, turquesa = menos, negro = el nivel actual del perfil.
    actual = modelo.dias_estimados(perfil, m3)[0]
    colores = [graficos.TINTA if abs(x - actual) < 1e-9 else graficos.MAS if x > actual else graficos.MENOS
               for x in df["dias"]]
    fig = graficos.intervalos(df, "valor", "dias", "inf", "sup", colores=colores)
    fig.add_vline(x=actual, line=dict(color=graficos.REFERENCIA, dash="dash"))
    if variable == "capitulo":
        fig.update_traces(customdata=[etiquetas.etiqueta(variable, v) for v in df["valor"]],
                          hovertemplate="%{customdata}: %{x:.2f} días<extra></extra>")
        fig.update_layout(height=max(400, len(df) * 26 + 120))
        fig.update_yaxes(dtick=1)
    else:
        fig.update_traces(hovertemplate="%{y}: %{x:.2f} días<extra></extra>")
    fig.update_xaxes(title="Días estimados")
    fig.update_yaxes(autorange="reversed")
    return fig


def leyenda_capitulos(m3: dict):
    return ui.tags.details(
        ui.tags.summary("Ver nombres de los capítulos CIE-10"),
        ui.tags.ul(*[ui.tags.li(etiquetas.etiqueta("capitulo", c)) for c in m3["niveles"]["capitulo"]]),
    )


@module.ui
def pestana_ui():
    sels = [ui.input_select(f, e, []) for f, e in TEXTOS["etiquetas"].items()]
    return ui.div(
        ui.h3(TEXTOS["titulo"]), ui.p(TEXTOS["intro"]),
        _formula(TEXTOS["formula_whatif"]),
        ui.layout_sidebar(
            ui.sidebar(ui.h5(TEXTOS["entradas_titulo"]), sels[0], ui.output_ui("detalle_capitulo"), *sels[1:],
                       ui.input_slider("edad", TEXTOS["edad"], 0, 92, EDAD_REF, step=1), width=320),
            componente.componente(
                TEXTOS["resultado_titulo"], ui.output_ui("resultado"),
                abierto=True,
                resumen=ui.p(TEXTOS["resumen_resultado"]), detalle=_guia("resultado"),
            ),
            componente.componente(
                TEXTOS["edad_titulo"], ui.h4(TEXTOS["edad_titulo"]), ui.p(TEXTOS["edad_nota"]),
                graficos.salida("graf_edad"),
                resumen=ui.p(TEXTOS["resumen_edad"]), detalle=_guia("edad"),
            ),
            componente.componente(
                TEXTOS["niveles_titulo"], ui.h4(TEXTOS["niveles_titulo"]), ui.p(TEXTOS["niveles_nota"]),
                ui.div(
                    ui.input_select("variable", TEXTOS["niveles_sel"], TEXTOS["etiquetas"], selected="establecimiento"),
                    graficos.salida("graf_niveles"), ui.output_ui("ayuda_capitulos"),
                    class_="vista-niveles",
                ),
                resumen=ui.p(TEXTOS["resumen_niveles"]), detalle=_guia("niveles"),
            ),
        ),
        class_="pestana-texto",
    )


@module.server
def pestana_server(input, output, session, d):
    m3 = d.m3

    @reactive.effect
    def _niveles():
        for f, niv in m3["niveles"].items():
            ui.update_select(f, choices=etiquetas.opciones(f, niv), selected=niv[0])

    @reactive.calc
    def perfil():
        p = {f: input[f]() for f in m3["niveles"]}
        for f, v in p.items():
            if v not in m3["niveles"][f]:  # los selects aún no recibieron sus niveles
                return perfil_ref(m3)
        return {**p, "edad": input.edad()}

    @render.ui
    def resultado():
        return resultado_html(perfil(), m3, d.cifras)

    @render.ui
    def detalle_capitulo():
        return ui.p(etiquetas.etiqueta("capitulo", perfil()["capitulo"]), class_="detalle-capitulo")

    @render.ui
    def ayuda_capitulos():
        return leyenda_capitulos(m3) if input.variable() == "capitulo" else None

    @graficos.render_plotly
    def graf_edad():
        return fig_edad(perfil(), m3)

    @graficos.render_plotly
    def graf_niveles():
        return fig_niveles(perfil(), input.variable(), m3)
