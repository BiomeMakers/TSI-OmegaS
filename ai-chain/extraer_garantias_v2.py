"""Extractor v2.1: garantias, respaldos y compromisos fuera de balance en informes a la SEC.

Cambios respecto a la v1:
  - mas terminos (respaldos, financiacion a proveedores, compromisos incondicionales, toma o pago,
    acuerdos de suministro, empresas conjuntas no consolidadas, y "guarantee" a secas)
  - guarda TODOS los importes de la frase, no solo el primero
  - guarda la frase anterior y la siguiente, para poder verificar sin abrir el informe
  - clasifica cada frase en un concepto y descarta las aristas que apuntan a la propia empresa

Uso:
  python3 extraer_garantias_v2.py --email tu.correo@dominio.com
  python3 extraer_garantias_v2.py --email ... --desde 2024-01-01 --empresas NVDA,AVGO

Salidas: garantias_v2_frases.csv, garantias_v2_aristas.csv
"""
import argparse, csv, json, re, sys, time
import urllib.request, urllib.parse, urllib.error

EMPRESAS = {
    "META": 1326801, "GOOGL": 1652044, "MSFT": 789019, "AMZN": 1018724,
    "ORCL": 1341439, "NVDA": 1045810, "AVGO": 1730168, "CRWV": 1769628,
    "EQIX": 1101239, "DLR": 1297996, "OWL": 1823945, "ETN": 1551182, "VRT": 1674101,
}
TERMINOS = [
    "residual value guarantee", "residual value support",
    "backstop", "financial guarantee", "credit derivative",
    "vendor financing", "customer financing", "supplier financing",
    "off-balance sheet", "special purpose vehicle", "special purpose entity",
    "unconsolidated variable interest entit", "unconsolidated joint venture",
    "maximum exposure to loss", "maximum loss exposure",
    "leases that have not yet commenced", "not yet commenced",
    "unconditional purchase obligation", "take or pay", "supply agreement",
]
CONCEPTO = [
    ("garantia de valor residual", ["residual value guarantee", "residual value support"]),
    ("respaldo o garantia financiera", ["backstop", "financial guarantee", "credit derivative"]),
    ("financiacion a clientes o proveedores", ["vendor financing", "customer financing", "supplier financing"]),
    ("arrendamientos firmados no iniciados", ["not yet commenced"]),
    ("vehiculo o entidad no consolidada", ["special purpose", "variable interest entit",
                                           "unconsolidated joint venture", "maximum exposure to loss",
                                           "maximum loss exposure", "off-balance sheet"]),
    ("compromiso de compra o suministro", ["unconditional purchase obligation", "take or pay", "supply agreement"]),
]
CONTRAPARTES = ["Blue Owl", "Anthropic", "OpenAI", "SB Energy", "SoftBank", "Pimco", "BlackRock",
                "Apollo", "Beignet", "Stargate", "CoreWeave", "Oracle", "Broadcom", "Nvidia",
                "Google", "Alphabet", "Microsoft", "Meta", "Amazon", "xAI", "Equinix",
                "Digital Realty", "Vantage", "Crusoe", "TeraWulf", "Nebius", "Lambda", "Applied Digital"]
ALIAS = {"META": ["Meta"], "GOOGL": ["Google", "Alphabet"], "MSFT": ["Microsoft"], "AMZN": ["Amazon"],
         "ORCL": ["Oracle"], "NVDA": ["Nvidia", "NVIDIA"], "AVGO": ["Broadcom"], "CRWV": ["CoreWeave"],
         "EQIX": ["Equinix"], "DLR": ["Digital Realty"], "OWL": ["Blue Owl"]}
IMPORTE = re.compile(r"\$\s?([\d,]+(?:\.\d+)?)\s*(billion|million|trillion|bn|mn)?", re.I)


def pide(url, email, intentos=3, silencioso=False):
    req = urllib.request.Request(url, headers={
        "User-Agent": f"Biome Makers research {email}", "Accept-Encoding": "gzip, deflate"})
    for i in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                datos = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    datos = gzip.decompress(datos)
                return datos.decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            if e.code in (400, 500):        # el buscador rechaza ese termino: no insistir
                if not silencioso:
                    print(f"  el buscador rechaza la consulta ({e.code})", file=sys.stderr)
                return ""
            if i == intentos - 1:
                if not silencioso:
                    print(f"  fallo: {e}", file=sys.stderr)
                return ""
            time.sleep(2 + 2 * i)
        except Exception as e:
            if i == intentos - 1:
                if not silencioso:
                    print(f"  fallo: {e}", file=sys.stderr)
                return ""
            time.sleep(2 + 2 * i)
    return ""


def busca(termino, cik, desde, hasta, email):
    def consulta(q):
        url = (f"https://efts.sec.gov/LATEST/search-index?q={q}&forms=10-K,10-Q,8-K"
               f"&dateRange=custom&startdt={desde}&enddt={hasta}&ciks={cik:010d}")
        return pide(url, email, silencioso=True)
    txt = consulta(urllib.parse.quote(f'"{termino}"'))
    if not txt:                                  # reintento sin comillas
        txt = consulta(urllib.parse.quote(termino))
    if not txt:
        print(f"  termino sin resultados o rechazado: {termino}", file=sys.stderr)
    try:
        d = json.loads(txt) if txt else {}
    except json.JSONDecodeError:
        return []
    out = []
    for h in d.get("hits", {}).get("hits", []):
        f = h.get("_source", {})
        acc, _, doc = h.get("_id", "").partition(":")
        out.append({"formulario": f.get("file_type") or f.get("root_form", ""),
                    "fecha": f.get("file_date", ""),
                    "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{doc}"})
    return out


def texto(html):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    for a, b in [("&nbsp;", " "), ("&amp;", "&"), ("&#8217;", "'"), ("&#8212;", "-")]:
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


def importes(frase):
    vals = []
    for m in IMPORTE.finditer(frase):
        v = float(m.group(1).replace(",", "")); u = (m.group(2) or "").lower()
        if u.startswith("b"): v *= 1000
        elif u.startswith("t"): v *= 1_000_000
        vals.append(round(v, 1))
    return vals


def concepto(t):
    for nombre, claves in CONCEPTO:
        if any(k in t for k in claves):
            return nombre
    return "otro"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True)
    ap.add_argument("--desde", default="2024-01-01")
    ap.add_argument("--hasta", default=time.strftime("%Y-%m-%d"))
    ap.add_argument("--empresas", default=",".join(EMPRESAS))
    a = ap.parse_args()

    filas, vistos = [], set()
    for tk in [x.strip().upper() for x in a.empresas.split(",")]:
        cik = EMPRESAS.get(tk)
        if not cik:
            print(f"{tk}: sin CIK"); continue
        informes = {}
        for term in TERMINOS:
            for inf in busca(term, cik, a.desde, a.hasta, a.email):
                informes[inf["url"]] = inf
            time.sleep(0.15)
        print(f"{tk}: {len(informes)} informes", flush=True)
        for url, inf in informes.items():
            if (tk, url) in vistos:
                continue
            vistos.add((tk, url))
            t = texto(pide(url, a.email)); time.sleep(0.2)
            fr = re.split(r"(?<=\.)\s+", t)
            bajo = [s.lower() for s in fr]
            for i, s in enumerate(fr):
                if not any(term in bajo[i] for term in TERMINOS):
                    continue
                vals = importes(s)
                filas.append({
                    "empresa": tk, "formulario": inf["formulario"], "fecha": inf["fecha"],
                    "concepto": concepto(bajo[i]),
                    "importes_musd": ";".join(str(v) for v in vals),
                    "mayor_musd": max(vals) if vals else "",
                    "frase": s[:900],
                    "anterior": fr[i - 1][-250:] if i else "",
                    "siguiente": fr[i + 1][:250] if i + 1 < len(fr) else "",
                    "url": url})
    if not filas:
        print("sin resultados"); return
    with open("garantias_v2_frases.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0])); w.writeheader(); w.writerows(filas)

    with open("garantias_v2_aristas.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["garante", "contraparte", "concepto", "fecha", "mayor_musd", "frase", "url"])
        for r in filas:
            propios = [x.lower() for x in ALIAS.get(r["empresa"], [])]
            for c in CONTRAPARTES:
                if c.lower() in propios:
                    continue
                if re.search(r"\b" + re.escape(c) + r"\b", r["frase"], re.I):
                    w.writerow([r["empresa"], c, r["concepto"], r["fecha"], r["mayor_musd"],
                                r["frase"][:400], r["url"]])
    print(f"\n{len(filas)} frases. Devuelve los dos CSV.")


if __name__ == "__main__":
    main()
