from django.db import models
from django.contrib.auth.models import User


class Serre(models.Model):
    name = models.CharField(unique=True, default="New serre", max_length=250)
    type_culture = models.CharField(default="Cannabis", max_length=250)
    # Authentification
    token = models.CharField(unique=True, max_length=64, default="000000")

    # Actionneurs
    chauffage = models.BooleanField(default=False)
    ventilo = models.BooleanField(default=False)
    arrosage = models.BooleanField(default=False)
    lumiere = models.BooleanField(default=False)
    trappe_open = models.BooleanField(default=False)

    # Seuils
    seuil_temp = models.FloatField(default=20)
    seuil_air_humid = models.FloatField(default=20)
    seuil_sol_humid = models.FloatField(default=50)
    seuil_lumino_value = models.IntegerField(default=1500)
    debut_jour = models.TimeField(default=None)
    fin_jour = models.TimeField(default=None)

    # Options
    DeviceEUI = models.CharField(default=None, max_length=16, null=True)
    user = models.ForeignKey(User, models.CASCADE, default=None)


class Releves(models.Model):
    serre = models.ForeignKey(Serre, models.CASCADE, default=None)
    temperature = models.FloatField(default=0)
    air_humidity = models.FloatField(default=0)
    sol_humidity = models.FloatField(default=0)
    luminosite = models.IntegerField(default=0)
    air_qualite = models.FloatField(default=0)
    accelero_x = models.FloatField(default=0)
    accelero_y = models.FloatField(default=0)
    accelero_z = models.FloatField(default=0)
    timestamp = models.DateTimeField(default=None)
