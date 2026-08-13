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
- Atributos: `self.A`, `self.b` (copias de la entrada original), `self.determinante = 1.0` (acumulador de signo por swaps), `self.tolerance = 1e-13`, `self.frame: List[Dict[str, Any]] = []`, `self.pivots: List[Tuple[int,int]] = []`.

---

## 3. El `frame`

`self.frame` es una **lista** ordenada de pasos (no un diccionario indexado por texto), producida por `utils.printMethods.log_step`. Cada paso es un `dict` con claves `index, text, matrix, det, tag, extra`.

---

## 4. Métodos públicos

### `gauss_method() -> List[Dict[str, Any]]`

Triangulariza `self.matriz` (debe ser la aumentada; lanza `RuntimeError` si `is_augmented` es `False`). Antes de operar, si la matriz es cuadrada, llama a `null_determinant()`: si detecta una condición que implica determinante 0 (fila/columna toda-cero, filas/columnas repetidas), registra el motivo y **corta ahí**, sin seguir eliminando. Si no, recorre columnas, elige pivote por máximo valor absoluto en la columna (`sel = max(range(row, m), key=lambda r: abs(aug[r][col]))`), intercambia filas si hace falta, elimina hacia abajo, y al final — si la matriz es cuadrada — llama a `determinant_result()`.

### `fordward_elimination_aug() -> Tuple[Matrix, List[Tuple[int,int]]]`

Variante de la misma eliminación hacia adelante (nombre con el typo histórico "fordward"), usada por `solve_and_log()` cuando se quiere sólo triangular sin el chequeo de `null_determinant()`. Devuelve `(matriz_triangular, pivots)`.

### `solve_and_log() -> Dict[str, Any]`

Asume que la triangulación ya corrió. Llama a `solve_from_upper(self.matriz, pivots=self.pivots)` (de `gauss_solver.py`) y **devuelve exactamente ese resultado**, sin agregarle nada — a diferencia de `GaussJordanMethod.solve_and_log()`, que enriquece el dict con `parametric_solution`, `tipo_sistema`, `dependencia`, `determinant`, `is_singular` (ver `documentation/GaussJordanMethod.md`). `GaussMethod` no calcula ninguno de esos extras: sólo registra un resumen del tipo de solución y las variables básicas/libres en el `frame`, y retorna el dict crudo de `solve_from_upper`.

**Shape exacto del retorno** (claves de `solve_from_upper`, ver sección 6): `m, n, pivots, rank, basic_vars, free_vars, inconsistent_rows, status, solution`.

### `null_determinant() -> bool`

Heurística rápida y conservadora para matrices cuadradas: detecta fila toda-cero, columna toda-cero, dos filas iguales, o dos columnas iguales. Si encuentra alguna, registra el motivo en el `frame` (`tag="singular"`) y devuelve `True`. No es exhaustiva — una matriz puede ser singular sin caer en ninguno de estos cuatro casos, y en ese caso la triangulación sigue normalmente (el pivote ≈ 0 se detecta más adelante, columna por columna).

### `determinant_result()`

Sólo si la matriz es cuadrada: multiplica la diagonal de la matriz ya triangularizada, ajusta por `self.determinante` (el signo acumulado por los intercambios de fila), y registra el resultado (`tag="det"`).

### `swipe_rows(fila_a, fila_b)`

Intercambia dos filas, invierte el signo de `self.determinante` si la matriz es cuadrada, y registra el paso (`tag="swap_rows"`).

---

## 5. Tags del `frame`

`start`, `pivot`, `no_pivot`, `swap_rows`, `elim`, `upper`, `det`, `singular`, `summary`, `inconsistent`, `solution`, `vars` — mismo vocabulario que `GaussJordanMethod` para los pasos compartidos (ver esa documentación para el detalle de cada uno).

---

## 6. `core/system_solver/gauss_solver.py`

Trabaja **sólo** sobre una matriz aumentada ya triangularizada (o al menos con la eliminación hacia adelante completada), y lo reutilizan tanto `GaussMethod` como `GaussJordanMethod`.

```py
find_pivots_from_upper(U, tol) -> List[Tuple[int,int]]
analyze_argumented(U, tol=1e-12) -> Dict[str, Any]
    # claves: m, n, pivots, rank, basic_vars, free_vars, inconsistent_rows, status
    # status ∈ {'unique', 'infinite', 'inconsistent'}
solve_from_upper(U, pivots=None, tol=1e-12, col_permutation=None) -> Dict[str, Any]
    # {**analyze_argumented(...), 'solution': x | None}
    # 'solution' es None si status == 'inconsistent'; si no, una solución
    # particular (variables libres = 0) por sustitución hacia atrás.
```

`status` se determina así: `'inconsistent'` si hay alguna fila `0 ... 0 | c` con `c ≠ 0`; `'unique'` si `rank == n` (todas las columnas de coeficientes tienen pivote); `'infinite'` en cualquier otro caso.

---

## 7. Consideraciones numéricas

- **Tolerancia**: `self.tolerance` (`1e-13` en `GaussMethod`, más estricta que la de `GaussJordanMethod` — ver esa documentación) decide cuándo un valor se trata como 0.
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
