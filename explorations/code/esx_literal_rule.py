"""Their published rule, applied literally, against the TSI with a matched basket.

This is the comparison on THEIR terms. The rule is exactly the one in
arXiv:2512.10606 with the thresholds they publish for ESX (tau_G = 0.75,
tau_L = 0.25): hold the assets whose local balance departs from the global
balance by at least tau_L, in windows where the global balance is at least
tau_G, and hold 1/N otherwise. The TSI arm holds, in each window, the SAME
NUMBER of assets their rule selected there, chosen by smallest normalised
diag(A^3). So neither arm can win by concentrating more or trading more often.
The inverted TSI arm is the direction control.

Scored their way: in sample on the last five days of the estimation window,
which is the panel they publish for ESX, and out of sample on the five days
after it, which for ESX they do not publish. A permutation p-value against
random baskets of the same size is added, since their protocol has none.
"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0,"code"); sys.path.insert(0,"code/validation")
from esx_replication import load, build, FWD, TAU_G, TAU_L
rng=np.random.default_rng(0); NP=2000
ret=load(); R,n=build(ret)
fire=(R.kappa>=TAU_G).values
sizes=np.array([int((g>=TAU_L).sum()) for g in R.gap])
print(f"N={n}, {len(R)} ventanas. Su regla literal: dispara {fire.mean():.1%}, "
      f"selecciona >0 activos en {(fire&(sizes>0)).mean():.1%} de las ventanas, "
      f"cesta media cuando selecciona {sizes[sizes>0].mean():.1f}")

def run(name, pick_of, hz):
    port,bench,sel,ben,perm=[],[],[],[],[]
    for j,(_,row) in enumerate(R.iterrows()):
        f=row[hz]; m=sizes[j] if fire[j] else 0
        if m==0:
            port.append(f.mean())
        else:
            p=pick_of(row,m); port.append(f[p].mean())
            sel.append(f[p].mean()); ben.append(f.mean())
            perm.append([f[rng.choice(n,m,replace=False)].mean() for _ in range(NP)])
        bench.append(f.mean())
    port,bench,sel,ben,perm=map(np.array,(port,bench,sel,ben,perm))
    obs=sel.mean()-ben.mean(); p=float(np.mean(perm.mean(axis=0)-ben.mean()>=obs))
    sr=port.mean()/port.std()*np.sqrt(252/FWD); srb=bench.mean()/bench.std()*np.sqrt(252/FWD)
    print(f"  {name:<28}{np.exp(port.sum()):>9.2f}{np.exp(bench.sum()):>9.2f}"
          f"{obs*100:>+10.3f}{p:>9.3f}{sr:>8.2f}{srb:>8.2f}")

for hz,lab in [('ins','DENTRO DE MUESTRA (ultimos 5 dias de la ventana) = lo que ELLOS publican para ESX'),
               ('oos','FUERA DE MUESTRA (5 dias siguientes) = lo que NO publican para ESX')]:
    print(f"\n{lab}")
    print(f"  {'regla':<28}{'valor':>9}{'1/N':>9}{'cesta-1/N':>10}{'p':>9}{'SR':>8}{'SR 1/N':>8}")
    run("balance, umbrales suyos", lambda r,m: np.argsort(-r['gap'])[:m], hz)
    run("TSI, misma cesta/ventana", lambda r,m: np.argsort(r['tri'])[:m], hz)
    run("TSI invertido (control)", lambda r,m: np.argsort(-r['tri'])[:m], hz)
