# Documentación del Método de Gauss

> **Repositorio / Archivos:** `models/GaussMethod.py`, `models/system_solver/GaussSolver.py`

Documento técnico y pedagógico que describe la implementación del método de eliminación gaussiana incluida en el proyecto. Cubre la API, comportamiento, registro de pasos (`frame`), consideraciones numéricas y ejemplos de uso.

---

# 1. Resumen general

El módulo implementa la eliminación gaussiana para:

- matrices normales `A` (cálculo de determinante cuando `A` es cuadrada),
- y matrices aumentadas `[A|b]` para resolver sistemas `Ax = b`.

Separa responsabilidades en dos capas:

1. `GaussMethod` — eliminación, operaciones elementales y logging (registro de pasos).
2. `GaussSolver` — análisis y resolución desde una matriz aumentada triangular (sustitución hacia atrás, clasificación de variables, estado del sistema).

El `frame` (registro) permite imprimir paso a paso el procedimiento con funciones helper (`utils.printMethods`).

---

# 2. Archivo: `models/GaussMethod.py` — API y comportamiento

## Constructor

```py
GaussMethod(matriz: List[List[float]], b: Optional[List[float]])
```

**Comportamiento**

- Si `b` != `None` construye la matriz aumentada `aug = [row + [b_i] for row,b_i in zip(matriz,b)]` y marca `self.is_augmented = True`.
- Guarda copias `self.A` y `self.b` con los datos originales.
- Inicializa atributos clave: `self.determinante`, `self.tolerance`, `self.frame`, `self.pivots`, `self.analize`.

**Errores**

- Si `b` tiene distinto número de filas que `matriz` lanza `ValueError`.

---

## Atributos principales

- `self.matriz`: matriz actual (aumentada si aplica).
- `self.filas`, `self.columnas`: dimensiones (heredadas de `Matrix`).
- `self.is_augmented`: bool, si la instancia contiene `[A|b]`.
- `self.A`, `self.b`: copias de la entrada original.
- `self.determinante`: acumulador de cambios de signo por swaps (usado al calcular determinante cuando es cuadrada).
- `self.tolerance`: umbral para comparar con 0 (`isclose`).
- `self.frame`: registro de pasos (dict).
- `self.pivots`: lista de `(fila, columna)` pivotes encontrados.

---

## Firma del `frame` (registro)

El `frame` es un `dict[str, dict]` con la estructura:

```py
frame[message_str] = {
  "matrix": <deepcopy de la matriz estado>,
  "det": Optional[float | str],
  "tag": Optional[str]
}
```

- `message_str`: texto legible describiendo el paso (ej. `"F2 -> F2 - 2*F1"`).
- `matrix`: estado de la matriz en ese paso (copiado).
- `det`: valor del determinante o `None`.
- `tag`: etiqueta corta para clasificar (ej. `swap_rows`, `elim`, `upper`, `det`, `pivot`, `summary`).

Las funciones de `utils.printMethods` esperan este formato para presentar los pasos.

---

## Métodos públicos principales

### `gauss_method() -> dict`

**Uso**: triangulariza `self.matriz` (no aumentada normalmente) y calcula el determinante si la matriz es cuadrada.

**Proceso**:
1. Reinicia `frame` y `determinante`.
2. Si cuadrada, comprueba `null_determinant()` (heurísticas conservadoras). Si `True` retorna `frame`.
3. Para `col` en `0..min(filas,columnas)-1`: llama a `pivote(col)` y `triangular_reduction(col)`.
4. Si cuadrada, llama a `determinant_result()`.
5. Retorna `frame`.

**Observaciones**: diseñado para mostrar cada paso del proceso en `frame`.

---

### `fordward_elimination_aug() -> Tuple[U, pivots]`

**Propósito**: realizar la eliminación hacia delante sobre **matriz aumentada** `self.matriz` y devolver la matriz triangular superior `U` y la lista de pivotes.

**Pasos**:
- Verifica `is_augmented`.
- Registra el estado inicial: `log_step(..., tag="start")`.
- Recorre columnas `col=0..n-1` (n = nº variables).
  - Selecciona `sel = argmax_{r>=row} |aug[r][col]|` (pivote parcial por filas).
  - Si `|aug[sel][col]| ≈ 0` registra `no_pivot` y continúa.
  - Si `sel != row` hace `swipe_rows(row, sel)` (y `log_step` interno).
  - Añade `(row, col)` a `pivots` y registra el pivote.
  - Realiza eliminación hacia abajo: para cada `r > row` calcula `factor` y actualiza columnas `c=col..n` (incluye RHS), registrando cada eliminación con `tag="elim"`.
  - Incrementa `row`.
- Actualiza `self.matriz`, `self.filas`, `self.columnas` y `self.pivots`.
- Registra `tag="upper"` con la matriz `U`.
- Retorna `(U, pivots)`.

**Notas**: esta función no intercambia columnas; es la versión usada para resolver sistemas con pivoteo parcial por filas.

---

### `solve_and_log() -> Dict`

**Propósito**: orquesta la eliminación y la resolución completa para una matriz aumentada.

**Flujo**:
1. Llama `fordward_elimination_aug()`.
2. Llama `solve_from_upper(self.matriz, pivots=self.pivots)` (módulo `GaussSolver`).
3. Extrae `status`, `solution`, `basic_vars`, `free_vars`.
4. Registra en `frame` un `summary` con `status`; si `inconsistent` registra `inconsistent`; si hay `solution` registra `solution` (particular con variables libres = 0) y `vars` (básicas/libres).
5. Retorna `result` (diccionario devuelto por `solve_from_upper`).

**Salida esperada**: `result` con claves `{status, solution, pivots, basic_vars, free_vars, rank, inconsistent_rows}`.

---

### `null_determinant() -> bool`

**Propósito**: heurísticas para detectar singularidad en matrices cuadradas antes de hacer trabajo.

**Chequeos**:
- fila toda-cero => singular (registra `singular`).
- columna toda-cero => singular.
- filas repetidas => singular.
- columnas repetidas => singular.

**Retorno**: `True` si detecta condición que implica `determinante = 0`, `False` en otro caso.

**Nota**: es una prueba rápida, no exhaustiva, y está pensada para evitar trabajo innecesario cuando la matriz es manifiestamente singular.

---

### `determinant_result()`

**Propósito**: cuando la matriz es cuadrada, calcula el determinante a partir del producto diagonal tras triangularización.

**Cálculo**:
- `diag_product = prod(self.matriz[i][i] for i in 0..limit-1)` donde `limit = min(filas,columnas)`.
- `final_dect = self.determinante * diag_product` (ajusta swaps realizados).
- Registra un mensaje detallado con cada factor formateado usando `format_number` y `tag="det"`.

---

### Operaciones elementales y auxiliares

- `swipe_rows(fila_a, fila_b)` — intercambia filas, ajusta `self.determinante` si cuadrada, registra con `tag="swap_rows"`.
- `swipe_col(col_a, col_b)` — intercambia columnas, ajusta determinante si cuadrada, registra `tag="swap_cols"`.
- `triangular_reduction(col)` — asume pivote en `(col,col)`; para `fila = col+1..` aplica eliminación y registra cada paso con `tag="elim"`. Si `pivote ≈ 0` registra `no_pivot_for_reduction`.
- `pivote(col)` — localiza el mejor candidato de pivote en la columna `col` (prefiere valores cercanos a 1) y, si lo encuentra en otra fila/columna, intercambia filas o columnas usando `swipe_*`.

---

# 3. Archivo: `models/system_solver/GaussSolver.py`

Módulo de apoyo que trabaja **solo** con la matriz aumentada **ya triangularizada** (o al menos con la eliminación hacia delante completada). Está dividido en funciones pequeñas y reutilizables.

## `find_pivots_from_upper(U, tol) -> List[(r,c)]`
- Busca en cada fila la primera columna `c` tal que `|U[r][c]| > tol`.
- Devuelve lista de pivotes `(r,c)`.

## `analyze_argumented(U, tol) -> Dict`
- Devuelve un diccionario con: `m`, `n`, `pivots`, `rank`, `basic_vars`, `free_vars`, `inconsistent_rows`, `status`.
- Detecta filas inconsistentes: coeficientes ≈ 0 y RHS ≠ 0.
- Determina `status`:
  - `inconsistent` si hay filas inconsistentes,
  - `unique` si `rank == n` (todas las columnas con pivote),
  - `infinite` en otro caso.

## `solve_from_upper(U, pivots=None, tol=...) -> Dict`
- Si `pivots` es `None` llama a `analyze_argumented`.
- Si `status == 'inconsistent'` retorna sin solución (`solution: None`).
- Si `status != 'inconsistent'` construye una **solución particular** fijando variables libres = 0 y usando sustitución hacia atrás:
  - Recorre pivotes en orden inverso y calcula `x[c] = (rhs - sum_{j>c} U[r][j]*x[j]) / U[r][c]`.
  - Si `pivot ≈ 0` asigna `0` (prevención division por cero).
- Si se suministra `col_permutation` remapea la solución al orden de variables original.
- Retorna `info` extendido con `'solution': x`.

## `solve_system_direct(A,b)`
- Helper: construye `aug`, aplica eliminación con pivote parcial (filas), analiza y llama a `solve_from_upper`.
- Útil para pruebas rápidas cuando no se desea separar pasos.

---

# 4. Tags / Mensajes en `frame` (guía de interpretación)

Los `tag` más relevantes y su significado:

- `start` — estado inicial de la aumentada.
- `pivot` — pivote elegido (posición y valor).
- `pivot_use` — pivote usado en `triangular_reduction`.
- `no_pivot`, `no_pivot_for_reduction` — no se encontró pivote significativo.
- `swap_rows`, `swap_cols` — intercambios realizados.
- `elim` — eliminación de fila (Fj -> Fj - factor*Fi).
- `upper` — la matriz `U` (triangular superior) tras forward elimination.
- `det` — detalle del cálculo del determinante final.
- `solution` — solución particular registrada.
- `vars` — variables básicas / libres en formato legible.
- `summary` — resumen final con el tipo de solución.
- `inconsistent` — sistema inconsistente detectado.
- `sarrus` — (opcional, si se implementa) matriz extendida Sarrus para 3x3.

---

# 5. Comportamiento numérico y consideraciones

- **Tolerancia**: `self.tolerance` (o `tol` en `GaussSolver`) decide cuándo un valor se considera 0 — fundamental para detectar pivotes y filas nulas.
- **Pivote parcial**: la implementación usa pivot parcial por filas (selección del mayor valor absoluto en la columna) para mayor estabilidad numérica que usar el primer valor no nulo.
- **Intercambio de columnas**: existe `swipe_col` y `pivote` puede cambiar columnas si encuentra una entrada más cercana a 1 en otra columna; si se hacen permutaciones de columnas hay que mantener y propagar un `col_permutation` para remapear la solución final (ya contemplado en `solve_from_upper`).
- **Determinante**: calculado por producto diagonal * `self.determinante` (ajusta swaps). Válido si la eliminación se ha hecho sólo con operaciones elementales registradas.
- **Inestabilidad / mal condicionadas**: sistemas con matrices casi singulares pueden producir errores numéricos. Para robustez extra considera escala de filas o pivotaje completo.

---

# 6. Casos límite y reglas de seguridad

- Matriz vacía (`m == 0`) → los helpers devuelven `status='unique'` y solución `[]` por convenio.
- `fordward_elimination_aug` lanza `RuntimeError` si la instancia no es aumentada.
- `null_determinant()` es conservadora: evita cálculos costosos si la matriz es manifiestamente singular (filas/columnas nulas o repetidas).
- Cuando `solve_from_upper` encuentra pivote ≈ 0 en sustitución, asigna 0 al coeficiente para evitar división por cero.

---

# 7. Ejemplos de uso (rápido)

### Resolver un sistema Ax=b y ver pasos:

```py
from models.GaussMethod import GaussMethod
from utils.printMethods import run_and_print, print_summary

A = [[2,1,-1],[1,-1,2],[3,2,1]]
b = [0,9,7]

gauss = GaussMethod(A, b)
result = gauss.solve_and_log()
run_and_print(frame=gauss.frame)   # imprime todos los pasos
print_summary(result)
```

### Obtener solo U y pivots (sin resolver automáticamente):

```py
gauss = GaussMethod(A, b)
U, pivots = gauss.fordward_elimination_aug()
# inspeccionar U y luego usar solve_from_upper(U, pivots)
```

---