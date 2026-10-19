# Cálculo simbólico: derivadas e integrales

> **Archivos:**\
> `core/calculo.py` (derivada e integral simbólicas)\
> `core/numeric/_expresiones.py` (`parsear`, compartido con los métodos numéricos)\
> (interfaz API) `api/adapters/calculo.py`, `api/adapters/latex.py`\
> (frontend) `frontend/src/components/general/DerivativeInputs.tsx`, `IntegralInputs.tsx`

Secciones 1 a 7: derivadas (issue #10). Sección 8: integrales indefinidas (issue #12).

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

## 8. Integrales indefinidas

`POST /api/v1/calculus/integral` (issue #12):

```py
integrar_simbolica(f_str, variable="x") -> Dict        # sin límite de tiempo
integrar_con_limite(f_str, variable="x", segundos=10)  # la que usa la API
```

$$\int f(x)\,dx = F(x) + C, \qquad F'(x) = f(x)$$

**Entrada y variable.** Mismo recorrido que las derivadas (sección 2): LaTeX estricto (con el rechazo de exponentes y factoriales numéricos mayores que 1000 sobre el árbol sin evaluar), `parsear()` con la variable elegida (una letra minúscula distinta de `e`, `x` por defecto, la expresión sólo puede usar esa letra), variable **real**, decimales a racionales exactos (`0.5x^2 → x³/6`), rechazo de operadores de cálculo. Además, el integrando no puede superar 60 operaciones (`count_ops`).

**Constante de integración.** `+ C` se agrega sólo al LaTeX (`result.latex`); `result.expression` es `F` sin la constante, para que la primitiva siga siendo verificable. Si `F = 0` (integrando nulo), el LaTeX es `C`.

**Dominio real y logaritmos.** Un `ln(u)` de la primitiva se muestra como `ln|u|` salvo que `u` sea positivo o que el integrando ya contenga `ln(u)` (lo que restringe el dominio a `u > 0`): `∫1/x = ln|x| + C` (válida por separado en cada intervalo que no contiene al 0), `∫tan x = −ln|cos x| + C`, `∫2x/(x²+1) = ln(x²+1) + C`, pero `∫ln x = x ln x − x + C`. `ln|u|` y `ln u` tienen la misma derivada `u'/u` donde están definidas.

**Verificación.** Antes de devolverla, la primitiva se deriva y se compara con el integrando en varios puntos reales del dominio. Los tests lo hacen además de forma independiente para cada caso.

**Política para resultados no elementales.**

| sympy devuelve | respuesta |
|---|---|
| primitiva con funciones elementales | `200` |
| primitiva con funciones especiales admitidas: `erf`, `erfi`, `erfc`, `Si`, `Ci`, `Shi`, `Chi`, `Ei`, `li`, Fresnel `S`/`C` (`fresnels`/`fresnelc`) | `200`, con `special_functions`, `note` y la definición de cada una en `definitions` (LaTeX). Es una primitiva correcta (`F' = f`), no elemental. |
| la integral sin evaluar (`Integral`) | `422 INTEGRAL_NOT_RESOLVED`: "sympy no encontró una primitiva… Eso no prueba que no exista" |
| una primitiva por tramos (`Piecewise`, p. ej. `∫|x|`) u otras funciones especiales | `422 INTEGRAL_NOT_RESOLVED` |

El mensaje nunca afirma que la función no tenga primitiva elemental: sólo que el motor no la encontró. Ejemplos: `∫e^{−x²} = (√π/2)·erf(x) + C`, `∫1/ln x = li(x) + C`, `∫sin x / x = Si(x) + C`, `∫sin(x²)` en términos de Fresnel (las constantes con Γ se simplifican); `∫x^x`, `∫sin(sin x)` y `∫√(tan x)` quedan sin resolver.

**Tiempo.** `sympy.integrate` no tiene límite propio y hay integrandos breves que no terminan (`∫1/(x⁵+x+1)` supera los 30 s). La API integra en un **proceso aparte** (`multiprocessing`, contexto `spawn`, igual en Windows y Linux) y lo **termina** (`terminate`, y `kill` si hiciera falta) si no responde dentro de `TIEMPO_MAXIMO_INTEGRAL_S = 10 s`, arranque incluido (~1.5 s en Windows por importar sympy en el hijo): menos que los 15 s del timeout de axios, con margen para la red y el render. Un hilo no sirve: no se puede cancelar y seguiría consumiendo CPU después de responder. A lo sumo 2 integrales corren a la vez **en toda la máquina**, no por proceso del servidor (con varios workers WSGI/ASGI un semáforo de `threading` se multiplicaría por worker): cada turno es un archivo en el directorio temporal con un bloqueo del sistema operativo (`msvcrt.locking` en Windows, `fcntl.flock` en Linux), que comparten todos los procesos y que el sistema libera aunque el proceso muera. Si no hay turno en 1 s, la respuesta es `503 SERVER_BUSY`. Con varias máquinas, el límite es por máquina. Los errores de entrada se detectan **antes** de lanzar el proceso (respuesta inmediata, sin pagar el arranque).

| situación | HTTP | `error.code` |
|---|---|---|
| entrada inválida | 400 | `VALIDATION_ERROR` |
| sin primitiva presentable | 422 | `INTEGRAL_NOT_RESOLVED` |
| tiempo agotado | 422 | `INTEGRAL_TIMEOUT` |
| demasiadas integrales en curso | 503 | `SERVER_BUSY` |

**Contrato.** Entrada `{"function_latex": "x^{2}", "variable": "x"}` (`variable` opcional). Respuesta `200`:

```json
{"ok": true,
 "data": {"input": {"latex": "x^{2}", "variable": "x", "interpreted_latex": "x^{2}", "expression": "x**2"},
          "result": {"latex": "\\frac{x^{3}}{3} + C", "expression": "x**3/3",
                     "special_functions": [], "definitions": {}, "note": null}}}
```

El LaTeX usa `\ln` y `\arctan` (no `\log`/`\operatorname{atan}`) y sólo comandos que MathQuill 0.10 renderiza (sin el espaciado `\,`).

| Integrando | `result.latex` |
|---|---|
| `x^{2}` | `\frac{x^{3}}{3} + C` |
| `7` | `7 x + C` |
| `0` | `C` |
| `\sin(x)` | `- \cos{\left(x \right)} + C` |
| `e^{x}` | `e^{x} + C` |
| `\ln(x)` | `x \ln{\left(x \right)} - x + C` |
| `\frac{1}{x}` | `\ln{\left(\left\|{x}\right\| \right)} + C` |
| `\frac{1}{x^{2}+1}` | `\arctan{\left(x \right)} + C` |
| `t^{2}` (variable `t`) | `\frac{t^{3}}{3} + C` |
| `e^{-x^{2}}` | `\frac{\sqrt{\pi} \operatorname{erf}{\left(x \right)}}{2} + C` |
