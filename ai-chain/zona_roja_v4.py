#!/usr/bin/env python3
"""
zona_roja_v4.py

Calculo del credito de la cadena de la IA, declarado y ajustado, sobre la serie
reconstruida con definicion escrita (serie_credito_c.py) y la extraccion de
arrendamientos verificada contra los informes (extraer_no_iniciados_b.py).

QUE CAMBIA RESPECTO A LA v2 Y POR QUE

1. Rejilla trimestral completa. La v2 calculaba el crecimiento a tres anos con
   shift(12), que cuenta doce FILAS, no doce trimestres. Con series que tienen
   huecos eso retrocede mucho mas de tres anos sin avisar: la serie de Meta
   tenia 26 trimestres con dato en una rejilla de 59. Aqui se construye la
   rejilla completa primero y el desplazamiento es sobre ella.

2. Recorte a 2015Q1. Antes de esa fecha faltan precios en todas las empresas
   (la serie de precios empieza mas tarde que la de deuda) y la deuda tiene
   huecos. De 2022 en adelante no falta nada, asi que la ventana que usa el
   indicador, doce trimestres hacia atras desde junio de 2026, esta completa.

3. Los huecos de deuda anteriores a 2023 se rellenan con CERO, no se
   interpolan. Son ceros reales: ni Meta ni Amazon tenian deuda financiera en
   esos trimestres. El programa dice cuantos rellena por empresa.

4. El resultado principal es el RATIO, no el percentil. El percentil de cada
   empresa se calcula sobre unas cuarenta observaciones de esa sola empresa,
   mientras que el 0,80 de Greenwood, Hanson, Shleifer y Sorensen esta
   calibrado sobre mas de un siglo de credito empresarial de paises enteros.
   No son la misma cantidad y compararlas directamente seria pasarse. El ratio
   entre lo firmado sin comenzar y la deuda financiera declarada no depende de
   ninguna calibracion historica, y es lo que sostiene el argumento.

USO:
  python3 zona_roja_v4.py --series zona_roja_series_d.csv \\
                          --no-iniciados no_iniciados_b.csv \\
                          --desde 2015Q1
"""
import argparse

import numpy as np
import pandas as pd

QUINTIL, TERCIL = 0.80, 2.0 / 3.0
TRIMESTRES = 12  # tres anos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", default="zona_roja_series_d.csv")
    ap.add_argument("--no-iniciados", default="no_iniciados_b.csv")
    ap.add_argument("--desde", default="2015Q1")
    ap.add_argument("--salida", default="zona_roja_v4_series.csv")
    a = ap.parse_args()

    d = pd.read_csv(a.series)
    n = pd.read_csv(a.no_iniciados)

    # el trimestre del dato es el del cierre al que se refiere, no el de
    # presentacion: un 10-Q presentado en julio informa de junio
    n["a_fecha"] = pd.to_datetime(n["a_fecha"], errors="coerce")
    n = n.dropna(subset=["a_fecha"])
    n["trimestre"] = n["a_fecha"].dt.to_period("Q").astype(str)
    n = n.sort_values("musd").groupby(["empresa", "trimestre"], as_index=False).last()

    d = d.drop(columns=["fuera_balance", "deuda_ajustada"], errors="ignore")
    d = d.merge(n[["empresa", "trimestre", "musd"]], on=["empresa", "trimestre"],
                how="left").rename(columns={"musd": "fuera_balance"})
    d["fuera_balance"] = d["fuera_balance"].fillna(0.0)

    # rejilla completa por empresa desde --desde
    desde = pd.Period(a.desde, freq="Q")
    d["p"] = pd.PeriodIndex(d.trimestre, freq="Q")
    trozos = []
    rellenos = {}
    for e, g in d.groupby("empresa"):
        g = g[g.p >= desde].set_index("p").sort_index()
        if g.empty:
            continue
        rej = pd.period_range(max(g.index.min(), desde), g.index.max(), freq="Q")
        g = g.reindex(rej)
        rellenos[e] = int(g["deuda_declarada"].isna().sum())
        g["deuda_declarada"] = g["deuda_declarada"].fillna(0.0)
        g["fuera_balance"] = g["fuera_balance"].fillna(0.0)
        g["empresa"] = e
        g["trimestre"] = g.index.astype(str)
        trozos.append(g.reset_index(drop=True))
    d = pd.concat(trozos, ignore_index=True)
    d["deuda_ajustada"] = d["deuda_declarada"] + d["fuera_balance"]

    print(f"Serie recortada desde {a.desde}, rejilla trimestral completa.")
    print("huecos de deuda rellenados con cero (son ceros reales, no datos perdidos):")
    for e in sorted(rellenos):
        print(f"  {e:<8}{rellenos[e]:>3}")

    # crecimientos sobre la rejilla, ahora shift(12) si son doce trimestres
    d = d.sort_values(["empresa", "trimestre"])
    for col in ("deuda_declarada", "deuda_ajustada"):
        d[f"g3_{col}"] = d.groupby("empresa")[col].transform(
            lambda s: s - s.shift(TRIMESTRES))        # en nivel, no en tasa:
        # una tasa con denominador casi cero se dispara sin significar nada
        d[f"pct_g3_{col}"] = d.groupby("empresa")[f"g3_{col}"].rank(pct=True)
    d["g3_precio"] = d.groupby("empresa")["precio"].transform(
        lambda s: np.log(s / s.shift(TRIMESTRES)))
    d["pct_g3_precio"] = d.groupby("empresa")["g3_precio"].rank(pct=True)

    d["zona_roja_declarada"] = (
        (d["pct_g3_deuda_declarada"] >= QUINTIL) & (d["pct_g3_precio"] >= TERCIL))
    d["zona_roja_ajustada"] = (
        (d["pct_g3_deuda_ajustada"] >= QUINTIL) & (d["pct_g3_precio"] >= TERCIL))
    d.to_csv(a.salida, index=False)

    ult = d[d.fuera_balance > 0].sort_values("trimestre").groupby("empresa").last()

    print("\n" + "=" * 68)
    print("RESULTADO PRINCIPAL: credito declarado frente a credito comprometido")
    print("=" * 68)
    print(f"\n{'empresa':<9}{'trimestre':<10}{'declarado':>13}{'sin comenzar':>15}"
          f"{'ajustado':>13}{'ratio':>8}")
    td = ta = tf = 0.0
    for e, r in ult.iterrows():
        td += r["deuda_declarada"]; tf += r["fuera_balance"]
        ta += r["deuda_ajustada"]
        print(f"{e:<9}{r['trimestre']:<10}{r['deuda_declarada']:>13,.0f}"
              f"{r['fuera_balance']:>15,.0f}{r['deuda_ajustada']:>13,.0f}"
              f"{r['fuera_balance'] / r['deuda_declarada']:>8.2f}")
    print(f"{'TOTAL':<19}{td:>13,.0f}{tf:>15,.0f}{ta:>13,.0f}{tf / td:>8.2f}")
    print(f"\nEl balance oficial enseña el {100 * td / ta:.0f}% del compromiso de credito.")

    print("\nratio por trimestre, ultimos 8 (lo firmado sin comenzar sobre la")
    print("deuda financiera declarada):")
    for e in sorted(ult.index):
        s = d[(d.empresa == e) & (d.fuera_balance > 0)].tail(8)
        rr = s.fuera_balance / s.deuda_declarada.replace(0, np.nan)
        print(f"  {e:<8}" + "  ".join("." if pd.isna(x) else f"{x:.2f}" for x in rr))

    print("\n" + "=" * 68)
    print("ILUSTRACION SECUNDARIA: las dos patas del indicador")
    print("=" * 68)
    print("\nEl percentil de cada empresa sale de unas cuarenta observaciones")
    print("suyas; el 0,80 del articulo esta calibrado sobre mas de un siglo de")
    print("credito empresarial de paises enteros. No se comparan de tu a tu.\n")
    print(f"{'empresa':<9}{'trim':<9}{'pct decl':>10}{'pct ajust':>11}"
          f"{'pct precio':>12}{'n precio':>10}   zona")
    for e, r in ult.iterrows():
        g = d[d.empresa == e]
        zd = "SI" if r["zona_roja_declarada"] else "no"
        za = "SI" if r["zona_roja_ajustada"] else "no"
        marca = "  <-- solo al ajustar" if (r["zona_roja_ajustada"]
                                            and not r["zona_roja_declarada"]) else ""
        def f(x):
            return "." if pd.isna(x) else f"{x:.2f}"
        print(f"{e:<9}{r['trimestre']:<9}{f(r['pct_g3_deuda_declarada']):>10}"
              f"{f(r['pct_g3_deuda_ajustada']):>11}{f(r['pct_g3_precio']):>12}"
              f"{g.g3_precio.notna().sum():>10}   {zd}/{za}{marca}")

    pocos = [e for e in ult.index
             if d[d.empresa == e].g3_precio.notna().sum() < 12]
    if pocos:
        print(f"\nCon menos de 12 crecimientos de precio calculables, el percentil")
        print(f"no es interpretable: {', '.join(pocos)}")


if __name__ == "__main__":
    main()
