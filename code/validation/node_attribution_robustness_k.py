"""Attribution robustness to an UNKNOWN number of epicentres (Section 3.6c).
Compares triangle attribution diag(A^3) -- native to Omega -- against
fixed-k spectral attribution and the simpler degree rule, across regimes with
1 to 4 simultaneous epicentres. Headline: triangles are hyperparameter-free and
stay at 0.978-0.997 while fixed-k spectral drops to 0.747 when k is wrong.
"""
"""Is degree-based attribution more robust than spectral attribution when the
number of epicentres is unknown? The spectral route has to choose k
eigenvectors, and in production k is fixed. Degree needs no such choice."""
import numpy as np
rng=np.random.default_rng(0)

def gen(n=16, T=200, epicentres=None, t0=100, seed=0):
    """epicentres: list of tuples, each a group stressed by its own factor."""
    r=np.random.default_rng(seed)
    Fs=[r.normal(0,1,T) for _ in epicentres]
    bg=r.normal(0,1,T)
    R=np.zeros((T,n)); memb={}
    for gi,g in enumerate(epicentres):
        for i in g: memb[i]=gi
    for t in range(T):
        for i in range(n):
            if t<t0: R[t,i]=r.normal(0,1)
            elif i in memb: 
                b=0.90; R[t,i]=b*Fs[memb[i]][t]+np.sqrt(1-b**2)*r.normal(0,1)
            else:
                b=0.25; R[t,i]=b*bg[t]+np.sqrt(1-b**2)*r.normal(0,1)
    return R

def attribs(win, k_fijo=2):
    C=np.corrcoef(win.T); A=np.abs(C); np.fill_diagonal(A,0)
    ev,V=np.linalg.eigh(C)
    out=dict(degree=A.sum(1), triangles=np.diag(A@A@A))
    # spectral attribution with FIXED k (what a production system would do)
    out[f'espectral_k{k_fijo}']=np.sum(np.abs(V[:,-k_fijo:]),axis=1)
    # spectral attribution with ORACLE k (= true number of epicentres): an upper bound
    return out, ev, V

def hit(s, nodos_foco, k):
    return len(set(np.argsort(s)[::-1][:k]) & set(nodos_foco))/len(nodos_foco)

print("Attribution when the number of epicentres varies and the spectral rule uses k=2")
print("(hit in the top |epicentres|; chance is about |epicentres|/16)\n")
print(f"{'epicentres':>10} | {'chance':>6} | {'degree':>6} | {'triangle':>8} | {'spec_k2':>8} | {'spec_ORACLE':>12}")
for nf in (1,2,3,4):
    res={'degree':[],'triangles':[],'spec2':[],'specO':[]}
    for s in range(80):
        idx=rng.permutation(16); epicentres=[tuple(idx[3*j:3*j+3]) for j in range(nf)]
        nodes=[i for g in epicentres for i in g]
        R=gen(epicentres=epicentres,seed=400+s); win=R[120:160]
        a,ev,V=attribs(win,k_fijo=2)
        res['degree'].append(hit(a['degree'],nodes,len(nodes)))
        res['triangles'].append(hit(a['triangles'],nodes,len(nodes)))
        res['spec2'].append(hit(a['espectral_k2'],nodes,len(nodes)))
        specO=np.sum(np.abs(V[:,-nf:]),axis=1)          # k = true number of epicentres (oracle)
        res['specO'].append(hit(specO,nodes,len(nodes)))
    az=3*nf/16
    print(f"{nf:>9} | {az:5.2f} | {np.mean(res['degree']):6.3f} | {np.mean(res['triangles']):6.3f} | "
          f"{np.mean(res['spec2']):8.3f} | {np.mean(res['specO']):13.3f}")
