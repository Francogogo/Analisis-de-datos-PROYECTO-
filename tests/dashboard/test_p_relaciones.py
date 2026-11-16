import json
import re
from pathlib import Path

import pandas as pd
import pytest

import datos
import p_relaciones as pr

RAIZ = Path(__file__).resolve().parents[2]
PROHIBIDAS = ["odds", "OR", "logística", "McFadden", "pseudo-R²", "AUC", "ROC", "MAE", "RMSE", "train", "test set",
              "entrenamiento", "predicción", "predictor", "machine learning", "sobreajuste"]


@pytest.fixture(scope="module")
def d():
    cifras = json.loads((RAIZ / "results" / "cifras_avance2_v8.json").read_text(encoding="utf-8"))
    base = pd.read_parquet(RAIZ / "dashboard" / "datos_app" / "base.parquet").sample(6000, random_state=1)
    for c in base.columns[base.dtypes.astype(str).isin(["str", "object"])]:
        base[c] = base[c].astype("category")
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


def test_20_pruebas(d):
    ks = pr.claves(d.cifras)
    assert len(ks) == 20 and len(pr.opciones(d.cifras)) == 20
    for v, r in ks:
        f = dict(pr.ficha(d.cifras, v, r))
        assert len(f) == 7 and all(f.values())
        assert "nan" not in " ".join(f.values()).lower()
        assert str(pr.fig_prueba(d, v, r).to_json())


def test_prueba_ejemplo(d):
    p = pr.prueba(d.cifras, "edad", "días")
    assert p["prueba"] == "Spearman" and p["medida"] == "ρ" and p["efecto"] == 0.249696


def test_etiquetas_de_pruebas_conservan_valores(d):
    opciones = pr.opciones(d.cifras)
    assert set(opciones) == {f"{v}|{r}" for v, r in pr.claves(d.cifras)}
    assert opciones["edad|días"] == "Edad y días de estada"
    assert opciones["sexo|prolongada"] == "Sexo y estadía prolongada (más de 15 días)"
    assert opciones["edad|normalidad"] == "Normalidad de edad"


def test_p_cero(d):
    assert pr.fmt_p(0.0) == "< 0,001" and pr.fmt_p(0.0234) == "0,0234" and pr.fmt_p(float("nan")) == "—"
    assert dict(pr.ficha(d.cifras, "sexo", "días"))["Valor-$p$"] == "< 0,001"
    assert "&lt; 0,001" in str(pr.tabla_pruebas(d.cifras))


def test_magnitud():
    assert pr.magnitud("r", -0.374) == "mediano" and pr.magnitud("ε²", 0.12) == "mediano"
    assert pr.magnitud("V", 0.053) == "despreciable" and pr.magnitud("ρ", 0.25) == "pequeño"


def test_holm_y_cramer(d):
    assert "202 de los 210" in dict(pr.ficha(d.cifras, "capitulo", "días"))["Lectura"]
    m = pr.matriz_cramer(d.cifras)
    assert m.shape == (6, 6) and m.loc["Capítulo CIE-10", "Cirugía"] == 0.4287


def test_ui_y_acentos():
    h = str(pr.pestana_ui("x"))
    assert "Relaciones" in h and "$H_0$" in h and "<img" not in h


def test_componentes_y_defensa():
    h = str(pr.pestana_ui("x"))
    assert h.count("componente-abrir") == 2 and h.count("componente-detalle") == 3 and "componente--abierto" in h
    assert "¿Hay normalidad en los datos?" in h and "¿Por qué casi todo da" in h


def test_vocabulario():
    for t in _textos(pr.TEXTOS):
        for p in PROHIBIDAS:
            patron = rf"\b{re.escape(p)}\b" if p in ("OR", "ROC", "AUC", "MAE") else re.escape(p)
            assert not re.search(patron, t, 0 if p in ("OR", "ROC", "AUC", "MAE") else re.I), (p, t)


def test_tabla_20_pruebas(d):
    f = pr.filas_pruebas(d.cifras)
    assert len(f) == 20 and all(len(x) == 8 and all(x) for x in f)
    assert f[2][2] == "Spearman" and f[-1][4] == "15" and f[-1][5] == "< 0,001"
    assert "pruebas" in str(pr.pestana_ui("x"))


def test_qq_ln_dias(d):
    fig = pr.fig_normalidad(d.base, "edad")
    assert [a.text for a in fig.layout.annotations][1:] == ["Q-Q días", "Q-Q ln(días)", "Q-Q edad"]
    assert all(len(t.x) <= 5000 for t in fig.data[1:])


def test_contingencia_total_pct(d):
    h = str(pr.tabla_contingencia(d.cifras, "sexo"))
    assert "Total" in h and "% prolongadas" in h and "387.368" in h and "13,1 %" in h


def test_colores_prolongada_y_referencia(d):
    assert set(pr.fig_prueba(d, "sexo", "prolongada").data[0].marker.color) <= set(pr.graficos.CARGA)
    qq = pr.fig_normalidad(d.base, "edad")
    assert all(t.line.color == pr.graficos.REFERENCIA for t in qq.data if getattr(t, "mode", None) == "lines")
