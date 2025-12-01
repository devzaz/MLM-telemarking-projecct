from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    referral_code = forms.CharField(
        max_length=12, required=False,
        label='Referral code (optional)',
        widget=forms.TextInput(attrs={'placeholder': 'Enter referral code', 'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'role', 'password1', 'password2']