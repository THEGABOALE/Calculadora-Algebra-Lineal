from __future__ import annotations
from typing import List
from models.Vector import Vector
from models.Matrix import Matrix
from models.GaussJordan import GaussJordanMethod
from utils.vector_tools import (
    read_vector, read_vectors, verify_vector_properties,
    matrix_vector_product_steps, pretty_linear_comb
)
from utils.printMethods import print_frame, print_summary, print_equation
from helpers.inputsmatrix import inputs_matrix
from utils.EquationFunctions import format_number

# -------- Runner 1: Propiedades de vectores --------
def run_vector_props():
    print("\n--- Propiedades algebraicas en R^n ---")
    n = int(input("Dimensión n del espacio: ").strip())
    v = read_vector(n, "Vector v")
    w = read_vector(n, "Vector w")
    u = read_vector(n, "Vector u")
    c = float(input("Escalar c: ").strip())
    d = float(input("Escalar d: ").strip())

    results = verify_vector_properties(v, w, u, c, d)
    print("\nResultados:")
    for name, ok, detail in results:
        print(f" - {name}: {'✔' if ok else '✘'}")
        print(f"   {detail}")

# -------- Runner 2: Combinación lineal / Ecuación vectorial --------
def run_vector_combination():
    """
    Pide k vectores v_i en R^m y un vector objetivo b, construye [v1 ... vk | b]
    y resuelve c1..ck con Gauss–Jordan. Muestra el frame y el resumen.
    """
    print("\n--- Combinación lineal / Ecuación vectorial ---")
    m = int(input("Dimensión de los vectores (m): ").strip())
    k = int(input("Cantidad de vectores disponibles (k): ").strip())

    print("\nIngresa los vectores columna v1..vk:")
    vecs = read_vectors(k, m, prefix="v")
    print("\nVector objetivo b:")
    b = read_vector(m)

    # Construir A con v_i como columnas
    A = [[vecs[j].data[i] for j in range(k)] for i in range(m)]
    b_list = b.data[:]

    # Mostrar planteo
    print("\nPlanteo:  A·c = b  con  A = [v1 v2 ... vk]")
    print("Combinación:", pretty_linear_comb([0]*k, vecs).replace("0", "c"))  # c1·v1 + c2·v2 + ...
    print(print_equation(A, b_list))

    gj = GaussJordanMethod(A, b_list)
    gj.run()
    result = gj.solve_and_log()

    print_frame(gj.frame)
    print(print_equation(A, b_list))
    print_summary(result)

# -------- Runner 3: Producto Ax con regla fila–vector --------
def run_matrix_times_vector():
    """
    Pide A (m×n) y x (n) y muestra Ax con el desarrollo fila–vector.
    """
    print("\n--- Producto Ax por regla fila–vector ---")
    rows, cols = inputs_matrix()
    A, _ = Matrix.make_equation(rows, cols)  # solo A (ignora b leído por la función)
    x = read_vector(cols, "Vector x:")

    y, steps = matrix_vector_product_steps(A, x)
    print("\nA x =")
    for line in steps:
        print("  ", line)
    print("\nResultado Ax =", Vector(y))
