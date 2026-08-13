# Documentación de Operaciones con Matrices

> **Archivos:**\
> `core/matrix_tools.py`\
> (interfaz CLI) `cli/matrix_runners.py`, `utils/matrix_memory.py`\
> (interfaz API) `api/adapters/matrices.py`, `api/adapters/properties.py`

Documento técnico que describe las operaciones con matrices que no son sistemas de ecuaciones: aritmética matricial, determinante, inversa, rango/núcleo, traspuesta, y las verificaciones de propiedades algebraicas.

---

## 1. Resumen general

`core/matrix_tools.py` trabaja sobre `Matrix = List[List[float]]` (listas planas, no una clase propia). Cada operación aritmética devuelve `(resultado, texto_de_pasos)`, donde `texto_de_pasos` es un string multilínea, no un `frame` al estilo Gauss-Jordan — salvo `inverse()`, que sí puede poblar un `frame` si se le pasa uno.

No hay clase `Matrix` involucrada aquí (no confundir con `core/matrix.py`, que es la clase base de la que heredan `GaussMethod`, `GaussJordanMethod` y `CramerMethod`): `matrix_tools.py` es un módulo de funciones puras sobre listas de listas.

---

## 2. Validaciones y formas

- `shape_of(M) -> (filas, columnas)`
- `same_size(A, B) -> bool`
- `mult_compatible(A, B) -> bool` — `columnas(A) == filas(B)`.

---

## 3. Operaciones con dos matrices

| Función | Firma | Requiere |
|---|---|---|
| `add_matrices` | `(A, B) -> (C, texto)` | `same_size(A, B)` |
| `sub_matrices` | `(A, B) -> (C, texto)` | `same_size(A, B)` |
| `scalar_mult` | `(alpha, A) -> (C, texto)` | — |
| `transpose` | `(A) -> (T, texto)` | — |
| `matmul` | `(A, B) -> (C, texto)` | `mult_compatible(A, B)` |

Cada una arma `texto` con una línea por fila del resultado (`add_matrices`/`sub_matrices`/`scalar_mult`) o una línea por celda (`matmul`, `c_ij = ...`). Todas lanzan `ValueError` con un mensaje explícito si las dimensiones no calzan.

## 4. Operaciones en cadena (N matrices)

- `sum_many(mats) -> (C, texto)` — `M1 + M2 + ... + Mk`, exige al menos 2 matrices del mismo tamaño.
- `sub_many(first, rest) -> (C, texto)` — `M1 - M2 - ... - Mk`.
- `matmul_chain(mats) -> (C, texto)` — `M1·M2·...·Mk`, verifica compatibilidad en cada paso y concatena el texto de cada `matmul` intermedio.

---

## 5. Rango y núcleo

```py
_rref_matrix(A, tol=1e-12) -> (M_rref, rango)
rank_of(A, tol=1e-12) -> int
nullspace_vector(A, tol=1e-12) -> Optional[List[float]]
```

`rank_of` lleva una copia de `A` a RREF (pivoteo parcial por filas) y cuenta los pivotes no nulos. `nullspace_vector` intenta construir un vector `x ≠ 0` tal que `Ax = 0`: si el sistema homogéneo asociado sólo tiene la solución trivial (rango = columnas), devuelve `None`; si no, fija la primera variable libre en `1` y despeja las básicas.

---

## 6. Determinante, singularidad e inversa

```py
determinant(A, tol=1e-12) -> float
is_singular(A, tol=1e-12) -> Optional[bool]
inverse(A, tol=1e-12, frame=None, b=None, check_props=True) -> (Ainv, texto)
```

- `determinant`: reducción tipo Gauss-Jordan con pivoteo parcial, acumulando el producto de los pivotes y el signo de los intercambios de fila. Lanza `ValueError` si `A` no es cuadrada. Devuelve `0.0` si `A` es singular (no lanza excepción en ese caso).
- `is_singular`: `None` si `A` no es cuadrada; si no, `abs(determinant(A)) <= tol`.
- `inverse`: Gauss-Jordan sobre `[A | I]`. Si `A` es singular, **no** intenta la reducción: lanza `ValueError` con un mensaje pedagógico que incluye el determinante, el rango, y un vector no trivial del núcleo si existe. Si `A` es invertible, además de `Ainv` calcula la matriz de cofactores, la adjunta, y `Adj(A)/det(A)` como verificación cruzada del resultado.

**El parámetro `frame`:** si se pasa un `dict`, `inverse()` llama a `log_step` en cada paso (matriz aumentada inicial, cada operación elemental, RREF, resultado, cofactores, adjunta, determinante) — el mismo formato que usan `GaussJordanMethod`/`GaussMethod`, así que se puede imprimir con `print_frame` (CLI) o `frame_to_html` (web) sin ningún adaptador. Es la única función de este archivo que integra directamente con ese contrato; las demás sólo devuelven texto plano.

**El parámetro `b`:** si se pasa un vector, además de la inversa se verifica `x = A⁻¹b` contra `Ax = b`, y ese chequeo se agrega al texto de salida (y al `frame`, si se pasó uno).

---

## 7. Verificación de propiedades algebraicas

```py
verify_transpose_props(A, B=None) -> str
verify_inverse_props(A, B=None, tol=1e-12) -> str
```

Devuelven un bloque de texto con cada propiedad marcada `OK`, `FALSO`, o `No evaluada` (cuando falta `B` o las dimensiones no son compatibles para esa propiedad puntual):

**Traspuesta:** dimensiones de `A` y `Aᵀ`; `(Aᵀ)ᵀ = A`; `(αA)ᵀ = αAᵀ` (con `α=2`); `(A+B)ᵀ = Aᵀ+Bᵀ`; `(AB)ᵀ = BᵀAᵀ`.

**Inversa** (requiere `A` cuadrada e invertible; si no, devuelve `"No evaluada: ..."` con el motivo):
- a) `(A⁻¹)⁻¹ = A`
- b) `(AB)⁻¹ = B⁻¹A⁻¹` (si se da `B` y es compatible)
- c) `(Aᵀ)⁻¹ = (A⁻¹)ᵀ`

`verify_inverse_props` es la que usa internamente `inverse()` cuando `check_props=True` (el valor por defecto); se pasa `check_props=False` en las llamadas internas para evitar recursión.

---

## 8. Interfaz interactiva (CLI)

`cli/matrix_runners.py` expone un menú (`[6] Matrices` en `cli/startup.py`) con: suma/resta/escalar en cadena, multiplicación en cadena, traspuesta, inversa, y una **memoria de resultados** (`utils/matrix_memory.py`) que permite nombrar una matriz calculada y reutilizarla como entrada de la siguiente operación sin volver a teclearla — es una conveniencia sólo del CLI, no existe equivalente en la web (cada request HTTP es independiente).

---

## 9. Interfaz API

Dos endpoints, con las 8 operaciones aritméticas y las 3 propiedades separadas — porque no comparten shape de respuesta (una devuelve una matriz, la otra no):

| Endpoint | Adaptador | Cubre |
|---|---|---|
| `POST /api/v1/matrix/operate` | `api/adapters/matrices.py` | `add`, `sub`, `scalar`, `transpose`, `matmul`, `sum_many`, `sub_many`, `matmul_chain`, `inverse` — las 9 operaciones de las secciones 3, 4 y 6 (`inverse` incluida). Cada una arma `{input, steps, result: {matrix, matrix_pretty}}`; `inverse` usa el `frame` real (sección 6) traducido al envelope `step_states`. |
| `POST /api/v1/matrix/determinant` | (ver `documentation/CramerMethod.md`, sección 8) | `method=sarrus`/`cofactors` sobre `core/cramer.py`, no sobre `determinant()` de este archivo — `matrix_tools.determinant()` se usa internamente en otros adaptadores (`matrix/reduce`, `matrix/properties`) pero no tiene endpoint propio. |
| `POST /api/v1/matrix/properties` | `api/adapters/properties.py` | `rank_of`, `is_singular`, `nullspace_vector` (sección 5). Documentado aparte en `documentation/MatrixProperties.md`. |

A diferencia de la vieja web de templates de este proyecto (retirada), **sí** se exponen las operaciones que necesitan dos matrices — suma, resta, multiplicación, y las versiones en cadena — todas vía `matrix/operate`.

**No expuesto**: `verify_transpose_props`/`verify_inverse_props` (sección 7) no tienen endpoint. Devuelven un bloque de texto plano formateado para consola, no datos estructurados — conectarlos a un endpoint JSON exigiría antes reescribirlos para que devuelvan algo que el frontend pueda renderizar campo por campo, no un `<pre>` con el texto del CLI adentro. Ver `documentation/AppWeb.md`, sección "Capacidad conocida pero no expuesta".

---

## 10. Ejemplo de uso programático

```py
from core.matrix_tools import determinant, inverse, rank_of

A = [[4.0, 7.0], [2.0, 6.0]]
print(determinant(A))          # 10.0

Ainv, texto = inverse(A)
print(Ainv)                    # [[0.6, -0.7], [-0.2, 0.4]]

singular = [[1.0, 2.0], [2.0, 4.0]]
print(rank_of(singular))       # 1
```
