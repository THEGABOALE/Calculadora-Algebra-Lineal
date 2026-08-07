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


class MatrixReduceSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=["gauss", "gauss-jordan"])
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
                "determinantes. Usá matrix/reduce con method='cramer' (Fase 7)."
            )

        A = data["A"]
        if not self._is_matrix(A):
            raise serializers.ValidationError("'A' no puede ser vacía.")
        if any(len(row) != len(A[0]) for row in A):
            raise serializers.ValidationError("Todas las filas de 'A' deben tener la misma longitud.")
        if len(A) != len(A[0]):
            raise serializers.ValidationError("La matriz debe ser cuadrada para calcular el determinante.")

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
