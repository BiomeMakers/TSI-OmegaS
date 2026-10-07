#!/usr/bin/env python3
"""
serie_concentracion_b.py

Corrige tres fallos de serie_concentracion.py.

FALLO 1, "50 largest customers" contaba como mayor cliente. El patron
"largest customer" encaja dentro de "our 50 largest customers", asi que Equinix
salia con un mayor cliente del 36% cuando el suyo es del 2%. Se arregla
exigiendo que no haya un numero justo antes de "largest".

FALLO 2, el resumen cogia el porcentaje MAS ALTO. Los informes ponen siempre el
periodo anterior al lado para comparar, asi que el mas alto suele ser el del
año pasado: CoreWeave salia con el 71% de junio de 2025 en vez del 36% de junio
de 2026, y Broadcom con el 55% del trimestre en vez del 50% de los tres
trimestres. Ahora cada porcentaje se ancla al periodo que la frase nombra
("for the three months ended June 30, 2026") y el resumen se queda con el mas
reciente, no con el mayor.

FALLO 3, las listas. CoreWeave no da el agregado de sus tres mayores clientes,
da los tres por separado: "36%, 26%, and 10% ... from our top three customers".
Eso se detecta y se suma, guardando los sumandos.

USO:
  python3 serie_concentracion_b.py --informes informes \\
                                   --salida concentracion_series_b.csv
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

PROVEEDORES = ["DLR", "EQIX", "OWL", "NVDA", "AVGO", "VRT", "ETN", "ORCL", "CRWV"]

PCT = r"(\d{1,3}(?:\.\d+)?)\s*%"
# lista de porcentajes: "36%, 26%, and 10%"
LISTA = re.compile(r"((?:\d{1,3}(?:\.\d+)?\s*%\s*,?\s*(?:and\s+)?){2,})", re.I)

MESES = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}
PERIODO = re.compile(
    r"(?:ended|as\s+of)\s+(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2}),?\s*(20\d{2})", re.I)
PERIODO_ANIO = re.compile(r"(?:fiscal|year)\s+(20\d{2})", re.I)

REGLAS = [
    # el (?<![\d\s]\d) evita "50 largest customers"
    (re.compile(rf"(?<!\d )(?<!\d{{2}} )largest\s+customer(?:'s)?[^.]{{0,130}}?{PCT}", re.I),
     "mayor_cliente", None),
    (re.compile(rf"{PCT}\s+of\s+(?:our\s+)?(?:total\s+)?revenue[s]?\s+from\s+"
                rf"(?:our\s+)?top\s+customer", re.I), "mayor_cliente", None),
    (re.compile(rf"(?:top|largest)\s+(\w+)\s+(?:end\s+)?customers[^.]{{0,170}}?{PCT}", re.I),
     "top_n", "n_primero"),
    (re.compile(rf"{PCT}\s+of\s+(?:our\s+)?revenue[s]?\s+from\s+(?:our\s+)?"
                rf"top\s+(\w+)\s+customers", re.I), "top_n", "pct_primero"),
    (re.compile(rf"no\s+(?:single\s+|one\s+|other\s+individual\s+)?customer"
                rf"[^.]{{0,150}}?{PCT}", re.I), "umbral", None),
]

PALABRAS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
            "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twenty": 20,
            "thirty": 30, "forty": 40, "fifty": 50}

BASES = [("accounts receivable", "cuentas por cobrar"),
         ("annualized recurring revenue", "ingresos recurrentes anualizados"),
         ("recurring revenue", "ingresos recurrentes"),
         ("net revenue", "ingresos netos"),
         ("total revenue", "ingresos totales"),
         ("net sales", "ventas netas"),
         ("revenue", "ingresos")]

FECHA_FICHERO = re.compile(r"(20\d{2})(\d{2})(\d{2})")


def texto_plano(ruta):
    crudo = open(ruta, "rb").read().decode("utf-8", "ignore")
    crudo = BLOQUE.sub(" ", crudo)
    return ESPACIOS.sub(" ", html.unescape(TAG.sub(" ", crudo)))


def num_clientes(txt):
    t = txt.strip().lower()
    return int(t) if t.isdigit() else PALABRAS.get(t)


def base_del_pct(frase):
    f = frase.lower()
    for clave, nombre in BASES:
        if clave in f:
            return nombre
    return "sin identificar"


def periodo_de(cola):
    """El periodo que la frase nombra JUSTO DESPUES del porcentaje."""
    m = PERIODO.search(cola)
    if m:
        return f"{m.group(3)}-{MESES[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    m = PERIODO_ANIO.search(cola)
    if m:
        return f"{m.group(1)}-12-31"
    return ""


def suma_de_lista(cola_previa, n):
    """Para 'X%, Y%, and Z% ... top three customers': suma los n sumandos."""
    m = LISTA.search(cola_previa)
    if not m:
        return None, None
    nums = [float(x) for x in re.findall(r"\d{1,3}(?:\.\d+)?", m.group(1))]
    if n and len(nums) == n:
        return sum(nums), nums
    return None, None


def leer(ruta):
    plano = texto_plano(ruta)
    salida, visto = [], set()
    for regla, tipo, donde in REGLAS:
        for m in regla.finditer(plano):
            g = m.groups()
            if tipo == "top_n":
                if donde == "n_primero":
                    n, pct = num_clientes(g[0]), g[1]
                else:
                    pct, n = g[0], num_clientes(g[1])
                if n is None:
                    continue
            else:
                n, pct = (1 if tipo == "mayor_cliente" else None), g[0]
            try:
                valor = float(pct)
            except (TypeError, ValueError):
                continue
            if not 0 < valor <= 100:
                continue

            frase = plano[max(0, m.start() - 170):m.end() + 170].strip()
            sumandos = ""
            if tipo == "top_n":
                total, nums = suma_de_lista(plano[max(0, m.start() - 170):m.end()], n)
                if total is not None and abs(total - valor) > 0.5:
                    valor = total
                    sumandos = " + ".join(f"{x:g}" for x in nums)

            per = periodo_de(plano[m.end():m.end() + 200])
            clave = (tipo, n, valor, per)
            if clave in visto:
                continue
            visto.add(clave)
            salida.append({"tipo": tipo, "n_clientes": n, "pct": valor,
                           "periodo": per, "sumandos": sumandos,
                           "base": base_del_pct(frase), "frase": frase})
    return salida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--informes", default="informes")
    ap.add_argument("--salida", default="concentracion_series_b.csv")
    a = ap.parse_args()

    filas = []
    for ruta in sorted(glob.glob(os.path.join(a.informes, "*"))):
        base = os.path.basename(ruta)
        t = base.split("_")
        if len(t) < 3 or t[0] not in PROVEEDORES:
            continue
        f_fich = FECHA_FICHERO.findall(base)
        a_fecha = (f"{f_fich[-1][0]}-{f_fich[-1][1]}-{f_fich[-1][2]}"
                   if f_fich else "")
        for r in leer(ruta):
            r.update({"empresa": t[0], "presentado": t[1], "a_fecha": a_fecha,
                      "fichero": base})
            filas.append(r)

    campos = ["empresa", "presentado", "a_fecha", "tipo", "n_clientes", "pct",
              "periodo", "sumandos", "base", "fichero", "frase"]
    filas.sort(key=lambda f: (f["empresa"], f["presentado"], f["tipo"]))
    with open(a.salida, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        for f in filas:
            w.writerow({**f, "frase": f["frase"][:400]})
    print(f"{len(filas)} frases -> {a.salida}\n")

    buenos = [f for f in filas
              if f["base"] not in ("cuentas por cobrar", "sin identificar")
              and f["periodo"]]
    print("CONCENTRACION DE CLIENTES, DATO MAS RECIENTE DE CADA EMPRESA")
    print("anclado al periodo que nombra la propia frase, no al mayor valor\n")
    print(f"{'empresa':<8}{'periodo':<12}{'tipo':<15}{'n':>4}{'pct':>7}  "
          f"{'base':<28}sumandos")
    for emp in PROVEEDORES:
        de_emp = [f for f in buenos if f["empresa"] == emp]
        if not de_emp:
            print(f"{emp:<8}sin dato de concentracion sobre ingresos con periodo")
            continue
        for tipo in ("mayor_cliente", "top_n", "umbral"):
            cand = [f for f in de_emp if f["tipo"] == tipo]
            if not cand:
                continue
            r = max(cand, key=lambda f: (f["periodo"], f["presentado"]))
            n = r["n_clientes"] if r["n_clientes"] else "-"
            print(f"{emp:<8}{r['periodo']:<12}{tipo:<15}{str(n):>4}"
                  f"{r['pct']:>7.1f}  {r['base']:<28}{r['sumandos']}")

    print("\nComprobar a mano antes de usar: el mayor cliente de CRWV, los 20")
    print("mayores de DLR y los 5 de AVGO. Las frases estan en el CSV.")


if __name__ == "__main__":
    main()
