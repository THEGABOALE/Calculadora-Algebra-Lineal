"""
STARTUP / MENÚ INTERACTIVO

Propósito
- Menú visual para métodos con matrices (Gauss–Jordan, Gauss, Cramer, ver A|b)
  y utilidades con vectores (propiedades, combinación lineal, Ax).
"""

from models.CramerMethod import run_crammer
from models.GaussMethod import run_gauss
from models.GaussJordan import run_gauss_jordan
from utils.display import mostrar_sistema_desde_input
from helpers.inputsmatrix import inputs_matrix

# NUEVO: runners de vectores
from vector_runners import run_vector_props, run_vector_combination, run_matrix_times_vector

def _pause(msg: str = "\nPresiona Enter para continuar..."):
    try:
        input(msg)
    except KeyboardInterrupt:
        pass

def _run_display_only():
    rows, cols = inputs_matrix()
    mostrar_sistema_desde_input(rows, cols)
    _pause()

def print_header():
    import os, sys, shutil
    title = "CALCULADORA DE ÁLGEBRA LINEAL"
    use_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    def C(code): return f"\033[{code}m" if use_color else ""
    RESET = C("0"); BOLD = C("1")
    CYAN  = C("96"); WHITE = C("97")
    term_w = shutil.get_terminal_size(fallback=(80, 20)).columns
    inner_w = max(len(title) + 10, 48)
    box_w = min(inner_w, term_w - 6)
    TL, TR, BL, BR, H, V = "╔", "╗", "╚", "╝", "═", "║"
    top    = CYAN + BOLD + TL + (H * box_w) + TR + RESET
    empty  = CYAN + V + RESET + " " * box_w + CYAN + V + RESET
    middle = (CYAN + V + RESET + BOLD + WHITE + title.center(box_w) + RESET + CYAN + V + RESET)
    bottom = CYAN + BOLD + BL + (H * box_w) + BR + RESET
    print(); print(top); print(empty); print(middle); print(empty); print(bottom); print()

def print_menu_visual():
    import os, sys
    use_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    def C(c): return f"\033[{c}m" if use_color else ""
    RESET=C("0"); BOLD=C("1"); WHITE=C("97"); MAG=C("95")
    items = [
        ("1", "Forma Escalonada Reducida (Gauss–Jordan)"),
        ("2", "Forma Escalonada (Gauss)"),
        ("3", "Regla de Cramer"),
        ("4", "Mostrar solo el sistema (A | b)"),
        # NUEVO: vectores
        ("5", "Vectores: Propiedades en R^n"),
        ("6", "Vectores: Combinación lineal / ecuación vectorial"),
        ("7", "Vectores: Producto Ax (fila–vector)"),
        ("0", "Salir"),
    ]
    for k, label in items:
        print(f"{MAG}{BOLD}[{k}]{RESET} {WHITE}{label}{RESET}")

def _print_menu():
    print_header()
    print_menu_visual()
    print()

def startup():
    actions = {
        "1": ("Gauss–Jordan (RREF)", run_gauss_jordan),
        "2": ("Gauss", run_gauss),
        "3": ("Cramer", run_crammer),
        "4": ("Mostrar sistema", _run_display_only),
        # NUEVO: vectores
        "5": ("Propiedades en R^n", run_vector_props),
        "6": ("Combinación lineal / Ecuación vectorial", run_vector_combination),
        "7": ("Producto Ax (fila–vector)", run_matrix_times_vector),
    }
    while True:
        _print_menu()
        opt = input("\nSelecciona una opción: ").strip().lower()
        if opt in ("0", "q", "salir"):
            print("Saliendo... ¡Hasta luego!")
            break
        action = actions.get(opt)
        if not action:
            print("Opción inválida. Intenta de nuevo.")
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