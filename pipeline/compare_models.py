"""
Comparación Gemma vs DeepSeek (v2) sobre el MISMO esquema de extracción de extract_arguments.py.

En la v1 la comparación medía el bug de índices (Gemma base 0, DeepSeek base 1), no los
modelos. Ahora ambos reciben el prompt por letras y pasan por la misma validación.

Dos modos:

  python compare_models.py                                   # muestra nueva: 4 por pregunta = 128
  python compare_models.py Resultados/validation_emily_done.xlsx
        # SOBRE LOS MISMOS ÍTEMS QUE ETIQUETÓ EMILY -> es el único modo que decide el modelo,
        # porque después score_validation puntúa a los dos contra el mismo gold:
        #   python score_validation.py <hoja de Emily> Resultados/model_comparison.csv

El primer modo mide acuerdo entre modelos (sin gold): sirve para encontrar dónde divergen y
sembrar la muestra grande de la Fase 3. El segundo mide acierto contra la codificadora.
"""
import os
import sys
import time
import json
import pandas as pd
from openai import OpenAI
from config import *
from taxonomy import get_taxonomy
from extract_arguments import extract_single
from consensus_metrics import unit_from_raw, to_question_unit, derive_band

MODELS = {
    # max_tokens por modelo: DeepSeek es de razonamiento y con 512 se queda sin presupuesto
    # antes de emitir el JSON (la v1 ya usaba 2000 por esto mismo). Gemma responde directo.
    "gemma":    {"url": "http://172.28.230.10:12559/v1", "model": "google/gemma-4-12B-it",
                 "max_tokens": 512},
    # OJO: el id cambió el 30-08-2026 (era "DeepSeek-V4-Flash"). Es un snapshot distinto al que
    # se usó en la comparación v1, así que el kappa de DeepSeek v1 (0.79) NO es directamente
    # comparable con lo que salga ahora. El id queda registrado en model_comparison_raw.json.
    "deepseek": {"url": "http://172.28.230.10:12555/v1", "model": "deepseek-ai/DeepSeek-V4-Flash-0731",
                 "max_tokens": 2500},
}
N_PER_QUESTION = 4
MAX_FALLOS_SEGUIDOS = 3     # aborta en vez de moler 44 respuestas contra un endpoint caído
RANDOM_STATE = 42


def comparable_label(res, tax):
    """
    Etiqueta comparable con el gold humano: la OPCIÓN en categóricas y la BANDA en numéricas
    (derivada del valor ya llevado a la unidad de la pregunta, igual que consensus_metrics y
    score_validation). Emily etiqueta bandas, no valores: comparar "8 hours/day" contra
    "Moderate" daría un kappa de cero por comparar cosas distintas.
    """
    if res.get("extraction_status") != "ok":
        return None
    if res["question_type"] in ("nominal", "binary"):
        return res.get("selected_option")
    u, _src = unit_from_raw(res.get("value_raw"), res.get("value_unit"))
    v, _st = to_question_unit(res.get("numeric_value"), u, tax.get("unit"))
    b = derive_band(v, tax.get("bands", {}))
    return b if b is not None else res.get("band")


def raw_value(res):
    """El número tal como quedó extraído, para poder auditar el desacuerdo."""
    v, u = res.get("numeric_value"), res.get("value_unit")
    return f"{v:g} {u}" if v is not None else None


def build_sample(ind):
    valid = ind[ind["is_valid_response"]].copy()
    parts = []
    for (p, q), grp in valid.groupby([COL_PANEL, COL_QUESTION]):
        parts.append(grp.sample(min(N_PER_QUESTION, len(grp)), random_state=RANDOM_STATE))
    sample = pd.concat(parts).reset_index(drop=True)
    sample["qtype"] = [get_taxonomy(p, q)["type"] for p, q in zip(sample[COL_PANEL], sample[COL_QUESTION])]
    print(f"Muestra: {len(sample)} respuestas")
    print(sample["qtype"].value_counts().to_string())
    return sample


def preflight(name, cfg):
    """¿El endpoint responde y sirve el modelo configurado? (evita 44 fallos en silencio)"""
    import urllib.request
    url = cfg["url"].rstrip("/") + "/models"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            served = [m["id"] for m in json.load(r)["data"]]
    except Exception as e:
        return False, f"no responde — {type(e).__name__}: {str(e)[:70]}"
    if cfg["model"] not in served:
        return False, (f"responde pero NO sirve '{cfg['model']}'.\n"
                       f"      Sirve ahora: {', '.join(served) or '(nada)'}\n"
                       f"      -> actualiza MODELS['{name}']['model'] en compare_models.py")
    return True, f"ok — sirve {cfg['model']}"


def run_model(name, cfg, sample):
    client = OpenAI(base_url=cfg["url"], api_key=API_KEY)
    out, latencies, transporte, n_json_fail = {}, [], 0, 0
    print(f"\n── Running {name} ({cfg['model']}) ──")
    for i, (_, row) in enumerate(sample.iterrows()):
        tax = get_taxonomy(row[COL_PANEL], row[COL_QUESTION])
        t0 = time.time()
        res = extract_single(client, row["response_id"], row[COL_RESPONSE], row[COL_QUESTION_TEXT],
                             int(row[COL_ROUND]), tax, model=cfg["model"],
                             max_tokens=cfg.get("max_tokens"))
        dt = time.time() - t0
        latencies.append(dt)
        out[row["response_id"]] = res
        if res.get("extraction_status") == "ok":
            transporte = 0
            print(f"  [{i+1}/{len(sample)}] {row['response_id']} -> {comparable_label(res, tax)}  ({dt:.1f}s)")
        else:
            err = str(res.get("error") or "")
            es_json = err.startswith("json:")
            if es_json:
                # el modelo respondió pero no en JSON: es un RESULTADO de la comparación
                # (mide la fiabilidad de formato), no un fallo de infraestructura.
                n_json_fail += 1
                transporte = 0
            else:
                transporte += 1
            print(f"  [{i+1}/{len(sample)}] {row['response_id']} -> "
                  f"{'SIN JSON' if es_json else 'FALLO'}: {err}  ({dt:.1f}s)")
            if transporte >= MAX_FALLOS_SEGUIDOS:
                raise RuntimeError(
                    f"{name}: {transporte} fallos de conexión seguidos.\n"
                    f"  Último error: {err}\n"
                    f"  Comprueba {cfg['url']}/models (runbook §1).")
    if n_json_fail:
        print(f"  -> {name}: {n_json_fail}/{len(sample)} respuestas sin JSON válido")
    return out, (sum(latencies) / len(latencies) if latencies else 0)


def sample_from_labels(ind, path):
    """Muestra = exactamente los response_id que ya tienen etiqueta humana."""
    lab = pd.read_excel(path) if str(path).endswith("xlsx") else pd.read_csv(path)
    ids = set(lab["response_id"])
    sample = ind[ind["response_id"].isin(ids)].copy()
    faltan = ids - set(sample["response_id"])
    if faltan:
        print(f"⚠ {len(faltan)} response_id de la hoja no están en el dataset: {sorted(faltan)[:5]}")
    sample["qtype"] = [get_taxonomy(p, q)["type"] for p, q in zip(sample[COL_PANEL], sample[COL_QUESTION])]
    print(f"Muestra = ítems etiquetados por la codificadora: {len(sample)}")
    print(sample["qtype"].value_counts().to_string())
    return sample.reset_index(drop=True)


def main(labels_path=None):
    ind = pd.read_csv(os.path.join(OUTPUT_DIR, "01_individual_clean.csv"))
    sample = sample_from_labels(ind, labels_path) if labels_path else build_sample(ind)
    print("\n── Comprobando endpoints ──")
    vivos = {}
    for name, cfg in MODELS.items():
        ok, msg = preflight(name, cfg)
        print(f"  {name:9s} {cfg['url']}  {msg}")
        if ok:
            vivos[name] = cfg
    if not vivos:
        raise SystemExit("\nNingún endpoint disponible: no hay nada que comparar.")
    if len(vivos) < len(MODELS):
        faltan = [n for n in MODELS if n not in vivos]
        print(f"\n⚠ Sigo sólo con {list(vivos)}; sin {faltan} esto NO decide el modelo, "
              f"sólo puntúa a los que respondieron.")

    results, lats = {}, {}
    for name, cfg in vivos.items():
        try:
            results[name], lats[name] = run_model(name, cfg, sample)
        except RuntimeError as e:
            print(f"\n⚠ {e}\n  Sigo con los modelos que sí terminaron.")
    if not results:
        raise SystemExit("Ningún modelo completó la corrida.")

    rows = []
    names = list(results)
    for _, r in sample.iterrows():
        rid = r["response_id"]
        rec = {"response_id": rid, "qtype": r["qtype"], "response": r[COL_RESPONSE][:80]}
        tax = get_taxonomy(r[COL_PANEL], r[COL_QUESTION]) or {}
        for n in names:
            res = results[n].get(rid, {})
            rec[n] = comparable_label(res, tax)              # <- lo que puntúa score_validation
            rec[f"{n}_value"] = raw_value(res)
            rec[f"{n}_status"] = res.get("classification_status") or res.get("extraction_status")
            rec[f"{n}_mismatch"] = res.get("letter_text_mismatch")
        rec["agree"] = (rec[names[0]] == rec[names[1]]) if len(names) == 2 else None
        rows.append(rec)
    comp = pd.DataFrame(rows)
    out_path = os.path.join(OUTPUT_DIR, "model_comparison.csv")
    comp.to_csv(out_path, index=False)
    with open(os.path.join(OUTPUT_DIR, "model_comparison_raw.json"), "w") as f:
        json.dump(results, f, indent=1, ensure_ascii=False)

    print("\n═══ RESUMEN DE COMPARACIÓN ═══════════════════════════")
    for n in names:
        res = results[n]
        n_fail = sum(1 for v in res.values() if v.get("extraction_status") != "ok")
        n_json = sum(1 for v in res.values() if str(v.get("error") or "").startswith("json:"))
        n_unc = sum(1 for v in res.values() if v.get("selected_option") == "Unclassified")
        n_mis = sum(1 for v in res.values() if v.get("letter_text_mismatch"))
        print(f"\n  {n}:")
        print(f"    Sin salida válida           : {n_fail}/{len(sample)}  (de ellos, JSON inválido: {n_json})")
        print(f"    Unclassified                : {n_unc}/{len(sample)}")
        print(f"    Letra≠texto (inconsistencia): {n_mis}/{len(sample)}")
        print(f"    Latencia media              : {lats[n]:.1f}s por respuesta")
    if len(names) == 2:
        print(f"\n  Acuerdo entre modelos: {comp['agree'].mean()*100:.1f}%")
        print("  Desacuerdos por tipo:")
        print(comp[~comp["agree"]].groupby("qtype").size().to_string())
    else:
        print(f"\n  Un solo modelo disponible ({names[0]}): sin comparación entre modelos.")
    print(f"\n  Detalle: {out_path}")
    print("══════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
