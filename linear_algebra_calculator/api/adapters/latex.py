"""
LaTeX -> texto plano para core/numeric.

core/numeric/_expresiones.py parsea con sympy.parsing.sympy_parser.parse_expr,
texto tipo "x**2 - 2" -- no LaTeX. El frontend a portar tiene un teclado
matemático (MathQuill/KaTeX) que emite LaTeX, así que hace falta traducir
antes de llegar a core/.

sympy.parsing.latex.parse_latex necesita antlr4-python3-runtime, una
dependencia pesada y con una versión puntual (4.11.x: sympy 1.14 generó su
gramática con esa versión; una más nueva revienta con ImportError al primer
parseo, verificado). Se confina ACÁ, en la capa API -- core/ sigue
string-first sin saber que LaTeX existe, y el CLI (que sólo escribe texto
plano tipo "x**2 - 2") nunca importa este módulo ni antlr4. Import diferido
dentro de la función, mismo criterio que sympy en core/numeric/_expresiones.py.
"""

from __future__ import annotations

import re


# Tope para exponentes y factoriales numéricos. 2^{1000000000} o 1000000!
# construirían enteros gigantes al reparsear el texto con evaluate=True
# (core/numeric/_expresiones.parsear): se rechazan sobre el árbol que deja
# parse_latex, que todavía no evaluó nada.
NUMERO_MAXIMO_EN_EXPONENTE = 1000


def _rechazar_numeros_enormes(expr) -> None:
    from sympy import Pow, factorial

    for nodo in expr.atoms(Pow, factorial):
        argumento = nodo.exp if isinstance(nodo, Pow) else nodo.args[0]
        if not argumento.is_number:
            continue
        try:
            # evalf sobre el árbol sin evaluar: punto flotante de mpmath,
            # barato aunque el exponente sea 10^10.
            magnitud = abs(argumento.evalf(15))
            demasiado = bool(magnitud > NUMERO_MAXIMO_EN_EXPONENTE)
        except Exception:
            demasiado = True
        if demasiado:
            que = "un exponente" if isinstance(nodo, Pow) else "un factorial"
            raise ValueError(
                f"La expresión tiene {que} demasiado grande "
                f"(máximo {NUMERO_MAXIMO_EN_EXPONENTE} en valor absoluto)."
            )


_ESPACIADO = re.compile(r"\\(?:qquad|quad)(?![A-Za-z])|\\[ ,;:!]|~")


def latex_a_texto(latex: str, estricto: bool = False) -> str:
    """Convierte una expresión LaTeX a texto que core/numeric puede parsear.

    parse_latex ya devuelve un Expr de sympy; se lo vuelve a convertir a
    texto con str() -- sympy garantiza que sea reparseable -- para que
    core/numeric._expresiones.parsear() lo reciba como el string plano que
    espera (compilar()/parsear() lo vuelven a parsear con parse_expr). No se
    le pasa el Expr directo: así el mismo camino (texto plano) sirve para
    CLI y web, y core/ no necesita saber que este módulo existe.

    `estricto=True` usa el modo estricto de parse_latex: el modo por defecto
    "recupera" entradas truncadas en silencio ("x^{" o "x+" se leen como
    "x"). En entradas válidas los dos modos dan lo mismo. Los métodos
    numéricos siguen con el default; el cálculo simbólico (calculus/*) usa el
    estricto para no derivar una función distinta de la escrita.
    """
    from sympy.parsing.latex import parse_latex

    texto = latex.strip()
    if texto.startswith("$") and texto.endswith("$"):
        texto = texto[1:-1].strip()
    texto = texto.replace(r"\left", "").replace(r"\right", "")
    # Comandos de espaciado (\ , \, \; \: \! \quad \qquad, ~): MathQuill los
    # inserta al escribir un espacio y no tienen significado matemático, pero
    # el parser estricto no los entiende ("\sqrt{\ x}", "\pi\ \frac{1}{4}").
    texto = _ESPACIADO.sub(" ", texto).strip()

    if not texto:
        raise ValueError("La expresión LaTeX está vacía.")

    try:
        expr = parse_latex(texto, strict=estricto)
    except Exception as exc:
        raise ValueError(f"No se pudo interpretar la expresión LaTeX {latex!r}: {exc}") from exc

    _rechazar_numeros_enormes(expr)
    return str(expr)


__all__ = ["latex_a_texto"]
