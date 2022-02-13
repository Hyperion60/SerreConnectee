from django.urls import path, re_path
from Serre import views


urlpatterns = [
    path('add/', views.serre_add, name="serre-add"),
    path('update/token/<str:token>/', views.renew_token, name="renew-token"),
    path('modify/<int:pk>/', views.modify_serre, name="modify-serre"),
    path('lora/add/', views.lora_releve, name="lora-add"),
    path('wifi/add/', views.wifi_releve, name="wifi-add"),
    path('del/<int:pk>/', views.delete_serre, name="delete-serre"),
]
