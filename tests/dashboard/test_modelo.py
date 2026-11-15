import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "dashboard"))

import modelo  # noqa: E402

M3 = {
    "nombres": ["Intercept", "establecimiento: SNSS", "edad_c", "I(edad_c ** 2)"],
    "beta": [0.6, 0.53, 0.009, 0.00001],
    "cov": np.diag([1e-4, 4e-4, 1e-8, 1e-14]).tolist(),
    "edad_prom": 45.0,
    "sigma2": 0.86,
    "gl_resid": 1000,
    "niveles": {"establecimiento": ["No SNSS", "SNSS"]},
}
PERFIL = {"establecimiento": "No SNSS", "edad": 45.0}


def test_referencia_es_exp_intercepto():
    dias, _, _ = modelo.dias_estimados(PERFIL, M3)
    assert dias == pytest.approx(math.exp(0.6))


def test_snss_sube_70():
    base, _, _ = modelo.dias_estimados(PERFIL, M3)
    snss, _, _ = modelo.dias_estimados({**PERFIL, "establecimiento": "SNSS"}, M3)
    assert snss / base == pytest.approx(math.exp(0.53))


def test_nivel_desconocido():
    with pytest.raises(ValueError, match="Marte"):
        modelo.fila({**PERFIL, "establecimiento": "Marte"}, M3)


def test_ic_contiene():
    p = {**PERFIL, "establecimiento": "SNSS", "edad": 60.0}
    dias, inf, sup = modelo.dias_estimados(p, M3)
    x = modelo.fila(p, M3)
    ee = math.sqrt(x @ np.array(M3["cov"]) @ x)
    eta = x @ np.array(M3["beta"])
    assert inf < dias < sup
    assert inf == pytest.approx(math.exp(eta - 1.96 * ee))
    assert sup == pytest.approx(math.exp(eta + 1.96 * ee))


def test_edad_cuadratica():
    x = modelo.fila({**PERFIL, "edad": 50.0}, M3)
    assert x[-2] == pytest.approx(5.0) and x[-1] == pytest.approx(25.0)


def test_curvas():
    c = modelo.curva(PERFIL, "edad", M3)
    assert list(c.columns) == ["valor", "dias", "inf", "sup"] and len(c) == 93
    assert c.valor.iloc[0] == 0 and c.valor.iloc[-1] == 92
    s = modelo.curva(PERFIL, "establecimiento", M3)
    assert list(s.valor) == ["No SNSS", "SNSS"]
    assert (s.inf < s.dias).all() and (s.dias < s.sup).all()
