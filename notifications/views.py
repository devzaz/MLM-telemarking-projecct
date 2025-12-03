# notifications/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification
from django.utils.timesince import timesince

@login_required
def unread_json(request):
    items = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    data = {
        'unread_count': unread_count,
        'items': [
            {'id': n.pk, 'title': n.title, 'message': n.message[:120], 'url': n.url or '#', 'time': timesince(n.created_at) + ' ago'}
            for n in items
        ]
    }
    return JsonResponse(data)

@login_required
def notifications_list(request):
    qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications/list.html', {'notifications': qs})

@login_required
def mark_read(request, pk):
    n = Notification.objects.filter(pk=pk, user=request.user).first()
    if n:
        n.is_read = True
        n.save()
    return JsonResponse({'ok': True})
