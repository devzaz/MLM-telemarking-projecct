from django.urls import path
from . import views
app_name = 'notifications'
urlpatterns = [
  path('unread_json/', views.unread_json, name='unread_json'),
  path('', views.notifications_list, name='list'),
  path('mark_read/<int:pk>/', views.mark_read, name='mark_read'),
]
