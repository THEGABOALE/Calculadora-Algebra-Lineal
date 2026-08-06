from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home_page, name='home'),
    path('calculatorMain/', views.calculatorMain, name='calculatorMain'),
    ## Sistemas de ecuaciones lineales ##
    path('ecuationInput/', views.ecuationInput, name='ecuationInput'),
    path('ecuationResolution/', views.ecuationResolution, name='ecuationResolution'),
    ## Resolución de operación de vectores ##
    path('vectorInput/', views.vectorInput, name='vectorInput'),
    path('vectorResolution/', views.vectorResolution, name='vectorResolution'),
    ## Operaciones con matrices (determinante, inversa, rango, transpuesta) ##
    path('matrixInput/', views.matrixInput, name='matrixInput'),
    path('matrixOperationResolution/', views.matrixOperationResolution, name='matrixOperationResolution'),
]
