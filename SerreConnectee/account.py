from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required(login_url="/login/")
def account_detail(request):
    context = {
        'errors': [],
        'user': request.user,
    }
    return render(request, "User/detail.html", context)
