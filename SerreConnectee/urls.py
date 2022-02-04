"""SerreConnectee URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include

from SerreConnectee import views, account
import Serre

urlpatterns = [
    path('', views.index, name="index"),
    path('about/', views.about, name="about"),
    path('account/detail/', account.account_detail, name="detail"),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-\']+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',
            views.activate_account, name="activate"),
    path('admin/', admin.site.urls, name="admin"),
    path('detail/', views.user_detail, name="detail"),
    path('login/', views.login_user, name="login"),
    path('logout/', views.logout_user, name="logout"),
    re_path(r'^modify/(?P<uidb64>[0-9A-Za-z_\-\']+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',
            views.modify_password, name="modify-password"),
    path('recover/', views.recover_password, name="recover-password"),
    path('serre/', include('Serre.urls')),
    path('signup/', views.signup_user, name="signup"),
    path('test/', views.test_arduino),
    path('delete/<int:pk>/', views.user_ask_delete, name="ask-delete"),
    re_path(r'^delete/(?P<uidb64>[0-9A-Za-z_\-\']+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',
            views.user_delete, name="delete-user"),
    # path('serre/get/token/', Serre.views)
]
