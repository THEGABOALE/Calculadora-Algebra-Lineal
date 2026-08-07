"""
ENTRADA Y SALIDA POR CONSOLA DE LOS MÉTODOS NUMÉRICOS

Estas ocho funciones vivían dentro de core/numeric/metodos_cerrados.py y
core/numeric/metodos_abiertos.py: eran la excepción a la regla de corte del
proyecto (core/ calcula, cli/ hace I/O), documentada como deuda conocida
porque venían así del código portado. Con la migración del motor a sympy se
mueven acá y la excepción deja de existir: core/numeric/ ya no tiene un solo
input() ni print().

Lo que quedó en core/ es sólo cálculo y validación. Estas funciones traducen
esas excepciones a mensajes de consola; no revalidan nada por su cuenta.
"""

from typing import Dict, List, Optional, Tuple

from core.numeric.metodos_cerrados import verificar_intervalo
from core.numeric._expresiones import compilar, evaluar

EJEMPLOS_FUNCIONES = (
    "  - x**2 - 4",
    "  - x**3 - 2*x - 5",
    "  - exp(x) - 3*x",
    "  - sin(x) - x/2",
)


# ---------------------------------------------------------------- salida ----

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


def imprimir_resultado_cerrado(resultado: Dict) -> None:
    """
    Imprime el resultado final de un método cerrado.
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


def imprimir_resultado_abierto(resultado: Dict) -> None:
    """
    Imprime el resultado final de un método abierto.
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


# ---------------------------------------------------------------- entrada ---

def solicitar_datos_metodo_cerrado() -> Tuple[str, float, float, float]:
    """
    Solicita al usuario los datos necesarios para los métodos cerrados.

    Retorna:
    - Tupla con (función, a, b, tolerancia)
    """
    print("\n--- Ingreso de datos ---")
    print("Ejemplos de funciones:")
    for ejemplo in EJEMPLOS_FUNCIONES:
        print(ejemplo)

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
                f, _, _ = compilar(f_str)
                fa = evaluar(f, a, f_str)
                fb = evaluar(f, b, f_str)
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
            tolerancia = float(input("Ingresa el error deseado (ej: 0.001): "))
            if tolerancia <= 0:
                print("Error: el error debe ser un valor positivo.")
                continue
            break
        except ValueError:
            print("Error: ingresa un número válido.")

    return f_str, a, b, tolerancia


def solicitar_datos_newton() -> Tuple[str, float, float, Optional[str]]:
    """
    Solicita datos para Newton-Raphson.

    Ya no se pregunta por la derivada como paso obligatorio: se deriva
    simbólicamente. Se sigue ofreciendo escribirla a mano para quien quiera
    forzar una.
    """
    print("\n--- Ingreso de datos para Newton-Raphson ---")
    print("Ejemplos de funciones:")
    for ejemplo in EJEMPLOS_FUNCIONES[:3]:
        print(ejemplo)

    f_str = input("\nIngresa la función f(x): ").strip()

    usar_derivada = input(
        "¿Deseas ingresar la derivada manualmente? (s/n, por defecto se deriva sola): "
    ).strip().lower()
    derivada = None
    if usar_derivada == 's':
        derivada = input("Ingresa f'(x): ").strip()

    while True:
        try:
            x0 = float(input("Ingresa el valor inicial x₀: "))
            break
        except ValueError:
            print("Error: ingresa un número válido.")

    while True:
        try:
            tolerancia = float(input("Ingresa el error deseado (ej: 0.001): "))
            if tolerancia <= 0:
                print("Error: el error debe ser positivo.")
                continue
            break
        except ValueError:
            print("Error: ingresa un número válido.")

    return f_str, x0, tolerancia, derivada


def solicitar_datos_secante() -> Tuple[str, float, float, float]:
    """
    Solicita datos para el método de la Secante.
    """
    print("\n--- Ingreso de datos para Método de la Secante ---")
    print("Ejemplos de funciones:")
    for ejemplo in EJEMPLOS_FUNCIONES[:3]:
        print(ejemplo)

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
            tolerancia = float(input("Ingresa el error deseado (ej: 0.001): "))
            if tolerancia <= 0:
                print("Error: el error debe ser positivo.")
                continue
            break
        except ValueError:
            print("Error: ingresa un número válido.")

    return f_str, x0, x1, tolerancia


__all__ = [
    "imprimir_tabla_iteraciones",
    "imprimir_resultado_cerrado",
    "imprimir_tabla_newton",
    "imprimir_tabla_secante",
    "imprimir_resultado_abierto",
    "solicitar_datos_metodo_cerrado",
    "solicitar_datos_newton",
    "solicitar_datos_secante",
]
