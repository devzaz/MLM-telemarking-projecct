from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.core.mail import send_mail
from django.contrib import messages
from .forms import UserRegisterForm
from .models import User
import uuid


def register(request):
    if request.method =='POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            verification_token = str(uuid.uuid4())
            request.session['verify_token'] = verification_token
            send_mail(
                'Verify your SSB Account',
                f'Hello {user.username}, please verify your account using this link: '
                f'http://127.0.0.1:8000/verify/{verification_token}/',
                'noreply@ssbcrm.com',
                [user.email],
            )
            messages.success(request, 'Please check your email to verify your account.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})



def verify_account(request, token):
    stored = request.session.get('verify_token')
    if stored and stored == token:
        user = User.objects.last()
        user.is_verified = True
        user.save()
        messages.success(request, 'Your account has been verified. You can now log in.')
        return redirect('login')
    messages.error(request, 'Verification failed. Invalid token.')
    return redirect('register')