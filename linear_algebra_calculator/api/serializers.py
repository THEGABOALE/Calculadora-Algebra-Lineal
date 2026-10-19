"""
Serializers de la API. Validan FORMA de la request (tipos, presencia de
campos, dimensiones consistentes) -- no reglas matemáticas del dominio. Esas
viven en core/ y llegan hasta la vista como ValueError.

La distinción importa: es la lección del repo del que se portó el frontend,
donde el chequeo de Bolzano de bisección vivía en el serializer y no en el
algoritmo -- cualquier consumidor que no pasara por esa API REST (el CLI de
este repo, por ejemplo) quedaba sin esa validación. Acá "dimensiones
compatibles para sumar" es forma (una lista tiene el largo que dice tener);
"la matriz es singular" es matemática y se entera recién core/matrix_tools.
"""

from __future__ import annotations

from rest_framework import serializers

from core.calculo import LARGO_MAXIMO, validar_variable
from core.numeric.errores import (
    DECIMALES_APROXIMACION_MAXIMOS,
    DECIMALES_MAXIMOS,
    DECIMALES_POR_DEFECTO,
    DECIMALES_PRESENTACION_POR_DEFECTO,
    ITERACIONES_MAXIMAS,
    leer_decimal,
    leer_monto,
    leer_tasa,
)


class MatrixOperateSerializer(serializers.Serializer):
    operation = serializers.ChoiceField(
        choices=[
            "add", "sub", "scalar", "transpose", "matmul",
            "sum_many", "sub_many", "matmul_chain", "inverse",
        ]
    )
    A = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()), required=False
    )
    B = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()), required=False
    )
    matrices = serializers.ListField(
        child=serializers.ListField(child=serializers.ListField(child=serializers.FloatField())),
        required=False,
    )
    scalar = serializers.FloatField(required=False)

    @staticmethod
    def _is_matrix(M) -> bool:
        return isinstance(M, list) and len(M) > 0 and all(isinstance(row, list) for row in M)

    @staticmethod
    def _same_size(A, B) -> bool:
        return len(A) == len(B) and len(A[0]) == len(B[0])

    @staticmethod
    def _exigir_filas_iguales(M, nombre: str) -> None:
        # Las demás comprobaciones de este serializer miran sólo len(M[0]):
        # con filas de distinto largo, core/ reventaba (500) o, en transpose
        # y matmul_chain, devolvía 200 con elementos perdidos. Mismo mensaje
        # que los otros serializers de matrices.
        if any(len(row) != len(M[0]) for row in M):
            raise serializers.ValidationError(
                f"Todas las filas de '{nombre}' deben tener la misma longitud."
            )

    def validate(self, data):
        op = data["operation"]
        A, B = data.get("A"), data.get("B")
        matrices = data.get("matrices")
        scalar = data.get("scalar")

        if op in ("add", "sub"):
            if A is None or B is None:
                raise serializers.ValidationError(f"Para '{op}' se requieren 'A' y 'B'.")
            if not self._is_matrix(A) or not self._is_matrix(B):
                raise serializers.ValidationError("A y B deben ser matrices no vacías.")
            self._exigir_filas_iguales(A, "A")
            self._exigir_filas_iguales(B, "B")
            if not self._same_size(A, B):
                raise serializers.ValidationError("A y B deben tener la misma dimensión.")

        elif op == "scalar":
            if A is None or scalar is None:
                raise serializers.ValidationError("Para 'scalar' se requieren 'A' y 'scalar'.")
            if not self._is_matrix(A):
                raise serializers.ValidationError("A debe ser una matriz no vacía.")
            self._exigir_filas_iguales(A, "A")

        elif op == "transpose":
            if A is None:
                raise serializers.ValidationError("Para 'transpose' se requiere 'A'.")
            if not self._is_matrix(A):
                raise serializers.ValidationError("A debe ser una matriz no vacía.")
            self._exigir_filas_iguales(A, "A")

        elif op == "matmul":
            if A is None or B is None:
                raise serializers.ValidationError("Para 'matmul' se requieren 'A' y 'B'.")
            if not self._is_matrix(A) or not self._is_matrix(B):
                raise serializers.ValidationError("A y B deben ser matrices no vacías.")
            self._exigir_filas_iguales(A, "A")
            self._exigir_filas_iguales(B, "B")
            if len(A[0]) != len(B):
                raise serializers.ValidationError(
                    f"Incompatibilidad dimensional: cols(A)={len(A[0])} != filas(B)={len(B)}."
                )

        elif op in ("sum_many", "sub_many", "matmul_chain"):
            if not matrices or len(matrices) < 2:
                raise serializers.ValidationError(
                    f"'{op}' requiere 'matrices' con al menos 2 matrices."
                )
            if any(not self._is_matrix(M) for M in matrices):
                raise serializers.ValidationError("Todas las 'matrices' deben ser no vacías.")
            for i, M in enumerate(matrices):
                self._exigir_filas_iguales(M, f"matrices[{i}]")
            if op in ("sum_many", "sub_many"):
                first = matrices[0]
                if any(not self._same_size(first, M) for M in matrices[1:]):
                    raise serializers.ValidationError(
                        "Todas las matrices deben tener la misma dimensión."
                    )
            else:  # matmul_chain
                for i in range(len(matrices) - 1):
                    if len(matrices[i][0]) != len(matrices[i + 1]):
                        raise serializers.ValidationError(
                            f"Incompatibilidad en la cadena en la posición {i} -> {i+1}."
                        )

        elif op == "inverse":
            if A is None:
                raise serializers.ValidationError("Para 'inverse' se requiere 'A'.")
            if not self._is_matrix(A):
                raise serializers.ValidationError("A debe ser una matriz no vacía.")
            self._exigir_filas_iguales(A, "A")
            if len(A) != len(A[0]):
                raise serializers.ValidationError("La matriz debe ser cuadrada para invertir.")

        return data


class MatrixReduceSerializer(serializers.Serializer):
    # 'cramer' entra acá y no en matrix/determinant: resuelve sistemas, así
    # que necesita A y b igual que gauss y gauss-jordan. Que la matriz sea
    # cuadrada -- lo único que Cramer exige de más -- NO se valida acá: lo
    # exige CramerMethod.__init__ con un ValueError, y la vista lo traduce a
    # 400. Duplicarlo sería dejar la regla en dos lugares que pueden
    # divergir, que es justo lo que este módulo evita por diseño.
    method = serializers.ChoiceField(choices=["gauss", "gauss-jordan", "cramer"])
    A = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()), required=False
    )
    b = serializers.ListField(child=serializers.FloatField(), required=False)
    Ab = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()), required=False
    )

    @staticmethod
    def _is_matrix(M) -> bool:
        return isinstance(M, list) and len(M) > 0 and all(isinstance(row, list) for row in M)

    def validate(self, data):
        A, b, Ab = data.get("A"), data.get("b"), data.get("Ab")

        if Ab is None and (A is None or b is None):
            raise serializers.ValidationError("Enviá 'A' y 'b', o 'Ab'.")
        if Ab is not None and (A is not None or b is not None):
            raise serializers.ValidationError("Enviá 'Ab', o 'A' y 'b', no ambos.")

        if Ab is not None:
            if not self._is_matrix(Ab) or len(Ab[0]) < 2:
                raise serializers.ValidationError(
                    "'Ab' debe ser una matriz no vacía con al menos 2 columnas."
                )
            if any(len(row) != len(Ab[0]) for row in Ab):
                raise serializers.ValidationError("Todas las filas de 'Ab' deben tener la misma longitud.")
            # Última columna = b; el resto, A. Se resuelve acá para que el
            # adaptador siempre reciba A y b ya separados.
            data["A"] = [row[:-1] for row in Ab]
            data["b"] = [row[-1] for row in Ab]
        else:
            if not self._is_matrix(A):
                raise serializers.ValidationError("'A' no puede ser vacía.")
            if any(len(row) != len(A[0]) for row in A):
                raise serializers.ValidationError("Todas las filas de 'A' deben tener la misma longitud.")
            if len(b) != len(A):
                raise serializers.ValidationError(
                    f"Dimensiones inconsistentes: A es {len(A)}x{len(A[0])} y b tiene longitud {len(b)}."
                )

        return data


class MatrixDeterminantSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=["sarrus", "cofactors", "cramer"])
    A = serializers.ListField(child=serializers.ListField(child=serializers.FloatField()))

    @staticmethod
    def _is_matrix(M) -> bool:
        return isinstance(M, list) and len(M) > 0 and all(isinstance(row, list) for row in M)

    def validate(self, data):
        method = data["method"]

        if method == "cramer":
            # No es un error de forma: 'cramer' es una opción reconocida,
            # pero no calcula determinantes -- resuelve sistemas (necesita A
            # y b). Se rechaza acá, explícito, en vez de redirigirlo en
            # silencio a cofactores.
            raise serializers.ValidationError(
                "method='cramer' resuelve sistemas de ecuaciones, no calcula "
                "determinantes. Usá matrix/reduce con method='cramer', que "
                "toma A y b."
            )

        A = data["A"]
        if not self._is_matrix(A):
            raise serializers.ValidationError("'A' no puede ser vacía.")
        if any(len(row) != len(A[0]) for row in A):
            raise serializers.ValidationError("Todas las filas de 'A' deben tener la misma longitud.")
        if len(A) != len(A[0]):
            raise serializers.ValidationError("La matriz debe ser cuadrada para calcular el determinante.")

        return data


class MatrixPropertiesSerializer(serializers.Serializer):
    A = serializers.ListField(child=serializers.ListField(child=serializers.FloatField()))

    @staticmethod
    def _is_matrix(M) -> bool:
        return isinstance(M, list) and len(M) > 0 and all(isinstance(row, list) for row in M)

    def validate(self, data):
        A = data["A"]
        if not self._is_matrix(A):
            raise serializers.ValidationError("'A' no puede ser vacía.")
        if any(len(row) != len(A[0]) for row in A):
            raise serializers.ValidationError("Todas las filas de 'A' deben tener la misma longitud.")
        # No se exige cuadrada: rank_of y nullspace_vector aceptan
        # rectangulares, e is_singular ya devuelve None (no un error) cuando
        # A no es cuadrada. Rechazar acá duplicaría una decisión que core/ ya
        # toma sola.
        return data


class VectorOperateSerializer(serializers.Serializer):
    operation = serializers.ChoiceField(choices=["add", "sub", "escalar", "comb2", "comb3", "dot"])
    vectors = serializers.DictField(child=serializers.ListField(child=serializers.FloatField()))
    scalars = serializers.DictField(child=serializers.FloatField(), required=False)

    def validate(self, data):
        op = data["operation"]
        vecs = data.get("vectors") or {}
        sc = data.get("scalars") or {}

        def requerir(*nombres):
            for nombre in nombres:
                if nombre not in vecs:
                    raise serializers.ValidationError(f"Falta el vector '{nombre}'.")

        def misma_dimension(*nombres):
            requerir(*nombres)
            largos = {len(vecs[n]) for n in nombres}
            if len(largos) != 1:
                raise serializers.ValidationError(
                    f"Los vectores {', '.join(nombres)} deben tener la misma dimensión."
                )

        if op in ("add", "sub"):
            misma_dimension("u", "v")
        elif op == "escalar":
            requerir("u")
            if "c" not in sc:
                raise serializers.ValidationError("Para 'escalar' se requiere scalars.c.")
        elif op == "comb2":
            misma_dimension("u", "v")
            if "c" not in sc or "d" not in sc:
                raise serializers.ValidationError("Para 'comb2' se requieren scalars.c y scalars.d.")
        elif op == "comb3":
            misma_dimension("u", "v", "w")
            if "c" not in sc or "d" not in sc:
                raise serializers.ValidationError("Para 'comb3' se requieren scalars.c y scalars.d.")
        elif op == "dot":
            # dot usa las claves 'v' y 'w', no 'u' y 'v': así arma el
            # request el frontend (payload.vectors = {v: u, w: v}).
            misma_dimension("v", "w")

        return data


class VectorCombinationSerializer(serializers.Serializer):
    A = serializers.ListField(child=serializers.ListField(child=serializers.FloatField()))
    b = serializers.ListField(child=serializers.FloatField())

    @staticmethod
    def _is_matrix(M) -> bool:
        return isinstance(M, list) and len(M) > 0 and all(isinstance(row, list) for row in M)

    def validate(self, data):
        A, b = data["A"], data["b"]
        if not self._is_matrix(A):
            raise serializers.ValidationError("'A' no puede ser vacía.")
        if any(len(row) != len(A[0]) for row in A):
            raise serializers.ValidationError("Todas las filas de 'A' deben tener la misma longitud.")
        if len(b) != len(A):
            raise serializers.ValidationError(
                f"Dimensiones inconsistentes: A es {len(A)}x{len(A[0])} y b tiene longitud {len(b)}."
            )
        return data


# ---------------------------------------------------------------------------
# Métodos numéricos de búsqueda de raíces.
#
# Validan sólo forma: que function_latex/xi/xu/tolerance/x0/x1 estén
# presentes y tengan el tipo correcto. Lo matemático -- xi < xu, tolerancia
# positiva, Bolzano (f(xi)·f(xu) < 0), derivada nula, denominador nulo --
# vive en core/numeric/ y llega hasta la vista como ValueError o
# ZeroDivisionError. No se duplica ninguna de esas reglas acá: es la misma
# lección del comentario de arriba del módulo, aplicada a este dominio.
#
# max_iter vs. max_iterations: no es un error de tipeo -- así arma cada
# request AlgebraicMethods.tsx/BisectionInputs.tsx et al. Bisección es la
# única que manda 'max_iter'; regla falsa, Newton y secante mandan
# 'max_iterations'. Confirmado leyendo el código de cada componente, no
# asumido por analogía.
# ---------------------------------------------------------------------------

class BisectionSerializer(serializers.Serializer):
    function_latex = serializers.CharField(allow_blank=False)
    xi = serializers.FloatField()
    xu = serializers.FloatField()
    tolerance = serializers.FloatField()
    max_iter = serializers.IntegerField(required=False, min_value=1)


class FalsePositionSerializer(serializers.Serializer):
    function_latex = serializers.CharField(allow_blank=False)
    xi = serializers.FloatField()
    xu = serializers.FloatField()
    tolerance = serializers.FloatField()
    max_iterations = serializers.IntegerField(required=False, min_value=1)


class NewtonRaphsonSerializer(serializers.Serializer):
    function_latex = serializers.CharField(allow_blank=False)
    x0 = serializers.FloatField()
    tolerance = serializers.FloatField()
    max_iterations = serializers.IntegerField(required=False, min_value=1)
    # Aceptado por compatibilidad con el payload que arma el frontend; no se
    # usa. core/numeric siempre deriva simbólicamente, que es el único modo
    # que ofrece el selector del componente (una sola opción: "symbolic").
    derivate_mode = serializers.CharField(required=False)


class SecantSerializer(serializers.Serializer):
    function_latex = serializers.CharField(allow_blank=False)
    x0 = serializers.FloatField()
    x1 = serializers.FloatField()
    tolerance = serializers.FloatField()
    max_iterations = serializers.IntegerField(required=False, min_value=1)
    # Unidad de los argumentos de sin/cos/tan (issue #24). Antes se aceptaba
    # cualquier texto y se ignoraba: 'deg' devolvía la raíz en radianes. La
    # conversión vive en core/numeric/_expresiones.py; omitido = 'rad'.
    angle_mode = serializers.ChoiceField(choices=["rad", "deg"], required=False, default="rad")


# ---------------------------------------------------------------------------
# Cálculo de errores.
#
# Los valores llegan como texto (el frontend manda strings) y se validan con
# el mismo lector que usa core/numeric/errores.py: una sola regla de "qué es
# un número válido" para la API y para cualquier otro consumidor. Los
# mensajes van en castellano porque el frontend los muestra tal cual.
# ---------------------------------------------------------------------------

def _valor_numerico(nombre: str) -> serializers.CharField:
    return serializers.CharField(error_messages={
        "required": f"Falta el {nombre}.",
        "blank": f"Ingresá el {nombre}.",
        "null": f"Ingresá el {nombre}.",
        "invalid": f"El {nombre} debe ser un número.",
    })


class AbsRelErrorSerializer(serializers.Serializer):
    true_value = _valor_numerico("valor verdadero")
    approx_value = _valor_numerico("valor aproximado")
    decimals_display = serializers.IntegerField(
        required=False,
        default=DECIMALES_POR_DEFECTO,
        min_value=0,
        max_value=DECIMALES_MAXIMOS,
        error_messages={
            "invalid": "La cantidad de decimales debe ser un número entero.",
            "null": "La cantidad de decimales debe ser un número entero.",
            "min_value": "La cantidad de decimales no puede ser negativa.",
            "max_value": f"La cantidad de decimales no puede superar {DECIMALES_MAXIMOS}.",
        },
    )

    @staticmethod
    def _leer(valor: str, nombre: str) -> str:
        try:
            leer_decimal(valor, nombre)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))
        return valor

    def validate_true_value(self, valor):
        return self._leer(valor, "valor verdadero")

    def validate_approx_value(self, valor):
        return self._leer(valor, "valor aproximado")


def _entero(descripcion: str, minimo: int, maximo: int, **kwargs) -> serializers.IntegerField:
    mensaje = f"{descripcion} debe ser un número entero entre {minimo} y {maximo}."
    return serializers.IntegerField(
        min_value=minimo,
        max_value=maximo,
        error_messages={
            "required": f"Falta {descripcion[0].lower()}{descripcion[1:]}.",
            "invalid": mensaje,
            "null": mensaje,
            "min_value": mensaje,
            "max_value": mensaje,
        },
        **kwargs,
    )


class ErrorAccumulationSerializer(serializers.Serializer):
    # Mismo criterio que AbsRelErrorSerializer: los números llegan como texto
    # y se validan con los lectores de core/numeric/errores.py. Ningún campo
    # del cálculo tiene default -- un campo vacío es un error, no un 0 --; el
    # único opcional es interest_display_decimals, que sólo afecta la
    # presentación.
    initial_amount = _valor_numerico("monto inicial")
    rate = _valor_numerico("valor de la tasa")
    iterations = _entero("La cantidad de iteraciones", 1, ITERACIONES_MAXIMAS)
    mode = serializers.ChoiceField(
        choices=["trunc", "round"],
        error_messages={
            "required": "Falta el modo (trunc o round).",
            "invalid_choice": "El modo debe ser 'trunc' (truncar) o 'round' (redondear).",
            "null": "El modo debe ser 'trunc' (truncar) o 'round' (redondear).",
        },
    )
    approx_decimals = _entero(
        "La cantidad de decimales de la aproximación", 0, DECIMALES_APROXIMACION_MAXIMOS
    )
    interest_display_decimals = _entero(
        "La cantidad de decimales de presentación", 0, DECIMALES_MAXIMOS,
        required=False, default=DECIMALES_PRESENTACION_POR_DEFECTO,
    )

    @staticmethod
    def _leer(lector, valor):
        try:
            lector(valor)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))
        return valor

    def validate_initial_amount(self, valor):
        return self._leer(leer_monto, valor)

    def validate_rate(self, valor):
        return self._leer(leer_tasa, valor)


# ---------------------------------------------------------------------------
# Cálculo simbólico.
# ---------------------------------------------------------------------------

class DerivativeSerializer(serializers.Serializer):
    function_latex = serializers.CharField(
        max_length=LARGO_MAXIMO,
        error_messages={
            "required": "Falta la función a derivar (function_latex).",
            "blank": "Ingresá la función a derivar.",
            "null": "Ingresá la función a derivar.",
            "invalid": "La función debe enviarse como texto LaTeX.",
            "max_length": f"La expresión es demasiado larga (máximo {LARGO_MAXIMO} caracteres).",
        },
    )
    # Antes el frontend mostraba este campo pero no lo enviaba. Omitido = x.
    variable = serializers.CharField(
        required=False,
        default="x",
        error_messages={
            "blank": "Indicá la variable de derivación (por ejemplo x o t).",
            "null": "Indicá la variable de derivación (por ejemplo x o t).",
            "invalid": "La variable de derivación debe ser una letra.",
        },
    )

    def validate_variable(self, valor):
        try:
            validar_variable(valor)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))
        return valor


class PropagationErrorSerializer(serializers.Serializer):
    # x0 y delta_x son LaTeX de MathQuill (\frac{\pi}{6}, 0.5, ...), no
    # números: se validan como expresiones en core/numeric/propagacion.py.
    function_latex = serializers.CharField(
        max_length=LARGO_MAXIMO,
        error_messages={
            "required": "Falta la función f(x) (function_latex).",
            "blank": "Ingresá la función f(x).",
            "null": "Ingresá la función f(x).",
            "max_length": f"La función es demasiado larga (máximo {LARGO_MAXIMO} caracteres).",
        },
    )
    x0 = serializers.CharField(
        max_length=100,
        error_messages={"required": "Falta x₀.", "blank": "Ingresá x₀.", "null": "Ingresá x₀.",
                        "max_length": "x₀ es demasiado largo (máximo 100 caracteres)."},
    )
    delta_x = serializers.CharField(
        max_length=100,
        error_messages={"required": "Falta Δx.", "blank": "Ingresá Δx.", "null": "Ingresá Δx.",
                        "max_length": "Δx es demasiado largo (máximo 100 caracteres)."},
    )
    angle_mode = serializers.ChoiceField(
        choices=["rad", "deg"], required=False, default="rad",
        error_messages={"invalid_choice": "El modo angular debe ser 'rad' (radianes) o 'deg' (grados)."},
    )
    decimals = _entero("La cantidad de decimales", 0, DECIMALES_MAXIMOS, required=False, default=6)
