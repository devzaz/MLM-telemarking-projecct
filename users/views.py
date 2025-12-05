from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.core.mail import send_mail
from django.contrib import messages
from .forms import UserRegisterForm
from .models import User
import uuid
from django.utils import timezone
from django.urls import reverse


# def register(request):
#     get_ref = request.GET.get('ref')
#     if request.method =='POST':
#         form = UserRegisterForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.is_active = False
#             # attach referral code temporarily so mlm.signals can pick it up
#             ref = form.cleaned_data.get('referral_code') or get_ref
#             if ref:
#                 user._mlm_referral_code = ref.strip()
#             user.save()
#             verification_token = str(uuid.uuid4())
#             request.session['verify_token'] = verification_token
#             send_mail(
#                 'Verify your SSB Account',
#                 f'Hello {user.username}, please verify your account using this link: '
#                 f'http://127.0.0.1:8000/verify/{verification_token}/',
#                 'noreply@ssbcrm.com',
#                 [user.email],
#             )
#             messages.success(request, 'Please check your email to verify your account.')
#             return redirect('users:login')
#     else:
#         initial = {}
#         if get_ref:
#             initial['referral_code'] = get_ref
#         form = UserRegisterForm()
#     return render(request, 'users/register.html', {'form': form, 'ref': get_ref})


#testing
def register(request):
    get_ref = request.GET.get('ref')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # keep account inactive until they verify
            user.is_active = False

            # attach referral code temporarily so mlm.signals can pick it up
            ref = form.cleaned_data.get('referral_code') or get_ref
            if ref:
                user._mlm_referral_code = ref.strip()

            # generate verification token and save on user
            verification_token = str(uuid.uuid4())
            user.verification_token = verification_token
            user.verification_sent_at = timezone.now()
            user.save()

            # build absolute verification URL
            verify_url = request.build_absolute_uri(
                reverse('users:verify', args=[verification_token])
            )

            # send verification email
            send_mail(
                'Verify your SSB Account',
                f'Hello {user.username}, please verify your account using this link: {verify_url}',
                'noreply@ssbcrm.com',
                [user.email],
            )

            messages.success(request, 'Please check your email to verify your account.')
            return redirect('users:login')  # use namespaced login
    else:
        initial = {}
        if get_ref:
            initial['referral_code'] = get_ref
        form = UserRegisterForm()

    return render(request, 'users/register.html', {'form': form, 'ref': get_ref})


# def verify_account(request, token):
#     stored = request.session.get('verify_token')
#     if stored and stored == token:
#         user = User.objects.last()
#         user.is_verified = True
#         user.save()
#         messages.success(request, 'Your account has been verified. You can now log in.')
#         return redirect('login')
#     messages.error(request, 'Verification failed. Invalid token.')
#     return redirect('register')


#testing
def verify_account(request, token):
    try:
        # find the user who has this token and is not yet verified
        user = User.objects.get(verification_token=token, is_verified=False)
    except User.DoesNotExist:
        messages.error(request, 'Verification failed. Invalid or expired token.')
        return redirect('users:register')

    # mark as verified + activate for login
    user.is_verified = True
    user.is_active = True  # IMPORTANT: allow login now
    user.verification_token = None  # clear token so it can't be reused
    user.save(update_fields=['is_verified', 'is_active', 'verification_token'])

    messages.success(request, 'Your account has been verified. You can now log in.')
    return redirect('users:login')
