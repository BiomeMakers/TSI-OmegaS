import numpy as np
from itertools import combinations

def rips_persistence(D, max_dim=2):
    """
    Persistent homology of a Vietoris-Rips filtration over a matrix
    of distances D (n x n). Returns (dim, birth, death) triples for H0 and H1.
    Self-contained implementation (boundary-matrix reduction over Z2)
    ya que el entorno no tiene acceso a red para instalar ripser/gudhi.
    Factible aqui porque n es pequeno (8-11 activos -> <=231 simplices).
    """
    n = D.shape[0]
    simplices = [(0, (i,), 0.0) for i in range(n)]
    for i, j in combinations(range(n), 2):
        simplices.append((1, (i, j), D[i, j]))
    if max_dim >= 2:
        for i, j, k in combinations(range(n), 3):
            filt = max(D[i, j], D[i, k], D[j, k])
            simplices.append((2, (i, j, k), filt))

    order = sorted(range(len(simplices)), key=lambda idx: (simplices[idx][2], simplices[idx][0]))
    ordered = [simplices[idx] for idx in order]
    index_of = {verts: pos for pos, (dim, verts, filt) in enumerate(ordered)}

    col_sets = []
    for dim, verts, filt in ordered:
        if dim == 0:
            col_sets.append(set())
        else:
            faces = [verts[:k] + verts[k+1:] for k in range(len(verts))]
            col_sets.append({index_of[f] for f in faces})

    m = len(col_sets)
    low = [-1] * m
    pivot_to_col = {}
    for j in range(m):
        while col_sets[j]:
            piv = max(col_sets[j])
            if piv in pivot_to_col:
                col_sets[j] ^= col_sets[pivot_to_col[piv]]
            else:
                pivot_to_col[piv] = j
                low[j] = piv
                break

    pairs = []
    for j in range(m):
        if low[j] != -1:
            i = low[j]
            dim_i = ordered[i][0]
            birth = ordered[i][2]
            death = ordered[j][2]
            if death > birth:
                pairs.append((dim_i, birth, death))
    return pairs


def h1_persistence_norm(corr_matrix):
    """
    corr_matrix: matriz de correlacion (n x n).
    Convierte a distancia estandar de econofisica (Mantegna 1999):
    d_ij = sqrt(2*(1-corr_ij)), calcula homologia persistente H1
    y devuelve la norma L1 (suma de vidas de los lazos = suma de (death-birth)).
    """
    n = corr_matrix.shape[0]
    D = np.sqrt(np.clip(2 * (1 - corr_matrix), 0, None))
    np.fill_diagonal(D, 0.0)
    pairs = rips_persistence(D, max_dim=2)
    h1 = [(b, d) for (dim, b, d) in pairs if dim == 1]
    return sum(d - b for b, d in h1), len(h1)


if __name__ == "__main__":
    # sanity check: circulo de 6 puntos (debe generar un lazo H1 persistente)
    import numpy as np
    theta = np.linspace(0, 2*np.pi, 6, endpoint=False)
    pts = np.stack([np.cos(theta), np.sin(theta)], axis=1)
    D = np.sqrt(((pts[:, None, :] - pts[None, :, :])**2).sum(-1))
    pairs = rips_persistence(D)
    print("Pares (dim, birth, death):")
    for p in sorted(pairs):
        print(p)
