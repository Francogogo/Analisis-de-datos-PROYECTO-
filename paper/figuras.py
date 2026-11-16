"""Figuras del informe.

avance2_v8.ipynb llama a estas funciones con los datos que calcula, y además guarda en
results/base_figuras.parquet las columnas que usan los gráficos. Con esa base y
results/cifras_avance2_v8.json, las figuras se regeneran en segundos sin estimar ningún modelo:

    python3 paper/figuras.py        (desde la raíz del repositorio)

Antes de guardar, cada figura pasa por revisar_solapes(): si dos textos (rótulos, ticks, títulos,
leyendas) quedan a menos de 1 mm entre sí, o un texto invade el área de otro panel, se detiene.
"""
import json
import os
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from scipy import stats

RAIZ = Path(__file__).resolve().parent.parent
FIGS = RAIZ / "paper/figs"
teal, petroleo, coral = "#0E7C7A", "#0F2A33", "#D9534F"
verde_f, ambar_f, tinta_f = "#0E5E5C", "#B8741F", "#22343A"
ORDEN_TRAMO = ["menor de un año", "1 a 9", "10 a 19", "20 a 29", "30 a 39", "40 a 49", "50 a 59", "60 a 69",
               "70 a 79", "80 a 89", "90 y más"]
SEPARACION_MM = 1.0


def estilo():
    fuentes = [os.path.expanduser(f"~/.fonts/{f}") for f in ("Figtree-Regular.ttf", "Figtree-Medium.ttf")]
    if all(os.path.exists(f) for f in fuentes):
        for f in fuentes:
            fm.fontManager.addfont(f)
        plt.rcParams["font.family"] = "Figtree"
    plt.rcParams.update({"font.size": 7.5, "axes.labelsize": 7.5, "xtick.labelsize": 6.8, "ytick.labelsize": 6.8,
                         "legend.fontsize": 6.8, "axes.titlesize": 8, "lines.linewidth": 1.1, "lines.markersize": 3.2,
                         "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3,
                         "pdf.fonttype": 42})


def corto(n):
    """Nombre de región abreviado para los ejes."""
    for pre in ("De ", "Del "):
        if n.startswith(pre):
            n = n[len(pre):]
    return {"Aisén del Gral. C. Ibáñez del Campo": "Aisén", "Magallanes y de La Antártica Chilena": "Magallanes",
            "Libertador B. O'Higgins": "O'Higgins", "Metropolitana de Santiago": "Metropolitana"}.get(n, n)


# ---------- revisión de solapes
def _textos(fig):
    """Cajas (en píxeles) de cada texto visible, con el panel al que pertenece."""
    cajas = []
    for ax in fig.axes:
        elems = [ax.xaxis.label, ax.yaxis.label, ax.title]
        for eje in (ax.xaxis, ax.yaxis):                   # solo los ticks dentro de los límites del eje (los dibujados)
            lo, hi = sorted(eje.get_view_interval())
            tol = 1e-9 * max(1, abs(hi - lo))
            elems += [t.label1 for t in eje.get_major_ticks() if lo - tol <= t.get_loc() <= hi + tol]
        elems += [t for t in ax.texts]
        for t in elems:
            if t.get_visible() and t.get_text().strip():
                cajas.append((ax, t.get_text(), t.get_window_extent(), t in ax.texts))
        if ax.get_legend():
            cajas.append((ax, "leyenda", ax.get_legend().get_window_extent(), False))
    for t in fig.texts:
        if t.get_visible() and t.get_text().strip():
            cajas.append((None, t.get_text(), t.get_window_extent(), False))
    for leg in fig.legends:
        cajas.append((None, "leyenda", leg.get_window_extent(), False))
    return cajas


def revisar_solapes(fig):
    """Lista de choques: textos de paneles distintos a menos de SEPARACION_MM, textos de un mismo panel que se
    tocan, o texto dentro del área de otro panel."""
    fig.draw_without_rendering()                       # funciona con cualquier backend, también el inline de Jupyter
    pad = SEPARACION_MM / 25.4 * fig.dpi / 2
    cajas = _textos(fig)
    choques = []
    for (a1, t1, b1, d1), (a2, t2, b2, d2) in combinations(cajas, 2):
        if d1 and d2 and a1 is a2:                     # textos dentro de un mismo panel (celdas de un mapa de calor)
            continue
        p = 0 if (a1 is a2 and a1 is not None) else pad  # dentro de un panel basta con que no se toquen
        if b1.padded(p).overlaps(b2.padded(p)):
            choques.append(f"«{t1}» con «{t2}»")
    for ax, t, b, dentro in cajas:
        if dentro:
            continue
        for otro in fig.axes:
            if otro is ax:
                continue
            if b.overlaps(otro.get_window_extent()):
                choques.append(f"«{t}» invade el panel «{otro.get_title() or otro.get_ylabel() or 'sin título'}»")
    return choques


def guardar(fig, nombre, png=False):
    choques = revisar_solapes(fig)
    if choques:
        raise AssertionError(f"{nombre}: " + "; ".join(choques))
    fig.savefig(FIGS / f"{nombre}.pdf", dpi=250, bbox_inches="tight")
    if png:
        fig.savefig(FIGS / f"{nombre}.png", dpi=250, bbox_inches="tight")


# ---------- figuras del cuerpo
def distribucion(dias, log_dias, pct_egresos, pct_dias):
    orden = np.sort(np.asarray(dias))[::-1]                   # de la estadía más larga a la más corta
    x_conc = 100 * np.arange(1, len(orden) + 1) / len(orden)
    y_conc = 100 * orden.cumsum() / orden.sum()
    fig, ax = plt.subplots(1, 3, figsize=(6.0, 2.05), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.06, wspace=0.08)
    ax[0].hist(dias, bins=range(1, 61), color=teal)
    ax[0].set_xlabel("Días de estada (hasta 60)")
    ax[0].set_ylabel("Egresos")
    ax[1].hist(log_dias, bins=40, color=teal)
    ax[1].set_xlabel("ln(días de estada)")
    ax[2].plot(x_conc[::500], y_conc[::500], color=petroleo)
    ax[2].plot([0, 100], [0, 100], color="gray", linestyle="--")
    ax[2].scatter([pct_egresos], [pct_dias], color=coral, zorder=3)
    ax[2].set_xlabel("% de egresos (de más larga a más corta)")
    ax[2].set_ylabel("% acumulado de días-cama")
    for a in ax[:2]:
        a.yaxis.set_major_formatter(lambda v, _: f"{v / 1000:.0f} mil" if v else "0")
    return fig


def bivariado(df):
    orden_cap = df.groupby("capitulo")["log_dias"].median().sort_values().index
    fig = plt.figure(figsize=(5.9, 3.0), layout="constrained")
    gs = fig.add_gridspec(2, 2, width_ratios=[1.5, 1])
    ax0 = fig.add_subplot(gs[:, 0])
    ax0.boxplot([df.loc[df["capitulo"] == k, "log_dias"] for k in orden_cap], orientation="horizontal", showfliers=False,
                patch_artist=True, boxprops=dict(facecolor=teal, alpha=0.6), medianprops=dict(color=petroleo))
    ax0.set_yticks(range(1, len(orden_cap) + 1), orden_cap, fontsize=6)
    ax0.set_xlabel("ln(días de estada)")
    ax0.set_title("Capítulo CIE-10", fontsize=7.5)
    ax0.tick_params(axis="x", labelsize=6.5)
    ax0.xaxis.label.set_size(7)
    for ax, col, tit in [(fig.add_subplot(gs[0, 1]), "establecimiento", "Establecimiento"),
                         (fig.add_subplot(gs[1, 1]), "sexo", "Sexo")]:
        niv = sorted(df[col].unique())
        ax.boxplot([df.loc[df[col] == n, "log_dias"] for n in niv], orientation="horizontal", showfliers=False,
                   patch_artist=True, boxprops=dict(facecolor=teal, alpha=0.6), medianprops=dict(color=petroleo))
        ax.set_yticks(range(1, len(niv) + 1), [n if "SNSS" in n else n.capitalize() for n in niv], fontsize=6.5)
        ax.tick_params(axis="x", labelsize=6.5)
        ax.xaxis.label.set_size(7)
        ax.set_xlabel("ln(días de estada)")
        ax.set_title(tit, fontsize=7.5)
    return fig


def cramer(V):
    cats = list(V.index)
    fig, ax = plt.subplots(figsize=(2.9, 2.4), layout="constrained")
    im = ax.imshow(V.values, cmap="Greens", vmin=0, vmax=1)
    ax.set_xticks(range(len(cats)), cats, rotation=90, fontsize=6)
    ax.set_yticks(range(len(cats)), cats, fontsize=6)
    for i in range(len(cats)):
        for j in range(len(cats)):
            v = V.iloc[i, j]
            ax.text(j, i, f"{v:.2f}".replace(".", ","), ha="center", va="center",
                    color="white" if v > 0.6 else "black", fontsize=5.5)
    ax.grid(False)
    cb = fig.colorbar(im, fraction=0.046, pad=0.04)
    cb.set_label("V de Cramér", fontsize=6.5)
    cb.ax.tick_params(labelsize=6)
    return fig


def edad(por_tramo):
    fig, ax = plt.subplots(figsize=(2.9, 2.3), layout="constrained")
    ax.plot(por_tramo.index, por_tramo["log_dias"], marker="o", color=teal, label="media observada")
    ax.plot(por_tramo.index, por_tramo["ajuste_ln"], marker="s", color=coral, label="media ajustada por M3")
    ax.set_xlabel("Edad (punto medio del tramo)", fontsize=6.5)
    ax.set_ylabel("ln(días de estada)", fontsize=6.5)
    ax.tick_params(labelsize=6)
    ax.legend(fontsize=6, loc="upper left")
    return fig


def forest(coef):
    filas = []
    for k, v in coef[["%Δ", "%Δ inf", "%Δ sup"]].to_dict("index").items():
        if k.startswith("capitulo"): filas.append(("Cap. " + k.split(": ")[1], v, verde_f))
        elif k == "cirugia: Sí": filas.append(("Cirugía", v, verde_f))
        elif k == "fallecido: Sí": filas.append(("Egreso: fallecido", v, verde_f))
        elif k == "sexo: HOMBRE": filas.append(("Sexo: hombre", v, tinta_f))
        elif k == "establecimiento: SNSS": filas.append(("Establecimiento: SNSS", v, ambar_f))
        elif k.startswith("region"): filas.append((corto(k.split(": ")[1]), v, ambar_f))
    filas.sort(key=lambda r: r[1]["%Δ"])
    with plt.rc_context({"axes.grid": False, "grid.alpha": 1.0, "xtick.labelsize": 6.5, "ytick.labelsize": 6.3,
                         "legend.fontsize": 6.3, "axes.labelsize": 6.8, "axes.titlesize": 7.5}):
        fig, axs = plt.subplots(1, 2, figsize=(5.9, 3.3), sharex=True, gridspec_kw={"width_ratios": [1.15, 1]},
                                layout="constrained")
        grupos = [("Capítulos CIE-10", [r for r in filas if r[0].startswith("Cap. ")]),
                  ("Otros factores", [r for r in filas if not r[0].startswith("Cap. ")])]
        for ax, (tit, fs) in zip(axs, grupos):
            for i, (n, v, c) in enumerate(fs):
                ax.plot([v["%Δ inf"], v["%Δ sup"]], [i, i], color=c, lw=1.1)
                ax.plot(v["%Δ"], i, "o", color=c, ms=3)
            ax.axvline(0, color="#5F6F74", lw=0.8, ls="--")
            ax.set_yticks(range(len(fs)), [r[0] for r in fs], fontsize=6.3)
            ax.set_ylim(-0.7, len(fs) - 0.3)
            ax.set_title(tit)
            ax.grid(axis="x", color="#B9CFCD", lw=0.4)
            for sp in ("top", "right"): ax.spines[sp].set_visible(False)
        fig.supxlabel("Cambio porcentual en la media geométrica de días (IC 95 %)", fontsize=6.8)
        fig.legend(handles=[Line2D([], [], marker="o", ls="", color=c, label=l) for c, l in
                            ((verde_f, "Clínico"), (tinta_f, "Demográfico"), (ambar_f, "Sistema de salud"))],
                   loc="outside upper center", ncol=3, frameon=False)
    return fig


def residuos(ajustado, residuo):
    ajustado, r = np.asarray(ajustado), np.asarray(residuo)
    pos = np.linspace(0, len(r) - 1, min(20000, len(r)), dtype=int)
    dec = pd.qcut(pd.Series(ajustado).rank(method="first"), 20, labels=False)
    medias = pd.DataFrame({"ajustado": ajustado, "residuo": r}).groupby(dec).mean()
    fig, ax = plt.subplots(1, 3, figsize=(5.9, 2.45), layout="constrained")
    ax[0].scatter(ajustado[pos], r[pos], s=3, alpha=0.15, color=teal, rasterized=True)
    ax[0].plot(medias["ajustado"], medias["residuo"], color=coral, marker="o", label="media por ventiles")
    ax[0].axhline(0, color="gray", linestyle="--")
    ax[0].set_xlabel("ln(días) ajustado")
    ax[0].set_ylabel("Residuo")
    ax[1].hist(r, bins=60, color=teal)
    ax[1].set_xlabel("Residuo")
    stats.probplot(r[pos], plot=ax[2])
    ax[2].set_title("")
    ax[2].get_lines()[0].set_color(teal)
    ax[2].get_lines()[0].set_rasterized(True)          # 20.000 puntos: en el PDF van como imagen
    ax[2].get_lines()[1].set_color(coral)
    ax[2].set_xlabel("Cuantiles teóricos")
    ax[2].set_ylabel("Cuantiles observados")
    for a in ax:
        a.tick_params(labelsize=6.3)
        a.xaxis.label.set_size(7)
        a.yaxis.label.set_size(7)
    fig.legend(handles=ax[0].get_legend_handles_labels()[0], labels=["Media de los residuos por ventil de valor ajustado"],
               loc="outside upper left", fontsize=6.3, frameon=False)
    return fig


# ---------- figuras del anexo A
def normalidad(df):
    muestra = df.sample(5000, random_state=1)                 # la misma muestra de Shapiro-Wilk
    fig, ax = plt.subplots(1, 4, figsize=(6.0, 1.85), layout="constrained")
    ax[0].hist(df["edad"], bins=np.arange(-0.5, 101, 10), color=teal)
    ax[0].set_xlabel("Edad (punto medio del tramo)", fontsize=6.5)
    ax[0].set_ylabel("Egresos", fontsize=6.5)
    ax[0].yaxis.set_major_formatter(lambda v, _: f"{v / 1000:.0f} mil" if v else "0")
    for a, col, tit in zip(ax[1:], ["dias_estada", "log_dias", "edad"], ["Q-Q días", "Q-Q ln(días)", "Q-Q edad"]):
        stats.probplot(muestra[col].astype(float), plot=a)
        a.get_lines()[0].set_color(teal); a.get_lines()[0].set_markersize(1.5); a.get_lines()[1].set_color(coral)
        a.get_lines()[0].set_rasterized(True)
        a.set_title(tit, fontsize=7); a.set_xlabel("Cuantiles teóricos", fontsize=6.5); a.set_ylabel("")
    for a in ax:
        a.tick_params(labelsize=6)
    return fig


def cajas(df):
    fig = plt.figure(figsize=(6.0, 3.5), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.06, wspace=0.06)
    gs = fig.add_gridspec(4, 3, width_ratios=[1, 1.15, 1])

    def panel(ax, col, niveles, etiquetas, titulo):
        ax.boxplot([df.loc[df[col] == n, "log_dias"] for n in niveles], orientation="horizontal", showfliers=False,
                   patch_artist=True, boxprops=dict(facecolor=teal, alpha=0.6), medianprops=dict(color=petroleo))
        ax.set_yticks(range(1, len(niveles) + 1), etiquetas, fontsize=5.8)
        ax.set_title(titulo, fontsize=7)
        ax.tick_params(axis="x", labelsize=6)

    panel(fig.add_subplot(gs[:, 0]), "tramo_edad", ORDEN_TRAMO, ORDEN_TRAMO, "Tramo de edad (Spearman)")
    reg = df.groupby("region")["log_dias"].median().sort_values().index
    panel(fig.add_subplot(gs[:, 1]), "region", reg, [corto(n) for n in reg], "Región")
    for i, (col, tit) in enumerate([("cirugia", "Cirugía"), ("fallecido", "Fallecido"),
                                    ("nacionalidad", "Nacionalidad"), ("etnia", "Pueblo originario")]):
        niv = sorted(df[col].unique())
        panel(fig.add_subplot(gs[i, 2]), col, niv, [n.capitalize() for n in niv], tit)
    fig.supxlabel("ln(días de estada)", fontsize=6.8)
    return fig


def prolongadas(pct):
    """pct: dict variable -> Serie con el % de estadías prolongadas por categoría."""
    binarias = [("sexo", "Sexo"), ("nacionalidad", "Nacionalidad"), ("etnia", "Pueblo originario"),
                ("cirugia", "Cirugía"), ("fallecido", "Fallecido"), ("establecimiento", "Establecimiento")]
    nivel = lambda n: n if "SNSS" in n else n.capitalize()
    fig, axs = plt.subplots(2, 2, figsize=(6.0, 6.6), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.06, wspace=0.06)

    def apiladas(ax, filas, titulo):
        si = np.array([p for _, p in filas])
        y = np.arange(len(filas))
        ax.barh(y, si, color=coral, label="Prolongada (> 15 días)")
        ax.barh(y, 100 - si, left=si, color=teal, alpha=0.35, label="No prolongada")
        ax.set_yticks(y, [e for e, _ in filas], fontsize=6)
        ax.set_ylim(len(filas) - 0.5, -0.5)
        ax.set_xlim(0, 100); ax.set_title(titulo, fontsize=7.5); ax.tick_params(axis="x", labelsize=6); ax.grid(False)
        ax.set_xlabel("% de egresos", fontsize=6.5)

    apiladas(axs[0, 0], [(k, pct["capitulo"][k]) for k in pct["capitulo"].sort_values(ascending=False).index], "Capítulo CIE-10")
    apiladas(axs[0, 1], [(corto(k), pct["region"][k]) for k in pct["region"].sort_values(ascending=False).index], "Región")
    apiladas(axs[1, 0], [(k, pct["tramo_edad"][k]) for k in ORDEN_TRAMO], "Tramo de edad")
    apiladas(axs[1, 1], [(f"{t}: {nivel(k)}", pct[v][k]) for v, t in binarias for k in sorted(pct[v].index)],
             "Factores de dos grupos")
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="outside lower center", ncol=2, fontsize=6.3, frameon=False)
    return fig


def matriz_cramer(df, cats=("capitulo", "cirugia", "fallecido", "sexo", "establecimiento", "region")):
    cats = list(cats)
    V = pd.DataFrame(1.0, index=cats, columns=cats)
    for i, a in enumerate(cats):
        for b in cats[i + 1:]:
            tabla = pd.crosstab(df[a], df[b])
            chi2 = stats.chi2_contingency(tabla)[0]
            V.loc[a, b] = V.loc[b, a] = np.sqrt(chi2 / (len(df) * (min(tabla.shape) - 1)))
    return V


def todas(base, cifras):
    """Genera las nueve figuras a partir de la base de figuras y del JSON de cifras."""
    pct = {k: pd.Series(v) for k, v in cifras["pct_prolongadas_por_grupo"].items()}
    coef = pd.DataFrame(cifras["coef"]).T
    por_tramo = base.groupby("edad")[["log_dias", "ajuste_ln"]].mean()
    figuras = [
        (distribucion(base["dias_estada"], base["log_dias"], cifras["pct_prolongadas"], cifras["pct_dias_cama"]),
         "avance2_distribucion", True),
        (bivariado(base), "avance2_bivariado", True),
        (cramer(matriz_cramer(base)), "avance2_cramer", True),
        (edad(por_tramo), "avance2_edad", True),
        (forest(coef), "forest", True),
        (residuos(base["ajuste_ln"], base["residuo"]), "avance2_residuos", True),
        (normalidad(base), "anexo_normalidad", False),
        (cajas(base), "anexo_cajas", False),
        (prolongadas(pct), "anexo_prolongadas", False),
    ]
    for fig, nombre, png in figuras:
        guardar(fig, nombre, png)
        plt.close(fig)
        print("ok", nombre)


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    estilo()
    base = pd.read_parquet(RAIZ / "results/base_figuras.parquet")
    todas(base, json.loads((RAIZ / "results/cifras_avance2_v8.json").read_text()))
