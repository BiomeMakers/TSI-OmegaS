import csv, urllib.request, time, os
os.makedirs('informes', exist_ok=True)
vistos = set()
EMP = ('NVDA','AVGO','ORCL','EQIX','DLR','VRT','ETN','CRWV','OWL')
for r in csv.DictReader(open('garantias_v2_frases.csv')):
    if r['empresa'] not in EMP: continue
    if r['formulario'] not in ('10-K','10-Q'): continue
    u = r['url'].split('#')[0]
    k = (r['empresa'], u)
    if k in vistos: continue
    vistos.add(k)
    n = 'informes/' + r['empresa'] + '_' + r['fecha'] + '_' + os.path.basename(u)
    if os.path.exists(n): continue
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Alberto Acedo acedo@biomemakers.com'})
        open(n, 'wb').write(urllib.request.urlopen(req, timeout=90).read())
        print(n)
    except Exception as e:
        print('FALLO', u, e)
    time.sleep(0.3)
print(len(vistos), 'informes')
