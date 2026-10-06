#!/usr/bin/env python3
"""
comprobar_meta.py

El resultado dice que Meta entra en la zona roja solo al sumar lo que tiene
fuera de balance: percentil 0.58 con credito declarado, 0.95 con el ajustado.
Esto comprueba si ese 0.95 aguanta o si sale de un artefacto.

EL ARTEFACTO QUE SE BUSCA. En la serie ajustada, los trimestres anteriores a
que la empresa empezara a divulgar arrendamientos no iniciados llevan cero en
esa columna, asi que ahi deuda_ajustada es igual a deuda_declarada. El salto
del cero al primer valor real mete un crecimiento ficticio en la historia, y
eso desplaza todos los percentiles. Si se recorta la ventana a los trimestres
donde el dato existe de verdad, tanto en t como en t-12, el artefacto
desaparece y se ve lo que hay.

  python3 comprobar_meta.py --series zona_roja_v2_series.csv
"""
import argparse
import pandas as pd

QUINTIL, TERCIL = 0.80, 2.0 / 3.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", default="zona_roja_v2_series.csv")
    ap.add_argument("--empresas", default="META,MSFT,GOOGL,AMZN")
    a = ap.parse_args()
    d = pd.read_csv(a.series).sort_values(["empresa", "trimestre"])

    print("ventana completa frente a ventana con dato real\n")
    print(f"{'empresa':<9}{'n total':>9}{'n real':>8}"
          f"{'decl':>8}{'ajust':>8}{'decl*':>8}{'ajust*':>8}{'precio':>8}   zona*")

    for e in a.empresas.split(","):
        s = d[d.empresa == e].copy().reset_index(drop=True)
        if s.empty:
            continue
        # un trimestre cuenta como real si hay dato fuera de balance en t y en t-12
        s["real"] = (s["fuera_balance"] > 0) & (s["fuera_balance"].shift(12) > 0)
        r = s[s["real"]].copy()
        if len(r) < 6:
            print(f"{e:<9}{len(s):>9}{len(r):>8}   ventana demasiado corta "
                  f"({len(r)} trimestres), no se puede rehacer el percentil")
            continue
        # percentiles rehechos SOLO dentro de la ventana real
        for col in ("g3_deuda_declarada", "g3_deuda_ajustada", "g3_precio"):
            r[f"p_{col}"] = r[col].rank(pct=True)
        u = r.iloc[-1]
        zona = ((u["p_g3_deuda_ajustada"] >= QUINTIL) and (u["p_g3_precio"] >= TERCIL))
        zona_d = ((u["p_g3_deuda_declarada"] >= QUINTIL) and (u["p_g3_precio"] >= TERCIL))
        marca = "  <-- sigue entrando solo al ajustar" if zona and not zona_d else ""
        print(f"{e:<9}{len(s):>9}{len(r):>8}"
              f"{u['pct_g3_deuda_declarada']:>8.2f}{u['pct_g3_deuda_ajustada']:>8.2f}"
              f"{u['p_g3_deuda_declarada']:>8.2f}{u['p_g3_deuda_ajustada']:>8.2f}"
              f"{u['p_g3_precio']:>8.2f}   "
              f"{'SI' if zona_d else 'no'}/{'SI' if zona else 'no'}{marca}")

    print("\n  decl y ajust: percentiles de la corrida anterior, ventana completa")
    print("  decl* y ajust*: rehechos solo con los trimestres de dato real")
    print("\n  Si el ajustado se mantiene por encima de 0.80 en la columna con")
    print("  asterisco, el resultado no viene del relleno con ceros. Si cae, si.")

    print("\ncrecimiento a tres anos de la ultima fila, en bruto:")
    for e in a.empresas.split(","):
        s = d[d.empresa == e]
        if s.empty:
            continue
        u = s.iloc[-1]
        print(f"  {e:<8} declarado {u['g3_deuda_declarada']:+7.1%}   "
              f"ajustado {u['g3_deuda_ajustada']:+8.1%}   "
              f"precio {u['g3_precio']:+7.1%}")
    print("\n  Esto es lo que de verdad hay que contar: el crecimiento, no el")
    print("  percentil. El percentil depende de la historia disponible y el")
    print("  crecimiento no.")


if __name__ == "__main__":
    main()
