# -*- coding: utf-8 -*-
"""
Figuras del sitio y del artículo, generadas desde Resultados/*.csv.

Salida en SVG: escala sin pixelarse, el texto sigue siendo texto (buscable y seleccionable) y
pesa menos que un PNG a 300 dpi. Las mismas funciones guardan PNG a 300 dpi para el manuscrito.

Criterios de diseño aplicados en todas:
  * un solo eje por figura (nunca dos escalas verticales),
  * color por entidad y no por posición: una opción conserva su color aunque cambie de orden,
  * el color nunca va solo: cada marca lleva además un símbolo, una letra o una etiqueta,
  * el n siempre visible — con paneles de 7 a 10 personas, un porcentaje sin n engaña,
  * rejilla y ejes recesivos, etiquetas directas en vez de leyendas cuando caben.

Paleta (16-10-2026), validada con el script de la guía de visualización (validate_palette.js,
modo claro, superficie #fcfcfb). Cada color hace un solo trabajo:
  * postura — polaridad: azul (a favor) / gris neutro (condicional) / rojo (en contra);
  * resultado — 4 categorías en el orden fijo de la paleta (adyacentes: ΔE daltonismo 9.1,
    visión normal 22.9);
  * opciones de una pregunta — sólo 3 colores, porque en la cuadrícula cualquier par puede
    quedar al lado (todos los pares: ΔE 9.2 / 24.0); el resto va en gris como «otras».
El agua y el amarillo quedan por debajo de 3:1 sobre el fondo: por eso toda marca lleva texto.
"""
import os
import html
import textwrap
import collections

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch

import datos

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figuras")

AZUL, GRIS, ROJO = "#2a78d6", "#898781", "#e34948"          # postura
CATEG3 = ["#2a78d6", "#eb6834", "#1baf7a"]                   # opciones (A, B, C)
OTRAS = "#c3c2b7"
COL_RESULTADO = {"Consenso": "#2a78d6", "Consenso no consolidado": "#eb6834",
                 "Disenso estable": "#1baf7a", "Sin estabilizar": "#eda100",
                 "Insuficiente": "#c3c2b7"}
TINTA, TINTA2, TINTA3 = "#0b0b0b", "#52514e", "#898781"
LINEA, PANEL, VACIO = "#e1e0d9", "#ffffff", "#f4f2ee"

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


def _corta(s, n=26):
    s = str(s)
    return s if len(s) <= n else s[:n - 1] + "…"


def _envuelve(s, ancho=22, lineas=3):
    partes = textwrap.wrap(str(s), ancho) or [""]
    if len(partes) > lineas:
        partes = partes[:lineas]
        partes[-1] = _corta(partes[-1], ancho)
    return "\n".join(partes)


def _tinta_sobre(color):
    """Texto negro o blanco según la luminancia del relleno."""
    r, g, b = (int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lin = [c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4 for c in (r, g, b)]
    lum = .2126 * lin[0] + .7152 * lin[1] + .0722 * lin[2]
    return TINTA if lum > .3 else "white"


# ── esquema de color por pregunta ─────────────────────────────────────────────

ORDEN_POSTURA = ["A favor", "Condicional", "En contra", "Sin postura"]
COL_POSTURA = dict(zip(ORDEN_POSTURA, (AZUL, GRIS, ROJO, OTRAS)))
MARCA_POSTURA = {"A favor": "✓", "Condicional": "~", "En contra": "✕", "Sin postura": "·"}


def esquema(q, valores):
    """Cómo se pinta una pregunta: (categoría(opción), {cat: color}, orden, {cat: marca}).

    En las preguntas de sí / no la categoría es la postura (criterio 1.2: el consenso se mide
    sobre ella), con los mismos colores en todas. En las demás, cada opción elegida lleva su
    letra (A, B, C… en el orden de la taxonomía), pero sólo las tres más elegidas llevan color:
    con más de tres colores en contacto, dos se confunden con daltonismo. Las demás van en gris
    y se distinguen por la letra.
    """
    from stance_map import STANCE_MAP, STANCE_ES, stance_of
    if q in STANCE_MAP:
        def cat(o):
            if not isinstance(o, str) or o in datos.SIN_OPCION:
                return None
            return STANCE_ES.get(stance_of(q, o)[0]) or "Sin postura"
        return cat, COL_POSTURA, ORDEN_POSTURA, MARCA_POSTURA
    from taxonomy import EMILY_TAXONOMY
    tax = EMILY_TAXONOMY.get(q, {}).get("options", [])
    pos = {o: i for i, o in enumerate(tax)}
    cuenta = collections.Counter(v for v in valores
                                 if isinstance(v, str) and v not in datos.SIN_OPCION)
    top = set(sorted(cuenta, key=lambda o: (-cuenta[o], pos.get(o, 99)))[:3])
    orden = sorted(cuenta, key=lambda o: pos.get(o, 99))
    colores = iter(CATEG3)
    pal = {o: (next(colores) if o in top else OTRAS) for o in orden}
    marcas = {o: chr(ord("A") + i) for i, o in enumerate(orden)}

    def cat(o):
        if not isinstance(o, str) or o in datos.SIN_OPCION:
            return None
        return o
    return cat, pal, orden, marcas


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
    Aluvial: cómo se reparten los panelistas entre categorías en cada ronda y quién se mueve.
    Cada cinta es un grupo de panelistas; el color es su categoría DE ORIGEN, así que se puede
    seguir a dónde fue cada bloque inicial. Las cintas de quien no se mueve van más tenues.
    En las preguntas de sí / no las categorías son las posturas.
    """
    d = datos.clasificadas()
    qids = [q for q in qids if q in set(d.qid)]
    n = len(qids)
    fig, axes = plt.subplots(1, n, figsize=(7.2 * n, 4.1))
    axes = np.atleast_1d(axes)

    for ax, q in zip(axes, qids):
        g = d[d.qid == q]
        cat, pal, orden, marcas = esquema(q, g.selected_option)
        g = g.assign(cat=g.selected_option.map(cat))
        rondas = sorted(g.Round.unique())
        piv = g.pivot_table(index="Panelist", columns="Round", values="cat", aggfunc="first")
        piv = piv.reindex(columns=rondas)
        cats = [c for c in orden if any((piv[r] == c).any() for r in rondas)]

        bandas, GAP = {}, .06
        for r in rondas:
            cuenta = piv[r].value_counts()
            total = cuenta.sum()
            if not total:
                continue
            y = 0.0
            for c_ in cats:
                k = cuenta.get(c_, 0)
                if not k:
                    continue
                h = k / total * (1 - GAP * max(0, len(cuenta) - 1))
                bandas[(r, c_)] = (y, y + h, k)
                y += h + GAP

        SEP = 2.6
        for i, (r0, r1) in enumerate(zip(rondas, rondas[1:])):
            sub = piv[[r0, r1]].dropna()
            flujos = collections.Counter(zip(sub[r0], sub[r1]))
            desde = collections.defaultdict(float)
            hacia = collections.defaultdict(float)
            for (o0, o1), k in sorted(flujos.items(), key=lambda kv: (cats.index(kv[0][0]),
                                                                     cats.index(kv[0][1]))):
                if (r0, o0) not in bandas or (r1, o1) not in bandas:
                    continue
                b0, b1 = bandas[(r0, o0)], bandas[(r1, o1)]
                h0 = (b0[1] - b0[0]) * k / b0[2]
                h1 = (b1[1] - b1[0]) * k / b1[2]
                y0 = b0[0] + desde[o0]
                y1 = b1[0] + hacia[o1]
                _cinta(ax, i * SEP + .16, (i + 1) * SEP - .16, y0, y0 + h0, y1, y1 + h1,
                       pal[o0], .60 if o0 != o1 else .22)
                desde[o0] += h0
                hacia[o1] += h1

        for j, r in enumerate(rondas):
            for c_ in cats:
                if (r, c_) not in bandas:
                    continue
                y0, y1, k = bandas[(r, c_)]
                ax.add_patch(plt.Rectangle((j * SEP - .16, y0), .32, y1 - y0,
                                           facecolor=pal[c_], edgecolor=PANEL,
                                           linewidth=1.5, zorder=3))
                if y1 - y0 > .07:
                    ax.text(j * SEP, (y0 + y1) / 2, str(k), ha="center", va="center",
                            color=_tinta_sobre(pal[c_]), fontsize=8.5, fontweight="bold",
                            zorder=4)
                etiqueta = f"{marcas[c_]}  {_envuelve(c_, 24)}" if c_ in marcas else _envuelve(c_, 24)
                if j == 0:
                    ax.text(-.32, (y0 + y1) / 2, etiqueta, ha="right", va="center",
                            fontsize=7.8, color=TINTA2, zorder=4, linespacing=1.15)
                elif j == len(rondas) - 1:
                    ax.text(j * SEP + .32, (y0 + y1) / 2, etiqueta, ha="left", va="center",
                            fontsize=7.8, color=TINTA2, zorder=4, linespacing=1.15)

        seguidos = piv.dropna(subset=[rondas[0], rondas[-1]])
        movidos = int((seguidos[rondas[0]] != seguidos[rondas[-1]]).sum())
        que = "de postura" if pal is COL_POSTURA else "de opción"
        ax.set_title(f"{q} — {_corta(datos.texto(q), 60)}\n"
                     f"{movidos} de {len(seguidos)} cambian {que} entre la 1.ª y la "
                     f"{rondas[-1]}.ª ronda", fontsize=9.5, color=TINTA, loc="left", pad=10)
        ax.set_xticks([j * SEP for j in range(len(rondas))])
        ax.set_xticklabels([f"Ronda {r}" for r in rondas])
        ax.set_xlim(-2.5, (len(rondas) - 1) * SEP + 2.5)
        ax.set_ylim(-.04, 1.06)
        ax.set_yticks([])
        for s in ("left", "bottom"):
            ax.spines[s].set_visible(False)
        ax.tick_params(length=0)

    fig.tight_layout()
    return _guardar(fig, nombre, png)


# ── 2. Cuadrícula panelista × pregunta ────────────────────────────────────────

def _preguntas_cat(panel):
    d = datos.cargar_extraidas()
    g = d[(d.Panel == panel) & d.is_valid_response &
          d.question_type.isin(["nominal", "binary"])]
    preguntas = sorted(g.qid.unique(), key=lambda q: int(q.split("_Q")[1]))
    return g, preguntas


def _es_postura(q):
    from stance_map import STANCE_MAP
    return q in STANCE_MAP


def _orden_filas(g, preguntas, esq, ronda):
    """Panelistas ordenados por parecido en la ronda final, sobre TODAS las preguntas de opción
    del panel: así las dos cuadrículas comparten el orden de filas."""
    panelistas = sorted(g.Panelist.unique())
    ref = g[g.Round == ronda].pivot_table(index="Panelist", columns="qid",
                                          values="cat", aggfunc="first")
    ref = ref.reindex(index=panelistas, columns=preguntas)
    orden, restantes = [], list(panelistas)
    actual = restantes.pop(0)
    orden.append(actual)
    while restantes:
        def parecido(p_):
            amb = ref.loc[actual].notna() & ref.loc[p_].notna()
            return (ref.loc[actual][amb] == ref.loc[p_][amb]).sum() if amb.any() else -1
        actual = max(restantes, key=parecido)
        restantes.remove(actual)
        orden.append(actual)
    return orden


def fig_cuadricula(panel, png=False):
    """
    Quién respondió qué, panelista por panelista y pregunta por pregunta, en cada ronda.

    Sustituye a la red de acuerdo entre panelistas que había antes, que promediaba el acuerdo
    sobre 2 a 5 preguntas por par. Esto no promedia nada: se ve en QUÉ preguntas coincide cada
    grupo y en cuáles se parte, y las respuestas sin clasificar quedan como huecos.

    Son DOS figuras con el mismo orden de filas: una para las preguntas de sí / no (postura:
    azul ✓ a favor, rojo ✕ en contra, gris ~ condicional) y otra para las de opciones (tres
    colores + letra). En una sola, el azul significaba «a favor» en unas columnas y «opción A»
    en otras; y cinco colores juntos no se distinguen con daltonismo, así que no hay paleta que
    lo resuelva dentro de una figura.

    Devuelve {"postura": ruta o None, "opciones": ruta o None}.
    """
    g, preguntas = _preguntas_cat(panel)
    rondas = sorted(g.Round.unique())
    esq = {q: esquema(q, g[g.qid == q].selected_option) for q in preguntas}
    g = g.assign(cat=[esq[q][0](o) for q, o in zip(g.qid, g.selected_option)])
    orden = _orden_filas(g, preguntas, esq, rondas[-1])
    salida = {}
    for tipo, qs in (("postura", [q for q in preguntas if _es_postura(q)]),
                     ("opciones", [q for q in preguntas if not _es_postura(q)])):
        salida[tipo] = (_cuadricula(g, qs, esq, orden, rondas,
                                    f"fig_cuadricula_{tipo}_panel{panel}", png) if qs else None)
    return salida


def _cuadricula(g, preguntas, esq, orden, rondas, nombre, png):
    ancho = max(1.9, .52 * len(preguntas) + .3)
    fig, axes = plt.subplots(1, len(rondas), figsize=(ancho * len(rondas) + 1.4,
                                                      0.42 * len(orden) + 1.9),
                             sharey=True)
    axes = np.atleast_1d(axes)
    from config import OFF_TOPIC_LABEL
    for ax, r in zip(axes, rondas):
        gr = g[g.Round == r]
        piv = gr.pivot_table(index="Panelist", columns="qid", values="cat", aggfunc="first")
        piv = piv.reindex(index=orden, columns=preguntas)
        # la opción cruda distingue por qué falta la categoría
        crudo = gr.pivot_table(index="Panelist", columns="qid", values="selected_option",
                               aggfunc="first").reindex(index=orden, columns=preguntas)
        for i, p_ in enumerate(orden):
            for j, q in enumerate(preguntas):
                v = piv.loc[p_, q]
                _, pal, _, marcas = esq[q]
                if pd.isna(v):
                    o = crudo.loc[p_, q]
                    # sin respuesta: celda vacía; fuera de tema: FT; respondió pero no se pudo
                    # clasificar (ninguna opción encaja, o las corridas no forman mayoría): ?
                    marca = ("" if not isinstance(o, str) else
                             "FT" if o == OFF_TOPIC_LABEL else "?")
                    ax.add_patch(plt.Rectangle((j + .06, i + .06), .88, .88, facecolor=VACIO,
                                               edgecolor="#d9d6cf" if marca else PANEL,
                                               linewidth=1.0 if marca else 1.4))
                    if marca:
                        ax.text(j + .5, i + .52, marca, ha="center", va="center",
                                fontsize=7.5, color=TINTA2, fontweight="bold")
                    continue
                col = pal.get(v, OTRAS)
                ax.add_patch(plt.Rectangle((j + .06, i + .06), .88, .88, facecolor=col,
                                           edgecolor=PANEL, linewidth=1.4))
                ax.text(j + .5, i + .52, marcas.get(v, "·"), ha="center", va="center",
                        fontsize=8.5, color=_tinta_sobre(col), fontweight="bold")
        ax.set_xlim(0, len(preguntas)); ax.set_ylim(len(orden), 0)
        ax.set_xticks([j + .5 for j in range(len(preguntas))])
        ax.set_xticklabels([q.split("_")[1] for q in preguntas], fontsize=8)
        ax.set_yticks([i + .5 for i in range(len(orden))])
        ax.set_yticklabels([str(p_) for p_ in orden], fontsize=8)
        ax.set_title(f"Ronda {r}", fontsize=9.5, color=TINTA, pad=8)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(length=0)
    axes[0].set_ylabel("Panelista", fontsize=8.5)
    fig.tight_layout()
    return _guardar(fig, nombre, png)


def leyenda_opciones(panel):
    """Leyenda HTML de la cuadrícula de opciones: qué letra es qué opción, por pregunta."""
    g, preguntas = _preguntas_cat(panel)
    bloques = []
    for q in [q for q in preguntas if not _es_postura(q)]:
        cat, pal, orden, marcas = esquema(q, g[g.qid == q].selected_option)
        usados = {cat(o) for o in g[g.qid == q].selected_option} - {None}
        chips = "".join(
            f'<span class="chip"><i style="background:{pal[c]}"></i>'
            f'<b>{marcas[c]}</b> {html.escape(_corta(c, 38))}</span>'
            for c in orden if c in usados)
        bloques.append(f'<div class="legq"><b>{q.split("_")[1]}</b> '
                       f'<span class="legqt">{html.escape(_corta(datos.texto(q), 52))}</span>'
                       f'{chips}</div>')
    return '<div class="leygrid">' + "".join(bloques) + "</div>"


# ── 3. Trayectoria del acuerdo por pregunta ───────────────────────────────────

def fig_trayectoria(panel, png=False):
    """
    Cuánto se concentra el panel en su postura u opción mayoritaria, ronda a ronda, para las
    preguntas de ESTE panel. Una línea por pregunta, con su id al final y coloreada según su
    resultado. El último tramo va punteado si no es estable (cambio neto > 15 %).

    Las líneas se separan levemente en horizontal para que dos preguntas con los mismos
    valores no se tapen, y cada etiqueta se une a su punto.
    """
    import json as _json
    from config import CONSENSUS_THRESHOLD, AGREEMENT_LEVELS
    cv = datos.convergencia()
    cv = cv[(cv.Panel == panel) & (cv.type == "categorical")].sort_values("qid")
    rondas = sorted({int(r) for s in cv.rounds for r in _json.loads(s)})
    fig, ax = plt.subplots(figsize=(6.6, 4.0))

    k = len(cv)
    finales = []
    for i, (_, fila) in enumerate(cv.iterrows()):
        sh = {int(r): v for r, v in _json.loads(fila.shares).items() if v is not None}
        if not sh:
            continue
        xs = sorted(sh)
        dx = (i - (k - 1) / 2) * .035
        col = COL_RESULTADO.get(fila.resultado, OTRAS)
        ys = [sh[x] * 100 for x in xs]
        xx = [x + dx for x in xs]
        inestable = fila.stable is False or str(fila.stable) == "False"
        for a in range(len(xx) - 1):
            ultimo = a == len(xx) - 2
            ax.plot(xx[a:a + 2], ys[a:a + 2], color=col, lw=2.0, zorder=3,
                    ls=(0, (3, 2)) if (ultimo and inestable) else "-")
        ax.scatter(xx, ys, s=34, color=PANEL, edgecolor=col, linewidth=1.8, zorder=4)
        if xs[-1] == rondas[-1]:
            finales.append([ys[-1], xx[-1], fila.qid, col])

    # etiquetas a la derecha, separadas al menos 5,5 puntos y unidas a su punto
    finales.sort()
    pos = []
    for y, _, _, _ in finales:
        pos.append(max(y, pos[-1] + 5.5) if pos else y)
    for (y, x, q, col), yy in zip(finales, pos):
        xe = rondas[-1] + .22
        ax.plot([x + .03, xe - .03], [y, yy], color=LINEA, lw=.8, zorder=2)
        ax.text(xe, yy, q, fontsize=8, color=TINTA2, va="center")

    ax.axhline(CONSENSUS_THRESHOLD * 100, color=TINTA3, lw=1.0, ls=(0, (4, 3)), zorder=1)
    ax.text(rondas[0] - .12, CONSENSUS_THRESHOLD * 100 + 1.5, "acuerdo alto · 70 %",
            fontsize=7.4, color=TINTA2, ha="left")
    for nombre, u in AGREEMENT_LEVELS[1:]:
        ax.axhline(u * 100, color=LINEA, lw=.9, ls=(0, (1, 2)), zorder=1)
        ax.text(rondas[0] - .12, u * 100 + 1.5, nombre.replace("Acuerdo ", "") +
                f" · {int(u * 100)} %", fontsize=7.2, color=TINTA3, ha="left")

    ax.set_xticks(rondas)
    ax.set_xticklabels([f"Ronda {r}" for r in rondas])
    ax.set_xlim(rondas[0] - .15, rondas[-1] + .6)
    ax.set_ylim(0, 106)
    # Es un porcentaje del panel, no un conteo: con paneles de 7 a 10 personas, un eje que
    # llega a «100» sin el signo se leía como cien panelistas.
    ax.set_yticks(range(0, 101, 20))
    ax.set_yticklabels([f"{v} %" for v in range(0, 101, 20)])
    ax.set_ylabel("% del panel en la postura u opción mayoritaria")
    ax.grid(axis="y", color=LINEA, lw=.5, zorder=0, alpha=.6)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    ax.tick_params(length=0)
    usadas = set(cv.resultado)
    manijas = [plt.Line2D([], [], color=v, lw=2.2, label=k_) for k_, v in COL_RESULTADO.items()
               if k_ in usadas]
    if any(str(s) == "False" for s in cv.stable):
        manijas.append(plt.Line2D([], [], color=TINTA3, lw=2.0, ls=(0, (3, 2)),
                                  label="último tramo no estable (> 15 %)"))
    if manijas:
        ax.legend(handles=manijas, frameon=False, fontsize=8, ncol=2,
                  loc="upper center", bbox_to_anchor=(.5, -.1))
    fig.tight_layout()
    return _guardar(fig, f"fig_trayectoria_panel{panel}", png)


# ── 4. Árbol de la taxonomía (pregunta → postura → calificador) ───────────────

def fig_arbol(panel, png=False):
    """
    La taxonomía de cada pregunta de opción y cómo la usó el panel en la ronda final.

    Pregunta → postura → calificadores en las de sí / no; pregunta → opciones en las demás.
    La barra es cuántos panelistas eligieron cada hoja en la ronda final, sobre los
    clasificados. Las hojas que nadie eligió también salen (en gris y con 0): muestran qué
    parte de la taxonomía usó el panel y cuál no.
    """
    from stance_map import STANCE_MAP, STANCE_ES
    from taxonomy import EMILY_TAXONOMY
    from config import OFF_TOPIC_OPTION
    d = datos.clasificadas()
    d = d[d.Panel == panel]
    _, preguntas = _preguntas_cat(panel)
    res = {r.qid: r for _, r in datos.convergencia().iterrows()}

    filas = []           # (tipo, nivel, texto, n, total, color, extra)
    for q in preguntas:
        g = d[d.qid == q]
        if g.empty:
            continue
        fin = g[g.Round == g.Round.max()]
        cuenta = collections.Counter(fin.selected_option)
        total = sum(cuenta.values())
        opciones = [o for o in EMILY_TAXONOMY[q].get("options", []) if o != OFF_TOPIC_OPTION]
        rr = res.get(q)
        filas.append(("pregunta", 0, f"{q}  {datos.texto(q)}", total, total, None,
                      rr.resultado if rr is not None else ""))
        if q in STANCE_MAP:
            grupos = collections.OrderedDict((p, []) for p in ORDEN_POSTURA)
            for o in opciones:
                st, calif = STANCE_MAP[q].get(o, (None, None))
                grupos[STANCE_ES.get(st) or "Sin postura"].append((calif or (o if not st else "(sin matiz)"), o))
            for p, hojas in grupos.items():
                if not hojas:
                    continue
                n_p = sum(cuenta.get(o, 0) for _, o in hojas)
                filas.append(("postura", 1, p, n_p, total, COL_POSTURA[p], ""))
                for texto, o in hojas:
                    filas.append(("hoja", 2, texto, cuenta.get(o, 0), total, COL_POSTURA[p], ""))
        else:
            _, pal, _, _ = esquema(q, g.selected_option)
            for o in opciones:
                filas.append(("hoja", 1, o, cuenta.get(o, 0), total, pal.get(o, OTRAS), ""))
        filas.append(("espacio", 0, "", 0, 0, None, ""))

    alto = .23
    fig, ax = plt.subplots(figsize=(7.4, max(2.5, len(filas) * alto + .4)))
    X_TXT, X_BAR, ANCHO = (0, .32, .64), 5.1, 2.2
    y = 0
    padre = {}
    for tipo, nivel, texto, n, total, col, extra in filas:
        if tipo == "espacio":
            y += .6
            continue
        x = X_TXT[nivel]
        if nivel > 0 and padre.get(nivel - 1) is not None:     # conector en codo
            xp = X_TXT[nivel - 1] + .12
            ax.plot([xp, xp, x - .06], [padre[nivel - 1] + .25, y, y], color=LINEA, lw=.9,
                    zorder=1)
        if tipo == "pregunta":
            ax.text(x, y, _corta(texto, 82), fontsize=8.6, color=TINTA, fontweight="bold",
                    va="center")
            if extra:
                ax.add_patch(plt.Rectangle((X_BAR + ANCHO + .02, y - .17), .16, .34,
                                           facecolor=COL_RESULTADO.get(extra, OTRAS),
                                           edgecolor="none"))
                ax.text(X_BAR + ANCHO + .24, y, extra, fontsize=7.8, color=TINTA2, va="center")
            padre = {0: y}
        elif tipo == "postura":
            ax.text(x, y, MARCA_POSTURA[texto] + "  " + texto, fontsize=8.3, color=TINTA,
                    va="center")
            ax.text(X_BAR - .1, y, f"{n} de {total}", fontsize=7.8, color=TINTA2,
                    va="center", ha="right")
            padre[1] = y
        else:
            usado = n > 0
            ax.text(x, y, _corta(texto, 60 if nivel == 2 else 64), fontsize=7.9,
                    color=TINTA2 if usado else TINTA3, va="center")
            if usado and total:
                ax.add_patch(plt.Rectangle((X_BAR, y - .16), ANCHO * n / total, .32,
                                           facecolor=col, edgecolor="none"))
            ax.text(X_BAR + (ANCHO * n / total if total and usado else 0) + .06, y, str(n),
                    fontsize=7.8, color=TINTA2 if usado else TINTA3, va="center")
        y += 1
    ax.set_xlim(0, X_BAR + ANCHO + 1.9)
    ax.set_ylim(y, -1)
    ax.axis("off")
    fig.tight_layout()
    return _guardar(fig, f"fig_arbol_panel{panel}", png)


# ── 5. Argumentos: por qué (taxonomía de Emily) ───────────────────────────────

def _argumentos(panel):
    """Respuestas del panel con su argumento (04_argumentos.csv), o None si no existe."""
    p = os.path.join(datos.RUTA_RESULTADOS, "04_argumentos.csv")
    if not os.path.exists(p):
        return None
    a = pd.read_csv(p)
    return a[a.Panel == panel]


def fig_argumentos(panel, png=False):
    """
    Por qué responde el panel lo que responde: de la postura (u opción) de cada panelista en la
    ronda final al argumento que da, en la taxonomía de Emily. Cada cinta son panelistas.
    Los argumentos van en gris neutro y con su nombre: el color queda para la postura.
    """
    from argumentos import ARGUMENTOS, NINGUNO
    a = _argumentos(panel)
    if a is None or a.empty:
        return None
    orden_arg = list(ARGUMENTOS) + [NINGUNO]
    preguntas = sorted(a.question_id.unique(), key=lambda q: int(q.split("_Q")[1]))
    alto = []
    bloques = []
    for q in preguntas:
        g = a[a.question_id == q]
        fin = g[g.Round == g.Round.max()]
        cat, pal, orden, marcas = esquema(q, g.selected_option)
        pares = collections.Counter((cat(o), arg) for o, arg in zip(fin.selected_option, fin.argumento))
        pares = {k: v for k, v in pares.items() if k[0] is not None}
        if not pares:
            continue
        izq = [c for c in orden if any(a_ == c for a_, _ in pares)]
        der = [x for x in orden_arg if any(b == x for _, b in pares)]
        bloques.append((q, pares, izq, der, pal, marcas))
        alto.append(max(len(izq), len(der)))
    if not bloques:
        return None
    fig, axes = plt.subplots(len(bloques), 1, figsize=(7.6, sum(.42 * h + 1.0 for h in alto)),
                             gridspec_kw={"height_ratios": [.42 * h + 1.0 for h in alto]})
    axes = np.atleast_1d(axes)
    GAP = .06
    for ax, (q, pares, izq, der, pal, marcas) in zip(axes, bloques):
        total = sum(pares.values())

        def apilar(claves, lado):
            pos, y = {}, 0.0
            for k in claves:
                n = sum(v for (x, b), v in pares.items() if (x if lado == 0 else b) == k)
                h = n / total * (1 - GAP * (len(claves) - 1))
                pos[k] = [y, y + h, n, 0.0]
                y += h + GAP
            return pos
        pi, pd_ = apilar(izq, 0), apilar(der, 1)
        for (x, b), n in sorted(pares.items(), key=lambda kv: (izq.index(kv[0][0]), der.index(kv[0][1]))):
            h0 = (pi[x][1] - pi[x][0]) * n / pi[x][2]
            h1 = (pd_[b][1] - pd_[b][0]) * n / pd_[b][2]
            y0, y1 = pi[x][0] + pi[x][3], pd_[b][0] + pd_[b][3]
            _cinta(ax, .12, 1.88, y0, y0 + h0, y1, y1 + h1, pal.get(x, OTRAS), .5)
            pi[x][3] += h0
            pd_[b][3] += h1
        for k, (y0, y1, n, _) in pi.items():
            ax.add_patch(plt.Rectangle((0, y0), .12, y1 - y0, facecolor=pal.get(k, OTRAS),
                                       edgecolor=PANEL, lw=1.5))
            ax.text(-.06, (y0 + y1) / 2, f"{marcas.get(k, '')}  {_corta(k, 30)}  ({n})",
                    ha="right", va="center", fontsize=7.8, color=TINTA2)
        for k, (y0, y1, n, _) in pd_.items():
            ax.add_patch(plt.Rectangle((1.88, y0), .12, y1 - y0, facecolor=OTRAS,
                                       edgecolor=PANEL, lw=1.5))
            ax.text(2.08, (y0 + y1) / 2, f"{_envuelve(k, 30, 2)}  ({n})", ha="left",
                    va="center", fontsize=7.8, color=TINTA2 if k != "Sin argumento" else TINTA3,
                    linespacing=1.1)
        ax.set_title(f"{q} — {_corta(datos.texto(q), 66)}   (ronda final, n = {total})",
                     fontsize=8.8, color=TINTA, loc="left")
        ax.set_xlim(-2.1, 4.2)
        ax.set_ylim(1.03, -.04)
        ax.axis("off")
    fig.tight_layout()
    return _guardar(fig, f"fig_argumentos_panel{panel}", png)


def fig_grafo(panel, png=False):
    """
    Grafo de ontología del panel: cada pregunta·postura (ronda final) unida a los perfiles de
    argumento de Emily que la sostienen. A diferencia del árbol y de los grafos por pregunta,
    aquí los perfiles se COMPARTEN: un mismo argumento puede sostener posturas de preguntas
    distintas, y eso es lo que el grafo deja ver. No se junta con otros paneles: son estudios
    independientes.

    Nodo izquierdo: tamaño = panelistas en esa postura u opción; color = postura (o la opción en
    las preguntas que no son de sí / no). Nodo derecho: perfil. Arista: panelistas que dan esa
    razón para esa postura. «Sin argumento» no se dibuja; queda en la etiqueta de cada nodo.
    Orden: perfiles por peso total; posturas por baricentro de sus perfiles (menos cruces).
    """
    from argumentos import ARGUMENTOS, NINGUNO
    a = _argumentos(panel)
    if a is None or a.empty:
        return None
    fin = a[a.Round == a.groupby("question_id").Round.transform("max")]
    nodos, aristas = {}, collections.Counter()
    for q, g in fin.groupby("question_id"):
        cat, pal, _, marcas = esquema(q, a[a.question_id == q].selected_option)
        for o, arg in zip(g.selected_option, g.argumento):
            c = cat(o)
            if c is None:
                continue
            k = (q, c)
            # color sólo para la postura: las opciones van en gris con su letra y su nombre
            # (en un mismo grafo, el azul de «opción A» se confundiría con «a favor»)
            n = nodos.setdefault(k, {"n": 0, "sin": 0,
                                     "col": pal.get(c, OTRAS) if pal is COL_POSTURA else OTRAS,
                                     "marca": marcas.get(c, "")})
            n["n"] += 1
            if arg == NINGUNO or not isinstance(arg, str):
                n["sin"] += 1
            else:
                aristas[(k, arg)] += 1
    if not aristas:
        return None
    peso = collections.Counter()
    for (_, arg), w in aristas.items():
        peso[arg] += w
    perfiles = sorted(peso, key=lambda x: -peso[x])
    ydch = {x: i for i, x in enumerate(perfiles)}
    def baricentro(k):
        ws = [(ydch[arg], w) for (kk, arg), w in aristas.items() if kk == k]
        return sum(y * w for y, w in ws) / sum(w for _, w in ws) if ws else len(perfiles)
    izq = sorted(nodos, key=lambda k: (baricentro(k), k))
    H = max(len(izq), len(perfiles))
    yi = {k: i * (H - 1) / max(1, len(izq) - 1) for i, k in enumerate(izq)}
    yd = {x: i * (H - 1) / max(1, len(perfiles) - 1) for i, x in enumerate(perfiles)}

    fig, ax = plt.subplots(figsize=(8.2, .36 * H + 1.0))
    XI, XD = 0.0, 4.0
    wmax = max(aristas.values())
    for (k, arg), w in sorted(aristas.items(), key=lambda kv: kv[1]):
        y0, y1 = yi[k], yd[arg]
        xs = np.linspace(XI, XD, 40)
        t_ = (xs - XI) / (XD - XI)
        ys = y0 + (y1 - y0) * (3 * t_ ** 2 - 2 * t_ ** 3)       # curva suave
        ax.plot(xs, ys, color=nodos[k]["col"], lw=1.2 + 5.5 * w / wmax, alpha=.45,
                solid_capstyle="butt", zorder=1)
    nmax = max(v["n"] for v in nodos.values())
    for k in izq:
        v = nodos[k]
        ax.scatter([XI], [yi[k]], s=40 + 260 * v["n"] / nmax, color=v["col"], edgecolor=PANEL,
                   linewidth=1.5, zorder=3)
        nombre = k[1] if k[1] in ("A favor", "En contra", "Condicional", "Sin postura") else _corta(k[1], 28)
        extra = f", {v['sin']} sin arg." if v["sin"] else ""
        ax.text(XI - .14, yi[k], f"{k[0]}  {v['marca']} {nombre}  ({v['n']}{extra})",
                ha="right", va="center", fontsize=7.6, color=TINTA2)
    pmax = max(peso.values())
    for x in perfiles:
        ax.scatter([XD], [yd[x]], s=40 + 260 * peso[x] / pmax, color=TINTA2, edgecolor=PANEL,
                   linewidth=1.5, zorder=3, marker="s")
        ax.text(XD + .3, yd[x], f"{x}  ({peso[x]})", ha="left", va="center", fontsize=8,
                color=TINTA)
    ax.text(XI, -1.1, "Pregunta · postura (ronda final)", ha="center", fontsize=8, color=TINTA3)
    ax.text(XD, -1.1, "Perfil de argumento (Emily)", ha="center", fontsize=8, color=TINTA3)
    ax.set_xlim(XI - 3.6, XD + 3.4)
    ax.set_ylim(H - .3, -1.6)
    ax.axis("off")
    fig.tight_layout()
    return _guardar(fig, f"fig_grafo_panel{panel}", png)


def fig_perfiles(panel, png=False):
    """Qué argumentos predominan en el panel: respuestas de la ronda final por argumento."""
    from argumentos import ARGUMENTOS, NINGUNO
    a = _argumentos(panel)
    if a is None or a.empty:
        return None
    fin = a[a.Round == a.groupby("question_id").Round.transform("max")]
    cuenta = fin.argumento.value_counts()
    orden = [x for x in list(ARGUMENTOS) + [NINGUNO] if cuenta.get(x, 0)]
    orden.sort(key=lambda x: (x == NINGUNO, -cuenta[x]))
    fig, ax = plt.subplots(figsize=(6.8, .34 * len(orden) + .7))
    total = cuenta.sum()
    for i, x in enumerate(orden):
        n = int(cuenta[x])
        ax.barh(i, n, height=.62, color=AZUL if x != NINGUNO else OTRAS)
        ax.text(n + total * .01, i, f"{n}  ({n / total * 100:.0f} %)", va="center",
                fontsize=8, color=TINTA2)
    ax.set_yticks(range(len(orden)))
    ax.set_yticklabels(orden, fontsize=8.2)
    ax.invert_yaxis()
    ax.set_xticks([])
    for s in ("left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    ax.set_xlim(0, cuenta.max() * 1.25)
    ax.set_title(f"Respuestas de la ronda final por argumento (n = {total}, todas las preguntas de opción)",
                 fontsize=8.8, color=TINTA, loc="left")
    fig.tight_layout()
    return _guardar(fig, f"fig_perfiles_panel{panel}", png)


# ── 6. Hacia dónde se mueve la gente ─────────────────────────────────────────

TIPOS_MOV = ["Hacia la mayoría", "Otro cambio", "Se alejó de la mayoría", "Se mantuvo"]
COL_MOV = {"Hacia la mayoría": AZUL, "Otro cambio": GRIS, "Se alejó de la mayoría": "#eb6834",
           "Se mantuvo": LINEA}


def movimientos(panel):
    """Una fila por panelista × pregunta × par de rondas seguidas, con el tipo de movimiento.

    La referencia es la mayoría de la ronda ANTERIOR, que es lo que el panelista vio en la
    síntesis antes de volver a responder. Se compara la postura en las preguntas de sí / no y
    la opción en las demás (la misma base que el consenso). Si en la ronda anterior había empate
    en el primer puesto, «la mayoría» son todas las empatadas.
    """
    d = datos.clasificadas()
    d = d[d.Panel == panel]
    filas = []
    for q, g in d.groupby("qid"):
        cat, _, _, _ = esquema(q, g.selected_option)
        g = g.assign(c=g.selected_option.map(cat)).dropna(subset=["c"])
        piv = g.pivot_table(index="Panelist", columns="Round", values="c", aggfunc="first")
        rondas = sorted(piv.columns)
        for r0, r1 in zip(rondas, rondas[1:]):
            cuenta = piv[r0].value_counts()
            if cuenta.empty:
                continue
            mayoria = set(cuenta[cuenta == cuenta.max()].index)
            for p_ in piv.index:
                a, b = piv.loc[p_, r0], piv.loc[p_, r1]
                if pd.isna(a) or pd.isna(b):
                    continue
                if a == b:
                    tipo = "Se mantuvo"
                elif b in mayoria and a not in mayoria:
                    tipo = "Hacia la mayoría"
                elif a in mayoria and b not in mayoria:
                    tipo = "Se alejó de la mayoría"
                else:
                    tipo = "Otro cambio"
                filas.append({"qid": q, "transicion": f"Ronda {r0} → {r1}", "panelista": p_,
                              "tipo": tipo})
    return pd.DataFrame(filas)


def fig_movimiento(panel, png=False):
    """Barras apiladas por par de rondas: cómo se movieron los panelistas respecto de la mayoría."""
    m = movimientos(panel)
    if m.empty:
        return None
    trans = sorted(m.transicion.unique())
    fig, ax = plt.subplots(figsize=(7.2, .62 * len(trans) + 1.3))
    for i, t_ in enumerate(trans):
        sub_ = m[m.transicion == t_]
        total, x = len(sub_), 0
        for tipo in TIPOS_MOV:
            n = int((sub_.tipo == tipo).sum())
            if not n:
                continue
            ax.barh(i, n / total * 100, left=x, height=.56, color=COL_MOV[tipo],
                    edgecolor=PANEL, linewidth=2)
            if n / total > .035:
                ax.text(x + n / total * 50, i, str(n), ha="center", va="center", fontsize=8.5,
                        fontweight="bold", color=_tinta_sobre(COL_MOV[tipo]))
            x += n / total * 100
        cambian = int((sub_.tipo != "Se mantuvo").sum())
        hacia = int((sub_.tipo == "Hacia la mayoría").sum())
        ax.text(101.5, i, f"{cambian} de {total} cambian;\n{hacia} hacia la mayoría",
                va="center", fontsize=7.8, color=TINTA2)
    ax.set_yticks(range(len(trans)))
    ax.set_yticklabels(trans, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels([f"{v} %" for v in (0, 25, 50, 75, 100)])
    ax.set_xlabel("Respuestas (panelista × pregunta) entre dos rondas seguidas")
    for s_ in ("left",):
        ax.spines[s_].set_visible(False)
    ax.tick_params(length=0)
    manijas = [plt.Rectangle((0, 0), 1, 1, color=COL_MOV[t_]) for t_ in TIPOS_MOV]
    ax.legend(manijas, TIPOS_MOV, frameon=False, fontsize=8, ncol=4, loc="upper center",
              bbox_to_anchor=(.45, -.32 if len(trans) < 3 else -.22))
    fig.tight_layout()
    return _guardar(fig, f"fig_movimiento_panel{panel}", png)


# ── 7. Perfil de argumento de cada panelista ──────────────────────────────────

RAMPA = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"]   # azul 100→600


def fig_perfil_panelistas(panel, png=False):
    """
    Panelista × perfil de argumento: en cuántas preguntas (ronda final) cada panelista dio cada
    tipo de razón. Muestra si cada persona razona siempre desde el mismo lugar o cambia según
    la pregunta. Escala secuencial de un solo azul, con el número en cada celda.
    """
    from argumentos import ARGUMENTOS, NINGUNO
    a = _argumentos(panel)
    if a is None or a.empty:
        return None
    fin = a[a.Round == a.groupby("question_id").Round.transform("max")]
    cols = [x for x in list(ARGUMENTOS) + [NINGUNO] if (fin.argumento == x).any()]
    piv = (fin.assign(v=1).pivot_table(index="Panelist", columns="argumento", values="v",
                                        aggfunc="sum", fill_value=0).reindex(columns=cols, fill_value=0))
    reales = [c for c in cols if c != NINGUNO]
    piv = piv.loc[sorted(piv.index, key=lambda p_: (reales.index(piv.loc[p_, reales].idxmax())
                                                    if piv.loc[p_, reales].sum() else 99, p_))]
    fig, ax = plt.subplots(figsize=(.78 * len(cols) + 2.0, .4 * len(piv) + 2.2))
    for i, p_ in enumerate(piv.index):
        for j, c in enumerate(cols):
            n = int(piv.loc[p_, c])
            col = (VACIO if n == 0 else OTRAS if c == NINGUNO
                   else RAMPA[min(n, len(RAMPA)) - 1])
            ax.add_patch(plt.Rectangle((j + .05, i + .05), .9, .9, facecolor=col, edgecolor=PANEL))
            if n:
                ax.text(j + .5, i + .52, str(n), ha="center", va="center", fontsize=8,
                        color=_tinta_sobre(col), fontweight="bold")
    ax.set_xlim(0, len(cols)); ax.set_ylim(len(piv), 0)
    ax.set_xticks([j + .5 for j in range(len(cols))])
    ax.set_xticklabels([_envuelve(c, 14, 3) for c in cols], fontsize=7.4, rotation=0)
    ax.xaxis.tick_top()
    ax.set_yticks([i + .5 for i in range(len(piv))])
    ax.set_yticklabels([str(p_) for p_ in piv.index], fontsize=8)
    ax.set_ylabel("Panelista", fontsize=8.5)
    for s_ in ax.spines.values():
        s_.set_visible(False)
    ax.tick_params(length=0)
    fig.tight_layout()
    return _guardar(fig, f"fig_perfil_panelistas_panel{panel}", png)


# ── 8. Diagrama del método ────────────────────────────────────────────────────

def fig_metodo(png=False):
    """De la respuesta en texto libre a la conclusión por pregunta, con las cifras del estudio."""
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    from config import CONSENSUS_THRESHOLD, STABILITY_MAX_CHANGE
    ctx = datos.contexto()
    k = next((x.get("k_corridas") for x in reversed(datos.manifiesto())
              if x.get("step") == "consolidar"), 3)
    pasos = [
        ("Respuestas en texto libre", f"{ctx['n_validas']} válidas · {ctx['n_paneles']} paneles\n"
                                      f"{ctx['n_rondas']} rondas · {ctx['n_preguntas']} preguntas"),
        ("Taxonomía de la experta", "posturas, opciones, bandas\ny perfiles de argumento"),
        ("Clasificación automática", f"modelo de lenguaje en el\nservidor universitario,\n{k} corridas independientes"),
        ("Voto mayoritario", "sin mayoría entre corridas:\nsin clasificar"),
        ("Resultado por pregunta", f"acuerdo ≥ {int(CONSENSUS_THRESHOLD * 100)} %\n× estabilidad "
                                   f"≤ {int(STABILITY_MAX_CHANGE * 100)} %"),
    ]
    fig, ax = plt.subplots(figsize=(11.2, 2.9))
    W, H, GAP = 2.0, 1.25, .38
    for i, (titulo, det) in enumerate(pasos):
        x = i * (W + GAP)
        ax.add_patch(FancyBboxPatch((x, 0), W, H, boxstyle="round,pad=0.02,rounding_size=0.08",
                                    facecolor="#f4f7fc" if i != 1 else "#fdf6e7",
                                    edgecolor=AZUL if i != 1 else "#c9a227", linewidth=1.2))
        ax.text(x + W / 2, H - .24, titulo, ha="center", va="center", fontsize=8.6,
                fontweight="bold", color=TINTA)
        ax.text(x + W / 2, H / 2 - .12, det, ha="center", va="center", fontsize=7.6,
                color=TINTA2, linespacing=1.25)
        if i < len(pasos) - 1:
            ax.add_patch(FancyArrowPatch((x + W + .04, H / 2), (x + W + GAP - .04, H / 2),
                                         arrowstyle="-|>", mutation_scale=11, color=TINTA3, lw=1.2))
    # validación: debajo, contra la clasificación
    xv = 2 * (W + GAP)
    ax.add_patch(FancyBboxPatch((xv - .05, -1.15), W + .1, .72,
                                boxstyle="round,pad=0.02,rounding_size=0.08", facecolor=PANEL,
                                edgecolor=TINTA3, linewidth=1.0, linestyle=(0, (3, 2))))
    ax.text(xv + W / 2, -.79, "Validación contra personas\n(dos codificadores, en curso)",
            ha="center", va="center", fontsize=7.6, color=TINTA2, linespacing=1.25)
    ax.add_patch(FancyArrowPatch((xv + W / 2, -.43), (xv + W / 2, -.03), arrowstyle="-|>",
                                 mutation_scale=10, color=TINTA3, lw=1.0, linestyle=(0, (3, 2))))
    ax.text(1 * (W + GAP) + W / 2, -.32, "definida por Emily", ha="center", fontsize=7.2,
            color="#8a6d10")
    ax.set_xlim(-.1, len(pasos) * (W + GAP) - GAP + .1)
    ax.set_ylim(-1.3, H + .1)
    ax.axis("off")
    fig.tight_layout()
    return _guardar(fig, "fig_metodo", png)


def construir_todo(png=False):
    """Genera las figuras de cada panel por separado. No hay figuras entre paneles."""
    d = datos.clasificadas()
    salida = {}
    for panel in sorted(d.Panel.unique()):
        panel = int(panel)
        g = d[d.Panel == panel]
        mov = g.pivot_table(index=["qid", "Panelist"], columns="Round",
                            values="selected_option", aggfunc="first")
        ri, rf = min(mov.columns), max(mov.columns)
        mov = mov.dropna(subset=[ri, rf])
        top = (mov.assign(c=mov[ri] != mov[rf]).groupby("qid").c.sum()
               .sort_values(ascending=False))
        elegidas = [q for q in top.head(2).index if top[q] > 0]
        salida[panel] = {
            "cuadricula": fig_cuadricula(panel, png),        # {"postura", "opciones"}
            "trayectoria": fig_trayectoria(panel, png),
            "arbol": fig_arbol(panel, png),
            "argumentos": fig_argumentos(panel, png),
            "perfiles": fig_perfiles(panel, png),
            "grafo": fig_grafo(panel, png),
            "movimiento": fig_movimiento(panel, png),
            "perfil_panelistas": fig_perfil_panelistas(panel, png),
            "flujos": [(q, fig_flujo([q], png, f"fig_flujo_{q}")) for q in elegidas],
        }
    return salida


if __name__ == "__main__":
    import sys
    r = construir_todo(png="--png" in sys.argv)
    print("Figuras generadas en", SALIDA + "/")
    for panel, v in r.items():
        print(f"  Panel {panel}: cuadrícula + trayectoria + árbol + {len(v['flujos'])} aluvial(es)")
