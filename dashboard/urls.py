from django.urls import path
from .views import index
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', index, name='dashboard-index'),
    # API endpoints
    path('api/summary/', views.DashboardSummaryAPIView.as_view(), name='api_summary'),
    path('api/telemarketer/<int:user_id>/overview/', views.TelemarketerOverviewAPIView.as_view(), name='api_tele_overview'),
]
