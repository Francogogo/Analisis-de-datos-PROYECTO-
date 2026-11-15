"""Resúmenes puros sobre la base de egresos (sin Shiny, sin gráficos)."""
import numpy as np
import pandas as pd

UMBRAL_PROLONGADA = 15  # prolongada = dias_estada > 15


def filtrar(base: pd.DataFrame, filtros: dict) -> pd.DataFrame:
    """Filtra por columna; una lista vacía o None significa 'sin filtro'."""
    activos = [(col, vals) for col, vals in filtros.items() if vals is not None and len(vals) > 0]
    if not activos:
        return base
    mask = np.ones(len(base), dtype=bool)
    for col, vals in activos:
        mask &= base[col].isin(list(vals)).to_numpy(dtype=bool)
    return base[mask]


def descriptivos(df: pd.DataFrame) -> dict:
    d = df["dias_estada"]
    if len(d) == 0:
        nan = float("nan")
        return {"n": 0, "media": nan, "mediana": nan, "p90": nan,
                "pct_prolongadas": nan, "pct_dias_cama_prolongadas": nan}
    larga = d > UMBRAL_PROLONGADA
    return {
        "n": int(len(d)),
        "media": float(d.mean()),
        "mediana": float(d.median()),
        "p90": float(d.quantile(0.9)),
        "pct_prolongadas": float(larga.mean() * 100),
        "pct_dias_cama_prolongadas": float(d[larga].sum() / d.sum() * 100),
    }


def concentracion(df: pd.DataFrame) -> pd.DataFrame:
    """Curva de concentración: % de días-cama que suma el p% de egresos más largos."""
    p = np.arange(101)
    n_rows = len(df)
    if n_rows == 0:
        return pd.DataFrame({"pct_egresos": p, "pct_dias": np.nan})
    col = df["dias_estada"].to_numpy()
    # Vía O(n + 365) por conteo exacto cuando son enteros en [0, 365]
    if np.issubdtype(col.dtype, np.integer) and n_rows > 1000:
        cmin, cmax = int(col.min()), int(col.max())
        if cmin >= 0 and cmax <= 365:
            counts = np.bincount(col, minlength=cmax + 1)[::-1]
            vals = np.arange(cmax, -1, -1, dtype=np.float64)
            total = float((counts * vals).sum())
            if total == 0:
                return pd.DataFrame({"pct_egresos": p, "pct_dias": np.nan})
            cum_n = np.cumsum(counts)
            cum_s = np.cumsum(counts * vals)
            ks = np.round(p / 100 * n_rows).astype(int)
            idx = np.searchsorted(cum_n, ks, side="left")
            pct_dias = np.empty(101, dtype=np.float64)
            pct_dias[0] = 0.0
            for i in range(1, 101):
                k = ks[i]
                if k == 0:
                    pct_dias[i] = 0.0
                else:
                    j = idx[i]
                    prev_n = cum_n[j - 1] if j > 0 else 0
                    prev_s = cum_s[j - 1] if j > 0 else 0.0
                    pct_dias[i] = (prev_s + (k - prev_n) * vals[j]) / total * 100.0
            return pd.DataFrame({"pct_egresos": p, "pct_dias": pct_dias})
    d = np.sort(col.astype(float))[::-1]
    if d.sum() == 0:
        return pd.DataFrame({"pct_egresos": p, "pct_dias": np.nan})
    acum = np.concatenate([[0.0], np.cumsum(d)]) / d.sum() * 100
    k = np.round(p / 100 * len(d)).astype(int)
    return pd.DataFrame({"pct_egresos": p, "pct_dias": acum[k]})


def cajas(df: pd.DataFrame, por: str, y: str) -> pd.DataFrame:
    """Cinco números por grupo; bigotes a 1,5 RIC recortados al dato; orden por mediana."""
    filas = []
    for g, s in df.groupby(por, observed=True)[y]:
        q1, med, q3 = s.quantile([0.25, 0.5, 0.75])
        ric = q3 - q1
        dentro = s[(s >= q1 - 1.5 * ric) & (s <= q3 + 1.5 * ric)]
        filas.append({"grupo": g, "n": int(len(s)), "q1": q1, "mediana": med,
                      "q3": q3, "min": dentro.min(), "max": dentro.max()})
    cols = ["grupo", "n", "q1", "mediana", "q3", "min", "max"]
    return pd.DataFrame(filas, columns=cols).sort_values("mediana").reset_index(drop=True)


def histograma(df: pd.DataFrame, y: str, tope: float | None) -> pd.DataFrame:
    """Conteos por intervalo (40); con tope se descartan valores mayores a él."""
    v = df[y].dropna().to_numpy(dtype=float)
    if tope is not None:
        v = v[v <= tope]
    if len(v) == 0:
        return pd.DataFrame(columns=["inicio", "fin", "n"])
    n, bordes = np.histogram(v, bins=40)
    return pd.DataFrame({"inicio": bordes[:-1], "fin": bordes[1:], "n": n})
