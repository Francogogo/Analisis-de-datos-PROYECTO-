import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "dashboard"))
import graficos  # noqa: E402


def test_num_coma_decimal():
    assert graficos.num(968098, 0) == "968.098"
    assert graficos.num(47.07, 1) == "47,1"
    assert graficos.num(1234567.891, 2) == "1.234.567,89"
    assert graficos.num(-0.5, 1) == "-0,5"


def test_num_nan():
    assert graficos.num(float("nan")) == "—"
    assert graficos.num(np.nan, 0) == "—"


def test_cajas_precalculadas():
    df = pd.DataFrame({"grupo": ["a", "b"], "n": [5, 7], "q1": [1, 2], "mediana": [2, 3],
                       "q3": [3, 4], "min": [0, 1], "max": [5, 6]})
    f = graficos.cajas(df)
    assert len(f.data) == 1 and f.data[0].type == "box"
    t = f.data[0]
    assert list(t.q1) == [1, 2] and list(t.median) == [2, 3] and list(t.q3) == [3, 4]
    assert t.y is None


def test_tema():
    import plotly.graph_objects as go
    f = graficos.tema(go.Figure(), "Título")
    assert "Public Sans" in f.layout.font.family
    assert f.layout.separators == ",."
    assert f.layout.font.color == graficos.TINTA and f.layout.colorway[0] == graficos.ACENTO


def test_dispersion_es_una_imagen():
    import base64
    fig = graficos.dispersion(pd.DataFrame({"x": range(50000), "y": range(50000)}), "x", "y")
    assert len(fig.data) == 0 and len(fig.layout.images) == 1
    png = base64.b64decode(fig.layout.images[0].source.split(",", 1)[1])
    assert png.startswith(b"\x89PNG") and fig.layout.xaxis.range[0] < 0 < 49999 < fig.layout.xaxis.range[1]


def test_resto_construye():
    df = pd.DataFrame({"x": ["a", "b"], "y": [1.0, 2.0], "lo": [0.5, 1.5], "hi": [1.5, 2.5]})
    assert len(graficos.barras(df, "x", "y", horizontal=True, linea=1.5).data) == 1
    assert len(graficos.barras(df, "x", "y", linea=1.5).data) == 1
    assert len(graficos.lineas(df, "x", ["y"], banda=("lo", "hi")).data) == 3
    assert len(graficos.intervalos(df, "x", "y", "lo", "hi").data) == 1
    assert len(graficos.calor(pd.DataFrame([[1, 2], [3, 4]], columns=["a", "b"])).data) == 1


def test_colores_de_serie_y_umbral():
    df = pd.DataFrame({"x": [1, 2], "observada": [2, 3], "ajustada": [1, 2], "lo": [1, 2], "hi": [3, 4]})
    fig = graficos.lineas(df, "x", ["observada", "ajustada"], banda=("lo", "hi"))
    assert [t.line.color for t in fig.data[2:]] == [graficos.ACENTO, graficos.TINTA]
    assert graficos.UMBRAL not in fig.layout.colorway
    assert graficos.barras(df, "x", "observada", linea=2).layout.shapes[0].line.color == graficos.UMBRAL
