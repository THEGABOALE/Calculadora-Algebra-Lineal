"""
MÉTODOS ABIERTOS DE BÚSQUEDA DE RAÍCES
- Newton-Raphson
- Secante

Estos métodos no requieren intervalo, pero necesitan punto(s) inicial(es).
"""

import math
from typing import Callable, List, Dict, Optional

def evaluar_funcion(f_str: str, x: float) -> float:
    """
    Evalúa una función ingresada como string en un punto x.
    """
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
        f_str = f_str.replace('^', '**')
        return float(eval(f_str, {"__builtins__": {}}, safe_dict))
    except Exception as e:
        raise ValueError(f"Error al evaluar f(x) en x = {x}: {e}")


def calcular_derivada_numerica(f_str: str, x: float, h: float = 1e-8) -> float:
    """
    Calcula la derivada numérica usando diferencias centrales.
    f'(x) ≈ [f(x+h) - f(x-h)] / (2h)
    """
    try:
        f_mas = evaluar_funcion(f_str, x + h)
        f_menos = evaluar_funcion(f_str, x - h)
        return (f_mas - f_menos) / (2 * h)
    except Exception as e:
        raise ValueError(f"Error al calcular derivada en x = {x}: {e}")


def calcular_error_relativo(x_nuevo: float, x_viejo: float) -> float:
    """
    Calcula el error relativo porcentual.
    """
    if abs(x_nuevo) < 1e-15:
        return 0.0
    return abs((x_nuevo - x_viejo) / x_nuevo) * 100


def metodo_newton_raphson(f_str: str, x0: float, error_deseado: float, 
                          max_iter: int = 100, derivada_str: Optional[str] = None) -> Dict:
    """
    Método de Newton-Raphson para encontrar raíces.
    
    Fórmula: x_{n+1} = x_n - f(x_n)/f'(x_n)
    
    Parámetros:
    - f_str: función como string
    - x0: punto inicial
    - error_deseado: tolerancia del error relativo porcentual
    - max_iter: máximo número de iteraciones
    - derivada_str: derivada como string (si None, se calcula numéricamente)
    
    Retorna:
    - Dict con: raiz, iteraciones, historial, error_final
    """
    historial = []
    x_actual = x0
    error_actual = float('inf')
    
    for i in range(1, max_iter + 1):
        # Evaluar función
        fx = evaluar_funcion(f_str, x_actual)
        
        # Calcular derivada
        if derivada_str:
            dfx = evaluar_funcion(derivada_str, x_actual)
        else:
            dfx = calcular_derivada_numerica(f_str, x_actual)
        
        # Verificar que la derivada no sea cero
        if abs(dfx) < 1e-15:
            return {
                'raiz': x_actual,
                'iteraciones': i,
                'historial': historial,
                'error_final': error_actual,
                'metodo': 'Newton-Raphson',
                'advertencia': 'Derivada muy pequeña (cerca de cero)'
            }
        
        # Calcular siguiente aproximación
        x_nuevo = x_actual - fx / dfx
        
        # Calcular error relativo
        if i > 1:
            error_actual = calcular_error_relativo(x_nuevo, x_actual)
        else:
            error_actual = float('inf')
        
        # Guardar información
        historial.append({
            'iteracion': i,
            'x': x_actual,
            'f(x)': fx,
            "f'(x)": dfx,
            'x_nuevo': x_nuevo,
            'error': error_actual
        })
        
        # Verificar convergencia
        if error_actual < error_deseado and i > 1:
            return {
                'raiz': x_nuevo,
                'iteraciones': i,
                'historial': historial,
                'error_final': error_actual,
                'metodo': 'Newton-Raphson'
            }
        
        # Verificar si f(x) está muy cerca de cero
        if abs(fx) < 1e-15:
            return {
                'raiz': x_actual,
                'iteraciones': i,
                'historial': historial,
                'error_final': error_actual,
                'metodo': 'Newton-Raphson',
                'nota': 'f(x) ≈ 0 alcanzado'
            }
        
        x_actual = x_nuevo
    
    return {
        'raiz': x_nuevo,
        'iteraciones': max_iter,
        'historial': historial,
        'error_final': error_actual,
        'metodo': 'Newton-Raphson',
        'advertencia': 'Alcanzado número máximo de iteraciones'
    }


def metodo_secante(f_str: str, x0: float, x1: float, error_deseado: float, max_iter: int = 100) -> Dict:
    """
    Método de la Secante para encontrar raíces.
    
    Fórmula: x_{n+1} = x_n - f(x_n) * (x_n - x_{n-1}) / (f(x_n) - f(x_{n-1}))
    
    Parámetros:
    - f_str: función como string
    - x0: primer punto inicial
    - x1: segundo punto inicial
    - error_deseado: tolerancia del error relativo porcentual
    - max_iter: máximo número de iteraciones
    
    Retorna:
    - Dict con: raiz, iteraciones, historial, error_final
    """
    historial = []
    x_anterior = x0
    x_actual = x1
    error_actual = float('inf')
    
    for i in range(1, max_iter + 1):
        # Evaluar función en ambos puntos
        fx_anterior = evaluar_funcion(f_str, x_anterior)
        fx_actual = evaluar_funcion(f_str, x_actual)
        
        # Verificar que f(x_n) - f(x_{n-1}) no sea cero
        denominador = fx_actual - fx_anterior
        if abs(denominador) < 1e-15:
            return {
                'raiz': x_actual,
                'iteraciones': i,
                'historial': historial,
                'error_final': error_actual,
                'metodo': 'Secante',
                'advertencia': 'Denominador muy pequeño (f(x_n) ≈ f(x_{n-1}))'
            }
        
        # Calcular siguiente aproximación
        x_nuevo = x_actual - fx_actual * (x_actual - x_anterior) / denominador
        
        # Calcular error relativo
        if i > 1:
            error_actual = calcular_error_relativo(x_nuevo, x_actual)
        else:
            error_actual = float('inf')
        
        # Guardar información
        historial.append({
            'iteracion': i,
            'x_{n-1}': x_anterior,
            'x_n': x_actual,
            'f(x_{n-1})': fx_anterior,
            'f(x_n)': fx_actual,
            'x_{n+1}': x_nuevo,
            'error': error_actual
        })
        
        # Verificar convergencia
        if error_actual < error_deseado and i > 1:
            return {
                'raiz': x_nuevo,
                'iteraciones': i,
                'historial': historial,
                'error_final': error_actual,
                'metodo': 'Secante'
            }
        
        # Verificar si f(x) está muy cerca de cero
        if abs(fx_actual) < 1e-15:
            return {
                'raiz': x_actual,
                'iteraciones': i,
                'historial': historial,
                'error_final': error_actual,
                'metodo': 'Secante',
                'nota': 'f(x) ≈ 0 alcanzado'
            }
        
        # Actualizar para siguiente iteración
        x_anterior = x_actual
        x_actual = x_nuevo
    
    return {
        'raiz': x_nuevo,
        'iteraciones': max_iter,
        'historial': historial,
        'error_final': error_actual,
        'metodo': 'Secante',
        'advertencia': 'Alcanzado número máximo de iteraciones'
    }


def imprimir_tabla_newton(historial: List[Dict]) -> None:
    """
    Imprime tabla de iteraciones para Newton-Raphson.
    """
    print("\n" + "="*90)
    print(f"{'Iter':<6} {'x_n':<14} {'f(x_n)':<14} {'f\'(x_n)':<14} {'x_{n+1}':<14} {'Error %':<12}")
    print("="*90)
    
    for reg in historial:
        iter_num = reg['iteracion']
        x = reg['x']
        fx = reg['f(x)']
        dfx = reg["f'(x)"]
        x_nuevo = reg['x_nuevo']
        error = reg['error']
        
        error_str = "---" if error == float('inf') else f"{error:.6f}"
        
        print(f"{iter_num:<6} {x:<14.8f} {fx:<14.6e} {dfx:<14.6e} {x_nuevo:<14.8f} {error_str:<12}")
    
    print("="*90)


def imprimir_tabla_secante(historial: List[Dict]) -> None:
    """
    Imprime tabla de iteraciones para Secante.
    """
    print("\n" + "="*100)
    print(f"{'Iter':<6} {'x_{n-1}':<14} {'x_n':<14} {'f(x_n)':<14} {'x_{n+1}':<14} {'Error %':<12}")
    print("="*100)
    
    for reg in historial:
        iter_num = reg['iteracion']
        x_ant = reg['x_{n-1}']
        x_act = reg['x_n']
        fx_act = reg['f(x_n)']
        x_nuevo = reg['x_{n+1}']
        error = reg['error']
        
        error_str = "---" if error == float('inf') else f"{error:.6f}"
        
        print(f"{iter_num:<6} {x_ant:<14.8f} {x_act:<14.8f} {fx_act:<14.6e} {x_nuevo:<14.8f} {error_str:<12}")
    
    print("="*100)


def imprimir_resultado(resultado: Dict) -> None:
    """
    Imprime el resultado final del método.
    """
    print("\n" + "="*60)
    print(f"RESULTADO FINAL - Método: {resultado['metodo']}")
    print("="*60)
    print(f"Raíz aproximada: {resultado['raiz']:.10f}")
    print(f"Iteraciones totales: {resultado['iteraciones']}")
    print(f"Error relativo final: {resultado['error_final']:.6f}%")
    
    if 'advertencia' in resultado:
        print(f"\n⚠️  ADVERTENCIA: {resultado['advertencia']}")
    
    if 'nota' in resultado:
        print(f"\nℹ️  Nota: {resultado['nota']}")
    
    print("="*60)


def solicitar_datos_newton() -> tuple:
    """
    Solicita datos para Newton-Raphson.
    """
    print("\n--- Ingreso de datos para Newton-Raphson ---")
    print("Ejemplos de funciones:")
    print("  - x**2 - 4")
    print("  - x**3 - 2*x - 5")
    print("  - exp(x) - 3*x")
    
    f_str = input("\nIngresa la función f(x): ").strip()
    
    usar_derivada = input("¿Deseas ingresar la derivada manualmente? (s/n): ").strip().lower()
    derivada_str = None
    if usar_derivada == 's':
        derivada_str = input("Ingresa f'(x): ").strip()
        print("(Si la derivada es incorrecta, se usará aproximación numérica)")
    
    while True:
        try:
            x0 = float(input("Ingresa el valor inicial x₀: "))
            break
        except ValueError:
            print("Error: ingresa un número válido.")
    
    while True:
        try:
            error_deseado = float(input("Ingresa el error deseado (ej: 0.001): "))
            if error_deseado <= 0:
                print("Error: el error debe ser positivo.")
                continue
            break
        except ValueError:
            print("Error: ingresa un número válido.")
    
    return f_str, x0, error_deseado, derivada_str


def solicitar_datos_secante() -> tuple:
    """
    Solicita datos para el método de la Secante.
    """
    print("\n--- Ingreso de datos para Método de la Secante ---")
    print("Ejemplos de funciones:")
    print("  - x**2 - 4")
    print("  - x**3 - 2*x - 5")
    print("  - exp(x) - 3*x")
    
    f_str = input("\nIngresa la función f(x): ").strip()
    
    while True:
        try:
            x0 = float(input("Ingresa el primer valor inicial x₀: "))
            x1 = float(input("Ingresa el segundo valor inicial x₁: "))
            
            if x0 == x1:
                print("Error: x₀ y x₁ deben ser diferentes.")
                continue
            
            break
        except ValueError:
            print("Error: ingresa números válidos.")
    
    while True:
        try:
            error_deseado = float(input("Ingresa el error deseado (ej: 0.001): "))
            if error_deseado <= 0:
                print("Error: el error debe ser positivo.")
                continue
            break
        except ValueError:
            print("Error: ingresa un número válido.")
    
    return f_str, x0, x1, error_deseado