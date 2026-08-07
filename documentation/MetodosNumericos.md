# Documentación de Métodos Numéricos (búsqueda de raíces)

> **Archivos:**\
> `core/numeric/_expresiones.py` (parseo de f(x), derivada simbólica)\
> `core/numeric/metodos_cerrados.py` (Bisección, Regla Falsa)\
> `core/numeric/metodos_abiertos.py` (Newton-Raphson, Secante)\
> (interfaz) `cli/numeric_io.py` (entrada/salida por consola), `cli/numerical_methods_runners.py`, `cli/startup.py` opción `[8]`

Documento técnico que describe los cuatro métodos de búsqueda de raíces del proyecto: dos cerrados (requieren un intervalo con cambio de signo) y dos abiertos (requieren punto(s) inicial(es), sin garantía de convergencia).

---

## 1. Resumen general

Los cuatro métodos comparten la misma forma de entrada (una función como texto, p. ej. `"x**2 - 4"`) y el mismo núcleo de salida: un diccionario con `raiz`, `iteraciones`, `historial` (una entrada por iteración), `error_final`, `metodo`, `funcion_latex`, `detalles` (explicación LaTeX por iteración), `conclusion`, y opcionalmente `advertencia`.

`core/numeric/` es puro cálculo: 0 `input()`, 0 `print()`. Toda la entrada/salida por consola vive en `cli/numeric_io.py` y `cli/numerical_methods_runners.py`.

No hay equivalente en la interfaz web: sigue siendo una operación exclusiva del CLI.

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

## 7. Ejemplo de uso programático

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
