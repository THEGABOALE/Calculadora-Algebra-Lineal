# Calculadora de Álgebra Lineal

Calculadora didáctica de álgebra lineal: resuelve sistemas de ecuaciones
(Gauss, Gauss-Jordan, Cramer), opera con vectores y matrices, descompone
números en notación posicional, y busca raíces por métodos numéricos.
Cada método registra sus pasos, no sólo el resultado final.

El motor matemático (`linear_algebra_calculator/core/`) es compartido: se
consume tanto desde una interfaz de línea de comandos como desde una app
web (Django), sin duplicar lógica entre las dos.

## Instalación

Requiere Python 3.12+.

```bash
python -m venv .venv
```

En Windows (PowerShell o Git Bash):
```bash
.venv/Scripts/activate
```
En Linux/macOS:
```bash
source .venv/bin/activate
```

Con el entorno activado:
```bash
pip install -r requirements.txt
```

## Ejecutar el CLI

```bash
cd linear_algebra_calculator
python -m cli.main
```

Abre un menú interactivo con las opciones: Gauss-Jordan, Gauss, Cramer,
mostrar sólo el sistema, Vectores (operaciones básicas, combinación lineal,
producto A·x, propiedades en Rⁿ), Matrices (suma, resta, escalar,
multiplicación, traspuesta, inversa, memoria de resultados), Notación
Posicional (base 10 y base 2), y Métodos Numéricos (bisección, regla falsa,
Newton-Raphson, secante).

## Ejecutar la app web

```bash
cd linear_algebra_calculator
python manage.py runserver
```

Abre `http://127.0.0.1:8000/home/` en el navegador. Desde ahí:

- `/calculatorMain/` — menú principal de la calculadora.
- `/ecuationInput/` — sistemas de ecuaciones (Gauss, Gauss-Jordan, y sobre
  la misma ruta: combinación lineal y producto A·x).
- `/vectorInput/` — operaciones de vectores (suma, resta, producto punto).
- `/matrixInput/` — operaciones de matrices (determinante, inversa, rango
  y núcleo, traspuesta).

La app usa SQLite (`db.sqlite3`) pero no guarda nada en base de datos hoy:
ninguna de las vistas actuales persiste datos entre requests.

## Ejecutar los tests

Desde la raíz del repo (no desde `linear_algebra_calculator/`):

```bash
PYTHONPATH=linear_algebra_calculator python -m unittest discover tests -v
```

En Windows PowerShell:
```powershell
$env:PYTHONPATH="linear_algebra_calculator"; python -m unittest discover tests -v
```

La suite incluye tests del motor matemático (`core/`) y tests de las rutas
web con `django.test.Client`, sin necesitar `manage.py test` ni una base de
datos de prueba.

## Estructura del proyecto

```
linear_algebra_calculator/
├── manage.py
├── linear_algebra_calculator/   # settings, urls, wsgi/asgi de Django
├── core/                        # motor matemático puro, sin I/O
│   ├── gauss.py, gauss_jordan.py, cramer.py
│   ├── vector.py, vector_tools.py, matrix_tools.py
│   ├── positional_notation.py
│   ├── system_solver/
│   └── numeric/                 # bisección, regla falsa, Newton, secante
├── utils/                       # compartido entre CLI y web
│   ├── EquationFunctions.py     # formato de números, fracciones, subíndices
│   ├── symbolic_equations.py    # evaluación/derivación simbólica (symengine)
│   ├── printMethods.py          # registro de pasos (frame) y su impresión en CLI
│   ├── html_display.py          # el mismo frame, renderizado como HTML
│   └── matrix_memory.py
├── calculator/                  # app Django: views, urls, templates, static
└── cli/                         # todo lo interactivo (menús, runners)
    ├── main.py, startup.py, inputsmatrix.py
    └── *_runners.py
tests/                           # en la raíz del repo, no dentro de linear_algebra_calculator/
documentation/                   # documentación técnica por método
```

**Regla de separación:** si un módulo llama a `input()`/`print()`, vive en
`cli/`. Si sólo formatea sin decidir nada, vive en `utils/`. Si calcula,
vive en `core/` y no depende de símbolos pesados como `symengine` (ese
import queda aislado en `utils/symbolic_equations.py`, sin consumidores
hoy, para que cargarlo sea opcional).

## Documentación técnica

En `documentation/` hay un documento por tema, con su API, el formato del
registro de pasos (`frame`), consideraciones numéricas y ejemplos de uso:

- [`GaussMethod.md`](documentation/GaussMethod.md), [`GaussJordanMethod.md`](documentation/GaussJordanMethod.md), [`CramerMethod.md`](documentation/CramerMethod.md)
- [`Vectores.md`](documentation/Vectores.md)
- [`Matrices.md`](documentation/Matrices.md)
- [`NotacionPosicional.md`](documentation/NotacionPosicional.md)
- [`MetodosNumericos.md`](documentation/MetodosNumericos.md)
- [`AppWeb.md`](documentation/AppWeb.md) — cómo la app Django consume `core/`, y el patrón que siguen todas sus rutas.
