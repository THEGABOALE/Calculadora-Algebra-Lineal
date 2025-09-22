from __future__ import annotations
from typing import List, Tuple
from models.Vector import Vector
from utils.EquationFunctions import format_number

# ---------- Entrada y helpers ----------

def read_vector(dim: int, prompt: str = "") -> Vector:
    """Lee un vector de dimensión 'dim' desde input."""
    if prompt:
        print(prompt)
    vals = input(f"Ingresa {dim} valores separados por espacio: ").strip().split()
    if len(vals) != dim:
        raise ValueError(f"Se esperaban {dim} valores.")
    return Vector([float(x) for x in vals])

def read_vectors(cnt: int, dim: int, prefix: str = "v") -> List[Vector]:
    """Lee 'cnt' vectores de dimensión 'dim'."""
    vecs = []
    for i in range(cnt):
        vecs.append(read_vector(dim, f"{prefix}{i+1}:"))
    return vecs

def zero_vector(dim: int) -> Vector:
    return Vector([0.0] * dim)

def pretty_linear_comb(coeffs: List[float], vectors: List[Vector]) -> str:
    """c1 v1 + c2 v2 + ... (solo visual)."""
    parts = []
    for i, c in enumerate(coeffs, start=1):
        s = format_number(c)
        parts.append(f"{s}·v{i}")
    return " + ".join(parts)

# ---------- Propiedades en R^n ----------

def verify_vector_properties(v: Vector, w: Vector, u: Vector, c: float, d: float, tol: float = 1e-12) -> List[Tuple[str, bool, str]]:
    """
    Devuelve lista de (propiedad, cumple, detalle).
    Propiedades: conmutativa, asociativa, existencia de 0, opuesto, distributivas.
    """
    # conmutativa: v + w = w + v
    p1 = v.add(w).equals(w.add(v), tol)

    # asociativa: (u + v) + w = u + (v + w)
    p2 = (u.add(v).add(w)).equals(u.add(v.add(w)), tol)

    # existencia de 0: v + 0 = v
    z = zero_vector(v.n)
    p3 = v.add(z).equals(v, tol)

    # opuesto: v + (-v) = 0
    p4 = v.add(v.scale(-1)).equals(z, tol)

    # A(u+v) = Au + Av  (distributiva vectorial) -> con escalares c,d simulamos A como escalar: c(u+v) = cu + cv
    p5 = u.add(v).scale(c).equals(u.scale(c).add(v.scale(c)), tol)

    # (c+d)u = cu + du (distributiva escalar)
    p6 = u.scale(c + d).equals(u.scale(c).add(u.scale(d)), tol)

    results = [
        ("Conmutativa: v + w = w + v", p1, f"{v} + {w} {'=' if p1 else '≠'} {w} + {v}"),
        ("Asociativa: (u + v) + w = u + (v + w)", p2, f"({u}+{v})+{w} {'=' if p2 else '≠'} {u}+({v}+{w})"),
        ("Existencia de 0: v + 0 = v", p3, f"{v} + {z} {'=' if p3 else '≠'} {v}"),
        ("Vector opuesto: v + (-v) = 0", p4, f"{v} + ({v.scale(-1)}) {'=' if p4 else '≠'} {z}"),
        ("Distributiva A(u+v)=Au+Av (simulada): c(u+v) = cu + cv", p5, f"{c}·({u}+{v}) {'=' if p5 else '≠'} {u.scale(c)} + {v.scale(c)}"),
        ("Distributiva (c+d)u = cu + du", p6, f"({c}+{d})·{u} {'=' if p6 else '≠'} {u.scale(c)} + {u.scale(d)}"),
    ]
    return results

# ---------- Producto Ax por regla fila–vector (solo visual) ----------

def matrix_vector_product_steps(A: List[List[float]], x: Vector) -> Tuple[List[float], List[str]]:
    """
    Calcula y explica cada entrada (i-ésima fila de A) · x.
    Retorna (resultado, pasos_formateados)
    """
    m = len(A)
    n = len(A[0]) if m else 0
    if x.n != n:
        raise ValueError("Dimensiones incompatibles: columnas(A) deben coincidir con entradas(x).")

    steps = []
    y = []
    for i in range(m):
        terms = [f"{format_number(A[i][j])}·{format_number(x.data[j])}" for j in range(n)]
        val = sum(A[i][j] * x.data[j] for j in range(n))
        y.append(val)
        steps.append(" + ".join(terms) + f"  =  {format_number(val)}")
    return y, steps
