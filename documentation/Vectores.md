# Documentación de Vectores

> **Archivos:**\
> `core/vector.py` (clase `Vector`)\
> `core/vector_tools.py` (lectura, propiedades, combinación lineal, producto Ax)\
> (interfaz CLI) `cli/vector_runners.py`\
> (interfaz API) `api/adapters/vectores.py`, `POST /api/v1/vectors/operate` y `POST /api/v1/vectors/combination`

Documento técnico que describe las operaciones con vectores en Rⁿ del proyecto: la clase `Vector`, la verificación de los 6 axiomas de espacio vectorial, la combinación lineal / ecuación vectorial, y el producto matriz-vector.

---

## 1. Resumen general

`core/vector.py` y `core/vector_tools.py` no tienen entrada/salida: reciben datos ya parseados y devuelven resultados o texto para imprimir. Lo interactivo vive fuera: por consola en `cli/vector_runners.py`, por HTTP en `api/adapters/vectores.py`.

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

**"¿Es b combinación lineal de v₁..vₖ?" es exactamente "¿tiene solución Ax = b?"** con `A = [v₁ v₂ ... vₖ]` (los vectores como columnas). Por eso `run_vector_combination()` en el CLI, y `linear_combination()` en `api/adapters/vectores.py`, no reimplementan nada: arman `A` con los vectores como columnas y llaman a `matrix_reduce(method="gauss-jordan", A, b)` (el mismo adaptador de `matrix/reduce`, ver `documentation/GaussJordanMethod.md`) — la misma llamada que ya resuelve cualquier sistema.

Lo que sí es propio de esta operación:

1. La construcción de `A` a partir de los vectores columna.
2. La verificación explícita componente a componente con `linear_combination_verification_steps`, usando la solución particular (libres = 0) del `summary` que devuelve `matrix_reduce`.
3. La conclusión en lenguaje de combinación lineal en vez de "tipo de solución":
   - `status == "unique"` o `"infinite"` → `is_linear_combination: true`, "b es una combinación lineal de las columnas de A".
   - `status == "inconsistent"` → `is_linear_combination: false`.

---

## 5. Producto Ax: qué es y qué no es

`run_matrix_times_vector()` (CLI) **calcula** `Ax`, no resuelve un sistema. No hay `status`/`solution` al estilo Gauss-Jordan: sólo un vector resultado. Además hace un paso pedagógico extra: una vez calculado `b := Ax`, resuelve `A·c = b` con Gauss-Jordan como verificación (siempre consistente por construcción, porque `b` se definió como `Ax`).

**No expuesto vía API**: no existe un endpoint para el producto `Ax` — `vectors/operate` tiene 6 operaciones entre vectores (sección 6), y ninguna toma una matriz. Es capacidad conocida y no expuesta, no un descuido: ver `documentation/AppWeb.md`, sección "Capacidad conocida pero no expuesta".

---

## 6. Interfaz CLI

`cli/vector_runners.py` expone 4 runners, todos bajo el submenú `[5] Vectores ▸` de `cli/startup.py`:

| Opción | Runner | Qué hace |
|---|---|---|
| `[1]` | `run_vector_calc()` | Suma, resta, escalar, combinaciones `c·u+d·v`, producto punto — sobre `Vector`. |
| `[2]` | `run_vector_combination()` | Combinación lineal / ecuación vectorial (sección 4). |
| `[3]` | `run_matrix_times_vector()` | Producto Ax + verificación (sección 5). |
| `[4]` | `run_vector_props()` | Los 6 axiomas de `verify_vector_properties` (sección 3). |

---

## 7. Interfaz API

`api/adapters/vectores.py` expone dos endpoints:

| Endpoint | Operaciones | Devuelve |
|---|---|---|
| `POST /api/v1/vectors/operate` | `add`, `sub`, `escalar`, `comb2`, `comb3`, `dot` (`OPERACIONES` en el adaptador) | `{input, steps, result}`. Cinco de las seis devuelven `result: {vector, vector_pretty}`; `dot` es la excepción y devuelve `result: {scalar, scalar_pretty}` — cambia de shape porque el resultado no es un vector. |
| `POST /api/v1/vectors/combination` | Combinación lineal (sección 4) | `{input, gauss_jordan: {steps, summary}, check: {Ax, ok, verification_steps}, result: {is_linear_combination, coefficients_particular, columns_statement}}` |

`dot` usa las claves `v`/`w` en el payload (`vectors: {v: ..., w: ...}`), no `u`/`v` como las demás operaciones — así arma el request el frontend (`AlgebraicMethods.tsx`), no una inconsistencia del adaptador.

`vector_operate` también arma, para cada operación, un bloque `diagram` (`{vectors: [{label, from, to, emphasis?}]}`) con las coordenadas de cada vector involucrado desde el origen — formato de presentación puro para que el frontend pueda dibujar flechas en 2D/3D. Ningún componente del frontend lo consume hoy (verificado: `diagram` no aparece en ningún `.tsx`); se mantiene disponible porque no cuesta nada, no porque haya una vista que lo pinte.

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
