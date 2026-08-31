import os
from cabecera import *   # datos, figuras y texto editorial

HTML = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Delphi Pipeline — Estado y decisiones pendientes</title>
<meta name="description" content="Resultados del análisis computacional del estudio Delphi de currículo médico, USFQ. Estado del pipeline, validación y decisiones de taxonomía pendientes.">
<!-- Documento de trabajo con resultados no publicados: fuera de buscadores. Quitar al publicar. -->
<meta name="robots" content="noindex, nofollow">
<style>
:root{{
  --surface:#fcfcfb; --panel:#ffffff; --line:#e5e3dd; --line-soft:#efedE8;
  --ink:#0b0b0b; --ink-2:#52514e; --ink-3:#84827c;
  --favor:{C_FAVOR}; --cond:{C_COND}; --contra:{C_CONTRA};
  --accent:#1c5cab;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}}
*{{box-sizing:border-box}}
html{{-webkit-text-size-adjust:100%}}
body{{margin:0;background:var(--surface);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:60rem;margin:0 auto;padding:0 1.5rem}}

header.top{{border-bottom:1px solid var(--line);background:var(--panel);padding:3.5rem 0 2.5rem}}
.kicker{{font-size:.75rem;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-3);margin:0 0 .9rem}}
h1{{font-family:var(--serif);font-size:2.6rem;line-height:1.15;margin:0 0 .8rem;font-weight:600;letter-spacing:-.01em}}
.sub{{font-size:1.12rem;color:var(--ink-2);max-width:46rem;margin:0 0 1.6rem}}
.meta{{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;font-size:.86rem;color:var(--ink-3);
  border-top:1px solid var(--line-soft);padding-top:1.1rem}}
.meta b{{color:var(--ink-2);font-weight:600}}

nav.toc{{position:sticky;top:0;z-index:10;background:var(--bg);
  backdrop-filter:saturate(180%) blur(8px);border-bottom:1px solid var(--line);
  font-size:.83rem;overflow-x:auto}}
nav.toc ul{{display:flex;gap:1.4rem;list-style:none;margin:0 auto;padding:.75rem 1.5rem;max-width:60rem;white-space:nowrap}}
nav.toc a{{color:var(--ink-2);text-decoration:none;padding-bottom:2px;border-bottom:2px solid transparent}}
nav.toc a:hover{{color:var(--accent);border-color:var(--accent)}}

section{{padding:3.2rem 0 .6rem;scroll-margin-top:3.4rem}}
section+section{{border-top:1px solid var(--line-soft)}}
h2{{font-family:var(--serif);font-size:1.75rem;margin:0 0 .4rem;font-weight:600;letter-spacing:-.005em}}
h2 .sec-n{{color:var(--ink-3);font-size:1rem;font-family:var(--sans);font-weight:500;margin-right:.6rem;
  letter-spacing:.04em}}
.lead{{font-size:1.04rem;color:var(--ink-2);max-width:46rem;margin:.2rem 0 1.8rem}}
h3{{font-size:1.02rem;margin:2.2rem 0 .5rem;font-weight:650}}
p{{margin:0 0 1rem;max-width:46rem}}
.audience{{display:inline-block;font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;
  color:var(--accent);border:1px solid #cfe0f5;background:#f2f7fd;border-radius:99px;
  padding:.16rem .6rem;margin-bottom:.9rem;font-weight:600}}

.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:6px;overflow:hidden;margin:2rem 0}}
.tile{{background:var(--panel);padding:1.25rem 1.3rem}}
.tile .v{{font-family:var(--serif);font-size:2.1rem;line-height:1;font-weight:600;letter-spacing:-.02em}}
.tile .k{{font-size:.83rem;color:var(--ink-2);margin-top:.5rem;line-height:1.45}}

table{{width:100%;border-collapse:collapse;font-size:.88rem;margin:.6rem 0 1.2rem}}
caption{{text-align:left;font-size:.83rem;color:var(--ink-3);padding-bottom:.7rem;line-height:1.5}}
th{{text-align:left;font-weight:600;font-size:.74rem;letter-spacing:.05em;text-transform:uppercase;
  color:var(--ink-3);border-bottom:1px solid var(--line);padding:.5rem .55rem}}
td{{padding:.5rem .55rem;border-bottom:1px solid var(--line-soft);vertical-align:middle}}
tbody tr:hover{{background:#faf9f6}}
.qid{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.78rem;color:var(--ink-3);white-space:nowrap}}
.qtxt{{color:var(--ink);min-width:15rem}}
.opt{{color:var(--ink-2)}}
.n{{text-align:right;color:var(--ink-3);font-variant-numeric:tabular-nums;white-space:nowrap;font-size:.82rem}}
.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
.num.sec{{color:var(--ink-3);font-size:.82rem}}
.antes{{color:var(--ink-3);text-decoration:line-through;text-decoration-color:#d9d7d1}}
.ahora{{font-weight:600}}

.cbar{{width:15rem;min-width:11rem}}
.bar{{position:relative;height:22px;border-radius:3px;background:#f1efea;overflow:hidden}}
.bar .seg{{position:absolute;top:0;bottom:0;display:flex;align-items:center;justify-content:center;
  box-shadow:0 0 0 1px var(--panel) inset}}
.bar .seg span{{font-size:.7rem;font-weight:700;color:#fff;font-variant-numeric:tabular-nums}}
.bar.empty{{display:flex;align-items:center;padding-left:.5rem;font-size:.74rem;color:var(--ink-3)}}
.bar .seg.gap{{background:repeating-linear-gradient(135deg,#e6e2da 0 4px,#f1efea 4px 8px)}}
.leyenda{{display:flex;flex-wrap:wrap;gap:1.1rem;font-size:.82rem;color:var(--ink-2);margin:.2rem 0 1.3rem}}


figure.fig{{margin:1.2rem 0 1.6rem;padding:.6rem .4rem;background:var(--panel);
  border:1px solid var(--line);border-radius:5px}}
figure.fig svg{{display:block;width:100%;height:auto}}
figure.fig figcaption{{font-size:.84rem;color:var(--ink-3);padding:.5rem .8rem 0;max-width:44rem}}
.netrow{{margin:1.5rem 0 .5rem;padding-bottom:1.2rem;border-bottom:1px solid var(--line-soft)}}
.netrow:last-of-type{{border-bottom:0}}
.nethead{{display:flex;flex-wrap:wrap;align-items:baseline;gap:.5rem 1rem;margin-bottom:.5rem}}
.nethead b{{font-size:1rem}}
.netn,.netser{{font-size:.82rem;color:var(--ink-3)}}
.netser{{font-variant-numeric:tabular-nums}}
.netrow svg{{display:block;width:100%;height:auto}}
.netlec{{font-size:.9rem;color:var(--ink-2);margin:.7rem 0 0;max-width:44rem}}
.leyenda i.edw,.leyenda i.eds{{width:22px;height:0;border-radius:0;vertical-align:3px;
  border-top:1px solid #2a78d6;opacity:.45}}
.leyenda i.eds{{border-top-width:2.4px;opacity:.9}}
.tcapas td.capa{{font-weight:600;color:var(--ink);width:15rem;min-width:12rem}}
.tcapas td.quien{{white-space:nowrap;font-size:.86rem;color:var(--ink-2)}}
.tcapas td.qtxt{{max-width:26rem}}
.est{{display:inline-block;white-space:nowrap;font-size:.78rem;font-weight:650;
  padding:.16rem .55rem;border-radius:3px;border:1px solid}}
.est.e-ok{{background:#eef6ee;border-color:#cbe3cb;color:#2c6b34}}
.est.e-wip{{background:#fbf4e6;border-color:#ecdcb8;color:#7d5a15}}
.est.e-block{{background:#fdecec;border-color:#f6cccc;color:#a32c2c}}
.est.e-todo{{background:#f2f1ee;border-color:#e0ded8;color:#5f5d58}}
.tile .de{{font-size:1.1rem;color:var(--ink-3);font-weight:500}}
.sub.tit{{font-size:.95rem;background:#f5f7fa;border:1px solid var(--line);border-radius:4px;
  padding:.8rem 1rem;margin-top:1rem;color:var(--ink-2)}}
.sub.tit i{{color:var(--ink)}}
.nota{{font-size:.9rem;color:var(--ink-2);border-left:2px solid var(--line);
  padding-left:.9rem;margin:.9rem 0 1rem}}
.num sup, td sup{{color:var(--accent);font-weight:700;cursor:help}}
.leyenda i{{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:.4rem;vertical-align:-1px}}
.leyenda i.gapkey{{background:repeating-linear-gradient(135deg,#e6e2da 0 3px,#f1efea 3px 6px);
  border:1px solid var(--line)}}

.tag{{display:inline-block;font-size:.73rem;font-weight:650;padding:.15rem .5rem;border-radius:3px;
  white-space:nowrap;border:1px solid}}
.e-fuerte{{background:#eaf3fc;border-color:#c2dbf6;color:#16508f}}
.e-clara{{background:#f2f7fd;border-color:#d8e7f8;color:#1c5cab}}
.e-dom{{background:#f6f5f2;border-color:#e2e0d9;color:#5a5852}}
.e-sin{{background:#fdeeee;border-color:#f7d4d3;color:#a8302f}}
.e-insuf{{background:#f6f5f2;border-color:#e2e0d9;color:#84827c;font-style:italic}}

.callout{{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);
  border-radius:0 5px 5px 0;padding:1.15rem 1.3rem;margin:1.6rem 0;max-width:46rem}}
.callout p:last-child{{margin-bottom:0}}
.callout .ct{{font-weight:650;margin-bottom:.35rem;display:block}}
.warn{{border-left-color:#c8a415}}

.dec{{background:var(--panel);border:1px solid var(--line);border-radius:6px;
  padding:1.3rem 1.4rem;margin:0 0 1rem}}
.dec h3{{margin:0 0 .7rem;font-size:1.05rem;display:flex;align-items:baseline;gap:.65rem}}
.numdec{{display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;
  width:1.55rem;height:1.55rem;border-radius:50%;background:#f2f7fd;color:var(--accent);
  border:1px solid #cfe0f5;font-size:.8rem;font-weight:700}}
.dec p{{margin:0 0 .6rem;font-size:.92rem;max-width:none}}
.dec p:last-child{{margin-bottom:0}}
.dec .lab{{display:block;font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;
  color:var(--ink-3);font-weight:650;margin-bottom:.15rem}}
.dec-ev{{color:var(--ink-2)}}
.dec-ask{{background:#faf9f6;border-radius:4px;padding:.7rem .85rem;margin-top:.85rem!important}}

ol.fases{{list-style:none;counter-reset:f;padding:0;margin:1.4rem 0}}
ol.fases li{{counter-increment:f;position:relative;padding:0 0 1.15rem 2.6rem;
  border-left:2px solid var(--line);margin-left:.7rem}}
ol.fases li:last-child{{border-left-color:transparent;padding-bottom:0}}
ol.fases li::before{{content:counter(f);position:absolute;left:-.78rem;top:0;width:1.5rem;height:1.5rem;
  border-radius:50%;background:var(--panel);border:1px solid var(--line);color:var(--ink-3);
  font-size:.76rem;font-weight:700;display:flex;align-items:center;justify-content:center}}
ol.fases li.done::before{{content:"✓";background:#eaf3fc;border-color:#c2dbf6;color:#16508f}}
ol.fases > li > b{{display:block;font-size:.97rem;margin-bottom:.15rem}}
ol.fases span{{font-size:.9rem;color:var(--ink-2)}}
ol.fases .estado{{font-size:.72rem;letter-spacing:.05em;text-transform:uppercase;font-weight:650;
  color:var(--ink-3);margin-left:.5rem}}
ol.fases li.done .estado{{color:#16508f}}

footer{{border-top:1px solid var(--line);margin-top:3.5rem;padding:2rem 0 3rem;
  font-size:.83rem;color:var(--ink-3)}}
footer p{{max-width:46rem}}

@media (max-width:640px){{
  h1{{font-size:1.95rem}} h2{{font-size:1.42rem}}
  .cbar{{width:8rem;min-width:7rem}}
  .qtxt{{min-width:9rem;font-size:.85rem}}
  table{{font-size:.82rem}}
  .scroll{{overflow-x:auto}}
}}
@media print{{
  nav.toc{{display:none}} body{{font-size:11pt}} section{{page-break-inside:avoid}}
  .dec,.tiles{{page-break-inside:avoid}}
}}
</style>
</head>
<body>

<header class="top">
  <div class="wrap">
    <p class="kicker">Universidad San Francisco de Quito · Estudio Delphi de currículo médico</p>
    <h1>Qué decidió el panel, y cómo llegó ahí</h1>
    <p class="sub">Resultados del análisis computacional del estudio Delphi, la evolución del
    consenso ronda por ronda, y las decisiones que hacen falta para cerrar el artículo.</p>
    <p class="sub tit"><b>Sobre el título de trabajo</b> —<i>Mapping the Evolution of Citizen
    Consensus: A Visual and Network Analysis of Delphi Rounds</i>—: las secciones 3 y 4 son la
    respuesta. Tres de sus seis piezas ya están (rondas, consenso, evolución); la red y el
    análisis visual se pueden construir sobre estos mismos datos y hay una primera versión en la
    sección 3; «citizen» es la que pide el estudio de eutanasia, no el de currículo.</p>
    <div class="meta">
      <span><b>Datos</b> {CTX['n_respuestas']} respuestas · {CTX['n_preguntas']} preguntas · {CTX['n_paneles']} paneles · {CTX['n_rondas']} rondas</span>
      <span><b>Equipo</b> Pancho (implementación) · Emily (marco clínico) · Jonathan Guillemot (supervisión)</span>
      <span><b>Actualizado</b> {FECHA}</span>
    </div>
  </div>
</header>

<nav class="toc"><ul>
  <li><a href="#resumen">Resumen</a></li>
  <li><a href="#resultados">Lo que decidió el panel</a></li>
  <li><a href="#evolucion">Evolución entre rondas</a></li>
  <li><a href="#ideas">Qué más se puede hacer</a></li>
  <li><a href="#estado">Estado por capa</a></li>
  <li><a href="#decisiones">Lo que hace falta decidir</a></li>
  <li><a href="#plan">Plan y riesgos</a></li>
  <li><a href="#confianza">Confiabilidad</a></li>
</ul></nav>

<main class="wrap">

<section id="resumen">
  <h2><span class="sec-n">01</span>En treinta segundos</h2>
  <p class="lead">Los resultados del panel ya están completos y son confiables. Lo que falta para
  cerrar el estudio no es trabajo de programación: son ocho decisiones sobre cómo están definidas
  las opciones de cada pregunta, y sólo las puede tomar el equipo clínico.</p>

  <div class="tiles">
    <div class="tile"><div class="v">{T_POS}</div>
      <div class="k">preguntas de sí/no/depende <b>resueltas</b>: consenso fuerte o mayoría clara</div></div>
    <div class="tile"><div class="v">{T_CAT}</div>
      <div class="k">preguntas de opción con una posición mayoritaria identificada</div></div>
    <div class="tile"><div class="v">{T_CUANT}</div>
      <div class="k">preguntas numéricas con consenso; el resto sigue disperso o depende de las
      unidades</div></div>
    <div class="tile"><div class="v">{N_DEC}</div>
      <div class="k">decisiones pendientes, todas de <b>Emily</b> — sección 6</div></div>
  </div>

  <div class="callout">
    <span class="ct">Si sólo se va a leer una cosa</span>
    <p><b>Secciones 2 y 3:</b> lo que decidió el panel y cómo se llegó ahí ronda por ronda. <b>Sección 4:</b> siete análisis posibles sobre estos datos, para elegir cuáles entran en el artículo. <b>Secciones 5 y 6:</b> en qué estado está cada parte y las ocho decisiones que hacen falta para seguir. La 7 es el plan y la 8, lo técnico — no hace falta leerla.</p>
  </div>
</section>

<section id="resultados">
  <h2><span class="sec-n">02</span>Lo que decidió el panel</h2>
  <p class="lead">Resultados de la ronda final. La vista principal es por <b>postura</b> —a favor,
  condicional, en contra— que es el nivel en el que la estructura de la taxonomía de Emily
  distingue de verdad, y el que proponemos usar para medir consenso en el paper.</p>

  <h3>Consenso por postura</h3>
  <div class="leyenda">
    <span><i style="background:{C_FAVOR}"></i>A favor</span>
    <span><i style="background:{C_COND}"></i>Condicional</span>
    <span><i style="background:{C_CONTRA}"></i>En contra</span>
    <span><i class="gapkey"></i>Sin postura asignable</span>
    <span style="color:var(--ink-3)">Los números dentro de las barras son panelistas, no porcentajes.</span>
  </div>
  <div class="scroll">
  <table>
    <caption>13 preguntas de sí / no / depende, ronda final. «n» es cuántas respuestas se pudieron
    clasificar sobre el total del panel.</caption>
    <thead><tr><th>Id</th><th>Pregunta</th><th>Distribución</th><th>n</th><th>Resultado</th></tr></thead>
    <tbody>
{filas_postura}
    </tbody>
  </table>
  </div>

  <div class="callout">
    <span class="ct">Un resultado que sólo se ve a nivel de postura</span>
    <p>P2_Q7 («¿son necesarios los exámenes escritos en ABP?») aparece como «sin consenso» si se
    miran las opciones una por una, porque los panelistas se reparten entre varias. Pero los 6
    están <b>a favor</b>: discrepan en el cómo, no en el qué. Ese matiz se pierde con la lista
    plana de opciones y aparece con la estructura anidada del documento de posturas.</p>
  </div>

  <h3>Detalle por opción</h3>
  <div class="scroll">
  <table>
    <caption>Las 20 preguntas categóricas en la ronda final, con la opción más votada.</caption>
    <thead><tr><th>Id</th><th>Pregunta</th><th>Opción mayoritaria</th><th>n</th><th>Resultado</th></tr></thead>
    <tbody>
{filas_categ}
    </tbody>
  </table>
  </div>

  <h3>Preguntas numéricas</h3>
  <p>Estos resultados son <b>preliminares</b>: dependen de decisiones sobre unidades y bandas que
  están en la sección 6. Se incluyen para mostrar dónde están los problemas, no como resultado
  definitivo.</p>
  <div class="scroll">
  <table>
    <caption>Ronda final. La mediana y el rango intercuartílico son más robustos que el promedio
    con paneles de 7 a 10 personas.</caption>
    <thead><tr><th>Id</th><th>Pregunta</th><th>Mediana</th><th>RIC</th><th>Unidad</th><th>n</th><th>Resultado</th></tr></thead>
    <tbody>
{filas_cuant}
    </tbody>
  </table>
  </div>
  <p>Dos cosas que conviene mirar aquí. La primera: <b>el Panel 1 responde estas preguntas de
  forma narrativa</b>. De 7 panelistas sólo 4 o 5 dan una cifra; el resto contesta con un criterio
  («las horas necesarias para cubrir el programa»). Por eso P1_Q1 no alcanza el mínimo y las otras
  dos quedan justo en el límite. Es un problema de la pregunta, no del análisis, y es el punto 7
  de la sección 6.</p>
  <p>La segunda: en P3_Q1 y P3_Q6 (marcadas con <b>*</b>) la unidad la asumimos nosotros porque no
  está declarada. <b>«Convergencia moderada» en P3_Q6 se apoya en ese supuesto</b>: si la unidad
  fuera otra, el resultado cambia. Es el punto 5 de la sección 6 y es la razón por la que toda
  esta tabla es preliminar.</p>
</section>

<section id="evolucion">
  <h2><span class="sec-n">03</span>La evolución entre rondas</h2>
  <p class="lead">Los resultados de arriba son la foto final. Esta sección es la película: cómo
  se llegó a ellos. Es la parte que el análisis tenía calculada pero no estaba mirando, y es
  donde está el material para «mapear la evolución del consenso».</p>

  <h3>Quién coincide con quién, ronda por ronda</h3>
  <p>Cada círculo es un panelista y cada línea, cuánto coinciden sus respuestas en esa ronda:
  tenue si coinciden en más de la mitad de las preguntas, marcada si en tres cuartos o más. El
  tamaño del círculo son sus vínculos fuertes. <b>La posición de cada panelista se calcula una
  sola vez sobre las tres rondas juntas</b>: si se recalculara por ronda, el lector vería
  moverse los nodos y lo atribuiría al panel cuando en realidad sería el algoritmo de dibujo.</p>
{bloques_red}

  <h3>Quién cambió de opinión, y hacia dónde</h3>
  <p>El detalle que ninguna tabla de resultados puede dar: no sólo cuántos acabaron en cada
  opción, sino de dónde venía cada uno. El color de cada cinta es la opción <b>de origen</b>,
  así que se puede seguir a dónde fue a parar cada bloque inicial; las cintas tenues son quienes
  no se movieron. Estas tres son las preguntas con más movimiento ({QS_FLUJO}); se puede generar
  la figura para cualquiera de las 32.</p>
{bloques_flujo}

  <div class="callout">
    <span class="ct">Moverse no es lo mismo que converger</span>
    <p>El {MOV_TOT['pct']} % de las respuestas individuales cambia de opción entre la primera ronda
    y la última: hay deliberación real, la gente sí se mueve. Pero el panel que <b>más</b> se
    mueve (Panel 1, 53 %) es el que <b>no</b> converge, y el que <b>menos</b> se mueve (Panel 4,
    19 %) es el que converge del todo. Movimiento sin convergencia es rotación, no acuerdo — y
    distinguir las dos cosas es justamente lo que una tabla de resultados finales no puede hacer.</p>
  </div>

  <h3>Y a nivel de pregunta</h3>
  <p>Cada línea es una pregunta y su altura, cuánta gente está en la opción mayoritaria. Las
  cuatro facetas separan lo que le pasó a cada una; en gris, todas las demás como referencia.
  Las dos líneas horizontales son los umbrales de mayoría clara (60 %) y consenso fuerte (75 %).</p>
  <figure class="fig">{fig_trayectoria}
    <figcaption>De las {CTX['cat_total']} preguntas de opción: {CONV_SI} convergieron,
    {CONV_NO} se dispersaron, {CONV_EST_OK} ya estaban resueltas desde la primera ronda y
    {CONV_EST_NO} se quedaron estables sin acuerdo.</figcaption>
  </figure>

  <h3>Moverse no es converger</h3>
  <p>Un punto por panel. En el eje horizontal, cuánta gente cambia de opción; en el vertical,
  cuánto se acerca el panel entre sí. Si discutir llevara a acordar, los puntos subirían hacia
  la derecha.</p>
  <figure class="fig">{fig_movimiento}</figure>
</section>

<section id="ideas">
  <h2><span class="sec-n">04</span>Qué más se puede hacer con esto</h2>
  <span class="audience">Para Emily y Jonathan</span>
  <p class="lead">Siete análisis posibles sobre estos mismos datos. Los cuatro primeros se pueden
  hacer ya; los tres últimos dependen de decisiones de taxonomía. La idea es que elijan cuáles
  entran en el artículo, no que entren todos.</p>
  <div class="scroll">
  <table class="tcapas">
    <thead><tr><th>Análisis</th><th>Estado</th><th>Qué pregunta responde</th><th>Qué hace falta</th></tr></thead>
    <tbody>
{filas_ideas}
    </tbody>
  </table>
  </div>
  <div class="callout warn">
    <span class="ct">La limitación honesta, y qué hacer con ella</span>
    <p>Los paneles son de 7 a 10 personas. Eso alcanza para <b>mostrar</b> el método y para leer
    las figuras a ojo, pero no para estadística de redes: con 7 nodos, medidas como centralidad o
    modularidad son inestables y no se deberían reportar como resultado. La red con tamaño
    suficiente es la del estudio de eutanasia. La estructura natural del artículo es entonces:
    <b>currículo médico como banco de pruebas del método, eutanasia como la aplicación
    ciudadana</b> — que es además lo que el proyecto ya es.</p>
  </div>
</section>

<section id="estado">
  <h2><span class="sec-n">05</span>Estado por capa</h2>
  <p class="lead">En qué punto está cada parte del proyecto, qué falta y de quién depende. Las
  dos primeras filas son las que producen los resultados de la sección anterior; están cerradas.
  Lo que queda abierto está abajo.</p>
  <div class="scroll">
  <table class="tcapas">
    <thead><tr><th>Parte del proyecto</th><th>Estado</th><th>Qué falta</th><th>Depende de</th></tr></thead>
    <tbody>
{filas_capas}
    </tbody>
  </table>
  </div>
  <div class="callout">
    <span class="ct">Qué hay que hacer ahora, en orden</span>
    <p><b>1. Una sesión con Emily</b> para cerrar las ocho decisiones de la sección 6. Es lo único
    que bloquea todo lo demás; hora y media debería alcanzar.
    <br><b>2. Conseguir un segundo codificador</b> — cualquier persona del área que pueda
    etiquetar respuestas. No hace falta que sepa nada del sistema, y no depende de la decisión
    anterior, así que puede ir en paralelo.
    <br><b>3. Confirmar con Jonathan</b> el manejo de datos del estudio de eutanasia, antes de
    empezarlo y no después.</p>
  </div>
</section>


<section id="decisiones">
  <h2><span class="sec-n">06</span>Lo que hace falta decidir</h2>
  <span class="audience">Para Emily</span>
  <p class="lead">Ocho decisiones. Cada una viene con lo que pasa hoy, la evidencia en los datos y
  la pregunta concreta. Ninguna requiere saber nada de programación: son decisiones sobre cómo
  debe estar definida la taxonomía. Una sesión de una hora y media debería alcanzar para la
  mayoría.</p>
{filas_dec}
  <div class="callout">
    <span class="ct">Lo único que falta además de las decisiones</span>
    <p>La versión más reciente del documento de posturas. La hoja de validación muestra que para
    P1_Q3 ya se está usando una lista que no está en la versión 2.0 que tenemos, y hay una
    mención a una mejor clasificación para P3_Q3.</p>
  </div>
</section>

<section id="plan">
  <h2><span class="sec-n">07</span>Plan y riesgos</h2>
  <span class="audience">Para Jonathan</span>
  <p class="lead">El objetivo es un artículo de métodos: un marco computacional para analizar
  estudios Delphi a gran escala, validado contra codificación humana, sobre infraestructura
  propia. El conjunto de prueba (currículo médico) es el banco de pruebas; el conjunto real
  (eutanasia, ~22 000 respuestas) es la aplicación.</p>
  <ol class="fases">
    <li class="done"><b>Fase 0 — Integridad del análisis<span class="estado">Cerrada</span></b>
      <span>Corregir la extracción, las métricas de consenso y la reproducibilidad. Resultados
      coherentes con las respuestas en las 20 preguntas, κ 0,72, consistencia 100 %.</span></li>
    <li><b>Fase 1 — Taxonomía v2<span class="estado">Bloqueada por las decisiones de la sección 6</span></b>
      <span>Postura y calificadores por separado, umbrales numéricos, unidades, y la taxonomía de
      argumentos. Es el cuello de botella real del proyecto.</span></li>
    <li><b>Fase 2 — Criterios de consenso y figuras<span class="estado">1 semana</span></b>
      <span>Fijar los criterios con la literatura Delphi (acuerdo y estabilidad entre rondas) antes
      de mirar los resultados, no después.</span></li>
    <li><b>Fase 3 — Validación formal<span class="estado">2–3 semanas</span></b>
      <span>200–300 respuestas, <b>dos</b> codificadores humanos independientes. El acuerdo entre
      ellos es el techo contra el que se juzga al sistema.</span></li>
    <li><b>Fase 4 — Conjunto real (eutanasia)<span class="estado">Pendiente</span></b>
      <span>Requiere confirmar el manejo de datos sensibles y la taxonomía del nuevo dominio.</span></li>
  </ol>

  <h3>Riesgos</h3>
  <p><b>El segundo codificador.</b> Sin acuerdo entre dos personas no hay techo contra el cual
  juzgar al sistema, y un revisor lo va a pedir. Es la dependencia que conviene resolver antes.</p>
  <p><b>Datos sensibles.</b> El conjunto de eutanasia probablemente exige que todo se quede en
  infraestructura institucional. Ya se trabaja así, pero conviene confirmarlo formalmente antes
  de empezar, no después.</p>
  <p><b>Lo técnico</b> —la reproducibilidad exacta entre corridas y el tamaño de los
  paneles— está en la sección 8.</p>
</section>

<section id="confianza">
  <h2><span class="sec-n">08</span>Confiabilidad y notas técnicas</h2>
  <p class="lead">Esta sección es la respuesta a «¿por qué creerle a estos números?». No hace
  falta leerla para usar los resultados.</p>

  <h3>Cómo se obtienen los números</h3>
  <p>Los panelistas responden con texto libre. Emily define, para cada pregunta, el conjunto
  cerrado de respuestas posibles; un modelo de lenguaje alojado <b>en el servidor de la
  universidad</b> —los datos nunca salen de la infraestructura institucional— asigna cada
  respuesta a una de esas opciones; y se mide, ronda por ronda, cuánto se concentra el panel.
  El sistema no inventa categorías: si una respuesta no encaja en ninguna opción, queda marcada
  como tal en vez de forzarse.</p>

  <h3>Qué tan bien coincide con una persona</h3>
  <p>Emily etiquetó a ciegas 44 respuestas, sin ver la salida del sistema. Coinciden en el 75 %
  (κ = 0,72; el estándar habitual entre dos codificadores humanos en investigación cualitativa).
  Leídas a nivel de postura —a favor / en contra / depende, sin el matiz— coinciden en 21 de 24.
  Con 44 respuestas el margen de error es amplio: por eso la validación formal usará entre 200 y
  300 y un segundo codificador.</p>
  <p>Otras tres comprobaciones. <b>Consistencia:</b> treinta panelistas repitieron su respuesta
  palabra por palabra entre rondas y el sistema les dio la misma etiqueta en los treinta casos.
  <b>Contraste con los facilitadores:</b> las conclusiones coinciden con las síntesis escritas a
  mano en las 20 preguntas — y en dos casos la síntesis humana es la que se equivoca, lo que es
  en sí un argumento a favor de tener registro de cada respuesta.
  <b>Dos modelos distintos:</b> se probaron dos sistemas de familias diferentes sobre las mismas
  44 respuestas, con resultados equivalentes. De los ocho errores que le quedan al elegido,
  <b>siete son exactamente las mismas respuestas que falla el otro</b> — señal de que el límite
  ya no está en el software sino en la taxonomía, y los siete están en la sección 6.</p>

  <h3>Dos advertencias para el paper</h3>
  <p><b>El servidor no da resultados idénticos entre corridas</b>, aun fijando todos los
  parámetros: entre dos ejecuciones cambiaron 3 etiquetas de 44 (el acuerdo pasó de 0,72 a 0,79).
  Lo que hace reproducible un resultado es archivar el registro de la corrida, que el sistema ya
  genera. Hay que decirlo así en métodos en vez de afirmar determinismo.</p>
  <p><b>Los paneles son pequeños</b>, de 7 a 10 personas: cada panelista mueve entre 10 y 14
  puntos porcentuales. Por eso todos los resultados llevan el n al lado y no se etiqueta consenso
  por debajo de un mínimo de respuestas.</p>

  <h3>Sobre los números anteriores</h3>
  <p>Si alguien recuerda conclusiones distintas de una versión previa: el análisis anterior tenía
  un error de programación que corría un lugar las opciones e invertía cinco conclusiones. Está
  corregido y comprobado. Las cinco que cambiaron:</p>
  <div class="scroll">
  <table>
    <thead><tr><th>Id</th><th>Pregunta</th><th>Decía antes</th><th>Dice ahora</th></tr></thead>
    <tbody>
{filas_inv}
    </tbody>
  </table>
  </div>
  <p>La columna de la derecha es la que coincide con las respuestas de los panelistas y con las
  síntesis de los facilitadores. El error se detectó justamente comparando contra esas síntesis,
  y esa comparación es ahora un paso fijo del procedimiento.</p>
</section>
</main>



<footer>
  <div class="wrap">
    <p>Documento de trabajo interno · Estudio Delphi de currículo médico, USFQ · {FECHA}.
    Los resultados de las preguntas numéricas son preliminares y dependen de las decisiones de
    la sección 6. El diagnóstico técnico completo, con el detalle de las comprobaciones, está en
    el repositorio del proyecto.</p>
  </div>
</footer>

</body>
</html>
"""
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"), "w", encoding="utf-8").write(HTML)
print(f"index.html — {len(HTML):,} bytes")
