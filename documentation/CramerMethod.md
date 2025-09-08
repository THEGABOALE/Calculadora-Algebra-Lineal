# Documentación del Método de Cramer

> **Archivo:** `models/CramerMethod.py`

Documento técnico y pedagógico que describe la implementación del **método de Cramer** en el proyecto. Incluye la API, comportamiento, registro de pasos (`frame`), consideraciones numéricas, casos límite y recomendaciones de pruebas.

---

## 1. Resumen general

El **método de Cramer** resuelve sistemas lineales cuadrados \(A x = b\) usando determinantes. Para cada incógnita \(x_i\) se construye una matriz reemplazando la columna \(i\) de \(A\) por el vector \(b\), se calcula su determinante

La implementación está pensada para ser **didáctica**: registra los pasos principales (cálculo de determinantes, matrices de Cramer, verificación) en un `frame` que puede imprimirse con las utilidades del proyecto.

**Limitaciones importantes**:
- Solo acepta **sistemas cuadrados** (n ecuaciones, n incógnitas).
- Si `det(A) = 0` no devuelve solución por regla de Cramer (puede detectar inconsistencia o infinitas soluciones pero no parametrizarlas).

---

## 2. Resumen de la clase `CramerMethod`

**Constructor**

```py
CramerMethod(matriz: List[List[float]], b: List[float])
```

- Valida que `len(b) == len(matriz)` (número de ecuaciones = número de términos independientes).
- Copia `matrix_A` y `vector_b` internamente.
- Inicializa atributos: `n_variables`, `tolerance`, `frame`, `determinant_A`, `solution`.

### Atributos principales

- `self.matrix_A` — matriz de coeficientes (n x n).
- `self.vector_b` — vector RHS.
- `self.n_variables` — número de incógnitas (n).
- `self.tolerance` — umbral numérico.
- `self.frame` — registro de pasos (ver formato abajo).
- `self.determinant_A` — valor del determinante de A (después del cálculo).
- `self.solution` — lista con la solución (cuando existe) o `None`.

---

## 3. Métodos públicos y comportamiento

### `calculate_determinant(matrix: List[List[float]], show_sarrus: bool = False) -> float`

- Implementa determinantes por recursión (expansión por cofactores).
- Casos base: 1x1 y 2x2 (fórmula directa).
- Caso n==3: opción de usar **Regla de Sarrus** y cuando `show_sarrus=True` registra la matriz extendida en `frame` (útil para enseñanza).
- Para n>3 usa recursión por cofactores (ineficiente pero claro y didáctico).

**Registro**: si `show_sarrus` es `True` se hace `log_step(self.frame, "Sarrus - Matriz Extendida", extended, tag="sarrus")`.


### `create_cramer_matrix(col_index: int) -> List[List[float]]`

- Devuelve una copia de `A` donde la columna `col_index` está reemplazada por `b`.
- No modifica `self.matrix_A` ni `self.vector_b`.

**Uso**: se llama para calcular determinantes `det(A_i)` para cada variable.


### `solve() -> Dict[str, Any]`

**Flujo principal**:
1. Calcula `detA = calculate_determinant(A)` y lo registra con `log_step`.
2. Si `detA ≈ 0`:
   - Registra que `detA == 0` y considera casos:
     * Si algún `det(A_i) ≠ 0` → **inconsistente** (no tiene solución única) — registra y retorna `status: 'inconsistent'`.
     * Si todos `det(A_i) == 0` → **infinitas soluciones** — registra `status: 'infinite'`.
   - En ambos casos `solution` será `None`.
3. Si `detA != 0`:
   - Para cada variable `i` construye `C = create_cramer_matrix(i)`, computa `detC = calculate_determinant(C)` y obtiene `x_i = detC / detA`.
   - Registra la matriz de Cramer y su determinante en `frame`.
   - Guarda la solución vectorial y registra la línea final `solution` y `vars`.

**Retorna** un diccionario con claves estándar: `status` (`unique`/`inconsistent`/`infinite`), `solution`, `basic_vars`, `free_vars`, `determinant`.


### `verify_solution(log: bool = True) -> Dict[str, Any]`

- Si `solution` no existe retorna `{'ok': False}`.
- En otro caso evalúa cada ecuación con la solución calculada y compara con `b` dentro de `tolerance`.
- Registra la verificación en `frame` (cada ecuación y la diferencia).
- Devuelve `{'ok': bool, 'differences': [...]}`.


### `run()`

- Interfaz interactiva: pide entrada por consola (número de variables, coeficientes, vector `b`) — no es necesaria si se usa el constructor programáticamente.
- Llama a `solve()` y `display_solution()` y opcionalmente a `verify_solution()` si el usuario lo solicita.


### `run_crammer()`

- Helper fuera de la clase que solicita datos, instanci a `CramerMethod`, ejecuta `solve()`, imprime registro (`print_frame`) y resumen (`print_summary`).

---

## 4. Estructura del `frame` (registro) y `tags`

El `frame` usa la misma estructura estándar del proyecto:

```py
frame["mensaje"] = {"matrix": <deepcopy>, "det": Optional, "tag": Optional}
```

Tags útiles en este módulo:
- `Determinante A` — registro del determinante de la matriz principal.
- `cramer_x{i}` / `cramer_check_x{i}` — matrices de Cramer y su determinante para cada variable.
- `solution` — registro de la solución particular (cuando `detA != 0`).
- `vars` — variables básicas (en Cramer: todas son básicas si `detA != 0`).
- `inconsistent` / `infinite` — estados detectados cuando `detA == 0`.
- `sarrus` — matriz extendida usada para mostrar el proceso de Sarrus (n==3).

---

## 5. Consideraciones numéricas y limitaciones

- **Sólo cuadrados**: Cramer aplica únicamente para sistemas `n x n`.
- **Eficiencia**: el cálculo recursivo de determinantes es `O(n!)` en la práctica para recursión por cofactores (muy ineficiente para n grandes). Se acepta por claridad didáctica. Para producción conviene usar eliminación gaussiana u algoritmos más eficientes (LU).
- **Tolerancia**: se usa `tolerance` para considerar ceros numéricos; importante en la comparación `det == 0`.
- **Casos `detA == 0`**: Cramer detecta inconsistencia si algún `det(A_i) != 0` (no hay solución); si todos `det(A_i) == 0` indica infinitas soluciones, pero no proporciona la parametrización (no devuelve variables libres ni base del espacio de soluciones) — esa parte queda para métodos basados en eliminación (Gauss/Gauss–Jordan).

---

## 6. Sarrus para 3x3

- Para `n == 3` opcionalmente se usa Regla de Sarrus para explicar el cálculo de determinante: se copia la primera y segunda fila al final (matriz extendida) y se computan sumas de diagonales.
- Cuando `show_sarrus=True` `calculate_determinant` registra esa matriz extendida en `frame` con `tag="sarrus"`.

---

## 7. Ejemplo de uso programático

```py
from models.CramerMethod import CramerMethod
from utils.printMethods import print_frame, print_summary, print_equation

A = [[1,2],[2,3]]
b = [3,4]
cm = CramerMethod(A, b)
res = cm.solve()
print_frame(cm.frame)
print_summary(res)
```

Salida esperada (resumen): `status: 'unique'`, `solution: [...]` y `determinant`.

---

## 10. Archivos relacionados

- `utils/printMethods.py` — helpers para `log_step`, formateo e impresión del `frame` y `print_summary`.
- `models/Matrix.py` — funciones de entrada y utilidades de matriz.
- `models/GaussMethod.py` — eliminación y análisis (complemento para parametrizar soluciones cuando `detA == 0`).

---