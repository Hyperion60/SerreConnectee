from django.shortcuts import render
# Create your views here.


def login(request):
    context = {
        'next': request.GET.get('next', ''),
        'errors': [],
    }
    if request.user.is_authenticated:
        context['errors'].append("Vous êtes déjà connecté !")
        return render(request, "index.html", context)

    if request.POST:
        pass

    return render(request, "User/login.html", context)
