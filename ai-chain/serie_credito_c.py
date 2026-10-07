#!/usr/bin/env python3
"""
serie_credito_c.py

Igual que serie_credito_b.py, con dos arreglos.

ARREGLO 1, EL RELLENO POR TRIMESTRE. La version b elegia, para cada componente,
la etiqueta de MAYOR COBERTURA y usaba solo esa. Eso rompe en las empresas que
cambian de etiqueta con los anos: Alphabet declaraba su deuda larga bajo
LongTermDebtAndCapitalLeaseObligations y dejo de hacerlo, asi que esa etiqueta
cubre muchos trimestres antiguos y ninguno reciente, y la deuda de 2026 salia
en 1.999 millones. Ahora cada trimestre se rellena con la PRIMERA etiqueta
candidata que informe ESE trimestre, en orden de preferencia, y el programa
imprime cuantos trimestres ha puesto cada etiqueta.

ARREGLO 2, LOS PRECIOS. stooq no devolvio nada. Los precios de la serie del
6-oct si son correctos (Amazon a 18,60 en el primer trimestre de 2015 es el
cierre ajustado por el desdoblamiento) y estan en el CSV viejo, CoreWeave
incluido. El problema de aquella serie era la deuda, no el precio, asi que los
precios se toman de alli en vez de volver a bajarlos.

DEFINICION DE DEUDA (sin cambios respecto a la version b)
  deuda declarada = deuda financiera a largo plazo no corriente
                  + porcion corriente de la deuda a largo plazo
                  + deuda a corto plazo y papel comercial
  Sin arrendamientos: van por el otro canal y sumarlos aqui los contaria dos
  veces. Sin avales: no son deuda hasta que se ejecutan.

USO:
  python3 serie_credito_c.py --precios zona_roja_series.csv \\
                             --salida zona_roja_series_c.csv
"""
import argparse
import json
import time
import urllib.request

import pandas as pd

AGENTE = {"User-Agent": "Alberto Acedo acedo@biomemakers.com"}
EMPRESAS = ["MSFT", "META", "GOOGL", "AMZN", "CRWV"]

# en orden de preferencia: la primera que informe un trimestre, lo pone
LARGO_NO_CORRIENTE = [
    "LongTermDebtNoncurrent",
    "LongTermDebtAndCapitalLeaseObligations",
    "SeniorNotesNoncurrent",
    "ConvertibleDebtNoncurrent",
    "LongTermNotesPayable",
]
LARGO_CORRIENTE = [
    "LongTermDebtCurrent",
    "LongTermDebtAndCapitalLeaseObligationsCurrent",
    "SeniorNotesCurrent",
    "ConvertibleDebtCurrent",
]
CORTO = [
    "CommercialPaper",
    "ShortTermBorrowings",
    "OtherShortTermBorrowings",
    "NotesPayableCurrent",
]
COMPONENTES = [("largo_no_corriente", LARGO_NO_CORRIENTE),
               ("largo_corriente", LARGO_CORRIENTE),
               ("corto_plazo", CORTO)]


def baja(url, reintentos=3):
    for i in range(reintentos):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=AGENTE), timeout=90).read()
        except Exception:
            if i == reintentos - 1:
                raise
            time.sleep(2)


def cik_por_ticker():
    d = json.loads(baja("https://www.sec.gov/files/company_tickers.json"))
    return {v["ticker"].upper(): f"{v['cik_str']:010d}" for v in d.values()}


def instantaneos(facts, etiqueta):
    for tax in ("us-gaap", "ifrs-full"):
        info = facts.get("facts", {}).get(tax, {}).get(etiqueta)
        if not info:
            continue
        filas = [{"fin": u["end"], "musd": u["val"] / 1e6, "filed": u.get("filed", "")}
                 for u in info.get("units", {}).get("USD", [])
                 if not u.get("start") and u.get("form") in ("10-K", "10-Q")]
        if not filas:
            continue
        f = pd.DataFrame(filas)
        f["fin"] = pd.to_datetime(f["fin"])
        f = f.sort_values("filed").groupby("fin", as_index=False).last()
        f["trimestre"] = f["fin"].dt.to_period("Q").astype(str)
        f = f.sort_values("fin").groupby("trimestre", as_index=False).last()
        return f[["trimestre", "musd"]]
    return pd.DataFrame(columns=["trimestre", "musd"])


def componente_rellenado(facts, candidatas):
    """Cada trimestre lo pone la primera candidata que lo informe."""
    valor, origen = {}, {}
    for e in candidatas:
        s = instantaneos(facts, e)
        for _, r in s.iterrows():
            if r["trimestre"] not in valor:
                valor[r["trimestre"]] = r["musd"]
                origen[r["trimestre"]] = e
    if not valor:
        return pd.DataFrame(columns=["trimestre", "musd"]), {}
    df = pd.DataFrame({"trimestre": list(valor), "musd": list(valor.values())})
    cuenta = {}
    for e in origen.values():
        cuenta[e] = cuenta.get(e, 0) + 1
    return df.sort_values("trimestre"), cuenta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--precios", default="zona_roja_series.csv")
    ap.add_argument("--salida", default="zona_roja_series_c.csv")
    a = ap.parse_args()

    precios = pd.read_csv(a.precios)[["empresa", "trimestre", "precio"]]

    ciks = cik_por_ticker()
    trozos, usadas = [], []

    for emp in EMPRESAS:
        if emp not in ciks:
            print(f"{emp}: sin CIK")
            continue
        facts = json.loads(baja(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{ciks[emp]}.json"))
        total, partes = None, []
        for nombre, candidatas in COMPONENTES:
            s, cuenta = componente_rellenado(facts, candidatas)
            if not cuenta:
                usadas.append((emp, nombre, "(no declara)", 0))
            for e, n in sorted(cuenta.items(), key=lambda x: -x[1]):
                usadas.append((emp, nombre, e, n))
            if s.empty:
                continue
            s = s.rename(columns={"musd": nombre})
            total = s if total is None else total.merge(s, on="trimestre", how="outer")
            partes.append(nombre)
        if total is None:
            continue
        total["deuda_declarada"] = total[partes].fillna(0.0).sum(axis=1)
        s = total[["trimestre", "deuda_declarada"] + partes]
        s.insert(0, "empresa", emp)
        s = s.merge(precios, on=["empresa", "trimestre"], how="left")
        trozos.append(s)

    print("ETIQUETAS USADAS, Y CUANTOS TRIMESTRES PONE CADA UNA")
    print(f"{'empresa':<8}{'componente':<22}{'etiqueta':<48}{'trim':>5}")
    for emp, nombre, tag, n in usadas:
        print(f"{emp:<8}{nombre:<22}{tag:<48}{n:>5}")

    out = pd.concat(trozos, ignore_index=True).sort_values(["empresa", "trimestre"])
    out["fuera_balance"] = 0.0
    out["deuda_ajustada"] = out["deuda_declarada"]
    out.to_csv(a.salida, index=False)

    print(f"\nSERIE -> {a.salida}  ({len(out)} filas)")
    print(f"{'empresa':<8}{'trim':>6}{'desde':>9}{'hasta':>9}"
          f"{'deuda final':>14}{'precio final':>14}{'sin precio':>11}")
    for emp, g in out.groupby("empresa"):
        g = g.sort_values("trimestre")
        u = g.iloc[-1]
        pr = f"{u['precio']:,.2f}" if pd.notna(u["precio"]) else "falta"
        print(f"{emp:<8}{len(g):>6}{g.trimestre.min():>9}{g.trimestre.max():>9}"
              f"{u['deuda_declarada']:>14,.0f}{pr:>14}{g.precio.isna().sum():>11}")

    print("\nultimos 4 trimestres, por si algun componente se queda en blanco:")
    for emp, g in out.groupby("empresa"):
        g = g.sort_values("trimestre").tail(4)
        print(f"\n  {emp}")
        cols = [c for c in ("largo_no_corriente", "largo_corriente", "corto_plazo")
                if c in g.columns]
        for _, r in g.iterrows():
            trozo = "  ".join(f"{c[:9]}={r[c]:,.0f}" if pd.notna(r[c]) else f"{c[:9]}=."
                              for c in cols)
            print(f"    {r['trimestre']}  total={r['deuda_declarada']:>10,.0f}   {trozo}")


if __name__ == "__main__":
    main()
