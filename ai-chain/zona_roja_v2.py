#!/usr/bin/env python3
"""
zona_roja_v2.py

Recalcula la zona roja sustituyendo la parte fuera de balance por la serie
LEIDA DE LOS INFORMES, no raspada con un buscador de frases.

POR QUE HAY UNA v2. La v1 tomaba el importe de la frase donde aparecia, y en
los 10-Q esa frase va justo detras de la tabla de coste de arrendamiento, asi
que lo que entraba en la serie eran numeros de la tabla y no el dato. Ademas
Microsoft, Alphabet y Amazon lo expresan de tres formas distintas: dos de ellas
dan DOS importes que hay que sumar ("operating and finance ... respectively"),
y Amazon no usa frase sino una fila de tabla. Nada de eso se puede resolver sin
abrir los informes, y en XBRL la partida no existe: Microsoft publica 562
etiquetas y ninguna es esta.

USO:
  python3 zona_roja_v2.py --series zona_roja_series.csv \
                          --no-iniciados arrendamientos_no_iniciados.csv

Toma la deuda declarada y los precios de la corrida anterior, que venian de
XBRL y estaban bien, y solo cambia la columna de fuera de balance.
"""
import argparse
import pandas as pd

QUINTIL, TERCIL = 0.80, 2.0 / 3.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", default="zona_roja_series.csv")
    ap.add_argument("--no-iniciados", default="arrendamientos_no_iniciados.csv")
    a = ap.parse_args()

    d = pd.read_csv(a.series)
    n = pd.read_csv(a.no_iniciados)

    # el trimestre es el de la fecha A LA QUE se refiere el dato, no el de
    # presentacion: un 10-Q presentado en julio informa de junio
    n["a_fecha"] = pd.to_datetime(n["a_fecha"], errors="coerce")
    n = n.dropna(subset=["a_fecha"])
    n["trimestre"] = n["a_fecha"].dt.to_period("Q").astype(str)
    n = n.sort_values("musd").groupby(["empresa", "trimestre"], as_index=False).last()

    d = d.drop(columns=["fuera_balance", "deuda_ajustada"], errors="ignore")
    d = d.merge(n[["empresa", "trimestre", "musd"]], on=["empresa", "trimestre"],
                how="left").rename(columns={"musd": "fuera_balance"})
    d["fuera_balance"] = d["fuera_balance"].fillna(0.0)
    d["deuda_ajustada"] = d["deuda_declarada"] + d["fuera_balance"]

    d = d.sort_values(["empresa", "trimestre"])
    for col in ("deuda_declarada", "deuda_ajustada"):
        d[f"g3_{col}"] = d.groupby("empresa")[col].transform(lambda s: s / s.shift(12) - 1)
        d[f"pct_g3_{col}"] = d.groupby("empresa")[f"g3_{col}"].rank(pct=True)

    d["zona_roja_declarada"] = (
        (d["pct_g3_deuda_declarada"] >= QUINTIL) & (d["pct_g3_precio"] >= TERCIL))
    d["zona_roja_ajustada"] = (
        (d["pct_g3_deuda_ajustada"] >= QUINTIL) & (d["pct_g3_precio"] >= TERCIL))
    d.to_csv("zona_roja_v2_series.csv", index=False)

    print("ZONA ROJA, con la serie leida de los informes")
    print("umbrales del articulo, sin ajustar: credito 0.80, precio 0.667\n")
    print(f"{'empresa':<9}{'trimestre':<10}{'decl':>7}{'ajust':>8}{'precio':>8}"
          f"{'f.balance':>12}   zona")
    ult = d[d.fuera_balance > 0].sort_values("trimestre").groupby("empresa").last()
    cambia = []
    for e, r in ult.iterrows():
        zd = "SI" if r["zona_roja_declarada"] else "no"
        za = "SI" if r["zona_roja_ajustada"] else "no"
        marca = ""
        if r["zona_roja_ajustada"] and not r["zona_roja_declarada"]:
            marca = "  <-- solo al ajustar"; cambia.append(e)
        print(f"{e:<9}{r['trimestre']:<10}{r['pct_g3_deuda_declarada']:>7.2f}"
              f"{r['pct_g3_deuda_ajustada']:>8.2f}{r['pct_g3_precio']:>8.2f}"
              f"{r['fuera_balance']:>12,.0f}   {zd}/{za}{marca}")

    print("\nratio fuera de balance sobre deuda declarada, ultimos 6 trimestres:")
    for e in sorted(ult.index):
        s = d[(d.empresa == e) & (d.fuera_balance > 0)].tail(6)
        rr = (s.fuera_balance / s.deuda_declarada)
        print(f"  {e:<8}" + "  ".join(f"{x:.2f}" for x in rr))

    print()
    if cambia:
        print(f"Cruzan el umbral solo al ajustar: {', '.join(cambia)}")
    else:
        print("Ninguna cambia de lado. El ajuste mueve la pata de credito pero")
        print("no enciende el indicador; decirlo tal cual, con cuanto la mueve.")


if __name__ == "__main__":
    main()
