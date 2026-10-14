# Documentación del Método de Gauss

> **Archivos:**\
> `core/gauss.py` (clase `GaussMethod`)\
> `core/system_solver/gauss_solver.py` (análisis y resolución desde una matriz triangular)\
> (interfaz CLI) `cli/method_runners.py` (`run_gauss`)\
> (interfaz API) `api/adapters/reduce.py`, `POST /api/v1/matrix/reduce` con `method="gauss"`

Documento técnico que describe la eliminación gaussiana (forward elimination + sustitución hacia atrás) del proyecto.

---

## 1. Resumen general

`GaussMethod` triangulariza `[A|b]` (o `A` sola, si no se pasa `b`) con pivoteo parcial por filas, registra cada paso en un `frame`, y calcula el determinante cuando la matriz es cuadrada. La resolución del sistema (rango, variables básicas/libres, solución particular) es responsabilidad de un módulo separado y reutilizable: `core/system_solver/gauss_solver.py`.

**Contrato de dos pasos**, el mismo que `GaussJordanMethod`:

```py
g = GaussMethod(A, b)
g.gauss_method()        # triangulariza y deja self.matriz en forma escalonada
r = g.solve_and_log()   # sólo analiza y resume lo ya eliminado
```

**Pivoteo parcial por filas únicamente — no se intercambian columnas.** Hacerlo permutaría las variables, y no hay forma de deshacer esa permutación al presentar la solución (a diferencia de `solve_from_upper`, que sí acepta un `col_permutation` si algún día hiciera falta esa permutación).

---

## 2. Constructor

```py
GaussMethod(matriz: List[List[float]], b: Optional[List[float]])
```

- Si `b is not None`: valida `len(b) == len(matriz)` (`ValueError` si no), construye la aumentada `aug = [row + [b_i] for ...]`, marca `self.is_augmented = True`.
- Si `b is None`: envuelve `matriz` sola, `self.is_augmented = False` (sólo tiene sentido para calcular un determinante, no para resolver un sistema).
- Atributos: `self.A`, `self.b` (copias de la entrada original), `self.determinante` (`det(A)` si `A` es cuadrada, se llena en `gauss_method()`; `None` si no), `self.tolerance = 1e-13` (se conserva por compatibilidad, **ya no decide nada**: ver sección 7), `self.frame: List[Dict[str, Any]] = []`, `self.pivots: List[Tuple[int,int]] = []`.

---

## 3. El `frame`

`self.frame` es una **lista** ordenada de pasos (no un diccionario indexado por texto), producida por `utils.printMethods.log_step`. Cada paso es un `dict` con claves `index, text, matrix, det, tag, extra`.

---

## 4. Métodos públicos

### `gauss_method() -> List[Dict[str, Any]]`

Triangulariza `self.matriz` (debe ser la aumentada; lanza `RuntimeError` si `is_augmented` es `False`). Si `A` es cuadrada, primero llama a `null_determinant()`, que sólo **registra** atajos de singularidad; la eliminación **siempre se completa**. Recorre columnas, elige pivote por máximo valor absoluto entre las entradas que no son ruido según el criterio de la sección 7, intercambia filas si hace falta, elimina hacia abajo y deja el ruido en `0.0` exacto. Al final, si `A` es cuadrada, llama a `determinant_result()`.

**Corrección (fix/gauss-consistency).** Antes, `null_determinant()` **cortaba** la eliminación y el análisis leía la matriz sin reducir. Además, la condición "cuadrada" se evaluaba sobre la **aumentada** (m×(n+1)): nunca se cumplía para un sistema cuadrado, y sí para `A` de m×(m−1). Un 3×2 con dos ecuaciones repetidas y solución única salía "infinitas". Que `A` sea singular no distingue un sistema incompatible de uno indeterminado; eso sólo lo dice la eliminación completa.

### `fordward_elimination_aug() -> Tuple[Matrix, List[Tuple[int,int]]]`

La misma eliminación hacia adelante que `gauss_method()` (nombre con el typo histórico "fordward"), sin los pasos de singularidad y determinante. Devuelve `(matriz_triangular, pivots)`. Antes era una copia del código con sus propias reglas; hoy ambos llaman a `_eliminar_hacia_adelante()`.

### `solve_and_log() -> Dict[str, Any]`

Asume que la triangulación ya corrió. Llama a `solve_from_upper(self.matriz, pivots=self.pivots)` (de `gauss_solver.py`) y **devuelve exactamente ese resultado**, sin agregarle nada — a diferencia de `GaussJordanMethod.solve_and_log()`, que enriquece el dict con `parametric_solution`, `tipo_sistema`, `dependencia`, `determinant`, `is_singular` (ver `documentation/GaussJordanMethod.md`). `GaussMethod` no calcula ninguno de esos extras: sólo registra un resumen del tipo de solución y las variables básicas/libres en el `frame`, y retorna el dict crudo de `solve_from_upper`.

**Shape exacto del retorno** (claves de `solve_from_upper`, ver sección 6): `m, n, pivots, rank, basic_vars, free_vars, inconsistent_rows, status, solution`.

### `null_determinant() -> bool`

Atajos de singularidad **sobre `A`** (no sobre `[A|b]`), sólo si `A` es cuadrada: fila toda-cero, columna toda-cero, dos filas iguales o dos columnas iguales. La comparación es exacta, porque son datos de entrada. Si encuentra alguno, registra el motivo en el `frame` (`tag="singular"`), con la aclaración de que no hay solución única y que la eliminación continúa, y devuelve `True`. **No corta el procedimiento** y no decide el tipo de sistema. No es exhaustiva: una matriz puede ser singular sin caer en ninguno de estos casos, y eso lo detecta la eliminación (una columna sin pivote).

### `determinant_result()`

Sólo si `A` es cuadrada: `det(A) = (signo de los intercambios) · producto de la diagonal de la parte A de U`. Lo guarda en `self.determinante` y lo registra (`tag="det"`), p. ej. `Determinante de A = (2)(5/2) = 5`, o `Determinante de A = −(…)(…)(…) = …` si hubo un número impar de intercambios. Si `A` es singular, la última fila de la parte A de U es nula y el resultado es `0`.

El producto se calcula con `core.matrix_tools.producto_sin_desborde`, el mismo que usa `matrix_tools.determinant`: mantisa y exponente por separado, armados al final. Antes era `math.prod`, y `diag(1e-200, 1e-200, 1e300)` daba `0` con un paso que decía "no representable", aunque `det = 1e-100` sí lo es. Ahora el paso sólo dice "no representable (subdesborda/desborda)" si el **resultado** no entra en un `double` (`1e-110·I₃`, `1e110·I₃`).Antes se calculaba sobre la diagonal de la **aumentada**, sólo cuando ésta era cuadrada (es decir, para `A` de m×(m−1), donde no es `det(A)`), y nunca para un sistema cuadrado.

### `swipe_rows(fila_a, fila_b)`

Intercambia dos filas (y sus cotas de redondeo) y registra el paso (`tag="swap_rows"`). Si `A` es cuadrada, invierte el signo que usa `determinant_result()` y lo indica en el texto: "(cambia el signo de det(A))".

---

## 5. Tags del `frame`

`start`, `pivot`, `no_pivot`, `swap_rows`, `elim`, `upper`, `det`, `singular`, `summary`, `inconsistent`, `solution`, `vars` — mismo vocabulario que `GaussJordanMethod` para los pasos compartidos (ver esa documentación para el detalle de cada uno).

---

## 6. `core/system_solver/gauss_solver.py`

Trabaja **sólo** sobre una matriz aumentada ya triangularizada (o al menos con la eliminación hacia adelante completada), y lo reutilizan tanto `GaussMethod` como `GaussJordanMethod` y el adaptador `api/adapters/reduce.py`.

**Qué es cero acá.** Estas funciones no deciden qué es ruido de redondeo: eso lo decide la eliminación que produjo `U`, con el criterio de [`CriterioNumerico.md`](CriterioNumerico.md), y lo deja escrito como `0.0` exacto. Por eso, con `tol=None` (el default), un valor es cero si y sólo si es `0.0`. Un `tol` numérico se sigue aceptando como umbral absoluto. Antes el default era `1e-12` absoluto sobre la matriz final: tomaba `0 = 1e-13` por `0 = 0` y no encontraba pivotes en sistemas de escala `1e-13`.

```py
find_pivots_from_upper(U, tol=None) -> List[Tuple[int,int]]
analyze_argumented(U, tol=None) -> Dict[str, Any]
    # claves: m, n, pivots, rank, basic_vars, free_vars, inconsistent_rows, status
    # status ∈ {'unique', 'infinite', 'inconsistent'}
solve_from_upper(U, pivots=None, tol=None, col_permutation=None) -> Dict[str, Any]
    # {**analyze_argumented(...), 'solution': x | None}
    # 'solution' es None si status == 'inconsistent'; si no, una solución
    # particular (variables libres = 0) por sustitución hacia atrás.
```

`status` se determina así: `'inconsistent'` si hay alguna fila `0 ... 0 | c` con `c ≠ 0`; `'unique'` si `rank == n` (todas las columnas de coeficientes tienen pivote); `'infinite'` en cualquier otro caso.

```py
solve_system_direct(A, b, tol=None) -> Dict[str, Any]
```

Eliminación hacia adelante + análisis + sustitución, **sin registro de pasos** (para pruebas y comprobaciones rápidas; acepta `A` rectangular). Mismo criterio de cero y mismo retorno que `solve_from_upper`. No tiene consumidores en la app. Nunca había funcionado: `List(map(...))` llamaba al genérico `typing.List` (`TypeError` con cualquier entrada) y el pivote se leía de `aug[row][row]` en vez de `aug[row][col]`. Corregida y cubierta en `tests/test_gauss_consistencia.py`.

---

## 7. Consideraciones numéricas

- **Criterio de cero**: el de [`CriterioNumerico.md`](CriterioNumerico.md), igual que `matrix_tools` y Cramer. La eliminación lleva en paralelo la cota de redondeo de cada entrada (`core.matrix_tools.CotasDeRedondeo`). Un candidato a pivote o una entrada recalculada es cero si es menor que el redondeo que pudo acumular, y se escribe como `0.0` exacto. Antes era `1e-13` absoluto: con coeficientes de alrededor de `1e-13` no había pivotes, y con coeficientes de alrededor de `1e8` el ruido pasaba por dato.
- **Pivote parcial por filas**: más estable numéricamente que tomar el primer valor no nulo de la columna. No hay pivoteo por columnas — ver la nota del constructor.
- **Determinante**: sólo tiene sentido si la matriz es cuadrada y `is_augmented=True` no interfiere (el determinante se calcula sobre la parte `A`, ajustado por los swaps registrados en la eliminación).

---

## 8. Ejemplo de uso programático

```py
from core.gauss import GaussMethod
from utils.printMethods import print_frame, print_summary

A = [[2.0, 1.0, -1.0], [1.0, -1.0, 2.0], [3.0, 2.0, 1.0]]
b = [0.0, 9.0, 7.0]

g = GaussMethod(A, b)
g.gauss_method()
result = g.solve_and_log()

print_frame(g.frame)
print_summary(result)
```

---

## 9. Interfaz CLI

`cli/method_runners.py::run_gauss()` pide `A`/`b` (`cli.inputsmatrix`), ejecuta el contrato de dos pasos, e imprime el `frame` y el resumen. Menú: `[2] Forma Escalonada (Gauss)` en `cli/startup.py`.

---

## 10. Interfaz API — `POST /api/v1/matrix/reduce`

`{"method": "gauss", "A": [...], "b": [...]}` (o `"Ab"` con la matriz aumentada directa). El adaptador (`api/adapters/reduce.py`) **no** usa el `solve_and_log()` crudo de `GaussMethod` para el `summary` de la respuesta: calcula un `summary` unificado llamando directamente a `analyze_argumented` + `solve_from_upper` sobre la matriz final, para que la respuesta tenga el mismo shape sin importar si se resolvió con `gauss` o `gauss-jordan` (que internamente devuelven dicts distintos). `steps` es la lista plana (`frame_to_steps`), a diferencia de Cramer (ver `documentation/CramerMethod.md`, sección 8).
