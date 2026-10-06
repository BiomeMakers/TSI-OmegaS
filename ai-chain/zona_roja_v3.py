#!/usr/bin/env python3
"""
zona_roja_v3.py

Sitúa la cadena de la IA en el indicador de Greenwood, Hanson, Shleifer y
Sørensen (Journal of Finance 77(2), 2022) EN SUS UNIDADES Y CON SUS CORTES
ABSOLUTOS, en vez de con percentiles calculados sobre la historia propia.

LOS CORTES, de la nota 8 del artículo:
    crédito  Δ3(Deuda empresarial / PIB) > 8.99 puntos porcentuales
    precios  Δ3 log(índice bursátil real) > 26.56 %
y la zona amarilla, más laxa, en los percentiles 60 y 33.3.
Cuando los dos se cumplen a la vez, la probabilidad de crisis en los tres años
siguientes es del 45.3%, frente al 4.1% incondicional a un año.

POR QUÉ IMPORTA LA UNIDAD. Su medida de crédito es deuda SOBRE PIB, no el
crecimiento porcentual de la deuda. Eso elimina el efecto de base que hace que
Alphabet parezca disparada por haber partido de 16.726 millones: lo que entra
en el indicador es cuántos puntos de PIB ha ganado la deuda, no por cuánto se
ha multiplicado.

LO QUE ESTE CÁLCULO NO ES. Su unidad de observación es un PAÍS y su umbral se
refiere a TODO el crédito empresarial de ese país. Aquí se mide un puñado de
empresas, así que el resultado no se lee como "la cadena está en la zona roja":
se lee como cuántos puntos de PIB aporta por sí sola esta parte de la cadena
frente al umbral que define un país entero. Decirlo de otra forma seria falso.

USO:
  python3 zona_roja_v3.py --series zona_roja_v2_series.csv --pib pib_usa.csv

pib_usa.csv: dos columnas, trimestre y pib_musd, con el PIB nominal de EE.UU.
en millones. Se baja de FRED, serie GDP, en
https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDP
(viene en miles de millones: multiplicar por 1000).
"""
import argparse
import numpy as np
import pandas as pd

CORTE_CREDITO = 8.99      # puntos porcentuales de PIB, 3 anos
CORTE_PRECIO = 26.56      # % log, 3 anos
CORTE_CREDITO_Y = None    # la zona amarilla va por percentil 60, no publicado
EMP = ["MSFT", "META", "GOOGL", "AMZN"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", default="zona_roja_v2_series.csv")
    ap.add_argument("--pib", default="pib_usa.csv")
    a = ap.parse_args()

    d = pd.read_csv(a.series)
    d = d[d.empresa.isin(EMP)]
    try:
        pib = pd.read_csv(a.pib)
    except FileNotFoundError:
        print(f"falta {a.pib}. Bajalo de FRED:")
        print("  curl -s 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDP'"
              " -o gdp.csv")
        print("  y conviertelo a dos columnas: trimestre (2026Q2) y pib_musd")
        return

    # agregado de la cadena, por trimestre
    g = d.groupby("trimestre").agg(
        declarada=("deuda_declarada", "sum"),
        ajustada=("deuda_ajustada", "sum"),
        fuera=("fuera_balance", "sum"),
        n=("empresa", "count")).reset_index()
    # solo trimestres donde estan todas, para que la suma sea comparable
    g = g[g.n == g.n.max()]
    g = g.merge(pib, on="trimestre", how="inner").sort_values("trimestre")
    if g.empty:
        print("sin trimestres en comun entre las series y el PIB"); return

    for col in ("declarada", "ajustada"):
        g[f"{col}_pib"] = 100.0 * g[col] / g.pib_musd
        g[f"d3_{col}"] = g[f"{col}_pib"] - g[f"{col}_pib"].shift(12)

    # precios: indice igualmente ponderado de la cadena, log real seria lo
    # correcto; aqui se usa nominal y se dice
    pr = d.pivot_table(index="trimestre", columns="empresa", values="precio")
    pr = pr.dropna()
    idx = (pr / pr.iloc[0]).mean(axis=1)
    g = g.merge(idx.rename("indice").reset_index(), on="trimestre", how="left")
    g["d3_precio"] = 100.0 * (np.log(g.indice) - np.log(g.indice.shift(12)))

    print("EN LAS UNIDADES DEL ARTICULO")
    print(f"cortes: credito > {CORTE_CREDITO} puntos de PIB en 3 anos, "
          f"precio > {CORTE_PRECIO}% log en 3 anos\n")
    print(f"{'trimestre':<10}{'decl/PIB':>10}{'ajus/PIB':>10}"
          f"{'d3 decl':>9}{'d3 ajus':>9}{'d3 precio':>11}   zona")
    for _, r in g.dropna(subset=["d3_declarada"]).tail(10).iterrows():
        zd = (r.d3_declarada > CORTE_CREDITO) and (r.d3_precio > CORTE_PRECIO)
        za = (r.d3_ajustada > CORTE_CREDITO) and (r.d3_precio > CORTE_PRECIO)
        print(f"{r.trimestre:<10}{r.declarada_pib:>10.2f}{r.ajustada_pib:>10.2f}"
              f"{r.d3_declarada:>9.2f}{r.d3_ajustada:>9.2f}{r.d3_precio:>11.1f}"
              f"   {'SI' if zd else 'no'}/{'SI' if za else 'no'}")

    u = g.dropna(subset=["d3_declarada"]).iloc[-1]
    print(f"\nULTIMO TRIMESTRE ({u.trimestre}), {int(u.n)} empresas")
    print(f"  deuda declarada            {u.declarada/1e6:>8.2f} billones, "
          f"{u.declarada_pib:>5.2f}% del PIB")
    print(f"  mas lo firmado no iniciado {u.ajustada/1e6:>8.2f} billones, "
          f"{u.ajustada_pib:>5.2f}% del PIB")
    print(f"\n  cambio en 3 anos, en puntos de PIB:")
    print(f"    con credito declarado   {u.d3_declarada:>6.2f}  "
          f"({100*u.d3_declarada/CORTE_CREDITO:.0f}% del umbral de un pais entero)")
    print(f"    con credito ajustado    {u.d3_ajustada:>6.2f}  "
          f"({100*u.d3_ajustada/CORTE_CREDITO:.0f}% del umbral)")
    print(f"    factor entre las dos    {u.d3_ajustada/max(u.d3_declarada,1e-9):>6.2f}x")
    print(f"\n  La lectura honesta: estas {int(u.n)} empresas, por si solas,")
    print(f"  aportan ese numero de puntos de PIB frente a un umbral de "
          f"{CORTE_CREDITO} que")
    print("  en el articulo corresponde a TODO el credito empresarial de un pais.")

    g.to_csv("zona_roja_v3_series.csv", index=False)
    print("\nescrito zona_roja_v3_series.csv")
    print("\nAVISO: el indice de precios es nominal e igualmente ponderado. El")
    print("articulo usa el indice bursatil REAL del pais. Deflactar por IPC y")
    print("ponderar por capitalizacion antes de dar la cifra por buena.")


if __name__ == "__main__":
    main()
