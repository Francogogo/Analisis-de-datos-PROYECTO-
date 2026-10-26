"""Avance 1: pruebas de relaciones entre variables (sección 5 de la guía).

Datos: egresos hospitalarios DEIS-MINSAL 2020, solo beneficiarios FONASA.
Salida: figures/avance1/*.png y results/avance1_resultados.json

Uso: .venv/Scripts/python scripts/01_avance1_relaciones.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import lilliefors
from statsmodels.stats.multicomp import pairwise_tukeyhsd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data/raw/x2020/EGRE_DATOS_ABIERTOS_2020.csv"
DIC = ROOT / "data/raw/x2020/Diccionario BD egresos hospitalario.xlsx"
FIG = ROOT / "figures/avance1"
OUT = ROOT / "results"
FIG.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

ALPHA = 0.05
SEED = 2026
UMBRAL_PROLONGADA = 15  # percentil 90 de DIAS_ESTADA (FONASA 2020)
rng = np.random.default_rng(SEED)
R = {}  # resultados

# ---------------------------------------------------------------- carga
df = pd.read_csv(CSV, sep=";", encoding="cp1252", dtype=str)
n_total = len(df)
df = df[df["PREVISION"] == "1"].copy()  # FONASA
n_fonasa = len(df)
df["dias"] = pd.to_numeric(df["DIAS_ESTADA"])
n_mas_365 = int((df["dias"] > 365).sum())
df = df[df["dias"] <= 365].copy()

# Capítulo CIE-10 desde el diccionario (subcategoría; si no calza, categoría)
cie = pd.read_excel(DIC, "codigo CIE-10", header=8)
cie.columns = [c.strip() for c in cie.columns]
sub2cap = dict(zip(cie["CODIGO SUBCATEGORIA"], cie["CAPITULO"]))
cat2cap = dict(zip(cie["CODIGO CATEGORIA"], cie["CAPITULO"]))
df["capitulo"] = df["DIAG1"].map(sub2cap).fillna(df["DIAG1"].str[:3].map(cat2cap))
df["categoria"] = df["DIAG1"].str[:3]

EDAD_MEDIA = {"menor de un año": 0.5, "1 a 9": 5, "10 a 19": 14.5, "20 a 29": 24.5,
              "30 a 39": 34.5, "40 a 49": 44.5, "50 a 59": 54.5, "60 a 69": 64.5,
              "70 a 79": 74.5, "80 a 89": 84.5, "90 y más": 92.5}
ORDEN_EDAD = list(EDAD_MEDIA)
df["edad_media"] = df["GRUPO_EDAD"].map(EDAD_MEDIA)
df["log_dias"] = np.log(df["dias"])
df["prolongada"] = np.where(df["dias"] > UMBRAL_PROLONGADA, "Sí", "No")
df["cirugia"] = df["INTERV_Q"].map({"1": "Sí", "2": "No"})
df["fallecido"] = df["CONDICION_EGRESO"].map({"1": "Vivo", "2": "Fallecido"})
df["snss"] = np.where(df["PERTENENCIA_ESTABLECIMIENTO_SALUD"].str.startswith("Pertenecientes"),
                      "SNSS", "No SNSS")
df["region"] = df["GLOSA_REGION_RESIDENCIA"]

R["datos"] = {
    "n_total_2020": n_total, "n_fonasa": n_fonasa, "n_excluidos_mas_365": n_mas_365,
    "n_analisis": len(df), "capitulo_sin_mapear": int(df["capitulo"].isna().sum()),
    "dias_desc": {k: float(v) for k, v in df["dias"].describe(
        percentiles=[.25, .5, .75, .9, .95, .99]).items()},
    "pct_prolongada": float((df["prolongada"] == "Sí").mean()),
    "pct_cirugia": float((df["cirugia"] == "Sí").mean()),
    "pct_fallecido": float((df["fallecido"] == "Fallecido").mean()),
    "pct_mujer": float((df["SEXO"] == "MUJER").mean()),
    "skew": float(stats.skew(df["dias"])), "kurtosis": float(stats.kurtosis(df["dias"])),
}

# ---------------------------------------------------------------- 5.1 normalidad
def normalidad(x, nombre):
    x = np.asarray(x, float)
    sub = rng.choice(x, 5000, replace=False)  # Shapiro-Wilk válido hasta n≈5000
    sw = stats.shapiro(sub)
    ks_stat, ks_p = lilliefors(x, dist="norm", pvalmethod="approx")
    ad = stats.anderson(x, dist="norm")
    return {"variable": nombre,
            "shapiro_W": float(sw.statistic), "shapiro_p": float(sw.pvalue), "shapiro_n": 5000,
            "lilliefors_D": float(ks_stat), "lilliefors_p": float(ks_p), "lilliefors_n": len(x),
            "ad_A2": float(ad.statistic), "ad_crit_5pct": float(ad.critical_values[2])}

R["normalidad"] = [normalidad(df["dias"], "dias_estada"),
                   normalidad(df["log_dias"], "log(dias_estada)"),
                   normalidad(df["edad_media"], "edad_media")]

fig, ax = plt.subplots(2, 3, figsize=(15, 8))
for j, (col, tit) in enumerate([("dias", "Días de estada"), ("log_dias", "log(días de estada)"),
                                ("edad_media", "Edad (punto medio del grupo)")]):
    x = df[col]
    ax[0, j].hist(x.clip(upper=60) if col == "dias" else x, bins=60, color="#4C72B0")
    ax[0, j].set_title(tit + (" (recortado a 60)" if col == "dias" else ""))
    stats.probplot(rng.choice(x.values, 5000, replace=False), dist="norm", plot=ax[1, j])
    ax[1, j].set_title("Q-Q normal: " + tit)
fig.tight_layout(); fig.savefig(FIG / "01_normalidad_hist_qq.png", dpi=120); plt.close(fig)

# ---------------------------------------------------------------- 5.2 numérica vs numérica
def correlaciones(x, y):
    p = stats.pearsonr(x, y); s = stats.spearmanr(x, y)
    return {"n": len(x), "pearson_r": float(p.statistic), "pearson_p": float(p.pvalue),
            "spearman_rho": float(s.statistic), "spearman_p": float(s.pvalue)}

R["num_num"] = {}
R["num_num"]["edad_vs_dias"] = correlaciones(df["edad_media"], df["dias"])
med_edad = df.groupby("GRUPO_EDAD")["dias"].agg(["mean", "median"]).reindex(ORDEN_EDAD)
R["num_num"]["edad_vs_dias"]["medias_por_grupo"] = med_edad.round(2).reset_index().values.tolist()

# Nivel categoría CIE-10 (3 caracteres, n >= 100): estadía mediana vs letalidad
agg = df.groupby("categoria").agg(n=("dias", "size"), est_media=("dias", "mean"),
                                  est_mediana=("dias", "median"),
                                  letalidad=("fallecido", lambda s: (s == "Fallecido").mean()))
agg = agg[agg["n"] >= 100]
R["num_num"]["cat_estadia_vs_letalidad"] = correlaciones(agg["est_media"], agg["letalidad"])

fig, ax = plt.subplots(1, 2, figsize=(13, 5))
sm = df.sample(20000, random_state=SEED)
ax[0].scatter(sm["edad_media"] + rng.uniform(-3, 3, len(sm)), sm["dias"], s=3, alpha=.25)
ax[0].plot(med_edad.index.map(EDAD_MEDIA), med_edad["mean"], "r-o", label="media por grupo")
ax[0].set_yscale("log"); ax[0].set_xlabel("Edad (punto medio, con jitter)")
ax[0].set_ylabel("Días de estada (log)"); ax[0].legend()
ax[0].set_title("Edad vs días de estada (muestra 20.000)")
ax[1].scatter(agg["letalidad"] * 100, agg["est_media"], s=np.sqrt(agg["n"]), alpha=.5)
ax[1].set_xlabel("Letalidad hospitalaria (%)"); ax[1].set_ylabel("Estadía media (días)")
ax[1].set_title(f"Categorías CIE-10 (n={len(agg)}, ≥100 egresos)")
fig.tight_layout(); fig.savefig(FIG / "02_dispersion.png", dpi=120); plt.close(fig)

# ---------------------------------------------------------------- 5.3 numérica vs categórica
def dos_grupos(var, a, b):
    xa = df.loc[df[var] == a, "dias"].values; xb = df.loc[df[var] == b, "dias"].values
    lev = stats.levene(xa, xb, center="median")
    t_st = stats.ttest_ind(xa, xb, equal_var=True)
    t_w = stats.ttest_ind(xa, xb, equal_var=False)
    mw = stats.mannwhitneyu(xa, xb, alternative="two-sided")
    n1, n2 = len(xa), len(xb)
    sp = np.sqrt(((n1 - 1) * xa.var(ddof=1) + (n2 - 1) * xb.var(ddof=1)) / (n1 + n2 - 2))
    return {"var": var, "grupos": [a, b], "n": [n1, n2],
            "media": [float(xa.mean()), float(xb.mean())],
            "mediana": [float(np.median(xa)), float(np.median(xb))],
            "levene_W": float(lev.statistic), "levene_p": float(lev.pvalue),
            "t_student": float(t_st.statistic), "t_student_p": float(t_st.pvalue),
            "t_welch": float(t_w.statistic), "t_welch_p": float(t_w.pvalue),
            "cohen_d": float((xa.mean() - xb.mean()) / sp),
            "mannwhitney_U": float(mw.statistic), "mannwhitney_p": float(mw.pvalue),
            "rank_biserial": float(2 * mw.statistic / (n1 * n2) - 1)}

def k_grupos(var, min_n=0):
    g = df.groupby(var)["dias"]
    grupos = {k: v.values for k, v in g if len(v) >= min_n}
    vals = list(grupos.values()); N = sum(map(len, vals)); k = len(vals)
    lev = stats.levene(*vals, center="median")
    an = stats.f_oneway(*vals)
    kw = stats.kruskal(*vals)
    allx = np.concatenate(vals); gm = allx.mean()
    ss_b = sum(len(v) * (v.mean() - gm) ** 2 for v in vals); ss_t = ((allx - gm) ** 2).sum()
    return {"var": var, "k": k, "N": int(N),
            "levene_W": float(lev.statistic), "levene_p": float(lev.pvalue),
            "anova_F": float(an.statistic), "anova_p": float(an.pvalue), "eta2": float(ss_b / ss_t),
            "kruskal_H": float(kw.statistic), "kruskal_p": float(kw.pvalue),
            "epsilon2": float((kw.statistic - k + 1) / (N - k)),
            "medianas": {str(kk): float(np.median(v)) for kk, v in grupos.items()},
            "medias": {str(kk): float(v.mean()) for kk, v in grupos.items()}}

R["num_cat"] = {
    "sexo": dos_grupos("SEXO", "HOMBRE", "MUJER"),
    "cirugia": dos_grupos("cirugia", "Sí", "No"),
    "snss": dos_grupos("snss", "SNSS", "No SNSS"),
    "capitulo": k_grupos("capitulo", min_n=1000),
    "grupo_edad": k_grupos("GRUPO_EDAD"),
}

# Tukey HSD (capítulos, sobre log días para estabilizar varianzas) y Dunn-Bonferroni aprox.
cap_ok = [c for c, n in df["capitulo"].value_counts().items() if n >= 1000]
d_cap = df[df["capitulo"].isin(cap_ok)]
tk = pairwise_tukeyhsd(d_cap["log_dias"].values, d_cap["capitulo"].values, alpha=ALPHA)
tk_df = pd.DataFrame(tk.summary().data[1:], columns=tk.summary().data[0])
R["num_cat"]["tukey_capitulo"] = {"n_pares": len(tk_df), "n_rechaza": int(tk_df["reject"].sum())}
tk_df.to_csv(OUT / "avance1_tukey_capitulos.csv", index=False)

# Post-hoc no paramétrico de Kruskal-Wallis: Mann-Whitney por pares con Bonferroni
pares = []
caps = sorted(cap_ok)
for i in range(len(caps)):
    for j in range(i + 1, len(caps)):
        a = d_cap.loc[d_cap["capitulo"] == caps[i], "dias"]; b = d_cap.loc[d_cap["capitulo"] == caps[j], "dias"]
        u = stats.mannwhitneyu(a, b)
        pares.append((caps[i], caps[j], u.pvalue))
m = len(pares)
R["num_cat"]["posthoc_mw_bonf"] = {"n_pares": m, "n_signif": int(sum(p * m < ALPHA for *_, p in pares))}

fig, ax = plt.subplots(1, 3, figsize=(18, 6), gridspec_kw={"width_ratios": [1, 1, 3]})
for a_, var, orden in [(ax[0], "SEXO", ["HOMBRE", "MUJER"]), (ax[1], "cirugia", ["Sí", "No"])]:
    a_.boxplot([df.loc[df[var] == o, "dias"] for o in orden], tick_labels=orden, showfliers=False)
    a_.set_title(f"Días de estada por {var} (sin outliers)")
orden_cap = d_cap.groupby("capitulo")["dias"].median().sort_values().index
ax[2].boxplot([d_cap.loc[d_cap["capitulo"] == c, "dias"] for c in orden_cap],
              tick_labels=orden_cap, showfliers=False)
ax[2].tick_params(axis="x", rotation=60); ax[2].set_title("Días de estada por capítulo CIE-10")
fig.tight_layout(); fig.savefig(FIG / "03_boxplots.png", dpi=120); plt.close(fig)

# ---------------------------------------------------------------- 5.4 categórica vs categórica
def chi2(var, y="prolongada"):
    tab = pd.crosstab(df[var], df[y])
    c = stats.chi2_contingency(tab)
    n = tab.values.sum(); r, k = tab.shape
    v = np.sqrt(c.statistic / (n * (min(r, k) - 1)))
    res = {"var": var, "y": y, "chi2": float(c.statistic), "gl": int(c.dof), "p": float(c.pvalue),
           "cramer_v": float(v), "min_esperada": float(c.expected_freq.min()),
           "pct_esperadas_menor_5": float((c.expected_freq < 5).mean()),
           "tabla": tab.to_dict(), "pct_si": (tab["Sí"] / tab.sum(1)).round(4).to_dict() if "Sí" in tab else None}
    if tab.shape == (2, 2):
        odds, pf = stats.fisher_exact(tab.values)
        res.update(fisher_OR=float(odds), fisher_p=float(pf))
    return res

R["cat_cat"] = {v: chi2(v) for v in ["SEXO", "cirugia", "fallecido", "GRUPO_EDAD", "capitulo", "region"]}
R["cat_cat"]["cirugia_x_fallecido"] = chi2("cirugia", y="fallecido")
R["cat_cat"]["cirugia_x_fallecido"]["pct_si"] = None

fig, ax = plt.subplots(1, 2, figsize=(16, 6))
p_edad = pd.crosstab(df["GRUPO_EDAD"], df["prolongada"], normalize="index").reindex(ORDEN_EDAD) * 100
p_edad.plot(kind="bar", stacked=True, ax=ax[0], color=["#9ecae1", "#de2d26"])
ax[0].set_ylabel("%"); ax[0].set_title("Estadía prolongada (>15 días) por grupo de edad")
p_cap = (pd.crosstab(d_cap["capitulo"], d_cap["prolongada"], normalize="index")["Sí"] * 100).sort_values()
ax[1].barh(p_cap.index, p_cap.values, color="#de2d26")
ax[1].set_xlabel("% estadías prolongadas"); ax[1].set_title("% prolongadas por capítulo CIE-10")
fig.tight_layout(); fig.savefig(FIG / "04_barras_chi2.png", dpi=120); plt.close(fig)

# Mapa de calor: residuos estandarizados capítulo x prolongada
tab = pd.crosstab(d_cap["capitulo"], d_cap["prolongada"])
exp = stats.contingency.expected_freq(tab)
res = (tab - exp) / np.sqrt(exp)
fig, ax = plt.subplots(figsize=(5, 9))
im = ax.imshow(res.values, cmap="RdBu_r", vmin=-60, vmax=60, aspect="auto")
ax.set_yticks(range(len(res)), res.index); ax.set_xticks([0, 1], res.columns)
ax.set_title("Residuos estandarizados χ²\n(capítulo × prolongada)"); fig.colorbar(im)
fig.tight_layout(); fig.savefig(FIG / "05_heatmap_residuos.png", dpi=120); plt.close(fig)

with open(OUT / "avance1_resultados.json", "w", encoding="utf-8") as fh:
    json.dump(R, fh, ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: v for k, v in R.items()}, ensure_ascii=False, indent=1, default=str)[:20000])
