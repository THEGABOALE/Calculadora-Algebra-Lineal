"""
STARTUP / MENÚ INTERACTIVO

Propósito
- Menú visual para métodos con matrices (Gauss–Jordan, Gauss, Cramer, ver A|b).
- Submenú para VECTORES (propiedades, combinación lineal, producto Ax).

Notas
- Sin dependencias externas; colores ANSI solo si stdout es TTY y NO_COLOR no está definido.
- Cada acción es una función (runner) ya existente; este módulo solo orquesta.
- `_run_display_only` reutiliza `make_equation` y `mostrar_sistema_desde_input`.
"""

from cli.method_runners import (
    run_cramer,
    run_gauss,
    run_gauss_jordan,
    mostrar_sistema_desde_input,
)
from cli.inputsmatrix import inputs_matrix

# Submenú: runners de VECTORES
from cli.vector_runners import (
    run_vector_props,
    run_vector_combination,
    run_matrix_times_vector,
    run_vector_calc,
)

from cli.matrix_runners import matrices_menu_loop
from core.positional_notation import run_positional_notation_menu
from cli.numerical_methods_runners import metodos_numericos_menu_loop

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
        ("1", "Forma Escalonada Reducida (Gauss–Jordan)"),
        ("2", "Forma Escalonada (Gauss)"),
        ("3", "Regla de Cramer"),
        ("4", "Mostrar solo el sistema (A | b)"),
        ("5", "Vectores ▸"),
        ("6", "Matrices"),
        ("7", "Notación Posicional ▸"),
        ("8", "Métodos Numéricos ▸"),
        ("0", "Salir"),
    ]
    for k, label in items:
        print(f"{MAG}{BOLD}[{k}]{RESET} {WHITE}{label}{RESET}")

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
        #("1", "Propiedades en R^n"),
        ("1", "Operaciones con Vectores"),
        ("2", "Combinación lineal / Ecuación vectorial"),
        ("3", "Producto Ax (regla fila–vector)"),
        ("0", "Volver"),
    ]
    for k, label in items:
        print(f"{MAG}{BOLD}[{k}]{RESET} {WHITE}{label}{RESET}")
    print()

def _vectors_menu_loop():
    """Bucle del submenú de vectores."""
    actions = {
        #"4": ("Propiedades en R^n", run_vector_props),
        "1": ("Cálculo de Vectores", run_vector_calc),
        "2": ("Combinación lineal / Ecuación vectorial", run_vector_combination),
        "3": ("Producto Ax (fila–vector)", run_matrix_times_vector),
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
        "1": ("Gauss–Jordan (RREF)", run_gauss_jordan),
        "2": ("Gauss", run_gauss),
        "3": ("Cramer", run_cramer),
        "4": ("Mostrar sistema", _run_display_only),
        # "5" abre submenú, no se mapea aquí
        "7": ("Notación Posicional ▸", run_positional_notation_menu),
    }

    while True:
        print_header()
        _print_main_menu()
        print()
        opt = input("\nSelecciona una opción: ").strip().lower()

        if opt in ("0", "q", "salir"):
            print("Saliendo... ¡Hasta luego!")
            break

        if opt == "5":
            _vectors_menu_loop()
            continue
        
        if opt == "6":
            matrices_menu_loop()
            continue

        if opt == "8":
            metodos_numericos_menu_loop()
            continue

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