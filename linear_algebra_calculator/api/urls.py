from django.urls import path

from api.views import (
    AbsRelErrorView,
    BisectionView,
    DerivativeView,
    ErrorAccumulationView,
    IntegralView,
    FalsePositionView,
    MatrixDeterminantView,
    MatrixOperateView,
    MatrixPropertiesView,
    MatrixReduceView,
    NewtonRaphsonView,
    PropagationErrorView,
    SecantView,
    VectorCombinationView,
    VectorOperateView,
)

app_name = "api"

urlpatterns = [
    path("matrix/operate", MatrixOperateView.as_view(), name="matrix-operate"),
    path("matrix/reduce", MatrixReduceView.as_view(), name="matrix-reduce"),
    path("matrix/determinant", MatrixDeterminantView.as_view(), name="matrix-determinant"),
    path("matrix/properties", MatrixPropertiesView.as_view(), name="matrix-properties"),
    path("vectors/operate", VectorOperateView.as_view(), name="vectors-operate"),
    path("vectors/combination", VectorCombinationView.as_view(), name="vectors-combination"),
    path("numeric/abs-rel-error", AbsRelErrorView.as_view(), name="abs-rel-error"),
    path("numeric/error-accumulation", ErrorAccumulationView.as_view(), name="error-accumulation"),
    path("numeric/propagation-error", PropagationErrorView.as_view(), name="propagation-error"),
    path("numeric/bisection-method", BisectionView.as_view(), name="bisection-method"),
    path("numeric/false-position", FalsePositionView.as_view(), name="false-position"),
    path("numeric/newton-raphson", NewtonRaphsonView.as_view(), name="newton-raphson"),
    path("numeric/secant", SecantView.as_view(), name="secant"),
    # "derivate" (sic): es la ruta que ya usa frontend/src/api/client.ts.
    path("calculus/derivate", DerivativeView.as_view(), name="derivate"),
    path("calculus/integral", IntegralView.as_view(), name="integral"),
]
