# payments/admin.py
from django.contrib import admin
from .models import PayoutRequest

@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = ('id','request_id','user','amount','currency','method','status','created_at','processed_at','processed_by')
    list_filter = ('status','currency','method')
    search_fields = ('request_id','user__username','user__email')
