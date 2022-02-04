import binascii, datetime, os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError

from Serre.models import Serre


@login_required(login_url="/login/")
def serre_add(request):
    context = {
        'errors': [],
        'user': request.user,
        'serre': None,
        'next': request.GET.get('next', ''),
        'restricted': "Yes",
    }

    if request.POST:
        try:
            name = request.POST['name']
            culture = request.POST['culture']
            try:
                Serre.objects.get(name=name)
                raise ReferenceError()
            except Serre.DoesNotExist:
                pass
            new_serre = Serre(name=name,
                              type_culture=culture,
                              debut_jour=datetime.time(8, 00, 00),
                              fin_jour=datetime.time(20, 00, 00),
                              user_id=request.user.pk,
                              token=binascii.hexlify(os.urandom(15)).decode())
            new_serre.save()
            context['serre'] = new_serre
        except MultiValueDictKeyError:
            context['errors'].append("Champs manquants")
        except ReferenceError:
            context['errors'].append("Une serre porte déjà ce nom")

    return render(request, "Serre/add-serre.html", context)
