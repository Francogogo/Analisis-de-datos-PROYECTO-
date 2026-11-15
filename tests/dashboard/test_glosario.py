"""Glosario: ids, contenido, regex válidas, cobertura en las pestañas y vocabulario."""
import ast
import re
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[2] / "dashboard"
sys.path.insert(0, str(AQUI))

import glosario  # noqa: E402
from verificar import palabras_prohibidas  # noqa: E402

TERMINOS = glosario.TERMINOS
ID_RX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MATE_RX = re.compile(r"\$\$(.+?)\$\$|\$(.+?)\$", re.S)


def _cadenas_paginas() -> list[str]:
    """Todas las cadenas literales de dashboard/p_*.py, ya decodificadas (un solo backslash)."""
    cadenas = []
    for ruta in sorted(AQUI.glob("p_*.py")):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        cadenas += [n.value for n in ast.walk(arbol)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    return cadenas


CADENAS = _cadenas_paginas()
TEXTO_PAGINAS = "\n".join(CADENAS)
FORMULAS = [a or b for s in CADENAS for a, b in MATE_RX.findall(s)]


def _texto_termino(t: dict) -> str:
    partes = [t["nombre"], t["corto"]]
    for sub, txt in t["largo"]:
        partes += [sub, txt]
    return "\n".join(partes)


@pytest.mark.parametrize("t", TERMINOS, ids=lambda t: t["id"])
def test_forma_del_termino(t):
    assert ID_RX.match(t["id"]), t["id"]
    assert t["nombre"].strip()
    assert t["corto"].strip()
    assert len(t["largo"]) >= 2
    for sub, txt in t["largo"]:
        assert sub.strip() and txt.strip()
    assert t.get("patrones") or t.get("tex"), "sin patrones ni tex"


def test_ids_unicos():
    ids = [t["id"] for t in TERMINOS]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("t", TERMINOS, ids=lambda t: t["id"])
def test_regex_compilan(t):
    for p in t.get("patrones", []):
        re.compile(p, re.IGNORECASE)
    for p in t.get("tex", []):
        re.compile(p)


@pytest.mark.parametrize("t", TERMINOS, ids=lambda t: t["id"])
def test_aparece_en_paginas(t):
    texto = [p for p in t.get("patrones", []) if re.search(p, TEXTO_PAGINAS, re.IGNORECASE)]
    formula = [p for p in t.get("tex", []) if any(re.search(p, f) for f in FORMULAS)]
    assert texto or formula, f"{t['id']} no calza en dashboard/p_*.py"


@pytest.mark.parametrize("t", TERMINOS, ids=lambda t: t["id"])
def test_sin_vocabulario_prohibido(t):
    assert palabras_prohibidas(_texto_termino(t)) == []


# Fórmulas sin tooltip del reporte de auditoría en navegador (LaTeX original).
# Excluidas: bloque \begin{aligned} largo; fragmento "\\" suelto; "favorable. El primer corte de" (texto sin math); "0{,}68" (número suelto, sin símbolo).
FORMULAS_AUDITORIA = [
    'H_0',
    'p',
    'F',
    '\\ln(\\text{días})',
    't',
    '\\eta^2_{\\text{parcial}}',
    '\\text{BIC}',
    'V',
    '\\rho_s = 0{,}250',
    '\\text{gl} = 1',
    'R^2_{\\text{aj.}}',
    'k',
    'H_{0b}',
    'H_{0c}',
    'H_{0d}',
    'g_1',
    'Q_1',
    '\\text{gl}',
    '\\text{edad}_c',
    '\\text{IC}_{95\\%}',
    'e^{\\hat{\\mu}}',
    '\\text{edad}',
    '\\text{edad}^2',
    'p < 0{,}001',
    'g_1 = 9{,}04',
    'W = 0{,}442',
    'W = 0{,}957',
    'p \\le 0{,}01',
    'V = 0{,}4287',
    '\\text{edad}_c^2',
    '\\eta^2',
    '\\Delta\\text{BIC}',
    '\\%\\Delta',
    'H_{0a}',
    'H_1',
    '\\rho_s',
    'U',
    '\\beta_j=0',
    '\\beta_j\\neq0',
    'r',
    '\\varepsilon^2',
    'P_{90} = 15',
    '\\ln',
    'n = 968.098',
    'Q_3 = 7',
    '\\ln(2) \\approx 0{,}69',
    '\\bar{x} = 1{,}25',
    'M_e = 1{,}10',
    'V = 0{,}251',
    'r = -0{,}374',
    '\\varepsilon^2 = 0{,}120',
    'D = 0{,}129',
    'V = 0{,}165',
    'r = -0{,}292',
    'A^2 = 13.546',
    'D = 0{,}328',
    'A^2 = 150.921',
    'V = 0{,}109',
    'V = 0{,}103',
    'r = 0{,}224',
    'Q_3',
    'V \\approx 0{,}43',
    'Q_4',
    '\\hat{y}_i',
    '\\bar{e} = 0',
    'F = 5.830',
    '\\beta',
    'p<0{,}001',
    'W',
    '\\rho_s=0',
    '\\rho_s\\neq0',
    'H',
    '\\chi^2',
    'D',
    'A^2',
    'H_{1a}',
    'H_{1b}',
    'H_{1c}',
    'H_{1d}',
    'p < 0{,}05',
    '\\alpha = 0{,}05',
    '\\beta_j',
    'L_s = Q_3 + 1{,}5\\,\\text{RIC}',
    'M_e',
    '\\bar{x} = 6{,}70',
    '\\ln(365) \\approx 5{,}90',
    'Q_1 = 2',
    'M_e = 2{,}0',
    'M_e = 3{,}00',
    '\\bar{x}',
    '\\ln(1) = 0',
    's = 12{,}79',
    'g_1 = 0{,}01',
    '\\ln(3) \\approx 1{,}10',
    'M_e = 3',
    'L_s = 14,5',
    '|\\rho_s|,\\; |r|,\\; V: \\quad 0{,}10\\;\\text{(pequeño)} \\;\\;\\big|\\;\\; 0{,}30\\;\\text{(mediano)} \\;\\;\\big|\\;\\; 0{,}50\\;\\text{(grande)}',
    'p = 0{,}0002',
    '1/\\sqrt{n}',
    '\\varepsilon^2: \\quad 0{,}01\\;\\text{(pequeño)} \\;\\;\\big|\\;\\; 0{,}06\\;\\text{(mediano)} \\;\\;\\big|\\;\\; 0{,}14\\;\\text{(grande)}',
    'V \\le 0{,}049',
    '\\rho_s = 0',
    '\\rho_s \\neq 0',
    'e^y',
    'U = 128.229.165.044{,}0',
    'r = 0{,}140',
    'U = 18.931.464.786{,}5',
    'r = 0{,}062',
    'U = 9.770.718.101{,}0',
    'r = -0{,}025',
    'U = 134.328.097.919{,}0',
    'U = 12.299.582.842{,}0',
    'U = 43.570.528.856{,}5',
    'H = 116.410{,}6',
    'H = 2.259{,}7',
    '\\varepsilon^2 = 0{,}002',
]


@pytest.mark.parametrize("formula", FORMULAS_AUDITORIA)
def test_formula_auditada_tiene_tex(formula):
    assert any(re.search(r, formula) for t in TERMINOS for r in t.get("tex", [])), formula
