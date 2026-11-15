import json
import re
from pathlib import Path

import p_modelos

RAIZ = Path(__file__).parents[2]
C = json.loads((RAIZ / "results" / "cifras_avance2_v8.json").read_text(encoding="utf-8"))
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


def test_ranking_orden():
    r = p_modelos.ranking(C)
    assert list(r["eta2"]) == sorted(r["eta2"], reverse=True)
    assert list(r["factor"][:3]) == ["capítulo", "establecimiento", "edad (edad y edad²)"]
    assert r["F"].iloc[0] == C["ftest"]["capitulo"]["F"]
    fig = p_modelos.fig_ranking(C)
    assert list(fig.data[0].x) == list(r["eta2"])
    assert fig.layout.shapes[0].x0 == 0.01
    assert p_modelos.filas_ranking(C)[0][:3] == ["1", "Capítulo", "0,0740"]


def test_vocabulario():
    for t in _textos(p_modelos.TEXTOS):
        for p in PROHIBIDAS:
            ci = p not in ("OR", "ROC", "AUC", "MAE")
            patron = re.escape(p) if ci else rf"\b{p}\b"
            assert not re.search(patron, t, re.I if ci else 0), (p, t)


def test_coeficientes_hc3_y_filtro():
    todos = p_modelos.coeficientes(C)
    assert len(todos) == 41 and "Intercept" not in set(todos["variable"])
    h = p_modelos.coeficientes(C, hc3=True, factor="sexo")
    assert list(h["variable"]) == ["sexo: HOMBRE"]
    v = C["coef"]["sexo: HOMBRE"]
    assert h["inf"].iloc[0] == v["%Δ HC3 inf"] and h["sup"].iloc[0] == v["%Δ HC3 sup"]
    assert p_modelos.coeficientes(C, factor="sexo")["inf"].iloc[0] == v["%Δ inf"]
    assert set(p_modelos.coeficientes(C, factor="edad")["variable"]) == {"edad_c", "I(edad_c ** 2)"}
    assert len(p_modelos.coeficientes(C, factor="capitulo")) == 20
    f = p_modelos.fig_forest(h)
    assert f.layout.shapes[0].x0 == 0


def test_tablas_y_metrica():
    assert p_modelos.filas_modelos(C)[3][:4] == ["M3", "42", "0,1980", "0,1980"]
    assert p_modelos.filas_modelos(C)[3][4] == "2.601.099"
    assert p_modelos.filas_modelos(C)[0][5] == "—"
    assert p_modelos.filas_anova(C)[0][5] == "<0,001"
    assert len(p_modelos.filas_espec(C)) == 4 and len(p_modelos.filas_forward(C)) == 8
    assert len(p_modelos.filas_sens(C)) == 2 and len(p_modelos.filas_bloques(C)) == 4
    assert list(p_modelos.metrica_modelos(C, "BIC")["valor"])[3] == C["modelos"]["M3"]["BIC"]
    assert p_modelos.fig_metrica(C, "R² aj.").data[0].y[3] == C["modelos"]["M3"]["R² aj."]


def test_ui():
    h = str(p_modelos.pestana_ui("m"))
    for i in ("metrica", "se", "factor", "graf_ranking", "graf_forest"):
        assert f"m-{i}" in h
    assert "<img" not in h and "[[" not in str(p_modelos.TEXTOS["espec"].replace("[[menor_bic]]", ""))


def test_tablas_desplazables_con_nombre():
    html = str(p_modelos.pestana_ui("m"))
    for id_, titulo in (
        ("tabla_modelos", "anidados_titulo"), ("tabla_anova", "anova_titulo"),
        ("tabla_bloques", "bloques_titulo"), ("tabla_ranking", "ranking_titulo"),
        ("tabla_coef", "coef_titulo"), ("tabla_espec", "espec_titulo"),
        ("tabla_sens", "sens_titulo"), ("tabla_forward", "fwd_titulo"),
    ):
        region = html.split(f'aria-label="{p_modelos.TEXTOS[titulo]}"', 1)[1].split("</div>", 1)[0]
        assert f'id="m-{id_}"' in region
        assert f'role="region" tabindex="0" aria-label="{p_modelos.TEXTOS[titulo]}"' in html
