from models.Matrix import Matrix
from utils.display import mostrar_sistema_ecuaciones
from models.GaussJordan import gauss_jordan
from models.GaussMethod import GaussMethod
from utils.printMethods import print_frame, print_equation, print_summary

def main():
    #matriz_lista = Matrix.make_matrix(3, 3)
    #matriz = Matrix(matriz_lista)
    #gauss = GaussMethod(matriz_lista)
    #gauss.gauss_method()
    #print_frame(gauss.frame)
    matriz, vector = Matrix.make_equation(3, 3)
    print(print_equation(matriz, vector))
    gauss = GaussMethod(matriz, vector)
    results = gauss.solve_and_log()
    
    print_frame(gauss.frame)
    print(print_equation(matriz, vector))
    print_summary(results)
    
if __name__ == "__main__":
    main()