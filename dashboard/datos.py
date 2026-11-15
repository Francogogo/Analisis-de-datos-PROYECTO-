"""Carga de datos del dashboard: base, modelo M3 y cifras del paper."""
import json
import shutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtri

APP = Path(__file__).resolve().parent / "datos_app"
RAIZ = Path(__file__).resolve().parents[1]
REFS = {"capitulo": "K00-K93", "region": "Metropolitana de Santiago", "sexo": "MUJER",
        "establecimiento": "No SNSS", "cirugia": "No", "fallecido": "No"}


@dataclass(frozen=True)
class Datos:
    base: pd.DataFrame
    cifras: dict
    m3: dict


def preparar() -> None:
    """Reajusta M3 con la base completa, valida contra el paper y escribe datos_app/."""
    base = pd.read_parquet(RAIZ / "results" / "base_figuras.parquet")
    cifras = json.loads((RAIZ / "results" / "cifras_avance2_v8.json").read_text(encoding="utf-8"))
    nombres = list(cifras["coef"])
    edad_prom = float(base["edad"].mean())
    niveles = {f: [r] for f, r in REFS.items()}
    for n in nombres:
        if ": " in n:
            f, lv = n.split(": ", 1)
            niveles[f].append(lv)
    X = np.empty((len(base), len(nombres)), dtype=np.float64)
    ec = (base["edad"] - edad_prom).to_numpy(dtype=np.float64)
    for j, n in enumerate(nombres):
        if n == "Intercept":
            X[:, j] = 1.0
        elif n == "edad_c":
            X[:, j] = ec
        elif n == "I(edad_c ** 2)":
            X[:, j] = ec ** 2
        else:
            f, lv = n.split(": ", 1)
            X[:, j] = (base[f] == lv).to_numpy()
    y = base["log_dias"].to_numpy(dtype=np.float64)
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    ajuste = X @ beta
    res = y - ajuste
    gl = len(y) - len(nombres)
    sigma2 = float(res @ res / gl)
    cov = sigma2 * xtx_inv
    sct = float(((y - y.mean()) ** 2).sum())
    r2_aj = 1 - (float(res @ res) / gl) / (sct / (len(y) - 1))
    # validaciones contra el paper antes de escribir
    assert np.abs(ajuste - base["ajuste_ln"].to_numpy()).max() < 1e-7, "ajuste_ln no calza"
    for n, b, e in zip(nombres, beta, np.sqrt(np.diag(cov))):
        assert round(float(b), 6) == cifras["coef"][n]["β"], f"beta {n}"
        assert abs(e - cifras["coef"][n]["EE"]) < 1e-6, f"EE {n}"
    assert abs(r2_aj - cifras["modelos"]["M3"]["R² aj."]) < 1e-6, "R2 aj"
    m3 = {"nombres": nombres, "beta": beta.tolist(), "cov": cov.tolist(), "edad_prom": edad_prom,
          "sigma2": sigma2, "gl_resid": gl, "r2_aj": r2_aj, "niveles": niveles}
    APP.mkdir(exist_ok=True)
    for c in base.select_dtypes(["object", "string"]).columns:
        base[c] = base[c].astype("category")
    # sin pérdida: días <= 365 y edades en múltiplos de 0,5 caben en int16 / float32
    base["dias_estada"] = base["dias_estada"].astype("int16")
    base["edad"] = base["edad"].astype("float32")
    base.to_parquet(APP / "base.parquet", compression="zstd", index=False)
    (APP / "m3.json").write_text(json.dumps(m3, ensure_ascii=False), encoding="utf-8")
    shutil.copyfile(RAIZ / "results" / "cifras_avance2_v8.json", APP / "cifras.json")


@lru_cache(maxsize=16)
def cuantiles_normales(n: int) -> np.ndarray:
    """Cuantiles teóricos de N(0,1) vectorizados y en caché por tamaño n."""
    return ndtri((np.arange(n, dtype=np.float64) + 0.5) / n)


@lru_cache(maxsize=1)
def cargar() -> Datos:
    base = pd.read_parquet(APP / "base.parquet")
    cifras = json.loads((APP / "cifras.json").read_text(encoding="utf-8"))
    m3 = json.loads((APP / "m3.json").read_text(encoding="utf-8"))
    return Datos(base, cifras, m3)
