""" Pequeño modulo para pedir tamaño de matriz """

def inputs_matrix() -> int :
    valid_values = set("0123456789")
    rows, cols = None
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
        except ValueError:
            print(ValueError)
    
    return int(rows, cols)