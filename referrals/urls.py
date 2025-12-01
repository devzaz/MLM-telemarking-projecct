from django.urls import path
from . import views

app_name = 'referrals'

urlpatterns = [
    path('api/record-conversion/', views.api_record_conversion, name='api_record_conversion'),
    path('api/metrics/', views.api_referral_metrics, name='api_referral_metrics'),

    # new UI pages (staff-protected)
    path('dashboard/', views.referrals_dashboard_page, name='referrals_dashboard_page'),
    path('partner-onboarding/', views.partner_onboarding, name='partner_onboarding'),
    path('partner-dashboard/', views.partner_dashboard, name='partner_dashboard'),
]
