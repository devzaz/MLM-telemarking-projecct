# reports/urls.py
from django.urls import path
from . import views

app_name = 'reports'
urlpatterns = [
    path('', views.reports_list, name='reports_list'),
    path('builder/', views.report_builder, name='report_builder'),
    path('detail/<int:report_id>/', views.report_detail, name='report_detail'),
    path('report/<int:report_id>/export/', views.enqueue_export, name='enqueue_export'),
    path('exports/', views.export_list, name='export_list'),
    path('export/<int:export_id>/download/', views.download_export, name='download_export'),
    path('export/<int:export_id>/status/', views.export_status, name='export_status'),   # <-- new
]



# # reports/urls.py
# from django.urls import path
# from . import views

# app_name = 'reports'
# urlpatterns = [
#     path('', views.reports_list, name='reports_list'),
#     path('builder/', views.report_builder, name='report_builder'),
#     path('detail/<int:report_id>/', views.report_detail, name='report_detail'),
#     path('report/<int:report_id>/export/', views.enqueue_export, name='enqueue_export'),
#     path('exports/', views.export_list, name='export_list'),
#     path('export/<int:export_id>/download/', views.download_export, name='download_export'),
#     path('export/<int:export_id>/status/', views.export_status, name='export_status'),   # <-- new
# ]
