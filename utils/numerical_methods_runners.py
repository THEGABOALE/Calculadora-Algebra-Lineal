# numerical_methods_runners.py (corregido para importar módulos locales)

"""
RUNNERS PARA MÉTODOS NUMÉRICOS DE BÚSQUEDA DE RAÍCES

Funciones que conectan los métodos con el menú principal.
"""

from metodos_cerrados import (
    metodo_biseccion,
    metodo_regla_falsa,
    solicitar_datos_metodo_cerrado,
    imprimir_tabla_iteraciones,
    imprimir_resultado as imprimir_resultado_cerrado
)

from metodos_abiertos import (
    metodo_newton_raphson,
    metodo_secante,
    solicitar_datos_newton,
    solicitar_datos_secante,
    imprimir_tabla_newton,
    imprimir_tabla_secante,
    imprimir_resultado as imprimir_resultado_abierto
)


def run_biseccion():
    """
    Ejecuta el método de Bisección.
    """
    try:
        print("\n╔══════════════════════════════════════════╗")
        print("║      MÉTODO DE BISECCIÓN                 ║")
        print("╚══════════════════════════════════════════╝")
        
        # Solicitar datos
        f_str, a, b, error_deseado = solicitar_datos_metodo_cerrado()
        
        # Ejecutar método
        print("\nEjecutando método de Bisección...")
        resultado = metodo_biseccion(f_str, a, b, error_deseado)
        
        # Mostrar tabla de iteraciones
        print("\n📊 TABLA DE ITERACIONES:")
        imprimir_tabla_iteraciones(resultado['historial'])
        
        # Mostrar resultado final
        imprimir_resultado_cerrado(resultado)
        
        # Interpretación
        print("\n📝 INTERPRETACIÓN:")
        print(f"El método de Bisección encontró que la raíz de f(x) = {f_str}")
        print(f"está aproximadamente en x = {resultado['raiz']:.10f}")
        print(f"con un error relativo de {resultado['error_final']:.6f}%")
        print(f"después de {resultado['iteraciones']} iteraciones.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def run_regla_falsa():
    """
    Ejecuta el método de Regla Falsa.
    """
    try:
        print("\n╔══════════════════════════════════════════╗")
        print("║      MÉTODO DE REGLA FALSA               ║")
        print("╚══════════════════════════════════════════╝")
        
        # Solicitar datos
        f_str, a, b, error_deseado = solicitar_datos_metodo_cerrado()
        
        # Ejecutar método
        print("\nEjecutando método de Regla Falsa...")
        resultado = metodo_regla_falsa(f_str, a, b, error_deseado)
        
        # Mostrar tabla de iteraciones
        print("\n📊 TABLA DE ITERACIONES:")
        imprimir_tabla_iteraciones(resultado['historial'])
        
        # Mostrar resultado final
        imprimir_resultado_cerrado(resultado)
        
        # Interpretación
        print("\n📝 INTERPRETACIÓN:")
        print(f"El método de Regla Falsa encontró que la raíz de f(x) = {f_str}")
        print(f"está aproximadamente en x = {resultado['raiz']:.10f}")
        print(f"con un error relativo de {resultado['error_final']:.6f}%")
        print(f"después de {resultado['iteraciones']} iteraciones.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def run_newton_raphson():
    """
    Ejecuta el método de Newton-Raphson.
    """
    try:
        print("\n╔══════════════════════════════════════════╗")
        print("║      MÉTODO DE NEWTON-RAPHSON            ║")
        print("╚══════════════════════════════════════════╝")
        
        # Solicitar datos
        f_str, x0, error_deseado, derivada_str = solicitar_datos_newton()
        
        # Ejecutar método
        print("\nEjecutando método de Newton-Raphson...")
        resultado = metodo_newton_raphson(f_str, x0, error_deseado, derivada_str=derivada_str)
        
        # Mostrar tabla de iteraciones
        print("\n📊 TABLA DE ITERACIONES:")
        imprimir_tabla_newton(resultado['historial'])
        
        # Mostrar resultado final
        imprimir_resultado_abierto(resultado)
        
        # Interpretación
        print("\n📝 INTERPRETACIÓN:")
        print(f"El método de Newton-Raphson encontró que la raíz de f(x) = {f_str}")
        print(f"está aproximadamente en x = {resultado['raiz']:.10f}")
        print(f"con un error relativo de {resultado['error_final']:.6f}%")
        print(f"después de {resultado['iteraciones']} iteraciones.")
        if derivada_str:
            print("(Se usó la derivada proporcionada por el usuario)")
        else:
            print("(Se usó aproximación numérica de la derivada)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def run_secante():
    """
    Ejecuta el método de la Secante.
    """
    try:
        print("\n╔══════════════════════════════════════════╗")
        print("║      MÉTODO DE LA SECANTE                ║")
        print("╚══════════════════════════════════════════╝")
        
        # Solicitar datos
        f_str, x0, x1, error_deseado = solicitar_datos_secante()
        
        # Ejecutar método
        print("\nEjecutando método de la Secante...")
        resultado = metodo_secante(f_str, x0, x1, error_deseado)
        
        # Mostrar tabla de iteraciones
        print("\n📊 TABLA DE ITERACIONES:")
        imprimir_tabla_secante(resultado['historial'])
        
        # Mostrar resultado final
        imprimir_resultado_abierto(resultado)
        
        # Interpretación
        print("\n📝 INTERPRETACIÓN:")
        print(f"El método de la Secante encontró que la raíz de f(x) = {f_str}")
        print(f"está aproximadamente en x = {resultado['raiz']:.10f}")
        print(f"con un error relativo de {resultado['error_final']:.6f}%")
        print(f"después de {resultado['iteraciones']} iteraciones.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def metodos_cerrados_menu_loop():
    """
    Submenú para métodos cerrados.
    """
    def _pause(msg: str = "\nPresiona Enter para continuar..."):
        try:
            input(msg)
        except KeyboardInterrupt:
            pass
    
    while True:
        print("\n" + "="*50)
        print("        MÉTODOS CERRADOS")
        print("="*50)
        print("[1] Bisección")
        print("[2] Regla Falsa (False Position)")
        print("[0] Volver al menú anterior")
        print()
        
        opt = input("Selecciona una opción: ").strip()
        
        if opt in ("0", "volver", "back"):
            break
        elif opt == "1":
            run_biseccion()
            _pause()
        elif opt == "2":
            run_regla_falsa()
            _pause()
        else:
            print("Opción inválida. Intenta de nuevo.")
            _pause()


def metodos_abiertos_menu_loop():
    """
    Submenú para métodos abiertos.
    """
    def _pause(msg: str = "\nPresiona Enter para continuar..."):
        try:
            input(msg)
        except KeyboardInterrupt:
            pass
    
    while True:
        print("\n" + "="*50)
        print("        MÉTODOS ABIERTOS")
        print("="*50)
        print("[1] Newton-Raphson")
        print("[2] Secante")
        print("[0] Volver al menú anterior")
        print()
        
        opt = input("Selecciona una opción: ").strip()
        
        if opt in ("0", "volver", "back"):
            break
        elif opt == "1":
            run_newton_raphson()
            _pause()
        elif opt == "2":
            run_secante()
            _pause()
        else:
            print("Opción inválida. Intenta de nuevo.")
            _pause()


def metodos_numericos_menu_loop():
    """
    Menú principal de métodos numéricos (búsqueda de raíces).
    """
    def _pause(msg: str = "\nPresiona Enter para continuar..."):
        try:
            input(msg)
        except KeyboardInterrupt:
            pass
    
    while True:
        print("\n" + "="*50)
        print("   MÉTODOS NUMÉRICOS - BÚSQUEDA DE RAÍCES")
        print("="*50)
        print("[1] Métodos Cerrados ▸")
        print("    (Bisección, Regla Falsa)")
        print("[2] Métodos Abiertos ▸")
        print("    (Newton-Raphson, Secante)")
        print("[0] Volver al menú principal")
        print()
        
        opt = input("Selecciona una opción: ").strip()
        
        if opt in ("0", "volver", "back"):
            break
        elif opt == "1":
            metodos_cerrados_menu_loop()
        elif opt == "2":
            metodos_abiertos_menu_loop()
        else:
            print("Opción inválida. Intenta de nuevo.")
            _pause()


if __name__ == "__main__":
    # Ejecuta el menú principal si se llama directamente
    metodos_numericos_menu_loop()
