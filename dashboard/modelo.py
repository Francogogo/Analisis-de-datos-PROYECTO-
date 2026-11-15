"""Modelo M3: dias estimados (media geometrica ajustada) y curvas por variable."""
import numpy as np
import pandas as pd

Z = 1.96
EDAD_MAX = 92


def fila(perfil: dict, m3: dict) -> np.ndarray:
    """Vector de diseno x de M3 para un perfil; ValueError si falta un dato o un nivel no existe."""
    for factor, niveles in m3["niveles"].items():
        if perfil.get(factor) not in niveles:
            raise ValueError(f"Nivel desconocido para {factor}: {perfil.get(factor)!r}")
    ec = float(perfil["edad"]) - m3["edad_prom"]
    x = []
    for n in m3["nombres"]:
        if n == "Intercept":
            x.append(1.0)
        elif n == "edad_c":
            x.append(ec)
        elif n == "I(edad_c ** 2)":
            x.append(ec**2)
        else:
            factor, nivel = n.split(": ", 1)
            x.append(1.0 if perfil[factor] == nivel else 0.0)
    return np.array(x)


def dias_estimados(perfil: dict, m3: dict) -> tuple[float, float, float]:
    """(media geometrica ajustada, inf, sup) con IC 95 % de la media, no intervalo individual."""
    x = fila(perfil, m3)
    eta = float(x @ np.asarray(m3["beta"]))
    ee = float(np.sqrt(x @ np.asarray(m3["cov"]) @ x))
    return float(np.exp(eta)), float(np.exp(eta - Z * ee)), float(np.exp(eta + Z * ee))


def curva(perfil: dict, variable: str, m3: dict) -> pd.DataFrame:
    """Dias estimados al variar una variable (edad 0..92 o los niveles de un factor), el resto fijo."""
    valores = list(range(EDAD_MAX + 1)) if variable == "edad" else m3["niveles"][variable]
    filas = [(v, *dias_estimados({**perfil, variable: v}, m3)) for v in valores]
    return pd.DataFrame(filas, columns=["valor", "dias", "inf", "sup"])
