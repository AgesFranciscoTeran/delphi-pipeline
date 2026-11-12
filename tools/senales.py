"""Experimento de señales, etapa 1 (sin llamadas al GLM). Diseño: docs/experimento_senales.md.

Objetivo 1: predecir qué respuestas cambian de etiqueta (eje principal) entre las k corridas.
Señales de esta etapa:
  S0  longitud de la respuesta (línea base trivial; más corta = más sospechosa)
  S3p cita aproximada: qué tan literales son las key_phrases que ya devuelve la extracción
  S4  embeddings (bge-m3, Ollama): margen entre la opción más parecida y la etiqueta votada
  comb regresión logística con validación cruzada (5 pliegues) sobre S0, S3p y S4

Uso (contenedor de la H200):
  python3 tools/senales.py Resultados_v4f [--ollama http://172.28.230.10:11434]
Salida: <res>/senales/05_senales.csv, resumen.json, curva_esfuerzo.png, cache de embeddings.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
from taxonomy import get_taxonomy  # noqa: E402

MODELO_EMB = "bge-m3"
EMB_VARIANTE, EMB_FALLIDOS = [], []
CATEG = {"nominal", "ordinal", "binary", "categorical"}


# ---------------------------------------------------------------- objetivo 1
def etiqueta(row):
    if str(row.get("question_type")) == "quantitative":
        b = row.get("band")
        return "∅" if pd.isna(b) else str(b)
    s = row.get("selected_option")
    return "∅" if pd.isna(s) else str(s)


def con_banda_final(d):
    """Reemplaza `band` por la banda que usa el consenso (`band_final` de consensus_metrics):
    la del número convertido a la unidad de la pregunta; la del modelo sólo si no hay número.

    12-11-2026: hasta aquí el experimento usaba la banda que escribe el modelo, que a veces
    queda vacía aunque el número esté extraído ("4 hours" -> 4.0, banda nula). Eso inflaba la
    inestabilidad con casos que el consenso ya resolvía. La original queda en `band_llm`.
    """
    from consensus_metrics import derive_band, separar_medida, to_question_unit, unit_from_raw
    d = d.copy()
    d["band_llm"] = d["band"]
    for i, r in d.iterrows():
        if str(r.question_type) not in ("quantitative", "hybrid"):
            continue
        tax = get_taxonomy(int(r.Panel), int(r.Question)) or {}
        v, banda = r.numeric_value, r.band
        kw = tax.get("measure_keywords")
        if kw:
            v, _ = separar_medida(r.Response, r.numeric_value, r.get("value_secondary"), kw)
            if pd.isna(v) and not pd.isna(r.numeric_value):
                banda = None                       # la banda del modelo era la del total
        u, _ = unit_from_raw(r.get("value_raw"), r.get("value_unit"))
        vv, _ = to_question_unit(v, u, tax.get("unit"))
        b = derive_band(vv, tax.get("bands", {}))
        d.at[i, "band"] = b if b is not None else banda
    return d


def inestabilidad(res, k):
    """1 si la etiqueta del eje principal no es la misma en las k corridas."""
    etiq = []
    for i in range(1, k + 1):
        d = pd.read_csv(f"{res}_k{i}/02_extracted.csv")
        d = con_banda_final(d[d.is_valid_response.astype(bool)])
        etiq.append(d.set_index("response_id").apply(etiqueta, axis=1).rename(f"k{i}"))
    e = pd.concat(etiq, axis=1)
    return (e.nunique(axis=1, dropna=False) > 1).astype(int).rename("inestable"), e


# ---------------------------------------------------------------- S3p
def _norm(t):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s/]", " ", str(t).lower())).strip()


def parecido_frase(frase, texto):
    """1.0 si la frase está literal; si no, el mejor parecido con una ventana del mismo largo."""
    f, t = _norm(frase), _norm(texto)
    if not f:
        return np.nan
    if f in t:
        return 1.0
    fw, tw = f.split(), t.split()
    n = len(fw)
    if n == 0 or not tw:
        return 0.0
    mejor = 0.0
    for i in range(max(1, len(tw) - n + 1)):
        mejor = max(mejor, difflib.SequenceMatcher(None, f, " ".join(tw[i:i + n])).ratio())
    return mejor


def s3p(row):
    try:
        frases = json.loads(row["key_phrases"]) if isinstance(row["key_phrases"], str) else []
    except json.JSONDecodeError:
        frases = []
    vals = [parecido_frase(f, row["Response"]) for f in frases if isinstance(f, str)]
    vals = [v for v in vals if not np.isnan(v)]
    return min(vals) if vals else np.nan      # la peor frase manda


# ---------------------------------------------------------------- S4
def embed(textos, url, cache_path):
    cache = {}
    if os.path.exists(cache_path):
        z = np.load(cache_path, allow_pickle=True)
        cache = dict(zip(z["claves"], z["vecs"]))
    clave = lambda t: hashlib.sha1(t.encode("utf-8")).hexdigest()
    faltan = sorted({t for t in textos if clave(t) not in cache})
    def pedir(lote):
        req = urllib.request.Request(f"{url}/api/embed", method="POST",
                                     data=json.dumps({"model": MODELO_EMB, "input": lote,
                                                      "truncate": True}).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.load(r)["embeddings"]

    # bge-m3 en Ollama devuelve NaN para algunos textos (error 500). Regla fija: se prueban,
    # en este orden, variantes que no cambian el contenido; si todas fallan, el texto queda sin
    # vector (la señal S4 queda vacía para esa respuesta).
    variantes = lambda t: [t, t.rstrip(".!?;: "), t + " ", t + "\n", t.rstrip(".!?;: ") + " ."]
    for i in range(0, len(faltan), 8):
        lote = faltan[i:i + 8]
        try:
            vecs = pedir(lote)
        except urllib.error.HTTPError:
            vecs = []
            for t in lote:
                v = None
                for j, tv in enumerate(variantes(t)):
                    try:
                        v = pedir([tv])[0]
                        if j:
                            EMB_VARIANTE.append(t)
                        break
                    except urllib.error.HTTPError:
                        continue
                if v is None:
                    EMB_FALLIDOS.append(t)
                vecs.append(v)
        for t, v in zip(lote, vecs):
            if v is None:
                continue
            v = np.asarray(v, dtype=np.float32)
            cache[clave(t)] = v / np.linalg.norm(v)
        print(f"  embeddings {min(i + 8, len(faltan))}/{len(faltan)}", flush=True)
    if faltan:
        np.savez(cache_path, claves=np.array(list(cache)), vecs=np.stack(list(cache.values())))
    return {t: cache.get(clave(t)) for t in textos}


def huella(url):
    with urllib.request.urlopen(f"{url}/api/tags", timeout=30) as r:
        for m in json.load(r)["models"]:
            if m["name"].split(":")[0] == MODELO_EMB:
                return m["digest"]
    return None


def s4(df, url, cache_path):
    textos = set(df.Response.astype(str))
    opciones = {}
    for (p, q), _ in df.groupby(["Panel", "Question"]):
        ops = (get_taxonomy(int(p), int(q)) or {}).get("options") or []
        opciones[(p, q)] = ops
        textos |= set(ops)
    E = embed(sorted(textos), url, cache_path)
    margen, rango = [], []
    for _, r in df.iterrows():
        ops = opciones[(r.Panel, r.Question)]
        lab = r.selected_option
        if str(r.question_type) not in CATEG or lab not in ops:
            margen.append(np.nan); rango.append(np.nan); continue
        v = E[str(r.Response)]
        if v is None or any(E[o] is None for o in ops):
            margen.append(np.nan); rango.append(np.nan); continue
        sims = np.array([float(v @ E[o]) for o in ops])
        s_lab = sims[ops.index(lab)]
        margen.append(float(sims.max() - s_lab))           # 0 = la etiqueta es la más parecida
        rango.append(int((sims > s_lab).sum()) + 1)
    return np.array(margen), np.array(rango)


# ---------------------------------------------------------------- reglas deterministas
# Agregadas el 10-11-2026 tras mirar el objetivo 1 (permitido por el diseño; nunca el objetivo 2).
NUM = re.compile(r"\b(\d+([.,]\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
                 r"twelve|fifteen|twenty|thirty|forty|fifty|half|dos|tres|cuatro|cinco|seis|ocho)\b",
                 re.I)


def anidadas(ops):
    """Opciones que son general/específica entre sí ("No" y "No, subjective…")."""
    base = lambda o: re.split(r"[,(]", o)[0].strip().lower()
    return {o for o in ops for p in ops if o != p and (base(p) == o.strip().lower()
                                                       or base(o) == p.strip().lower())}


def rasgos(df):
    r1, r2 = [], []
    for _, r in df.iterrows():
        cuant = str(r.question_type) == "quantitative"
        r1.append(int(cuant and bool(NUM.search(str(r.Response))) and pd.isna(r.band)))
        ops = (get_taxonomy(int(r.Panel), int(r.Question)) or {}).get("options") or []
        r2.append(int(not cuant and r.selected_option in anidadas(ops)))
    return r1, r2


# ---------------------------------------------------------------- S2, S3, S5 (GLM, k = 1)
def senales_llm(df, corrida):
    """S2 desde el caché de la extracción; S3 y S5 desde senales_llm.jsonl."""
    cache = json.load(open(os.path.join(corrida, "02_extraction_cache.json"), encoding="utf-8"))
    s2 = {}
    for v in cache.values():
        x = v.get("s2") if isinstance(v, dict) else None
        if x and x.get("encontrado") and x.get("margen") is not None:
            s2[v["response_id"]] = x["margen"]
    llm = {}
    for linea in open(os.path.join(corrida, "senales_llm.jsonl"), encoding="utf-8"):
        d = json.loads(linea)
        llm[d["response_id"]] = d
    S2, S3, S5 = [], [], []
    for rid, r in df.iterrows():
        S2.append(s2.get(rid, np.nan))
        d = llm.get(rid, {})
        ev = (d.get("s3") or {}).get("evidence")
        S3.append(np.nan if ev is None else (0.0 if not str(ev).strip()
                                             else parecido_frase(ev, r.Response)))
        S5.append(alarmas_s5(r, d.get("s5") or {}))
    return S2, S3, S5


def alarmas_s5(r, t):
    """Reglas fijas: cuántos rasgos del texto contradicen la etiqueta."""
    if not t or "error" in t:
        return np.nan
    postura = str(t.get("stance", "")).lower()
    num, dep, tema = bool(t.get("gives_number")), bool(t.get("says_depends")), bool(t.get("on_topic"))
    n = 0
    if str(r.question_type) in ("quantitative", "hybrid"):
        n += int(num and pd.isna(r.band))                # dice un número y no hay banda
        n += int(not num and not pd.isna(r.band))        # hay banda sin número en el texto
        return n
    lab = str(r.selected_option)
    base = lab.split(",")[0].strip().lower()
    vacia = lab in ("nan", "Unclassified", "Off-topic")
    n += int(base == "yes" and postura == "no")
    n += int(base == "no" and postura == "yes")
    n += int(lab.strip().lower() in ("yes", "no") and (dep or postura == "conditional"))
    n += int(lab == "Off-topic" and tema)
    n += int(not vacia and not tema)
    return n


# ---------------------------------------------------------------- evaluación
def curva(score, y):
    """% revisado contra % de casos positivos detectados (más sospechoso primero)."""
    orden = np.argsort(-score, kind="stable")
    yy = y[orden]
    x = np.arange(1, len(y) + 1) / len(y)
    return np.r_[0, x], np.r_[0, np.cumsum(yy) / max(1, yy.sum())]


def auc(score, y):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, score)) if 0 < y.sum() < len(y) else np.nan


def capturado(score, y, frac):
    x, c = curva(score, y)
    return float(np.interp(frac, x, c))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("res")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--ollama", default="http://172.28.230.10:11434")
    ap.add_argument("--corrida", help="carpeta de la corrida con señales del GLM (p. ej. Resultados_v4f_k4)")
    a = ap.parse_args()
    out = os.path.join(a.res, "senales" + ("_" + os.path.basename(a.corrida.rstrip("/")) if a.corrida else ""))
    os.makedirs(out, exist_ok=True)

    # Las señales se calculan sobre UNA corrida: la pregunta práctica es si una corrida más
    # alarmas baratas puede reemplazar a correr k veces. Sin --corrida, la corrida es k1 y el
    # objetivo, la inestabilidad entre k1..k; con --corrida (p. ej. la k4 con logprobs) hay dos:
    #   inestable  la etiqueta cambia entre k1..k y la corrida
    #   se_aparta  la corrida no coincide con el voto de k1..k (sin mayoría cuenta como 1)
    corrida = a.corrida or f"{a.res}_k1"
    df = pd.read_csv(f"{corrida}/02_extracted.csv")
    df = con_banda_final(df[df.is_valid_response.astype(bool)]).set_index("response_id")
    y, etiq = inestabilidad(a.res, a.k)
    df = df.join(etiq)
    objetivos = ["inestable"]
    if a.corrida:
        df["kc"] = df.apply(etiqueta, axis=1)
        ks = list(etiq.columns)
        df["inestable"] = (df[ks + ["kc"]].nunique(axis=1, dropna=False) > 1).astype(int)
        def aparta(r):
            v = pd.Series([r[k] for k in ks]).value_counts()
            return int(not (v.iloc[0] * 2 > len(ks) and v.index[0] == r.kc))
        df["se_aparta"] = df.apply(aparta, axis=1)
        objetivos.append("se_aparta")
    else:
        df = df.join(y)
    df["S0_corta"] = -df.Response.astype(str).str.len()
    df["S3p_cita"] = df.apply(s3p, axis=1)
    m, rg = s4(df, a.ollama, os.path.join(out, f"emb_{MODELO_EMB}.npz"))
    df["S4_margen"], df["S4_rango"] = m, rg
    df["R1_numero_sin_banda"], df["R2_opcion_anidada"] = rasgos(df)

    # sospecha: más alto = más sospechoso
    sos = pd.DataFrame(index=df.index)
    sos["S0 longitud"] = df.S0_corta
    sos["S3p cita"] = 1 - df.S3p_cita
    sos["S4 embeddings"] = df.S4_margen
    sos["R reglas (código)"] = df.R1_numero_sin_banda + df.R2_opcion_anidada
    if a.corrida:
        s2, s3, s5 = senales_llm(df, corrida)
        df["S2_margen"], df["S3_cita"], df["S5_alarmas"] = s2, s3, s5
        sos["S2 probabilidades"] = -df.S2_margen
        sos["S3 cita verificada"] = 1 - df.S3_cita
        sos["S5 rasgos"] = df.S5_alarmas

    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.impute import SimpleImputer

    resumen = {"modelo_embeddings": MODELO_EMB, "huella": huella(a.ollama),
               "emb_con_variante": len(EMB_VARIANTE), "emb_fallidos": len(EMB_FALLIDOS),
               "corrida": os.path.basename(corrida.rstrip("/")), "n": int(len(df)),
               "positivos": {o: int(df[o].sum()) for o in objetivos}, "evaluaciones": {}}

    def evaluar(obj, mask):
        d = sos[mask]
        yy = df[obj][mask].to_numpy()
        comb = cross_val_predict(
            make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression()),
            d.to_numpy(), yy, cv=StratifiedKFold(5, shuffle=True, random_state=42),
            method="predict_proba")[:, 1]
        # sin dato = máxima sospecha (no se puede descartar lo que no se pudo medir)
        cols = {c: d[c].fillna(d[c].max()).to_numpy() for c in d.columns}
        cols["Combinación (VC)"] = comb
        r = {"n": int(len(yy)), "positivos": int(yy.sum()), "señales": {}}
        for c, s in cols.items():
            r["señales"][c] = {"auc": round(auc(s, yy), 3), "sin_dato": int(d[c].isna().sum())
                               if c in d else 0,
                               **{f"captura_{int(f*100)}": round(capturado(s, yy, f), 3)
                                  for f in (.1, .2, .3)}}
        return cols, yy, r

    cat = df.question_type.astype(str).isin(CATEG) & df.S4_margen.notna()
    paneles = []
    for obj in objetivos:
        for sub, mask in (("todas", pd.Series(True, index=df.index)), ("categoricas", cat)):
            cols, yy, r = evaluar(obj, mask)
            resumen["evaluaciones"][f"{obj}/{sub}"] = r
            paneles.append((obj, sub, cols, yy))

    df.to_csv(os.path.join(out, "05_senales.csv"))
    json.dump(resumen, open(os.path.join(out, "resumen.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(resumen, ensure_ascii=False, indent=1))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    estilo = {"S0 longitud": ("#898781", "-"), "S3p cita": ("#eda100", ":"),
              "S4 embeddings": ("#2a78d6", "-"), "R reglas (código)": ("#1baf7a", "-"),
              "S2 probabilidades": ("#7d58c9", "-"), "S3 cita verificada": ("#eda100", "-"),
              "S5 rasgos": ("#3d3c38", "-"), "Combinación (VC)": ("#e34948", "-")}
    nombres = {"inestable": "inestables", "se_aparta": "se apartan del voto"}
    filas = len(objetivos)
    fig, axs = plt.subplots(filas, 2, figsize=(11, 4.6 * filas), sharey=True, squeeze=False)
    for ax, (obj, sub, cols, yy) in zip(axs.flat, paneles):
        ax.plot([0, 100], [0, 100], ls="--", c="#c3c2b7", lw=1, label="al azar")
        for c, s in cols.items():
            x, cc = curva(s, yy)
            col, ls = estilo[c]
            ax.plot(x * 100, cc * 100, c=col, ls=ls, lw=2, label=f"{c} (AUC {auc(s, yy):.2f})")
        tit = "todas (S4 sólo en categóricas)" if sub == "todas" else "categóricas con etiqueta en la taxonomía"
        ax.set_title(f"{tit}\nn = {len(yy)}, {nombres[obj]} = {int(yy.sum())}", fontsize=10)
        ax.set_xlabel("% de respuestas revisadas (más sospechosas primero)")
        ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.grid(alpha=.3)
        ax.legend(fontsize=7.5, loc="lower right")
        ax.set_ylabel(f"% de {nombres[obj]} detectadas")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "curva_esfuerzo.png"), dpi=150)


if __name__ == "__main__":
    main()
