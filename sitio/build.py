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
FECHA = "31 de agosto de 2026"
FIGS = figuras.construir_todo()
PANELES = datos.paneles()


def esc(t):
    return html.escape(str(t))


def clase_etiqueta(e):
    return {"Consenso fuerte": "e-fuerte", "Mayoría clara": "e-clara",
            "Opción dominante": "e-dom", "Convergencia moderada": "e-clara",
            "Sin consenso": "e-sin", "Insuficiente": "e-insuf"}.get(e, "")


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


SUP = ('<sup title="Unidad asumida por nosotros, no declarada en la taxonomía '
       '(decisión 7)">*</sup>')


def tabla_postura(filas):
    if not filas:
        return ""
    cuerpo = "\n".join(
        f'<tr><td class="qid">{r["qid"]}</td><td class="qtxt">{esc(r["texto"])}</td>'
        f'<td class="cbar">{barra_postura(r)}</td><td class="n">{r["n"]}/{r["total"]}</td>'
        f'<td><span class="tag {clase_etiqueta(r["etiqueta"])}">{r["etiqueta"]}</span></td></tr>'
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
        f'<td><span class="tag {clase_etiqueta(r["etiqueta"])}">{r["etiqueta"]}</span></td></tr>'
        for r in filas)
    return f'''
  <h3>Preguntas de opción</h3>
  <div class="scroll"><table>
    <caption>Ronda final, con la opción más votada y cuántas respuestas se pudieron clasificar
    sobre el total del panel.</caption>
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
        f'<td class="num">{r["mediana"]}</td><td class="num sec">{r["iqr"]}</td>'
        f'<td class="num sec">{esc(r["unidad"])}{SUP if r["asumida"] else ""}</td>'
        f'<td class="n">{r["n"]}/{r["total"]}</td>'
        f'<td class="n{" alerta" if r["n_asumidas"] and r["n"] and r["n_asumidas"]/r["n"] >= .4 else ""}">'
        f'{r["n_asumidas"] or "—"}</td>'
        f'<td><span class="tag {clase_etiqueta(r["etiqueta"])}">{r["etiqueta"]}</span></td></tr>'
        for r in filas)
    asumidas = sum(r["n_asumidas"] for r in filas)
    aviso = f'''
  <div class="callout warn">
    <span class="ct">Estos números todavía no son reportables</span>
    <p>La columna «unidad asumida» cuenta las respuestas cuya unidad tuvo que adivinar el
    sistema: {asumidas} en este panel. Cuando alguien escribe «8 horas» sin decir si es al día
    o a la semana, se toma la unidad de la pregunta; cuando escribe «8 horas al día» en una
    pregunta medida por semana, se convierte — <b>×5</b>. El mismo texto vale 8 o 40.</p>
    <p>Corrimos el análisis dos veces sobre los mismos datos y con el mismo código: las
    preguntas de opción dieron <b>exactamente el mismo resultado</b>, y 4 de las 12 numéricas
    <b>cambiaron de etiqueta</b>. Hasta que se cierre la decisión 5, esta tabla es diagnóstico,
    no resultado.</p>
  </div>''' if asumidas else ""
    return f'''
  <h3>Preguntas numéricas</h3>
  <div class="scroll"><table>
    <caption>Ronda final. La mediana y el rango intercuartílico son más robustos que el promedio
    con paneles de este tamaño.</caption>
    <thead><tr><th>Id</th><th>Pregunta</th><th>Mediana</th><th>RIC</th><th>Unidad</th><th>n</th>
    <th title="Respuestas contadas cuya unidad se asumió">Unidad<br>asumida</th><th>Resultado</th></tr></thead>
    <tbody>
{cuerpo}
    </tbody>
  </table></div>{aviso}'''


def decisiones_de(panel):
    ds = [d for d in contenido.DECISIONES if panel in d["paneles"]]
    return "\n".join(
        f'<div class="dec"><h3><span class="numdec">{d["n"]}</span>{d["titulo"]}</h3>'
        f'<p>{d["hoy"]}</p><p class="ev"><span class="lbl">Evidencia</span>{d["evidencia"]}</p>'
        f'<div class="pide"><span class="lbl">Decisión</span>{d["decision"]}</div></div>'
        for d in ds), len(ds)


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
    <div class="tile"><div class="v">{c['resueltas']} <span class="de">de {c['n_cat']}</span></div>
      <div class="k">preguntas de opción <b>resueltas</b>: consenso fuerte o mayoría clara</div></div>
    <div class="tile"><div class="v">{c['convergieron']}</div>
      <div class="k">preguntas donde el panel se acercó entre la primera ronda y la última</div></div>
    <div class="tile"><div class="v">{c['n_cuant']}</div>
      <div class="k">preguntas numéricas, {'todas preliminares' if c['n_cuant'] else '—'}</div></div>
    <div class="tile"><div class="v">{n_decs}</div>
      <div class="k">decisiones de taxonomía que afectan a este panel</div></div>
  </div>
{tabla_postura(c['postura'])}
{tabla_categ(c['cat'])}
{tabla_cuant(c['cuant'])}
</section>

<section id="evolucion">
  <h2><span class="sec-n">02</span>Cómo llegó ahí</h2>
  <p class="lead">Las tablas de arriba son la foto final. Esto es el proceso: cómo se movió la
  gente entre rondas y cómo se fueron formando (o no) los acuerdos.</p>

  <h3>Quién coincide con quién, ronda por ronda</h3>
  <p>Cada círculo es un panelista y cada línea, cuánto coinciden sus respuestas en esa ronda:
  tenue si coinciden en más de la mitad de las preguntas, marcada si en tres cuartos o más. El
  tamaño del círculo son sus vínculos fuertes. <b>La posición de cada panelista se calcula una
  sola vez sobre las tres rondas</b>, así que lo que cambia entre los tres dibujos es el
  acuerdo, no el diagrama.</p>
  <figure class="fig">{figuras.inline(f['red'])}
    <figcaption>{contenido.LECTURA_RED.get(panel, '')}</figcaption>
  </figure>

  <h3>Concentración por pregunta</h3>
  <p>Cuánta gente está en la opción mayoritaria de cada pregunta, ronda a ronda.</p>
  <figure class="fig">{figuras.inline(f['trayectoria'])}</figure>

  {'<h3>Quién cambió de opinión, y hacia dónde</h3><p>El color de cada cinta es la opción '
   '<b>de origen</b>, así que se puede seguir a dónde fue a parar cada bloque inicial; las '
   'cintas tenues son quienes no se movieron. Estas son las preguntas con más movimiento del '
   'panel.</p>' + flujos if flujos else ''}
</section>

<section id="decisiones">
  <h2><span class="sec-n">03</span>Lo que hace falta decidir</h2>
  <span class="audience">Para Emily</span>
  <p class="lead">{n_decs} de las ocho decisiones de taxonomía afectan a este panel. Ninguna
  requiere saber programación: son decisiones sobre cómo debe estar definida la taxonomía.</p>
{decs}
</section>
'''
    return envoltura(f"Panel {panel}", contenido.NOTA_PANELES, nav, cuerpo,
                     f"Panel {panel} de 4.")


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
            f'<p class="pc-res"><b>{c["resueltas"]} de {c["n_cat"]}</b> preguntas de opción '
            f'resueltas · <b>{c["convergieron"]}</b> convergieron</p>'
            f'<p class="pc-pend">{n_decs} decisiones pendientes · {c["n_cuant"]} preguntas '
            f'numéricas preliminares</p></a>')
    nav = ('<li><a href="#paneles">Los paneles</a></li>'
           '<li><a href="#metodo">Cómo funciona</a></li>'
           '<li><a href="#estado">Estado</a></li>'
           '<li><a href="#confianza">Confiabilidad</a></li>')
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
    <p><b>1. Una sesión con Emily</b> para cerrar las decisiones de taxonomía, empezando por la
    número 5 (unidades), que es la que hace que los resultados numéricos cambien entre corridas.
    <br><b>2. Conseguir un segundo codificador.</b> Con cuatro artículos separados hace falta
    validar cada panel por su cuenta, y hoy hay unas 11 respuestas etiquetadas por panel.
    <br><b>3. Confirmar con Jonathan</b> el manejo de datos del estudio de eutanasia.</p>
  </div>
</section>

<section id="confianza">
  <h2><span class="sec-n">04</span>Confiabilidad</h2>
  <p class="lead">La respuesta a «¿por qué creerle a estos números?». No hace falta leerla para
  usar los resultados.</p>

  <h3>Acuerdo con la codificación manual</h3>
  <p>Emily etiquetó a ciegas 44 respuestas sin ver la salida del sistema. Coinciden en el 75 %
  (κ = 0,72), y leídas a nivel de postura, en 21 de 24. Es el rango habitual entre dos
  codificadores humanos en investigación cualitativa. Esas 44 están repartidas entre los cuatro
  paneles: unas once por panel, insuficiente para reportar la fiabilidad de cada artículo por
  separado. La validación formal necesita 200–300 <b>por panel</b> y un segundo codificador.</p>

  <h3>Otras tres comprobaciones</h3>
  <p><b>Consistencia:</b> treinta panelistas repitieron su respuesta palabra por palabra entre
  rondas y el sistema les dio la misma etiqueta en los treinta casos.
  <b>Contraste con los facilitadores:</b> las conclusiones coinciden con las síntesis escritas a
  mano — y en dos casos la síntesis humana es la que se equivoca, lo que es en sí un argumento a
  favor de tener registro de cada respuesta.
  <b>Dos modelos distintos:</b> se probaron dos sistemas de familias diferentes sobre las mismas
  44 respuestas, con resultados equivalentes; de los ocho errores que le quedan al elegido,
  siete son exactamente las mismas respuestas que falla el otro.</p>

  <h3>Qué es estable y qué no</h3>
  <p>Dos corridas completas del mismo código sobre los mismos datos: <b>las preguntas de opción
  y las posturas dieron resultados idénticos</b>; <b>4 de las 12 numéricas cambiaron de
  etiqueta</b>. La parte que sólo requiere elegir entre opciones cerradas es estable; la que
  exige interpretar una magnitud, no. Por eso los resultados numéricos de cada panel están
  marcados como preliminares.</p>
  <p>El servidor tampoco garantiza resultados idénticos entre corridas aunque se fijen todos los
  parámetros. Lo que hace reproducible un resultado es archivar el registro de la corrida, que
  el sistema ya genera.</p>

  <h3>Sobre los números anteriores</h3>
  <p>Si alguien recuerda conclusiones distintas de una versión previa: el análisis anterior tenía
  un error que corría un lugar las opciones e invertía cinco conclusiones. Está corregido y
  comprobado contra las síntesis de los facilitadores, que es como se detectó.</p>
</section>
'''
    return envoltura("Qué decidió cada panel",
                     "Resultados del análisis computacional del estudio Delphi, panel por panel, "
                     "y lo que hace falta para cerrar cada artículo.", nav, cuerpo)


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
