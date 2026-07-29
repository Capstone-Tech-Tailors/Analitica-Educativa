"""Métricas de acuerdo entre anotadores (inter-annotator agreement).

Implementaciones propias validadas contra valores publicados, porque el entorno no
dispone de `statsmodels` ni del paquete `krippendorff`:

    Fleiss κ  (ejemplo canónico 10x14x5) ....... 0.2099  [publicado 0.210]
    Krippendorff α nominal (matriz canónica) ... 0.6914  [publicado 0.691]
    Krippendorff α ordinal (misma matriz) ...... 0.8067  [publicado 0.807]

Uso previsto: consolidar la anotación humana de `anotacion/` (ver PROTOCOLO_ANOTACION.md).
α de Krippendorff es la métrica titular porque admite anotadores por ítem variables
(diseño incompleto: bloque de evaluación con 3 anotadores + bloque de entrenamiento con 1).
"""

import numpy as np, itertools
from sklearn.metrics import cohen_kappa_score, confusion_matrix

def fleiss_kappa(counts):
    """counts: matriz (N items x K categorias) con el numero de anotadores que eligio cada categoria.
    Requiere el mismo numero de anotadores n en todos los items."""
    counts = np.asarray(counts, float)
    N, K = counts.shape
    n = counts.sum(axis=1)
    assert np.allclose(n, n[0]), "Fleiss exige n constante por item"
    n = n[0]
    P_i = (np.square(counts).sum(axis=1) - n) / (n * (n - 1))
    P_bar = P_i.mean()
    p_j = counts.sum(axis=0) / (N * n)
    P_e = np.square(p_j).sum()
    return (P_bar - P_e) / (1 - P_e), P_bar, P_e

def krippendorff_alpha(data, level="nominal", categories=None):
    """data: matriz (anotadores x items) con np.nan para faltantes. Admite datos faltantes
    y numero variable de anotadores por item (a diferencia de Fleiss)."""
    data = np.asarray(data, float)
    if categories is None:
        categories = np.unique(data[~np.isnan(data)])
    categories = np.asarray(categories, float)
    K = len(categories)
    idx = {c: i for i, c in enumerate(categories)}
    # matriz de coincidencias observadas
    O = np.zeros((K, K))
    for j in range(data.shape[1]):
        col = data[:, j]
        col = col[~np.isnan(col)]
        m = len(col)
        if m < 2:
            continue  # unidades con 1 solo anotador no aportan a alpha
        for a, b in itertools.permutations(col, 2):
            O[idx[a], idx[b]] += 1.0 / (m - 1)
    n_total = O.sum()
    n_c = O.sum(axis=1)
    if level == "nominal":
        delta = 1.0 - np.eye(K)
    elif level == "ordinal":
        delta = np.zeros((K, K))
        for a in range(K):
            for b in range(K):
                lo, hi = min(a, b), max(a, b)
                s = n_c[lo:hi + 1].sum() - (n_c[lo] + n_c[hi]) / 2.0
                delta[a, b] = s ** 2
    else:
        raise ValueError(level)
    D_o = (O * delta).sum()
    E = np.outer(n_c, n_c) - np.diag(n_c)
    D_e = (E * delta).sum() / (n_total - 1)
    return 1.0 - D_o / D_e

def mean_pairwise_cohen(data, labels=None):
    """data: (anotadores x items). Cohen por pares sobre items co-anotados; devuelve media y detalle."""
    data = np.asarray(data, float)
    R = data.shape[0]
    out = {}
    for i, j in itertools.combinations(range(R), 2):
        m = ~np.isnan(data[i]) & ~np.isnan(data[j])
        out[(i, j)] = cohen_kappa_score(data[i][m], data[j][m], labels=labels)
    return float(np.mean(list(out.values()))), out

def observed_agreement_triples(data):
    """% de items con unanimidad, mayoria 2/1, y sin mayoria 1/1/1 (3 anotadores, 3 clases)."""
    data = np.asarray(data)
    unan = maj = none = 0
    for j in range(data.shape[1]):
        _, c = np.unique(data[:, j], return_counts=True)
        if c.max() == 3: unan += 1
        elif c.max() == 2: maj += 1
        else: none += 1
    N = data.shape[1]
    return unan / N, maj / N, none / N

# ---------------- VALIDACION contra valores publicados ----------------
if __name__ == "__main__":
    # 1) Fleiss (1971) / ejemplo canonico: 10 sujetos, 14 anotadores, 5 categorias -> kappa = 0.210
    fleiss_ref = [[0,0,0,0,14],[0,2,6,4,2],[0,0,3,5,6],[0,3,9,2,0],[2,2,8,1,1],
                  [7,7,0,0,0],[3,2,6,3,0],[2,5,3,2,2],[6,5,2,1,0],[0,2,2,3,7]]
    k, Pbar, Pe = fleiss_kappa(fleiss_ref)
    print(f"Fleiss kappa (ejemplo canonico) = {k:.4f}  [referencia publicada 0.210]  Pbar={Pbar:.4f} Pe={Pe:.4f}")

    # 2) Krippendorff: ejemplo con faltantes de 'Computing Krippendorff's Alpha-Reliability'
    #    -> nominal 0.691, ordinal 0.807
    nan = np.nan
    kd_ref = np.array([
        [nan,nan,nan,nan,nan, 3, 4, 1, 2, 1, 1, 3, 3,nan, 3],
        [ 1 ,nan, 2 , 1 , 3 , 3, 4, 3,nan,nan,nan,nan,nan,nan,nan],
        [nan,nan, 2 , 1 , 3 , 4, 4,nan, 2, 1, 1, 3, 3,nan, 4]])
    print(f"Krippendorff alpha nominal = {krippendorff_alpha(kd_ref,'nominal'):.4f}  [referencia 0.691]")
    print(f"Krippendorff alpha ordinal = {krippendorff_alpha(kd_ref,'ordinal'):.4f}  [referencia 0.807]")

    # 3) Coherencia: con 3 anotadores completos y sin faltantes, alpha nominal ~= Fleiss kappa
    rng = np.random.default_rng(0)
    sim = rng.choice([0,1,2], size=(3, 400), p=[.69,.13,.18])
    cnt = np.stack([(sim==c).sum(axis=0) for c in (0,1,2)], axis=1)
    print(f"\nDatos completos: Fleiss={fleiss_kappa(cnt)[0]:.4f}  alpha_nominal={krippendorff_alpha(sim,'nominal'):.4f}  (deben coincidir ~1/N)")
