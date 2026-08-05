from __future__ import annotations
from core.matrix import Matrix
from core.gauss_jordan import GaussJordanMethod
from core.vector import Vector
from core.vector_tools import (
    read_vector, read_vectors, verify_vector_properties,
    matrix_vector_product_steps, pretty_linear_comb,
    ax_check, pretty_vector, linear_combination_verification_steps, pretty_equation_vectorial
)
from cli.inputsmatrix import inputs_matrix, read_matrix_only
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
    Combinación lineal / Ecuación vectorial.
    Flujo:
      1) Lee v1..vk (columna) en R^m y b.
      2) Construye A = [v1 v2 ... vk] y plantea 'Ecuación vectorial: x1·v1 + ... + xk·vk = b'.
      3) Resuelve A·x = b con Gauss–Jordan, imprime frame y summary.
      4) Si infinite -> imprime forma paramétrica (RREF) con parámetros s1, s2, ...
      5) Verifica explícitamente x1 v1 + ... + xk vk = b con la solución particular (libres = 0).
      6) Conclusión (unique / infinite / inconsistent).
    """
    print("\n--- Combinación lineal / Ecuación vectorial ---")
    m = _read_positive_int("Dimensión de los vectores (m): ")
    k = _read_positive_int("Cantidad de vectores disponibles (k): ")

    print("\nIngresa los vectores columna v1..vk:")
    vecs = read_vectors(k, m, prefix="v")
    print("\nVector objetivo b:")
    b = read_vector(m)

    # A con v_i como columnas
    A = [[vecs[j].data[i] for j in range(k)] for i in range(m)]
    b_list = b.data[:]

    # Planteo
    print("\nPlanteo:  A·x = b  con  A = [v1 v2 ... vk]")
    print(pretty_equation_vectorial("x", k))
    print(print_equation(A, b_list))

    # Resolver con Gauss–Jordan
    gj = GaussJordanMethod(A, b_list)
    gj.run()
    result = gj.solve_and_log()

    # Proceso (frame) + summary
    print_frame(gj.frame)
    print(print_equation(A, b_list))
    print_summary(result)

    status = result.get("status")
    x_part = result.get("solution")  # solución particular (libres = 0) si no inconsistent

    # Forma paramétrica si hay infinitas soluciones
    if status == "infinite":
        print("\n--- Familia de soluciones (forma paramétrica) ---")
        print(print_parametric_solution_from_rref(gj.matriz))

    # Verificación explícita x1 v1 + ... + xk vk = b con x_part
    if x_part is not None:
        y, steps = linear_combination_verification_steps(x_part, vecs, b_list)
        print("\n--- Verificación: x1·v1 + x2·v2 + ... + xk·vk = b (solución particular) ---")
        for line in steps:
            print("  ", line)
        print("\nx*  =", pretty_vector(x_part))
        print("A·x* =", pretty_vector(y))
        print("b    =", pretty_vector(b_list))

    # Conclusión
    if status == "unique":
        print("\nConclusión: b ES combinación lineal de {v1,...,vk} de forma ÚNICA.")
    elif status == "infinite":
        print("\nConclusión: b ES combinación lineal de {v1,...,vk} en INFINITAS formas (ver paramétrica).")
    else:
        print("\nConclusión: b NO es combinación lineal de {v1,...,vk}.")

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
        
# ======== NUEVO: Runner de cálculo de operaciones vectoriales ========

def _menu_vector_ops():
    print("\n--- Operaciones con vectores ---")
    print("[1] Suma: v + w")
    print("[2] Resta: v - w")
    print("[3] Escalamiento: c · v")
    print("[4] Combinación: c · u + d · v")
    print("[5] Combinación avanzada: u + c · v + d · w   (ej. u - 2v)")
    print("[6] Producto punto: v · w")
    print("[0] Volver")
    return input("Selecciona una opción: ").strip()

def run_vector_calc():
    """
    Permite escoger una operación y la resuelve mostrando el desarrollo.
    Usa parse_fraction para admitir fracciones (p. ej. 3/4, -5/2)
    y format_number para formatear resultados.
    """
    while True:
        opt = _menu_vector_ops()

        if opt == "0":
            print("Volviendo al menú de Vectores…")
            return

        # Dimensión para todas las operaciones
        try:
            n = _read_positive_int("Dimensión n: ")
        except Exception:
            continue

        if opt == "1":  # v + w
            v = read_vector(n, "Vector v")
            w = read_vector(n, "Vector w")
            r = v.add(w)
            print(f"\nv = {v}")
            print(f"w = {w}")
            print(f"v + w = {r}")

        elif opt == "2":  # v - w
            v = read_vector(n, "Vector v")
            w = read_vector(n, "Vector w")
            r = v.sub(w)
            print(f"\nv = {v}")
            print(f"w = {w}")
            print(f"v - w = {r}")

        elif opt == "3":  # c · v
            v = read_vector(n, "Vector v")
            c = _read_scalar("Escalar c: ")
            r = v.scale(c)
            print(f"\nv = {v}")
            print(f"c = {format_number(c)}")
            print(f"c · v = {r}")

        elif opt == "4":  # c · u + d · v
            u = read_vector(n, "Vector u")
            v = read_vector(n, "Vector v")
            c = _read_scalar("Escalar c: ")
            d = _read_scalar("Escalar d: ")
            r = u.scale(c).add(v.scale(d))
            print(f"\nu = {u}")
            print(f"v = {v}")
            print(f"c = {format_number(c)}, d = {format_number(d)}")
            print(f"c·u + d·v = {r}")

        elif opt == "5":  # u + c · v + d · w (ej.: u - 2v => c=-2, d=0)
            u = read_vector(n, "Vector u")
            v = read_vector(n, "Vector v")
            w = read_vector(n, "Vector w")
            c = _read_scalar("Escalar c (para v): ")
            d = _read_scalar("Escalar d (para w): ")
            r = u.add(v.scale(c)).add(w.scale(d))
            print(f"\nu = {u}")
            print(f"v = {v}")
            print(f"w = {w}")
            print(f"c = {format_number(c)}, d = {format_number(d)}")
            print(f"u + c·v + d·w = {r}")
            print("\nEjemplo: para u - 2v usa c = -2 y d = 0")

        elif opt == "6":  # v · w (producto punto)
            v = read_vector(n, "Vector v")
            w = read_vector(n, "Vector w")
            val = v.dot(w)
            terms = [f"{format_number(a)}·{format_number(b)}" for a, b in zip(v.data, w.data)]
            print(f"\nv = {v}")
            print(f"w = {w}")
            print("v · w =", " + ".join(terms), "=", format_number(val))

        else:
            print("Opción inválida. Intenta de nuevo.")
            continue

        input("\nPresiona Enter para continuar...")