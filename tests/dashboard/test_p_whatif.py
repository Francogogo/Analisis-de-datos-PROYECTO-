import json
import re
from pathlib import Path

import numpy as np
import pytest

import p_whatif

RAIZ = Path(__file__).parents[2]
C = json.loads((RAIZ / "results" / "cifras_avance2_v8.json").read_text(encoding="utf-8"))
PROHIBIDAS = ["odds", "OR", "logística", "McFadden", "pseudo-R²", "AUC", "ROC", "MAE", "RMSE", "train", "test set",
              "entrenamiento", "predicción", "predictor", "machine learning", "sobreajuste"]
NIVELES = {"capitulo": ["K00-K93", "A00-B99"], "region": ["Metropolitana de Santiago", "Norte"],
           "sexo": ["MUJER", "HOMBRE"], "establecimiento": ["No SNSS", "SNSS"],
           "cirugia": ["No", "Sí"], "fallecido": ["No", "Sí"]}


@pytest.fixture
def m3():
    nombres = ["Intercept", "capitulo: A00-B99", "cirugia: Sí", "fallecido: Sí", "sexo: HOMBRE",
               "establecimiento: SNSS", "region: Norte", "edad_c", "I(edad_c ** 2)"]
    beta = [0.6, 0.64, 0.3, 0.1, -0.05, 0.4, 0.02, 0.01, 0.0002]
    return {"nombres": nombres, "beta": beta, "cov": (np.eye(9) * 1e-5).tolist(), "edad_prom": 45.0,
            "sigma2": 0.86, "gl_resid": 1000, "r2_aj": 0.198, "niveles": NIVELES}


def _textos(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from _textos(v)
    else:
        for v in x:
            yield from _textos(v)


def test_entradas():
    h = str(p_whatif.pestana_ui("w"))
    assert h.count("<select") == 7  # seis del perfil y el selector de variable del gráfico
    for f in NIVELES:
        assert f'id="w-{f}"' in h
    m = re.search(r'<input[^>]*id="w-edad"[^>]*>', h).group(0)
    assert 'data-min="0"' in m and 'data-max="92"' in m and "<img" not in h


def test_r2_visible(m3):
    h = str(p_whatif.resultado_html(p_whatif.perfil_ref(m3), m3, C))
    assert "0,198" in h and "[[" not in h
    assert "asociación ajustada" in p_whatif.TEXTOS["intro"] and "individual" in p_whatif.TEXTOS["intro"]


def test_vocabulario():
    for t in _textos(p_whatif.TEXTOS):
        for p in PROHIBIDAS:
            ci = p not in ("OR", "ROC", "AUC", "MAE")
            patron = re.escape(p) if ci else rf"\b{p}\b"
            assert not re.search(patron, t, re.I if ci else 0), (p, t)


def test_perfil_y_cambio(m3):
    ref = p_whatif.perfil_ref(m3)
    assert ref == {**{f: n[0] for f, n in NIVELES.items()}, "edad": 45}
    v = p_whatif.textos_resultado(ref, m3)
    assert v["cambio"] == "0,0" and v["dias"] == v["ref"]
    v2 = p_whatif.textos_resultado({**ref, "establecimiento": "SNSS"}, m3)
    assert v2["cambio"] == "+" + p_whatif.graficos.num((np.exp(0.4) - 1) * 100, 1)
    assert p_whatif.cambio_pct(2.0, 1.0) == 100.0


def test_figuras(m3):
    p = {**p_whatif.perfil_ref(m3), "edad": 70}
    f = p_whatif.fig_edad(p, m3)
    assert f.data[-1].x[0] == 70 and len(f.data[2].x) == 93
    n = p_whatif.fig_niveles(p, "sexo", m3)
    assert [y for t in n.data for y in t.y] == ["MUJER", "HOMBRE"]
