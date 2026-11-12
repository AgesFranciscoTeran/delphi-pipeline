# -*- coding: utf-8 -*-
"""
Genera el sitio: una portada + una página por panel.

Cada panel es un estudio independiente (distintos panelistas, distintas preguntas), así que
tiene su propia página y no se agregan resultados entre ellos.

    python3 build.py            -> index.html, panel1.html … panel4.html
"""
import os
import html

import datos
import figuras
import contenido
from estilos import CSS

AQUI = os.path.dirname(os.path.abspath(__file__))
def _fecha_de_la_corrida():
    """La fecha del pie sale de la corrida, no de una constante.

    Estaba escrita a mano («31 de agosto de 2026») y siguió ahí durante tres corridas y dos
    cambios de taxonomía: el pie decía agosto en una página generada en septiembre. Es el mismo
    error que las tablas copiadas a mano, en pequeño."""
    MESES = ("enero febrero marzo abril mayo junio julio agosto septiembre octubre "
             "noviembre diciembre").split()
    ext = [r for r in (datos.manifiesto() or []) if r.get("step") == "extract_arguments"]
    sello = ext[-1].get("timestamp") if ext else None
    if sello:
        a, m, d = str(sello)[:10].split("-")
        return f"{int(d)} de {MESES[int(m) - 1]} de {a}"
    import datetime
    hoy = datetime.date.today()
    return f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"


FECHA = _fecha_de_la_corrida()
FIGS = figuras.construir_todo()
PANELES = datos.paneles()


def esc(t):
    return html.escape(str(t))


def clase_etiqueta(e):
    return {"Acuerdo alto": "e-fuerte", "Acuerdo moderado": "e-clara", "Acuerdo bajo": "e-dom",
            "Sin acuerdo": "e-sin", "Insuficiente": "e-insuf",
            "Consenso": "e-fuerte", "Consenso no consolidado": "e-clara",
            "Disenso estable": "e-dom", "Sin estabilizar": "e-sin"}.get(e, "")


def tag(e):
    return f'<span class="tag {clase_etiqueta(e)}">{esc(e)}</span>' if e else "—"


def celda_resultado(r):
    """El resultado (acuerdo × estabilidad) y, debajo, el nivel de acuerdo de la ronda final."""
    if r.get("por_postura"):
        return '<span class="sec">ver «Consenso por postura»</span>'
    return (f'{tag(r.get("resultado"))}<div class="sec" style="margin-top:4px">'
            f'{esc(r["etiqueta"])}</div>')


def barra_postura(r):
    """
    Barra apilada divergente normalizada sobre el TOTAL de panelistas, no sobre los
    clasificados: así el largo es la cobertura y una pregunta con 1 respuesta de 7 no se
    lee como unanimidad. El tramo rayado son las respuestas sin postura asignable.
    """
    n, base = r["n"], r["total"] or r["n"]
    if n == 0:
        return '<div class="bar empty">sin datos suficientes</div>'
    segs = [("A favor", r["favor"], figuras.AZUL), ("Condicional", r["condicional"], figuras.GRIS),
            ("En contra", r["contra"], figuras.ROJO)]
    out, left = [], 0.0
    for nombre, v, color in segs:
        if not v:
            continue
        pct = v / base * 100
        out.append(f'<div class="seg" style="left:{left}%;width:{pct}%;background:{color}" '
                   f'title="{nombre}: {v} de {n} clasificadas ({base} panelistas)">'
                   f'<span>{v if pct >= 9 else ""}</span></div>')
        left += pct
    if base > n:
        out.append(f'<div class="seg gap" style="left:{left}%;width:{(base-n)/base*100}%" '
                   f'title="Sin postura asignable: {base-n} de {base}"></div>')
    return '<div class="bar">' + "".join(out) + "</div>"


def num_decision(clave):
    """Número de una decisión por una palabra de su título. Las referencias en prosa («la
    decisión 5») se escribían a mano y quedaron mal en cuanto la lista se reordenó por
    urgencia: unidades pasó de la 5 a la 3 y el texto seguía diciendo 5."""
    for i, d in enumerate(contenido.DECISIONES, 1):
        if clave.lower() in d["titulo"].lower():
            return i
    return "?"


SUP = '<sup title="Unidad asumida por nosotros, no declarada en la taxonomía">*</sup>'


def tabla_postura(filas):
    if not filas:
        return ""
    cuerpo = "\n".join(
        f'<tr><td class="qid">{r["qid"]}</td><td class="qtxt">{esc(r["texto"])}</td>'
        f'<td class="cbar">{barra_postura(r)}</td><td class="n">{r["n"]}/{r["total"]}</td>'
        f'<td>{celda_resultado(r)}</td></tr>'
        for r in filas)
    return f'''
  <h3>Consenso por postura</h3>
  <div class="leyenda">
    <span><i style="background:{figuras.AZUL}"></i>A favor</span>
    <span><i style="background:{figuras.GRIS}"></i>Condicional</span>
    <span><i style="background:{figuras.ROJO}"></i>En contra</span>
    <span><i class="gapkey"></i>Sin postura asignable</span>
    <span style="color:var(--ink-3)">Los números son panelistas, no porcentajes.</span>
  </div>
  <div class="scroll"><table>
    <caption>Preguntas de sí / no / depende en la ronda final, leídas al nivel de la postura
    y no de la opción concreta.</caption>
    <thead><tr><th>Id</th><th>Pregunta</th><th>Distribución</th><th>n</th><th>Resultado</th></tr></thead>
    <tbody>
{cuerpo}
    </tbody>
  </table></div>'''


def tabla_categ(filas):
    cuerpo = "\n".join(
        f'<tr><td class="qid">{r["qid"]}</td><td class="qtxt">{esc(r["texto"])}</td>'
        f'<td class="opt">{esc(r["opcion"])}</td><td class="n">{r["n"]}/{r["total"]}</td>'
        f'<td>{celda_resultado(r)}</td></tr>'
        for r in filas)
    return f'''
  <h3>Preguntas de opción</h3>
  <div class="scroll"><table>
    <caption>Ronda final, con la opción más votada y cuántas respuestas se pudieron clasificar
    sobre el total del panel. En las preguntas de sí / no el consenso se mide sobre la postura
    (tabla de arriba); aquí la opción muestra el matiz.</caption>
    <thead><tr><th>Id</th><th>Pregunta</th><th>Opción mayoritaria</th><th>n</th><th>Resultado</th></tr></thead>
    <tbody>
{cuerpo}
    </tbody>
  </table></div>'''


def tabla_cuant(filas):
    if not filas:
        return ""
    cuerpo = "\n".join(
        f'<tr><td class="qid">{r["qid"]}</td><td class="qtxt">{esc(r["texto"])}</td>'
        f'<td class="opt">{esc(r["banda"])}</td>'
        f'<td class="num">{r["mediana"]}</td><td class="num sec">{r["iqr"]}</td>'
        f'<td class="num sec">{esc(r["unidad"])}{SUP if r["asumida"] else ""}</td>'
        f'<td class="n">{r["n"]}/{r["total"]}</td>'
        f'<td class="n{" alerta" if r["n_asumidas"] and r["n"] and r["n_asumidas"]/r["n"] >= .4 else ""}">'
        f'{r["n_asumidas"] or "—"}</td>'
        f'<td>{celda_resultado(r)}</td></tr>'
        for r in filas)
    asumidas = sum(r["n_asumidas"] for r in filas)
    aviso = f'''
  <div class="callout warn">
    <span class="ct">Respuestas sin periodo</span>
    <p>La columna «unidad asumida» cuenta las respuestas en las que el panelista no escribió el
    periodo: {asumidas} en este panel. Se les aplica la unidad que declara la pregunta; cuando
    alguien escribe «8 horas al día» en una pregunta medida por semana, se convierte —
    <b>×5</b>.</p>
  </div>''' if asumidas else ""
    return f'''
  <h3>Preguntas numéricas</h3>
  <div class="scroll"><table>
    <caption>Ronda final. El consenso se mide sobre la banda; la mediana y el rango
    intercuartílico describen los valores.</caption>
    <thead><tr><th>Id</th><th>Pregunta</th><th>Banda mayoritaria</th><th>Mediana</th><th>RIC</th><th>Unidad</th><th>n</th>
    <th title="Respuestas contadas cuya unidad se asumió">Unidad<br>asumida</th><th>Resultado</th></tr></thead>
    <tbody>
{cuerpo}
    </tbody>
  </table></div>{aviso}'''


def decisiones_de(panel):
    """El número de cada decisión es su posición en contenido.DECISIONES, que está ordenada por
    urgencia. Así el mismo asunto lleva el mismo número en las cuatro páginas y reordenar la
    lista no obliga a renumerar nada a mano."""
    ds = [(i, d) for i, d in enumerate(contenido.DECISIONES, 1) if panel in d["paneles"]]
    return "\n".join(
        f'<div class="dec"><h3><span class="numdec">{i}</span>{d["titulo"]}</h3>'
        f'<p>{d["hoy"]}</p><p class="ev"><span class="lbl">Evidencia</span>{d["evidencia"]}</p>'
        f'<div class="pide"><span class="lbl">Decisión</span>{d["decision"]}</div></div>'
        for i, d in ds), len(ds)


def banda_corrida():
    """Qué modelo y qué taxonomía produjeron estos números. Sale del manifiesto de la corrida,
    no de un texto escrito a mano: si cambia el modelo, cambia la banda sin que nadie la edite."""
    runs = datos.manifiesto()
    ext = [r for r in runs if r.get("step") == "extract_arguments"] if runs else []
    if not ext:
        return ""
    r = ext[-1]
    fecha = str(r.get("timestamp", ""))[:10]
    # Si la salida es una consolidación de k corridas, decirlo: es la diferencia entre "esto es
    # lo que salió" y "esto es lo que sale la mayoría de las veces".
    consolidado = next((x for x in reversed(runs) if x.get("step") == "consolidar"), None)
    if consolidado:
        k = consolidado.get("k_corridas")
        aviso = (f' Voto mayoritario de <b>{k}</b> corridas independientes, no una sola: '
                 f'ver «Qué es estable y qué no».')
        fecha = str(consolidado.get("timestamp", fecha))[:10]
    else:
        fallidas = int(r.get("n_failed", 0) or 0)
        aviso = (f' Quedaron <b>{fallidas}</b> respuestas sin extraer.' if fallidas else "")
    # La parte mecánica (modelo, fecha, taxonomía) sale del manifiesto. La nota de contexto es
    # editorial y vive en contenido.py, para poder quitarla cuando deje de hacer falta sin
    # tocar la plantilla.
    return (f'<p class="corrida"><b>Resultados preliminares.</b> Clasificados por '
            f'<code>{esc(str(r.get("model", "?")))}</code> el {fecha}, contra la taxonomía '
            f'<code>{esc(str(r.get("taxonomy_hash", "?")))}</code>.{aviso} '
            f'{contenido.NOTA_MODELO} Faltan además las decisiones de taxonomía de la sección '
            f'de abajo.</p>')


def envoltura(titulo, subtitulo, nav, cuerpo, pie_extra=""):
    return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title>
<meta name="robots" content="noindex, nofollow">
<style>
{CSS}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <p class="kicker">Universidad San Francisco de Quito · Estudio Delphi de currículo médico</p>
    <h1>{titulo}</h1>
    <p class="sub">{subtitulo}</p>
    {banda_corrida()}
  </div>
</header>
<nav class="toc"><ul>{nav}</ul></nav>
<main class="wrap">
{cuerpo}
</main>
<footer>
  <div class="wrap">
    <p>Documento de trabajo interno · {FECHA}. {pie_extra}
    Generado desde la salida del pipeline; ningún número está escrito a mano.</p>
  </div>
</footer>
</body>
</html>
'''


def pagina_panel(panel):
    c = datos.contexto_panel(panel)
    f = FIGS[panel]
    decs, n_decs = decisiones_de(panel)
    flujos = "\n".join(f'<figure class="fig">{figuras.inline(ruta)}</figure>'
                       for _, ruta in f["flujos"])
    nav = ('<li><a href="index.html">← Los cuatro paneles</a></li>'
           '<li><a href="#resultados">Resultados</a></li>'
           '<li><a href="#evolucion">Evolución</a></li>'
           '<li><a href="#decisiones">Decisiones</a></li>')
    cuerpo = f'''
<section id="resultados">
  <h2><span class="sec-n">01</span>Lo que decidió el panel {panel}</h2>
  <p class="lead">{c['n_panelistas']} panelistas · {c['n_preguntas']} preguntas ·
  {c['n_rondas']} rondas · {c['n_respuestas']} respuestas. Todo lo de esta página es de este
  panel: no se mezcla con los otros tres.</p>
  <div class="tiles">
    <div class="tile"><div class="v">{c['consenso']} <span class="de">de {c['n_eval']}</span></div>
      <div class="k">preguntas con <b>consenso</b>: acuerdo alto (≥ 70 %) y estable entre las dos
      últimas rondas</div></div>
    <div class="tile"><div class="v">{c['disenso']}</div>
      <div class="k">con <b>disenso estable</b>: el panel no se pone de acuerdo, y no se mueve</div></div>
    <div class="tile"><div class="v">{c['n_cuant']}</div>
      <div class="k">preguntas numéricas, medidas sobre la banda</div></div>
    <div class="tile"><div class="v">{n_decs}</div>
      <div class="k">decisiones de taxonomía que afectan a este panel</div></div>
  </div>
{tabla_postura(c['postura'])}
{tabla_categ(c['cat'])}
{tabla_cuant(c['cuant'])}
{tabla_ejes(panel)}

  <h3>La taxonomía y cómo la usó el panel</h3>
  <p>Cada pregunta de opción con su taxonomía completa: en las de sí / no, la postura y debajo
  sus matices; en las demás, las opciones. La barra es cuántos panelistas eligieron cada una en
  la ronda final. Las que nadie eligió también aparecen, en gris y con 0: muestran qué parte de
  la taxonomía usó el panel y cuál no. A la derecha de cada pregunta, su resultado.</p>
  <figure class="fig">{figuras.inline(f['arbol'])}</figure>
{seccion_argumentos(f)}
</section>

<section id="evolucion">
  <h2><span class="sec-n">02</span>Cómo llegó ahí</h2>
  <p class="lead">Las tablas de arriba son la foto final. Esto es el proceso: cómo se movió la
  gente entre rondas y cómo se fueron formando (o no) los acuerdos.</p>

  <h3>Quién respondió qué</h3>
  <p>Una fila por panelista (el número es su código en el estudio: 301 es el panelista 1 del
  panel 3), una columna por pregunta. Las filas están ordenadas por parecido en la última ronda,
  así que los bloques contiguos son grupos que responden igual, y van en el mismo orden en las
  dos cuadrículas. {contenido.LECTURA_RED.get(panel, '')}</p>
  {cuadricula_postura(f)}
  {cuadricula_opciones(f, panel)}

  <h3>Concentración por pregunta</h3>
  <p>Cuánta gente está en la postura (preguntas de sí / no) u opción mayoritaria de cada
  pregunta, ronda a ronda. El color es el resultado; el último tramo va punteado cuando, entre
  las dos últimas rondas, cambió de opción más del 15 % del panel.</p>
  <figure class="fig">{figuras.inline(f['trayectoria'])}</figure>
  {significado_resultados()}
{seccion_movimiento(f)}

  {'<h3>Quién cambió de opinión, y hacia dónde</h3><p>El color de cada cinta es la postura u '
   'opción <b>de origen</b>, así que se puede seguir a dónde fue a parar cada bloque inicial; '
   'las cintas tenues son quienes no se movieron. Estas son las preguntas con más movimiento '
   'del panel.</p>' + flujos if flujos else ''}
</section>

<section id="decisiones">
  <h2><span class="sec-n">03</span>Lo que hace falta decidir</h2>
  <span class="audience">Para Emily</span>
  <p class="lead">{n_decs} de las {len(contenido.DECISIONES)} decisiones de taxonomía abiertas
  afectan a este panel. Ninguna requiere saber programación: son decisiones sobre cómo debe
  estar definida la taxonomía.</p>
  <p class="lead">{contenido.CERRADAS}</p>
{decs}
</section>
'''
    return envoltura(f"Panel {panel}", contenido.NOTA_PANELES, nav, cuerpo,
                     f"Panel {panel} de 4.")


def parrafo_conclusiones():
    """Cuántas conclusiones cambiarían con una sola corrida. Sale de los CSV, no del texto."""
    e = datos.estabilidad_conclusiones()
    if not e:
        return ""
    if e["n_cambian"]:
        cuales = ", ".join(e["cambian"])
        mayoria = ("y en todas el voto coincide con lo que dice la mayoría de las corridas"
                   if not e["contra_mayoria"] else
                   "y en <b>%s</b> el voto no coincide con la mayoría de las corridas"
                   % ", ".join(e["contra_mayoria"]))
        detalle = (f'<b>{e["n_cambian"]} de {e["n"]}</b> conclusiones de ronda final cambian '
                   f'según qué corrida suelta se mire ({cuales}), {mayoria}.')
    else:
        detalle = f'Ninguna de las {e["n"]} conclusiones de ronda final cambia entre corridas.'
    return (f'<p><b>Lo que importa es si cambian las conclusiones.</b> {detalle} Las respuestas '
            f'en las que las {e["k"]} corridas no forman mayoría quedan sin clasificar en vez de '
            f'resolverse por el orden de las corridas.</p>')


NOTA_HUECOS = ('<p class="nota-fig"><b>Celdas sin color.</b> Vacía: el panelista no respondió esa '
               'pregunta en esa ronda (por ejemplo, porque no participó en ella). <b>FT</b>: '
               'respondió, pero algo que no contesta la pregunta (fuera de tema); no cuenta en el '
               'consenso. <b>?</b>: respondió, pero la respuesta no encaja en ninguna opción de la '
               'taxonomía, o las tres corridas del sistema no se pusieron de acuerdo.</p>')


def cuadricula_postura(f):
    ruta = f["cuadricula"].get("postura")
    if not ruta:
        return ""
    return (f'<h4>Preguntas de sí / no: la postura</h4>'
            f'<div class="leyenda"><span><i style="background:{figuras.AZUL}"></i>✓ A favor</span>'
            f'<span><i style="background:{figuras.GRIS}"></i>~ Condicional</span>'
            f'<span><i style="background:{figuras.ROJO}"></i>✕ En contra</span>'
            f'<span><i style="background:{figuras.OTRAS}"></i>· Sin postura: eligió una opción a '
            f'la que la taxonomía no asigna postura (p. ej. «Obligatory» en P2_Q5)</span></div>'
            f'<figure class="fig">{figuras.inline(ruta)}</figure>{NOTA_HUECOS}')


def cuadricula_opciones(f, panel):
    ruta = f["cuadricula"].get("opciones")
    if not ruta:
        return ""
    return (f'<h4>Preguntas de opciones</h4><p>Cada letra es una opción de esa pregunta (debajo, '
            f'qué es cada una); sólo las tres más elegidas llevan color. <b>Las letras y los '
            f'colores se comparan dentro de su columna</b>: la A de una pregunta no tiene nada que '
            f'ver con la A de otra, y el azul aquí no significa «a favor».</p>'
            f'<figure class="fig">{figuras.inline(ruta)}</figure>'
            f'{figuras.leyenda_opciones(panel)}{NOTA_HUECOS}')


def seccion_argumentos(f):
    if not f.get("argumentos"):
        return ""
    perfiles = f'<figure class="fig">{figuras.inline(f["perfiles"])}</figure>' if f.get("perfiles") else ""
    panelistas = (f'<h4>Cómo razona cada panelista</h4><p>En cuántas preguntas (ronda final) dio '
                  f'cada panelista cada tipo de argumento. Si una fila se concentra en una columna, '
                  f'esa persona razona siempre desde el mismo lugar; si se reparte, cambia según la '
                  f'pregunta. Más oscuro = más preguntas.</p>'
                  f'<figure class="fig">{figuras.inline(f["perfil_panelistas"])}</figure>'
                  if f.get("perfil_panelistas") else "")
    grafo = (f'<h4>El mapa de argumentos del panel</h4><p>Cada pregunta, con su postura u opción '
             f'en la ronda final (izquierda), unida a los perfiles de argumento que la sostienen '
             f'(derecha). Los perfiles son los mismos para todas las preguntas, así que se ve qué '
             f'razones atraviesan varias preguntas del panel. El tamaño de cada nodo y el grosor de '
             f'cada línea son panelistas; las respuestas sin argumento se cuentan en la etiqueta y '
             f'no se dibujan.</p><figure class="fig">{figuras.inline(f["grafo"])}</figure>'
             if f.get("grafo") else "")
    return f'''
  <h3>Por qué: los argumentos</h3>
  <p>{contenido.NOTA_ARGUMENTOS}</p>
  {perfiles}
  {grafo}
  {panelistas}
  <p>Pregunta por pregunta: a la izquierda, la postura (u opción) de cada panelista en la
  ronda final; a la derecha, el argumento que da. Cada cinta son panelistas.</p>
  <figure class="fig">{figuras.inline(f["argumentos"])}</figure>'''


def seccion_movimiento(f):
    if not f.get("movimiento"):
        return ""
    return f'''
  <h3>Hacia dónde se movió la gente</h3>
  <p>Entre dos rondas seguidas, cada panelista en cada pregunta se mantuvo, se movió hacia la
  postura u opción mayoritaria de la ronda anterior (la que vio en la síntesis), se alejó de
  ella, o cambió entre opciones que no eran la mayoría. Es la pregunta de fondo del Delphi: si
  la retroalimentación produce convergencia. Muchos movimientos «hacia la mayoría» indican que
  el panel se alinea con lo que se le muestra; muchos «se alejó» o «otro cambio», que la
  retroalimentación no lo arrastra.</p>
  <figure class="fig">{figuras.inline(f["movimiento"])}</figure>'''


def tabla_ejes(panel):
    filas = datos.ejes_secundarios(panel)
    if not filas:
        return ""
    cuerpo = "\n".join(
        f'<tr><td class="qid">{r["qid"]}</td><td class="qtxt">{esc(r["texto"])}</td>'
        f'<td class="sec">{esc(r["eje"])}</td><td class="opt">{esc(r["opcion"])}</td>'
        f'<td class="n">{r["n"]}</td><td class="n sec">{r["mencionan"]} de {r["total"]}</td>'
        f'<td>{celda_resultado(r)}</td></tr>' for r in filas)
    return f'''
  <h3>Otros ejes de las preguntas</h3>
  <div class="scroll"><table>
    <caption>Varias preguntas tienen más de una dimensión (por ejemplo, cuántas horas <i>y</i> de
    qué depende). Cada eje se mide aparte, con el mismo criterio, entre quienes hablaron de él
    («lo mencionan», sobre todas las respuestas de la pregunta en todas las rondas): no decir
    nada de una dimensión no es estar en desacuerdo. Ronda final.</caption>
    <thead><tr><th>Id</th><th>Pregunta</th><th>Eje</th><th>Opción mayoritaria</th><th>n</th>
    <th>Lo mencionan</th><th>Resultado</th></tr></thead>
    <tbody>
{cuerpo}
    </tbody>
  </table></div>'''


def significado_resultados():
    """Qué significa cada resultado, con el mismo color que en la figura."""
    filas = "".join(
        f'<div class="sig"><span class="chip"><i style="background:'
        f'{figuras.COL_RESULTADO.get(nombre, figuras.OTRAS)}"></i><b>{nombre}</b></span>'
        f'<span>{texto}</span></div>'
        for nombre, texto in contenido.SIGNIFICADO_RESULTADOS)
    return (f'<div class="callout"><span class="ct">Qué significa cada resultado</span>'
            f'<div class="sigs">{filas}</div></div>')


def portada():
    filas_capas = "\n".join(
        f'<tr><td class="capa">{n}</td><td><span class="est e-{cl}">{est}</span></td>'
        f'<td class="qtxt">{falta}</td><td class="quien">{quien}</td></tr>'
        for n, est, cl, falta, quien in contenido.CAPAS)
    tarjetas = []
    for p in PANELES:
        c = datos.contexto_panel(p)
        _, n_decs = decisiones_de(p)
        tarjetas.append(
            f'<a class="panelcard" href="panel{p}.html"><h3>Panel {p}</h3>'
            f'<p class="pc-meta">{c["n_panelistas"]} panelistas · {c["n_preguntas"]} preguntas · '
            f'{c["n_rondas"]} rondas</p>'
            f'<p class="pc-res"><b>{c["consenso"]} de {c["n_eval"]}</b> preguntas con consenso · '
            f'<b>{c["disenso"]}</b> con disenso estable</p>'
            f'<p class="pc-pend">{n_decs} decisi{"ón" if n_decs == 1 else "ones"} '
            f'pendiente{"" if n_decs == 1 else "s"} · {c["n_cuant"]} '
            f'pregunta{"" if c["n_cuant"] == 1 else "s"} numérica{"" if c["n_cuant"] == 1 else "s"}'
            f'</p></a>')
    nav = ('<li><a href="#paneles">Los paneles</a></li>'
           '<li><a href="#metodo">Cómo funciona</a></li>'
           '<li><a href="#estado">Estado</a></li>'
           '<li><a href="#confianza">Confiabilidad</a></li>'
           '<li><a href="revision.html">Qué revisar a mano</a></li>')
    cuerpo = f'''
<section id="paneles">
  <h2><span class="sec-n">01</span>Cuatro estudios, cuatro páginas</h2>
  <p class="lead">{contenido.NOTA_PANELES}</p>
  <div class="panelgrid">
{"".join(tarjetas)}
  </div>
  <div class="callout">
    <span class="ct">Por qué no hay una tabla que los junte</span>
    <p>Una versión anterior de esta página agregaba los cuatro paneles y comparaba entre ellos
    —cuánto se mueve cada uno, cuánto converge—. Se retiró: con panelistas distintos y
    preguntas distintas, la variación entre paneles está confundida con la dificultad de sus
    preguntas, y cuatro estudios no comparables no sostienen ninguna conclusión.</p>
  </div>
</section>

<section id="metodo">
  <h2><span class="sec-n">02</span>Cómo se obtienen los números</h2>
  <p>Los panelistas responden con texto libre. Emily define, para cada pregunta, el conjunto
  cerrado de respuestas posibles; un modelo de lenguaje alojado <b>en el servidor de la
  universidad</b> —los datos nunca salen de la infraestructura institucional— asigna cada
  respuesta a una de esas opciones; y se mide, ronda por ronda, cuánto se concentra el panel.
  El sistema no inventa categorías: si una respuesta no encaja en ninguna opción, queda marcada
  como tal en vez de forzarse.</p>
  <figure class="fig">{figuras.inline(figuras.fig_metodo())}</figure>
  <p>{contenido.CRITERIOS}</p>
</section>

<section id="estado">
  <h2><span class="sec-n">03</span>Estado del método</h2>
  <p class="lead">En qué punto está cada parte y de quién depende.</p>
  <div class="scroll"><table class="tcapas">
    <thead><tr><th>Parte</th><th>Estado</th><th>Qué falta</th><th>Depende de</th></tr></thead>
    <tbody>
{filas_capas}
    </tbody>
  </table></div>
  <div class="callout">
    <span class="ct">Qué hay que hacer ahora, en orden</span>
    <p><b>1. Etiquetar a ciegas</b> la muestra de validación (Emily y una segunda persona). La
    validación del método necesita 200–300 respuestas etiquetadas por dos personas, repartidas
    entre los cuatro paneles; hoy hay 44 y las etiqueta una sola.
    <br><b>2. Revisar P3_Q7 y P4_Q6</b> (Emily), después de la hoja ciega.
    <br><b>3. Poner el veredicto</b> a la hoja de contraste con las síntesis de los
    facilitadores.</p>
  </div>
</section>

<section id="confianza">
  <h2><span class="sec-n">04</span>Confiabilidad</h2>
  <p class="lead">La respuesta a «¿por qué creerle a estos números?». No hace falta leerla para
  usar los resultados.</p>
  <div class="callout warn">{contenido.NOTA_CONFIANZA}</div>

  <h3>Consistencia <span class="est e-ok">Modelo actual</span></h3>
  <p>Treinta panelistas repitieron su respuesta palabra por palabra entre rondas, y el sistema les
  dio la misma etiqueta en los treinta casos: 24 de opción y 6 numéricas. Se cumple en el voto
  consolidado y en cada una de las tres corridas por separado.</p>

  <h3>Acuerdo con la codificación manual <span class="est e-wip">Modelo anterior</span></h3>
  <p>Emily etiquetó a ciegas 44 respuestas sin ver la salida del sistema. Con el modelo anterior
  coincidían en el 75 % (κ = 0,72), y leídas a nivel de postura, en 21 de 24: el rango habitual
  entre dos codificadores humanos. <b>Ese número no se puede recalcular con la taxonomía
  actual.</b> En 19 de las 44 respuestas Emily propuso una categoría que entonces no existía, y
  las versiones v3 y v4 incorporaron varias de ellas («First years: A-F / Last years:
  Pass-Fail», «With passing exam», «Final years»). Ahora el modelo elige justo esa opción y la
  puntuación la cuenta como desacuerdo, porque compara contra etiquetas hechas para opciones que
  ya no existen. Hace falta etiquetar de nuevo contra la v4. Lo más eficiente es hacerlo
  directamente con la muestra de la validación formal: 200–300 respuestas estratificadas por
  panel, con dos codificadores.</p>

  <h3>Contraste con los facilitadores <span class="est e-wip">Modelo anterior</span></h3>
  <p>Con el modelo anterior, las conclusiones coincidían con las síntesis escritas a mano, y en
  dos casos la síntesis humana era la que se equivocaba. Para rehacerlo, la hoja que pone cada
  distribución al lado de su síntesis ya está generada con la corrida actual; falta que una
  persona le ponga el veredicto a cada pregunta-ronda. Un caso ya se ve sin la hoja: en P3_Q1 la
  síntesis de la ronda 1 cambió la pregunta de «por semana» a «por día», y el panel la
  siguió.</p>

  <h3>Dos modelos distintos <span class="est e-wip">Modelo anterior</span></h3>
  <p>Se probaron dos sistemas de familias diferentes sobre las mismas 44 respuestas, con
  resultados equivalentes; de los ocho errores que le quedaban al elegido, siete eran
  exactamente las mismas respuestas que fallaba el otro. Hoy el servidor de modelos rápido sirve
  un solo modelo. Hay otros en la máquina, pero cargarlos ocupa memoria de GPU compartida y hay
  que pedirlo antes.</p>

  <h3>Qué es estable y qué no</h3>
  <p>{contenido.ESTABILIDAD}</p>
  <p>{contenido.ESTABILIDAD_CONSECUENCIA}</p>
  {parrafo_conclusiones()}

  <h3>Sobre los números anteriores</h3>
  <p>Si alguien recuerda conclusiones distintas de una versión previa: el análisis anterior tenía
  un error que corría un lugar las opciones e invertía cinco conclusiones. Está corregido y
  comprobado contra las síntesis de los facilitadores, que es como se detectó.</p>
</section>
'''
    return envoltura("Qué decidió cada panel",
                     "Resultados del análisis computacional del estudio Delphi, panel por panel, "
                     "y lo que hace falta para cerrar el artículo de método.", nav, cuerpo)


def _coma(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")


def pagina_revision():
    """Experimento de señales: qué respuestas debería revisar una persona.

    Lee la salida de tools/senales.py --corrida y tools/fig_senales.py (ningún número a mano).
    """
    import glob
    import sys
    carpetas = sorted(glob.glob(os.path.join(datos.RUTA_RESULTADOS, "senales_*")))
    nav = ('<li><a href="index.html">← Los cuatro paneles</a></li>'
           '<li><a href="#problema">El problema</a></li>'
           '<li><a href="#senales">Las señales</a></li>'
           '<li><a href="#resultados">Resultados</a></li>'
           '<li><a href="#falta">Qué falta</a></li>')
    if not carpetas:
        return envoltura("Qué revisar a mano", "Experimento de señales.", nav,
                         '<section><p>Esta corrida no tiene el experimento de señales.</p></section>')
    carpeta = carpetas[-1]
    raiz = os.path.dirname(AQUI)
    for sub_ in ("tools", "pipeline"):
        if os.path.join(raiz, sub_) not in sys.path:
            sys.path.insert(0, os.path.join(raiz, sub_))
    import fig_senales as fs
    from stance_map import STANCE_MAP, stance_of

    t, puntajes, d = fs.calcular(carpeta)
    ruta_svg = os.path.join(figuras.SALIDA, "fig_senales.svg")
    fs.dibujar(t, puntajes, [ruta_svg], idioma="es")
    s = {r.key: r for r in t.itertuples()}

    n, pos = len(d), int(d.inestable.sum())
    aparta = int(d.se_aparta.sum()) if "se_aparta" in d else 0
    inest = d[d.inestable == 1]
    n_num = int(inest.question_type.isin(["quantitative", "hybrid"]).sum())
    cat = inest[~inest.question_type.isin(["quantitative", "hybrid"])]

    def postura(r):
        q = f"P{r.Panel}_Q{r.Question}"
        if q not in STANCE_MAP:
            return "sin"
        ks = [c for c in ("k1", "k2", "k3", "kc") if c in r.index]
        return "misma" if len({stance_of(q, r[k])[0] for k in ks}) == 1 else "cambia"
    cp = cat.apply(postura, axis=1).value_counts() if len(cat) else {}
    misma, cambia, sin = (int(cp.get(k, 0)) for k in ("misma", "cambia", "sin"))
    cita_vacia = d.S3_cita.eq(0)
    rasgos = d.S5_alarmas.gt(0)

    def auc(k):
        r = s[k]
        return f"AUC {_coma(r.auc)}, IC 95 % {_coma(r.ci_low)}–{_coma(r.ci_high)}"

    def det(k):
        return f"{s[k].detected_at_20:.0f} %"

    cuerpo = f'''
<section id="problema">
  <h2><span class="sec-n">01</span>El problema</h2>
  <p class="lead">El modelo que clasifica las respuestas no es del todo repetible y no explica por
  qué elige una etiqueta. Revisar a mano las {n} respuestas anularía la ventaja de automatizar.
  La pregunta es <b>qué señal, calculada con una sola corrida, indica las respuestas que una
  persona debería revisar</b>.</p>
  <p>Mientras no estén las etiquetas de Emily, la prueba es la <b>inestabilidad</b>: se corrió
  cuatro veces el mismo prompt y se marcó cada respuesta cuya etiqueta cambia entre corridas. Una
  buena señal debería poner esas respuestas al principio de la lista de revisión. El diseño se
  fijó por escrito el 9-11-2026, antes de calcular nada (docs/experimento_senales.md).</p>
</section>

<section id="senales">
  <h2><span class="sec-n">02</span>Las señales</h2>
  <div class="scroll"><table>
    <thead><tr><th>Señal</th><th>Qué mide</th><th>Llamadas extra al modelo</th></tr></thead>
    <tbody>
      <tr><td>Longitud</td><td>respuesta más corta = más sospechosa. Sólo sirve de línea base.</td><td>ninguna</td></tr>
      <tr><td>Embeddings</td><td>parecido del texto con cada opción (bge-m3, en el servidor de la
        universidad); sospechosa si la opción asignada no es de las más parecidas. Sólo preguntas de opciones.</td><td>ninguna</td></tr>
      <tr><td>Reglas de código</td><td>(1) pregunta numérica, el texto tiene un número y no hay
        banda; (2) la opción asignada tiene una versión general o específica en la taxonomía
        («No» / «No, subjective…»).</td><td>ninguna</td></tr>
      <tr><td>Probabilidades del modelo</td><td>qué tan seguro está el modelo del token que decide la
        etiqueta, frente a la alternativa siguiente.</td><td>ninguna (la misma llamada)</td></tr>
      <tr><td>Cita verificada</td><td>se le muestra la etiqueta y se le pide el fragmento literal que
        la sostiene; el código comprueba que exista. Cita vacía = máxima sospecha.</td><td>una por respuesta</td></tr>
      <tr><td>Rasgos atómicos</td><td>sin ver la etiqueta, el modelo dice si la respuesta es sí / no
        / condicional, si da un número, si dice «depende» y si habla del tema; reglas fijas marcan
        las contradicciones con la etiqueta.</td><td>una por respuesta</td></tr>
      <tr><td>Combinación</td><td>todas juntas, con regresión logística y validación cruzada.</td><td>—</td></tr>
    </tbody>
  </table></div>
</section>

<section id="resultados">
  <h2><span class="sec-n">03</span>Resultados</h2>
  <p class="lead">De {n} respuestas, <b>{pos} cambian de etiqueta</b> entre las cuatro corridas
  ({_coma(100 * pos / n, 1)} %){f" y en {aparta} la cuarta corrida se aparta del voto de las otras tres" if aparta else ""}.
  Ninguna señal de una sola corrida las encuentra bien: correr varias veces y votar sigue siendo
  necesario.</p>
  <figure class="fig">{figuras.inline(ruta_svg)}
    <figcaption><b>A.</b> Qué tan bien ordena cada señal las respuestas inestables: 0,5 es el azar
    y 1 sería perfecto; la línea gris es el intervalo de confianza. <b>B.</b> Si una persona revisa
    las respuestas de más a menos sospechosas, qué parte de las inestables encuentra; el punto
    marca el 20 % revisado. La diagonal es revisar al azar.</figcaption></figure>
  <h3>Qué se encontró</h3>
  <p><b>Reglas de código</b>: la mejor ({auc("R")}). Revisando el 20 % que marcan como más
  sospechoso se encuentra el {det("R")} de las inestables. Combinar todas las señales no las mejora
  ({auc("comb")}; {det("comb")} al 20 %).</p>
  <p><b>Rasgos atómicos</b> ({auc("S5")}) y <b>cita verificada</b> ({auc("S3")}): débiles, pero
  se explican solas. En {int(cita_vacia.sum())} respuestas el modelo, viendo su propia etiqueta, no
  encontró nada en el texto que la sostuviera; {int((cita_vacia & d.inestable.eq(1)).sum())} de ellas
  son inestables. Los rasgos contradicen la etiqueta en {int(rasgos.sum())} respuestas,
  {int((rasgos & d.inestable.eq(1)).sum())} inestables.</p>
  <p><b>Embeddings</b> ({auc("S4")}, sólo preguntas de opciones): el intervalo incluye el azar.
  Miden de qué habla el texto, no qué postura toma: no distinguen un «sí» de un «no» sobre lo mismo.</p>
  <p><b>Probabilidades del modelo</b> ({auc("S2")}): no sirven. Después de razonar, el modelo está
  casi seguro de todas sus etiquetas —el margen nunca baja de {_coma(d.S2_margen.min(), 0)} en
  logprob—, incluso de las que cambian en otra corrida.</p>
  <h3>De dónde viene la inestabilidad</h3>
  <p>Casi toda viene del instrumento, no de cómo lee el modelo:</p>
  <ul>
    <li><b>{n_num} respuestas numéricas</b> con el periodo ambiguo («4 hours into two days», «an hour
    and a half, three days a week»): unas corridas lo leen por sesión y otras por semana.</li>
    <li><b>{len(cat)} respuestas de opciones</b>: en {misma} sólo cambia el matiz dentro de la misma
    postura («No» / «No, subjective…»), lo que no afecta el consenso, que en las preguntas sí/no
    se mide por postura; {cambia} cambian de postura y {sin} son de preguntas sin postura sí/no.</li>
  </ul>
  <div class="callout">
    <span class="ct">Para el artículo</span>
    <p>La auditabilidad no la da el razonamiento del modelo ni los embeddings. La dan tres cosas
    que cualquiera puede verificar: cada etiqueta con su cita comprobada por código, una regla
    medida que decide qué se revisa, y una persona que revisa esos casos.</p>
  </div>
</section>

<section id="falta">
  <h2><span class="sec-n">04</span>Qué falta</h2>
  <p>La prueba que cuenta es contra personas: <b>qué señales encuentran los errores del modelo
  frente a las etiquetas de Emily</b> en la muestra de validación. Las señales de las {n}
  respuestas ya están guardadas; cuando llegue la hoja, el análisis se corre sin volver a llamar
  al modelo. Los umbrales y la combinación no se ajustan mirando esas etiquetas.</p>
  <p>Hay que confirmar también si Emily vio las etiquetas del modelo al codificar: cambia cómo se
  describe la validación.</p>
</section>
'''
    return envoltura("Qué revisar a mano",
                     "Experimento de señales: cómo elegir las respuestas que una persona debería "
                     "revisar. Borrador para el artículo de método.", nav, cuerpo)


def escribir(nombre, texto):
    ruta = os.path.join(AQUI, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"  {nombre} — {len(texto):,} bytes")


if __name__ == "__main__":
    print("Sitio generado:")
    escribir("index.html", portada())
    for p in PANELES:
        escribir(f"panel{p}.html", pagina_panel(p))
    escribir("revision.html", pagina_revision())
