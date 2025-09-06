from models.Matrix import Matrix

def mostrar_sistema_ecuaciones(matrix: Matrix):
    """Muestra el sistema de ecuaciones de manera algebraica"""
    print("\nSistema de ecuaciones ingresado:")
    for i, fila in enumerate(matrix.matriz):
        terms = []
        for j in range(len(fila) - 1):
            coef = fila[j]
            if coef == 0:
                continue
            elif coef == 1:
                terms.append(f"x{j+1}")
            elif coef == -1:
                terms.append(f"-x{j+1}")
            else:
                terms.append(f"{coef}*x{j+1}")
            ecuacion = " + ".join(terms)
            ecuacion += f" = {fila[-1]}"
        print(ecuacion)

