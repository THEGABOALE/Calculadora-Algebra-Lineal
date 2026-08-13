from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from api.adapters.determinant import matrix_determinant
from api.adapters.matrices import matrix_operate
from api.adapters.numerico import (
    bisection_method,
    false_position_method,
    newton_raphson_method,
    secant_method,
)
from api.adapters.reduce import matrix_reduce
from api.adapters.vectores import linear_combination, vector_operate
from api.serializers import (
    BisectionSerializer,
    FalsePositionSerializer,
    MatrixDeterminantSerializer,
    MatrixOperateSerializer,
    MatrixReduceSerializer,
    NewtonRaphsonSerializer,
    SecantSerializer,
    VectorCombinationSerializer,
    VectorOperateSerializer,
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


class VectorOperateView(APIView):
    """POST /api/v1/vectors/operate -- las 6 operaciones de core/vector.Vector."""

    def post(self, request):
        serializer = VectorOperateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = vector_operate(
                operation=data["operation"],
                vectors=data["vectors"],
                scalars=data.get("scalars"),
            )
        except ValueError as exc:
            return Response(
                {"error": {"code": "VECTOR_OP_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class VectorCombinationView(APIView):
    """POST /api/v1/vectors/combination -- Ax=b sobre core/vector_tools.py."""

    def post(self, request):
        serializer = VectorCombinationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = linear_combination(A=data["A"], b=data["b"])
        except ValueError as exc:
            return Response(
                {"error": {"code": "VECTOR_COMB_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Métodos numéricos. ValueError y ZeroDivisionError vienen de core/numeric/ --
# LaTeX inválido, intervalo sin cambio de signo, tolerancia no positiva,
# derivada nula, denominador nulo -- y la vista los traduce a 400 con el
# mensaje del motor, no un mensaje genérico de la capa HTTP.
# ---------------------------------------------------------------------------

class BisectionView(APIView):
    """POST /api/v1/numeric/bisection-method -- core/numeric/metodos_cerrados.py."""

    def post(self, request):
        serializer = BisectionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = bisection_method(
                function_latex=data["function_latex"],
                xi=data["xi"],
                xu=data["xu"],
                tolerance=data["tolerance"],
                max_iter=data.get("max_iter", 100),
            )
        except (ValueError, ZeroDivisionError) as exc:
            return Response(
                {"error": {"code": "BISECTION_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class FalsePositionView(APIView):
    """POST /api/v1/numeric/false-position -- core/numeric/metodos_cerrados.py."""

    def post(self, request):
        serializer = FalsePositionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = false_position_method(
                function_latex=data["function_latex"],
                xi=data["xi"],
                xu=data["xu"],
                tolerance=data["tolerance"],
                max_iter=data.get("max_iterations", 100),
            )
        except (ValueError, ZeroDivisionError) as exc:
            return Response(
                {"error": {"code": "FALSE_POSITION_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class NewtonRaphsonView(APIView):
    """POST /api/v1/numeric/newton-raphson -- core/numeric/metodos_abiertos.py."""

    def post(self, request):
        serializer = NewtonRaphsonSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = newton_raphson_method(
                function_latex=data["function_latex"],
                x0=data["x0"],
                tolerance=data["tolerance"],
                max_iter=data.get("max_iterations", 100),
            )
        except (ValueError, ZeroDivisionError) as exc:
            return Response(
                {"error": {"code": "NEWTON_RAPHSON_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class SecantView(APIView):
    """POST /api/v1/numeric/secant -- core/numeric/metodos_abiertos.py."""

    def post(self, request):
        serializer = SecantSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = secant_method(
                function_latex=data["function_latex"],
                x0=data["x0"],
                x1=data["x1"],
                tolerance=data["tolerance"],
                max_iter=data.get("max_iterations", 100),
            )
        except (ValueError, ZeroDivisionError) as exc:
            return Response(
                {"error": {"code": "SECANT_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)
