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

`_reducir()` es la única eliminación (Gauss-Jordan con pivoteo parcial) detrás de `rank_of`, `determinant`, `is_singular`, `nullspace_vector` y `system_ranks`. `inverse()` usa el mismo criterio en su propio bucle, que tiene que registrar cada paso. Por construcción, la **singularidad** no puede discrepar entre funciones:

```
rank_of(A) < n   <=>   is_singular(A)   <=>   inverse(A) levanta ValueError   =>   determinant(A) == 0.0
```

La última flecha es **sólo de ida**. `determinant` devuelve el producto de los pivotes **sin compararlo contra ningún umbral**, y ese producto puede no entrar en un `double` aunque la matriz sea invertible:

| Caso | `rank_of` / `is_singular` | `determinant` |
|---|---|---|
| singular numérica (rango < n) | `< n` / `True` | `0.0` exacto |
| invertible, det representable (`1e-5·I₃`, `diag(1e-200, 1e-200, 1e300)`) | `n` / `False` | el valor: `1e-15`, `1e-100` |
| invertible, \|det\| < ~5e-324 (`1e-110·I₃`: det = 1e-330) | `n` / `False` | `0.0` por **subdesbordamiento** + `RuntimeWarning` |
| invertible, \|det\| > ~1.8e308 (`1e110·I₃`: det = 1e330) | `n` / `False` | `inf` por **desbordamiento** + `RuntimeWarning` |

Son dos cosas distintas:

- **Singularidad numérica**: una propiedad de la matriz, decidida por los pivotes.
- **Pérdida de representabilidad**: un límite del formato `double` para guardar un número.

Para decidir singularidad se usa `is_singular`/`rank_of`, nunca `determinant(A) == 0.0`.

El producto de pivotes se acumula como mantisa y exponente (`math.frexp`) y se arma al final. Así sólo se pierde cuando el **resultado** no es representable, no por un producto parcial: `diag(1e-200, 1e-200, 1e300)` da `1e-100`, mientras que multiplicando de a uno daba `0.0`. Se mantuvo el tipo de retorno `float` para no cambiar el contrato de quienes llaman a `determinant()`; la alternativa que no se implementó está en la sección 4.1.

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
- **Rango de la coma flotante.** Si el `det(A)` final no es representable, la matriz sigue siendo invertible, pero cada función lo maneja así:
  - `determinant()` devuelve `0.0`/`inf` con un `RuntimeWarning` (sección 3.1).
  - `inverse()` lo dice en su texto ("no representable en coma flotante… A es invertible") en vez de mostrar `det(A) = 0`. Si algún cofactor tampoco es representable, avisa que la adjunta no es confiable a esa escala.
  - Cramer lo rechaza con `ValueError`.
  - `gauss_jordan.run()` sigue mostrando "Determinante de A = 0" en ese caso, porque su registro de pasos no se modifica en esta ronda.

  **No implementado (requiere decisión):** devolver el determinante como `(mantisa, exponente)` o como `log|det|` permitiría mostrar `1e-330`. Pero cambia el tipo de retorno de `determinant()` y obliga a tocar a todos sus llamadores: `inverse`, `gauss_jordan.run`, el CLI de matrices y `printMethods`.
- **Gauss y Gauss-Jordan no usan todavía este criterio** en su eliminación (`core/gauss.py`, `core/gauss_jordan.py`, `core/system_solver/gauss_solver.py` siguen con `1e-12`/`1e-13` absolutos). Coinciden con Cramer y con `matrix_tools` mientras las entradas no sean del orden de `1e-12` o menores. Con `1e-13·[[2,1],[1,3]]`, Gauss-Jordan clasifica mal un sistema invertible. Está fijado como `expectedFailure` en `tests/test_tolerancias_numericas.py`. Sí usan el `determinant()` nuevo para el valor que muestran.
- **Un `tol` explícito sigue siendo absoluto.** Todas las funciones de `matrix_tools` aceptan `tol`; si se pasa un número, se usa como umbral absoluto (el comportamiento anterior, sin el umbral sobre el determinante final). Sin `tol` rige el criterio de este documento.

## 5. Mostrar números: `format_number`

El formato no decide si algo es cero: eso lo decide el algoritmo con el criterio de arriba, y lo escribe como `0.0` exacto. `format_number` muestra lo que recibe, en una de tres presentaciones.

### 5.1. Las tres presentaciones

1. **Exacta del valor guardado**:
   - `0` sólo para el cero exacto.
   - Un entero con todas sus cifras mientras sea exacto (`|x| < 2⁵³`; más allá, `repr`, que también es exacto).
   - Una fracción legible cuyo valor en `float` **es** el guardado.
   - O el decimal más corto que reproduce el `float` (`repr`), si tiene ≤ 15 cifras significativas.
2. **Simplificada**: sólo para un valor cuya representación exacta necesita 16–17 cifras (no es un decimal "limpio"). Se muestra el entero, la fracción legible o el decimal de ≤ 10 cifras que esté a **≤ 128 ulps** (≈ 3·10⁻¹⁴ relativo). Es ruido de redondeo alrededor de un número simple.
3. **Aproximación visible**: si no hay nada simple tan cerca, 10 cifras con `≈` adelante. No se presenta como exacto algo que no lo es.

"Fracción legible" significa denominador ≤ 10 000 y \|numerador\| ≤ 10⁶.

### 5.2. Por qué estos números

- **Por qué 15 cifras.** Es `DBL_DIG`: todo decimal de hasta 15 cifras sobrevive idéntico al pasar por un `double`. Si `repr(x)` tiene ≤ 15 cifras, ese decimal **es** el valor (`1000000000.25`, `1e-15`) y no hay ruido que limpiar. Por eso un valor limpio nunca se acerca a otro.
- **Por qué 128 ulps.** Se midió el ruido real del motor sobre 3 000 sistemas enteros 2×2–4×4 contra sus soluciones racionales exactas:
  - Cramer da resultados exactos.
  - Gauss-Jordan y la inversa quedan a p99 ≈ 35 ulps y p99,9 ≈ 470 ulps. 128 ulps cubre el 99,7 %.
  - Sobre 200 000 `float` aleatorios, 128 ulps con denominador ≤ 10 000 no aceptó ninguna fracción falsa (con 1024 ulps hubo 16). Tampoco convirtió en fracción ninguna constante (π, e, √2, √3, ln 2, φ…).
  - El 0,3 % de ruido que excede 128 ulps no se muestra mal: sale como aproximación visible (`≈…`).
- **Por qué denominador ≤ 10 000.** El 99,4 % de las soluciones exactas de esos sistemas tiene denominador ≤ 10 000. Con ≤ 1000, el tope de la ronda anterior, sólo el 83 %: se perdían fracciones como `1/1024`, `1/2048`, `1/4096` y una de cada seis soluciones de sistemas con enteros de un dígito.
  - El tope de denominador ya no es lo que impide fracciones engañosas como `3126535/995207` para π. Eso lo garantiza exigir que la fracción **sea** el valor (presentación exacta) o esté a ≤ 128 ulps de él (simplificada).
- **Por qué numerador ≤ 10⁶.** Evita que `1000000000.25` salga como `4000000001/4`.
- **Por qué ≤ 10 cifras para el decimal cercano.** Con 14, cualquier número quedaría a menos de 128 ulps de su redondeo: π saldría `3.1415926535898`, presentado como exacto. Con 10, sólo un 0,017 % de floats aleatorios cae por casualidad tan cerca de un decimal corto, y ninguna constante.

### 5.3. Ejemplos

| Valor | Se muestra | Presentación |
|---|---|---|
| `0.0`, `-0.0` | `0` | exacta |
| `1000000000000001.0` | `1000000000000001` | exacta (antes `1e15`: se perdía una unidad representable) |
| `1e20` | `1e20` | exacta (`repr`) |
| `0.5`, `-2.5`, `0.1` | `1/2`, `-5/2`, `1/10` | exacta: `float(1/10) == 0.1` |
| `1/1024`, `1/2048`, `3/4096` | `1/1024`, `1/2048`, `3/4096` | exacta |
| `1000000000.25` | `1000000000.25` | exacta (antes `1000000000`) |
| `-1000000000.75` | `-1000000000.75` | exacta (antes `-1000000001`: **otro entero**) |
| `1e-15`, `2.5e-10` | `1e-15`, `2.5e-10` | exacta |
| `0.0015` | `3/2000` | exacta: la fracción es el valor |
| `1.9999999999999998` | `2` | simplificada (1 ulp) |
| `0.1 + 0.2` = `0.30000000000000004` | `3/10` | simplificada (1 ulp) |
| `1.0000000000000001e-16` (det calculado de `diag(1e-8,1e-8)`) | `1e-16` | simplificada (1 ulp) |
| `1000000000000000.5` | `1000000000000000` | simplificada: necesita 17 cifras y está a 4 ulps del entero (la diferencia, 0.5, es 5·10⁻¹⁶ relativo) |
| `pi`, `sqrt(2)` | `≈3.141592654`, `≈1.414213562` | aproximación visible |
| `1/12347` | `≈8.099133393e-5` | aproximación visible (denominador > 10 000) |
| `inf`, `nan` | `inf`, `nan` | antes reventaba en `int()` |

### 5.4. Reglas anteriores descartadas

- `abs(x − int(x)) < 1e-9` mostraba como `"0"` cualquier valor menor que `1e-9`.
- `limit_denominator()` sin tope redondeaba a `0` todo lo menor que `~5e-7`.
- La tolerancia relativa `1e-9` de la ronda anterior se medía contra toda la magnitud: a `1e9` dejaba un margen de `1.0`.

Ninguna sobrevive:

- **Ningún valor finito distinto de cero se muestra como `0`.**
- **Dos `float` cuya diferencia supera 128 ulps nunca se muestran iguales sin `≈`.**

### 5.5. Lo que significa cada presentación

1. **Cero matemático** (decidido por el algoritmo): se escribe `0`. Si la aritmética había dado ruido, el paso lo explica.
2. **Presentación exacta**: lo que se ve es el valor guardado.
3. **Presentación simplificada**: lo que se ve está a ≤ 128 ulps del valor guardado.
4. **Aproximación visible** (`≈`): lo que se ve son 10 cifras de un valor que no tiene una forma corta.
