"""
STARTUP / MENÚ INTERACTIVO

Propósito
- Menú visual para métodos con matrices (Gauss–Jordan, Gauss, Cramer, ver A|b)
  y utilidades con vectores (propiedades, combinación lineal, Ax).
"""

from helpers.inputsmatrix import inputs_matrix
from utils.display import mostrar_sistema_desde_input

# Runners de matrices
from models.GaussJordan import run_gauss_jordan
from models.GaussMethod import run_gauss
from models.CramerMethod import run_crammer

# Runners de vectores (asegurado que existen)
from utils.vector_runners import (
    run_vector_props,           # Propiedades en R^n
    run_vector_combination,     # Combinación lineal / Ecuación vectorial
    run_matrix_times_vector,    # Producto Ax (regla fila–vector)
)


def _pause(msg: str = "\nPresiona Enter para continuar...") -> None:
    """Pausa para leer salida antes de volver al menú."""
    try:
        input(msg)
    except KeyboardInterrupt:
        pass


def _run_display_only() -> None:
    """Pide filas/columnas y muestra A|b + ecuaciones (sin resolver)."""
    rows, cols = inputs_matrix()
    mostrar_sistema_desde_input(rows, cols)
    _pause()


def print_header() -> None:
    """Cabecera visual (cuadro Unicode con color ANSI opcional)."""
    import os, sys, shutil

    title = "CALCULADORA DE ÁLGEBRA LINEAL"
    use_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

    def C(code: str) -> str:
        return f"\033[{code}m" if use_color else ""

    RESET = C("0"); BOLD = C("1")
    CYAN  = C("96"); WHITE = C("97")

    term_w = shutil.get_terminal_size(fallback=(80, 20)).columns
    inner_w = max(len(title) + 10, 48)
    box_w = min(inner_w, term_w - 6)

    TL, TR, BL, BR, H, V = "╔", "╗", "╚", "╝", "═", "║"
    top    = CYAN + BOLD + TL + (H * box_w) + TR + RESET
    empty  = CYAN + V + RESET + " " * box_w + CYAN + V + RESET
    middle = (CYAN + V + RESET
              + BOLD + WHITE + title.center(box_w) + RESET
              + CYAN + V + RESET)
    bottom = CYAN + BOLD + BL + (H * box_w) + BR + RESET

    print()
    print(top)
    print(empty)
    print(middle)
    print(empty)
    print(bottom)
    print()


def print_menu_visual() -> None:
    """Imprime opciones de menú (matrices y vectores)."""
    import os, sys
    use_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

    def C(c: str) -> str:
        return f"\033[{c}m" if use_color else ""

    RESET = C("0"); BOLD = C("1")
    WHITE = C("97"); MAG = C("95"); CYAN = C("96")

    print(f"{CYAN}{BOLD}== Métodos con matrices =={RESET}")
    for k, label in [
        ("1", "Forma Escalonada Reducida (Gauss–Jordan)"),
        ("2", "Forma Escalonada (Gauss)"),
        ("3", "Regla de Cramer"),
        ("4", "Mostrar solo el sistema (A | b)"),
    ]:
        print(f"{MAG}{BOLD}[{k}]{RESET} {WHITE}{label}{RESET}")

    print()
    print(f"{CYAN}{BOLD}== Vectores =={RESET}")
    for k, label in [
        ("5", "Propiedades en R^n (conmutativa, asociativa, opuesto, etc.)"),
        ("6", "Combinación lineal / Ecuación vectorial (planteo y resolución)"),
        ("7", "Producto Ax (regla fila–vector), paso a paso"),
    ]:
        print(f"{MAG}{BOLD}[{k}]{RESET} {WHITE}{label}{RESET}")

    print(f"\n{MAG}{BOLD}[0]{RESET} {WHITE}Salir{RESET}")


def _print_menu() -> None:
    """Dibuja encabezado + menú (sin leer entrada)."""
    print_header()
    print_menu_visual()
    print()


def startup() -> None:
    """Bucle principal. Mapea teclas a runners y maneja salida limpia."""
    actions = {
        # Matrices
        "1": ("Gauss–Jordan (RREF)", run_gauss_jordan),
        "2": ("Gauss", run_gauss),
        "3": ("Cramer", run_crammer),
        "4": ("Mostrar sistema (A|b)", _run_display_only),

        # Vectores
        "5": ("Propiedades en R^n", run_vector_props),
        "6": ("Combinación lineal / Ecuación vectorial", run_vector_combination),
        "7": ("Producto Ax (fila–vector)", run_matrix_times_vector),
    }

    while True:
        _print_menu()
        opt = input("Selecciona una opción: ").strip().lower()

        if opt in ("0", "q", "salir"):
            print("Saliendo... ¡Hasta luego!")
            break

        entry = actions.get(opt)
        if not entry:
            print("Opción inválida. Intenta de nuevo.")
            _pause()
            continue

        nombre, fn = entry
        print(f"\n--- {nombre} ---")
        try:
            fn()
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario.")
        except Exception as e:
            print(f"\nOcurrió un error: {e}")
        _pause()