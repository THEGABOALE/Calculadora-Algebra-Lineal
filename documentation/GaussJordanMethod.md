# Documentación del Método de Gauss–Jordan (RREF)

> **Archivos:**\
> `core/gauss_jordan.py` (clase `GaussJordanMethod`)\
> `core/system_solver/gauss_solver.py` (análisis y resolución, compartido con Gauss)\
> (interfaz CLI) `cli/method_runners.py` (`run_gauss_jordan`)\
> (interfaz API) `api/adapters/reduce.py`, `POST /api/v1/matrix/reduce` con `method="gauss-jordan"`

Documento técnico que describe la implementación de **Gauss–Jordan**: lleva `[A|b]` a forma reducida por filas (RREF) y, a diferencia de lo que documentaba una versión anterior de este archivo, **sí calcula y reporta el determinante** cuando `A` es cuadrada.

---

## 1. Resumen general

`GaussJordanMethod` trabaja siempre sobre la matriz aumentada `[A|b]` (`b` es obligatorio — a diferencia de `GaussMethod`, que lo acepta `None`) y hace dos fases:

1. **Forward** (`forward_elimination`): triangulación superior, ceros debajo de cada pivote.
2. **Backward + normalize** (`backward_elimination_and_normalize`): pivotes a 1, ceros arriba y abajo — **RREF** completo.

El análisis del sistema resultante (rango, variables básicas/libres, tipo de solución, solución particular) reutiliza `core/system_solver/gauss_solver.py`, el mismo módulo que usa `GaussMethod` (ver `documentation/GaussMethod.md`, sección 6).

---

## 2. Constructor

```py
GaussJordanMethod(matriz: List[List[float]], b: List[float])
```

- `b` es obligatorio: `ValueError` si es `None`.
- Valida forma y tipo **antes** de construir la aumentada, con mensajes explícitos: `A` no vacía y lista de listas, todas las filas del mismo largo, todos los valores de `A` y `b` numéricos (`ValueError`/`TypeError`). Esto es deliberado — sin estas validaciones, el `list(map(float, ...))` de más abajo reventaría con un error genérico de `float()` en vez de decir qué está mal.
- Atributos: `self.A`, `self.b` (copias originales), `self.tolerance = 1e-12`, `self.frame: List[Dict[str, Any]] = []`, `self.pivots: List[Tuple[int,int]] = []`, `self.determinante: Optional[float] = None` (se llena en `run()`), `self.is_homogeneous` (`True` si todos los `b_i ≈ 0`).

---

## 3. El `frame`

Lista ordenada de pasos (no un diccionario), igual que `GaussMethod` — ver `documentation/GaussMethod.md`, sección 3.

---

## 4. Métodos públicos

### `run() -> List[Dict[str, Any]]`

Orquestador. Reinicia `self.frame`, y en orden:

1. Registra si el sistema es homogéneo o no (`tag="homogeneity_check"`).
2. Intenta calcular `determinant(self.A)` y `is_singular()` (via `core.matrix_tools`), y los registra — envuelto en `try/except` amplio para no interrumpir el proceso si `A` no es cuadrada o algo falla. **Esto sí se calcula y se reporta**, a diferencia de lo que decía una versión anterior de esta documentación ("no se informa el determinante porque se escalan filas"): el determinante se obtiene con `core.matrix_tools.determinant`, que es un cálculo aparte (Gauss con pivoteo parcial, sin las normalizaciones de RREF), no derivado de la reducción de Gauss-Jordan en curso.
3. `forward_elimination()`.
4. `backward_elimination_and_normalize()`.

### `forward_elimination() -> List[Tuple[int, int]]`

Pivoteo parcial por filas (`_select_pivot_row`), elimina hacia abajo (`_row_elim`), registra cada paso. Guarda `self.pivots`.

### `backward_elimination_and_normalize() -> None`

Recorre los pivotes de abajo hacia arriba: normaliza cada uno a 1 (`_scale_row`) y elimina hacia arriba (`_row_elim`). Si `self.pivots` está vacío, corre `forward_elimination()` primero.

### `analyze() -> Dict[str, Any]`

`analyze_argumented(self.matriz, tol=self.tolerance)` — ver `documentation/GaussMethod.md`, sección 6, para las claves exactas.

### `solve_and_log() -> Dict[str, Any]`

El método más rico de la clase. Además del resumen y la solución particular (igual que `GaussMethod`), calcula y registra:

- **Dependencia lineal de las filas de A**: `dependent = rank(A) < filas(A)`. Nota de corrección: el criterio anterior era `rank < min(filas, n_vars)`, que fallaba con más filas que columnas — una matriz 3×2 de rango 2 daba "independiente" cuando 3 vectores en R² son necesariamente dependientes.
- **Forma paramétrica** (sólo si `status == "infinite"`): `print_parametric_solution_from_rref(self.matriz, tol=...)`, que nombra las variables libres `s1, s2, ...` y las básicas `x1, x2, ...` sobre la matriz ya en RREF.
- **Clasificación combinada homogéneo/no-homogéneo × único/infinitas**, con mensajes distintos para cada combinación (`homogeneous_unique`, `homogeneous_infinite`, `particular_solution`, `nonhom_infinite`) y una conclusión final en lenguaje natural.

**Shape del retorno:**

- Si `status == "inconsistent"`: `{**info, "solution": None}` (donde `info` es lo que devuelve `analyze()`).
- Si no: `{**result, "parametric_solution", "tipo_sistema", "dependencia", "determinant", "is_singular"}`, donde `result` es lo que devuelve `solve_from_upper(...)`. Es decir, las claves finales son: `m, n, pivots, rank, basic_vars, free_vars, inconsistent_rows, status, solution, parametric_solution, tipo_sistema, dependencia, determinant, is_singular`.

Este shape es **más rico** que el de `GaussMethod.solve_and_log()` (que devuelve el dict crudo de `solve_from_upper`, sin extras) — es la diferencia real entre los dos métodos a nivel de API de Python, más allá del algoritmo.

### `is_singular() -> Optional[bool]`

`None` si `A` no es cuadrada. Si es cuadrada, `rank(A) < n` según `analyze()`.

---

## 5. Operaciones elementales privadas

`_swap_rows`, `_scale_row` (lanza `ValueError` si el factor es ≈ 0), `_row_elim`, `_select_pivot_row` (pivote parcial por filas), `_zero_small` (limpia valores casi-cero).

---

## 6. Tags del `frame`

`homogeneity_check`, `det`, `singularity`, `start`, `pivot`, `no_pivot`, `swap_rows`, `elim`, `upper`, `scale`, `rref`, `summary`, `inconsistent`, `solution`, `vars`, `dependency_check`, `homogeneous_unique`, `trivial_solution`, `homogeneous_infinite`, `parametric_solution`, `particular_solution`, `nonhom_infinite`, `conclusion`.

---

## 7. Consideraciones numéricas

- **Tolerancia**: `1e-12` **absoluta** en los pivotes de la eliminación (levemente más laxa que la de `GaussMethod`, `1e-13`). No usa todavía el criterio por cota de redondeo de [`CriterioNumerico.md`](CriterioNumerico.md): con entradas del orden de `1e-12` o menores puede no encontrar pivotes y clasificar mal un sistema invertible (fijado como `expectedFailure` en `tests/test_tolerancias_numericas.py`).
- **Pivote parcial por filas**; no se intercambian columnas.
- **Determinante**: se calcula aparte con `core.matrix_tools.determinant` (criterio por cota de redondeo, sin `tol` absoluto) sobre `self.A` original, no derivado de las operaciones de RREF (que escalan filas y alterarían el determinante por esos factores si se intentara leerlo de la diagonal final).

---

## 8. Ejemplo de uso programático

```py
from core.gauss_jordan import GaussJordanMethod
from utils.printMethods import print_frame, print_summary

A = [[1.0, 1.0, 1.0], [2.0, -1.0, 1.0], [1.0, 2.0, -1.0]]
b = [6.0, 3.0, 3.0]

gj = GaussJordanMethod(A, b)
gj.run()
result = gj.solve_and_log()

print_frame(gj.frame)
print_summary(result)
print(result["tipo_sistema"], result["dependencia"], result["determinant"])
```

---

## 9. Interfaz CLI

`cli/method_runners.py::run_gauss_jordan()`. Menú: `[1] Forma Escalonada Reducida (Gauss–Jordan)` en `cli/startup.py`.

También es el motor detrás de la **combinación lineal / ecuación vectorial** (`cli/vector_runners.py::run_vector_combination`, y `POST /api/v1/vectors/combination`): "¿es `b` combinación lineal de `v₁..vₖ`?" es exactamente "¿tiene solución `Ax=b`?" con los vectores como columnas de `A` — ver `documentation/Vectores.md`, sección 4.

---

## 10. Interfaz API — `POST /api/v1/matrix/reduce`

`{"method": "gauss-jordan", "A": [...], "b": [...]}`. Mismo `summary` unificado que `gauss` (ver `documentation/GaussMethod.md`, sección 10) — el adaptador no expone directamente el dict rico de `solve_and_log()` descrito en la sección 4: recalcula `summary` desde `analyze_argumented`/`solve_from_upper` sobre la matriz final, para que la respuesta no dependa de cuál de los dos métodos resolvió el sistema.
