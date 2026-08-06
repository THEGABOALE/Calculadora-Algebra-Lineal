""" Entrada interactiva: tamaño de la matriz y captura de A y b.

Aquí vive todo lo que pide datos por consola. `make_matrix` y `make_equation`
estaban antes como staticmethods de Matrix; se movieron para que core.matrix
quede sin I/O.
"""

from utils.EquationFunctions import parse_fraction

def inputs_matrix() -> tuple[int, int]:
    valid_values = set("0123456789")
    while True:
        try:
            print("Ingrese la cantidad de ecuaciones: ")
            rows = input(" -> ")
            if not all(char in valid_values for char in rows):
                raise ValueError("La entrada es invalida, intente nuevamente...")
            print("Ingrese la cantidad de variables: ")
            cols = input(" -> ")
            if not all(char in valid_values for char in cols):
                raise ValueError("La entrada es invalida, intente nuevamente...")
            break
        except ValueError as e:
            print(e)
    return int(rows), int(cols)

# --- NUEVO: leer SOLO una matriz A (sin pedir b) ---
def read_matrix_only(rows: int, cols: int) -> list[list[float]]:
    """
    Lee una matriz de tamaño rows x cols pidiendo solo los coeficientes.
    Acepta fracciones tipo '3/4' o decimales.
    No modifica nada del flujo de inputs_matrix.
    """
    A: list[list[float]] = []
    for i in range(rows):
        while True:
            raw = input(f"Ingrese {cols} valores para la fila {i+1}: ").strip().split()
            if len(raw) != cols:
                print(f"Se esperaban {cols} valores. Intenta de nuevo.")
                continue
            try:
                row = [parse_fraction(x) for x in raw]
                A.append(row)
                break
            except Exception as e:
                print(f"Entrada inválida ({e}). Intenta de nuevo.")
    return A

def make_matrix(cntFilas: int, cntColums: int) -> list[list[float]]:
    matriz = []
    valid_values = set("0123456789.-/ ")
    for fila in range(cntFilas):
        while True:
            try:
                print(f"Ingrese {cntColums} valores para la fila {fila+1}: ")
                inputs = input(" -> ")
                ''' Validar las entradas usando valid_values '''
                if not all(char in valid_values for char in inputs):
                    raise ValueError("La entrada es inválida, ingrese los valores correctamente...")

                content = list(map(parse_fraction, inputs.split()))

                ''' Verificar la cantidd de numeros ingresados por fila '''
                if len(content) != cntColums:
                    raise ValueError(f"Introduce {cntColums} en total, intente nuevamente...")
                matriz.append(content)
                break
            except ValueError:
                print(ValueError)
    return matriz

def make_equation(cntFilas: int, cntColums: int):
    matriz = []
    vector = []
    valid_values = set("0123456789.-/ ")

    for fila in range(cntFilas):
        while True:
            try:
                print(f"Ingrese {cntColums} valores para la fila {fila+1}: ")
                inputs = input(" -> ")
                if not all(char in valid_values for char in inputs):
                    raise ValueError("La entrada es inválida, intente nuvamente...")
                content = list(map(parse_fraction, inputs.split()))
                if len(content) != cntColums:
                    raise ValueError(f"Introduce {cntColums} valores en total...")
                matriz.append(content)
                break
            except ValueError:
                print(ValueError)

        while True:
            try:
                eq = parse_fraction(input(f"Ingrese la equivalencia para la fila {fila+1}: "))
                vector.append(eq)
                break
            except ValueError:
                print(ValueError)
    return matriz, vector

__all__ = ['inputs_matrix', 'make_matrix', 'make_equation', 'read_matrix_only']