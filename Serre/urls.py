from django.urls import path, re_path
from Serre import views


urlpatterns = [
    path('add/', views.serre_add, name="serre-add"),
]