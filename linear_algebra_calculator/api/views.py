from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from api.adapters.calculo import derivative
from api.adapters.determinant import matrix_determinant
from api.adapters.matrices import matrix_operate
from api.adapters.numerico import (
    abs_rel_error,
    bisection_method,
    error_accumulation,
    false_position_method,
    newton_raphson_method,
    secant_method,
)
from api.adapters.properties import matrix_properties
from api.adapters.reduce import matrix_reduce
from api.adapters.vectores import linear_combination, vector_operate
from api.serializers import (
    AbsRelErrorSerializer,
    BisectionSerializer,
    DerivativeSerializer,
    ErrorAccumulationSerializer,
    FalsePositionSerializer,
    MatrixDeterminantSerializer,
    MatrixOperateSerializer,
    MatrixPropertiesSerializer,
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
    """POST /api/v1/matrix/reduce -- Gauss, Gauss-Jordan y Cramer.

    Los tres resuelven Ax=b: core/gauss.py, core/gauss_jordan.py y
    core/cramer.py. El ValueError que atrapa el except incluye el de
    CramerMethod.__init__ cuando A no es cuadrada.
    """

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


class MatrixPropertiesView(APIView):
    """POST /api/v1/matrix/properties -- rango, singularidad y núcleo sobre core/matrix_tools."""

    def post(self, request):
        serializer = MatrixPropertiesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = matrix_properties(A=data["A"])
        except ValueError as exc:
            return Response(
                {"error": {"code": "MATRIX_PROPERTIES_ERROR", "message": str(exc)}},
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
                angle_mode=data["angle_mode"],
            )
        except (ValueError, ZeroDivisionError) as exc:
            return Response(
                {"error": {"code": "SECANT_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class AbsRelErrorView(APIView):
    """POST /api/v1/numeric/abs-rel-error -- core/numeric/errores.py."""

    def post(self, request):
        serializer = AbsRelErrorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = abs_rel_error(
                true_value=data["true_value"],
                approx_value=data["approx_value"],
                decimals_display=data["decimals_display"],
            )
        except ValueError as exc:
            return Response(
                {"error": {"code": "ABS_REL_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class ErrorAccumulationView(APIView):
    """POST /api/v1/numeric/error-accumulation -- core/numeric/errores.py."""

    def post(self, request):
        serializer = ErrorAccumulationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = error_accumulation(
                initial_amount=data["initial_amount"],
                iterations=data["iterations"],
                mode=data["mode"],
                rate=data["rate"],
                approx_decimals=data["approx_decimals"],
                interest_display_decimals=data["interest_display_decimals"],
            )
        except ValueError as exc:
            return Response(
                {"error": {"code": "ERROR_ACCUMULATION_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class DerivativeView(APIView):
    """POST /api/v1/calculus/derivate -- core/calculo.py.

    Toda falla es de la entrada (LaTeX inválido, función desconocida, letra
    que no es la variable): 400 VALIDATION_ERROR, con el mensaje como texto.
    """

    def post(self, request):
        serializer = DerivativeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = derivative(function_latex=data["function_latex"], variable=data["variable"])
        except ValueError as exc:
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)
