from django.urls import path

from api.views import MatrixOperateView

app_name = "api"

urlpatterns = [
    path("matrix/operate", MatrixOperateView.as_view(), name="matrix-operate"),
]
