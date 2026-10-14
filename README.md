# Calculadora de Álgebra Lineal

Calculadora didáctica de álgebra lineal: resuelve sistemas de ecuaciones
(Gauss, Gauss-Jordan, Cramer), opera con vectores y matrices, calcula rango/
singularidad/núcleo, descompone números en notación posicional, y busca
raíces por métodos numéricos (bisección, regla falsa, Newton-Raphson,
secante). Cada método registra sus pasos, no sólo el resultado final.

## Arquitectura

Un único motor matemático (`linear_algebra_calculator/core/`), sin `input()`
ni `print()`, consumido por dos interfaces independientes que no comparten
código entre sí más que ese motor:

- **CLI** (`linear_algebra_calculator/cli/`) — menú interactivo por consola.
- **API REST** (`linear_algebra_calculator/api/`, Django + Django REST
  Framework) — consumida por un **frontend React/TypeScript** aparte
  (`frontend/`, Vite), que corre en su propio proceso y le habla a la API
  por HTTP.

No hay una tercera interfaz web de templates de Django generando HTML en el
servidor — esa arquitectura existió en versiones anteriores del proyecto y
se retiró: hoy la única forma de usar el motor desde un navegador es API +
frontend desacoplados.

```
┌─────────────┐        ┌──────────────────┐        ┌──────────────┐
│  cli/ (CLI) │───┐    │  api/ (REST)     │───┐    │              │
└─────────────┘   ├───▶│                  │    ├───▶│  core/       │
┌─────────────┐   │    └──────────────────┘   │    │  (motor)     │
│ frontend/   │───┼────────────▲───────────────┘    │              │
│ (React/Vite)│   │  HTTP      │                     └──────────────┘
└─────────────┘   └────────────┘ (frontend habla sólo con api/, nunca con core/ directo)
```

`core/` no sabe que `cli/` o `api/` existen. `cli/` y `api/` no se conocen
entre sí. La única capa que importa `core/` directo en ambos casos es cada
una de esas dos interfaces, cada una con su propio traductor de resultados
(`utils/printMethods.py` para el CLI, `api/adapters/` para la API).

## Instalación

Requiere Python 3.12+ y Node 18+ (para el frontend).

### Backend (CLI y/o API)

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

### Frontend (sólo hace falta si vas a usar la API desde un navegador)

```bash
cd frontend
npm install
```

## Ejecutar el CLI

```bash
cd linear_algebra_calculator
python -m cli.main
```

Abre un menú interactivo: Gauss-Jordan, Gauss, Cramer, mostrar sólo el
sistema, Vectores (operaciones básicas, combinación lineal, producto A·x,
propiedades en Rⁿ), Matrices (suma, resta, escalar, multiplicación,
traspuesta, inversa, memoria de resultados), Notación Posicional (base 10 y
base 2), y Métodos Numéricos (bisección, regla falsa, Newton-Raphson,
secante). No necesita el frontend ni el servidor de la API corriendo — es
completamente independiente.

## Ejecutar la API + el frontend

Dos procesos, cada uno en su propia terminal.

**API** (Django):
```bash
cd linear_algebra_calculator
python manage.py runserver
```
Queda escuchando en `http://localhost:8000/api/v1/`. Ver
[`documentation/AppWeb.md`](documentation/AppWeb.md) para la lista completa
de endpoints.

**Frontend** (Vite):
```bash
cd frontend
npm run dev
```
Abre `http://localhost:5173`. Habla con la API en `localhost:8000` vía HTTP
(`VITE_API_BASE`, variable de entorno del frontend, para apuntar a otra URL
si hiciera falta).

La API usa SQLite (`db.sqlite3`) sólo porque Django lo requiere para
`django.contrib.sessions`/`auth`; ninguna vista guarda ni lee datos de la
base — cada cómputo es puro, a partir del `POST` de esa misma request.

## Ejecutar los tests

Sólo el backend tiene suite de tests (Python). Desde la raíz del repo (no
desde `linear_algebra_calculator/`):

```bash
PYTHONPATH=linear_algebra_calculator python -m unittest discover tests -v
```

En Windows PowerShell:
```powershell
$env:PYTHONPATH="linear_algebra_calculator"; python -m unittest discover tests -v
```

La suite (195 tests) cubre el motor matemático (`core/`) y los endpoints de
la API con `rest_framework.test.APIClient`, sin necesitar `manage.py test`
ni una base de datos de prueba.

Para el frontend: `cd frontend && npx tsc --noEmit && npm run build`
(typecheck + build; no hay suite de tests de UI en este repo).

## Estructura del proyecto

```
linear_algebra_calculator/
├── manage.py
├── linear_algebra_calculator/   # settings, urls, wsgi/asgi de Django
├── core/                        # motor matemático puro, sin I/O
│   ├── gauss.py, gauss_jordan.py, cramer.py
│   ├── vector.py, vector_tools.py, matrix_tools.py
│   ├── positional_notation.py
│   ├── system_solver/           # análisis/resolución compartido por Gauss y Gauss-Jordan
│   └── numeric/                 # bisección, regla falsa, Newton-Raphson, secante (sympy)
├── api/                         # API REST (Django REST Framework)
│   ├── views.py, serializers.py, urls.py
│   └── adapters/                # un traductor core/ -> JSON por dominio
├── utils/                       # compartido entre CLI y API
│   ├── EquationFunctions.py     # formato de números, fracciones, subíndices
│   ├── symbolic_equations.py    # evaluación/derivación simbólica (symengine, sin consumidores hoy)
│   ├── printMethods.py          # registro de pasos (frame) y su impresión en CLI
│   └── matrix_memory.py
└── cli/                         # todo lo interactivo (menús, runners)
    ├── main.py, startup.py, inputsmatrix.py
    └── *_runners.py

frontend/                        # React + TypeScript + Vite, independiente de linear_algebra_calculator/
└── src/
    ├── api/client.ts            # una función por endpoint de la API
    └── components/              # AlgebraicMethods.tsx, ResultPretty.tsx, ...

tests/                           # en la raíz del repo, no dentro de linear_algebra_calculator/
documentation/                   # documentación técnica por método/dominio
```

**Regla de separación:** si un módulo llama a `input()`/`print()`, vive en
`cli/`. Si arma JSON o valida una request HTTP, vive en `api/`. Si sólo
formatea sin decidir nada, vive en `utils/`. Si calcula, vive en `core/` y no
depende de símbolos pesados como `sympy`/`antlr4`/`symengine` a nivel de
módulo — esos imports quedan diferidos dentro de las funciones que
efectivamente los necesitan (`core/numeric/_expresiones.py`,
`api/adapters/latex.py`), para que el CLI no los cargue en cada arranque.

## Documentación técnica

En `documentation/` hay un documento por tema: la API de `core/`, el formato
del registro de pasos (`frame`), consideraciones numéricas, la interfaz CLI,
la interfaz API (endpoint, request, response), y ejemplos de uso.

- [`GaussMethod.md`](documentation/GaussMethod.md), [`GaussJordanMethod.md`](documentation/GaussJordanMethod.md), [`CramerMethod.md`](documentation/CramerMethod.md) — los tres métodos para resolver `Ax=b`.
- [`Vectores.md`](documentation/Vectores.md) — clase `Vector`, axiomas de espacio vectorial, combinación lineal, producto `Ax`.
- [`Matrices.md`](documentation/Matrices.md) — aritmética matricial, determinante, inversa, verificación de propiedades.
- [`MatrixProperties.md`](documentation/MatrixProperties.md) — rango, singularidad y núcleo como endpoint propio.
- [`CriterioNumerico.md`](documentation/CriterioNumerico.md) — cuándo un número calculado "es cero": el criterio compartido por rango, determinante, inversa y Cramer, su calibración y sus límites; y cómo `format_number` muestra números chicos.
- [`NotacionPosicional.md`](documentation/NotacionPosicional.md) — descomposición en base 10 y base 2 (sólo CLI).
- [`MetodosNumericos.md`](documentation/MetodosNumericos.md) — bisección, regla falsa, Newton-Raphson, secante.
- [`AppWeb.md`](documentation/AppWeb.md) — cómo la API consume `core/`, la lista completa de endpoints, y qué capacidad del motor **no** está expuesta vía API todavía (a propósito, no por olvido).
