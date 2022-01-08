#!/bin/sh

python manage.py makemigrations
python manage.py makemigrations Serre

python manage.py migrate
python mange.py migrate Serre

python manage.py collectstatic

uwsgi --ini "deploiements/settings.ini"