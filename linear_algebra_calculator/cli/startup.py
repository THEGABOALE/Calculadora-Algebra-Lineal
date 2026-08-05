"""
STARTUP / MENÚ INTERACTIVO

Propósito:
- Proveer un bucle de menú simple y visual para ejecutar los métodos de la
  calculadora (Gauss-Jordan, Gauss, Cramer) o solo mostrar el sistema [A | b].
- Mantener separada la UI/entrada de usuario de la lógica de cómputo.

Notas de diseño:
- Sin dependencias externas; colores ANSI solo si stdout es TTY y NO_COLOR no está definido.
- Cada acción es una función (runner) ya existente; este módulo solo orquesta.
- `_run_display_only` reutiliza `make_equation` y `mostrar_sistema_desde_input`.
"""

from cli.method_runners import (
    run_crammer,
    run_gauss,
    run_gauss_jordan,
    mostrar_sistema_desde_input,
)
from cli.inputsmatrix import inputs_matrix

def _pause(msg: str = "\nPresiona Enter para continuar..."):
    """Pausa la consola para que el usuario lea la salida antes de volver al menú."""
    try:
        input(msg)
    except KeyboardInterrupt:
        # Permite salir de la pausa con Ctrl+C sin romper el flujo
        pass
    
def _run_display_only():
    """Pide filas/columnas y muestra A|b + ecuaciones sin resolver."""
    rows, cols = inputs_matrix()
    mostrar_sistema_desde_input(rows, cols)
    _pause()

def print_header():
    """
    Cabecera visual del programa (cuadro Unicode con color ANSI opcional).
    Se adapta de forma conservadora al ancho de la terminal.
    """
    import os, sys, shutil

    title = "CALCULADORA DE ÁLGEBRA LINEAL"

    # Habilitar color solo si la salida es TTY y el usuario no desactiva con NO_COLOR
    use_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    def C(code): return f"\033[{code}m" if use_color else ""
    RESET = C("0"); BOLD = C("1")
    CYAN  = C("96"); WHITE = C("97")

    # Ancho del cuadro (mínimo cómodo; deja márgenes laterales)
    term_w = shutil.get_terminal_size(fallback=(80, 20)).columns
    inner_w = max(len(title) + 10, 48)               # ancho mínimo cómodo
    box_w = min(inner_w, term_w - 6)                 # deja margen lateral
    
    # Caracteres de borde (Unicode)
    TL, TR, BL, BR, H, V = "╔", "╗", "╚", "╝", "═", "║"
    
    top    = CYAN + BOLD + TL + (H * box_w) + TR + RESET
    empty  = CYAN + V + RESET + " " * box_w + CYAN + V + RESET
    middle = (CYAN + V + RESET
              + BOLD + WHITE + title.center(box_w) + RESET
              + CYAN + V + RESET)
    bottom = CYAN + BOLD + BL + (H * box_w) + BR + RESET

    print()                # margen superior
    print(top)
    print(empty)
    print(middle)
    print(empty)
    print(bottom)
    print()                # margen inferior
    
def print_menu_visual():
    """
    Lista de opciones del menú en formato compacto con color ANSI opcional.
    No realiza lecturas de entrada; solo imprime.
    """
    import os, sys
    use_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    def C(c): return f"\033[{c}m" if use_color else ""
    RESET=C("0"); BOLD=C("1"); WHITE=C("97"); MAG=C("95"); GREEN=C("92")

    items = [
        ("1", "Forma Escalonada Reducida (Gauss Jordan)"),
        ("2", "Forma Escalonada (Gauss)"),
        ("3", "Regla de Cramer"),
        ("4", "Mostrar solo el sistema (A | b)"),
        ("0", "Salir"),
    ]
    for k, label in items:
        # [k] en magenta/negrita + etiqueta en blanco
        print(f"{MAG}{BOLD}[{k}]{RESET} {WHITE}{label}{RESET}")

def _print_menu():
    """
    Renderiza el encabezado y el menú (sin leer input).
    Llamada por cada iteración del bucle principal.
    """
    print_header()
    print_menu_visual()
    print() # separación con el prompt de entrada

def startup():
    """
    Bucle principal del programa.
    - Mapea teclas a acciones (runners)
    - Controla salida limpia (0 / q / salir)
    """
    # Dispatcher: clave -> (nombre amigable, función a ejecutar)
    actions = {
        "1": ("Gauss-Jordan (RREF)", run_gauss_jordan),
        "2": ("Gauss", run_gauss),
        "3": ("Cramer", run_crammer),
        "4": ("Mostrar sistema", _run_display_only),
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
            fn() # ejecuta el runner seleccionado
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario.")
        except Exception as e:
             # Manejo genérico: mostrar el error y permitir continuar
            print(f"\nOcurrió un error: {e}")
        _pause()  # pausa antes de redibujar el menú