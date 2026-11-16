"""Genera las tablas largas de los anexos del informe a partir de results/cifras_avance2_v8.json.

Uso, desde la raíz del repositorio: python3 paper/gen_anexos.py
Escribe fragmentos LaTeX en paper/anexos/ que informe.tex incluye con \\input.
Ninguna cifra de los anexos se escribe a mano.
"""
import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
d = json.loads((RAIZ / "results/cifras_avance2_v8.json").read_text(), parse_constant=lambda c: float(c))
SALIDA = RAIZ / "paper/anexos"
SALIDA.mkdir(exist_ok=True)


def num(x, dec=2, signo=False):
    """Número con coma decimal y punto de miles, en modo matemático si es negativo."""
    s = f"{abs(x):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    s = s.replace(",", "{,}")
    if x < 0 and float(f"{abs(x):.{dec}f}") != 0:
        return f"$-{s}$"
    if signo and x > 0:
        return f"$+{s}$"
    return f"${s}$" if "{,}" in s else s


def cient(x, dec=2):
    """Notación científica para coeficientes muy chicos."""
    e = math.floor(math.log10(abs(x)))
    m = x / 10**e
    ms = f"{m:.{dec}f}".replace(".", "{,}")
    return f"${ms}\\times10^{{{e}}}$"


def pval(p):
    return "$<0{,}001$" if p < 0.001 else num(p, 4)


def esc(s):
    return s.replace("&", "\\&").replace("_", "\\_")


CAPS = {
    "A00-B99": "infecciosas", "C00-D48": "tumores", "D50-D89": "sangre", "E00-E90": "endocrinas",
    "F00-F99": "mentales", "G00-G99": "nervioso", "H00-H59": "ojo", "H60-H95": "oído",
    "I00-I99": "circulatorio", "J00-J99": "respiratorio", "K00-K93": "digestivo", "L00-L99": "piel", "M00-M99": "osteomuscular",
    "N00-N99": "genitourinario", "O00-O99": "embarazo y parto", "P00-P96": "perinatal",
    "Q00-Q99": "congénitas", "R00-R99": "síntomas", "S00-T98": "traumatismos",
    "U00-U99": "uso especial", "Z00-Z99": "factores de contacto",
}


def rotulo(k):
    if k == "Intercept":
        return "Intercepto"
    var, _, nivel = k.partition(": ")
    if var == "capitulo":
        return f"Capítulo {nivel.replace('-', '--')} ({CAPS[nivel]})"
    if var == "region":
        for pre in ("De ", "Del "):
            if nivel.startswith(pre):
                nivel = nivel[len(pre):]
        corto = {"Aisén del Gral. C. Ibáñez del Campo": "Aisén", "Magallanes y de La Antártica Chilena": "Magallanes",
                 "Libertador B. O'Higgins": "O'Higgins"}
        return f"Región: {esc(corto.get(nivel, nivel))}"
    if var == "tramo_edad":
        return f"Edad: {nivel} años" if "año" not in nivel else f"Edad: {nivel}"
    return {"cirugia: Sí": "Cirugía", "fallecido: Sí": "Condición de egreso: fallecido",
            "sexo: HOMBRE": "Sexo: hombre", "establecimiento: SNSS": "Establecimiento: SNSS",
            "edad_c": "Edad centrada (por año)", "I(edad_c ** 2)": "Edad centrada al cuadrado"}[k]


# ---------- Anexo A: las 20 pruebas de a pares
NOMBRE = {"edad": "Edad", "sexo": "Sexo", "nacionalidad": "Nacionalidad", "etnia": "Etnia",
          "cirugia": "Cirugía", "fallecido": "Condición de egreso", "establecimiento": "Establecimiento",
          "capitulo": "Capítulo \\cie", "region": "Región", "tramo_edad": "Tramo de edad"}
H = {
    "Spearman": ("$\\rho_s=0$", "$\\rho_s\\neq0$"),
    "Mann-Whitney U": ("misma distribución de días en ambos grupos", "un grupo tiende a más días"),
    "Kruskal-Wallis": ("misma distribución de días en todos los grupos", "al menos un grupo difiere"),
    "Chi-cuadrado": ("la variable y la estadía prolongada son independientes", "no son independientes"),
}
MEDIDA = {"ρ": "\\rho", "r": "r", "ε²": "\\varepsilon^2", "V": "V"}


def cohen(medida, e):
    e = abs(e)
    if medida in ("ε²",):
        cortes = (0.01, 0.06, 0.14)
    else:
        cortes = (0.1, 0.3, 0.5)
    if e < cortes[0]:
        return "despreciable"
    if e < cortes[1]:
        return "pequeño"
    if e < cortes[2]:
        return "mediano"
    return "grande"


pruebas = []                                   # una entrada por prueba: (tipo, variable, respuesta, estadístico, valor-p, efecto)
nrm = d["normalidad"]
for var, nom in (("dias_estada", "Días de estada"), ("edad", "Edad")):
    n = nrm[var]
    pruebas.append(("Normalidad", nom, "---",
                    f"$W={num(n['Shapiro-Wilk W'], 3).strip('$')}$; $D={num(n['Lilliefors D'], 3).strip('$')}$; "
                    f"$A^2={num(n['Anderson-Darling A²'], 0).strip('$')}$",
                    "SW y KS $<0{,}001$; AD $0{,}01$", "---"))
for p in d["pares"]:
    est = p["estadístico"]
    if p["prueba"] == "Spearman":
        e_txt = f"$\\rho_s={num(est, 3).strip('$')}$"
    elif p["prueba"] == "Mann-Whitney U":
        e_txt = f"$U={num(est / 1e9, 2).strip('$')}\\times10^{{9}}$"
    elif p["prueba"] == "Kruskal-Wallis":
        gl = {"capitulo": 20, "region": 15}[p["variable"]]
        e_txt = f"$H={num(est, 1).strip('$')}$ ({gl} gl)"
    else:
        e_txt = f"$\\chi^2={num(est, 1).strip('$')}$ ({int(p['gl'])} gl)"
    m = p["medida"]
    pruebas.append((p["prueba"], NOMBRE[p["variable"]], "Días" if p["respuesta"] == "días" else "Prolongada", e_txt,
                    pval(p["valor-p"]), f"${MEDIDA[m]}={num(p['efecto'], 3).strip('$')}$, {cohen(m, p['efecto'])}"))
assert len(pruebas) == d["n_pruebas_pares"] == 20

# informe.tex (página horizontal): una fila por prueba con sus hipótesis
H["Normalidad"] = ("la variable es normal", "no es normal")
PRUEBA = {"Normalidad": "Shapiro--Wilk, Lilliefors, Anderson--Darling"}
filas = []
for k, (tipo, var, resp, e_txt, pv, ef) in enumerate(pruebas, 1):
    h0, h1 = H[tipo]
    resp = "Normalidad" if tipo == "Normalidad" else resp
    filas.append(f"{k} & {var} & {resp} & {PRUEBA.get(tipo, tipo.replace('-', '--'))} & {h0} & {h1} & {e_txt} & {pv} & "
                 f"Se rechaza & {ef} \\\\")
(SALIDA / "pares.tex").write_text("\n".join(filas) + "\n")

# informe_v2.tex (página vertical): las hipótesis van una vez, en la fila de título de cada tipo de prueba
filas, actual = [], None
for k, (tipo, var, resp, e_txt, pv, ef) in enumerate(pruebas, 1):
    if tipo != actual:
        actual = tipo
        h0, h1 = H[tipo]
        nombre = PRUEBA.get(tipo, tipo.replace("-", "--"))
        filas.append(f"\\multicolumn{{7}}{{>{{\\raggedright\\arraybackslash}}p{{\\dimexpr\\linewidth-2\\tabcolsep}}}}"
                     f"{{\\cellcolor{{white}}\\textbf{{{nombre}.}} $H_0$: {h0}. $H_1$: {h1}.}} \\\\")
    filas.append(f"{k} & {var} & {resp} & {e_txt.replace(' gl)', '~gl)')} & {pv} & Se rechaza & {ef} \\\\")
(SALIDA / "pares_vertical.tex").write_text("\n".join(filas) + "\n")
# informe_v3.tex: igual que la vertical, pero Anderson-Darling se informa como p <= 0,01 (scipy no da valores menores)
(SALIDA / "pares_v3.tex").write_text("\n".join(filas).replace("AD $0{,}01$", "AD $\\le0{,}01$") + "\n")

# ---------- Anexo B: coeficientes completos de M3
filas = []
for k, c in d["coef"].items():
    if k.startswith("edad_c") or k.startswith("I(edad_c"):
        b, ee, hc = cient(c["β"]), cient(c["EE"], 1), cient(c["EE HC3"], 1)
        pc = num(c["%Δ"], 3, True) if c["%Δ"] > 0.01 else cient(c["%Δ"])
        ic = (f"{num(c['%Δ inf'], 3)} a {num(c['%Δ sup'], 3)}" if c["%Δ"] > 0.01
              else f"{cient(c['%Δ inf'])} a {cient(c['%Δ sup'])}")
    else:
        b, ee, hc = num(c["β"], 3), num(c["EE"], 4), num(c["EE HC3"], 4)
        pc = num(c["%Δ"], 1, True)
        ic = f"{num(c['%Δ inf'], 1)} a {num(c['%Δ sup'], 1)}"
    if k in ("Intercept", "I(edad_c ** 2)"):
        pc, ic = "---", "---"
    filas.append(f"{rotulo(k)} & {b} & {ee} & {hc} & {num(c['t'], 1)} & {pval(c['valor-p HC3'])} & {pc} & {ic} \\\\")
(SALIDA / "coef_m3.tex").write_text("\n".join(filas) + "\n")

# ---------- Anexo D: recorrido forward por BIC
filas = []
for i, s in sorted(d["forward_pasos"].items(), key=lambda t: int(t[0])):
    if i == "0":
        filas.append(f"0 & Intercepto & {s['k']} & {num(s['BIC'], 0)} & --- & {num(0, 3)} & --- \\\\")
        continue
    filas.append(f"{i} & {s['entra'].capitalize()} & {s['k']} & {num(s['BIC'], 0)} & {num(s['ΔBIC'], 0)} & "
                 f"{num(s['R² ajustado'], 3)} & {num(s['F parcial'], 0)} \\\\")
(SALIDA / "forward.tex").write_text("\n".join(filas) + "\n")

# ---------- Anexo E: supuestos (deciles, edad observada y ajustada)
filas = []
for k, v in d["deciles"].items():
    filas.append(f"{k} & {num(v['egresos'], 0)} & {num(v['ajustada (media geométrica)'], 2)} & "
                 f"{num(v['observada (media geométrica)'], 2)} & {num(v['observada (mediana)'], 0)} \\\\")
(SALIDA / "deciles.tex").write_text("\n".join(filas) + "\n")

TRAMO = {"0.5": "menor de un año", "5.0": "1 a 9", "14.5": "10 a 19", "24.5": "20 a 29", "34.5": "30 a 39",
         "44.5": "40 a 49", "54.5": "50 a 59", "64.5": "60 a 69", "74.5": "70 a 79", "84.5": "80 a 89",
         "92.5": "90 y más"}
filas = []
for k, v in d["edad_observada_ajustada"].items():
    filas.append(f"{TRAMO[k]} & {num(float(k), 1)} & {num(v['log_dias'], 2)} & {num(v['ajuste_ln'], 2)} & "
                 f"{num(math.exp(v['log_dias']), 2)} & {num(math.exp(v['ajuste_ln']), 2)} \\\\")
(SALIDA / "edad.tex").write_text("\n".join(filas) + "\n")

# ---------- Anexo A (informe_v2): tablas de contingencia de los chi-cuadrado
ORDEN_TRAMO = ["menor de un año", "1 a 9", "10 a 19", "20 a 29", "30 a 39", "40 a 49", "50 a 59", "60 a 69",
               "70 a 79", "80 a 89", "90 y más"]
FACTOR = [("capitulo", "Capítulo \\cie"), ("tramo_edad", "Tramo de edad"), ("sexo", "Sexo"),
          ("nacionalidad", "Nacionalidad"), ("etnia", "Pueblo originario"), ("cirugia", "Cirugía"),
          ("fallecido", "Fallecido"), ("establecimiento", "Establecimiento"), ("region", "Región")]
filas = []
for var, nom in FACTOR:
    tabla = d["contingencia"][var]
    niveles = ORDEN_TRAMO if var == "tramo_edad" else sorted(tabla)
    for i, n in enumerate(niveles):
        no, si = tabla[n]["No"], tabla[n]["Sí"]
        assert abs(100 * si / (no + si) - d["pct_prolongadas_por_grupo"][var][n]) < 0.01
        if var == "capitulo":
            cat = f"{n.replace('-', '--')} ({CAPS[n]})"
        elif var == "region":
            cat = rotulo(f"region: {n}").removeprefix("Región: ")
        else:
            cat = n if "SNSS" in n else n.capitalize()
        filas.append(f"{nom if i == 0 else ''} & {cat} & {num(no, 0)} & {num(si, 0)} & {num(no + si, 0)} & "
                     f"{num(100 * si / (no + si), 1)} \\\\")
    filas[-1] += "\\midrule" if var != "region" else ""
assert sum(sum(v.values()) for v in d["contingencia"]["sexo"].values()) == d["n"]
(SALIDA / "contingencia.tex").write_text("\n".join(filas) + "\n")

print("anexos escritos en", SALIDA)
