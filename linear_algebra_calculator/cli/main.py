"""
PUNTO DE ENTRADA DEL CLI

Uso, desde el directorio linear_algebra_calculator/:

    python -m cli.main

Es el antiguo main.py de la raíz, que se borró al migrar a Django
(commit 78e8f09). Vuelve aquí porque el motor de core/ lo comparten
ahora el CLI y la app web.
"""

import sys

from cli.startup import startup


def _configurar_encoding_consola() -> None:
    """Fuerza UTF-8 en stdout/stderr antes de imprimir nada.

    core/ y utils/ usan subíndices Unicode (x₁, x₂, ...) en toda la salida
    -- tablas de iteraciones, resúmenes de sistemas, la forma paramétrica de
    Gauss-Jordan. La consola de Windows arranca en cp1252 (el codepage por
    defecto, no UTF-8), que no tiene esos caracteres: el primer print con un
    subíndice revienta con UnicodeEncodeError y tira abajo el programa antes
    de que el usuario vea nada. reconfigure(encoding='utf-8') existe desde
    Python 3.7 en streams de texto; el try/except cubre el caso de que
    stdout/stderr ya no sean un TextIOWrapper reconfigurable (redirigidos a
    algo que no lo soporta) -- si eso pasa, se sigue igual: es mejor
    arriesgarse a un UnicodeEncodeError más adelante que no arrancar el CLI
    por esto.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def main() -> None:
    _configurar_encoding_consola()
    startup()


if __name__ == '__main__':
    main()
