# Documentación de Notación Posicional

> **Archivo:** `core/positional_notation.py`\
> (interfaz) `cli/startup.py`, opción `[7] Notación Posicional ▸`

Documento técnico que describe la descomposición de números en notación posicional: base 10 (parte entera y fraccionaria) y base 2, con el desarrollo paso a paso.

---

## 1. Resumen general

Descompone un número en la forma `dígito × base^potencia`, muestra cada término y la suma que reconstruye el número original. Es un módulo autocontenido: sólo depende de `utils.EquationFunctions` para `num_to_sub`/`format_number`, y si por algún motivo esa importación fallara, define sus propias versiones de respaldo (`try/except` al importar) — no tiene ninguna otra dependencia dentro del proyecto.

No tiene equivalente en la interfaz web: es una operación exclusiva del CLI.

---

## 2. Base 10

```py
decompose_base10_decimal(n: int | float | str) -> Dict[str, Any]
```

Separa la parte entera y hasta 8 dígitos fraccionarios significativos, y devuelve:

- `int_part`, `frac_part`
- `terms`: lista de `(dígito, potencia, valor)`, incluida la parte fraccionaria con potencias negativas.
- `frac_terms`: sólo los términos con potencia `< 0`.
- `expression`: el desarrollo completo como string, p. ej. `"13.5 = 1×10¹ + 3×10⁰ + 5×10⁻¹"`.
- `total`: la suma de los términos (debe reconstruir el número original).
- `negative`: si el número original era negativo.

```py
pretty_print_base10_decimal(n) -> str
```

Arma un texto de varias líneas: la expresión, el detalle término por término (sólo los no nulos), y la suma paso a paso.

**Nota conocida:** para números negativos, `expression` antepone un `-` explícito al string `n` original, que en Python ya incluye su propio signo (`str(-27)` es `"-27"`) — el resultado visual es un doble signo (`"--27 = ..."`). El valor numérico (`total`) no se ve afectado, es sólo un detalle de presentación heredado del código original.

---

## 3. Base 2

```py
decompose_base2_str(value: str) -> Dict[str, Any]
```

Valida que `value` sea una cadena binaria (`_validate_binary_string`, sólo `0` y `1`, sin ceros a la izquierda salvo que sea `"0"`) y descompone cada bit como `bit × 2^potencia`. Devuelve `bits`, `terms`, `expression`, `total` (el valor decimal equivalente), y `decimal_equiv` (mismo valor que `total`, alias por claridad de la API).

```py
pretty_print_base2_str(value: str) -> str
```

Además del desarrollo `bit × 2^potencia`, agrega una **confirmación por el camino inverso**: divide el valor decimal obtenido entre 2 sucesivamente (`decimal ÷ 2 = cociente resto r`) hasta llegar a 0, mostrando que el binario reconstruido coincide con el original.

---

## 4. Superíndices y símbolo de multiplicación

`to_superscript(n)` convierte un entero (incluido negativo) a su representación Unicode en superíndice, usada para las potencias (`10⁻²`, `2³`). `MULT_SIGN = '×'` es el símbolo usado en todos los términos.

---

## 5. Interfaz interactiva (CLI)

```py
run_positional_notation_menu() -> None
```

Menú de 3 opciones: `[1]` descomponer en base 10, `[2]` descomponer en base 2, `[0]` volver. Cada opción pide el valor por consola, valida, y si falla imprime el mensaje de error y vuelve a mostrar el menú (no termina el programa).

---

## 6. Ejemplo de uso programático

```py
from core.positional_notation import decompose_base10_decimal, decompose_base2_str

d = decompose_base10_decimal("13.5")
print(d["expression"])   # 13.5 = 1×10¹ + 3×10⁰ + 5×10⁻¹
print(d["total"])        # 13.5

b = decompose_base2_str("1101")
print(b["decimal_equiv"])  # 13
```
