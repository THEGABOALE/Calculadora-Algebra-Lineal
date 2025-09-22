from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home_page, name='home'),
    path('systemsolver/', views.system_solver, name='system_solver'),
    path('calculate/', views.calculate, name='calculate'),
]
