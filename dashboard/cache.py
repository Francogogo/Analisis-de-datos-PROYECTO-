"""Caché de arranque para agregados pesados de la base completa (sin alterar filtros ni pruebas)."""
from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd

import datos
import p_diagnosticos
import p_exploracion
import p_relaciones
import resumen

_CACHE: dict[int, dict[str, Any]] = {}


def _entrada(d: datos.Datos) -> dict[str, Any]:
    bid = id(d.base)
    if bid not in _CACHE:
        _CACHE[bid] = {"base_ref": d.base, "cajas_rel": {}, "norm_figs": {}}
    return _CACHE[bid]


def exploracion_base(d: datos.Datos) -> dict[str, Any]:
    """Agregados de la base sin filtrar para la pestaña Exploración."""
    e = _entrada(d)
    if "exploracion" not in e:
        e["exploracion"] = {
            "cajas": p_exploracion.cajas_valores(d.base, d.cifras),
            "tabla": p_exploracion.tabla_desc(d.base, d.cifras),
            "h_dias": resumen.histograma(d.base, "dias_estada", 60).rename(columns={"inicio": "x"}),
            "h_ln": resumen.histograma(d.base, "log_dias", None).rename(columns={"inicio": "x"}),
            "conc": resumen.concentracion(d.base),
        }
    return e["exploracion"]


def diagnosticos_base(d: datos.Datos) -> dict[str, Any]:
    """Muestra, ventiles e histograma de residuos precalculados para Diagnósticos."""
    e = _entrada(d)
    if "diagnosticos" not in e:
        e["diagnosticos"] = {
            "muestra": p_diagnosticos.muestra(d.base),
            "ventiles": p_diagnosticos.ventiles(d.base),
            "hist": resumen.histograma(d.base, "residuo", None),
        }
    return e["diagnosticos"]


def cajas_relaciones(d: datos.Datos, por: str) -> pd.DataFrame:
    e = _entrada(d)
    if por not in e["cajas_rel"]:
        cj = resumen.cajas(d.base, por, "log_dias")
        if por == "tramo_edad":
            orden = d.base.groupby("tramo_edad", observed=True)["edad"].mean().sort_values().index.tolist()
            cj = cj.set_index("grupo").loc[orden].reset_index()
        e["cajas_rel"][por] = cj
    return e["cajas_rel"][por]


@lru_cache(maxsize=4)
def _cramer_keyed(key: int):
    return None


def calentar(d: datos.Datos | None = None) -> datos.Datos:
    """Precalcula en el arranque las vistas pesadas de la base completa."""
    d = d or datos.cargar()
    exploracion_base(d)
    diagnosticos_base(d)
    # Precarga las variables de Relaciones más consultadas en exposición oral
    for por in ("tramo_edad", "capitulo", "establecimiento", "sexo"):
        cajas_relaciones(d, por)
    return d
