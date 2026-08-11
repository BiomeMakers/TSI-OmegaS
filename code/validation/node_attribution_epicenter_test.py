"""Node-attribution validation (Section 3.6c): does the culprit-asset rule
recover the true epicentre of a shock? Synthetic ground truth, incl. the
two-epicentre regime, benchmarked against eigenvector-loading attribution.
"""
import numpy as np
rng=np.random.default_rng(0)
def gen_multi(T=200,n=12,epiA=(0,1,2),epiB=(6,7,8),t0=100,seed=0):
    """Two simultaneous epicentres driven by DIFFERENT factors (a modular crisis)."""
    r=np.random.default_rng(seed); FA=r.normal(0,1,T); FB=r.normal(0,1,T)
    R=np.zeros((T,n))
    for t in range(T):
        for i in range(n):
            if t<t0: R[t,i]=r.normal(0,1)
            else:
                if i in epiA: b,F=0.90,FA[t]
                elif i in epiB: b,F=0.90,FB[t]
                else: b,F=0.25,FA[t]
                R[t,i]=b*F+np.sqrt(max(1e-3,1-b**2))*r.normal(0,1)
    return R
def attribs(win):
    C=np.corrcoef(win.T); A=np.abs(C); np.fill_diagonal(A,0)
    ev,V=np.linalg.eigh(C)
    return dict(degree=A.sum(1), triangles=np.diag(A@A@A), eigenvector=np.abs(V[:,-1]),
                eigenvec_top2=np.abs(V[:,-1])+np.abs(V[:,-2]))
def hit(s,epi,k=6): return len(set(np.argsort(s)[::-1][:k])&set(epi))/len(epi)
W=40; res={k:[] for k in ['degree','triangles','eigenvector','eigenvec_top2']}
for s in range(80):
    idx=rng.permutation(12); A_=tuple(idx[:3]); B_=tuple(idx[3:6]); epi=set(A_)|set(B_)
    R=gen_multi(epiA=A_,epiB=B_,seed=300+s); a=attribs(R[120:120+W])
    for k in res: res[k].append(hit(a[k],epi))
print("TWO-EPICENTRE CRISIS: does it recover the 6 nodes of both epicentres?")
print("(hits in the top 6; 80 simulations; chance = 0.500)")
for k,v in res.items(): print(f"   {k:13s}: {np.mean(v):.3f}")
