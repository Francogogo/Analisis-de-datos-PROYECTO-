import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[2] / "dashboard"))
import resumen  # noqa: E402


def base():
    return pd.DataFrame({
        "dias_estada": [1, 2, 3, 24],
        "sexo": ["MUJER", "HOMBRE", "MUJER", "HOMBRE"],
        "region": ["A", "A", "B", "B"],
    })


def test_filtrar_ejemplo():
    r = resumen.filtrar(base(), {"sexo": ["MUJER"], "region": []})
    assert list(r.dias_estada) == [1, 3]


def test_filtro_vacio_no_filtra():
    b = base()
    assert len(resumen.filtrar(b, {})) == 4
    assert len(resumen.filtrar(b, {"sexo": [], "region": None})) == 4


def test_descriptivos():
    d = resumen.descriptivos(base())
    assert d["n"] == 4 and d["media"] == 7.5 and d["mediana"] == 2.5
    assert d["pct_prolongadas"] == 25.0
    assert abs(d["pct_dias_cama_prolongadas"] - 80.0) < 1e-9
    assert abs(d["p90"] - np.quantile([1, 2, 3, 24], 0.9)) < 1e-9


def test_prolongada_mayor_15():
    df = pd.DataFrame({"dias_estada": [15, 16]})
    assert resumen.descriptivos(df)["pct_prolongadas"] == 50.0


def test_sin_filas():
    d = resumen.descriptivos(base().iloc[0:0])
    assert d["n"] == 0
    assert all(np.isnan(v) for k, v in d.items() if k != "n")
    assert len(resumen.concentracion(base().iloc[0:0])) == 101
    assert resumen.cajas(base().iloc[0:0], "sexo", "dias_estada").empty
    assert resumen.histograma(base().iloc[0:0], "dias_estada", None).empty


def test_cajas_orden_mediana():
    c = resumen.cajas(base(), "sexo", "dias_estada")
    assert list(c.columns) == ["grupo", "n", "q1", "mediana", "q3", "min", "max"]
    assert list(c.grupo) == ["MUJER", "HOMBRE"]  # medianas 2 y 13
    assert c.mediana.is_monotonic_increasing


def test_cajas_bigotes_recortados():
    df = pd.DataFrame({"g": "a", "y": [1, 2, 3, 4, 100]})
    c = resumen.cajas(df, "g", "y").iloc[0]
    assert c["min"] == 1 and c["max"] == 4  # 100 queda fuera del bigote


def test_concentracion():
    c = resumen.concentracion(base())
    assert len(c) == 101 and list(c.columns) == ["pct_egresos", "pct_dias"]
    assert c.pct_dias.iloc[0] == 0 and abs(c.pct_dias.iloc[100] - 100) < 1e-9
    assert abs(c.pct_dias.iloc[25] - 80.0) < 1e-9  # el egreso más largo
    assert c.pct_dias.is_monotonic_increasing


def test_histograma_tope():
    h = resumen.histograma(base(), "dias_estada", 10)
    assert h.n.sum() == 3
    assert resumen.histograma(base(), "dias_estada", None).n.sum() == 4
