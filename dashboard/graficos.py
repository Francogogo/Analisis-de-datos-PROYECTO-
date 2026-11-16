"""Gráficos Plotly con el tema común del dashboard y formato numérico es-CL."""
import base64
import math
import struct
import zlib

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from shiny import ui
from shiny.module import resolve_id
from shiny.ui.fill import as_fill_item
from shiny.render.renderer import Jsonifiable, Renderer

# Marcas neutras en cobalto institucional; grilla y ejes en gris azulado, recesivos.
TINTA, ACENTO, CLARO, GRIS = "#0f1b2d", "#1d4ed8", "#e3e9f0", "#5b6b7f"
# Líneas de referencia (recta Q-Q, cero, promedio): neutras, para que ningún color de dato se gaste en ellas.
REFERENCIA = "#44546a"
UMBRAL = "#8a3220"  # líneas de corte de un criterio (η² = 0,01)
SERIES = [ACENTO, TINTA, GRIS]

# Código de color clínico. Cada familia tiene un solo significado en todo el dashboard y se validó con
# simulación de daltonismo (Machado et al. 2009) y contraste sobre blanco.
#
# Carga: % de estadías prolongadas (> 15 días) de un grupo. Escala secuencial naranja -> rojo profundo, como
# OrRd de ColorBrewer (Harrower y Brewer 2003): más oscuro = más carga de días-cama. Luminancia monótona.
CARGA = ["#c9a25c", "#d9762c", "#bf4a2a", "#8f2327", "#5b1120"]
CORTES_CARGA = [5, 10, 15, 25]
TRAMOS_CARGA = ["< 5 %", "5–10 %", "10–15 %", "15–25 %", "≥ 25 %"]

# Semáforo: estado de un supuesto o de un criterio, siempre con ícono y texto (no solo color).
# Verde azulado, ámbar y bermellón: pares separados para deuteranopía, a diferencia del rojo/verde puro.
ESTADO = {"cumple": ("#0f8a62", "✓", "Cumple"), "alerta": ("#c98a00", "!", "Con reparos"),
          "no": ("#b42318", "✕", "No cumple")}

# Divergente: cambio frente a la referencia. Turquesa = menos días, rojo = más días, gris = sin diferencia clara.
# Turquesa en vez del azul de RdBu para no confundirse con el cobalto de las marcas neutras; el par se
# validó con simulación de deuteranopía.
MENOS, NEUTRO, MAS = "#0d7f8c", "#8a979b", "#b2182b"

# Geografía: macrozonas de norte a sur con el color de su paisaje dominante: desierto, valles de vino,
# bosque, lagos y hielo austral. Cinco tonos en vez de 16 para que se distingan.
ZONAS = {"Norte": "#b8621b", "Centro": "#8e3f86", "Centro Sur": "#2e8540", "Sur": "#1b86a6", "Austral": "#4c4f9e"}
REGIONES = [  # de norte a sur, con su macrozona
    ("De Arica y Parinacota", "Norte"), ("De Tarapacá", "Norte"), ("De Antofagasta", "Norte"),
    ("De Atacama", "Norte"), ("De Coquimbo", "Centro"), ("De Valparaíso", "Centro"),
    ("Metropolitana de Santiago", "Centro"), ("Del Libertador B. O'Higgins", "Centro"),
    ("Del Maule", "Centro Sur"), ("De Ñuble", "Centro Sur"), ("Del Bíobío", "Centro Sur"),
    ("De La Araucanía", "Centro Sur"), ("De Los Ríos", "Sur"), ("De Los Lagos", "Sur"),
    ("De Aisén del Gral. C. Ibáñez del Campo", "Austral"), ("De Magallanes y de La Antártica Chilena", "Austral"),
]
MACROZONA = dict(REGIONES)
# Fallecido: negro, como la etiqueta negra del triage START; los que egresan vivos van en gris.
FALLECIDO = "#1d2326"


def tramo_carga(pct: float) -> int:
    """Índice en CARGA del % de estadías prolongadas."""
    return sum(pct >= c for c in CORTES_CARGA)


def css_tokens() -> str:
    """Variables CSS con el mismo código de color, para que la interfaz y los gráficos no se separen."""
    v = {f"--carga-{i + 1}": c for i, c in enumerate(CARGA)}
    v |= {f"--estado-{k}": c for k, (c, _, _) in ESTADO.items()}
    v |= {"--menos": MENOS, "--neutro": NEUTRO, "--mas": MAS, "--umbral": UMBRAL, "--fallecido": FALLECIDO}
    v |= {"--zona-" + k.lower().replace(" ", "-"): c for k, c in ZONAS.items()}
    return ":root { " + " ".join(f"{k}: {c};" for k, c in v.items()) + " }"
FUENTE = "'Public Sans', system-ui, sans-serif"
MAX_PUNTOS = 20000  # muestra de la nube de residuos; se dibuja como imagen (ver puntos), no como nodos SVG


def num(x: float, dec: int = 1) -> str:
    """Coma decimal y punto de miles; NaN -> '—'."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{x:,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def tema(fig: go.Figure, titulo: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=21, color=TINTA, weight=700), x=0.01, xanchor="left"),
        font=dict(family=FUENTE, size=16, color=TINTA),
        colorway=SERIES,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        separators=",.", hovermode="closest",
        hoverlabel=dict(bgcolor=TINTA, bordercolor=TINTA, font=dict(color="white", family=FUENTE, size=16)),
        margin=dict(l=55, r=24, t=58 if titulo else 28, b=55),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor=CLARO, linecolor=GRIS, automargin=True, zerolinecolor=GRIS)
    fig.update_yaxes(gridcolor=CLARO, linecolor=GRIS, automargin=True, zerolinecolor=GRIS)
    return fig


def barras(df, x, y, horizontal=False, linea=None, colores=None):
    fig = go.Figure(go.Bar(
        x=df[y] if horizontal else df[x], y=df[x] if horizontal else df[y],
        orientation="h" if horizontal else "v", marker_color=ACENTO if colores is None else list(colores),
        hovertemplate="%{y}: %{x}<extra></extra>" if horizontal else "%{x}: %{y}<extra></extra>"))
    if linea is not None:
        (fig.add_vline if horizontal else fig.add_hline)(
            **{"x" if horizontal else "y": linea}, line=dict(color=UMBRAL, dash="dash"))
    return tema(fig)


def cajas(df, clases=None, colores=None, leyenda=""):
    """Caja con cuartiles y bigotes ya calculados (salida de resumen.cajas).

    Con `clases` (una por fila) y `colores` ({clase: color}) arma una traza por clase, en el orden de `colores`,
    para que la leyenda sea la clave del color. El eje conserva el orden de las filas."""
    if clases is None:
        clases, colores = ["" for _ in range(len(df))], {"": ACENTO}
    clases = pd.Series(list(clases), index=df.index)
    fig = go.Figure()
    for clase, color in colores.items():
        sub = df[clases == clase]
        if sub.empty:
            continue
        fig.add_trace(go.Box(
            x=sub["grupo"], q1=sub["q1"], median=sub["mediana"], q3=sub["q3"],
            lowerfence=sub["min"], upperfence=sub["max"], marker_color=color, name=clase or "grupos",
            showlegend=bool(clase), customdata=sub["n"], hovertemplate="n = %{customdata}<extra></extra>"))
    fig.update_xaxes(categoryorder="array", categoryarray=list(df["grupo"]))
    tema(fig)
    if leyenda:
        # Título a la izquierda de las entradas: con el título arriba Plotly deja de pasar entradas a otra fila.
        fig.update_layout(legend=dict(title_text=leyenda, x=0, xanchor="left"), margin=dict(t=100))
    return fig


def lineas(df, x, ys, banda=None):
    fig = go.Figure()
    if banda:
        fig.add_trace(go.Scatter(x=df[x], y=df[banda[1]], mode="lines", line=dict(width=0),
                                 hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=df[x], y=df[banda[0]], mode="lines", line=dict(width=0),
                                 fill="tonexty", fillcolor="rgba(29,78,216,0.14)",
                                 hoverinfo="skip", showlegend=False))
    for i, y in enumerate(ys):
        fig.add_trace(go.Scatter(x=df[x], y=df[y], mode="lines",
                                 line=dict(width=2.5, color=SERIES[i % len(SERIES)]), name=y))
    return tema(fig)


def intervalos(df, etiqueta, centro, inf, sup, colores=None):
    """Punto e intervalo por fila. Con `colores` (uno por fila), cada intervalo toma el color de su punto."""
    if colores is None:
        fig = go.Figure(go.Scatter(
            x=df[centro], y=df[etiqueta], mode="markers", marker=dict(color=ACENTO, size=8),
            error_x=dict(type="data", symmetric=False, color=GRIS,
                         array=df[sup] - df[centro], arrayminus=df[centro] - df[inf])))
        return tema(fig)
    fig = go.Figure()
    colores = pd.Series(list(colores), index=df.index)
    for color in dict.fromkeys(colores):
        sub = df[colores == color]
        fig.add_trace(go.Scatter(
            x=sub[centro], y=sub[etiqueta], mode="markers", marker=dict(color=color, size=10),
            error_x=dict(type="data", symmetric=False, color=color, thickness=2,
                         array=sub[sup] - sub[centro], arrayminus=sub[centro] - sub[inf]), showlegend=False))
    # dtick=1: con muchas categorías Plotly salta etiquetas y los puntos quedarían sin nombre.
    fig.update_yaxes(categoryorder="array", categoryarray=list(df[etiqueta]), dtick=1)
    fig.update_layout(height=max(380, len(df) * 24 + 130))
    return tema(fig)


def _png(rgba: np.ndarray) -> bytes:
    """PNG RGBA mínimo con la biblioteca estándar (sin Pillow)."""
    alto, ancho, _ = rgba.shape
    filas = np.hstack([np.zeros((alto, 1), np.uint8), rgba.reshape(alto, -1)])  # filtro 0 en cada fila
    def trozo(tipo, dato):
        return struct.pack(">I", len(dato)) + tipo + dato + struct.pack(">I", zlib.crc32(tipo + dato))
    return (b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 6, 0, 0, 0))
            + trozo(b"IDAT", zlib.compress(filas.tobytes(), 6)) + trozo(b"IEND", b""))


def puntos(fig, x, y, row=None, col=None, ancho=1800, alto=580, radio=4, alfa=0.5, color=ACENTO):
    """Dibuja la nube de puntos como una sola imagen bajo los ejes de Plotly.

    Miles de marcadores SVG obligan al navegador a recomponer la capa en cada cuadro de scroll; una imagen
    es un nodo. Cada punto es un disco de `radio` px con opacidad `alfa`; donde se superponen k puntos la
    opacidad es 1 - (1 - alfa)^k, igual que al apilar marcadores semitransparentes. Sin hover por punto."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    def rango(v):
        lo, hi = float(np.min(v)), float(np.max(v))
        m = (hi - lo) * 0.04 or 1.0
        return lo - m, hi + m
    (x0, x1), (y0, y1) = rango(x), rango(y)
    px = np.rint((x - x0) / (x1 - x0) * (ancho - 1)).astype(int)
    py = np.rint((y1 - y) / (y1 - y0) * (alto - 1)).astype(int)
    cuenta = np.zeros((alto, ancho), np.uint32)
    for dx in range(-radio, radio + 1):
        for dy in range(-radio, radio + 1):
            if dx * dx + dy * dy <= radio * radio:
                np.add.at(cuenta, (np.clip(py + dy, 0, alto - 1), np.clip(px + dx, 0, ancho - 1)), 1)
    rgba = np.zeros((alto, ancho, 4), np.uint8)
    rgba[..., :3] = [int(color[k:k + 2], 16) for k in (1, 3, 5)]
    rgba[..., 3] = np.rint(255 * (1 - (1 - alfa) ** cuenta.astype(float)))
    fig.add_layout_image(source="data:image/png;base64," + base64.b64encode(_png(rgba)).decode(),
                         xref="x", yref="y", x=x0, y=y1, sizex=x1 - x0, sizey=y1 - y0, sizing="stretch",
                         xanchor="left", yanchor="top", layer="below", row=row, col=col)
    fig.update_xaxes(range=[x0, x1], row=row, col=col)
    fig.update_yaxes(range=[y0, y1], row=row, col=col)
    return fig


def dispersion(df, x, y, **kw):
    return puntos(tema(go.Figure()), df[x], df[y], **kw)


def calor(matriz):
    fig = go.Figure(go.Heatmap(
        z=matriz.values, x=list(matriz.columns), y=list(matriz.index),
        colorscale=[[0, "#eef3fd"], [0.5, "#7da0ef"], [1, "#163a9e"]], hovertemplate="%{y} / %{x}: %{z}<extra></extra>"))
    return tema(fig)


def _icono(d: str) -> ui.Tag:
    return ui.HTML(f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.2" '
                   f'stroke-linecap="round" stroke-linejoin="round"><path d="{d}"/></svg>')


ICONOS = {"cumple": _icono("M5 12.5l4.5 4.5L19 7.5"), "alerta": _icono("M12 5v9M12 19.2v.1"),
          "no": _icono("M6.5 6.5l11 11M17.5 6.5l-11 11")}


def semaforo(estado: str, titulo: str, nota: str = "") -> ui.Tag:
    """Ficha de estado: ícono, palabra y color dicen lo mismo, para que no dependa solo del color."""
    _, _, palabra = ESTADO[estado]
    return ui.div(
        ui.span(ICONOS[estado], class_="semaforo-icono", aria_hidden="true"),
        ui.div(ui.p(ui.tags.strong(titulo), ui.span(palabra, class_="semaforo-estado")),
               ui.p(nota, class_="semaforo-nota") if nota else None),
        class_=f"semaforo semaforo--{estado}",
    )


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
