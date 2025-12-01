from django.urls import path
from . import views

app_name = 'commissions'

urlpatterns = [
    # API to record sale
    path('api/record-sale/', views.api_record_sale, name='api_record_sale'),

    # Staff/frontend pages
    path('dashboard/wallet/', views.wallet_summary_view, name='wallet_summary'),
    path('history/', views.commission_history_view, name='commission_history'),
]
