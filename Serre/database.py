import datetime

from Serre.models import Releves


def clean_database():
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    releves = Releves.objects.filter(timestamp__gt=now + datetime.timedelta(days=7))
    old = releves.filter(timestamp__gt=now + datetime.timedelta(days=14))
    two_weeks = releves.filter(timestamp__gt=now + datetime.timedelta(days=7)).filter(timestamp__lte=now + datetime.timedelta(days=14))

    old_len = len(old)
    two_len = len(two_weeks)

    for i in range(0, two_len):
        begin = two_weeks[i].timestamp
        j = 0
        sum_temp, sum_hygro_air, sum_hygro_sol, sum_light, sum_pres = 0, 0, 0, 0, 0
        while (begin - two_weeks[i + j].timestamp).total_seconds > 300:
            sum_temp += two_weeks[i + j].temperature
            sum_hygro_air += two_weeks[i + j].air_humidity
            sum_hygro_sol += two_weeks[i + j].sol_humidity
            sum_light += two_weeks[i + j].luminosite
            sum_pres += two_weeks[i + j].pression
            two_weeks[i + j].delete()
            j += 1

        two_weeks[i].temperature = sum_temp / j
        two_weeks[i].air_humidity = sum_hygro_air / j
        two_weeks[i].sol_humidity = sum_hygro_sol / j
        two_weeks[i].luminosite = sum_light / j
        two_weeks[i].pression = sum_pres / j
        two_weeks[i].save()
        i += (j - 1)

    for i in range(0, old_len):
        begin = old[i].timestamp
        j = 0
        sum_temp, sum_hygro_air, sum_hygro_sol, sum_light, sum_pres = 0, 0, 0, 0, 0
        while (begin - old[i + j].timestamp).total_seconds > 60 * 15:
            sum_temp += old[i + j].temperature
            sum_hygro_air += old[i + j].air_humidity
            sum_hygro_sol += old[i + j].sol_humidity
            sum_light += old[i + j].luminosite
            sum_pres += old[i + j].pression
            old[i + j].delete()
            j += 1

        old[i].temperature = sum_temp / j
        old[i].air_humidity = sum_hygro_air / j
        old[i].sol_humidity = sum_hygro_sol / j
        old[i].luminosite = sum_light / j
        old[i].pression = sum_pres / j
        old[i].save()
        i += (j - 1)
