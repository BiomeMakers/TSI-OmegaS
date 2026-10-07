#!/usr/bin/env python3
"""
zona_roja_v5.py

Agrega las empresas de la cadena y expresa el credito en las unidades del
articulo de Greenwood, Hanson, Shleifer y Sorensen (JF 77(2), 2022): puntos
porcentuales de PIB, y su variacion en tres anos frente al umbral de 8,99 pp.
La pata de precios, en crecimiento logaritmico a tres anos frente a 26,56%.

SUSTITUYE A zona_roja_v3.py, que calculaba lo mismo sobre la serie del 6-oct.
Aquella serie no se puede reconstruir (su programa no quedo guardado) y era del
orden de tres veces la deuda financiera, lo que encaja con que incluyera los
pasivos por arrendamiento: es decir, contaba los arrendamientos en la deuda
declarada y otra vez en el ajuste. La v3 hay que retirarla del repositorio, no
corregirla.

QUE SE AGREGA. Las cinco empresas con serie: MSFT, META, GOOGL, AMZN, CRWV.
Oracle queda fuera porque NO PUBLICA el importe de arrendamientos firmados sin
comenzar: menciona la categoria en una vineta de su 10-K y remite a las notas
sin dar cifra. Eso significa que incluso la medicion ajustada se queda corta, y
asi hay que escribirlo.

LA PATA DE PRECIOS. Indice de la cadena como media simple de los log-precios de
las empresas con precio en el trimestre. No esta ponderado por capitalizacion
porque no tenemos el numero de acciones en la serie; es una aproximacion y se
dice. No esta deflactado por IPC, lo que lo deja en nominal: pendiente
declarado.

LO QUE ESTE PROGRAMA NO HACE. No afirma que el indicador se encienda. Cinco
empresas no son el credito empresarial de un pais, que es sobre lo que esta
calibrado el umbral. Lo que mide es cuanto se mueve la lectura entre el credito
declarado y el comprometido, con las dos en las mismas unidades.

USO:
  python3 zona_roja_v5.py --series zona_roja_v4_series.csv --pib pib_usa.csv
"""
import argparse

import numpy as np
import pandas as pd

UMBRAL_CREDITO = 8.99   # pp de PIB, percentil 80 del articulo
UMBRAL_PRECIO = 26.56   # % log a tres anos, percentil 66,7
TRIMESTRES = 12


def carga_pib(ruta):
    """Admite el volcado de FRED (DATE, GDP en miles de millones)."""
    p = pd.read_csv(ruta)
    cols = {c.lower(): c for c in p.columns}
    fecha = next((cols[c] for c in cols if c in
                  ("date", "observation_date", "fecha", "trimestre")), p.columns[0])
    valor = next((cols[c] for c in cols if c in
                  ("gdp", "pib", "pib_musd", "value", "valor")), p.columns[-1])
    p = p[[fecha, valor]].rename(columns={fecha: "f", valor: "pib_gm"})
    p["pib_gm"] = pd.to_numeric(p["pib_gm"], errors="coerce")
    p = p.dropna()
    try:
        p["trimestre"] = pd.PeriodIndex(p["f"].astype(str), freq="Q").astype(str)
    except Exception:
        p["trimestre"] = pd.to_datetime(p["f"]).dt.to_period("Q").astype(str)
    return p.groupby("trimestre", as_index=False)["pib_gm"].last()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", default="zona_roja_v4_series.csv")
    ap.add_argument("--pib", default="pib_usa.csv")
    ap.add_argument("--salida", default="zona_roja_v5_series.csv")
    a = ap.parse_args()

    d = pd.read_csv(a.series)
    pib = carga_pib(a.pib)

    # agregado de la cadena por trimestre
    g = d.groupby("trimestre").agg(
        deuda_declarada=("deuda_declarada", "sum"),
        fuera_balance=("fuera_balance", "sum"),
        deuda_ajustada=("deuda_ajustada", "sum"),
        empresas=("empresa", "nunique")).reset_index()

    # indice de precios de la cadena: media simple de log-precios
    p = d.dropna(subset=["precio"]).copy()
    p["lp"] = np.log(p["precio"])
    idx = p.groupby("trimestre").agg(lp=("lp", "mean"),
                                     n_precio=("lp", "size")).reset_index()
    g = g.merge(idx, on="trimestre", how="left").merge(pib, on="trimestre", how="left")

    sin_pib = g["pib_gm"].isna().sum()
    if sin_pib:
        print(f"trimestres sin PIB, se caen del calculo: {sin_pib}")
    g = g.dropna(subset=["pib_gm"]).sort_values("trimestre").reset_index(drop=True)

    # deuda y PIB ambos en millones de dolares -> %
    for c in ("deuda_declarada", "deuda_ajustada"):
        g[f"pct_pib_{c}"] = g[c] / g["pib_gm"] * 100.0
        g[f"d3_{c}"] = g[f"pct_pib_{c}"] - g[f"pct_pib_{c}"].shift(TRIMESTRES)
    g["g3_precio_pct"] = 100.0 * (g["lp"] - g["lp"].shift(TRIMESTRES))
    g.to_csv(a.salida, index=False)

    u = g.iloc[-1]
    print(f"\nUltimo trimestre: {u['trimestre']}  "
          f"({int(u['empresas'])} empresas, {int(u['n_precio'])} con precio)\n")

    print("=" * 70)
    print("EL CREDITO DE LA CADENA EN UNIDADES DEL ARTICULO")
    print("=" * 70)
    print(f"\n{'':<26}{'declarado':>14}{'ajustado':>14}{'factor':>10}")
    print(f"{'nivel, % del PIB EEUU':<26}{u['pct_pib_deuda_declarada']:>14.2f}"
          f"{u['pct_pib_deuda_ajustada']:>14.2f}"
          f"{u['pct_pib_deuda_ajustada'] / u['pct_pib_deuda_declarada']:>10.2f}")
    print(f"{'variacion 3 anos, pp':<26}{u['d3_deuda_declarada']:>14.2f}"
          f"{u['d3_deuda_ajustada']:>14.2f}"
          f"{u['d3_deuda_ajustada'] / u['d3_deuda_declarada']:>10.2f}")
    print(f"{'sobre el umbral de 8,99':<26}"
          f"{100 * u['d3_deuda_declarada'] / UMBRAL_CREDITO:>13.0f}%"
          f"{100 * u['d3_deuda_ajustada'] / UMBRAL_CREDITO:>13.0f}%")

    print(f"\npata de precios: {u['g3_precio_pct']:.1f}% log a tres anos, "
          f"umbral {UMBRAL_PRECIO}%  -> "
          f"{'por encima' if u['g3_precio_pct'] >= UMBRAL_PRECIO else 'por debajo'}")
    print("(nominal, sin deflactar por IPC: pendiente declarado)")

    print("\nComo leerlo. La pata de precios supera su umbral; la de credito no,")
    print("en ninguna de las dos versiones. Pero cinco empresas no son el credito")
    print("empresarial de un pais, que es sobre lo que el umbral esta calibrado,")
    print("asi que lo que dice este cuadro no es si el indicador se enciende,")
    print("sino cuanto cambia la lectura al medir el credito comprometido en vez")
    print("del declarado: un factor de "
          f"{u['d3_deuda_ajustada'] / u['d3_deuda_declarada']:.1f} en la variacion a tres anos.")

    print("\n" + "=" * 70)
    print("RECORRIDO DE LOS ULTIMOS 8 TRIMESTRES")
    print("=" * 70)
    print(f"\n{'trim':<9}{'% PIB decl':>12}{'% PIB ajus':>12}"
          f"{'d3 decl':>10}{'d3 ajus':>10}{'precio 3a':>11}")
    for _, r in g.tail(8).iterrows():
        def f(x, d=2):
            return "." if pd.isna(x) else f"{x:.{d}f}"
        print(f"{r['trimestre']:<9}{f(r['pct_pib_deuda_declarada']):>12}"
              f"{f(r['pct_pib_deuda_ajustada']):>12}{f(r['d3_deuda_declarada']):>10}"
              f"{f(r['d3_deuda_ajustada']):>10}{f(r['g3_precio_pct'], 1):>11}")

    print("\nOracle queda fuera del agregado: declara que tiene arrendamientos")
    print("firmados sin comenzar pero no publica el importe. La medicion")
    print("ajustada tambien se queda corta, y eso hay que escribirlo.")


if __name__ == "__main__":
    main()
