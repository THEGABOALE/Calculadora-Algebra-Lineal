# Documentación de Vectores

> **Archivos:**\
> `core/vector.py` (clase `Vector`)\
> `core/vector_tools.py` (lectura, propiedades, combinación lineal, producto Ax)\
> (interfaz) `cli/vector_runners.py` y las rutas `/vectorInput/`, `/vectorResolution/`,
> más los métodos `combinacion_lineal` y `ax` de `/ecuationResolution/`

Documento técnico que describe las operaciones con vectores en Rⁿ del proyecto: la clase `Vector`, la verificación de los 6 axiomas de espacio vectorial, la combinación lineal / ecuación vectorial, y el producto matriz-vector.

---

## 1. Resumen general

`core/vector.py` y `core/vector_tools.py` no tienen entrada/salida: reciben datos ya parseados y devuelven resultados o texto para imprimir. Lo interactivo (pedir vectores por consola o por formulario web) vive fuera, en `cli/vector_runners.py` y en `calculator/views.py`.

Todas las operaciones que devuelven un vector devuelven una instancia de `Vector`, no una lista suelta; las que devuelven un desarrollo paso a paso devuelven `(resultado, lista_de_strings)`.

---

## 2. Archivo: `core/vector.py` — clase `Vector`

```py
Vector(data: List[float])
```

Valida que `data` sea una lista de números; convierte todo a `float`. Lanza `ValueError` si no.

### Atributos y propiedades

- `self.data: List[float]`
- `self.n: int` (propiedad) — dimensión del vector.

### Métodos

| Método | Firma | Comportamiento |
|---|---|---|
| `add` | `(other: Vector) -> Vector` | Suma componente a componente. |
| `sub` | `(other: Vector) -> Vector` | Resta componente a componente. |
| `scale` | `(c: float) -> Vector` | Escala por `c`. |
| `dot` | `(other: Vector) -> float` | Producto punto. |
| `equals` | `(other: Vector, tol=1e-12) -> bool` | Igualdad componente a componente bajo tolerancia. |
| `copy` | `() -> Vector` | Copia superficial de los datos. |

`add`, `sub` y `dot` llaman a `_check_same_dim` y lanzan `ValueError` si las dimensiones no coinciden.

`__str__` devuelve `"[v1, v2, ...]"` usando `format_number` (fracciones cuando corresponde, no siempre decimales).

---

## 3. Archivo: `core/vector_tools.py`

### Lectura (CLI)

- `read_vector(dim, prompt="") -> Vector` — pide `dim` valores separados por espacio, admite fracciones (`parse_fraction`), reintenta ante error.
- `read_vectors(cnt, dim, prefix="v") -> List[Vector]` — llama a `read_vector` `cnt` veces.
- `zero_vector(dim) -> Vector` — vector cero de dimensión `dim`.

### Propiedades en Rⁿ

```py
verify_vector_properties(v, w, u, c, d, tol=1e-12) -> List[Tuple[str, bool, str]]
```

Verifica 6 axiomas de espacio vectorial y devuelve una lista de `(nombre, cumple, detalle_texto)`:

1. Conmutativa: `v + w = w + v`
2. Asociativa: `(u + v) + w = u + (v + w)`
3. Existencia de 0: `v + 0 = v`
4. Vector opuesto: `v + (-v) = 0`
5. Distributiva: `c(u + v) = cu + cv`
6. Distributiva: `(c + d)u = cu + du`

Cada verificación compara con `Vector.equals(tol)`, no con `==` exacto.

### Producto Ax y verificación

```py
matrix_vector_product_steps(A: List[List[float]], x: Vector) -> Tuple[List[float], List[str]]
```

Calcula `y = Ax` fila por fila y devuelve, además del resultado, una lista de strings tipo `"2·1 + 3·4 = 14"` por cada fila. Lanza `ValueError` si `x.n != columnas(A)`.

```py
ax_check(A, x_list, b_list, tol=1e-9) -> Tuple[List[float], bool]
```

Calcula `Ax` y devuelve `(Ax, ok)` donde `ok` es `True` si `Ax ≈ b` bajo tolerancia.

### Combinación lineal / ecuación vectorial

```py
linear_combination_verification_steps(coeffs, vectors, b_list) -> Tuple[List[float], List[str]]
```

Dado un conjunto de coeficientes `x₁..xₖ` y vectores `v₁..vₖ`, calcula `y = Σ xᵢvᵢ` componente a componente y devuelve el desarrollo como texto, comparando cada componente contra el objetivo `b_list[j]`.

### Presentación

- `pretty_vector(lst) -> str` — `"[v1, v2, ...]"`.
- `pretty_linear_comb(coeffs, vectors) -> str` — `"c1·v1 + c2·v2 + ..."` (sólo visual, no calcula).
- `pretty_equation_vectorial(prefix_x, k) -> str` — `"Ecuación vectorial: x1·v1 + ... + xk·vk = b"`.

---

## 4. Combinación lineal: cómo se resuelve realmente

**"¿Es b combinación lineal de v₁..vₖ?" es exactamente "¿tiene solución Ax = b?"** con `A = [v₁ v₂ ... vₖ]` (los vectores como columnas). Por eso `run_vector_combination()` en el CLI, y el método `combinacion_lineal` en la web, no reimplementan nada: arman `A` con los vectores como columnas y llaman a `GaussJordanMethod(A, b).run() + .solve_and_log()` — la misma llamada que ya resuelve cualquier sistema.

Lo que sí es propio de esta operación:

1. La construcción de `A` a partir de los vectores columna.
2. La verificación explícita componente a componente con `linear_combination_verification_steps`, usando la solución particular (libres = 0) que devuelve `solve_and_log()`.
3. La conclusión en lenguaje de combinación lineal en vez de "tipo de solución":
   - `status == "unique"` → "b ES combinación lineal... de forma ÚNICA."
   - `status == "infinite"` → "b ES combinación lineal... en INFINITAS formas."
   - `status == "inconsistent"` → "b NO es combinación lineal..."

---

## 5. Producto Ax: qué es y qué no es

`run_matrix_times_vector()` (CLI) y el método `ax` (web) **calculan** `Ax`, no resuelven un sistema. No hay `status`/`solution` al estilo Gauss-Jordan: sólo un vector resultado.

El CLI además hace un paso pedagógico extra: una vez calculado `b := Ax`, resuelve `A·c = b` con Gauss-Jordan como verificación (siempre consistente por construcción, porque `b` se definió como `Ax`). La web no reproduce ese segundo paso: sólo muestra el cómputo de `Ax`.

**Limitación de la ruta web:** `/ecuationResolution/` con `method=ax` reutiliza el campo `vector` del formulario de sistemas, que siempre tiene longitud `filas(A)`. Para que `Ax` tenga sentido, ese vector necesita longitud `columnas(A)`. Si `A` no es cuadrada, `matrix_vector_product_steps` lanza `ValueError` con un mensaje explícito ("columnas(A) deben coincidir con entradas(x)"), capturado por el mismo manejador de errores de la vista. No hay un formulario propio para `x` de longitud distinta a `b`.

---

## 6. Interfaz interactiva (CLI)

`cli/vector_runners.py` expone 4 runners, todos bajo el submenú `[5] Vectores ▸` de `cli/startup.py`:

| Opción | Runner | Qué hace |
|---|---|---|
| `[1]` | `run_vector_calc()` | Suma, resta, escalar, combinaciones `c·u+d·v`, producto punto — sobre `Vector`. |
| `[2]` | `run_vector_combination()` | Combinación lineal / ecuación vectorial (sección 4). |
| `[3]` | `run_matrix_times_vector()` | Producto Ax + verificación (sección 5). |
| `[4]` | `run_vector_props()` | Los 6 axiomas de `verify_vector_properties` (sección 3). |

---

## 7. Interfaz web

| Ruta | Método HTTP | Qué hace |
|---|---|---|
| `/vectorInput/` | GET / POST | Pide la dimensión `n` de los vectores `v` y `w`. |
| `/vectorResolution/` | POST | Recibe `v`, `w`, `method` (`suma`/`resta`/`producto_punto`), calcula y muestra el resultado. |
| `/ecuationResolution/` con `method=combinacion_lineal` | POST | Sección 4. Reutiliza el formulario de sistemas ya existente. |
| `/ecuationResolution/` con `method=ax` | POST | Sección 5. Ídem. |

`vectorResolution` construye su propio `frame` con `log_step` (entrada, resultado) y lo renderiza con `frame_to_html`, igual que el resto de las rutas — no usa una librería ni un patrón de presentación distinto.

---

## 8. Ejemplo de uso programático

```py
from core.vector import Vector
from core.vector_tools import verify_vector_properties, matrix_vector_product_steps

v = Vector([1.0, 2.0])
w = Vector([3.0, 4.0])
print(v.add(w))       # [4, 6]
print(v.dot(w))        # 11

y, pasos = matrix_vector_product_steps([[2.0, 1.0], [1.0, -1.0]], Vector([1.0, 1.0]))
print(y)               # [3, 0]
for paso in pasos:
    print(paso)
```
