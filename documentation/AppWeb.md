# Documentación de la App Web (API REST + frontend React)

> **Archivos:**\
> `linear_algebra_calculator/api/` (app Django: `views.py`, `serializers.py`, `urls.py`, `adapters/`)\
> `linear_algebra_calculator/linear_algebra_calculator/` (settings, urls raíz, wsgi/asgi)\
> `frontend/` (React + TypeScript + Vite, en la raíz del repo)

Documento técnico que describe cómo la API REST consume el mismo motor
matemático (`core/`) que el CLI, y cómo se conecta con el frontend
desacoplado.

La web de templates de Django (`calculator/`) que existía antes se retiró:
la arquitectura final es API REST + frontend React/TS, sin generar HTML en
el servidor.

---

## 1. Resumen general

La API no tiene su propia copia del motor: cada adaptador en `api/adapters/`
importa directamente de `core.*` (`core.gauss.GaussMethod`,
`core.gauss_jordan.GaussJordanMethod`, `core.cramer.CramerMethod`,
`core.vector.Vector`, `core.vector_tools.*`, `core.matrix_tools.*`,
`core.numeric.*`). El único código propio de la API son los adaptadores
(traducen la entrada/salida al contrato JSON que espera el frontend), los
serializers (validan forma, no matemática) y las vistas (dispatch HTTP).

`BASE_DIR` (en `settings.py`) es `linear_algebra_calculator/`, la raíz de
`sys.path` cuando se corre `manage.py`: por eso `core.*` y `utils.*` se
importan igual desde la API que desde el CLI, sin rutas relativas ni
paquetes duplicados.

El frontend es un proyecto Vite/React separado en `frontend/`, fuera de
`linear_algebra_calculator/` (que es raíz de `sys.path` de Python). Corre
en su propio dev server (`localhost:5173`) y habla con la API vía HTTP;
`src/api/client.ts` usa una `baseURL` absoluta a `localhost:8000`, así que
hace falta `CORS_ALLOWED_ORIGINS` en `settings.py` (el proxy de
`vite.config.js` no interviene cuando la baseURL ya es absoluta).

---

## 2. El patrón de cada adaptador (validar forma → llamar a core/ → traducir)

Todos los adaptadores siguen la misma forma, sin excepción:

1. **El serializer** (`api/serializers.py`) valida FORMA de la request:
   tipos, presencia de campos, dimensiones consistentes entre sí (p. ej.
   "una matriz no vacía", "A y b del mismo largo"). No valida reglas
   matemáticas del dominio.
2. **El adaptador** (`api/adapters/*.py`) llama a `core/` con los datos ya
   validados en forma, y traduce el resultado (y el `frame` de pasos, si el
   método lo produce) al contrato JSON que espera el frontend.
3. **La vista** (`api/views.py`) atrapa `ValueError`/`ZeroDivisionError` que
   suben desde `core/` y los traduce a `400` con el mensaje del motor, no un
   mensaje genérico de la capa HTTP.

Esta separación es deliberada: el chequeo matemático (matriz singular,
intervalo sin cambio de signo, sistema con más incógnitas que ecuaciones)
vive en `core/` y no se duplica en el serializer. Es la lección de que un
consumidor que no pase por la API REST (el CLI, por ejemplo) no debe quedar
sin esa validación.

---

## 3. Endpoints

| Endpoint | Adaptador | `core/` que consume |
|---|---|---|
| `POST /api/v1/matrix/operate` | `adapters/matrices.py` | `core/matrix_tools.py` (add, sub, scalar, transpose, matmul, sum_many, sub_many, matmul_chain, inverse) |
| `POST /api/v1/matrix/reduce` | `adapters/reduce.py` | `core/gauss.py`, `core/gauss_jordan.py`, `core/cramer.py` (`method`: gauss, gauss-jordan, cramer) |
| `POST /api/v1/matrix/determinant` | `adapters/determinant.py` | `core/cramer.py` (Sarrus y cofactores; `method=cramer` se rechaza acá con 400 explícito -- resuelve sistemas, no calcula un determinante suelto) |
| `POST /api/v1/matrix/properties` | `adapters/properties.py` | `core/matrix_tools.py` (`rank_of`, `is_singular`, `nullspace_vector`) |
| `POST /api/v1/vectors/operate` | `adapters/vectores.py` | `core/vector.Vector` (add, sub, escalar, comb2, comb3, dot) |
| `POST /api/v1/vectors/combination` | `adapters/vectores.py` | `core/vector_tools.linear_combination_verification_steps` |
| `POST /api/v1/numeric/bisection-method` | `adapters/numerico.py` + `adapters/latex.py` | `core/numeric/metodos_cerrados.py` |
| `POST /api/v1/numeric/false-position` | `adapters/numerico.py` + `adapters/latex.py` | `core/numeric/metodos_cerrados.py` |
| `POST /api/v1/numeric/newton-raphson` | `adapters/numerico.py` + `adapters/latex.py` | `core/numeric/metodos_abiertos.py` |
| `POST /api/v1/numeric/secant` | `adapters/numerico.py` + `adapters/latex.py` | `core/numeric/metodos_abiertos.py` |
| `POST /api/v1/numeric/abs-rel-error` | `adapters/numerico.py` | `core/numeric/errores.py` (error absoluto y relativo con `decimal.Decimal`) |
| `POST /api/v1/numeric/error-accumulation` | `adapters/numerico.py` | `core/numeric/errores.py` (error acumulado en interés compuesto con `decimal.Decimal`) |

Los cuatro métodos numéricos reciben la función en LaTeX
(`function_latex`); `adapters/latex.py` la traduce a texto plano para
`core/numeric`, que sigue siendo string-first -- esa dependencia (sympy
parseando LaTeX, y `antlr4-python3-runtime` que necesita) queda confinada
al adaptador, y el CLI nunca la carga.

---

## 4. `api/adapters/frame.py` — el `frame` como JSON

Es el equivalente REST de `utils/printMethods.py` (que imprime el mismo
`frame` por consola para el CLI). Cada método de `core/` que registra pasos
produce un `frame`: una lista ordenada de `Step` (`{index, text, matrix,
det, tag, extra}`). `adapters/frame.py` lo traduce a tres formas distintas,
porque `ResultPretty.tsx` (frontend) tiene tres caminos de render según
cómo llega `steps`:

```py
frame_to_steps(frame) -> list[dict]                  # lista plana: gauss, gauss-jordan
frame_to_step_states_envelope(frame) -> dict          # {frame:{step_states}, text_steps}: inverse
frame_to_states_envelope(frame) -> dict                # {frame:{states}, text_steps}: sarrus, cofactors, cramer
```

`core/` no sabe que existe este módulo -- la regla de corte del proyecto
(`core/` calcula, no formatea para su consumidor) se mantiene igual que se
mantiene con `utils/printMethods.py` para el CLI: cada consumidor tiene su
propio traductor de `frame`.

---

## 5. El frontend (`frontend/`)

React + TypeScript sobre Vite. `src/api/client.ts` concentra las llamadas a
cada endpoint (`matrixOperate`, `matrixReduce`, `matrixDeterminant`,
`matrixProperties`, `vectorOperate`, `vectorCombination`, los cuatro
métodos numéricos). `AlgebraicMethods.tsx` arma el payload según la
operación elegida y guarda la respuesta cruda en `localStorage` bajo
`calc_last_result`; `ResultPretty.tsx` la interpreta y renderiza --
distintas ramas de render según `input.operation`/`input.method` y la forma
de `steps` (ver sección 4).

`VITE_API_BASE` (variable de entorno del frontend) apunta a la URL de la
API; sin configurar, cae a `http://localhost:8000`.

---

## 6. Validación matemática vs. validación de forma

**No se duplica la validación matemática entre `core/` y la API.** Ejemplos
concretos:

- "A y B deben tener la misma dimensión" (matrix/operate, add/sub) es
  FORMA: se valida en el serializer.
- "La matriz es singular" (matrix/operate, inverse) es MATEMÁTICA: la
  descubre `core/matrix_tools.inverse` con un `ValueError`, y la vista lo
  traduce a 400.
- "El intervalo no tiene cambio de signo" (los cuatro métodos numéricos) es
  MATEMÁTICA: la descubre `core/numeric/*`, no un chequeo de Bolzano
  repetido en el serializer.

---

## 7. Capacidad conocida pero no expuesta

Lo que sigue quedó **fuera de alcance a propósito**, con evidencia concreta en el código de que es una decisión, no un olvido silencioso.

### 7.1. Funciones de `frontend/src/api/client.ts` sin endpoint

Eran cinco; `errorAbsRel` (issue #9) y `errorAcumulado` (issue #8) ya tienen endpoint (sección 3). `errorPropagation`, `derivativeMethod` e `integralMethod` siguen llamando a rutas que **no existen** en `api/urls.py`:

| Función | Ruta que llama | ¿Existe en `api/urls.py`? |
|---|---|---|
| `errorAcumulado` | `POST api/v1/numeric/error-accumulation` | Sí (issue #8) |
| `errorAbsRel` | `POST api/v1/numeric/abs-rel-error` | Sí (issue #9) |
| `errorPropagation` | `POST api/v1/numeric/propagation-error` | No |
| `derivativeMethod` | `POST api/v1/calculus/derivate` | No |
| `integralMethod` | `POST api/v1/calculus/integral` | No |

Son componentes de frontend que se portaron **tal cual** en la Fase 6 (junto con el resto de `frontend/`), pero cuyo endpoint nunca se construyó porque no hay una función equivalente en `core/`: no hay error acumulado, error absoluto/relativo, propagación de error, derivadas ni integrales simbólicas independientes en el motor matemático de este repo (Newton-Raphson deriva internamente con `sympy.diff`, pero no hay un endpoint que exponga "derivar esta expresión" como operación propia). Conectar estos cinco pediría escribir la función en `core/` primero — no es trabajo de adaptador, es motor nuevo.

Si se llaman hoy, fallan con un 404 de Django (ninguna vista responde en esa ruta), no con un error de la API.

### 7.2. `verify_transpose_props` / `verify_inverse_props`

`core/matrix_tools.py` las tiene y funcionan — las usa `inverse()` internamente (`check_props=True` por defecto) y el CLI las expone en su menú de matrices — pero **devuelven un bloque de texto plano** (`str`, con líneas "OK"/"FALSO"/"No evaluada"), no datos estructurados. No hay endpoint porque no hay un contrato JSON razonable que exponer: el frontend necesitaría parsear ese texto para renderizarlo campo por campo, que es exactamente el patrón que el resto de la API evita (cada adaptador arma la estructura que el frontend consume directo, nunca un bloque de texto para parsear del otro lado). Exponerlas de verdad exige antes reescribirlas en `core/` para que devuelvan una lista de `{propiedad, cumple, detalle}` en vez de un string — trabajo de motor, no de adaptador.

### 7.3. Otros dos, más chicos, con la misma raíz

- **Producto `Ax`** (`core.vector_tools.matrix_vector_product_steps`): el CLI lo expone (`run_matrix_times_vector`, ver `documentation/Vectores.md` sección 5); `vectors/operate` no tiene una operación para "matriz por vector" — sus 6 operaciones son todas entre vectores.
- **`iterations_estimate` para Newton-Raphson y Secante**: el frontend espera esa sección con forma propia (`formula_newton`/`formula_secant`, etc.) en la respuesta de esos dos endpoints, pero `core/numeric/metodos_abiertos.py` no calcula ninguna cota de iteraciones de forma cerrada para métodos abiertos (sí existe para bisección, `log₂((b-a)/E)` — ver `documentation/MetodosNumericos.md`, sección 3). Marcado explícitamente como "GAP CONOCIDO" en el docstring de `api/adapters/numerico.py`: el adaptador deja esa sección sin poblar y el frontend usa acceso opcional (`?.`) en cada campo, así que queda vacía en vez de romper.

---

## 8. Qué no persiste en base de datos

La app tiene `db.sqlite3` porque Django lo requiere para
`django.contrib.sessions`/`auth`/etc. en `INSTALLED_APPS`, pero **ninguna
vista de la API guarda ni lee datos de la base**: cada cómputo es puro, a
partir de lo que llega en el `POST` de esa misma request. No hay historial
de cálculos entre sesiones ni entre backend y frontend más allá de lo que
el frontend cachea en `localStorage` del lado del navegador.

---

## 9. Ejecutar y probar

```bash
cd linear_algebra_calculator
python manage.py runserver
```

```bash
cd frontend
npm install
npm run dev
```

Con ambos corriendo, el frontend en `http://localhost:5173` habla con la
API en `http://localhost:8000/api/v1/`.

Los tests de los endpoints (`tests/test_api_*.py`, en la raíz del repo)
usan `rest_framework.test.APIClient` directo, no `django.test.TestCase`:
ninguna vista toca base de datos, así que no hace falta la maquinaria de
transacciones/DB de prueba de Django, y los tests corren con el mismo
`python -m unittest discover tests` que el resto de la suite -- no con
`manage.py test`.
