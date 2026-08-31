# -*- coding: utf-8 -*-
"""
Cabecera de build.py: prepara todas las variables que la plantilla HTML interpola.

Regla del módulo: **ningún número se escribe a mano**. Todo sale de datos.py, que a su vez
lee Resultados/*.csv. Lo único escrito a mano es texto editorial —las decisiones pendientes,
las lecturas de cada panel, la tabla de análisis posibles—, y va marcado como tal.
"""
import html

import datos
import figuras

FECHA = "30 de agosto de 2026"

CTX = datos.contexto()
POSTURA = datos.posturas_ronda_final()
CATEG = datos.categoricas_ronda_final()
CUANT = datos.cuantitativas_ronda_final()
CONV = datos.resumen_convergencia()
MOV_TOT, MOV_PANEL = datos.movimiento()
FIGS = figuras.construir_todo()

C_FAVOR, C_COND, C_CONTRA = figuras.AZUL, figuras.GRIS, figuras.ROJO


def esc(t):
    return html.escape(str(t))


def n_es(x):
    return str(x).replace(".", ",")


# ── texto editorial (lo único no derivado de los CSV) ─────────────────────────

CAPAS = [
 ("Convertir las respuestas en etiquetas", "Listo", "ok",
  f"Nada. {CTX['n_validas']} de {CTX['n_respuestas']} respuestas clasificadas, sin fallos. "
  f"Las {CTX['n_respuestas'] - CTX['n_validas']} restantes están vacías.", "—"),
 ("Calcular el consenso de cada pregunta", "Listo", "ok",
  "Nada. Mediana y rango para las numéricas, distribución y n para las de opción.", "—"),
 ("Definir qué cuenta como «consenso»", "Provisional", "wip",
  "Los umbrales actuales los fijamos mirando los datos. Hay que fijarlos con la literatura "
  "Delphi (acuerdo + estabilidad entre rondas) <b>antes</b> de volver a mirar resultados.",
  "Pancho · 1 semana"),
 ("La taxonomía: las opciones de cada pregunta", "Es lo que bloquea todo", "block",
  "Ocho decisiones, sección 6. Es el cuello de botella real: sin esto no avanza nada más.",
  "<b>Emily</b> · una sesión"),
 ("Saber si el sistema codifica tan bien como una persona", "A medias", "wip",
  "Hoy hay 44 respuestas etiquetadas por una sola persona. Para publicar hacen falta 200–300 "
  "y <b>un segundo codificador</b>.", "Emily + 2.º codificador"),
 ("Las razones que dan los panelistas", "Sin empezar", "todo",
  "Es la parte más grande que queda. Hay que construir una lista de argumentos —el porqué de "
  "cada postura— igual que se hizo con las opciones.", "Emily + Pancho"),
 ("El estudio real (eutanasia, ~22 000 respuestas)", "Pendiente", "todo",
  "Confirmar formalmente el manejo de datos sensibles y definir la taxonomía del nuevo tema.",
  "<b>Jonathan</b>"),
]

IDEAS = [
 ("Red de panelistas por ronda", "Hecha", "ok",
  "Cómo se forman y se deshacen los bloques de acuerdo a lo largo del proceso.",
  "Nada — es la figura de la sección 3."),
 ("Flujo de opiniones entre rondas", "Hecha", "ok",
  "Quién cambió de posición y hacia dónde, pregunta por pregunta.",
  "Nada. Está en la sección 3; se puede generar para cualquier pregunta."),
 ("Trayectoria de consenso por pregunta", "Hecha", "ok",
  "Qué preguntas convergen, cuáles se dispersan y cuáles nacen ya resueltas.",
  "Nada — es la figura de las cuatro facetas."),
 ("Movimiento frente a convergencia", "Hecha", "ok",
  "¿El panel que más discute es el que más acuerda? En estos datos, al revés.",
  "Nada. Con 4 paneles es una señal; con el estudio real será medible."),
 ("Red de posturas que viajan juntas", "Depende de Emily", "wip",
  "Qué posiciones forman paquete: quien defiende X, ¿defiende también Y? Es el mapa "
  "ideológico del panel, no el de las personas.",
  "La decisión 1 (separar postura de calificadores). Después, casi inmediato."),
 ("Red de argumentos", "Depende de Emily", "block",
  "Qué razones sostienen cada postura y cuáles son compartidas por gente que no está de "
  "acuerdo en la conclusión. Es la más rica de todas.",
  "La decisión 8: construir la lista de argumentos. Es el trabajo más grande que queda."),
 ("Quién arrastra al panel", "Con reservas", "todo",
  "Si hay panelistas cuya posición inicial anticipa hacia dónde se mueve el resto.",
  "Se puede calcular, pero con 7–10 personas el resultado no es fiable. Sólo tendría sentido "
  "sobre el estudio de eutanasia."),
]

INVERSIONES = [
 ("P2_Q4", "¿Evaluar la asistencia?", "Consenso fuerte: Sí", "Opción dominante: No"),
 ("P2_Q6", "¿Clases en fin de semana?", "Sólo en años clínicos", "Mayoría clara: No"),
 ("P4_Q3", "¿NBME para graduarse?", "Junto con evaluación clínica", "Consenso fuerte: No (8/8)"),
 ("P3_Q10", "¿Cuándo empiezan los turnos?", "Años preclínicos (100 %)", "Consenso fuerte: Años finales"),
 ("P3_Q7", "¿Peso de cada materia?", "Igualdad entre materias (100 %)", "Consenso fuerte: Prioridad a clínicas"),
]

LECTURA = {
 1: "No converge. El acuerdo se mantiene bajo las tres rondas — pero es el panel con los "
    "problemas de taxonomía (P1_Q3 casi sin clasificar), así que parte puede ser artefacto.",
 2: "Se desdibuja: el panel termina algo más disperso de lo que empezó.",
 3: "Se parte y después se reagrupa. La ronda 2 rompe el grupo inicial y la 3 lo reconstruye "
    "más fuerte. Esa forma no aparece en ninguna tabla por pregunta.",
 4: "Convergencia de manual: de un grafo casi vacío a uno denso, y los pares en desacuerdo "
    "fuerte desaparecen.",
}

DECISIONES = [
 ("Separar postura de calificadores",
  "Hoy cada pregunta tiene una lista única de opciones excluyentes que mezcla la postura con sus condiciones. «Sí, pero sólo en ciencias básicas» encaja en tres opciones a la vez.",
  f"Su propio documento de posturas ya trae esta estructura anidada y ya está codificada: a nivel de postura, {sum(1 for r in POSTURA if r['etiqueta'] == 'Consenso fuerte')} de {len(POSTURA)} preguntas dan consenso fuerte y el acuerdo con sus etiquetas sube de 18/24 a 21/24.",
  "Confirmar dos casos del documento: «Replaced by clinical cases» cuelga de <em>Sí</em> en P2_Q7 (¿debería ser No o Depende?), y «According to the subject» cuelga de <em>Sí</em> en P4_Q8 pero de <em>Depende</em> en P2_Q4."),
 ("P1_Q3 (DCI): volver a tipificar",
  "El 86 % de las respuestas quedó sin clasificar: los panelistas no eligen una postura, describen cómo debería ser el DCI.",
  "Al validar, Emily creó una categoría que no existía en la taxonomía («Less semesters»).",
  "¿Dividirla en dos capas —cuántos semestres (con bandas) y qué actividades (abierta)— o mantenerla como una sola pregunta abierta?"),
 ("P3_Q3: umbrales de depuración",
  "«Alta / Moderada / Baja depuración» no tienen números. En los datos aparecen 20 %, 15 %, «menos del 10 %», «20 estudiantes», y tres personas que dicen que no debe haber porcentaje fijo.",
  "Sin umbral, ni el modelo ni una persona clasifican igual dos veces. Ambos modelos fallan este ítem.",
  "Fijar los cortes (Alta &gt; X %, Moderada Y–X %, Baja &lt; Y %) y decidir si se añade «Sin porcentaje fijo / según mérito», que hoy es la respuesta más frecuente y no existe como opción."),
 ("P4_Q5: opción «mixto»",
  "Dos panelistas proponen letras los primeros años y aprobado/reprobado los últimos.",
  "Emily los etiquetó «Both: letter system, Pass/Fail» — una categoría que la taxonomía no tiene.",
  "¿Se añade «Mixto (letras + aprobado/reprobado por etapa)»?"),
 ("Unidades y bordes de las bandas",
  "Las bandas 3-5 / 6-8 / &gt;9 dejan fuera valores como 5,5 y 8,5. Las de admisión (&lt;50 / 50 / &gt;50) mandan a «Alta» casi todo el Panel 3, cuyas respuestas van de 20 a 120.",
  "Ya incorporamos lo que Emily aclaró en sus notas: P1_Q6 por semana con módulo ≈ 1 mes, P1_Q7 por día a partir del promedio semanal, P3_Q5 y P3_Q8 por semana.",
  "Confirmar P3_Q1 y P3_Q6 (hoy asumidos), hacer los bordes contiguos, y revisar las bandas de admisión. Y un caso concreto: si alguien escribe «8 horas» sin periodo en P1_Q6 —que pregunta por módulo pero cuyas bandas son por semana— ¿qué se asume?"),
 ("¿Puede asignarse banda sin número?",
  "Emily asignó bandas a respuestas que no dan ninguna cifra («restringir las prácticas a internos» → Mínima).",
  "El modelo tiene prohibido hacerlo, y son 3 de los 9 desacuerdos que quedan.",
  "¿Se permite, y con qué regla escrita?"),
 ("Panel 1: ¿son preguntas numéricas?",
  "De 7 panelistas sólo 4 o 5 dan una cifra; el resto responde con un criterio («las horas necesarias para cubrir el programa»).",
  "Por eso P1_Q1 no alcanza el mínimo de respuestas y las otras dos quedan al límite.",
  "¿Se re-tipifican como preguntas de opción, se dejan abiertas, o se acepta reportarlas con n bajo?"),
 ("Taxonomía de argumentos",
  "Hoy se clasifica <b>qué</b> responde cada panelista, pero no <b>por qué</b>. Las razones están en el texto y no se están usando.",
  "Es lo que haría falta para la red de argumentos de la sección 4, que es el análisis más rico de los siete.",
  "Es el trabajo más grande y conviene empezarlo antes que los otros siete puntos, aunque se cierre después."),
]


# ── filas HTML ────────────────────────────────────────────────────────────────

def clase_etiqueta(e):
    return {"Consenso fuerte": "e-fuerte", "Mayoría clara": "e-clara",
            "Opción dominante": "e-dom", "Convergencia moderada": "e-clara",
            "Sin consenso": "e-sin", "Insuficiente": "e-insuf"}.get(e, "")


def barra_postura(favor, cond, contra, n, tot=None):
    """
    Barra apilada divergente, normalizada sobre el TOTAL de panelistas y no sobre los
    clasificados: así el largo de la barra es la cobertura y una pregunta con 1 respuesta
    de 7 no se lee como unanimidad. El tramo rayado son las respuestas sin postura asignable.
    """
    if n == 0:
        return '<div class="bar empty">sin datos suficientes</div>'
    base = tot or n
    segs = [("A favor", favor, C_FAVOR), ("Condicional", cond, C_COND),
            ("En contra", contra, C_CONTRA)]
    out, left = [], 0.0
    for nombre, v, color in segs:
        if v == 0:
            continue
        pct = v / base * 100
        out.append(
            f'<div class="seg" style="left:{left}%;width:{pct}%;background:{color}" '
            f'title="{nombre}: {v} de {n} clasificadas ({base} panelistas)">'
            f'<span>{v if pct >= 9 else ""}</span></div>')
        left += pct
    if base > n:
        out.append(f'<div class="seg gap" style="left:{left}%;width:{(base-n)/base*100}%" '
                   f'title="Sin postura asignable: {base-n} de {base}"></div>')
    return '<div class="bar">' + "".join(out) + "</div>"


SUP_ASUM = ('<sup title="Unidad asumida por nosotros, no declarada por Emily '
            '(punto 5 de la sección 6)">*</sup>')

filas_postura = "\n".join(
    f'<tr><td class="qid">{r["qid"]}</td><td class="qtxt">{esc(r["texto"])}</td>'
    f'<td class="cbar">{barra_postura(r["favor"], r["condicional"], r["contra"], r["n"], r["total"])}</td>'
    f'<td class="n">{r["n"]}/{r["total"]}</td>'
    f'<td><span class="tag {clase_etiqueta(r["etiqueta"])}">{r["etiqueta"]}</span></td></tr>'
    for r in POSTURA)

filas_categ = "\n".join(
    f'<tr><td class="qid">{r["qid"]}</td><td class="qtxt">{esc(r["texto"])}</td>'
    f'<td class="opt">{esc(r["opcion"])}</td><td class="n">{r["n"]}/{r["total"]}</td>'
    f'<td><span class="tag {clase_etiqueta(r["etiqueta"])}">{r["etiqueta"]}</span></td></tr>'
    for r in CATEG)

filas_cuant = "\n".join(
    f'<tr><td class="qid">{r["qid"]}</td><td class="qtxt">{esc(r["texto"])}</td>'
    f'<td class="num">{r["mediana"]}</td><td class="num sec">{r["iqr"]}</td>'
    f'<td class="num sec">{esc(r["unidad"])}{SUP_ASUM if r["asumida"] else ""}</td>'
    f'<td class="n">{r["n"]}/{r["total"]}</td>'
    f'<td><span class="tag {clase_etiqueta(r["etiqueta"])}">{r["etiqueta"]}</span></td></tr>'
    for r in CUANT)

filas_capas = "\n".join(
    f'<tr><td class="capa">{n}</td><td><span class="est e-{cl}">{est}</span></td>'
    f'<td class="qtxt">{falta}</td><td class="quien">{quien}</td></tr>'
    for n, est, cl, falta, quien in CAPAS)

filas_ideas = "\n".join(
    f'<tr><td class="capa">{n}</td><td><span class="est e-{cl}">{est}</span></td>'
    f'<td class="qtxt">{resp}</td><td class="qtxt sec">{falta}</td></tr>'
    for n, est, cl, resp, falta in IDEAS)

filas_inv = "\n".join(
    f'<tr><td class="qid">{q}</td><td class="qtxt">{esc(t)}</td>'
    f'<td class="antes">{esc(a)}</td><td class="ahora">{esc(b)}</td></tr>'
    for q, t, a, b in INVERSIONES)

filas_dec = "\n".join(
    f'<div class="dec"><h3><span class="numdec">{i+1}</span>{t}</h3>'
    f'<p>{hoy}</p><p class="ev"><span class="lbl">Evidencia</span>{ev}</p>'
    f'<div class="pide"><span class="lbl">Decisión</span>{pide}</div></div>'
    for i, (t, hoy, ev, pide) in enumerate(DECISIONES))

# figuras: SVG incrustado
bloques_flujo = "\n".join(
    f'<figure class="fig">{figuras.inline(ruta)}</figure>'
    for q, ruta in FIGS["flujos"])
fig_trayectoria = figuras.inline(FIGS["trayectoria"])
fig_movimiento = figuras.inline(FIGS["movimiento"])

bloques_red = "\n".join(
    f'<div class="netrow"><div class="nethead"><b>Panel {p}</b>'
    f'<span class="netn">{MOV_PANEL[p]["n"]} trayectorias · se mueve el {MOV_PANEL[p]["pct"]} %</span>'
    f'</div>{figuras.inline(FIGS["redes"][p])}'
    f'<p class="netlec">{LECTURA.get(p, "")}</p></div>'
    for p in sorted(FIGS["redes"]))

# cifras de cabecera, todas derivadas
T_POS = f'{CTX["pos_resueltas"]} <span class="de">de {CTX["pos_total"]}</span>'
T_CAT = f'{CTX["cat_con_modal"]} <span class="de">de {CTX["cat_total"]}</span>'
T_CUANT = f'{CTX["cuant_fuerte"]} <span class="de">de {CTX["cuant_total"]}</span>'
N_DEC = len(DECISIONES)
CONV_SI = CONV.get("Convergió", 0)
CONV_NO = CONV.get("Se dispersó", 0)
CONV_EST_OK = CONV.get("Estable en acuerdo", 0)
CONV_EST_NO = CONV.get("Estable sin acuerdo", 0)
QS_FLUJO = ", ".join(FIGS["flujo_qids"])
