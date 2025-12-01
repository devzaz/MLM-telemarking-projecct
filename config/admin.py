# config/admin.py or someapp/admin.py
from django.contrib import admin
from rest_framework.authtoken.models import Token

admin.site.register(Token)
