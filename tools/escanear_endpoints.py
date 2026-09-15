#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pregunta al servidor qué modelos sirve. La documentación sobra.

    python3 tools/escanear_endpoints.py              # barre el rango habitual
    python3 tools/escanear_endpoints.py --probar     # además comprueba que genera, y mide latencia
    python3 tools/escanear_endpoints.py --puertos 12500-12600
    DELPHI_HOST=otra.ip python3 tools/escanear_endpoints.py

Por qué existe
-------------
La lista de endpoints se ha escrito a mano en tres sitios —config.py, compare_models.py y una
página de Notion— y los tres se desactualizaron. Cada vez costó una corrida: la del 14-09-2026
fueron 706 extracciones fallidas contra un modelo que el servidor ya no tenía.

Un escaneo tarda segundos y no puede quedar desactualizado, porque se hace en el momento.
Lo que imprime al final se pega tal cual en config.py.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HOST = os.environ.get("DELPHI_HOST", "172.28.230.10")
PUERTOS_HABITUALES = "12550-12570"
TIMEOUT = 3.0


def rango(txt):
    """'12555,12559' o '12550-12570' o una mezcla -> lista de enteros."""
    puertos = []
    for trozo in txt.split(","):
        trozo = trozo.strip()
        if "-" in trozo:
            a, b = trozo.split("-", 1)
            puertos.extend(range(int(a), int(b) + 1))
        elif trozo:
            puertos.append(int(trozo))
    return sorted(set(puertos))


def sondear(puerto):
    """(puerto, [modelos], error). No lanza: un puerto cerrado es un resultado, no un fallo."""
    url = f"http://{HOST}:{puerto}/v1/models"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            datos = json.load(r)
        return puerto, [m["id"] for m in datos.get("data", [])], None
    except Exception as e:
        return puerto, [], type(e).__name__


def generar(puerto, modelo):
    """Comprueba que además de listarse, genera. Devuelve (ok, segundos, detalle)."""
    # 64 y no 5: un modelo de razonamiento gasta el presupuesto pensando antes de escribir
    # nada, y con 5 devuelve content=None. Eso no es "no genera", es "no le alcanzó".
    cuerpo = json.dumps({
        "model": modelo,
        "messages": [{"role": "user", "content": "Responde exactamente: OK"}],
        "max_tokens": 64, "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        f"http://{HOST}:{puerto}/v1/chat/completions", data=cuerpo,
        headers={"Content-Type": "application/json", "Authorization": "Bearer local"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)
        eleccion = d["choices"][0]
        msg = eleccion.get("message", {})
        txt = msg.get("content")
        fuente = ""
        if not (txt or "").strip():
            # Canal de razonamiento: los modelos que "piensan" dejan aquí lo escrito cuando
            # se les acaba el presupuesto antes de redactar la respuesta.
            txt = msg.get("reasoning_content")
            fuente = " [razonamiento]"
        if not (txt or "").strip():
            motivo = eleccion.get("finish_reason")
            return False, time.time() - t0, (
                "agotó max_tokens razonando" if motivo == "length"
                else f"respuesta vacía (finish_reason={motivo})")
        return True, time.time() - t0, repr(txt.strip()[:30]) + fuente
    except Exception as e:
        return False, time.time() - t0, f"{type(e).__name__}: {str(e)[:60]}"


def _una_llamada(puerto, cuerpo):
    req = urllib.request.Request(
        f"http://{HOST}:{puerto}/v1/chat/completions", data=json.dumps(cuerpo).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer local"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    eleccion = d["choices"][0]
    msg = eleccion.get("message", {})
    contenido = (msg.get("content") or "").strip()
    razonado = (msg.get("reasoning_content") or "").strip()
    txt = contenido or razonado
    obj = None
    try:
        i, j = txt.find("{"), txt.rfind("}")
        if i != -1 and j > i:
            obj = json.loads(txt[i:j + 1])
    except Exception:
        pass
    return {"seg": time.time() - t0, "motivo": eleccion.get("finish_reason"),
            "chars": len(txt), "razono": bool(razonado), "json": obj, "txt": txt}


def capacidades(puerto, modelo, presupuestos=(512, 2500, 6000)):
    """¿Qué extras acepta el servidor Y sirven, dándoles presupuesto suficiente?

    Dos versiones anteriores de esta función se equivocaron por lo mismo: medir con muy pocos
    tokens. La primera pidió 5 y leyó `content=None` como "no genera". La segunda pidió 512,
    mostró 40 caracteres de la salida y NO mostró `finish_reason`, así que un "no es JSON
    usable" podía ser en realidad "se quedó sin tokens explicando". Con un modelo de
    razonamiento, un presupuesto corto no distingue "no sabe" de "no le alcanzó".

    Ahora cada variante escala el presupuesto mientras el servidor diga `finish_reason=length`,
    y se informa SIEMPRE el motivo y el tamaño de la salida. Así se puede responder la pregunta
    correcta: ¿esto falla, o sólo necesita más sitio?
    """
    ESQUEMA = {"type": "object",
               "properties": {"option_letter": {"type": "string", "enum": ["A", "B", "NONE"]},
                              "option_text": {"type": "string"}},
               "required": ["option_letter", "option_text"]}
    PETICION = ('Classify this response into ONE option.\n\nResponse: """I agree completely, '
                'the program should keep it as it is."""\n\nOptions:\n  A. Yes\n  B. No\n\n'
                'Respond ONLY with valid JSON:\n'
                '{"option_letter": "<A, B or NONE>", "option_text": "<text of the option>"}')
    variantes = {
        "sin extras (control)": {},
        "guided_json": {"guided_json": ESQUEMA},
        "enable_thinking=false": {"chat_template_kwargs": {"enable_thinking": False}},
        "las dos juntas": {"guided_json": ESQUEMA,
                           "chat_template_kwargs": {"enable_thinking": False}},
    }
    salida = {}
    for nombre, extra in variantes.items():
        intentos = []
        for presupuesto in presupuestos:
            cuerpo = {"model": modelo, "max_tokens": presupuesto, "temperature": 0,
                      "messages": [{"role": "user", "content": PETICION}], **extra}
            try:
                r = _una_llamada(puerto, cuerpo)
            except urllib.error.HTTPError as ex:
                salida[nombre] = ("ERROR", f"HTTP {ex.code} — el servidor lo rechaza")
                intentos = None
                break
            except Exception as ex:
                salida[nombre] = ("ERROR", type(ex).__name__)
                intentos = None
                break
            intentos.append((presupuesto, r))
            if r["json"] is not None and "option_letter" in r["json"]:
                break                      # ya salió: no hace falta más presupuesto
            if r["motivo"] != "length":
                break                      # terminó solo y aun así no hay JSON: no es presupuesto
        if intentos is None:
            continue
        presupuesto, r = intentos[-1]
        marca = (f"{presupuesto} tok, {r['seg']:.1f}s, {r['chars']} chars, "
                 f"finish={r['motivo']}" + (", razonó" if r["razono"] else ""))
        if r["json"] is not None and "option_letter" in r["json"]:
            veredicto = "sí" if presupuesto == presupuestos[0] else f"sí con {presupuesto}"
            salida[nombre] = (veredicto, f"option_letter={r['json']['option_letter']!r} ({marca})")
        elif r["motivo"] == "length":
            salida[nombre] = ("NO", f"sigue truncando al máximo probado ({marca})")
        else:
            salida[nombre] = ("NO", f"termina sin JSON: {r['txt'][:70]!r} ({marca})")
    return salida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--puertos", default=PUERTOS_HABITUALES)
    ap.add_argument("--probar", action="store_true",
                    help="además de listar, comprobar que genera y medir latencia")
    ap.add_argument("--capacidades", action="store_true",
                    help="probar guided_json y apagar el pensamiento, escalando el presupuesto")
    args = ap.parse_args()

    puertos = rango(args.puertos)
    print(f"Host {HOST} · {len(puertos)} puertos ({puertos[0]}–{puertos[-1]})\n")

    with ThreadPoolExecutor(max_workers=32) as pool:
        resultados = list(pool.map(sondear, puertos))

    vivos = [(p, ms) for p, ms, _ in resultados if ms]
    mudos = [(p, err) for p, ms, err in resultados if not ms and err not in
             ("URLError", "timeout", "TimeoutError", "ConnectionRefusedError")]

    if not vivos:
        print("Ningún puerto sirve modelos.")
        print("  ¿VPN activa? ¿El rango es el correcto? Probar --puertos 12000-13000")
        if mudos:
            print("\n  Puertos que respondieron algo raro:")
            for p, err in mudos:
                print(f"    {p}: {err}")
        return 1

    print("── Modelos servidos ──")
    unicos = {}
    for puerto, modelos in vivos:
        for m in modelos:
            unicos.setdefault(m, []).append(puerto)
            linea = f"  {puerto}  {m}"
            if args.probar:
                ok, seg, detalle = generar(puerto, m)
                linea += f"   {'genera' if ok else 'NO GENERA'} en {seg:.1f}s  {detalle}"
            print(linea)

    if args.capacidades:
        print("\n── Qué extras acepta el servidor ──")
        puerto, modelos = vivos[0]
        for nombre, (ok, detalle) in capacidades(puerto, modelos[0]).items():
            print(f"  {nombre:24} {ok:3}  {detalle}")
        print("\n  «sí» = JSON parseable con la clave pedida. «sí con N» = lo logra, pero")
        print("  necesita N tokens: no es que no sepa, es que primero explica. «NO» con")
        print("  finish=length significa que sigue truncando al máximo probado.")
        print("    enable_thinking=false ->  DELPHI_SIN_RAZONAMIENTO=1 ./run.sh")
        print("    guided_json           ->  USE_GUIDED_JSON = True en config.py")

    print(f"\n── Resumen: {len(unicos)} modelo(s) distinto(s) ──")
    for m, ps in unicos.items():
        rep = " (replicado)" if len(ps) > 1 else ""
        print(f"  {m}  en {', '.join(map(str, ps))}{rep}")

    if len(unicos) == 1:
        print("\n  Sólo hay un modelo: no se puede comparar nada, sólo puntuarlo.")

    principal = max(unicos.items(), key=lambda kv: len(kv[1]))
    print("\n── Para pipeline/config.py ──")
    print(f'  URL_LLM   = _os.environ.get("DELPHI_LLM_URL", "http://{HOST}:{principal[1][0]}/v1")')
    print(f'  MODEL_LLM = _os.environ.get("DELPHI_MODELO", "{principal[0]}")')
    print("\n  Cambiar el modelo invalida el caché y vuelve a extraer todo con uno solo;")
    print("  no mezcla corridas. Cuál se usó queda en Resultados/run_manifest.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
