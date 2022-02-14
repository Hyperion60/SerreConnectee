#!/bin/sh

cd /home/django/
mv Serre/apps.py /tmp/

python manage.py makemigrations
python manage.py makemigrations Serre

python manage.py migrate
python mange.py migrate Serre

mv /tmp/apps.py Serre/apps.py

mkdir /media/www/csv/

python manage.py collectstatic --noinput

uwsgi --ini "/home/django/deploiements/settings.ini"