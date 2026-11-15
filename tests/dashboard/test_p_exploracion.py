import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import p_exploracion as p

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


def _muestra():
    return pd.read_parquet(RAIZ / "dashboard" / "datos_app" / "base.parquet").sample(3000, random_state=1)


def test_siete_filtros():
    h = str(p.pestana_ui("x"))
    for k in ["region", "capitulo", "tramo_edad", "sexo", "establecimiento", "cirugia", "fallecido"]:
        assert f'id="x-{k}"' in h
    assert len(re.findall(r"<select", h)) == 7


def test_vocabulario():
    h = str(p.pestana_ui("x"))
    for t in list(_textos(p.TEXTOS)) + [h]:
        for w in PROHIBIDAS:
            if w in ("OR", "AUC", "ROC", "MAE", "RMSE"):
                assert not re.search(rf"\b{w}\b", t), w
            else:
                assert w.lower() not in t.lower(), w


def test_cajas_con_referencia_del_paper():
    c = p.cajas_valores(_muestra(), CIFRAS)
    assert [x[0] for x in c] == [p.TEXTOS[k] for k in ("caja_n", "caja_mediana", "caja_prol", "caja_cama")]
    assert c[0][1] == "3.000" and c[0][2] == "968.098"
    assert c[2][2] == "9,4 %" and c[3][2] == "47,1 %"


def test_cajas_sin_filas():
    c = p.cajas_valores(_muestra().iloc[0:0], CIFRAS)
    assert c[0][1] == "0" and c[1][1] == "—"


def test_tabla_desc_base():
    t = p.tabla_desc(_muestra(), CIFRAS)
    assert list(t.Variable.unique()) == ["Días de estada", "ln(días)", "Edad (años)"]
    assert t.shape == (15, 4) and t.columns[-1] == "base completa (paper)"
    assert p.tabla_desc(_muestra().iloc[0:0], CIFRAS).iloc[0, 2] == "—"
    html = str(p.tabla_desc_html(t))
    assert html.count("<tr>") == 7 and html.count('colspan="2"') == 3


def test_tabla_sin_filtro_calza_paper():
    base = pd.read_parquet(RAIZ / "dashboard" / "datos_app" / "base.parquet", columns=["dias_estada", "log_dias", "edad"])
    t = p.tabla_desc(base, CIFRAS)
    assert (t["Con el filtro"] == t["base completa (paper)"]).all()
    assert t.iloc[3, 2] == "9,04"


def test_asimetria():
    assert abs(p.asimetria(pd.Series([1, 2, 3]))) < 1e-12
    assert p.asimetria(pd.Series([1, 1, 1, 10])) > 0
    assert np.isnan(p.asimetria(pd.Series([2.0])))


def test_notas_depuracion():
    n = " ".join(p.notas_depuracion(CIFRAS))
    assert "99.978" in n and "397" in n and "7,29" in n and "59,74" in n and "14,5" in n
    assert "[[" not in n
