import csv
import os
import time
from django.http import JsonResponse
from django_sendfile import sendfile
from django.views.decorators.cache import cache_page

import Serre.views
from SerreConnectee.settings import STATIC_ROOT
from Serre.models import Releves, Serre


# create_csv(Serre serre)
def create_csv(serre):
    headers = ['id', 'Temperature', 'Humidite air', 'Humidite sol', 'luminosite', 'pression', 'date']
    data = []
    for releve in Releves.objects.filter(serre=serre).order_by('pk'):
        dico = {
            'id': releve.pk,
            'Temperature': releve.temperature,
            'Humidite air': releve.air_humidity,
            'Humidite sol': releve.sol_humidity,
            'luminosite': releve.luminosite,
            'pression': releve.pression,
            'date': releve.timestamp.strftime("%Y/%m/%d %H:%M:%S"),
        }
        data.append(dico)

    if not os.getenv("PRODUCTION"):
        csv_path = "static/csv/data_{}.csv".format(serre.pk)
    else:
        csv_path = "{}csv/data_{}.csv".format(STATIC_ROOT, serre.pk)

    # Regenerate if file has more than 60 seconds from the last generation
    if os.path.exists(csv_path) and time.time() - os.path.getmtime(csv_path) < 60:
        return "data_{}.csv".format(serre.pk)

    with open(csv_path, 'w+', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

    return "data_{}.csv".format(serre.pk)


# download_csv(Request request, int pk)
def download_csv(request, pk):
    try:
        serre = Serre.objects.get(pk=pk)
    except Serre.DoesNotExist:
        return JsonResponse({"error": "La serre n'existe pas"})

    path_csv = create_csv(serre)
    return sendfile(request, path_csv, True, path_csv, "text/csv")


# create_json(Serre serre)
def create_json(serre):
    releves = []
    for releve in Releves.objects.filter(serre__pk=serre.pk):
        releves.append({
            'time': releve.timestamp.strftime("%d/%m/%Y %H:%M"),
            'temp': releve.temperature,
            'air': releve.air_humidity,
            'sol': releve.sol_humidity,
            'light': releve.luminosite,
            'pres': releve.pression,
        })
    return releves


@cache_page(60 * 3)
def get_releve(request, pk):
    context = {}
    try:
        context['serre'] = Serre.objects.get(pk=pk)
    except Serre.DoesNotExist:
        return JsonResponse(request, {'error': "La serre demandée n'existe pas"})

    return JsonResponse(request, {'data': create_json(context['serre'])})
