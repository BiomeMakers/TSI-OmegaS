#!/usr/bin/env python3
"""
extraer_concentracion.py

El otro lado de la cadena. Hasta ahora hemos medido cuanto hay comprometido por
quien PROMETE PAGAR (los que alquilan centros de datos). Esto busca lo otro:
quien se ENDEUDO contra esa promesa, y cuanto depende de ella.

LA PREGUNTA. Un compromiso de Microsoft es seguro mientras Microsoft pague. El
riesgo no esta ahi: esta en quien construyo el centro con dinero prestado
contra ese contrato, y en como de concentrada esta su cartera de inquilinos. Un
casero cuyo mayor cliente es el 40% de sus ingresos no tiene un negocio
diversificado, tiene una apuesta.

QUE BUSCA. Las frases de concentracion de clientes que las empresas declaran en
sus 10-K, que suelen tener una de estas formas:
  "our largest customer accounted for X% of ... revenue"
  "our top 20 customers represented X% of ..."
  "no customer accounted for more than X% of ..."
  "one customer represented X% of total revenues"

ESTA ES UNA PASADA DE DESCUBRIMIENTO. No produce un numero todavia: imprime las
frases encontradas con su contexto para poder leerlas y decidir que partida
cuenta y cual no, igual que se hizo con los arrendamientos. Primero se mira lo
que dicen, luego se mide.

USO:
  python3 extraer_concentracion.py --informes informes
  python3 extraer_concentracion.py --informes informes --empresa DLR --todos
"""
import argparse
import glob
import html
import os
import re

TAG = re.compile(r"<[^>]+>")
BLOQUE = re.compile(r"(?is)<(script|style)\b.*?</\1>")
ESPACIOS = re.compile(r"\s+")

# el lado proveedor: caseros, avalistas, prestamistas, fabricantes
PROVEEDORES = ["DLR", "EQIX", "OWL", "NVDA", "AVGO", "VRT", "ETN", "ORCL", "CRWV"]

PATRONES = [
    (r"largest\s+customer[^.]{0,200}?\d[\d.]*\s*%", "mayor cliente"),
    (r"(?:top|largest)\s+\d+\s+customers[^.]{0,200}?\d[\d.]*\s*%", "top N clientes"),
    (r"no\s+(?:single\s+)?customer[^.]{0,160}?\d[\d.]*\s*%", "ningun cliente supera"),
    (r"one\s+customer[^.]{0,160}?\d[\d.]*\s*%", "un cliente"),
    (r"customer\s+concentration[^.]{0,250}", "concentracion de clientes"),
    (r"\d[\d.]*\s*%\s+of\s+(?:our\s+)?(?:total\s+)?(?:revenues?|rental\s+revenue)"
     r"[^.]{0,120}?customer", "porcentaje de ingresos por cliente"),
]
PATRONES = [(re.compile(p, re.I), n) for p, n in PATRONES]

# nombres con los que los caseros se refieren a los inquilinos grandes
INQUILINOS = re.compile(
    r"\b(Microsoft|Meta\s+Platforms|Alphabet|Google|Amazon|Oracle|CoreWeave|"
    r"OpenAI|Anthropic|xAI|ByteDance|Tesla|IBM)\b")


def texto_plano(ruta):
    crudo = open(ruta, "rb").read().decode("utf-8", "ignore")
    crudo = BLOQUE.sub(" ", crudo)
    return ESPACIOS.sub(" ", html.unescape(TAG.sub(" ", crudo)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--informes", default="informes")
    ap.add_argument("--empresa", default="")
    ap.add_argument("--todos", action="store_true",
                    help="todos los informes; por defecto solo el mas reciente")
    a = ap.parse_args()

    por_empresa = {}
    for ruta in sorted(glob.glob(os.path.join(a.informes, "*"))):
        base = os.path.basename(ruta)
        t = base.split("_")
        if len(t) < 3:
            continue
        emp, fecha = t[0], t[1]
        if a.empresa and emp != a.empresa:
            continue
        if not a.empresa and emp not in PROVEEDORES:
            continue
        por_empresa.setdefault(emp, []).append((fecha, ruta))

    if not por_empresa:
        print("ningun informe de las empresas del lado proveedor")
        return

    for emp in sorted(por_empresa):
        informes = sorted(por_empresa[emp])
        if not a.todos:
            # los 10-K llevan la concentracion; los 10-Q casi nunca
            informes = informes[-3:]
        print("\n" + "=" * 72)
        print(f"{emp}   ({len(por_empresa[emp])} informes, se leen {len(informes)})")
        print("=" * 72)

        hubo = False
        for fecha, ruta in informes:
            plano = texto_plano(ruta)
            visto = set()
            for pat, nombre in PATRONES:
                for m in pat.finditer(plano):
                    frase = plano[max(0, m.start() - 120):m.end() + 160]
                    clave = frase[:90]
                    if clave in visto:
                        continue
                    visto.add(clave)
                    hubo = True
                    print(f"\n  [{fecha}] {nombre}")
                    print(f"    ...{frase.strip()}...")
            nombres = sorted(set(INQUILINOS.findall(plano)))
            if nombres:
                print(f"\n  [{fecha}] inquilinos o clientes nombrados en el informe:")
                print(f"    {', '.join(nombres)}")
                hubo = True
        if not hubo:
            print("\n  sin frases de concentracion en los informes leidos")
            print("  (probar con --todos, o la empresa no lo declara asi)")

    print("\n" + "=" * 72)
    print("Esto es una pasada de descubrimiento: hay que LEER las frases antes")
    print("de convertirlas en numero. Lo que se busca es (1) que porcentaje de")
    print("sus ingresos depende de sus mayores clientes y (2) si esos clientes")
    print("son las mismas cinco empresas que firman los arrendamientos. Si lo")
    print("son, la cadena no esta diversificada: es la misma apuesta contada")
    print("dos veces, una por quien promete pagar y otra por quien presto.")


if __name__ == "__main__":
    main()
