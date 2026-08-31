# -*- coding: utf-8 -*-
"""
Figuras del sitio y del artículo, generadas desde Resultados/*.csv.

Salida en SVG: escala sin pixelarse, el texto sigue siendo texto (buscable y seleccionable) y
pesa menos que un PNG a 300 dpi. Las mismas funciones guardan PNG a 300 dpi para el manuscrito.

Criterios de diseño aplicados en todas:
  * un solo eje por figura (nunca dos escalas verticales),
  * color por entidad y no por posición: una opción conserva su color aunque cambie de orden,
  * el n siempre visible — con paneles de 7 a 10 personas, un porcentaje sin n engaña,
  * rejilla y ejes recesivos, etiquetas directas en vez de leyendas cuando caben.
"""
import os
import math
import itertools
import collections

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import networkx as nx

import datos

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figuras")

# Paleta divergente validada para daltonismo (ΔE CVD 8.4, visión normal 18.1).
AZUL, GRIS, ROJO = "#2a78d6", "#8a8880", "#e34948"
TINTA, TINTA2, TINTA3 = "#0b0b0b", "#52514e", "#84827c"
LINEA, PANEL = "#e5e3dd", "#ffffff"
# Escala categórica para opciones: orden fijo, nunca ciclada.
CATEG = ["#2a78d6", "#e34948", "#8a8880", "#1b9e77", "#8b5cf6", "#d97706", "#0891b2"]

plt.rcParams.update({
    "figure.facecolor": PANEL, "axes.facecolor": PANEL,
    "savefig.facecolor": PANEL, "savefig.bbox": "tight", "savefig.dpi": 300,
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial", "sans-serif"],
    "font.size": 9, "axes.titlesize": 10.5, "axes.labelsize": 9,
    "axes.edgecolor": LINEA, "axes.linewidth": .8, "axes.labelcolor": TINTA2,
    "xtick.color": TINTA3, "ytick.color": TINTA3,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "svg.fonttype": "none",          # el texto queda como texto en el SVG
    "axes.spines.top": False, "axes.spines.right": False,
})


def _guardar(fig, nombre, png=False):
    os.makedirs(SALIDA, exist_ok=True)
    ruta = os.path.join(SALIDA, nombre + ".svg")
    fig.savefig(ruta, format="svg", transparent=False)
    if png:
        fig.savefig(os.path.join(SALIDA, nombre + ".png"))
    plt.close(fig)
    return ruta


def inline(ruta):
    """Devuelve el SVG listo para incrustar: sin cabecera XML y con ancho fluido."""
    with open(ruta, encoding="utf-8") as f:
        s = f.read()
    s = s[s.index("<svg"):]
    s = s.replace('width="', 'data-w="', 1).replace('height="', 'data-h="', 1)
    return s.replace("<svg ", '<svg style="width:100%;height:auto" ', 1)


def _paleta_opciones(opciones):
    return {o: CATEG[i % len(CATEG)] for i, o in enumerate(opciones)}


def _corta(s, n=26):
    s = str(s)
    return s if len(s) <= n else s[:n - 1] + "…"


# ── 1. Flujo de opiniones entre rondas (aluvial) ──────────────────────────────

def _cinta(ax, x0, x1, y0a, y0b, y1a, y1b, color, alpha):
    """Cinta entre dos bandas, con bordes en curva de Bézier."""
    dx = (x1 - x0) * .5
    verts = [(x0, y0a), (x0 + dx, y0a), (x1 - dx, y1a), (x1, y1a),
             (x1, y1b), (x1 - dx, y1b), (x0 + dx, y0b), (x0, y0b), (x0, y0a)]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
             Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), facecolor=color, edgecolor="none",
                           alpha=alpha, zorder=1))


def fig_flujo(qids, png=False, nombre="fig_flujo"):
    """
    Aluvial: cómo se reparten los panelistas entre opciones en cada ronda y quién se mueve.
    Cada cinta es un grupo de panelistas; el color es su opción DE ORIGEN, así que se puede
    seguir a dónde fue cada bloque inicial. Las cintas de quien no se mueve van más tenues.
    """
    d = datos.clasificadas()
    qids = [q for q in qids if q in set(d.qid)]
    n = len(qids)
    fig, axes = plt.subplots(1, n, figsize=(6.8 * n, 3.9))
    axes = np.atleast_1d(axes)

    for ax, q in zip(axes, qids):
        g = d[d.qid == q]
        rondas = sorted(g.Round.unique())
        piv = g.pivot_table(index="Panelist", columns="Round",
                            values="selected_option", aggfunc="first")
        piv = piv.reindex(columns=rondas)
        opciones = sorted({v for c in rondas for v in piv[c].dropna().unique()})
        pal = _paleta_opciones(opciones)

        # posición vertical de cada banda por ronda
        bandas, GAP = {}, .06
        for r in rondas:
            cuenta = piv[r].value_counts()
            total = cuenta.sum()
            if not total:
                continue
            y = 0.0
            for o in opciones:
                c = cuenta.get(o, 0)
                if not c:
                    continue
                h = c / total * (1 - GAP * max(0, len(cuenta) - 1))
                bandas[(r, o)] = (y, y + h, c)
                y += h + GAP

        SEP = 2.6
        for i, (r0, r1) in enumerate(zip(rondas, rondas[1:])):
            sub = piv[[r0, r1]].dropna()
            flujos = collections.Counter(zip(sub[r0], sub[r1]))
            desde = collections.defaultdict(float)
            hacia = collections.defaultdict(float)
            for (o0, o1), c in sorted(flujos.items(), key=lambda kv: (opciones.index(kv[0][0]),
                                                                     opciones.index(kv[0][1]))):
                if (r0, o0) not in bandas or (r1, o1) not in bandas:
                    continue
                b0, b1 = bandas[(r0, o0)], bandas[(r1, o1)]
                h0 = (b0[1] - b0[0]) * c / b0[2]
                h1 = (b1[1] - b1[0]) * c / b1[2]
                y0 = b0[0] + desde[o0]
                y1 = b1[0] + hacia[o1]
                _cinta(ax, i * SEP + .16, (i + 1) * SEP - .16, y0, y0 + h0, y1, y1 + h1,
                       pal[o0], .60 if o0 != o1 else .22)
                desde[o0] += h0
                hacia[o1] += h1

        for j, r in enumerate(rondas):
            for o in opciones:
                if (r, o) not in bandas:
                    continue
                y0, y1, c = bandas[(r, o)]
                ax.add_patch(plt.Rectangle((j * SEP - .16, y0), .32, y1 - y0,
                                           facecolor=pal[o], edgecolor=PANEL,
                                           linewidth=1.2, zorder=3))
                if y1 - y0 > .07:
                    ax.text(j * SEP, (y0 + y1) / 2, str(c), ha="center", va="center",
                            color="white", fontsize=8.5, fontweight="bold", zorder=4)
                if j == 0:
                    ax.text(-.32, (y0 + y1) / 2, _corta(o, 19), ha="right", va="center",
                            fontsize=8, color=TINTA2, zorder=4)
                elif j == len(rondas) - 1:
                    ax.text(j * SEP + .32, (y0 + y1) / 2, _corta(o, 19), ha="left", va="center",
                            fontsize=8, color=TINTA2, zorder=4)

        seguidos = piv.dropna(subset=[rondas[0], rondas[-1]])
        movidos = int((seguidos[rondas[0]] != seguidos[rondas[-1]]).sum())
        ax.set_title(f"{q} — {_corta(datos.texto(q), 44)}\n"
                     f"{movidos} de {len(seguidos)} cambian de opción entre la 1.ª y la 3.ª",
                     fontsize=9.5, color=TINTA, loc="left", pad=10)
        ax.set_xticks([j * SEP for j in range(len(rondas))])
        ax.set_xticklabels([f"Ronda {r}" for r in rondas])
        ax.set_xlim(-2.0, (len(rondas) - 1) * SEP + 2.0)
        ax.set_ylim(-.04, 1.06)
        ax.set_yticks([])
        for s in ("left", "bottom"):
            ax.spines[s].set_visible(False)
        ax.tick_params(length=0)

    fig.tight_layout()
    return _guardar(fig, nombre, png)


# ── 2. Red de panelistas por ronda ────────────────────────────────────────────

def _acuerdos(piv, min_comun=3):
    out = {}
    for a, b in itertools.combinations(piv.index, 2):
        amb = piv.loc[a].notna() & piv.loc[b].notna()
        if amb.sum() < min_comun:
            continue
        out[(a, b)] = float((piv.loc[a][amb] == piv.loc[b][amb]).mean())
    return out


def fig_red(panel, png=False, umbral=.50, fuerte=.75):
    """
    Nodos = panelistas, aristas = cuánto coinciden en esa ronda.

    El layout se calcula UNA vez sobre el grafo acumulado de las tres rondas y se reutiliza:
    si se recalculara por ronda, el lector vería moverse los nodos y atribuiría al panel un
    cambio que en realidad es del algoritmo de dibujo. Es el error más común de estas figuras.
    El tamaño del nodo es su número de vínculos fuertes en esa ronda.
    """
    d = datos.clasificadas()
    g = d[d.Panel == panel]
    rondas = sorted(g.Round.unique())
    panelistas = sorted(g.Panelist.unique())

    pivs, acs = {}, {}
    for r in rondas:
        p = g[g.Round == r].pivot_table(index="Panelist", columns="qid",
                                        values="selected_option", aggfunc="first")
        pivs[r] = p.reindex(panelistas)
        acs[r] = _acuerdos(pivs[r])

    G = nx.Graph()
    G.add_nodes_from(panelistas)
    acum = collections.defaultdict(list)
    for r in rondas:
        for par, v in acs[r].items():
            acum[par].append(v)
    # El layout usa TODOS los pares con su peso, no sólo los que superan el umbral: si se
    # filtrara, un panel con poco acuerdo daría un grafo casi vacío y spring_layout colapsaría
    # los nodos unos sobre otros. El umbral es sólo para decidir qué aristas se DIBUJAN.
    for (a, b), vs in acum.items():
        G.add_edge(a, b, weight=max(sum(vs) / len(vs), 1e-3))
    pos = nx.spring_layout(G, weight="weight", seed=7, k=2.2 / math.sqrt(len(panelistas)),
                           iterations=600)

    fig, axes = plt.subplots(1, len(rondas), figsize=(3.05 * len(rondas), 3.35))
    axes = np.atleast_1d(axes)
    for ax, r in zip(axes, rondas):
        ac = acs[r]
        grado = collections.Counter()
        for (a, b), v in ac.items():
            if v >= fuerte:
                grado[a] += 1
                grado[b] += 1
        for (a, b), v in sorted(ac.items(), key=lambda kv: kv[1]):
            if v < umbral:
                continue
            es_f = v >= fuerte
            ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]],
                    color=AZUL, lw=2.2 if es_f else 1.0,
                    alpha=.85 if es_f else .28, zorder=1, solid_capstyle="round")
        for p in panelistas:
            x, y = pos[p]
            s = 120 + 46 * grado.get(p, 0)
            ax.scatter([x], [y], s=s, facecolor=PANEL, edgecolor=GRIS,
                       linewidth=1.1, zorder=3)
            ax.text(x, y, str(p)[-2:], ha="center", va="center",
                    fontsize=7.2, color=TINTA2, zorder=4)
        vals = list(ac.values())
        medio = sum(vals) / len(vals) if vals else 0
        ax.set_title(f"Ronda {r}", fontsize=9.5, color=TINTA, pad=6)
        ax.text(.5, -.06, f"acuerdo medio {medio:.2f}".replace(".", ","),
                transform=ax.transAxes, ha="center", va="top",
                fontsize=8.5, color=TINTA3)
        ax.set_axis_off()
        ax.margins(.20)
    fig.tight_layout()
    return _guardar(fig, f"fig_red_panel{panel}", png)


# ── 3. Trayectoria del consenso por pregunta ──────────────────────────────────

def fig_trayectoria(png=False):
    """
    Cuánto se concentra el panel en su opción mayoritaria, ronda a ronda.

    Un panel por clase de evolución en vez de las 20 preguntas en un solo eje: veinte líneas
    cruzándose son ilegibles y las etiquetas se pisan. Cada faceta muestra sus preguntas en
    color y el resto en gris de fondo, así que se mantiene la referencia sin el enredo.
    """
    c = pd.read_csv(datos._ruta("03_categorical_consensus.csv"))
    c["qid"] = [datos.qid(p_, q) for p_, q in zip(c.Panel, c.Question)]
    conv = datos.convergencia().set_index("qid")["convergence"].to_dict()

    CLASES = [("Convergió", AZUL), ("Se dispersó", ROJO),
              ("Estable en acuerdo", "#1b9e77"), ("Estable sin acuerdo", GRIS)]
    series = {}
    for q, g in c.groupby("qid"):
        g = g.sort_values("Round")
        if g.modal_share.isna().all():
            continue
        series[q] = (list(g.Round), list(g.modal_share * 100))

    rondas = sorted(c.Round.unique())
    fig, axes = plt.subplots(1, len(CLASES), figsize=(3.5 * len(CLASES), 4.0), sharey=True)

    for ax, (clase, col) in zip(np.atleast_1d(axes), CLASES):
        for q, (xs, ys) in series.items():          # fondo: todas, muy tenues
            ax.plot(xs, ys, color=LINEA, lw=1.0, zorder=1)
        propias = [q for q in series if conv.get(q) == clase]
        finales = []
        for q in propias:
            xs, ys = series[q]
            ax.plot(xs, ys, color=col, lw=1.9, marker="o", markersize=4.6,
                    markerfacecolor=PANEL, markeredgewidth=1.5, markeredgecolor=col, zorder=3)
            finales.append((ys[-1], q))
        # etiquetas al final, separadas para que no se pisen
        finales.sort()
        ultimo = -99
        for y, q in finales:
            yy = max(y, ultimo + 4.6)
            ax.annotate(q, (rondas[-1], yy), xytext=(7, 0), textcoords="offset points",
                        fontsize=7.4, color=TINTA2, va="center",
                        xycoords="data", annotation_clip=False)
            ultimo = yy
        for y in (75, 60):
            ax.axhline(y, color=LINEA, lw=1, zorder=0)
        ax.set_title(f"{clase}  ({len(propias)})", fontsize=9.5, color=col, pad=8)
        ax.set_xticks(rondas)
        ax.set_xticklabels([f"R{r}" for r in rondas])
        ax.set_xlim(rondas[0] - .12, rondas[-1] + .72)
        ax.set_ylim(20, 106)
        ax.grid(axis="y", color=LINEA, lw=.6, zorder=0)
        ax.set_axisbelow(True)
        ax.spines["left"].set_visible(False)
        ax.tick_params(length=0)

    a0 = np.atleast_1d(axes)[0]
    a0.set_ylabel("Panelistas en la opción mayoritaria (%)")
    fig.tight_layout()
    return _guardar(fig, "fig_trayectoria", png)


# ── 4. Movimiento frente a convergencia ───────────────────────────────────────

def fig_movimiento(png=False):
    """
    Un punto por panel: cuánto se mueve su gente (eje x) contra cuánto se acerca entre sí
    (eje y, cambio del acuerdo medio entre la primera ronda y la última). Si moverse llevara
    a acordar, los puntos subirían hacia la derecha. Van al revés.
    """
    _, por_panel = datos.movimiento()
    d = datos.clasificadas()
    fig, ax = plt.subplots(figsize=(6.4, 4.5))

    xs, ys = [], []
    for panel in sorted(d.Panel.unique()):
        g = d[d.Panel == panel]
        rondas = sorted(g.Round.unique())
        panelistas = sorted(g.Panelist.unique())
        medios = []
        for r in rondas:
            p = g[g.Round == r].pivot_table(index="Panelist", columns="qid",
                                            values="selected_option", aggfunc="first")
            v = list(_acuerdos(p.reindex(panelistas)).values())
            medios.append(sum(v) / len(v) if v else 0)
        x = por_panel[int(panel)]["pct"]
        y = (medios[-1] - medios[0]) * 100
        xs.append(x)
        ys.append(y)
        col = AZUL if y > 5 else (ROJO if y < -5 else GRIS)
        ax.scatter([x], [y], s=190, color=col, zorder=3, alpha=.9)
        ax.annotate(f"Panel {panel}\n{len(panelistas)} personas",
                    (x, y), xytext=(0, -30), textcoords="offset points",
                    ha="center", fontsize=8.4, color=TINTA2)

    if len(xs) > 2:
        m, b = np.polyfit(xs, ys, 1)
        xx = np.linspace(min(xs) - 4, max(xs) + 4, 10)
        ax.plot(xx, m * xx + b, color=LINEA, lw=1.4, ls=(0, (5, 4)), zorder=1)
        ax.text(.98, .97, "Con 4 paneles esto es una señal, no una correlación medible",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=8.2, color=TINTA3, style="italic")

    ax.axhline(0, color=LINEA, lw=1.2, zorder=0)
    ax.set_xlabel("Respuestas que cambian de opción entre la primera y la última ronda (%)")
    ax.set_ylabel("Cambio del acuerdo\nmedio del panel (puntos)")
    ax.grid(axis="y", color=LINEA, lw=.7, zorder=0)
    ax.set_axisbelow(True)
    ax.margins(x=.20, y=.34)
    fig.tight_layout()
    return _guardar(fig, "fig_movimiento", png)


def construir_todo(png=False):
    d = datos.clasificadas()
    mov = (d.pivot_table(index=["qid", "Panelist"], columns="Round",
                         values="selected_option", aggfunc="first"))
    ri, rf = min(mov.columns), max(mov.columns)
    mov = mov.dropna(subset=[ri, rf])
    top = (mov.assign(c=mov[ri] != mov[rf]).groupby("qid").c.sum()
           .sort_values(ascending=False))
    elegidas = list(top.head(3).index)

    salida = {"flujos": [(q, fig_flujo([q], png, f"fig_flujo_{q}")) for q in elegidas],
              "flujo_qids": elegidas,
              "trayectoria": fig_trayectoria(png), "movimiento": fig_movimiento(png),
              "redes": {int(p): fig_red(int(p), png) for p in sorted(d.Panel.unique())}}
    return salida


if __name__ == "__main__":
    import sys
    r = construir_todo(png="--png" in sys.argv)
    print("Figuras generadas en", SALIDA + "/")
    for k, v in r.items():
        print(" ", k, v if not isinstance(v, dict) else list(v.values()))
