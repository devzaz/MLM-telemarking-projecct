# payments/urls.py
from django.urls import path
from . import views

app_name = 'payments'
urlpatterns = [
    path('', views.list_payouts, name='list'),
    path('create/', views.create_payout, name='create'),
    path('detail/<int:pk>/', views.payout_detail, name='detail'),
    path('process/<int:pk>/', views.process_payout, name='process'),

    path('request/', views.payout_request, name='payout_request'),
    path('history/', views.payout_history, name='payout_history'),
    path('admin/', views.payout_admin_list, name='payout_admin_list'),
]
