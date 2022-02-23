import datetime

from Serre.models import Releves


def clean_database():
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    two_weeks = Releves.objects.filter(timestamp__lt=now - datetime.timedelta(days=2)).filter(timestamp__gte=now - datetime.timedelta(days=7))
    two_len = len(two_weeks)
    i = 0

    while i < two_len:
        begin = two_weeks[i].timestamp
        j = 0
        sum_temp, sum_hygro_air, sum_hygro_sol, sum_light, sum_pres = 0, 0, 0, 0, 0
        while i + j < two_len and (two_weeks[i + j].timestamp - begin).total_seconds() < 300:
            sum_temp += two_weeks[i + j].temperature
            sum_hygro_air += two_weeks[i + j].air_humidity
            sum_hygro_sol += two_weeks[i + j].sol_humidity
            sum_light += two_weeks[i + j].luminosite
            sum_pres += two_weeks[i + j].pression
            print("Pression(pk={}): {}, sum={}".format(two_weeks[i + j].pk, two_weeks[i + j].pression, sum_pres))
            if j > 0:
                two_weeks[i + j].delete()
            j += 1

        if i + j > two_len:
            j -= 1
        if j != 0:
            two_weeks[i].temperature = sum_temp / j
            two_weeks[i].air_humidity = sum_hygro_air / j
            two_weeks[i].sol_humidity = sum_hygro_sol / j
            two_weeks[i].luminosite = sum_light / j
            two_weeks[i].pression = sum_pres / j
            print("Total: {}/{} = {}".format(sum_pres, j, two_weeks[i].pression))
            two_weeks[i].save()
            i += j
        else:
            i += 1

    old = Releves.objects.filter(timestamp__lt=now - datetime.timedelta(days=7))
    old_len = len(old)
    i = 0
    while i < old_len:
        begin = old[i].timestamp
        j = 0
        sum_temp, sum_hygro_air, sum_hygro_sol, sum_light, sum_pres = 0, 0, 0, 0, 0
        while i + j < old_len and (old[i + j].timestamp - begin).total_seconds() < 15 * 60:
            sum_temp += old[i + j].temperature
            sum_hygro_air += old[i + j].air_humidity
            sum_hygro_sol += old[i + j].sol_humidity
            sum_light += old[i + j].luminosite
            sum_pres += old[i + j].pression
            print("Pression(pk={}): {}, sum={}".format(old[i + j].pk, old[i + j].pression, sum_pres))
            if i + j < old_len and j > 0:
                old[i + j].delete()
            j += 1

        if i + j > old_len:
            j -= 1
        if j > 0:
            old[i].temperature = sum_temp / j
            old[i].air_humidity = sum_hygro_air / j
            old[i].sol_humidity = sum_hygro_sol / j
            old[i].luminosite = sum_light / j
            old[i].pression = sum_pres / j
            print("Total: {}/{} = {}".format(sum_pres, j, old[i].pression))
            old[i].save()
            i += j
        else:
            i += 1

    trash = Releves.objects.filter(timestamp__lt=now - datetime.timedelta(weeks=10))
    for releve in trash:
        releve.delete()


def clean_invalid():
    for releve in Releves.objects.all():
        if releve.luminosite > 65536 or releve.sol_humidity > 100 or releve.air_humidity > 100:
            releve.delete()
