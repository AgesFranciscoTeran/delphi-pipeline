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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--puertos", default=PUERTOS_HABITUALES)
    ap.add_argument("--probar", action="store_true",
                    help="además de listar, comprobar que genera y medir latencia")
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
