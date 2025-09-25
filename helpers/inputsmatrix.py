""" Pequeño modulo para pedir tamaño de matriz """

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
    # import local para no tocar cabecera ni crear dependencias globales
    from utils.EquationFunctions import parse_fraction

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


__all__ = ['inputs_matrix', 'read_matriz_only']