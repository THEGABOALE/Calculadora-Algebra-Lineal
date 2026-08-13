from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from api.adapters.determinant import matrix_determinant
from api.adapters.matrices import matrix_operate
from api.adapters.reduce import matrix_reduce
from api.serializers import (
    MatrixDeterminantSerializer,
    MatrixOperateSerializer,
    MatrixReduceSerializer,
)


class MatrixOperateView(APIView):
    """POST /api/v1/matrix/operate -- las 8 operaciones de core/matrix_tools."""

    def post(self, request):
        serializer = MatrixOperateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = matrix_operate(
                operation=data["operation"],
                A=data.get("A"),
                B=data.get("B"),
                matrices=data.get("matrices"),
                scalar=data.get("scalar"),
            )
        except ValueError as exc:
            # Errores matemáticos de core/ (dimensiones que el serializer no
            # pudo anticipar del todo, matriz singular en inverse, etc.).
            return Response(
                {"error": {"code": "MATRIX_OP_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class MatrixReduceView(APIView):
    """POST /api/v1/matrix/reduce -- Gauss y Gauss-Jordan sobre core/gauss*.py."""

    def post(self, request):
        serializer = MatrixReduceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = matrix_reduce(
                method=data["method"], A=data["A"], b=data["b"]
            )
        except ValueError as exc:
            return Response(
                {"error": {"code": "MATRIX_REDUCE_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class MatrixDeterminantView(APIView):
    """POST /api/v1/matrix/determinant -- Sarrus y cofactores sobre core/cramer.py."""

    def post(self, request):
        serializer = MatrixDeterminantSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = matrix_determinant(method=data["method"], A=data["A"])
        except ValueError as exc:
            return Response(
                {"error": {"code": "MATRIX_DETERMINANT_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)
