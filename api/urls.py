# api/urls.py
from django.urls import path
from .views import SaleVerifyView, ReferralCheckView

urlpatterns = [
    path('sale/verify/', SaleVerifyView.as_view(), name='sale_verify'),
    path('referral/check/', ReferralCheckView.as_view(), name='referral_check'),
]
