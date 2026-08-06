"""
PUNTO DE ENTRADA DEL CLI

Uso, desde el directorio linear_algebra_calculator/:

    python -m cli.main

Es el antiguo main.py de la raíz, que se borró al migrar a Django
(commit 78e8f09). Vuelve aquí porque el motor de core/ lo comparten
ahora el CLI y la app web.
"""

from cli.startup import startup


def main() -> None:
    startup()


if __name__ == '__main__':
    main()
