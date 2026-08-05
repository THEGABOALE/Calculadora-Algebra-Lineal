"""
RUNNERS INTERACTIVOS DE LOS MÉTODOS

Propósito:
- Pedir A y b por consola, ejecutar el método correspondiente del motor
  (core.*) e imprimir proceso y resumen con utils.printMethods.

Notas de diseño:
- Estos runners vivían al final de models/GaussJordan.py, models/GaussMethod.py
  y models/CramerMethod.py. Se movieron aquí para que core/ quede sin I/O y
  pueda ser consumido igual por el CLI y por las vistas de Django.
- La lógica no cambió: es el mismo cuerpo de función.
"""

from core.cramer import CramerMethod
from core.gauss import GaussMethod
from core.gauss_jordan import GaussJordanMethod
from core.matrix import Matrix
from cli.inputsmatrix import inputs_matrix, make_equation
from utils.display import mostrar_sistema_ecuaciones
from utils.printMethods import print_frame, print_summary, print_equation

from typing import List, Optional


def run_gauss_jordan() -> None:
    """Runner interactivo: pide A y b, ejecuta Gauss–Jordan y muestra proceso + resumen."""
    rows, cols = inputs_matrix()
    matriz, vector = make_equation(rows, cols)

    # Mostrar sistema ingresado (formato algebraico)
    print(print_equation(matriz, vector))

    # Ejecutar Gauss-Jordan con logs
    gj = GaussJordanMethod(matriz, vector)
    gj.run()
    results = gj.solve_and_log()

    # Imprimir proceso y resumen
    print_frame(gj.frame)
    print(print_equation(matriz, vector))
    print_summary(results)


def run_gauss():
    rows, cols = inputs_matrix()

    matriz, vector = make_equation(rows, cols)
    print(print_equation(matriz, vector))
    gauss = GaussMethod(matriz, vector)
    # Contrato de dos pasos, igual que run_gauss_jordan: primero se elimina,
    # después se analiza. solve_and_log() ya no re-elimina por su cuenta.
    gauss.gauss_method()
    results = gauss.solve_and_log()

    print_frame(gauss.frame)
    print(print_equation(matriz, vector))
    print_summary(results)


def run_crammer():
    rows, cols = inputs_matrix()

    matrix, vector = make_equation(rows, cols)
    print(print_equation(matrix, vector))

    if rows != cols:
        print("Error: Cramer solo acepta sistemas cuadrados (mismo número de ecuaciones y variables).")
        return

    crammer = CramerMethod(matrix, vector)
    result = crammer.solve()

    print_frame(crammer.frame)
    print(print_equation(matrix, vector))
    print_summary(result)


def mostrar_sistema_desde_input(
    cntFilas: int,
    cntColums: int,
    nombres_vars: Optional[List[str]] = None,  # mantenido por compatibilidad (no usado aquí)
    mostrar_matriz: bool = True,
) -> None:
    """Conveniencia: pide A y b (make_equation) y muestra el sistema."""
    matriz, vector = make_equation(cntFilas, cntColums)
    A = Matrix(matriz)
    mostrar_sistema_ecuaciones(A, vector, nombres_vars, mostrar_matriz)


__all__ = [
    'run_gauss_jordan',
    'run_gauss',
    'run_crammer',
    'mostrar_sistema_desde_input',
]
