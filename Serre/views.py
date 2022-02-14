import binascii
import datetime
import os
import json
import re

import pytz
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt

from SerreConnectee.settings import TIME_ZONE
from Serre.models import Serre, Releves


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
                print("longueur: {}".format(len(context['debutjour'].split(':'))))
                raise AttributeError
            if not context['debutjour'].split(':')[0].isdigit() or \
                    not context['debutjour'].split(':')[1].isdigit():
                raise TypeError
            if 23 < int(context['debutjour'].split(':')[0]) < 0 or \
                    23 < int(context['debutjour'].split(':')[1]) < 0:
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
                print("longueur: {}".format(len(context['finjour'].split(':'))))
                raise AttributeError
            if not context['finjour'].split(':')[0].isdigit() or \
                    not context['finjour'].split(':')[1].isdigit():
                raise TypeError
            if 23 < int(context['finjour'].split(':')[0]) < 0 or \
                    23 < int(context['finjour'].split(':')[1]) < 0:
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

        # Récupération du Device EUID
        try:
            context['devEUI'] = request.POST.get('dev-eui', None)
            if context['devEUI']:
                if len(context['devEUI']) != 16:
                    raise ValueError
                for char in context['devEUI']:
                    if 'F' < char < '0':
                        raise TypeError
        except ValueError:
            context['errors'].append("Le Device EUI doit faire 16 caractères hexadécimales de long")
        except TypeError:
            context['errors'].append("Le Device EUI contient des caractères invalides (non-compris entre 0 et F)")

        # Récupération du Device Address
        try:
            context['devAdr'] = request.POST.get('dev-adr', None)
            if context['devAdr']:
                if len(context['devAdr']) != 8:
                    raise ValueError
                for char in context['devAdr']:
                    if 'F' < char < '0':
                        raise TypeError
        except ValueError:
            context['errors'].append("Le Device Address doit faire 8 caractères hexadécimales de long")
        except TypeError:
            context['errors'].append("Le Device Address contient des caractères invalides (non-compris entre 0 et F)")

        # Récupération de la clé Réseau
        try:
            context['nwkSKey'] = request.POST.get('nwkskey', None)
            if context['nwkSKey']:
                if len(context['nwkSKey'].split(',')) != 16:
                    raise ValueError
                if not re.match("(0x[0-9A-F]{2}){1}(, 0x[0-9A-F]{2}){15}", context['nwkSKey']) and \
                        not re.match("(0x[0-9A-F]{2}){1}(,0x[0-9A-F]{2}){15}", context['nwkSKey']):
                    raise TypeError
        except ValueError:
            context['errors'].append("La Clé Réseau doit faire 16 elements de long")
        except TypeError:
            context['errors'].append("La Clé Réseau contient des caractères invalides (non-compris entre 0 et F)")

        # Récupération de la clé applicative
        try:
            context['appSKey'] = request.POST.get('appskey', None)
            if context['appSKey']:
                if len(context['appSKey'].split(',')) != 16:
                    raise ValueError
                if not re.match("(0x[0-9A-F]{2}){1}(, 0x[0-9A-F]{2}){15}", context['appSKey']) and \
                        not re.match("(0x[0-9A-F]{2}){1}(,0x[0-9A-F]{2}){15}", context['appSKey']):
                    raise TypeError
        except ValueError:
            context['errors'].append("La Clé Applicative doit faire 16 elements de long")
        except TypeError:
            context['errors'].append("La Clé Applicative contient des caractères invalides (non-compris entre 0 et F)")

        # Récupération du nom de la Wifi
        context['ssid'] = request.POST.get('wifi-name', None)

        # Récupération de la clé Wifi WPA
        context['pass-wpa'] = request.POST.get('wpa-key', None)

        # Récupération des crédentials PEAP
        context['login-peap'] = request.POST.get('peap-id', None)
        context['pass-peap'] = request.POST.get('peap-key', None)

        # Mise à jour de la serre
        context['serre'].name = context['name']
        context['serre'].type_culture = context['culture']

        context['serre'].seuil_temp = context['temp']
        context['serre'].seuil_air_humid = context['hum-air']
        context['serre'].seuil_sol_humid = context['hum-sol']
        context['serre'].debut_jour = datetime.time(
            hour=int(context['debut'].split(':')[0]),
            minute=int(context['debut'].split(':')[1])
        )
        context['serre'].fin_jour = datetime.time(
            hour=int(context['fin'].split(':')[0]),
            minute=int(context['fin'].split(':')[1])
        )

        context['serre'].DeviceEUI = context['devEUI']
        context['serre'].DevAddr = context['devAdr']
        context['serre'].NetworkSKey = context['nwkSKey']
        context['serre'].AppSKey = context['appSKey']

        context['serre'].ssid = context['ssid']
        context['serre'].password_wpa = context['pass-wpa']
        context['serre'].login_peap = context['login-peap']
        context['serre'].password_peap = context['pass-peap']

        context['serre'].save()
        return redirect("/detail/?code=1")
    return render(request, "Serre/modify-serre.html", context)


@login_required(login_url="/login/")
def delete_serre(request, pk):
    context = {}
    try:
        context['serre'] = Serre.objects.get(pk=pk)
        if not context['serre'].user.pk == request.user.pk:
            raise KeyError
    except Serre.DoesNotExist:
        return redirect("/detail/?err=1")
    except KeyError:
        return redirect("/detail/?err=2")

    if request.POST:
        if request.POST.get('cancel', None):
            return redirect("/detail/?code=2")
        else:
            for releve in Releves.objects.filter(serre_id=context['serre'].pk):
                releve.delete()
            context['serre'].delete()
            return redirect("/detail/?code=3")

    return render(request, "Serre/delete_serre.html", context)


@csrf_exempt
def lora_releve(request):
    context = {
        'errors': [],
        'json': json.loads(request.body.decode()),
        'serre': Serre.objects.get(DeviceEUI__exact=json.loads(request.body.decode())['end_device_ids']['dev_eui']),
        'str': ""
    }
    if not context['json']:
        return HttpResponse("Données manquantes")

    debut = False
    for ele in context['json']['uplink_message']['decoded_payload']['brut']:
        if ele == ord('#'):
            debut = True
        if ele and debut and ele != ord('#'):
            context['str'] += chr(ele)

    print(context['str'])
    context['list'] = context['str'].split(',')

    new_releve = Releves(
        serre=context['serre'],
        temperature=float(context['list'][0]),
        air_humidity=float(context['list'][1]),
        sol_humidity=(int(context['list'][2]) * 100) / 256,
        pression=int(context['list'][3]),
        luminosite=int(context['list'][4]),
        timestamp=datetime.datetime.now(pytz.timezone(TIME_ZONE)),
    )
    new_releve.save()

    return HttpResponse("Relevé ajouté !")


@csrf_exempt
def wifi_releve(request):
    context = {
        'errors': [],
        'data': request.body.decode(),
    }
    # Input format : <releves>\n<token>

    try:
        data = context['data'].split('\n')[0]
        token = context['data'].split('\n')[1]
        context['serre'] = Serre.objects.get(token__exact=token)
        debut = False
        for ele in data:
            if ele == ord('#'):
                debut = True
            if ele and debut and ele != ord('#'):
                context['str'] += chr(ele)

        context['list'] = context['str'].split(',')

        new_releve = Releves(
            serre=context['serre'],
            temperature=float(context['list'][0]),
            air_humidity=float(context['list'][1]),
            sol_humidity=(int(context['list'][2]) * 100) / 256,
            pression=int(context['list'][3]),
            luminosite=int(context['list'][4]),
            timestamp=datetime.datetime.now(pytz.timezone(TIME_ZONE)),
        )
        new_releve.save()
    except Serre.DoesNotExist:
        return HttpResponse("KO - Invalid Token")

    now = datetime.datetime.now(pytz.timezone(TIME_ZONE))

    response = "{},{},{},{},{},{},{}".format(
        context['serre'].seuil_temp,
        context['serre'].seuil_sol_humid,
        context['serre'].seuil_air_humid,
        context['serre'].seuil_lumino_value,
        context['serre'].debut_jour.hour * 60 + context['serre'].debut_jour.minute,
        context['serre'].fin_jour.hour * 60 + context['serre'].fin_jour.minute,
        now.hour * 60 + now.minute,
    )
    return HttpResponse(response)
