# Documentación de Métodos Numéricos (búsqueda de raíces)

> **Archivos:**\
> `core/numeric/_expresiones.py` (parseo de f(x), derivada simbólica)\
> `core/numeric/metodos_cerrados.py` (Bisección, Regla Falsa)\
> `core/numeric/metodos_abiertos.py` (Newton-Raphson, Secante)\
> (interfaz CLI) `cli/numeric_io.py` (entrada/salida por consola), `cli/numerical_methods_runners.py`, `cli/startup.py` opción `[8]`\
> (interfaz API) `api/adapters/numerico.py`, `api/adapters/latex.py`\
> `core/numeric/errores.py` (error absoluto y relativo, sección 9; error acumulado, sección 10)

Documento técnico que describe los cuatro métodos de búsqueda de raíces del proyecto: dos cerrados (requieren un intervalo con cambio de signo) y dos abiertos (requieren punto(s) inicial(es), sin garantía de convergencia).

---

## 1. Resumen general

Los cuatro métodos comparten la misma forma de entrada (una función como texto, p. ej. `"x**2 - 4"`) y devuelven un diccionario. Claves comunes a los cuatro: `raiz`, `iteraciones`, `historial` (una entrada por iteración, ver secciones 4 y 5 para las claves exactas de cada fila), `error_final`, `metodo`, `funcion_latex`, `detalles` (una entrada `{iteracion, lineas}` por iteración, con el desarrollo en LaTeX), `conclusion` (dict: `raiz`, `iteraciones`, `criterio_paro`, `latex`), y opcionalmente `advertencia` (si se alcanzó `max_iter` sin converger). Los cerrados agregan además `intervalo_final` y `criterio`, y opcionalmente `estimacion_iteraciones` (sección 3); Newton-Raphson agrega `derivada_latex`.

`core/numeric/` es puro cálculo: 0 `input()`, 0 `print()`. La entrada/salida por consola vive en `cli/numeric_io.py` y `cli/numerical_methods_runners.py`; la entrada/salida HTTP, en `api/adapters/numerico.py` (sección 7).

---

## 2. Evaluación de funciones

`core/numeric/_expresiones.py` parsea `f(x)` con `sympy` en vez de `eval()`:

```py
parsear(f_str: str, modo_angular="rad") -> (expr, x)
compilar(f_str: str, modo_angular="rad") -> (f, expr, x)   # f es una función numérica (lambdify)
derivar(expr, x, derivada_str=None)       # -> (f_prime, expr_prime)
evaluar(f, x_val, f_str="") -> float
error_relativo(x_nuevo, x_viejo) -> float
```

`^` se traduce a `**` antes de parsear (igual que antes): en sympy, como en Python, `^` es XOR, no potencia, y sin la traducción `x^2` parsearía silenciosamente distinto de `x**2`.

Funciones soportadas: `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `sqrt`, `abs`, `pi`, `e`. Un nombre de función no reconocido (`sen(x)`, típico error al escribir en castellano) o una variable distinta de `x` levantan `ValueError` con el nombre problemático — sympy no lo hace por sí solo: una función desconocida parsea como "función indefinida" sin fallar, así que la validación está en `parsear()`, no delegada al parser.

**Modo angular.** `modo_angular` (`"rad"` por defecto, o `"deg"`) fija la unidad de los argumentos de `sin`, `cos` y `tan`. Con `"deg"`, el parser construye `sin(pi*arg/180)` (y análogo para `cos`, `tan`) al leer cada llamada, sobre el árbol de sympy y no con reemplazos de texto:

- sólo cambian los argumentos de esas tres funciones: en `x**2 + sin(x)` el `x**2` queda igual; `sin(2*x)` pasa a `sin(pi*x/90)`;
- la conversión ocurre antes de que sympy simplifique la llamada, así que `sin(x + pi)` en grados es `sin(pi*(x + pi)/180)` (el `pi` es el número 3.14159…, no 180°), no `-sin(x)` convertido después;
- no hay trigonométricas inversas soportadas (`asin`, `acos`, `atan`), así que ningún resultado se devuelve como ángulo: el modo afecta sólo a los argumentos;
- funciones sin trigonométricas (`x**2 - 4`, `exp(x) - 2`) dan exactamente el mismo resultado en los dos modos.

Hoy sólo `metodo_secante` expone el modo (issue #24); Newton-Raphson, Bisección y Regla Falsa siguen evaluando en radianes. Un valor distinto de `"rad"`/`"deg"` levanta `ValueError`.

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
metodo_secante(f_str, x0, x1, tolerancia, max_iter=100, modo_angular="rad") -> Dict
```

`x_{n+1} = x_n - f(x_n)·(x_n - x_{n-1})/(f(x_n) - f(x_{n-1}))`. No necesita derivada, sólo dos puntos iniciales. Si `f(x_n) - f(x_{n-1}) = 0` en alguna iteración, levanta `ZeroDivisionError`.

Con `modo_angular="deg"`, `x0`, `x1`, todas las aproximaciones y la raíz están en grados, cada `f(x)` del historial es la función evaluada en grados, y los `detalles` y la `conclusion` marcan las aproximaciones con `^\circ`. `funcion_latex` muestra la función que efectivamente se evaluó (p. ej. `\sin{\left(\frac{\pi x}{180} \right)}`). El resultado incluye `modo_angular`. Ejemplo: `sin(x) - 0.5` con `x0=20`, `x1=40` da 30 en grados y 52.88… en radianes (la raíz de `sin(x) = 0.5` que encuentra el método en radianes).

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

**`angle_mode` (sólo secante):** `"rad"` (default si se omite) o `"deg"`; cualquier otro valor responde `400 VALIDATION_ERROR`. Se pasa hasta `metodo_secante(modo_angular=...)` y la respuesta lo repite en el campo `angle_mode`. Antes del issue #24 el parámetro se aceptaba sin validar y se ignoraba: con `"deg"` la API devolvía la raíz en radianes.

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

---

## 9. Error absoluto y relativo

`core/numeric/errores.py`, expuesto en `POST /api/v1/numeric/abs-rel-error` (issue #9).

```py
calcular_error_absoluto_relativo(valor_verdadero, valor_aproximado, decimales=6) -> Dict
```

Definiciones, con `m` el valor verdadero y `m̃` la aproximación:

- error absoluto: `Ea = |m - m̃|`;
- error relativo: `Er = |m - m̃| / |m|`, sólo si `m ≠ 0`. Con `m = 0` es **indefinido**: `valor`, `texto` y `porcentaje` son `None` y `nota` lo explica. No se inventa un número.

Los dos son siempre `≥ 0`, sea cual sea el signo de `m` y `m̃`. (La implementación del repositorio de referencia calculaba `m - m̃` con signo y rotulaba la fórmula como `xr - x` sobre `x`; acá se usan las definiciones de arriba.)

**Aritmética decimal.** Las entradas se leen con `decimal.Decimal` desde el texto tal como se escribió (`leer_decimal`), no con `float`: un cálculo de error no puede introducir el error de representación que pretende medir (`0.3 - 0.1` da `0.2`, no `0.19999999999999998`). La resta es exacta; el cociente de `Er` se calcula con 50 cifras significativas.

**Entradas admitidas:** enteros, decimales con punto y notación científica (`3.14`, `-2`, `.5`, `1e-5`). Se rechazan con `ValueError` (en la API, `400 VALIDATION_ERROR` con el mensaje por campo): vacío, texto no numérico, `NaN`, infinitos, fracciones `a/b`, coma decimal, magnitudes fuera de `1e-100 … 1e100` y más de 50 cifras significativas.

**Presentación.** `decimales` (0 a 15; 6 por defecto) sólo controla cómo se muestra el resultado, no la precisión interna. Mismo criterio que `format_number`: un valor redondeado al mostrarse lleva `≈` (`0.000477… → "≈ 0.0005"`); uno exacto, no (`"0.0015"`). Un error distinto de cero nunca se muestra como `0`: si con `decimales` quedaría en cero, pasa a notación científica (`1e-9` con 6 decimales → `"1.000000E-9"`). La sustitución usa los valores tal como se ingresaron, sin redondear.

Respuesta de la API (las claves que lee `ErrorAbsRelInputs.tsx`, más campos agregados que el frontend puede ignorar):

```json
{
  "input": {"true_value": "3.1415", "approx_value": "3.14",
            "true_value_pretty": "3.1415", "approx_value_pretty": "3.14", "decimals_display": 4},
  "absolute_error": {"operation": {"numerator": "|m - m̃|"},
                     "formula": {"numerator": "|3.1415 - 3.14|"},
                     "result": "0.0015", "exact": "0.0015"},
  "relative_error": {"operation": {"numerator": "|m - m̃|", "denominator": "|m|"},
                     "formula": {"numerator": "|3.1415 - 3.14|", "denominator": "|3.1415|"},
                     "result": "≈ 0.0005", "exact": "0.000477478911348082…",
                     "percent": "≈ 0.0477 %", "defined": true, "note": null}
}
```

---

## 10. Error acumulado (interés compuesto)

`core/numeric/errores.py`, expuesto en `POST /api/v1/numeric/error-accumulation` (issue #8).

```py
calcular_error_acumulado(monto_inicial, tasa, iteraciones, modo="trunc", decimales_aproximacion=2) -> Dict
```

Compara dos trayectorias que parten del mismo monto `P`, con tasa `r` por período escrita como **fracción decimal** (`0.05` = 5 %):

| | interés del período | saldo |
|---|---|---|
| real (sin aproximaciones) | `I_k = r·R_{k-1}` | `R_k = R_{k-1} + I_k = P(1+r)^k` |
| aproximada | `Ĩ_k = q(r·A_{k-1})` | `A_k = A_{k-1} + Ĩ_k` |

con `R_0 = A_0 = P`. `q` es la operación que se estudia y se aplica al **interés** de cada período antes de sumarlo al saldo, como un banco que acredita intereses en centavos:

- `trunc`: trunca hacia cero (`ROUND_DOWN`): `1.25 → 1.2`, `-1.25 → -1.2` (no `-1.3`, que sería redondear hacia −∞);
- `round`: redondea mitad hacia arriba, lejos de cero (`ROUND_HALF_UP`, igual que la sección 9): `1.25 → 1.3`, `-1.25 → -1.3`, `9.995 → 10.00`.

La trayectoria aproximada se alimenta de su propio saldo anterior `A_{k-1}`: nunca se recalcula desde `P`.

**Qué es cada columna de error:**

- `diferencia_k = I_k − Ĩ_k`: cuánto crece la brecha **en esa iteración**;
- `error_acumulado_k = R_k − A_k = Σ diferencia_j`: el error **total** hasta esa iteración.

La diferencia se descompone en `error_local_k = r·A_{k-1} − Ĩ_k` (lo que `q` quitó o agregó en el período) y `error_propagado_k = r·E_{k-1}` (el interés que no generó el error anterior), así que `E_k = (1+r)·E_{k-1} + error_local_k`. El error acumulado no es sólo la suma de los redondeos: cada centavo perdido deja de ganar interés en los períodos siguientes.

**Decisión respecto del repositorio de referencia.** Allí el "monto real" de cada fila se calculaba sobre el saldo **ya aproximado** (`prev + prev·r` con `prev = A_{k-1}`), así que su "error acumulado" sumaba sólo los errores locales y omitía la propagación. Acá la trayectoria real es la del capital sin ninguna aproximación (`P(1+r)^k`), que es la que permite medir el error que produce la aproximación.

**Ejemplo** (`P = 1000`, `r = 0.05`, truncar a 2 decimales):

| k | I real | Ĩ | R | A | diferencia | E |
|---|---|---|---|---|---|---|
| 1 | 50 | 50.00 | 1050 | 1050.00 | 0 | 0 |
| 2 | 52.5 | 52.50 | 1102.5 | 1102.50 | 0 | 0 |
| 3 | 55.125 | 55.12 | 1157.625 | 1157.62 | 0.005 | 0.005 |
| 4 | 57.88125 | 57.88 | 1215.50625 | 1215.50 | 0.00125 | 0.00625 |

En la iteración 4, el error local es `0.05·1157.62 − 57.88 = 0.001` y el propagado es `0.05·0.005 = 0.00025`. Redondeando, `55.125 → 55.13` deja el aproximado **por encima** del real, y el error final es `−0.00375`.

**Aritmética.** Todo en `Decimal` exacto (salvo `q`, que es el redondeo estudiado), con un contexto de 2000 cifras y trap de `Inexact` que verifica, en vez de suponer, que ninguna operación de las trayectorias redondeó. **Límites:** monto `|P| ≤ 1e15` con hasta 10 decimales (negativo admitido: una deuda), tasa `0 ≤ r ≤ 1` con hasta 10 decimales (`0` explícito admitido; vacío, no), de 1 a 50 iteraciones, de 0 a 10 decimales de aproximación.

**Presentación (API).** `approx_decimals` es parámetro del cálculo; `interest_display_decimals` (0 a 15, 4 por defecto) sólo cambia cómo se muestran la trayectoria real, las diferencias y los errores (con `≈` si se redondean al mostrarse). La trayectoria aproximada se muestra exacta con `approx_decimals` decimales. Los valores exactos van como texto decimal (`difference`, `error_accum`, `amount_real`, `local_error`, `propagated_error`, `summary.final_error_accum`), nunca como `float`. `summary.initial_amout_pretty` (sic) se conserva como alias de `initial_amount_pretty` para compatibilidad.
