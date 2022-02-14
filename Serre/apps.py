import datetime

import pytz
from django.apps import AppConfig


class SerreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Serre'

    # Création du compte super-utilisateur
    def ready(self):
        from django.contrib.auth.models import User
        import sqlite3

        try:
            User.objects.get(username__exact="admin")
        except User.DoesNotExist:
            admin = User(username="admin", is_superuser=True, is_staff=True, is_active=True)
            admin.set_password("Admin80080")
            admin.save()
        except sqlite3.OperationalError:
            pass
