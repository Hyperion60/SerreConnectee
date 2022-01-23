from django.contrib.auth import authenticate, logout
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt

from SerreConnectee.tokens import account_activation_token
from SerreConnectee.settings import EMAIL_HOST_USER


def __check_email(context, email):
    if not '@' in email or ';' in email:
        context['errors'].append("Format d'email invalide")


def __send_verification_email(request, user):
    mail_subject = "Activation du compte pour le site Serre Connectée"
    current_site = get_current_site(request)
    mail_message = render_to_string('User/email/activate_email.html',
        {
            'user': user,
            'domain': current_site,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user=user)
        }
    )
    send_mail(mail_subject, mail_message, EMAIL_HOST_USER, [user.email], fail_silently=False)


def __send_recover_email(request, user):
    mail_subject = "Réinitialisation du mot de passe - Serre Connectée"
    current_site = get_current_site(request)
    mail_message = render_to_string('User/email/recover_password.html',
        {
            'user': user,
            'domain': current_site,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user=user)
        }
    )
    send_mail(mail_subject, mail_message, EMAIL_HOST_USER, [user.email], fail_silently=False)


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
            __check_email(context, request.POST['email'])
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
            __send_verification_email(request, new_user)
            context['restricted'] = None
            context['message'] = "Un lien de validation a été envoyé à votre adresse email pour l'activation du compte"
            return render(request, "index.html", context)
    return render(request, "User/signup.html", context)


def activate_account(request, uidb64, token):
    context = {
        'errors': [],
    }
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None:
        if account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)
            context['message'] = "Votre compte a été validé avec succès !"
        else:
            if user.is_active:
                context['errors'].append("Votre compte a déjà été activé !")
    else:
        context['errors'].append("Le lien est invalide, veuillez contacter un administrateur")

    return render(request, "index.html", context)


def recover_password(request):
    context = {
        'errors': [],
    }
    if request.POST:
        try:
            context['email'] = request.POST['email']
            context['user'] = User.objects.get(email__exact=context['email'])
            __send_recover_email(request, context['user'])
            context['message'] = "Un email vient de vous être envoyer pour réinitialiser votre mot de passe"
            return render(request, "index.html", context)
        except MultiValueDictKeyError:
            context['errors'].append("Champ email manquant")
        except User.DoesNotExist:
            context['errors'].append("L'adresse email est introuvable")

    return render(request, "User/before-password.html", context)


def modify_password(request, uidb64, token):
    context = {
        'errors': [],
    }
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None:
        if request.POST:
            if account_activation_token.check_token(user, token):
                try:
                    password = request.POST['password']
                    password2 = request.POST['password2']
                    if password2 == password:
                        user.set_password(password)
                        user.save()
                    else:
                        context['errors'].append("Les mots de passes ne correspondent pas")
                except MultiValueDictKeyError:
                    context['errors'].append("Un ou plusieurs champs requis ne sont pas renseignés")
            else:
                context['errors'].append("Le lien est invalide, veuillez recommencer la procédure")
    else:
        context['errors'].append("Le lien est invalide, veuillez recommencer la procédure")

    return render(request, "User/after-password.html", context)


@csrf_exempt
def test_arduino(request):
    if request.POST:
        print(request)
        print(request.POST.content)
    print(request.body.decode())
    return HttpResponse("OK")
