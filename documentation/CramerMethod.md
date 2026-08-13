# Documentación del Método de Cramer

> **Archivos:**\
> `core/cramer.py` (clase `CramerMethod`)\
> (interfaz CLI) `cli/method_runners.py` (`run_cramer`, alias `run_crammer`)\
> (interfaz API) `api/adapters/reduce.py` — **no** `api/adapters/determinant.py`

Documento técnico que describe la implementación del **método de Cramer**: resuelve sistemas lineales cuadrados `Ax = b` usando determinantes, con el procedimiento paso a paso registrado en un `frame`.

**Cramer resuelve sistemas, no calcula un determinante suelto.** Esto no siempre fue así en la copia del frontend de la que se portó parte de este proyecto: ahí `determinant_cramer(A)` era literalmente `return determinant_cofactors(A)` — un alias falso que nunca mostraba una regla de Cramer real. En este repo `method=cramer` está explícitamente **rechazado con 400** en `matrix/determinant` (`api/adapters/determinant.py`) y resuelto de verdad en `matrix/reduce` (`api/adapters/reduce.py`), que es donde vive todo lo que resuelve `Ax=b`.

---

## 1. Resumen general

Para cada incógnita `xᵢ` se construye una matriz `Aᵢ` reemplazando la columna `i` de `A` por el vector `b`, se calcula `det(Aᵢ)`, y `xᵢ = det(Aᵢ) / det(A)`. La implementación registra cada determinante calculado (el de `A` y los `n` de `Aᵢ`) en un `frame`, así que el procedimiento completo — no sólo el resultado — se puede imprimir o renderizar.

**Limitaciones, ambas deliberadas y documentadas en el código:**
- Sólo acepta **sistemas cuadrados** (`n` ecuaciones, `n` incógnitas) — `__init__` lanza `ValueError` si no.
- Si `det(A) = 0`, Cramer puede distinguir *inconsistente* de *infinitas soluciones* (mirando si algún `det(Aᵢ) ≠ 0`), pero **no parametriza** las infinitas soluciones — no identifica variables libres ni construye una base del núcleo. Esa parte es trabajo de Gauss-Jordan (`core/gauss_jordan.py`), no de esta regla.

---

## 2. La clase `CramerMethod`

```py
CramerMethod(matriz: List[List[float]], b: List[float])
```

- Valida `len(b) == len(matriz)`.
- Valida que `matriz` sea cuadrada (`n x n`) — si no, `ValueError` explícito ("CramerMethod sólo acepta matrices cuadradas...").
- Copia `matrix_A` y `vector_b`; inicializa `n_variables`, `tolerance = 1e-12`, `frame: List[Dict[str, Any]] = []`, `determinant_A`, `solution`.

`self.frame` es una **lista** ordenada de pasos, no un diccionario — cada paso tiene su propio índice, así que dos pasos con el mismo texto (p. ej. `n` matrices "Matriz Cramer para xᵢ") no se pisan entre sí. Esto fue una corrección real (commit `3b477fc`): con el frame como `dict` indexado por descripción, los `n` pasos de Cramer sobrevivían sólo como uno.

---

## 3. Métodos de cálculo de determinante

`CramerMethod` trae **tres** implementaciones distintas de determinante, cada una con un propósito distinto:

| Método | Uso | Registra en `frame` |
|---|---|---|
| `calculate_determinant(matrix, show_sarrus=False)` | El que usa `solve()` internamente para resolver | Sólo si `show_sarrus=True` y `n==3` (matriz extendida, tag `"sarrus"`) |
| `calculate_determinant_sarrus(matrix)` | Expuesto en `matrix/determinant` (`method=sarrus`), sólo 3×3 | Todo el desarrollo: diagonales, sumas, resultado |
| `calculate_determinant_cofactors(matrix, level=0, show_steps=True)` | Expuesto en `matrix/determinant` (`method=cofactors`), cualquier `n` | Todo el desarrollo recursivo: cofactor por cofactor |

`calculate_determinant_sarrus` sólo acepta `n == 3` — lanza `ValueError` para cualquier otro tamaño. `calculate_determinant_cofactors` funciona para `n` arbitrario por recursión (caso base 1×1 y 2×2).

`create_cramer_matrix(col_index)` devuelve una copia de `A` con la columna `col_index` reemplazada por `b`, sin mutar `self.matrix_A`.

---

## 4. `solve() -> Dict[str, Any]`

**Flujo:**

1. Calcula `detA = calculate_determinant(A, show_sarrus=(n==3))` y lo registra (`tag="Determinante A"`).
2. **Si `detA ≠ 0`** (solución única): para cada variable `i`, construye `Aᵢ`, calcula `det(Aᵢ)`, obtiene `xᵢ = det(Aᵢ)/det(A)`, y registra la matriz de Cramer con su determinante (`tag=f"cramer_x{i+1}"`). Todas las variables se declaran básicas.
3. **Si `detA = 0`**: calcula los `n` determinantes de Cramer igual (son justamente los que distinguen los dos casos), y:
   - Si algún `det(Aᵢ) ≠ 0` → **inconsistente**.
   - Si todos `det(Aᵢ) = 0` → **infinitas soluciones**.

**Shape exacto del resultado** (las tres ramas comparten claves):

| Clave | `status='unique'` | `status='inconsistent'` / `'infinite'` |
|---|---|---|
| `status` | `'unique'` | `'inconsistent'` / `'infinite'` |
| `solution` | `List[float]` | `None` |
| `basic_vars` | `list(range(n))` | `[]` |
| `free_vars` | `[]` | `[]` |
| `determinant` | `det(A)` | `det(A)` (= 0) |

**Dos correcciones sobre el comportamiento original, ambas con comentarios en el código explicando por qué:**

- `basic_vars` es `[]`, no `list(range(n))`, cuando no hay solución única. "Variable básica" es una noción de Gauss (qué columna tiene pivote), y la regla de Cramer no la calcula — declarar todas básicas en un sistema con infinitas soluciones afirmaría exactamente lo contrario de la verdad (ahí *hay* variables libres, sólo que Cramer no las identifica).
- `solution` es `None` en la rama `'infinite'`. Antes el código devolvía el literal `'Crammer'` (con una eme de más — el nombre del método, no una solución) en ese campo; quien necesite distinguir "infinitas" de "inconsistente" ya tiene `status` para eso.

---

## 5. `verify_solution(log: bool = True) -> Dict[str, Any]`

Si no hay `self.solution` (no se resolvió, o no hubo solución única), devuelve `{'ok': False, 'differences': []}`. Si no, evalúa cada ecuación con la solución calculada, compara con `b` dentro de `tolerance`, y opcionalmente registra la verificación en `frame`. Devuelve `{'ok': bool, 'differences': List[float]}`.

---

## 6. Tags del `frame`

- `"Determinante A"` — determinante de la matriz principal.
- `f"cramer_x{i+1}"` — matriz de Cramer y su determinante para la variable `i` (rama única).
- `f"cramer_check_x{i+1}"` — lo mismo, en las ramas singulares (se calculan igual, para poder distinguir inconsistente de infinitas).
- `"solution"` — solución particular (rama única).
- `"vars"` — variables básicas/libres (rama única).
- `"inconsistent"` / `"infinite"` — estado detectado cuando `det(A) = 0`.
- `"sarrus_*"` — pasos de la Regla de Sarrus (ver `calculate_determinant_sarrus`, sección 3).
- `"verify"` — pasos de `verify_solution`.

---

## 7. Interfaz CLI

`cli/method_runners.py::run_cramer()` pide `A` y `b` por consola (`cli.inputsmatrix`), rechaza sistemas no cuadrados antes de instanciar `CramerMethod` (mensaje explícito, sin excepción), llama a `solve()`, e imprime el `frame` y el resumen con `utils.printMethods`. `run_crammer` es un alias del mismo objeto (`run_crammer = run_cramer`) — el nombre histórico traía el typo "crammer"; se conserva por si algo lo sigue llamando así.

Menú: `[3] Regla de Cramer` en el menú principal de `cli/startup.py`.

---

## 8. Interfaz API — `POST /api/v1/matrix/reduce`

Cramer es un `method` de **`matrix/reduce`** (`{"method": "cramer", "A": ..., "b": ...}`), igual que `gauss` y `gauss-jordan` — **no** un `method` de `matrix/determinant`. La única validación de forma extra que exige (matriz cuadrada) la levanta `CramerMethod.__init__` como `ValueError`, y la vista la traduce a 400; el serializer no la duplica.

La respuesta (`api/adapters/reduce.py::_matrix_cramer`) trae dos cosas que `solve()` no da directo:

- **Los n+1 determinantes**, no sólo `det(A)`: `result.determinants` es una lista con `det(A)` (`variable: null`) seguido de un `det(Aᵢ)` por variable, cada uno con su matriz. Es la corrección de la regresión que arregló `3b477fc` (ver sección 2) llevada hasta la respuesta HTTP — mostrar un solo determinante para Cramer es mostrar exactamente lo que Cramer no es.
- `steps` usa el envelope `frame.states` (no la lista plana de gauss/gauss-jordan): es la rama de render que `ResultPretty.tsx` (frontend) elige cuando `method` es `sarrus`/`cofactors`/`cramer`.

El `summary` **no** trae `rank`/`ranks`: Cramer no calcula rangos, y fabricarlos exigiría correr Gauss por detrás bajo el rótulo de Cramer.

```py
# api/adapters/reduce.py
def matrix_reduce(*, method: str, A: Matrix, b: List[float]) -> Dict[str, Any]:
    if method == "cramer":
        return _matrix_cramer(A, b)
    ...
```

**`matrix/determinant` rechaza `method=cramer` con 400 explícito** (`api/adapters/determinant.py`), en vez de redirigirlo en silencio a cofactores.

---

## 9. Ejemplo de uso programático

```py
from core.cramer import CramerMethod

A = [[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]]
b = [4.0, 5.0, 6.0]

cm = CramerMethod(A, b)
res = cm.solve()
print(res['status'])      # 'unique'
print(res['solution'])    # [6.0, 15.0, -23.0]
print(res['determinant']) # -1.0
```

Sistema singular (infinitas soluciones), para ver la otra rama:

```py
cm2 = CramerMethod([[1.0, 2.0], [2.0, 4.0]], [0.0, 0.0])
res2 = cm2.solve()
print(res2['status'])      # 'infinite'
print(res2['solution'])    # None
print(res2['basic_vars'])  # []
```

---

## 10. Archivos relacionados

- `utils/printMethods.py` — `log_step`, `print_frame`, `print_summary` (interfaz CLI).
- `api/adapters/reduce.py` — traduce `CramerMethod.solve()` al contrato JSON de `matrix/reduce`.
- `api/adapters/determinant.py` — expone `calculate_determinant_sarrus`/`_cofactors` bajo `matrix/determinant`; rechaza `method=cramer`.
- `core/gauss_jordan.py` — complemento para parametrizar soluciones cuando `det(A) = 0` (Cramer no lo hace).
