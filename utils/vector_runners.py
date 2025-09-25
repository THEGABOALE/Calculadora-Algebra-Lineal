from __future__ import annotations
from models.Matrix import Matrix
from models.GaussJordan import GaussJordanMethod
from models.Vector import Vector
from utils.vector_tools import (
    read_vector, read_vectors, verify_vector_properties,
    matrix_vector_product_steps, pretty_linear_comb,
    ax_check, pretty_vector
)
from helpers.inputsmatrix import inputs_matrix, read_matrix_only
from utils.printMethods import (print_frame, print_summary, print_equation, print_parametric_solution_from_rref)
from utils.EquationFunctions import format_number, parse_fraction

# ------- Validadores simples (positivos) -------

def _read_positive_int(prompt: str) -> int:
    while True:
        try:
            v = int(input(prompt).strip())
            if v <= 0:
                print("Debe ser un entero positivo. Intenta de nuevo.")
                continue
            return v
        except ValueError:
            print("Entrada inválida. Ingresa un entero positivo.")

def _read_scalar(prompt: str) -> float:
    while True:
        try:
            return parse_fraction(input(prompt).strip())
        except Exception as e:
            print(f"Escalar inválido ({e}). Intenta de nuevo.")

# -------- Runner 1: Propiedades de vectores --------
def run_vector_props():
    print("\n--- Propiedades algebraicas en R^n ---")
    n = _read_positive_int("Dimensión n del espacio: ")
    v = read_vector(n, "Vector v")
    w = read_vector(n, "Vector w")
    u = read_vector(n, "Vector u")
    c = _read_scalar("Escalar c: ")
    d = _read_scalar("Escalar d: ")

    results = verify_vector_properties(v, w, u, c, d)
    print("\nResultados:")
    for name, ok, detail in results:
        print(f" - {name}: {'✔' if ok else '✘'}")
        print(f"   {detail}")

# -------- Runner 2: Combinación lineal / Ecuación vectorial --------
def run_vector_combination():
    """
    Pide k vectores v_i en R^m y un vector objetivo b, construye A=[v1 ... vk],
    resuelve A·c=b con Gauss–Jordan y muestra:
      - planteo algebraico,
      - frame de operaciones,
      - resumen,
      - forma paramétrica (si aplica),
      - verificación Ax=b con la solución particular (libres=0).
    """
    print("\n--- Combinación lineal / Ecuación vectorial ---")
    m = _read_positive_int("Dimensión de los vectores (m): ")
    k = _read_positive_int("Cantidad de vectores disponibles (k): ")

    print("\nIngresa los vectores columna v1..vk:")
    vecs = read_vectors(k, m, prefix="v")
    print("\nVector objetivo b:")
    b = read_vector(m)

    # Construir A con v_i como columnas
    A = [[vecs[j].data[i] for j in range(k)] for i in range(m)]
    b_list = b.data[:]

    # Planteo
    print("\nPlanteo:  A·c = b  con  A = [v1 v2 ... vk]")
    print("Combinación: c1·v1 + c2·v2 + ... + ck·vk")
    print(print_equation(A, b_list))

    # Resolver con Gauss–Jordan
    gj = GaussJordanMethod(A, b_list)
    gj.run()
    result = gj.solve_and_log()

    print_frame(gj.frame)
    print(print_equation(A, b_list))
    print_summary(result)

    # Forma paramétrica si hay infinitas soluciones
    if result.get("status") == "infinite":
        print("\n--- Forma paramétrica (RREF) ---")
        print(print_parametric_solution_from_rref(gj.matriz))

    # Verificación Ax=b con la solución particular (libres=0)
    x_part = result.get("solution")
    if x_part is not None:
        y, ok = ax_check(A, x_part, b_list)
        print("\n--- Verificación Ax = b (con solución particular) ---")
        print("x* =", pretty_vector(x_part))
        print("Ax  =", pretty_vector(y))
        print("b   =", pretty_vector(b_list))
        print("¿Ax=b? ->", "OK ✅" if ok else "NO ❌")

def run_matrix_times_vector():
    """
    Pide A (m×n) y x (n), muestra Ax por la regla fila–vector y además:
      • resuelve A·c = b con b:=Ax usando Gauss–Jordan,
      • imprime TODO el proceso (pivotes, eliminaciones, RREF),
      • muestra el summary (única / infinita / inconsistente),
      • concluye si b es combinación lineal de las columnas de A,
      • si hay infinitas, imprime la forma paramétrica (parámetros s1, s2, ...),
      • verifica Ax=b con la solución particular.
    """
    print("\n--- Producto Ax por regla fila–vector ---")
    rows, cols = inputs_matrix()
    A = read_matrix_only(rows, cols)  # solo coeficientes
    x = read_vector(cols, "Vector x:")

    # 1) Desarrollo fila–vector
    y, steps = matrix_vector_product_steps(A, x)
    print("\nA x =")
    for line in steps:
        print("  ", line)
    print("\nResultado Ax =", Vector(y))

    # 2) Gauss–Jordan sobre A·c=b (b := Ax) — mostramos TODO el proceso
    print("\n--- Gauss–Jordan para A·c = b (con b := Ax) ---")
    gj = GaussJordanMethod(A, y)
    gj.run()
    result = gj.solve_and_log()

    # proceso completo con pivoteo, eliminaciones y RREF
    print_frame(gj.frame)

    # resumen (única / infinita / inconsistente)
    print_summary(result)

    status = result.get("status")

    # 3) Si hay infinitas: forma paramétrica con parámetros s1, s2, ...
    if status == "infinite":
        print("\n--- Familia de soluciones (forma paramétrica) ---")
        # Nota pedagógica más explícita
        print("Existen infinitas combinaciones: cada variable libre se toma como un parámetro sₖ,")
        print("y las variables básicas se expresan en función de esos parámetros.\n")
        print(print_parametric_solution_from_rref(gj.matriz, param_base="s"))

    # 4) Verificación explícita Ax=b con la solución particular
    x_part = result.get("solution")
    if x_part is not None:
        y_check, ok = ax_check(A, x_part, y)
        print("\n--- Chequeo Ax = b con la solución particular (libres=0) ---")
        print("c* =", pretty_vector(x_part))
        print("A·c* =", pretty_vector(y_check))
        print("b    =", pretty_vector(y))
        print("¿A·c* = b? ->", "OK ✅" if ok else "NO ❌")

    # 5) Conclusión didáctica
    if status == "unique":
        print("\nConclusión: b ES una combinación lineal de las columnas de A, y es ÚNICA.")
    elif status == "infinite":
        print("\nConclusión: b ES una combinación lineal de las columnas de A, en INFINITAS formas (ver arriba).")
    elif status == "inconsistent":
        # Con b := Ax nunca debería pasar; si ocurre, hay error de entrada
        print("\nConclusión: Inconsistente (esto no debería ocurrir con b := Ax). Revisa los datos.")