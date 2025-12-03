# payments/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse
from .models import PayoutRequest
from notifications.models import Notification
from django.conf import settings
from django.contrib import messages
from .tasks import send_payout_notifications
from django.utils import timezone

def is_staff(user):
    return user.is_authenticated and user.is_staff

@login_required
def create_payout(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        method = request.POST.get('method','bank_transfer')
        details = request.POST.get('details','')  # JSON string or simple text
        try:
            amount = float(amount)
        except Exception:
            messages.error(request, "Invalid amount")
            return redirect('payments:create')

        pr = PayoutRequest.objects.create(user=request.user, amount=amount, method=method, details={'raw': details})
        # create notification for admin(s)
        Notification.objects.create(user=request.user, title='Payout request submitted', message=f'Your payout request {pr.request_id} for {pr.amount} has been submitted.', url=reverse('payments:detail', args=[pr.pk]))
        # notify admins/staff
        send_payout_notifications.delay(pr.pk, event='created')
        messages.success(request, "Payout request submitted")
        return redirect('payments:list')
    return render(request, 'payments/create.html')

@login_required
def list_payouts(request):
    # user's own payouts or if staff see all
    if request.user.is_staff:
        qs = PayoutRequest.objects.all()
    else:
        qs = PayoutRequest.objects.filter(user=request.user)
    return render(request, 'payments/list.html', {'payouts': qs})

@login_required
def payout_detail(request, pk):
    pr = get_object_or_404(PayoutRequest, pk=pk)
    if not (request.user.is_staff or pr.user == request.user):
        return HttpResponseForbidden("Not allowed")
    return render(request, 'payments/detail.html', {'pr': pr})

@login_required
@user_passes_test(is_staff)
def process_payout(request, pk):
    pr = get_object_or_404(PayoutRequest, pk=pk)
    action = request.POST.get('action')
    admin_user = request.user
    if action == 'approve':
        pr.status = 'approved'
        pr.processed_by = admin_user
        pr.processed_at = pr.processed_at or timezone.now()
        pr.admin_note = request.POST.get('admin_note','')
        pr.save()
        # send notifications async
        send_payout_notifications.delay(pr.pk, event='approved')
        messages.success(request, "Payout approved")
    elif action == 'reject':
        pr.status = 'rejected'
        pr.processed_by = admin_user
        pr.processed_at = pr.processed_at or timezone.now()
        pr.admin_note = request.POST.get('admin_note','')
        pr.save()
        send_payout_notifications.delay(pr.pk, event='rejected')
        messages.success(request, "Payout rejected")
    elif action == 'mark_paid':
        pr.status = 'paid'
        pr.processed_by = admin_user
        pr.processed_at = pr.processed_at or timezone.now()
        pr.save()
        send_payout_notifications.delay(pr.pk, event='paid')
        messages.success(request, "Payout marked as paid")
    else:
        messages.error(request, "Unknown action")
    return redirect('payments:detail', pk=pr.pk)





# payments/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import PayoutRequest

def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
def payout_request(request):
    # Very simple skeleton: GET shows form, POST creates request (you'll add form validation later)
    if request.method == 'POST':
        amount = request.POST.get('amount')
        # minimal creation; replace with form/validation later
        PayoutRequest.objects.create(user=request.user, amount=amount, currency='BDT', method=request.POST.get('method',''))
        return redirect('payments:payout_history')
    return render(request, 'payments/request.html')

@login_required
def payout_history(request):
    qs = PayoutRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'payments/history.html', {'payouts': qs})

@login_required
@user_passes_test(is_admin)
def payout_admin_list(request):
    # Admin view: list all payout requests for approval
    qs = PayoutRequest.objects.all().order_by('-created_at')
    return render(request, 'payments/admin_list.html', {'payouts': qs})
