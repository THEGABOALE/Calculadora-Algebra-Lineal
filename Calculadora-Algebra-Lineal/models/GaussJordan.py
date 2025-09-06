import copy
from models.Matrix import Matrix

def imprimir_matriz(A):
    """Imprime la matriz aumentada"""
    for fila in A:
        print(" ".join(f"{valor:.3f}" for valor in fila))
    print() #línea en blanco

def gauss_jordan(matrix: Matrix):
    """
    Ejecuta el método de Gauss Jordan sobre la matriz aumentada.
    Muestra paso a paso cada una de las operaciones y retorna el conjunto solución.
    """
    
    A = copy.deepcopy(matrix.matriz)
    n = len(A)
    m = len(A[0])
    
    for i in range(n):
        pivote = A[i][i]
        if pivote == 0:
            raise ValueError(f"Pivote NULO en fila {i+1}, columna {i+1}. No se puede continuar.")
        
        #Normalizar la fila i
        for j in range(m):
            A[i][j] /= pivote
        print(f"F{i+1} -> F{i+1} / {pivote:.3f}")
        imprimir_matriz(A)
        
        #Eliminar la columna i en otras filas
        for k in range(n):
            if k != i:
                factor = A[k][i]
                for j in range(m):
                    A[k][j] -= factor * A[i][j]
                signo = "+" if factor < 0 else "-"
                print(f"F{k+1} -> F{k+1} {signo} {abs(factor):.3f}*F{i+1}")
                imprimir_matriz(A)
    
    #Conjunto Solución
    solucion = [A[i][-1] for i in range(n)]
    print("Conjunto Solución:")
    print(f"({', '.join(f'{val:.3f}' for val in solucion)})")
    
    return solucion
        