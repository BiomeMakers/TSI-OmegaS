#!/usr/bin/env python3
"""
extraer_plazos.py

Añade la dimension que faltaba: el PLAZO de los arrendamientos firmados sin
comenzar.

POR QUE HACE FALTA. Hasta ahora la medicion cuenta igual 300.000 millones
comprometidos a tres años que a quince, y no son el mismo riesgo. Los contratos
son de una decada o mas y la tecnologia se renueva cada dos o tres años: si un
chip futuro hace el mismo trabajo con una fraccion de la energia, el que firmo
sigue pagando por un edificio dimensionado para la tecnologia de hoy. El riesgo
de esta cadena no es que nadie pueda pagar, es que lo prometido deje de merecer
la pena, y eso depende del plazo y de cuando empieza.

ES EL PATRON DE LAS TELECOS DE 2001, no el de las hipotecas de 2007. La fibra
que se tendio entonces funcionaba y la demanda llego, pero llego tarde y con
tanta capacidad instalada que los precios se hundieron. No fallo la tecnologia,
fallo el calendario.

QUE BUSCA, en las mismas frases de "not yet commenced" que ya se extraen:
  cuando empiezan   "these leases will commence between 2026 and 2029"
                    "with lease terms commencing in fiscal 2027"
  cuanto duran      "estimated lease terms of seven to sixteen years"
                    "with terms of up to 15 years"
  plazo medio       "weighted average remaining lease term of 8 years"

NO INVENTA NADA. Si una empresa no declara el plazo, la fila sale vacia y se
dice. Un plazo estimado por nosotros no seria un dato.

USO:
  python3 extraer_plazos.py --informes informes --salida plazos.csv
"""
import argparse
import csv
import glob
import html
import os
import re

TAG = re.compile(r"<[^>]+>")
BLOQUE = re.compile(r"(?is)<(script|style)\b.*?</\1>")
ESPACIOS = re.compile(r"\s+")

EMPRESAS = ["MSFT", "META", "GOOGL", "AMZN", "CRWV", "ORCL", "DLR", "EQIX"]

CLAVE = re.compile(r"not\s+yet\s+commenc", re.I)

PALABRAS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
            "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
            "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
            "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
            "twenty": 20, "twenty-five": 25, "thirty": 30}
NUM = r"(\d{1,2}|" + "|".join(sorted(PALABRAS, key=len, reverse=True)) + r")"

# cuando empiezan
INICIO_RANGO = re.compile(r"commenc\w*\s+(?:between|from)\s+(20\d{2})\s+"
                          r"(?:and|to|through)\s+(20\d{2})", re.I)
INICIO_ANIO = re.compile(r"(?:will\s+)?commenc\w*\s+(?:in|during)\s+"
                         r"(?:fiscal\s+)?(20\d{2})", re.I)

# cuanto duran
PLAZO_RANGO = re.compile(rf"(?:lease\s+)?terms?\s+(?:of\s+)?{NUM}\s+to\s+{NUM}\s+years", re.I)
PLAZO_HASTA = re.compile(rf"terms?\s+of\s+up\s+to\s+{NUM}\s+years", re.I)
PLAZO_MEDIO = re.compile(rf"weighted[- ]average\s+(?:remaining\s+)?lease\s+term"
                         rf"[^.]{{0,60}}?{NUM}(?:\.\d+)?\s+years", re.I)

FECHA_FICHERO = re.compile(r"(20\d{2})(\d{2})(\d{2})")


def texto_plano(ruta):
    crudo = open(ruta, "rb").read().decode("utf-8", "ignore")
    crudo = BLOQUE.sub(" ", crudo)
    return ESPACIOS.sub(" ", html.unescape(TAG.sub(" ", crudo)))


def a_num(t):
    t = t.strip().lower()
    return int(t) if t.isdigit() else PALABRAS.get(t)


def leer(ruta):
    plano = texto_plano(ruta)
    filas = []
    for m in CLAVE.finditer(plano):
        ventana = plano[m.start():min(len(plano), m.end() + 700)]
        r = {"inicio_desde": "", "inicio_hasta": "", "plazo_min": "",
             "plazo_max": "", "plazo_medio": "", "frase": ""}

        g = INICIO_RANGO.search(ventana)
        if g:
            r["inicio_desde"], r["inicio_hasta"] = g.group(1), g.group(2)
        else:
            g = INICIO_ANIO.search(ventana)
            if g:
                r["inicio_desde"] = r["inicio_hasta"] = g.group(1)

        g = PLAZO_RANGO.search(ventana)
        if g:
            r["plazo_min"], r["plazo_max"] = a_num(g.group(1)), a_num(g.group(2))
        else:
            g = PLAZO_HASTA.search(ventana)
            if g:
                r["plazo_max"] = a_num(g.group(1))

        g = PLAZO_MEDIO.search(ventana)
        if g:
            r["plazo_medio"] = a_num(g.group(1))

        if any(r[k] != "" for k in ("inicio_desde", "plazo_min", "plazo_max",
                                    "plazo_medio")):
            r["frase"] = ventana[:380].strip()
            filas.append(r)
    if not filas:
        return None
    # la mas informativa: la que rellena mas campos
    return max(filas, key=lambda f: sum(1 for k, v in f.items()
                                        if k != "frase" and v != ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--informes", default="informes")
    ap.add_argument("--salida", default="plazos.csv")
    a = ap.parse_args()

    filas, sin_plazo = [], {}
    for ruta in sorted(glob.glob(os.path.join(a.informes, "*"))):
        base = os.path.basename(ruta)
        t = base.split("_")
        if len(t) < 3 or t[0] not in EMPRESAS:
            continue
        r = leer(ruta)
        if r is None:
            sin_plazo[t[0]] = sin_plazo.get(t[0], 0) + 1
            continue
        f = FECHA_FICHERO.findall(base)
        r.update({"empresa": t[0], "presentado": t[1],
                  "a_fecha": f"{f[-1][0]}-{f[-1][1]}-{f[-1][2]}" if f else "",
                  "fichero": base})
        filas.append(r)

    campos = ["empresa", "presentado", "a_fecha", "inicio_desde", "inicio_hasta",
              "plazo_min", "plazo_max", "plazo_medio", "fichero", "frase"]
    filas.sort(key=lambda f: (f["empresa"], f["presentado"]))
    with open(a.salida, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        for f in filas:
            w.writerow({**f, "frase": f["frase"][:380]})
    print(f"{len(filas)} informes con plazo declarado -> {a.salida}\n")

    print("PLAZOS DECLARADOS, ULTIMO INFORME DE CADA EMPRESA")
    print(f"\n{'empresa':<8}{'presentado':<12}{'empiezan':<16}"
          f"{'duran (años)':<15}{'medio':>7}")
    por_emp = {}
    for f in filas:
        por_emp.setdefault(f["empresa"], []).append(f)
    for e in sorted(por_emp):
        u = sorted(por_emp[e], key=lambda f: f["presentado"])[-1]
        ini = (f"{u['inicio_desde']}-{u['inicio_hasta']}"
               if u["inicio_desde"] and u["inicio_hasta"] != u["inicio_desde"]
               else (u["inicio_desde"] or "no lo dice"))
        if u["plazo_min"] != "" and u["plazo_max"] != "":
            dur = f"{u['plazo_min']} a {u['plazo_max']}"
        elif u["plazo_max"] != "":
            dur = f"hasta {u['plazo_max']}"
        else:
            dur = "no lo dice"
        med = u["plazo_medio"] if u["plazo_medio"] != "" else "."
        print(f"{e:<8}{u['presentado']:<12}{ini:<16}{dur:<15}{str(med):>7}")

    if sin_plazo:
        print("\ninformes con la partida pero SIN plazo declarado:")
        for e in sorted(sin_plazo):
            print(f"  {e:<8}{sin_plazo[e]}")
    print("\nEl plazo medio solo se toma si esta EN la frase de los")
    print("arrendamientos sin comenzar. El que las empresas declaran aparte")
    print("se refiere a toda su cartera, incluidos los ya en marcha, y no es")
    print("comparable.")
    print("\nDonde no lo declaran, la fila va vacia. Un plazo estimado por")
    print("nosotros no seria un dato.")


if __name__ == "__main__":
    main()
