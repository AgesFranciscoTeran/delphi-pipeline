# -*- coding: utf-8 -*-
"""
Lee la salida del pipeline (Resultados/*.csv) y devuelve las estructuras que consume el sitio.

Nada de datos escritos a mano: si una tabla del sitio no sale de un CSV, es un bug. La versión
anterior tenía las tablas copiadas a mano y una de ellas quedó desactualizada cinco filas cuando
cambió el tratamiento de unidades. Por eso este módulo existe.

La única excepción son las traducciones al español de los enunciados (TEXTOS): el pipeline los
guarda en inglés, tal como se preguntaron. Si falta una traducción se cae al texto original.
"""
import os
import sys
import json
import collections
import pandas as pd

# El sitio es una VISTA del pipeline, así que importa su taxonomía en vez de duplicarla.
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_PIPELINE = os.environ.get("DELPHI_PIPELINE", os.path.join(_RAIZ, "pipeline"))
RUTA_RESULTADOS = os.environ.get("DELPHI_RESULTADOS", os.path.join(_RAIZ, "Resultados"))
sys.path.insert(0, RUTA_PIPELINE)

ORDEN_ETIQUETAS = ["Consenso fuerte", "Mayoría clara", "Convergencia moderada",
                   "Opción dominante", "Sin consenso", "Insuficiente"]

TEXTOS = {
 "P1_Q1": "¿Cuántos semestres de cirugía deberían recibir los estudiantes?",
 "P1_Q2": "¿La especialización debe darse por formación académica o práctica clínica?",
 "P1_Q3": "¿Cómo debería impartirse el Desarrollo Comunitario Integral (DCI)?",
 "P1_Q4": "¿Deberían dar clases los recién graduados?",
 "P1_Q5": "¿Debería existir un organismo regulador imparcial?",
 "P1_Q6": "¿Cuántas horas de práctica clínica por módulo?",
 "P1_Q7": "¿Cuántas horas de docencia por semana?",
 "P2_Q1": "¿Es el ABP apropiado para la educación médica?",
 "P2_Q2": "¿Qué distribución de práctica y teoría deberían recibir?",
 "P2_Q3": "¿Cuántas horas diarias de clase presencial?",
 "P2_Q4": "¿Debería evaluarse la asistencia a clases magistrales?",
 "P2_Q5": "¿Debería haber atención en salud mental obligatoria?",
 "P2_Q6": "¿Debería haber clases los fines de semana?",
 "P2_Q7": "¿Son necesarios los exámenes escritos en ABP?",
 "P3_Q1": "¿Cuántas horas de docencia teórica por semana?",
 "P3_Q2": "¿Cuántos estudiantes deberían aceptarse en primer año?",
 "P3_Q3": "¿Cuántos estudiantes deberían ser rechazados en primer año?",
 "P3_Q4": "¿Es el ABP un buen método para enseñar medicina?",
 "P3_Q5": "¿Cuántas horas de ABP deberían dictarse?",
 "P3_Q6": "¿Cuántas horas de práctica deberíamos tener?",
 "P3_Q7": "¿Qué peso debería tener cada materia?",
 "P3_Q8": "¿Cuántas horas de colegio general deberían dictarse?",
 "P3_Q9": "¿Las artes liberales encajan con la educación médica de la USFQ?",
 "P3_Q10": "¿Cuándo deberían empezar los turnos nocturnos?",
 "P4_Q1": "¿Cuántas horas de docencia teórica por día?",
 "P4_Q2": "¿Cuántas horas de docencia práctica por día?",
 "P4_Q3": "¿Debería aprobarse el NBME para graduarse?",
 "P4_Q4": "¿Con qué frecuencia deberían evaluarse los estudiantes?",
 "P4_Q5": "¿Qué sistema de calificación debería usarse?",
 "P4_Q6": "¿Deberían recibir clases magistrales?",
 "P4_Q7": "¿Cuántos estudiantes deberían aceptarse en primer año?",
 "P4_Q8": "¿Debería la participación ser parte de la evaluación?",
}

# Traducción de las etiquetas de postura del pipeline a las del sitio.
POSTURA_ES = {"favor": "A favor", "conditional": "Condicional", "against": "En contra"}


def _ruta(nombre):
    return os.path.join(RUTA_RESULTADOS, nombre)


def qid(panel, question):
    q = str(question)
    return f"P{panel}_Q{q[1:] if q.upper().startswith('Q') else q}"


def texto(qid_, respaldo=""):
    return TEXTOS.get(qid_, respaldo or qid_)


def cargar_extraidas():
    d = pd.read_csv(_ruta("02_extracted.csv"))
    d["qid"] = [qid(p, q) for p, q in zip(d.Panel, d.Question)]
    return d


def clasificadas(d=None):
    """Sólo respuestas con una opción asignada: es el denominador de todo lo categórico."""
    d = cargar_extraidas() if d is None else d
    return d[d.is_valid_response & d.selected_option.notna()
             & (d.selected_option != "Unclassified")]


# ── tablas del sitio ──────────────────────────────────────────────────────────

def categoricas_ronda_final():
    c = pd.read_csv(_ruta("03_categorical_consensus.csv"))
    c = c[c.Round == c.Round.max()].copy()
    c["qid"] = [qid(p, q) for p, q in zip(c.Panel, c.Question)]
    c["orden"] = c.consensus_label.map(lambda x: ORDEN_ETIQUETAS.index(x)
                                       if x in ORDEN_ETIQUETAS else 99)
    c = c.sort_values(["orden", "modal_share"], ascending=[True, False])
    return [{"qid": r.qid, "texto": texto(r.qid, r["Question Text"]),
             "opcion": "(sin datos suficientes)" if r.consensus_label == "Insuficiente"
                       else str(r.modal_option),
             "n": int(r.n_classified), "total": int(r.n_responses),
             "etiqueta": r.consensus_label, "empate": bool(r.is_tie)}
            for _, r in c.iterrows()]


def cuantitativas_ronda_final():
    q = pd.read_csv(_ruta("03_quantitative_consensus.csv"))
    q = q[q.Round == q.Round.max()].copy()
    q["qid"] = [qid(p, qq) for p, qq in zip(q.Panel, q.Question)]
    q["orden"] = q.consensus_label.map(lambda x: ORDEN_ETIQUETAS.index(x)
                                       if x in ORDEN_ETIQUETAS else 99)
    q = q.sort_values(["orden", "qid"])

    def num(v):
        if pd.isna(v):
            return "—"
        return f"{v:g}".replace(".", ",")

    return [{"qid": r.qid, "texto": texto(r.qid, r["Question Text"]),
             "unidad": r.question_unit, "asumida": bool(r.unit_assumed),
             # cuántas de las respuestas contadas descansan en un supuesto de unidad:
             # el panelista dijo "8 horas" sin periodo y se tomó la unidad de la pregunta.
             # Es la fuente principal de inestabilidad entre corridas.
             "n_asumidas": int(r.get("n_unit_assumed", 0) or 0),
             "mediana": num(r["median"]),
             "iqr": "—" if pd.isna(r.q1) or pd.isna(r.q3) else f"{num(r.q1)}–{num(r.q3)}",
             "n": int(r.n_numeric), "total": int(r.n_responses),
             "etiqueta": r.consensus_label}
            for _, r in q.iterrows()]


def posturas_ronda_final():
    """Consenso a nivel de postura. Necesita stance_map.py del pipeline."""
    try:
        from stance_map import stance_of, STANCE_MAP
    except ImportError:
        return []
    # OJO con el denominador: `n` son las respuestas con postura asignable y `total` son
    # los panelistas que contestaron esa pregunta, clasificables o no. Contar `total` sobre
    # las clasificadas haría que una pregunta con 5 de 8 respuestas se leyera como 5/5,
    # es decir, como unanimidad.
    todas = cargar_extraidas()
    todas = todas[todas.is_valid_response & (todas.Round == todas.Round.max())]
    n_panel = todas.groupby("qid").size().to_dict()
    d = clasificadas()
    d = d[d.Round == d.Round.max()]
    filas = []
    for q, g in d.groupby("qid"):
        if q not in STANCE_MAP:
            continue
        c = collections.Counter()
        for o in g.selected_option:
            p, _ = stance_of(q, o)
            if p:
                c[p] += 1
        n = sum(c.values())
        tot = n_panel.get(q, len(g))
        f, co, ag = c.get("favor", 0), c.get("conditional", 0), c.get("against", 0)
        mx = max(f, co, ag)
        share = mx / n if n else 0
        ordenados = sorted([f, co, ag], reverse=True)
        empate = mx > 0 and ordenados[0] == ordenados[1]
        filas.append({"qid": q, "texto": texto(q), "favor": f, "condicional": co,
                      "contra": ag, "n": n, "total": tot, "share": share,
                      "etiqueta": etiqueta_consenso(share, n, empate)})
    filas.sort(key=lambda r: (ORDEN_ETIQUETAS.index(r["etiqueta"]), -r["share"]))
    return filas


def etiqueta_consenso(share, n, empate=False, min_n=5):
    """Mismos umbrales que config.py del pipeline. Son provisionales (Fase 2)."""
    if n < min_n:
        return "Insuficiente"
    if empate:
        return "Sin consenso"
    if share >= 0.75:
        return "Consenso fuerte"
    if share >= 0.60:
        return "Mayoría clara"
    if share >= 0.40:
        return "Opción dominante"
    return "Sin consenso"


def convergencia():
    c = pd.read_csv(_ruta("03_convergence.csv"))
    c["qid"] = [qid(p, q) for p, q in zip(c.Panel, c.Question)]
    return c


def resumen_convergencia():
    c = convergencia()
    cat = c[c.type == "categorical"]
    return collections.Counter(cat.convergence.dropna())


def movimiento():
    """Trayectorias panelista×pregunta que cambian de opción entre primera y última ronda."""
    d = clasificadas()
    piv = d.pivot_table(index=["Panel", "qid", "Panelist"], columns="Round",
                        values="selected_option", aggfunc="first")
    ri, rf = min(piv.columns), max(piv.columns)
    piv = piv.dropna(subset=[ri, rf])
    piv = piv.assign(cambio=piv[ri] != piv[rf]).reset_index()
    total = {"n": len(piv), "cambian": int(piv.cambio.sum())}
    total["pct"] = round(total["cambian"] / total["n"] * 100) if total["n"] else 0
    por_panel = {int(p): {"n": len(g), "cambian": int(g.cambio.sum()),
                          "pct": round(g.cambio.mean() * 100)}
                 for p, g in piv.groupby("Panel")}
    return total, por_panel


def panel_de(qid_):
    """P3_Q7 -> 3"""
    return int(qid_.split("_")[0][1:])


def por_panel(filas, panel):
    """Filtra una lista de filas (dicts con 'qid') a un solo panel."""
    return [r for r in filas if panel_de(r["qid"]) == panel]


def paneles():
    d = cargar_extraidas()
    return sorted(int(p) for p in d.Panel.unique())


def contexto_panel(panel):
    """
    Cifras de un panel. Cada panel es un ESTUDIO INDEPENDIENTE: distintos panelistas
    (no hay ninguno repetido) y distintas preguntas (de 32, sólo una se repite entre
    paneles). Por eso no se agregan ni se comparan entre sí.
    """
    d = cargar_extraidas()
    g = d[d.Panel == panel]
    cat = por_panel(categoricas_ronda_final(), panel)
    cua = por_panel(cuantitativas_ronda_final(), panel)
    pos = por_panel(posturas_ronda_final(), panel)
    c = convergencia()
    cv = c[(c.qid.map(panel_de) == panel) & (c.type == "categorical")]
    resueltas = sum(1 for r in cat if r["etiqueta"] in ("Consenso fuerte", "Mayoría clara"))
    return {"panel": panel,
            "n_panelistas": g.Panelist.nunique(), "n_preguntas": g.qid.nunique(),
            "n_respuestas": len(g), "n_rondas": g.Round.nunique(),
            "cat": cat, "cuant": cua, "postura": pos,
            "n_cat": len(cat), "n_cuant": len(cua), "n_pos": len(pos),
            "resueltas": resueltas,
            "convergieron": int((cv.convergence == "Convergió").sum()),
            "dispersaron": int((cv.convergence == "Se dispersó").sum()),
            "n_asumidas": sum(r["n_asumidas"] for r in cua)}


def contexto():
    """Cifras de cabecera, todas derivadas."""
    d = cargar_extraidas()
    cat = categoricas_ronda_final()
    cua = cuantitativas_ronda_final()
    pos = posturas_ronda_final()
    resueltas_pos = sum(1 for r in pos if r["etiqueta"] in ("Consenso fuerte", "Mayoría clara"))
    con_modal = sum(1 for r in cat if r["etiqueta"] not in ("Sin consenso", "Insuficiente"))
    return {"n_respuestas": len(d), "n_validas": int(d.is_valid_response.sum()),
            "n_preguntas": d.qid.nunique(), "n_paneles": d.Panel.nunique(),
            "n_rondas": d.Round.nunique(), "n_panelistas": d.Panelist.nunique(),
            "pos_resueltas": resueltas_pos, "pos_total": len(pos),
            "cat_con_modal": con_modal, "cat_total": len(cat),
            "cuant_fuerte": sum(1 for r in cua if r["etiqueta"] == "Consenso fuerte"),
            "cuant_total": len(cua)}


def manifiesto():
    """Datos de la corrida, si el pipeline dejó el manifiesto."""
    p = _ruta("run_manifest.json")
    if not os.path.exists(p):
        return {}
    with open(p) as f:
        return json.load(f)


if __name__ == "__main__":
    ctx = contexto()
    print("Contexto:", json.dumps(ctx, indent=1, ensure_ascii=False))
    print("\nConvergencia:", dict(resumen_convergencia()))
    tot, pp = movimiento()
    print("Movimiento:", tot)
    print(f"\nCategóricas: {len(categoricas_ronda_final())} | "
          f"Cuantitativas: {len(cuantitativas_ronda_final())} | "
          f"Posturas: {len(posturas_ronda_final())}")
