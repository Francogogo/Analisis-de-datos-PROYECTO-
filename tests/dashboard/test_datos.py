import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dashboard"))
import datos  # noqa: E402


@pytest.fixture(scope="module")
def d():
    datos.cargar.cache_clear()
    return datos.cargar()


def test_beta_calza_paper(d):
    assert len(d.m3["nombres"]) == 42
    for n, b in zip(d.m3["nombres"], d.m3["beta"]):
        assert round(b, 6) == d.cifras["coef"][n]["β"]


def test_ee_calza(d):
    ee = np.sqrt(np.diag(np.array(d.m3["cov"])))
    for n, e in zip(d.m3["nombres"], ee):
        assert abs(e - d.cifras["coef"][n]["EE"]) < 1e-6


def test_r2(d):
    assert abs(d.m3["r2_aj"] - 0.197986) < 1e-6
    assert d.m3["gl_resid"] == 968098 - 42


def test_base_n(d):
    assert len(d.base) == 968098 == d.cifras["n"]
    assert list(d.base.columns)[:2] == ["dias_estada", "log_dias"] and d.base.shape[1] == 15
    for c in ["capitulo", "region", "sexo", "establecimiento", "cirugia", "fallecido"]:
        assert str(d.base[c].dtype) == "category"
    assert d.base.memory_usage(deep=True).sum() < 40e6


def test_niveles_referencia_primero(d):
    n = d.m3["niveles"]
    assert {f: l[0] for f, l in n.items()} == datos.REFS
    assert "De Ñuble" in n["region"]
    assert set(n["region"]) == set(d.base["region"].astype(str).unique())


def test_cargar_cacheado(d):
    assert datos.cargar() is d
