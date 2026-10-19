# Cálculo simbólico: derivadas

> **Archivos:**\
> `core/calculo.py` (derivada simbólica)\
> `core/numeric/_expresiones.py` (`parsear`, compartido con los métodos numéricos)\
> (interfaz API) `api/adapters/calculo.py`, `api/adapters/latex.py`\
> (frontend) `frontend/src/components/general/DerivativeInputs.tsx`

## 1. Qué hace

`POST /api/v1/calculus/derivate` (issue #10) recibe una función en LaTeX y devuelve su derivada **exacta** (`sympy.diff`) en LaTeX, lista para MathQuill.

```py
derivar_simbolica(f_str, variable="x") -> Dict
```

## 2. Recorrido de una entrada

1. **LaTeX → texto** con `latex_a_texto(..., estricto=True)`. El modo estricto de `parse_latex` rechaza entradas truncadas (`x^{`, `x+`, `x)`) que el modo por defecto "recupera" en silencio leyéndolas como `x`. Para entradas válidas los dos modos dan lo mismo; los métodos numéricos siguen con el modo por defecto.
2. **Texto → expresión** con `parsear(texto, variable=...)`: las mismas reglas que los métodos numéricos (`^` como potencia, `e` como constante de Euler, rechazo de funciones desconocidas y de letras que no son la variable).
3. **Validaciones propias del cálculo simbólico:** se rechazan operadores de cálculo dentro de la entrada (`\int`, `\frac{d}{dx}`, sumatorias, productos, límites), y expresiones de más de 500 caracteres.
4. **Derivada:** la variable pasa a ser un símbolo **real** (con el símbolo complejo por defecto de sympy, `d|x|/dx` sale en términos de `re(x)` e `im(x)`; con uno real es `sign(x)`), los decimales pasan a racionales exactos (`0.5 → 1/2`) y se deriva con `sympy.diff`.
5. **Simplificación:** se usa la forma de `sympy.simplify` sólo si reduce las operaciones al menos un 25 %. `d/dx((x+1)/(x-1))` queda `-2/(x-1)^2`; `d/dx(x² sin x)` queda `x² cos x + 2x sin x` (la forma de la regla del producto), no la factorización `x(x cos x + 2 sin x)` que propondría `simplify`.

## 3. Derivada nula

`d/dx(7) = 0` es un resultado válido. `core/numeric/_expresiones.derivar()` (la que usa Newton-Raphson) **sigue** rechazando una derivada idénticamente nula, porque Newton divide por `f'(x)` y con `f' = 0` su fórmula no está definida: es una regla del método, no de la derivada. Por eso `core/calculo.py` no reutiliza `derivar()`, pero sí `parsear()`.

## 4. Variable de derivación

El campo "Variable" del frontend antes se mostraba pero no se enviaba. Ahora se envía y el backend la respeta:

- una sola letra minúscula ASCII distinta de `e` (reservada para la constante de Euler): `x`, `t`, `y`, …;
- omitida, es `x`; vacía o inválida, `400`;
- la expresión sólo puede usar esa letra: con `t`, `x^2 + t` se rechaza. No hay parámetros simbólicos (`a`, `b`): `d/dx(a·x)` sería una derivada parcial con constantes, fuera de alcance.

`parsear()` ganó el parámetro `variable="x"`; los métodos numéricos usan siempre el default, así que su contrato no cambia.

## 5. Funciones admitidas

Las del parser de los métodos numéricos (`sin`, `cos`, `tan`, `exp`, `log`/`\ln`, `log10`, `sqrt`, `abs`/`|x|`, `\pi`, `e`) y las que el parser LaTeX de sympy reconoce y sympy conoce (`\sec`, `\csc`, `\cot`, `\arcsin`, `\arccos`, `\arctan`, `\sinh`, …). Un nombre no reconocido (`\operatorname{sen}`) se rechaza.

## 6. Contrato

Entrada:

```json
{"function_latex": "x^{2}\\sin(x)", "variable": "x"}
```

`variable` es opcional (default `x`). Respuesta `200`:

```json
{"ok": true,
 "data": {"input": {"latex": "x^{2}\\sin(x)", "variable": "x",
                    "expression": "x**2*sin(x)",
                    "interpreted_latex": "x^{2} \\sin{\\left(x \\right)}"},
          "result": {"latex": "x^{2} \\cos{\\left(x \\right)} + 2 x \\sin{\\left(x \\right)}",
                     "expression": "x**2*cos(x) + 2*x*sin(x)"}}}
```

`data.result.latex` es el campo que muestra el frontend; `input.expression`/`interpreted_latex` muestran lo que se entendió de la entrada, y `result.expression` es la derivada en sintaxis de sympy. Errores: `400 {"error": {"code": "VALIDATION_ERROR", "message": ...}}`, con `message` como texto (LaTeX inválido, función desconocida, letra ajena, operador de cálculo) o como objeto campo → mensajes (campo faltante, vacío o demasiado largo, variable inválida).

La ruta se llama `derivate` (sic) porque es la que ya usaba `frontend/src/api/client.ts`.

## 7. Ejemplos

| Función (LaTeX) | Derivada (LaTeX devuelto) |
|---|---|
| `x^{2}` | `2 x` |
| `7` | `0` |
| `3x+2` | `3` |
| `x^{2}\sin(x)` | `x^{2} \cos{\left(x \right)} + 2 x \sin{\left(x \right)}` |
| `\frac{1}{x}` | `- \frac{1}{x^{2}}` |
| `\sin(x^{2})` | `2 x \cos{\left(x^{2} \right)}` |
| `e^{x}` | `e^{x}` |
| `\ln(x)` | `\frac{1}{x}` |
| `\frac{x+1}{x-1}` | `- \frac{2}{\left(x - 1\right)^{2}}` |
| `\left\|x\right\|` | `\operatorname{sign}{\left(x \right)}` |
| `t^{3}+\cos(t)` (variable `t`) | `3 t^{2} - \sin{\left(t \right)}` |

sympy y antlr se importan dentro de las funciones, nunca a nivel de módulo: importar `core.calculo` no carga ninguno de los dos, y el CLI sigue arrancando sin ellos.
