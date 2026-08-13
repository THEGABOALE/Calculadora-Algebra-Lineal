# Documentación de Métodos Numéricos (búsqueda de raíces)

> **Archivos:**\
> `core/numeric/_expresiones.py` (parseo de f(x), derivada simbólica)\
> `core/numeric/metodos_cerrados.py` (Bisección, Regla Falsa)\
> `core/numeric/metodos_abiertos.py` (Newton-Raphson, Secante)\
> (interfaz CLI) `cli/numeric_io.py` (entrada/salida por consola), `cli/numerical_methods_runners.py`, `cli/startup.py` opción `[8]`\
> (interfaz API) `api/adapters/numerico.py`, `api/adapters/latex.py`

Documento técnico que describe los cuatro métodos de búsqueda de raíces del proyecto: dos cerrados (requieren un intervalo con cambio de signo) y dos abiertos (requieren punto(s) inicial(es), sin garantía de convergencia).

---

## 1. Resumen general

Los cuatro métodos comparten la misma forma de entrada (una función como texto, p. ej. `"x**2 - 4"`) y devuelven un diccionario. Claves comunes a los cuatro: `raiz`, `iteraciones`, `historial` (una entrada por iteración, ver secciones 4 y 5 para las claves exactas de cada fila), `error_final`, `metodo`, `funcion_latex`, `detalles` (una entrada `{iteracion, lineas}` por iteración, con el desarrollo en LaTeX), `conclusion` (dict: `raiz`, `iteraciones`, `criterio_paro`, `latex`), y opcionalmente `advertencia` (si se alcanzó `max_iter` sin converger). Los cerrados agregan además `intervalo_final` y `criterio`, y opcionalmente `estimacion_iteraciones` (sección 3); Newton-Raphson agrega `derivada_latex`.

`core/numeric/` es puro cálculo: 0 `input()`, 0 `print()`. La entrada/salida por consola vive en `cli/numeric_io.py` y `cli/numerical_methods_runners.py`; la entrada/salida HTTP, en `api/adapters/numerico.py` (sección 7).

---

## 2. Evaluación de funciones

`core/numeric/_expresiones.py` parsea `f(x)` con `sympy` en vez de `eval()`:

```py
parsear(f_str: str) -> (expr, x)
compilar(f_str: str) -> (f, expr, x)      # f es una función numérica (lambdify)
derivar(expr, x, derivada_str=None)       # -> (f_prime, expr_prime)
evaluar(f, x_val, f_str="") -> float
error_relativo(x_nuevo, x_viejo) -> float
```

`^` se traduce a `**` antes de parsear (igual que antes): en sympy, como en Python, `^` es XOR, no potencia, y sin la traducción `x^2` parsearía silenciosamente distinto de `x**2`.

Funciones soportadas: `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `sqrt`, `abs`, `pi`, `e`. Un nombre de función no reconocido (`sen(x)`, típico error al escribir en castellano) o una variable distinta de `x` levantan `ValueError` con el nombre problemático — sympy no lo hace por sí solo: una función desconocida parsea como "función indefinida" sin fallar, así que la validación está en `parsear()`, no delegada al parser.

**Import diferido, a propósito:** `sympy` se importa dentro de las funciones de `_expresiones.py`, nunca a nivel de módulo. `cli/startup.py` importa `cli.numerical_methods_runners` a nivel de módulo, así que si `core/numeric/` importara `sympy` arriba, el CLI entero pagaría esa carga en cada arranque, antes de mostrar el menú, aunque el usuario sólo fuera a resolver una matriz. Mismo motivo por el que `utils/symbolic_equations.py` aísla `symengine`.

`evaluar_funcion` y `calcular_error_relativo`, que antes vivían duplicadas — cuerpo idéntico — en `metodos_cerrados.py` y `metodos_abiertos.py`, ahora son una sola implementación acá.

---

## 3. Criterio de paro

Los cuatro métodos aceptan `tolerancia` (antes `error_deseado`). Los cerrados, además, aceptan `criterio`:

| `criterio` | corta cuando | default |
|---|---|---|
| `"error_relativo"` | error relativo porcentual entre iteraciones sucesivas `< tolerancia` | **sí** |
| `"intervalo"` | longitud del intervalo `< tolerancia` | no |

Con `criterio="intervalo"` el resultado incluye además `estimacion_iteraciones`: la cota `n ≥ log₂((b−a)/tolerancia)`, calculada antes de iterar.

Los métodos abiertos (Newton-Raphson, Secante) sólo soportan error relativo — no hay intervalo del que calcular una longitud.

**El default cambia según quién llama.** `core/` por defecto usa `"error_relativo"` (para no alterar el significado de `tolerancia` en llamadas que ya existían antes de que `criterio` existiera). La API (`api/adapters/numerico.py`) fuerza `criterio="intervalo"` **siempre** para bisección y regla falsa, sin exponer el parámetro en el serializer — porque el encabezado de columna que muestra el frontend dice literalmente "xu-xi < E", y mostrar un criterio distinto del que efectivamente se usó sería mentir en la tabla. El CLI, en cambio, deja el default de `core/` (`error_relativo`) salvo que el usuario pida explícitamente el otro. No hay forma de pedirle a la API el criterio de error relativo para los métodos cerrados hoy.

---

## 4. Métodos cerrados

Ambos exigen `f(a)·f(b) < 0` antes de empezar (además de `a < b` y `tolerancia > 0`); si no se cumple, lanzan `ValueError`. **Esta validación vive en el motor**, no en quien lo llama: `verificar_intervalo(f_str, a, b)` es pública y la usan tanto `metodo_biseccion` como `metodo_regla_falsa` internamente.

```py
metodo_biseccion(f_str, a, b, tolerancia, criterio="error_relativo", max_iter=100) -> Dict
```

Punto medio `xr = (a+b)/2` en cada iteración; actualiza `[a, xr]` o `[xr, b]` según el signo de `f(a)·f(xr)`.

```py
metodo_regla_falsa(f_str, a, b, tolerancia, criterio="error_relativo", max_iter=100) -> Dict
```

Igual esquema, pero el siguiente punto es la intersección de la secante entre `(a, f(a))` y `(b, f(b))` con el eje x: `xr = b - f(b)·(b-a)/(f(b)-f(a))`, en vez del punto medio. Si `f(b) - f(a) = 0` en alguna iteración (secante horizontal), levanta `ZeroDivisionError`.

Si se alcanza `max_iter` sin converger, el resultado incluye `advertencia: "Alcanzado número máximo de iteraciones"` en vez de fallar.

---

## 5. Métodos abiertos

No requieren cambio de signo, sólo punto(s) inicial(es); pueden no converger o diverger.

```py
metodo_newton_raphson(f_str, x0, tolerancia, max_iter=100, derivada=None) -> Dict
```

`x_{n+1} = x_n - f(x_n)/f'(x_n)`. La derivada es **simbólica** (`sympy.diff`), no numérica: exacta, sin error de truncamiento. Si `derivada` es un string, se usa esa expresión en vez de derivar. Levanta:

- `ValueError` si la derivada es idénticamente cero (función constante) — no hay forma de que Newton avance.
- `ZeroDivisionError` si `f'(x_k) = 0` en alguna iteración puntual, aunque la derivada no sea nula en general.

```py
metodo_secante(f_str, x0, x1, tolerancia, max_iter=100) -> Dict
```

`x_{n+1} = x_n - f(x_n)·(x_n - x_{n-1})/(f(x_n) - f(x_{n-1}))`. No necesita derivada, sólo dos puntos iniciales. Si `f(x_n) - f(x_{n-1}) = 0` en alguna iteración, levanta `ZeroDivisionError`.

**Cambio de comportamiento respecto de la versión anterior:** las degeneraciones (derivada nula, denominador nulo) antes devolvían un resultado con `advertencia` y una "raíz" aproximada; ahora levantan excepción. Son condiciones donde la fórmula del método no está definida, no un resultado aproximado — devolver una raíz ahí afirmaba algo que el método no había calculado.

---

## 6. Interfaz interactiva (CLI)

La entrada/salida por consola vive en `cli/numeric_io.py`: `solicitar_datos_metodo_cerrado`/`solicitar_datos_newton`/`solicitar_datos_secante`, `imprimir_tabla_iteraciones`/`imprimir_tabla_newton`/`imprimir_tabla_secante`, `imprimir_resultado_cerrado`/`imprimir_resultado_abierto`.

`cli/numerical_methods_runners.py` expone `run_biseccion`, `run_regla_falsa`, `run_newton_raphson`, `run_secante`, que llaman a esas funciones de I/O y al motor de `core/numeric/`.

Newton-Raphson ya no pide la derivada como paso obligatorio (se deriva sola); sigue ofreciendo la opción de escribirla a mano.

Menú de tres niveles bajo `[8] Métodos Numéricos ▸` en `cli/startup.py`:

```
[8] Métodos Numéricos ▸
  [1] Métodos Cerrados ▸
    [1] Bisección
    [2] Regla Falsa
  [2] Métodos Abiertos ▸
    [1] Newton-Raphson
    [2] Secante
```

---

## 7. Interfaz API

| Endpoint | `core/` que llama | `criterio` |
|---|---|---|
| `POST /api/v1/numeric/bisection-method` | `metodo_biseccion` | forzado a `"intervalo"` |
| `POST /api/v1/numeric/false-position` | `metodo_regla_falsa` | forzado a `"intervalo"` |
| `POST /api/v1/numeric/newton-raphson` | `metodo_newton_raphson` | — (no aplica) |
| `POST /api/v1/numeric/secant` | `metodo_secante` | — (no aplica) |

**Entrada en LaTeX, no en texto plano.** El frontend tiene un teclado matemático que produce LaTeX; `api/adapters/latex.py::latex_a_texto` lo traduce a la sintaxis de texto que espera `core/numeric` (`sympy.parsing.latex.parse_latex`, que necesita `antlr4-python3-runtime`). Esa dependencia queda confinada al adaptador — ni `core/` ni el CLI la cargan nunca.

**Los nombres de campo cambian respecto de `core/`**, porque el frontend se portó de otro repo con su propio vocabulario y no vale la pena reescribirlo para que coincida con el español de `core/`. `api/adapters/numerico.py` hace el rename fila por fila:

| `core/` (español) | API (inglés) | Sólo en |
|---|---|---|
| `iteracion` | `iteration` | los 4 |
| `a` / `b` | `xl` / `xu` | cerrados |
| `f(a)` / `f(b)` | `yl` / `yu` | cerrados |
| `xr` / `f(xr)` | `xr` / `yr` | cerrados |
| `x` / `f(x)` / `f'(x)` / `x_nuevo` | `xk` / `fxk` / `fprimexk` / `x_next` | Newton |
| `x_{n-1}` / `x_n` / `x_{n+1}` | `x_prev` / `x_curr` / `x_next` | secante |
| `f(x_{n-1})` / `f(x_n)` / `f(x_{n+1})` | `f_prev` / `f_curr` / `f_next` | secante |
| `error` | `Ea` | los 4 |

Además agrega dos campos derivados que `core/` no calcula: `interval_length` (`xu - xl`, sólo en los cerrados) y `Ea_lt_E` (`error < tolerancia`, booleano, en los 4) — ambos se computan en el adaptador a partir de datos que la fila ya trae, no piden nada nuevo al motor.

**`float('inf')` no es JSON válido.** La primera fila de cualquier historial trae `error = inf` (no hay iteración anterior con la que comparar) — DRF revienta al serializar un `inf` crudo. El adaptador lo sanea a `None` con `_finito()` antes de armar la respuesta; `Ea_lt_E` se calcula *antes* de sanear, sobre el float crudo (`inf < tolerancia` da `False` de forma natural, sin caso especial).

**Gap conocido, marcado explícitamente en el código** (no es un olvido silencioso): el frontend espera, para Newton y secante, una sección `iterations_estimate` con forma propia (`formula_newton`/`formula_secant`, etc.) — pero no hay una cota de iteraciones de forma cerrada para esos métodos como sí la hay para bisección (`log₂`, sección 3). El adaptador la deja sin poblar; el frontend usa acceso opcional (`?.`) en cada campo, así que esa sección queda vacía en vez de romper.

---

## 8. Ejemplo de uso programático

```py
from core.numeric.metodos_cerrados import metodo_biseccion, verificar_intervalo
from core.numeric.metodos_abiertos import metodo_newton_raphson

# raíz de x^2 - 2 = sqrt(2) ≈ 1.41421356
verificar_intervalo("x**2 - 2", 1.0, 2.0)          # True

r1 = metodo_biseccion("x**2 - 2", 1.0, 2.0, tolerancia=1e-6)
print(r1["raiz"])          # ~1.4142141342

# derivada simbólica (sympy.diff), exacta
r2 = metodo_newton_raphson("x**2 - 2", x0=1.5, tolerancia=1e-6)
print(r2["raiz"])          # ~1.4142135624
print(r2["derivada_latex"])  # "2 x"

# criterio por longitud de intervalo, con estimación previa de iteraciones
r3 = metodo_biseccion("x**2 - 2", 1.0, 2.0, tolerancia=1e-8, criterio="intervalo")
print(r3["estimacion_iteraciones"]["n_minimo"])
```
