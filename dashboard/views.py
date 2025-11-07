from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    user = request.user
    if not user.is_verified or not user.is_approved:
        return render(request, 'dashboard/pending.html')
    return render(request, 'dashboard/index.html', {'user': user})