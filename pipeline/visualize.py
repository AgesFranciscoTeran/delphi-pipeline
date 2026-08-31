"""
Paso 6 — figuras (v2, Fase 0: fig1–fig4).

Cambios respecto a la v1:
  * Las etiquetas de consenso y de convergencia se leen de los CSV de consensus_metrics.py
    (un solo criterio; antes fig1 y fig2 usaban criterios distintos y contradecían la tabla).
  * n visible en todas partes (clasificadas/total, numéricas/total). Con 7–10 panelistas cada
    persona mueve 10–14 puntos y el lector tiene que verlo.
  * Colores consistentes por opción (mismo texto = mismo color en todas las filas). La v1
    coloreaba por índice: azul era "Yes" en unas filas y "No" en otras.
  * Un solo denominador (clasificadas) en la barra y en la etiqueta; el "sin clasificar" va en
    el texto de la fila.
  * fig4 facetada por unidad (estudiantes vs horas/día vs horas/semana), mediana e IQR, IDs
    para distinguir preguntas con el mismo texto.
  * fig5–fig7 se retiran hasta la capa de argumentos v2.
"""
import os
import json
import textwrap
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from config import *
from taxonomy import get_taxonomy

plt.rcParams.update({
    "font.family": "serif", "font.size": 11, "axes.titlesize": 13,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 120, "savefig.dpi": 300, "savefig.bbox": "tight",
})

CAT_CSV = os.path.join(OUTPUT_DIR, "03_categorical_consensus.csv")
QUANT_CSV = os.path.join(OUTPUT_DIR, "03_quantitative_consensus.csv")
CONV_CSV = os.path.join(OUTPUT_DIR, "03_convergence.csv")

CONV_COLORS = {
    "Convergió": "#1D9E75", "Se dispersó": "#E84855",
    "Estable en acuerdo": "#3B7DD8", "Estable sin acuerdo": "#8A8A8A", "Insuficiente": "#C8C8C8",
}
FIXED_OPTION_COLORS = {
    "Yes": "#2E8B57", "No": "#C0392B", "Depends": "#E0A100", "Balanced": "#E0A100",
    "Unclassified": "#D9D9D9",
}
PALETTE = list(matplotlib.colormaps["tab20"].colors)


def option_palette(cat_df):
    """Un color por texto de opción, estable en toda la figura."""
    colors = dict(FIXED_OPTION_COLORS)
    i = 0
    for _, r in cat_df.iterrows():
        for opt in json.loads(r["option_counts"]).keys():
            if opt not in colors:
                colors[opt] = PALETTE[i % len(PALETTE)]
                i += 1
    return colors


def wrap(s, width):
    return "\n".join(textwrap.wrap(str(s), width=width))


def load_conv():
    if not os.path.exists(CONV_CSV):
        return {}
    conv = pd.read_csv(CONV_CSV)
    return {(r["question_id"]): r["convergence"] for _, r in conv.iterrows()}


# ── fig1: concentración por ronda ─────────────────────────────────────────────

def fig1_concentration_trajectory():
    if not os.path.exists(CAT_CSV):
        print("  skip fig1"); return
    df = pd.read_csv(CAT_CSV)
    conv = load_conv()
    qids = df.drop_duplicates("question_id")[["question_id", COL_QUESTION_TEXT]]
    n = len(qids); ncols = 3; nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(14, 2.9 * nrows))
    axes = np.array(axes).flatten()

    for ax, (_, qrow) in zip(axes, qids.iterrows()):
        qid = qrow["question_id"]
        sub = df[df["question_id"] == qid].sort_values(COL_ROUND)
        rounds = sub[COL_ROUND].to_numpy()
        shares = sub["modal_share"].to_numpy() * 100
        ok = (sub["consensus_label"] != "Insuficiente").to_numpy()
        color = CONV_COLORS.get(conv.get(qid, "Insuficiente"), "#C8C8C8")

        ax.plot(rounds, shares, "-", color=color, lw=2, zorder=2)
        ax.scatter(rounds[ok], shares[ok], s=55, color=color, zorder=3)
        ax.scatter(rounds[~ok], shares[~ok], s=55, facecolors="white", edgecolors=color, lw=1.5, zorder=3)
        ax.axhline(STRONG_AGREEMENT * 100, ls=":", color="#999", lw=0.8)
        ax.axhline(CLEAR_MAJORITY * 100, ls=":", color="#CCC", lw=0.8)

        last = sub.iloc[-1]
        if last["consensus_label"] != "Insuficiente" and pd.notna(last["modal_option"]):
            txt = f"{last['consensus_label']}: {last['modal_option']}"
        else:
            txt = f"Insuficiente (n={int(last['n_classified'])}/{int(last['n_responses'])})"
        ax.text(0.02, 0.97, wrap(txt, 38), transform=ax.transAxes, fontsize=6.5,
                va="top", ha="left", color=color, zorder=5,
                bbox=dict(facecolor="white", alpha=0.75, edgecolor="none", pad=1.5))

        ax.set_xticks(rounds)
        ax.set_xticklabels([f"R{r}\n{int(c)}/{int(t)}" for r, c, t in
                            zip(rounds, sub["n_classified"], sub["n_responses"])], fontsize=7)
        ax.set_ylim(0, 112); ax.set_yticks([0, 50, 75, 100]); ax.tick_params(labelsize=7)
        ax.set_title(f"{qid} · " + wrap(qrow[COL_QUESTION_TEXT], 42), fontsize=8)

    for ax in axes[n:]:
        ax.axis("off")
    handles = [mpatches.Patch(color=c, label=k) for k, c in CONV_COLORS.items()]
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=9, bbox_to_anchor=(0.5, -0.005))
    fig.suptitle("Concentración del panel por pregunta a través de las rondas\n"
                 "(% de respuestas clasificadas en la opción más votada; bajo cada ronda: clasificadas/total; "
                 "punto hueco = cobertura insuficiente)", fontsize=12, y=1.0)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "fig1_concentration_trajectory.png"))
    plt.close(fig); print("  fig1_concentration_trajectory.png")


# ── fig2: dispersión inicial vs final ─────────────────────────────────────────

def fig2_convergence_scatter():
    if not os.path.exists(CONV_CSV):
        print("  skip fig2"); return
    conv = pd.read_csv(CONV_CSV)
    pts = conv[(conv["type"] == "categorical") & (conv["convergence"] != "Insuficiente")].copy()
    pts = pts.dropna(subset=["initial", "final"]).reset_index(drop=True)
    if pts.empty:
        print("  skip fig2"); return
    pts["num"] = np.arange(1, len(pts) + 1)
    rng = np.random.default_rng(42)
    pts["jx"], pts["jy"] = pts["initial"].copy(), pts["final"].copy()
    for _, g in pts.groupby([pts["initial"].round(2), pts["final"].round(2)]):
        if len(g) > 1:
            for idx in g.index:
                pts.loc[idx, "jx"] += rng.uniform(-0.03, 0.03)
                pts.loc[idx, "jy"] += rng.uniform(-0.03, 0.03)

    fig, ax = plt.subplots(figsize=(12.5, 7))
    lim = 1.08
    ax.plot([0, lim], [0, lim], "--", color="gray", lw=1)
    for cls, g in pts.groupby("convergence"):
        ax.scatter(g["jx"], g["jy"], s=190, color=CONV_COLORS.get(cls, "#999"), alpha=0.8,
                   label=cls, zorder=3)
    for _, r in pts.iterrows():
        ax.text(r["jx"], r["jy"], str(int(r["num"])), ha="center", va="center", fontsize=8,
                fontweight="bold", color="white", zorder=4)
    ax.set_xlim(-0.06, lim); ax.set_ylim(-0.06, lim)
    ax.set_xlabel("Dispersión de opciones — ronda inicial")
    ax.set_ylabel("Dispersión de opciones — ronda final")
    ax.set_title("Convergencia del consenso por pregunta\n(puntos bajo la diagonal = el panel se concentró)")
    ax.legend(fontsize=9, loc="upper left")
    fig.text(0.02, 0.01, "Métrica: entropía normalizada por el número de opciones de la taxonomía "
             "(0 = acuerdo total, 1 = todas las opciones por igual). Cambios menores a "
             f"±{ENTROPY_DELTA} se consideran estables. Puntos coincidentes desplazados levemente.",
             fontsize=7.5, color="gray", style="italic")
    fig.subplots_adjust(right=0.56, bottom=0.12)
    n = len(pts)
    for i, (_, r) in enumerate(pts.iterrows()):
        y_pos = 0.92 - 0.84 * (i / max(n - 1, 1))
        fig.text(0.58, y_pos, f"{int(r['num'])}.  {r['question_id']} · {r[COL_QUESTION_TEXT]}",
                 fontsize=8.5, va="center", family="serif")
    fig.savefig(os.path.join(FIGURES_DIR, "fig2_convergence_scatter.png"))
    plt.close(fig); print("  fig2_convergence_scatter.png")


# ── fig3: resultado categórico (ronda final) ─────────────────────────────────

def fig3_final_categorical():
    if not os.path.exists(CAT_CSV):
        print("  skip fig3"); return
    df = pd.read_csv(CAT_CSV)
    ext = pd.read_csv(os.path.join(OUTPUT_DIR, "02_extracted.csv"))
    cat_map = ext.drop_duplicates([COL_PANEL, COL_QUESTION]).set_index([COL_PANEL, COL_QUESTION])[COL_CATEGORY]
    final = df.loc[df.groupby("question_id")[COL_ROUND].idxmax()].copy()
    final[COL_CATEGORY] = [cat_map.get((p, q), "") for p, q in zip(final[COL_PANEL], final[COL_QUESTION])]
    final = final.sort_values([COL_CATEGORY, "modal_share"], ascending=[True, False]).reset_index(drop=True)
    colors = option_palette(df)

    # una fila vacía por categoría (cabecera), para que el nombre no choque con las etiquetas
    rows, prev_cat = [], None
    for _, r in final.iterrows():
        if r[COL_CATEGORY] != prev_cat:
            rows.append(("header", r[COL_CATEGORY])); prev_cat = r[COL_CATEGORY]
        rows.append(("row", r))
    y_all = np.arange(len(rows))[::-1]
    fig, ax = plt.subplots(figsize=(15, max(4, 0.55 * len(rows))))
    ticks, ticklabels = [], []
    for yi, (kind, item) in zip(y_all, rows):
        if kind == "header":
            ax.text(0, yi, item, transform=ax.get_yaxis_transform(), fontsize=8.5,
                    fontweight="bold", color="#555", style="italic", va="center", ha="left")
            continue
        r = item
        counts = json.loads(r["option_counts"])
        n_cls = r["n_classified"]
        left = 0.0
        if r["consensus_label"] == "Insuficiente":
            ax.barh(yi, 100, color="#EFEFEF", height=0.65, hatch="///", edgecolor="#BBBBBB", lw=0.5)
        else:
            for opt, c in sorted(counts.items(), key=lambda kv: -kv[1]):
                if c == 0:
                    continue
                pct = c / n_cls * 100
                ax.barh(yi, pct, left=left, color=colors.get(opt, "#999"), height=0.65)
                if pct >= 14:
                    lines = textwrap.wrap(opt, 16)
                    label = "\n".join(lines[:2]) + ("…" if len(lines) > 2 else "")
                    ax.text(left + pct / 2, yi, label, va="center", ha="center",
                            fontsize=6.2, color="white", linespacing=0.9)
                left += pct
        verdict = (f"{r['consensus_label']}: {r['modal_option']}" if r["consensus_label"] != "Insuficiente"
                   else f"Insuficiente ({int(n_cls)} clasificadas de {int(r['n_responses'])})")
        ax.text(102, yi, wrap(verdict, 48), va="center", fontsize=8, clip_on=False)
        ticks.append(yi)
        ticklabels.append(f"{r['question_id']} · {wrap(r[COL_QUESTION_TEXT], 60)}\n"
                          f"n = {int(n_cls)} clasificadas / {int(r['n_responses'])} respuestas")

    ax.set_yticks(ticks); ax.set_yticklabels(ticklabels, fontsize=7.5)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_xlim(0, 100); ax.set_xticks([0, 25, 50, 75, 100])
    ax.axvline(STRONG_AGREEMENT * 100, ls=":", color="#999", lw=0.8)
    ax.axvline(CLEAR_MAJORITY * 100, ls=":", color="#CCC", lw=0.8)
    ax.set_xlabel("% de las respuestas clasificadas (ronda final)")
    ax.set_title("Resultado del consenso por pregunta — preguntas categóricas", fontsize=13)
    fig.subplots_adjust(left=0.36, right=0.78)
    fig.savefig(os.path.join(FIGURES_DIR, "fig3_final_categorical.png"))
    plt.close(fig); print("  fig3_final_categorical.png")


# ── fig4: resultado cuantitativo (ronda final), facetado por unidad ──────────

def fig4_final_quantitative():
    if not os.path.exists(QUANT_CSV):
        print("  skip fig4"); return
    df = pd.read_csv(QUANT_CSV)
    final = df.loc[df.groupby("question_id")[COL_ROUND].idxmax()].copy()
    final = final[final["median"].notna()]
    if final.empty:
        print("  skip fig4"); return
    order = ["students", "semesters", "years", "hours/day", "hours/week", "hours/module", "hours/semester"]
    present = list(final["question_unit"].fillna("?").unique())
    units = [u for u in order if u in present] + [u for u in present if u not in order]
    heights = [0.5 * (final["question_unit"].fillna("?") == u).sum() + 0.45 for u in units]
    fig, axes = plt.subplots(len(units), 1, figsize=(12, sum(heights) + 1.2),
                             gridspec_kw={"height_ratios": heights})
    axes = np.atleast_1d(axes)
    label_colors = {"Consenso fuerte": "#1D9E75", "Convergencia moderada": "#E0A100",
                    "Sin consenso": "#E84855", "Insuficiente": "#B0B0B0"}
    for ax, unit in zip(axes, units):
        sub = final[final["question_unit"].fillna("?") == unit].sort_values("median").reset_index(drop=True)
        y = np.arange(len(sub))[::-1]
        for yi, (_, r) in zip(y, sub.iterrows()):
            c = label_colors.get(r["consensus_label"], "#999")
            ax.plot([r["min"], r["max"]], [yi, yi], color=c, lw=1, alpha=0.5)
            ax.plot([r["q1"], r["q3"]], [yi, yi], color=c, lw=6, alpha=0.85, solid_capstyle="butt")
            ax.plot(r["median"], yi, "o", color="white", mec=c, mew=2, ms=8, zorder=3)
            extra = f", {int(r['n_other_unit'])} en otra unidad" if r["n_other_unit"] else ""
            ax.text(1.01, yi, f"mediana {r['median']:.3g} · {r['consensus_label']} "
                              f"(n={int(r['n_numeric'])}/{int(r['n_responses'])}{extra})",
                    transform=ax.get_yaxis_transform(), va="center", fontsize=8, clip_on=False)
        ax.set_yticks(y)
        ax.set_yticklabels([f"{r['question_id']} · {wrap(r[COL_QUESTION_TEXT], 55)}" for _, r in sub.iterrows()],
                           fontsize=8)
        title = f"Unidad: {unit}" + ("  (asumida)" if bool(sub["unit_assumed"].iloc[0]) else "")
        ax.set_title(title, fontsize=9, loc="left", color="#555")
        ax.set_xlim(0, float(sub["max"].max()) * 1.15 + 1e-9)
        ax.set_ylim(-0.6, len(sub) - 0.4)
        ax.grid(axis="x", color="#EEE")
    axes[-1].set_xlabel("Valor (mediana, caja = IQR, línea fina = mín–máx; ronda final)")
    fig.suptitle("Resultado del consenso por pregunta — preguntas cuantitativas", fontsize=13)
    handles = [mpatches.Patch(color=c, label=k) for k, c in label_colors.items()]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=8.5, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.03, 0.72, 0.97))
    fig.savefig(os.path.join(FIGURES_DIR, "fig4_final_quantitative.png"))
    plt.close(fig); print("  fig4_final_quantitative.png")


def main():
    os.makedirs(FIGURES_DIR, exist_ok=True)
    print("\n═══ VISUALIZATIONS v2 ═════════════════════════════\n")
    print("Capa 1 — Proceso:")
    fig1_concentration_trajectory()
    fig2_convergence_scatter()
    print("Capa 2 — Resultados:")
    fig3_final_categorical()
    fig4_final_quantitative()
    print("Capa 3 — Argumentos: fig5–fig7 retiradas hasta la capa de argumentos v2 (ver diagnóstico).")
    print(f"\nFiguras guardadas en {FIGURES_DIR}/\n")


if __name__ == "__main__":
    main()
