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
from utils.matrix_tools import inverse, determinant, is_singular
from utils.matrix_memory import list_names as mem_list, get as mem_get, save as mem_save, remove as mem_remove, pretty_inventory as mem_inv

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

# --- NUEVO: leer desde memoria o teclado
def _maybe_pick_from_memory(expected_rc: tuple[int, int] | None = None) -> Matrix | None:
    if not mem_list():
        return None
    ans = input("¿Usar una matriz guardada? [s/N]: ").strip().lower()
    if ans != "s":
        return None
    print("\nMemoria disponible:")
    print(mem_inv())
    name = input("Nombre exacto: ").strip()
    M = mem_get(name)
    if M is None:
        print("No existe una matriz con ese nombre.")
        return None
    if expected_rc:
        r0, c0 = expected_rc
        r, c = shape_of(M)
        if (r, c) != (r0, c0):
            print(f"Incompatible: se esperaba {r0}x{c0} y '{name}' es {r}x{c}.")
            return None
    return M

def _ask_store_result(M: Matrix) -> None:
    ans = input("\n¿Guardar este resultado en memoria? [s/N]: ").strip().lower()
    if ans != "s":
        return
    while True:
        name = input("Nombre para guardar (ej. A, B, Prod1): ").strip()
        if not name:
            print("El nombre no puede estar vacío.")
            continue
        if name in mem_list():
            over = input("Ya existe. ¿Sobrescribir? [s/N]: ").strip().lower()
            if over != "s":
                continue
        mem_save(name, M)
        print(f"Guardado como '{name}'.")
        break

def _read_many_same_size(k: int) -> List[Matrix]:
    """Pide k matrices del mismo tamaño (o elige de memoria)."""
    r, c = inputs_matrix()
    mats: List[Matrix] = []
    for i in range(k):
        print(f"\nMatriz M{i+1} ({r}x{c}):")
        M = _maybe_pick_from_memory((r, c))
        if M is None:
            M = read_matrix_only(r, c)
        mats.append(M)
    return mats

def _read_many_for_product(k: int) -> List[Matrix]:
    """Pide k matrices para producto encadenado (posible uso de memoria)."""
    mats: List[Matrix] = []
    for i in range(k):
        print(f"\nDimensiones de M{i+1}")
        r, c = inputs_matrix()
        print(f"\nMatriz M{i+1} ({r}x{c}):")
        M = _maybe_pick_from_memory((r, c))
        if M is None:
            M = read_matrix_only(r, c)
        mats.append(M)
        if i >= 1 and not mult_compatible(mats[i-1], mats[i]):
            r1, c1 = shape_of(mats[i-1]); r2, c2 = shape_of(mats[i])
            raise ValueError(f"Incompatibilidad en M{i}·M{i+1}: {c1} != {r2}.")
    return mats

# --------------------------
# Submenú de encadenamiento con el resultado
# --------------------------
def _chain_with_result(current: Matrix):
    """Permite seguir operando usando 'current' como A (y guardarlo cuando quieras)."""
    while True:
        print("\n¿Deseas continuar con el resultado actual?")
        print("[1] Sumar MÁS matrices (mismo tamaño)")
        print("[2] Restar MÁS matrices (A - M2 - M3 - ...)")
        print("[3] Multiplicar por escalar (αA)")
        print("[4] Multiplicar por OTRA matriz / cadena (A·M2[·M3…])")
        print("[5] Trasponer (Aᵀ)")
        print("[S] Guardar resultado en memoria")
        print("[0] Terminar")
        opt = input("Elige: ").strip().lower()

        try:
            if opt == "0":
                break

            if opt == "s":
                _ask_store_result(current)
                continue

            if opt == "1":
                k = _read_positive_int("¿Cuántas matrices adicionales vas a sumar? ")
                r, c = shape_of(current)
                extras: List[Matrix] = []
                for i in range(k):
                    print(f"\nMatriz extra E{i+1} ({r}x{c}):")
                    M = _maybe_pick_from_memory((r, c))
                    if M is None:
                        M = read_matrix_only(r, c)
                    extras.append(M)
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
                    M = _maybe_pick_from_memory((r, c))
                    if M is None:
                        M = read_matrix_only(r, c)
                    rest.append(M)
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
                    print("Matriz:")
                    M = _maybe_pick_from_memory((r, c))
                    if M is None:
                        M = read_matrix_only(r, c)
                    chain.append(M)
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

                # Probar identidades con otra matriz B (opcional)
                B = None
                if mem_list():
                    if input("¿Usar una B de memoria para probar identidades? [s/N]: ").strip().lower() == "s":
                        print(mem_inv())
                        name = input("Nombre de B: ").strip()
                        B = mem_get(name)
                        if B is None:
                            print("No existe una matriz con ese nombre.")

                print("Propiedades verificadas:")
                print(verify_transpose_props(current, B))
                current = AT

            else:
                print("Opción inválida.")
        except Exception as e:
            print(f"\nNo se pudo completar la operación: {e}")

# --------------------------
# Runners principales
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
    _ask_store_result(C)
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
    _ask_store_result(C)
    _chain_with_result(C)

def run_matrix_scalar():
    print("\n--- Multiplicación por escalar (αA) ---")
    r, c = inputs_matrix()
    print("\nMatriz A:")
    A = _maybe_pick_from_memory((r, c)) or read_matrix_only(r, c)
    alpha = _read_scalar("\nEscalar α: ")

    C, steps = scalar_mult(alpha, A)
    print(pretty_show("A", A))
    print(f"Pasos (α = {format_number(alpha)}):")
    print(steps)
    print(pretty_show("αA =", C))
    _ask_store_result(C)
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
    _ask_store_result(C)
    _chain_with_result(C)

def run_matrix_transpose():
    print("\n--- Matriz traspuesta (Aᵀ) ---")
    r, c = inputs_matrix()
    print("\nMatriz A:")
    A = _maybe_pick_from_memory((r, c)) or read_matrix_only(r, c)

    AT, steps = transpose(A)
    print(pretty_show("A", A))
    print("Cómo se obtiene Aᵀ (filas ↔ columnas):")
    print(steps)
    print(pretty_show("Aᵀ =", AT))

    # Probar identidades con posible B de memoria
    B = None
    if mem_list():
        if input("¿Usar una B de memoria para probar identidades? [s/N]: ").strip().lower() == "s":
            print(mem_inv())
            name = input("Nombre de B: ").strip()
            B = mem_get(name)
            if B is None:
                print("No existe una matriz con ese nombre.")

    print("Propiedades verificadas:")
    print(verify_transpose_props(A, B))
    _ask_store_result(AT)
    _chain_with_result(AT)


def run_matrix_inverse():
    print("\n--- Matriz inversa (A⁻¹) ---")
    r, c = inputs_matrix()
    if r != c:
        print("La matriz debe ser cuadrada para calcular su inversa.")
        return
    print("\nMatriz A:")
    A = _maybe_pick_from_memory((r, c)) or read_matrix_only(r, c)

    try:
        det_val = determinant(A)
        if abs(det_val) <= 1e-12:
            print("La matriz es singular (determinante = 0) y no tiene inversa.")
            return
    except Exception:
        # si falla el determinante, seguimos y dejamos que inverse lance
        pass

    try:
        Ainv, steps = inverse(A)
        print(pretty_show("A", A))
        print("Pasos (Gauss-Jordan sobre [A | I]):")
        print(steps)
        print(pretty_show("A⁻¹ =", Ainv))
        _ask_store_result(Ainv)
        _chain_with_result(Ainv)
    except Exception as e:
        print(f"No se pudo calcular la inversa: {e}")

# --------------------------
# Menú de MEMORIA (gestión básica y prueba de (AB)^T)
# --------------------------
def matrices_memory_menu():
    while True:
        print("\n--- Memoria de matrices ---")
        print("[1] Listar matrices guardadas")
        print("[2] Ver una matriz")
        print("[3] Eliminar una matriz")
        print("[4] Probar (AB)ᵀ = BᵀAᵀ con matrices guardadas")
        print("[0] Volver")
        opt = input("Elige: ").strip()

        if opt == "0":
            break
        elif opt == "1":
            print("\n" + mem_inv())
        elif opt == "2":
            print("\n" + mem_inv())
            name = input("Nombre: ").strip()
            M = mem_get(name)
            if M is None:
                print("No existe ese nombre.")
            else:
                r, c = shape_of(M)
                print(pretty_show(f"{name} ({r}x{c})", M))
        elif opt == "3":
            print("\n" + mem_inv())
            name = input("Nombre a eliminar: ").strip()
            if mem_remove(name):
                print("Eliminada.")
            else:
                print("No existe ese nombre.")
        elif opt == "4":
            if not mem_list():
                print("Memoria vacía.")
                continue
            print("\n" + mem_inv())
            a = input("Nombre de A: ").strip()
            b = input("Nombre de B: ").strip()
            A = mem_get(a); B = mem_get(b)
            if A is None or B is None:
                print("Alguna matriz no existe.")
                continue
            print("Comprobaciones de traspuesta:")
            print(verify_transpose_props(A, B))
        else:
            print("Opción inválida.")

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
        print("[6] Matriz inversa  A⁻¹")
        print("[7] Memoria")
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
            elif opt == "6":
                run_matrix_inverse()
            elif opt == "7":
                matrices_memory_menu()
            
            else:
                print("Opción inválida. Intenta de nuevo.")
        except Exception as e:
            print(f"\nNo se pudo completar la operación: {e}")
