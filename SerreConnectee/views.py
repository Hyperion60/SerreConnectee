from django.contrib.auth import authenticate, logout
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.utils.datastructures import MultiValueDictKeyError


def check_email(context, email):
    if not '@' in email or ';' in email:
        context['errors'].append("Format d'email invalide")


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


def signup_user(request):
    context = {
        'next': request.GET.get('next', '/'),
        'errors': [],
        'restricted': True,
    }

    if request.POST:
        try:
            context['username'] = request.POST['username']
            check_email(context, request.POST['email'])
            if len(User.objects.filter(email__exact=request.POST['email'])):
                context['errors'].append("L'adresse e-mail est déjà utilisée")
            if not len(context['errors']):
                context['email'] = request.POST['email']
                if request.POST['password1'] != request.POST['password2']:
                    context['errors'].append("Les mots de passe ne correspondent pas.")
                else:
                    context['password'] = request.POST['password1']
        except MultiValueDictKeyError:
            context['errors'].append("Champ(s) manquant(s)")

        if not len(context['errors']):
            new_user = User(username=context['username'],
                            email=context['email'],
                            is_active=False)
            new_user.set_password(context['password'])
            new_user.save()
            context['message'] = "Un lien de validation a été envoyé à votre adresse email pour l'activation du compte"
            return render(request, "index.html", context)
    return render(request, "User/signup.html", context)
