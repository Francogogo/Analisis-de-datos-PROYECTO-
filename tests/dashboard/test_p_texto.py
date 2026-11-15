import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "dashboard"))

import p_conclusiones  # noqa: E402
import p_contexto  # noqa: E402

RAIZ = Path(__file__).parents[2]
CIFRAS = json.loads((RAIZ / "results" / "cifras_avance2_v8.json").read_text(encoding="utf-8"))
PROHIBIDAS = ["odds", "OR", "logística", "McFadden", "pseudo-R²", "AUC", "ROC", "MAE", "RMSE", "train", "test set",
              "entrenamiento", "predicción", "predictor", "machine learning", "sobreajuste"]


def _textos(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from _textos(v)
    else:
        for v in x:
            yield from _textos(v)


def test_hipotesis_presentes():
    h = str(p_contexto.pestana_ui("c"))
    for g in "abcd":
        assert f"$H_{{0{g}}}$" in h and f"$H_{{1{g}}}$" in h
    assert "$H_0$" in h and "$H_1$" in h
    for fila in p_contexto.TEXTOS["pruebas"]:
        for celda in fila:
            assert celda.replace("&", "&amp;").replace("<", "&lt;") in h or celda in h


def test_vocabulario():
    for mod in (p_contexto, p_conclusiones):
        for t in _textos(mod.TEXTOS):
            for p in PROHIBIDAS:
                patron = rf"\b{re.escape(p)}\b" if p in ("OR", "ROC", "AUC", "MAE") else re.escape(p)
                assert not re.search(patron, t, re.I if p not in ("OR", "ROC", "AUC", "MAE") else 0), (p, t)


def test_numeros_desde_cifras():
    v = p_contexto.valores(CIFRAS)
    assert v["pct_prol"] == "9,4" and v["pct_cama"] == "47,1" and v["n"] == "968.098"
    html = str(p_contexto._problema_html(CIFRAS))
    assert "47,1 %" in html and "[[" not in html
    assert "[[" not in str(p_contexto._datos_html(CIFRAS))


def test_concentracion_usa_cada_porcentaje_y_denominador():
    cifras = {**CIFRAS, "pct_prolongadas": 12.5, "pct_dias_cama": 63.4, "percentil_90_dias": 20}
    html = str(p_contexto._concentracion_html(cifras))
    assert 'width="12.5"' in html and 'width="63.4"' in html
    assert "12,5 %" in html and "63,4 %" in html and "más de 20 días" in html
    assert "total de egresos" in html and "total de días-cama" in html


def test_conclusiones_tablas():
    filas = p_conclusiones.filas_hipotesis(CIFRAS)
    assert len(filas) == 4
    assert "+70,0 %" in filas[2][1] and "$F=3.867$" in filas[0][1]
    assert "+0,89 %" in filas[1][1] and "0,074" in filas[0][3]
    assert "Rechaza" in filas[3][2] and "$F=7,49$" in filas[3][1] and "12,6" in filas[3][3]


def test_conclusiones_sin_marcas():
    h = str(p_conclusiones._cuerpo(CIFRAS))
    assert "[[" not in h and "+214,8 %" in h and "21,5 %" in h and "19,8 %" in h


def test_tablas_desplazables_accesibles():
    tablas = [
        p_contexto._tabla(p_contexto.TEXTOS["vars_cols"], p_contexto.TEXTOS["vars"],
                          p_contexto.TEXTOS["vars_titulo"], p_contexto.valores(CIFRAS)),
        p_contexto._tabla(p_contexto.TEXTOS["pruebas_cols"], p_contexto.TEXTOS["pruebas"],
                          p_contexto.TEXTOS["pruebas_titulo"]),
        p_conclusiones._tabla(p_conclusiones.TEXTOS["hip_cols"], p_conclusiones.filas_hipotesis(CIFRAS),
                              p_conclusiones.TEXTOS["resp_titulo"]),
    ]
    nombres = [p_contexto.TEXTOS["vars_titulo"], p_contexto.TEXTOS["pruebas_titulo"],
               p_conclusiones.TEXTOS["resp_titulo"]]
    for tabla, nombre in zip(tablas, nombres):
        html = str(tabla)
        assert 'tabindex="0"' in html and 'role="region"' in html and f'aria-label="{nombre}"' in html
