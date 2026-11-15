"""Pruebas de rendimiento, caché de arranque, preload y activos locales (Blender/SVG/JS)."""
from statistics import NormalDist
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).parents[2]
sys.path.insert(0, str(RAIZ / "dashboard"))

import app  # noqa: E402
import cache  # noqa: E402
import datos  # noqa: E402
import p_diagnosticos  # noqa: E402
import p_exploracion  # noqa: E402
import resumen  # noqa: E402


def test_concentracion_rapida_exacta():
    rng = np.random.default_rng(42)
    df = pd.DataFrame({"dias_estada": rng.integers(1, 366, size=2500, dtype=np.int16)})
    rapida = resumen.concentracion(df)
    d = np.sort(df["dias_estada"].to_numpy(dtype=float))[::-1]
    acum = np.concatenate([[0.0], np.cumsum(d)]) / d.sum() * 100
    k = np.round(np.arange(101) / 100 * len(d)).astype(int)
    assert np.allclose(rapida["pct_dias"].to_numpy(), acum[k], atol=1e-10)


def test_cuantiles_normales_vectorizados():
    n = 200
    nd = NormalDist()
    esperado = np.array([nd.inv_cdf((i + 0.5) / n) for i in range(n)])
    assert np.allclose(datos.cuantiles_normales(n), esperado, atol=1e-9)


def test_cache_coincide_con_calculo_directo():
    d = datos.cargar()
    pre_e = cache.exploracion_base(d)
    assert pre_e["cajas"] == p_exploracion.cajas_valores(d.base, d.cifras)
    pre_d = cache.diagnosticos_base(d)
    assert len(pre_d["muestra"]) == p_diagnosticos.MAX_PUNTOS
    assert len(pre_d["ventiles"]) == 20


def test_preload_y_activos_locales():
    from starlette.testclient import TestClient

    html = str(app.app_ui)
    assert 'rel="preload"' in html and 'hero-3d-poster.webp' in html
    assert 'hero-3d-img' in html and 'hero-3d-poster.webp' in html
    assert 'hero-3d-canvas' not in html and 'hero-3d-toggle' not in html
    assert 'fetchpriority="high"' in html and 'fetchpriority="low"' in html
    assert 'atlas-engine.js' in html

    c = TestClient(app.app)
    html_http = c.get("/").text
    assert 'favicon.svg' in html_http and 'rel="icon"' in html_http
    for ruta in (
        "/assets/hero-3d-poster.webp",
        "/assets/favicon.svg",
        "/js/atlas-engine.js",
    ):
        r = c.get(ruta)
        assert r.status_code == 200 and len(r.content) > 100


def test_graficos_sin_widgets_y_plotly_js_de_la_misma_version():
    """Los gráficos viajan como JSON (no como widgets que cargaban plotly.js por gráfico) y el
    plotly.js servido es la misma versión que trae plotly.py, porque el JSON usa arreglos base64."""
    import asyncio
    import json
    import re

    import plotly

    import graficos

    for f in (RAIZ / "dashboard").glob("*.py"):
        assert not re.search(r"^\s*(from|import) shinywidgets", f.read_text(encoding="utf-8"), re.M), f.name
    fig = graficos.dispersion(pd.DataFrame({"x": np.arange(50.0), "y": np.arange(50.0)}), "x", "y")
    js = json.loads(asyncio.run(graficos.render_plotly().transform(fig)))
    assert js["data"][0]["x"]["dtype"] == "f4" and js["layout"]["separators"] == ",."

    version = re.compile(rb"plotly\.js(?: \(cartesian - minified\))? v(\d+\.\d+\.\d+)")
    servido = (RAIZ / "dashboard/www/plotly/plotly-cartesian.min.js").read_bytes()[:200]
    propio = (Path(plotly.__file__).parent / "package_data/plotly.min.js").read_bytes()[:200]
    assert version.search(servido).group(1) == version.search(propio).group(1)


def test_compresion_y_cache_inmutable():
    from starlette.testclient import TestClient

    c = TestClient(app.app)
    html = c.get("/", headers={"Accept-Encoding": "gzip"})
    assert html.headers.get("content-encoding") == "gzip"
    assert "immutable" not in html.headers.get("cache-control", "")
    ruta = app.estatico("plotly/plotly-cartesian.min.js")
    assert ruta in html.text and app.estatico("js/graficos.js") in html.text
    r = c.get("/" + ruta, headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200 and r.headers["content-encoding"] == "gzip"
    assert "immutable" in r.headers["cache-control"]
    assert "immutable" not in c.get("/assets/favicon.svg").headers.get("cache-control", "")
