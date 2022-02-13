from django.urls import path, re_path
from Serre import views


urlpatterns = [
    path('add/', views.serre_add, name="serre-add"),
    path('update/token/<str:token>/', views.renew_token, name="renew-token"),
    path('modify/<int:pk>/', views.modify_serre, name="modify-serre"),
    path('del/<int:pk>/', views.delete_serre, name="delete-serre"),
]
