import binascii, datetime, os

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.datastructures import MultiValueDictKeyError

from Serre.models import Serre


@login_required(login_url="/login/")
def serre_add(request):
    context = {
        'errors': [],
        'user': request.user,
        'serre': None,
        'next': request.GET.get('next', ''),
        'restricted': "Yes",
    }

    if request.POST:
        try:
            name = request.POST['name']
            culture = request.POST['culture']
            try:
                Serre.objects.get(name=name)
                raise ReferenceError()
            except Serre.DoesNotExist:
                pass
            new_serre = Serre(name=name,
                              type_culture=culture,
                              debut_jour=datetime.time(8, 00, 00),
                              fin_jour=datetime.time(20, 00, 00),
                              user_id=request.user.pk,
                              token=binascii.hexlify(os.urandom(15)).decode())
            new_serre.save()
            context['serre'] = new_serre
            return redirect("/?code=5")
        except MultiValueDictKeyError:
            context['errors'].append("Champs manquants")
        except ReferenceError:
            context['errors'].append("Une serre porte déjà ce nom")

    return render(request, "Serre/add-serre.html", context)


def renew_token(request, token):
    context = {}
    try:
        context['serre'] = Serre.objects.get(token__exact=token)
    except Serre.DoesNotExist:
        return JsonResponse({'error': "Token invalide, veuillez rafraîchir la page avant de réessayer"})

    context['serre'].token = binascii.hexlify(os.urandom(15)).decode()
    context['serre'].save()
    return JsonResponse({'token': context['serre'].token})


@login_required(login_url="/login/")
def modify_serre(request, pk):
    context = {
        'errors': [],
        'next': request.GET.get('next', '/detail'),
    }
    try:
        context['serre'] = Serre.objects.get(pk=pk)
        context['debut'] = "{:02d}:{:02d}".format(context['serre'].debut_jour.hour, context['serre'].debut_jour.minute)
        context['fin'] = "{:02d}:{:02d}".format(context['serre'].fin_jour.hour, context['serre'].fin_jour.minute)
        if not context['serre'].DeviceEUI:
            context['eui'] = ""
        else:
            context['eui'] = context['serre'].DeviceEUI
        if request.user != context['serre'].user:
            raise AssertionError
    except Serre.DoesNotExist:
        context['errors'].append("La serre demandée n'existe pas, clé primaire introuvable")
    except AssertionError:
        context['errors'].append("Vous ne pouvez pas modifier une serre qui ne vous appartient pas")

    if len(context['errors']):
        return render(request, "User/detail.html", context)

    if request.POST:
        try:
            context['name'] = request.POST['name']
            context['culture'] = request.POST['culture']
            context['lora'] = request.POST.get('lora', '')
            context['debutjour'] = request.POST['debut']
            context['finjour'] = request.POST['fin']
            if not len(context['name']):
                raise ValueError("Name")
            if not len(context['culture']):
                raise ValueError("Culture")
            if not context['debutjour'].split(':')[0].isdigit() or \
                    not context['debutjour'].split(':')[1].isdigit():
                raise TypeError("Debut")
            if not context['finjour'].split(':')[0].isdigit() or \
                    not context['finjour'].split(':')[1].isdigit():
                raise TypeError("Fin")
            context['serre'].name = context['name']
            context['serre'].type_culture = context['culture']
            if len(context['lora']):
                context['serre'].DeviceEUI = context['lora']
            context['serre'].debut_jour = datetime.time(
                hour=int(context['debutjour'].split(':')[0]),
                minute=int(context['debutjour'].split(':')[1]),
            )
            context['serre'].fin_jour = datetime.time(
                hour=int(context['finjour'].split(':')[0]),
                minute=int(context['finjour'].split(':')[1]),
            )
            context['serre'].save()
            return redirect("/detail/?code=1")
        except MultiValueDictKeyError:
            context['errors'].append("Un ou plusieurs champs manquants")
        except (IndexError, TypeError):
            context['errors'].append("Le format des champs de temps est '13:59'")
        except ValueError as err:
            context['errors'].append("Le champs {} ne peut pas être vide".format(err.args[0]))

    return render(request, "Serre/modify-serre.html", context)
