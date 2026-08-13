from django.urls import path

from api.views import (
    MatrixDeterminantView,
    MatrixOperateView,
    MatrixReduceView,
    VectorCombinationView,
    VectorOperateView,
)

app_name = "api"

urlpatterns = [
    path("matrix/operate", MatrixOperateView.as_view(), name="matrix-operate"),
    path("matrix/reduce", MatrixReduceView.as_view(), name="matrix-reduce"),
    path("matrix/determinant", MatrixDeterminantView.as_view(), name="matrix-determinant"),
    path("vectors/operate", VectorOperateView.as_view(), name="vectors-operate"),
    path("vectors/combination", VectorCombinationView.as_view(), name="vectors-combination"),
]
