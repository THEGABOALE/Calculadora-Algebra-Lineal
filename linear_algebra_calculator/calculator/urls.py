from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home_page, name='home'),
    path('ecuationInput/', views.ecuationInput, name='ecuationInput'),
    path('ecuationResolution/', views.ecuationResolution, name='ecuationResolution'),
]
