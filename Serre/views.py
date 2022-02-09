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
        # Récupération du nom de la serre
        try:
            context['name'] = request.POST['name']
            if not len(context['name']):
                raise ValueError
        except MultiValueDictKeyError:
            context['errors'].append("Le champs 'nom de la serre' est manquant")
        except ValueError:
            context['errors'].append("Le nom de la serre ne peut pas être vide")

        # Récupération du type de culture
        try:
            context['culture'] = request.POST['culture']
            if not len(context['culture']):
                raise ValueError
        except MultiValueDictKeyError:
            context['errors'].append("Le champs 'type de culture' est manquant")
        except ValueError:
            context['errors'].append("Le type de culture ne peut pas être vide")

        # Récupération de la luminosité minimale
        try:
            context['lumino'] = request.POST['lumino']
            if not context['lumino'].isdigit():
                raise TypeError
            if int(context['lumino']) < 0:
                raise ValueError
        except MultiValueDictKeyError:
            context['errors'].append("Le champ 'Luminosité' est manquant")
        except TypeError:
            context['errors'].append("La luminosité doit être un nombre")
        except ValueError:
            context['errors'].append("La luminosité ne peut pas être négative")

        # Récupération de l'heure de début de journée
        try:
            context['debutjour'] = request.POST['debut']
            if not len(context['debutjour']):
                raise ValueError
            if len(context['debutjour'].split(':')) != 2:
                raise AttributeError
            if not context['debutjour'].split(':')[0].isdigit() or \
                    not context['debutjour'].split(':')[1].isdigit():
                raise TypeError
            if 23 < context['debutjour'].split(':')[0] < 0 or \
                    23 < context['debutjour'].split(':')[1] < 0:
                raise OverflowError
        except MultiValueDictKeyError:
            context['errors'].append("Le champ 'Debut de journée' est manquant")
        except ValueError:
            context['errors'].append("L'heure de début ne peut pas être vide")
        except (AttributeError, TypeError, OverflowError):
            context['errors'].append("L'heure de début n'est pas dans le bon format '13:59'")

        # Récupération de l'heure de fin de journée
        try:
            context['finjour'] = request.POST['fin']
            if not len(context['finjour']):
                raise ValueError
            if len(context['finjour'].split(':')) != 2:
                raise AttributeError
            if not context['finjour'].split(':')[0].isdigit() or \
                    not context['finjour'].split(':')[1].isdigit():
                raise TypeError
            if 23 < context['finjour'].split(':')[0] < 0 or \
                    23 < context['finjour'].split(':')[1] < 0:
                raise OverflowError
        except MultiValueDictKeyError:
            context['errors'].append("Le champ 'Fin de journée' est manquant")
        except ValueError:
            context['errors'].append("L'heure de fin ne peut pas être vide")
        except (AttributeError, TypeError, OverflowError):
            context['errors'].append("L'heure de fin n'est pas dans le bon format '13:59'")

        # Récupération de la température
        try:
            context['temp'] = request.POST['temperature']
            if not len(context['temp']):
                raise ValueError
            if not context['temp'].isdigit():
                raise TypeError
            if int(context['temp']) < -273:
                raise OverflowError
        except MultiValueDictKeyError:
            context['errors'].append("Le champ 'Température' est manquant")
        except ValueError:
            context['errors'].append("La température ne peut pas être vide")
        except OverflowError:
            context['errors'].append("La température ne peut pas être inférieure au zéro absolu")

        # Récupération de l'humidité de l'air
        try:
            context['hum-air'] = request.POST['hum-air']
            if not len(context['hum-air']):
                raise ValueError
            if not context['hum-air'].isdigit():
                raise TypeError
            if 100 < int(context['hum-air']) < 0:
                raise OverflowError
        except MultiValueDictKeyError:
            context['errors'].append("Le champ 'Humidité de l'air' est manquant")
        except ValueError:
            context['errors'].append("L'humidité de l'air ne peut pas être vide")
        except OverflowError:
            context['errors'].append("L'humidité de l'air doit être compris entre 0 et 100")

        # Récupération de l'humidité du sol
        try:
            context['hum-sol'] = request.POST['hum-sol']
            if not len(context['hum-air']):
                raise ValueError
            if not context['hum-air'].isdigit():
                raise TypeError
            if 100 < int(context['hum-air']) < 0:
                raise OverflowError
        except MultiValueDictKeyError:
            context['errors'].append("Le champ 'Humidité du sol' est manquant")
        except ValueError:
            context['errors'].append("L'humidité du sol ne peut pas être vide")
        except OverflowError:
            context['errors'].append("L'humidité du sol doit être compris entre 0 et 100")

    return render(request, "Serre/modify-serre.html", context)
