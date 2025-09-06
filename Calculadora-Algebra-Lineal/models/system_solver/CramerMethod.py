from typing import Dict, Union 

def Cramer2x2  (A:list[list[float]], B: list[float]) -> Dict[str, Union[str, list[float], None]]:    
    
    
    # Este metodo resuelve un sistema 2x2 con el metodo Cramer. 
    #El sistema es: 
    # a11*x + a12*y = b1
    # a21*x + a22*y = b2

    # Caracteristicas: 
    # A: Matriz 2x2 de elementos
    # B: Terminos independientes (Longitud max 2)

# ALT 691 = │(Esto fue a lo random la verdad.)
# ALT 961 = ö(Delta minuscula, el mayuscula ni p### idea)
    # Resulado: 
    # "Status: "Unica solucion" │ "Sin solucion" │ "Infinitas soluciones"│
    # Solucion: [x, y] o None, 

    # det (Determinante): ö, 
    # det_x: öx 
    # det_y: öy 

    a11, a12 = A[0]
    a21, a22 = A[1]
    b1,b2 = B

    det = a11*a22 - a12*a21
    det_X = b1*a22 - a12*b2
    det_Y = a11*b2 - b1*a21
    if abs(det) < 1e-12: # Lo de que ö = 0 para soluciones infinitas
        if abs(det_X) < 1e-12 and abs(det_Y) < 1e-12:
            estado = "Initas soluciones" 
            solucion = None
        else: estado = "Sin solucion" # Matriz inconsistente 

    else:  
        estado = "Unica Solucion"
        solucion = [det/det_X , det_Y/det]

        
    return{
        "Estado": estado, 
        "Solucion":  solucion,
        "det": det, 
        "det_x": det_X,
        "det_y": det_Y
}

A = [[2,1], 
    [5,3]]
B = [8,18]

resultado = Cramer2x2(A,B)
print(resultado)