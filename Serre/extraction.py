import csv
import datetime
import json
import os
import time
from django.http import JsonResponse, HttpResponse
from django_sendfile import sendfile

import Serre.views
from Serre.database import clean_database
from SerreConnectee.settings import STATIC_ROOT
from Serre.models import Releves, Serre


def __getUTCJS__(timestamp, epoch=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)):
    return int((timestamp - epoch).total_seconds() * 1000)


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
    releves = [
        {
            'name': 'Temperature',
            'data': [],
        },
        {
            'name': 'Hygrometrie de l\'air',
            'data': [],
        },
        {
            'name': 'Hygrometrie du sol',
            'data': [],
        },
        {
            'name': 'Luminosite',
            'data': [],
        },
        {
            'name': 'Pression atmospherique',
            'data': [],
        }
    ]

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    if not serre.last_clean or (now - serre.last_clean).total_seconds() > 60 * 60 * 24:
        clean_database()
        serre.last_clean = now
        serre.save()

    for releve in Releves.objects.filter(serre__pk=serre.pk).order_by('timestamp'):
        ts = __getUTCJS__(releve.timestamp)
        releves[0]['data'].append([ts, releve.temperature])
        releves[1]['data'].append([ts, releve.air_humidity])
        releves[2]['data'].append([ts, releve.sol_humidity])
        releves[3]['data'].append([ts, releve.luminosite])
        releves[4]['data'].append([ts, releve.pression])

    return releves


def get_releve(request, pk):
    context = {}
    try:
        context['serre'] = Serre.objects.get(pk=pk)
    except Serre.DoesNotExist:
        return JsonResponse(request, {'error': "La serre demandée n'existe pas"})

    data = create_json(context['serre'])
    data = json.dumps(data)
    return HttpResponse(data)
