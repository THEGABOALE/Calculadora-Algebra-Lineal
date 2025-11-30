"""
MÉTODOS CERRADOS DE BÚSQUEDA DE RAÍCES
- Bisección
- Regla Falsa (False Position)

Ambos métodos requieren un intervalo [a,b] donde f(a)·f(b) < 0
"""

import math
from typing import Callable, Tuple, List, Dict, Optional

def evaluar_funcion(f_str: str, x: float) -> float:
    """
    Evalúa una función ingresada como string en un punto x.
    Soporta funciones matemáticas comunes.
    """
    # Crear un entorno seguro con funciones matemáticas
    safe_dict = {
        'x': x,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'exp': math.exp,
        'log': math.log,
        'log10': math.log10,
        'sqrt': math.sqrt,
        'abs': abs,
        'pi': math.pi,
        'e': math.e,
    }
    try:
        # Reemplazar ^ por ** para potencias
        f_str = f_str.replace('^', '**')
        return float(eval(f_str, {"__builtins__": {}}, safe_dict))
    except Exception as e:
        raise ValueError(f"Error al evaluar f(x) = {f_str} en x = {x}: {e}")


def verificar_intervalo(f_str: str, a: float, b: float) -> bool:
    """
    Verifica que f(a) · f(b) < 0 (cambio de signo en el intervalo).
    """
    try:
        fa = evaluar_funcion(f_str, a)
        fb = evaluar_funcion(f_str, b)
        return fa * fb < 0
    except Exception:
        return False


def calcular_error_relativo(x_nuevo: float, x_viejo: float) -> float:
    """
    Calcula el error relativo porcentual entre dos aproximaciones.
    Error = |x_nuevo - x_viejo| / |x_nuevo| * 100
    """
    if abs(x_nuevo) < 1e-15:  # Evitar división por cero
        return 0.0
    return abs((x_nuevo - x_viejo) / x_nuevo) * 100


def metodo_biseccion(f_str: str, a: float, b: float, error_deseado: float, max_iter: int = 100) -> Dict:
    """
    Método de Bisección para encontrar raíces.
    
    Parámetros:
    - f_str: función como string (ej: "x**2 - 4")
    - a: límite inferior del intervalo
    - b: límite superior del intervalo
    - error_deseado: tolerancia del error relativo porcentual
    - max_iter: máximo número de iteraciones
    
    Retorna:
    - Dict con: raiz, iteraciones, historial, error_final, intervalo_final
    """
    # Verificar condición inicial
    if not verificar_intervalo(f_str, a, b):
        raise ValueError("El intervalo no es válido: f(a)·f(b) debe ser < 0")
    
    historial = []
    xr_anterior = a  # Inicializar para el cálculo del error
    error_actual = float('inf')
    
    for i in range(1, max_iter + 1):
        # Calcular punto medio
        xr = (a + b) / 2.0
        fxr = evaluar_funcion(f_str, xr)
        
        # Calcular error relativo
        if i > 1:
            error_actual = calcular_error_relativo(xr, xr_anterior)
        else:
            error_actual = float('inf')
        
        # Evaluar en los extremos
        fa = evaluar_funcion(f_str, a)
        fb = evaluar_funcion(f_str, b)
        
        # Guardar información de la iteración
        historial.append({
            'iteracion': i,
            'a': a,
            'b': b,
            'xr': xr,
            'f(xr)': fxr,
            'error': error_actual
        })
        
        # Verificar convergencia
        if error_actual < error_deseado and i > 1:
            return {
                'raiz': xr,
                'iteraciones': i,
                'historial': historial,
                'error_final': error_actual,
                'intervalo_final': (a, b),
                'metodo': 'Bisección'
            }
        
        # Actualizar intervalo
        if fa * fxr < 0:
            b = xr
        else:
            a = xr
        
        xr_anterior = xr
    
    # Si no convergió en max_iter
    return {
        'raiz': xr,
        'iteraciones': max_iter,
        'historial': historial,
        'error_final': error_actual,
        'intervalo_final': (a, b),
        'metodo': 'Bisección',
        'advertencia': 'Alcanzado número máximo de iteraciones'
    }


def metodo_regla_falsa(f_str: str, a: float, b: float, error_deseado: float, max_iter: int = 100) -> Dict:
    """
    Método de Regla Falsa (False Position) para encontrar raíces.
    
    Parámetros:
    - f_str: función como string (ej: "x**2 - 4")
    - a: límite inferior del intervalo
    - b: límite superior del intervalo
    - error_deseado: tolerancia del error relativo porcentual
    - max_iter: máximo número de iteraciones
    
    Retorna:
    - Dict con: raiz, iteraciones, historial, error_final, intervalo_final
    """
    # Verificar condición inicial
    if not verificar_intervalo(f_str, a, b):
        raise ValueError("El intervalo no es válido: f(a)·f(b) debe ser < 0")
    
    historial = []
    xr_anterior = a  # Inicializar para el cálculo del error
    error_actual = float('inf')
    
    for i in range(1, max_iter + 1):
        # Evaluar función en extremos
        fa = evaluar_funcion(f_str, a)
        fb = evaluar_funcion(f_str, b)
        
        # Calcular punto de intersección (regla falsa)
        xr = b - (fb * (b - a)) / (fb - fa)
        fxr = evaluar_funcion(f_str, xr)
        
        # Calcular error relativo
        if i > 1:
            error_actual = calcular_error_relativo(xr, xr_anterior)
        else:
            error_actual = float('inf')
        
        # Guardar información de la iteración
        historial.append({
            'iteracion': i,
            'a': a,
            'b': b,
            'xr': xr,
            'f(xr)': fxr,
            'error': error_actual
        })
        
        # Verificar convergencia
        if error_actual < error_deseado and i > 1:
            return {
                'raiz': xr,
                'iteraciones': i,
                'historial': historial,
                'error_final': error_actual,
                'intervalo_final': (a, b),
                'metodo': 'Regla Falsa'
            }
        
        # Actualizar intervalo
        if fa * fxr < 0:
            b = xr
        else:
            a = xr
        
        xr_anterior = xr
    
    # Si no convergió en max_iter
    return {
        'raiz': xr,
        'iteraciones': max_iter,
        'historial': historial,
        'error_final': error_actual,
        'intervalo_final': (a, b),
        'metodo': 'Regla Falsa',
        'advertencia': 'Alcanzado número máximo de iteraciones'
    }


def imprimir_tabla_iteraciones(historial: List[Dict]) -> None:
    """
    Imprime una tabla formateada con el historial de iteraciones.
    """
    print("\n" + "="*90)
    print(f"{'Iter':<6} {'a':<12} {'b':<12} {'xr':<12} {'f(xr)':<12} {'Error %':<12}")
    print("="*90)
    
    for registro in historial:
        iter_num = registro['iteracion']
        a = registro['a']
        b = registro['b']
        xr = registro['xr']
        fxr = registro['f(xr)']
        error = registro['error']
        
        # Formatear error
        if error == float('inf'):
            error_str = "---"
        else:
            error_str = f"{error:.6f}"
        
        print(f"{iter_num:<6} {a:<12.6f} {b:<12.6f} {xr:<12.6f} {fxr:<12.6e} {error_str:<12}")
    
    print("="*90)


def imprimir_resultado(resultado: Dict) -> None:
    """
    Imprime el resultado final del método de manera clara.
    """
    print("\n" + "="*60)
    print(f"RESULTADO FINAL - Método: {resultado['metodo']}")
    print("="*60)
    print(f"Raíz aproximada: {resultado['raiz']:.10f}")
    print(f"Iteraciones totales: {resultado['iteraciones']}")
    print(f"Error relativo final: {resultado['error_final']:.6f}%")
    
    a_final, b_final = resultado['intervalo_final']
    print(f"Intervalo final: [{a_final:.6f}, {b_final:.6f}]")
    
    if 'advertencia' in resultado:
        print(f"\n⚠️  ADVERTENCIA: {resultado['advertencia']}")
    
    print("="*60)


# Función de entrada para solicitar datos al usuario
def solicitar_datos_metodo_cerrado() -> Tuple[str, float, float, float]:
    """
    Solicita al usuario los datos necesarios para los métodos cerrados.
    
    Retorna:
    - Tupla con (función, a, b, error_deseado)
    """
    print("\n--- Ingreso de datos ---")
    print("Ejemplos de funciones:")
    print("  - x**2 - 4")
    print("  - x**3 - 2*x - 5")
    print("  - exp(x) - 3*x")
    print("  - sin(x) - x/2")
    
    f_str = input("\nIngresa la función f(x): ").strip()
    
    while True:
        try:
            a = float(input("Ingresa el límite inferior a: "))
            b = float(input("Ingresa el límite superior b: "))
            
            if a >= b:
                print("Error: el límite inferior debe ser menor que el superior.")
                continue
            
            # Verificar que el intervalo sea válido
            if not verificar_intervalo(f_str, a, b):
                print(f"\n⚠️  El intervalo [{a}, {b}] no es válido.")
                print("   f(a)·f(b) debe ser < 0 (debe haber cambio de signo)")
                fa = evaluar_funcion(f_str, a)
                fb = evaluar_funcion(f_str, b)
                print(f"   f({a}) = {fa:.6f}")
                print(f"   f({b}) = {fb:.6f}")
                print(f"   f(a)·f(b) = {fa*fb:.6f}")
                
                continuar = input("\n¿Deseas ingresar otro intervalo? (s/n): ").strip().lower()
                if continuar != 's':
                    raise ValueError("Intervalo no válido")
                continue
            
            break
            
        except ValueError as e:
            print(f"Error: {e}. Intenta nuevamente.")
    
    while True:
        try:
            error_deseado = float(input("Ingresa el error deseado (ej: 0.001): "))
            if error_deseado <= 0:
                print("Error: el error debe ser un valor positivo.")
                continue
            break
        except ValueError:
            print("Error: ingresa un número válido.")
    
    return f_str, a, b, error_deseado