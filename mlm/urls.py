from django.urls import path
from . import views

app_name = 'mlm'

urlpatterns = [
    path('network/', views.user_network_view, name='user_network'),
    path('api/node/<int:node_id>/', views.api_node_detail, name='api_node_detail'),
    path('api/subtree/<int:node_id>/', views.api_subtree, name='api_subtree'),
    path('api/admin/place/', views.api_force_place, name='api_force_place'),
]
