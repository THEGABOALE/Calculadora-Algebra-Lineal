# Documentación del Método de Gauss–Jordan (RREF)

> **Repositorio / Archivos:**\
> `models/GaussJordan.py`\
> (apoya en) `models/system_solver/GaussSolver.py` y `utils/printMethods.py`

Documento técnico y pedagógico que describe la implementación del método de **Gauss–Jordan** incluida en el proyecto. Cubre la API, comportamiento, registro de pasos (`frame`), consideraciones numéricas y ejemplos de uso.

---

# 1. Resumen general

El módulo implementa **Gauss–Jordan** para sistemas lineales:

- Trabaja **siempre** sobre la **matriz aumentada** `[A | b]`.
- Realiza dos fases:
  1. **Eliminación hacia adelante** (*forward*): triangulación superior (ceros **debajo** del pivote).
  2. **Normalización + eliminación hacia atrás** (*backward*): lleva a **RREF** (pivotes = 1 y ceros **arriba** y **abajo** de cada pivote).

El diseño separa responsabilidades:

1. `GaussJordanMethod` — operaciones elementales, selección de pivotes, **RREF** y **logging** del proceso en `self.frame`.
2. `GaussSolver` — análisis del sistema a partir de una aumentada triangular/RREF (rango, pivotes, básicas/libres, inconsistencias) y **cálculo de una solución particular** (fijando variables libres = 0).

Las utilidades de `utils.printMethods` permiten imprimir el proceso y el sistema en forma algebraica (`print_frame`, `print_equation`, `print_summary`).

---

# 2. Archivo: `models/GaussJordan.py` — API y comportamiento

## Constructor

```py
GaussJordanMethod(matriz: List[List[float]], b: Optional[List[float]])
```

**Comportamiento**

- Requiere **siempre** el vector `b` (recomendado obtener `A` y `b` con `Matrix.make_equation`).
- Construye la aumentada `aug = [row + [b_i] for row, b_i in zip(matriz, b)]` y delega tamaños a `Matrix`.
- Guarda copias `self.A` y `self.b` con los datos originales.
- Inicializa atributos clave: `self.tolerance`, `self.frame`, `self.pivots`.\
  *(El determinante no se reporta aquí porque Gauss–Jordan normaliza filas.)*

**Errores**

- Si `b` es `None` o su longitud no coincide con el nº de filas de `A` → `ValueError`.

---

## Atributos principales

- `self.matriz`: matriz **aumentada** actual `[A|b]`.
- `self.filas`, `self.columnas`: dimensiones (heredadas de `Matrix`).
- `self.A`, `self.b`: copias de la entrada original.
- `self.tolerance: float = 1e-12`: umbral para tratar números “casi cero”.
- `self.frame: Dict[str, Dict[str, Any]]`: **registro de pasos**.
- `self.pivots: List[Tuple[int,int]]`: posiciones de pivote `(fila, columna)` detectadas en el forward.
- `self.determinante: Optional[float] = None`: no se informa en Gauss–Jordan.

---

## Firma del `frame` (registro)

El `frame` es un `dict[str, dict]` con la estructura:

```py
frame[message_str] = {
  "matrix": <deepcopy del estado de la matriz>,
  "det": Optional[float | str],
  "tag": Optional[str]
}
```

- `message_str`: texto legible describiendo el paso (ej. `"F2 -> F2 - 2*F1"`).
- `matrix`: estado de la matriz en ese paso (copiado para no mutar el log).
- `det`: no se usa en Gauss–Jordan; queda `None`.
- `tag`: etiqueta corta (`swap_rows`, `elim`, `upper`, `rref`, `pivot`, `summary`, ...).

Las funciones de `utils.printMethods` esperan este formato para presentar los pasos.

---

## Métodos públicos principales

### `run() -> Dict[str, Dict[str, Any]]`

**Uso**: orquesta **forward + backward** para llevar `[A|b]` a **RREF** con registro de pasos.

**Proceso**:

1. Limpia `self.frame`.
2. `forward_elimination()` — triangulación superior (ceros abajo de pivotes).
3. `backward_elimination_and_normalize()` — pivotes a 1 y ceros arriba.
4. Devuelve el `frame`.

---

### `forward_elimination() -> List[Tuple[int,int]]`

**Propósito**: generar ceros **debajo** de los pivotes (forma triangular superior) con **pivoteo parcial por filas**.

**Pasos**:

- Registra el estado inicial con `tag="start"`.
- Para cada columna `col` de los coeficientes (excluye RHS):
  - Selecciona `sel = argmax_{r>=row} |A[r,col]|` — pivote parcial por filas.
  - Si `|A[sel,col]| ≈ 0` → registra `tag="no_pivot"` y continúa.
  - Si `sel != row` → `_swap_rows(row, sel)` con `tag="swap_rows"`.
  - Registra pivote con `tag="pivot"`.
  - Para cada fila `r > row` → `_row_elim(r, row, col)` con `tag="elim"`.
  - Guarda `(row, col)` en `self.pivots` y `row += 1`.
- Registra `tag="upper"` al finalizar.

---

### `backward_elimination_and_normalize() -> None`

**Propósito**: llevar a **RREF** (pivotes a 1 y ceros **arriba** de cada pivote).

**Pasos**:

- Si `self.pivots` está vacío, llama a `forward_elimination()`.
- Recorre pivotes de **abajo hacia arriba**:
  - Escala la fila del pivote: `_scale_row(r, piv)` (`tag="scale"`).
  - Elimina por **encima** del pivote: para `rr in [0, r)` → `_row_elim(rr, r, c)` (`tag="elim"`).
- Registra `tag="rref"` al finalizar.

---

### `analyze() -> Dict[str, Any]`

**Propósito**: invoca `analyze_argumented(self.matriz, tol=self.tolerance)` y devuelve:

- `rank`, `pivots`, `basic_vars`, `free_vars`, `inconsistent_rows`, `status` (`unique` | `infinite` | `inconsistent`).

---

### `solve_and_log() -> Dict[str, Any]`

**Propósito**: registrar un **resumen** del tipo de solución y producir una **solución particular** fijando variables libres = 0.

**Flujo**:

1. `info = analyze()` → obtiene `status` y `pivots`.
2. Registra `tag="summary"` con el tipo de solución.
3. Si `status == "inconsistent"` → registra `tag="inconsistent"` y retorna `{**info, "solution": None}`.
4. Si no, usa `solve_from_upper(self.matriz, pivots=pivots, tol=self.tolerance)` para obtener la solución particular `x`.
5. Registra `tag="solution"` y `tag="vars"` (básicas/libres). Devuelve el `dict` resultante.

---

### `is_singular() -> Optional[bool]`

**Propósito**: indica si `A` es singular **solo** cuando `A` es cuadrada.

- Calcula `n = self.columnas - 1` (coeficientes) y `m = self.filas`.
- Si `n != m` → `None` (no aplica a matrices no cuadradas).
- Si cuadrada → retorna `rank(A) < n` según `analyze()`.

---

## Operaciones elementales y auxiliares

- `_swap_rows(r1, r2)` — intercambio de filas; registra `tag="swap_rows"`.
- `_scale_row(r, factor)` — normaliza fila: `F_r := F_r / factor`; registra `tag="scale"`.
- `_row_elim(target_r, pivot_r, pivot_c)` — eliminación: `F_target := F_target - (A[target,pivot_c]/A[pivot_r,pivot_c]) * F_pivot`; registra `tag="elim"`.
- `_select_pivot_row(start_row, col)` — pivote parcial por filas: argmax de `|A[r,col]|`.
- `_zero_small(x)` — limpia valores próximos a cero según `self.tolerance`.

---

# 3. Archivo: `models/system_solver/GaussSolver.py` (resumen de uso)

Este módulo trabaja **sobre la aumentada** tras el *forward/RREF* y provee utilidades pequeñas y puras:

- `find_pivots_from_upper(U, tol)` — detecta pivotes por fila.
- `analyze_argumented(U, tol)` — devuelve `rank`, `basic_vars`, `free_vars`, `inconsistent_rows`, `status`.
- `solve_from_upper(U, pivots=None, tol, col_permutation=None)` — sustitución hacia atrás para una **solución particular** (fija libres = 0). Si hay permutación de columnas, remapea.

> En Gauss–Jordan se reutiliza `solve_from_upper` aunque la matriz ya esté en RREF; funciona igualmente.

---

# 4. Tags / Mensajes en `frame` (guía de interpretación)

`tag` más relevantes:

- `start` — estado inicial de la aumentada.
- `pivot` — pivote elegido (posición y valor).
- `no_pivot` — no se encontró pivote significativo en la columna.
- `swap_rows` — intercambio de filas.
- `elim` — eliminación de fila `Fj -> Fj ± k*Fi`.
- `upper` — matriz triangular superior tras el *forward*.
- `rref` — forma reducida por filas al finalizar el *backward*.
- `solution` — solución particular (si existe).
- `vars` — variables básicas / libres.
- `summary` — resumen del tipo de solución.
- `inconsistent` — se detectó inconsistencia (fila `0 ... 0 | c≠0`).

Las funciones `print_frame`, `print_equation`, `print_summary` presentan el proceso y los resultados de forma legible.

---

# 5. Consideraciones numéricas

- **Tolerancia (**``**)**: decide cuándo un valor se considera “≈ 0”. Afecta a la detección de pivotes y a la limpieza visual (`_zero_small`).
- **Pivote parcial por filas**: más estable que tomar el primer no nulo. No se intercambian columnas en Gauss–Jordan.
- **Determinante**: no se informa aquí porque **se escalan filas** (normalización de pivotes a 1), lo que altera el determinante por factores. Si necesitas determinantes, usa el método de Gauss clásico.

---

# 6. Casos límite y reglas de seguridad

- Si la matriz está vacía (`m == 0`) → por convenio, no hay trabajo que hacer; analiza resultará `unique` con solución vacía.
- Si se pide `is_singular()` en matrices no cuadradas → retorna `None` (no aplica).
- Si en `_scale_row` el `factor` es “≈ 0” → se lanza `ValueError` (evita división por cero).
- `solve_and_log()` devuelve `solution = None` cuando el sistema es `inconsistent`.

---

# 7. Ejemplos de uso

## 7.1. Uso programático (sin runner interactivo)

```py
from models.GaussJordan import GaussJordanMethod
from utils.printMethods import print_equation, print_frame, print_summary

A = [[1, 1, 1],
     [2,-1, 1],
     [1, 2,-1]]
b = [6, 3, 3]

print(print_equation(A, b))  # forma algebraica

gj = GaussJordanMethod(A, b)
gj.run()                     # forward + backward (RREF)
result = gj.solve_and_log()  # resumen y solución particular

print_frame(gj.frame)
print(print_equation(A, b))
print_summary(result)
```

## 7.2. Runner interactivo `run_gauss_jordan()`

```py
from models.GaussJordan import run_gauss_jordan

# Solicita filas/columnas, pide A y b, ejecuta Gauss–Jordan, imprime proceso y resumen
run_gauss_jordan()
```

---

# 8. Flujo de ejecución (paso a paso)

1. **Entrada**: se registra `A` y `b` (típicamente con `Matrix.make_equation`).
2. **Construcción**: se crea `[A | b]` y se instancia `GaussJordanMethod(A, b)`.
3. **Forward** (`forward_elimination`):
   - se escogen pivotes por columna con pivoteo parcial por filas,
   - se hacen `swap_rows` cuando conviene,
   - se eliminan los valores **debajo** del pivote (`elim`),
   - se marca `upper`.
4. **Backward + normalize** (`backward_elimination_and_normalize`):
   - cada pivote se normaliza a 1 (`scale`),
   - se anulan los valores **encima** del pivote (`elim`),
   - se marca `rref`.
5. **Análisis y solución** (`solve_and_log`):
   - `analyze_argumented` determina `rank`, `status`, básicas/libres, inconsistencias,
   - si procede, `solve_from_upper` devuelve una **solución particular** (libres = 0).
6. **Salida**: se puede imprimir el `frame` completo y el **summary**.

---

# 9. Errores comunes y diagnóstico

- **Resultados absurdos (p. ej. repite la misma variable en básicas)**: revisar que el *forward* generó pivotes correctos (mirar `tag="pivot"`) y que no hubo divisiones por valores casi cero. Ajustar `tolerance` si es necesario.
- **No aparece **``** o \*\*\*\***``: verificar que los bucles recorren las columnas de coeficientes (`n = columnas-1`), no incluyen la RHS como columna de pivote.
- **Sistema marcado \*\*\*\***``: confirmar que existe una fila del tipo `0 0 ... 0 | c` con `c ≠ 0` en la aumentada (el análisis así lo detecta).

---

# 10. Extensiones futuras

- **Pivoteo completo** (filas + columnas) con seguimiento de una `col_permutation` para remapear la solución final.
- **Parámetros de tolerancia** configurables por el usuario desde CLI.
- **Exportar pasos** (`frame`) a JSON/CSV y generar reportes.
- **Modo silencioso** (sin `frame`) para ejecución rápida.

---

## Anexo A — Firma de utilidades usadas

```py
# utils.printMethods
log_step(frame, step, matrix_state, det=None, tag=None)
print_frame(frame, show_det=True, sep="-"*40)
print_equation(matriz, vector) -> str
print_summary(result_dict) -> None

# models/system_solver/GaussSolver
analyze_argumented(U, tol=1e-12) -> Dict[str, Any]
solve_from_upper(U, pivots=None, tol=1e-12, col_permutation=None) -> Dict[str, Any]
```

> **Nota**: En Gauss–Jordan no se calcula ni informa el determinante, ya que la normalización de filas lo haría depender de los factores de escala. Para determinantes, usar el método de Gauss clásico.