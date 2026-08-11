"""Spectral benchmarks: effective rank & Vendi vs Omega (Section 3.6b of the preprint).
Faithful replication of the paper pipeline (OFR FSI,
window=20, step=3, composite Omega + EMA memory, AR on the COVARIANCE with k=n/5,
F1@p90, ventanas de crisis originales, block bootstrap) + RIVALES ESPECTRALES."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, FIG  # noqa: E402
import numpy as np, pandas as pd
np.random.seed(42)
B = os.path.join(os.path.dirname(RAW("x")), "..") + os.sep
df=pd.read_csv(B+"raw/ofr_financial_stress_index.csv",parse_dates=['Date']).sort_values('Date').reset_index(drop=True)
nodes=['Credit','Equity valuation','Safe assets','Funding','Volatility','United States','Other advanced economies','Emerging markets']
n=len(nodes)
diffs=df[nodes].diff().dropna().reset_index(drop=True); dates=df['Date'].iloc[1:].reset_index(drop=True)
orig=pd.read_csv(B+"results/ofr_full_history_memory.csv",parse_dates=['date'])
origAR=pd.read_csv(B+"results/ofr_AR_full_history.csv",parse_dates=['date'])

def omega_c(A):
    A2=A@A; T=np.trace(A2@A); den=A2.sum()-np.trace(A2); C=T/den if den>0 else 0.
    deg=A.sum(1); D=A.sum()/(n*(n-1)); ev=np.sort(np.linalg.eigvalsh(np.diag(deg)-A))
    M=1./max(ev[1],1e-6); return (C*D/M)*np.var(deg)
def ar_cov(win,k): 
    ev=np.sort(np.linalg.eigvalsh(win.cov().values))[::-1]; return ev[:k].sum()/ev.sum()

win_len,step=20,3; k_ar=max(1,round(n/5))
rec=[]
for i in range(win_len,len(diffs),step):
    w=diffs.iloc[i-win_len:i]
    A=np.abs(w.corr().values); np.fill_diagonal(A,0.)
    Cm=np.nan_to_num(w.corr().values,nan=0.); ev=np.clip(np.linalg.eigvalsh(Cm),1e-9,None)
    p=ev/ev.sum(); erank=float(np.exp(-(p*np.log(p)).sum()))
    s=np.linalg.svd(w.values-w.values.mean(0),compute_uv=False); q=s/s.sum(); q=q[q>1e-12]
    rec.append(dict(date=dates.iloc[i-1],Omega=omega_c(A),AR=ar_cov(w,k_ar),
                    erank=erank,vendi=erank,erank_data=float(np.exp(-(q*np.log(q)).sum()))))
R=pd.DataFrame(rec)
m=R.merge(orig[['date','Omega']],on='date',suffixes=('','_o'))
print(f"REPLICA: n={len(R)} (orig {len(orig)}), solapan {len(m)}, corr Omega={np.corrcoef(m.Omega,m.Omega_o)[0,1]:.4f}")
mA=R.merge(origAR,on='date'); print(f"         corr AR={np.corrcoef(mA.AR,mA.AbsorptionRatio)[0,1]:.4f}")
# EMA calibrada
best=None
for a in np.arange(0.02,0.51,0.01):
    mm=pd.DataFrame({'date':R.date,'m':R.Omega.ewm(alpha=a,adjust=False).mean()}).merge(orig[['date','Omega_memory']],on='date')
    e=np.mean(np.abs(mm.m-mm.Omega_memory))
    if best is None or e<best[1]: best=(a,e)
R['Omega_memory']=R.Omega.ewm(alpha=best[0],adjust=False).mean()
print(f"         alpha EMA={best[0]:.2f}")

cw=[("2000-03-01","2002-10-01"),("2007-08-01","2009-06-01"),("2009-12-01","2010-05-01"),("2010-08-01","2010-10-15"),
("2011-06-01","2012-09-01"),("2013-06-01","2013-09-01"),("2014-02-15","2014-04-15"),("2015-06-15","2015-07-15"),
("2015-08-01","2015-11-10"),("2016-06-01","2016-09-01"),("2016-09-10","2016-10-10"),("2017-04-15","2017-05-30"),
("2017-08-01","2017-09-30"),("2017-10-01","2017-10-10"),("2018-01-15","2018-02-15"),("2018-03-15","2018-08-31"),
("2018-09-01","2018-12-31"),("2019-08-01","2019-09-30"),("2020-02-01","2020-07-31"),("2021-07-15","2021-09-30"),
("2022-01-01","2022-12-01"),("2023-03-01","2023-04-15"),("2024-07-15","2024-09-30")]
R['crisis']=R.date.apply(lambda x: any(pd.Timestamp(s)<=x<=pd.Timestamp(e) for s,e in cw)); cr=R.crisis.values
def f1(x,c,pct=.9):
    thr=np.quantile(x,pct); al=x>=thr
    tp=np.sum(al&c);fp=np.sum(al&~c);fn=np.sum(~al&c)
    p=tp/(tp+fp) if tp+fp else 0; r=tp/(tp+fn) if tp+fn else 0
    return 2*p*r/(p+r) if p+r else 0
sig={'Omega_memory':1,'Omega':1,'AR':1,'erank':-1,'vendi':-1,'erank_data':-1}
print("\n=== F1 @ p90 (the original metric) ===")
for c in ['Omega_memory','Omega','AR','erank','vendi','erank_data']:
    print(f"   {c:14s}: F1 {f1(sig[c]*R[c].values,cr):.4f}")
N=len(R); bl=60; nb=N//bl
def bd(cA,cB,Bn=2000):
    a=sig[cA]*R[cA].values; b=sig[cB]*R[cB].values; o=[]
    for _ in range(Bn):
        idx=[]
        for _ in range(nb+1):
            s=np.random.randint(0,N-bl); idx.extend(range(s,s+bl))
        idx=np.array(idx[:N]); o.append(f1(a[idx],cr[idx])-f1(b[idx],cr[idx]))
    o=np.array(o); return o.mean(),np.percentile(o,2.5),np.percentile(o,97.5),np.mean(o<=0)
print("\n=== Does Omega-with-memory beat each rival? (block bootstrap) ===")
for c in ['AR','erank','vendi','erank_data']:
    d,lo,hi,p=bd('Omega_memory',c)
    print(f"   vs {c:11s}: ΔF1 {d:+.4f}  IC95 [{lo:+.4f},{hi:+.4f}]  p={p:.4f}  → "
          f"{'GANA' if lo>0 else ('PIERDE' if hi<0 else 'EMPATA')}")
