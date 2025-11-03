"""
STARTUP / MENÚ INTERACTIVO

Propósito
- Menú visual para métodos con matrices (Gauss—Jordan, Gauss, Cramer, ver A|b).
- Submenú para VECTORES (propiedades, combinación lineal, producto Ax).
- Submenú para CRAMER (resolver sistema, calcular determinantes).

Notas
- Sin dependencias externas; colores ANSI solo si stdout es TTY y NO_COLOR no está definido.
- Cada acción delega en un "runner" ya existente.
"""

# Importaciones desde models
from models.CramerMethod import run_cramer, CramerMethod
from models.GaussMethod import run_gauss
from models.GaussJordan import run_gauss_jordan
from utils.display import mostrar_sistema_desde_input
from helpers.inputsmatrix import inputs_matrix
from utils.printMethods import (
    print_frame,
    format_matrix,
    compare_determinant_methods
)

# Submenú: runners de VECTORES
from utils.vector_runners import (
    run_vector_props,
    run_vector_combination,
    run_matrix_times_vector,
    run_vector_calc, 
)

from utils.matrix_runners import matrices_menu_loop

# ---------------------------
# Utilidades de UI
# ---------------------------
def _pause(msg: str = "\nPresiona Enter para continuar..."):
    """Pausa la consola para que el usuario lea la salida antes de volver al menú."""
    try:
        input(msg)
    except KeyboardInterrupt:
        pass

def _run_display_only():
    """Pide filas/columnas y muestra A|b + ecuaciones sin resolver."""
    rows, cols = inputs_matrix()
    mostrar_sistema_desde_input(rows, cols)
    _pause()

def _colors_enabled() -> bool:
    """Habilita color solo si la salida es TTY y el usuario no desactiva con NO_COLOR."""
    import os, sys
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")

def print_header(title: str = "CALCULADORA DE ÁLGEBRA LINEAL"):
    """Cabecera visual del programa (cuadro Unicode con color ANSI opcional)."""
    import shutil
    use_color = _colors_enabled()
    def C(code): return f"\033[{code}m" if use_color else ""
    RESET = C("0"); BOLD = C("1")
    CYAN  = C("96"); WHITE = C("97")

    term_w = shutil.get_terminal_size(fallback=(80, 20)).columns
    inner_w = max(len(title) + 10, 48)  # ancho mínimo cómodo
    box_w = min(inner_w, term_w - 6)    # deja margen lateral

    TL, TR, BL, BR, H, V = "╔", "╗", "╚", "╝", "═", "║"
    top    = CYAN + BOLD + TL + (H * box_w) + TR + RESET
    empty  = CYAN + V + RESET + " " * box_w + CYAN + V + RESET
    middle = (CYAN + V + RESET + BOLD + WHITE + title.center(box_w) + RESET + CYAN + V + RESET)
    bottom = CYAN + BOLD + BL + (H * box_w) + BR + RESET

    print()
    print(top); print(empty); print(middle); print(empty); print(bottom)
    print()

# ---------------------------
# Menú principal
# ---------------------------
def _print_main_menu():
    """Lista de opciones del menú principal."""
    use_color = _colors_enabled()
    def C(c): return f"\033[{c}m" if use_color else ""
    RESET=C("0"); BOLD=C("1"); WHITE=C("97"); MAG=C("95")

    items = [
        ("1", "Forma Escalonada Reducida (Gauss—Jordan)"),
        ("2", "Forma Escalonada (Gauss)"),
        ("3", "Regla de Cramer ▸"),
        ("4", "Mostrar solo el sistema (A | b)"),
        ("5", "Vectores ▸"),
        ("6", "Matrices"),
        ("0", "Salir"),
    ]
    for k, label in items:
        print(f"{MAG}{BOLD}[{k}]{RESET} {WHITE}{label}{RESET}")

# ---------------------------
# Submenú CRAMER
# ---------------------------
def _print_cramer_menu():
    """Opciones del submenú de Cramer."""
    use_color = _colors_enabled()
    def C(c): return f"\033[{c}m" if use_color else ""
    RESET=C("0"); BOLD=C("1"); WHITE=C("97"); MAG=C("95"); CYAN=C("96")

    print_header("REGLA DE CRAMER Y DETERMINANTES")
    items = [
        ("1", "Resolver sistema con Regla de Cramer"),
        ("2", "Calcular Determinante"),
        ("", "    " + CYAN + "• Método de Cramer (básico)" + RESET),
        ("", "    " + CYAN + "• Regla de Sarrus (3×3)" + RESET),
        ("", "    " + CYAN + "• Expansión por Cofactores (cualquier n×n)" + RESET),
        ("", "    " + CYAN + "• Comparar todos los métodos (3×3)" + RESET),
        ("0", "Volver"),
    ]
    for k, label in items:
        if k:
            print(f"{MAG}{BOLD}[{k}]{RESET} {WHITE}{label}{RESET}")
        else:
            print(f"{label}")
    print()

def _run_determinant_calculator():
    """Ejecuta el calculador de determinantes con menú interactivo."""
    use_color = _colors_enabled()
    def C(c): return f"\033[{c}m" if use_color else ""
    RESET=C("0"); BOLD=C("1"); WHITE=C("97"); MAG=C("95")
    
    while True:
        print_header("MÉTODOS PARA CALCULAR DETERMINANTES")
        
        items = [
            ("1", "Método de Cramer (básico)"),
            ("2", "Regla de Sarrus (solo 3×3)"),
            ("3", "Expansión por Cofactores (cualquier n×n)"),
            ("4", "Comparar todos los métodos (solo 3×3)"),
            ("0", "Volver"),
        ]
        for k, label in items:
            print(f"{MAG}{BOLD}[{k}]{RESET} {WHITE}{label}{RESET}")
        print()
        
        try:
            opcion = input("Selecciona una opción: ").strip()
            
            if opcion == "0":
                break
            
            if opcion not in ["1", "2", "3", "4"]:
                print("⚠ Opción no válida. Intente nuevamente.")
                _pause()
                continue
            
            # Solicitar tamaño de matriz
            print("\n" + "═" * 50)
            print("INGRESO DE MATRIZ")
            print("═" * 50)
            n = int(input("Ingrese el tamaño de la matriz (n×n): "))
            
            if n < 1:
                print("Error: El tamaño debe ser al menos 1×1")
                _pause()
                continue
            
            # Validar método según tamaño
            if opcion == "2" and n != 3:
                print(f"\n⚠ Error: La Regla de Sarrus solo aplica para matrices 3×3")
                print(f"Su matriz es {n}×{n}. Use otro método.")
                _pause()
                continue
            
            if opcion == "4" and n != 3:
                print(f"\n⚠ Error: La comparación de métodos solo está disponible para matrices 3×3")
                print(f"Su matriz es {n}×{n}.")
                _pause()
                continue
            
            # Ingresar elementos de la matriz
            print(f"\nIngrese los elementos de la matriz {n}×{n}:")
            matrix = []
            for i in range(n):
                while True:
                    try:
                        row_str = input(f"Fila {i+1} (separada por espacios): ")
                        row = [float(x) for x in row_str.split()]
                        if len(row) != n:
                            print(f"Error: Debe ingresar exactamente {n} elementos")
                            continue
                        matrix.append(row)
                        break
                    except ValueError:
                        print("Error: Ingrese solo números válidos")
            
            print("\nMatriz ingresada:")
            print(format_matrix(matrix))
            
            # Crear vector b dummy (solo para instanciar CramerMethod)
            vector_b = [0.0] * n
            cramer_obj = CramerMethod(matrix, vector_b)
            
            # Ejecutar método seleccionado
            if opcion == "1":
                # Método de Cramer (básico)
                print("\n" + "═" * 60)
                print("MÉTODO: CRAMER (BÁSICO)")
                print("═" * 60)
                det = cramer_obj.calculate_determinant(matrix, show_sarrus=False)
                print(f"\n{BOLD}Determinante: {det}{RESET}")
                print("═" * 60)
                
            elif opcion == "2":
                # Regla de Sarrus
                print("\n" + "═" * 60)
                print("MÉTODO: REGLA DE SARRUS (3×3)")
                print("═" * 60)
                cramer_obj.frame = {}
                det = cramer_obj.calculate_determinant_sarrus(matrix)
                print("\nPASOS DETALLADOS:")
                print_frame(cramer_obj.frame, show_det=False)
                print(f"\n{BOLD}Determinante final: {det}{RESET}")
                print("═" * 60)
                
            elif opcion == "3":
                # Expansión por Cofactores
                print("\n" + "═" * 60)
                print("MÉTODO: EXPANSIÓN POR COFACTORES")
                print("═" * 60)
                cramer_obj.frame = {}
                det = cramer_obj.calculate_determinant_cofactors(matrix)
                print("\nPASOS DETALLADOS:")
                print_frame(cramer_obj.frame, show_det=False)
                print(f"\n{BOLD}Determinante final: {det}{RESET}")
                print("═" * 60)
                
            elif opcion == "4":
                # Comparar todos los métodos
                compare_determinant_methods(cramer_obj, matrix)
            
            _pause()
            
        except ValueError as e:
            print(f"\n⚠ Error: {e}")
            _pause()
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario.")
            break
        except Exception as e:
            print(f"\n⚠ Error inesperado: {e}")
            import traceback
            traceback.print_exc()
            _pause()

def _cramer_menu_loop():
    """Bucle del submenú de Cramer."""
    actions = {
        "1": ("Resolver con Cramer", run_cramer),
        "2": ("Calcular Determinante", _run_determinant_calculator),
    }
    while True:
        try:
            _print_cramer_menu()
            opt = input("Selecciona una opción (Cramer): ").strip()
            
            if opt in ("0", "volver", "b", "back"):
                print("Volviendo al menú principal...")
                break
            
            action = actions.get(opt)
            if not action:
                print("⚠ Opción inválida. Intenta de nuevo.")
                _pause()
                continue
            
            nombre, fn = action
            print(f"\n{'═' * 60}")
            print(f"  {nombre}")
            print('═' * 60)
            
            try:
                fn()
            except KeyboardInterrupt:
                print("\n⚠ Operación cancelada por el usuario.")
            except Exception as e:
                print(f"\n⚠ Ocurrió un error: {e}")
                import traceback
                traceback.print_exc()
            
            _pause()
            
        except KeyboardInterrupt:
            print("\n⚠ Operación cancelada. Volviendo al menú principal...")
            break
        except Exception as e:
            print(f"\n⚠ Error en el menú de Cramer: {e}")
            import traceback
            traceback.print_exc()
            _pause()
            break

# ---------------------------
# Submenú VECTORES
# ---------------------------
def _print_vectors_menu():
    """Opciones del submenú de vectores."""
    use_color = _colors_enabled()
    def C(c): return f"\033[{c}m" if use_color else ""
    RESET=C("0"); BOLD=C("1"); WHITE=C("97"); MAG=C("95")

    print_header("MÓDULO DE VECTORES")
    items = [
        ("1", "Operaciones con Vectores"),
        ("2", "Combinación lineal / Ecuación vectorial"),
        ("3", "Producto Ax (regla fila—vector)"),
        ("0", "Volver"),
    ]
    for k, label in items:
        print(f"{MAG}{BOLD}[{k}]{RESET} {WHITE}{label}{RESET}")
    print()

def _vectors_menu_loop():
    """Bucle del submenú de vectores."""
    actions = {
        "1": ("Cálculo de Vectores", run_vector_calc),
        "2": ("Combinación lineal / Ecuación vectorial", run_vector_combination),
        "3": ("Producto Ax (fila—vector)", run_matrix_times_vector),
    }
    while True:
        _print_vectors_menu()
        opt = input("\nSelecciona una opción (Vectores): ").strip().lower()
        if opt in ("0", "volver", "b", "back"):
            break
        action = actions.get(opt)
        if not action:
            print("Opción inválida. Intenta de nuevo.")
            _pause()
            continue
        nombre, fn = action
        print(f"\n--- {nombre} ---")
        try:
            fn()
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario.")
        except Exception as e:
            print(f"\nOcurrió un error: {e}")
        _pause()

# ---------------------------
# Bucle principal
# ---------------------------
def startup():
    """Bucle principal del programa."""
    actions = {
        "1": ("Gauss—Jordan (RREF)", run_gauss_jordan),
        "2": ("Gauss", run_gauss),
        # "3" abre submenú de Cramer, no se mapea aquí
        "4": ("Mostrar sistema", _run_display_only),
        # "5" abre submenú de Vectores, no se mapea aquí
        # "6" abre submenú de Matrices, no se mapea aquí
    }

    while True:
        try:
            print_header()
            _print_main_menu()
            print()
            opt = input("\nSelecciona una opción: ").strip()

            if opt in ("0", "q", "Q", "salir", "exit"):
                print("\n" + "═" * 50)
                print("  Saliendo... ¡Hasta luego!")
                print("═" * 50)
                break

            if opt == "3":
                _cramer_menu_loop()
                continue

            if opt == "5":
                _vectors_menu_loop()
                continue
            
            if opt == "6":
                matrices_menu_loop()
                continue

            action = actions.get(opt)
            if not action:
                print("⚠ Opción inválida. Intenta de nuevo.")
                _pause()
                continue

            nombre, fn = action
            print(f"\n{'═' * 60}")
            print(f"  {nombre}")
            print('═' * 60)
            
            try:
                fn()
            except KeyboardInterrupt:
                print("\n⚠ Operación cancelada por el usuario.")
            except Exception as e:
                print(f"\n⚠ Ocurrió un error: {e}")
                import traceback
                traceback.print_exc()
            
            _pause()
            
        except KeyboardInterrupt:
            print("\n\n" + "═" * 50)
            print("  Programa interrumpido. ¡Hasta luego!")
            print("═" * 50)
            break