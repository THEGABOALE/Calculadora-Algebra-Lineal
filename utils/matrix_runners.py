# utils/matrix_runners.py
from __future__ import annotations
from typing import List
from helpers.inputsmatrix import inputs_matrix, read_matrix_only
from utils.EquationFunctions import parse_fraction, format_number
from utils.matrix_tools import (
    add_matrices, sub_matrices, scalar_mult, matmul, transpose,
    sum_many, sub_many, matmul_chain,
    verify_transpose_props, pretty_show, shape_of, same_size, mult_compatible
)

Matrix = List[List[float]]

# --------------------------
# Helpers de entrada
# --------------------------
def _read_scalar(prompt: str) -> float:
    while True:
        try:
            return parse_fraction(input(prompt).strip())
        except Exception as e:
            print(f"Escalar inválido ({e}). Intenta de nuevo.")

def _read_positive_int(prompt: str) -> int:
    while True:
        try:
            v = int(input(prompt).strip())
            if v <= 0:
                print("Debe ser un entero positivo.")
                continue
            return v
        except ValueError:
            print("Ingresa un entero válido.")

def _read_many_same_size(k: int) -> List[Matrix]:
    """Pide k matrices del mismo tamaño (pide filas/cols una sola vez)."""
    r, c = inputs_matrix()
    mats = []
    for i in range(k):
        print(f"\nMatriz M{i+1} ({r}x{c}):")   # Confirmación de dimensiones
        mats.append(read_matrix_only(r, c))
    return mats

def _read_many_for_product(k: int) -> List[Matrix]:
    """Pide k matrices para producto encadenado (pide dims cada una)."""
    mats = []
    for i in range(k):
        print(f"\nDimensiones de M{i+1}")
        r, c = inputs_matrix()
        print(f"\nMatriz M{i+1} ({r}x{c}):")    # Confirmación de dimensiones
        mats.append(read_matrix_only(r, c))
    # Verificación rápida
    for i in range(len(mats)-1):
        if not mult_compatible(mats[i], mats[i+1]):
            raise ValueError(f"Incompatibilidad en M{i+1}·M{i+2}: cols(M{i+1}) != filas(M{i+2}).")
    return mats

# --------------------------
# Submenú de encadenamiento con el resultado
# --------------------------
def _chain_with_result(current: Matrix):
    """Permite seguir operando usando 'current' como A."""
    while True:
        print("\n¿Deseas continuar con el resultado actual como A?")
        print("[1] Sumar MÁS matrices (mismo tamaño)")
        print("[2] Restar MÁS matrices (A - M2 - M3 - ...)")
        print("[3] Multiplicar por escalar (αA)")
        print("[4] Multiplicar por OTRA matriz / cadena (A·M2[·M3…])")
        print("[5] Trasponer (Aᵀ)")
        print("[0] Terminar")
        opt = input("Elige: ").strip()

        try:
            if opt == "0":
                break

            if opt == "1":
                k = _read_positive_int("¿Cuántas matrices adicionales vas a sumar? ")
                r, c = shape_of(current)
                extras: List[Matrix] = []
                for i in range(k):
                    print(f"\nMatriz extra E{i+1} ({r}x{c}):")
                    extras.append(read_matrix_only(r, c))
                C, steps = sum_many([current] + extras)
                print(pretty_show("Resultado previo (A)", current))
                for i, E in enumerate(extras, start=1):
                    print(pretty_show(f"E{i}", E))
                print("Pasos (suma acumulada):")
                print(steps)
                current = C
                print(pretty_show("Nuevo resultado A =", current))

            elif opt == "2":
                k = _read_positive_int("¿Cuántas matrices vas a RESTAR? ")
                r, c = shape_of(current)
                rest: List[Matrix] = []
                for i in range(k):
                    print(f"\nMatriz a restar R{i+1} ({r}x{c}):")
                    rest.append(read_matrix_only(r, c))
                C, steps = sub_many(current, rest)
                print(pretty_show("Resultado previo (A)", current))
                for i, R in enumerate(rest, start=1):
                    print(pretty_show(f"R{i}", R))
                print("Pasos (resta en cadena):")
                print(steps)
                current = C
                print(pretty_show("Nuevo resultado A =", current))

            elif opt == "3":
                alpha = _read_scalar("Escalar α: ")
                C, steps = scalar_mult(alpha, current)
                print(pretty_show("A", current))
                print(f"Pasos (α = {format_number(alpha)}):")
                print(steps)
                current = C
                print(pretty_show("Nuevo resultado A =", current))

            elif opt == "4":
                k = _read_positive_int("¿Cuántas matrices vas a multiplicar a derecha? (≥1) ")
                chain = [current]
                for i in range(k):
                    print("\nDimensiones de la nueva matriz:")
                    r, c = inputs_matrix()
                    print(f"Matriz ({r}x{c}):")   # Confirmación de dimensiones
                    chain.append(read_matrix_only(r, c))
                C, steps = matmul_chain(chain)
                print(pretty_show("A (resultado previo)", current))
                for i, M in enumerate(chain[1:], start=2):
                    print(pretty_show(f"M{i}", M))
                print("Desarrollo por etapas (producto en cadena):")
                print(steps)
                current = C
                print(pretty_show("Nuevo resultado A =", current))

            elif opt == "5":
                AT, steps = transpose(current)
                print(pretty_show("A", current))
                print("Cómo se obtiene Aᵀ:")
                print(steps)
                print(pretty_show("Aᵀ =", AT))
                print("Propiedades verificadas:")
                from utils.matrix_tools import verify_transpose_props
                print(verify_transpose_props(current))
                current = AT

            else:
                print("Opción inválida.")
        except Exception as e:
            print(f"\nNo se pudo completar la operación: {e}")

# --------------------------
# Runners principales (entrada libre)
# --------------------------
def run_matrix_add():
    print("\n--- Suma de matrices (M1 + M2 + ... + Mk) ---")
    k = _read_positive_int("¿Cuántas matrices vas a sumar? (k ≥ 2): ")
    if k < 2:
        print("Debes ingresar al menos 2 matrices.")
        return
    mats = _read_many_same_size(k)

    C, steps = sum_many(mats)
    for i, M in enumerate(mats, start=1):
        print(pretty_show(f"M{i}", M))
    print("Pasos (suma elemento a elemento):")
    print(steps)
    print(pretty_show("Resultado =", C))

    # Encadenar con el resultado
    _chain_with_result(C)

def run_matrix_sub():
    print("\n--- Resta en cadena (M1 - M2 - ... - Mk) ---")
    k = _read_positive_int("¿Cuántas matrices en total? (k ≥ 2): ")
    if k < 2:
        print("Debes ingresar al menos 2 matrices.")
        return
    mats = _read_many_same_size(k)
    C, steps = sub_many(mats[0], mats[1:])

    for i, M in enumerate(mats, start=1):
        print(pretty_show(f"M{i}", M))
    print("Pasos (resta elemento a elemento):")
    print(steps)
    print(pretty_show("Resultado =", C))

    _chain_with_result(C)

def run_matrix_scalar():
    print("\n--- Multiplicación por escalar (αA) ---")
    r, c = inputs_matrix()
    print(f"\nMatriz A ({r}x{c}):")             # Confirmación de dimensiones
    A = read_matrix_only(r, c)
    alpha = _read_scalar("\nEscalar α: ")

    C, steps = scalar_mult(alpha, A)
    print(pretty_show("A", A))
    print(f"Pasos (α = {format_number(alpha)}):")
    print(steps)
    print(pretty_show("αA =", C))

    _chain_with_result(C)

def run_matrix_prod():
    print("\n--- Multiplicación en cadena (M1 · M2 · ... · Mk) ---")
    k = _read_positive_int("¿Cuántas matrices vas a multiplicar? (k ≥ 2): ")
    if k < 2:
        print("Debes ingresar al menos 2 matrices.")
        return
    mats = _read_many_for_product(k)

    C, steps = matmul_chain(mats)
    for i, M in enumerate(mats, start=1):
        print(pretty_show(f"M{i}", M))
    print("Desarrollo c_ij = (fila i)·(columna j) por etapas:")
    print(steps)
    print(pretty_show("Resultado =", C))

    _chain_with_result(C)

def run_matrix_transpose():
    print("\n--- Matriz traspuesta (Aᵀ) ---")
    r, c = inputs_matrix()
    print(f"\nMatriz A ({r}x{c}):")             # Confirmación de dimensiones
    A = read_matrix_only(r, c)

    AT, steps = transpose(A)
    print(pretty_show("A", A))
    print("Cómo se obtiene Aᵀ (filas ↔ columnas):")
    print(steps)
    print(pretty_show("Aᵀ =", AT))
    print("Propiedades verificadas:")
    print(verify_transpose_props(A))

    _chain_with_result(AT)

# --------------------------
# Submenú (invocado por startup)
# --------------------------
def matrices_menu_loop():
    while True:
        print("\n=== MÓDULO DE MATRICES ===")
        print("[1] Sumar varias matrices  M1 + M2 + ... + Mk")
        print("[2] Restar en cadena       M1 - M2 - ... - Mk")
        print("[3] Multiplicar por escalar  αA")
        print("[4] Multiplicación en cadena M1·M2·...·Mk")
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
