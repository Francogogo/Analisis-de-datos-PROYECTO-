"""Gráficos Plotly con el tema común del dashboard y formato numérico es-CL."""
import math

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from shiny import ui
from shiny.module import resolve_id
from shiny.ui.fill import as_fill_item
from shiny.render.renderer import Jsonifiable, Renderer

TINTA, ACENTO, CLARO, ALERTA, GRIS = "#132f38", "#086c70", "#dcece8", "#a94530", "#6b7c82"
REFERENCIA = "#365b86"
SERIES = [ACENTO, REFERENCIA, TINTA, GRIS]
FUENTE = "Figtree, system-ui, sans-serif"
MAX_PUNTOS = 20000


def num(x: float, dec: int = 1) -> str:
    """Coma decimal y punto de miles; NaN -> '—'."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{x:,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def tema(fig: go.Figure, titulo: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=16, color=TINTA), x=0.02, xanchor="left"),
        font=dict(family=FUENTE, size=12, color=TINTA),
        colorway=SERIES,
        paper_bgcolor="#fffefa", plot_bgcolor="#fffefa",
        separators=",.", hovermode="closest",
        hoverlabel=dict(bgcolor=TINTA, bordercolor=TINTA, font=dict(color="white", family=FUENTE)),
        margin=dict(l=55, r=24, t=58 if titulo else 28, b=55),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor=CLARO, linecolor=GRIS, automargin=True, zerolinecolor=GRIS)
    fig.update_yaxes(gridcolor=CLARO, linecolor=GRIS, automargin=True, zerolinecolor=GRIS)
    return fig


def barras(df, x, y, horizontal=False, linea=None):
    fig = go.Figure(go.Bar(
        x=df[y] if horizontal else df[x], y=df[x] if horizontal else df[y],
        orientation="h" if horizontal else "v", marker_color=ACENTO,
        hovertemplate="%{y}: %{x}<extra></extra>" if horizontal else "%{x}: %{y}<extra></extra>"))
    if linea is not None:
        (fig.add_vline if horizontal else fig.add_hline)(
            **{"x" if horizontal else "y": linea}, line=dict(color=ALERTA, dash="dash"))
    return tema(fig)


def cajas(df):
    """Caja con cuartiles y bigotes ya calculados (salida de resumen.cajas)."""
    fig = go.Figure(go.Box(
        x=df["grupo"], q1=df["q1"], median=df["mediana"], q3=df["q3"],
        lowerfence=df["min"], upperfence=df["max"], marker_color=ACENTO,
        customdata=df["n"], hovertemplate="n = %{customdata}<extra></extra>"))
    return tema(fig)


def lineas(df, x, ys, banda=None):
    fig = go.Figure()
    if banda:
        fig.add_trace(go.Scatter(x=df[x], y=df[banda[1]], mode="lines", line=dict(width=0),
                                 hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=df[x], y=df[banda[0]], mode="lines", line=dict(width=0),
                                 fill="tonexty", fillcolor="rgba(8,108,112,0.15)",
                                 hoverinfo="skip", showlegend=False))
    for i, y in enumerate(ys):
        fig.add_trace(go.Scatter(x=df[x], y=df[y], mode="lines",
                                 line=dict(width=2.5, color=SERIES[i % len(SERIES)]), name=y))
    return tema(fig)


def intervalos(df, etiqueta, centro, inf, sup):
    fig = go.Figure(go.Scatter(
        x=df[centro], y=df[etiqueta], mode="markers", marker=dict(color=ACENTO, size=8),
        error_x=dict(type="data", symmetric=False, color=GRIS,
                     array=df[sup] - df[centro], arrayminus=df[centro] - df[inf])))
    return tema(fig)


def dispersion(df, x, y):
    if len(df) > MAX_PUNTOS:
        raise ValueError(f"máximo {MAX_PUNTOS} puntos, recibidos {len(df)}")
    # float32 basta para dibujar y para hovers de 2–3 decimales, y pesa la mitad en el envío
    fig = go.Figure(go.Scatter(x=df[x].astype("float32"), y=df[y].astype("float32"), mode="markers",
                               marker=dict(color=ACENTO, size=4, opacity=0.5)))
    return tema(fig)


def calor(matriz):
    fig = go.Figure(go.Heatmap(
        z=matriz.values, x=list(matriz.columns), y=list(matriz.index),
        colorscale=[[0, CLARO], [1, ACENTO]], hovertemplate="%{y} / %{x}: %{z}<extra></extra>"))
    return tema(fig)


def salida(id_: str) -> ui.Tag:
    """Contenedor de un gráfico; lo dibuja www/js/graficos.js. Como `output_widget`, se estira
    al alto de su fila cuando la figura no fija `height`."""
    return as_fill_item(ui.div(id=resolve_id(id_), class_="plotly-salida"))


class render_plotly(Renderer[go.Figure]):
    """Manda la figura como JSON (los arreglos numéricos van en base64) a `salida`.

    Reemplaza a shinywidgets: cada FigureWidget enviaba por el websocket su propia copia de
    plotly.js (unos 5 MB por gráfico). Aquí plotly.js se sirve una vez como archivo estático."""

    async def transform(self, value: go.Figure) -> Jsonifiable:
        return pio.to_json(value, validate=False)
