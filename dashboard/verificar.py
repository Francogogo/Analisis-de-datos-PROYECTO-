"""Verificaciones del dashboard: vocabulario, cobertura del informe, imagenes y cifras.

Uso: python dashboard/verificar.py  (sale con codigo 1 si hay alguna FALLA).
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))

PESTANAS = ["p_contexto", "p_exploracion", "p_relaciones", "p_diagnosticos", "p_modelos", "p_whatif", "p_conclusiones"]
PROHIBIDAS = ["odds", "OR", "logística", "McFadden", "pseudo-R²", "AUC", "ROC", "MAE", "RMSE", "train", "test set",
              "entrenamiento", "predicción", "predictor", "machine learning", "sobreajuste"]
SIGLAS_MAYUS = {"OR"}  # solo mayúsculas: "or" no es problema, pero "por" y "valor" nunca coinciden


def _patron(p: str) -> re.Pattern:
    base = r"(?<!\w)" + re.escape(p) + r"(?:e?s)?(?!\w)"
    return re.compile(base, 0 if p in SIGLAS_MAYUS else re.IGNORECASE)


PATRONES = {p: _patron(p) for p in PROHIBIDAS}


def palabras_prohibidas(texto: str) -> list[str]:
    return [p for p, rx in PATRONES.items() if rx.search(texto)]


def _cadenas(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from _cadenas(v)
    elif isinstance(x, (list, tuple, set)):
        for v in x:
            yield from _cadenas(v)


def revisar_vocabulario() -> list[str]:
    import importlib
    malas = []
    for nombre in PESTANAS:
        for t in _cadenas(importlib.import_module(nombre).TEXTOS):
            malas += [f"{nombre}: '{w}' en «{t[:50]}»" for w in palabras_prohibidas(t)]
    for md in AQUI.rglob("*.md"):
        malas += [f"{md.name}: '{w}'" for w in palabras_prohibidas(md.read_text(encoding="utf-8"))]
    return malas


def clave_caption(linea: str) -> str:
    """Primeras 4 palabras de un \\caption{...}, sin LaTeX: así se identifica su fila en COBERTURA.md."""
    return " ".join(re.sub(r"[\\${}]", "", linea).split()[:4])


def captions(tex: Path | None = None) -> list[str]:
    tex = tex or RAIZ / "paper" / "informe_v5.tex"
    return [clave_caption(m.group(1)) for m in re.finditer(r"\\caption(?:of\{\w+\})?\{(.*)", tex.read_text(encoding="utf-8"))]


def imagenes_informe(tex: Path | None = None) -> list[str]:
    """Rutas de cada \\includegraphics del informe (cada una necesita su fila en COBERTURA.md)."""
    tex = tex or RAIZ / "paper" / "informe_v5.tex"
    return re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", tex.read_text(encoding="utf-8"))


def filas_cobertura(md: Path | None = None) -> list[tuple[str, str]]:
    """(caption, estado) de cada fila de la tabla de COBERTURA.md."""
    md = md or AQUI / "COBERTURA.md"
    filas = []
    for ln in md.read_text(encoding="utf-8").splitlines():
        celdas = [c.strip() for c in ln.strip().strip("|").split("|")]
        est = re.match(r"(cubierto|parcial|falta)\b", celdas[-1])
        if ln.startswith("|") and len(celdas) == 5 and est:
            filas.append((celdas[0], est.group(1)))
    return filas


def revisar_cobertura(caps: list[str] | None = None, filas: list[tuple[str, str]] | None = None,
                      imgs: list[str] | None = None):
    """Devuelve (sin_fila, falta, parcial); sin_fila incluye captions e imágenes sin fila."""
    caps = captions() if caps is None else caps
    filas = filas_cobertura() if filas is None else filas
    imgs = imagenes_informe() if imgs is None else imgs
    sin = [c for c in caps if not any(f[0].startswith(c) for f in filas)]
    sin += [i for i in imgs if not any(i in f[0] for f in filas)]
    return (sin, [f[0] for f in filas if f[1] == "falta"], [f[0] for f in filas if f[1] == "parcial"])


def imagenes_en_pestanas() -> list[str]:
    return [n for n in PESTANAS if "<img" in (AQUI / f"{n}.py").read_text(encoding="utf-8")]


def revisar_cifras() -> list[str]:
    import datos
    import resumen
    d = datos.cargar()
    r, c, fallos = resumen.descriptivos(d.base), d.cifras, []
    if r["n"] != c["n"] or r["n"] != 968098:
        fallos.append(f"n = {r['n']}")
    if abs(r["pct_prolongadas"] - c["pct_prolongadas"]) > 0.01:
        fallos.append(f"% prolongadas {r['pct_prolongadas']:.3f} vs {c['pct_prolongadas']:.3f}")
    if abs(r["pct_dias_cama_prolongadas"] - c["pct_dias_cama"]) > 0.01:
        fallos.append(f"% días-cama {r['pct_dias_cama_prolongadas']:.3f} vs {c['pct_dias_cama']:.3f}")
    return fallos


def main() -> int:
    n_falla = 0

    def linea(estado, texto):
        nonlocal n_falla
        n_falla += estado == "FALLA"
        print(f"{estado}: {texto}")

    malas = revisar_vocabulario()
    linea("FALLA" if malas else "OK", "vocabulario prohibido" + "".join(f"\n    {m}" for m in malas))
    sin, falta, parcial = revisar_cobertura()
    linea("FALLA" if sin else "OK", f"cada caption e imagen del informe tiene fila en COBERTURA.md ({len(captions())} captions, {len(imagenes_informe())} imágenes)"
          + "".join(f"\n    sin fila: {s}" for s in sin))
    linea("FALLA" if falta else "OK", "ninguna fila 'falta'" + "".join(f"\n    falta: {s}" for s in falta))
    linea("AVISO" if parcial else "OK", f"filas 'parcial': {len(parcial)}" + "".join(f"\n    parcial: {s}" for s in parcial))
    img = imagenes_en_pestanas()
    linea("FALLA" if img else "OK", "sin <img en las pestañas" + (f": {img}" if img else ""))
    f = revisar_cifras()
    linea("FALLA" if f else "OK", "cifras sin filtro coinciden con cifras.json" + (f": {f}" if f else ""))
    return 1 if n_falla else 0


if __name__ == "__main__":
    sys.exit(main())
