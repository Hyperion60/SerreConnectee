import datetime

import pytz
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page

from Serre.models import Serre, Releves
from SerreConnectee.tokens import account_activation_token
from SerreConnectee.settings import EMAIL_HOST_USER, TIME_ZONE


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


def __send_delete_email(request, user):
    mail_subject = "Suppression du compte - Serre Connectée"
    current_site = get_current_site(request)
    mail_message = render_to_string('User/email/delete_user.html',
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
    context = {}
    if request.GET.get('code', '') == '1':
        context['message'] = "Mot de passe modifié avec succès"
    elif request.GET.get('code', '') == '2':
        context['message'] = "La suppression a été annulée"
    elif request.GET.get('code', '') == '3':
        context['message'] = "Le compte utilisateur a été supprimé avec succès"
    elif request.GET.get('code', '') == '4':
        context['message'] = "Un email de validation vient de vous être envoyé pour confirmer la suppression"
    elif request.GET.get('code', '') == '5':
        context['message'] = "La serre a été créée avec succès"

    context['serres'] = Serre.objects.all().order_by('pk')
    return render(request, "index.html", context)


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
            if len(User.objects.filter(username__exact=request.POST['username'])):
                context['errors'].append("Le nom d'utilisateur est déjà utilisé")
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
                            is_active=False,
                            date_joined=datetime.datetime.now(pytz.timezone(TIME_ZONE)))
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
        'restricted': True,
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
        'token': token,
        'uidb64': uidb64,
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
                        return redirect("/?code=1")
                    else:
                        context['errors'].append("Les mots de passes ne correspondent pas")
                except MultiValueDictKeyError:
                    context['errors'].append("Un ou plusieurs champs requis ne sont pas renseignés")
            else:
                context['errors'].append("Le lien est invalide, veuillez recommencer la procédure")
    else:
        context['errors'].append("Le lien est invalide, veuillez recommencer la procédure")

    return render(request, "User/after-password.html", context)


@login_required(login_url="/login/")
def user_detail(request):
    context = {
        'errors': [],
        'user': request.user,
        'date_joined': request.user.date_joined.replace(microsecond=0),
        'code': request.GET.get('code', None),
        'err': request.GET.get('err', None),
    }
    if context['code'] == '1':
        context['message'] = "La serre a été modifiée avec succès"
    if context['code'] == '2':
        context['message'] = "La suppression de la serre a été annulée"
    if context['code'] == '3':
        context['message'] = "La serre a été supprimée avec succès"
    if context['err'] == '1':
        context['errors'].append("La serre demandée est introuvable, la clé primaire est introuvable")
    if context['err'] == '2':
        context['errors'].append("Vous ne pouvez pas supprimer une serre qui ne vous appartient pas")

    if request.POST:
        try:
            old_pass = request.POST['old-password']
            new_pass = request.POST['new-password']
            new_pass1 = request.POST['new-password1']
            if request.user.check_password(old_pass) and new_pass == new_pass1:
                request.user.set_password(new_pass)
                request.user.save()
                context['message'] = "Mot de passe modifié avec succès"
            else:
                if new_pass != new_pass1:
                    context['errors'].append("Les nouveaux mots de passes ne correspondent pas")
                else:
                    context['errors'].append("L'ancien mot de passe est invalide")
        except MultiValueDictKeyError:
            context['errors'].append("Un ou plusieurs champs sont manquants")

    context['serres'] = Serre.objects.filter(user=request.user)
    context['status'] = []
    context['date'] = []
    for serre in context['serres']:
        releves = Releves.objects.filter(serre=serre).order_by('-timestamp')
        if not len(releves):
            context['date'].append("Jamais")
            context['status'].append("Hors ligne")
        else:
            last = releves[0].timestamp
            context['date'].append("{:02d}/{:02d}/{:04d} - {:02d}:{:02d}:{:02d}".format(last.day,
                                                                                        last.month,
                                                                                        last.year,
                                                                                        last.hour,
                                                                                        last.minute,
                                                                                        last.second))
            if timezone.now() - releves[0].timestamp < timezone.timedelta(hours=6):
                context['status'].append("En ligne")
            else:
                context['status'].append("Hors ligne")

    context['list_serres'] = zip(context['serres'],
                                 range(1, len(context['serres']) + 1),
                                 context['status'],
                                 context['date'])
    return render(request, "User/detail.html", context)


def user_delete(request, uidb64, token):
    context = {
        'errors': [],
        'token': token,
        'uidb64': uidb64
    }

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, User.DoesNotExist):
        user = None
        context['errors'].append("Le lien est invalide, contactez un administrateur")

    if user is not None:
        if request.POST:
            if account_activation_token.check_token(user, token):
                if request.POST.get('cancel', None):
                    return redirect("/?code=2")
                if request.POST.get('delete', None):
                    user.delete()
                    return redirect("/?code=3")
            context['errors'].append("Le lien est invalide, recommencez la procédure")

    return render(request, "User/delete.html", context)


@login_required(login_url="/login/")
def user_ask_delete(request, pk):
    context = {
        'errors': [],
        'user': None,
    }
    if request.POST:
        try:
            context['user'] = User.objects.get(pk=pk)
        except User.DoesNotExist:
            context['errors'].append("L'utilisateur demandé n'existe pas.")

        if context['user'] is not None:
            __send_delete_email(request, context['user'])
            return redirect("/?code=4")

    return render(request, "User/detail.html", context)
