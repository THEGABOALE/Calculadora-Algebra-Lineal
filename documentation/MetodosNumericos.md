# Documentación de Métodos Numéricos (búsqueda de raíces)

> **Archivos:**\
> `core/numeric/metodos_cerrados.py` (Bisección, Regla Falsa)\
> `core/numeric/metodos_abiertos.py` (Newton-Raphson, Secante)\
> (interfaz) `cli/numerical_methods_runners.py`, `cli/startup.py` opción `[8]`

Documento técnico que describe los cuatro métodos de búsqueda de raíces del proyecto: dos cerrados (requieren un intervalo con cambio de signo) y dos abiertos (requieren punto(s) inicial(es), sin garantía de convergencia).

---

## 1. Resumen general

Los cuatro métodos comparten la misma forma de entrada (una función como texto, p. ej. `"x**2 - 4"`) y el mismo formato de salida: un diccionario con `raiz`, `iteraciones`, `historial` (una entrada por iteración), `error_final`, `metodo`, y opcionalmente `advertencia` o `nota`.

No hay equivalente en la interfaz web: es una operación exclusiva del CLI.

---

## 2. Evaluación de funciones y seguridad

```py
evaluar_funcion(f_str: str, x: float) -> float
```

Reemplaza `^` por `**` y evalúa con `eval(f_str, {"__builtins__": {}}, safe_dict)`, donde `safe_dict` sólo expone `x`, `pi`, `e`, `abs`, y las funciones de `math` (`sin`, `cos`, `tan`, `exp`, `log`, `log10`, `sqrt`). **Nota de seguridad, decisión existente del proyecto:** es un `eval()` acotado, no una sandbox perfecta (Python permite ciertos escapes incluso con `__builtins__` vacío, vía atributos dunder de objetos), pero es la superficie que ya traía el código portado; no se amplió ni se endureció al incorporarlo. `metodos_cerrados.py` y `metodos_abiertos.py` cada uno tiene su propia copia de esta función y de `calcular_error_relativo`, sin compartir código entre sí — duplicación heredada, no introducida en este proyecto.

---

## 3. Métodos cerrados

Ambos exigen `verificar_intervalo(f_str, a, b)` — `f(a)·f(b) < 0` — antes de empezar; si no se cumple, lanzan `ValueError`.

```py
metodo_biseccion(f_str, a, b, error_deseado, max_iter=100) -> Dict
```

Punto medio `xr = (a+b)/2` en cada iteración; actualiza `[a, xr]` o `[xr, b]` según el signo de `f(a)·f(xr)`. Converge cuando el error relativo porcentual entre iteraciones consecutivas cae debajo de `error_deseado`.

```py
metodo_regla_falsa(f_str, a, b, error_deseado, max_iter=100) -> Dict
```

Igual esquema, pero el siguiente punto es la intersección de la secante entre `(a, f(a))` y `(b, f(b))` con el eje x: `xr = b - f(b)·(b-a)/(f(b)-f(a))`, en vez del punto medio.

Si se alcanza `max_iter` sin converger, el resultado incluye `advertencia: "Alcanzado número máximo de iteraciones"` en vez de fallar.

---

## 4. Métodos abiertos

No requieren cambio de signo, sólo punto(s) inicial(es); pueden no converger o diverger.

```py
calcular_derivada_numerica(f_str, x, h=1e-8) -> float
```

Derivada por **diferencias centrales**: `f'(x) ≈ [f(x+h) - f(x-h)] / (2h)`.

```py
metodo_newton_raphson(f_str, x0, error_deseado, max_iter=100, derivada_str=None) -> Dict
```

`x_{n+1} = x_n - f(x_n)/f'(x_n)`. Si `derivada_str` es `None` (el caso por defecto), la derivada se calcula numéricamente con `calcular_derivada_numerica`; si se provee una derivada como texto, se evalúa directamente con `evaluar_funcion`. Si `|f'(x)| < 1e-15` en algún punto, se detiene con `advertencia: "Derivada muy pequeña (cerca de cero)"` en vez de dividir por un valor casi nulo.

```py
metodo_secante(f_str, x0, x1, error_deseado, max_iter=100) -> Dict
```

`x_{n+1} = x_n - f(x_n)·(x_n - x_{n-1})/(f(x_n) - f(x_{n-1}))`. No necesita derivada, sólo dos puntos iniciales distintos. Si el denominador es casi nulo, se detiene con `advertencia: "Denominador muy pequeño..."`.

Ambos métodos abiertos, además, se detienen anticipadamente con `nota: "f(x) ≈ 0 alcanzado"` si `|f(x)| < 1e-15` en algún punto, incluso si el error relativo todavía no bajó del umbral pedido.

---

## 5. Interfaz interactiva (CLI)

`cli/numerical_methods_runners.py` expone `run_biseccion`, `run_regla_falsa`, `run_newton_raphson`, `run_secante`, cada uno pidiendo los datos por consola (`solicitar_datos_metodo_cerrado`/`solicitar_datos_newton`/`solicitar_datos_secante`), mostrando la tabla de iteraciones (`imprimir_tabla_iteraciones`/`imprimir_tabla_newton`/`imprimir_tabla_secante`) y el resultado final (`imprimir_resultado`).

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

## 6. Ejemplo de uso programático

```py
from core.numeric.metodos_cerrados import metodo_biseccion, verificar_intervalo
from core.numeric.metodos_abiertos import metodo_newton_raphson

# raíz de x^2 - 2 = sqrt(2) ≈ 1.41421356
verificar_intervalo("x**2 - 2", 1.0, 2.0)          # True

r1 = metodo_biseccion("x**2 - 2", 1.0, 2.0, error_deseado=1e-6)
print(r1["raiz"])          # ~1.4142141342

# derivada numérica (h=1e-8), sin proveer una derivada analítica
r2 = metodo_newton_raphson("x**2 - 2", x0=1.5, error_deseado=1e-6)
print(r2["raiz"])          # ~1.4142135624 (converge en 4 iteraciones)
```
