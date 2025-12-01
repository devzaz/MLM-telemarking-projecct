from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('', views.lead_list, name='lead_list'),
    path('create/', views.lead_create, name='lead_create'),
    path('<int:pk>/edit/', views.lead_update, name='lead_update'),
    path('<int:pk>/delete/', views.lead_delete, name='lead_delete'),
    path('<int:pk>/', views.lead_detail, name='lead_detail'),
    path('assign/<int:pk>/', views.assign_lead, name='lead_assign'),
    path('import-csv/', views.import_leads_view, name='lead_import_csv'),
    path('api/leads/', views.leads_api, name='leads_api'),
]
