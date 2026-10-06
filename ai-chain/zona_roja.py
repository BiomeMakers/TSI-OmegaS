#!/usr/bin/env python3
"""
zona_roja.py

Sitúa cada empresa de la cadena de la IA en el indicador de Greenwood, Hanson,
Shleifer y Sørensen (Journal of Finance 77(2), 2022), y lo hace DOS VECES: con
la deuda que declaran en balance, y con la deuda ajustada por lo que mantienen
fuera de él.

POR QUÉ. Su indicador se enciende cuando el crecimiento del crédito y el de los
precios de los activos están elevados a la vez durante tres años, y eso lleva la
probabilidad de crisis del 7% al 40% a tres años vista. La entrada de crédito
que usan es la declarada. Van Nieuwerburgh (BPEA, otoño 2026) señala que en esta
cadena el apalancamiento declarado subestima la exposición real porque ha
migrado a garantías, vehículos y arrendamientos comprometidos. Si el indicador
cruza su umbral solo al sumar esa parte, el instrumento está mirando la mitad
del crédito justo donde más crédito hay fuera de balance.

NO SE AJUSTA NADA. Los umbrales son los de su artículo: quintil superior de
crecimiento del crédito y tercil superior de revalorización. No se tocan.

QUÉ NO ES. No es un predictor nuevo y no se valida como tal: su calibración
viene de 42 países y 66 años, y aquí hay una cadena, diez años y ninguna crisis.
Lo único que se mide es dónde cae esta cadena en un instrumento ya calibrado,
con una entrada bien medida y con otra mal medida.

USO (en tu Mac, porque la SEC no es accesible desde el contenedor):

  1) Rehacer la extracción con más historia. El extractor ya existe:
       cd ai-chain
       python3 extraer_garantias_v2.py --email acedo@biomemakers.com --desde 2018-01-01
     Tarda, son 13 empresas por 21 términos. Deja garantias_v2_frases.csv nuevo.

  2) python3 -m pip install --user yfinance pandas numpy
  3) python3 zona_roja.py --email acedo@biomemakers.com --frases garantias_v2_frases.csv

SALIDAS: zona_roja_series.csv (la serie por empresa y trimestre, las dos
versiones) y zona_roja_resumen.txt (quién entra en la zona roja, con cuál).
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.request
from collections import defaultdict

import numpy as np
import pandas as pd

CIK = {
    "META": 1326801, "GOOGL": 1652044, "MSFT": 789019, "AMZN": 1018724,
    "ORCL": 1341439, "NVDA": 1045810, "AVGO": 1730168, "CRWV": 1769628,
    "EQIX": 1101239, "DLR": 1297996, "OWL": 1823945, "ETN": 1551182,
    "VRT": 1674101,
}

# Deuda en balance. Se suman las etiquetas que existan; XBRL no es uniforme
# entre empresas, así que se toma lo que cada una publique.
TAGS_DEUDA = [
    "LongTermDebtNoncurrent", "LongTermDebtCurrent", "LongTermDebt",
    "ShortTermBorrowings", "CommercialPaper",
    "FinanceLeaseLiabilityNoncurrent", "FinanceLeaseLiabilityCurrent",
    "OperatingLeaseLiabilityNoncurrent", "OperatingLeaseLiabilityCurrent",
]

# Conceptos del extractor que cuentan como crédito fuera de balance. Se dejan
# fuera "vehiculo o entidad no consolidada" y "respaldo o garantia financiera"
# porque sus frases rara vez traen un importe comparable entre trimestres.
CONCEPTOS_FUERA = [
    "garantia de valor residual",
    "arrendamientos firmados no iniciados",
    "compromiso de compra o suministro",
    "financiacion a clientes o proveedores",
]


def sec_json(url, email):
    req = urllib.request.Request(url, headers={"User-Agent": f"Alberto Acedo {email}"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def deuda_declarada(email):
    """Serie trimestral de deuda en balance, por empresa, desde XBRL."""
    out = []
    for tic, cik in CIK.items():
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
        try:
            f = sec_json(url, email)
        except Exception as e:
            print(f"  {tic}: sin datos ({e})", file=sys.stderr)
            continue
        gaap = f.get("facts", {}).get("us-gaap", {})
        por_fecha = defaultdict(float)
        visto = defaultdict(set)
        for tag in TAGS_DEUDA:
            if tag not in gaap:
                continue
            for u in gaap[tag].get("units", {}).get("USD", []):
                if "end" not in u or u.get("form") not in ("10-K", "10-Q"):
                    continue
                q = pd.Period(u["end"], freq="Q")
                # una etiqueta por trimestre: la presentación más reciente
                if tag in visto[q]:
                    continue
                visto[q].add(tag)
                por_fecha[q] += float(u["val"])
        for q, v in por_fecha.items():
            out.append({"empresa": tic, "trimestre": str(q), "deuda_declarada": v / 1e6})
        print(f"  {tic}: {len(por_fecha)} trimestres")
        time.sleep(0.15)   # la SEC pide no más de 10 peticiones por segundo
    return pd.DataFrame(out)


def fuera_de_balance(path_frases):
    """Serie trimestral de compromisos fuera de balance, del extractor."""
    rows = []
    for r in csv.DictReader(open(path_frases)):
        if r["formulario"] not in ("10-K", "10-Q"):
            continue
        if r["concepto"] not in CONCEPTOS_FUERA:
            continue
        if not r["mayor_musd"].strip():
            continue
        rows.append({
            "empresa": r["empresa"],
            "trimestre": str(pd.Period(r["fecha"], freq="Q")),
            "concepto": r["concepto"],
            "musd": float(r["mayor_musd"]),
            "url": r["url"],
        })
    d = pd.DataFrame(rows)
    if d.empty:
        return d
    # por empresa, trimestre y concepto se queda el MAYOR importe de la frase,
    # porque el mismo concepto aparece varias veces en el mismo informe
    d = d.sort_values("musd").groupby(
        ["empresa", "trimestre", "concepto"], as_index=False).last()
    return d


def precios(email):
    """Revalorización trimestral. Requiere yfinance."""
    import yfinance as yf
    p = yf.download(list(CIK), start="2015-01-01", progress=False, auto_adjust=True)
    cl = p["Close"] if isinstance(p.columns, pd.MultiIndex) else p
    q = cl.resample("QE").last()
    out = []
    for tic in cl.columns:
        s = q[tic].dropna()
        for idx, v in s.items():
            out.append({"empresa": tic, "trimestre": str(pd.Period(idx, freq="Q")),
                        "precio": float(v)})
    return pd.DataFrame(out)


def crecimiento_3a(df, col):
    """Crecimiento real a tres años, en términos relativos."""
    df = df.sort_values(["empresa", "trimestre"]).copy()
    df["g3"] = df.groupby("empresa")[col].transform(lambda s: s / s.shift(12) - 1.0)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True, help="la SEC exige una dirección de contacto")
    ap.add_argument("--frases", default="garantias_v2_frases.csv")
    a = ap.parse_args()

    print("1. deuda declarada, desde XBRL")
    dd = deuda_declarada(a.email)
    if dd.empty:
        sys.exit("sin deuda declarada, no se puede seguir")

    print("\n2. compromisos fuera de balance, del extractor")
    fb = fuera_de_balance(a.frases)
    if fb.empty:
        print("  AVISO: ninguna frase con importe en 10-K o 10-Q.")
        print("  Vuelve a correr extraer_garantias_v2.py con --desde más atrás.")
        fb_tot = pd.DataFrame(columns=["empresa", "trimestre", "fuera_balance"])
    else:
        fb_tot = fb.groupby(["empresa", "trimestre"], as_index=False)["musd"].sum()
        fb_tot = fb_tot.rename(columns={"musd": "fuera_balance"})
        print(f"  {len(fb)} partidas, {fb['empresa'].nunique()} empresas, "
              f"{fb['trimestre'].nunique()} trimestres")

    print("\n3. precios")
    pr = precios(a.email)

    d = dd.merge(fb_tot, on=["empresa", "trimestre"], how="left")
    d["fuera_balance"] = d["fuera_balance"].fillna(0.0)
    d["deuda_ajustada"] = d["deuda_declarada"] + d["fuera_balance"]
    d = d.merge(pr, on=["empresa", "trimestre"], how="inner")

    for col in ("deuda_declarada", "deuda_ajustada", "precio"):
        d = crecimiento_3a(d, col).rename(columns={"g3": f"g3_{col}"})

    # posición de cada crecimiento dentro de la historia de la propia empresa
    for col in ("g3_deuda_declarada", "g3_deuda_ajustada", "g3_precio"):
        d[f"pct_{col}"] = d.groupby("empresa")[col].rank(pct=True)

    # los umbrales son los del artículo y no se tocan
    QUINTIL, TERCIL = 0.80, 2.0 / 3.0
    d["zona_roja_declarada"] = (
        (d["pct_g3_deuda_declarada"] >= QUINTIL) & (d["pct_g3_precio"] >= TERCIL))
    d["zona_roja_ajustada"] = (
        (d["pct_g3_deuda_ajustada"] >= QUINTIL) & (d["pct_g3_precio"] >= TERCIL))

    d.to_csv("zona_roja_series.csv", index=False)

    ult = d.sort_values("trimestre").groupby("empresa").last()
    lineas = []
    lineas.append("ZONA ROJA DE GREENWOOD, HANSON, SHLEIFER Y SORENSEN")
    lineas.append("umbrales del articulo: credito en quintil superior (0.80),")
    lineas.append("revalorizacion en tercil superior (0.667). No se ajustan.\n")
    lineas.append(f"{'empresa':<9}{'trimestre':<10}{'decl':>7}{'ajust':>8}"
                  f"{'precio':>8}   zona")
    cambia = []
    for e, r in ult.iterrows():
        za = "SI" if r["zona_roja_ajustada"] else "no"
        zd = "SI" if r["zona_roja_declarada"] else "no"
        marca = ""
        if r["zona_roja_ajustada"] and not r["zona_roja_declarada"]:
            marca = "  <-- entra SOLO al ajustar"
            cambia.append(e)
        lineas.append(f"{e:<9}{r['trimestre']:<10}"
                      f"{r['pct_g3_deuda_declarada']:>7.2f}"
                      f"{r['pct_g3_deuda_ajustada']:>8.2f}"
                      f"{r['pct_g3_precio']:>8.2f}   {zd}/{za}{marca}")
    lineas.append("")
    if cambia:
        lineas.append(f"EL HALLAZGO, si aguanta la verificacion: {', '.join(cambia)}")
        lineas.append("cruzan el umbral solo cuando se suma lo que esta fuera de balance.")
        lineas.append("Antes de escribirlo, abrir el 10-K de cada una y comprobar el")
        lineas.append("importe en su fuente, como se hizo con cada cifra de la nota.")
    else:
        lineas.append("Ninguna empresa cambia de lado al ajustar. Eso tambien es un")
        lineas.append("resultado: en esta muestra, la parte fuera de balance no mueve")
        lineas.append("el indicador, y conviene decirlo tal cual.")
    txt = "\n".join(lineas)
    open("zona_roja_resumen.txt", "w").write(txt + "\n")
    print("\n" + txt)
    print("\nEscritos zona_roja_series.csv y zona_roja_resumen.txt")


if __name__ == "__main__":
    main()
