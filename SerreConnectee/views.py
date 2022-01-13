from django.contrib.auth import authenticate, logout
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.utils.datastructures import MultiValueDictKeyError


def about(request):
    return render(request, "about.html")


def index(request):
    return render(request, "index.html")


def logout_user(request):
    logout(request)
    return redirect("/")


def login_user(request):
    context = {
        'next': request.GET.get('next', '/'),
        'errors': [],
        'restricted': True,
    }
    if request.user.is_authenticated:
        context['errors'].append("Vous êtes déjà connecté !")
        return render(request, "index.html", context)

    if request.POST:
        user = None
        try:
            username = request.POST['username']
            password = request.POST['password']
            user = User.objects.get(username__exact=username)
            if not user.check_password(password):
                context['errors'].append("Mot de passe invalide")
            else:
                user = authenticate(username=username, password=password)
        except MultiValueDictKeyError:
            context['errors'].append("Champ(s) manquant(s)")
        except User.DoesNotExist:
            context['errors'].append("Utilisateur introuvable")

        if not len(context['errors']) and user:
            login(request, user)
            return redirect(context['next'])

    return render(request, "User/login.html", context)
