from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


app_name = "users"

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify/<str:token>/', views.verify_account, name='verify'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html')),

]
