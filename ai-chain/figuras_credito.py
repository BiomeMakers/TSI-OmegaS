#!/usr/bin/env python3
"""
figuras_credito.py

Rehace las figuras con la serie reconstruida. Las del 6-oct (niveles_credito,
curvas_credito) quedan invalidadas: estaban calculadas sobre una serie de deuda
que incluia pasivos por arrendamiento, es decir que contaba los arrendamientos
dos veces.

TRES FIGURAS
  1. credito_nivel    el credito de la cadena como % del PIB, declarado y
                      comprometido, 2015 en adelante. La figura es la brecha.
  2. credito_var3     variacion a tres anos en pp, con el umbral de 8,99 del
                      articulo dibujado para dar escala, no para decir que se
                      alcanza.
  3. ratio_empresa    lo firmado sin comenzar sobre la deuda financiera
                      declarada, por empresa, ultimos tres anos.

USO:
  python3 figuras_credito.py --agregado zona_roja_v5_series.csv \\
                             --empresas zona_roja_v4_series.csv
"""
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

UMBRAL = 8.99
GRIS = "#6b6b6b"
AZUL = "#1f4e79"
ROJO = "#a63a2b"


def eje_trimestres(ax, trimestres, cada=4):
    pos = range(len(trimestres))
    ax.set_xticks([p for p in pos if p % cada == 0])
    ax.set_xticklabels([trimestres[p] for p in pos if p % cada == 0],
                       rotation=45, ha="right", fontsize=8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agregado", default="zona_roja_v5_series.csv")
    ap.add_argument("--empresas", default="zona_roja_v4_series.csv")
    ap.add_argument("--desde", default="2015Q1")
    a = ap.parse_args()

    g = pd.read_csv(a.agregado).sort_values("trimestre")
    g = g[g.trimestre >= a.desde].reset_index(drop=True)
    t = list(g.trimestre)
    x = np.arange(len(t))

    # ---------- figura 1: niveles ----------
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.fill_between(x, g.pct_pib_deuda_declarada, g.pct_pib_deuda_ajustada,
                    color=ROJO, alpha=0.13, label="fuera del balance")
    ax.plot(x, g.pct_pib_deuda_ajustada, color=ROJO, lw=2,
            label="credito comprometido")
    ax.plot(x, g.pct_pib_deuda_declarada, color=AZUL, lw=2,
            label="credito declarado en balance")
    u = g.iloc[-1]
    ax.annotate(f"{u.pct_pib_deuda_ajustada:.2f}%", (x[-1], u.pct_pib_deuda_ajustada),
                xytext=(6, 0), textcoords="offset points", color=ROJO,
                fontsize=9, va="center")
    ax.annotate(f"{u.pct_pib_deuda_declarada:.2f}%", (x[-1], u.pct_pib_deuda_declarada),
                xytext=(6, 0), textcoords="offset points", color=AZUL,
                fontsize=9, va="center")
    ax.set_ylabel("% del PIB de EE.UU.")
    ax.set_title("El credito de la cadena de la IA: lo que el balance enseña\n"
                 "y lo que esta comprometido", fontsize=11, loc="left")
    eje_trimestres(ax, t)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.margins(x=0.02)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(f"credito_nivel.{ext}", dpi=200)
    plt.close(fig)

    # ---------- figura 2: variacion a tres anos ----------
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.axhline(UMBRAL, color=GRIS, ls="--", lw=1)
    ax.text(0, UMBRAL, f" umbral del articulo, {UMBRAL} pp",
            va="bottom", fontsize=8, color=GRIS)
    ax.plot(x, g.d3_deuda_ajustada, color=ROJO, lw=2, label="comprometido")
    ax.plot(x, g.d3_deuda_declarada, color=AZUL, lw=2, label="declarado")
    ax.set_ylabel("variacion en 3 años, pp de PIB")
    ax.set_ylim(bottom=0)
    ax.set_title("Variacion del credito a tres años\n"
                 "El umbral da escala: cinco empresas no son el credito "
                 "empresarial de un pais", fontsize=11, loc="left")
    eje_trimestres(ax, t)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.margins(x=0.02)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(f"credito_var3.{ext}", dpi=200)
    plt.close(fig)

    # ---------- figura 3: ratio por empresa ----------
    d = pd.read_csv(a.empresas)
    d = d[(d.fuera_balance > 0) & (d.deuda_declarada > 0)].copy()
    d["ratio"] = d.fuera_balance / d.deuda_declarada
    d = d[d.trimestre >= "2023Q3"]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    orden = (d.groupby("empresa").ratio.last().sort_values(ascending=False).index)
    colores = plt.cm.tab10(np.linspace(0, 1, 10))
    for i, e in enumerate(orden):
        s = d[d.empresa == e].sort_values("trimestre")
        ax.plot(range(len(s)), s.ratio.values, lw=2, color=colores[i], label=e,
                marker="o", ms=3)
        ax.annotate(f"{s.ratio.iloc[-1]:.1f}x", (len(s) - 1, s.ratio.iloc[-1]),
                    xytext=(6, 0), textcoords="offset points",
                    color=colores[i], fontsize=9, va="center")
    ax.axhline(1.0, color=GRIS, ls=":", lw=1)
    ax.text(0, 1.0, " paridad: tanto firmado como declarado",
            va="bottom", fontsize=8, color=GRIS)
    ax.set_ylabel("firmado sin comenzar / deuda declarada")
    ax.set_xlabel("trimestres desde 2023Q3")
    ax.set_title("Cuanto compromiso hay por cada dolar de deuda reconocida",
                 fontsize=11, loc="left")
    ax.legend(frameon=False, fontsize=9, ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.margins(x=0.06)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(f"ratio_empresa.{ext}", dpi=200)
    plt.close(fig)

    print("credito_nivel.png/pdf")
    print("credito_var3.png/pdf")
    print("ratio_empresa.png/pdf")
    print(f"\nultimo trimestre del agregado: {u.trimestre}")
    print(f"  declarado {u.pct_pib_deuda_declarada:.2f}%  "
          f"ajustado {u.pct_pib_deuda_ajustada:.2f}%  "
          f"factor {u.pct_pib_deuda_ajustada / u.pct_pib_deuda_declarada:.2f}")


if __name__ == "__main__":
    main()
