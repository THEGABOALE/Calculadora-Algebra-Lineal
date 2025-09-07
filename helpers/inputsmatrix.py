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

__all__ = ['inputs_matrix']