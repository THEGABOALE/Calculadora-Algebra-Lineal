# Documentación de Propiedades de Matriz (rango, singularidad, núcleo)

> **Archivos:**\
> `core/matrix_tools.py` (`rank_of`, `is_singular`, `nullspace_vector`)\
> (interfaz API) `api/adapters/properties.py`, `POST /api/v1/matrix/properties`\
> (interfaz CLI) no existe — ver sección 4

Documento técnico sobre el endpoint `matrix/properties`: rango, singularidad y vector del núcleo de una matriz. No tenía documentación propia — vivía repartido entre `documentation/Matrices.md` (sección 5, "Rango y núcleo") y el código del endpoint, sin un documento que describiera el endpoint en sí.

---

## 1. Por qué es un endpoint aparte

`matrix/operate` (ver `documentation/Matrices.md`) tiene 9 operaciones y todas devuelven una matriz (`result.matrix`/`matrix_pretty`). Rango, singularidad y núcleo no encajan en ese shape: son datos escalares/pequeños sobre una matriz, no una matriz transformada. Forzarlos como una décima "operación" de `matrix/operate` habría sido más confuso que un endpoint propio — así que `matrix/properties` es un endpoint separado, sin `steps`/`frame`: no hay un procedimiento paso a paso que mostrar, son tres cálculos independientes sobre la misma `A`.

---

## 2. `core/matrix_tools.py` — las tres funciones

```py
rank_of(A: Matrix, tol: float = 1e-12) -> int
nullspace_vector(A: Matrix, tol: float = 1e-12) -> List[float] | None
is_singular(A: Matrix, tol: float = 1e-12) -> bool | None
```

- `rank_of`: lleva una copia de `A` a RREF (pivoteo parcial por filas, vía `_rref_matrix`) y cuenta los pivotes no nulos. Acepta matrices rectangulares.
- `nullspace_vector`: intenta construir un vector `x ≠ 0` tal que `Ax = 0`. Si el sistema homogéneo asociado sólo tiene la solución trivial (rango = columnas), devuelve `None`. Si no, fija la primera variable libre en `1` y despeja las básicas. También acepta rectangulares.
- `is_singular`: **sólo está definida para matrices cuadradas**. Si `A` no es cuadrada, devuelve `None` — no `False`, no una excepción. Si es cuadrada, `abs(determinant(A)) <= tol`.

Ninguna de las tres exige `A` cuadrada salvo `is_singular`, y esa exigencia se resuelve devolviendo `None`, no rechazando la entrada.

---

## 3. `POST /api/v1/matrix/properties`

**Request:**

```json
{ "A": [[1.0, 2.0], [2.0, 4.0]] }
```

El serializer (`MatrixPropertiesSerializer`) valida sólo forma: que `A` sea una matriz no vacía con todas las filas del mismo largo. **No exige que `A` sea cuadrada** — sería duplicar una decisión que `core/` ya toma sola (`is_singular` devuelve `None`, no error, cuando no lo es).

**Response** (`api/adapters/properties.py::matrix_properties`):

```json
{
  "input": { "operation": "properties", "A": [[1.0, 2.0], [2.0, 4.0]] },
  "result": {
    "rank": 1,
    "is_singular": true,
    "nullspace": [-2.0, 1.0],
    "nullspace_pretty": ["-2", "1"]
  }
}
```

| Campo | Tipo | Notas |
|---|---|---|
| `rank` | `int` | Siempre presente. |
| `is_singular` | `bool \| null` | `null` si `A` no es cuadrada — se propaga el `None` de `core/` tal cual, no se fuerza a `false`. |
| `nullspace` | `List[float] \| null` | `null` si sólo hay solución trivial (matriz de rango completo en columnas). |
| `nullspace_pretty` | `List[str] \| null` | Igual que `nullspace`, formateado con `format_number` (fracciones en vez de decimales cuando corresponde). |

No hay `steps` ni `frame` en la respuesta — a diferencia de casi todos los demás endpoints de la API, este no registra un procedimiento paso a paso.

---

## 4. Interfaz CLI: no existe

**Esto es deliberado, no un olvido.** El CLI expone rango y núcleo indirectamente (Gauss-Jordan calcula y muestra el rango como parte de su resumen — ver `documentation/GaussJordanMethod.md`, sección 4), pero no hay un runner ni una opción de menú que llame a `rank_of`/`is_singular`/`nullspace_vector` directamente y sólo eso. `matrix/properties` es, hoy, la única forma de pedir estos tres datos juntos y de forma aislada sobre una matriz cualquiera.

---

## 5. Frontend

`AlgebraicMethods.tsx` expone dos entradas nuevas en `matrixOperations` — `rank` (`rango(A)`) y `nullspace` (`Núcleo (Ax = 0)`), ambas de una sola matriz de entrada — que interceptan el envío antes del flujo genérico de `matrixOperate` y llaman a `matrixProperties({A})` en cambio. Los dos botones pegan al mismo endpoint, porque `matrix/properties` ya calcula rango, singularidad y núcleo juntos para la misma `A` — no hay razón para pedirlos por separado.

`ResultPretty.tsx::renderMatrixPropertiesResult` hace el render: rango como número, singularidad como "Sí"/"No"/"No definido (A no es cuadrada)" (el tercer valor no es un error — es lo que `is_singular` devuelve cuando `A` no es cuadrada, y hay que mostrarlo sin fingir un booleano), y el núcleo reutilizando el mismo `renderMatrixObject` que pinta cualquier matriz (envuelto como columna `n×1`), sin un componente nuevo para vectores.

---

## 6. Ejemplo de uso programático

```py
from core.matrix_tools import rank_of, is_singular, nullspace_vector

singular = [[1.0, 2.0], [2.0, 4.0]]  # filas dependientes
print(rank_of(singular))        # 1
print(is_singular(singular))    # True
print(nullspace_vector(singular))  # [-2.0, 1.0]

regular = [[4.0, 7.0], [2.0, 6.0]]
print(rank_of(regular))         # 2
print(is_singular(regular))     # False
print(nullspace_vector(regular))  # None

rectangular = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
print(is_singular(rectangular))  # None -- no está definida para no cuadradas
```

---

## 7. Archivos relacionados

- `documentation/Matrices.md` — el resto de las operaciones de matriz (aritmética, determinante, inversa).
- `documentation/GaussJordanMethod.md` — otra vía para llegar al rango de una matriz, como parte de resolver un sistema.
- `tests/test_api_matrix_properties.py` — paridad contra `core/matrix_tools` llamado directo, reusando las matrices singular/regular de `tests/test_matrix_tools.py`.
