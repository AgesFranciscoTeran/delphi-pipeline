#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera pipeline/taxonomy.py y pipeline/stance_map.py desde el documento de Emily.

Entrada:  docs/emily_posturas_varias_opciones.json  (lectura estructurada del .docx)
Salida:   pipeline/taxonomy.py, pipeline/stance_map.py

Por qué existe
--------------
Hasta la v1 la taxonomía se transcribía a mano y `stance_map.py` reconstruía a mano la
anidación que el documento tenía y la transcripción aplanaba. Dos transcripciones manuales
del mismo documento es una de más: cuando Emily manda una versión nueva hay que repetir las
dos y cualquier desajuste entre ellas es un bug silencioso.

La v2 del documento declara la anidación de forma explícita (celda «- Yes» con sus
calificadores, celda «- No» con los suyos), así que las dos se pueden derivar de la misma
fuente. Este script es esa derivación.

Cómo aplana
-----------
El pipeline pide UNA opción de una lista cerrada. El árbol se aplana metiendo la postura en
el texto de la opción:

    - Yes → Only in clinical subjects      ==>   "Yes, only in clinical subjects"
    - No  → Lack of preparation            ==>   "No, lack of preparation"

Así la opción es autocontenida (el modelo no puede elegir un calificador sin comprometerse
con una postura, que es el error que más se veía) y el mapa de posturas sale del prefijo sin
intervención humana.

Qué NO hace
-----------
Las preguntas cuantitativas siguen siendo cuantitativas: se les actualizan las bandas, pero
su eje nominal de la v2 NO entra en la lista de opciones, porque convertirlas a nominal
destruiría la capa numérica (valor + unidad), que es la que alimenta el consenso cuantitativo.
Ese eje queda anotado en `extra_axes` para que no se pierda de vista: capturarlo de verdad es
la medición multi-eje de la Fase 1, y necesita confirmación de Emily.
"""
import json
import os
import re
import sys
from collections import OrderedDict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRADA = os.path.join(RAIZ, "docs", "emily_posturas_varias_opciones.json")
SALIDA_TAX = os.path.join(RAIZ, "pipeline", "taxonomy.py")
SALIDA_STANCE = os.path.join(RAIZ, "pipeline", "stance_map.py")

# El tipo de cada pregunta lo fija el pipeline, no el documento: cambiarlo cambiaría el
# contrato con consensus_metrics.py y con el sitio. Se conserva el de la taxonomía vigente.
TIPOS = {
    "P1_Q1": "quantitative", "P1_Q2": "nominal", "P1_Q3": "nominal", "P1_Q4": "nominal",
    "P1_Q5": "nominal", "P1_Q6": "quantitative", "P1_Q7": "quantitative",
    "P2_Q1": "nominal", "P2_Q2": "nominal", "P2_Q3": "quantitative", "P2_Q4": "nominal",
    "P2_Q5": "nominal", "P2_Q6": "nominal", "P2_Q7": "nominal",
    "P3_Q1": "quantitative", "P3_Q2": "hybrid", "P3_Q3": "nominal", "P3_Q4": "nominal",
    "P3_Q5": "quantitative", "P3_Q6": "quantitative", "P3_Q7": "nominal",
    "P3_Q8": "quantitative", "P3_Q9": "nominal", "P3_Q10": "nominal",
    "P4_Q1": "quantitative", "P4_Q2": "quantitative", "P4_Q3": "nominal",
    "P4_Q4": "nominal", "P4_Q5": "nominal", "P4_Q6": "nominal", "P4_Q7": "hybrid",
    "P4_Q8": "nominal",
}

# P2_Q5 pasa de 'binary' a 'nominal': la v2 le da rama Sí/No MÁS calificadores MÁS un eje de
# sesiones por mes, así que dos opciones ya no alcanzan.

EMILY_NUM = {}
_n = 0
for _p, _k in ((1, 7), (2, 7), (3, 10), (4, 8)):
    for _i in range(1, _k + 1):
        _n += 1
        EMILY_NUM["P%d_Q%d" % (_p, _i)] = _n

# ── unidades ─────────────────────────────────────────────────────────────────
# La unidad sale del NOMBRE del eje cuando el documento la declara ("Numerical per week").
# Cuando no la declara se hereda la de la taxonomía vigente y se marca 'assumed', que es lo
# que el sitio muestra como «unidad asumida» y lo que bloquea la decisión 5.
UNIDAD_HEREDADA = {
    "P1_Q1": ("semesters", False),
    "P1_Q6": ("hours/week", False),
    "P1_Q7": ("hours/day", False),
    "P2_Q3": ("hours/day", False),
    "P3_Q1": ("hours/day", True),
    "P3_Q2": ("students", False),
    "P3_Q5": ("hours/week", False),
    "P3_Q6": ("hours/week", True),
    "P3_Q8": ("hours/week", False),
    "P4_Q1": ("hours/day", False),
    "P4_Q2": ("hours/day", False),
    "P4_Q7": ("students", False),
}

PERIODOS = [
    ("per week", "hours/week"), ("per month", "hours/month"), ("per day", "hours/day"),
    ("per semester", "hours/semester"), ("per module", "hours/module"),
]


def unidad_declarada(tipo_eje):
    """Devuelve la unidad si el nombre del eje declara el periodo; si no, None."""
    t = tipo_eje.lower()
    if "session" in t and "per month" in t:
        return "sessions/month"
    for marca, unidad in PERIODOS:
        if marca in t:
            return unidad
    return None


# ── carga y normalización ────────────────────────────────────────────────────

def cargar():
    with open(ENTRADA, encoding="utf-8") as f:
        bruto = json.load(f)
    cuenta = {}
    fuera = OrderedDict()
    for item in bruto:
        p = item["panel"]
        cuenta[p] = cuenta.get(p, 0) + 1
        fuera["P%d_Q%d" % (p, cuenta[p])] = item
    return fuera


def limpiar(op):
    """Quita el guion inicial de las celdas de rama y normaliza espacios."""
    return re.sub(r"\s+", " ", op.strip().lstrip("-").strip())


def es_rama(op):
    """'- Yes' / '- No' abren una rama de postura. Devuelve 'Yes', 'No' o None."""
    t = limpiar(op).lower().rstrip(".:")
    return {"yes": "Yes", "no": "No"}.get(t)


def capitalizar(s):
    return s[0].upper() + s[1:] if s else s


def descapitalizar(s):
    # "Only in clinical subjects" -> "only in clinical subjects", pero "NBME ..." se respeta.
    if len(s) > 1 and s[1].isupper():
        return s
    return s[0].lower() + s[1:] if s else s


# Una opción que no cuelga de ninguna rama pero empieza así expresa una postura condicional.
# Es una inferencia del generador, no del documento: Emily las escribe en una celda aparte,
# en paralelo al Sí/No, no debajo de ninguno. Sin esta regla el pipeline perdería la postura
# "conditional", que hoy existe y sostiene buena parte de la capa de posturas.
PREFIJOS_CONDICIONALES = ("depends", "depending", "according to", "only if", "it depends")


def aplanar_ejes(ejes):
    """
    Recorre los ejes en orden y devuelve (opciones, ejes_numericos, ramas).

    Una celda que empieza por '- Yes' o '- No' abre una rama: esa opción y todas las que la
    siguen EN ESA MISMA CELDA son calificadores de esa postura. Una celda que no empieza así
    aporta sus opciones sin prefijo.
    """
    opciones, numericos, ramas = [], [], {}
    vistas = set()

    def anadir(texto, postura, calificador):
        if texto.lower() in vistas:
            return
        vistas.add(texto.lower())
        opciones.append(texto)
        if postura:
            ramas[texto] = (postura, calificador)

    for eje in ejes:
        tipo = eje["tipo"]
        ops = [o for o in eje["opciones"] if limpiar(o)]
        if not ops:
            continue
        postura = es_rama(ops[0])
        es_num = tipo.lower().startswith(("numer", "quantit", "cuantit"))

        if es_num and not postura:
            numericos.append({"tipo": tipo, "opciones": [limpiar(o) for o in ops]})
            continue

        # Una celda que lista Sí Y No como opciones sueltas es un eje de postura puro
        # (así viene el eje "Binary" de P2_Q5): cada una es su propia postura y lo que
        # quede en la celda son calificadores en paralelo, no colgados de ninguna.
        sueltas = [es_rama(o) for o in ops]
        if sueltas.count("Yes") and sueltas.count("No"):
            for o, s in zip(ops, sueltas):
                if s:
                    anadir(s, s, None)
                else:
                    anadir(capitalizar(limpiar(o)), None, None)
        elif postura:
            anadir(postura, postura, None)
            for o in ops[1:]:
                q = limpiar(o)
                anadir("%s, %s" % (postura, descapitalizar(q)), postura, q)
        else:
            for o in ops:
                anadir(capitalizar(limpiar(o)), None, None)

    # Segunda pasada: sólo si la pregunta tiene ramas, las opciones sueltas de tipo
    # "Depends on ..." se leen como postura condicional (ver PREFIJOS_CONDICIONALES).
    if ramas:
        for texto in opciones:
            if texto in ramas:
                continue
            if texto.lower().startswith(PREFIJOS_CONDICIONALES):
                ramas[texto] = ("Depends", texto)

    return opciones, numericos, ramas


def bandas_de(eje_numerico):
    """'Minimal: 3-5' -> ('Minimal', '3-5'). Sin ':' el texto es a la vez nombre y rango."""
    bandas = OrderedDict()
    for op in eje_numerico["opciones"]:
        if ":" in op:
            nombre, rango = op.split(":", 1)
            bandas[nombre.strip()] = rango.strip()
        else:
            bandas[op.strip()] = op.strip()
    return bandas


def construir():
    doc = cargar()
    tax = OrderedDict()
    stance = OrderedDict()
    informe = []

    for qid, item in doc.items():
        tipo = TIPOS[qid]
        opciones, numericos, ramas = aplanar_ejes(item["ejes"])
        entrada = OrderedDict()
        entrada["emily_num"] = EMILY_NUM[qid]
        entrada["text"] = item["pregunta"].strip()
        entrada["type"] = tipo

        if tipo in ("quantitative", "hybrid"):
            if not numericos:
                raise SystemExit("%s es %s pero la v2 no le da eje numérico" % (qid, tipo))
            entrada["bands"] = bandas_de(numericos[0])
            politicas_usadas = False
            if tipo == "hybrid":
                # El eje nominal contiguo son las políticas asociadas a cada banda. Sólo se
                # emparejan si hay tantas políticas como bandas; si no, emparejarlas por
                # posición inventaría una correspondencia que el documento no dice.
                nombres = list(entrada["bands"].keys())
                if len(opciones) == len(nombres):
                    entrada["band_policies"] = OrderedDict(zip(nombres, opciones))
                    politicas_usadas = True
                else:
                    informe.append(
                        "POLITICAS    %s: %d bandas y %d opciones nominales; no se emparejan "
                        "por posicion, el eje nominal pasa a extra_axes"
                        % (qid, len(nombres), len(opciones)))
            # Lo que la v2 añade y esta corrida NO mide todavía.
            extra = []
            if opciones and not politicas_usadas:
                extra.append({"tipo": "Nominal", "opciones": opciones})
            extra.extend({"tipo": e["tipo"], "opciones": e["opciones"]} for e in numericos[1:])
            if extra:
                entrada["extra_axes"] = extra
            unidad = unidad_declarada(numericos[0]["tipo"])
            heredada, asumida = UNIDAD_HEREDADA.get(qid, (None, True))
            if unidad:
                entrada["unit"] = unidad
                entrada["unit_assumed"] = False
                if heredada and unidad != heredada:
                    informe.append("UNIDAD CAMBIA  %s: %s -> %s (el documento v2 la declara)"
                                   % (qid, heredada, unidad))
            elif heredada:
                entrada["unit"] = heredada
                entrada["unit_assumed"] = True
                informe.append("UNIDAD ASUMIDA %s: %s (la v2 dice sólo «%s»)"
                               % (qid, heredada, numericos[0]["tipo"]))
        else:
            # Los ejes numéricos de una pregunta nominal entran como opciones de texto:
            # ya vienen escritos como etiquetas discretas («Up to 4 semesters», «Maximum 20%»).
            for e in numericos:
                for o in e["opciones"]:
                    if o.lower() not in {x.lower() for x in opciones}:
                        opciones.append(capitalizar(o))
            entrada["options"] = opciones

        tax[qid] = entrada
        if ramas:
            stance[qid] = ramas

    return tax, stance, informe


# ── escritura ────────────────────────────────────────────────────────────────

def py(v, sangria=0):
    sp = " " * sangria
    if isinstance(v, (dict, OrderedDict)):
        if not v:
            return "{}"
        cuerpo = "".join('%s    %s: %s,\n' % (sp, json.dumps(k, ensure_ascii=False),
                                              py(x, sangria + 4)) for k, x in v.items())
        return "{\n%s%s}" % (cuerpo, sp)
    if isinstance(v, list):
        if not v:
            return "[]"
        cuerpo = "".join("%s    %s,\n" % (sp, py(x, sangria + 4)) for x in v)
        return "[\n%s%s]" % (cuerpo, sp)
    if isinstance(v, tuple):
        return "(%s)" % ", ".join(py(x) for x in v)
    if v is True or v is False or v is None:
        return repr(v)          # json.dumps daría true/false/null, que no son Python
    return json.dumps(v, ensure_ascii=False)


CABECERA_TAX = '''"""
Taxonomía de preguntas y opciones — definida y revisada por Emily (experta de dominio).

GENERADO por tools/build_taxonomy.py desde docs/emily_posturas_varias_opciones.json.
NO EDITAR A MANO: edita el documento de Emily, vuelve a extraer el JSON y regenera.

Fuente: «Posturas varias opciones» v2 (Emily, 14-09-2026).

Cómo se aplanó el árbol
-----------------------
El documento anida: la celda «- Yes» lleva sus calificadores y la celda «- No» los suyos.
El pipeline pide UNA opción de una lista cerrada, así que la postura va dentro del texto
de la opción ("Yes, only in clinical subjects"). Ventaja: el modelo no puede elegir un
calificador sin comprometerse con una postura — que era el fallo más común — y stance_map.py
se deriva del prefijo en vez de transcribirse a mano.

Tipos:
  - quantitative : pide un número; tiene 'bands'
  - nominal      : conjunto cerrado de opciones; tiene 'options'
  - hybrid       : número acoplado a una política; tiene 'bands' + 'band_policies'

'extra_axes' (sólo en preguntas cuantitativas) es lo que la v2 añade y esta corrida todavía
NO mide: convertir esas preguntas a nominal destruiría la capa numérica. Medir varios ejes a
la vez es la Fase 1 y necesita confirmación de Emily.

Numeración de Emily -> nuestros IDs:
  Panel 1 -> #1-7   (P1_Q1 .. P1_Q7)
  Panel 2 -> #8-14  (P2_Q1 .. P2_Q7)
  Panel 3 -> #15-24 (P3_Q1 .. P3_Q10)
  Panel 4 -> #25-32 (P4_Q1 .. P4_Q8)
"""
'''

PIE_TAX = '''

def taxonomy_hash():
    """SHA1 del contenido de la taxonomía: entra en la clave del caché y en el manifiesto."""
    import hashlib, json
    blob = json.dumps(EMILY_TAXONOMY, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]


def get_taxonomy(panel, question):
    """Look up the taxonomy entry for a (panel, question) pair."""
    q = str(question)
    return EMILY_TAXONOMY.get("P%s_Q%s" % (panel, q[1:] if q.upper().startswith("Q") else q))


if __name__ == "__main__":
    from collections import Counter
    tipos = Counter(v["type"] for v in EMILY_TAXONOMY.values())
    print("Preguntas: %d   hash: %s" % (len(EMILY_TAXONOMY), taxonomy_hash()))
    for t, n in sorted(tipos.items()):
        print("  %-14s %d" % (t, n))
    n_opts = [len(v["options"]) for v in EMILY_TAXONOMY.values() if "options" in v]
    print("Opciones por pregunta nominal: min %d / mediana %d / max %d"
          % (min(n_opts), sorted(n_opts)[len(n_opts) // 2], max(n_opts)))
'''

CABECERA_STANCE = '''"""
Mapa opción -> (postura, calificador).

GENERADO por tools/build_taxonomy.py desde la anidación del documento de Emily.
NO EDITAR A MANO.

Antes esto era una transcripción manual: el documento anidaba las opciones bajo la postura,
taxonomy.py las aplanaba perdiendo el nivel de arriba, y este módulo lo reconstruía opción por
opción. Dos transcripciones a mano del mismo documento, que podían desajustarse en silencio.
Ahora las dos salen de la misma fuente y el prefijo de la opción ("Yes, ...") determina la
postura sin que nadie decida nada.

Posturas: "favor" | "against" | "conditional". Las preguntas sin anidación (elección entre
alternativas, no sí/no) no aparecen aquí y se analizan por opción.
"""

F, A, C = "favor", "against", "conditional"

'''

PIE_STANCE = '''
STANCE_ES = {"favor": "A favor", "against": "En contra", "conditional": "Condicional"}


def stance_of(qid, option):
    """(postura, calificador) de una opción; (None, None) si la pregunta no tiene postura."""
    entrada = STANCE_MAP.get(qid)
    if not entrada:
        return None, None
    if option in entrada:
        return entrada[option]
    objetivo = " ".join(str(option).lower().split())
    for k, v in entrada.items():
        if " ".join(k.lower().split()) == objetivo:
            return v
    return None, None


if __name__ == "__main__":
    print("Preguntas con postura: %d" % len(STANCE_MAP))
    for q, m in STANCE_MAP.items():
        from collections import Counter
        c = Counter(p for p, _ in m.values())
        print("  %-7s %2d opciones  %s" % (q, len(m), dict(c)))
'''


def main():
    tax, stance, informe = construir()

    with open(SALIDA_TAX, "w", encoding="utf-8") as f:
        f.write(CABECERA_TAX)
        f.write("\nEMILY_TAXONOMY = %s\n" % py(tax))
        f.write(PIE_TAX)

    with open(SALIDA_STANCE, "w", encoding="utf-8") as f:
        f.write(CABECERA_STANCE)
        f.write("STANCE_MAP = {\n")
        for qid, mapa in stance.items():
            f.write("    %s: {\n" % json.dumps(qid))
            for opcion, (postura, calif) in mapa.items():
                sigla = {"Yes": "F", "No": "A"}.get(postura, "C")
                f.write("        %s: (%s, %s),\n"
                        % (json.dumps(opcion, ensure_ascii=False), sigla,
                           json.dumps(calif, ensure_ascii=False) if calif else "None"))
            f.write("    },\n")
        f.write("}\n")
        f.write(PIE_STANCE)

    print("taxonomy.py      %d preguntas" % len(tax))
    print("stance_map.py    %d preguntas con postura, %d opciones mapeadas"
          % (len(stance), sum(len(m) for m in stance.values())))
    if informe:
        print("\nAvisos:")
        for linea in informe:
            print("  " + linea)
    return 0


if __name__ == "__main__":
    sys.exit(main())
