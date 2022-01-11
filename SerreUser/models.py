import os
from uuid import uuid4

from django.db import models
from django.contrib.auth.models import User


def rename_file(path):
    def wrapper(instance, filename):
        ext = filename.split('.')[-1]
        if instance.pk:
            filename = "{}.{}".format(instance.pk, ext)
        else:
            filename = "{}.{}".format(uuid4().hex, ext)
        return os.path.join(path, filename)
    return wrapper


class SerreUser(models.Model):
    user = models.ForeignKey(User, unique=True)
    user_image = models.ImageField(upload_to=rename_file('avatar/'))

    def is_active(self):
        return self.user.is_active

    def is_staff(self):
        return self.user.is_staff

