"""Figura del artículo: señales para decidir qué revisa una persona (objetivo 1, corrida k4).

Lee <res>/senales_<corrida>/05_senales.csv (de tools/senales.py --corrida) y produce
  fig_senales.png / .pdf   A: AUC con IC 95 % (bootstrap)   B: curvas de esfuerzo
  fig_senales_tabla.csv    los números de la figura (AUC, IC, % detectado al 10/20/30 %)
Uso:  python3 tools/fig_senales.py Resultados_v4f/senales_Resultados_v4f_k4
"""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

CAT = {"nominal", "ordinal", "binary", "categorical"}
# nombre en la figura -> (columna, signo: +1 si más alto = más sospechoso, subconjunto)
SENALES = [
    ("Response length (baseline)", "S0_corta", 1, "all"),
    ("Embeddings, bge-m3*", "S4_margen", 1, "cat"),
    ("Token probabilities", "S2_margen", -1, "all"),
    ("Verified quotation", "S3_cita", -1, "all"),
    ("Atomic features", "S5_alarmas", 1, "all"),
    ("Code rules", "R", 1, "all"),
    ("Combined (cross-validated)", "comb", 1, "all"),
]
INK, MUTED, GRID, SURF = "#2b2a27", "#6b6a64", "#e6e5e0", "#fcfcfb"
COLOR = {"Combined (cross-validated)": "#2a78d6", "Code rules": "#1baf7a",
         "Atomic features": "#eb6834"}


def puntaje(d, col, signo):
    s = d[col] * signo
    return s.fillna(s.max()).to_numpy()


def curva(s, y):
    o = np.argsort(-s, kind="stable")
    x = np.arange(1, len(y) + 1) / len(y)
    return np.r_[0, x] * 100, np.r_[0, np.cumsum(y[o]) / y.sum()] * 100


def main():
    carpeta = sys.argv[1]
    d = pd.read_csv(os.path.join(carpeta, "05_senales.csv"))
    d["R"] = d.R1_numero_sin_banda + d.R2_opcion_anidada
    y_all = d.inestable.to_numpy()
    X = pd.DataFrame({c: d[c] * s for _, c, s, _ in SENALES if c not in ("comb",)})
    d["comb"] = cross_val_predict(
        make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression()),
        X.to_numpy(), y_all, cv=StratifiedKFold(5, shuffle=True, random_state=42),
        method="predict_proba")[:, 1]
    cat = d.question_type.isin(CAT) & d.S4_margen.notna()

    rng = np.random.default_rng(42)
    filas, puntajes = [], {}
    for nombre, col, signo, sub in SENALES:
        dd = d[cat] if sub == "cat" else d
        s, y = puntaje(dd, col, signo), dd.inestable.to_numpy()
        puntajes[nombre] = (s, y)
        boots = []
        for _ in range(2000):
            i = rng.integers(0, len(y), len(y))
            if 0 < y[i].sum() < len(i):
                boots.append(roc_auc_score(y[i], s[i]))
        x, c = curva(s, y)
        filas.append({"signal": nombre, "n": len(y), "positives": int(y.sum()),
                      "auc": roc_auc_score(y, s), "ci_low": np.percentile(boots, 2.5),
                      "ci_high": np.percentile(boots, 97.5),
                      **{f"detected_at_{p}": float(np.interp(p, x, c)) for p in (10, 20, 30)}})
    t = pd.DataFrame(filas)
    t.to_csv(os.path.join(carpeta, "fig_senales_tabla.csv"), index=False, float_format="%.3f")
    print(t.round(2).to_string(index=False))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED,
                         "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                         "text.color": INK, "axes.spines.top": False,
                         "axes.spines.right": False})
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.5, 4.2), gridspec_kw={"width_ratios": [1, 1.15]})
    fig.patch.set_facecolor(SURF)
    for ax in (a, b):
        ax.set_facecolor(SURF)

    # A: AUC con IC
    yy = np.arange(len(t))[::-1]
    a.axvline(0.5, color=MUTED, lw=1, ls="--")
    a.text(0.495, -0.55, "chance", color=MUTED, ha="right", fontsize=8)
    a.hlines(yy, t.ci_low, t.ci_high, color="#b5b4ad", lw=2)
    a.scatter(t.auc, yy, s=36, color=INK, zorder=3, edgecolor=SURF, linewidth=1.5)
    for yi, r in zip(yy, t.itertuples()):
        a.text(r.ci_high + 0.012, yi, f"{r.auc:.2f}", va="center", fontsize=8, color=MUTED)
    a.set_yticks(yy, t.signal)
    a.set_xlim(0.3, 0.92)
    a.set_ylim(-0.8, len(t) - 0.5)
    a.set_xlabel("AUC for run-to-run instability (95% bootstrap CI)")
    a.grid(axis="x", color=GRID, lw=0.8)
    a.set_axisbelow(True)
    a.set_title("A", loc="left", fontweight="bold")

    # B: curvas de esfuerzo, las tres mejores
    b.plot([0, 100], [0, 100], color=MUTED, lw=1, ls="--")
    b.text(62, 55, "random review", color=MUTED, rotation=33, fontsize=8)
    marcas = []
    for nombre in ("Combined (cross-validated)", "Code rules", "Atomic features"):
        s, y = puntajes[nombre]
        x, c = curva(s, y)
        b.plot(x, c, color=COLOR[nombre], lw=2, label=nombre)
        yi = float(c[np.searchsorted(x, 20, side="right") - 1])
        b.scatter([20], [yi], s=40, color=COLOR[nombre], edgecolor=SURF, linewidth=2, zorder=3)
        marcas.append((yi, nombre))
    # etiquetas a la derecha del 20 %, separadas al menos 5 puntos
    ult = -99
    for yi, nombre in sorted(marcas):
        yt = max(yi, ult + 5)
        b.annotate(f"{yi:.0f}%", (20, yi), xytext=(23, yt), textcoords="data", fontsize=8,
                   color=INK, va="center")
        ult = yt
    b.axvline(20, color=GRID, lw=1)
    b.set_xlim(0, 100); b.set_ylim(0, 100)
    b.set_xlabel("Responses reviewed, most suspicious first (%)")
    b.set_ylabel("Unstable responses found (%)")
    b.grid(color=GRID, lw=0.8)
    b.set_axisbelow(True)
    b.legend(frameon=False, loc="lower right", fontsize=8)
    b.set_title("B", loc="left", fontweight="bold")

    n, pos = int(t.n.iloc[0]), int(t.positives.iloc[0])
    fig.text(0.01, -0.02, f"n = {n} responses, {pos} unstable across four runs. Signals computed "
             f"from a single run. *Categorical questions only (n = {int(t.n.iloc[1])}).",
             fontsize=7.5, color=MUTED)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(carpeta, f"fig_senales.{ext}"), dpi=200, bbox_inches="tight",
                    facecolor=SURF)


if __name__ == "__main__":
    main()
