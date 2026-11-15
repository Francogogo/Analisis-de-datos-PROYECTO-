import json
import re
from pathlib import Path

import pandas as pd
import pytest

import datos
import p_diagnosticos as pd_

RAIZ = Path(__file__).resolve().parents[2]
PROHIBIDAS = ["odds", "OR", "logística", "McFadden", "pseudo-R²", "AUC", "ROC", "MAE", "RMSE", "train", "test set",
              "entrenamiento", "predicción", "predictor", "machine learning", "sobreajuste"]


@pytest.fixture(scope="module")
def d():
    cifras = json.loads((RAIZ / "results" / "cifras_avance2_v8.json").read_text(encoding="utf-8"))
    base = pd.read_parquet(RAIZ / "dashboard" / "datos_app" / "base.parquet").sample(3000, random_state=1)
    return datos.Datos(base=base, cifras=cifras, m3={})


def _textos(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from _textos(v)
    else:
        for v in x:
            yield from _textos(v)


def test_muestra_20000(d):
    grande = pd.DataFrame({"ajuste_ln": range(50000), "residuo": range(50000)})
    assert len(pd_.muestra(grande)) == 20000 and len(pd_.muestra(d.base)) == 3000
    for fig in (pd_.fig_residuos(grande), pd_.fig_qq(grande)):
        assert max(len(t.x) for t in fig.data) <= 20000


def test_figuras(d):
    for f in (pd_.fig_histograma(d.base), pd_.fig_edad(d.cifras), pd_.fig_deciles(d.cifras), pd_.fig_sd(d.cifras)):
        assert f.to_json()
    assert len(pd_.ventiles(d.base)) == 20
    assert len(pd_.tabla_deciles(d.cifras)) == 10 and len(pd_.tabla_edad(d.cifras)) == 11


def test_observada_y_ajustada_conservan_color(d):
    for fig in (pd_.fig_edad(d.cifras), pd_.fig_deciles(d.cifras)):
        assert {t.name: t.line.color for t in fig.data} == {
            "Observada": pd_.graficos.ACENTO, "Ajustada": pd_.graficos.REFERENCIA,
        }
        observada, ajustada = fig.data
        assert observada.line.dash != "dash" and ajustada.line.dash == "dash"
        assert observada.mode == ajustada.mode == "lines+markers"


def test_textos_con_cifras(d):
    v = pd_.valores(d)
    assert v["vif"] == "2,36" and v["asim"] == "0,492" and v["aj10"] == "8,05" and v["ob7"] == "4,56"
    for k in ("resid_texto", "hist_texto", "decil_texto", "vif", "hc3", "intro"):
        t = pd_.llenar(pd_.TEXTOS[k], v)
        assert "[[" not in t and not re.search(r"\bnan\b", t.lower())
    assert "F00-F99" in pd_.llenar(pd_.TEXTOS["hc3"], v)


def test_ui():
    h = str(pd_.pestana_ui("x"))
    assert "Diagnósticos" in h and "<img" not in h


def test_vocabulario():
    for t in _textos(pd_.TEXTOS):
        for p in PROHIBIDAS:
            patron = rf"\b{re.escape(p)}\b" if p in ("OR", "ROC", "AUC", "MAE") else re.escape(p)
            assert not re.search(patron, t, 0 if p in ("OR", "ROC", "AUC", "MAE") else re.I), (p, t)


def test_tabla_edad_visible(d):
    h = str(pd_.html_edad(d.cifras, d.base))
    assert "Media geométrica" in h and "menor de un año" in h and "90 y más" in h
    assert "4,35" in h and "3,79" in h   # exp(1,47) y exp(1,33), anexo del informe
