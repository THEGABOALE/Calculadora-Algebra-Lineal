# utils/matrix_runners.py
from __future__ import annotations
from typing import List
from helpers.inputsmatrix import inputs_matrix, read_matrix_only
from utils.EquationFunctions import parse_fraction, format_number
from utils.matrix_tools import (
    add_matrices, sub_matrices, scalar_mult, matmul, transpose,
    verify_transpose_props, pretty_show, shape_of, same_size, mult_compatible
)

# --------------------------
# Helpers de entrada robustos
# --------------------------
def _read_scalar(prompt: str) -> float:
    while True:
        try:
            return parse_fraction(input(prompt).strip())
        except Exception as e:
            print(f"Escalar inválido ({e}). Intenta de nuevo.")

# --------------------------
# Runners
# --------------------------
def run_matrix_add():
    print("\n--- Suma de matrices ---")
    r, c = inputs_matrix()
    print("\nMatriz A:")
    A = read_matrix_only(r, c)
    print("\nMatriz B:")
    B = read_matrix_only(r, c)

    print("\nCompatibilidad: ", "OK ✔" if same_size(A, B) else "NO ❌")
    C, steps = add_matrices(A, B)

    print(pretty_show("A", A))
    print(pretty_show("B", B))
    print("Pasos:")
    print(steps)
    print(pretty_show("A + B =", C))

def run_matrix_sub():
    print("\n--- Resta de matrices (A - B) ---")
    r, c = inputs_matrix()
    print("\nMatriz A:")
    A = read_matrix_only(r, c)
    print("\nMatriz B:")
    B = read_matrix_only(r, c)

    print("\nCompatibilidad: ", "OK ✔" if same_size(A, B) else "NO ❌")
    C, steps = sub_matrices(A, B)

    print(pretty_show("A", A))
    print(pretty_show("B", B))
    print("Pasos:")
    print(steps)
    print(pretty_show("A - B =", C))

def run_matrix_scalar():
    print("\n--- Multiplicación por escalar (αA) ---")
    r, c = inputs_matrix()
    print("\nMatriz A:")
    A = read_matrix_only(r, c)
    alpha = _read_scalar("\nEscalar α: ")

    C, steps = scalar_mult(alpha, A)
    print(pretty_show("A", A))
    print(f"Pasos (α = {format_number(alpha)}):")
    print(steps)
    print(pretty_show("αA =", C))

def run_matrix_prod():
    print("\n--- Multiplicación de matrices (A·B) ---")
    print("Dimensiones de A")
    rA, cA = inputs_matrix()
    print("\nMatriz A:")
    A = read_matrix_only(rA, cA)

    print("\nDimensiones de B")
    rB, cB = inputs_matrix()
    print("\nMatriz B:")
    B = read_matrix_only(rB, cB)

    print("\nCompatibilidad: ", "OK ✔" if mult_compatible(A, B) else "NO ❌")
    C, steps = matmul(A, B)

    print(pretty_show("A", A))
    print(pretty_show("B", B))
    print("Desarrollo c_ij = (fila i de A) · (columna j de B):")
    print(steps)
    print(pretty_show("A·B =", C))

def run_matrix_transpose():
    print("\n--- Matriz traspuesta (Aᵀ) ---")
    r, c = inputs_matrix()
    print("\nMatriz A:")
    A = read_matrix_only(r, c)

    AT, steps = transpose(A)
    print(pretty_show("A", A))
    print("Cómo se obtiene Aᵀ (filas ↔ columnas):")
    print(steps)
    print(pretty_show("Aᵀ =", AT))
    print("Propiedades verificadas:")
    print(verify_transpose_props(A))

# --------------------------
# Submenú (invocado por startup)
# --------------------------
def matrices_menu_loop():
    while True:
        print("\n=== MÓDULO DE MATRICES ===")
        print("[1] Sumar matrices  A + B")
        print("[2] Restar matrices A - B")
        print("[3] Multiplicar por escalar  αA")
        print("[4] Multiplicación de matrices  A·B")
        print("[5] Matriz traspuesta  Aᵀ")
        print("[0] Volver")
        opt = input("Elige una opción: ").strip()

        if opt in ("0", "volver", "b"):
            break
        try:
            if opt == "1":
                run_matrix_add()
            elif opt == "2":
                run_matrix_sub()
            elif opt == "3":
                run_matrix_scalar()
            elif opt == "4":
                run_matrix_prod()
            elif opt == "5":
                run_matrix_transpose()
            else:
                print("Opción inválida. Intenta de nuevo.")
        except Exception as e:
            print(f"\nNo se pudo completar la operación: {e}")
