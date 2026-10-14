# Criterio numérico: cuándo un número "es cero"

> **Archivos:**\
> `core/matrix_tools.py` (`_reducir`, `_es_cero`, `FACTOR_REDONDEO`, `rank_of`, `system_ranks`, `determinant`, `is_singular`, `inverse`)\
> `core/cramer.py` (`solve`, `_clasificar_por_rangos`, `_descartar_ruido`)\
> `utils/EquationFunctions.py` (`format_number`)

Casi ninguna cuenta en coma flotante da `0` exacto. Para decir "esta matriz es singular", "este sistema es incompatible" o "esta columna no tiene pivote" hay que decidir cuándo un número calculado es cero. Este documento explica qué criterio usa el proyecto, por qué, y hasta dónde llega.

---

## 1. El problema del umbral absoluto

Antes, todas esas decisiones comparaban contra un umbral **absoluto** `1e-12` (`abs(x) <= 1e-12`), incluso sobre el valor final del determinante. Eso falla en las dos direcciones:

| Matriz | Verdad | Con `1e-12` absoluto |
|---|---|---|
| `diag(1e-8, 1e-8)` | invertible, `det = 1e-16` | `det = 0`, "singular", inversa rechazada, Cramer: "inconsistente" |
| `1e-5·I₃` | invertible, `det = 1e-15` | ídem |
| `1e-13·[[2,1],[1,3]]` | invertible, `det = 5e-26` | rango 0 |
| `1e8·[[1,2,3],[4,5,6],[7,8,9]]` | **singular** (rango 2) | rango 3, `det ≈ -2.7e9`, "invertible" |

El tamaño de `det(A)` no mide singularidad: `det(c·I) = cⁿ` puede ser tan chico como se quiera con `c·I` perfectamente invertible.

## 2. Por qué no alcanza con un umbral "relativo"

La corrección obvia, `abs(x) <= k·eps·max|A|`, rompe otros casos:

- `diag(1e8, 1e-8)` es invertible (`det = 1`), pero `1e-8` queda debajo de `k·eps·1e8`.
- En `[A|b]` con `b` de otra magnitud que `A` (`A ~ 1e-10`, `b ~ 1e10`), toda la parte de `A` queda debajo del umbral de `b`.

Normalizar filas o columnas antes de eliminar tampoco es inocuo en `[A|b]`: si la fila se escala mirando también `b`, una ecuación con `b` grande achica sus coeficientes hasta hacerlos "cero".

## 3. El criterio elegido: cota de redondeo por entrada

Junto a cada entrada `M[i][j]` de la eliminación se lleva `S[i][j]`, una cota de las magnitudes que intervinieron en calcularla:

- al inicio, `S = |M|`;
- en cada operación `M[r] ← M[r] − f·M[p]`, se hace `S[r] ← S[r] + |f|·S[p]`;
- al dividir una fila por su pivote `p`, también se divide su `S` por `|p|`.

El error de redondeo acumulado en `M[i][j]` es del orden de `eps·S[i][j]`, con `eps ≈ 2.2·10⁻¹⁶`. Una entrada se declara cero si

```
|M[i][j]| <= tau · S[i][j],      tau = FACTOR_REDONDEO · max(m, n) · eps,   FACTOR_REDONDEO = 1e4
```

es decir, **si es más chica que el error que pudo haber acumulado al calcularla**.

Propiedades:

- Un dato que es `0` exacto sigue siendo `0` (su cota es `0`).
- Una entrada que no participó en ninguna operación nunca se declara cero, por chica que sea: `1e-300` es un dato, no ruido.
- Multiplicar una fila o una columna por una constante no cambia ninguna decisión.
- Cada columna se juzga con sus propias magnitudes. En particular, la columna `b` de `[A|b]` se juzga sin normalizarla contra `A`.

### 3.1. Una sola eliminación detrás de todo

`_reducir()` es la única eliminación (Gauss-Jordan con pivoteo parcial) detrás de `rank_of`, `determinant`, `is_singular`, `nullspace_vector` y `system_ranks`. `inverse()` usa el mismo criterio en su propio bucle, que tiene que registrar cada paso. Por construcción:

```
determinant(A) == 0.0   <=>   rank_of(A) < n   <=>   is_singular(A)   <=>   inverse(A) levanta ValueError
```

`determinant` devuelve el producto de los pivotes **sin compararlo contra ningún umbral**. Devuelve `0.0` exacto sólo cuando alguna columna se quedó sin pivote.

### 3.2. Sistemas: `system_ranks(A, b)`

Devuelve `(rango(A), rango([A|b]))` a partir de **una** eliminación de `[A|b]`. Las columnas se procesan de izquierda a derecha y la elección de pivote en una columna de `A` no mira la de `b`, así que el rango de `A` que resulta es el mismo que daría `rank_of(A)`, y `rango([A|b]) − rango(A)` es 0 o 1. Con eso se aplica Rouché–Frobenius:

| | Clasificación |
|---|---|
| `rango(A) < rango([A|b])` | incompatible |
| `rango(A) = rango([A|b]) = n` | compatible determinado |
| `rango(A) = rango([A|b]) < n` | compatible indeterminado (`n − rango(A)` parámetros libres) |

### 3.3. Cramer

En `CramerMethod.solve()`, toda afirmación "`det = 0`" o "`det ≠ 0`" se decide por el rango (de `A` o de `Aᵢ`) con este criterio, no por el tamaño del número:

- `det(A) ≠ 0` si `rango(A) = n`. Entonces `xᵢ = det(Aᵢ)/det(A)`, usando los determinantes calculados por cofactores o Sarrus, aunque sean chicos (`1e-15`).
- Si `A` es numéricamente singular pero la aritmética dio, por ejemplo, `-2.78e-17` (pasa con la matriz `0.1…0.9`), el paso lo dice: *"la aritmética da −2.776e-17, que es ruido de redondeo: A es numéricamente singular… así que det(A) = 0"*.
- `det(Aᵢ) ≠ 0` si `rango(Aᵢ) = n`. La regla de la primera ronda (algún `det(Aᵢ) ≠ 0` ⇒ incompatible; todos `0` ⇒ se decide por rangos) no cambia.
- Si `A` tiene rango completo pero `det(A)` no es representable en coma flotante (entradas `~1e-110` en 3×3: `det ~1e-330`, que subdesborda a `0.0`), Cramer levanta `ValueError` con un mensaje explícito en vez de dividir por cero. En la API eso es un 400.

`calculate_determinant_sarrus` y `calculate_determinant_cofactors` (los procedimientos de `matrix/determinant`) siguen mostrando la aritmética completa. Si el resultado es ruido de una matriz numéricamente singular, agregan un paso final (`sarrus_rounding` / `cofactor_rounding`) que lo explica y devuelven `0`.

## 4. Calibración y zona ambigua

`FACTOR_REDONDEO = 1e4` es una **calibración empírica, no un teorema**. Los decimales que tipea un usuario (`0.1`, `0.3`…) no son representables en binario, así que una matriz singular "tal como se escribió" llega a la máquina levemente no singular, y la cota de primer orden `eps·S` subestima ese efecto.

Mediciones sobre 20.000 matrices singulares de 2×2 a 4×4, con entradas decimales de 1–2 cifras y filas que son combinaciones exactas (en decimal) de otras:

- el ruido de los pivotes espurios llegó hasta ~2.5·10³ (en unidades de `max(m,n)·eps·S`), con el 99,9 % por debajo de 20;
- los pivotes legítimos quedaron todos por encima de 5·10¹⁰;
- con `FACTOR_REDONDEO = 1e4`, 0 errores de rango sobre otras 20.000 matrices (otra semilla, incluyendo rango completo). Con `1e3` hubo 1.

**Consecuencia, que es una decisión y no un error:** una matriz cuya singularidad se decide recién en la ~12ª cifra significativa se trata como **numéricamente singular**.

| Matriz | Resultado |
|---|---|
| `[[1, 1], [1, 1 + 1e-9]]` | invertible, `det ≈ 1e-9` |
| `[[1, 1], [1, 1 + 1e-11]]` | invertible |
| `[[1, 1], [1, 1 + 1e-12]]` | **singular** (numéricamente) |
| `[[1, 1], [1, 1 + 1e-13]]` | **singular** (numéricamente) |

En esa zona (número de condición ≳ 10¹²) el resultado no es una afirmación matemática sobre la matriz exacta. La pregunta no se puede responder con 16 cifras: `1 + 1e-13` ni siquiera se representa exactamente.

### 4.1. Lo que este criterio no garantiza

- **No es un algoritmo revelador de rango.** La eliminación con pivoteo parcial puede fallar en matrices construidas a propósito (p. ej. la matriz de Kahan), donde sólo una SVD da el rango numérico confiable. No se usa SVD para no agregar NumPy y para no reemplazar un procedimiento que se muestra paso a paso por uno opaco.
- **Casi singular ≠ resultado exacto.** Una matriz invertible pero mal condicionada (número de condición `κ`) se resuelve, pero la solución puede tener un error relativo de hasta `~κ·eps`. El sistema no lo advierte.
- **Rango de la coma flotante.** Si `det(A)` subdesborda o desborda (`|det| < 1e-308` o `> 1e308`), `determinant()` devuelve `0.0`/`inf` aunque el rango sea completo. Cramer lo detecta y lo rechaza; `determinant()` y `inverse()` no lo advierten.
- **Gauss y Gauss-Jordan no usan todavía este criterio** en su eliminación (`core/gauss.py`, `core/gauss_jordan.py`, `core/system_solver/gauss_solver.py` siguen con `1e-12`/`1e-13` absolutos). Coinciden con Cramer y con `matrix_tools` mientras las entradas no sean del orden de `1e-12` o menores. Con `1e-13·[[2,1],[1,3]]`, Gauss-Jordan clasifica mal un sistema invertible. Está fijado como `expectedFailure` en `tests/test_tolerancias_numericas.py`. Sí usan el `determinant()` nuevo para el valor que muestran.
- **Un `tol` explícito sigue siendo absoluto.** Todas las funciones de `matrix_tools` aceptan `tol`; si se pasa un número, se usa como umbral absoluto (el comportamiento anterior, sin el umbral sobre el determinante final). Sin `tol` rige el criterio de este documento.

## 5. Mostrar números: `format_number`

El formato no decide si algo es cero: eso lo decide el algoritmo con el criterio de arriba, y lo escribe como `0.0` exacto. `format_number` muestra lo que recibe:

| Valor | Se muestra | Regla |
|---|---|---|
| `0.0`, `-0.0` | `0` | cero exacto |
| `2.0`, `1.9999999999999998` | `2` | entero salvo redondeo **relativo** `1e-9` |
| `0.5`, `1/3`, `0.30000000000000004` | `1/2`, `1/3`, `3/10` | fracción con denominador ≤ 1000, salvo redondeo relativo `1e-9` |
| `1e-15`, `2.5e-10`, `-3.5e-12` | `1e-15`, `2.5e-10`, `-3.5e-12` | decimal con 10 cifras significativas, notación científica si hace falta |
| `pi` | `3.141592654` | antes salía `3126535/995207`: una aproximación presentada como valor exacto |
| `1/1024` | `0.0009765625` | denominador > 1000: se muestra en decimal (es exacto) |
| `1e20` | `1e20` | enteros desde `1e15` en notación científica |
| `inf`, `nan` | `inf`, `nan` | antes reventaba en `int()` |

Antes, `abs(x − int(x)) < 1e-9` mostraba como `"0"` cualquier valor menor que `1e-9` (`det(1e-5·I) = 1e-15` aparecía como `0`). Además, `limit_denominator()` redondeaba a `0` cualquier valor menor que `~5e-7`. Ninguna de las dos reglas sobrevive: **ningún valor finito distinto de cero se muestra como `0`**.

Tres categorías que los pasos distinguen:

1. **Cero matemático** (decidido por el criterio): se escribe `0`. Si la aritmética había dado ruido, el paso lo explica.
2. **Redondeo de visualización**: `1.9999999999999998` → `2`, `0.30000000000000004` → `3/10`. Es la misma cantidad a 10 cifras.
3. **Aproximación numérica**: `pi` → `3.141592654`, un decimal que no pretende ser exacto.
