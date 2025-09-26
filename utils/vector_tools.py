from __future__ import annotations
from typing import List, Tuple
from models.Vector import Vector
from utils.EquationFunctions import format_number, parse_fraction

# -------- Entrada y helpers --------

def read_vector(dim: int, prompt: str = "") -> Vector:
    """Lee un vector de dimensión 'dim' desde input (admite fracciones tipo 3/4)."""
    if prompt:
        print(prompt)
    while True:
        raw = input(f"Ingresa {dim} valores separados por espacio: ").strip().split()
        if len(raw) != dim:
            print(f"Se esperaban {dim} valores. Intenta de nuevo.")
            continue
        try:
            vals = [parse_fraction(x) for x in raw]
            return Vector(vals)
        except Exception as e:
            print(f"Entrada inválida ({e}). Intenta de nuevo.")

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

# -------- Propiedades en R^n --------

def verify_vector_properties(v: Vector, w: Vector, u: Vector, c: float, d: float, tol: float = 1e-12) -> List[Tuple[str, bool, str]]:
    """Devuelve lista de (propiedad, cumple, detalle)."""
    p1 = v.add(w).equals(w.add(v), tol)
    p2 = (u.add(v).add(w)).equals(u.add(v.add(w)), tol)
    z = zero_vector(v.n)
    p3 = v.add(z).equals(v, tol)
    p4 = v.add(v.scale(-1)).equals(z, tol)
    p5 = u.add(v).scale(c).equals(u.scale(c).add(v.scale(c)), tol)
    p6 = u.scale(c + d).equals(u.scale(c).add(u.scale(d)), tol)
    results = [
        ("Conmutativa: v + w = w + v", p1, f"{v} + {w} {'=' if p1 else '≠'} {w} + {v}"),
        ("Asociativa: (u + v) + w = u + (v + w)", p2, f"({u}+{v})+{w} {'=' if p2 else '≠'} {u}+({v}+{w})"),
        ("Existencia de 0: v + 0 = v", p3, f"{v} + {z} {'=' if p3 else '≠'} {v}"),
        ("Vector opuesto: v + (-v) = 0", p4, f"{v} + ({v.scale(-1)}) {'=' if p4 else '≠'} {z}"),
        ("Distributiva c(u+v) = cu + cv", p5, f"{c}·({u}+{v}) {'=' if p5 else '≠'} {u.scale(c)} + {v.scale(c)}"),
        ("Distributiva (c+d)u = cu + du", p6, f"({c}+{d})·{u} {'=' if p6 else '≠'} {u.scale(c)} + {u.scale(d)}"),
    ]
    return results

# -------- Producto Ax y verificación --------

def matrix_vector_product_steps(A: List[List[float]], x: Vector) -> Tuple[List[float], List[str]]:
    """Calcula y explica cada entrada (fila i de A) · x."""
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

def ax_check(A: List[List[float]], x_list: List[float], b_list: List[float], tol: float = 1e-9):
    """Devuelve (A*x, ok) con ok=True si A*x ≈ b bajo tolerancia."""
    m = len(A)
    n = len(A[0]) if m else 0
    if len(x_list) != n:
        raise ValueError("Dimensiones incompatibles entre A y x.")
    y = [sum(A[i][j] * x_list[j] for j in range(n)) for i in range(m)]
    ok = (len(b_list) == m) and all(abs(y[i] - b_list[i]) <= tol for i in range(m))
    return y, ok

def pretty_vector(lst: List[float]) -> str:
    return "[" + ", ".join(format_number(v) for v in lst) + "]"


def linear_combination_verification_steps(coeffs: List[float], vectors: List[Vector], b_list: List[float]) -> Tuple[List[float], List[str]]:
    """
    Genera el desarrollo 'x1 v1 + x2 v2 + ...' componente a componente y el resultado final.
    Retorna (y, steps), donde y = sum_i (x_i * v_i), y 'steps' son líneas tipo:
       x1* v1(j) + x2* v2(j) + ... = b_j
    """
    if not vectors:
        return [], ["(Sin vectores)"]

    m = vectors[0].n
    k = len(vectors)
    if any(v.n != m for v in vectors):
        raise ValueError("Todos los vectores deben tener la misma dimensión.")
    if len(coeffs) != k:
        raise ValueError("La cantidad de coeficientes debe coincidir con la cantidad de vectores.")
    if len(b_list) != m:
        raise ValueError("La dimensión de b no coincide con los vectores.")

    # y = sum_i x_i * v_i
    y = [0.0]*m
    steps = []
    for j in range(m):
        term_strs = []
        acc = 0.0
        for i in range(k):
            c = coeffs[i]
            v_ij = vectors[i].data[j]
            acc += c * v_ij
            c_txt   = format_number(c)
            vij_txt = format_number(v_ij)
            term_strs.append(f"{c_txt}·{vij_txt}")
        y[j] = acc
        steps.append(" + ".join(term_strs) + f"  =  {format_number(acc)}   (objetivo: {format_number(b_list[j])})")

    return y, steps


def pretty_equation_vectorial(prefix_x: str, k: int) -> str:
    """
    Devuelve: 'Ecuación vectorial: x1·v1 + x2·v2 + ... + xk·vk = b'
    """
    parts = [f"{prefix_x}{i}·v{i}" for i in range(1, k+1)]
    return "Ecuación vectorial: " + " + ".join(parts) + " = b"

