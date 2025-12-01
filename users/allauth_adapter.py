# users/allauth_adapter.py
from allauth.account.adapter import DefaultAccountAdapter

class MyAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        ref = request.GET.get('ref') or request.POST.get('ref')
        user = super().save_user(request, user, form, commit=False)
        if ref:
            user._mlm_referral_code = ref.strip()
        if commit:
            user.save()
        return user
