#!/usr/bin/env python3
"""
extraer_no_iniciados_b.py

Igual que extraer_no_iniciados.py, con un fallo corregido.

EL FALLO. La version anterior buscaba el patron de DOS importes en los 400
caracteres siguientes a la frase clave, y lo prefería al patron de un importe.
Eso dejaba que una pareja de cifras lejana ganase a la cifra que va pegada a la
frase: en el 10-Q de Alphabet de septiembre de 2021 la frase dice que los
arrendamientos no iniciados son $6.3 billion, y el programa devolvia 17.700,
que sale de sumar los $15.5 billion de pagos futuros totales y los $2.2 billion
de activos por arrendamiento de las frases vecinas.

LA CORRECCION. El importe bueno es el PRIMERO que aparece despues de la frase.
Solo se suma un segundo si va inmediatamente detras, encadenado con "and", que
es como Microsoft separa operativos y financieros. Si entre la frase y la cifra
hay mas de 200 caracteres, no se da por buena: esa distancia ya es otra frase.
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

CLAVE = re.compile(r"not\s+yet\s+commenc", re.I)
IMPORTE = re.compile(r"\$\s*([\d][\d,]*(?:\.\d+)?)\s*(billion|million)?", re.I)
ENCADENADO = re.compile(
    r"^\s*(?:,\s*)?and\s+\$\s*([\d][\d,]*(?:\.\d+)?)\s*(billion|million)?", re.I)
FILA = re.compile(
    r"not\s+yet\s+commenc\w*\s+((?:\$?\s*[\d][\d,]*(?:\.\d+)?\s+){2,})", re.I)

DISTANCIA = 200  # caracteres entre la frase y la cifra

FECHA_FICHERO = re.compile(r"(20\d{2})(\d{2})(\d{2})")
FECHA_TEXTO = re.compile(
    r"as\s+of\s+(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2}),\s*(20\d{2})", re.I)
MESES = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}


def texto_plano(ruta):
    crudo = open(ruta, "rb").read().decode("utf-8", "ignore")
    crudo = BLOQUE.sub(" ", crudo)
    return ESPACIOS.sub(" ", html.unescape(TAG.sub(" ", crudo)))


def a_musd(valor, unidad, por_defecto):
    n = float(valor.replace(",", ""))
    u = (unidad or por_defecto or "").lower()
    return n * 1000.0 if u == "billion" else n


def fecha_del_dato(nombre, ventana):
    trozos = FECHA_FICHERO.findall(os.path.basename(nombre))
    if trozos:
        a, m, d = trozos[-1]
        return f"{a}-{m}-{d}"
    t = FECHA_TEXTO.search(ventana)
    if t:
        return f"{t.group(3)}-{MESES[t.group(1).lower()]:02d}-{int(t.group(2)):02d}"
    return ""


def leer_informe(ruta):
    plano = texto_plano(ruta)
    candidatos = []

    for m in CLAVE.finditer(plano):
        ini = max(0, m.start() - 400)
        ventana = plano[ini:min(len(plano), m.end() + 500)]
        cola = plano[m.end():min(len(plano), m.end() + 600)]

        fila = FILA.search(plano[m.start():m.end() + 400])
        if fila:
            numeros = re.findall(r"[\d][\d,]*(?:\.\d+)?", fila.group(1))
            if len(numeros) >= 3:
                candidatos.append((float(numeros[-1].replace(",", "")),
                                   f"tabla, total de {len(numeros)} columnas",
                                   ventana))
                continue

        primero = IMPORTE.search(cola)
        if not primero or primero.start() > DISTANCIA:
            continue

        resto = cola[primero.end():]
        segundo = ENCADENADO.match(resto)
        if segundo:
            # "of $X billion and $Y billion, respectively": la unidad puede ir
            # solo en el segundo importe
            unidad = primero.group(2) or segundo.group(2)
            total = (a_musd(primero.group(1), primero.group(2), unidad)
                     + a_musd(segundo.group(1), segundo.group(2), unidad))
            candidatos.append((total, "dos importes sumados", ventana))
        else:
            candidatos.append((a_musd(primero.group(1), primero.group(2), None),
                               "un importe", ventana))

    if not candidatos:
        return None
    return max(candidatos, key=lambda c: c[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--informes", default="informes")
    ap.add_argument("--salida", default="no_iniciados_b.csv")
    ap.add_argument("--comparar", default="")
    a = ap.parse_args()

    filas, sin_partida = [], {}
    for ruta in sorted(glob.glob(os.path.join(a.informes, "*"))):
        base = os.path.basename(ruta)
        trozos = base.split("_")
        if len(trozos) < 3:
            continue
        r = leer_informe(ruta)
        if r is None:
            sin_partida[trozos[0]] = sin_partida.get(trozos[0], 0) + 1
            continue
        musd, modo, ventana = r
        filas.append({"empresa": trozos[0], "presentado": trozos[1],
                      "a_fecha": fecha_del_dato(base, ventana),
                      "musd": round(musd, 1), "modo": modo, "fichero": base,
                      "contexto": ventana[:300]})

    filas.sort(key=lambda f: (f["empresa"], f["presentado"]))
    with open(a.salida, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["empresa", "presentado", "a_fecha",
                                           "musd", "modo", "fichero", "contexto"])
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} informes con la partida -> {a.salida}\n")

    por_empresa = {}
    for f in filas:
        por_empresa.setdefault(f["empresa"], []).append(f)
    print(f"{'empresa':<9}{'informes':>9}{'ultimo':>12}{'musd':>14}  modo")
    for e in sorted(por_empresa):
        u = sorted(por_empresa[e], key=lambda f: f["presentado"])[-1]
        print(f"{e:<9}{len(por_empresa[e]):>9}{u['presentado']:>12}"
              f"{u['musd']:>14,.0f}  {u['modo']}")

    if a.comparar and os.path.exists(a.comparar):
        viejo = {}
        with open(a.comparar) as fh:
            for r in csv.DictReader(fh):
                viejo[(r["empresa"], r["presentado"])] = float(r["musd"])
        nuevo = {(f["empresa"], f["presentado"]): f["musd"] for f in filas}
        comunes = set(viejo) & set(nuevo)
        distintos = sorted(k for k in comunes if abs(viejo[k] - nuevo[k]) >= 1.0)
        print(f"\nCOMPROBACION contra {a.comparar}")
        print(f"  importes que coinciden : {len(comunes) - len(distintos)} de {len(comunes)}")
        if distintos:
            print(f"  {'empresa':<8}{'presentado':<12}{'antes':>14}{'ahora':>14}")
            for k in distintos[:25]:
                print(f"  {k[0]:<8}{k[1]:<12}{viejo[k]:>14,.0f}{nuevo[k]:>14,.0f}")
        solo_antes = sorted(set(viejo) - set(nuevo))
        if solo_antes:
            print(f"  estaban antes y ahora no: {len(solo_antes)}")


if __name__ == "__main__":
    main()
