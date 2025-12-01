from django.contrib import admin
from .models import Lead, LeadNote

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'assigned_to')
    search_fields = ('name', 'email', 'phone')
    raw_id_fields = ('assigned_to', 'created_by')
    date_hierarchy = 'created_at'

@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'lead', 'author', 'created_at')
    search_fields = ('lead__name', 'author__username', 'text')
