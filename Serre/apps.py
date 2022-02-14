import datetime

import pytz
from django.apps import AppConfig


class SerreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Serre'

    # Création du compte super-utilisateur
    def ready(self):
        from django.contrib.auth.models import User
        from Serre.models import Releves
        from SerreConnectee.settings import TIME_ZONE
        import sqlite3

        try:
            User.objects.get(username__exact="admin")
            releves = Releves.objects.all()
            for releve in releves:
                if releve.timestamp.tzinfo == datetime.timezone.utc:
                    releve.replace(hour=releve.hour + 1, tzinfo=pytz.timezone(TIME_ZONE))
                    releve.save()
        except User.DoesNotExist:
            admin = User(username="admin", is_superuser=True, is_staff=True, is_active=True)
            admin.set_password("Admin80080")
            admin.save()
        except sqlite3.OperationalError:
            pass
