import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "dashboard"))

import verificar  # noqa: E402


def test_vocabulario_detecta():
    assert "OR" in verificar.palabras_prohibidas("el OR fue 2")
    assert verificar.palabras_prohibidas("el valor fue 2, por prueba") == []
    assert verificar.palabras_prohibidas("el valor fue or") == []
    assert "test set" in verificar.palabras_prohibidas("el Test Set")
    assert verificar.palabras_prohibidas("test estadístico y prueba") == []
    assert "AUC" in verificar.palabras_prohibidas("la auc sube")


@pytest.mark.skipif(not (Path(__file__).parents[2] / "dashboard/COBERTURA.md").exists(), reason="cobertura local no versionada")
def test_cobertura_completa():
    sin, falta, _ = verificar.revisar_cobertura()
    assert sin == [] and falta == []
    assert len(verificar.captions()) == 25


def test_cobertura_detecta_falta():
    sin, falta, parcial = verificar.revisar_cobertura(["A b c d", "E f g h"], [("A b c d x", "falta"), ("Z", "parcial")], [])
    assert sin == ["E f g h"] and falta == ["A b c d x"] and parcial == ["Z"]


def test_sin_img_ni_vocabulario():
    assert verificar.imagenes_en_pestanas() == []
    assert verificar.revisar_vocabulario() == []


def test_imagenes_requieren_fila():
    assert len(verificar.imagenes_informe()) == 9
    sin, _, _ = verificar.revisar_cobertura([], [("figs/a.pdf", "cubierto")], ["figs/a.pdf", "figs/b.pdf"])
    assert sin == ["figs/b.pdf"]
    cobertura = Path(__file__).parents[2] / "dashboard/COBERTURA.md"
    if cobertura.exists():
        assert any("avance2_cramer.pdf" in f[0] for f in verificar.filas_cobertura())


def test_captionof_cuenta():
    assert "V de Cramér entre" in verificar.captions()
