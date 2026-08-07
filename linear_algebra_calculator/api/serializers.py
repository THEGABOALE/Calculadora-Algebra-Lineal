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
            if not self._same_size(A, B):
                raise serializers.ValidationError("A y B deben tener la misma dimensión.")

        elif op == "scalar":
            if A is None or scalar is None:
                raise serializers.ValidationError("Para 'scalar' se requieren 'A' y 'scalar'.")
            if not self._is_matrix(A):
                raise serializers.ValidationError("A debe ser una matriz no vacía.")

        elif op == "transpose":
            if A is None:
                raise serializers.ValidationError("Para 'transpose' se requiere 'A'.")
            if not self._is_matrix(A):
                raise serializers.ValidationError("A debe ser una matriz no vacía.")

        elif op == "matmul":
            if A is None or B is None:
                raise serializers.ValidationError("Para 'matmul' se requieren 'A' y 'B'.")
            if not self._is_matrix(A) or not self._is_matrix(B):
                raise serializers.ValidationError("A y B deben ser matrices no vacías.")
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
            if len(A) != len(A[0]):
                raise serializers.ValidationError("La matriz debe ser cuadrada para invertir.")

        return data
