from django.contrib import admin
from django.urls import path, include
from dashboard import views as dashboard_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls', namespace='dashboard')),
    path('', include('users.urls',namespace='users')),
    path('mlm/', include('mlm.urls', namespace='mlm')),
    path('crm/', include(('crm.urls', 'crm'), namespace='crm')),
    path('referrals/', include(('referrals.urls', 'referrals'), namespace='referrals')),
    path('commissions/', include('commissions.urls', namespace='commissions')),
    path('api/', include('api.urls')),
    path('reports/', include('reports.urls', namespace='reports')),



]


from rest_framework_simplejwt.views import TokenObtainPairView
urlpatterns += [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
]
