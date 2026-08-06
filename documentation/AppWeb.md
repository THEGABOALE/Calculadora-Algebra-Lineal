# Documentación de la App Web (Django)

> **Archivos:**\
> `linear_algebra_calculator/calculator/` (app Django: `views.py`, `urls.py`, `templates/`, `static/`)\
> `linear_algebra_calculator/utils/html_display.py` (el `frame` renderizado como HTML)\
> `linear_algebra_calculator/linear_algebra_calculator/` (settings, urls raíz, wsgi/asgi)

Documento técnico que describe cómo la app Django consume el mismo motor matemático (`core/`) que el CLI, y el patrón que siguen todas sus vistas.

---

## 1. Resumen general

La web no tiene su propia copia del motor: `calculator/views.py` importa directamente de `core.*` (`core.gauss.GaussMethod`, `core.gauss_jordan.GaussJordanMethod`, `core.vector.Vector`, `core.vector_tools.*`, `core.matrix_tools.*`). El único código propio de la app son las vistas (parseo del `request.POST`, dispatch por `method`, armado de HTML) y los templates.

`BASE_DIR` (en `settings.py`) es `linear_algebra_calculator/`, la raíz de `sys.path` cuando se corre `manage.py`: por eso `core.*` y `utils.*` se importan igual desde la web que desde el CLI, sin rutas relativas ni paquetes duplicados.

---

## 2. El patrón de cada ruta (dimensiones → datos → resultado)

Todas las rutas de cómputo siguen la misma forma de tres pasos, sin excepción:

1. **Vista de dimensiones** (GET, o POST desde el paso anterior): pide tamaño (filas/columnas, o dimensión `n`) y renderiza el formulario de datos correspondiente.
2. **Vista de datos** (el mismo template del paso 1 lo posts a sí mismo, o a la vista de dimensiones, según la ruta): entrada de la matriz/vector/es y selector de `method`.
3. **Vista de resolución** (POST): parsea, valida que ningún campo esté vacío, calcula, y renderiza `result.html` con tres fragmentos de HTML ya armados.

| Familia | Dimensiones | Datos + método | Resolución |
|---|---|---|---|
| Sistemas de ecuaciones | `/ecuationInput/` (GET) | `/ecuationInput/` (POST) → `ecuation_input.html` | `/ecuationResolution/` |
| Vectores | `/vectorInput/` (GET) | `/vectorInput/` (POST) → `vector_form.html` | `/vectorResolution/` |
| Matrices | `/matrixInput/` (GET) | `/matrixInput/` (POST) → `matrix_form.html` | `/matrixOperationResolution/` |

`/matrixInput/` reutiliza `make_matrix.html` sin modificarlo: ya era un formulario genérico de "filas/columnas".

---

## 3. `utils/html_display.py` — el `frame` como HTML

Es el equivalente web de `utils/printMethods.py` (que imprime el mismo `frame` por consola). Cuatro funciones:

```py
equation_to_html(matriz, vector) -> str      # "2x₁ + x₂ = 5" por fila, envuelto en .equation-pretty
summary_to_html(result) -> str               # status/solution/basic_vars/free_vars -> .solution-box
frame_to_html(frame, show_det=True) -> str   # el frame completo, paso a paso -> .step-log
matrix_to_html(matrix) -> str                # una matriz como <table class='pretty-matrix'>
```

`frame_to_html` es completamente genérico: itera el `dict` del `frame` (`{descripción: {"matrix", "det", "tag"}}`) sin saber qué método lo produjo. Por eso `core.matrix_tools.inverse(A, frame=mi_frame)` se puede pasar un `frame` armado a mano en la vista (ver `matrixOperationResolution`) y renderizarlo exactamente igual que el de `GaussJordanMethod`.

`equation_to_html` y `summary_to_html`, en cambio, **asumen la forma de un sistema resuelto** (`status` en `unique`/`infinite`/`inconsistent`, `solution`, `basic_vars`, `free_vars`). Las operaciones que no son sistemas — vectores, determinante, inversa, rango, transpuesta, producto `Ax` — arman su propio HTML de entrada/resultado directamente en la vista (reutilizando `matrix_to_html` y las mismas clases CSS: `.equation-pretty`, `.solution-box`), en vez de forzar esos dos helpers a una forma que no les corresponde.

---

## 4. `calculator/views.py` — vistas por ruta

| Vista | Rutas | `method` soportados |
|---|---|---|
| `home_page`, `calculatorMain` | `/home/`, `/calculatorMain/` | — (páginas estáticas) |
| `ecuationInput`, `ecuationResolution` | `/ecuationInput/`, `/ecuationResolution/` | `gauss`, `gauss_jordan`, `combinacion_lineal`, `ax` |
| `vectorInput`, `vectorResolution` | `/vectorInput/`, `/vectorResolution/` | `suma`, `resta`, `producto_punto` |
| `matrixInput`, `matrixOperationResolution` | `/matrixInput/`, `/matrixOperationResolution/` | `determinante`, `inversa`, `rango`, `transpuesta` |

**`combinacion_lineal` y `ax` no son rutas propias.** Se agregaron como valores nuevos de `method` sobre `/ecuationResolution/`, que ya existía: `combinacion_lineal` es literalmente `Ax=b` con las columnas de `A` como los vectores (misma llamada que `gauss_jordan`, más la verificación componente a componente); `ax` calcula `Ax` sin resolver nada. Ver `documentation/Vectores.md` secciones 4 y 5 para el detalle matemático de las dos.

**Parseo de números:** todas las vistas usan `parse_fraction`/`format_number` de `utils.EquationFunctions` (no una copia propia de la app): acepta enteros, decimales, y fracciones tipo `"3/4"` o `"7/2"`.

**Manejo de errores:** cada vista de resolución envuelve el cómputo en `try/except ValueError`, re-renderizando el formulario de datos con un mensaje de error y los valores ya ingresados (para no perder lo que el usuario escribió). Es el mismo patrón en las tres familias de rutas.

---

## 5. Navegación

`calculator_main.html` es el menú de entrada con tres opciones: sistemas de ecuaciones (`/ecuationInput/`), vectores (`/vectorInput/`), matrices (`/matrixInput/`). `result.html` tiene un enlace "Realizar Nueva Cálculo" que usa `back_url` del contexto (con `/ecuationInput/` como valor por defecto, para no romper las rutas que no lo pasan) — cada familia de rutas pasa su propio `back_url` para volver al punto correcto, no siempre al de sistemas de ecuaciones.

---

## 6. Qué no persiste en base de datos

La app tiene `db.sqlite3` (vacío) porque Django lo requiere para `django.contrib.sessions`/`auth`/etc. en `INSTALLED_APPS`, pero **ninguna vista actual guarda ni lee datos de la base**: cada cómputo es puro, a partir de lo que llega en el `POST` de esa misma request. No hay historial de cálculos entre sesiones.

---

## 7. Ejecutar y probar

```bash
cd linear_algebra_calculator
python manage.py runserver
```

Los tests de las rutas (`tests/test_web_vectores_matrices.py`, en la raíz del repo) usan `django.test.Client` directo, no `django.test.TestCase`: ninguna vista toca base de datos, así que no hace falta la maquinaria de transacciones/DB de prueba de Django, y los tests corren con el mismo `python -m unittest discover tests` que el resto de la suite — no con `manage.py test`.
